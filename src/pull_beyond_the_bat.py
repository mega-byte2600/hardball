#!/usr/bin/env python3
"""Moneyball 2.0 exhibit — "Beyond the bat" (Explorer companion panel
under Figure 19, alongside the Cycle 75 bat-speed exhibit).

Fetches three Baseball Savant public leaderboard families for
2024-2026, joins them to the 2027 free-agent pool, and computes
year-to-year persistence plus a small out-of-sample pitch-trait test.
Everything is DIAGNOSTIC: per standing claim N04, Savant traits do NOT
adjust projections, and this script feeds no projection.

Boards (all keyless Savant leaderboard CSVs, same fetch family as
src/carpe.py):
  arms   — pitch-arsenal run values (min=100 board: established arms)
  gloves — Outs Above Average (min=1)
  legs   — sprint speed (min=25, the carpe.py form)
  catchers (2026 only) — framing + blocking; both endpoints IGNORE
    year selection (verified 2026-11-12: 2024/2025/2026 pulls
    byte-identical under every parameter form tried), so no
    persistence is computed for catchers.

Outputs (committed):
  data/savant_oaa_{2024,2025,2026}.json
  data/savant_arsenal_{2024,2025,2026}.json
  data/savant_sprint_{2024,2025,2026}.json (refreshed, carpe.py shape)
  data/savant_framing_2026.json, data/savant_blocking_2026.json
  data/pitching_actuals_2024_2026.json (StatsAPI ERA + FIP components)
  data/beyond_the_bat_2027.json (the exhibit artifact)
Raw CSVs land in data/raw/savant/ (local-only, gitignored) and are
registered in data/raw/manifest.jsonl like every other pull.

Fail-closed per block: a failed fetch or an uncomputable persistence
marks that block "unavailable" with a reason; the panel renders
"data unavailable" for it and never fakes a number.
"""
import csv
import hashlib
import io
import json
import math
import os
import time
from datetime import datetime, timezone

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw")
SAVANT_RAW = os.path.join(RAW, "savant")
MLB_RAW = os.path.join(RAW, "mlb_api")
os.makedirs(SAVANT_RAW, exist_ok=True)
os.makedirs(MLB_RAW, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (HARDBALL/1.0 carpe-data)"}
SAVANT = "https://baseballsavant.mlb.com"
MLB = "https://statsapi.mlb.com/api/v1"
FIP_CONSTANT = 3.10  # standard FIP constant; labeled wherever FIP prints
MIN_TOTAL_PITCHES = 300  # workload floor for pitcher-level persistence/model

BOARDS = {
    "oaa": ("leaderboard/outs_above_average?year={y}&position=&team="
            "&min=1&csv=true", "oaa_{y}.csv"),
    "arsenal": ("leaderboard/pitch-arsenal-stats?year={y}&position="
                "&team=&min=100&csv=true", "arsenal_{y}.csv"),
    "sprint": ("leaderboard/sprint_speed?year={y}&position=&team="
               "&min=25&csv=true", "sprint_{y}.csv"),
}
CATCHER_BOARDS = {
    "framing": ("leaderboard/catcher-framing?year=2026&team="
                "&min=100&csv=true", "framing_2026.csv"),
    "blocking": ("leaderboard/catcher-blocking?year=2026&team="
                 "&min=1&csv=true", "blocking_2026.csv"),
}


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _pearson(xs, ys):
    n = len(xs)
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    syy = math.fsum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def _quant(vals, q):
    sv = sorted(vals)
    pos = q * (len(sv) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sv) - 1)
    return sv[lo] * (1 - (pos - lo)) + sv[hi] * (pos - lo)


def _persistence(boards, key, qualifier=None):
    """Year-to-year Pearson r on matched ids, per pair + pooled
    (the Cycle 75 bat-speed shape). boards: {year: {id: row}}."""
    px, py, pairs = [], [], {}
    for a, b in ((2024, 2025), (2025, 2026)):
        ids = [p for p in boards[a] if p in boards[b]]
        if qualifier:
            ids = [p for p in ids
                   if qualifier(boards[a][p]) and qualifier(boards[b][p])]
        xs = [float(boards[a][p][key]) for p in ids]
        ys = [float(boards[b][p][key]) for p in ids]
        pairs[f"{a}_{b}"] = {"r": _pearson(xs, ys), "n": len(ids)}
        px += xs
        py += ys
    return {"pairs": pairs,
            "pooled": {"r": _pearson(px, py), "n_pairs": len(px)}}


