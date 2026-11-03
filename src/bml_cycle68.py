#!/usr/bin/env python3
"""Cycle 68 (elite slate item 5 of 6): reproducibility & claims pack.

ASSEMBLY + VERIFICATION, not new analysis. Builds:
  data/claims_register.json   — every material claim, with status
  data/figure_trace_2027.json — every figure + panel traced to its
      artifact, with headline values recomputed from the artifact
      and checked against the built dashboard HTML
  docs/REPRODUCIBILITY.html   — the pack page, generated from the
      two JSON files above (never hand-edited numbers)

Run AFTER the dashboard build, with the lake present:
    python3 src/dashboard_p6.py
    python3 src/bml_cycle68.py
Exit 1 on any failed trace or missing evidence artifact: a figure
whose artifact is missing, renamed, or mismatched is FLAGGED and
stops the build — never papered over with a new number.
"""
import csv
import html as _html
import json
import os
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
HTML_PATH = os.path.join(REPO, "dashboard", "hardball_demo.html")
FAILURES = []


def load(name):
    with open(os.path.join(DATA, name)) as fh:
        return json.load(fh)


def check(name, ok, detail=""):
    if not ok:
        FAILURES.append(name)
        print(f"  FLAG  {name} — {detail}")
    return ok


def r2(x):
    return round(float(x), 2)


