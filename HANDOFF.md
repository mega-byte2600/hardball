# HANDOFF — toby/finale (PR #4, stacked on PR #3)

Finale pass, 2026-10-31: the last four audit gaps closed (G6, G7, G8,
G11) plus a presentation pass on the dashboard. **Stacked on
`toby/solutions` (PR #3)** — merge #1 → #2 → #3 → this.

## Audit closeout

- **G6 ROOT-CAUSED**: the 2019 fold (MAE 51.9) in Cycle 19's grouped CV
  predicts the 60-game 2020 season with a 162-game-trained model — a
  units mismatch, not model error. `bml_cycle19_lagged.py` now excludes
  target-season-2020 folds from the headline mean and reports them
  separately: grouped CV MAE 13.01 → **10.23**. Verdict unchanged.
- **G7**: BML log backfilled for Cycles 14/16/17 from scripts +
  committed outputs; Cycle 17's missing output was restored by re-run
  (linear wins, MAE 3.84; the unscaled MLP blowup is in the record).
  Cycle 3 provenance note added (its script was never committed;
  Savant ingestion now lives in `carpe.py`).
- **G8**: `formula_prod.json` annotated in-file (status: DIAGNOSTIC
  ONLY; cv_scope: two-season same-year cross-fit) and `bml_cycle14.py`
  writes the annotation on regeneration, so the 4.3/0.764 can no
  longer circulate as forecast accuracy.
- **G11**: W-L "anomalies" verified against MLB Stats API final 2026
  standings — all 30 records match; NYY 93-68 and BAL 79-82 (161 games)
  are REAL (unplayed game), annotated in `payroll.py` with the pull
  provenance; dashboard footer scopes the ESPN check to the 2025
  validation set; `bml_cycle6_pitching.py` lake path is repo-based.

## Presentation pass (dashboard)

Story flow with seven navy section bands (I The Proof → VII The
Future), a five-card stat strip (cap, 509 team-seasons, 303 players
projected — counted live from the artifacts, Steamer r, 100% real
data), panels in white cards on warm paper, and a branded Plotly
template (navy/red/gold). Presentation only — no data or model
changes. Clean-clone offline build verified: 14 panels, 7 sections,
5 cards. (Browser-based visual QA was attempted three ways and the
browser environment couldn't reach the file; structural verification
stands, and the v0.9.1-demo release carries the built HTML for the
owner's own eyes — that's the real P7 gate anyway.)

## State after this PR

Audit G1–G12 all closed. Remaining: owner merge of PRs #1–#4, P7 UAT,
and the self-healing Spotrac rerun (6 salary pages) whenever.
