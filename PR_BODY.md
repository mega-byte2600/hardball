# Cycle 69 — claims-pack open item O01 resolved

Bookkeeping only — no new analysis, no claim status changes, no figure changes. The Cycle 68 pack's one open item is closed on the record, because the label it asked for has shipped.

## What changed

- **O01 resolved:** Figure 9's in-sample label shipped in the owner's lane (commit 4219e079, "Figure 9 (owner item #1): relabel in-sample model fit as calibration, overlay actual wins"). The shipped title is "2026 — Model fit (in-sample) vs actual wins, by team" and its caption states "this is calibration, not a forecast". The register now records O01 as RESOLVED with that standing record, instead of carrying it open.
- **`src/bml_cycle69.py`** — verifies the two label strings in `src/dashboard_p6.py`, moves O01 from `open_items` to a new `resolved_items` section, updates the Figure 9 trace headline, and regenerates the pack page. It fails closed if the shipped figure does not carry the label.
- **`data/claims_register.json`** — 16 SUPPORTED / 7 NOT SUPPORTED / 3 RETRACTED (unchanged), 0 open, 1 resolved. **`data/figure_trace_2027.json`** — Figure 9 headline now reads "resolved Cycle 69"; 25/25 figures + 8/8 panels still verified. **`docs/REPRODUCIBILITY.html`** — regenerated with a Resolved items section; the open section now reads "None — no open items."
- **Dashboard panel** — the stale "One item is still open" paragraph is replaced with "No items are open" and the O01 resolution note. Story stays 6 chapters, Boardroom stays 15 slides, figures stay 25.

## Verification

- Gate: **93 checks ALL PASS** (checks updated for the resolved item, none added: register requires O01 resolved + open empty + counts reconcile including resolved; panel requires the new paragraph and forbids the stale one; pack page requires the Resolved section). The gate's evidence-artifact loop now covers `resolved_items` too, so O01's evidence stays checked. Spellcheck green.
- Platform clean: ingest 25 datasets, 0 failures (Savant bands hold; transactions 120,552); curate 19 tables, contracts pass; curated parquets + build report byte-identical to main (no data PR from the platform step); warehouse rebuilt from 19 tables; parity r = 0.889 / 201. Dashboard rebuilt with the lake present: 25 figures, none missing.
- Salary gap unchanged: Spotrac probe single GET 403; FanGraphs RosterResource payroll probe single GET 403 (Cloudflare, same as Cycle 32) — both stopped for the run per the rate-limit rule, no routing around either block. Salaries stay 24/30, forced-seller 6/7.

## Release

Release v1.1.7 follows per the Cycle 60 pattern (tag + GitHub release, no asset uploads; the merged tree already carries the rebuilt dashboard).
