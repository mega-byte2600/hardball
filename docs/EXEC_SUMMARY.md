# HARDBALL — One-page exec summary (ready target: Dec 3, 2026)

## The problem (why now)
The owners' proposed 2027 hard cap ($245.3M cap / $171.2M floor / 15% max per
player; CBA expires Dec 1 2026) kills the "outspend everyone" model. Winners
must build CONTACT + OBP rosters cheap enough for the middle — the Moneyball
edge moved from "buy undervalued singles" to "win while cheap, cap-constrained."

## What the real data shows (all verified, no invented numbers)
1. Durability: over 2000-2024 (721 team-seasons), low payroll quartiles win
   ~152 wins/$100M vs ~63 for the top quartile. A 25-year law, not a fluke.
2. Honest catch: cheap teams win MORE PER $, not MORE WINS (76 vs 87). The
   real edge = winning-cheap outliers (MIL/TB/CLE: 95-103 wins at 1/3-1/4 cost)
   that do BOTH.
3. 16-season panel (2011-2026, 509 team-seasons, MLB Stats API): same-year
   run-diff → wins R² ≈ 0.55 (real, but diagnostic — describes, not forecasts).
4. PLAYER-LEVEL validation (the measurable edge): input skills PERSIST
   year-to-year — contact r=0.90, walk% r=0.66, ISO r=0.58. Raw OBP is noisy
   (r=0.30). Buying persistent contact/walks is a provable edge (57% error
   reduction predicting next-year contact).
5. Honest negatives (tested, logged): team health proxy, xwOBA, and KPI-only
   CROSS-YEAR win forecasting do NOT add signal. The 2-year "R² 0.80 / MAE
   4.0" number was retracted after the 16-season panel — it was a favorable
   window. No fake confidence left.

## The deliverable
- One self-contained offline HTML dashboard (11 panels) at
  dashboard/hardball_demo.html, MLB-styled: skill persistence (edge), run-diff,
  payroll-vs-wins, KPI signature, projected wins, 25-yr durability, player
  projections, pitching, health, 2027 roster (13H+13P), sensitivity.
- src/panel_builder.py — 16-season panel; src/bml_cycle20_player.py — the
  persistence proof; src/bml_cycle12.py — 2027 roster.
- Rebuild anytime: `python src/dashboard_p6.py`.

## The thesis in words (what an owner does)
Buy the PERSISTENT INPUTS (contact %, walk discipline) and low-walk arms, not
the noisy output (OBP/BA/luck). These inputs carry year to year and are exactly
what winning-cheap teams over-index on. Price the roster against the cap.

## Honest limits (survives expert scrutiny)
- Cross-year TEAM win forecasting is weak (MAE 9-13); we say so on the page.
- Cap figures are the owners' PROPOSED 2027 numbers, not law yet.
- Player-level sample is 80 (>=200 PA both 2025+2026); a 3+ season sample
  (2023-24 backfill) would tighten it further. That is the next build.

## Status against P1-P7
P1 datasets ✓  P2 infra ✓  P3 literature ✓  P4 problem ✓  P5 copycat ✓
P6 MVP ✓  P7 UAT — PENDING until the GP accepts (open the dashboard).
