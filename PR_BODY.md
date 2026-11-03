# Cycle 57 — Evidence surveillance: PubMed behind Figure 14

Owner-directed (2026-11-02): the APE PFAC toolkit's "What the evidence
says now" PubMed-surveillance pattern, applied to the injury
literature behind HARDBALL's availability edge. Additive only — no
claim, figure, or model changes; figure count stays 25.

## What ships

- **`src/pull_evidence_surveillance.py`** — standalone serving pull
  (not a platform ingest source). Four fixed lanes on PubMed via
  NCBI E-utilities (keyless, `tool=hardball`, sequential, fail
  closed on any non-200, 6-day staleness guard like the feed
  refresh). Queries and counts as run 2026-11-02, recorded verbatim
  in the artifact: UCL return to play **157** · baseball injury
  prevention & workload **426** · cellular recovery / muscle
  regeneration **404** · tendon healing & biologics **119**
  (SR/MA filter inside that query). Selection is deterministic —
  systematic reviews / meta-analyses first, then most recent, 3
  cards per lane (a re-pull reproduced the identical 12 PMIDs).
- **`data/evidence_surveillance.json`** — per card: PMID, authors,
  AMA citation, DOI, PubMed URL, publication types, and the full
  abstract. **`data/evidence_plain_lines.json`** — the overlay of
  plain-language headlines/Findings, merged by the pull; the page
  generator fails closed if a selected card ever lacks one.
- **`docs/EVIDENCE.html`** via **`src/make_evidence_page.py`**
  (one-pager pattern, committed artifact only). Professional plain
  language for front-office readers: lane intros (UCL/PRP glossed
  once), a per-card **Finding** drawn only from the paper's stored
  abstract (past tense; author conclusions attributed), AMA
  citation as the credibility layer. The intro names the anchor:
  Figure 14 measures the playtime injuries take away; this page is
  the literature under that measurement. Labeled on the page:
  **"Literature surveillance — context, not a model input."**
- **Dashboard**: one asterisked footnote line directly under the
  Figure 14 panel in Explorer — "* What the evidence says now —
  the published research on injury recovery and prevention." with
  the four lane counts inside it and the link to
  `docs/EVIDENCE.html`. No block, no new panel. Footer gains
  PubMed / NCBI E-utilities (LIVE · keyless, pull date from the
  artifact).

## Flagged, not fixed (claim hygiene)

- The biologics evidence is weak where it is most marketed: two
  RCT meta-analyses found platelet concentrates/PRP did not
  improve patient-reported outcomes after ACL reconstruction
  (PMIDs 41313368, 40744844); a 419-study scoping review calls
  PRP/stem-cell evidence inconsistent (PMID 42963566). Recorded in
  the scorecard; no desk claim touched (the model prices measured
  IL time only).
- The owner's data-driven intro line (costliest body part by IL
  days) was **checked and not shipped**: `fact_il_stints` has no
  body-part field, and its free-text injury strings leave ≈25% of
  IL days unclassifiable — no clean split, not forced. Elbow-named
  stints lead indicatively (≈68.8k vs ≈47.6k shoulder days), so
  the UCL lane already leads the page. Detail in the scorecard.

## Verification

- Platform: ingest 25 datasets / 0 failures; curate 19 tables, all
  contracts pass; warehouse rebuilt; parity **r = 0.889 / 201**.
- Gate: **75 checks offline, ALL PASS** (71 + 4 new evidence
  checks: artifact integrity; every card's count/PMID/DOI/Finding
  rendered on the page; the Figure 14 footnote text/counts/link
  pinned to the artifact and positioned under the panel; footer
  names PubMed). Spellcheck green. Dashboard rebuilds at 25
  figures. No browser visual QA (standing rule). GitHub Actions
  ignored per the owner's blackout directive (until Dec 1).

## Docs

`docs/DATA_PLATFORM.md` (literature-surveillance section),
`docs/CARPE_SCORECARD.md` (Cycle 57 addendum: probes, final
queries, contrary-evidence flags, body-part check),
`docs/BML_LOG.md`, `HANDOFF.md` (Next: the evidence refresh joins
the same pending cron-wiring decision as the feed refresh).
