# HARDBALL — Literature Spine (P3)

Research base grounding the 2027 projection demo. Every source below was
fetched and read during the P3 sweep; citations are to the exact documents.
No fabricated references. This is the load-bearing wall the model design
(P4-P7) must build from — glean the math here, do not reinvent it.

Status: live working base, Nov 2026. Sources are registered in the
grounded-citations ledger — now committed to the repo at
`docs/citations_ledger.json` (30 sources with access dates), so every agent
and collaborator with repo access can audit the evidence trail. The local
agent cache mirror lives at `~/.hermes/cache/citations/ledger.json`.

---

## 1. The Moneyball frame (why this project has value)

- Moneyball (Michael Lewis, 2003): the edge = finding where the *market*
  misprices players, not merely computing more stats. Lewis, at MIT Sloan
  2025: analytics movement is a product of expensive decisions — "if you're
  going to pay them $50 million, you better get it right." [20]
- The edge has *moved*: everyone now hunts the same advanced stats, so
  HARDBALL's question is where the market is still wrong today (the
  copycat-league analysis in P5).

## 2. The projection math (what a 2027 offense projection actually is)

### 2a. Marcel (Tango) — the baseline every system is measured against
- Weighted average of the past 3 seasons, most recent weighted most
  (canonical 5/4/3 weights), regressed toward league mean, plus an age
  adjustment. MLB data only, no minors/college. [9]
- Steamer = Marcel-style weighted average but with regression weights *fit
  by regression analysis per stat* rather than fixed; ZiPS = weighted avg
  over 4 years (3 for very young/very old) + historical-player comparison
  clustering (PECOTA-like). [9][8]
- KBO Marcel-style implementation (empirical Bayes regression-to-mean,
  delta-method aging, temporal backtest 2021-24): Marcel beats prior-year-
  only and league-average baselines on all 5 hitter stats (wOBA, ISO, HR%,
  K%, BB%); optimal regression m≈1 at 300+ PA; aging peak 24-27. [17]

### 2b. The critical result on aging (do NOT over-invest here)
- Pre-registered Bayesian (Stan) dynamic hierarchical aging curve vs Marcel
  on 2025 MLB data: **statistically indistinguishable** — MAE -0.00067 vs
  no-aging -0.00071, both 95% CIs include 0. Peak age 26-27. [15]
  Implication: for next-season wOBA, a baseline projection + modest aging
  beat is defensible; elaborate aging math buys ~nothing.
- Survival bias: aging curves overestimate decline when unobserved/retired
  seasons are ignored. Multiple imputation (Nguyen & Matthews) and
  imputation+regression (Schuckers, Lopez, Macdonald) correct this. [1][2]
  For our 1-season-ahead demo this matters less than for long career arcs,
  but it justifies regression-to-mean.

### 2c. MIT relevance-based prediction (RBP) — the most current, full-text authoritation
- Czasonis, Kee, Kritzman, Turkington, Cambridge Sports Analytics / MIT Sloan
  lecturer. "Prediction with Transparency: Offensive Value in Baseball,"
  Nov 5 2025. [18]
- Method: model-free. Prediction = relevance-weighted average of prior
  players' observed outcomes, where relevance = similarity + informativeness,
  both Mahalanobis distances (eqs 1-4). Fit = per-prediction reliability
  (equal to R^2 when aggregated, eqs 10-12). Grid prediction = reliability-
  weighted blend across all variable/threshold calibrations (eqs 13-16).
- Validation: training 1,601 players (2015-23), predict 2025 wRC+.
  Transparency: high-conviction predictions spread 34, low-conviction 2 —
  RBP distinguishes trustworthy from doubtful predictions in advance, which
  regression cannot. On the linear dataset, RBP's overall accuracy equals
  linear regression (spread 18 = 18).
- Soto case: predicted wRC+ 157 (99.6th pct, 99.9th pct conviction) vs
  realized 156. Carroll: predicted 114 vs realized 139 (underestimated, as
  its lower conviction flagged).
- Practitioner uptake: this is the current, defensible "market-price-the-
  outlier" approach — relevant players weighted by how like the target they
  are. Strong candidate backbone for P6.

### 2d. Machine-learning successors
- Heaton & Mitra, "Learning to Describe Player Form in the MLB" (SSAC 2022
  finalist, open code): Statcast form embeddings, 59% game-winner accuracy
  combined with sabermetrics. [19]
- LSTM-based MLB prediction (arXiv 2206.09654): Marcel background +
  sequential/age modeling. [8][3]

