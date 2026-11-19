# Chart readability and research navigation

The shared `dashboard/assets/chart-readability.js` layer separates HTML captions,
chart controls and plotting regions in Story, Boardroom and Explorer. It loads
before the existing Plotly initialization scripts and is included by the generator.
Figure 7 uses five full-width metric panels. Figure 3 displays each season-pair correlation as a dot on a 0 to 1 axis, avoiding an invalid visual sum. Multi-column Cartesian panels stack
at narrow initial viewport widths. Axis labels use automatic margins and title
standoff. Chart wrapper height follows the rendered content.

Research navigation appears immediately below the masthead, beside the three
view selectors, and beside Figure 14. All links lead to `docs/EVIDENCE.html`.

## Checks

- Offline generator completed successfully. Published initialization scripts were
  retained from the existing artifact because a clean build with different local
  scientific dependencies changed some fitted chart values. This presentation fix
  preserves all 48 original initialization scripts, data, frames and controls.
- `python -m pytest tests/test_dashboard_artifact.py -q`: 6 passed.
- `node tests/test_chart_readability.cjs`: 48 chart specifications at 390, 768 and
  1280 px; original trace coordinates, error arrays and custom data preserved;
  captions, KPI panel separation and animation title migration passed.
- `python src/verify_data.py`: all checks passed.
- `python src/spellcheck_gate.py`: passed.
- Browser review: desktop, 390 px and 768 px embedded viewports. All 25 Explorer
  plots stay inside their panel bounds. Phone axis-title versus tick-label
  collision check returned none. Figures 7, 18 and 24 inspected visually.

Responsive browser viewports are not physical-device or Safari certification.
Dense scatterplots still offer zoom and hover for individual observations.

## Repeat before publishing layout changes

Check all three modes and both dashboard aliases. Check a phone width, a tablet
width and desktop. Captions and toolbar controls must occupy separate rows;
axis titles, ticks, subplot headings and legends need their own space. Test the
team dropdown (ATH caption update verified) and animation after any change to layout metadata. Keep all chart
values and uncertainty intervals unchanged unless an analytical change is explicitly
requested. Do not replace these checks with an unsupported numerical design score.

Rollback: revert the presentation commit to restore the prior generator, both
HTML aliases and shared asset. No data migrations or API configuration changes.
