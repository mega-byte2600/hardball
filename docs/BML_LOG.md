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

---
## Cycle 20 — PLAYER-LEVEL validation: the dependable edge (measured)
- Built: src/bml_cycle20_player.py — test 80 real players w/ >=200 PA both
  seasons whether SKILL persists year-over-year (2025->2026).
- Measured: within-player r = Contact 0.899, BB% 0.655, ISO 0.584, OBP 0.298.
  Predicting next-year contact% from own prior: MAE 2.12 vs naive 4.97
  = 57% error reduction, R2 0.81. OBP itself is noisy (beats naive by 1pt).
- LEARNED (the defensible thesis): buy the PERSISTENT INPUTS (contact +
  walk discipline), not the noisy OUTPUT (OBP/BA). Winning-cheap teams
  over-index on these exact inputs (team KPI data) AND they carry year to
  year (player data). This is the provable Moneyball edge, replacing the
  discredited team-wins formula.
- Shipped: player_level_validation.json, player_yoy.json, dashboard panel 11
  (skill persistence chart moved to first chart).

---
## Cycle 22 — 2027 CAP-SCENARIO (who the cap/floor forces to act, real 2026 payrolls)
- Built: src/bml_cycle22_cap.py -> data/cap_scenario_2027.json. Parsed the
  Spotrac 2026 PAYROLL_2026 tuples (team, record, $string).
- Measured: 7 teams OVER the proposed cap must cut -- NYM $101M (29%), LAD
  $94M (28%), NYY $63M, PHI $47M. 15 teams UNDER the floor must spend up --
  CLE $96.7M, MIA $88M, TB $75.6M are the biggest forced-adders. Winning-cheap
  CLE/TB are exactly the forced-spenders -> the floor hands disciplined
  winners $75-97M to deploy. Cap=necessity, floor=pool for the efficient.
- Shipped: dashboard Figure 13 (cap-era bar, red=over/must cut,
  green=under/gets pool). 13 figures total.

---
## Cycle 23 — PERSISTENCE WITH CONFIDENCE (bounded edge, not bare r)
- Built: src/bml_cycle23_ci.py -> data/persistence_ci.json. Bootstrap 95% CI
  on every year-over-year skill correlation, on every adjacent season pair.
- Measured: pooled contact persistence r=0.839, 95% CI [0.779, 0.883], across
  173 player-year pairs (2024-25 n=93 + 2025-26 n=80). BB r=0.71, OBP r=0.58
  (noisy). The edge is now stated WITH its confidence bound, not as a point.
- Also: rewrote the "what the math provably supports" dashboard box from
  run-on scrawl to clean executive prose (same honest claims). New FIGURE INDEX
  box at top (all 13 charts mappable). Fixed int64 json serialization bug.
- Shipped: Figure 1 now cites pooled r=0.84 (95% CI 0.78-0.88, 173 pairs) with
  an explicit color legend. Dashboard 13 figures, 4.949MB.

---
## Cycle 24 — DEPLOY THE CAP POOL (how a forced-spender allocates the floor money)
- Built: src/bml_cycle24_deploy.py -> data/cap_pool_deployment.json. For every
  team forced up to the 2027 floor (CLE +96.7M, MIA +87.9M, TB +75.6M), split
  the pool toward where it has measured relative strength (robust-MAD z of team
  wOBA vs FIP). CLE/TB/MIL lean arms (their current edge is FIP); ATH/COL lean
  hitting.
- MEASURED-A-BUG: raw scale-split (wOBA delta / FIP delta) printed 100/0 for
  nearly everyone because the scales differ ~1000x. Fixed with MAD-robust z.
  Honest label: allocation model, NOT per-player salary (unavailable publicly).

---
## Cycle 21b — 2022 LOADED → persistence edge now 4 season pairs (~400+ players)
- The overnight backfill fetched 2022 raw data but ended before the lake upsert;
  wrote load_lake_2022.py to idempotently upsert cached 2022 into the lake.
- Re-ran cycle 21 on 5 seasons (2022-2026). Multiple season pairs now, pooled
  contact persistence held stable. Figure 1 title/subtitle made dynamic on
  len(pairs) so it reads "(N real season pairs, N players)" automatically.

---
## Cycle 21 (full) — BACKFILL COMPLETE: 5-season player lake (2022-2026)
- backfill_players.py finished clean (exited 0): stored 2022=262, 2023=243,
  2024=241 hitters; 2025/2026 were already present. Lake = 1,026 player-seasons,
  457 distinct players; 179 players have >=3 hitting seasons.
- Cycle 21 re-run over ALL 4 season pairs: contact persists in EVERY pair —
  2022-23 r=0.82, 23-24 r=0.83, 24-25 r=0.77, 25-26 r=0.90. Pooled r=0.83
  over 422 player-year pairs.
- Cycle 23 (bootstrap CI) on the full set: pooled contact r=0.83,
  95% CI [0.792, 0.862], n=422 pairs. VERDICT = STABLE (r>=0.6 every pair).
- Dashboard Figure 1 is now dynamic: "4 real season pairs, 457 players" with
  per-pair bars and the CI subtitle. Centerpiece verified rendering (13 plots).
- BUG FIXED: the backfill had cached 2022 raw but ended before lake upsert;
  wrote load_lake_2022.py to upsert. Fixed int64 json serialization in
  cycle21 + cycle23.


## Cycle 25 — POKA-YOKE novice pass (GP: "someone who knows little about baseball sees and gets it")
- Root-cause fix first: every figure had the SAME crowded top strip because the shared
  `_number()` helper forced legends to y≈1.02 (above the plot, colliding title + subtitles).
  Moved ALL legends below the charts, removed floating top annotations, cut redundant
  legend rows that duplicated the global COLOR KEY. Verified by DOM geometry + screenshots:
  all 13 figures = title above, legend below, zero overlap.
- Added BASEBALL PLAIN-ENGLISH KEY glossary box (PA, OBP, contact%, BB%, ISO, run diff,
  wOBA/wRC+, FIP, K-BB%, WAR-as-proprietary-honest-note).
- Plain-language cue under every Figure 4 KPI subplot label (reach base %, walks, home runs,
  hits ball, strikeouts). "Payroll ($M)" → "($ millions)".
- Fixed "forward team-wins" → "forward-looking team-wins" (parallel with point 1).
- Measured: build clean; browser-verified glossary renders + Figure 4 cues live.
- Learned: one shared layout bug is the real "why won't it stop overlapping" answer —
  patch the helper, not each figure.
  [Ported into the integrated dashboard 2026-10-31 — PR #6: glossary box,
  KPI plain-language cues, and axis wording all carried over.]

