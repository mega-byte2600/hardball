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
  dim_player_xwalk    data/raw/chadwick/people.csv (Cycle 44; grain one
                      row per person carrying an MLBAM key)
  fact_il_stints      data/raw/injury_report/il_stints_2019_2026.csv
                      (Cycle 44; grain one IL stint)
  fact_salaries_cots  data/salaries_cots_2027.json (Cycle 44; labeled
                      Cot's LRP-2027 cross-check layer — separate basis,
                      never summed with fact_salaries)
  fact_il_current     data/il_current_live.json (Cycle 51; grain one
                      row per currently listed injured player — the
                      union of the Statyx + FastballAPI live-feed
                      snapshots in data/raw/, built by
                      src/bml_cycle51.py; the static history layer
                      stays fact_il_stints)
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
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

    # Cycle 44: Chadwick crosswalk (raw zone, when present) -------------------
    chad = RAW / "chadwick" / "people.csv"
    if chad.exists():
        d = pd.read_csv(chad, low_memory=False)
        d = d[d["key_mlbam"].notna() & (d["key_mlbam"] != "")]
        df = pd.DataFrame({
            "player_id": d["key_mlbam"].astype(int),
            "retro_id": d["key_retro"], "bbref_id": d["key_bbref"],
            "bbref_minors_id": d["key_bbref_minors"],
            "fg_id": pd.to_numeric(d["key_fangraphs"], errors="coerce"),
            "npb_id": d["key_npb"], "wikidata_id": d["key_wikidata"],
            "name_last": d["name_last"], "name_first": d["name_first"],
            "birth_year": pd.to_numeric(d["birth_year"], errors="coerce"),
        }).drop_duplicates("player_id")
        emit("dim_player_xwalk", df, "one row per person (MLBAM key)",
             ["raw/chadwick/people.csv (Chadwick Bureau Register, ODC-BY)"],
             [("rows > 50000", len(df) > 50000),
              ("player_id unique", df.player_id.is_unique),
              ("player_id not null", df.player_id.notna().all())])
    else:
        print("  dim_player_xwalk: SKIPPED (chadwick raw absent)")

    # Cycle 44: Injury Report IL stints (raw zone, when present) ---------------
    il = RAW / "injury_report" / "il_stints_2019_2026.csv"
    if il.exists():
        df = pd.read_csv(il, low_memory=False)
        emit("fact_il_stints", df, "one IL stint (player x placement)",
             ["raw/injury_report/il_stints_2019_2026.csv "
              "(The Injury Report, from MLB IL transactions)"],
             [("rows >= 6000", len(df) >= 6000),
              ("seasons 2019-2026", df["season"].nunique() == 8),
              ("player_id present", "player_id" in df.columns)])
    else:
        print("  fact_il_stints: SKIPPED (injury report raw absent)")

    # Cycle 44: Cot's labeled salary cross-check layer -------------------------
    cots = load("salaries_cots_2027.json")
    df = pd.DataFrame(cots["players"])
    emit("fact_salaries_cots", df, "player x team (Cot's LRP 2027)",
         ["salaries_cots_2027.json"],
         [("rows == metadata", len(df) == cots["metadata"]["rows"]),
          ("30 teams", df.team.nunique() == 30),
          ("every row labeled cots", bool((df.source == "cots_baseball_prospectus").all()))])

    # Cycle 74: Cot's full-sheet parse (all rows, figures + markers) -----------
    cots_full = load("salaries_cots_full_2027.json")
    df = pd.DataFrame(cots_full["players"])
    emit("fact_salaries_cots_full", df,
         "Cot's sheet row (player or charge) x team — full parse, "
         "LRP 2026 + 2027 figure/marker",
         ["salaries_cots_full_2027.json"],
         [("rows == metadata", len(df) == cots_full["metadata"]["rows"]),
          ("30 teams", df.team.nunique() == 30),
          ("every row labeled cots",
           bool((df.source == "cots_baseball_prospectus").all())),
          ("figure rows == Cycle 44 file rows",
           int(df.lrp_2027.notna().sum()) == len(cots["players"]))])

    # Cycle 51: live-feed current IL picture (Statyx + FastballAPI) ------------
    ilc = load("il_current_live.json")
    df = pd.DataFrame(ilc["rows"])
    emit("fact_il_current", df, "one row per currently listed injured player",
         ["il_current_live.json (Statyx + FastballAPI snapshots, "
          "data/raw/{statyx,fastballapi}/*_2026-11-02.json, via "
          "src/bml_cycle51.py)"],
         [("rows >= 150", len(df) >= 150),
          ("player_name unique", df.player_name.is_unique),
          ("every row in at least one feed",
           bool((df.in_fastball | df.in_statyx).all())),
          ("pulled_at present", df.pulled_at.notna().all())])

    # Cycle 55: feed event layer (census baseline vs current diff) --------------
    ile_path = DATA / "il_events.json"
    if ile_path.exists():
        ile = json.loads(ile_path.read_text())
        ev_cols = ["event_id", "player_name", "event_type", "feeds",
                   "status_from", "status_to", "type_from", "type_to",
                   "statyx_commentary", "in_fa_pool", "fa_player_id",
                   "scenario_rosters", "baseline_date", "current_date"]
        ev = pd.DataFrame(ile["events"], columns=ev_cols)
        ev["feeds"] = ev["feeds"].map(
            lambda v: ",".join(v) if isinstance(v, list) else v)
        ev["scenario_rosters"] = ev["scenario_rosters"].map(
            lambda v: ",".join(v) if isinstance(v, list) else v)
        emit("fact_il_events", ev,
             "one row per IL movement event (append-only diff log)",
             ["il_events.json (src/bml_cycle55.py: baseline vs newest "
              "landed Statyx + FastballAPI injuries snapshots)"],
             [("rows == artifact summary",
               len(ev) == ile["summary"]["events_total"]),
              ("event types valid",
               set(ev.event_type) <= {"new_il", "returned",
                                      "status_change"}),
              ("fa flags reconcile",
               int(ev.in_fa_pool.sum())
               == sum(1 for e in ile["events"] if e["in_fa_pool"]))])
    else:
        print("  fact_il_events: SKIPPED (il_events.json absent)")

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
