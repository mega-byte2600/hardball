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
