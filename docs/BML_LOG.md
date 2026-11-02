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

## Cycle 39 — PERSISTENCE RECOMPUTE: THE "OBP r ≈ 0.3" CLAIM CORRECTED (toby, 2026-11-02 ~04:40 PT, overnight sprint)

- Backlog item (h): the MIT/Moneyball study's flagged persistence item —
  recompute the demo's headline persistence figures in HARDBALL's own
  sample and fix the r-vs-R²-adjacent labeling before Dec 1.
- FINDING 1 — the copy generalized one pair. The demo's prose (Story
  chapter 3, talk-track THE EDGE, exec summary) said OBP "carries at
  only about 0.3" across four season pairs. The committed per-pair data
  never said that: OBP r = 0.576 / 0.595 / 0.582 / 0.298. Only the latest
  pair (2025→2026, n=80) is 0.30; the first three pairs are 0.55-0.60.
  The 0.298 is a genuine Pearson r (recomputed twice, see below), NOT a
  mislabeled R² — but note the first three pairs' OBP R² values are
  0.33 / 0.35 / 0.30, which is plausibly where a stray "0.3" came from.
  Pooled OBP r on the restored lake is 0.534 (R² 0.285, n=457 pairs) —
  weaker than contact (0.843), not zero. The thesis direction stands;
  the number was overstated.
- FINDING 2 — the committed persistence artifacts were NOT reproducible
  from the lake as found. Re-running src/bml_cycle21_multiyear.py +
  src/bml_cycle23_ci.py on the lake in the working tree (543 hitting
  rows, 2023-2026 only) reproduced ONLY the 2025→2026 pair exactly and
  dropped the 2022→2023 pair entirely. Root cause: the lake is gitignored
  and src/ingest.py's init_schema DROPs stat_lines and reloads only
  qualified rows; a later reload wiped the Cycle 21 backfill (2022-2024
  leaders-based rows, 1,026 player-seasons) and its raw cache, which no
  longer exists in this environment. The platform (ingest_platform.py)
  does NOT touch the lake — the hazard is the legacy loader, which
  remains runnable. Follow-up for a later cycle: poka-yoke ingest.py
  (refuse to DROP a lake holding seasons it will not reload) or retire
  it; until then, never run src/ingest.py against a backfilled lake.
- RESTORE (this cycle, live MLB Stats API, committed script only):
  re-ran src/backfill_players.py — stored counts reproduced Cycle 21
  exactly (2022=262, 2023=243, 2024=241). The restored lake initially had
  223 duplicate (season, player) rows where the legacy qualified reload
  overlapped the backfill; all 223 pairs had byte-identical stat_json,
  so deleting the legacy copy was value-neutral. Restored lake: 1,066
  hitting rows (Cycle 21's 1,026 + 40 legacy-only qualified rows for
  2023/2024), 466 players. Re-running both persistence scripts on it:
  2025→2026 identical to committed on every figure; other pairs moved
  by ≤0.05 (extra 40 rows + larger n: pairs n=133/141/103/80 vs
  committed 125/124/93/80); pooled contact r = 0.843 (95% CI 0.810-0.872,
  457 pairs) vs committed 0.83 (0.792-0.862, 422 pairs). Verdict still
  STABLE (contact r ≥ 0.6 in every pair). Pooled on the restored lake:
  contact 0.843, BB% 0.721, ISO 0.613, OBP 0.534.
- WHAT THIS PR CHANGES (owner call — claim numbers move, so left open,
  NOT merged): data/player_persistence_multiyear.json +
  data/persistence_ci.json refreshed to the restored-lake recomputation
  (same scripts, same MIN_PA=200 method, real MLB API data); Story
  chapter 3, talk-track THE EDGE + back-pocket numbers, and exec summary
  rewritten to the new figures (OBP pooled 0.53, per-pair 0.58/0.59/0.55/
  0.30; pooled contact 0.84, CI 0.81-0.87; pooled walk 0.72; 466 players;
  error cut 42-57%). The one-pager needs no change: it quotes only the
  latest pair (contact 0.899, BB 0.655, OBP 0.298, n=80), which is
  unchanged, and its n==80 assertion still passes. Dashboard Figure 3
  itself was always honest (it plots the per-pair bars); only the prose
  headlines generalized the last pair.
- Platform run this cycle, on main f8ab2726 (unmoved since Cycle 38):
  ingest 21 datasets, 0 failures; Savant volumes in band (expected
  651-673, bat-tracking 595-619, sprint 489-506); NPB BIS leaderboards
  340 rows; curate 14 tables, all contracts pass; warehouse rebuilt;
  parity r = 0.889, 201 matched; curated byte-identical to main (no
  data PR from the platform step); gate ALL PASS on the rebuilt
  dashboard (23 figures, Story 6 chapters, Boardroom ≤15 slides,
  Explorer all 23, 8 percentile cards, Figure 23 Explorer-only).
- Spotrac probe (once per run): still 403. FanGraphs probe (once per
  run): still 403 Cloudflare. Salaries remain 24/30, forced-seller 6/7
  (CHC uncovered); the reconciled-FanGraphs lane stays closed under
  the Cycle 32 guard — it reopens only on a 200 probe.
- Verified by DOM/data checks only (no browser visual QA, per standing
  rule): gate ALL PASS after the copy + data refresh; dashboard rebuild
  holds figures 1-23 with no duplicates.
- Next: owner decision on this PR (merge = new persistence numbers go
  live); otherwise item (h) continues — next drift re-run or the
  ingest.py poka-yoke; no new claims.

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

