# Cycle 53 — FIG-QA: Figures 1–25 traced, corrected, gated

Owner-directed 2026-11-02 ("improve QA of figures 1-25").
**Figure count stays 25. No claim changes** — number and label
corrections only; the one item that would change a claim is
held as an owner item below. GitHub Actions ignored per the
owner's 2026-11-02 directive (minutes exhausted until Dec 1) —
the local gate, platform, and parity below carry the
verification.

## What shipped

- **Trace audit (CARPE_SCORECARD Cycle 53 addendum):** a
  25-row table — figure → source artifact(s) → check method.
  Figures traced 25/25; numbering/titles verified identical
  across dashboard build order, Explorer, README, TALKTRACK,
  EXEC_SUMMARY and ONEPAGER. Pre-swap numbers (42.0/45.7/52.3,
  stress 38.3/41.7/47.7) survive only as labeled benchmark or
  dated historical context.
- **Gate (`src/verify_data.py`):** 25 new FIG-QA checks, one
  per figure, each computing its expected value from the
  committed artifact at gate time (pooled r and pair count,
  over-cap count, fee checkpoint, benchmark r and overlap,
  live-IL counts and pull date, …). A wrong number in any
  figure now turns the gate red. **40 → 65 checks offline,
  41 → 66 with --live, ALL PASS.**
- **Fixes (7 edits):**
  - Stat card: pooled contact "r = .83, 422 pairs" → **.84,
    457 pairs** (persistence_ci.json).
  - Story appendix: latest-pair-only contact/walk r values
    (.90/.66) presented as general → pooled .84, walk .66–.77
    across the four pairs.
  - EXEC_SUMMARY: "walk discipline at pooled r = 0.72" (no
    pooled walk value exists in any artifact) → per-pair
    range 0.66–0.77; P7 line corrected from PENDING to the
    owner's recorded MVP-level approval (2026-10-31).
  - WAR precision convention: player-card Steamer WAR and the
    Figure 16 roster table now print WAR at 1 decimal.
  - Bottom line: "roughly half payroll" → traced fraction
    (~ a third of the biggest payrolls; ~95 = winning-cheap
    trio average wins, ~79 = rest-of-league average, both
    computed from kpi_2026.json).
  - Story chapter 5: floor's ±20% range completed (45.0–53.2).

## Owner item (not in this PR)

Figure 9's `projections_2026.json` is in-sample fitted values
(`src/model_p6.py`: 2025+2026 fit applied to 2026 teams) under
the title "Model-projected wins by team", with no in-sample /
diagnostic label — while the demo elsewhere disclaims
team-wins forecasting. Adding the disclosure changes the
figure's claim presentation; it is the owner's call.

## Verification

Platform: ingest 25 datasets / 0 failures; curate 18 tables,
all contracts pass; warehouse rebuilt; parity r = 0.889 / 201.
Gate ALL PASS offline (65) and --live (66, standings 30/30).
Spellcheck green. No browser visual QA (standing rule).
Docs: CARPE_SCORECARD Cycle 53 addendum (trace table),
BML_LOG Cycle 53, HANDOFF.
