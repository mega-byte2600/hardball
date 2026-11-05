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

---
## Cycle 53 — FIG-QA: full audit of Figures 1–25 (2026-11-02, owner-directed)
- Built: per-figure trace audit of the whole dashboard — every
  rendered number checked against its committed source artifact;
  trace table (figure → artifact(s) → check method) recorded as
  the CARPE_SCORECARD Cycle 53 addendum. Gate extended with 25
  FIG-QA checks in `src/verify_data.py`, one per figure, each
  computing its expected value from the artifact at gate time.
- Fixed (7 edits, no claim changes): stat card pooled contact
  r = .83 / 422 pairs → .84 / 457 (persistence_ci.json); Story
  appendix latest-pair-only r = .90 / .66 → pooled .84 and walk
  .66–.77 across pairs; EXEC_SUMMARY "pooled walk r = 0.72"
  (no such artifact value) → per-pair range; EXEC_SUMMARY P7
  line PENDING → owner-recorded MVP approval 2026-10-31;
  player-card Steamer WAR 2 dp → 1 dp; Figure 16 roster-table
  WAR 2 dp → 1 dp; bottom-line "roughly half payroll" →
  traced fraction (~ a third; ~95 trio avg vs ~79 rest-of-league
  avg, computed from kpi_2026.json); Story chapter 5 floor
  range completed to 45.0–53.2 across ±20% price error.
- Measured: figures traced 25/25. Defects by class — stale
  numbers 2, untraceable-as-stated 2 passages (3 values),
  convention violations 4, count mismatches 0 open. Figure
  numbering/titles verified identical across dashboard build
  order, Explorer, README, TALKTRACK, EXEC_SUMMARY, ONEPAGER;
  pre-swap numbers (42.0/45.7/52.3, stress 38.3/41.7/47.7)
  survive only as labeled benchmark/historical context.
- Owner item (held, not fixed): Figure 9's projections_2026
  values are in-sample fits (model_p6.py) under a
  "Model-projected wins" title with no in-sample label — a
  disclosure/claim call for the owner.
- GATE: platform + gate on the final tree — ingest 25
  datasets / 0 failures; curate 18 tables, contracts pass;
  warehouse rebuilt; parity r = 0.889 / 201; gate ALL PASS
  offline (65 checks, was 40) and --live (66, was 41);
  spellcheck green. GitHub Actions ignored per the owner's
  blackout directive (until Dec 1). No browser visual QA
  (standing rule).
- Next: feed-architecture cycle (FastballAPI census + Statyx
  event layer) per the owner's 2026-11-02 design direction,
  then UNC-1.

## Cycle 54 — UNC-1: AVAILABILITY-CAP OUT-OF-SAMPLE BACKTEST (toby, 2026-11-02)

- NUMBERING NOTE: this is the programme's UNC-1 increment. It is
  numbered 54, not 53, because the parallel lane merged its own
  Cycle 53 (FIG-QA, PR #35) onto main 8b604edf while this cycle was
  being built; this cycle rebased onto that head before shipping.
  No FIG-QA file is touched here.
- WHY: programme increment 5 of 6. The demo caps projected PA by
  measured availability (Cycle 9: proj_PA_health = proj_PA x avail_pct
  from prior-2-season IL days) and Cycle 27 stress-tests rosters the
  same way — but nobody had ever tested, out of sample, whether the
  cap improves a forecast. UNC-1 is that test, on the FA classes
  entering 2022, 2023, 2024.
- METHOD (declared before running; script `src/bml_cycle54.py`):
  FA class T = "Signed as Free Agent" transactions Nov (T-1)–Apr (T)
  from the MLB Stats API (the committed transactions stream starts
  Dec 2024, so these historical classes are pulled fresh, monthly,
  sequential; any non-200 aborts with no artifact). Evaluation set =
  class members with a qualified hitting line in season T (same pool
  as the lake loader). Actuals: lake for 2023/2024, fresh pulls for
  2022; priors: lake where present, fresh pulls for 2020–2022 (the
  protected lake is read-only here). Availability: committed
  fact_il_stints days summed per player-season, capped at 182/season
  (263 player-seasons sum above 182 from overlapping stint rows),
  over T-2 and T-1, avail = clip(1 - days/(2*182), 0.3, 1.0) — Cycle
  9's formula exactly. Forecasts: flat500, flat500 x avail, Marcel
  PA (5:4 prior PA), Marcel PA x avail. 2020 is NEVER a PA prior
  (60-game season, PA not on a full-season scale; no scaling
  invented) — class 2022 therefore uses 2021 only, labeled.
- VERDICT RULE (fixed in advance): SUPPORTED only if capped MAE <
  uncapped MAE on BOTH baselines pooled; MIXED if one; else NOT
  SUPPORTED. Result: NOT SUPPORTED. Pooled n=39 qualified FA
  regulars (5,153 signings screened; the rest are minor-league deals
  or players with no qualified T-season line — counted, not hidden).
  Flat: MAE 95.1 uncapped → 132.3 capped. Marcel: 46.2 → 61.1.
  Per class, the cap wins on Marcel only in 2022 (37.4 → 36.0) and
  loses in 2023 (46.6 → 67.0) and 2024 (55.4 → 81.6); on flat it
  loses in all three classes (win rate 0.0 — every evaluated player
  actually topped 500 PA, min 505, so the flat 500 baseline already
  undershoots and any penalty only worsens it).
- WHY IT LOSES, AND WHAT IT DOES NOT MEAN: the cap is a
  one-directional penalty, so it can only help forecasts that
  overshoot. On the 20 players where Marcel overshot, the cap helped
  65% of the time — it does what it should directionally. Pooled it
  loses because the baselines are roughly unbiased (Marcel bias
  +9.8 PA) or undershooting (flat bias −95.1), and roughly half the
  pool undershoots. The honest reading is NOT "availability doesn't
  matter": it is "a cap is a downside adjustment, not a point
  forecast improvement." That is the UNC-2 input: carry availability
  as an interval/downside layer, not as a point-forecast correction.
  Frame limit, stated in the artifact: the qualified pool excludes
  players who fell below qualification in season T — exactly the
  players a bad injury removes — which biases AGAINST the cap, so
  this negative is conservative for regulars and says nothing about
  unqualified players.
- SCOPE KEPT: workpaper only. No demo number, figure, or 2027 cap
  changes; no talk-track change. Gate gains a UNC-1 check (artifact
  present, 3 classes, pooled MAEs recompute from rows, verdict
  follows the declared rule). Platform + gate on the final tree:
  ingest 25 datasets / 0 failures; curate 18 tables, contracts
  pass, parquets byte-identical to committed; warehouse rebuilt;
  parity r = 0.889 / 201; dashboard rebuilt with lake at 25 figures;
  gate ALL PASS (offline AND --live, standings 30/30, incl. the new
  UNC-1 check); spellcheck green. GitHub Actions ignored per the
  owner's blackout directive (until Dec 1). No browser visual QA
  (standing rule).
- Next: UNC-2 (uncertainty layer — intervals on scenario WAR +
  projection error bands) — final programme increment. (The
  parallel lane's Cycle 53 note queues a feed-architecture cycle
  before UNC-1; UNC-1 shipped here first because it was built and
  verified this run and touches no feed files — the two lanes do not
  collide.)
## Cycle 55 — API-2: feed architecture, census/event/validator (2026-11-02, owner-directed)
- Built: fixed feed roles — FastballAPI = CENSUS (canonical IL
  snapshot), Statyx = EVENT layer (recent moves), StatsAPI =
  standings of record, FastballAPI standings = validator.
  `src/bml_cycle55.py`: Statyx standings join test, state-aware
  landing (volatile-field stripping), baseline-vs-current event
  comparison → `data/il_events.json`; curated append-only table
  `fact_il_events` (src/curate.py). `src/bml_cycle51.py` now
  resolves the newest landed snapshot stem per (source, kind) —
  rebuild of il_current_live.json verified byte-identical
  (md5 da5e995f…). `src/refresh_live_feeds.py`: the production
  refresh path — 20h watermark skip, hard skip at 200 FastballAPI
  credits/month counted from the manifest ledger, fail-closed
  pull → land → rebuild both artifacts → one-line summary; the
  gate never calls it (offline-safe by construction).
- Measured: Statyx standings test DROPPED — only identifier is
  Statyx-internal team_id 1794–1823 (25 distinct), no
  name/abbreviation/code fields, no crosswalk in repo, 25 of 30
  teams per season (2025+2026); kept raw-only (verdict + evidence
  in il_events.json metadata and the CARPE_SCORECARD Cycle 55
  addendum). Fresh pull (one call per endpoint, all 200, 4
  FastballAPI credits; November total 8 of 500): standings and
  FastballAPI injuries byte-identical to baseline; Statyx page
  identical in players/status/type/detail/return, differing only
  in all 50 records' updated_at (re-stamped at page generation —
  hand-verified) → first event comparison = 0 events (0 new IL /
  0 returned / 0 status changes), the correct result, shipped as
  baseline-established. Health figure gains the movement line
  (third row, from il_events.json); figure count stays 25;
  dashboard sources footer now labels the census/event roles and
  the standings drop.