## Cycle 43 — DRIFT RE-RUN: CYCLE 23 PERSISTENCE + INGEST.PY POKA-YOKE (toby, 2026-11-02 ~07:12 PT, overnight sprint)
- Backlog item (h): re-ran src/bml_cycle23_ci.py (persistence with
  bootstrap CIs, MIN_PA=200) on the current lake and diffed the
  regenerated data/persistence_ci.json against the committed artifact.
- Result: NOT byte-identical — and the cause is already diagnosed, not
  new drift. Exactly as Cycle 39 found: the lake in this environment
  holds only 2023-2026 (543 hitting rows) while the committed artifact
  was computed on the Cycle 21 backfilled lake (2022-2026, 1,026
  player-seasons). The re-run reproduces ONLY the 2025->2026 pair
  exactly (n=80, contact r=0.899, BB% 0.655, OBP r=0.298 — every figure
  identical to committed) and drops the 2022->2023 pair entirely;
  other pairs move because n shrinks (2023->2024 n=84 vs 124,
  2024->2025 n=88 vs 93; pooled contact 0.872 on 252 pairs vs committed
  0.83 on 422). No upstream source moved: the 2025->2026 exact match
  on the same script + same lake rows rules that out. The regenerated
  file is NOT shipped — data/persistence_ci.json stays at the
  committed version, and this run changes no claim, figure, or number
  in the demo. The Cycle 39 restored-lake recomputation (PR #21, still
  open) remains the owner's call.
- Shipped instead, closing Cycle 39's flagged follow-up: the
  ingest.py poka-yoke. src/ingest.py's init_schema() used to DROP
  stat_lines/players unconditionally while main() reloads only
  2025-2026 — the mechanism that wiped the 2022-2024 backfill. Now
  init_schema() inspects the existing lake first and raises (fail
  closed, lake untouched) if it holds any season outside
  RELOAD_SEASONS=(2025, 2026), naming the seasons at risk and refusing
  the drop. Verified on copies of both lakes, not on live data: the
  subset lake (2023-2026) is refused with seasons [2023, 2024]
  named and all 743 rows intact; the restored lake is refused with
  [2022, 2023, 2024] named and all 1,266 rows intact; a fresh lake
  initializes normally; a reload-only (2025-2026) lake reloads
  normally. The legacy loader can no longer silently destroy a
  backfilled lake; the platform (ingest_platform.py) never touched
  the lake and is unchanged.
- Platform run this cycle, on main c16280d0 (unmoved since Cycle 42):
  ingest skipped per the sprint courtesy (Cycle 42's ingest ran
  within the hour, no source changes, main unmoved); curate 14
  tables, all contracts pass; warehouse rebuilt; parity r = 0.889,
  201 matched; curated Parquet + build report byte-identical to main
  (no data PR from the platform step); gate ALL PASS; dashboard
  rebuilds with the 23-chart index intact (Story 6 chapters,
  Boardroom <=15 slides, Explorer all 23 figures, 8 percentile
  cards, Figure 23 Explorer-only with BIS label).
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

## Cycle 44 — ACCURACY STACK: PERSISTENCE CORRECTION LANDED + LABELED SALARY LAYERS + CROSSWALK + IL HISTORY (toby, 2026-11-02 ~08:20 PT)

- Owner directive (2026-11-02 08:11 PT): "do what takes to make
  accurate, optimal and professional." That is this cycle's
  authorization, including merging on gate pass and superseding
  PR #21. Base: current main 93cb55ce (verified live before building;
  fresh tarball tree, kpi.py clean).
- (1) PERSISTENCE ACCURACY FIX — PR #21 SUPERSEDED, CORRECTION
  LANDED. A direct merge of PR #21 failed (mergeable=False/dirty
  against main after Cycles 40–43), so the correction was re-applied
  by hand onto current main: PR #21's versions of
  src/dashboard_p6.py (1 claim hunk), docs/TALKTRACK.md (2 hunks),
  docs/EXEC_SUMMARY.md (1 hunk), data/player_persistence_multiyear.json
  and data/persistence_ci.json (restored-lake recompute), plus its
  Cycle 39 BML entry inserted in chronological position. Current main
  wins on everything unrelated (Cycles 40–43 entries intact). The
  corrected claims: OBP pooled r ≈ 0.53 (per-pair 0.58/0.59/0.55/0.30),
  contact pooled r = 0.84 (95% CI 0.81–0.87), walk pooled r = 0.72,
  466 players / 457 pairs, error cut 42–57%. No other claims changed.
  PR #21 is closed as superseded with an explanatory comment.
- (2) COT'S AS SECOND LABELED DATASET (owner option b). New
  src/bml_cycle44.py builds data/salaries_cots_2027.json from the
  Cycle 41 mirror cache: 237 rows, 30 teams — every player with a
  published Cot's LRP-2027 dollar figure, each row labeled
  source=cots_baseball_prospectus, basis in the file metadata (LRP:
  PV deferrals, buyout option years). data/salaries_2026.json
  UNTOUCHED; forced-seller math UNCHANGED (still 6/7, CHC uncovered,
  on the Spotrac-basis file). Curated as fact_salaries_cots.
- (3) BREF WAR SALARY CROSS-CHECK — FAILED CLOSED. BRef's salary
  column is real but partial (2026: 495 player-team rows, ~30% of
  players). Reconciliation (workpaper data/salary_recon_cycle44.json):
  vs the Spotrac-basis file, 195/927 matched (21.0%), 28.7% within
  $50k — basis difference by construction (2026 actual vs the file's
  2027 basis). Vs Cot's LRP-2026 (same season) for the 6 gap teams:
  114 matched, 71.1% within $50k — under the 80% credibility bar, so
  NO BRef salary dataset ships. Disagreements are documented
  convention gaps (traded players: Cot's books the acquiring club's
  share, BRef the full-season figure; deferred/PV cases). The WAR
  files land in the raw zone for WAR cross-checks only.
