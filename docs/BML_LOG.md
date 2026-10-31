# HARDBALL — Autonomous BML Log (working while GP signed off)

Each entry = one small Build-Measure-Learn cycle: what I built, what I
measured, what I learned, and where it shipped (commit). Everything below is
verified by a real command run, not self-asserted. GP review pending on all.

## Cycle 0 — poka-yoke bottom line
- Built: green "BOTTOM LINE (read this first)" box showing the takeaway +
  the single owner action (buy contact/OBP, not power) + why to trust it.
- Shipped: commit 671c824.
- Learn: dashboard had charts but no chart-agnostic takeaway; a non-expert
  could misread it. Fixed.

---
## Cycle 1 — is winning-cheap durable or a fluke? (2000-2024, n=721)
- Built: src/bml_cycle1.py — analyzed jeremyliao0411/mlb-payroll-wins
  df_final_merged.csv (721 MLB team-seasons 2000-2024, Lahman + public payroll).
- Measured: efficiency gradient is monotonic and durable — lowest payroll
  quartile wins 152/$100M vs top quartile 63/$100M across 25 years.
  BUT cheap teams win FEWER total wins (76.1 vs 87.3) — frugality ≠ winning.
- Learned: 'wins per $100M' rewards cheap-mediocre teams, NOT genuine
  winning-cheap outliers. The MIL/TB/CLE edge (95-103 wins at low cost) sits
  ABOVE the curve and is the real target. Sharpen the demo message from
  'be efficient' to 'be efficient AND competitive-plus.'
- Shipped: src/bml_cycle1.py pushed (commit pending).

---
## Cycle 2 — does team health (injury proxy) improve the wins model? → NO (honest negative)
- Built: src/bml_cycle2.py — pulled all player transactions 2025+2026 (17,968 +
  17,188 = 35k events archived to data/raw/), built team-season health proxy
  (IL placements + rehab assignments), joined to the hitting model.
- Measured: hitting-only CV MAE 7.29 wins vs hitting+health 7.31 — essentially
  flat, slightly worse. Health added NO predictive signal at team level.
