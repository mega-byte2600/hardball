# HARDBALL workflows for Codex

This document adapts the Claude Code workflow kit on the `claude/workflow-kit`
branch (`CLAUDE.md`, `.claude/loop.md`, and its kickoff/build/review/ship and
web-performance skills) to this repository's Codex workflow. The branch is a
reference source, not an instruction to merge or copy its Claude-specific
configuration. `AGENTS.md` and the project skills under `.agents/skills/` are
the Codex entry points.

## Kickoff: define the result before editing

For work spanning multiple files or changing a user-visible decision:

1. Read `AGENTS.md`, the applicable project skill, current source/data, and
   relevant project methodology.
2. Write observable acceptance criteria in `docs/specs/` before implementation.
3. Identify a known reference case, null state, and regression path.
4. Search for existing helpers and reuse them. Avoid parallel implementations.

## Build: small red/green/refactor/verify steps

1. Add or update the narrowest deterministic check that reproduces the defect.
2. Make the smallest source-of-truth change that makes that check pass.
3. Refactor only after the behavior is pinned.
4. Regenerate committed dashboard artifacts from `src/` and `data/`.
5. Run the data, copy, freshness, and relevant layout gates. Record an
   environmental limitation as blocked; do not reinterpret it as a pass.

Prefer the project's documented offline build. Never add Actions usage, paid
API calls, scheduled polling, or new credentials as a side effect of a fix.

## Review: verify or disprove each finding

Review the complete diff against `main`, including generated outputs. For each
finding, trace the displayed claim to its source artifact and method, reproduce
it with the narrowest check, and distinguish confirmed defects from assumptions.
Check null/unknown cases, keyboard behavior, responsive geometry, accessible
labels, units, source dates, uncertainty, and mode-to-mode consistency. Resolve
every critical/high finding before calling the change ready.

## Web performance and visual QA

Capture before/after at a narrow phone, tablet, and desktop width whenever the
browser environment permits. Inspect all three HARDBALL modes and every affected
figure. Measure document/panel overflow, clipping, selector/chart intersections,
plot visibility, and browser errors; then visually inspect hierarchy, legends,
labels, contrast, and actionability. Plotly controls belong in normal document
flow, outside the SVG. Dynamic copy must wrap and must not expand chart titles.

Run `python src/verify_dashboard_layout.py` for the automated viewport and
interaction sweep. Install Playwright's pinned browser once with
`python -m playwright install chromium`; avoid substituting a system Chromium
wrapper unless deliberately testing it via `CHROMIUM_PATH`. If Chromium cannot launch or inspect the built artifact in
the available environment, report that specific blocker and leave the visual
gate pending. Do not claim a 9+ quality score without evidence for each scored
dimension.

## Ship: explicit release boundary

Before offering a release candidate, run all relevant gates, inspect the staged
diff, confirm generated files are fresh and byte-identical where required, and
summarize evidence, blockers, and rollback surface. A pull request is reviewable
work. Merging to `main` publishes GitHub Pages, so never merge or deploy without
the owner's explicit approval. Keep secrets, credentials, and user data out of
logs, artifacts, commits, and prompts.

## Bounded maintenance loop

When the user requests a repository health pass, continue unfinished work first,
then inspect review/CI findings, run local gates, check committed data freshness,
and only then take one small hygiene item. Stop at the first substantive defect
and fix it before continuing. Do not turn maintenance into unrequested feature
work or recurring automation.
