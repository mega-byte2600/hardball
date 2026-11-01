#!/usr/bin/env python3
"""HARDBALL curation — raw + committed artifacts -> typed Parquet.

Kimball discipline: every table declares its grain; joins happen on
MLBAM ids only; schema contracts are enforced and the build FAILS
CLOSED on violation. Output: data/curated/*.parquet +
data/curated/_build_report.json (rows, inputs, checks per table —
the lineage record).

Sources of truth per table (documented in the report):
  dim_player          data/player_xwalk.json + player_ages.json
  dim_team            src/payroll.py W-L table (30 clubs)
  fact_team_season    data/panel_2011_2026.csv (grain team x season)
  fact_stat_lines     data/mlb_lake.db if present (grain player x season)
  fact_proj_hitters   data/projections_2027.json
  fact_proj_pitchers  data/projections_2027_pitchers.json
  fact_savant_expected data/savant_expected_{2023..2026}.json
  fact_steamer_bat    data/fg_steamer_2027_bat.json
  fact_steamer_pit    data/fg_steamer_2027_pit.json
  fact_salaries       data/salaries_2026.json (grain player x team)
  fact_fa_class       data/fa_shopping_2027.json
  fact_pipeline       data/pipeline_2026.json (grain organization)
  fact_health         data/health_2025_2026.json (grain team x season)
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "curated"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = {"tables": {}, "failures": []}


def emit(name, df, grain, inputs, checks):
    for cname, ok in checks:
        if not ok:
            REPORT["failures"].append(f"{name}: {cname}")
            print(f"  FAIL {name}: {cname}")
            return
    df.to_parquet(OUT / f"{name}.parquet", index=False)
    REPORT["tables"][name] = {"rows": len(df), "grain": grain,
                              "inputs": inputs, "checks": [c for c, _ in checks]}
    print(f"  {name}: {len(df)} rows (grain: {grain})")


def load(name):
    return json.loads((DATA / name).read_text())


def main():
    # dim_player ------------------------------------------------------------
    xw = load("player_xwalk.json")
    ages = {r["mlbam_id"]: r for r in load("player_ages.json")} \
        if (DATA / "player_ages.json").exists() else {}
    rows = []
    for v in xw:
        pid = int(v["mlbam_id"])
        a = ages.get(pid) or {}
        rows.append({"player_id": pid, "fg_id": v.get("fg_id"),
                     "name": v.get("name"),
                     "birth_date": a.get("birth_date"),
                     "current_age": a.get("current_age")})
    df = pd.DataFrame(rows)
    emit("dim_player", df, "one row per player (MLBAM id)",
         ["player_xwalk.json", "player_ages.json"],
         [("player_id unique", df.player_id.is_unique),
          ("player_id not null", df.player_id.notna().all())])

    # dim_team ---------------------------------------------------------------
    src = (ROOT / "src" / "payroll.py").read_text()
    rows = [{"team": a, "name": n, "wins": int(w), "losses": int(l)}
            for a, n, w, l in re.findall(r'"([A-Z]{2,3})": \("([^"]+)", "(\d+)-(\d+)"', src)]
    df = pd.DataFrame(rows)
    emit("dim_team", df, "one row per club", ["src/payroll.py"],
         [("30 teams", len(df) == 30), ("team unique", df.team.is_unique)])

    # fact_team_season ---------------------------------------------------------
    df = pd.read_csv(DATA / "panel_2011_2026.csv")
    emit("fact_team_season", df, "team x season", ["panel_2011_2026.csv"],
         [("rows >= 500", len(df) >= 500),
          ("seasons 2011-2026", df.season.nunique() == 16)])

    # fact_stat_lines (lake, when present) --------------------------------------
    lake = DATA / "mlb_lake.db"
    if lake.exists():
        con = sqlite3.connect(lake)
        df = pd.read_sql("SELECT * FROM stat_lines", con)
        con.close()
        emit("fact_stat_lines", df, "player x season", ["mlb_lake.db:stat_lines"],
             [("rows > 500", len(df) > 500),
              ("player_id present", "player_id" in df.columns)])
    else:
        print("  fact_stat_lines: SKIPPED (lake absent in this environment)")

    # projections ---------------------------------------------------------------
    df = pd.DataFrame(load("projections_2027.json"))
    emit("fact_proj_hitters", df, "player x 2027", ["projections_2027.json"],
         [("rows >= 190", len(df) >= 190)])
    df = pd.DataFrame(load("projections_2027_pitchers.json"))
    emit("fact_proj_pitchers", df, "player x 2027", ["projections_2027_pitchers.json"],
         [("rows >= 95", len(df) >= 95)])

    # savant expected, stacked ---------------------------------------------------
    frames = []
    for y in (2023, 2024, 2025, 2026):
        d = load(f"savant_expected_{y}.json")
        f = pd.DataFrame(d if isinstance(d, list) else d.get("rows", []))
        f["season"] = y
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    emit("fact_savant_expected", df, "player x season",
         [f"savant_expected_{y}.json" for y in (2023, 2024, 2025, 2026)],
         [("4 seasons", df.season.nunique() == 4), ("rows > 2000", len(df) > 2000)])

    # steamer ----------------------------------------------------------------------
    for nm, srcf in (("fact_steamer_bat", "fg_steamer_2027_bat.json"),
                     ("fact_steamer_pit", "fg_steamer_2027_pit.json")):
        d = load(srcf)
        df = pd.DataFrame(d if isinstance(d, list) else d.get("rows", []))
        emit(nm, df, "player (2027 projection)", [srcf],
             [("rows > 1000", len(df) > 1000),
              ("xMLBAMID present", "xMLBAMID" in df.columns)])

    # salaries -----------------------------------------------------------------------
    sal = load("salaries_2026.json")
    df = pd.DataFrame(sal["players"])
    emit("fact_salaries", df, "player x team (2026)", ["salaries_2026.json"],
         [("rows == metadata", len(df) == sal["metadata"]["rows"])])

    # fa class -------------------------------------------------------------------------
    fa = load("fa_shopping_2027.json")
    df = pd.DataFrame(fa["class"])
    emit("fact_fa_class", df, "player (2027 class)", ["fa_shopping_2027.json"],
         [("rows >= 240", len(df) >= 240)])

    # pipeline ----------------------------------------------------------------------------
    pl = load("pipeline_2026.json")
    df = pd.DataFrame([{k: v for k, v in o.items()
                        if not isinstance(v, (dict, list))} for o in pl["orgs"]])
    emit("fact_pipeline", df, "organization (2026)", ["pipeline_2026.json"],
         [("30 orgs", len(df) == 30)])

    # health ---------------------------------------------------------------------------------
    df = pd.DataFrame(load("health_2025_2026.json"))
    emit("fact_health", df, "team x season", ["health_2025_2026.json"],
         [("rows >= 50", len(df) >= 50)])

    # cap scenario -----------------------------------------------------------------
    cap = load("cap_scenario_2027.json")
    df = pd.DataFrame(cap["teams"])
    emit("fact_cap_scenario", df, "team (2027 scenario)", ["cap_scenario_2027.json"],
         [("30 teams", len(df) == 30),
          ("7 over cap", int((df.gap_to_cap > 0).sum()) == cap["n_over_cap"])])

    (OUT / "_build_report.json").write_text(json.dumps(REPORT, indent=1))
    if REPORT["failures"]:
        print("CURATE: FAIL —", REPORT["failures"])
        return 1
    print(f"CURATE: {len(REPORT['tables'])} tables built, all contracts pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
