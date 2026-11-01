#!/usr/bin/env python3
"""HARDBALL data-quality gate (poka-yoke).

Encodes the full verification pass of 2026-10-31 as structural checks
that run offline in seconds. Every check corresponds to a failure that
either happened or was hunted that day:

- the silent Savant year-copy trap (bat-tracking files must differ),
- the retracted team-wins claim (formula_prod must stay annotated),
- the 2020-fold units bug (lagged forecast must keep its exclusion),
- ESPN validation misread (HR must match exactly, player by player),
- AZ/ARI-class identity slips (30 teams everywhere teams are counted),
- scenario builders drifting from their constraints (26 men, budget),
- figure references rotting after merges (glossary + talk track).

Run:  python3 src/verify_data.py          (offline gate; exit 1 on fail)
      python3 src/verify_data.py --live   (adds MLB API standings check)

No writes. No network unless --live.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FAIL = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAIL.append(name)


def load(name):
    return json.loads((DATA / name).read_text())


def main() -> int:
    live = "--live" in sys.argv

    # --- required artifacts exist -------------------------------
    required = ["kpi_2025.json", "kpi_2026.json", "panel_2011_2026.csv",
                "projections_2027.json", "projections_2027_pitchers.json",
                "projections_2027_health.json", "fg_benchmark_2027.json",
                "formula_prod.json", "lagged_forecast.json", "wow_scenarios.json",
                "salaries_2026.json", "fa_shopping_2027.json", "pipeline_2026.json",
                "team_explorer.json", "validation_2025.json", "validation_2026.json",
                "cap_scenario_2027.json", "roster_2027.json"]
    missing = [f for f in required if not (DATA / f).exists()]
    check("required artifacts present", not missing, f"missing: {missing}")

    # --- KPI snapshots: 30 teams, sane ranges -------------------
    for yr in (2025, 2026):
        rows = load(f"kpi_{yr}.json")
        ok = (len(rows) == 30
              and all(40 <= r["wins"] <= 115 for r in rows)
              and all(0.28 <= r["OBP"] <= 0.37 for r in rows)
              and len({r["team"] for r in rows}) == 30)
        check(f"kpi_{yr}: 30 unique teams, sane wins/OBP", ok)

    # --- panel --------------------------------------------------
    with open(DATA / "panel_2011_2026.csv") as fh:
        panel = list(csv.DictReader(fh))
    seasons = {r["season"] for r in panel}
    check("panel: >=500 rows, seasons 2011-2026",
          len(panel) >= 500 and len(seasons) == 16,
          f"rows={len(panel)} seasons={len(seasons)}")

    # --- projections --------------------------------------------
    check("projections: >=190 hitters, >=95 pitchers",
          len(load("projections_2027.json")) >= 190
          and len(load("projections_2027_pitchers.json")) >= 95)

    # --- benchmark integrity ------------------------------------
    b = load("fg_benchmark_2027.json")
    h = b["hitters"]
    check("benchmark: all Marcel hitters ID-matched to Steamer",
          h["matched_n"] == h["marcel_n"] and not h.get("unmatched_marcel_ids"),
          f"matched {h['matched_n']}/{h['marcel_n']}")
    check("benchmark: OBP r in [0.80, 0.95]", 0.80 <= h["obp"]["pearson_r"] <= 0.95)

    # --- honesty annotations stay on ----------------------------
    fp = load("formula_prod.json")
    check("formula_prod annotated DIAGNOSTIC ONLY",
          "DIAGNOSTIC ONLY" in str(fp.get("status", "")))
    lf = load("lagged_forecast.json")
    excl = lf.get("excluded_folds", [])
    excl_years = {e.get("feature_season") if isinstance(e, dict) else e for e in excl}
    check("lagged forecast: 2020 fold excluded, grouped MAE < 11",
          2019 in excl_years and lf["grouped_cv"]["mae_mean"] < 11)

    # --- ESPN validation: HR exact, player by player ------------
    for yr in (2025, 2026):
        v = load(f"validation_{yr}.json")
        bad = [p for p in v["players"] if str(p["mlb_hr"]) != str(p["decoded_hr"])]
        check(f"ESPN {yr}: HR exact for all {v['players_compared']} players", not bad,
              f"{len(bad)} HR mismatches")

    # --- Savant: no silent year copies ---------------------------
    hashes = {}
    for y in (2024, 2025, 2026):
        hashes[y] = hashlib.md5((DATA / f"savant_bat_tracking_{y}.json").read_bytes()).hexdigest()
    check("Savant bat-tracking year files all distinct",
          len(set(hashes.values())) == 3)

    # --- scenarios obey their constraints ------------------------
    wow = load("wow_scenarios.json")
    ok = len(wow["scenarios"]) == 3
    for s in wow["scenarios"]:
        ok = ok and len(s["roster"]) == 26 and s["spend"] <= s["budget"]
        ok = ok and abs(sum(p["war"] for p in s["roster"]) - s["total_war"]) <= 0.2
    check("scenarios: 3 budgets, 26 men each, spend <= budget, WAR sums hold", ok)
    check("scenarios: availability stress present (Cycle 27)",
          "availability_stress" in wow)

    # --- salaries honesty ----------------------------------------
    sal = load("salaries_2026.json")
    check("salaries: metadata consistent, failures labeled",
          sal["metadata"]["rows"] == len(sal["players"])
          and isinstance(sal["metadata"].get("team_failures"), list))

    # --- FA class -------------------------------------------------
    fa = load("fa_shopping_2027.json")
    with_war = sum(1 for r in fa["class"] if r.get("steamer_war") is not None)
    check("FA class: >=240 players, >=220 with Steamer WAR",
          len(fa["class"]) >= 240 and with_war >= 220,
          f"class={len(fa['class'])} war={with_war}")

    # --- pipeline internal consistency ----------------------------
    pl = load("pipeline_2026.json")
    ranks = sorted(o["rank"] for o in pl["orgs"])
    check("pipeline: 30 orgs, unique ranks 1-30", ranks == list(range(1, 31)))

    # --- payroll.py W-L table parses to 30 rows -------------------
    src = (ROOT / "src" / "payroll.py").read_text()
    rows = re.findall(r'"[A-Z]{2,3}": \("[^"]+", "\d+-\d+"', src)
    check("payroll.py: 30 team W-L rows", len(rows) == 30, f"found {len(rows)}")

    # --- committed dashboard is the current build -----------------
    html = (ROOT / "dashboard" / "hardball_demo.html").read_text(errors="ignore")
    check("dashboard HTML: >=19 figures, PRESS PLAY present",
          html.count("plotly-graph-div") >= 19 and "PRESS PLAY" in html)
    check("dashboard HTML: no stale figure references",
          "see Figure 12)" not in html and "all 22 real-data charts" in html)

    # --- talk track references exist in the merged deck -----------
    tt = (ROOT / "docs" / "TALKTRACK.md").read_text()
    refs = {int(n) for n in re.findall(r"Figure (\d+)", tt)}
    check("talk track: all figure references <= 22", refs and max(refs) <= 22,
          f"refs: {sorted(refs)}")


    # --- data platform: curated layer contracts ------------------
    rep_path = DATA / "curated" / "_build_report.json"
    check("platform: curated build report present, no failures",
          rep_path.exists() and not json.loads(rep_path.read_text())["failures"]
          if rep_path.exists() else False)
    if rep_path.exists():
        rep = json.loads(rep_path.read_text())
        import pyarrow.parquet as pq
        bad = []
        for t, meta in rep["tables"].items():
            f = DATA / "curated" / f"{t}.parquet"
            if not f.exists() or pq.read_metadata(f).num_rows != meta["rows"]:
                bad.append(t)
        check("platform: every curated table matches its build report",
              not bad, f"mismatch: {bad}")
        check("platform: >=13 curated tables", len(rep["tables"]) >= 13,
              f"tables={len(rep['tables'])}")

    # --- optional live check ---------------------------------------
    if live:
        import requests
        r = requests.get("https://statsapi.mlb.com/api/v1/standings",
                         params={"leagueId": "103,104", "season": 2026,
                                 "standingsTypes": "regularSeason"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        api = {}
        for rec in r.json()["records"]:
            for tr in rec["teamRecords"]:
                api[tr["team"]["name"]] = tr["wins"]
        snap = {row["team"]: row["wins"] for row in load("kpi_2026.json")}
        # repo abbr -> standings short name (the standings endpoint uses
        # short names; this exact map passed 30/30 on 2026-10-31)
        short = {"NYM": "Mets", "LAD": "Dodgers", "NYY": "Yankees",
                 "PHI": "Phillies", "TOR": "Blue Jays", "ATL": "Braves",
                 "CHC": "Cubs", "HOU": "Astros", "SD": "Padres",
                 "BOS": "Red Sox", "DET": "Tigers", "ARI": "D-backs",
                 "TEX": "Rangers", "SF": "Giants", "LAA": "Angels",
                 "SEA": "Mariners", "BAL": "Orioles", "KC": "Royals",
                 "MIL": "Brewers", "CIN": "Reds", "COL": "Rockies",
                 "MIN": "Twins", "PIT": "Pirates", "CHW": "White Sox",
                 "WSH": "Nationals", "ATH": "Athletics", "STL": "Cardinals",
                 "TB": "Rays", "MIA": "Marlins", "CLE": "Guardians"}
        bad = []
        for abbr, w in snap.items():
            key = short.get(abbr, "")
            if api.get(key) != w:
                bad.append((abbr, key, w, api.get(key)))
        check("LIVE: kpi_2026 wins match MLB API standings (30/30)", not bad,
              f"mismatch: {bad}")

    print()
    if FAIL:
        print(f"GATE: FAIL ({len(FAIL)} check(s)): {', '.join(FAIL)}")
        return 1
    print("GATE: ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
