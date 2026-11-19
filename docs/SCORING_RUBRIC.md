# Scoring rubric — what a 9 means here

Independent reviews swung ±1 between rounds with no code change (reviewer
variance). To iterate faster and converge, every dimension now has explicit,
mostly machine-checkable criteria. `python src/scorecard.py` evaluates the
checkable ones in seconds; a human or agent reviewer confirms the rest. A
dimension scores 9 only when **every** item in its list holds.

## Code quality
- [auto] Lint clean (`ruff check src tests`).
- [auto] Unit tests pass. There are at least 25 tests, and every new shared
  module (`http_client`, `check_freshness`, `forecast_eval`, `decision_brief`,
  `check_connectors`) has a test file.
- [auto] CI workflow runs lint, tests, the rebuild diff and all gates.
- [auto] The build is deterministic: no random div ids in the artifact.
- [review] Shared logic lives in modules, not copied across cycle scripts.

## API & data health
- [auto] **Zero** external fetches bypass `http_client` (ratchet test).
- [auto] 403/429 are never retried (project rule). 5xx are retried with
  jittered backoff.
- [auto] `verify_data.py` passes: every cited snapshot is committed and its
  hash matches.
- [auto] `check_freshness.py` passes: provenance and artifact checks.
- [auto] Connector check uses a rolling window and reports errors.

## UI/UX
- [auto] Plotly is vendored. The page renders 48/48 charts offline with 0
  console errors.
- [auto] `lang`, main landmark, and `role="figure"` with `aria-label` on every
  panel.
- [auto] No horizontal scroll at 390 px. The decision brief sits above the
  colour key.
- [review] First screen states the decision; the glossary does not push it
  down.

## Insight
- [auto] A decision brief exists with a ranked, priced list and a surplus.
- [review] At least one non-obvious, quantified finding a front office would
  not already know (e.g. N08: Marcel ≈ repeat-last-season; S25: only one
  move clears +$5M).

## Rigor
- [auto] Projection error is reported with bootstrap CIs and a
  Diebold–Mariano test against naive baselines.
- [auto] The claims register reconciles. NOT SUPPORTED and RETRACTED claims
  stay visible.
- [review] Bands are derived from measured error, and the limits are stated.

## Actionability
- [auto] The decision brief has an act-by date, a P10–P90 band, a price
  basis, a fallback and a CSV export.
- [review] A reader knows what to do this week without opening another
  figure.
