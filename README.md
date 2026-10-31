# HARDBALL — Cap-Era Moneyball

An MLB 2027 prediction demo for the December 1 Winter Meetings: under the
owners' proposed 2027 hard cap ($245.3M cap / $171.2M floor / 15% per-player
max; CBA expires Dec 1, 2026), how does a mid-payroll team win? Thesis,
tested on real data: **contact + OBP bats, low-walk arms, availability,
and an under-26 pipeline** — priced against the cap.

## Open the demo (30 seconds, offline)

```bash
pip install -r requirements.txt
python src/dashboard_p6.py
open dashboard/hardball_demo.html
```

The build works from a clean clone with **no network and no database**:
every panel reads committed snapshots under `data/`. The result is one
self-contained HTML file (14 interactive Plotly panels) — the file you
can open on a plane to the Winter Meetings.

## What you're looking at

- **The evidence**: payroll-vs-wins, the winning-cheap KPI signature
  (MIL/TB/CLE vs the league, both seasons, all 30 teams), 25-year
  durability of the efficiency edge, run differential, sensitivity.
- **The product**: player-level Marcel projections (201 hitters, 102
  pitchers) with injury-availability caps → a 26-man cap roster.
  The Marcel is backtested, not asserted: 3-season 5-4-3 weights +
  age adjustments whose slopes were fitted on 2025/2026 backtest
  residuals (Cycles 21/24).
- **The benchmark**: our projections vs FanGraphs Steamer 2027,
  joined by player ID (hitter OBP r = .889). The pitcher side's
  residual optimism is printed on the panel.
- **The pipeline**: under-26 AAA/AA depth index for all 30 orgs —
  the winning-cheap three all rank top-7 (Cycle 23).
- **The shopping list**: the real 2027 free-agent class (Spotrac)
  with Steamer WAR and prior-contract AAV as a labeled last-price
  anchor (Cycle 25).

## Honesty rules this repo runs on

- Real data only; a panel with no data says so. Hypotheticals are
  labeled hypothetical.
- Every model claim was tested out-of-sample before it shipped, and
  the failures are in the log, not deleted: the R² 0.80 team-wins
  claim was **retracted** (Cycles 18-19), Savant trait adjustments
  were **rejected** (Cycle 20), team health/xwOBA were **rejected**
  (Cycles 2-3). Read `docs/BML_LOG.md` — it's the audit trail.
- Joins are by MLBAM player_id, never by name string.

## Data sources (all keyless)

MLB Stats API (stats, transactions, minors, people) · Baseball Savant
leaderboards (xwOBA, EV/barrels, bat tracking, sprint, arm strength) ·
FanGraphs API (Steamer projections + ID crosswalk) · Spotrac (payroll,
salaries, FA class) · ESPN (cross-validation). Connector:
`src/carpe.py`. Kept/dropped/unavailable per source:
`docs/CARPE_SCORECARD.md`.

## Repo map

- `src/dashboard_p6.py` — the demo build (start here)
- `src/bml_cycle*.py` — the measured research cycles (see BML_LOG)
- `src/carpe.py` — data connectors + snapshot refresh
- `src/ingest.py`, `src/kpi.py`, `src/model_p6.py` — lake + KPI + panel model
- `data/` — committed snapshots every panel reads
- `docs/` — BML_LOG (audit trail), EXEC_SUMMARY (one-pager),
  LITERATURE_SPINE, PROBLEM_P4, COPYCAT_P5, CARPE_SCORECARD

## Status

P1–P6 complete; CarpeData + solutions passes shipped as stacked PRs
(#1 audit fixes, #2 CarpeData, #3 solutions). P7 = GP review of the
dashboard. Deadline: December 1, 2026.
