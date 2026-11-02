#!/usr/bin/env python3
"""BML Cycle 54 — UNC-1: availability-cap out-of-sample backtest.

Programme increment 5 of 6 (owner-approved 2026-11-02). Question: does
capping a player's projected playing time by measured availability —
the demo's own mechanism (Cycle 9: proj_PA_health = proj_PA x avail_pct,
avail from prior-2-season IL days over a 182-day season, clipped to
[0.3, 1.0]) — actually improve out-of-sample PA forecasts for free-agent
classes? Tested on the three FA classes entering 2022, 2023, 2024.

Design (declared before running; verdict rule below):
- FA class T = players with a "Signed as Free Agent" transaction from
  the MLB Stats API in Nov (T-1) through Apr (T), deduplicated by
  MLBAM id (earliest signing kept). Source is the same keyless API the
  lake loader uses; the committed transactions stream starts Dec 2024,
  so these historical classes are pulled fresh here, in monthly
  partitions, sequential, with a short pause. Any non-200 aborts the
  run (fail closed, no artifact written).
- Evaluation set = class members with a QUALIFIED hitting line in
  season T (same pool the lake loader uses: playerPool=qualified,
  sortStat=homeRuns, limit 300). Actuals: lake stat_lines for
  2023/2024, fresh pulls for 2022; priors: lake where present, fresh
  pulls for 2020-2022. Hitters only — the demo's PA cap is a hitter
  mechanism; FA pitchers never enter the hitting pool and are counted
  as excluded, not silently dropped.
- Availability: IL days from the committed fact_il_stints table
  (The Injury Report stints, 2019-2026), summed per player-season and
  CAPPED at 182 days per season (263 player-seasons in the file sum
  above 182 from overlapping stint rows; uncapped sums would overstate
  time lost), over seasons T-2 and T-1. avail = clip(1 - days/(2*182),
  0.3, 1.0) — Cycle 9's formula exactly.
- Forecasts: flat500 (the demo's flat proj_PA for 2027), flat500 x
  avail, marcelPA (5:4-weighted prior-season PA; T-1 only where T-2
  is missing, flagged; 2020 NEVER a prior — 60-game season, PA not
  on a full-season scale, no scaling invented), marcelPA x avail. Metric: MAE on PA, per class
  and pooled, plus bias (mean forecast minus actual) and the share of
  players whose capped forecast is closer to actual than the uncapped.
- VERDICT RULE (fixed before seeing results): the cap is SUPPORTED
  only if capped MAE < uncapped MAE on BOTH baselines pooled; MIXED
  if it wins on one baseline only; NOT SUPPORTED otherwise. This is
  a WORKPAPER verdict: it changes no demo number, no figure, and no
  2027 cap — UNC-2 (uncertainty layer) is where any adoption is
  decided, and the owner keeps that call.
- Known frame limit, stated in the artifact: the qualified pool
  excludes players who fell below qualification in season T — exactly
  the players a bad injury removes from frame. That biases AGAINST
  the cap, so a cap win here is conservative; a cap loss here is not
  proof the cap is useless for unqualified players.

Output: data/unc1_availability_backtest.json (method, per-class and
pooled metrics, per-player rows, exclusion counts). No network beyond
the MLB Stats API pulls above. No lake writes (the protected lake is
read-only here; fresh seasons live only in this run's memory).
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LAKE = DATA / "mlb_lake.db"
BASE = "https://statsapi.mlb.com/api/v1"
UA_STATS = {"User-Agent": "nutweet-data-lake/1.0"}
UA_TXN = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
TARGETS = (2022, 2023, 2024)
SEASON_DAYS = 182


def months_for_class(t):
    """Nov (t-1) .. Apr (t) as (year, month) pairs."""
    return [(t - 1, 11), (t - 1, 12)] + [(t, m) for m in (1, 2, 3, 4)]


def month_bounds(y, m):
    import calendar
    return (f"{y}-{m:02d}-01", f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}")


def fetch_fa_class(t):
    """Return {player_id: {'name':, 'signed_date':}} for offseason t."""
    out = {}
    for y, m in months_for_class(t):
        a, b = month_bounds(y, m)
        r = requests.get(f"{BASE}/transactions",
                         params={"startDate": a, "endDate": b},
                         headers=UA_TXN, timeout=60)
        if r.status_code != 200:
            raise SystemExit(f"FAIL: transactions {a}..{b} -> HTTP {r.status_code}; aborting, no artifact")
        for tx in r.json().get("transactions", []):
            if tx.get("typeDesc") != "Signed as Free Agent":
                continue
            p = tx.get("person") or {}
            pid = p.get("id")
            if not pid:
                continue
            d = tx.get("date", "")
            if pid not in out or d < out[pid]["signed_date"]:
                out[pid] = {"name": p.get("fullName"), "signed_date": d}
        time.sleep(0.2)
    return out


def fetch_qualified_hitting(season):
    """Fresh qualified hitting pull, identical params to src/ingest.py."""
    r = requests.get(f"{BASE}/stats",
                     params={"stats": "season", "group": "hitting",
                             "season": season, "sportId": 1,
                             "playerPool": "qualified", "sortStat": "homeRuns",
                             "order": "desc", "limit": 300},
                     headers=UA_STATS, timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"FAIL: qualified hitting {season} -> HTTP {r.status_code}; aborting, no artifact")
    out = {}
    for split in r.json().get("stats", [{}])[0].get("splits", []):
        p = split.get("player", {})
        stat = split.get("stat", {})
        if p.get("id") is not None and stat.get("plateAppearances") is not None:
            out[p["id"]] = {"name": p.get("fullName"),
                            "pa": int(stat["plateAppearances"])}
    time.sleep(0.2)
    return out


def lake_hitting(season):
    con = sqlite3.connect(f"file:{LAKE}?mode=ro", uri=True)
    out = {}
    for pid, name, sjson in con.execute(
            "SELECT player_id, name, stat_json FROM stat_lines "
            "WHERE season=? AND group_name='hitting'", (season,)):
        s = json.loads(sjson)
        if s.get("plateAppearances") is not None:
            out[pid] = {"name": name, "pa": int(s["plateAppearances"])}
    con.close()
    return out


def main() -> None:
    # Actuals + priors: lake for 2023/2024, fresh pulls for 2020-2022.
    hitting = {}
    for s in (2023, 2024):
        hitting[s] = lake_hitting(s)
        print(f"lake hitting {s}: {len(hitting[s])} qualified players")
    for s in (2020, 2021, 2022):
        hitting[s] = fetch_qualified_hitting(s)
        print(f"fresh hitting {s}: {len(hitting[s])} qualified players")

    # Availability: per-season IL days capped at 182, from committed stints.
    import pandas as pd
    stints = pd.read_parquet(DATA / "curated" / "fact_il_stints.parquet")
    stints["days_capped"] = stints["days_in_season"].clip(upper=SEASON_DAYS)
    il_days = (stints.groupby(["player_id", "season"])["days_capped"]
               .sum().to_dict())

    def avail(pid, t):
        days = sum(il_days.get((pid, s), 0) for s in (t - 2, t - 1))
        return round(max(0.3, min(1.0, 1.0 - days / (2 * SEASON_DAYS))), 4), int(days)

    classes = {}
    pooled_rows = []
    for t in TARGETS:
        fa = fetch_fa_class(t)
        actual = hitting[t]
        rows = []
        n_no_line = 0
        n_no_prior = 0
        for pid, info in fa.items():
            if pid not in actual:
                n_no_line += 1
                continue
            pa_prev1 = hitting[t - 1].get(pid, {}).get("pa")
            # 2020 was a 60-game season: its PA is not on a full-season
            # scale, so it is NEVER a PA prior. For class 2022 that
            # leaves 2021 only (labeled); no scaling is invented.
            pa_prev2 = hitting[t - 2].get(pid, {}).get("pa") if t - 2 != 2020 else None
            if pa_prev1 is None and pa_prev2 is None:
                n_no_prior += 1
                continue
            if pa_prev1 is not None and pa_prev2 is not None:
                marcel = (5 * pa_prev1 + 4 * pa_prev2) / 9.0
                marcel_basis = "5:4"
            elif t - 2 == 2020:
                marcel = float(pa_prev1)
                marcel_basis = "T-1 only (2020 excluded, 60-game season)"
            else:
                marcel = float(pa_prev1 if pa_prev1 is not None else pa_prev2)
                marcel_basis = "T-1 only"
            av, days = avail(pid, t)
            act = actual[pid]["pa"]
            rows.append({
                "player_id": pid, "name": actual[pid]["name"],
                "signed_date": info["signed_date"], "target_season": t,
                "actual_pa": act, "il_days_prior2": days, "avail_pct": av,
                "flat500": 500, "flat500_capped": round(500 * av, 1),
                "marcel_pa": round(marcel, 1),
                "marcel_pa_capped": round(marcel * av, 1),
                "marcel_basis": marcel_basis,
            })
        classes[str(t)] = {"n_signed": len(fa), "n_evaluated": len(rows),
                           "n_no_target_line": n_no_line,
                           "n_no_prior": n_no_prior, "rows": rows}
        pooled_rows.extend(rows)
        print(f"class {t}: signed={len(fa)} evaluated={len(rows)} "
              f"no_line={n_no_line} no_prior={n_no_prior}")

    def metrics(rows):
        if not rows:
            return {}
        n = len(rows)
        out = {"n": n, "mean_actual_pa": round(sum(r["actual_pa"] for r in rows) / n, 1),
               "mean_avail": round(sum(r["avail_pct"] for r in rows) / n, 4),
               "share_avail_below_1": round(sum(1 for r in rows if r["avail_pct"] < 1.0) / n, 3)}
        for key in ("flat500", "flat500_capped", "marcel_pa", "marcel_pa_capped"):
            errs = [abs(r[key] - r["actual_pa"]) for r in rows]
            bias = [r[key] - r["actual_pa"] for r in rows]
            out[f"mae_{key}"] = round(sum(errs) / n, 1)
            out[f"bias_{key}"] = round(sum(bias) / n, 1)
        out["win_rate_flat_capped"] = round(
            sum(1 for r in rows if abs(r["flat500_capped"] - r["actual_pa"]) < abs(r["flat500"] - r["actual_pa"])) / n, 3)
        out["win_rate_marcel_capped"] = round(
            sum(1 for r in rows if abs(r["marcel_pa_capped"] - r["actual_pa"]) < abs(r["marcel_pa"] - r["actual_pa"])) / n, 3)
        # Diagnostic (not part of the verdict rule): the cap is a
        # one-directional penalty, so it can only help forecasts that
        # overshoot. Report its hit rate on the overshoot subset alone.
        for key, capped in (("flat500", "flat500_capped"), ("marcel_pa", "marcel_pa_capped")):
            over = [r for r in rows if r[key] > r["actual_pa"]]
            if over:
                out[f"overshoot_n_{key}"] = len(over)
                out[f"overshoot_win_rate_{capped}"] = round(
                    sum(1 for r in over if abs(r[capped] - r["actual_pa"]) < abs(r[key] - r["actual_pa"])) / len(over), 3)
        return out

    per_class = {t: metrics(c["rows"]) for t, c in classes.items()}
    pooled = metrics(pooled_rows)
    flat_win = pooled["mae_flat500_capped"] < pooled["mae_flat500"]
    marcel_win = pooled["mae_marcel_pa_capped"] < pooled["mae_marcel_pa"]
    verdict = ("SUPPORTED" if (flat_win and marcel_win)
               else "MIXED" if (flat_win or marcel_win) else "NOT SUPPORTED")
    artifact = {
        "cycle": "UNC-1 (Cycle 54)",
        "method": {
            "fa_class": "Signed as Free Agent transactions, Nov (T-1) to Apr (T), MLB Stats API, deduplicated by MLBAM id",
            "pool": "Qualified hitting (playerPool=qualified, sortStat=homeRuns, limit 300), same as src/ingest.py load_qualified",
            "actuals": "Lake stat_lines for 2023/2024; fresh MLB API pulls for 2022 actuals and 2020-2022 priors (lake is read-only here)",
            "availability": "fact_il_stints days_in_season summed per player-season, capped at 182/season, over T-2 and T-1; avail = clip(1 - days/(2*182), 0.3, 1.0) = Cycle 9 formula",
            "forecasts": ["flat500", "flat500_capped", "marcel_pa (5:4, T-1 only where T-2 missing)", "marcel_pa_capped"],
            "verdict_rule": "SUPPORTED only if capped MAE < uncapped MAE on BOTH baselines pooled; MIXED if one; else NOT SUPPORTED",
            "frame_limit": "Qualified pool only: players who fell below qualification in season T are out of frame, which biases AGAINST the cap",
            "scope": "Workpaper only: no demo number, figure, or 2027 cap changes. Adoption, if any, is UNC-2 / owner call.",
        },
        "verdict": verdict,
        "per_class": per_class,
        "pooled": pooled,
        "classes": {t: {k: v for k, v in c.items() if k != "rows"} for t, c in classes.items()},
        "rows": pooled_rows,
    }
    out_path = DATA / "unc1_availability_backtest.json"
    out_path.write_text(json.dumps(artifact, indent=2))
    print(f"\nPOOLED n={pooled['n']} verdict={verdict}")
    print(json.dumps(pooled, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