def _fetch_csv(url, raw_path):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    with open(raw_path, "w") as f:
        f.write(r.text)
    rows = list(csv.DictReader(io.StringIO(r.text.lstrip("\ufeff"))))
    return rows, r.text


def _manifest(source, dataset, text, rows, note=None):
    entry = {"source": source, "dataset": dataset,
             "fetched_at": datetime.now(timezone.utc).isoformat(),
             "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
             "bytes": len(text.encode()), "rows": rows, "status": "ok"}
    if note:
        entry["note"] = note
    with open(os.path.join(RAW, "manifest.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def _save_json(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
    print(f"wrote {path}")
    return path


def _ip_to_float(s):
    """Baseball IP notation ('182.1' = 182 + 1/3) to float innings."""
    s = str(s)
    if "." not in s:
        return float(s)
    whole, frac = s.split(".")
    return float(whole) + int(frac) / 3.0


def fetch_pitching_actuals(pitcher_ids):
    """Season ERA + FIP components for the arsenal universe, from the
    MLB Stats API (the lake's own source), batched like carpe.py."""
    ids = sorted(pitcher_ids)
    out = {}
    for season in (2024, 2025, 2026):
        rows = []
        for i in range(0, len(ids), 50):
            chunk = ids[i:i + 50]
            r = requests.get(
                f"{MLB}/people",
                params={"personIds": ",".join(str(x) for x in chunk),
                        "hydrate": ("stats(group=[pitching],"
                                    f"type=[season],season={season})")},
                headers=UA, timeout=60)
            r.raise_for_status()
            for p in r.json().get("people", []):
                for grp in p.get("stats", []):
                    for sp in grp.get("splits", []):
                        st = sp["stat"]
                        try:
                            ip = _ip_to_float(st["inningsPitched"])
                        except (KeyError, ValueError):
                            continue
                        if ip <= 0:
                            continue
                        fip = ((13 * st.get("homeRuns", 0)
                                + 3 * (st.get("baseOnBalls", 0)
                                       + st.get("hitBatsmen", 0))
                                - 2 * st.get("strikeOuts", 0)) / ip
                               + FIP_CONSTANT)
                        rows.append({
                            "player_id": p["id"], "season": season,
                            "name": p.get("fullName"),
                            "era": _num(st.get("era")),
                            "fip": round(fip, 4),
                            "ip": round(ip, 3),
                            "k": st.get("strikeOuts"),
                            "bb": st.get("baseOnBalls"),
                            "hbp": st.get("hitBatsmen"),
                            "hr": st.get("homeRuns")})
            time.sleep(1)
        out[season] = {r["player_id"]: r for r in rows}
        raw_path = os.path.join(MLB_RAW, f"pitching_stats_{season}.json")
        with open(raw_path, "w") as f:
            json.dump(rows, f, indent=1)
        _manifest("mlb_api", f"pitching_stats_{season}",
                  json.dumps(rows), len(rows),
                  "StatsAPI hydrate season pitching; FIP constant 3.10")
        print(f"pitching actuals {season}: {len(rows)} pitchers")
    return out


def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    provenance = {"pulled_at_utc": pulled_at, "boards": {}}
    boards, failures = {}, {}

    for family, (tmpl, fname) in BOARDS.items():
        boards[family] = {}
        for y in (2024, 2025, 2026):
            url = f"{SAVANT}/{tmpl.format(y=y)}"
            try:
                rows, text = _fetch_csv(
                    url, os.path.join(SAVANT_RAW, fname.format(y=y)))
                if len(rows) < 100:
                    raise ValueError(f"only {len(rows)} rows")
                boards[family][y] = rows
                provenance["boards"][f"{family}_{y}"] = {
                    "url": url, "rows": len(rows)}
                _manifest("savant", f"{family}_{y}", text, len(rows))
            except Exception as e:  # fail closed per board
                failures[f"{family}_{y}"] = f"{type(e).__name__}: {e}"
                print(f"FAIL {family} {y}: {e}")
            time.sleep(2)
        # year-differentiation trap check: identical pulls = ignored param
        texts = []
        for y in (2024, 2025, 2026):
            p = os.path.join(SAVANT_RAW, fname.format(y=y))
            if os.path.exists(p):
                texts.append(open(p).read())
        if len(texts) == 3 and (texts[0] == texts[1] == texts[2]):
            failures[family] = ("year parameter ignored: all three "
                                "pulls byte-identical")
            print(f"FAIL {family}: year trap")

    catchers = {}
    for family, (path, fname) in CATCHER_BOARDS.items():
        url = f"{SAVANT}/{path}"
        try:
            rows, text = _fetch_csv(url, os.path.join(SAVANT_RAW, fname))
            if len(rows) < 30:
                raise ValueError(f"only {len(rows)} rows")
            catchers[family] = rows
            provenance["boards"][family + "_2026"] = {"url": url,
                                                      "rows": len(rows)}
            _manifest("savant", family + "_2026", text, len(rows),
                      "year selection ignored by endpoint; 2026 board")
        except Exception as e:
            failures[family] = f"{type(e).__name__}: {e}"
            print(f"FAIL {family}: {e}")
        time.sleep(2)

    # ---- parsed JSON boards (the carpe.py pattern) ------------------
    def _parse_oaa(rows):
        return [{"player_id": int(r["player_id"]),
                 "name": r["last_name, first_name"],
                 "team": r.get("display_team_name"),
                 "pos": r.get("primary_pos_formatted"),
                 "outs_above_average": _num(r["outs_above_average"]),
                 "fielding_runs_prevented":
                     _num(r["fielding_runs_prevented"])}
                for r in rows if r.get("player_id")]

    def _parse_arsenal(rows):
        return [{"player_id": int(r["player_id"]),
                 "name": r["last_name, first_name"],
                 "team": r.get("team_name_alt"),
                 "pitch_type": r["pitch_type"],
                 "pitch_name": r["pitch_name"],
                 "run_value_per_100": _num(r["run_value_per_100"]),
                 "run_value": _num(r["run_value"]),
                 "pitches": int(float(r["pitches"])),
                 "pitch_usage": _num(r["pitch_usage"]),
                 "whiff_percent": _num(r["whiff_percent"]),
                 "k_percent": _num(r["k_percent"]),
                 "put_away": _num(r["put_away"]),
                 "est_woba": _num(r["est_woba"]),
                 "hard_hit_percent": _num(r["hard_hit_percent"])}
                for r in rows if r.get("player_id")]

    def _parse_sprint(rows):
        return [{"player_id": int(r["player_id"]),
                 "name": r["last_name, first_name"],
                 "team": r.get("team"), "pos": r.get("position"),
                 "competitive_runs": _num(r["competitive_runs"]),
                 "sprint_speed": _num(r["sprint_speed"]),
                 "hp_to_1b": _num(r["hp_to_1b"]),
                 "age": _num(r.get("age"))}
                for r in rows if r.get("player_id")]

    parsed = {}
    for y in (2024, 2025, 2026):
        if y in boards["oaa"]:
            parsed[("oaa", y)] = _parse_oaa(boards["oaa"][y])
            _save_json(f"savant_oaa_{y}.json", parsed[("oaa", y)])
        if y in boards["arsenal"]:
            parsed[("arsenal", y)] = _parse_arsenal(boards["arsenal"][y])
            _save_json(f"savant_arsenal_{y}.json", parsed[("arsenal", y)])
        if y in boards["sprint"]:
            parsed[("sprint", y)] = _parse_sprint(boards["sprint"][y])
            _save_json(f"savant_sprint_{y}.json", parsed[("sprint", y)])
    if "framing" in catchers:
        _fr = [{"player_id": int(r["id"]), "name": r["name"],
                "pitches": int(float(r["pitches"])),
                "framing_runs": _num(r["rv_tot"])}
               for r in catchers["framing"] if r.get("id")]
        _save_json("savant_framing_2026.json", _fr)
        parsed[("framing", 2026)] = _fr
    if "blocking" in catchers:
        _bl = [{"player_id": int(r["player_id"]),
                "name": r["player_name"], "team": r.get("team_name"),
                "pitches": int(float(r["pitches"])),
                "blocks_above_average": _num(r["blocks_above_average"]),
                "catcher_blocking_runs": _num(r["catcher_blocking_runs"])}
               for r in catchers["blocking"] if r.get("player_id")]
        _save_json("savant_blocking_2026.json", _bl)
        parsed[("blocking", 2026)] = _bl

    # ---- FA pool join ----------------------------------------------
    fa = json.load(open(os.path.join(DATA, "fa_shopping_2027.json")))
    fa_rows = {r["player_id"]: r for r in fa["class"] if r.get("player_id")}
    reg = json.load(open(os.path.join(DATA, "claims_register.json")))
    n04 = next(c for c in reg["claims"] if c["id"] == "N04")
    artifact = {
        "provenance": provenance,
        "fa_pool": {"class_n": fa["metadata"]["class_n"],
                    "with_id": len(fa_rows)},
        "n04": {"claim": n04["claim"], "status": n04["status"]},
        "failures": failures,
    }

    # ---- ARMS -------------------------------------------------------
    if all(("arsenal", y) in parsed for y in (2024, 2025, 2026)):
        by_year = {}
        for y in (2024, 2025, 2026):
            agg = {}
            for r in parsed[("arsenal", y)]:
                a = agg.setdefault(r["player_id"], {
                    "name": r["name"], "pitches": 0, "run_value": 0.0,
                    "whiff": 0.0, "k": 0.0, "hh": 0.0, "xwoba": 0.0})
                p = r["pitches"]
                a["pitches"] += p
                a["run_value"] += r["run_value"] or 0.0
                for src, dst in (("whiff_percent", "whiff"),
                                 ("k_percent", "k"),
                                 ("hard_hit_percent", "hh"),
                                 ("est_woba", "xwoba")):
                    if r[src] is not None:
                        a[dst] += r[src] * p
            for a in agg.values():
                a["rv100"] = 100.0 * a["run_value"] / a["pitches"]
                for dst in ("whiff", "k", "hh", "xwoba"):
                    a[dst] /= a["pitches"]
            by_year[y] = agg
        qual = lambda a: a["pitches"] >= MIN_TOTAL_PITCHES
        stab = _persistence(by_year, "rv100", qualifier=qual)
        # pitch-type table, 2026 (aggregate run value per 100 pitches)
        pt = {}
        for r in parsed[("arsenal", 2026)]:
            t = pt.setdefault(r["pitch_type"], {
                "pitch_name": r["pitch_name"], "pitchers": set(),
                "pitches": 0, "run_value": 0.0})
            t["pitchers"].add(r["player_id"])
            t["pitches"] += r["pitches"]
            t["run_value"] += r["run_value"] or 0.0
        types = sorted(
            [{"pitch_type": k, "pitch_name": v["pitch_name"],
              "n_pitchers": len(v["pitchers"]), "pitches": v["pitches"],
              "run_value": round(v["run_value"], 1),
              "rv100": round(100.0 * v["run_value"] / v["pitches"], 3)}
             for k, v in pt.items()],
            key=lambda d: -d["rv100"])
        fa26 = [(pid, a) for pid, a in by_year[2026].items()
                if pid in fa_rows and qual(a)]
        fa_top = sorted(
            [{"name": fa_rows[pid]["name"], "pos": fa_rows[pid]["pos"],
              "pitches": a["pitches"], "rv100": round(a["rv100"], 3)}
             for pid, a in fa26], key=lambda d: -d["rv100"])[:5]
        arms = {"status": "ok",
                "board_rows": {str(y): len(parsed[("arsenal", y)])
                               for y in (2024, 2025, 2026)},
                "pitchers_2026": len(by_year[2026]),
                "min_total_pitches": MIN_TOTAL_PITCHES,
                "stability_rv100": stab,
                "pitch_types_2026": types,
                "fa_pool_n": len(fa26),
                "fa_top_rv100_2026": fa_top}

        # Out-of-sample pitch-trait test: traits in year t predict
        # ERA in year t+1. Train 2024->2025, test 2025->2026.
        # Baselines: prior-year ERA, prior-year FIP (constant 3.10).
        try:
            import numpy as _np
            all_ids = set()
            for y in (2024, 2025, 2026):
                all_ids |= set(by_year[y])
            actuals = fetch_pitching_actuals(all_ids)
            _save_json("pitching_actuals_2024_2026.json",
                       [r for y in (2024, 2025, 2026)
                        for r in actuals[y].values()])

            def _design(t):
                X, yv, era_b, fip_b = [], [], [], []
                for pid, a in by_year[t].items():
                    if not qual(a):
                        continue
                    cur, nxt = actuals[t].get(pid), actuals[t + 1].get(pid)
                    if not cur or not nxt:
                        continue
                    if cur["era"] is None or nxt["era"] is None:
                        continue
                    X.append([a["whiff"], a["k"], a["hh"], a["xwoba"]])
                    yv.append(nxt["era"])
                    era_b.append(cur["era"])
                    fip_b.append(cur["fip"])
                return (_np.array(X), _np.array(yv),
                        _np.array(era_b), _np.array(fip_b))

            Xtr, ytr, _, _ = _design(2024)
            Xte, yte, era_te, fip_te = _design(2025)
            mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
            sd[sd == 0] = 1.0
            beta, *_ = _np.linalg.lstsq(
                _np.column_stack([_np.ones(len(Xtr)),
                                  (Xtr - mu) / sd]),
                ytr, rcond=None)
            pred = (_np.column_stack([_np.ones(len(Xte)),
                                      (Xte - mu) / sd]) @ beta)
            mae = lambda a, b: float(_np.mean(_np.abs(a - b)))
            m_model, m_era, m_fip = (mae(pred, yte), mae(era_te, yte),
                                     mae(fip_te, yte))
            arms["trait_model_oos"] = {
                "status": "ok",
                "features": ["usage-weighted whiff%",
                             "usage-weighted K%",
                             "usage-weighted hard-hit%",
                             "usage-weighted expected wOBA"],
                "train": "2024 traits -> 2025 ERA",
                "test": "2025 traits -> 2026 ERA",
                "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
                "mae_trait_model": round(m_model, 4),
                "mae_prior_era": round(m_era, 4),
                "mae_prior_fip": round(m_fip, 4),
                "fip_constant": FIP_CONSTANT,
                "beats_baselines": bool(m_model < m_era
                                        and m_model < m_fip)}
        except Exception as e:
            arms["trait_model_oos"] = {"status": "unavailable",
                                       "reason": f"{type(e).__name__}: {e}"}
            print(f"trait model unavailable: {e}")
        artifact["arms"] = arms
    else:
        artifact["arms"] = {
            "status": "unavailable",
            "reason": "arsenal board fetch failed: " +
                      "; ".join(failures.get(f"arsenal_{y}", "?")
                                for y in (2024, 2025, 2026))}

    # ---- GLOVES -----------------------------------------------------
    if all(("oaa", y) in parsed for y in (2024, 2025, 2026)):
        oaa = {y: {r["player_id"]: r for r in parsed[("oaa", y)]}
               for y in (2024, 2025, 2026)}
        stab = _persistence(oaa, "outs_above_average")
        vals26 = [r["outs_above_average"] for r in parsed[("oaa", 2026)]]
        fa26 = [r for r in parsed[("oaa", 2026)]
                if r["player_id"] in fa_rows]
        top = sorted(fa26, key=lambda r: -r["outs_above_average"])[:5]
        gloves = {"status": "ok",
                  "board_rows": {str(y): len(parsed[("oaa", y)])
                                 for y in (2024, 2025, 2026)},
                  "stability_oaa": stab,
                  "distribution_2026": {
                      "n": len(vals26),
                      "median": _quant(vals26, 0.5),
                      "p25": _quant(vals26, 0.25),
                      "p75": _quant(vals26, 0.75),
                      "min": min(vals26), "max": max(vals26)},
                  "fa_pool_n": len(fa26),
                  "fa_top_oaa_2026": [
                      {"name": fa_rows[r["player_id"]]["name"],
                       "pos": fa_rows[r["player_id"]]["pos"],
                       "outs_above_average": r["outs_above_average"],
                       "fielding_runs_prevented":
                           r["fielding_runs_prevented"]} for r in top]}
        # Catchers, 2026 only (endpoints ignore year selection).
        if ("framing", 2026) in parsed and ("blocking", 2026) in parsed:
            fr = {r["player_id"]: r for r in parsed[("framing", 2026)]}
            bl = {r["player_id"]: r for r in parsed[("blocking", 2026)]}
            rows = []
            for pid, f in fa_rows.items():
                if f["pos"] != "C":
                    continue
                a, b = fr.get(pid), bl.get(pid)
                if a is None and b is None:
                    continue
                rows.append({
                    "name": f["name"],
                    "framing_runs": (a["framing_runs"] if a else None),
                    "blocks_above_average": (b["blocks_above_average"]
                                             if b else None),
                    "catcher_blocking_runs": (b["catcher_blocking_runs"]
                                              if b else None)})
            rows.sort(key=lambda d: -(d["framing_runs"] or -99))
            gloves["catchers_2026"] = {
                "status": "ok",
                "note": ("2026 only: both Savant catcher endpoints "
                         "ignore year selection (verified "
                         "byte-identical pulls for 2024/2025/2026), "
                         "so no persistence is computed."),
                "abs_caveat": ("Contested: framing value may compress "
                               "as automated ball-strike challenges "
                               "expand — treat 2026 framing runs as "
                               "an upper bound, not a forward price."),
                "fa_catchers_n": len(rows), "rows": rows}
        else:
            gloves["catchers_2026"] = {
                "status": "unavailable",
                "reason": "catcher board fetch failed"}
        artifact["gloves"] = gloves
    else:
        artifact["gloves"] = {
            "status": "unavailable",
            "reason": "OAA board fetch failed"}

    # ---- LEGS -------------------------------------------------------
    if all(("sprint", y) in parsed for y in (2024, 2025, 2026)):
        spr = {y: {r["player_id"]: r for r in parsed[("sprint", y)]}
               for y in (2024, 2025, 2026)}
        stab = _persistence(spr, "sprint_speed")
        vals26 = [r["sprint_speed"] for r in parsed[("sprint", 2026)]]
        fa26 = [r for r in parsed[("sprint", 2026)]
                if r["player_id"] in fa_rows]
        fast = sorted(fa26, key=lambda r: -r["sprint_speed"])[:5]
        artifact["legs"] = {
            "status": "ok",
            "board_rows": {str(y): len(parsed[("sprint", y)])
                           for y in (2024, 2025, 2026)},
            "stability_sprint": stab,
            "distribution_2026": {
                "n": len(vals26),
                "median": round(_quant(vals26, 0.5), 2),
                "p25": round(_quant(vals26, 0.25), 2),
                "p75": round(_quant(vals26, 0.75), 2),
                "min": min(vals26), "max": max(vals26)},
            "fa_pool_n": len(fa26),
            "fa_fastest_2026": [
                {"name": fa_rows[r["player_id"]]["name"],
                 "pos": fa_rows[r["player_id"]]["pos"],
                 "sprint_speed": r["sprint_speed"],
                 "competitive_runs": r["competitive_runs"]}
                for r in fast]}
    else:
        artifact["legs"] = {"status": "unavailable",
                            "reason": "sprint board fetch failed"}

    _save_json("beyond_the_bat_2027.json", artifact)
    print("failures:", failures or "none")
    return artifact


if __name__ == "__main__":
    main()
