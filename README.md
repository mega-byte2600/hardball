# Hardball

Hardball is a public research dashboard for MLB roster decisions. It puts player performance, availability, health evidence, payroll, and free-agent context in the same view so a decision can be inspected instead of taken on faith.

**Live dashboard:** <https://mega-byte2600.github.io/hardball/dashboard/>

## Scope

The project covers:

- hitting and pitching performance;
- injured-list and availability history;
- projections, validation, sensitivity analysis, and roster optimization;
- payroll scenarios and free-agent eligibility; and
- a Plotly dashboard with Story, Boardroom, and Explorer views.

The working question is simple: which inputs remain useful when performance, availability, role, and cost are considered together?

## Data and evidence

Inputs come from public baseball sources, including MLB Stats API, Baseball Savant, FanGraphs, ESPN, official transaction data, and Spotrac-derived payroll snapshots. Health and performance claims are linked to the literature record in `docs/`.

The repository keeps the source data used for published outputs. Social posts may help locate a lead, but they are not treated as proof of a signing, injury, or medical finding.

- Connector notes: [`docs/CARPE_SCORECARD.md`](docs/CARPE_SCORECARD.md)
- Citation record: [`docs/citations_ledger.json`](docs/citations_ledger.json)
- Reproducibility notes: [`docs/REPRODUCIBILITY.html`](docs/REPRODUCIBILITY.html)

## Run locally

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python src/dashboard_p6.py
python3 -m http.server 8893
```

Open <http://127.0.0.1:8893/dashboard/>.

Check the public connectors with:

```bash
./.venv/bin/python src/check_connectors.py
```

## Presenting in 5 minutes

Open the live dashboard above, or the local build. Story is the default
landing. The crest carries the data-as-of stamp (tracker, injured list,
and evidence dates, each traced to its feed artifact).

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

## Repository map

| Path | Purpose |
| --- | --- |
| `src/` | ingestion, metrics, models, validation, and dashboard generation |
| `data/` | cached public inputs and derived outputs |
| `dashboard/` | generated HTML dashboard |
| `docs/` | methods, evidence, citations, and reproducibility notes |

The dashboard is a generated artifact. Rebuild it from `src/` after changing code or data.

## Reading the results

Hardball is decision support, not a promise about future wins. A model fit is not proof of causation. Budget figures are scenarios, and player-value measures follow the definitions and source methods documented with each analysis. Uncertainty, coverage, and withdrawn claims are shown in the dashboard rather than hidden.

## Contributing

Keep changes reproducible. Cite new sources, update the relevant method or evidence record, and run the applicable checks before opening a pull request.