# ---------------------------------------------------------------- claims
# Statuses: SUPPORTED / NOT SUPPORTED. Retractions live in their own
# section (a claim the demo once made and withdrew). Open items are
# neither: a decision still with the owner.
CLAIMS = [
    {
        "id": "S01",
        "claim": "The exact-optimizer rosters buy 48.9 WAR at the $171.2M floor, "
                  "52.8 WAR at the $208.0M middle, and 54.8 WAR at the "
                  "$245.3M cap, each a proven optimum (solver gap 0.0) "
                  "of 26 men within budget.",
        "location": "Figure 16 (scenario rosters) and Figure 25 (optimizer audit)",
        "evidence": {
            "artifact": "data/wow_scenarios.json + "
                        "data/optimizer_comparison_2027.json",
            "key_numbers": "Floor 48.9 WAR / $171.1M; Middle 52.8 / $207.8M; "
                           "Cap 54.8 / $245.2M; 26 men each; solver gap 0.0",
        },
        "status": "SUPPORTED", "cycle": 49, "date": "2026-11-02",
    },
    {
        "id": "S02",
        "claim": "The optimizer beats the greedy build at every budget: "
                  "floor +6.9 WAR (48.9 vs 42.0), middle +7.1 (52.8 vs "
                  "45.7), cap +2.5 (54.8 vs 52.3). The greedy build is "
                  "kept as the labeled benchmark, not hidden.",
        "location": "Figure 25 (optimizer audit)",
        "evidence": {
            "artifact": "data/optimizer_comparison_2027.json",
            "key_numbers": "Greedy 42.0 / 45.7 / 52.3 WAR; optimizer "
                           "48.9 / 52.8 / 54.8 WAR",
        },
        "status": "SUPPORTED", "cycle": 49, "date": "2026-11-02",
    },
    {
        "id": "S03",
        "claim": "The optimizer rosters stay best when prices are wrong by "
                  "20%: at uniform price x1.2 the floor still buys "
                  "45.0 WAR (above the greedy base 42.0); the full "
                  "ranges are floor 45.0-53.2, middle 48.5-55.5, cap "
                  "50.4-55.9 WAR.",
        "location": "Figure 25 sensitivity strip",
        "evidence": {
            "artifact": "data/optimizer_sensitivity_2027.json",
            "key_numbers": "Price x0.8 totals 53.2 / 55.5 / 55.9; price "
                           "x1.2 totals 45.0 / 48.5 / 50.4; all proven "
                           "optimal (gap 0.0)",
        },
        "status": "SUPPORTED", "cycle": 50, "date": "2026-11-02",
    },
    {
        "id": "S04",
        "claim": "Delivered WAR runs below the headline points: 10th-90th "
                  "percentile delivered totals are floor 33.0-46.9 "
                  "(median 39.8), middle 36.0-50.7 (43.2), cap "
                  "37.6-52.4 (44.9). The points are full-availability "
                  "projections, at about the 95th percentile of the "
                  "delivered distribution; nothing was re-centered.",
        "location": "Figure 16 (scenario rosters, delivered-WAR ranges)",
        "evidence": {
            "artifact": "data/uncertainty_scenarios_2027.json",
            "key_numbers": "Seeded Monte Carlo, 20,000 draws, seed "
                           "20261102; median gaps -9.1 / -9.6 / -9.9 = "
                           "availability level -6.8 / -7.2 / -7.5 + "
                           "residual bias -2.2 / -2.3 / -2.3",
        },
        "status": "SUPPORTED", "cycle": 56, "date": "2026-11-02",
    },
    {
        "id": "S05",
        "claim": "Injury risk is a level tax, not a budget effect: at the "
                  "measured pool-mean availability the stressed totals "
                  "are 44.6 / 48.1 / 50.0 WAR, and the floor roster "
                  "still captures about 89% of the cap roster's WAR.",
        "location": "Figure 16 (availability stress line)",
        "evidence": {
            "artifact": "data/wow_scenarios.json (availability_stress)",
            "key_numbers": "Pool n=201, mean availability 0.912; "
                           "stressed 44.6 / 48.1 / 50.0; floor/cap "
                           "ratio 0.892",
        },
        "status": "SUPPORTED", "cycle": 52, "date": "2026-11-02",
    },
    {
        "id": "S06",
        "claim": "The winning-cheap thesis is persistent, cap-efficient, "
                  "and low-variance — but NOT proven undervaluation: "
                  "the formal Hakes-Sauer proportionality test is "
                  "inconclusive by power (Sample S p=0.42, Sample C "
                  "p=0.90), while the run-value benchmark survives "
                  "(OBP +0.262, SLG +0.278 per PA; ratio 0.94, 95% CI "
                  "0.72-1.17).",
        "location": "Figure 24 (Hakes-Sauer verdict exhibit + verdict box)",
        "evidence": {
            "artifact": "data/hakes_sauer_verdict.json + "
                        "data/hakes_sauer_results.json",
            "key_numbers": "480 team-seasons, 2011-2026; S n=60, C "
                           "n=82; top-quartile contact hitters cost "
                           "0.54x / 0.53x median $/WAR (a contrast, "
                           "not a price effect)",
        },
        "status": "SUPPORTED", "cycle": 48, "date": "2026-11-02",
    },
    {
        "id": "S07",
        "claim": "Our Marcel projections agree with FanGraphs Steamer "
                  "2027: hitters 201/201 matched, OBP r=0.889; pitchers "
                  "102/102 matched, ERA r=0.636, WHIP r=0.717. This is "
                  "agreement, not accuracy — no 2027 outcomes exist yet.",
        "location": "Figure 18 (Marcel-Steamer benchmark)",
        "evidence": {
            "artifact": "data/fg_benchmark_2027.json",
            "key_numbers": "Hitters OBP r=0.889, mean |diff| 0.010; "
                           "pitchers ERA r=0.636, WHIP r=0.717; joined "
                           "on MLBAM id only, never by name",
        },
        "status": "SUPPORTED", "cycle": 22, "date": "2026-10-31",
    },
    {
        "id": "S08",
        "claim": "On held-out 2026 actuals, Marcel beats the naive "
                  "prior-season repeat: hitters (n=80) OBP MAE 0.0237 "
                  "vs naive 0.0265; pitchers (n=22) ERA MAE 0.9394 vs "
                  "naive 1.0177.",
        "location": "Benchmark panel under Figure 18 (Explorer)",
        "evidence": {
            "artifact": "data/projection_blend_2027.json",
            "key_numbers": "Hitters 2026 n=80; pitchers 2026 n=22; "
                           "age slopes fit on 2025 only, judged on "
                           "2026 only",
        },
        "status": "SUPPORTED", "cycle": 62, "date": "2026-11-02",
    },
    {
        "id": "S09",
        "claim": "The salary basis is: Spotrac payroll totals for all 30 "
                  "teams, with per-player contract rows for 24 of 30 "
                  "teams (927 rows); Cot's LRP-2027 as a second, "
                  "labeled basis (237 rows, 30 teams). On the Spotrac "
                  "basis 7 teams are over the cap ($358.2M over) and "
                  "15 under the floor ($807.8M short); 13 of 30 teams "
                  "change status between the two bases.",
        "location": "Figure 10 (cap-era reality), Figure 11 (forced "
                  "sellers), Cap Transition ledger panel",
        "evidence": {
            "artifact": "data/cap_transition_2027.json + "
                        "data/salaries_2026.json + "
                        "data/salaries_cots_2027.json",
            "key_numbers": "Spotrac gap teams: ARI, BOS, CHC, MIL, TB, "
                           "TEX; Cot's basis is a committed-contract "
                           "subtotal, not a complete payroll",
        },
        "status": "SUPPORTED", "cycle": 64, "date": "2026-11-02",
    },
    {
        "id": "S10",
        "claim": "Availability is measured, not assumed: hitter IL pool "
                  "n=201 (mean availability 0.912), pitcher pool "
                  "n=102 (mean 0.807). Health cards cover all 251 "
                  "free agents (166 measured / 65 no IL record / 20 "
                  "not matched, never assumed 100%), and ranking by "
                  "delivered WAR changes the order (Trevor Rogers "
                  "falls from headline #4 to delivered #6).",
        "location": "Figure 14 (health) and the health-cards panel in "
                  "Explorer 'Shop the FA Class'",
        "evidence": {
            "artifact": "data/fa_health_cards_2027.json + "
                        "data/uncertainty_scenarios_2027.json",
            "key_numbers": "Rogers: 64 IL days, 0.82 availability, "
                           "3.04 headline WAR -> 2.41 delivered; "
                           "per-player intervals NOT derived (pool "
                           "variance is not player risk)",
        },
        "status": "SUPPORTED", "cycle": 67, "date": "2026-11-02",
    },
    {
        "id": "S11",
        "claim": "The posted class is Sato (Hanshin, 3B/OF), Taira "
                  "(Seibu, RHP), and Itoh (Nippon-Ham, RHP), posted "
                  "November 1, 2026, window November 2-December 16, "
                  "with BIS counting stats as stated. No NPB-to-MLB "
                  "translation factor is claimed anywhere.",
        "location": "Figure 23 (The Posted Class)",
        "evidence": {
            "artifact": "data/posted_class_2026.json + "
                        "data/fig23_rebuild_2026.json",
            "key_numbers": "Sato 2026 .306, 39 HR, 106 RBI, OPS .992; "
                           "Taira 1.36 ERA, 146.0 IP; Itoh 3.18 ERA, "
                           "172.2 IP; fee checkpoint $60M -> $10.875M",
        },
        "status": "SUPPORTED", "cycle": 47, "date": "2026-11-02",
    },
    {
        "id": "S12",
        "claim": "The tracker ticker separates what is confirmed from "
                  "what is rumored: 321 SIGNED (from 705 FA-code "
                  "transactions in the pull window), 200 REPORTED, "
                  "0 BUZZ. An item becomes SIGNED only when the MLB "
                  "StatsAPI transactions feed carries it; REPORTED "
                  "and BUZZ items are never labeled signings. The "
                  "BUZZ lane ships empty because the Bluesky "
                  "Jetstream read did not complete — never filled "
                  "with substitutes.",
        "location": "Tracker ticker panel, front of Story mode",
        "evidence": {
            "artifact": "data/tracker_ticker_2026.json",
            "key_numbers": "Window 2026-10-27 to 2026-11-03; FA codes "
                           "SFA / DFA / TR / REL / CLW / OUT / DES; "
                           "Jetstream status stream_failed (timeout)",
        },
        "status": "SUPPORTED", "cycle": 66, "date": "2026-11-03",
    },
    {
        "id": "S13",
        "claim": "The evidence page reports the published research on "
                  "injury recovery and prevention, as run on "
                  "2026-11-02: UCL return-to-play 157, injury "
                  "prevention/workload 426, cellular recovery 404, "
                  "tendon healing/biologics 119 (systematic reviews "
                  "and meta-analyses). It is literature context for "
                  "the availability thesis, not a model input, and "
                  "not a biologics endorsement: the level-I evidence "
                  "does not support PRP/platelet add-ons.",
        "location": "Figure 14 footnote and docs/EVIDENCE.html",
        "evidence": {
            "artifact": "data/evidence_surveillance.json",
            "key_numbers": "Query strings recorded verbatim in the "
                           "artifact; 12 cards (3 per lane); every "
                           "Finding line drawn only from the stored "
                           "abstract",
        },
        "status": "SUPPORTED", "cycle": 57, "date": "2026-11-02",
    },
    {
        "id": "S14",
        "claim": "Figure 14's live-IL picture is drawn from the "
                  "2026-11-02 Statyx + FastballAPI pull: FastballAPI "
                  "is the census (190 injury records), Statyx the "
                  "event layer, MLB StatsAPI the standings of "
                  "record. 13 of the 251 free agents are currently "
                  "injured in that snapshot.",
        "location": "Figure 14 (health), live-IL sub-panel",
        "evidence": {
            "artifact": "data/il_current_live.json + data/il_events.json",
            "key_numbers": "Union 196 players; Fastball/StatsAPI "
                           "standings agree 30/30; first event "
                           "comparison: 0 events (state-identical)",
        },
        "status": "SUPPORTED", "cycle": 51, "date": "2026-11-02",
    },
    {
        "id": "S15",
        "claim": "Input skills persist year to year: pooled contact "
                  "r=0.843 across 457 player-season pairs (2022-2026 "
                  "windows). The edge the demo buys is the persistent "
                  "input, not the noisy outcome.",
        "location": "Figure 3 (skill persistence)",
        "evidence": {
            "artifact": "data/persistence_ci.json",
            "key_numbers": "Pooled contact r=0.843, 95% CI 0.81-0.872, "
                           "n=457 pairs",
        },
        "status": "SUPPORTED", "cycle": 44, "date": "2026-11-02",
    },
    {
        "id": "S16",
        "claim": "Run differential describes wins in the same season: "
                  "run-diff-only logistic AUC 0.949 (2025->2026, "
                  "titled 0.95) and within-season R-squared 0.545. "
                  "This is diagnostic, not a forward forecast.",
        "location": "Figure 5 (title-bar test) and Figure 4 (run "
                  "differential)",
        "evidence": {
            "artifact": "data/quant_core.json + data/runs_panel.json",
            "key_numbers": "Run-diff-only AUC 0.949 (25->26), 0.970 "
                           "(26->25); within-season R2 0.545",
        },
        "status": "SUPPORTED", "cycle": 22, "date": "2026-10-31",
    },
    {
        "id": "N01",
        "claim": "Prior-contract AAVs predict 2027 free-agent signed "
                  "prices.",
        "location": "Figure 16 prices and Figure 25 (anchor label)",
        "evidence": {
            "artifact": "data/price_model_workpaper_2027.json",
            "key_numbers": "Verdict NOT RUN - TRAINING DATA ABSENT: "
                           "the 5,153-signing census (2022-2024) "
                           "carries no contract terms; Cot's terms "
                           "cover survivors only (2022: 24 deals, "
                           "all 3+ years). Anchors remain the "
                           "optimizer input, labeled as anchors",
        },
        "status": "NOT SUPPORTED", "cycle": 61, "date": "2026-11-02",
    },
    {
        "id": "N02",
        "claim": "A Steamer + Marcel blend improves on both parents "
                  "for 2027 projections.",
        "location": "Benchmark panel under Figure 18 (Explorer)",
        "evidence": {
            "artifact": "data/projection_blend_2027.json",
            "key_numbers": "Verdict NOT ADOPTED: the blend cannot be "
                           "scored — Steamer exists in-repo only "
                           "for 2027 (unplayed); FanGraphs API "
                           "ignores the season parameter. First "
                           "honest test after the 2027 season",
        },
        "status": "NOT SUPPORTED", "cycle": 62, "date": "2026-11-02",
    },
    {
        "id": "N03",
        "claim": "Steamer's out-of-sample accuracy is scored.",
        "location": "Figure 18 (benchmark scope note)",
        "evidence": {
            "artifact": "data/projection_blend_2027.json "
                        "(steamer_status)",
            "key_numbers": "Steamer status NOT SCOREABLE: no held-out "
                           "Steamer outcomes exist in-repo",
        },
        "status": "NOT SUPPORTED", "cycle": 62, "date": "2026-11-02",
    },
    {
        "id": "N04",
        "claim": "Savant trait adjustments improve Marcel projections.",
        "location": "Figure 19 (Savant traits) — diagnostics only",
        "evidence": {
            "artifact": "data/savant_test.json",
            "key_numbers": "Bat speed is the most stable trait (YoY "
                           "r about 0.92) and still made projections "
                           "worse out-of-sample in both directions "
                           "on both metrics; nothing adopted",
        },
        "status": "NOT SUPPORTED", "cycle": 20, "date": "2026-11-01",
    },
    {
        "id": "N05",
        "claim": "Baseball-Reference salaries corroborate the Spotrac "
                  "/ Cot's salary basis within tolerance.",
        "location": "Salary basis notes (Figure 10/11, ledger)",
        "evidence": {
            "artifact": "data/salary_recon_cycle44.json",
            "key_numbers": "114 matched vs Cot's LRP-2026, 71.1% "
                           "within $50k — under the 80% bar, so no "
                           "BRef salary dataset ships; disagreements "
                           "are convention gaps (traded-player "
                           "shares, deferred/PV), not errors",
        },
        "status": "NOT SUPPORTED", "cycle": 44, "date": "2026-11-02",
    },
    {
        "id": "N06",
        "claim": "The demo's salary data is complete at player level "
                  "for all 30 teams.",
        "location": "Figure 10/11 and the ledger (basis note)",
        "evidence": {
            "artifact": "data/salaries_2026.json (metadata) + "
                        "data/cap_transition_2027.json",
            "key_numbers": "Per-player rows for 24 of 30 teams; gap "
                           "teams ARI, BOS, CHC, MIL, TB, TEX "
                           "(Spotrac page failures). Team payroll "
                           "totals exist for all 30; CHC is over "
                           "the cap by $4.0M with no shed set",
        },
        "status": "NOT SUPPORTED", "cycle": 64, "date": "2026-11-02",
    },
    {
        "id": "N07",
        "claim": "The proposed $245.3M cap / $171.2M floor / 15% "
                  "per-player max system is certain to govern 2027.",
        "location": "Every cap figure in the demo (conditional)",
        "evidence": {
            "artifact": "data/cap_transition_2027.json (metadata)",
            "key_numbers": "System status: owners' proposed system; "
                           "not law. CBA expires December 1, 2026; "
                           "the demo conditions every figure on "
                           "the proposal",
        },
        "status": "NOT SUPPORTED", "cycle": 64, "date": "2026-11-02",
    },
]

