# Cycle 68 — reproducibility & claims pack (slate item 5)

Owner-approved slate, in order. The audit trail a league office can check: every material claim the demo makes, its artifact, and its status — plus every figure and panel traced to its artifact.

## What shipped

- **`src/bml_cycle68.py` → `data/claims_register.json`** — 16 SUPPORTED, 7 NOT SUPPORTED, 3 RETRACTED, 1 open item. A claim is SUPPORTED only if a committed artifact carries the numbers; a claim that failed its own test is NOT SUPPORTED, not softened.
- **`data/figure_trace_2027.json`** — 25/25 figures + 8/8 panels verified (FIG-QA method): headline values recomputed from the artifacts and matched against the built HTML.
- **`docs/REPRODUCIBILITY.html`** — the pack page, generated from the two JSON files, never hand-edited numbers. Per figure: artifact, headline value, build command, and lineage (ingest → curated Parquet → warehouse → serving).
- **Dashboard panel** — "Claims & reproducibility" closes Explorer (appendix, not a figure — count stays 25; Story stays 6 chapters, Boardroom stays 15 slides). It renders the counts, the three retracted claims in full, and the pack link. It fails closed: without the pack artifacts it renders nothing.

## Retracted — stated plainly, not deleted

- **R01:** the team-wins R-squared 0.80 claim (Cycles 18–19 — a favorable 2-year window; full-panel refit R-squared 0.534, lagged out-of-sample MAE 14.05 vs naive 9.76).
- **R02:** availability-capped point forecasts (UNC-1, Cycle 54 — pooled MAE 46.2 → 61.1 capped; the cap is a downside adjustment only).
- **R03:** the OBP persistence figure as first published (Cycle 39 recomputation; Cycle 44 shipped the corrected stack, PR #21 itself never merged).

## Not supported, stated plainly

Prior-AAV anchors as predicted prices (Cycle 61, training data absent); the Steamer+Marcel blend (Cycle 62, unscorable); Steamer out-of-sample accuracy (not scoreable); Savant trait adjustments (worse out-of-sample); BRef salary corroboration (71.1% < 80% bar); player-level salary completeness for all 30 teams (24/30); the proposed cap system as certain law (it is a proposal; CBA expires Dec 1).

## Open — not decided here

**O01:** Figure 9's "Model-projected wins" title presents in-sample fitted values without an in-sample/diagnostic label — still the owner's call. The trace verifies Figure 9's artifact and panel agree; it does not endorse the title.

## Verification

- Gate: **93 checks ALL PASS** (89 + 4 new Cycle 68 checks: register completeness + evidence existence + counts reconcile; trace coverage 25 + 8, all verified; panel renders in Explorer and not in Story; pack page carries the counts and retracted claims). Spellcheck green.
- Platform clean: curate rebuilt 17 tables, contracts pass, 2 skipped on absent raw with committed parquets standing; all 19 parquets byte-identical to main; warehouse rebuilt from 19 tables; parity r = 0.889 / 201. Dashboard rebuilt with the lake present: 25 figures, none missing. kpi.py md5-verified pristine.
- Release v1.1.6 follows per the Cycle 60 pattern (release commit atop main carrying only the rebuilt dashboard file; published file read back from the release tarball and probed).
