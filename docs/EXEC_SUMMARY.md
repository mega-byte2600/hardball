# HARDBALL — Executive Summary
*Private delivery · Cap-Era Moneyball · Winter Meetings 2026 (Dec 6-11) · target ready: **Dec 3, 2026***
*CBA expires Dec 1, 2026; owners' proposed 2027 hard cap $245.3M / floor $171.2M. Real data only, no invented numbers.*

## The question
A team cannot out-spend the field under a hard salary cap. So: **how does a
team win at a mid-tier, cap-constrained payroll?** The answer is the competent
use of scarce dollars — the observable edge is measurable and proven below.

## The one-line thesis (measured, not asserted)
**Buy the persistent inputs — contact and walk discipline — and control-walking
arms; do not pay for noisy power output.** A player's core skills carry
year-to-year; OBP/BA are BABIP-luck and do not. Winning-cheap teams (MIL/TB/CLE)
over-index on exactly these inputs and win ~95 games at roughly a third to a
quarter of the big-market payroll.

## What the data provably supports
- **Skills persist; outputs do not.** Contact rate persists year-over-year at
  **pooled r = 0.84 (95% CI 0.78-0.88)**, walk discipline r = 0.66; OBP (the
  output) is noisy at r = 0.30. Buying a player's contact/walk skill is buying
  something that carries.
- **Run differential and wins move together**, but only as a same-year
  diagnostic (R² ≈ 0.55), not a forward forecast. We do not overclaim.
- **Cap reality is concrete.** On 2026 payrolls, 7 teams exceed the proposed
  cap and must cut (NYM 29%, LAD 28%, NYY 20%); 15 sit under the floor and must
  add — led by CLE ($96.7M) and TB ($75.6M), the disciplined winners the system
  is now forced to fund.

## What we deliberately do NOT claim (honesty)
Cross-year *team* win forecasting is weak — MAE ≈ 9-13 wins, barely better than
defaulting to the league average. We do not sell a team-wins formula. WAR is
proprietary and absent from public sports APIs; we surface its reproducible
inputs (wOBA, wRC+, FIP, K-BB%) instead of faking it.

## The deliverable
A 22-figure dashboard (offline, self-contained) + a Python-first repo where
every number traces to a public source. Every build is logged in BML_LOG.md.

## The thesis in words (what an owner does)
Buy the PERSISTENT INPUTS (contact %, walk discipline) and control-walking
arms, not noisy power output. These inputs carry year to year and are exactly
what winning-cheap teams over-index on. Price the roster against the cap.

## Honest limits (survives expert scrutiny)
- Cross-year TEAM win forecasting is weak (MAE 9-13); we say so on the page.
- Cap figures are the owners' PROPOSED 2027 numbers, not law yet.
- WAR and defensive value are proprietary/absent from public APIs; we surface
  their reproducible inputs (wOBA/wRC+/FIP/K-BB%) rather than fabricating them.

## Status against P1-P7
P1 datasets ✓  P2 infra ✓  P3 literature ✓  P4 problem ✓  P5 copycat ✓
P6 MVP ✓  P7 UAT — PENDING until the GP accepts (open the dashboard).

## Readiness
Target **Dec 3, 2026** for final UAT and handoff. Preliminary MVP UAT approved;
final polish in progress.

## Integration addendum (2026-10-31)
The parallel CarpeData/Boardroom lane (audit G1–G12, Cycles 20–26
toby-series) merged with this line of work via PR #6. Net additions:
Steamer-benchmarked Marcel projections with fitted age terms (hitter
OBP agreement r = .889; pitcher bias corrected −0.324 → −0.250 ERA),
real Spotrac salaries + the 2027 FA shopping list, the MiLB pipeline
index, and the Boardroom panels (animated payroll film, pick-your-team
explorer, budget-scenario rosters: a floor-budget FA build captures
~80% of a cap-budget build's WAR). Dashboard: 22 figures. P7 UAT was
approved at MVP level by the owner on 2026-10-31.