- GATE: ingest 25 datasets / 0 failures; curate 19 tables (was
  18), all contracts pass, prior parquets byte-identical;
  warehouse rebuilt; parity r = 0.889 / 201; gate ALL PASS
  offline (67 checks, was 65 — two new API-2 checks) and
  spellcheck green. GitHub Actions ignored per the owner's
  blackout directive (until Dec 1). No browser visual QA
  (standing rule).
- Note: numbered Cycle 55 because the parallel lane's UNC-1
  took Cycle 54 (PR #36) while this cycle was in build; the two
  lanes touched disjoint files.
- Next: wire refresh_live_feeds.py into the 6-hourly job (parent
  lane), then UNC-2 (uncertainty layer) — final increment.

## Cycle 56 — UNC-2: uncertainty layer on the scenario rosters (2026-11-02, owner-approved programme)
- Built: `src/bml_cycle56.py` → `data/uncertainty_scenarios_2027.json`.
  Seeded Monte Carlo (20,000 draws, seed 20261102; re-runs reproduce
  the artifact byte for byte): each rostered player's delivered
  WAR = Steamer WAR × availability draw + rate-error delta at
  delivered volume. Error pools are the shipped Marcel's measured
  out-of-sample residuals, recomputed by importing
  src/bml_cycle21.py / src/bml_cycle24.py and replaying their
  variant-C cross-fit exactly, asserted against the committed
  backtest artifacts before simulating (hitters: paired OBP/SLG
  residuals n=196, MAE 0.0220/0.0453; pitchers: ERA residuals n=59,
  MAE 0.711). Availability pools: measured 2025-26 IL factors —
  hitters n=201 (mean 0.912), pitchers n=102 (mean 0.807); per
  UNC-1's verdict it shapes the distribution only, never the
  points. Rate → WAR conversion: Cycle 48 run-value slopes
  (0.2617/0.2778 runs per PA) and Steamer's own fitted runs-to-WAR
  scale (hitters 0.1132 WAR/run, R² 0.482; pitchers 0.0837,
  R² 0.215) — no outside constant.
- Measured: delivered-WAR intervals (10th–90th) — Floor 48.9 →
  33.0–46.9 (median 39.8, 20th–80th 35.3–44.4); Middle 52.8 →
  36.0–50.7 (43.2; 38.6–48.1); Cap 54.8 → 37.6–52.4 (44.9;
  40.0–49.8). Median gap decomposes exactly: availability level
  −6.8/−7.2/−7.5 + measured residual bias −2.2/−2.3/−2.3 (SLG
  −0.0078, ERA +0.078 actual-minus-projected); analytic mean
  reproduces simulated mean within 0.05 WAR. Cycle 52 uniform
  stress totals (44.6/48.1/50.0) inside all three intervals.
  Points sit at the ~95th percentile of the delivered
  distribution — they are full-availability projections, labeled
  as such wherever the ranges render.
- Consumers: Figure 16 titles (default + budget buttons), Story
  ch. 5, Boardroom slide 12, one-pager scenario table (generator
  asserts UNC-2 points tie to wow_scenarios). Figure count
  stays 25. README / EXEC_SUMMARY / TALKTRACK reconciled.
- GATE: ingest 25 datasets / 0 failures; curate 19 tables, all
  contracts pass; warehouse rebuilt; parity r = 0.889 / 201;
  gate ALL PASS offline (71 checks, was 68 — three new UNC-2
  checks) and --live (72); spellcheck green. GitHub Actions
  ignored per the owner's blackout directive (until Dec 1).
  No browser visual QA (standing rule).
- Programme status: MIT-gap programme COMPLETE (HS-1, HS-2,
  OPT-1, OPT-2, UNC-1, UNC-2 all shipped).
- Next: wire refresh_live_feeds.py into the 6-hourly job
  (parent lane); Figure 9 disclosure is an owner item; final
  release cut before Dec 1.

---
## Cycle 57 — evidence surveillance: PubMed behind Figure 14 (2026-11-02, owner-directed)
- Built: `src/pull_evidence_surveillance.py` — four fixed PubMed
  lanes via NCBI E-utilities (keyless, `tool=hardball`, fail
  closed on any non-200, 6-day staleness guard). Deterministic
  selection (SR/MA first, then most recent; 3 cards/lane);
  abstracts stored per card in `data/evidence_surveillance.json`.
  Plain headlines/Findings live in the overlay
  `data/evidence_plain_lines.json`, merged by the pull; the page
  generator fails closed if a selected card lacks one.
- Built: `docs/EVIDENCE.html` via `src/make_evidence_page.py`
  (one-pager pattern, committed artifacts only) — professional
  plain language, lane intros, a Finding per card drawn ONLY from
  its stored abstract, AMA citation + DOI + PubMed link as the
  credibility layer, labeled "Literature surveillance — context,
  not a model input." The page intro names its anchor: Figure 14
  measures the playtime injuries take away; this page is the
  literature under that measurement. Dashboard: one asterisked
  footnote line under the Figure 14 panel with the four lane
  counts and the page link (owner's final form — no block, no
  panel chrome); footer gains PubMed / NCBI E-utilities.
- Measured: lane counts as run 2026-11-02 — UCL return to play
  157; baseball prevention & workload 426; cellular recovery
  404; tendon healing & biologics 119 (SR/MA in query). Re-pull
  reproduced the identical 12 PMIDs (selection is deterministic).
- Learned (flagged, no claim changed): the biologics evidence is
  weak where it is most marketed — two RCT meta-analyses found no
  patient-reported-outcome benefit for platelet concentrates/PRP
  in ACL reconstruction; a 419-study scoping review calls the
  PRP/stem-cell evidence inconsistent. UCL return-to-play across
  21 studies spans 62.5%–100% — wide, like the Cycle 56
  delivered-WAR intervals. Also: `fact_il_stints` has no
  body-part field and its free-text injury strings do not support
  a clean body-part split of IL days (≈25% of days
  unclassifiable) — the owner's data-driven intro line was
  checked and NOT shipped rather than forced (see scorecard).
- GATE: ingest 25 datasets / 0 failures; curate 19 tables, all
  contracts pass; warehouse rebuilt; parity r = 0.889 / 201;
  gate ALL PASS offline (75 checks, was 71 — four new evidence
  checks pin the artifact, every rendered card on the page, the
  Figure 14 footnote, and the footer); spellcheck green. GitHub
  Actions ignored per the owner's blackout directive. No browser
  visual QA (standing rule).
- Next: wire `src/pull_evidence_surveillance.py` into the
  6-hourly job alongside `src/refresh_live_feeds.py` — the same
  pending cron-wiring decision (parent lane); Figure 9
  disclosure is an owner item; final release cut before Dec 1.

## Cycle 58 — record books & almanacs sweep (2026-11-02, owner standing directive)

- Built: nothing new — deliberately. This cycle is source work:
  the record-book class probed, verdicts logged, and nothing
  wired that did not earn it (a verified negative is a complete
  cycle, the Cycles 41/44 pattern). Docs only: scorecard Cycle 58
  addendum (the sweep table — the project's complete record-book
  layer in one place), a DATA_PLATFORM reference-layer section,
  HANDOFF, this entry, PR_BODY.
- Measured (live probes, 2026-11-02): Baseball Almanac —
  robots.txt 200 (permissive), homepage 200, record-book path
  /recbooks/ **403** → stopped; REFERENCE-ONLY (HTML compilation,
  no API/CSV route). Elias Sports Bureau — curl to the homepage
  dropped by the server (HTTP 000, empty reply, curl exit 52),
  text fetch refused 403, not retried; no public API/download
  exists →
  official-by-citation only. SABR — homepage 200 (110,244
  bytes); nothing separately wired (its role is already
  counted: it publishes Lahman). National
  Baseball Hall of Fame — homepage 200; museum/editorial site,
  no machine-readable product → REFERENCE-ONLY. The Baseball
  Cube — homepage 200 (evaluated cross-check status stands).
- Learned: "the official MLB record book" is a print object.
  MLB's records are kept by its official statistician, Elias;
  the latest record-book edition located is the 2021 "Elias Book
  of Baseball Records" (cited as a current authority in a
  Retrosheet research paper retrieved this cycle, which also
  notes a record it establishes was "not even included" in the
  most recent Elias or Sporting News books — even the official
  book is not exhaustive). MLB's own branded record book is a
  2013 print publication; no record-book PDF exists on MLB's
  static host (game-notes PDFs only). The Baseball America
  Almanac 2026 digital edition is password-protected —
  paywalled, logged as a gap.
- Learned (wiring test): the candidate job — cross-checking
  canonical records the demo states — has no object. Repo-wide
  grep for record language (streak / all-time / single-season /
  career record / canonical totals) across docs, src, and data:
  the demo states no canonical historical records. Nothing was
  invented to give the record books a surface. Citation rule set
  instead: any future record claim cites Elias / MLB official
  publications by hand.
- Learned (health & availability lens, one line each, in the
  scorecard): the record-book class adds no IL or workload data
  — Retrosheet never tracked the injured list (transactions
  froze Nov 2021), Lahman offers season innings/games as
  durability context only, Chadwick biographical span only,
  Elias nothing public. Figure 14's availability layer stays
  measured IL data (Injury Report + the live feeds), not
  record books.