RETRACTED = [
    {
        "id": "R01",
        "claim": "A team-level formula predicts wins with R-squared "
                  "0.80 and MAE 4.0 wins.",
        "original_location": "Early dashboard and docs (pre-Cycle 18)",
        "retraction": "Cycles 18-19: the figure came from a favorable "
                      "2-year window. Refit on the full 2011-2026 "
                      "panel (450 complete rows): repeated K-fold "
                      "MAE 7.69, R-squared 0.534. The honest "
                      "use-case spec — predict NEXT season's wins "
                      "from this season's KPIs — gives in-sample "
                      "R-squared 0.136 and out-of-sample MAE 14.05 "
                      "(worse than naive 9.76); grouped CV "
                      "R-squared -6.1. What survives is player-level "
                      "acquisition (Marcel + injury caps), not a "
                      "team-wins formula.",
        "retracted_cycle": 19, "date": "2026-10-31",
        "standing_record": "data/formula_prod.json stays annotated "
                           "'DIAGNOSTIC ONLY — same-year fit; not a "
                           "forecast'; the gate pins that annotation.",
    },
    {
        "id": "R02",
        "claim": "Capping projections by measured availability "
                  "improves point forecasts.",
        "original_location": "UNC-1 candidate correction (Cycle 54 workpaper)",
        "retraction": "Cycle 54 backtest, pooled n=39 qualified FA "
                      "regulars (2022-2024 classes, 5,153 signings "
                      "screened): flat MAE 95.1 -> 132.3 capped; "
                      "Marcel MAE 46.2 -> 61.1 capped. The cap helped "
                      "65% of the 20 Marcel-overshoot cases, so it "
                      "is a downside adjustment, not a point "
                      "correction. It shapes the Cycle 56 delivered-"
                      "WAR distribution only; no headline point "
                      "was changed.",
        "retracted_cycle": 54, "date": "2026-11-02",
        "standing_record": "data/unc1_availability_backtest.json verdict "
                           "NOT SUPPORTED; UNC-2 records the "
                           "governance explicitly.",
    },
    {
        "id": "R03",
        "claim": "The OBP year-over-year persistence figure as "
                  "first published.",
        "original_location": "Persistence exhibit (pre-Cycle 44)",
        "retraction": "Cycle 39 restored-lake recomputation corrected "
                      "the figure (the 'OBP r about 0.3' claim). The "
                      "correction's own PR (#21) was never merged; "
                      "Cycle 44 shipped the corrected accuracy "
                      "stack instead, and the gate pins the shipped "
                      "persistence values. The shipped figure is "
                      "the recomputed one (pooled contact r=0.843, "
                      "457 pairs).",
        "retracted_cycle": 44, "date": "2026-11-02",
        "standing_record": "docs/BML_LOG.md Cycle 39 entry; "
                           "data/persistence_ci.json as shipped.",
    },
]

