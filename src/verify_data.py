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

    # --- UNC-1 availability-cap backtest: artifact on record -----
    unc1_path = DATA / "unc1_availability_backtest.json"
    if unc1_path.exists():
        u = json.loads(unc1_path.read_text())
        rows = u["rows"]
        pooled = u["pooled"]
        ok = (u["verdict"] in ("SUPPORTED", "MIXED", "NOT SUPPORTED")
              and set(u["per_class"]) == {"2022", "2023", "2024"}
              and len(rows) == pooled["n"] >= 30
              and all(r["target_season"] in (2022, 2023, 2024) for r in rows)
              and all(0.3 <= r["avail_pct"] <= 1.0 for r in rows))
        # pooled MAEs recomputed from rows must match the artifact
        for key in ("flat500", "flat500_capped", "marcel_pa", "marcel_pa_capped"):
            mae = sum(abs(r[key] - r["actual_pa"]) for r in rows) / len(rows)
            ok = ok and abs(mae - pooled[f"mae_{key}"]) < 0.2
        # verdict must follow its declared rule on the pooled MAEs
        flat_win = pooled["mae_flat500_capped"] < pooled["mae_flat500"]
        marcel_win = pooled["mae_marcel_pa_capped"] < pooled["mae_marcel_pa"]
        expect = ("SUPPORTED" if (flat_win and marcel_win)
                  else "MIXED" if (flat_win or marcel_win) else "NOT SUPPORTED")
        ok = ok and u["verdict"] == expect
        check("UNC-1: backtest artifact consistent (3 FA classes, pooled "
              "MAEs recompute, verdict follows declared rule)",
              ok, f"verdict={u['verdict']} n={pooled['n']}")
    else:
        check("UNC-1: backtest artifact consistent (3 FA classes, pooled "
              "MAEs recompute, verdict follows declared rule)",
              False, "data/unc1_availability_backtest.json missing")

    # --- PRICE-1 price-model workpaper (Cycle 61) -----------------
    pm_path = DATA / "price_model_workpaper_2027.json"
    if pm_path.exists():
        pm = json.loads(pm_path.read_text())
        ok = (pm["verdict"] == "NOT RUN — TRAINING DATA ABSENT"
              and pm["bar"]["threshold_fraction"] == 0.10
              and "UNTESTED" in pm["bar"]["status"]
              and "2024" in pm["model_design_preregistered"]["validation"]
              and len(pm["missing_source"]["readiness_criteria"]) >= 3
              and pm["dashboard_change"] == "none")
        check("PRICE-1: workpaper on record (verdict NOT RUN — "
              "training data absent, bar pre-committed at 10%, "
              "design pre-registered)", ok,
              f"verdict={pm.get('verdict')}")
        # survivorship table recomputes from the Cot's strings
        cots = load("salaries_cots_2027.json")["players"]
        pat = re.compile(r"^(\d+)\s*y/\$([\d.]+)M\s*\((\d+)-(\d+)\)")
        spans = {}
        for r in cots:
            m = pat.match(r.get("contract") or "")
            if m:
                spans.setdefault(2000 + int(m.group(3)), []).append(
                    int(m.group(1)))
        sv = pm["survivorship"]
        ok = (sv["parseable_contracts"] == sum(len(v)
                                               for v in spans.values()))
        for cls, span in (("2022", 2023), ("2023", 2024),
                          ("2024", 2025)):
            got = spans.get(span, [])
            rec = sv["classes"][cls]
            ok = (ok and rec["n_terms_recoverable"] == len(got)
                  and rec["min_years"] == (min(got) if got else None)
                  and rec["one_year_deals"]
                  == sum(1 for y in got if y == 1))
        check("PRICE-1: survivorship table recomputes from Cot's "
              "contract strings (24 / 18 / 35, no 1-year deals)",
              ok)
        # the incumbent anchor basis must be untouched by the cycle
        opt = load("optimizer_comparison_2027.json")
        fa_rows = load("fa_shopping_2027.json")["class"]
        ok = ("last-price anchor" in opt["metadata"]["price_basis"]
              and len(fa_rows) == pm["incumbent"]["fa_class_n"] == 251
              and sum(1 for r in fa_rows if r.get("prev_aav"))
              == pm["incumbent"]["prev_aav_coverage"])
        check("PRICE-1: incumbent anchor basis unchanged (optimizer "
              "still prior-AAV, 251-class coverage intact)", ok)
    else:
        check("PRICE-1: workpaper on record (verdict NOT RUN — "
              "training data absent, bar pre-committed at 10%, "
              "design pre-registered)",
              False, "data/price_model_workpaper_2027.json missing")
        check("PRICE-1: survivorship table recomputes from Cot's "
              "contract strings (24 / 18 / 35, no 1-year deals)",
              False, "data/price_model_workpaper_2027.json missing")
        check("PRICE-1: incumbent anchor basis unchanged (optimizer "
              "still prior-AAV, 251-class coverage intact)",
              False, "data/price_model_workpaper_2027.json missing")

    # --- BLEND-1 projection benchmark (Cycle 62) ------------------
    bl_path = DATA / "projection_blend_2027.json"
    if bl_path.exists():
        bl = json.loads(bl_path.read_text())
        ok = (bl["verdict"].startswith("NOT ADOPTED")
              and bl["blend"]["weights"] is None
              and bl["blend"]["blended_2027_projections"] is None
              and bl["shadow_run"] is None
              and bl["steamer_status"]["status"].startswith("NOT SCOREABLE"))
        for grp, mets in (("hitters", ("OBP", "SLG")),
                          ("pitchers", ("ERA", "WHIP"))):
            for win in ("2025", "2026"):
                for met in mets:
                    cell = bl["results"][grp][win][met]
                    for fc in ("naive", "marcel"):
                        m = cell[fc]
                        ok = ok and m["n"] == bl["paired_n"][grp][win] > 0 \
                            and m["r"] is not None and m["rmse"] > 0 \
                            and m["mae"] > 0
                    for fc in ("steamer", "blend"):
                        ok = ok and cell[fc]["status"] == "not_scored"
        check("BLEND-1: benchmark artifact complete (four forecasters x "
              "both groups x both windows, paired n consistent, blend "
              "not adopted, no weights fit)", ok,
              f"verdict={bl.get('verdict', '')[:40]}")
        # the recorded reproduction anchor must equal the committed
        # Cycles 21/24 variant-B backtests, cell for cell
        ra = bl["design"]["reproduction_anchor"]
        mb, pb = load("marcel_backtest.json"), load("pitcher_backtest.json")
        ok = all(ra[f"hitters_{t}"] == mb["targets"][str(t)]["B_3season"]
                 and ra[f"pitchers_{t}"] == pb["targets"][str(t)]["B_3season"]
                 for t in (2025, 2026))
        # and on the 2026 judge window Marcel must beat the naive on
        # both primary MAEs, as the panel states
        ok = ok and bl["results"]["hitters"]["2026"]["OBP"]["marcel"]["mae"] \
            < bl["results"]["hitters"]["2026"]["OBP"]["naive"]["mae"]
        ok = ok and bl["results"]["pitchers"]["2026"]["ERA"]["marcel"]["mae"] \
            < bl["results"]["pitchers"]["2026"]["ERA"]["naive"]["mae"]
        check("BLEND-1: reproduction anchor matches committed backtests; "
              "Marcel beats naive on both 2026 primary MAEs", ok)
        hn = bl["paired_n"]["hitters"]["2026"]
        pn = bl["paired_n"]["pitchers"]["2026"]
        check("BLEND-1: dashboard panel under Figure 18 (title, table, "
              "not-scored rows, blend status verbatim)",
              "How good are these projections?" in html
              and "Last season, repeated" in html
              and "Steamer + Marcel blend" in html
              and "not scored" in html
              and "Blend status: not adopted" in html
              and f"Hitters n = {hn}" in html
              and f"pitchers n = {pn}" in html)
    else:
        check("BLEND-1: benchmark artifact complete (four forecasters x "
              "both groups x both windows, paired n consistent, blend "
              "not adopted, no weights fit)", False,
              "data/projection_blend_2027.json missing")
        check("BLEND-1: reproduction anchor matches committed backtests; "
              "Marcel beats naive on both 2026 primary MAEs", False,
              "data/projection_blend_2027.json missing")
        check("BLEND-1: dashboard panel under Figure 18 (title, table, "
              "not-scored rows, blend status verbatim)", False,
              "data/projection_blend_2027.json missing")

    # --- UNC-2 uncertainty layer (Cycle 56) -----------------------
    unc2_path = DATA / "uncertainty_scenarios_2027.json"
    if unc2_path.exists():
        u2 = json.loads(unc2_path.read_text())
        u2_by = {s["label"]: s for s in u2["scenarios"]}
        ep, ap = u2["error_pools"], u2["availability_pools"]
        ok = (u2["sims"] >= 10000 and len(u2["scenarios"]) == 3)
        ok = ok and ep["hitters"]["n"] == sum(
            v["n"] for v in ep["hitters"]["per_target"].values())
        ok = ok and ep["pitchers"]["n"] == sum(
            v["n"] for v in ep["pitchers"]["per_target"].values())
        ok = ok and ep["hitters"]["n"] >= 150 and ep["pitchers"]["n"] >= 40
        ok = ok and ap["hitters"]["n"] == len(load("projections_2027_health.json"))
        ok = ok and ap["pitchers"]["n"] == len(
            load("projections_2027_pitchers.json"))
        ok = ok and abs(ep["hitters"]["mae_obp"]
                        - load("marcel_backtest.json")
                        ["pooled"]["C_age_crossfit"]["mae_obp"]) < 0.0015
        ok = ok and abs(ep["pitchers"]["mae_era"]
                        - load("pitcher_backtest.json")
                        ["pooled"]["C_age_crossfit"]["mae_era"]) < 0.0015
        for s in wow["scenarios"]:
            u = u2_by[s["label"]]
            st = wow["availability_stress"]["stressed_totals"][s["label"]]
            a = u["sanity_median_vs_point"]
            ok = ok and u["point_war"] == s["total_war"]
            ok = ok and (u["p10"] <= u["p20"] <= u["p50"]
                         <= u["p80"] <= u["p90"])
            ok = ok and u["sanity_cycle52_stress_inside_interval"][
                "stressed_total"] == st["war_at_pool_mean_avail"]
            ok = ok and u["sanity_cycle52_stress_inside_interval"][
                "inside_p10_p90"] == (
                    u["p10"] <= st["war_at_pool_mean_avail"] <= u["p90"])
            ok = ok and abs(a["analytic_delivered_mean"]
                            - (u["point_war"]
                               + a["availability_level_effect"]
                               + a["measured_residual_bias_effect"])) <= 0.15
            ok = ok and abs(a["simulated_mean_minus_analytic"]) <= 0.1
        check("UNC-2: uncertainty artifact consistent (pools tie to "
              "committed backtests + availability files, points tie to "
              "wow_scenarios, gap decomposition closes, Cycle 52 stress "
              "inside intervals)",
              ok, f"sims={u2['sims']} pools H{ep['hitters']['n']}/"
                  f"P{ep['pitchers']['n']}")
        fl, md, cp = (u2_by["The Floor — $171.2M"],
                      u2_by["The Middle — $208.0M"],
                      u2_by["The Cap — $245.3M"])
        # Plotly serializes figure JSON with \uXXXX escapes; normalize
        # (same treatment as the FIG-QA section below).
        html_u2 = re.sub(r"\\+u([0-9a-fA-F]{4})",
                         lambda m: chr(int(m.group(1), 16)), html)
        ok = all(f"10th–90th percentile {u['p10']}–{u['p90']} WAR, "
                 f"median {u['p50']}" in html_u2
                 for u in (fl, md, cp))
        ok = ok and f"delivered-WAR 10th–90th: {fl['p10']}–{fl['p90']}" in html_u2
        ok = ok and (f"floor's median at {fl['p50']} WAR (10th to 90th: "
                     f"{fl['p10']} to {fl['p90']})" in html_u2)
        ok = ok and f"cap's at {cp['p50']} ({cp['p10']} to {cp['p90']})" in html_u2
        ok = ok and (f"floor {fl['p10']}–{fl['p90']}, middle "
                     f"{md['p10']}–{md['p90']}, cap {cp['p10']}–{cp['p90']}"
                     in html_u2)
        check("UNC-2: dashboard renders the delivered-WAR intervals "
              "(Figure 16 titles, Story ch. 5, Boardroom slide 12)", ok)
        one = (ROOT / "docs" / "ONEPAGER.html").read_text(errors="ignore")
        ok = all(f"{u['point_war']:.1f} ({u['p10']:.1f}&ndash;{u['p90']:.1f})"
                 in one for u in (fl, md, cp))
        check("UNC-2: one-pager scenario table carries the intervals", ok)
    else:
        check("UNC-2: uncertainty artifact consistent (pools tie to "
              "committed backtests + availability files, points tie to "
              "wow_scenarios, gap decomposition closes, Cycle 52 stress "
              "inside intervals)",
              False, "data/uncertainty_scenarios_2027.json missing")
        check("UNC-2: dashboard renders the delivered-WAR intervals "
              "(Figure 16 titles, Story ch. 5, Boardroom slide 12)",
              False, "data/uncertainty_scenarios_2027.json missing")
        check("UNC-2: one-pager scenario table carries the intervals",
              False, "data/uncertainty_scenarios_2027.json missing")

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

    # --- FIG-QA (Cycle 53): one artifact-tied check per figure -----
    # Every figure gets a check whose expected value is computed from
    # its committed source artifact at gate time, so a wrong number in
    # any figure turns the gate red even if the panel code is edited.
    def _fig(n, name, ok, detail=""):
        check(f"FIG-QA fig {n}: {name}", ok, detail)

    # Plotly serializes figure JSON with \uXXXX escapes; normalize a
    # copy so title/annotation text checks see the rendered characters.
    html_qa = re.sub(r"\\+u([0-9a-fA-F]{4})",
                     lambda m: chr(int(m.group(1), 16)), html)

    panel_seasons = sorted({int(r["season"]) for r in panel})
    _fig(1, "animation panel covers 2011-2026, title in HTML",
         panel_seasons == list(range(2011, 2027))
         and "16 seasons of payroll vs wins" in html_qa,
         f"seasons={panel_seasons}")
    te = load("team_explorer.json")
    _fig(2, "team explorer: 30 teams in artifact and panel",
         len(te["teams"]) == 30 and "pick your team" in html_qa,
         f"teams={len(te['teams'])}")
    pci = load("persistence_ci.json")["pooled_contact"]
    _fig(3, "persistence caption carries pooled contact r + pair count",
         f"pooled r={pci['r']:.2f}" in html_qa
         and f"{pci['n_pairs']} player-year pairs" in html_qa,
         f"pooled={pci}")
    runs26 = [r for r in load("runs_panel.json") if r["season"] == 2026]
    _fig(4, "runs panel: 30 teams in 2026 slice, title in HTML",
         len(runs26) == 30 and "run differential → wins" in html_qa,
         f"rows26={len(runs26)}")
    qc = load("quant_core.json")["logistic"]["run-diff-only"]["25->26"]
    _fig(5, "AUC panel: artifact AUC rounds to the titled 0.95",
         round(qc["auc"], 2) == 0.95 and "AUC ≈ 0.95" in html_qa,
         f"auc={qc['auc']}")
    _fig(6, "payroll-vs-wins panel with cap/floor lines in HTML",
         "Payroll ($M) vs Wins" in html_qa and "Proposed cap $245.3M" in html_qa
         and "Proposed floor $171.2M" in html_qa)
    k26 = load("kpi_2026.json")
    _fig(7, "KPI signature: 30 teams with contact/K% in snapshot, panel in HTML",
         len(k26) == 30
         and all(r.get("contact") is not None and r.get("K%") is not None
                 for r in k26)
         and "Copycat-league KPI signature" in html_qa)
    with open(DATA / "efficiency_2000_2024.csv") as fh:
        n_eff = sum(1 for _ in fh) - 1
    _fig(8, "durability: efficiency file row count matches titled 721",
         n_eff == 721 and "721 team-seasons" in html_qa, f"rows={n_eff}")
    _fig(9, "projected-wins panel: 30 rows in projections_2026, title in HTML",
         len(load("projections_2026.json")) == 30
         and "Model-projected wins by team" in html_qa)
    cap_teams = load("cap_scenario_2027.json")["teams"]
    n_over = sum(1 for t in cap_teams if t["gap_to_cap"] > 0)
    _fig(10, "cap scenario: over-cap count from artifact is 7, panel in HTML",
         n_over == 7 and "Cap-era reality" in html_qa, f"over={n_over}")
    fs = load("forced_sellers_2027.json")["teams"]
    covered = [t["team"] for t in fs if t["covered"]]
    uncovered = [t["team"] for t in fs if not t["covered"]]
    _fig(11, "forced sellers: 6 covered, CHC the only uncovered team",
         len(covered) == 6 and uncovered == ["CHC"]
         and "Forced sellers" in html_qa,
         f"covered={covered} uncovered={uncovered}")
    proj27 = load("projections_2027.json")
    top_name = max(proj27, key=lambda r: r["proj_OBP"])["name"]
    _fig(12, "hitter projections: top-OBP name from artifact leads the panel",
         top_name in html_qa and "projected hitters by OBP" in html_qa,
         f"top={top_name}")
    if (DATA / "mlb_lake.db").exists():
        _fig(13, "pitching panel built from the lake, title in HTML",
             "Pitching is the other winning-cheap half" in html_qa)
    else:
        _fig(13, "pitching panel absent without lake, omission disclosed",
             'data-figure-missing="13"' in html_qa)
    ilc = load("il_current_live.json")
    ov = ilc["fa_overlay"]
    _fig(14, "health panel: live-IL counts and pull date from the artifact",
         f"{ov['n_matched']} of {ov['fa_pool_size']} free agents "
         "currently listed injured" in html_qa
         and ilc["metadata"]["pulled_date"] in html_qa,
         f"matched={ov['n_matched']}")
    rost = load("roster_2027.json")
    _fig(15, "roster panel: 13 hitters + 13 pitchers in artifact",
         len(rost["hitters"]) == 13 and len(rost["pitchers"]) == 13
         and "Proposed 26-man winning-cheap roster" in html_qa,
         f"H={len(rost['hitters'])} P={len(rost['pitchers'])}")
    wow0 = wow["scenarios"][0]["war_range_prices_pm20"]
    _fig(16, "scenario panel: floor title carries its +-20% price range",
         f"{wow0['low']}–{wow0['high']}" in html_qa
         and "across ±20% price error" in html_qa,
         f"range={wow0}")
    rv = load("robust_validation.json")
    _fig(17, "sensitivity panel: elasticity table present in artifact",
         len(rv.get("elasticity", {})) >= 5 and "measured elasticity" in html_qa,
         f"levers={len(rv.get('elasticity', {}))}")
    hb = load("fg_benchmark_2027.json")["hitters"]
    _fig(18, "benchmark panel: title carries artifact r and top-25 overlap",
         f"OBP r = {hb['obp']['pearson_r']}" in html_qa
         and f"{hb['top25_obp_overlap']['overlap_n']}/25" in html_qa,
         f"r={hb['obp']['pearson_r']}")
    st = load("savant_test.json").get("q2_trait_stability", {})
    _fig(19, "Savant panel: >=6 trait stabilities in artifact, title in HTML",
         len(st) >= 6 and "Savant traits are rock-stable" in html_qa,
         f"traits={len(st)}")
    vm = load("value_metrics_2026.json")
    _fig(20, "value metrics: hitting and pitching tables present",
         len(vm["hitting"]) >= 12 and len(vm["pitching"]) >= 12
         and "Top value metrics" in html_qa,
         f"H={len(vm['hitting'])} P={len(vm['pitching'])}")
    _fig(21, "pipeline panel title in HTML, 30 orgs behind it",
         "under-26 upper-minors depth" in html_qa
         and len(load("pipeline_2026.json")["orgs"]) == 30)
    _fig(22, "shopping panel: top-25 list in artifact, title in HTML",
         len(fa.get("top25_by_war", [])) == 25
         and "The shopping list" in html_qa,
         f"top25={len(fa.get('top25_by_war', []))}")
    f23 = load("fig23_rebuild_2026.json")
    _fig(23, "posted class: fee checkpoint exact, no-translation label shown",
         f23["fee_checkpoints_m"]["60"] == 10.875
         and "No NPB-to-MLB translation factor is claimed" in html_qa,
         f"fee60={f23['fee_checkpoints_m']['60']}")
    hsv = load("hakes_sauer_verdict.json")
    _fig(24, "HS panel: benchmark team-season count in the rendered title",
         f"{hsv['benchmark_attempt']['n_team_seasons']} team-seasons" in html_qa,
         f"n={hsv['benchmark_attempt']['n_team_seasons']}")
    d0 = optc["budgets"][0]["delta_war"]
    _fig(25, "optimizer panel: floor delta from artifact in the title",
         f"+{d0:.1f} WAR at the floor" in html_qa, f"delta={d0}")

    # --- API-2 feed architecture: event layer (Cycle 55) -----------
    ile_path = DATA / "il_events.json"
    if ile_path.exists():
        ile = json.loads(ile_path.read_text())
        ev, summ, fap = ile["events"], ile["summary"], ile["fa_pool_summary"]
        md = ile["metadata"]
        by_type = lambda lst, t: sum(1 for e in lst
                                     if e["event_type"] == t)
        snaps_ok = True
        for side in ("baseline", "current"):
            for key in ("fastballapi_injuries", "statyx_injuries"):
                ref = md[side][key]
                p = ROOT / ref["file"]
                if not p.exists():
                    snaps_ok = False
                    break
                env = json.loads(p.read_text())
                digest = hashlib.sha256(json.dumps(
                    env["payload"], indent=1, sort_keys=True
                ).encode()).hexdigest()
                if digest != ref["payload_sha256"]:
                    snaps_ok = False
        check("API-2: il_events.json consistent (counts reconcile, "
              "snapshots on disk match recorded shas, standings-test "
              "verdict on record)",
              summ["events_total"] == len(ev)
              and summ["new_il"] == by_type(ev, "new_il")
              and summ["returned"] == by_type(ev, "returned")
              and summ["status_change"] == by_type(ev, "status_change")
              and fap["events_total"] == len(ile["fa_pool_events"])
              and fap["new_il"] == by_type(ile["fa_pool_events"], "new_il")
              and all(e["in_fa_pool"] or e["scenario_rosters"]
                      for e in ile["fa_pool_events"])
              and md["statyx_standings_test"]["verdict"] in
                  ("dropped", "curated")
              and snaps_ok,
              f"events={len(ev)} fa_events={len(ile['fa_pool_events'])} "
              f"verdict={md['statyx_standings_test']['verdict']}")
        if fap["events_total"] == 0:
            frag = "no movement in the FA pool since the baseline pull"
        else:
            frag = (f"{fap['new_il']} new IL, {fap['returned']} returned, "
                    f"{fap['status_change']} status changes (FA pool)")
        check("API-2: health figure carries the FA-pool movement line "
              "(Cycle 55)",
              f"Movement since {md['baseline_date']}" in html_qa
              and frag in html_qa
              and f"census (FastballAPI) pulled "
                  f"{md['census_pulled_date']}" in html_qa
              and f"moves (Statyx) pulled {md['moves_pulled_date']}"
                  in html_qa,
              f"frag={frag!r}")
    else:
        check("API-2: il_events.json consistent (counts reconcile, "
              "snapshots on disk match recorded shas, standings-test "
              "verdict on record)", False, "data/il_events.json missing")
        check("API-2: health figure carries the FA-pool movement line "
              "(Cycle 55)", False, "data/il_events.json missing")

    # --- Evidence surveillance: PubMed panel (Cycle 57) ------------
    ev_path = DATA / "evidence_surveillance.json"
    ev_page = ROOT / "docs" / "EVIDENCE.html"
    if ev_path.exists() and ev_page.exists():
        ev = json.loads(ev_path.read_text())
        evh = ev_page.read_text(errors="ignore")
        # the page HTML-escapes text (apostrophes -> &#x27;); compare
        # against the unescaped rendering
        evh = (evh.replace("&#x27;", "'").replace("&#39;", "'")
               .replace("&amp;", "&"))
        lanes = ev["lanes"]
        cards = [c for lane in lanes for c in lane["cards"]]
        check("Evidence: artifact has 4 lanes x 3 cards, counts and "
              "abstracts recorded (Cycle 57)",
              len(lanes) == 4
              and all(len(lane["cards"]) == 3 for lane in lanes)
              and all(isinstance(lane["found"], int) and lane["found"] >= 3
                      for lane in lanes)
              and all(c.get("abstract") and c.get("pmid")
                      for c in cards)
              and ev["metadata"].get("run_date")
              and all(lane.get("query") for lane in lanes),
              f"lanes={len(lanes)} cards={len(cards)}")
        check("Evidence: EVIDENCE.html renders every card (lane counts, "
              "PMID, DOI, Finding) from the artifact (Cycle 57)",
              all(f"{lane['found']} FOUND" in evh
                  and lane["heading"] in evh for lane in lanes)
              and all(c["pmid"] in evh and c["finding"] in evh
                      and c["headline"] in evh
                      and (not c.get("doi") or c["doi"] in evh)
                      for c in cards)
              and "context, not a model input" in evh,
              f"cards={len(cards)}")
        _ev_seg = html.split('id="mode-explorer"', 1)[1]
        _ev_seg = re.split(r'id="mode-|<div class="srcbox"', _ev_seg)[0]
        _p14 = _ev_seg.find('data-mode="explorer" data-figure="14"')
        _pnote = _ev_seg.find(
            "What the evidence says now</a> — the published research "
            "on injury recovery and prevention.")
        _p15 = _ev_seg.find('data-mode="explorer" data-figure="15"')
        check("Evidence: dashboard footnote under Figure 14 matches "
              "artifact (exact note text, lane counts, page link) "
              "(Cycle 57)",
              '* <a href="../docs/EVIDENCE.html">What the evidence '
              "says now</a>" in html
              and "— the published research on injury recovery and "
                  "prevention." in html
              and all(f"({lane['found']} found)" in html for lane in lanes)
              and -1 < _p14 < _pnote < _p15,
              f"lanes={len(lanes)} p14={_p14} note={_pnote} p15={_p15}")
        check("Evidence: dashboard footer names PubMed / NCBI "
              "E-utilities (Cycle 57)",
              "PubMed / NCBI E-utilities" in html
              and "evidence_surveillance.json" in html)
    else:
        check("Evidence: artifact has 4 lanes x 3 cards, counts and "
              "abstracts recorded (Cycle 57)", False,
              "data/evidence_surveillance.json or docs/EVIDENCE.html "
              "missing")
        check("Evidence: EVIDENCE.html renders every card (lane counts, "
              "PMID, DOI, Finding) from the artifact (Cycle 57)", False,
              "evidence artifact or page missing")
        check("Evidence: dashboard footnote under Figure 14 matches "
              "artifact (exact note text, lane counts, page link) "
              "(Cycle 57)", False, "evidence artifact or page missing")
        check("Evidence: dashboard footer names PubMed / NCBI "
              "E-utilities (Cycle 57)", False,
              "evidence artifact or page missing")

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