- GATE: ingest 25 datasets / 0 failures; curate 19 tables, all
  contracts pass; warehouse rebuilt; parity r = 0.889 / 201;
  gate ALL PASS offline (75 checks — unchanged; no new rendered
  pins, no source became active, dashboard footer untouched);
  spellcheck green; dashboard rebuilds at 25 figures from
  committed snapshots. GitHub Actions ignored per the owner's
  blackout directive. No browser visual QA (standing rule).
- Next: unchanged queue — wire `src/refresh_live_feeds.py` AND
  `src/pull_evidence_surveillance.py` into the 6-hourly job (one
  pending cron-wiring decision, parent lane); Figure 9
  disclosure is an owner item; Sportradar trial ~Nov 15; final
  release cut before Dec 1.

## Cycle 59 — Cycle 58 probe-evidence correction (2026-11-02, docs only)

- Corrected: two probe-evidence lines shipped in Cycle 58 did
  not match the probe record. SABR homepage — printed "HTTP
  429 → stopped"; the record shows HTTP 200 (110,244 bytes),
  re-confirmed on the record this cycle (single GET of
  https://sabr.org/ with a browser UA: 200, 110,244 bytes —
  the third agreeing observation, after the Cycle 58
  completion record and the Cycle 58 builder's re-probe).
  Elias homepage via curl — printed "HTTP 200 via curl
  (35,678 bytes)"; the record shows the server drops the curl
  connection (HTTP 000, empty reply, curl exit 52), likewise
  re-confirmed this cycle (single GET of
  https://www.eliassports.com/: 000, 0 bytes, exit 52).
- Cause, stated plainly: the Cycle 58 probe batch's in-flow
  result disagreed with its own completion record; the
  completion record and the re-probes govern.
- Verdicts unchanged: SABR — homepage answers 200; no separate
  ingestion is built, because its data role here (it publishes
  Lahman) is already counted. Elias — no public route;
  official-by-citation only, resting on the curl refusal plus
  the text fetch's 403. No demo numbers changed, nothing
  wired, dashboard footer untouched.
- Files: docs/CARPE_SCORECARD.md (Cycle 58 entries 3 and 8),
  docs/DATA_PLATFORM.md (reference-layer section), this log
  (the Cycle 58 "Measured" bullet, corrected above),
  HANDOFF.md (Cycle 58 section), PR_BODY.md (errata note
  appended — the PR #40 record is annotated, not rewritten).
- GATE: docs only; gate 75 checks offline ALL PASS;
  spellcheck green; platform spot-check unchanged (warehouse
  rebuilt from 19 curated tables, parity r = 0.889 / 201);
  dashboard rebuilds at 25 figures from committed snapshots.
- Next: unchanged queue — the pending cron-wiring decision
  (parent lane); Figure 9 owner item; Sportradar trial
  ~Nov 15; final release cut before Dec 1.

## Cycle 60 — publish the current dashboard: release v1.1.0 (2026-11-02, owner-directed)

- Prompt: the owner reported the health API feed was not visible
  on the site. Root cause, verified: `dashboard/hardball_demo.html`
  is gitignored on main and only enters the repo at release cuts;
  the newest release tag was v1.0.1 (2026-11-01), whose dashboard
  predates Cycles 51–59 (zero of: live-IL panel, movement line,
  optimizer headlines, UNC-2 intervals, evidence footnote).
- Build: `src/dashboard_p6.py` run offline in a fresh main tree
  (KPI URL pointed at an invalid host to force committed
  snapshots; src/kpi.py restored before any push) →
  dashboard/hardball_demo.html, 5,539,972 bytes.
- Measured (content probes on the built file, repeated on the
  published tag tree with identical counts): 25 figures;
  "Current IL picture" ×2; "Movement since" ×2; "48.9 WAR" ×9,
  "52.8 WAR" ×4, "54.8 WAR" ×5; ±20% ranges 45.0–53.2 / 48.5–55.5
  / 50.4–55.9 present; UNC-2 intervals 33.0–46.9 / 36.0–50.7 /
  37.6–52.4 present; Figure 14 evidence footnote ×1 in its exact
  wording, href `../docs/EVIDENCE.html` (resolves from dashboard/
  to docs/EVIDENCE.html — no source fix needed; the Cycle 57 gate
  check already pins the href); footer names Statyx, FastballAPI,
  PubMed.
- Publish: docs PR merged first, then a release commit atop main
  adding only the generated HTML; tag v1.1.0 at that commit;
  GitHub release v1.1.0 (assets not uploaded — release uploads
  return 401; the HTML lives in the tag tree, as in v1.0.1).
- GATE: 75 checks offline ALL PASS on the publish tree;
  spellcheck green; warehouse rebuilt from 19 curated tables,
  parity r = 0.889 / 201.
- Learn: a merged feature is not a published feature — the demo
  the owner opens is the release tree, so a user-visible cycle is
  not done until the built dashboard is re-published. Interim
  publish only: the December freeze tag is still owed.

## Cycle 61 — PRICE-1: predicted-price model, inventory first (2026-11-02, slate item 1 of 6)

- Build: slate item 1 asked for a predicted-price model to
  replace the optimizer's prior-AAV anchors, switched only if
  it beat the anchor baseline's held-out MAE by >= 10%
  (train 2022 + 2023, test 2024 — bar fixed before any fit).
  Step 0 audited every committed source for a training set of
  actual signed FA contracts (`src/bml_cycle61.py` ->
  `data/price_model_workpaper_2027.json`).
- Measured: the signing census exists without terms (StatsAPI
  transactions, Cycle 54: 1,645 / 1,849 / 1,659 signings,
  classes 2022–2024; no dollars, no years). Signed terms exist
  only as survivors: Cot's contract strings parse for 153
  players, but by class just 24 (2022) / 18 (2023) / 35 (2024)
  deals remain on 2027 payrolls — minimum length 3 / 3 / 2
  years, ZERO 1-year deals in any class, extensions mixed
  with FA signings. Spotrac's file is the same snapshot shape;
  HS-1 is active contracts, not signings (its own recorded
  design limit); no artifact repo-wide carries signing-terms
  fields.
- Verdict: NOT RUN — TRAINING DATA ABSENT. No model fit, no
  numbers invented, no blocked source scraped. Anchors stay
  as the optimizer input, labeled as before. The workpaper
  pre-registers the design (target ln(signed AAV); projected
  WAR / age / position / prior-AAV-as-feature; ridge first;
  anchor + naive $/WAR baselines; switch mechanics with
  UNC-2 intervals held on the anchor run until re-derived)
  and the readiness criteria for the missing source.
- GATE: 78 checks ALL PASS (3 new PRICE-1 checks: workpaper
  on record, survivorship recomputes from the Cot's strings,
  incumbent anchor basis untouched); spellcheck green;
  warehouse rebuilt from 19 curated tables, parity
  r = 0.889 / 201. No dashboard change -> no release cut.
- Learn: the demo's price weakness is a DATA gap, not a
  modeling gap — the honest fix order is land complete
  signing terms first (Sportradar coverage check, ~Nov 15),
  then run the pre-registered fit unchanged.

## Cycle 62 — BLEND-1: projection blend + the benchmark page (2026-11-02, slate item 2 of 6)

- Build: slate item 2 asked for a Steamer + Marcel blend,
  adopted only if it beat both parents on held-out actuals
  (bar fixed before results: weights fit on 2025, judged on
  2026; hitter MAE must beat both parents, pitcher MAE no
  worse than the best parent), plus the honest benchmark
  page either way (`src/bml_cycle62.py` ->
  `data/projection_blend_2027.json`).
- Measured: the Steamer leg of any paired set is absent —
  the repo holds Steamer only for 2027 (no outcomes exist);
  the FanGraphs API ignores its season parameter (probe:
  the "2026" response is the current set, 4,164 IDs in
  common with the committed 2027 file at update-noise
  distance); Steamer's own pre-season archive ends at 2024
  and the Marcel inputs for those targets are not committed
  (fact_stat_lines begins 2023). The scoreable forecasters
  were scored on paired sets from the curated warehouse
  (hitters n = 88 / 80, pitchers n = 23 / 22 for 2025 /
  2026; Cycles 21/24 variant-B backtests regenerated from
  fact_stat_lines and matched to the committed artifacts
  exactly before any new number was computed). 2026 judge
  window: hitter OBP MAE naive .0265 vs Marcel .0237
  (r .298 vs .410); pitcher ERA MAE naive 1.0177 vs Marcel
  .9394 (r −.086 vs −.020 — ranking near chance for both,
  n = 22).
- Verdict: blend NOT ADOPTED — unscored cannot meet a
  held-out bar; no weights fit, no shadow run. Steamer
  stays the published 2027 set, Marcel the spine. The
  dashboard gains the benchmark panel under Figure 18
  ("How good are these projections?") rendering the table
  from the artifact — agreement (Fig. 18) is not accuracy,
  and the panel says which rows cannot be scored and why.
- GATE: 81 checks ALL PASS (3 new BLEND-1 checks: artifact
  complete for all four forecasters, reproduction anchor
  matches the committed backtests, panel strings verbatim);
  spellcheck green; platform: 17 rebuilt tables
  byte-identical (2 skipped in the clean tree — raw absent,
  committed parquets stand), warehouse from 19 tables,
  parity r = 0.889 / 201. Dashboard changed -> release
  v1.1.2 per the Cycle 60 pattern.
- Learn: a projection system's accuracy history is an
  asset that has to be captured when the projections are
  pulled — Steamer 2027 is committed today precisely so it
  can be scored in a year. The blend question is not dead;
  it is scheduled by the calendar: first honest test after
  the 2027 season, on this same paired design.

## Cycle 63 (V&V record, 2026-11-02) — persistence headlines recomputed

Closed HANDOFF item 4 to the extent committed data allows:
- contact pooled r: claim 0.84 -> artifact 0.843, lake recompute 0.870 (CONFIRMED)
- OBP latest-pair r: claim 0.30 -> raw recompute 0.2983, n=80 (CONFIRMED)
- OBP pooled r: claim 0.53 -> NOT stored in committed artifact; pooled value needs the
  2022-23 backfill lake rows that are absent here. Per-pair r (0.576/0.591/0.548/0.298)
  bracket ~0.50 (naive mean 0.503), so 0.53 is plausible but NOT verified on this
  machine. Flagged, not assumed. Record: data/persistence_recompute_verify.json.
No claim or data changed; dashboard untouched (still 25 figures).

## Cycle 64 — slate item 3: the 2027 Cap Transition ledger (2026-11-02)

- BUILD: `data/cap_transition_2027.json` (builder
  `src/bml_cycle64.py`) — 30 team rows on committed
  data only: Spotrac payroll totals (Cycle 22 basis),
  Cycle 30 shed sets with Steamer WAR cost, spend gaps
  for the 15 under-floor teams as arithmetic at the
  optimizer pool's price distribution (n = 199, median
  prior salary $4,500,000), and the 15% per-player
  check on Cot's AAV (8 contracts, 5 teams).
- MEASURE (primary basis): 7 over cap ($358.2M over),
  15 under floor ($807.8M short), 8 inside the band.
  Shed sets clear 6 of 7 gaps; CHC over by $4.0M with
  no shed set ("shed set not covered — payroll basis
  gap"). Sensitivity on the Cot's published-rows
  subtotal (labeled a committed-contract subtotal,
  never a payroll): 1 over / 6 in band / 23 under;
  13 teams change status between bases — the ledger
  shows both readings. Definition sensitivity
  (benefits, pre-arb pool) not modeled: no committed
  team-level figure separates them.
- SURFACE: the ledger panel leads Boardroom, rendered
  from the artifact, fail-closed if absent. Not a
  figure (count stays 25), not a slide (Boardroom
  stays 15 slides).
- GATE: 84 checks ALL PASS (3 new CAPLEDGER checks:
  30 rows with basis labeled on every row; arithmetic
  recomputed from committed payrolls; panel strings
  verbatim ahead of Slide 1); spellcheck green;
  platform clean (17 rebuilt byte-identical, 2 skipped
  on absent raw, warehouse from 19 tables, parity
  r = 0.889 / 201). Dashboard changed -> release
  v1.1.3 per the Cycle 60 pattern.
- LEARN: the two payroll bases are not two estimates
  of one payroll — the Cot's file's dollar rows are a
  committed-contract subtotal, and calling its sum a
  payroll would have understated 23 teams below the
  floor by construction. Basis labels are part of the
  number.

## Cycle 65 (checklist refresh, 2026-11-02) — backlog item (g) refreshed
- No feature build, no claim change, no data change. Platform on main
  46a2ea44: ingest 25 datasets 0 failures (Savant bands hold;
  transactions raw 120,553, +198 watermark advance); curate 19 tables,
  contracts pass, build report byte-identical to committed; warehouse
  19 tables; parity r = 0.889 / 201; gate 84 checks ALL PASS;
  spellcheck green; dashboard rebuilds offline with 25 figures.
- Spotrac probe: single GET, 403 — salaries stay 24/30, forced-seller
  6/7. One-pager regenerates clean (timestamp only differs).
- HANDOFF December checklist refreshed to Cycle 65 state (25 figures,
  v1.1.3 current release, freeze tag still owed, print pack still
  day-before, gaps carried). Next build on record: FA tracker ticker
  wiring (owner-directed 2026-11-02 evening), then slate 4-6.

## Cycle 66 (tracker ticker, 2026-11-03) — probe stack wired into the dashboard
- src/pull_tracker_ticker.py -> data/tracker_ticker_2026.json
  (521 items: 321 SIGNED / 200 REPORTED / 0 BUZZ). SIGNED from
  StatsAPI transactions, FA codes only, 7-day window; DFA =
  declared free agency in StatsAPI codes, rendered with its
  exact move type so a declaration never reads as a signing.
  REPORTED from MLBTR (main + top-6 teams + top-12 players),
  MLB.com (top-6 teams), ESPN news + transactions, Google
  News (generic + top-12 players, redirect links deduped on
  title+source), RotoWire (5-item cap). Caps in the artifact:
  12 players, 6 teams, 200 REPORTED stored, 10 BUZZ stored.
- BUZZ ships EMPTY, honestly: Bluesky Jetstream is the only
  social source, and its stream read timed out in this runtime
  on both pull runs (0 events). The panel labels the lane
  "awaits stream verification" instead of filling it with
  substitutes. A standalone probe session was lost to runtime
  instability and contributes no verdict either way.
- GATE: 87 checks ALL PASS (3 new TICKER checks); spellcheck
  green (ticker div excluded from the spellcheck scan — wire
  headlines are quoted third-party copy, verified by source).
  Platform clean (17 tables rebuilt byte-identical, 2 skipped
  on absent raw with committed parquets standing; warehouse
  from 19 tables; parity r = 0.889 / 201). Dashboard rebuilt
  with the lake present: 25 figures, none missing.
- CAUGHT BY THE GATE: one StatsAPI transaction (id 947748,
  TR) carried no description and no player name; the pull now
  skips such rows and counts them (1 skipped this run) instead
  of rendering an empty bullet.
- LEARN: a gate freshness pin must survive later runs — the
  ticker gate pins pulled_at present-and-parseable, not
  "today", because the ticker pull is not yet a cron step and
  a "today" pin would fail every later cron gate run. The
  panel displays the pull date instead.
- Dashboard changed -> release v1.1.4 per the Cycle 60
  pattern. Cron diff that would add the ticker pull to the
  6-hourly build is proposed in HANDOFF (Next), NOT applied
  — it awaits the owner's tap.

## Cycle 67 — health cards: the shopping list ranks by delivered WAR (slate item 4)

- BUILD: src/bml_cycle67.py -> data/fa_health_cards_2027.json, 251
  cards. Measured availability from curated fact_il_stints
  (2025-26 stints, days/364, floored at 0; 3 players capped:
  Rendon, Jimenez, Graterol). Delivered WAR = Cycle 56 formula at
  player level (own measured factor, else pool mean, plus the
  residual-bias term at delivered PA/IP). No per-player intervals
  — pool-draw intervals would dress pool variance as player risk.
- SURFACE: Explorer "Shop the FA Class" panel, sortable by
  delivered WAR, 251 rows + header. Not a figure (25 figures
  stand), Story 6 chapters, Boardroom 15 slides.
- NUMBERS THAT MOVE: top 5 by delivered WAR — Skubal 4.86,
  Contreras 3.79, Rasmussen 2.91, Gray 2.73, Arraez 2.55. Trevor
  Rogers drops headline #4 -> delivered #6 (3.04 -> 2.41 on 64 IL
  days). That drop is the buying tool working.
- HONESTY NOTES: 65 players read "no IL record", never 100%; 20
  entries (NPB class + Spotrac name fragments) were not joined at
  all — name-only joins risk false attribution. The risk flag
  fires often by construction (76 of 166 measured players): the
  comparison pool includes players with no IL time while the
  flagged set is conditioned on having IL history. Evidence
  links go to a lane only where the dominant injury classifies
  cleanly (73); the rest link to the page top (178).
- GATE: 89 checks ALL PASS (2 new HEALTH checks: artifact
  recomputation + ranks, panel in Explorer not Story, four lane
  anchors). Spellcheck green (161 name tokens verified against
  the class file before whitelisting). Platform clean (19
  parquets byte-identical, warehouse rebuilt, parity r = 0.889 /
  201). Dashboard rebuilt with the lake present: 25 figures.
- Dashboard changed -> release v1.1.5 per the Cycle 60 pattern.

## Cycle 68 — reproducibility & claims pack (slate item 5, 2026-11-03)
- Built: src/bml_cycle68.py -> data/claims_register.json (16 SUPPORTED,
  7 NOT SUPPORTED, 3 RETRACTED, 1 open), data/figure_trace_2027.json
  (25/25 figures + 8/8 panels verified, FIG-QA method), docs/REPRODUCIBILITY.html
  (generated from the two JSONs, never hand-edited numbers).
- Surface: "Claims & reproducibility" panel closes Explorer (appendix, not a
  figure; Story 6 chapters, Boardroom 15 slides unchanged); fails closed
  without the pack artifacts, so the build runs in two passes.
- Retracted, stated plainly: R01 team-wins R-squared 0.80 (Cycles 18-19),
  R02 availability-capped point forecasts (UNC-1, Cycle 54), R03 OBP
  persistence as first published (Cycle 39/44). Open item O01 (Figure 9
  in-sample label) left for the owner; the trace verifies Figure 9's
  artifact/panel agreement without endorsing the title.
- Two builder catches fixed before shipping: evidence-artifact parsing
  (path regex, not "+" split) and the evidence-footnote marker (title
  renders as a link; checked as two halves). No figure trace failed.
- Gate 93 checks ALL PASS (4 new Cycle 68 checks); spellcheck green.
  Platform clean (17 curated rebuilt, 19 parquets byte-identical,
  warehouse rebuilt, parity r = 0.889 / 201). Released as v1.1.6 per the
  Cycle 60 pattern; published file probed from the release tarball.

## Cycle 69 — claims-pack open item O01 resolved (2026-11-03)

- BOOKKEEPING ONLY — no new analysis, no claim status changes, no
  figure changes. The Cycle 68 pack's one open item is closed on the
  record: Figure 9's in-sample label shipped in the owner's lane
  (commit 4219e079, "Figure 9 (owner item #1): relabel in-sample
  model fit as calibration, overlay actual wins"). The shipped
  title is "2026 — Model fit (in-sample) vs actual wins, by team"
  and its caption states "this is calibration, not a forecast".
- BUILD: src/bml_cycle69.py -> data/claims_register.json (open 1 ->
  0, resolved 1; 16 SUPPORTED / 7 NOT SUPPORTED / 3 RETRACTED
  unchanged) + data/figure_trace_2027.json (Figure 9 headline now
  reads "resolved Cycle 69"; 25/25 figures + 8/8 panels still
  verified) + docs/REPRODUCIBILITY.html regenerated (new Resolved
  items section, open section now "None — no open items").
  Dashboard panel paragraph replaced (stale "One item is still
  open" -> "No items are open", with the O01 resolution note);
  Story 6 chapters, Boardroom 15 slides, 25 figures all unchanged.
- GATE: 93 checks ALL PASS (checks updated for the resolved item,
  none added: register requires O01 resolved + open empty + counts
  reconcile incl. resolved; panel requires the new paragraph and
  forbids the stale one; pack page requires the Resolved section);
  spellcheck green. The gate's evidence-artifact loop now covers
  resolved_items too, so O01's evidence stays checked.
- PLATFORM: ingest 25 datasets, 0 failures (Savant bands hold:
  expected 651-673, bat-tracking 595-619, sprint 489-506;
  transactions 120,552); curate 19 tables, contracts pass;
  curated parquets + build report byte-identical to main (no data
  PR from the platform step); warehouse rebuilt from 19 tables;
  parity r = 0.889 / 201. Dashboard rebuilt with the lake present:
  25 figures, none missing.
- SALARY GAP UNCHANGED: Spotrac probe single GET 403; FanGraphs
  RosterResource payroll probe single GET 403 (Cloudflare, same as
  Cycle 32) — both stopped for the run per the rate-limit rule.
  Salaries stay 24/30, forced-seller 6/7. No routing around either
  block. Next salary route remains the Sportradar trial (~mid-Nov,
  timed to cover Dec 1).
- Dashboard changed -> release v1.1.7 per the Cycle 60 pattern
  (tag + GitHub release, no asset uploads; the merged tree already
  carries the rebuilt dashboard).

## Cycle 71 — ARBITRAGE: the surplus-value layer (Moneyball 2.0, owner request 2026-11-03)

- Front-office framing adopted: the number a real front office decides
  on is SURPLUS VALUE = projected dollars of wins MINUS contract
  cost (Miami Marlins VP of Baseball Systems, Posit Data Science
  Hangout, Aug 2025). Moneyball 2.0 is not "compute more stats" — it
  is "price the whole market against one value reality, then trade the
  gap."
- BUILD: src/bml_cycle71.py -> data/surplus_value_2027.json. For every
  free agent in the committed FA class (fa_shopping_2027.json):
  value_usd = steamer_war x market_usd_per_war, where market $/WAR =
  the MEDIAN of the class's own implied rate (spotrac_market_aav /
  steamer_war) = $8.16M. surplus_usd = value_usd - cost_aav (Spotrac
  market AAV). 12 of 25 surplus-positive. No rates invented — every
  input is committed data.
- CONTACT-SKILL ARBITRAGE surfaced from the committed Hakes–Sauer run
  (Cycle 46, data/hakes_sauer_results.json): top-quartile CONTACT
  hitters cost ~$8.0M/WAR vs ~$15.0M/WAR for the bottom quartile
  (~54% of the cost) — buying contact/OBP skill is buying wins at
  roughly half the dollars-per-WAR of a power ticket. Stated honestly
  as a descriptive contrast (the Hakes–Sauer mispricing test is
  INCONCLUSIVE), never as a proven price effect.
- LEADERBOARD sanity: Contreras +$20.6M surplus (4.3 WAR, $14.4M
  market), Sandoval +$14.1M (2.0 WAR, $2.4M), Skubal +$6.7M (near-fair
  — market already prices him). Red = overpriced vs the class's own
  rate. Surplus caveat on the panel: a player can be cheap for
  injury/role/age risk — valuation, not a settled mispricing.
- DASHBOARD: Figure 22 panel rewritten from the surplus artifact
  (rank by surplus, green/red color, value-vs-cost in the labels).
  figure_trace (cycle68) Fig 22 entry + verify_data gate updated to
  the honest surplus strings; cycle69 re-run to keep O01 resolved
  (cycle68 regen alone would have re-opened it).
- GATE: 75 checks ALL PASS + spellcheck green + accuracy monitor
  4/4. Run order for this cycle: bml_cycle71 -> dashboard build ->
  bml_cycle68 -> bml_cycle69 -> dashboard build -> verify + spell +
  monitor (cycle69 must follow cycle68 so O01 stays closed).

## Cycle 72 — tracker refresh + Cycle 24 drift re-run (2026-11-03, 24/7 job)

- SPOTRAC PROBE: single GET of the Tampa Bay 2026 payroll page -> HTTP
  403 (browser UA). Logged, not routed around. Salaries stay 24/30,
  forced-seller coverage 6/7 (CHC uncovered) until the Sportradar
  trial ~Nov 15.
- LIVE FEEDS (step 2b): refresh_live_feeds SKIP (last pull 17.6h old,
  < 20h watermark — normal); evidence surveillance SKIP (artifact
  1d old, < 6d guard — normal). Tracker ticker pulled 2026-11-03
  16:15 UTC (window Oct 27–Nov 3, class register 246): StatsAPI
  SIGNED lane + MLBTR + MLB.com + RotoWire OK; Google News 503 on
  every lane and Bluesky Jetstream timeout failed closed per source
  (logged, skipped, never routed around). Artifact: 535 items
  (335 SIGNED, 200 REPORTED), down from the committed 257,671 bytes
  to 222,531 on window roll.
- PLATFORM: ingest 25 datasets, 0 failures; row counts at known-good
  levels (Savant expected 651–673/season, bat-tracking 595–619,
  sprint 489–506). Curate: 19 tables, all contracts pass. Warehouse
  rebuilt. benchmark_parity: r = 0.889, 201 matched — exact, no
  upstream drift. No curated table changed vs main; no platform PR.
- BACKLOG (h — all of a–g already shipped, incl. Fig. 23 in Cycle 47
  and the README runbook on main): Cycle 24 pitcher Marcel backtest
  re-run against the refreshed lake. Output data/pitcher_backtest.json
  IDENTICAL to the committed artifact (pooled A MAE ERA 0.744 /
  WHIP 0.122; B 0.715 / 0.120; C 0.711 / 0.120) — no drift.
- DASHBOARD: rebuilt offline (KPI URL pointed at an invalid host to
  force committed snapshots; src/kpi.py verified byte-identical to
  main afterwards). Crest stamp now reads "Data as of Nov 3, 2026 ·
  tracker Nov 3 · injured list Nov 2 · evidence Nov 2".
- GATE: verify_data.py ALL CHECKS PASS (94 PASS lines) +
  spellcheck green. Shipped as PR + merge (owner pre-approval
  pattern): data/tracker_ticker_2026.json + rebuilt
  dashboard/hardball_demo.html + this log entry.

## Cycle 73 — PREDICTION TRANSPARENCY: the conviction layer (RBP-style, owner request 2026-11-03)

- The MIT/Sloan transparency point, done honestly: a black-box model says a
  number; relevance-based prediction says HOW TRUSTWORTHY that specific
  prediction is BEFORE it is acted on (RBP; LITERATURE_SPINE [18]). We
  adopt the transparency GOAL, computed from committed data rather than
  reimplementing the Mahalanobis reliability machinery — and we refuse the
  fake version.
- DESIGN DECISION the repo should keep: projected playing time (proj_PA) is
  deliberately NOT a conviction input, because in the committed artifact it
  is a uniform 500-PA default across all 201 hitters — a projection
  assumption, not a real workload signal. Feeding it in would be the exact
  invented differentiator this layer exists to remove. (First draft did
  exactly that and shipped a degenerate HIGH=49/MEDIUM=151/LOW=1; caught
  and killed it before commit.)
- BUILD: src/bml_cycle73.py -> data/prediction_conviction_2027.json. For
  every 201 hitter: conviction = input_stability from committed PRIOR-
  season contact% (tight <5.0 pts) + BB% (tight <3.0 pts) across 2+ years
  (data/player_yoy.json). HIGH=both tight (49), MEDIUM=one tight (30),
  LOW=neither (1), NO_PRIOR=no committed 2-season record (121). Honest
  distribution: the 80 players with records are the only ones we can call
  HIGH/MEDIUM/LOW; the 121 without are labeled NO_PRIOR, capped below HIGH —
  never an invented high score.
- DASHBOARD: Figure 12 (2027 projected hitters by OBP) now carries a
  conviction legend + per-bar label (● high / ○ medium / ▽ low / no prior
  record) + an in-title explanation. Honest and notable: Judge/Soto/Alvarez
  render NO_PRIOR because data/player_yoy.json (80 players) has no committed
  2-season record for them — the layer flags the gap rather than pretending.
- figure_trace Fig 12 entry + verify_data gate updated to the conviction
  strings; cycle68 -> cycle69 sequence preserves O01 resolved.
- GATE: 75 checks ALL PASS + spellcheck green + accuracy monitor.
- ITEM 2 STATUS: the Savant refinement backtest is ALREADY SHIPPED in this
  repo (data/savant_test.json, Cycle 20): xwOBA is a better projection INPUT
  (Q1) but every feature family (batted-ball, bat-tracking, all) was DROPPED
  as a projection adjustment (Q3 F1-F4) — bat speed, the most stable trait
  (YoY r .92), made projections WORSE out-of-sample; "no, bat speed does not
  improve this projection." Surfaced as claim N04 (NOT SUPPORTED) + Figure 19
  (diagnostics only). NOT a new build — an existing honest negative re-read.
- TODO handoff (Toby/owner): bat speed / swing-path / attack-angle as
  open BML question — already ANSWERED NEGATIVE as a projection feature by
  savant_test.json, so the open thread is product/demo framing only (e.g. a
  novel bat-speed exhibit), NOT a modeling claim.

## Cycle 75 — BAT-SPEED EXHIBIT: the trait as context, never as a claim (2026-11-03)

- QUESTION (from the Cycle 73 TODO handoff): bat speed / swing-path /
  attack-angle as an open product thread. The modeling question was
  already answered negative by Cycle 20 (data/savant_test.json,
  claim N04 NOT SUPPORTED), so this cycle builds the demo exhibit
  only — no projection claim added anywhere, nothing re-tested.
- DATA: committed Savant bat-tracking boards
  (data/savant_bat_tracking_2024/2025/2026.json; 595/619/619
  players). CORROBORATION: reconciled against the platform raw
  cache (mirror CSVs of the same boards) — counts equal and
  avg_bat_speed + swing_length EXACT for every matched player,
  1,833 of 1,833 player-seasons. Pitch-level attack-angle /
  swing-tilt columns are not in the committed data; the exhibit
  is scoped to bat speed + swing length + squared-up/blast and
  does not show or promise attack angle.
- MATH (all recomputed in the gate from the boards; artifact by
  src/bml_cycle75.py -> data/bat_speed_exhibit_2027.json):
  stability of avg_bat_speed, players matched by player_id —
  2024->2025 r = 0.908 (n = 490), 2025->2026 r = 0.905 (n = 487),
  pooled r = 0.907 (977 pairs). Cycle 20's committed 0.921
  (yoy_r_by_pair 0.919/0.924) reconciles as qualification: with
  a >=250-competitive-swing minimum in both seasons the same
  boards give 0.922 / 0.929 (pooled 0.925). The exhibit prints
  the recomputed values and the reconciliation, never the .92
  copied. 2026 distribution (n = 619): median 71.8 mph, middle
  half 70.0-73.6, range 61.7-79.4. Fastest/slowest tables at
  >=250 competitive swings (403 qualify): fastest Caminero
  79.4 mph; slowest Kwan 62.4.
- TEAM LENS: CUT on coverage evidence, recorded in the artifact:
  fact_stat_lines 2026 hitting covers 135 of 619 board players
  (selected subset), Steamer 2027 carries Team for 0 of 618,
  fact_proj_hitters covers 199 (benchmark subset). No team split
  printed rather than a partial one wearing team names.
- DASHBOARD: companion panel directly under Figure 19 in
  Explorer ("Bat speed, up close — context only"), rendered only
  from the artifact, fail-closed when absent. Carries the N04
  label and the register claim verbatim with its NOT SUPPORTED
  status. Figure count stays 25; Story/Boardroom untouched.
- GATE: 97 checks ALL PASS (94 + 3 Cycle 75: artifact recompute
  in-gate, panel placement + verbatim claim + rendered stats,
  no projection-claim wording) + spellcheck green + platform
  clean (curate 19 tables, parity r = 0.889 / 201).

## Cycle 74 — SALARY COMPLETION: the second-basis hackathon (2026-11-03)
- QUESTION: can the 24/30 Spotrac per-player gap (and the one visible
  hole, CHC's missing shed set) be closed at demo quality without a
  new scrape — by validating Cot's as a second basis hard enough to
  build on? Owner framing: a hackathon challenge to overcome.
- BUILD: src/bml_cycle74.py parses all 30 Cot's sheets into
  data/salaries_cots_full_2027.json (2,240 rows; figures where
  printed, markers where printed, nothing invented) and computes
  data/salary_reconciliation_2027.json from the raw sheets.
  Validation inside the build, fail-closed: the 237 figure rows are
  identical to the Cycle 44 file; the parse matches the independent
  Cycle 41 parse to the dollar per team; the other six forced-seller
  entries are asserted byte-identical after the CHC fill.
- RESULT (all recomputed, two-plus sources): totals reconcile —
  mean abs diff 0.63%, worst SD +3.07%, 26/30 within 2%. Shed sets
  agree across three bases on 5 of 6 known teams (AAV: 6 of 6); the
  one LRP difference (LAD) is Ohtani's deferral, present value vs
  nominal — labeled, not averaged away. USA TODAY's final-2026 LRD
  list corroborates externally on a different basis/snapshot
  (anchors within ~0.5%; WSH −11.2% the largest deviation, a
  deadline seller; Guerrero Jr. exact at $40,214,286).
- SHIPPED: CHC shed set on the Cot's LRP basis — Bregman alone,
  $29,527,000 against the pinned $4,019,956 gap; coverage 7/7;
  ledger regenerated (only CHC's action changed); Figure 11 +
  ledger render the set with its basis labeled; claim S17
  SUPPORTED, N06 corrected and standing; curate 20 tables, parity
  0.889/201; gate 102 ALL PASS.
- LEARNED: a blocked source is not a data gap if a second source
  can be validated to the dollar against everything the first
  source did publish. The residual risk is basis-mixing, and the
  defense is labeling: every Cot's-basis number in the demo says
  so where it renders.

## Cycle 76 — visual redesign: MLB colors + Rays secondary

- Presentation-only cycle (owner: "executives looking at this
  can't be junk"; palette directed in chat, superseding the
  brass draft). Page is now MLB Navy #041E42 with Rays Navy
  #092C5C panels, white text, Columbia Blue #8FBCE6 dim text,
  MLB Red #BF0D3E the single accent, Rays Gold #F5D130 only on
  the data-as-of stamp, numerals, and the posting-fee line.
  Fraunces / Inter / IBM Plex Mono via Google Fonts + fallbacks;
  one central Plotly template in _number() restyles all 25
  figures (transparent grounds, muted grids, Columbia legend).
- Group semantics recolored exactly (#1b5e20 -> #43b581,
  #e65100 -> #e08a3c, #1565c0 -> #8FBCE6, #d50032 -> #BF0D3E);
  key swatches gate-asserted equal to trace hexes. Figure-data
  audit: trace x/y/text arrays identical pre/post on 25/25
  figures — zero data movement. Dashboard 5,645,837 ->
  5,402,333 bytes.
- WCAG (computed, also recomputed in the gate): white/ink
  16.54:1, Columbia/ink 8.27:1, gold/ink 11.06:1, white/panel
  13.76:1, Columbia/panel 6.88:1, gold/panel 9.20:1, white/
  accent 6.28:1. Red-on-navy (2.63:1) is non-text chrome only.
  Numeral labels (chapter/slide) moved red -> gold for exactly
  this reason (9.20:1 on panel).
- Gate 107 ALL PASS (+5 Cycle 76 checks; no existing check
  edited — none pinned an old string). Spellcheck green.
  Parity r = 0.889 / 201. Release v1.1.11.
- LEARNED: a theme change is a data change until proven
  otherwise — the pre/post trace-array diff is the proof, and
  it is cheap enough to run every time a panel is touched.

## Cycle 78 — Figure 25 restored: the production artifact was built without the lake

- Owner-directed restore (chat, 2026-11-03 evening: "push back
  on and let codex know it kool") after Explorer was seen
  holding 24 panels and the page read much longer.
- DIAGNOSIS: source never dropped the panel. The production
  artifact on main was built without data/mlb_lake.db:
  panel_pitching() returns None lake-less, the figure drops
  out of the numbering list, and every later figure renumbers
  down one — the optimizer chart shipped wearing "Figure 24"
  inside the wrong Explorer group, and the Build a Roster
  slot for 25 rendered the "needs the lake file" fallback
  panel (data-figure-missing="25" in the served file). Every
  figure from 14 on was misnumbered by one in production.
- FIX: artifact only, zero source change — dashboard rebuilt
  from current main source with the lake copied in and the
  KPI endpoint forced to committed snapshots (the standing
  offline build pattern). Explorer: 25 unique panels,
  data-figure="25" = "Benchmark vs headline: the exact optimum
  beats the greedy build" (+6.9 / +7.1 / +2.5 WAR deltas,
  recomputed from data/optimizer_comparison_2027.json at
  build time). Story (7) and Boardroom (16) memberships
  unchanged; no within-mode duplicates; data-as-of stamp
  intact (Nov 3, 2026).
- Gate note: src/verify_data.py still crashes against the
  new build (mode-anchor IndexError + spellcheck UTF-8) —
  that alignment is a separate pending item; this cycle
  verified by direct DOM/data checks, listed in the PR.
- LEARNED: a lake-less build does not fail — it renumbers.
  Any build that will be committed must run with the lake
  present, and the figure census (25 uniques, zero
  data-figure-missing markers) is the cheap proof.

## Cycle 79 — tracker refresh + README demo runbook (24/7 job, 2026-11-03 evening PT)

- DEADLINE GUARD: 2026-11-03, inside the build window (closes Dec 1).
- SPOTRAC PROBE: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the Spotrac
  basis + Cot's second basis (Cycle 74, 7/7 shed sets). FanGraphs
  payroll page probed once -> 403 Cloudflare, so backlog item (c)
  stays failed-closed per its guard; no retry.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull 5.9h old, < 20h
  watermark); pull_evidence_surveillance.py SKIP (artifact 1d old,
  < 6d guard). Both SKIP lines are normal outcomes, not failures.
  No new evidence artifact, so docs/EVIDENCE.html is untouched.
- TICKER: pull_tracker_ticker.py OK — window rolled to
  2026-10-28..2026-11-04, SIGNED 362 -> 367, REPORTED 200, BUZZ 0,
  total 562 -> 567. New SIGNED items: one MLB release (Marlins RHP
  Bradley Blalock), one minor-league signing (Rangers RHP Enrique
  Pantoja), the rest minor-league DFA declarations. Google News
  503 on all queries and the Bluesky Jetstream timeout are the
  script's designed fail-closed behavior (logged, skipped, never
  routed around); the lanes shipped exactly as the script records.
- PLATFORM: ingest_platform.py 25 datasets, 0 failures; Savant
  expected 651-673/season, bat-tracking 595-619, sprint 489-506 —
  all inside the known-good bands, no silent-source move. curate.py
  20 tables, all contracts pass; the _build_report.json is
  byte-identical in counts to the committed report, so no curated
  table changed materially and none is shipped. build_warehouse.py
  rebuilt; query.py benchmark_parity r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1 (the current form of the forced-snapshot
  pattern). Census: 25 unique figures, zero data-figure-missing
  markers. Crest stamp now reads "Data as of Nov 4, 2026 · tracker
  Nov 4 · injured list Nov 3 · evidence Nov 2". Gate
  src/verify_data.py: ALL CHECKS PASS (the two pre-rebuild FAILs
  were the stale stamp and stale ticker pull date, both resolved
  by the rebuild — not source breaks).
- SPELLCHECK: failed on one token, "edu" — a pre-existing artifact,
  not from this cycle: it is the TLD fragment of the About contact
  email (michael.bolton.ph@dartmouth.edu) as tokenized from the
  built HTML, present in the previously committed artifact too.
  Mechanical fix: "edu" added to WHITELIST in
  src/spellcheck_gate.py with the source line cited. Spellcheck
  now OK. No contact text was changed.
- BACKLOG ITEM (f) DONE: README "Presenting in 5 minutes" — open
  the file (Story is the default landing), press play on the
  payroll-vs-wins animation, verdict first + 6 chapters, Boardroom
  for the room (15 slides, print-clean), Explorer for questions
  (all 25 figures by task, Pick Your Team on top), The Posted Class
  (Figure 23, Explorer-only) as the live-market exhibit, and where
  the honesty box lives (Story appendix + Explorer Claims &
  reproducibility + the Figure 23 translation box). Every mode
  count and chapter mapping was verified against the rebuilt
  artifact and docs/TALKTRACK.md; no new numbers.
- NEXT: backlog item (g) — December readiness checklist refresh in
  HANDOFF.md. Open PRs left untouched: #57 (Cycle 77 live refresh,
  predates the Cycle 78 restore and the current main) and #58
  (parallel-lane ticker trigger).
- REBASE NOTE (same cycle, before merge): main moved mid-work via
  PR #80 (README rewrite, Figure 3 readability, ticker slowed
  150s -> 210s, dashboard now published as dashboard/index.html)
  and PR #81 (legacy dashboard sync). The first PR (#82, from old
  main 9daf496d) was superseded, not merged: this cycle was rebuilt
  from the new head c16079b4 with the new builder, so the artifact
  carries the Figure 3 fix. The build writes dashboard/index.html;
  dashboard/hardball_demo.html is kept as a byte-identical copy
  (the #81 sync invariant; the root index and the gate both read
  it). Gates re-run green on the rebuilt pair.
- SPELLCHECK NOTE (rebase): the new main's README carries the live
  dashboard URL as bare prose, tokenizing to "https" — "http" was
  already whitelisted but "https" was not, so the rebuilt pair
  failed spellcheck on that one token. Same mechanical class as
  the "edu" fix above: "https" added to WHITELIST (URL scheme,
  not a typo). Spellcheck now OK; verify_data.py ALL CHECKS PASS.

## Cycle 80 — tracker refresh + December checklist refresh + Figure 14 gate alignment (24/7 job, 2026-11-04 ~02:15 PT)

- DEADLINE GUARD: 2026-11-04, inside the build window (closes Dec 1).
- SPOTRAC PROBE: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the Spotrac
  basis + Cot's second basis (Cycle 74, 7/7 shed sets). FanGraphs
  not re-probed; backlog item (c) stays failed-closed per its guard.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull 2026-11-03
  22:23 UTC, 11.9h old, < 20h watermark);
  pull_evidence_surveillance.py SKIP (artifact Nov 2, 2d old,
  < 6d guard). Both SKIP lines are normal outcomes, not failures.
  No new evidence artifact, so docs/EVIDENCE.html is untouched.