### 2e. State of the art 2025-26 — the frontier has moved past classic Marcel
- **THE BAT X / THE BATcast** (Derek Carty, FanGraphs) [31]: blends classic
  THE BAT (surface stats) with a Statcast "stuff" model (velocity, movement,
  spin, seam-shifted wake, pitch mirroring, tunneling/bridging across the full
  pitch trajectory, ~4,000 candidate pitch variables reduced by ML). Ball-in-
  play and pitching outcomes are projected from Statcast inputs, not surface
  stats alone. This is the current gold-standard Statcast-aware projection.
- **PECOTA 2025** (Baseball Prospectus) [32]: integrated StuffPro into balls-
  in-play projection; back-test on 2024 improved pitcher accuracy by >341 runs
  (rookies +113). Aging/projection still Marcel-style weighted history + analog
  matching, but Statcast-stuff features now enter the hit-model.
- **Temporal Fusion Transformer (TFT)** for pitcher ERA (Computers, Materials
  & Continua 2025) [33]: cuts sequence-horizon; on 2023 data Full-TFT beat
  12 RNN/CNN variants AND beat ZiPS, ATC, Depth Charts, Steamer, THE BAT — best
  RMSE 0.481 / MAE 0.363 on 4-season windows. Evidence the frontier is a
  transformer on recent Statcast+surface sequences, not a fixed-weight blend.
- **ZiPS 2025** [34]: four-year weighted history + analog aging + Monte Carlo
  (million team sims); the accuracy bar every new system is held to.
- **Bayesian/hierarchical matchup models** [35][36]: arXiv 2025 work shows
  pitcher-batter-handedness-recent hierarchical models predict plate-appearance
  outcomes toward subgame-perfect strategy — the "next" frontier after
  point projections, incl. win prediction across 6 model families.
- **Honest position for HARDBALL:** our player projections use Marcel-style
  history + regression-to-mean; we BENCHMARK publicly against Steamer (r=.889 /
  201 matched). The frontier systems (THE BAT X, PECOTA-StuffPro, TFT) are
  Statcast-aware and, per published back-tests, beat surface-stat blending. To
  stay current we adopt Statcast features (xwOBAcon, barrels) as a *tested*
  refinement layer and log a TFT / Statcast-feature baseline as an open BML
  question — we do not claim Marcel alone is state of the art; we claim a
  defensible, reproducible baseline benchmarked against the public frontier.

## 3. Statcast expected stats — what predicts vs just describes

- **xwOBA->next wOBA r^2 ~= .218** vs raw wOBA->wOBA .191 (Fantrax, 7
  seasons): expected stats are predictive but only *marginally* better than
  actuals. [10]
- xwOBAcon correlates more strongly year-to-year than wOBA or xwOBA for
  hitters, because it strips unstable BB/K. [10]
- Barrel% = similarly sticky to K%/BB% year-to-year; Brls/BBE% slightly
  stickier than Brls/PA%. Flares/burners are noisy. [10]
- Stay away from *average* exit velocity (noisy); prefer avg EV on FB/LD,
  max EV for small-sample young players, hard-hit%. [10]
- These are DESCRIPTIVE stats ("what should have happened"), not built
  projections; but as *features* feeding a projection they carry
  year-over-year signal. [10]

## 4. Biomechanics / kinematics — what drives bat speed (for the bat-speed angle)

- Bat speed correlates with lead-foot ground-reaction forces: vertical GRF
  r=0.622, posterior r=-0.574, resultant r=0.662 (Sports Biomech 2024,
  20 collegiate hitters, 500Hz / 1000Hz capture). The lead leg generates +
  transfers force up the kinetic chain. [4]
- Swing kinetics (J Appl Biomech 2018, 306 swings, 13-18y): force dominated
  by pull along bat long axis early; moment minimal until just before
  impact, then a rapid increase. [5]
- Skill levels differ on max bat speed (high caliber 36.8 vs low 33.8 m/s,
  p<0.05) and lead-elbow angular velocity (+36%), NOT on linear wrist/hip
  velocities. [6]
- Canonical kinetic-chain sequencing (Welch, JOSPT 1995): weight shift rear
  foot -> front-foot force ~123% BW -> hip 714 deg/s -> shoulder 937 deg/s ->
  max linear bat vel ~31 m/s. [7]
