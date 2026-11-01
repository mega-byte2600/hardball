# HARDBALL — Cap-Era Moneyball Decision Tool

A data-driven answer to the 2027 salary-cap question: **How does a team win
at a mid-tier, cap-constrained payroll?** Built on real MLB data, measured
honestly, no invented numbers. Ready for the Winter Meetings (target: **Dec 3,
2026**; Meetings run Dec 6-11).

## The one-line thesis (measured, not asserted)
Buy the **persistent inputs** (contact rate, walk discipline) and low-walk
arms — not the noisy output (OBP/BA). A player's contact and walk skills carry
year to year; OBP is BABIP-luck noise. Winning-cheap teams (MIL/TB/CLE)
over-index on exactly these inputs and win ~95 games at ~1/3-1/4 big-market cost.

## What you get
- **DASHBOARD** — 12 figures, self-contained offline HTML (works without
  internet at the meeting). See **How to run**.
- **Data** — 16-season team panel (2011-2026, 509 team-seasons) + player
  projections + injury/IL history. All from public APIs, cached locally.
- **Math** — linear + logistic regression, repeated K-fold validation,
  sensitivity/elasticity, run-differential (diagnostic) and value metrics
  (wOBA/wRC+/FIP/K-BB%). Honest negatives logged, nothing overclaimed.

## How to run (3 steps)
1. `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`
2. `.venv/bin/python src/dashboard_p6.py`  → rebuilds `dashboard/hardball_demo.html`
3. `open dashboard/hardball_demo.html` (or `python3 -m http.server 8893` then
   browse `http://127.0.0.1:8893/hardball_demo.html`)

## Repo layout
- `src/` — Python: data ingest, panel builder, model, value metrics, dashboard generator, BML cycles
- `data/` — real data artifacts (panel CSV, projections JSON, validation outputs)
- `docs/` — PROBLEM_P4 (cap-era framing), COPYCAT_P5 (KPI evidence), LITERATURE_SPINE,
  EXEC_SUMMARY (one-pager), BML_LOG (build-measure-learn audit trail)
- `dashboard/` — generated artifact (gitignored; rebuild from src/)

## Data sources (all real, all keyless)
- **MLB Stats API** (`statsapi.mlb.com/api/v1`) — team/player hitting, pitching, standings
- **ESPN API** — validation/redundancy (cross-checked)
- **Spotrac** (via MIT-licensed jasonbhorne/mlb-payroll) — payroll
- **MLB transactions feed** — injury/IL history (35k+ events)
- `WAR` and defensive value are **not fabricated** — they're proprietary
  (fWAR/bWAR) and absent from the API; we surface their reproducible inputs
  (wOBA/wRC+/FIP/K-BB%) and say so on the page.

## Honest limits
Cross-year TEAM win forecasting is weak (MAE 9-13 wins) and regresses to the
mean — this matches published literature and is stated on the dashboard. The
cap/floor are owners' **proposed** 2027 figures (CBA expires Dec 1 2026), not law.

Private repo. Audit trail in `docs/BML_LOG.md`.