- TICKER: pull_tracker_ticker.py OK — window still
  2026-10-28..2026-11-04, SIGNED 367 -> 369, REPORTED 200, BUZZ 0,
  total 567 -> 569. New SIGNED items: two Nov 3 winter-ball
  releases (Navegantes del Magallanes RHP Jesus Mosquera, RHP Jose
  Ramirez, both REL via StatsAPI transactions); nothing removed.
  Bluesky Jetstream handshake 403 is the script's designed
  fail-closed behavior (logged, skipped, never routed around);
  Google News answered 200 this run (Cycle 79: 503), so REPORTED
  churned on fresh links under the 200 cap. The lanes shipped
  exactly as the script records.
- PLATFORM: ingest_platform.py 25 datasets, 0 failures; Savant
  expected 651-673/season, bat-tracking 595-619, sprint 489-506 —
  all inside the known-good bands, no silent-source move.
  Transactions raw 121,411 (+2, the releases above; raw-zone only).
  curate.py 20 tables, all contracts pass; counts match Cycle 79
  exactly, so no curated table changed materially and none is
  shipped. build_warehouse.py rebuilt; query.py benchmark_parity
  r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1. Census: 25 unique figures, zero
  data-figure-missing markers. Crest stamp now reads "Data as of
  Nov 4, 2026 · tracker Nov 4 · injured list Nov 3 · evidence
  Nov 2". dashboard/hardball_demo.html kept as a byte-identical
  copy of dashboard/index.html (the #81 sync invariant).
- GATE FIX (mechanical, in this PR): the rebuilt dashboard failed
  verify_data.py on exactly one check — the Figure 14 evidence
  footnote. Cause was on main, not in this rebuild: PR #84
  relabeled the footnote ("Figure 14 evidence: What the evidence
  says now — PubMed research on injury recovery and prevention")
  without updating the gate's expected strings. Fix aligns the
  three expected strings in src/verify_data.py to the shipped #84
  wording; link, all four lane counts (157/426/404/119 found), and
  footnote position between Figures 14 and 15 were verified
  present before the edit. No claim, figure, or data changed.
  Gate now 107 checks ALL PASS. Spellcheck green.
- BACKLOG ITEM (g) REFRESHED: HANDOFF.md gains a Cycle 80 December
  readiness checklist refresh (structure from Cycle 36; status
  current on main 84e50bda). Freeze tag still owed; v1.1.12 is the
  current published release, not the freeze tag. Sportradar footer
  line correction still rides with the freeze cut (trial declined
  by the owner 2026-11-03).
- NEXT: final frozen-main release cut before Dec 1. Open PRs left
  untouched: #57 (Cycle 77 live refresh, predates the Cycle 78
  restore and the current main) and #58 (parallel-lane ticker
  trigger).

