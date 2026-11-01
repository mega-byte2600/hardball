"""BML Cycle 23: MiLB pipeline layer — the missing half of winning-cheap.

The roster tool prices today's MLB players, but MIL/TB/CLE's real edge is
the pre-arb pipeline behind them. This cycle builds a per-MLB-org pipeline
index for 2026 from the keyless MLB Stats API minor-league endpoints
(AAA sportId=11, AA sportId=12), upper minors only.

Method (deliberately simple and transparent — every knob is a constant
below and is echoed into the output metadata):
- A player-org "split" is one player's season line for one affiliate.
- A hitting split qualifies at >= 150 PA at that level; a pitching split
  at >= 40 IP at that level (IP parsed from baseball notation, outs/3).
- Only under-26 players count: age on 2026-06-30 (the standard baseball
  age convention) from the REAL birthDate on the MLB people endpoint.
  A qualifying player whose birthDate cannot be fetched is EXCLUDED
  (fail closed) and counted in the metadata, never guessed.
- Level weights: AAA 1.00, AA 0.85 (proximity to MLB).
- Org weighted OPS = sum(PA * level_w * OPS) / sum(PA * level_w) over
  qualified under-26 splits. Org weighted ERA = 9 * sum(level_w * ER) /
  sum(level_w * IP) — exactly the IP-weighted ERA — over qualified splits.
- League baselines are the same quantities over the whole qualified
  under-26 pool.
- Pipeline index = hit_score + pit_score, where
    hit_score = n_qualified_hitters * (org_wtd_OPS / league_wtd_OPS)
    pit_score = n_qualified_pitchers * (league_wtd_ERA / org_wtd_ERA)
  i.e. "league-average-equivalent qualified prospects", volume x quality.
  index_avg100 rescales so the average org = 100. Ranking is by index.

Outputs: data/pipeline_2026.json (metadata + 30 orgs, ranked).
Raw API payloads are NOT archived by this cycle (kept in memory only).

Limitations (also in the JSON metadata): upper minors only — no A-ball,
rookie ball, scouting grades, or prospect rankings; a player who spent
most of 2026 in MLB is invisible here no matter how young; ERA is not
park- or league-adjusted (PCL vs IL environments differ); a player traded
mid-season counts once per org he qualified for (player-org units);
2026 performance is descriptive, not a projection.
"""
import json
import os
import time
from datetime import date

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0 carpe-data"}
SEASON = 2026
AGE_DATE = date(2026, 6, 30)          # baseball-age convention
UNDER26_CUTOFF = date(2000, 7, 1)     # born on/after => age < 26 on AGE_DATE
MIN_PA = 150                          # per-level hitting qualification
MIN_IP = 40.0                         # per-level pitching qualification
LEVELS = {11: {"name": "AAA", "weight": 1.00},
          12: {"name": "AA", "weight": 0.85}}


