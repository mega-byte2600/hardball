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
