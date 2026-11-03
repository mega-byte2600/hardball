# HARDBALL — Feature Map (for collaborating agents)

Everything a working feature is and how to reproduce it. Source of truth is
the code + committed data + gates + `docs/BML_LOG.md` (build-measure-learn
audit trail, one entry per cycle). If a feature isn't here it doesn't exist
in this tree; if it is here but the gate red, it's the thing to fix first.

> How to work this repo: read `/docs/BML_LOG.md` max cycle before numbering a
> new cycle (lanes collide — always verify the next number is free, renumber
> if it isn't). Fetch + rebase `origin/main` before EVERY push (the owner and
> a second agent push live). Never force-overwrite. Commit small, push often —
> GitHub must visibly match work. Internal renders go to `/tmp` only.

## Build order (the pipeline that produces the deck)

```
1.  src/carpe.py                    keyless connectors: MLB Stats API, ESPN,
                                    Baseball Savant (statcast), FanGraphs
                                    Steamer, MLB minors   -> data/raw/*
2.  src/ingest.py / src/curate.py   lake -> curated tables -> build_warehouse
3.  src/bml_cycle<N>.py             each analysis cycle writes its committed
                                    data artifact + verifies it internally
4.  src/dashboard_p6.py             assembles dashboard/hardball_demo.html
                                    (the 25-figure, 3-mode deck)
5.  src/verify_data.py              THE GATE — 75 checks (prints
                                    "GATE: ALL CHECKS PASS" or FAIL + reasons)
6.  src/spellcheck_gate.py          no misspellings in user-visible text
7.  src/accuracy_monitor.py         watchdog (Hermes cron) runs gates + freshness
8.  src/make_onepager.py            docs/ONEPAGER.html (print executive sheet)
```

Run the gates after ANY change before you commit:
`.venv/bin/python src/verify_data.py` and `.venv/bin/python src/spellcheck_gate.py`.
The dashboard HTML is gitignored-but-tracked on this branch (a prior lane
committed it); when you rebuild you must also `git add` it so the artifact
matches the source you pushed.

## Live-market wire (cron / feeds)

- `src/refresh_live_feeds.py` — refresh the live-IL picture and the evidence
  surveillance lanes (fail-closed: watermark/credit guards, keys from env).
  NOTE: uses `Optional[datetime]` (Python 3.9-compatible) — never PEP 604 `|`.
- `src/pull_evidence_surveillance.py` — pull PubMed/NCBI evidence cards, fail-closed.
- `src/pull_tracker_ticker.py` — free-agency ticker: SIGNED (MLB StatsAPI
  transactions, codes SFA/DFA/TR/REL/CLW/OUT/DES) / REPORTED (news) / BUZZ (Bluesky).
- `src/accuracy_monitor.py` + `src/check_freshness.py` — 24/7 watchdog (4 checks:
  verify gate, freshness vs sources, artifact exists, served). Runs via Hermes
  cron every 20m; appends docs/HEALTH_LOG.md. Was silently broken by a restructure
  (missing file); restored 2026-11-03.
- Keys: never commit them. Only the env names `STATYX_API_KEY` / `FASTBALL_API_KEY`
  exist; values live on the offline `astra-worker` vault. Without them the feed
  scripts SKIP (fail-closed) — that is correct behavior, not a bug.

## The 25 figures (Explorer), each traced in data/figure_trace_2027.json

Traced and verified by `src/bml_cycle68.py` (trace + claims register) and
`src/bml_cycle69.py` (bookkeeping: closes open item O01 — Figure 9's in-sample
label). Sequence matters: cycle68 then cycle69, or cycle69's resolved item
regenerates open again. Trace asserts every figure's artifact exists and its
gate strings appear in the HTML.

1.  Animation: 16 seasons payroll vs wins (boardroom slide 1)
2.  Pick your team — radar (interactive, all 30 clubs)
3.  Skills persist year-to-year (contact r ~0.84 pooled; OBP weaker)
4.  Runs panel (30 teams, 2026 slice)
5.  AUC panel (run differential flags 90+ club, AUC ~0.95)
6.  Payroll vs wins, cap/floor lines
7.  KPI signature (contact/K%) — the winning-cheap profile
8.  Durability / efficiency
9.  Projected wins: "Model fit (in-sample) vs actual wins" + actual-wins overlay
   (relabeled Cycle 69 so in-sample values are labeled, not dressed as forecasts)
10. Cap scenario: over-cap count from artifact (7 teams over)
11. Forced sellers (6 covered, CHC the lone uncovered)
12. Hitter projections: top-OBP name leads
13. Pitching panel from the lake
14. Health panel: live-IL counts + pull date
15. Roster panel (13 hitters + 13 pitchers)
16. Scenario/floor: build vs cap at 3 budgets; headline = proven-optimal rosters
17. Sensitivity / elasticity table
18. Benchmark panel: Marcel vs Steamer (title carries r + top-25 overlap)
19. Savant trait-stability panel
20. Value metrics (hitting + pitching tables)
21. Pipeline panel (30 orgs)
22. **SURPLUS-VALUE arbitrage (Cycle 71)** — the 2027 FA market by surplus
    value (projected wins in dollars minus expected market cost). Source:
    data/surplus_value_2027.json, built by src/bml_cycle71.py from committed
    fa_shopping_2027.json (steamer_war, spotrac_market_aav) + Hakes–Sauer $/WAR.
23. The Posted Class (Japan: Sato/Taira/Itoh) — Explorer-only live-market exhibit
24. Hakes–Sauer verdict (our own pricing test; honest INCONCLUSIVE)
25. Optimizer audit (MILP vs greedy benchmark)

## Cycle-71 ARBITRAGE layer (Moneyball 2.0)