- Learned: the literature says injury matters CONTEXT-SPECIFICALLY (oblique
  hurts hitters not pitchers; labral repair kills pitcher innings) — a blunt
  team-count of IL placements washes that out. Health belongs as a PLAYER-level
  projection adjustment (weighted by position/severity/recovery), not a
  team-wins feature. This is a validated negative result (Lean: learning what
  doesn't work). Raw 35k-event transaction archive retained for future use.
- Shipped: src/bml_cycle2.py, data/health_2025_2026.json, raw transactions.

---
## Cycle 3 — does Statcast xwOBA add signal? → NO (honest negative, measured)
- Built: pulled per-player Statcast leaderboard xwOBA/xSLG (CSV) for 2025+2026,
  mapped player->team via MLB API rosters (145 and 135 qualified players
  mapped), aggregated to team-avg xwOBA -> data/statcast_team.json.
- Measured (CV MAE, win prediction): hitting-ONLY = 7.29 wins vs
  hitting+xwoba = 7.70 wins. Adding xwOBA made the model WORSE (~0.4 wins).
- Learned: matches P3 stickiness lit — xwOBA is descriptive, only marginally
  predictive of NEXT season; at team-wins level it adds no signal over raw
  OBP/contact/K%/BB%. Keeping the raw-KPI model is correct and principled.
  Raw pitch archive (statcast_2026.csv) retained for future use.
- Shipped: src/bml_cycle3.py, data/statcast_team.json, raw archive.

---
## Cycle 4 — Marcel player projection engine (the roster tool), built
- Built: src/bml_cycle4.py — next-season (2027) hitter projections from REAL
  2025+2026 lake data using the literature-validated Marcel method (simple
  weighted 3-2-1 with regression-to-mean m~300PA, mild aging toward peak).
  NOT invented math — the method our P3 literature showed competitive models
  couldn't beat.
- Measured: 200 qualified players projected; top by OBP includes Judge
  (.457), Alvarez (.432), Soto (.396), and — the thesis — winning-cheap
  contact types: Bauers-MIL .389, Hicks-TB .367, Perdomo-AZ .378,
  McGonigle-DET .376. Roiester tool priced vs cap $245.3M / individual max
  $36.8M.
- Learned: a real roster-construction tool is feasible on lake data alone;
  projections are sane (league-consistent). This is the artifact an owner
  actually uses ("build the roster around these"), turning team-level edge
  into player-level picks.
- Shipped: src/bml_cycle4.py, data/projections_2027.json.

---
## Cycle 5 — dashboard +2 panels: 25yr durability proof + 2027 projections
- Built: data/efficiency_2000_2024.csv (from Cycle 1) + data/projections_2027.json
  (from Cycle 4) wired into dashboard as panel 4 (durability, two-bar layout:
  wins/$100M AND wins by quartile) and panel 5 (2027 Marcel top-15 OBP,
  winning-cheap teams green-coded).
- Measured: VERIFIED in browser — 5 chart SVGs render, titles + data correct
  (Q1 $58M→152/$100M vs Q4 63; cheap wins per $ not wins 76 vs 87; Judge
  .457/Alvarez .432/Soto .396 top projections).
- Learned: the demo now answers "is this one lucky season?" visually (25-year
  durability) and shows the actionable artifact (player projections), keeping
  the honest caveat visible. Single offline HTML, 5 panels.
- Shipped: dashboard updated, data CSVs committed. Commit a8b5a7f (pending).

---
## Cycle 6 — pitching: do winning-cheap teams win on arms too? → YES (2026, real)
- Built: src/bml_cycle6_pitching.py — measured 2025+2026 pitching stat-lines
  (98 pitcher-seasons IP>=40) from the lake, IP-weighted, by group.
- Measured (2026): WIN_CHEAP ERA 3.29 vs 3.60 (rest of league), WHIP 1.09 vs
  1.19, BB/9 2.37 vs 2.82, K/9 ~9 (avg). The winning-cheap pitching was ELITE,
  notably low-walk — mirrors the contact/OBP identity on the arms side.
  2025: smaller edge (mostly K/9 9.22) — honest counter-evidence again.
- Learned: the winning-cheap formula is TWO halves that rhyme —
  contact/OBP bats + low-walk/prevent-run arms. And: the hitter-only model's
  R2 ceiling ~0.4 ≈ the missing pitching half of MLB wins. Building a pitching
  feature layer is the highest-value improvement to the demo (explains the
  ~60% of wins the hitters don't). GP nailed 'pitching depth is critical'.
- Shipped: src/bml_cycle6_pitching.py. NEXT: fold team pitching KPIs
  (ERA/walk/contact%) into model_p6 features and re-measure CV MAE.

---
## Cycle 7 — fold pitching into the model → MAE IMPROVES 7.29 → 6.47 (measured)
- Built: src/bml_cycle7.py — IP-weighted team pitching KPIs (ERA/WHIP/K9/BB9/HR9)
  from real lake data, joined to the hitting model.
- Measured (CV MAE, avg 25->26 and 26->25):
  hitting-only 7.29 wins | hitting+pitching 6.47 wins | pitching-only 6.94.
  Adding pitching cut MAE ~0.8 wins (~11%). Coefficients correct: p_ERA -5.87,
  p_WHIP -3.41 (lower=better -> more wins).
- Learned: pitching is the biggest real model lever — confirms Cycle 6 and
  GP's 'pitching depth is critical'. The hitting-only R2 ceiling was in part
  the missing pitching half. New deliverable formula: formula_pitching.json.
- Shipped: src/bml_cycle7.py, data/formula_pitching.json.
- NEXT: add a pitching panel + updated projections to the dashboard.

---
## Cycle 8 — pitching panel added to dashboard (6th chart)
- Built: dashboard now includes a team-pitching KPI panel (IP-weighted
  ERA / WHIP / BB9 by WIN_CHEAP vs CHEAP_MEDIOCRE vs OTHER, 2026) — the
  delivery half of the formula, complementing the hitting panels.
- Measured: VERIFIED in browser — 6 chart SVGs render; pitching axes correct
  (WIN_CHEAP lowest ERA/WHIP/BB9). Single offline HTML (4.9M) now 6 panels.
- Learned: demo tells the COMPLETE story — contact/OBP bats + low-walk arms.
  This plus cycle 7 (MAE 7.29->6.47) makes pitching a committed pillar, not a
  footnote. Next candidate: player-level health IR mask on projections
  (literature says go there, team test said no).
- Shipped: dashboard/hardball_demo.html updated.

---
## Cycle 9 — player-level health applied to 2027 projections (works)
- Built: src/bml_cycle9.py — matched per-player IL days from 35k archived
  transactions to the 200-player Marcel projections; converts IL days to a
  PA-availability penalty on projected playing time.
- Measured: 136 players had IL days; median PA penalty 5.5%; 20 players
  limited >=25%. Sane captures: Judge 180 IL days -> 253 projected PA (vs
  naive 500), Polanco 210 -> 212, Soto 40 -> 445. Byron Buxton/Royce Lewis
  (known-fragile) correctly capped.
- Learned: this is the health lever working at the level the literature
  requires (player, context-specific) — the team-level test (Cycle 2) failed
  for exactly this reason. Availability-adjusted projections are a real,
  citable upgrade over naive 500-PA. This is the health pillar as the GP
  flagged it, finally applied.
- Shipped: src/bml_cycle9.py, data/projections_2027_health.json.
- NEXT: (optional) add an availability panel to dashboard.

---
## Cycle 10 — health/availability panel (7th chart) completes the 3-pillar demo
- Built: dashboard health panel — top-10 players by IL-based PA penalty
  (Judge -49%, Polanco -58%, Buxton/Lewis capped) from real 2025-26 injury
  data (Cycle 9 output).
- Measured: VERIFIED in browser — 7 chart SVGs render. Demo now shows ALL
  THREE pillars GP flagged as key: contact/OBP bats (panels 2,5), low-walk
  arms (panel 6), availability (panel 7).
- Learned: the demo is now the complete winning-cheap formula, all derived
  from real data + literature, offline single-file, honest caveats visible.
- Shipped: dashboard/hardball_demo.html (7 panels).

---
## Cycle 11 — pitcher projections complete the roster tool (both halves)
- Built: src/bml_cycle11.py — Marcel-style 2027 pitcher projections (IP, ERA,
  WHIP, K9, BB9) from real 2025+2026 lake data with regression + IL-based IP
  availability. Outputs data/projections_2027_pitchers.json (76 pitchers).
- Measured: top projected arm is MILWAUKEE's Jacob Misiorowski (1.81 ERA,
  13.0 K/9, 0 BB/9) — a winning-cheap team carries the model's best pitcher.
  Health adjustment works on arms: Chris Sale (IL days) capped to 60 proj IP.
- Learned: roster tool now shows BOTH halves of the formula — contact/OBP
  bats + low-walk arms — plus availability. The winning-cheap edge is
  visible at player level on both sides. GP's 'pitching depth is critical'
  is now a committed, citable feature not a slogan.
- Shipped: src/bml_cycle11.py, data/projections_2027_pitchers.json.

---
## Cycle 12 — cap-constrained roster builder (the decision artifact)
- Built: src/bml_cycle12.py — assembles a 26-man winning-cheap roster (13H+13P)
  from the health-adjusted hitter + pitcher projections, priced against the
  cap ($245.3M) and 15% individual max ($36.8M). Outputs data/roster_2027.json.
- Measured: on pure talent value the roster keeps selecting winning-cheap
  players — Turang(MIL), Díaz(TB), Kwan(CLE) in bats; Misiorowski(MIL),
  Rasmussen(TB), Messick(CLE) in arms. The formula produces the roster.
- Learned: the demo now closes the full loop — data -> formula -> player picks
  -> roster under cap. HONEST LIMIT stated on output: lake has no per-player
  salaries, so this is TALENT selection under the cap constraint, not a dollar
  answer (owners price real contracts against the same numbers).
- Shipped: src/bml_cycle12.py, data/roster_2027.json.

---
## Cycle 13 — QUANT CORE (linear + logistic + sensitivity + Euler). Major win.
- Built: src/quant_core.py — the hardcore-math layer GP asked for. 1) linear
  wins model; 2) logistic (>=90-win title bar); 3) sensitivity/elasticity;
  4) Euler e as Pythag exponent + logit link. Added run differential (RS/RA
  from standings) — the previously-missing strongest lever.
