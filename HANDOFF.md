# HANDOFF — toby/carpe-data (PR #2, stacked on PR #1)

CarpeData pass for HARDBALL, 2026-10-31: every open/free endpoint hooked
up, every source tested before it was trusted, everything traced to its
source on the dashboard. **Stacked on `toby/audit-p0-fixes` (PR #1)** —
merge PR #1 first; this branch then fast-forwards cleanly.

Full kept/dropped/unavailable scorecard: `docs/CARPE_SCORECARD.md`.
Cycle write-ups: `docs/BML_LOG.md` (Cycles 20–23).

## What shipped

1. **Connector + snapshots** (`src/carpe.py`): Savant expected/batted-ball/
   bat-tracking/sprint/arm, FanGraphs Steamer (bat+pit), MLB people ages,
   Steamer-based ID crosswalk (379/379 lake players). Lake extended to
   2023–2026 (local artifact; snapshots are what's committed).
   - Trap found + fixed: Savant's bat-tracking `?year=` form silently
     returns the current season for every year. Only the date-range form
     works; 2023 doesn't exist (Hawk-Eye starts 2024).
2. **Cycle 21 — Marcel backtest → method adopted.** 3-season window was a
   wash vs 2-season; the cross-fitted age term improved OOS MAE both
   directions (pooled OBP .0226→.0220, SLG .0468→.0453). `bml_cycle4.py`
   now: explicit window {2026:5, 2025:4, 2024:3} + fitted age slopes
   (OBP .00158 / SLG .00390 per yr from 27; the old aging step was a dead
   stub). Cascade regenerated: 201 hitters (+Profar), Judge .457→.444.
   `bml_cycle11.py` pinned to its explicit 2-season window (pitcher
   3-season/age untested) — rerun verified **byte-identical**.
3. **Cycle 20 — Savant tested, honestly rejected as projection inputs.**
   xwOBA is the better input (Q1, all 3 pairs); traits are ultra-stable
   (bat speed YoY r .92) yet every adjustment family failed the
   both-directions OOS rule. Nothing adopted; Savant ships as diagnostics.
4. **Cycle 22 — Steamer benchmark.** Hitters: OBP r=.889, MAD=.010,
   top-25 overlap 18/25 (pre-adoption: .856 / 15 — the age term closed
   real gap). Pitchers: ERA bias **−0.324** vs Steamer — pitcher Marcel
   runs optimistic; disclosed on the dashboard, open item. ZiPS returned
   empty via the API; not included, not claimed.
5. **Cycle 23 — MiLB pipeline index.** AAA/AA under-26 depth by org
   (real birthdates, fail-closed): STL 151, CLE 143, MIL 127; TB #7 —
   all three winning-cheap orgs top-7. Limitations in JSON metadata.
6. **Dashboard 10 → 13 panels** (benchmark scatter, trait check,
   pipeline), sources box updated per-panel provenance. Clean-clone
   offline build re-verified: 13 panels, no lake, network blocked,
   ~4.95 MB self-contained HTML.

## Reviewer notes

- `requirements.txt` (from PR #1) does not pin `savant-extras` — it was
  used only to discover the correct bat-tracking URL form; `carpe.py`
  itself depends only on requests/pandas already in the stack.
- Projections changed on purpose (Cycle 21 adoption). Every downstream
  artifact (health, roster, benchmark) was regenerated in the same pass.
- Not in scope here (still open from the audit): G6–G11 minus G5.
  The pitcher-optimism bias is the natural next cycle.