---
## INTEGRATION NOTE — two cycle series converged (2026-10-31)
On 2026-10-31 two lanes worked this repo in parallel and both numbered
their cycles from 20. The main lane's Cycles 20-24 (player persistence,
cap pool deployment) and the toby lane's Cycles 20-26 (CarpeData,
solutions, Boardroom — appended below) are DIFFERENT work that shares
numbers. Entries are dated and titled; file names in src/ follow the
lane that wrote them (e.g. bml_cycle24_deploy.py is main-lane,
bml_cycle24.py is toby-lane). Nothing was renumbered, so history stays
traceable to its commits. The toby-lane entries follow.

## Cycles 14 / 16 / 17 — BACKFILLED 2026-10-31 (audit gap G7)
These three cycles shipped code and data but were never logged. Entries
reconstructed from the scripts and their committed outputs; Cycle 17's
output file was missing, so it was re-run on the same data to restore it.

- Cycle 14 (src/bml_cycle14.py) — PRODUCTION FORMULA + RUNS PANEL:
  promoted the run-differential model to the committed production
  artifact (data/formula_prod.json; KPIs + ISO + payroll + RD + PythE)
  and added the run-differential dashboard panel. Its recorded CV
  (MAE 4.3 / R2 0.764) is a two-season same-year cross-fit — Cycles
  18-19 later scoped this whole family as diagnostic, not forecast,
  and formula_prod.json now carries that annotation (G8).
- Cycle 16 (src/bml_cycle16_alloc.py + bml_cycle16_salary.py) — CAP
  ALLOCATION + the salary stub: allocation optimizer on real payroll
  profiles (data/cap_allocation.json: winning-cheap avg payroll $105.6M
  vs rich $332.6M; payroll coefficient ~0 once KPIs are in — "a
  cap-constrained team does not buy wins with dollars") plus the
  sensitivity panel. The salary half honestly reported its missing
  input (data/salaries_2026.json) for two cycles until Cycle 25
  supplied it (2026-10-31).
- Cycle 17 (src/bml_cycle17_ml.py) — MODEL-FAMILY COMPARISON: linear
  vs Ridge vs shallow RandomForest vs GradientBoosting vs poly-Ridge
  vs a small MLP, repeated K-fold on the same 58 team-seasons.
  Restored result (data/model_family_comparison.json, re-run
  2026-10-31): Linear MAE 3.84 (best), Ridge 4.16, RF 4.89, GBM 5.14,
  poly-Ridge 7.67, MLP 5112.9 (unscaled features at n=58 — a real,
  instructive blowup). Verdict stands as written: at this sample size
  the fancy families do not beat linear. Same-year scoping from
  Cycles 18-19 applies to the absolute numbers.

## Provenance note — Cycle 3 (audit gap G7, second half)
src/bml_cycle3.py and src/statcast_ingest.py do not exist in the repo:
the Cycle 3 result (team xwOBA adds no signal) survives in
data/statcast_team.json and the Cycle 3 entry above, but its generating
script was never committed. Savant ingestion is now covered, committed,
and tested by src/carpe.py (Cycle 20+); the gap is recorded here rather
than papered over with a reconstructed script.

## Correction — Cycle 19 grouped CV (audit gap G6, root-caused 2026-10-31)
The Cycle 19 entry below cites grouped CV "MAE 13.0, R2 -6.09". The
per-year fold keyed 2019 (MAE 51.9) predicts the 60-game 2020 season
with a 162-game-trained model — a units mismatch, not model error.
bml_cycle19_lagged.py now excludes target-season-2020 folds from the
headline mean and reports them separately: grouped CV MAE is 10.23
(R2 -0.081). The cycle's verdict is unchanged (the lagged model still
does not beat naive out-of-sample, 14.05 vs 9.75).

---

## Cycles 20-23 — CARPEDATA (every open/free endpoint, tested before trusted)
Connector: src/carpe.py (keyless). Scorecard: docs/CARPE_SCORECARD.md —
kept / dropped / unavailable, with reasons. All joins by MLBAM player_id;
name-string joins are retired in this work (the AZ/ARI failure class).

- Cycle 21 (src/bml_cycle21.py) — MARCEL BACKTEST, run first because it
  sets the baseline: shipped 2-season (5:4) vs classic 3-season (5-4-3)
  vs 3-season + age term (slope cross-fitted on the other year's
  residuals; lake extended to 2023+2024 via the same MLB API). Targets
  2025+2026, pooled n=196: A OBP MAE .0227 / SLG .0468; B .0226 / .0468
  (3rd season = a wash, +1 player of coverage); C .0220 / .0453 — the age
  term improved OOS in both directions. ADOPTED C's structure: cycle4
  now runs the explicit 3-season window {2026:5, 2025:4, 2024:3} plus
  pooled fitted age slopes (OBP .00158, SLG .00390 per year from age 27;
  ages from the lake's own per-season payloads — the old aging step was
  a hardcoded stub that adjusted nothing). Cascade regenerated (201
  hitters, +Profar; Judge .457->.444; aging veterans down). Cycle 11
  (pitchers) PINNED to its explicit 2-season window — untested there —
  and verified byte-identical after the pin.
- Cycle 20 (src/bml_cycle20.py) — SAVANT AT PLAYER LEVEL (Cycle 3 tested
  team level and killed it; player level was untested). Q1: prior xwOBA
  beats prior actual wOBA at predicting next-year wOBA in all 3 pairs
  (MAE .0279/.0304, .0256/.0260, .0266/.0286) — xwOBA is the better
  input. Q2: traits are far more stable than outcomes (YoY r: bat speed
  .92, EV50 .90, barrel% .80, squared-up .80 vs OBP .30-.57, SLG .36-.59).
  Q3: as ADJUSTMENTS on top of Marcel, every family failed the
  both-directions OOS rule — bat tracking worsened both metrics both
  directions; batted ball split; luck gap gained .0001-.0003 on OBP and
  split on SLG. ADOPTED: nothing. Stability is not incremental value;
  Marcel's outcome history already prices the traits. Savant ships as
  diagnostics (dashboard trait panel), not projection inputs.
- Cycle 22 (src/bml_cycle22.py) — BENCHMARK vs FanGraphs Steamer 2027
  (id-joined, 201/201 hitters, 76/76 pitchers): hitters OBP r=.889
  MAD=.010 bias=-.002; SLG r=.876 MAD=.020; top-25 OBP overlap 18/25.
  (Pre-adoption Marcel measured r=.856 / overlap 15 — the Cycle 21 age
  term measurably closed the benchmark gap.) Pitchers: ERA r=.663 but
  bias -0.324 — the pitcher Marcel is systematically OPTIMISTIC vs the
  public benchmark; WHIP bias -.093. Disclosed on the dashboard, open
  item. ZiPS via the FG API returned empty — not included, not claimed.