- Implication for HARDBALL: bat speed / swing length / attack angle are the
  *observables* of this kinetic chain, now tracked by Statcast (Hawk-Eye,
  2024+). Biomechanics literature supports them as meaningful mechanical
  descriptors; whether they add year-over-year *predictive* value on top of
  xwOBA is the empirically-testable question for P6 (test, don't assume).

## 5. Injury / recovery (health variable — injury is a data source, not just a variable)

The MLB Stats API exposes injury data (`teams/{id}/injuries`, league-wide
`injuries`, transactions) — so injury history is a *pulled, real data source*
we can join to projections, not a hypothetical.

### Hitters absorb injury impact; pitchers absorb workload impact
- **Oblique strains (2026)** — the injury with the biggest single published
  hitter-performance bite: hitters declined SLG .43->.38, OBP .323->.303,
  OPS .749->.686, BABIP .307->.280, avg exit velo 83.3->82.3, hard-hit
  25.3%->23.0%, OPS+ 103->92 (all p<.001). Pitchers: only K/9 declined
  (9.13->8.44). Time-to-return had no effect. Rehabilitation should restore
  *rotational power* in hitters. [21]
- **Shoulder labral repair** — a pitcher offramp: pitchers returned to MLB
  43.6% vs position players 92.9%, and took >200 days longer (493 vs 285).
  Returning pitchers were at <50% of preinjury fWAR their first season back;
  IP dropped 95.7->43.1; Stuff+ stayed depressed into season 2. [22] health
  flag for elite pitchers, not speed).
- **UCL (systematic review, 18 studies n=2887)** — RTP 80-91%; recovery
  ~11.6 months professionally; velocity is the strongest predictor of UCL
  tears. [24]

### Injury risk itself is modelable
- ML ensemble predicted next-season MLB injury with AUC 0.76 (position
  players) / 0.65 (pitchers) from age + injury history + performance. Injury
  risk is a legitimate projection input, not noise. [23]
- Workload (ACWR): acute:chronic ratio spikes >1.27 raised throwing-injury
  risk ~15x in a tracked cohort; chronic load >11.3 elevated risk. Pitch
  *count* alone is poor; velocity + intensity + age matter. [25][26]

### What this adds to HARDBALL
The market prices last season's *outcomes* but under-prices *recovery risk*
(Tommy John arms, hitters post-oblique). A 2027 projection that flags a
player as "past value masked by: injury history, position-specific recovery
curve, workload" is a genuinely underpriced variable — Moneyball-compliant.
Concretely: injury history + injury type + recovery timeline as features in
the projection layer, joinable from the MLB injuries endpoint.

## Journals targeted (and why)

| Journal / venue | Why |
|---|---|
| J. Quantitative Analysis in Sports (JQAS) | the peer-reviewed saber home; Fair aging, projection validation |
| Annals of Operations Research | Schuckers/Lopez/Macdonald aging paper |
| Sports Biomechanics / J Appl Biomech / JOSPT | swing kinetics-kinematics, bat speed drivers |
| J. Sports Analytics (IOS Press) | bridging analytics + sport science |
| MIT Sloan Sports Analytics Conference | where teams publish tracking/projection advances |
| arXiv (stat.ME, stat.AP, cs.LG) | modern ML projection methods, full text, no paywall |
| PLOS ONE / MDPI Sports | open-access full text we can ingest |

## Open-source projects surveyed (don't reinvent — adapt)

| Repo | What it offers |
|---|---|
| jackseeburger/baseball-projections | Bayesian PyMC + Marcel baseline + backtest harness |
| nielsjsc/LSTMLB | Marcel + LSTM, 7-component engine |
| yasumorishima/baseball-mlops | Statcast xwOBA prediction vs Marcel (LightGBM/CatBoost) |
| yasumorishima/baseball-bayes | pre-registered aging-vs-Marcel result (KEY evidence) |
| Jack1021ohoh/MLB_Position_Player_Aging_Analysis | GAM aging + IPW survivorship, 1980-2025 |
| kellytodhunter/KBO-Player-Analysis | Marcel + empirical-Bayes + delta-aging + backtest |

## Load-bearing conclusions for the build

1. Baseline = Marcel-style weighted projection (5/4/3) with regression-to-
   league-mean + modest age adjustment. Proven, documented, reproducible. [9][17]
2. Do NOT spend on elaborate aging curves — pre-registered evidence says
   they add ~nothing for next-season wOBA. [15]
3. The defensible differentiator is RBP-style *transparency* (per-prediction
   reliability + player/variable contribution), not a black-box model. [18]
4. Statcast features (xwOBAcon, barrels, bat speed) enter as a *tested*
   refinement layer; the pre-registered backtest decides if they beat the
   Marcel baseline. That honesty is the demo's credibility. [10]