## Cycle 81 — tracker refresh + December checklist refresh (24/7 job, 2026-11-04 ~08:15 PT)

- DEADLINE GUARD: 2026-11-04, inside the build window (closes Dec 1).
- SPOTRAC PROBE: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the Spotrac
  basis + Cot's second basis (Cycle 74, 7/7 shed sets). FanGraphs
  not re-probed; backlog item (c) stays failed-closed per its guard.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull 2026-11-03
  22:23 UTC, 17.9h old, < 20h watermark); pull_evidence_surveillance.py
  SKIP (artifact Nov 2, 2d old, < 6d guard). Both SKIP lines are
  normal outcomes, not failures. EVIDENCE.html untouched.
- TICKER: pull_tracker_ticker.py OK — window 2026-10-28..2026-11-04,
  SIGNED 369 -> 805, REPORTED 200, BUZZ 0, total 569 -> 1005. The
  +436 investigated before shipping: all dated Nov 2-4, no old item
  lost, driven by the post-season DFA wave (DFA 234 -> 659). The 5
  duplicate transaction ids are unchanged from Cycle 80 (bilateral
  trade rows). Jetstream handshake 403 fail-closed; Google News 200.
- PLATFORM: ingest_platform.py 25 datasets, 0 failures; Savant
  bands hold (expected 651-673, bat-tracking 595-619, sprint
  489-506). Transactions raw 121,411 -> 121,908 (raw-zone only).
  curate.py 20 tables, contracts pass; _build_report.json identical
  to main's, so no curated table changed materially and none is
  shipped. build_warehouse.py rebuilt; query.py benchmark_parity
  r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1. Census: 25 unique figures, zero
  data-figure-missing markers. Crest stamp "Data as of Nov 4, 2026
  · tracker Nov 4 · injured list Nov 3 · evidence Nov 2".
  dashboard/hardball_demo.html kept as a byte-identical copy of
  dashboard/index.html (the #81 sync invariant).
- GATE: src/verify_data.py 107 checks ALL PASS on the first run;
  spellcheck green. No gate fix needed this cycle.
- BACKLOG ITEM (g) REFRESHED: HANDOFF.md gains a Cycle 81 December
  readiness checklist refresh. Freeze tag still owed; v1.1.12 is the
  current published release, not the freeze tag. Sportradar footer
  line correction still rides with the freeze cut (trial declined
  by the owner 2026-11-03).
- NEXT: final frozen-main release cut before Dec 1. Open PRs left
  untouched: #57 (Cycle 77 live refresh, predates the Cycle 78
  restore and the current main) and #58 (parallel-lane ticker
  trigger).

