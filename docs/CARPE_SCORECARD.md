# CarpeData scorecard — HARDBALL (2026-10-31)

Every open/free source we tried for the CarpeData pass, what happened,
and the decision. Rule: paywalled/licensed sources are noted as gaps,
never pirated; a source joins the model only by passing a measured
BML cycle, not by being available.

Connector: `src/carpe.py` (keyless throughout). Snapshots committed
under `data/`; raw payloads archived under `data/raw/` (gitignored).

## KEPT — connected and in use

| Source | Endpoint form | Used for |
|---|---|---|
| MLB Stats API — historical seasons | `/stats` qualified leaders, 2023+2024 | Extended the lake 2023–2026 → enabled the Cycle 21 Marcel backtest |
| MLB Stats API — people | `/people?personIds=` batched | Real birthdates/ages for all 379 lake players (`player_ages.json`) |
| MLB Stats API — minors | `/teams?sportId=11/12`, `/stats` per affiliate | Cycle 23 pipeline index (AAA/AA under-26 depth, 30 orgs) |
| Baseball Savant — expected stats | `/expected_statistics?...&csv=true` 2023–2026 | Cycle 20 Q1: xwOBA beats actual wOBA as next-year input (all 3 pairs) |
| Baseball Savant — batted ball | `/statcast_leaderboard?...&csv=true` 2023–2026 | EV/barrels/sweet-spot; Cycle 20 Q2/Q3 |
| Baseball Savant — bat tracking | `/leaderboard/bat-tracking?dateStart=…&dateEnd=…&seasonStart=…&type=batter&csv=true` 2024–2026 | Bat speed/squared-up/blasts; Cycle 20 Q2/Q3. **Trap:** the bare `?year=` form silently ignores the year and returns the current season for every request (verified byte-identical) — only the date-range form works. No 2023 data exists (Hawk-Eye starts 2024) |
| Baseball Savant — sprint speed | `/leaderboard/sprint_speed?...&csv=true` 2023–2026 | Snapshot in repo; no cycle has needed it yet |
| Baseball Savant — arm strength | `/leaderboard/arm-strength?...&csv=true` 2026 | Snapshot in repo; fielding context, unused by cycles so far |
| FanGraphs API — Steamer projections | `/api/projections?type=steamer` (bat + pit) | Cycle 22 benchmark (Marcel vs Steamer) + WAR context |
| FanGraphs — player crosswalk | Steamer rows carry `xMLBAMID` + `playerid` | `player_xwalk.json`: covers 379/379 lake players; all CarpeData joins are by ID |

## TESTED AND DROPPED (measured, not vibes)

| Candidate | Result |
|---|---|
| Savant traits as Marcel adjustments (Cycle 20) | Bat speed is the most stable trait in the data (YoY r ≈ .92) and still made projections **worse** out-of-sample in both directions on both metrics. Barrels/squared-up/xwOBA-luck: splits or rounding-level gains. Nothing adopted; Savant stays as diagnostics/context |
| 2-season Marcel (Cycle 21) | Superseded: 3-season window ties it on accuracy, wins on coverage/fidelity; age term fitted on backtest residuals improved OOS MAE both directions (OBP .0226→.0220, SLG .0468→.0453 pooled) and was adopted |
| Name-string player joins | Replaced everywhere in CarpeData work by MLBAM-ID joins (the AZ/ARI and walks bugs were this failure class) |

## TRIED, UNAVAILABLE OR REDUNDANT (logged gaps)

| Source | Status |
|---|---|
| FanGraphs ZiPS projections | API returned an empty set on 2026-10-31. Not in the benchmark; Steamer only, labeled as such |
| Chadwick register flat file | `people.csv` 404s at its historical path. Redundant: the Steamer crosswalk covers our whole universe |
| Lahman / baseballdatabank | Repo paths restructured (404). Redundant: the MLB API itself supplies the 2023/2024 history we needed, single-source consistent with the lake |
| FanGraphs leaders endpoint (for crosswalk) | Works but paginates at 50 rows — a 1,000-row page request silently returns a subset (caught: only 30 of 379 players matched). Superseded by the Steamer crosswalk |
| Full pitch-level Statcast lake | Feasible but heavy (~25k-row response caps, ~17 MB per two weeks of games). Leaderboard-level Savant data answered every question this demo asks; the full lake is a post-Dec-1 build if a question ever needs pitch-level granularity |
| Spotrac live payroll API | No public API. Payroll stays the committed dated snapshots (already a G11 hygiene item), not a brittle scrape |
| Stathead / Inside Edge / sportsbook odds | Paid or key-gated. Noted as gaps per the rule; odds, if ever used, would be a labeled feature, never a label |

