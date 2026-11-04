# Hardball

Hardball is an evidence based MLB decision tool for evaluating player performance, health, role, payroll, and free agency in one auditable workflow.

It is built for baseball leaders, analysts, and people who want to see how the data supports a roster decision. The goal is not to predict baseball perfectly. The goal is to make the assumptions, evidence, uncertainty, and tradeoffs visible.

## Current status

| Area | Status |
| --- | --- |
| MLB team and player data pipeline | Done |
| Performance, health, payroll, and value metrics | Done |
| Free agent tracker and MLB eligibility join | Done in source |
| Official MLB, Statcast, FanGraphs, ESPN, and transaction connectors | Done |
| Validation, sensitivity analysis, and uncertainty scenarios | Done |
| Executive dashboard source | Done |
| Dashboard rebuild after the latest source changes | In progress |
| Social signals for market awareness | Experimental and unverified |
| Final rendered dashboard QA and release cleanup | In progress |

## What is implemented

The project currently includes:

- A 16 season team panel covering 2011 through 2026 and 509 team seasons.
- Player projections, injury and injured list history, payroll, and free agent data.
- Hitting and pitching measures including contact rate, walk discipline, wOBA, wRC+, FIP, and K BB%.
- Linear and logistic models with repeated K fold validation.
- Sensitivity and elasticity analysis.
- Budget scenario rosters, optimizer comparisons, and uncertainty ranges.
- A free agent tracker joined to official MLB free agent eligibility data.
- An offline Plotly dashboard with Story, Boardroom, and Explorer views.
- A literature spine and citations ledger so the research base can be audited.
- A repeatable connector smoke check for the live public data sources.

## The working question

Which inputs remain useful when an organization evaluates performance, availability, role, and cost together?

The project treats contact ability, walk discipline, pitching control, health, and price as decision inputs. It does not claim that one metric or one team model explains winning.

## Data sources

The project uses public data and stores reproducible local artifacts.

- MLB Stats API for team, player, hitting, pitching, standings, transactions, and free agent eligibility.
- Baseball Savant for Statcast and expected statistics.
- FanGraphs Steamer for projections where available.
- ESPN for cross checks.
- Spotrac payroll snapshots through the MIT licensed mlb-payroll project.
- MLB transaction data for injury and injured list history.
- NPB official BIS data for the posted player exhibit.
- Bluesky public search as an experimental social signal only. Social posts are never treated as confirmed transactions.

See docs/CARPE_SCORECARD.md for connector details and docs/citations_ledger.json for the source record.

## Run locally

Create an environment and install the dependencies:

~~~bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
~~~

Build the dashboard:

~~~bash
.venv/bin/python src/dashboard_p6.py
~~~

Open the generated file:

~~~bash
open dashboard/hardball_demo.html
~~~

For a local server:

~~~bash
python3 -m http.server 8893
~~~

Then open http://127.0.0.1:8893/dashboard/hardball_demo.html.

Run the connector check:

~~~bash
.venv/bin/python src/check_connectors.py
~~~

Use --json for machine readable output.

## Dashboard

The dashboard presents the same evidence in three ways:

- **Story** gives the shortest path through the main findings.
- **Boardroom** organizes the findings as a presentation sequence.
- **Explorer** lets a user move through the figures by decision question.

The generated HTML is an output artifact. Rebuild it from src/ after changing the source or data.

## Presenting in 5 minutes

Open `dashboard/hardball_demo.html`. Story is the default landing. The crest
carries the data-as-of stamp (tracker, injured list, and evidence dates,
each traced to its feed artifact).

1. **Press play (0:00).** The animated payroll vs wins panel runs 16 seasons
   (2011–2026): the winning-cheap three barely move while payrolls inflate
   around them. That is the thesis in motion.
2. **The verdict first.** Story leads with the free-agent market activity
   panel (SIGNED means confirmed by the MLB StatsAPI transactions feed;
   REPORTED and BUZZ items are never labeled signings), then 6 chapters:
   Chapter 1 Figure 3 (skills persist), Chapter 2 Figure 4 (run
   differential describes), Chapter 3 Figure 6 (payroll vs wins),
   Chapter 4 Figure 10 (cap reality), Chapter 5 Figure 16 (what the money
   buys), Chapter 6 Figure 18 (the Steamer benchmark). Method and the
   honesty box sit in the appendix at the end.
3. **Boardroom for the room.** Switch to Boardroom for the same case as
   15 slides, print-clean. The full 10-minute talk track is in
   `docs/TALKTRACK.md`; the one-page version is `docs/ONEPAGER.html`.
4. **Explorer for questions.** Switch to Explorer for all 25 figures,
   grouped by decision task (Cap Reality / Build a Roster / Shop the FA
   Class / Check the Model) with Pick Your Team on top. The live-market
   exhibit is The Posted Class (Figure 23, Explorer-only): the Sato /
   Taira / Itoh trio cards, the posting clock (window closes Dec 16 at
   5pm ET; the clock pauses if the Dec 1 lockout begins), the posting-fee
   tiers as a worked example, and the translation honesty box — no
   NPB-to-MLB translation factor is claimed anywhere in the figure.
5. **If challenged on a claim.** Explorer's Claims & reproducibility group
   carries the audit trail, including the retracted claims. Every figure
   names its source in its source box.

## Limits

The team win model is a diagnostic tool, not a guaranteed forecast. Cross year win prediction is weak and regresses toward the mean, with reported mean absolute error in the 9 to 13 win range.

Salary caps and budget scenarios are working assumptions, not league rules. WAR is not a single universal formula; FanGraphs and Baseball Reference use different methods. Where a translation is uncertain, the dashboard labels it rather than inventing precision.

The social signal reader is discovery support only. A post, hashtag, or rumor does not establish a signing, injury, value, or transaction.

## Repository map

- src/ contains ingestion, modeling, metrics, validation, and dashboard generation.
- data/ contains cached public data and model outputs.
- docs/ contains the literature spine, source ledger, scorecard, talk track, executive summary, and build log.
- FEATURES.md tracks feature ownership, source files, artifacts, gates, and build order.
- HANDOFF.md explains how another contributor can continue the work.
- dashboard/ contains generated outputs and is rebuilt from source.

## Next release work

1. Rebuild the generated dashboard from the current source.
2. Run the full regression and connector checks against the rebuilt artifact.
3. Finish the mobile and executive presentation pass.
4. Decide whether the experimental social lane belongs in the release or remains separate.
5. Record the release evidence in the build log.

## Mission

I’m on a mission to help baseball organizations make better player, performance, and health decisions through rigorous, evidence based analysis.
