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
- **Skills persist more than outputs.** Contact rate persists year-over-year at
  **pooled r = 0.84 (95% CI 0.81-0.87)**, walk discipline at r = 0.66-0.77 in
  every season pair;
  OBP (the output) persists more weakly at pooled r = 0.53, and only 0.30 in
  the latest pair. Buying a player's contact/walk skill is buying something
  that carries further.
- **Run differential and wins move together**, but only as a same-year
  diagnostic (R² ≈ 0.55), not a forward forecast. We do not overclaim.
- **Cap reality is concrete.** On 2026 payrolls, 7 teams exceed the proposed
  cap and must cut (NYM 29%, LAD 28%, NYY 20%); 15 sit under the floor and must
  add — led by CLE ($96.7M) and TB ($75.6M), the disciplined winners the system
  is now forced to fund.

## What we deliberately do NOT claim (honesty)
Cross-year *team* win forecasting is weak — MAE ≈ 9-13 wins, barely better than
defaulting to the league average. We do not sell a team-wins formula. WAR is
published free (fWAR/bWAR) but the formulas disagree and no MLB API returns it;
we surface its reproducible inputs (wOBA, wRC+, FIP, K-BB%) instead of inventing one.
**We do not claim the market misprices contact/OBP.** We ran our own
Hakes–Sauer pricing test (Cycles 46/48, Figure 24): with a run-value benchmark
derived from 480 team-seasons, the formal proportionality test is inconclusive
at current samples (n = 60 / 82) — it can neither confirm correct pricing nor
rule mispricing out. The descriptive contrast (top-quartile contact hitters at
about half the bottom quartile's median $/WAR, on both salary bases) is labeled
a contrast, not a price effect. The claim is persistence + cap-efficiency.
**The scenario rosters are proven-optimal builds, and we say what
"optimal" rests on.** An exact optimizer (Cycle 49, Figure 25) solves the
roster problem — same FA pool, Steamer WAR, prior-AAV anchors and quotas —
and proves its optima: 48.9 / 52.8 / 54.8 WAR at the floor / middle / cap
budgets, against the original greedy builds' 42.0 / 45.7 / 52.3. With the
owner's approval (Cycle 52) the optimizer rosters are the headline and
the greedy builds remain in Figure 25 as the benchmark. The headline WAR
always travels with its robustness range (Cycle 50): across ±20% price
error the floor build holds 45.0–53.2 WAR. It also travels with a
delivered-WAR range (Cycle 56, UNC-2): a Monte Carlo over measured
projection error and player availability puts the floor at a median
39.8 WAR (10th–90th: 33.0–46.9) and the cap at 44.9 (37.6–52.4) — the
points are full-availability projections; delivered WAR runs lower
and wider. Optimal means optimal under
the stated inputs — Steamer WAR and last-price anchors, not predicted
2027 salaries — and both builds satisfy every proposed constraint,
including the 15% per-player maximum, which binds nobody in this class.

## The deliverable
A 25-figure dashboard (offline, self-contained) + a Python-first repo where
every number traces to a public source. Every build is logged in BML_LOG.md.

## The thesis in words (what an owner does)
Buy the PERSISTENT INPUTS (contact %, walk discipline) and control-walking
arms, not noisy power output. These inputs carry year to year and are exactly
what winning-cheap teams over-index on. Price the roster against the cap.

## Honest limits (survives expert scrutiny)
- Cross-year TEAM win forecasting is weak (MAE 9-13); we say so on the page.
- Cap figures are the owners' PROPOSED 2027 numbers, not law yet.
- WAR is published free (fWAR/bWAR) but the two formulas disagree and no MLB API
  returns it; we surface its reproducible inputs (wOBA/wRC+/FIP/K-BB%) rather than inventing one.

## Status against P1-P7
P1 datasets ✓  P2 infra ✓  P3 literature ✓  P4 problem ✓  P5 copycat ✓
P6 MVP ✓  P7 UAT — approved at MVP level by the owner 2026-10-31 (MVP scope only).

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
~80% of a cap-budget build's WAR). Dashboard: 23 figures (Figure 23, Cycle 34,
Explorer-only: the posted NPB class from official BIS data). P7 UAT was
approved at MVP level by the owner on 2026-10-31.

## Cycle 52 addendum (2026-11-02)
The scenario rosters are now the proven-optimal builds (Cycle 49,
promoted with the owner's approval): floor 48.9 WAR, middle 52.8,
cap 54.8 — the floor build captures ~89% of the cap build's WAR. The
greedy builds remain as the Figure 25 benchmark. Dashboard: 25 figures.

## Cycle 56 addendum (2026-11-02)
UNC-2, the uncertainty layer, is shipped — the final increment of the
MIT-gap programme. Every headline scenario number now carries a
delivered-WAR range beside its price-error range: floor 48.9 WAR,
10th–90th 33.0–46.9 (median 39.8); middle 52.8, 36.0–50.7 (43.2);
cap 54.8, 37.6–52.4 (44.9). Method: seeded Monte Carlo (20,000 draws)
over the repo's measured Marcel-backtest residuals (hitters n=196,
pitchers n=59) and the measured 2025–26 availability pools (hitters
n=201, pitchers n=102). The medians sit below the points by the
measured availability level effect plus the backtest pools' measured
optimism (SLG and ERA bias); the points are unchanged. Artifact:
data/uncertainty_scenarios_2027.json. Dashboard: 25 figures.