- Cycle 23 (src/bml_cycle23_pipeline.py) — MiLB PIPELINE INDEX: AAA/AA
  under-26 qualified production by org (ages from real birthdates, fail
  closed; AAA 1.0 / AA 0.85 level weights; volume x quality, avg=100).
  STL 151, CLE 143, MIL 127, AZ 126, MIA 126; TB #7 at 112 — all three
  winning-cheap orgs sit top-7 in near-MLB depth, and STL shows a strong
  pipeline alone doesn't convert. Limitations in the JSON metadata
  (upper minors only, no park adjustment, player-org units).
- Dashboard: 10 -> 13 panels (benchmark scatter, Savant trait check,
  pipeline index), each traceable to its source; clean-clone offline
  build re-verified (13 panels, no lake, network blocked).

---

## Cycles 24-25 + P7 packaging — SOLUTIONS (2026-10-31)
- Cycle 24 (src/bml_cycle24.py) — PITCHER BIAS, ROOT-CAUSED: judged the
  shipped pitcher Marcel against ACTUALS (not just Steamer): bias -0.208
  ERA pooled — the optimism was ours, not Steamer's conservatism.
  Variants as per Cycle 21: 3-season MAE .715, + cross-fitted age term
  .711 with bias collapsing to -0.078. Age slope is NEGATIVE and large
  (ERA -0.0355/yr from 27): old arms are where the optimism lived
  (age >=32 band bias -0.301). ADOPTED into cycle11: explicit 3-season
  window + pooled fitted age slopes. Pool widened 76 -> 102 pitchers
  (Burnes/Ragans/Lopez/Eovaldi now covered); re-benchmarked vs Steamer:
  ERA bias -0.324 -> -0.250, MAD .556 -> .524 (r dipped .663 -> .636 —
  the added arms are harder cases). Residual gap disclosed on dashboard.
- Cycle 25 (src/bml_cycle25.py) — REAL SALARIES + FA SHOPPING LIST
  (Cycle 16's declared dependency, finally wired): Spotrac team payroll
  pages -> data/salaries_2026.json (927 rows, 864 id-matched via the
  Steamer+lake registry, accent-folded); Spotrac 2027 FA page (251
  players, 231 with Steamer WAR) -> data/fa_shopping_2027.json. Top of
  the class: Skubal 5.66 WAR (prior AAV $32.0M, Spotrac market est
  $39.5M); best value: Rasmussen 8.79 WAR per $10M of prior AAV,
  Brandon Lowe 5.81, Trevor Rogers 4.91. Prior AAV is labeled a
  last-price anchor everywhere, never a predicted price. Spotrac
  rate-limited 6 team pages mid-pull (ARI/BOS/CHC/MIL/TB/TEX — 500s
  then 403): coverage is 24/30 teams, logged in the JSON metadata;
  the script's cache makes any later rerun complete just the missing
  six. USA TODAY salaries returned 402 — tried, blocked, logged.
  Dashboard panel 14 ships the shopping list.
- P7 packaging: README.md (quickstart + honesty rules + repo map),
  EXEC_SUMMARY rewritten to the current state (was: 5 panels and the
  retracted formula family), dashboard now 14 panels; clean-clone
  offline build re-verified (14 panels, no lake, network blocked).

---

## Cycle 26 — the BOARDROOM layer (2026-10-31)
- Built: src/bml_cycle26_wow.py -> data/wow_scenarios.json +
  data/team_explorer.json; three dashboard panels (17 total).
- WHAT DOES THE MONEY BUY: 26-man rosters built ENTIRELY from the real
  2027 FA class (Spotrac + Steamer WAR, prior-AAV anchors) at three
  budgets — Floor $171.2M: 42.0 WAR for $171.0M; Middle $208M: 45.7 WAR;
  Cap $245.3M: 52.3 WAR for $244.6M. The floor build captures ~80% of
  the cap build's WAR; the last $73.6M buys ~10.3 WAR. Method: greedy
  WAR-per-dollar quota fill + WAR upgrades while budget holds;
  constraints asserted in code (26 men, spend <= budget). Anchors are
  last prices, labeled as such on the panel.
- PRESS PLAY: payroll-vs-wins animated over the 2011-2026 panel
  (16 seasons, bubble = wins per $100M, winning-cheap three in gold).
- PICK YOUR TEAM: per-club 2026 signature radar indexed to league=100
  (K%/HR inverted), with payroll, cap headroom, pipeline rank and top
  prospect in the title — all 30 clubs, from committed snapshots.

## Cycle 27 — AVAILABILITY STRESS on the Boardroom rosters (toby series, 2026-10-31)
- Question: "the 42 WAR floor roster assumes health — what survives
  injuries?" Method kept honest: per-player measured IL availability
  covers only 12 of 33 rostered players (45% of WAR), and applying it
  selectively would penalize the best-measured players — so the stress
  is UNIFORM, factors measured from the 201-player pool's real 2025-26
  IL records (mean availability 0.912, p25 0.890).
- Measured: Floor 42.0 → 38.3 WAR (p25: 37.4); Middle 45.7 → 41.7;
  Cap 52.3 → 47.7. Floor/cap ratio unchanged at 0.803.
- Learned: injury risk is a level tax (~4-5 WAR at every budget), not
  a big-spender rescue. The winning-cheap edge survives the stress.
  Measured-subset context (12 players): 26.4 → 24.4 WAR.
- Also this pass: docs/TALKTRACK.md renumbered to the merged 20-figure
  dashboard (Boardroom beats added: film opener, money-buys, pick-your-
  team close); dashboard glossary WAR reference corrected Figure 12 → 18.

## Cycle 28 — THE DATA PLATFORM (toby series, 2026-10-31)
Owner's call: "your role is data engineer" — the cycle-file pattern
became a real platform (docs/DATA_PLATFORM.md): ingest → raw →
curated → DuckDB warehouse → serving, built to the professional
canon (Reis & Housley lifecycle, Kleppmann, Kimball grain, Akidau
streaming terms, Moses et al. observability).
- src/ingest_platform.py: bounded-parallel batch (6 workers) for MLB
  API / Savant / FanGraphs + watermark micro-batch for transactions
  (120,313 events landed, deduped on id) + manifest lineage
  (sha256/rows/status per object). First run re-derived the Savant
  bat-tracking trap from scratch (a ?year= URL silently returns a
  209-row default board for every season) — caught by manifest
  VOLUME parity against known counts, fixed by mirroring carpe.py's
  proven date-range URLs; final counts match the committed snapshots
  exactly, all 15 datasets.
- src/curate.py: 14 schema-enforced Parquet tables with declared
  grains (dim_player/dim_team + 12 facts), fail-closed contracts.
- src/build_warehouse.py + queries/: DuckDB analytical store; the
  stakeholder questions are named SQL. PARITY PROOF: benchmark_parity
  reproduces Cycle 22 from curated tables alone (201 matched,
  OBP r = 0.889, mean |diff| 0.0101); persistence query reproduces
  the 2025→26 OBP YoY r = 0.298 exactly. Cap gaps match the talk
  track (NYM 101.4 / CLE +96.7 / TB +75.6).
- verify_data.py gate extended with curated-layer checks (25 total).
- Deliberately NOT built: Kafka/Spark/Airflow/cloud warehouse —
  wrong scale, breaks offline-from-clone. Reasons in the doc.

## Cycle 29 — EXECUTIVE ONE-PAGER (2026-11-01, 24/7 build cycle)
- Built: src/make_onepager.py -> docs/ONEPAGER.html, print-clean single
  page, no external assets, no scripts. Every number read from committed
  artifacts at generation time; the script FAILS CLOSED on a missing
  artifact, a broken contract (3 scenarios x 26 men, spend <= budget),
  or a moved headline number (benchmark r, salaries rows/failures,
  curated failures).
- Contents: thesis; edge numbers (2025->2026 persistence n=80: contact
  r=0.899, BB% r=0.655, OBP r=0.298; Marcel-vs-Steamer OBP r=0.889,
  n=201); winning-cheap 2026 table (MIL 103 wins / $146.7M, TB 98 /
  $95.6M, CLE 85 / $74.5M vs NYM 74 / $346.7M); cap reality (7 over cap,
  15 under floor; NYM $101.4M over, CLE $96.7M to add); scenario table
  incl. availability stress (Floor 42.0 -> 38.3, Middle 45.7 -> 41.7,
  Cap 52.3 -> 47.7; floor/cap ratio 0.803 unchanged); honesty box
  (retracted team-wins claim, stress as level tax, salaries 24/30,
  WAR proprietary); data-QC line (14 curated tables, zero failures).
- Verified: regenerated from the current main tree; all key figures
  present in the HTML; zero external references; gate + parity green
  on the same tree (see cycle run note: ingest 20 datasets 0 failures,
  curate unchanged, parity r=0.889, gate ALL PASS incl. live standings).
- This run also probed Spotrac (Tampa Bay 2026 payroll page): still 403
  — the 24/30 salaries gap stands, logged, no routing around the block.

## Cycle 30 — FORCED-SELLER PANEL (2026-11-01, 24/7 build cycle)
- Built: src/bml_cycle30.py -> data/forced_sellers_2027.json +
  dashboard Figure 10 (Section III, "The Cap"), new total 21 figures.
- Method: for each over-cap team in data/cap_scenario_2027.json, rank
  its data/salaries_2026.json contracts largest-first and take the
  minimal prefix covering the cap gap. Assertions: cap/floor unchanged,
  shed set minimal, coverage exactly 6/7 with CHC the sole uncovered team.
- Measured: NYM gap $101.4M -> shed 3 (Soto $57.5M, Bichette $42.0M,
  Lindor $34.1M) = $133.6M; LAD $94.0M -> 2 (Ohtani $70.0M, Tucker
  $55.0M) = $125.0M; NYY $63.0M -> 2 (Judge $40.0M, Bellinger $36.5M)
  = $76.5M; PHI $46.7M -> 2 (Wheeler $42.0M, Schwarber $33.0M) =
  $75.0M; TOR $30.8M -> 1 (Guerrero Jr. $40.2M) = $40.2M; ATL $18.2M
  -> 1 (Sale $27.0M) = $27.0M. CHC ($4.0M over) uncovered: no contract
  rows — its Spotrac page failed in Cycle 25, logged, not zero.
- Learned: every covered over-cap team closes its gap by shedding at
  most 3 contracts — the cap binds through a handful of deals, not a
  rebuild. Stated as arithmetic only: shedding is assumed to remove
  the full listed salary, which real trades rarely do, so each count
  is a lower bound, not a plan. Listed contracts need not sum to a
  team's cap-scenario payroll total (different payroll definitions /
  roster timing); the count uses individual values vs the gap.
