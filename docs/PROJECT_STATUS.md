# Hardball project status

Updated 2026-11-04 from `main` at `09b3b933`.

This is the current release ledger. `docs/BML_LOG.md` remains the historical build record. `HANDOFF.md` contains older contributor notes and is not the current release status.

## Functional and evidence work

| Area | Status | Current state |
| --- | --- | --- |
| Public repository and protected main | Done | Repository is public. Main protection is active and PR #60 merged. |
| MLB data pipeline | Done | Ingestion, curation, warehouse, and committed artifacts exist. |
| Performance metrics | Done | Hitting, pitching, contact, discipline, wOBA, wRC+, FIP, and K-BB% are included. |
| Health and availability | Done | Injury and injured-list history are integrated with source and date context. |
| Payroll and value | Done | Payroll, cost, value, budget scenarios, and salary reconciliation are implemented. |
| Free agent tracker | Done in source | Tracker is joined to official MLB eligibility data. |
| Salary completion | Done | Cot's all-team parse, reconciliation, and 7/7 forced-seller coverage are recorded. |
| Projections and validation | Done | Marcel-style baseline, Steamer comparison, repeated K-fold validation, and limits are documented. |
| Sensitivity and uncertainty | Done | Sensitivity, elasticity, and uncertainty ranges are included. |
| Optimizer and roster scenarios | Done | Budget builds, optimizer comparisons, and audit outputs are present. |
| Surplus value layer | Done | Free agents are ranked by projected value less expected market cost. |
| Prediction conviction | Done | Figure 12 carries an evidence stability label and no-prior-data state. |
| Bat-speed exhibit | Done | Context-only exhibit shipped. It is not used as a projection claim. |
| Japan posted-class exhibit | Done | Figure 23 is traced and Explorer-only. |
| Claims and reproducibility | Done | Claims register, figure trace, reproducibility page, and evidence links exist. |
| Live feed cadence | Done in source | Guarded refresh, tracker ticker, and data-as-of stamps are implemented. |
| Connector smoke checks | Done | Repeatable public connector checks exist. |
| Social signals | Partial | Bluesky reader is experimental and fail-closed. It does not confirm transactions. |
| Dashboard information architecture | Done in source | Story, Boardroom, and Explorer modes are implemented. |
| Figures and legends | Done in source | 25 figures, legends, sources, claims, and health panels are preserved. |

## Editorial, mobile, and presentation work

| Area | Status | Current state |
| --- | --- | --- |
| MLB Decision Intelligence positioning | Done in source | Crest, title, subtitle, and product language were rewritten. |
| Public copy cleanup | Done in source | Internal cycle, P7, private-repo, and development language is removed during rendering. |
| Color and visual system | Done in source | MLB Navy, Rays Navy, Columbia Blue, MLB Red, and gold tokens are documented and applied. |
| Baseball mark and crest hierarchy | Done in source | Baseball mark is larger and the crest has a clearer hierarchy. |
| Mobile phone layout | Done in source | Controls stack, touch targets are enlarged, and wide overflow is constrained. |
| Tablet layout | Done in source | Tablet spacing and controls are covered by responsive rules. |
| About and Contact module | Done in source | 20-word value proposition, Dartmouth email, LinkedIn, GitHub, PFAC Toolkit, and Dartmouth MPH links are present. |
| Editorial visual direction | Done | `docs/EDITORIAL_VISUAL_DIRECTION.md` documents the intended public design system. |

## Release state

| Item | Status | Truth |
| --- | --- | --- |
| Source changes merged to main | Done | Latest main is `09b3b933`. |
| README | Done, but status-aware | README correctly says the generated dashboard rebuild and final rendered QA remain in progress. |
| GitHub repository About metadata | Not verified as updated | The dashboard About module was updated. That is not the same as updating the GitHub repository description or topics. |
| Generated dashboard HTML | Not verified against latest source | PR #60 changed source and documentation only. The generated HTML was not included in that merge. |
| Rendered visual QA | Pending | 25 figures, legends, links, mobile layout, and public-copy cleanup still need verification on the rebuilt HTML. |
| Final release tag and evidence | Pending | The final frozen release record has not yet been cut from the current source. |

## Next release sequence

1. Rebuild `dashboard/hardball_demo.html` from current `main`.
2. Run the data, claims, spellcheck, connector, and rendered-copy checks.
3. Verify 25 figures, legends, Story, Boardroom, Explorer, About / Contact, and mobile behavior.
4. Commit the rebuilt artifact and record the final release SHA.
