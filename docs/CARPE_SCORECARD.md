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
