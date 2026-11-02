# Cycle 48 — HS-2: the Hakes–Sauer verdict exhibit (Figure 24)

Owner-approved MIT-gap programme, increment 2 of 6. HS-1 (Cycle 46)
deferred the formal proportionality test for one reason: no OBP/SLG
run-value benchmark existed in the repo. HS-2 derives one from
committed data under pre-registered fail-closed criteria, runs the
test, and publishes the verdict as **Figure 24** (Explorer-only,
Check the Model). **24 figures total**; figures 1–23 keep their
numbers; Story (6 chapters) and Boardroom (15 slides) unchanged.

## The benchmark attempt — survived, labeled aggregate

- `src/bml_cycle48.py` → `data/hakes_sauer_verdict.json`. Criteria
  fixed before estimation: FE coefficients > 0, p < 0.10, VIF < 10,
  ratio CI finite and excluding 0 — else publish the failure and run
  no test.
- Runs per PA on OBP + SLG, `fact_team_season`, **480 unique
  team-seasons 2011–2026** (29 duplicated 2026 rows in the committed
  table differ only in payroll-cell formatting; batting fields
  identical — deduped in the analysis, curate.py untouched).
- Season fixed effects: OBP **+0.262** (p ≈ 1.8e-26), SLG **+0.278**
  (p ≈ 1.9e-85), within R² = 0.865, VIF 2.45. **rho = 0.94** (95% CI
  0.72–1.17); pooled sensitivity 0.66 (0.44–0.88); per-season median
  1.00. Ecological limit labeled on the record: team aggregates
  split OBP/SLG's joint variation (corr 0.77), so the aggregate
  ratio sits below event-level linear-weights values.

## The formal test — inconclusive by power

- HS-1 spec A refit from the committed dataset reproduces HS-1's
  published coefficients/SEs **exactly** (asserted in code; the
  covariance matrix is only trusted because the refit matches).
- Wald test of beta_OBP − rho·beta_SLG = 0: Sample S (Spotrac basis,
  n = 60) contrast −6.49, SE 8.05, **p = 0.42**; Sample C (Cot's
  LRP-2027, n = 82) contrast +1.21, SE 9.43, **p = 0.90**. Pooled
  benchmark: p = 0.45 / 0.84.
- The power statement is the finding: the pricing ratios neither
  sample can reject at 5% span the entire scanned range **[−20, +20]**
  — correct pricing and large mispricing both survive.

## Verdict (rendered verbatim in Figure 24's verdict box)

**INCONCLUSIVE on mispricing.** The descriptive $/WAR contrast is
consistent across both bases (top-quartile contact ≈ 0.54× / 0.53×
the bottom quartile's median $/WAR — a contrast, not a price
effect). The defensible claim is **persistent + cap-efficient +
low-variance**, not proven undervaluation. Design limit: active-
contract cross-section, not newly-signed free agents.

## Claim hygiene — sentences changed

Grep of the dashboard source, EXEC_SUMMARY, TALKTRACK, README, and
ONEPAGER for unqualified "undervalued" / "mispriced" / "underpriced"
assertions about contact/OBP found **none to replace** — the
surfaces already carry the measured language. Changes are additive
verdict citations, listed in full:

- `docs/EXEC_SUMMARY.md` — "What we deliberately do NOT claim" gains:
  "**We do not claim the market misprices contact/OBP.** We ran our
  own Hakes–Sauer pricing test (Cycles 46/48, Figure 24): …
  inconclusive at current samples (n = 60 / 82) … The claim is
  persistence + cap-efficiency." (plus the 23→24 figure count)
- `docs/TALKTRACK.md` — honesty section gains: "And we do **not**
  claim the market misprices these skills — we ran the pricing test
  on ourselves (Fig 24): formally inconclusive at current samples,
  so the claim stays persistence and cap-efficiency, not proven
  undervaluation." Back-pocket gains the test's numbers; modes and
  counts updated to 24.
- `src/dashboard_p6.py` — sources box gains: "**Pricing claim,
  tested (Cycles 46/48):** our own Hakes–Sauer test … is formally
  inconclusive at current samples — Figure 24 carries the
  coefficients, the test, and the verdict; this page claims
  persistence and cap-efficiency, not proven undervaluation."

No thesis sentence was rewritten; winning-cheap via contact + OBP +
availability stands as strategy.

## Also in this PR

- Counts 23 → 24 in dashboard source (docstring, figure index,
  Explorer button/group), `src/verify_data.py` (24-chart check, talk
  track refs ≤ 24, **new** Figure 24 + HS-2 artifact checks),
  README, EXEC_SUMMARY, and `src/make_onepager.py` (ONEPAGER
  regenerated: 24 figures, 17 curated tables, parity 0.889/201).
- Spellcheck WHITELIST += sauer, misprices, mispricing, underprices,
  workpaper (verified spellings).
- Docs: CARPE_SCORECARD Cycle 48 addendum, BML_LOG Cycle 48,
  HANDOFF Cycle 48.

## Verification

- Platform: ingest 25 datasets / 0 failures, curate 17 tables
  (parquets byte-identical to committed), warehouse rebuilt.
- Parity: **r = 0.889 / n = 201** (unchanged).
- Gate: **ALL CHECKS PASS** (offline) — Figure 24 present in
  Explorer with the verdict box, footer sources intact, 6 chapters /
  15 slides / 8 cards unchanged.
- Spellcheck: green.