## Addendum — solutions pass (2026-10-31)

| Source | Status |
|---|---|
| Spotrac team payroll pages (per-player 2026 salaries) | KEPT with a caveat: 24/30 teams pulled (927 rows) before Spotrac rate-limited the pull (500s, then 403 — requests stopped, per policy, not routed around). Missing: ARI, BOS, CHC, MIL, TB, TEX. `bml_cycle25.py` caches successes, so any later rerun fetches only the missing six |
| Spotrac 2027 free-agents page | KEPT: full class (251 players) in one pull, before the rate limit |
| USA TODAY salary database | TRIED, BLOCKED: HTTP 402 access restricted. Logged, not circumvented |

---
## FULL VERIFICATION PASS — 2026-10-31 (post-merge, against main adbe2077)

Every source re-checked live or by independent recomputation. Verdicts:

| Source | Verdict | Evidence |
|---|---|---|
| MLB Stats API (KPI/standings/panel) | VERIFIED LIVE | All 30 teams' 2026 wins match live standings exactly (incl. D-backs 86, White Sox 84). Sampled team stats recomputed from the API match snapshots to the digit (MIL/NYY/CLE: OBP, HR, PA all exact). Panel: 509 rows / 16 seasons; the 59 payroll-incomplete rows are the documented 509-vs-450 gap, not corruption |
| Baseball Savant snapshots | VERIFIED LIVE | Live 2026 expected-stats pull compared player-by-player: 246 players, ZERO xwOBA differences > .002 vs the committed snapshot. Bat-tracking files for 2024/2025/2026 are byte-distinct (the silent-year trap from the first pull is absent). All 16 snapshot files present, counts sane (246–673 rows) |
| FanGraphs Steamer + crosswalk | VERIFIED | Crosswalk 379 entries; benchmark joins 201/201 Marcel hitters by MLBAM ID (unmatched: none); OBP r = .889 consistent between raw Steamer files and the benchmark artifact |
| ESPN cross-validation | VERIFIED (nuance) | HR counts match exactly for all 254 compared players (131 in 2025 + 123 in 2026) — the dashboard claim is HR-specific and true. The files' "mismatches: 2" per year are AVG differences of ≤ .002 on 2 players (non-HR field, scoring/rounding class), recorded here so the headline count is never misread |
| Spotrac payroll / W-L (payroll.py) | VERIFIED LIVE | All 30 records re-checked against live MLB API standings: no mismatches (the 161-game NYY/BAL totals are real) |
| Spotrac per-player salaries | STILL BLOCKED (24/30) | Completion rerun attempted 2026-10-31 ~19:45 PT — Spotrac still refusing the same 6 team pages (ARI/BOS/CHC/MIL/TB/TEX). Requests stopped, not routed around. Coverage is labeled 24/30 in the data metadata, the dashboard source box, and the release notes. `bml_cycle25.py` completes it on any later successful run (cache-aware). The FA class itself is complete: 251 players, 231 with Steamer WAR |
| MiLB pipeline (MLB minors) | VERIFIED (internal) | 30 orgs, ranks 1–30 unique, index mean exactly 100.0 by construction check, no top-hitter aged ≥26 (under-26 rule holds in the output) |
| Lake (local build artifact) | VERIFIED (local) | stat_lines 2023–2026 (743 rows), players registry 379 = crosswalk size. The 2022 backfill lives in the main lane's environment; ingest/backfill scripts regenerate the lake |
| Derived artifacts | VERIFIED | Projections 201 hitters / 102 pitchers; formula_prod.json carries the DIAGNOSTIC ONLY annotation on main; lagged_forecast.json carries the G6 exclusion (grouped MAE 10.23); efficiency file = 721 data rows (the 25-year claim); wow_scenarios constraints hold (26 men, spend ≤ budget at all three budgets) |
| Dashboard (from main) | VERIFIED | Fresh main tarball builds offline: 19 figures without the local lake (pitching omits gracefully), 20 with it; output byte-size identical to the integrated build (deterministic) |
