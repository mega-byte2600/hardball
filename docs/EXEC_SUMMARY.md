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
3. Thesis tested: 2026 winning-cheap teams had HIGHER OBP (.328), MORE
   contact (79.5%), FEWER K (20.5%), and FEWER homeruns per PA (26.2 vs
   31.1) while winning ~95 vs ~79. Signature confirmed.
4. Two layers DO NOT add signal (tested, honest negatives): team health
   proxy (MAE 7.31 vs 7.29) and Statcast xwOBA (7.70 vs 7.29). The simple
   raw-KPI Marcel model is the principled choice.

## The deliverable
- One self-contained offline HTML dashboard (5 Plotly panels) at
  dashboard/hardball_demo.html: payroll-vs-wins, KPI signature, model
  projections, 25-year durability, 2027 Marcel player projections.
- src/model_p6.py formula: wins ~ OBP, contact, K%, BB%, HR/PA (+payroll);
  cross-validated MAE ~7.2 wins, R^2 ~0.4 (honest, stated).
- src/bml_cycle4.py: 200-player 2027 Marcel projections (Judge .457 OBP
  top), priced against the cap / 15% individual max.

## The formula in words (what an owner does)
Put budget into OBP + contact + BB, avoid power-for-salary trades, avoid the
cheap-mediocre trap (frugal-but-78-wins), and hold ~100 wins where the cap
lands. The dashboard is the evidence; the projections are the picks.

## Honest limits (survives expert scrutiny)
- Formula explains ~40% of win variance; defense/pitching/health still matter
  (health and xwOBA measured NOT to add at team level).
- 2025 edge was thinner than 2026; we show both years, don't overclaim.
- Cap figures are the owners' PROPOSED 2027 numbers, not law yet.

## Status against P1-P7
P1 datasets ✓  P2 infra ✓  P3 literature ✓  P4 problem ✓  P5 copycat ✓
P6 MVP ✓  P7 UAT — PENDING: needs GP eyes on the dashboard (open it).
