---
name: hardball-dashboard-quality
description: Use when changing, building, reviewing, or scoring any HARDBALL dashboard, Plotly figure, generated HTML, or responsive layout. Prevents clipping and overlap while preserving data meaning, source context, accessibility, and behavior across Story, Boardroom, and Explorer.
metadata:
  short-description: Build and verify HARDBALL dashboards
---

# HARDBALL dashboard quality loop

## Ground truth

- Read `AGENTS.md`, `docs/EDITORIAL_VISUAL_DIRECTION.md`,
  `docs/VIZ_BEST_PRACTICES.md`, and the relevant method/data artifacts.
- Edit the Python/data source, then regenerate the dashboard. Never patch only
  the generated HTML.
- Treat Story, Boardroom, and Explorer as three presentations of the same
  evidence. Keep their meaning, selected state, sources, and caveats consistent.
- When the request covers all dashboards or figures, inventory every user-facing
  dashboard route, mode, and registered figure first. A passing check on the
  reported figure is not evidence that the full dashboard is healthy.
- Keep this repository's public-data and no-fabrication rules. Missing values
  must render as an explicit unavailable state.
- Keep external literature distinct from HARDBALL's own validation. Label a
  paper as external context until the project reproduces it; do not insert a
  non-medical study into the injury-surveillance lanes or imply it feeds a
  projection.

## Before editing

Write short, observable acceptance criteria for the affected figure and mode.
For multi-file work, record them in `docs/specs/`. Capture the current behavior
and test at least one representative narrow and wide viewport before changing
the layout.

## Layout rules learned from the HARDBALL team-profile defect

- Keep chart titles to the chart's subject. Do not put a paragraph, source list,
  dynamic team facts, or instructions in a Plotly title.
- Keep filters and selectors in a separate, labeled HTML control row. Use a
  native keyboard-accessible control when the interaction is a single choice.
- Place definitions, source/basis, and limitations in wrapping HTML captions
  outside SVG text. Show decision-relevant selected-item facts in a nearby
  responsive summary; keep the summary synchronized across modes.
- Never position a control outside the chart paper or use fixed pixel offsets
  that only work at one chart width. Enable Plotly responsive resizing and set
  the page viewport meta tag.
- Distinguish similarly named data concepts precisely. A project-specific
  index is not a scouting ranking; a proposed cap is a scenario, not a league
  rule; descriptive similarity is not causality.

## Required verification

1. Rebuild with the documented offline command and verify both published HTML
   files match.
2. Run `src/verify_data.py` and the relevant data/method checks. Pin at least
   one known reference case and verify missing-data states.
3. Run `src/verify_dashboard_layout.py` at 320, 375, 390, 768, 1024, 1440,
   and 2048 CSS pixels. Check each mode for page overflow, panel overflow,
   chart/control overlap, missing plots, and browser errors.
4. Exercise every option in a selector and verify its visible series, title,
   summary, and synchronized controls. Include null/unknown values.
5. Inspect screenshots of each mode at phone and desktop widths. Automated
   geometry checks do not replace visual review of legends, labels, color,
   hierarchy, and chart readability.
6. Review accuracy, actionability, UI/UX, methodological rigor, and requirement
   alignment separately. Score each from 1–10 using observed evidence; a
   release is ready only when every score is at least 9. State any dimension
   that cannot be measured instead of assigning an unsupported score.

## Regression checks for this defect class

Keep static checks for title length, out-of-bounds Plotly menu coordinates,
responsive configuration, viewport metadata, source terminology, and data
contracts. Keep browser checks for actual overflow, control geometry, selector
behavior, all modes, and the generated artifact. When a check fails, confirm it
fails for the product defect and not because its fixture or assumption is wrong.

## Report

Give the before/after measurement, viewport and mode coverage, data/method
checks, test commands and result, the five evidence-based scores, and remaining
limitations. Do not say “fixed,” “9+,” “verified,” or “live” unless the
corresponding checks actually passed; production requires a fresh measurement
after the release deploy.