- Renumbering cascade handled explicitly (the Figure-reference rot
  class the gate guards): old Figures 10-20 -> 11-21 in the figure
  index, TALKTRACK (incl. Fig 16 benchmark -> 17) and the dashboard
  glossary WAR reference (18 -> 19); gate bounds moved 20 -> 21 and
  18 -> 19. README + EXEC_SUMMARY counts moved 20 -> 21.
- Platform run on the same tree: Spotrac probe still 403 (24/30 gap
  stands); ingest 20 datasets, 0 failures, Savant volumes in band
  (expected 651-673, bat-tracking 595-619, sprint 489-506),
  transactions 120,313 (unchanged); curate 14 tables unchanged; parity
  r = 0.889, 201 matched; gate ALL PASS incl. live standings 30/30.

## Cycle 31 — SPELL-CHECK BUILD GATE + merge reconciliation (main lane, 2026-11-01)
- Built src/spellcheck_gate.py: fails the build (exit 2) on ANY misspelled
  word in user-visible text (parses visible words from the built dashboard
  HTML + doc prose; possessive-aware normalization; vocabulary whitelist for
  legit baseball/stats/team terms). Verified green on the full merged build.
- Fixed "provably" -> "What the data actually shows" (the box header is plain
  English, no dictionary argument possible) and "homeruns" -> "home runs".
- Rebased my local cycle onto the merged toby-lane main (origin moved 21
  commits ahead, Cycles 27-30: Boardroom, data platform, QC gate, forced
  sellers). 0 conflicts; local work sits on top; both lanes preserved.
- Fixed pandas 2.x FutureWarning in payroll.load_payroll_frame (all-NA
  avg_age in the 2026 rows triggered dtype-coercion deprecation): dropped
  the all-NA field from df26 rows. VERIFIED: 480 rows, 30 teams in 2026,
  avg_age still retained from historical frames, wins float / payroll int,
  ZERO warnings on clean rebuild.