Ranks the 2027 free agents by SURPLUS VALUE = projected dollars of
wins (Steamer WAR x market $/WAR) MINUS expected market cost (Spotrac market
AAV) — the operative number a real front office decides on (Miami Marlins VP of
Baseball Systems, Posit 2025). Moneyball 2.0 is pricing the whole market against
one value reality, then trading the gap.

- `src/bml_cycle71.py` -> `data/surplus_value_2027.json`
- market $/WAR = median of the class's OWN implied rate
  (spotrac_market_aav / steamer_war) = $8.16M. NOT invented — committed.
- 12 of 25 surplus-positive. Contact-skill discount surfaced from committed
  Hakes–Sauer run: top-quartile CONTACT hitters ~$8.0M/WAR vs ~$15.0M/WAR
  bottom quartile (~54% cost). Stated as descriptive contrast, never a proven
  price effect (the Hakes–Sauer test is INCONCLUSIVE).
- Panel: Figure 22 rewritten to rank by surplus; green = surplus-positive,
  red = overpriced; value-vs-cost in the labels.
- Honest caveat: surplus is a valuation, not a settled mispricing — a cheap
  player can be cheap for injury/role/age risk.

## Cycle-73 PREDICTION TRANSPARENCY layer (RBP-style conviction)

Per-project how-trustworthy-before-acting label, the MIT relevance-based
prediction goal done on committed data (no Mahalanobis reimplementation):
- `src/bml_cycle73.py` -> `data/prediction_conviction_2027.json`
- conviction = input_stability from committed PRIOR-season contact%/BB%
  spread across 2+ years (data/player_yoy.json). 49 HIGH / 30 MEDIUM /
  1 LOW / 121 NO_PRIOR. The 121 with no committed 2-season record are
  honestly labeled NO_PRIOR (capped below HIGH), never inflated.
- Proj_PA is deliberately NOT a signal (uniform 500-PA default = invented
  axis). Do not reintroduce it.
- Surface: per-bar label + legend on Figure 12 (2027 projected hitters).

## Savant refinement backtest — ALREADY SHIPPED (read, do not rebuild)

data/savant_test.json (Cycle 20): xwOBA is a better projection INPUT
(Q1), but every feature family (batted-ball, bat-tracking, all) was
DROPPED as a projection adjustment (F1-F4) — bat speed (YoY r .92, the
most stable trait) made projections WORSE out-of-sample. Claim N04 NOT
SUPPORTED; Figure 19 diagnostics only. If asked "can we add bat speed /
swing-path / attack-angle?", the honest answer is already committed: NOT
as a projection feature. Any further work is a product/demo exhibit only
(novel bat-speed framing), not a modeling claim — an open thread for Toby.

## The math (built literature-first)

Model + validation in `src/model_p6.py`; provenance in
`docs/LITERATURE_SPINE.md` + `docs/citations_ledger.json` (committed, in-repo).
- Baseline: Marcel-style weighted projection (5/4/3) + regression to league mean
  + modest age term. Benchmarked against Steamer (r=.889 / 201 matched).
- The frontier (THE BAT X / THE BATcast, PECOTA-StuffPro, Temporal Fusion
  Transformer) is Statcast-aware and, per published backtests, beats surface-stat
  blending. HARDBALL's honest position: a defensible reproducible baseline, NOT
  the frontier; Statcast features enter as a TESTED refinement (backtest decides),
  never assumed.
- Key rule (from the literature): do NOT over-invest in exotic aging math
  (pre-registered Bayesian test: indistinguishable from baseline). And: run
  differential describes wins, it does not forecast them — only a lagged spec
  is a real test.

## Data sources (all real, keyless where noted)

- MLB Stats API (statsapi.mlb.com/api/v1) — hitting, pitching, standings, schedule, transactions, injuries(via transactions)
- ESPN API — validation/redundancy
- Baseball Savant / Statcast — expected stats (xwOBA/xBA), exit velo, launch angle, sprint, bat/swing metrics. Export trick: append `csv=true` to any leaderboard URL (verified: 251 hitters, 14 cols, 0.6s). Only goes back to 2015.
- FanGraphs Steamer — 2027 projections (Marcel benchmark layer)
- Spotrac (MIT-licensed mlb-payroll) — 2026 salaries + 2027 FA class / market AAV
- MLB transactions feed — injury/IL history (120k+ events)
- Font: data/player_persistence*, data/persistence_ci for the persistence result

Known feed blockers (do NOT route around, log them): Spotrac single GET 403,
FanGraphs RosterResource 403 (Cloudflare), GDELT 429, NewsAPI/GNews dev-only,
X no free tier, Reddit 403, Bluesky AppView search 403. Salaries are 24/30
team pages, forced-sellers 6/7, until the Sportradar trial (~mid-Nov, timed to
cover the Dec 1 lockout).

## Gates & honesty

- `src/verify_data.py` — 75 checks, the load-bearing gate. Green = "GATE: ALL
  CHECKS PASS". Any figure's gate strings updated when the title/source changes
  (stale gate = the exact failure to look for).
- `src/spellcheck_gate.py` — no misspellings in user-visible text.
- `src/accuracy_monitor.py` — 4 checks, watchdog, writes docs/HEALTH_LOG.md.
- The deck's honesty boxes: Story appendix (method + honesty), Figure 23's
  translation box, the Honest limits section of README. Never a fabricated
  number; a claim that committed data can't support is FLAGGED, not smoothed.

## Presenting

Live at http://127.0.0.1:8890/dashboard/hardball_demo.html
Build: `.venv/bin/python src/dashboard_p6.py` then serve the `dashboard/` dir.
Three modes: Story (6 chapters), Boardroom (15 slides, print-clean via
docs/TALKTRACK.md), Explorer (all 25 figures by task).