5. Bat-speed observables are mechanically grounded (kinetic chain); their
   incremental predictive value is an open question we can genuinely
   contribute evidence on. [4][5][6][7]

## Sources

[1] https://arxiv.org/abs/2110.14017 — Estimation of Player Aging Curves: Regression & Imputation (Schuckers, Lopez, Macdonald)
[2] https://ar5iv.labs.arxiv.org/html/2210.02383 — Filling the Gaps: Multiple Imputation Aging Curves MLB (ar5iv)
[3] https://ar5iv.labs.arxiv.org/html/1712.05754 — Understanding Career Progression in Baseball via ML
[4] https://pubmed.ncbi.nlm.nih.gov/37853750 — Lower extremity kinematics/kinetics & bat speed (Sports Biomech 2024)
[5] https://pubmed.ncbi.nlm.nih.gov/29651903 — Kinetics of Swinging a Baseball Bat (J Appl Biomech 2018)
[6] https://pubmed.ncbi.nlm.nih.gov/21085044 — Kinematics of baseball swing, varying skill (2010)
[7] https://www.jospt.org/doi/10.2519/jospt.1995.22.5.193 — Hitting a Baseball: Biomechanical Description (Welch, JOSPT 1995)
[8] https://arxiv.org/pdf/2206.09654 — Performance Prediction in MLB by LSTM (arXiv)
[9] https://tht.fangraphs.com/evaluating-the-2014-projection-systems — Evaluating 2014 Projection Systems (Hardball Times)
[10] https://pitcherlist.com/fantasy-101-how-to-evaluate-hitters-using-multiple-statistics — Evaluating hitters: Statcast descriptiveness vs predictiveness
[15] https://github.com/yasumorishima/baseball-bayes — baseball-bayes: pre-registered Bayesian aging vs Marcel result
[17] https://github.com/kellytodhunter/KBO-Player-Analysis — KBO Marcel-style projection + empirical Bayes + delta aging + backtest
[18] https://mitsloan.mit.edu/shared/ods/documents?PublicationDocumentID=10724 — RBP: Prediction with Transparency - Offensive Value in Baseball (Czasonis/Kritzman, MIT/Cambridge Sports Analytics, Nov 2025)
[19] https://arxiv.org/pdf/2109.05280 — Learning to Describe Player Form in the MLB (Heaton & Mitra, SSAC 2022 finalist)
[20] https://news.mit.edu/2025/five-ways-to-succeed-sports-analytics-0313 — MIT News: Five ways to succeed in sports analytics (Lewis on Moneyball, Bill James runs created)
[21] https://www.tandfonline.com/doi/full/10.1080/00913847.2026.2723859 — Oblique strains in MLB: hitter performance decline (2026)
[22] https://pmc.ncbi.nlm.nih.gov/articles/PMC12953945 — RTP + performance after shoulder labral repair MLB (pitcher vs position)
[23] https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7672741/pdf/10.1177_2325967120963046.pdf — ML predicts next-season MLB injury: AUC 0.76 pos/0.65 pit (2020)
[24] https://pmc.ncbi.nlm.nih.gov/articles/PMC12853774 — UCL injury mechanisms + RTP criteria systematic review
[25] https://ijspt.org/wp-content/uploads/2024/01/4-Dowling-1.pdf — Workload comparison interval throwing programs, ACWR, >1.27 ~15x risk
[26] https://pubmed.ncbi.nlm.nih.gov/40021256 — RTP throwing programs (Clin Sports Med 2025)
[31] https://blogs.fangraphs.com/introducing-the-bat-x-for-pitchers-and-the-batcast-stuff-model/ — THE BAT X for pitchers + THE BATcast stuff model (Derek Carty, FanGraphs)
[32] https://www.baseballprospectus.com/news/article/96300/pecota-week-pecota-2025-an-introduction/ — PECOTA 2025: StuffPro integration (+341-run pitcher accuracy)
[33] https://www.sciopen.com/article/10.32604/cmc.2025.065413 — Pitcher Performance Prediction by Temporal Fusion Transformer (Computers, Materials & Continua 2025)
[34] https://blogs.fangraphs.com/the-official-and-hopefully-not-too-regretful-2025-zips-projections/ — Official 2025 ZiPS Projections (FanGraphs)
[35] https://arxiv.org/abs/2511.02815 — Assessing win strength in MLB win prediction models (arXiv, 2025)
[36] https://arxiv.org/abs/2511.17733 — Impacts of Increasingly Complex Matchup Models on Baseball Win Probability (arXiv, 2025)