- Race-managed with toby: remote had new toby/* branches (audit-p0-fixes,
  carpe-data, data-platform, data-qc, finale, forced-sellers, integrate,
  integrate2). Merged main converges both lanes; dashboard = 21 figures.

## Cycle 32 — FanGraphs salary lane BLOCKED + 22-figure gate repair (toby, 2026-11-01 ~14:15 PT)
- Deadline guard: 2026-11-01, inside the window (closes 2026-12-01). No change.
- Spotrac probe: single GET of the Tampa Bay payroll page still 403
  ("Update Your Browser" challenge page). Logged, not routed around.
  Salaries stay 24/30; forced-seller coverage stays 6/7 (CHC uncovered).
- FanGraphs RosterResource lane (backlog item c, owner-approved 2026-11-01):
  FAILED CLOSED, nothing shipped from it. Direct pulls of the
  ?season=2026 payroll pages return HTTP 403 (Cloudflare "Just a moment"
  challenge) for both a requests pull (chunked-encoding reset) and curl
  with a browser UA. Per the standing rule (403/429 = stop that source),
  the pull was stopped after the probe + one team page — no alternate
  endpoint, no browser automation to get around the challenge, and no
  rows were added to salaries_2026.json. The reconcile-first guard was
  therefore NOT run (no FanGraphs pull to reconcile), and salaries stay
  labeled 24/30 Spotrac in metadata, the dashboard source box, and the
  talk-track. A future attempt must first pin the field mapping: public
  RosterResource snapshots show the FanGraphs 2026 cash column differing
  from the Spotrac file on top guaranteed contracts (SD: Machado
  $25,090,909 FG 2026 vs $39,090,909 Spotrac; Tatis $20,714,286 vs
  $25,714,286; MIA: Alcantara $17,300,000 vs $21,000,000) — so a naive
  2026-column comparison would fail on definition, not on data. That
  observation is preliminary (page snapshots, not a full pull) and is
  NOT a reconciliation result.
- Platform run on current main (f1df9a8c, main lane moved since Cycle 30):
  ingest 20 datasets, 0 failures; Savant volumes in band (expected
  651-673, bat-tracking 595-619, sprint 489-506); Steamer raw +1 row
  each (4166/5169) with no curated change; transactions watermark
  120,313 -> 120,338; curate 14 tables, all contracts pass, counts
  unchanged; warehouse rebuilt; benchmark parity r = 0.889, 201 matched.
  No curated data changed, so no data PR from this run.
- Gate failure found on current main and fixed (mechanical renumbering
  only, no claim change): the main-lane merge added the Cycle 8 title-bar
  AUC panel as Figure 5, renumbering every later figure +1 (22 figures
  total), but verify_data.py still demanded the old "(see Figure 19)"
  cross-reference, which the merge had replaced with a section pointer,
  and TALKTRACK/README/EXEC_SUMMARY still said 21 figures. Fix in this
  PR: gate figure check now asserts the 22-chart index line and the
  talk-track bound moves 21 -> 22; TALKTRACK refs shifted old>=5 -> +1
  (Fig 5 AUC line added from the panel's own title; benchmark Fig 17 ->
  18; cap Figs 9+10+19 -> 10+11+20; money Figs 15+21 -> 16+22);
  dashboard docstring, README, and EXEC_SUMMARY moved 21 -> 22 figures.
  Rebuilt dashboard from committed snapshots: 22 plotly divs, PRESS PLAY
  present; gate ALL PASS incl. live standings 30/30; spellcheck gate
  green on the rebuilt dashboard + docs.
- Next: item (d) presentation restructure (owner-approved, same data,
  no new claims) is the next backlog item; item (c) retries only if
  FanGraphs serves a direct pull again, with the field mapping pinned
  first.

## Cycle 33 — PRESENTATION RESTRUCTURE (toby, 2026-11-01 ~20:15 PT)
- Deadline guard: 2026-11-01, inside the window (closes 2026-12-01). No change.
- Spotrac probe: single GET of the Tampa Bay payroll page still 403
  ("Update Your Browser" challenge page). Logged, not routed around.
  FanGraphs single probe (RosterResource payroll page, browser UA) still
  403 (Cloudflare "Just a moment"). Item (c) therefore stays BLOCKED and
  untouched: no rows added, salaries stay 24/30, forced-seller 6/7.
- Platform run on current main (2f2e626e, parallel lane moved since Cycle 32):
  ingest 20 datasets, 0 failures; Savant volumes in band (expected 651-673,
  bat-tracking 595-619, sprint 489-506); transactions watermark 120,338 ->
  120,351 (+13, no sharp move); curate 14 tables, all contracts pass,
  byte-identical to main (no data PR from this run); warehouse rebuilt;
  benchmark parity r = 0.889, 201 matched.
- Restructure (backlog item d, owner-approved 2026-11-01): src/dashboard_p6.py
  ASSEMBLY ONLY — no panel function, model, dataset, or claim changed, and
  figure numbers are unchanged (1-22 in the same order), so every talk-track
  reference still points at the same figure. Three modes from the same
  committed figures, with a mode switcher (Story is the default landing;
  without scripts all three modes simply show in order):
  (1) STORY — verdict first (thesis + the existing stat cards + Pick Your
  Team, Figure 2), then 6 chapters with ONE figure each: skills persist
  (Fig 3), run differential describes (Fig 4), payroll vs wins (Fig 6),
  cap reality (Fig 10), what the money buys (Fig 16), the Steamer
  benchmark (Fig 18). Each chapter headline is the claim that figure
  already proves, using only numbers already in the talk-track, plus a
  one-line "So what for the owner" and a source line; method + honesty
  box collapsed into an appendix at the end.
  (2) BOARDROOM — 15 slides in talk-track order (Figures 4+5 share one
  slide, which is how 16 talk-track figures fit 15 slides), each headed
  with its conclusion, with a print-boardroom control that prints only
  this section.
  (3) EXPLORER — all 22 figures reachable, grouped by task instead of one
  figure-numbered scroll: Cap Reality (1, 6, 9, 10, 11), Build a Roster
  (7, 8, 12, 13, 14, 15, 16, 17), Shop the FA Class (21, 22), Check the
  Model (3, 4, 5, 18, 19, 20), with Pick Your Team (Fig 2) on top — plus
  Savant-style percentile cards for the top 8 bargain free agents, ranked
  by WAR per $10M of prior salary (Rengifo 13.51, Rasmussen 8.79,
  Quantrill 8.75, Montgomery 8.69, France 7.51, Buehler 6.83, Bauers 6.47,
  Lorenzen 6.21). Percentiles are computed from the committed 2027
  free-agent pool only (231 players with Steamer WAR; each bar uses only
  the players who have that metric); a metric a player lacks in the
  committed projections is labeled "Not in the committed pool for this
  metric", never filled — pitchers have no hitter OBP/K%/xwOBA there,
  and four pitchers plus France have no availability row there.
  A lake-less build renders a labeled placeholder for the pitching panel
  instead of breaking or renumbering silently (G1 preserved).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): story 7 renders (hero + 6 chapters), 6 chapters; boardroom 15
  slides, 16 renders; explorer 22 renders, distinct figures 1-22 (no
  figure lost); all 8 card numbers match data/fa_shopping_2027.json and
  the recomputed OBP percentile for the first card (14) matches the bar;
  no double-numbered figure titles. Gate updated to the new assembly
  (chapter/slide/explorer/card checks) and ALL PASS, including the live
  standings check; spellcheck green (card surnames added to its whitelist
  as verified spellings).
- Docs: TALKTRACK gains a three-mode map (figure numbers unchanged);
  README moves "8 story sections" to the three modes; EXEC_SUMMARY still
  says 22 figures, which is still true, so it is untouched.
- Next: item (e) README demo-runbook rewritten around the three modes;
  item (c) retries only if FanGraphs serves a direct pull again.

## Cycle 34 — FIGURE 23: THE POSTED CLASS (toby, 2026-11-01 ~23:12 PT, overnight sprint)
- Deadline guard: 2026-11-01, inside the window (closes 2026-12-01). No change.
- Spotrac probe: single GET of the Tampa Bay payroll page still 403
  ("Update Your Browser" challenge page). Logged, not routed around.
  Salaries stay 24/30, forced-seller 6/7; item (c) retries only if a
  single FanGraphs probe returns 200 in a later cycle.
- Platform run on current main (1aa7d17a, unmoved since Cycle 33):
  ingest 20 datasets, 0 failures; Savant volumes in band (expected 651-673,
  bat-tracking 595-619, sprint 489-506); transactions watermark advanced to
  2026-11-02; curate 14 tables, all contracts pass, byte-identical to main
  (no data PR from the platform step); warehouse rebuilt; benchmark parity
  r = 0.889, 201 matched.
- Fig. 23 (backlog item e, owner-directed 2026-11-01): the posted class
  from the ready data package (~/workspace/hardball/fig23/, outside the
  repo). Committed: src/pull_npb_bis.py (standalone repro pull, lands raw
  under data/raw/npb_bis/ and never rewrites the curated trio file),
  an npb_bis source in src/ingest_platform.py (verified live this run:
  lands 340 rows, byte-identical to the committed leaderboard CSV),
  data/posted_class_2026.json (verified trio), and
  data/npb_leaderboards_2024_2026_raw.csv (340-row provenance).
  Figure 23 is one Plotly figure (2x2: Sato K% 26.8/27.3/26.7, Sato BB%
  7.3/9.5/11.1, Itoh IP 176.1/196.2/172.2 with BB% 3.6/4.7 on the 2025-26
  bars, Taira ERA 1.71 closer -> 1.36 starter) plus Explorer-only HTML:
  trio cards built from the JSON (no hardcoded rates), the posting clock
  (Nov 1 -> Nov 2 -> Dec 1 lockout pause -> Dec 16 17:00 ET), fee tiers
  with a $60M illustrative worked example ($10.875M fee, labeled not a
  predicted price), and the translation honesty box (Imai comp: projected
  6yr/$150M, signed 3yr/$54M Houston, 4.93 ERA, bullpen demotion — MLBTR).
  NO NPB-to-MLB translation factor is claimed anywhere. BIS is canonical
  over wire roundings (Sato .306 not .308; Itoh 34 BB not 32; Taira 45 BB).
  Itoh's 2024 row shows BB count only (no BB% in the dataset — not
  invented); Taira has no 2024 qualified row (reliever workload).
  Placement: Explorer-only, new "The Posted Class" group — Story stays
  6 chapters, Boardroom stays 15 slides, figures 1-22 unrenumbered, so
  every prior reference still points at the same figure. Gate moves
  22 -> 23 (index line, talk-track cap, new posted-class checks: trio
  JSON present, Figure 23 in Explorer with BIS source label).
  TALKTRACK gains the back-pocket "What about Japan?" Q&A; README and
  EXEC_SUMMARY move 22 -> 23 figures; CARPE_SCORECARD gains the NPB BIS
  kept row; spellcheck whitelist gains the trio/club names (verified
  spellings against the JSON).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): dashboard rebuilds with lake; explorer holds figures 1-23 with
  no duplicates and no missing figure; every Fig. 23 number recomputed
  from posted_class_2026.json matches the rendered bars/cards; gate ALL
  PASS; spellcheck green.
- Next: item (f) README demo-runbook rewritten around the three modes,
  pointing at Fig. 23 as the live-market exhibit.

## Cycle 35 — README DEMO-RUNBOOK (toby, 2026-11-02 ~00:12 PT, overnight sprint)
- Backlog item (f): README gains a "Presenting in 5 minutes" section,
  written around the three modes shipped in Cycle 33 and the Fig. 23
  exhibit shipped in Cycle 34. Story in 5 minutes (verdict screen, then
  Chapters 1/3/5 — Figures 3, 6, 16 — then the appendix); PRESS PLAY on
  Figure 1 as the film-first hook (Boardroom slide 1 / Explorer Cap
  Reality); Boardroom for the room (15 slides, talk-track order, Print
  boardroom button); Explorer for questions (all 23 figures by task,
  Pick Your Team on top); Figure 23 as the closer — the posted class
  (Sato, Taira, Itoh; Nov 1 -> Nov 2 -> Dec 1 lockout pause -> Dec 16
  17:00 ET) with its own translation honesty box. The section also names
  where the honesty box lives every time: the Story appendix, Figure 23's
  translation box, and the README Honest limits.
- No data, model, figure, or claim changed: README + this log entry only.
  Every number in the new section is already in the dashboard or the
  talk-track (win ~95 at a third to a quarter of big-market payroll;
  floor vs cap builds; posting dates and fee tiers from Cycle 34).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): platform gate ALL PASS on current main f294e245 (sprint
  courtesy: ingest skipped — Cycle 34's ingest ran within the hour and
  main unmoved; gate never skipped); benchmark parity r = 0.889, 201
  matched; dashboard rebuilds with 23-chart index intact, 6 story
  chapters, Figure 23 present; spellcheck green on the edited README.
- Spotrac probe (once per run): still 403. Salaries remain 24/30,
  forced-seller 6/7 (CHC uncovered).
- Next: item (g) December readiness checklist in HANDOFF.md.

## Cycle 36 — DECEMBER READINESS CHECKLIST (toby, 2026-11-02 ~01:15 PT, overnight sprint)
- Backlog item (g): HANDOFF.md gains a December readiness checklist
  (freeze + final refresh targets, demo-package checks, print pack,
  known gaps carried honestly, Dec 1 day-of sequence, post-Dec 1
  shutdown). No data, model, figure, or claim changed: HANDOFF.md +
  this log entry only.
- Status snapshot recorded in the checklist, all verified this run on
  main 10c217c8 (unmoved since Cycle 35): gate ALL PASS; parity
  r = 0.889, 201 matched; curated byte-identical to main (no data PR
  from the platform step); dashboard rebuilds with lake at 23 figures
  (Story 6 chapters, Boardroom 15 slides, Explorer all 23, 8 percentile
  cards, Figure 23 Explorer-only with BIS label).
- Platform run: ingest 21 datasets, 0 failures; Savant volumes in band
  (expected 651-673, bat-tracking 595-619, sprint 489-506); NPB BIS
  leaderboards 340 rows; transactions watermark advanced; curate 14
  tables, all contracts pass; warehouse rebuilt.
- Spotrac probe (once per run): still 403. Salaries remain 24/30,
  forced-seller 6/7 (CHC uncovered). FanGraphs lane not retried (no
  200 probe; Cycle 32 guard still binds).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): dashboard rebuild holds figures 1-23 with no duplicates;
  gate ALL PASS; spellcheck green on the edited files.
- Next: item (h) — drift re-run / docs polish (all backlog items a-g
  now done; no new claims).

## Cycle 37 — DRIFT RE-RUN: CYCLE 24 PITCHER BACKTEST (toby, 2026-11-02 ~02:12 PT, overnight sprint)
- Backlog item (h): re-ran src/bml_cycle24.py (pitcher Marcel backtest,
  targets 2025 + 2026) on the current lake and diffed the regenerated
  data/pitcher_backtest.json against the committed artifact.
- Result: NO DRIFT — regenerated artifact identical to committed, so no
  data or model change ships from this re-run. Pooled numbers unchanged:
  MAE ERA A 0.744 / B 0.715 / C 0.711; MAE WHIP 0.122 / 0.120 / 0.120;
  ERA bias -0.208 / -0.205 / -0.078. The shipped pitcher method stands.
- Platform run this cycle, on main a80989d0 (unmoved since Cycle 36):
  ingest 21 datasets, 0 failures; Savant volumes in band (expected
  651-673, bat-tracking 595-619, sprint 489-506); NPB BIS leaderboards
  340 rows; curate 14 tables, all contracts pass; warehouse rebuilt;
  parity r = 0.889, 201 matched; curated byte-identical to main (no
  data PR from the platform step); gate ALL PASS; dashboard rebuilds
  with 23-chart index intact (Story 6 chapters, Boardroom 15 slides,
  Explorer all 23 figures, 8 percentile cards, Figure 23 Explorer-only
  with BIS label).
- Spotrac probe (once per run): still 403. FanGraphs probe (once per
  run): still 403 Cloudflare. Salaries remain 24/30, forced-seller 6/7
  (CHC uncovered); the reconciled-FanGraphs lane stays closed under
  the Cycle 32 guard — it reopens only on a 200 probe.
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): gate ALL PASS; dashboard rebuild holds figures 1-23 with no
  duplicates.
- Next: item (h) continues — next drift re-run (Cycle 21 hitter
  backtest) or docs polish; no new claims.

## Cycle 38 — DRIFT RE-RUN: CYCLE 21 HITTER BACKTEST (toby, 2026-11-02 ~03:12 PT, overnight sprint)
- Backlog item (h): re-ran src/bml_cycle21.py (Marcel backtest, targets
  2025 + 2026) on the current lake and diffed the regenerated
  data/marcel_backtest.json against the committed artifact.
- Result: NO DRIFT — regenerated artifact byte-identical to committed,
  so no data or model change ships from this re-run. Pooled numbers
  unchanged: A (2-season) OBP MAE .0227 / SLG .0468; B (3-season) .0226 /
  .0468; C (age cross-fitted) .0220 / .0453. The shipped hitter method
  (C's structure, adopted in Cycle 21) stands.
- Platform run this cycle, on main 0a0910a9 (unmoved since Cycle 37):
  ingest 21 datasets, 0 failures; Savant volumes in band (expected
  651-673, bat-tracking 595-619, sprint 489-506); NPB BIS leaderboards
  340 rows; curate 14 tables, all contracts pass; warehouse rebuilt;
  parity r = 0.889, 201 matched; curated byte-identical to main (no
  data PR from the platform step); gate ALL PASS; dashboard rebuilds
  with 23-chart index intact (Story 6 chapters, Boardroom 15 slides,
  Explorer all 23 figures, 8 percentile cards, Figure 23 Explorer-only
  with BIS label).
- Spotrac probe (once per run): still 403. FanGraphs probe (once per
  run): still 403 Cloudflare. Salaries remain 24/30, forced-seller 6/7
  (CHC uncovered); the reconciled-FanGraphs lane stays closed under
  the Cycle 32 guard — it reopens only on a 200 probe.
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): gate ALL PASS; dashboard rebuild holds figures 1-23 with no
  duplicates.
- Next: item (h) continues — docs polish (e.g. the checklist's
  persistence-figure recompute, r vs R^2 labeling) or the next drift
  re-run; no new claims.

## Cycle 40 — DRIFT RE-RUN: CYCLE 20 SAVANT PLAYER-LEVEL TEST (toby, 2026-11-02 ~05:12 PT, overnight sprint)
- Backlog item (h): re-ran src/bml_cycle20.py (Savant at player level:
  Q1 luck correction, Q2 trait stability, Q3 Savant families as
  adjustments on Marcel, both-directions OOS) on the current lake and
  diffed the regenerated data/savant_test.json against the committed
  artifact.
- Result: NO DRIFT — regenerated artifact identical to committed, so
  no data or model change ships from this re-run. Numbers unchanged:
  Q1 xwOBA beats actual wOBA in all 3 pairs (MAE .0279/.0304,
  .0256/.0260, .0266/.0286); Q2 trait stability bat speed r .921,
  EV50 .897, barrel% .801, squared-up .798 vs outcome OBP .436 /
  SLG .478; Q3 no family improves OOS MAE in both directions on both
  metrics, so nothing is adopted — Savant stays diagnostics, not
  projection inputs, exactly as Cycle 20 concluded. The shipped
  projection method stands.
- Platform run this cycle, on main f8ab2726 (unmoved since Cycle 38):
  ingest skipped per the sprint courtesy (prior run's ingest within
  the last hour, no source changes, main unmoved); curate 14 tables,
  all contracts pass; warehouse rebuilt; parity r = 0.889, 201 matched;
  curated byte-identical to the prior rebuilt set (no data PR from
  the platform step); gate ALL PASS; dashboard rebuilds with
  23-chart index intact (Story 6 chapters, Boardroom 15 slides,
  Explorer all 23 figures, 8 percentile cards, Figure 23 Explorer-only
  with BIS label).
- Spotrac probe (once per run): still 403. FanGraphs probe (once per
  run): no response this run (HTTP 000, not a 200) — the
  reconciled-FanGraphs lane stays closed under the Cycle 32 guard;
  it reopens only on a 200 probe. Salaries remain 24/30, forced-seller
  6/7 (CHC uncovered).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): gate ALL PASS; dashboard rebuild holds figures 1-23 with no
  duplicates.
- Still awaiting the owner: PR #21 (Cycle 39 persistence correction)
  is open and unmerged — claim change, his call. This run changes
  nothing in it.
- Next: item (h) continues — next drift re-run (e.g. Cycle 22 Steamer
  benchmark) or docs polish; no new claims.

## Cycle 41 — COT'S SALARY LANE: RECONCILED, FAILED CLOSED (toby, 2026-11-02 ~06:20 PT, owner-approved lane)
- Owner approved the Cot's lane in chat ("Run the Cot's lane — reconcile,
  then fill the 6 teams"), mirroring the FanGraphs lane's discipline:
  pull, run the reconcile-first guard against the 24 Spotrac teams, fill
  only on a pass.
- Pull: legacy.baseballprospectus.com is Anubis-gated for direct fetch
  (challenge page, no data — not routed around). The Cot's index links
  public per-team Google Sheets ("26 YE", projected 40-man year-end
  through 11/1/26); all 30 exported as CSV (30/30 HTTP 200, polite rate)
  and cached in the mirror at data/raw/cots/ on the Spotrac pattern.
  2,240 payroll lines parsed: 1,369 main contract rows + 871 bonus /
  buyout / departed-player lines.
- Reconciliation discovery: the Spotrac salaries file is on a **2027**
  basis — cached pages are titled "2027 <Team> Payroll Table" (Spotrac
  had rolled seasons at the Cycle 25 pull, 2026-10-31). Contracted
  veterans match Cot's LRP-2027 to the dollar (ATH escalators exact).
  All four Cot's columns tested; LRP 2027 is the only viable mapping.
- Guard result: FAIL on every prong of the pass bar. Coverage 150/927
  (16.2%) — the unmatched 777 are 501 pre-arb rows at Spotrac's flat
  $1,000,000 placeholder, 209 arbitration projections, 58 names absent
  from the team's Cot's sheet, and 9 option/FA-marker veterans; Cot's
  does not publish estimates for unsigned players. Agreement 104/150 within
  $50k = 69.3% (bar 95%); plain-contract subset 85.5%. Team totals off
  by >2% in 16/24. Top-5 clean in 3/17 evaluable teams. Causes are
  accounting conventions: option years (Cot's books the buyout,
  Spotrac the exercised salary — Robert Jr. $2.0M vs $20.0M), deferred
  money (Cot's present value vs Spotrac nominal — Ohtani $28.216M vs
  $70.0M), signing-bonus proration residuals ≤ ~$1.7M. Full tables in
  docs/CARPE_SCORECARD.md (Cycle 41 addendum).
- FAILED CLOSED, as the guard requires: data/salaries_2026.json
  untouched, salaries remain 24/30 Spotrac, forced-seller coverage
  remains 6/7 (CHC uncovered), no platform or dashboard change. Cot's
  itself spot-verified accurate (CHC: Swanson AAV $25,285,714, Imanaga
  $22,025,000, Happ AAV $20,333,333). A fill would need a full-file
  basis conversion or a separately labeled Cot's dataset — owner's
  call, flagged in the scorecard, not taken here.
- This PR is docs-only (scorecard + this entry). Gate state unchanged
  from Cycle 40's ALL PASS on the same main head; the salaries honesty
  check still reads 24/30 because the data still is 24/30.
- Spotrac / FanGraphs not retried this lane beyond the standing
  per-run probes (both still blocked); no source was routed around.
- Next: owner's call on the two fill options above, or item (h)
  continues; PR #21 (Cycle 39 persistence correction) still open,
  untouched.

## Cycle 42 — DRIFT RE-RUN: CYCLE 22 STEAMER BENCHMARK (toby, 2026-11-02 ~06:12 PT, overnight sprint)
- Backlog item (h): re-ran src/bml_cycle22.py (Marcel vs FanGraphs
  Steamer 2027, MLBAM id join only, committed 2026-10-31 snapshots +
  lake players registry for pitcher ids) on the current lake and
  diffed the regenerated data/fg_benchmark_2027.json against the
  committed artifact.
- Result: NO DRIFT — regenerated artifact byte-identical to committed,
  so no data or model change ships from this re-run. Numbers unchanged:
  hitters matched 201/201, OBP r = 0.889, MAD 0.010, bias -0.002; SLG
  r = 0.876, MAD 0.020, bias -0.004; top-25-by-OBP overlap 18/25.
  Pitchers matched 102/102, ERA r = 0.636, MAD 0.524, bias -0.250;
  WHIP r = 0.717, MAD 0.100, bias -0.074. Agreement-with-Steamer only,
  not accuracy — neither system has 2027 outcomes yet, as Cycle 22
  scoped it. The shipped projection method stands.
- Platform run this cycle, on main e8b7be07: main moved mid-run when
  the parallel Cot's lane merged PR #23 (docs-only); this run's tree
  was rebuilt from the new head before the gate and drift checks, so
  nothing here is based on the superseded head. Ingest 21 datasets,
  0 failures (Savant expected 651-673/season, bat-tracking 595-619,
  sprint 489-506 — all at known-good counts, no silent-source move);
  curate 14 tables, all contracts pass; warehouse rebuilt; parity
  r = 0.889, 201 matched; curated Parquet + build report byte-identical
  to the prior tree (no data PR from the platform step); gate ALL PASS;
  dashboard rebuilds with the 23-chart index intact (Story 6 chapters,
  Boardroom <=15 slides, Explorer all 23 figures, 8 percentile cards,
  Figure 23 Explorer-only with BIS label).
- Spotrac probe (once per run): still 403. FanGraphs probe (once per
  run): no response this run (HTTP 000, not a 200) — the
  reconciled-FanGraphs lane stays closed under the Cycle 32 guard;
  it reopens only on a 200 probe. Salaries remain 24/30, forced-seller
  6/7 (CHC uncovered).
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): gate ALL PASS; dashboard rebuild holds figures 1-23 with no
  duplicates.
- Still awaiting the owner: PR #21 (Cycle 39 persistence correction)
  is open and unmerged — claim change, his call. The Cot's fill
  options from Cycle 41 (full-file basis conversion vs a separately
  labeled Cot's dataset) are also his call. This run changes nothing
  in either.
- Next: item (h) continues — next drift re-run or docs polish; no new
  claims.