- (4) CHADWICK REGISTER CROSSWALK — ADOPTED. ingest_platform gains a
  chadwick task (16 keyless GitHub shards, ODC-BY; 527,990 person
  rows landed); curate gains dim_player_xwalk (137,320 rows with an
  MLBAM key; Retro/BRef/FanGraphs/NPB/Wikidata keys). Join proof:
  379/379 dim_player registry players matched (100%); 370 carry
  FanGraphs IDs, 17 carry NPB keys.
- (5) INJURY REPORT IL HISTORY — ADOPTED. ingest gains an
  injury_report task (keyless CSV from MLB IL transactions); curate
  gains fact_il_stints: 6,632 stints, 2,177 players, 2019–2026 (the
  site's headline says 6,651 injuries; its CSV parses to 6,632
  stints — we count the CSV). Cross-check layer only: Cycle 27
  availability factors and all roster math unchanged.
- (6) KEY-BASED SOURCES PREP — DOCS + STUBS, NO SIGNUPS, NO KEYS.
  src/keyed_sources.py: env-key-gated fail-closed stubs for Tank01,
  Statyx, FastballAPI, Sportradar (verified: all four return labeled
  "data unavailable" with no key and make no network call).
  Scorecard + DATA_PLATFORM carry ready-to-activate entries;
  Sportradar trial flagged DO NOT START before mid-Nov (30-day
  window must cover Dec 1).
- Platform run this cycle, on the final tree: ingest 25 datasets,
  0 failures (Savant volumes in band; NPB BIS 340; transactions
  watermark at 120,355 events; FanGraphs Steamer raw pull answered
  this run — curated tables still build from the committed artifacts,
  byte-identical); curate 17 tables, all contracts pass (14 prior
  tables byte-identical, 3 new); warehouse rebuilt from 17 tables;
  parity r = 0.889, 201 matched; dashboard rebuilt (23 figures,
  corrected persistence copy live in Story ch. 3); gate ALL PASS
  (offline and --live, standings 30/30); spellcheck green.
- Spotrac probe (once per run): still 403 (CHC page). Salaries for
  the demo's math remain 24/30 Spotrac-basis, forced-seller 6/7 —
  now with a labeled Cot's layer beside them, stated as such.
- Verified by DOM/data checks only (no browser visual QA, per
  standing rule).
- Next: Sportradar trial decision mid-Nov (owner starts it, Toby
  wires it); the 24/7 cycle continues its drift/polish backlog.

## Cycle 45 — SOURCES FOOTER + API CONNECTIONS: STATYX & FASTBALLAPI LIVE (toby, 2026-11-02 ~10:25 PT)

Owner directives (2026-11-02 10:10–10:13 PT): "update repo so that
hardball shows all API sources at bottom of page when rendered! its
key for credibility! we just got two more!" and "make sure git knows
we have these apis as other agents collab on hardball project!"

