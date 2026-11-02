# Cycle 49 — OPT-1: roster optimizer (Figure 25)

Owner-approved MIT-gap programme, increment 3 of 6. A real optimizer
next to the Cycle 26 greedy builds, comparison published.
**25 figures total**; figures 1–24 keep their numbers; Story
(6 chapters) and Boardroom (15 slides) unchanged; Figure 16's
rosters unchanged. GitHub Actions ignored per the owner's 2026-11-02
directive (minutes exhausted until Dec 1) — the local gate, platform,
and parity below carry the verification.

## The optimizer

- `src/bml_cycle49.py` → `data/optimizer_comparison_2027.json`.
  MILP via `scipy.optimize.milp` (HiGHS): binary player-slot
  variables maximizing total Steamer WAR subject to Cycle 26's exact
  positional quotas, 26-man roster, spend <= budget, one slot per
  player, and prior AAV <= 15% of the proposed cap ($36.795M).
- **Identical inputs, asserted**: the script imports Cycle 26's
  builder and reproduces `wow_scenarios.json` exactly (spend to the
  dollar, WAR to 0.05, identical 26 names per budget) before
  optimizing. Same 199-player pool, same Steamer WAR, same prior-AAV
  anchors (labeled last-price anchors, not predicted salaries).

## Results — all three optima proven (solver gap 0)

| Budget | Greedy WAR | Optimizer WAR | Delta | Overlap |
|---|---|---|---|---|
| Floor $171.2M | 42.0 ($171.0M) | **48.9** ($171.1M) | +6.9 (+16.4%) | 16/26 |
| Middle $208.0M | 45.7 ($207.3M) | **52.8** ($207.8M) | +7.1 (+15.5%) | 17/26 |
| Cap $245.3M | 52.3 ($244.6M) | **54.8** ($245.2M) | +2.5 (+4.8%) | 21/26 |

- **Decomposition**: a DH-restricted sensitivity (DH open only to
  DH-mapped players — the greedy's effective search space, since its
  any-bat fallback never triggers with two DH-mapped players in the
  pool) still finds +5.5 / +5.2 / +0.4. The floor/middle edge is
  mostly combinatorics; the cap edge is mostly the DH slot: greedy
  carries Dominic Smith (0.01 WAR) at DH at every budget, the
  optimizer plays Brandon Lowe (2.32 WAR).
- **15% per-player rule**: binds nobody in this pool (max anchor
  $35.0M < $36.795M); all three greedy rosters satisfy it (max AAV
  $22.0M / $32.0M / $32.0M); enforced as a hard constraint anyway.

## Exhibit + docs

- **Figure 25** (Explorer, Build a Roster): grouped greedy /
  optimizer / DH-restricted bars per budget + facts box (overlap, DH
  slots, 15% rule) — every number rendered from the artifact.
- CARPE_SCORECARD Cycle 49 addendum (method, decomposition, scope),
  BML_LOG Cycle 49, HANDOFF Cycle 49 section.
- Counts 24 → 25: dashboard source (docstring, index, button,
  Explorer), gate (+ Figure 25 and OPT-1 artifact checks), README,
  TALKTRACK (+ optimizer back-pocket Q&A), EXEC_SUMMARY, ONEPAGER
  generator (regenerated). Spellcheck WHITELIST += combinatorics,
  dh, milp, scipy.

## Verification

- Platform: ingest 25 datasets / 0 failures; curate 17 tables, all
  contracts pass, parquets byte-identical to committed; warehouse
  rebuilt; parity r = 0.889 / 201.
- Gate: `src/verify_data.py` ALL CHECKS PASS (offline), including the
  new Figure 25 + OPT-1 artifact checks; spellcheck green; DOM/text
  checks confirm 25 figures, Figure 25 in Explorer, 6 chapters,
  15 slides. No browser visual QA (standing rule).