## Cycle 82 — live refresh (Nov 4) + December checklist refresh (24/7 job, 2026-11-04 ~14:15 PT)
- DEADLINE GUARD: 2026-11-04, inside the build window (closes Dec 1).
- BASE: main 9c52a75d (Cycle 81 merge + parallel-lane PR #87 Story
  opening). Tarball 404 on the codeload redirect again; base
  verified blob-by-blob (git blob hashes) via the API recursive
  tree after syncing PR #87's src/dashboard_p6.py — zero diffs.
- SPOTRAC PROBE: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the Spotrac
  basis + Cot's second basis (Cycle 74, 7/7 shed sets). FanGraphs
  not re-probed; backlog item (c) stays failed-closed per its guard.
- LIVE FEEDS: refresh_live_feeds.py OK (past the 20h watermark) —
  4 credits (20 MTD, November cap 200); Fastball injuries 145,
  Statyx page 50, union 164, standings 30/30 agree; FA overlay
  9/251 (1 differs from static). Evidence SKIP (artifact Nov 2,
  2d old, < 6d guard) — normal outcome. EVIDENCE.html untouched.
- IL UNION 182 -> 164 INVESTIGATED: Fastball 175 -> 145, Statyx
  16 -> 50, overlap 9 -> 31; 30 names out (post-season IL clearing),
  12 Statyx-only names in; both feeds 200, no block; substantive
  status changes few (Zerpa 60-Day-IL -> Out, Romy Gonzalez
  Day-To-Day -> Out). fact_il_events 123 -> 133 corroborates.