def _get(path, params, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(f"{BASE}{path}", params=params, headers=UA, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # retry transient API failures, then fail loud
            last = e
            time.sleep(2 * (i + 1))
    raise last


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _ip_outs(v):
    """Baseball IP notation '131.1' = 131 innings + 1 out -> total outs."""
    if v is None:
        return None
    whole, _, frac = str(v).partition(".")
    try:
        return int(whole) * 3 + int(frac or 0)
    except ValueError:
        return None


def load_orgs_and_affiliates():
    """30 MLB orgs (sportId=1) + their AAA/AA affiliates (parentOrgId)."""
    mlb = _get("/teams", {"sportId": 1, "season": SEASON}).get("teams", [])
    orgs = {t["id"]: {"org_id": t["id"], "org_name": t.get("name"),
                      "org_abbr": t.get("abbreviation") or t.get("fileCode"),
                      "affiliates": []} for t in mlb}
    for sport_id, lvl in LEVELS.items():
        teams = _get("/teams", {"sportId": sport_id, "season": SEASON}).get("teams", [])
        for t in teams:
            org = orgs.get(t.get("parentOrgId"))
            entry = {"team_id": t["id"], "team_name": t.get("name"),
                     "level": lvl["name"], "sport_id": sport_id}
            if org is None:
                entry["parent_missing"] = True
                orgs.setdefault(t.get("parentOrgId"),
                                {"org_id": t.get("parentOrgId"),
                                 "org_name": t.get("parentOrgName"),
                                 "org_abbr": None, "affiliates": []})
                org = orgs[t.get("parentOrgId")]
            org["affiliates"].append(entry)
    return orgs


def load_team_splits(team_id, sport_id, group, sort_stat):
    """Per-team season splits. NOTE: without playerPool=all + sortStat the
    /stats endpoint returns a small leaders view, not the full roster —
    probed 2026-10-31 (Toledo: 5 hitters by default, 36 with these params)."""
    data = _get("/stats", {"stats": "season", "group": group, "season": SEASON,
                           "sportId": sport_id, "teamId": team_id,
                           "playerPool": "all", "sortStat": sort_stat,
                           "order": "desc", "limit": 500})
    stats = data.get("stats") or []
    return stats[0].get("splits", []) if stats else []


def load_birthdates(player_ids):
    """Real birthDates from the people endpoint, batched 50 ids per call
    (same pattern as src/carpe.py player_xwalk_and_ages)."""
    out = {}
    ids = sorted(player_ids)
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        data = _get("/people", {"personIds": ",".join(str(x) for x in chunk)})
        for p in data.get("people", []):
            bd = p.get("birthDate")
            parsed = None
            if bd:
                try:
                    y, m, d = (int(x) for x in bd.split("-"))
                    parsed = date(y, m, d)
                except (ValueError, AttributeError):
                    parsed = None
            out[p["id"]] = parsed
    return out


def main():
    orgs = load_orgs_and_affiliates()
    team_to_org = {}
    for org in orgs.values():
        for a in org["affiliates"]:
            team_to_org[a["team_id"]] = (org["org_id"], a)
    print(f"orgs: {len(orgs)}  affiliates: {len(team_to_org)} "
          f"({sum(1 for a in team_to_org.values() if a[1]['level'] == 'AAA')} AAA, "
          f"{sum(1 for a in team_to_org.values() if a[1]['level'] == 'AA')} AA)")

    # --- Pull every affiliate's hitting + pitching splits, keep qualifying ---
    # candidates[org_id][group][player_id] = {name, splits: [...]}
    candidates = {oid: {"hitting": {}, "pitching": {}} for oid in orgs}
    n_splits = {"hitting": 0, "pitching": 0}
    for team_id, (oid, aff) in sorted(team_to_org.items()):
        w = LEVELS[aff["sport_id"]]["weight"]
        for split in load_team_splits(team_id, aff["sport_id"], "hitting", "plateAppearances"):
            n_splits["hitting"] += 1
            st, p = split.get("stat", {}), split.get("player", {})
            pa, ops = st.get("plateAppearances"), _num(st.get("ops"))
            if p.get("id") is None or pa is None or pa < MIN_PA or ops is None:
                continue
            rec = candidates[oid]["hitting"].setdefault(
                p["id"], {"player_id": p["id"], "name": p.get("fullName"), "splits": []})
            rec["splits"].append({"level": aff["level"], "weight": w, "team": aff["team_name"],
                                  "pa": int(pa), "ops": ops})
        for split in load_team_splits(team_id, aff["sport_id"], "pitching", "inningsPitched"):
            n_splits["pitching"] += 1
            st, p = split.get("stat", {}), split.get("player", {})
            outs, er = _ip_outs(st.get("inningsPitched")), st.get("earnedRuns")
            if p.get("id") is None or outs is None or outs / 3.0 < MIN_IP or er is None:
                continue
            rec = candidates[oid]["pitching"].setdefault(
                p["id"], {"player_id": p["id"], "name": p.get("fullName"), "splits": []})
            rec["splits"].append({"level": aff["level"], "weight": w, "team": aff["team_name"],
                                  "outs": int(outs), "er": int(er)})

    cand_ids = {pid for oid in candidates
                for g in ("hitting", "pitching") for pid in candidates[oid][g]}
    print(f"splits pulled: {n_splits}  qualifying-split players (pre-age): {len(cand_ids)}")

    # --- Real ages; fail closed on missing birthDate ---
    birth = load_birthdates(cand_ids)
    missing_age = sorted(pid for pid in cand_ids if birth.get(pid) is None)
    young = {pid for pid in cand_ids
             if birth.get(pid) is not None and birth[pid] >= UNDER26_CUTOFF}
    print(f"birthDates fetched: {len(birth) - len(missing_age)}/{len(cand_ids)}  "
          f"missing (excluded): {len(missing_age)}  under-26: {len(young)}")

    def age_years(pid):
        b = birth[pid]
        return round((AGE_DATE - b).days / 365.25, 1)

    # --- Aggregate per org over qualified under-26 player-org units ---
    rows = []
    lg = {"pa_w": 0.0, "ops_w": 0.0, "ip_w": 0.0, "er_w": 0.0}
    for oid, org in orgs.items():
        hitters, pitchers = [], []
        for pid, rec in candidates[oid]["hitting"].items():
            if pid not in young:
                continue
            pa_w = sum(s["pa"] * s["weight"] for s in rec["splits"])
            wtd_ops = sum(s["pa"] * s["weight"] * s["ops"] for s in rec["splits"]) / pa_w
            hitters.append({"player_id": pid, "name": rec["name"], "age": age_years(pid),
                            "levels": sorted({s["level"] for s in rec["splits"]}),
                            "pa": sum(s["pa"] for s in rec["splits"]),
                            "wtd_ops": round(wtd_ops, 3)})
            lg["pa_w"] += pa_w
            lg["ops_w"] += pa_w * wtd_ops
        for pid, rec in candidates[oid]["pitching"].items():
            if pid not in young:
                continue
            outs_w = sum(s["outs"] * s["weight"] for s in rec["splits"])
            er_w = sum(s["er"] * s["weight"] for s in rec["splits"])
            ip = sum(s["outs"] for s in rec["splits"]) / 3.0
            pitchers.append({"player_id": pid, "name": rec["name"], "age": age_years(pid),
                             "levels": sorted({s["level"] for s in rec["splits"]}),
                             "ip": round(ip, 1),
                             "wtd_era": round(27.0 * er_w / outs_w, 2)})
            lg["ip_w"] += outs_w / 3.0
            lg["er_w"] += er_w
        hit_pa_w = sum(sum(s["pa"] * s["weight"] for s in candidates[oid]["hitting"][h["player_id"]]["splits"])
                       for h in hitters)
        hit_ops = (sum(h["wtd_ops"] * sum(s["pa"] * s["weight"] for s in candidates[oid]["hitting"][h["player_id"]]["splits"])
                       for h in hitters) / hit_pa_w) if hit_pa_w else None
        pit_outs_w = sum(sum(s["outs"] * s["weight"] for s in candidates[oid]["pitching"][p["player_id"]]["splits"])
                         for p in pitchers)
        pit_er_w = sum(sum(s["er"] * s["weight"] for s in candidates[oid]["pitching"][p["player_id"]]["splits"])
                       for p in pitchers)
        pit_era = (27.0 * pit_er_w / pit_outs_w) if pit_outs_w else None
        rows.append({
            "org_id": oid, "org_name": org["org_name"], "org_abbr": org["org_abbr"],
            "affiliates": org["affiliates"],
            "n_hitters": len(hitters), "n_pitchers": len(pitchers),
            "hit_pa": sum(h["pa"] for h in hitters),
            "pit_ip": round(sum(p["ip"] for p in pitchers), 1),
            "wtd_ops": round(hit_ops, 3) if hit_ops is not None else None,
            "wtd_era": round(pit_era, 2) if pit_era is not None else None,
            "top_hitter": max(hitters, key=lambda h: h["wtd_ops"]) if hitters else None,
            "top_pitcher": min(pitchers, key=lambda p: p["wtd_era"]) if pitchers else None,
            "_hit_pa_w": hit_pa_w, "_pit_outs_w": pit_outs_w,
        })

    league_ops = lg["ops_w"] / lg["pa_w"]
    league_era = 9.0 * lg["er_w"] / lg["ip_w"]
    print(f"league qualified under-26 baselines: OPS {league_ops:.3f}  ERA {league_era:.2f}")

    for r in rows:
        r["hit_score"] = round(r["n_hitters"] * (r["wtd_ops"] / league_ops), 2) if r["wtd_ops"] else 0.0
        r["pit_score"] = round(r["n_pitchers"] * (league_era / r["wtd_era"]), 2) if r["wtd_era"] else 0.0
        r["pipeline_index"] = round(r["hit_score"] + r["pit_score"], 2)
    mean_index = sum(r["pipeline_index"] for r in rows) / len(rows)
    rows.sort(key=lambda r: r["pipeline_index"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["index_avg100"] = round(100.0 * r["pipeline_index"] / mean_index, 1)
        del r["_hit_pa_w"], r["_pit_outs_w"]
    for group in ("hit_score", "pit_score"):
        for i, r in enumerate(sorted(rows, key=lambda x: x[group], reverse=True), 1):
            r[group.replace("score", "rank")] = i

    out = {
        "metadata": {
            "cycle": "BML Cycle 23 — MiLB pipeline index (CarpeData)",
            "season": SEASON,
            "generated": str(date.today()),
            "source": "MLB Stats API (keyless) https://statsapi.mlb.com/api/v1",
            "endpoints": {
                "teams": "/teams?sportId=1 (orgs), 11 (AAA), 12 (AA) — parentOrgId maps affiliate -> org",
                "player_stats": "/stats?stats=season&group=hitting|pitching&teamId=<affiliate>&sportId=11|12&playerPool=all",
                "ages": "/people?personIds=<batched 50> — real birthDate per player",
            },
            "method": {
                "age_rule": f"under-26 = age < 26 on {AGE_DATE.isoformat()} (born on/after {UNDER26_CUTOFF.isoformat()}), from people-endpoint birthDate",
                "qualification": f"per-level split: hitters >= {MIN_PA} PA, pitchers >= {MIN_IP} IP at AAA or AA",
                "level_weights": {v["name"]: v["weight"] for v in LEVELS.values()},
                "wtd_ops": "sum(PA*w*OPS)/sum(PA*w) over qualified under-26 splits",
                "wtd_era": "9*sum(w*ER)/sum(w*IP) over qualified under-26 splits (IP-weighted ERA; IP from outs/3)",
                "index": "hit_score + pit_score; hit_score = n_hitters*(org OPS/league OPS), pit_score = n_pitchers*(league ERA/org ERA); index_avg100 rescales mean org to 100",
                "league_baselines": {"wtd_ops": round(league_ops, 3), "wtd_era": round(league_era, 2),
                                     "n_hitters": sum(r["n_hitters"] for r in rows),
                                     "n_pitchers": sum(r["n_pitchers"] for r in rows)},
            },
            "coverage": {
                "orgs": len(rows),
                "splits_pulled": n_splits,
                "players_qualifying_pre_age": len(cand_ids),
                "players_excluded_missing_birthdate": len(missing_age),
                "missing_birthdate_player_ids": missing_age,
            },
            "limitations": [
                "Upper minors only (AAA/AA): no A-ball, rookie ball, scouting grades, draft pedigree, or prospect rankings — this measures near-MLB depth, not total farm quality.",
                "Players who spent most of 2026 in MLB are invisible or undercounted here regardless of age/talent.",
                "ERA is not park- or league-adjusted; AAA Pacific Coast League parks inflate ERA vs International League.",
                "A player traded mid-season counts once per org he qualified for (player-org units), so league n is player-orgs, not unique players.",
                "2026 stat lines are descriptive performance, not projections; small-sample qualifiers sit exactly at the 150 PA / 40 IP floors.",
                "Players with no birthDate from the people endpoint were excluded (fail closed), never age-guessed; count is in coverage.",
            ],
        },
        "orgs": rows,
    }
    path = os.path.join(DATA, "pipeline_2026.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {path} ({len(rows)} orgs)")
    print("\n=== Pipeline index 2026 — top 10 ===")
    for r in rows[:10]:
        th, tp = r["top_hitter"] or {}, r["top_pitcher"] or {}
        print(f"{r['rank']:>2}. {r['org_abbr'] or r['org_name']:<4} idx {r['pipeline_index']:>6.2f} "
              f"(avg100 {r['index_avg100']:>6.1f})  H {r['n_hitters']} OPS {r['wtd_ops']}  "
              f"P {r['n_pitchers']} ERA {r['wtd_era']}  | top bat {th.get('name')} {th.get('wtd_ops')} / "
              f"top arm {tp.get('name')} {tp.get('wtd_era')}")
    print("\n=== bottom 5 ===")
    for r in rows[-5:]:
        print(f"{r['rank']:>2}. {r['org_abbr'] or r['org_name']:<4} idx {r['pipeline_index']:>6.2f}  "
              f"H {r['n_hitters']} OPS {r['wtd_ops']}  P {r['n_pitchers']} ERA {r['wtd_era']}")


if __name__ == "__main__":
    main()