- Measured (real 2025+2026, cross-validated both splits):
  raw-KPI linear: MAE 7.29, R2 0.39
  +RunDiff:       MAE 4.24, R2 0.78
  +PythE:         MAE 4.00, R2 0.80   <- about 2x better
  Logistic (>=90w, base rate 21%): AUC 0.95-0.97 on run-diff alone.
  Sensitivity (MIL profile): +5 pyth-wins -> +2.8 wins.
- Learned: run differential is THE missing lever — the old model's R2 0.39
  ceiling was exactly the run-to-win nexus it ignored. Euler is the correct
  transform for both the Pythag exponent and the logit. Next: make the
  committed production model use this, and add a runs panel to the dashboard.
- Shipped: src/quant_core.py, src/dashboard_p6.py (MLB crest + quant box +
  source footer), data/quant_core.json.

---
## Cycle 15 — RIGOROUS validation (repeated K-fold + elasticity + permutation)
- Built: src/bml_cycle15.py — repeated K-fold CV (4 folds x 20 repeats) on the
  production run-diff model; full-league elasticity; permutation importance;
  naive league-mean baseline. Real 2025+2026 only.
- Measured: repeated K-fold MAE ~4.1 wins, R2 ~0.80 (stable across 80 holds);
  beats naive league-mean baseline by ~4 wins MAE. Elasticity across all
  teams confirms run-diff/PythE biggest; permutation importance ranks
  PythE/RD and OBP top. (Full detail in data/robust_validation.json.)
