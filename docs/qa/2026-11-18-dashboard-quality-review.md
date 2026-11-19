# Dashboard quality review — updated 2026-11-19

## Scope

HARDBALL's generated dashboard has 25 registered figures and three user-facing
modes: Story, Boardroom, and Explorer. Figure 2, the team profile, was the
reported clipping and overlap defect. This review was rerun after reconciling
the fix with current upstream work.

## Evidence collected

- `src/verify_data.py` passes every check, including API-2 and all 25
  figure-specific checks.
- Figure 2's 30-team data contract passes, including source-backed Tampa Bay
  values. Its selector, summary facts, methodology/source caption, concise
  title, viewport metadata, and responsive Plotly configuration pass static
  checks in all three modes.
- The dashboard rebuilt from source in offline mode. `dashboard/index.html`
  and `dashboard/hardball_demo.html` are byte-identical (641,562 bytes).
- Evidence Says Now rebuilt with a cross-link to the separate statistics
  methods review. Its injury-literature scope and “context, not a model input”
  disclosure remain intact.
- `src/spellcheck_gate.py`, Python compilation of changed scripts, and
  `git diff --check` pass.
- The first development dependency install failed because
  `requirements-dev.txt` pinned `pyspellchecker==0.8.4` while
  `requirements.txt` pins `0.9.1`. Removing the duplicate conflicting pin fixed
  the install; `requirements-dev.txt` installs successfully now.
- `src/check_freshness.py` remains blocked by the missing ignored snapshot
  `data/raw/statyx/standings_2026-11-17.json`, referenced by
  `data/il_current_live.json`. Do not fabricate it or bypass provenance.
- Browser coverage is **0/21 viewport-mode combinations and 0/30 team
  selections**. Playwright's pinned Chromium download repeatedly returned a
  corrupt zero-byte archive. `/usr/bin/chromium` aborts because the environment
  denies its process-singleton socket. Visual and interactive checks remain
  pending.

## Scorecard

The requested 1–10 scores remain **unassigned** until browser geometry,
interaction, and visual checks can be observed. Assigning 9+ without those
measurements would overstate the evidence. The source, data, and static checks
support Figure 2's correction, but do not demonstrate the all-mode visual
release bar.

| Dimension | Status | Evidence still needed |
|---|---|---|
| UI/UX | Pending | Phone/tablet/desktop screenshots of all modes; inspect hierarchy, legibility, clipping, focus, and chart readability |
| Actionability | Pending | Verify team selection, visible data, synchronized facts, and clear units/context in a real browser |
| Rigor | Partial | Restore the missing Statyx provenance snapshot and complete the browser sweep |
| Accuracy | Partial | All 25 figure-specific data checks pass; inspect rendered behavior and labels in a browser |
| Requirement alignment | Partial | Acceptance criteria are encoded; browser behavior and the evidence-based 9+ bar remain unverified |

## Next verification

1. Restore the exact Statyx snapshot referenced by `data/il_current_live.json`
   from its provenance source, or revise the artifact through its owning data
   workflow. Do not fabricate or bypass snapshot validation.
2. Once Chromium is available, run `python src/check_freshness.py` and
   `python src/verify_dashboard_layout.py`.
3. Review screenshots at phone, tablet, and desktop widths for all three
   modes. Exercise all 30 teams, including unavailable pipeline cases. Score
   each dimension only from observed evidence; remediate every dimension below
   9 and rerun the full sweep.
