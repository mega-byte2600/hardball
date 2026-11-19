# HARDBALL statistics research gap analysis

**Prepared:** 2026-11-19

**Purpose:** Benchmark supplied baseball-statistics references against HARDBALL, identify point of parity and point of difference, and recommend how evidence should influence the product.

## Executive finding

The three supplied citations do not resolve cleanly to three papers with those exact titles and author lists. One is a title mismatch, one conflates a peer-reviewed cWAR paper with a separate student machine-learning poster, and one could not be verified. Do not publish the supplied citations as verified references or attribute the poster's results to the peer-reviewed paper.

The shared point of parity is that baseball decisions improve when raw performance is put in an explicit context and evaluated against a relevant reference. HARDBALL's defensible point of difference is its decision layer: it brings performance, availability, payroll, prospect pipeline, and roster constraints into one user-facing comparison. That is a product-scope distinction, not proof of superior model accuracy. None of the identified studies validates HARDBALL's MLB projections, salary assumptions, or roster recommendations.

## Citation resolution and benchmark

| Supplied citation | Source resolution | Question and method | Evidence and limits | HARDBALL implication |
|---|---|---|---|---|
| Lee Freeman, “Baseball Manager Performance Relative to Playing Position” | Exact title not verified. The primary AIS proceedings record for Freeman is **“The Impact of Analytics in Professional Baseball: How Long Before Performance Improves”** (MWAIS 2019). Do not treat it as a manager-by-position paper. | Uses reported 2014 analytics adoption across 30 MLB teams and examines winning percentage and attendance in 2015–17. | The abstract reports statistically significant differences and a declining strength of the winning-percentage result over time. The full PDF was inaccessible during this review, so detailed design, estimates, and author-stated limitations remain unverified. This is observational adoption evidence, not causal proof. | Learn to label time horizon and comparison design when evaluating a change. Do not claim “analytics caused wins” or attribute manager/position findings to Freeman without the correct source. |
| Kilanowski, Gelchie, Biancavilla, Gouveia, “Beyond cWAR: A Machine-Learning Model to Evaluate College Baseball Players for the Major League Draft” | No exact primary record matching that title and author list was verified. Two related but distinct works were located: (1) Kilanowski and Moloney's peer-reviewed 2024 article, **“Sabermetrics by the sea: Evaluating college players with the Cape Cod Baseball League”**; and (2) a Providence College student poster, **“Forecasting the Major League Baseball Draft Success: A Predictive Model for the Cape Cod League Talent,”** with seven student authors and Kilanowski as mentor. | The article constructs CCBL-specific cWAR from league run expectancy, wOBA and a temporary-player replacement baseline, then tests it against draft position and team wins. The separate poster describes TrackMan-derived features and compares ridge, lasso, elastic net, and linear models for draft-position prediction. | The article uses CCBL data from 2012–22; its 2021 batter cWAR association with 2022 draft position is modest but statistically significant (Spearman ρ = −0.3861, p = .0023), while pitcher cWAR is not significant (ρ = −0.2034, p = .0988). Team-win fit varies by year and pitching metric; the 2022 team-win correlation falls from 0.8518 before the positional adjustment to 0.8499 after it. The article notes missing fielding, short-season samples, pitcher exposure, and the influence of college-season performance. The poster reports both hitting and pitching models were overfit and draft-pick predictions clustered between picks 100 and 500. These are not validated MLB roster projections. | Reuse the discipline: define the target population, relevant replacement level, context, outcome, and comparator. Treat ML as a candidate only after leakage-safe out-of-time validation, calibration, and a simple baseline comparison. Keep college draft evaluation separate from MLB roster valuation. |
| Spencer Schmalz, “Weighted Earned Run Average: A Context-Adjusted Pitching Metric” | The exact paper/title and method were not located in searchable SABR records or exact-title searches. SABR has an author profile for Spencer Schmalz, but that does not verify this article. | Unknown until the article or a stable primary URL is supplied. | Do not infer the formula, data, validation, or results from the title. “Context-adjusted ERA” alone is not evidence of novelty or validity. | Keep the citation in an unresolved-source queue. If located, benchmark against the metric's intended estimand and appropriate established pitching baselines before considering adoption. |

### Source identity details

