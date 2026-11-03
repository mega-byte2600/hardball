# Cycle 60 — Publish the current dashboard (release v1.1.0)

Owner-directed (2026-11-02): the owner could not see the health
API feed on the site, and he was right. `dashboard/hardball_demo.html`
is gitignored on main ("Generated dashboard artifacts… neither is
source") and only enters the repo at release cuts; the newest
release tag was **v1.0.1 (2026-11-01)**, whose dashboard predates
Cycles 51–59 and contains none of the live-IL panel, the feed
movement line, the optimizer headlines, the UNC-2 ranges, or the
Figure 14 evidence footnote.

## This PR (docs only)

- HANDOFF.md: Cycle 60 release note; December readiness checklist
  gains the interim v1.1.0 record (the freeze tag is still owed).
- docs/BML_LOG.md: Cycle 60 entry.
- PR_BODY.md: this file.

## The release (cut from the merge of this PR)

A release commit atop the merged main adds the one generated file
`dashboard/hardball_demo.html` (5,539,972 bytes, built offline from
committed snapshots); tag **v1.1.0** points at that commit — the
same pattern as the v1.0.1 tree. Release assets are not uploaded
(uploads return 401); the HTML lives in the tag tree.

## Verification

Built file probed by content, in the scratch build and again in
the published tag tree (identical counts): 25 figures;
"Current IL picture — LIVE feeds (Statyx + FastballAPI, pulled
2026-11-02)"; the Cycle 55 movement line; headlines 48.9 / 52.8 /
54.8 WAR with ±20% price ranges (45.0–53.2 / 48.5–55.5 /
50.4–55.9); UNC-2 delivered-WAR intervals (33.0–46.9 / 36.0–50.7
/ 37.6–52.4); the Figure 14 footnote in its exact wording with
href `../docs/EVIDENCE.html`, which resolves from `dashboard/` to
`docs/EVIDENCE.html` (no source fix needed — the Cycle 57 gate
check already pins that href); sources footer naming Statyx,
FastballAPI, PubMed.

Gate on the publish tree: **75 checks offline, ALL PASS**;
spellcheck green; warehouse parity **r = 0.889 / 201**. No claims,
figures, or data changed. Interim publish — the December freeze
tag remains owed.