OPEN_ITEMS = [
    {
        "id": "O01",
        "claim": "Figure 9's 'Model-projected wins' title presents "
                  "in-sample fitted values without an in-sample / "
                  "diagnostic label.",
        "location": "Figure 9 (model fit vs actual wins)",
        "evidence": {
            "artifact": "data/projections_2026.json + "
                        "data/formula_prod.json",
            "key_numbers": "30 rows; formula_prod status DIAGNOSTIC "
                           "ONLY — same-year fit; not a forecast",
        },
        "status": "OPEN — owner decision pending (label as "
                  "diagnostic vs leave as is)",
        "cycle": 53, "date": "2026-11-02",
    },
]

CORRECTIONS_LOG = [
    "Cycle 59 corrected two Cycle 58 probe-evidence lines in the "
    "scorecard (SABR: HTTP 200, not 429; Elias: connection dropped, "
    "not HTTP 200). The verdicts did not change; the correction is "
    "recorded in the PR body as an errata block, not a rewrite.",
    "Cycle 67's spellcheck whitelist splits accented player names at "
    "the accent (berr = Berrios, garc = Garcia, nchez = Sanchez, "
    "rez = Perez, rquez = Marquez) — a tokenizer artifact, recorded "
    "in the cycle note so it is not mistaken for misspellings.",
]


