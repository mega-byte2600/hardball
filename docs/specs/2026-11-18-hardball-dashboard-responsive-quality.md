# HARDBALL dashboard responsive quality

## Problem and goal

Figure 2's team selector sat beyond the Plotly chart edge while a long dynamic
title carried team facts, method copy, and sources. The title clipped and
collided with the selector. The same copy also called an AA/AAA index rank a
farm-system rank, described the qualified hitter as a top prospect, and called
scenario room against a proposed cap unqualified “cap headroom.”

Goal: make every Story, Boardroom, and Explorer rendering of the team profile
responsive, usable, and semantically accurate, then add reusable Codex workflows
and regression coverage for this problem type.

## Acceptance criteria

1. Use an in-panel native team selector and concise chart title; no Plotly
   control may sit outside the chart paper.
2. Show wins, payroll, proposed-cap scenario room, HARDBALL AA/AAA index rank,
   and qualified hitter/pitcher context in a responsive selected-team summary.
3. Explain the profile's indexing, directional inversions, source basis, and
   limits beside the chart; do not describe the index as causal, universal,
   scouting, or full-farm quality.
4. Keep the selected team synchronized across Story, Boardroom, and Explorer.
5. Use viewport metadata and responsive Plotly rendering. Pass overflow and
   control-layout checks at 320, 375, 390, 768, 1024, 1440, and 2048 CSS px.
6. Verify all 30 team options against source artifacts, including missing
   pipeline cases and the Tampa Bay reference values.
7. Rebuild both generated dashboard files and keep them byte-identical.
8. Score UI/UX, actionability, rigor, accuracy, and requirement alignment from
   measured evidence; all scores must be at least 9 before release.

## Implementation plan

1. Correct the team-explorer data contract and labels in its generator.
2. Replace the Plotly dropdown/long title with responsive HTML controls and a
   synchronized selected-team summary in all three modes.
3. Add static data-contract gates and a headless browser layout/interaction
   sweep; document a bounded Codex maintenance loop and dashboard-quality skill.
4. Rebuild generated artifacts, run data/spell/freshness gates, run the browser
   sweep, inspect phone/desktop screenshots, and independently review the diff.

## Rollback

Revert this branch's source, data, generated HTML, and project-instruction
changes together. Do not merge or deploy without the owner's explicit approval.
