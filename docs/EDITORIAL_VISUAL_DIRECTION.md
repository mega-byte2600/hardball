# Hardball editorial and visual direction

## Product position

Hardball should read as MLB decision intelligence, not a generic Moneyball demo. The product connects player performance, health, availability, payroll, free agency, uncertainty, and evidence for a baseball decision maker.

The public story should answer three questions in order:

1. What decision can this help me make?
2. What evidence supports the decision?
3. What remains uncertain?

## Editorial rules

- Lead with the decision, not the implementation history.
- Use plain baseball language before technical detail.
- Present winning-efficient clubs as case studies, not universal prescriptions.
- Keep claims close to the figure or artifact that supports them.
- Separate confirmed data, reported information, and experimental signals.
- State uncertainty as part of the product, not as an apology.
- Keep internal cycle names, release labels, agent language, and build history out of public surfaces.
- Use one clear action per section: explore the evidence, compare a team, or contact the builder.

## Visual direction

- Use the existing MLB Navy, Rays Navy, Columbia Blue, MLB Red, and gold tokens consistently.
- Treat gold as a signal for action, date, or emphasis rather than decoration.
- Keep the crest, section labels, figure titles, legends, and source notes on one visual hierarchy.
- Use generous whitespace around dense charts.
- Keep the primary contact action visually distinct from secondary profile links.
- Preserve the current Story, Boardroom, and Explorer modes. They are different reading speeds for the same evidence, not separate products.
- Keep mobile layouts single column where content becomes compressed.

## Information flow

### Story

The shortest executive path. Start with the decision thesis, then the three headline findings, then the implications for roster construction, health, and cost.

### Boardroom

A presentation sequence for a meeting. Each slide should answer one question and carry its source or limitation with it.

### Explorer

The audit layer. Organize figures by decision question and keep claims, methods, source notes, and uncertainty available without interrupting the main story.

## Contact pattern

The About / Contact module uses one short value proposition, one prominent Dartmouth email action, and four secondary links:

- LinkedIn
- GitHub
- PFAC Toolkit
- Dartmouth MPH

This keeps contact visible without turning the dashboard into a biography page.

## Release gates

Before a public release:

- Rebuild the generated dashboard from source.
- Confirm all 25 figures are present.
- Confirm legends, color key, sources, and mobile layout remain intact.
- Confirm no internal cycle, P7, CarpeData, BML, private repository, or agent language appears in rendered HTML.
- Run connector and claims checks.
- Verify the About / Contact links and mailto action.
- Record the release SHA and evidence in the build log.

## Research basis

The structure follows common portfolio guidance: concise positioning, visible contact information, a small set of relevant links, clear information hierarchy, cohesive visual language, and mobile readability.

Reference examples:

- University of Florida, Portfolio Foundations: https://careerhub.ufl.edu/resources/portfolio-foundations-building-your-portfolio/
- Waida Studio, Personal Portfolio Website: https://www.waida.studio/learn/personal-portfolio-website
- Canva, Portfolio Websites: https://www.canva.com/website-builder/portfolio-websites/
- Format, Creative Portfolio Tips: https://www.format.com/magazine/resources/design/creative-portfolio-stand-out