- Learned: the MAE 4.0 / R2 0.80 result is ROBUST, not a lucky split; the
  model is defensible to rigorous scrutiny. Naive baseline gap proves value.
- Shipped: src/bml_cycle15.py, data/robust_validation.json, formula_prod.json.

---
(cycles appended as they complete)

---
## Cycle 18-19 — the PANEL TRUTH (honest negative, re-validated on 509 team-seasons)
- Built: src/panel_builder.py pulls 2011-2026 team hitting + standings + payroll
  from MLB Stats API (cached to data/raw/panel/, no refetch) -> data/panel_2011_2026.csv
  (509 raw rows, 450 complete).
- Cycle 18 (src/bml_cycle18_refit.py): refit the same model on 450 rows. Result:
  repeated K-fold MAE 7.69 +/- 1.25, R2 0.534. The old quoted "R2 0.80 / MAE 4.0"
  DID NOT SURVIVE the full panel — it was a favorable 2-year window. OBP coeff
  flipped NEGATIVE once more data + run-diff in model (collinearity: RD ~ contains OBP).
- Cycle 19 (src/bml_cycle19_lagged.py): the honest use-case spec — predict NEXT
  season's wins from this season's KPIs. In-sample R2 0.136; OOS forecast
  2020-2025 from <=2019 train: MAE 14.05, R2 -0.89 (WORSE than naive 9.76).
  Grouped CV: R2 -6.1, MAE 13.0 vs naive 12.7. Cross-year KPI forecasting is weak.
- LEARNED (the real finding): the contact/OBP thesis does NOT cleanly predict
  NEXT-YEAR wins. Same-year run-diff->wins is real (R2 ~0.55) but diagnostic,
  not a forward forecast. What survives is PLAYER-LEVEL acquisition (Marcel +
  injury caps -> roster), not a team-wins formula. Retracted the inflated R2 0.80
  claim from dashboard/docs. This is a proper negative result, logged honestly.
