# HARDBALL — One-page exec summary (for the GP / Winter Meetings)

## The problem (why now)
The owners' proposed 2027 hard cap ($245.3M cap / $171.2M floor / 15% max per
player; CBA expires Dec 1 2026) kills the "outspend everyone" model. Winners
must build CONTACT + OBP rosters cheap enough for the middle — the Moneyball
edge moved from "buy undervalued singles" to "win while cheap, cap-constrained."

## What the real data shows (all verified, no invented numbers)
1. Durability: over 2000-2024 (721 team-seasons), low payroll quartiles win
   ~152 wins/$100M vs ~63 for the top quartile. The efficiency edge is a
   25-year law, not a fluke.
2. Honest catch: cheap teams win MORE PER $, not MORE WINS (76 vs 87).
   The real edge = winning-cheap outliers (MIL/TB/CLE: 95-103 wins at
   1/3-1/4 big-market cost) that do BOTH.
3. Thesis tested: 2026 winning-cheap teams had HIGHER OBP, MORE contact,
   FEWER strikeouts, and FEWER homeruns per PA while winning ~95 vs ~79.
   Signature confirmed both seasons (2025 + 2026, all 30 teams).
4. The pipeline leg (new, Cycle 23): all three winning-cheap orgs rank
   top-7 in under-26 upper-minors depth (CLE #2, MIL #3, TB #7 of 30) —
   the cheap wins are fed by near-MLB talent pipelines, not luck.
5. Tested and REJECTED, honestly: team health proxy and team-level xwOBA
   add no signal (Cycles 2-3); Savant trait adjustments (bat speed,
   barrels) make player projections worse out-of-sample despite bat
   speed being the most stable trait in the data (Cycle 20); a
   team-wins forward formula does not survive the 2011-2026 panel
   (Cycles 18-19 — an earlier MAE 4.0 / R² 0.80 claim was retracted).

## The deliverable
- One self-contained offline HTML dashboard — **14 Plotly panels** at
  dashboard/hardball_demo.html: payroll-vs-wins, KPI signature, cap
  projections, 25-year durability, player projections, pitching, health,
  the 26-man cap roster, run differential, sensitivity — plus a
  Marcel-vs-Steamer benchmark, a Savant trait check, the MiLB pipeline
  index, and a 2027 free-agent shopping list. Builds from a clean clone
  with no network and no database (verified).
- Player projections are the product: backtested Marcel (3 seasons,
  5-4-3, regression + age terms fitted on backtest residuals — Cycles
  21/24), 201 hitters + 102 pitchers, health-capped, priced against
  the cap with real Spotrac salaries and the real 2027 FA class.
- Benchmarked, not just asserted: hitter projections agree with
  FanGraphs Steamer at r = .889 (OBP); the pitcher side's residual
  optimism vs Steamer (−0.25 ERA after the Cycle 24 fix) is printed
  on the dashboard, not buried.

## The formula in words (what an owner does)
Put budget into OBP + contact + BB and low-walk arms, feed it from your
own under-26 pipeline, shop the FA value list (projected WAR per dollar
of prior contract), avoid power-for-salary trades and the cheap-mediocre
trap (frugal-but-78-wins), and hold ~95 wins where the cap lands.

## Honest limits (survives expert scrutiny)
- Same-year run differential → wins is real (R² ≈ 0.55) but diagnostic,
  not a forecast; KPI-only next-year win forecasting is weak (panel
  OOS MAE ≈ 14 wins, worse than naive) and is not claimed.
- ~45% of win variance sits outside the formula (defense, luck,
  leverage) — stated on the dashboard.
- FA "prices" are prior-contract AAVs (last-price anchors), not
  predicted 2027 salaries. Salary coverage: 24/30 Spotrac team pages
  (6 rate-limited at pull time, logged; rerun completes them).
- Cap figures are the owners' PROPOSED 2027 numbers, not law yet.

## Status against P1-P7
P1 datasets ✓  P2 infra ✓  P3 literature ✓  P4 problem ✓  P5 copycat ✓
P6 MVP ✓  P7 UAT ✓ — MVP UAT approved by the owner 2026-10-31 (scoped
to the MVP demo; PR merges remain a separate owner decision).