- TICKER: pull_tracker_ticker.py OK — window 2026-10-28..2026-11-04,
  SIGNED 805 -> 849 (+44, none lost), REPORTED 200 (119 rotated by
  the newest-200 cap, by design), BUZZ 0, total 1005 -> 1049.
  Jetstream handshake 403 fail-closed; Google News 200.
- PLATFORM: ingest_platform.py 0 failures (Savant bands hold;
  transactions raw 121,908 -> 122,135, raw-zone only); curate.py
  20 tables, contracts pass; _build_report.json changed only in
  fact_il_current / fact_il_events, so only those two parquets +
  the report ship; ingest manifest appends restored, not shipped
  (Cycle 80/81 practice — shipped manifest = main's 68 lines +
  this run's 4 refresh entries). build_warehouse.py rebuilt;
  query.py benchmark_parity r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1; 25 figures, 0 missing; stamp "Data as
  of Nov 4, 2026 · tracker Nov 4 · injured list Nov 4 · evidence
  Nov 2"; hardball_demo byte-identical copy.
- GATE: 107 ALL PASS first run, spellcheck green — no gate fix needed.
- BACKLOG ITEM (g) REFRESHED: HANDOFF.md gains a Cycle 82 December
  readiness checklist refresh. Freeze tag still owed; v1.1.12 is the
  current published release, not the freeze tag. Sportradar footer
  line correction still rides with the freeze cut (trial declined
  by the owner 2026-11-03).
- NEXT: final frozen-main release cut before Dec 1. Open PRs left
  untouched: #57 (Cycle 77 live refresh, predates the Cycle 78
  restore and the current main) and #58 (parallel-lane ticker
  trigger).
