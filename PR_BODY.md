# Cycle 56 — UNC-2: the uncertainty layer

Final increment of the owner-approved MIT-gap programme
(HS-1 → UNC-2). **Figure count stays 25. No claim changes** — the
headline points are untouched; this adds the measured range
around them. GitHub Actions ignored per the owner's 2026-11-02
directive (minutes exhausted until Dec 1) — the local gate,
platform, and parity below carry the verification.

## What shipped

- **Artifact:** `src/bml_cycle56.py` → `data/uncertainty_scenarios_2027.json`.
  Seeded Monte Carlo (20,000 draws, seed 20261102; re-runs
  reproduce the artifact byte for byte). Each rostered player's
  delivered WAR = Steamer WAR × an availability draw, plus a
  rate-error delta at delivered volume.
- **Error pools — measured, replayed, asserted.** The shipped
  Marcel's out-of-sample residuals, recomputed by importing the
  Cycle 21 / 24 backtest scripts and replaying their variant-C
  cross-fitted construction; the replay is asserted against the
  committed backtest artifacts before any simulation runs.
  Hitters: paired (OBP, SLG) residuals, n=196 (MAE 0.0220 /
  0.0453). Pitchers: ERA residuals, n=59 (MAE 0.711). Steamer has
  no in-repo outcome history, so the pools price the projection
  error this repo has actually measured for this class of system
  (the spine tracks Steamer at OBP r = 0.889).
- **Availability pools:** measured 2025–26 IL factors — hitters
  n=201 (mean 0.912), pitchers n=102 (mean 0.807). Per UNC-1's
  verdict (NOT SUPPORTED as a point correction), availability
  shapes the distribution only; no point is re-centered.
- **Conversion:** Cycle 48 run-value slopes (0.2617 / 0.2778 runs
  per PA) and Steamer's own fitted runs-to-WAR scale (hitters
  0.1132 WAR/run, R² 0.482; pitchers 0.0837, R² 0.215). No
  outside runs-per-win constant.

## The intervals (delivered WAR)

| Scenario | Point | 10th–90th | Median | 20th–80th |
|---|---|---|---|---|
| Floor — $171.2M | 48.9 | 33.0–46.9 | 39.8 | 35.3–44.4 |
| Middle — $208.0M | 52.8 | 36.0–50.7 | 43.2 | 38.6–48.1 |
| Cap — $245.3M | 54.8 | 37.6–52.4 | 44.9 | 40.0–49.8 |

Sanity checks, recorded in the artifact: the median gap
decomposes exactly into the availability level effect
(−6.8 / −7.2 / −7.5) and the measured residual bias
(−2.2 / −2.3 / −2.3; the backtest pools are not zero-mean —
SLG −0.0078, ERA +0.078 actual-minus-projected); the analytic
delivered mean reproduces the simulated mean within 0.05 WAR;
the Cycle 52 uniform-stress totals (44.6 / 48.1 / 50.0) fall
inside all three intervals. The points sit at ~the 95th
percentile of the delivered distribution and are labeled the
full-availability projections wherever the ranges render.

## Consumers

Figure 16 titles (default + all three budget buttons), Story
chapter 5, Boardroom slide 12, and the executive one-pager's
scenario table (its generator now asserts the UNC-2 points tie
to wow_scenarios). README, EXEC_SUMMARY, TALKTRACK reconciled;
CARPE_SCORECARD Cycle 56 addendum; BML_LOG entry; HANDOFF
section.

## Verification

Platform: ingest 25 datasets / 0 failures; curate 19 tables,
all contracts pass; warehouse rebuilt; parity r = 0.889 / 201.
Gate ALL PASS offline (71 checks, was 68 — three new UNC-2
checks pin the artifact's pool ties and gap decomposition, the
rendered intervals on all three dashboard surfaces, and the
one-pager) and --live (72). Spellcheck green. No browser
visual QA (standing rule). No API credits spent.
