# Cycle 50 — OPT-2: optimizer sensitivity + mixed pre-arb/FA floor

Owner-approved MIT-gap programme, increment 4 of 6. Stress-tests
OPT-1's proven optima and runs the mixed pre-arb + FA floor build.
**Figure count stays 25**; Figure 16's rosters, Story (6 chapters)
and Boardroom (15 slides) unchanged — replacing the greedy rosters
remains an owner decision, explicitly out of scope. GitHub Actions
ignored per the owner's 2026-11-02 directive (minutes exhausted
until Dec 1) — the local gate, platform, and parity below carry
the verification.

## The build

- `src/bml_cycle50.py` → `data/optimizer_sensitivity_2027.json`.
  Cycle 49's MILP (scipy/HiGHS) imported unchanged; a base-case
  re-solve reproduces OPT-1's three rosters exactly (identical
  26 IDs, WAR to 0.05, spend to the dollar — asserted in code)
  before any scenario runs. Every solve publishes status, MIP gap
  and dual bound; all are proven optimal (gap 0).

## Results

| Scenario | Floor | Middle | Cap | Churn |
|---|---|---|---|---|
| Base optimum (OPT-1) | 48.9 | 52.8 | 54.8 | — |
| All prices ×0.8 | 53.2 | 55.5 | 55.9 | 6 / 6 / 4 |
| All prices ×1.2 | 45.0 | 48.5 | 50.4 | 3 / 4 / 4 |
| Floor targets ×1.2 only | 45.6 | — | — | 6 |
| WAR −15% at age 33+, re-scored on base WAR | 48.8 | 52.8 | 54.8 | 2 / 0 / 3 |

- The 15% per-player rule is applied to the prices in force: at
  ×1.2, Rendon ($42.0M scaled) and Skubal ($38.4M) cross the
  $36.795M maximum and are excluded.
- Targeted bid-up: bid the floor list up 20% and the solver drops
  6 of its own targets — its ace included — and still lands 45.6.
- Aging haircut: rosters chosen under a −15% WAR discount on the
  93 pool players aged 33+ re-score within 0.1 WAR of the base
  optima; each carries just 2 players aged 33+.

## The mixed floor (Kleinbard rebuttal test)

- Pre-arb pool from committed data only: `salaries_2026.json` rows
  with Spotrac status exactly "Pre-Arbitration" (553) → 509 usable
  (42 no committed ID, 1 duplicate, 1 no Steamer WAR, 0 in the FA
  class), priced at the file's flat **$1.0M placeholder** — the
  repo's pre-arb placeholder convention (Cycles 41/46), labeled as
  not-a-measured-salary everywhere it appears.
- Floor solve on the 708-player mixed pool, identical quotas:
  **74.8 WAR for $96.2M** — 19 pre-arb slots (53.0 WAR) + 7 FA
  slots, $75.0M of the floor unspent, proven optimal.
- Framing on the record: a club cannot sign another club's pre-arb
  players. This is what the floor buys a club that develops or
  holds pre-arb talent — internal production, not a shopping list.

## Exhibit + docs

- Figure 25 gains a sensitivity strip (scenario table + mixed
  block) under its OPT-1 facts box, all numbers rendered from the
  new artifact; the facts box gains one pointer sentence. No
  OPT-1 number changes.
- CARPE_SCORECARD Cycle 50 addendum, BML_LOG Cycle 50, HANDOFF
  Cycle 50 section. Gate gains an OPT-2 artifact check.
  Spellcheck WHITELIST += 15 pre-arb surnames rendered by the
  strip (verified against the salary file; sanctioned mechanism).

## Verification

- Platform: ingest 25 datasets / 0 failures; curate 17 tables, all
  contracts pass, parquets byte-identical to committed; warehouse
  rebuilt; parity r = 0.889 / 201.
- Gate: `src/verify_data.py` ALL CHECKS PASS (offline and --live,
  standings 30/30), including the new OPT-2 artifact check;
  spellcheck green; DOM/text checks confirm the strip inside
  Figure 25's Explorer block, figures 1–25 intact, 6 chapters,
  15 slides. No browser visual QA (standing rule).
