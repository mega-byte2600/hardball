# PR — Cycle 46: HS-1, the Hakes–Sauer pricing screen (workpaper only)

Owner-approved MIT-gap programme (2026-11-02 12:57 PT: "filling these
gaps in increments little by little... i want this better and like
these proposed chages!"), increment 1 of 6. HS-1 builds the dataset
and runs the first pricing regressions. It changes NO dashboard
claim, talk-track line, or exec-summary sentence — the verdict
exhibit and any re-headline are HS-2, and only on a supported
verdict.

## What ships
1. **src/bml_cycle46.py** — the full reproducible build (committed
   data only, no network, prints its own summary). Self-contained
   numpy OLS with classical standard errors (no statsmodels in the
   venv; nothing installed).
2. **data/hakes_sauer_dataset.json** — 142 player rows + metadata:
   per-sample basis labels, field provenance, and exclusion
   cascades. Sample S (Spotrac-basis file, 2027 basis per Cycle 41):
   927 rows → 553 pre-arb flat-$1M placeholders and 219 non-Bypassed
   arbitration projections excluded → 155 real contracts → 68
   pitchers, 1 two-way, 26 incomplete excluded → **n = 60**. Sample C
   (Cot's LRP-2027): 237 player-team rows aggregated to player level
   (same-basis obligations summed) → **n = 82** (CBT-AAV sensitivity
   n = 76). The Cycle 41 501/209 counts vs this cycle's 553/219 are
   reconciled in the metadata (subset vs whole-file rule).
3. **data/hakes_sauer_results.json** — per sample: spec A
   (ln salary on Marcel OBP, SLG, K%, BB% + age, Steamer WAR,
   Steamer PA) and spec B (no WAR control), coefficients / SEs /
   p-values / R² / VIFs; $/WAR-by-quartile tables (contact and OBP);
   realized-2026 descriptive sensitivity; sample notes.
4. **Docs** — docs/CARPE_SCORECARD.md Cycle 46 addendum (method,
   samples, headline numbers, limits, what HS-2 adds),
   docs/BML_LOG.md Cycle 46 entry, HANDOFF.md Cycle 46 section.

## Headline result — no verdict, stated plainly
- No skill coefficient is significant in either sample. Sample S
  (n = 60, R² = 0.359): OBP −3.91 (p = .549), SLG +2.73 (p = .226),
  K% −0.005 (p = .798), BB% +0.032 (p = .519). Sample C (n = 82,
  R² = 0.302): OBP +3.31 (p = .661), SLG +2.23 (p = .414), K% +0.026
  (p = .260), BB% −0.018 (p = .751). Age is significant in both.
- The descriptive OBP/SLG coefficient ratio flips sign across bases
  (−1.43 vs +1.48) and no OBP/SLG run-value benchmark exists in-repo,
  so the formal Hakes–Sauer proportionality test is deferred to
  HS-2 — not invented here.
- Descriptive quartile view (labeled a contrast, not a price
  effect): top-quartile contact hitters' median $/WAR is ~half the
  bottom quartile's in both samples (S: $8.03M vs $14.98M; C: $6.19M
  vs $11.64M; $/WAR = salary ÷ Steamer WAR, WAR > 0 only).
- Limits on record: active-contract cross-section (not HS's
  newly-signed-FA design — no signing-date field exists in the
  committed data); skills are 2027 projections with a
  qualified-hitters-only realized-2026 sensitivity (descriptives
  only); Sample S sits exactly at the n≈60 power floor and covers
  24/30 teams; pitchers out of scope; two-way players excluded (the
  build caught the file's "SP  /DH" spacing variant in-build and the
  dataset was re-verified clean).

## Verification
- Ingest 25 datasets, 0 failures; curate contracts pass; warehouse
  rebuilt from 17 tables; parity r = 0.889 / 201 matched.
- Dashboard rebuilt with lake: 23 figures. Gate: ALL CHECKS PASS
  (offline). Spellcheck green.
- No new source probed; salaries stay 24/30 Spotrac-basis + the
  labeled Cot's layer; forced-seller 6/7. No browser visual QA
  (standing rule).