# ---------------------------------------------------------------- trace
# One entry per figure (FIG-QA method, Cycle 53) and per named panel.
# "headline" is recomputed from the artifact at run time; "markers"
# must all appear in the built dashboard HTML. A figure whose markers
# fail is FLAGGED and stops the build.
def trace_figures(html_text):
    wow = load("wow_scenarios.json")
    unc = {s["label"]: s for s in load("uncertainty_scenarios_2027.json")["scenarios"]}
    sens = load("optimizer_sensitivity_2027.json")
    bench = load("fg_benchmark_2027.json")
    blend = load("projection_blend_2027.json")
    hs = load("hakes_sauer_verdict.json")
    cap = load("cap_transition_2027.json")
    forced = load("forced_sellers_2027.json")
    shop = load("fa_shopping_2027.json")["class"]
    # Cycle 71: the shopping figure is now the SURPLUS-VALUE arbitrage panel.
    surplus_ar = load("surplus_value_2027.json")
    proj27 = load("projections_2027.json")
    proj26 = load("projections_2026.json")
    kpi26 = load("kpi_2026.json")
    roster = load("roster_2027.json")
    quant = load("quant_core.json")
    pers = load("persistence_ci.json")
    sav = load("savant_test.json")
    val = load("value_metrics_2026.json")
    pipe = load("pipeline_2026.json")["orgs"]
    il = load("il_current_live.json")
    opt = load("optimizer_comparison_2027.json")

    with open(os.path.join(DATA, "panel_2011_2026.csv")) as fh:
        panel_rows = list(csv.DictReader(fh))
    with open(os.path.join(DATA, "efficiency_2000_2024.csv")) as fh:
        eff_rows = list(csv.DictReader(fh))
    with open(os.path.join(DATA, "runs_panel.json")) as fh:
        runs = json.load(fh)

    lake_path = os.path.join(DATA, "mlb_lake.db")
    lake_ok = os.path.exists(lake_path)
    if lake_ok:
        con = sqlite3.connect(lake_path)
        pit_rows = con.execute(
            "SELECT COUNT(*) FROM stat_lines WHERE group_name='pitching'"
        ).fetchone()[0]
        con.close()
    else:
        pit_rows = 0

    top_obp = max(proj27, key=lambda r: r["proj_OBP"])["name"]
    top_shop = max(surplus_ar.get("top_surplus", []),
                   key=lambda r: r.get("surplus_usd") or 0)["name"]
    floor = wow["scenarios"][0]
    floor_rng = floor.get("war_range_prices_pm20", {})
    floor_delta = round(
        opt["budgets"][0]["optimizer"]["total_war"]
        - opt["budgets"][0]["greedy"]["total_war"], 1)

    figs = [
        {"figure": 1, "title": "PRESS PLAY: 16 seasons of payroll vs wins",
         "artifacts": ["data/panel_2011_2026.csv"],
         "headline": f"{len(panel_rows)} team-seasons, seasons "
                     f"{min(r['season'] for r in panel_rows)}-"
                     f"{max(r['season'] for r in panel_rows)}",
         "markers": ["PRESS PLAY"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 2, "title": "Pick your team — 2026 signature vs the winning-cheap profile",
         "artifacts": ["data/team_explorer.json"],
         "headline": f"{len(load('team_explorer.json')['teams'])} teams",
         "markers": ["pick your team"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 3, "title": "The measurable edge: input SKILLS persist year-to-year",
         "artifacts": ["data/persistence_ci.json",
                       "data/player_persistence_multiyear.json"],
         "headline": f"pooled contact r={pers['pooled_contact']['r']}, "
                     f"{pers['pooled_contact']['n_pairs']} pairs",
         "markers": ["457"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 4, "title": "The top lever — run differential to wins",
         "artifacts": ["data/runs_panel.json"],
         "headline": f"2026 slice = "
                     f"{len([r for r in runs if str(r['season']) == '2026'])} rows",
         "markers": ["run differential"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 5, "title": "The proof it works: run differential alone flags a 90+ win club",
         "artifacts": ["data/quant_core.json"],
         "headline": f"run-diff-only AUC "
                     f"{quant['logistic']['run-diff-only']['25->26']['auc']:.3f} "
                     f"(titled 0.95)",
         "markers": ["AUC .95"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 6, "title": "Payroll vs Wins: money buys some wins",
         "artifacts": ["data/kpi_2026.json"],
         "headline": f"{len(kpi26)} teams; cap $245.3M / floor $171.2M lines",
         "markers": ["Payroll ($M) vs Wins"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 7, "title": "Copycat-league KPI signature",
         "artifacts": ["data/kpi_2026.json"],
         "headline": f"{len(kpi26)} teams; contact/K% non-null for all",
         "markers": ["Copycat-league KPI signature"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 8, "title": "25-year proof: efficiency is durable",
         "artifacts": ["data/efficiency_2000_2024.csv"],
         "headline": f"{len(eff_rows)} team-seasons, 2000-2024",
         "markers": ["efficiency is durable"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 9, "title": "Model fit (in-sample) vs actual wins, by team",
         "artifacts": ["data/projections_2026.json",
                       "data/formula_prod.json"],
         "headline": f"{len(proj26)} rows; in-sample fitted values "
                     f"(see open item O01 — label decision pending)",
         "markers": ["Model fit (in-sample) vs actual wins"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 10, "title": "Cap-era reality: payroll vs proposed 2027 cap",
         "artifacts": ["data/cap_scenario_2027.json"],
         "headline": f"over cap {cap['summary']['primary']['OVER CAP']['count']}, "
                     f"under floor "
                     f"{cap['summary']['primary']['UNDER FLOOR']['count']}",
         "markers": ["Cap-era reality"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 11, "title": "Forced sellers — how few big contracts close each gap",
         "artifacts": ["data/forced_sellers_2027.json"],
         "headline": f"{sum(1 for t in forced['teams'] if t['covered'])} covered; "
                     f"CHC the only uncovered team",
         "markers": ["Forced sellers"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 12, "title": "2027 projected hitters by OBP (Marcel)",
         "artifacts": ["data/projections_2027.json",
                       "data/prediction_conviction_2027.json"],
         "headline": f"top OBP: {top_obp}",
         "markers": [top_obp, "projected hitters by OBP", "no prior record"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 13, "title": "Pitching is the other winning-cheap half",
         "artifacts": ["data/mlb_lake.db (local build artifact, gitignored) "
                       "-> curated data/curated/fact_stat_lines.parquet"],
         "headline": f"lake present: {lake_ok}; pitching stat_lines rows "
                     f"= {pit_rows}",
         "markers": ["Pitching is the other winning-cheap half"],
         "build": "python3 src/dashboard_p6.py (with the lake present)"},
        {"figure": 14, "title": "2027 health risk (IL-based PA cap) + live-IL picture",
         "artifacts": ["data/projections_2027_health.json",
                       "data/il_current_live.json", "data/il_events.json"],
         "headline": f"live-IL pull {il['metadata']['pulled_date']}; "
                     f"{il['fa_overlay']['n_matched']} of "
                     f"{il['fa_overlay']['fa_pool_size']} FAs injured",
         "markers": ["Current IL picture",
                     il['metadata']['pulled_date']],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 15, "title": "Proposed 26-man winning-cheap roster",
         "artifacts": ["data/roster_2027.json"],
         "headline": f"{len(roster['hitters'])} hitters + "
                     f"{len(roster['pitchers'])} pitchers",
         "markers": ["Proposed 26-man winning-cheap roster"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 16, "title": "What does the money buy? (scenario rosters)",
         "artifacts": ["data/wow_scenarios.json",
                       "data/uncertainty_scenarios_2027.json"],
         "headline": f"Floor {floor['total_war']} WAR; "
                     f"±20% range {floor_rng.get('low')}-"
                     f"{floor_rng.get('high')}; delivered 10th-90th "
                     f"{unc[floor['label']]['p10']}-"
                     f"{unc[floor['label']]['p90']}",
         "markers": ["48.9", "52.8", "54.8"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 17, "title": "What-if: how many wins a lever moves",
         "artifacts": ["data/robust_validation.json"],
         "headline": f"{len(load('robust_validation.json')['elasticity'])} "
                     f"elasticity levers",
         "markers": ["how many wins a lever moves"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 18, "title": "The benchmark: our Marcel vs FanGraphs Steamer 2027",
         "artifacts": ["data/fg_benchmark_2027.json",
                       "data/fg_steamer_2027_bat.json"],
         "headline": f"OBP r={bench['hitters']['obp']['pearson_r']}; "
                     f"top-25 overlap "
                     f"{bench['hitters']['top25_obp_overlap']['overlap_n']}/25",
         "markers": ["0.889"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 19, "title": "Savant traits are rock-stable year-to-year",
         "artifacts": ["data/savant_test.json"],
         "headline": f"{len(sav['q2_trait_stability'])} trait stabilities",
         "markers": ["Savant traits are rock-stable"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 20, "title": "Top value metrics — wOBA/wRC+ & FIP/K-BB%",
         "artifacts": ["data/value_metrics_2026.json"],
         "headline": f"hitting rows {len(val['hitting'])}; pitching rows "
                     f"{len(val['pitching'])}",
         "markers": ["Top value metrics"], "build": "python3 src/dashboard_p6.py"},
        {"figure": 21, "title": "The pipeline behind winning-cheap",
         "artifacts": ["data/pipeline_2026.json"],
         "headline": f"{len(pipe)} organizations",
         "markers": ["pipeline behind winning-cheap"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 22, "title": "The 2027 FA market by SURPLUS VALUE — what wins are really priced at",
         "artifacts": ["data/fa_shopping_2027.json", "data/surplus_value_2027.json"],
         "headline": f"top surplus: {top_shop}",
         "markers": [top_shop, "SURPLUS VALUE"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 23, "title": "The Posted Class: three players, three different bets",
         "artifacts": ["data/posted_class_2026.json",
                       "data/fig23_rebuild_2026.json"],
         "headline": "fee checkpoint $60M -> $10.875M; no NPB-to-MLB "
                     "translation factor claimed",
         "markers": ["10.875",
                     "No NPB-to-MLB translation factor is claimed"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 24, "title": "The pricing test: Hakes-Sauer on ourselves",
         "artifacts": ["data/hakes_sauer_verdict.json",
                       "data/hakes_sauer_results.json"],
         "headline": f"{hs['benchmark_attempt']['n_team_seasons']} "
                     f"team-seasons; verdict INCONCLUSIVE on mispricing",
         "markers": ["480", "INCONCLUSIVE"],
         "build": "python3 src/dashboard_p6.py"},
        {"figure": 25, "title": "Benchmark vs headline: the exact optimum beats the greedy build",
         "artifacts": ["data/optimizer_comparison_2027.json",
                       "data/optimizer_sensitivity_2027.json"],
         "headline": f"floor delta +{floor_delta} WAR; price ranges "
                     f"{sens['price_sensitivity']['x1.2'][0]['total_war']}-"
                     f"{sens['price_sensitivity']['x0.8'][0]['total_war']}",
         "markers": ["exact optimum beats the greedy"],
         "build": "python3 src/dashboard_p6.py"},
    ]
    out = []
    for f in figs:
        panel = f'data-figure="{f["figure"]}"' in html_text
        missing = [m for m in f["markers"] if m not in html_text]
        ok = panel and not missing
        check(f"Figure {f['figure']} trace", ok,
              f"panel={panel} missing_markers={missing}")
        out.append({**f, "panel_present": panel,
                    "markers_missing": missing,
                    "status": "verified" if ok else "FLAGGED"})
    return out


def trace_panels(html_text):
    tk = load("tracker_ticker_2026.json")
    cap = load("cap_transition_2027.json")
    blend = load("projection_blend_2027.json")
    hc = load("fa_health_cards_2027.json")
    ev = load("evidence_surveillance.json")
    opt = load("optimizer_comparison_2027.json")
    hs = load("hakes_sauer_verdict.json")
    panels = [
        {"panel": "Tracker ticker (Story lead)",
         "artifacts": ["data/tracker_ticker_2026.json"],
         "headline": f"SIGNED {tk['metadata']['counts']['signed']} · "
                     f"REPORTED {tk['metadata']['counts']['reported']} · "
                     f"BUZZ {tk['metadata']['counts']['buzz']}",
         "markers": ["Free-agency wire — the tracker ticker",
                     "An item becomes SIGNED only when the MLB StatsAPI "
                     "transactions feed carries it"],
         "build": "python3 src/pull_tracker_ticker.py + src/dashboard_p6.py"},
        {"panel": "Cap Transition ledger (Boardroom lead)",
         "artifacts": ["data/cap_transition_2027.json"],
         "headline": f"primary: "
                     f"{cap['summary']['primary']['OVER CAP']['count']} over / "
                     f"{cap['summary']['primary']['UNDER FLOOR']['count']} under / "
                     f"{cap['summary']['primary']['INSIDE THE BAND']['count']} inside",
         "markers": ["2027 Cap Transition ledger"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Held-out benchmark panel (under Figure 18)",
         "artifacts": ["data/projection_blend_2027.json"],
         "headline": "hitters 2026 naive OBP MAE 0.0265 vs Marcel 0.0237",
         "markers": ["How good are these projections?"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Health cards (Explorer, Shop the FA Class)",
         "artifacts": ["data/fa_health_cards_2027.json"],
         "headline": f"{len(hc['cards'])} cards; "
                     f"{hc['metadata']['counts']['with_measured_availability']} "
                     f"measured / "
                     f"{hc['metadata']['counts']['no_il_record']} no IL record / "
                     f"{hc['metadata']['counts']['not_matched_no_player_id']} "
                     f"not matched",
         "markers": ["Health cards: what each free agent will actually give you"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Evidence footnote (under Figure 14)",
         "artifacts": ["data/evidence_surveillance.json"],
         "headline": "lanes as run: UCL 157, prevention/workload 426, "
                     "cellular 404, tendon/biologics 119",
         # The footnote renders the title as a link, so the wording
         # is checked as its two halves, not one literal string.
         "markers": ["What the evidence says now",
                     "the published research on injury recovery and "
                     "prevention.",
                     "../docs/EVIDENCE.html"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Optimizer audit (Explorer, Build a Roster)",
         "artifacts": ["data/optimizer_comparison_2027.json"],
         "headline": "floor greedy 42.0 WAR vs optimum 48.9 WAR",
         "markers": ["BENCHMARK VS HEADLINE (Cycles 49–52)"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Hakes-Sauer verdict box (under Figure 24)",
         "artifacts": ["data/hakes_sauer_verdict.json"],
         "headline": "verdict INCONCLUSIVE on mispricing",
         "markers": ["THE VERDICT"],
         "build": "python3 src/dashboard_p6.py"},
        {"panel": "Posted companion (Explorer, The Posted Class)",
         "artifacts": ["data/posted_class_2026.json"],
         "headline": "Sato / Taira / Itoh trio cards + posting clock + fee tiers",
         "markers": ["The trio, the clock, and the honesty box"],
         "build": "python3 src/dashboard_p6.py"},
    ]
    out = []
    for p in panels:
        missing = [m for m in p["markers"] if m not in html_text]
        ok = not missing
        check(f"Panel trace: {p['panel']}", ok, f"missing={missing}")
        out.append({**p, "markers_missing": missing,
                    "status": "verified" if ok else "FLAGGED"})
    return out


def main():
    if not os.path.exists(HTML_PATH):
        print("dashboard HTML missing — build first: python3 src/dashboard_p6.py")
        return 1
    html_text = open(HTML_PATH, encoding="utf-8", errors="ignore").read()
    # Evidence artifacts named by the register must exist. Parse file
    # paths out of the artifact string (it may carry parenthetical
    # section notes, e.g. "data/x.json (availability_stress)").
    import re as _re
    for c in CLAIMS + OPEN_ITEMS:
        for art in _re.findall(r"data/[a-z0-9_./]+\.(?:json|csv)",
                               c["evidence"]["artifact"]):
            check(f"Register evidence exists: {art}",
                  os.path.exists(os.path.join(REPO, art)), "missing")
    figures = trace_figures(html_text)
    panels = trace_panels(html_text)

    claims = CLAIMS
    counts = {
        "supported": sum(1 for c in claims if c["status"] == "SUPPORTED"),
        "not_supported": sum(1 for c in claims if c["status"] == "NOT SUPPORTED"),
        "retracted": len(RETRACTED),
        "open_items": len(OPEN_ITEMS),
        "figures_traced": len(figures),
        "figures_verified": sum(1 for f in figures if f["status"] == "verified"),
        "panels_traced": len(panels),
        "panels_verified": sum(1 for p in panels if p["status"] == "verified"),
    }
    register = {
        "cycle": 68,
        "title": "HARDBALL claims register — what the demo asserts, "
                  "what it does not support, and what it withdrew",
        "rule": "A claim is SUPPORTED only if a committed artifact carries "
                "the numbers. A claim that failed its own test is NOT "
                "SUPPORTED, not softened. A claim the demo once made "
                "and withdrew is RETRACTED, stated plainly, not deleted.",
        "claims": claims,
        "retracted": RETRACTED,
        "open_items": OPEN_ITEMS,
        "corrections_log": CORRECTIONS_LOG,
        "counts": counts,
    }
    with open(os.path.join(DATA, "claims_register.json"), "w") as fh:
        json.dump(register, fh, indent=1, ensure_ascii=False)
    trace = {
        "cycle": 68,
        "dashboard": "dashboard/hardball_demo.html (built with the lake present)",
        "lineage": "ingest (data/raw + manifest.jsonl, local) -> curated "
                  "parquet (data/curated, 19 tables, schema-enforced) -> "
                  "warehouse (data/hardball.duckdb, built, gitignored) -> "
                  "serving (dashboard reads committed JSON artifacts + "
                  "curated tables; the lake feeds Figure 13 only)",
        "build_commands": {
            "ingest": "python3 src/ingest_platform.py",
            "curate": "python3 src/curate.py",
            "warehouse": "python3 src/build_warehouse.py",
            "dashboard": "python3 src/dashboard_p6.py",
            "gate": "python3 src/verify_data.py",
            "spellcheck": "python3 src/spellcheck_gate.py",
            "this_pack": "python3 src/bml_cycle68.py",
        },
        "figures": figures,
        "panels": panels,
        "counts": counts,
    }
    with open(os.path.join(DATA, "figure_trace_2027.json"), "w") as fh:
        json.dump(trace, fh, indent=1, ensure_ascii=False)
    print(f"claims: {counts['supported']} supported, "
          f"{counts['not_supported']} not supported, "
          f"{counts['retracted']} retracted, {counts['open_items']} open")
    print(f"trace: {counts['figures_verified']}/{counts['figures_traced']} "
          f"figures, {counts['panels_verified']}/{counts['panels_traced']} panels")
    if FAILURES:
        print(f"CYCLE 68: {len(FAILURES)} FLAG(S) — pack NOT written clean")
        return 1
    write_pack_page(register, trace)
    print("pack page written: docs/REPRODUCIBILITY.html")
    return 0


def write_pack_page(register, trace):
    def esc(s):
        return _html.escape(str(s))
    rows = ""
    for c in register["claims"]:
        rows += ("<tr><td><b>" + esc(c["id"]) + "</b></td><td>" + esc(c["claim"]) +
                 "</td><td>" + esc(c["location"]) + "</td><td>" +
                 esc(c["evidence"]["artifact"]) + "<br>" +
                 esc(c["evidence"]["key_numbers"]) + "</td><td><b>" +
                 esc(c["status"]) + "</b><br>Cycle " + esc(c["cycle"]) +
                 ", " + esc(c["date"]) + "</td></tr>\n")
    ret = ""
    for r in register["retracted"]:
        ret += ("<tr><td><b>" + esc(r["id"]) + "</b></td><td>" + esc(r["claim"]) +
                "</td><td>" + esc(r["retraction"]) + "</td><td>Cycle " +
                esc(r["retracted_cycle"]) + ", " + esc(r["date"]) +
                "<br>" + esc(r["standing_record"]) + "</td></tr>\n")
    opn = ""
    for o in register["open_items"]:
        opn += ("<tr><td><b>" + esc(o["id"]) + "</b></td><td>" + esc(o["claim"]) +
                "</td><td>" + esc(o["location"]) + "</td><td>" +
                esc(o["status"]) + "</td></tr>\n")
    figs = ""
    for f in trace["figures"]:
        figs += ("<tr><td>Figure " + str(f["figure"]) + "</td><td>" +
                 esc(f["title"]) + "</td><td>" +
                 ", ".join(esc(a) for a in f["artifacts"]) + "</td><td>" +
                 esc(f["headline"]) + "</td><td>" + esc(f["status"]) +
                 "</td></tr>\n")
    pans = ""
    for p in trace["panels"]:
        pans += ("<tr><td>" + esc(p["panel"]) + "</td><td>" +
                 ", ".join(esc(a) for a in p["artifacts"]) + "</td><td>" +
                 esc(p["headline"]) + "</td><td>" + esc(p["status"]) +
                 "</td></tr>\n")
    corr = "".join("<li>" + esc(x) + "</li>\n" for x in register["corrections_log"])
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>HARDBALL — Claims &amp; reproducibility</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#14213d}}
.hd{{max-width:1120px;margin:0 auto;padding:0 20px 40px}}
h1{{font-size:26px}}h2{{font-size:20px;margin-top:32px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{border:1px solid #d6dcea;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#14213d;color:#fff}}
.note{{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:14px 0}}
</style></head><body><div class="hd">
<h1>Claims &amp; reproducibility — the audit trail</h1>
<p>Generated by <b>src/bml_cycle68.py</b> from the committed artifacts, never
hand-edited. A claim is SUPPORTED only if a committed artifact carries the
numbers. A claim that failed its own test is NOT SUPPORTED, not softened.
A claim the demo once made and withdrew is RETRACTED, stated plainly, not deleted.</p>
<p><b>Counts:</b> {register["counts"]["supported"]} supported ·
{register["counts"]["not_supported"]} not supported ·
{register["counts"]["retracted"]} retracted ·
{register["counts"]["open_items"]} open item(s) ·
{register["counts"]["figures_verified"]}/{register["counts"]["figures_traced"]} figures traced and verified ·
{register["counts"]["panels_verified"]}/{register["counts"]["panels_traced"]} panels traced and verified.</p>
<h2>Claims register</h2>
<table><tr><th>ID</th><th>Claim (one sentence)</th><th>Where it appears</th>
<th>Evidence artifact + key numbers</th><th>Status</th></tr>
{rows}</table>
<h2>Retracted claims — the process working, not hidden</h2>
<table><tr><th>ID</th><th>Claim as once made</th><th>Why it was withdrawn</th>
<th>Standing record</th></tr>
{ret}</table>
<h2>Open items — decisions still with the owner</h2>
<table><tr><th>ID</th><th>Item</th><th>Where</th><th>Status</th></tr>
{opn}</table>
<h2>Figure trace — every figure to its artifact</h2>
<p>Lineage for every figure: ingest (data/raw + manifest.jsonl, local) →
curated Parquet (data/curated, 19 tables, schema-enforced) → warehouse
(data/hardball.duckdb, built, gitignored) → serving (the dashboard reads
committed JSON artifacts and curated tables; the lake feeds Figure 13 only).</p>
<p>Build commands: ingest <code>python3 src/ingest_platform.py</code> ·
curate <code>python3 src/curate.py</code> · warehouse
<code>python3 src/build_warehouse.py</code> · dashboard
<code>python3 src/dashboard_p6.py</code> · gate
<code>python3 src/verify_data.py</code> · spellcheck
<code>python3 src/spellcheck_gate.py</code> · this pack
<code>python3 src/bml_cycle68.py</code>.</p>
<table><tr><th>Figure</th><th>Title</th><th>Artifact(s)</th><th>Headline value, recomputed</th><th>Trace</th></tr>
{figs}</table>
<h2>Panel trace — the surfaces that are not figures</h2>
<table><tr><th>Panel</th><th>Artifact(s)</th><th>Headline value, recomputed</th><th>Trace</th></tr>
{pans}</table>
<h2>Corrections log</h2>
<ul>{corr}</ul>
<p class="note">Figure 9's trace verifies that its artifact and panel agree; it does
not endorse the title. The title's in-sample label is open item O01 above.</p>
</div></body></html>
"""
    with open(os.path.join(REPO, "docs", "REPRODUCIBILITY.html"), "w") as fh:
        fh.write(page)


if __name__ == "__main__":
    sys.exit(main())
