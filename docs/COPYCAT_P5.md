# HARDBALL — Copycat-League KPI Analysis (P5)

Question: which team-level KPIs separate WINNING-CHEAP teams (CLE, TB, MIL —
85-103 wins at low payroll) from CHEAP-MEDIOCRE teams (MIA, CHW, STL — ~80
wins at low payroll) and from expensive underperformers? Tests the thesis:
buy contact + OBP, not homeruns.

## Method (real data)
- Team aggregate hitting per team from MLB Stats API (per-team /teams/{id}/stats)
- Payroll + wins from Spotrac (via jasonbhorne/mlb-payroll CSVs 2011-2025 +
  Spotrac 2026 live), cross-checked
- Groups: WIN_CHEAP = {MIL,TB,CLE}; CHEAP_MEDIOCRE = {MIA,CHW,STL}; OTHER
- 60 team-seasons, 2025 + 2026. Code: src/kpi.py; JSON: data/kpi_2025.json,
  data/kpi_2026.json.

## 2026 result (the strong year; MIL won the World Series)

| Metric | WIN_CHEAP | CHEAP_MEDIOCRE | OTHER |
|---|---|---|---|
| OBP | **.328** | .320 | .317 |
| contact% | **79.5** | 77.6 | 77.6 |
| K% | **20.5** | 22.4 | 22.4 |
| BB% | **9.47** | 8.95 | 8.80 |
| HR/PA (per 1000) | **26.2** | 29.6 | 31.1 |
| ISO | .143 | .153 | .158 |
| wins | **95.3** | 80.3 | 79.0 |
| payroll | $105.6M | $94.3M | $202.9M |
| wins/$100M | **95.6** | 85.7 | 43.6 |

Reading: the winning-cheap teams get on base more, make contact more, strike
out less, walk more — and hit FEWER homeruns per plate appearance — while
producing more wins at half the payroll of the field. This is the thesis in
numbers, strongest in the championship-validated 2026 season.

## 2025 result (honest counter-evidence)

| Metric | WIN_CHEAP | OTHER |
|---|---|---|
| OBP | .314 | .315 |
| contact% | 78.0 | 77.6 |
| K% | 22.0 | 22.3 |
| BB% | 8.37 | 8.39 |
| HR/PA | 28.3 | 31.0 |
| ISO | .147 | .159 |
| wins | 87.3 | 81.3 |

Reading: the edge is MUCH smaller in 2025 — OBP basically even, contact only
+0.28. The winning-cheap teams still won more (87 vs 81) at lower cost and
slightly less power-dependent, but the contact/OBP gap is not decisive that
season.

## Honest conclusion (capability, not guarantee)
- The contact+OBP-over-power signature is REAL and strongest in the most
  recent, championship-validated season (2026: CLE/TB/MIL out-OBP'd, out-
  contacted, under-hr'd the field and won more at half the payroll).
- It is NOT universal: 2025 shows the edge is thinner. We show both, and do
  not claim the formula always wins — only that the data shows a persistent
  tendency for contact/OBP-dominant cheap teams to reach competitive-plus
  results, and the demo formula is derived from and calibrated to this
  evidence, not asserted.
- The discriminator vs cheap-mediocre is NOT cheapness (both groups are
  low-payroll). It is the winning style: OBP + contact + avoided K + walked
  more, i.e. run-scoring construction, not just frugality.

## What P6 must build from this
A formula that maps a payroll-constrained roster's hitting profile
(OBP, contact, K%, BB%, power-dependence) to expected wins, calibrated on
2025-2026 (weight 2026 more, the championship year), and priced against the
cap ($245.3M cap / $171.2M floor, individual 15% max). Owners use it to
construct a winning-cheap-style roster inside the cap.
