# Cycle 62 — BLEND-1: projection blend + the benchmark page

Slate item 2 of 6 (owner-approved elite/asset slate,
2026-11-02). The task: blend Steamer + Marcel into one
projection set — **adopted only if it earns the switch on
held-out actuals**. The bar was pre-committed before any
result: blend weights fit on the 2025 window only, judged
on 2026 only; adoption requires the 2026 primary-metric
MAE to beat BOTH parents for hitters and be no worse than
the best parent for pitchers. The benchmark page ships
either way — it is the deliverable.

## Verdict: blend NOT ADOPTED — it cannot be scored.

Step 0 (paired sets first, fail closed) found that no
paired set containing Steamer can be built:

- The repo holds Steamer only for 2027 (FanGraphs API pull
  2026-10-31) — a season not yet played, so no outcomes
  exist to score it against.
- The FanGraphs API ignores its `season` parameter
  (probed 2026-11-02): the "2026" response is the current
  set — 4,166 rows, 4,164 MLBAM IDs in common with the
  committed 2027 file, differing only at update-noise
  level.
- steamerprojections.com's pre-season archive ends at
  2024, and the Marcel inputs for 2023/2024 targets
  (2020–2022 player lines) are not committed —
  `fact_stat_lines` begins 2023. Its weekly-logs page
  returned no usable content.

No weights were fit (nothing legitimate to fit them on),
no 2027 blended set was produced, and no optimizer shadow
run was made (adoption-gated). Steamer remains the
published 2027 projection set and Marcel the spine,
unchanged — headlines, UNC-2 intervals, and HS-2
untouched.

## What the benchmark does show (2026 judge window)

Paired sets from the curated warehouse, Cycles 21/24
loaders mirrored; `src/bml_cycle62.py` first regenerates
the committed variant-B backtests from `fact_stat_lines`
and matches them exactly (all four cells) before computing
anything new. Paired n: hitters 88 (2025) / 80 (2026),
pitchers 23 / 22.

| Forecaster | Hitter OBP r / RMSE / MAE | Pitcher ERA r / RMSE / MAE |
|---|---|---|
| Last season, repeated | .298 / .0329 / .0265 | −.086 / 1.1899 / 1.0177 |
| Marcel (shipped, cross-fitted age) | .410 / .0284 / .0237 | −.020 / 1.0928 / .9394 |
| Steamer | not scored | not scored |
| Steamer + Marcel blend | not scored | not scored |

Marcel beats the naive repeat on every error measure in
2026 (and on SLG/WHIP — in the artifact). Pitcher ERA
ranking was near chance for both forecasters that year
(n = 22); the panel states that plainly.

## This PR

- `src/bml_cycle62.py` — the benchmark build (design +
  bar stated in the docstring; reproduction assertion
  inside).
- `data/projection_blend_2027.json` — paired-set
  description, split design, the full metrics table (all
  four forecasters, both groups, both windows), Steamer
  probe evidence, the bar verdict, the recommendation.
- `src/dashboard_p6.py` — the benchmark panel "How good
  are these projections?" under Figure 18 in Explorer
  (companion HTML, not a figure; count stays 25), rendered
  from the artifact; absent the artifact it is omitted.
- `src/verify_data.py` — 3 new BLEND-1 gate checks
  (artifact complete for all four forecasters; reproduction
  anchor matches the committed backtests; panel strings
  verbatim).
- `src/spellcheck_gate.py` — whitelist: actuals, rmse.
- `docs/CARPE_SCORECARD.md` — Cycle 62 addendum.
- `HANDOFF.md` — Cycle 62 section + Next.
- `docs/BML_LOG.md` — Cycle 62 entry.
- `PR_BODY.md` — this file.

## Verification

Gate: **81 checks, ALL PASS**; spellcheck green; platform:
17 rebuilt curated tables byte-identical (2 skipped in the
clean tree — raw absent, committed parquets stand),
warehouse rebuilt from 19 tables, benchmark parity
**r = 0.889 / 201**. The dashboard changed, so release
**v1.1.2** is cut on the merged tree per the Cycle 60
pattern and the published copy probed from the release
tarball.

Recommendation on record: do not rewire the stack onto a
blend now — the first honest test arrives after the 2027
season, when the committed Steamer 2027 set can be scored
against 2027 actuals on this same paired design.