- REBASE (same run): main moved three times while PR #90 was open
  (#88 About portrait, #89 Story team errors, #91 Explorer player
  errors — all touch dashboard_p6.py and the built HTMLs). Branch
  rebuilt twice from the then-new main (ad069f3d, then fe34029f;
  #88/#89/#91 files synced in; Cycle 82 data/docs kept, bases
  verified unchanged by blob hash); dashboard rebuilt from the
  new code + Cycle 82 data and re-gated; PR #90 closed as
  superseded by the rebased PR.
- SPELLCHECK FIX (mechanical): rebased rebuild flagged "sabr"
  (SABR Defensive Index, Rawlings Gold Glove criteria, cited
  in-panel) — correct term, added to the spellcheck whitelist
  with a Cycle 82 comment per the script's own rule; no panel
  wording changed. Spellcheck green after; gate 107 ALL PASS.

## Cycle 83 — tracker refresh (Nov 4) + December checklist refresh (24/7 job, 2026-11-04 ~20:13 PT)
- DEADLINE GUARD: 2026-11-04, inside the build window (closes Dec 1).
- BASE: main e1801d20 (Cycle 82 merge + parallel-lane PR #93-#99). Tarball 404 on codeload redirect again; base verified blob-by-blob (git blob hashes) via the API recursive tree after syncing dashboard_p6.py + both built HTMLs — zero diffs.
- Spotrac probe: single GET Rays 2026 payroll -> 403. Salaries 24/30 + Cot's 7/7. FanGraphs not re-probed (item c failed-closed).
- Feeds SKIP: live feeds 5.9h < 20h watermark; evidence 2d < 6d guard. EVIDENCE.html untouched. No FastballAPI credits spent.
- Ticker: window 2026-10-29..2026-11-05; SIGNED 849 -> 846 (4 Oct-28 items aged out of the window, 1 Nov-4 item in — Zak Kent released by Washington; nothing else lost), REPORTED 200 (80 rotated by newest-200 cap, by design), BUZZ 0, total 1049 -> 1046. Jetstream handshake 403 fail-closed; Google News 200.
- Platform: ingest 0 failures (Savant bands hold; transactions raw 122,135 -> 122,163 raw-zone only); curate 20 tables, contracts pass; _build_report.json identical to main's — no curated change shipped; warehouse rebuilt; parity r = 0.889, 201 matched — exact. Routine ingest manifest appends restored, not shipped (Cycle 80-82 practice).
- Dashboard: rebuilt lake-present + HARDBALL_OFFLINE_BUILD=1 from synced parallel-lane code (#93-#99); 25 figures, 0 missing; stamp "Data as of Nov 5, 2026 · tracker Nov 5 · injured list Nov 4 · evidence Nov 2"; hardball_demo byte-identical copy.
- Gate: 107 ALL PASS first run, spellcheck green — no gate fix needed.
- Backlog item (g) refreshed: HANDOFF.md Cycle 83 section + BML_LOG.md Cycle 83 entry. Freeze tag still owed; v1.1.12 current release; Sportradar footer correction rides with freeze cut.
- Open PRs untouched: #57, #58. Next: final frozen-main release cut before Dec 1.
- Work tree: ~/workspace/hardball/work83 (verified main e1801d20 + lake copy; gitignored outputs excluded from PR).
