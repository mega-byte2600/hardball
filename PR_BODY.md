# Cycle 61 — PRICE-1: predicted-price model, inventory first (workpaper)

Slate item 1 of 6 (owner-approved elite/asset slate,
2026-11-02). The task: build a model that predicts 2027 FA
signed AAV and replaces the optimizer's prior-AAV anchors —
**only if it earns the switch in backtest**. The bar was
pre-committed before any fit: train classes 2022 + 2023,
test held-out class 2024; switch only if held-out MAE is
>= 10% below the anchor baseline's on the same players.

## Verdict: NOT RUN — TRAINING DATA ABSENT. Anchors stay.

Step 0 (inventory before modeling, fail closed) found no
usable training set of actual signed FA contracts in the
repo:

- The signing census exists but carries no terms: StatsAPI
  transactions (Cycle 54) give identity + date for 1,645 /
  1,849 / 1,659 signings (classes 2022–2024) — no dollars,
  no years.
- The only signed terms anywhere — Cot's contract strings,
  153 parseable — are **survivors on 2027 payrolls**: class
  2022 keeps 24 deals, ALL >= 3 years; class 2023 keeps 18,
  all >= 3 years; class 2024 keeps 35, none of them 1-year.
  Every expired 1–2 year deal is invisible, and spans mix
  extensions with FA signings. A backtest on survivors
  certifies long deals only, then prices a 251-man class
  full of short-deal candidates — a selection mechanism,
  not a sample. Not run.
- Spotrac's file is the same 2027 snapshot (it is the
  incumbent anchor source); HS-1 is active contracts, not
  signings (its own recorded design limit); the 2027 class
  file's `spotrac_market_aav` is another model's
  unbacktested output. No artifact repo-wide carries
  signing-terms fields. No contracts were invented and no
  blocked source was scraped (Spotrac / FanGraphs stand
  403).

## This PR

- `src/bml_cycle61.py` — the reproducible inventory audit.
- `data/price_model_workpaper_2027.json` — inventory,
  survivorship table, the exact missing source with
  readiness criteria (>= 90% of each class's census matched
  to terms; 1-year deals present; extensions separable),
  and the **pre-registered model design**: target ln(signed
  AAV); features pre-signing projected WAR, age, position
  group, prior AAV as a feature; ridge first; baselines =
  anchor + class-median $/WAR; the 10% bar; switch
  mechanics (MILP re-run, sensitivity re-run, UNC-2
  intervals stay on the anchor-priced run until re-derived,
  dashboard switch with its own release cut).
- `src/verify_data.py` — 3 new PRICE-1 gate checks:
  workpaper on record with the bar; survivorship table
  recomputes from the Cot's strings; incumbent anchor
  basis untouched.
- `docs/CARPE_SCORECARD.md` — Cycle 61 addendum.
- `HANDOFF.md` — Cycle 61 section; December checklist §4
  gains the price-model gap + the Sportradar verification
  job (its contracts coverage must reach expired deals,
  not just current rosters, to unblock PRICE-1).
- `docs/BML_LOG.md` — Cycle 61 entry.
- `PR_BODY.md` — this file.

## Verification

Gate: **78 checks, ALL PASS** (offline and --live);
spellcheck green; warehouse rebuilt from 19 curated
tables; benchmark parity **r = 0.889 / 201**. Optimizer
artifacts, scenario numbers, and headlines are byte-
identical to Cycle 60 — the anchors stay, labeled as
before. **No dashboard change, so no release cut** (a
release is part of a user-visible change; there is none).
