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

    # --- SWAP: headline scenarios are the proven-optimal rosters --
    optc = load("optimizer_comparison_2027.json")
    sens = load("optimizer_sensitivity_2027.json")
    opt_by_label = {b["label"]: b["optimizer"] for b in optc["budgets"]}
    rng_by_label = {}
    for scale, key in (("x1.2", "low"), ("x0.8", "high")):
        for e in sens["price_sensitivity"][scale]:
            rng_by_label.setdefault(e["label"], {})[key] = e["total_war"]
    ok = wow["metadata"].get("cycle") == 52
    for s in wow["scenarios"]:
        o = opt_by_label[s["label"]]
        ok = ok and s["total_war"] == o["total_war"] and s["spend"] == o["spend"]
        ok = ok and s.get("proven_optimal") and s.get("mip_gap") == 0
        ok = ok and s["war_range_prices_pm20"]["low"] == rng_by_label[s["label"]]["low"]
        ok = ok and s["war_range_prices_pm20"]["high"] == rng_by_label[s["label"]]["high"]
        st = wow["availability_stress"]["stressed_totals"][s["label"]]
        ok = ok and st["raw_war"] == s["total_war"]
    greedy_bench = {s["label"]: s["total_war"]
                    for s in wow["benchmark_greedy"]["scenarios"]}
    ok = ok and greedy_bench == {"The Floor — $171.2M": 42.0,
                                 "The Middle — $208.0M": 45.7,
                                 "The Cap — $245.3M": 52.3}
    check("SWAP: headline scenarios are the Cycle 49 proven-optimal rosters "
          "with Cycle 50 price-error ranges; greedy preserved as benchmark "
          "(Cycle 52)", ok)

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

    def _mode_figs(mode):
        seg = html.split(f'id="mode-{mode}"', 1)[1]
        seg = re.split(r'id="mode-|<div class="srcbox"', seg)[0]
        return [int(n) for n in re.findall(r'data-mode="' + mode + r'" data-figure="(\d+)"', seg)]

    all_figs = sorted({int(n) for n in re.findall(r'data-figure="(\d+)"', html)})
    n_chapters = len(re.findall(r'class="chapter"', html))
    n_slides = len(re.findall(r'class="slide"', html))
    n_cards = len(re.findall(r'class="pcard"', html))
    explorer_figs = sorted(set(_mode_figs("explorer")))
    check("dashboard HTML: PRESS PLAY present, 25-chart index intact",
          "PRESS PLAY" in html and "all 25 real-data charts" in html)
    check("dashboard HTML: no stale figure references",
          "see Figure 12)" not in html)
    check("dashboard modes: story has exactly 6 chapters",
          n_chapters == 6, f"chapters={n_chapters}")
    check("dashboard modes: boardroom has <=15 slides",
          1 <= n_slides <= 15, f"slides={n_slides}")
    check("dashboard modes: explorer holds every figure the build produced",
          explorer_figs == all_figs and len(all_figs) >= 21,
          f"explorer={explorer_figs} all={all_figs}")
    check("dashboard modes: 8 percentile player cards",
          n_cards == 8, f"cards={n_cards}")
    check("dashboard modes: explorer holds Figure 23 with BIS source label",
          23 in explorer_figs and "NPB official" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: explorer holds Figure 24 with HS verdict box",
          24 in explorer_figs and "INCONCLUSIVE ON MISPRICING" in html
          and "Hakes" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: explorer holds Figure 25 with optimizer audit",
          25 in explorer_figs and "optimizer" in html.lower()
          and "proven optimal" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: story/boardroom headline the optimizer rosters "
          "(Cycle 52)",
          "floor roster buys 48.9 WAR" in html
          and "The floor roster buys 48.9 WAR" in html
          and "48.9 WAR proven-optimal" in html
          and "floor roster buys 42.0 WAR" not in html
          and "cap roster buys 52.3" not in html)

    # --- HS-2 verdict artifact: status + benchmark on record -------
    hs_path = DATA / "hakes_sauer_verdict.json"
    if hs_path.exists():
        hs = json.loads(hs_path.read_text())
        check("HS-2: verdict artifact present, inconclusive, benchmark recorded",
              hs["verdict"]["status"] == "INCONCLUSIVE on mispricing"
              and hs["benchmark_attempt"]["n_team_seasons"] == 480
              and hs["benchmark_attempt"]["status"].startswith("DEFENSIBLE")
              and hs["formal_test"]["status"] == "RUN",
              f"status={hs.get('verdict', {}).get('status')}")
    else:
        check("HS-2: verdict artifact present, inconclusive, benchmark recorded",
              False, "data/hakes_sauer_verdict.json missing")
    footer_sources = ["MLB Stats API", "Baseball Savant", "ESPN", "Steamer",
                      "Spotrac", "Cot's", "Chadwick", "Injury Report",
                      "NPB official BIS", "Baseball-Reference", "Statyx",
                      "FastballAPI", "ALL DATA &amp; API SOURCES"]
    missing_src = [s for s in footer_sources if s not in html]
    check("dashboard footer: all data & API sources listed (Cycle 45)",
          not missing_src, f"missing: {missing_src}")

    # --- posted class: trio dataset present and verified ----------
    posted = DATA / "posted_class_2026.json"
    if posted.exists():
        pj = json.loads(posted.read_text())
        names = {p["name"] for p in pj["players"]}
        check("posted class: trio JSON present, 3 players + posting facts",
              len(pj["players"]) == 3
              and names == {"Teruaki Sato", "Kaima Taira", "Hiromi Itoh"}
              and pj["posting_facts"]["signing_deadline"] == "2026-12-16 17:00 ET"
              and "BIS" in str(pj["canonical_source"]["name"]),
              f"players={sorted(names)}")
    else:
        check("posted class: trio JSON present, 3 players + posting facts", False,
              "data/posted_class_2026.json missing")

    # --- talk track references exist in the merged deck -----------
    tt = (ROOT / "docs" / "TALKTRACK.md").read_text()
    refs = {int(n) for n in re.findall(r"Figure (\d+)", tt)}
    check("talk track: all figure references <= 25", refs and max(refs) <= 25,
          f"refs: {sorted(refs)}")

    # --- OPT-1 optimizer artifact: comparison on record -----------
    opt_path = DATA / "optimizer_comparison_2027.json"
    if opt_path.exists():
        opt = json.loads(opt_path.read_text())
        ok = len(opt["budgets"]) == 3
        for b in opt["budgets"]:
            ok = ok and len(b["greedy"]["roster"]) == 26
            ok = ok and len(b["optimizer"]["roster"]) == 26
            ok = ok and b["greedy"]["spend"] <= b["budget"]
            ok = ok and b["optimizer"]["spend"] <= b["budget"]
            ok = ok and b["optimizer"]["total_war"] >= b["greedy"]["total_war"]
            ok = ok and b["optimizer"]["proven_optimal"]
            ok = ok and b["optimizer"]["mip_gap"] == 0
            ok = ok and b["greedy"]["satisfies_15pct_rule"]
            ok = ok and b["optimizer"]["satisfies_15pct_rule"]
        check("OPT-1: 3 budgets, 26-man rosters, spend <= budget, optima "
              "proven, 15% rule holds for greedy and optimizer", ok)
    else:
        check("OPT-1: 3 budgets, 26-man rosters, spend <= budget, optima "
              "proven, 15% rule holds for greedy and optimizer", False,
              "data/optimizer_comparison_2027.json missing")

    # --- OPT-2 sensitivity artifact: scenarios on record ----------
    sens_path = DATA / "optimizer_sensitivity_2027.json"
    if sens_path.exists():
        s = json.loads(sens_path.read_text())
        ok = True
        for scale in ("x0.8", "x1.2"):
            entries = s["price_sensitivity"][scale]
            ok = ok and len(entries) == 3
            for e in entries:
                ok = ok and len(e["roster"]) == 26
                ok = ok and e["spend_scenario_prices"] <= e["budget"] + 1
                ok = ok and e["proven_optimal"] and e["mip_gap"] == 0
                ok = ok and 0 <= e["n_changed"] <= 26
        tb = s["targeted_bid_up"]
        ok = ok and len(tb["roster"]) == 26 and tb["proven_optimal"]
        ok = ok and tb["spend_scenario_prices"] <= tb["budget"] + 1
        for e in s["war_haircut"]:
            ok = ok and len(e["roster"]) == 26 and e["proven_optimal"]
            ok = ok and e["spend"] <= e["budget"] + 1
            # re-scored on base WAR, a haircut roster cannot beat the
            # proven base optimum and cannot score below its own
            # haircut value
            ok = ok and e["total_war_haircut"] <= \
                e["total_war_base_rescore"] + 0.05
        base_floor = s["base_optimizer"]["The Floor — $171.2M"]
        for e in s["war_haircut"]:
            ref = s["base_optimizer"][e["label"]]["total_war"]
            ok = ok and e["total_war_base_rescore"] <= ref + 0.05
        m = s["mixed_floor"]
        ok = ok and len(m["roster"]) == 26
        ok = ok and m["n_prearb_slots"] + m["n_fa_slots"] == 26
        ok = ok and m["spend"] <= m["budget"] + 1
        ok = ok and m["proven_optimal"] and m["mip_gap"] == 0
        ok = ok and m["total_war"] >= base_floor["total_war"]
        ok = ok and all(r["prev_aav"] == 1000000 for r in m["roster"]
                        if r["origin"] == "pre-arb")
        ok = ok and s["metadata"]["prearb_pool"]["pool_size"] >= 100
        check("OPT-2: price/targeted/haircut scenarios proven, mixed "
              "floor 26-man with $1M-placeholder pre-arb slots, spend "
              "within budget", ok)
    else:
        check("OPT-2: price/targeted/haircut scenarios proven, mixed "
              "floor 26-man with $1M-placeholder pre-arb slots, spend "
              "within budget", False,
              "data/optimizer_sensitivity_2027.json missing")

    # --- API-1 live-feed layer: artifact on record -----------------
    ilc_path = DATA / "il_current_live.json"
    if ilc_path.exists():
        ilc = json.loads(ilc_path.read_text())
        ov = ilc["fa_overlay"]
        sc = ilc["reconciliation"]["standings_check_fastball_vs_kpi_2026"]
        check("API-1: live-IL artifact consistent (union >= 150, FA "
              "overlay counts hold, Fastball standings agree 30/30)",
              len(ilc["rows"]) >= 150
              and ov["n_matched"] == len(ov["players"])
              and ov["n_differs_from_static"]
              == sum(1 for p in ov["players"] if p["differs_from_static"])
              and sc["teams_compared"] == 30
              and sc["wins_and_runs_agree"] == 30,
              f"rows={len(ilc['rows'])} matched={ov['n_matched']} "
              f"agree={sc['wins_and_runs_agree']}")
        check("API-1: health figure carries the live-IL picture (Cycle 51)",
              "Current IL picture" in html and "fact_il_current" in html)
    else:
        check("API-1: live-IL artifact consistent (union >= 150, FA "
              "overlay counts hold, Fastball standings agree 30/30)",
              False, "data/il_current_live.json missing")

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