- (1) CONNECTION EVENT — STATYX + FASTBALLAPI CONNECTED 2026-11-02.
  Both keys were supplied by the owner and live in Toby's Secure
  Vault connectors (custom.statyx / custom.fastballapi); keys are
  NEVER committed to git. Verified live by Toby before this cycle
  built on them: Statyx standings 200, injuries 200 with 16 live
  records (free tier DOES include MLB injuries — Cycle 44's open
  question, settled); FastballAPI standings 200 / 30 teams,
  injuries 200 with 190 records dated 2026-11-02. Committed
  connection record: HANDOFF.md ("API CONNECTIONS" section) +
  docs/DATA_PLATFORM.md ("API connections — Statyx + FastballAPI
  LIVE") + docs/CARPE_SCORECARD.md Cycle 45 addendum. Access route
  for other lanes: through Toby / the 6-hourly cycle, never a repo
  key hunt. No AGENTS.md exists anywhere in this repo (checked the
  full git tree) — HANDOFF.md is the collaborators' surface, so the
  record lives there and in DATA_PLATFORM.md.
- (2) DASHBOARD FOOTER — the rendered page's bottom sources box now
  carries an "ALL DATA & API SOURCES" enumeration: every source
  with what it provides and an honest status label — MLB Stats API
  (live, keyless), Baseball Savant (live, keyless), ESPN (verified
  cross-validation), FanGraphs Steamer (committed snapshot, site
  403 to automated pulls), Spotrac (committed, 24/30), Cot's
  (committed labeled cross-check layer, 30 teams / 237 rows),
  Chadwick Register (committed, joins 379/379), The Injury Report
  (committed, 6,632 stints), NPB official BIS (committed, keyless),
  Baseball-Reference WAR files (salary use FAILED CLOSED Cycle 44,
  stated on the page), Statyx (connected 2026-11-02, verified
  live), FastballAPI (connected 2026-11-02, verified live). Tank01
  (deferred — owner dropped the RapidAPI signup for now,
  2026-11-02) and Sportradar (trial starts mid-Nov) are listed
  explicitly as NOT yet connected and sources of nothing on the
  page. Presentation only — no data, figure, or claim changes;
  still 23 figures, Story 6 chapters / Boardroom ≤15 / Explorer
  all figures. Gate gains a footer check: all 13 source strings
  must appear in the rendered HTML. Spellcheck whitelist gains the
  Cycle 45 provider names.
- (3) src/keyed_sources.py CORRECTED TO VERIFIED REALITY.
  FastballAPI: base https://mcp.fastballapi.com/v1, tools are POST
  /v1/{tool} with a JSON body, key in the x-api-key header (the
  Cycle 44 Bearer-at-fastballapi.com entry was wrong — caught
  against the provider's own Python client during connection).
  Statyx: Bearer at api.statyx.io (was already correct), marked
  ACTIVE/VERIFIED with the record counts. Tank01 unchanged
  (X-RapidAPI-Key; status: deferred by the owner). Sportradar unchanged (DO NOT
  START before mid-Nov). Fail-closed behavior re-verified: with no
  env keys, all four return labeled "data unavailable" and make no
  network call.
- (4) CROSS-CHECKS (fresh pulls this cycle; FastballAPI cost 4
  credits of the 500/mo free pool — standings 2 + injuries 2;
  Statyx free). Standings: FastballAPI 2026 vs committed
  StatsAPI-derived data — vs data/kpi_2026.json, 30/30 teams,
  wins 30/30 agree, runs scored 30/30 agree, ZERO diffs; vs
  curated fact_team_season (carries losses), 29/29 comparable
  teams agree on wins + losses + runs allowed (Arizona is keyed
  "AZ" in the curated table vs "ARI" at FastballAPI — an
  abbreviation artifact, already covered by the KPI comparison).
  Injuries: 14 of Statyx's 16 records also appear in
  FastballAPI's 190 by player name (87.5%), all 14 agreeing on
  status AND injury type; Statyx-only: Brooks Kriske, Jalen Beeks
  (Statyx reads as a recent-moves feed vs FastballAPI's full IL
  snapshot — complementary, not contradictory). Full detail in
  the CARPE_SCORECARD Cycle 45 addendum. Neither feed feeds any
  figure or model yet — connecting + cross-checking is this
  cycle; wiring them into the availability layer is a future
  measured cycle, not a silent swap.
- Platform run this cycle, on the final tree: ingest 25 datasets,
  0 failures (Savant volumes in band — bat-tracking 595–619 per
  season; transactions watermark at 120,355 events; Chadwick
  527,990; Injury Report 6,632; NPB BIS 340; Spotrac cache
  present); curate 17 tables, all contracts pass, byte-identical
  to committed; warehouse rebuilt from 17 tables; parity
  r = 0.889, 201 matched; dashboard rebuilt from committed
  snapshots (23 figures; footer verified present by text/DOM
  check — all source names render below the three modes); gate
  ALL PASS (offline and --live, standings 30/30) incl. the new
  footer check; spellcheck green.
- Spotrac probe: not re-run this cycle (Cycle 44's 403 stands).
  Salaries remain 24/30 Spotrac-basis + labeled Cot's layer;
  forced-seller 6/7.
- Verified by DOM/data checks only (no browser visual QA, per
  standing rule).
- Next: Tank01 stays deferred unless the owner revives the
  RapidAPI signup (supplement only, nothing depends on it);
  Sportradar trial mid-Nov (owner starts it, Toby wires it); a future cycle
  decides, on measurements, whether the two live injury feeds join
  the availability layer.

## Cycle 46 — HS-1: HAKES–SAUER PRICING SCREEN, DATASET + FIRST REGRESSIONS (toby, 2026-11-02)

- Owner-approved MIT-gap programme (2026-11-02 12:57 PT), increment 1
  of 6: HS-1. Workpaper only — dashboard, talk track, and exec summary
  UNCHANGED (any verdict exhibit or re-headline is HS-2, and only if
  the verdict supports it). Base: main 021410f8 (verified live before
  building; fresh tarball tree, kpi.py clean).
- WHAT SHIPPED: `src/bml_cycle46.py` (full reproducible build, prints
  its own summary), `data/hakes_sauer_dataset.json` (142 player rows +
  metadata with basis labels and exclusion cascades),
  `data/hakes_sauer_results.json` (coefficients, SEs, p-values, R²,
  VIFs, quartile tables, sample notes), and the Cycle 46 addendum in
  docs/CARPE_SCORECARD.md.
- DESIGN: ln(2027 salary) on Marcel 2027 OBP, SLG, K%, BB% with age,
  Steamer WAR, and Steamer PA controls (spec A) plus a no-WAR spec B.
  Two samples, bases never mixed: S = Spotrac-basis file (2027 basis
  per Cycle 41), C = Cot's LRP-2027 aggregated from player-team rows
  to player level. Pitchers out of scope; two-way players excluded
  (the Spotrac "SP  /DH" spacing trap was caught in-build: the first
  run included the $70M two-way salary in the batting sample, the
  exclusion now matches the space-stripped position, and the dataset
  was re-verified to contain no two-way row).
- SAMPLES: S: 927 → −553 pre-arb flat-$1M placeholders → −219
  non-Bypassed arbitration projections → 155 real contracts → −68
  pitchers → −1 two-way → −26 incomplete → n = 60 (exactly at the
  pre-registered n≈60 floor; marginal). Cycle 41's 501/209 were the
  no-Cot's-counterpart subset; the whole-file rule is broader, and
  the difference is documented in the dataset metadata. C: 237
  player-team rows → 83 unique Marcel-matched players → −1 two-way →
  n = 82 (AAV sensitivity n = 76).
- FINDINGS (no verdict — that is the honest HS-1 result): no skill
  coefficient is significant in either sample (S: OBP −3.91 p = .549,
  SLG +2.73 p = .226, K% p = .798, BB% p = .519, R² = 0.359; C: OBP
  +3.31 p = .661, SLG +2.23 p = .414, K% p = .260, BB% p = .751,
  R² = 0.302; age significant in both). The descriptive OBP/SLG
  coefficient ratio flips sign across bases (−1.43 vs +1.48) and no
  in-repo run-value benchmark exists, so the formal HS
  proportionality test is deferred to HS-2. The non-parametric view
  points the thesis's way in both samples: top-quartile contact
  hitters' median $/WAR is ~half the bottom quartile's (S: $8.03M vs
  $14.98M, ratio 0.536; C: $6.19M vs $11.64M, ratio 0.532) — a
  descriptive contrast, labeled as such, not a price effect.
- LIMITS ON RECORD: active-contract cross-section, not HS's
  newly-signed-FA design; skills are projections (realized-2026
  sensitivity is qualified hitters only, descriptives only, no
  regression run on it); S covers 24/30 teams and sits at the power
  floor. Nothing failed closed except by design: no BRef-style new
  salary source was added, no blocked source was probed.
- Platform + gate on the final tree: ingest 25 datasets, 0 failures;
  curate contracts pass; warehouse rebuilt from 17 tables; parity
  r = 0.889 / 201 matched; dashboard rebuilt with lake at 23 figures;
  gate ALL PASS (offline). No browser visual QA (standing rule).
- Next: HS-2 (verdict exhibit + formal proportionality test, only on
  a supported verdict), then OPT-1 per the approved programme order.

## Cycle 47 — Figure 23 rebuilt as data storytelling (F23)

Owner-approved plan ("execute!", 2026-11-02). Figure 23's single
leaderboard panel became a 9-panel story — "three players, three
different bets" — inside the same figure number. Explorer-only;
Story (6 chapters) and Boardroom (15 slides) untouched; total figure
count unchanged at 23. No NPB→MLB translation factor claimed anywhere.

- **What shipped**
  - `src/bml_cycle47.py` — computes every new number into
    `data/fig23_rebuild_2026.json` from the two committed datasets
    (trio JSON + 340-row leaderboard CSV) and prints a verification
    table: **14/14 checks** — every trio leaderboard row re-derived
    from the CSV matches the trio dataset (PA/HR/RBI/BB/SO/AVG for
    Sato; ERA/IP/SO/BB/SV for both arms), Sato K% and Itoh BB%
    recomputed from raw counts match, and the fee on $60M reproduces
    the Cycle 34 worked example ($10.875M) exactly.
  - Panels: (1) Sato arc — BB% 7.3→9.5→11.1 climbing vs K% flat at
    ~27% (26.7% in 2026); (2) Itoh arc — IP bars 176.1/196.2/172.2
    with BB% 5.5/3.6/4.7; (3) Taira conversion — ERA bars by role
    (1.71 closer → 1.36 starter); (4) Taira workload — IP bars with
    the +93.8 jump annotated; (5) leaderboard-context percentile
    dots; (6) Sato K% vs the Central League qualified median (16.0%
    in 2026); (7) posting-fee curve $10M–$100M from the tier formula;
    (8) Imai projected vs signed; (9) the posting clock as a drawn
    timeline (Nov 2 → Dec 1 open, 29 days; Dec 1 → Dec 16 paused in a
    lockout, 15 days; Dec 1 marked as CBA expiry + demo deadline;
    Dec 16 17:00 ET signing deadline).
  - **Leaderboard context computed (2026, own-league qualified
    boards):** Sato #1 of 19 CL bats in HR (39), RBI (106) and OPS
    (.992) — 100th percentile three times over; Taira #1 of 11 PL
    ERA qualifiers (1.36) and #1 of 13 on the 2025 saves board (31);
    Itoh #2 of 11 in walk rate (4.7%, 90th percentile) but #7 of 11
    in ERA (3.18, 40th) — the thesis fit is walk suppression, and
    the figure says exactly that.
  - Companion HTML: trio cards kept; new Imai expectation-vs-reality
    strip; clock facts shortened (the timeline is drawn in-figure
    now); honesty box gains the computed-layer note.
  - `src/spellcheck_gate.py` WHITELIST += leaderboard (singular),
    src, py — the gate's sanctioned mechanism for verified spellings.
- **Data judgment calls, labeled in the figure and honesty box:**
  Itoh's 2024 BB% (5.5%) is computed from the leaderboard's
  batters-faced column (710 BF) — the trio dataset carries no 2024
  BF; his 2025–26 rates cross-check exactly. Taira 2024 stays absent
  (not on the qualified boards) — never backfilled. Pools are small
  and qualified-only; ranks are exact, percentiles coarse — labeled.
- **Verification:** platform clean (ingest 25 sources, curate 17
  tables, warehouse built), parity r = 0.889 / n = 201 unchanged,
  gate ALL PASS with Figure 23 present as Figure 23 in Explorer,
  spellcheck green. One build lesson: the first scratch build ran
  before the lake was copied in, a lake-dependent panel dropped out
  and the figures renumbered (Fig. 23 landed as 22) — the gate
  caught it; rebuilt with the lake present, all green. [VERIFIED]
- **Next:** the Fig. 23 panels update only when the posting window
  resolves (signings by Dec 16) or new BIS data lands; HS-2 follows
  Cycle 46's Hakes–Sauer workpaper.

## Cycle 48 — HS-2: HAKES–SAUER VERDICT EXHIBIT (toby, 2026-11-02)

- Owner-approved MIT-gap programme (2026-11-02 12:57 PT), increment 2
  of 6: HS-2. Base: main ed177ed3 (verified live before building;
  fresh tarball tree, kpi.py restored clean from the tarball).
- WHAT SHIPPED: `src/bml_cycle48.py` (benchmark + formal test +
  verdict, prints its own summary) writing
  `data/hakes_sauer_verdict.json`; Figure 24 (Explorer, Check the
  Model group) via `panel_hs_verdict()` + the verdict box
  (`_hs_verdict_html()`, text rendered verbatim from the artifact);
  figure count 23 → 24 across dashboard source, gate, README,
  TALKTRACK, EXEC_SUMMARY, and the ONEPAGER generator (regenerated:
  24 figures, 17 curated tables, parity r = 0.889 / 201). Figures
  1–23 keep their numbers — Figure 24 is appended last in the build
  order, so Story (6 chapters) and Boardroom (15 slides) are
  untouched. Spellcheck WHITELIST += sauer, misprices, mispricing,
  underprices, workpaper (verified spellings).
- BENCHMARK ATTEMPT — SURVIVED, LABELED AGGREGATE: pre-registered
  criteria fixed before estimation (FE coefs > 0, p < 0.10, VIF < 10,
  ratio CI finite excluding 0). Runs per PA on OBP + SLG,
  fact_team_season, 480 unique team-seasons 2011–2026 (29 duplicated
  2026 rows in the committed table differ only in payroll-cell
  formatting; batting fields identical, deduped, noted in the
  artifact — curate.py itself unchanged). Season-FE: OBP +0.262
  (p ≈ 1.8e-26), SLG +0.278 (p ≈ 1.9e-85), within R² = 0.865,
  VIF 2.45; rho = 0.94, 95% CI 0.72–1.17 (pooled sensitivity 0.66,
  0.44–0.88; per-season median 1.00). Ecological limit on record:
  team aggregates split OBP/SLG's joint variation (corr 0.77 through
  batting average), so the aggregate ratio sits below event-level
  linear-weights values — labeled wherever the benchmark is used.
- FORMAL TEST — INCONCLUSIVE BY POWER: HS-1 spec A refit from the
  committed dataset reproduces HS-1's published coefs/SEs exactly
  (asserted in code, max dev < 0.01). Wald vs FE rho: S (n = 60)
  contrast −6.49, SE 8.05, p = 0.42; C (n = 82) contrast +1.21,
  SE 9.43, p = 0.90 (pooled rho: p = 0.45 / 0.84). The ratios
  neither sample can reject at 5% span the whole scanned range
  [−20, +20] — correct pricing and large mispricing both survive.
- VERDICT (exact text rendered in Figure 24's box): INCONCLUSIVE on
  mispricing; descriptive $/WAR contrast consistent across both
  bases (0.54× / 0.53×); the defensible claim is persistence +
  cap-efficiency + low variance, not proven undervaluation. Design
  limit stands: active-contract cross-section, not newly-signed FAs.
- CLAIM HYGIENE: grep of dashboard source, EXEC_SUMMARY, TALKTRACK,
  README, ONEPAGER found NO unqualified undervalued/mispriced
  assertion about contact/OBP to replace — surfaces already carry
  the measured language. Additive hygiene only: verdict + Figure 24
  cite added to EXEC_SUMMARY's do-NOT-claim section, TALKTRACK's
  honesty section + back-pocket numbers, and the dashboard sources
  box. Thesis untouched (winning-cheap via contact + OBP +
  availability stands as strategy).
- Platform + gate on the final tree: ingest 25 datasets, 0 failures;
  curate 17 tables, contracts pass, parquets byte-identical to
  committed; warehouse rebuilt; parity r = 0.889 / 201 matched;
  dashboard rebuilt with lake at 24 figures; gate ALL PASS (offline,
  incl. new Figure 24 + HS-2 artifact checks); spellcheck green.
  No browser visual QA (standing rule).
- Next: OPT-1 (roster optimizer) per the approved programme order.

## Cycle 49 — OPT-1: ROSTER OPTIMIZER — EXACT MILP VS CYCLE 26 GREEDY (toby, 2026-11-02)

- Owner-approved MIT-gap programme (2026-11-02 12:57 PT), increment 3
  of 6: OPT-1. Base: main 5a80d614 (verified live before building;
  fresh tarball tree, kpi.py verified clean from the tarball).
  GitHub Actions ignored per the owner's 2026-11-02 directive (minutes
  exhausted until Dec 1) — local gate + platform + parity carry the
  verification, as in Cycles 44-48.
- WHAT SHIPPED: `src/bml_cycle49.py` (greedy reproduction + MILP +
  DH sensitivity, prints its own summary) writing
  `data/optimizer_comparison_2027.json` (full greedy, optimizer, and
  DH-restricted rosters for all three budgets); Figure 25 (Explorer,
  Build a Roster group) via `panel_optimizer()` + the facts box
  (`_optimizer_html()`, numbers rendered from the artifact); figure
  count 24 -> 25 across dashboard source (docstring, index, button,
  Explorer), gate expectations (+ new Figure 25 and OPT-1 artifact
  checks), README, TALKTRACK (+ back-pocket Q&A), EXEC_SUMMARY, and
  the ONEPAGER generator (regenerated: 25 figures). Spellcheck
  WHITELIST += combinatorics, dh, milp, scipy (sanctioned mechanism).
- GREEDY REPRODUCTION (asserted in code before optimizing): Cycle 26's
  build_roster on the identical 199-player pool reproduces
  wow_scenarios.json exactly — Floor 42.0 WAR / $170,955,000; Middle
  45.7 / $207,293,333; Cap 52.3 / $244,620,833; identical 26 names at
  every budget.
- RESULTS (all three optima PROVEN, HiGHS gap 0): Floor 42.0 -> 48.9
  WAR (+6.9, +16.4%; spend $171.1M; overlap 16/26). Middle 45.7 ->
  52.8 (+7.1, +15.5%; $207.8M; 17/26). Cap 52.3 -> 54.8 (+2.5, +4.8%;
  $245.2M; 21/26). The optimizer's floor roster (48.9) beats the
  greedy's middle roster (45.7) outright.
- DECOMPOSITION: DH-restricted sensitivity (DH open only to DH-mapped
  players = the greedy's effective search space) still finds +5.5 /
  +5.2 / +0.4 — the floor/middle edge is mostly combinatorics; the cap
  edge is mostly the DH rule (+2.1 of +2.5). The greedy carries
  Dominic Smith (0.01 WAR) at DH at all three budgets because Cycle
  26's any-bat fallback never triggers with two DH-mapped players in
  the pool; the optimizer plays Brandon Lowe (2.32 WAR) there.
- 15% PER-PLAYER RULE: binds nobody in the pool at prior-AAV anchors
  (max $35.0M < $36.795M); all three greedy rosters satisfy it
  (max AAV $22.0M / $32.0M / $32.0M); enforced as a hard constraint in
  the optimizer and checked in the gate for both methods.
- SCOPE KEPT: Figure 16 rosters and all Story/Boardroom numbers
  unchanged. Optimizer rosters replacing greedy ones is OPT-2 / owner
  territory.
- Platform + gate on the final tree: ingest 25 datasets, 0 failures;
  curate 17 tables, contracts pass, parquets byte-identical to
  committed; warehouse rebuilt; parity r = 0.889 / 201 matched;
  dashboard rebuilt with lake at 25 figures; gate ALL PASS (offline,
  incl. new Figure 25 + OPT-1 artifact checks); spellcheck green.
  No browser visual QA (standing rule).
- Next: OPT-2 (optimizer sensitivity + mixed pre-arb+FA floor roster)
  per the approved programme order.

## Cycle 50 — OPT-2: OPTIMIZER SENSITIVITY + MIXED PRE-ARB/FA FLOOR (toby, 2026-11-02)

- Owner-approved MIT-gap programme (2026-11-02 12:57 PT), increment 4
  of 6: OPT-2. Base: main 261a9645 (verified live before building;
  fresh tarball tree, kpi.py verified clean from the tarball).
  GitHub Actions ignored per the owner's 2026-11-02 directive (minutes
  exhausted until Dec 1) — local gate + platform + parity carry the
  verification, as in Cycles 44-49.
- WHAT SHIPPED: `src/bml_cycle50.py` (imports Cycle 49's solver and
  pool builder unchanged; asserts a base re-solve reproduces OPT-1's
  three rosters exactly before varying anything) writing
  `data/optimizer_sensitivity_2027.json`; Figure 25 extended with a
  sensitivity strip + mixed-build block (`_optimizer_sensitivity_html()`,
  numbers rendered from the artifact; figure count stays 25); gate
  gains an OPT-2 artifact check; spellcheck WHITELIST += the 15
  pre-arb surnames the strip renders (sanctioned mechanism).
- PRICE SENSITIVITY (all solves PROVEN, gap 0): anchors x0.8 ->
  Floor 53.2 / Middle 55.5 / Cap 55.9 WAR (churn 6/6/4 of 26);
  x1.2 -> 45.0 / 48.5 / 50.4 (churn 3/4/4). The 15% rule is applied
  to scaled prices: at x1.2, Rendon ($42.0M) and Skubal ($38.4M)
  cross the $36.795M max and are excluded.
- TARGETED BID-UP: only OPT-1's 26 floor-roster players at x1.2,
  floor re-solved: 45.6 WAR, churn 6 — the solver walks away from
  6 of its own targets, its ace Skubal included, and still lands
  within 3.3 WAR of the base optimum.
- WAR HAIRCUT (Steamer WAR x0.85 at age 33+, 93 of 199 pool players):
  rosters chosen under pessimism re-score on base WAR at 48.8 /
  52.8 / 54.8 vs base optima 48.9 / 52.8 / 54.8 (middle roster
  unchanged, churn 0); each haircut roster carries 2 players 33+.
- MIXED PRE-ARB + FA FLOOR: pre-arb pool from salaries_2026.json
  status exactly "Pre-Arbitration" — 553 rows, 509 usable (42 no
  ID, 1 duplicate, 1 no Steamer WAR, 0 in the FA class) — priced at
  the $1.0M placeholder convention (labeled as such everywhere),
  Steamer WAR, POSMAP positions. Floor solve on the 708-player
  mixed pool: 74.8 WAR (+25.9 vs FA-only 48.9) for $96.2M, 19
  pre-arb slots (53.0 WAR) / 7 FA slots, $75.0M of the floor
  unspent, proven optimal. Framed strictly as internal production
  a club develops or holds — not a shopping list.
- SCOPE KEPT: Explorer/workpaper only. Figure 16 rosters, Story
  (6 chapters) and Boardroom (15 slides) unchanged; replacing the
  greedy rosters remains an owner decision, explicitly out of scope.
- Platform + gate on the final tree: ingest 25 datasets, 0 failures;
  curate 17 tables, contracts pass, parquets byte-identical to
  committed; warehouse rebuilt; parity r = 0.889 / 201 matched;
  dashboard rebuilt with lake at 25 figures; gate ALL PASS (offline
  AND --live, standings 30/30, incl. the new OPT-2 artifact check);
  spellcheck green. No browser visual QA (standing rule).
- Next: UNC-1 (availability-cap out-of-sample backtest) per the
  approved programme order.

## Cycle 51 — API-1: STATYX + FASTBALLAPI WIRED INTO THE PLATFORM (toby, 2026-11-02)

- WHY: Cycles 44–45 left the two keyed feeds connected + verified
  but serving nothing — no figure or model read from them. The
  owner called it out ("does my hardball project get service from
  new APIs statyx and fastball?"). This cycle makes them serve.
- PULLED (2026-11-02, one call per endpoint, all HTTP 200, via the
  vault connector helpers — keys never in repo): Statyx injuries
  first page 50 records + standings 50 rows (no team names; raw
  only); FastballAPI get_injuries 190 records + get_standings
  30 teams. FastballAPI credits spent: 4 of 500/mo. Statyx free.
- WHAT SHIPPED: `src/bml_cycle51.py` (pull mode via helpers, fail
  closed on any non-200; offline build from committed snapshots
  with sha256 assertion) → `data/il_current_live.json`; dated raw
  snapshot envelopes in `data/raw/{statyx,fastballapi}/` +
  `data/raw/manifest.jsonl` entries; new curated table
  `fact_il_current` (196 rows) registered in `src/curate.py` with
  a declared contract; health-figure live-IL sub-panel in
  `src/dashboard_p6.py` (figure count stays 25); footer lines for
  both feeds now read SERVING and name the layer; gate checks for
  the artifact + panel in `src/verify_data.py`;
  `src/keyed_sources.py` statuses updated to SERVING.
- RECONCILIATION (in the artifact): union 196 players (44 in both
  feeds); FA overlay 13 of 251 FAs currently listed injured; 12/13
  agree with the static layer (on IL at 2026 season end); 1 differs
  — Garrett Whitlock (static stints all closed; live feed: Out,
  leg fracture, return 2027-02-01). Standings cross-check:
  FastballAPI vs kpi_2026, 30/30 wins + runs agree, zero diffs.
- Platform + gate on the final tree: ingest 25 datasets,
  0 failures; curate 18 tables, contracts pass, prior 17 parquets
  byte-identical to committed; warehouse rebuilt (18 tables);
  parity r = 0.889 / 201 matched; dashboard rebuilt with lake at
  25 figures; gate ALL PASS (offline AND --live, standings 30/30,
  incl. the new API-1 checks); spellcheck green. GitHub Actions
  ignored per the owner's blackout directive (until Dec 1). No
  browser visual QA (standing rule).
- Next: UNC-1 (availability-cap out-of-sample backtest) per the
  approved programme order; the roster SWAP runs after API-1 per
  the owner's "need all 1-3" approval.

## Cycle 52 — SWAP: OPTIMIZER ROSTERS BECOME THE HEADLINE (toby, 2026-11-02)

- WHY: OPT-1 (Cycle 49) proved the exact optima on Cycle 26's
  identical inputs — 48.9 / 52.8 / 54.8 WAR vs the greedy builds'
  42.0 / 45.7 / 52.3. OPT-2 (Cycle 50) stress-tested the optima.
  The owner approved the promotion on 2026-11-02 ("sounds like need
  all 1-3"), with the research condition that the optimizer is
  headlined but never as bare numbers: ranges and labels travel
  with the figures.
- WHAT SHIPPED: `src/bml_cycle52.py` (promotion only, no new
  solves) rewrites `data/wow_scenarios.json`: `scenarios` is now
  the Cycle 49 optimizer set, each entry carrying its Cycle 50
  price-error range; the greedy set moves verbatim to
  `benchmark_greedy` (scenarios + their Cycle 27 stress totals).
  The Cycle 27 availability stress is recomputed on the new totals
  with Cycle 27's exact method (unrounded pool mean / p25-index):
  44.6 / 48.1 / 50.0 WAR at the mean factor, 43.5 / 47.0 / 48.8 at
  p25; floor/cap ratio 0.803 -> 0.892; measured subset now 13 of
  35 rostered players.
- SURFACES: Figure 16 panel (title carries "WAR proven-optimal
  (low–high across ±20% price error)"; sub-copy: floor captures
  ~89% of cap WAR, last $74.1M buys 5.9 WAR, anchor label kept);
  Story chapter 5 and Boardroom slide 12 quote the optimizer
  values with ranges; Figure 25 + its facts box + the Explorer
  group framing become "benchmark vs headline"; README,
  EXEC_SUMMARY (honesty paragraph rewritten + Cycle 52 addendum),
  TALKTRACK (money-buys script, optimizer back-pocket Q&A,
  back-pocket numbers), ONEPAGER regenerated (ratio 89%, subset
  counts read from the artifact, "~10 WAR" corrected to 5.9).
- GATE: two new checks in `src/verify_data.py` — headline values
  equal the Cycle 49 artifact with Cycle 50 ranges attached and
  the greedy benchmark preserved; Story/Boardroom HTML carries
  the new headline and none of the old. Platform + gate on the
  final tree: ingest 25 datasets / 0 failures; curate 18 tables,
  contracts pass, all 18 parquets byte-identical to committed;
  warehouse rebuilt; parity r = 0.889 / 201; gate ALL PASS
  (offline AND --live, standings 30/30); spellcheck green.
  GitHub Actions ignored per the owner's blackout directive
  (until Dec 1). No browser visual QA (standing rule).
- Next: UNC-1 (availability-cap out-of-sample backtest) per the
  approved programme order.
