# HARDBALL — Data-Viz Best Practices (borrowed, not reinvented)
*Compiled from Microsoft Learn (Power BI), Tableau, and Few/Tufte.* These are the
rules the dashboard follows. Sources are the same authorities Tableau/Power BI
documentation cite — we don't guess.

## 1. Choose chart by QUESTION, not by data shape
- **Bar / column** = compare categories (best default; humans compare side-by-side bars well)
- **Line** = trend over time
- **Scatter** = relationship between two measures
- **Table/matrix** = lookup/detail — never the main story
- **AVOID**: 3D charts (distort), pie/donut/gauges (weak for comparison; pie only OK for
  part-to-whole with <8 categories — even then a bar is usually better)

## 2. One decision per screen — hierarchy and Z-layout
- The **single most important number first**, largest text on the page (Few: ~5-9
  primary metrics on one view, enough for a glance, not a novel).
- **Z/natural reading**: most important top-left, detail flows right and down.
- Dashboard = overview to monitor state; **drill into detail on demand**, don't
  cram every detail onto the surface.

## 3. Maximize the data-ink ratio (Tufte)
- Kill **chartjunk**: extra gridlines, shading, borders, gradients, 3D marks.
- White space is structure — use padding, not thick grid lines, to separate sections.
- Only data pixels need to exist; every other pixel needs justification.

## 4. Color tells the story, sparingly
- Highlight with color; **too many colors = cacophony**, one color / many shades = blends.
- Use intuitive colors and be **consistent** across every chart (our green/orange/blue/red
  key is the same everywhere — that's why it's a single COLOR KEY box).
- A light border/fill groups related controls (filters, legend).

## 5. Text and numbers, tuned for humans
- **Don't exceed 3-4 numerals**; scale to $M / k (read "3.4M", not "3,400,000").
- **Remove unnecessary data labels** — value is often readable from the bar; keep labels
  only where they add precision, move detail to hover/tooltip.
- **Sort by the measure** to highlight the highest/lowest; title/axis labels + units on
  everything (context).
- Consistent axis scales; don't mix a millions measure with a thousands measure on one scale.

## 6. Keep the reader oriented
- Meaningful titles, labeled axes, units, captions (all ours have "Figure N —" + a plain
  title describing the insight).
- Tooltips carry the detail (our run-diff chart holds all 30 team names there — that's why
  the chart itself is clean).

## Poka-yoke (novice-proofing) — added 2026-10-31
- **Assume the reader knows nothing.** Every stat label carries a plain-English cue right on the
  chart (OBP → "reach base %", HR/PA → "home runs", contact → "hits ball", K% → "strikeouts").
- **A glossary lives at the top** ("BASEBALL PLAIN-ENGLISH KEY") so no acronym goes unexplained:
  PA, OBP, BB%, ISO, run differential, wOBA/wRC+, FIP, K-BB%, WAR (with the honest note that WAR
  is published free by fWAR/bWAR but the formulas differ and no MLB API returns it; we show its real inputs instead).
- **Rule:** a chart at the Winter Meetings must be understood by the non-baseball owner in the room
  within 3 seconds; if a term needs a glossary, both the in-chart cue AND the glossary exist.

## Sources
- Microsoft Learn — "Tips for designing a great Power BI dashboard"
- Tableau — "Visual Best Practices" + "Data Visualization Tips"
- Purdue OWL — "Data Visualization" (Tufte 3 E's: Effective, Ethical, Efficient)
- Stephen Few — *Information Dashboard Design*; Edward Tufte — *The Visual Display of
  Quantitative Information*