- Freeman's primary proceedings record identifies the different title and states the 30-team, 2014-adoption, 2015–17 comparison. Its abstract cautions that adoption benefits may lag; it does not establish causality.
- The peer-reviewed cWAR article is by Humbert Kilanowski and Thomas Moloney, *Journal of Sports Analytics*, 10(1), 67–75 (2024), DOI [10.3233/JSA-240771](https://doi.org/10.3233/JSA-240771). The article's machine-learning/TrackMan model is future work, not a reported result of that article.
- The separate Providence College poster reports overfitting directly. Its team and author list differ from the supplied citation; the institutional project page describes the prior-year testing goal, while the poster provides the displayed overfitting caveat.

## Points of parity and difference

| Dimension | Papers / references | HARDBALL | Assessment |
|---|---|---|---|
| Contextualized comparison | cWAR adjusts run values, replacement level, park, and position; the purported WERA title also signals context adjustment but remains unverified; Freeman examines adoption over time. | Combines performance, availability, payroll, pipeline, and roster scenarios across decision views. | **POP:** explicit context and a comparison baseline matter. HARDBALL must make each denominator, scope, date, and baseline visible. |
| Decision target | Manager/club adoption outcomes, CCBL player evaluation/draft position, or an unverified pitching metric. | MLB roster choices under budget, availability, and prospect-pipeline constraints. | **POD:** different decision scope and audience. This supports product differentiation, not a claim that HARDBALL's underlying estimates are more accurate. |
| Validation | Varies materially: proceedings abstract; one-season player-to-draft associations and two-season team fits; student poster that reports overfit. | Repository literature spine and projection/backtest work, alongside decision exhibits and explicit model limitations. | **Opportunity:** bring source-quality and validation maturity into one comparable, inspectable evidence record. Never equate association, fit, forecast skill, or causal impact. |
| Actionability | Each source centers a particular measure or research question. | The intended value is to connect evidence to a roster, budget, or availability decision. | **POD opportunity:** show what changes in a decision when an assumption or player input changes, while retaining uncertainty and provenance. |

## What HARDBALL should learn and test

1. **Make the estimand explicit.** Every metric should say what it estimates (observed production, projected production, replacement value, availability, or scenario value), for whom, over what period, and relative to which comparison group.
2. **Use baseball-relevant baselines.** Test position, league, level, season, role, park, exposure, and replacement-pool choices where relevant. Record whether an adjustment changes player rankings or actual decision outcomes.
3. **Separate description from prediction and causality.** A player metric's association with draft position does not validate MLB projection accuracy; a team-level association does not prove an intervention caused wins; a display statistic is not automatically a simulator input.
4. **Require a reproducible validation protocol before adoption.** Compare against a simple baseline and established metrics on the same population. Use chronological holdouts, prevent player/team leakage, report sample sizes and missingness, quantify uncertainty, and test calibration and subgroup stability. Record the exact code/data version and retain a known reference case.
5. **Treat availability as decision context.** A performance estimate only becomes a roster decision after playing-time availability, replacement options, contract cost, and constraints are made explicit. Report assumptions and sensitivity rather than hiding them inside one score.
6. **Keep research conclusions reversible.** An external paper may motivate a hypothesis; it must not silently change a HARDBALL figure, projection, or recommendation. Require a project-specific reproduction and an explicit decision to promote a finding into the model.

## Evidence Says Now recommendation

The current Evidence Says Now page is a PubMed medical/injury-literature surveillance product tied to playing-time availability. Preserve its medical scope and its explicit statement that literature findings do not automatically become model inputs. Adding these papers to its injury lanes would blur the evidence boundary.

Create a separate **Baseball Methods & Decision Evidence** section or index, linked from Evidence Says Now as a related research resource. Use a structured evidence card with:

- verified citation, primary-source link, publication type, and source-resolution status;
- research question, population, season/window, sample size, and intended decision;
- metric definition, data provenance, comparison baseline, and adjustment set;
- validation design, test period, performance measures, uncertainty, and known failure modes;
- what the result supports, what it does not support, and whether HARDBALL has independently reproduced it;
- linked HARDBALL claim/figure/backtest, owner, review date, and next test.

Use explicit evidence states such as **external context**, **source unresolved**, **reproduced**, **project-tested**, and **approved for model use**. Never let an external-context card appear as a HARDBALL validation result. Add a link to the relevant figure or backtest only after confirming the connection; otherwise state “no current HARDBALL implementation link.”

## Recommended next experiments

| Priority | Experiment | Pass evidence |
|---|---|---|
| P0 | Resolve the Freeman and WERA source citations with the original PDFs/URLs or correct bibliographic records. | Exact title, authors, stable primary source, and document type recorded; unresolved items remain excluded from published claims. |
| P1 | Reproduce the CCBL cWAR article's decision target as a separate research exercise, without importing its metric into MLB projections. | Data and formulas documented; same-season and out-of-time results reported; limitations retained. |
| P1 | Audit HARDBALL's current player evaluation claims against its current projection/backtest baselines. | Each displayed claim maps to source/version, benchmark, holdout, calibration/uncertainty, and known failure modes. |
| P2 | Design a roster-decision comparison showing how performance, availability, cost, and constraints alter feasible options. | Same-player alternatives, budget/availability assumptions, sensitivity, and decision-relevant outcome are visible and reproducible. |

## References verified in this review

1. Freeman L. *The Impact of Analytics in Professional Baseball: How Long Before Performance Improves*. MWAIS 2019 Proceedings. https://aisel.aisnet.org/mwais2019/7
2. Kilanowski H, Moloney T. Sabermetrics by the sea: Evaluating college players with the Cape Cod Baseball League. *Journal of Sports Analytics*. 2024;10(1):67–75. doi:10.3233/JSA-240771.
3. Colannino G, Fitzgibbons C, Gelchie E, et al. *Forecasting the Major League Baseball Draft Success: A Predictive Model for the Cape Cod League Talent*. Providence College student poster. 2024. https://engaged-learning.providence.edu/wp-content/uploads/sites/32/2024/04/Colaninno-Group-foamboard.pdf
4. Providence College Center for Engaged Learning. *A Predictive Model for the Major League Baseball Draft*. Posted April 16, 2024. https://engaged-learning.providence.edu/a-predictive-model-for-the-major-league-baseball-draft/
5. Society for American Baseball Research. Spencer Schmalz author profile. https://sabr.org/authors/spencer-schmalz/ (author profile only; does not verify the supplied WERA title).
