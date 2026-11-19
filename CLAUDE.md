# CLAUDE.md — Hardball

Claude Code loads this file automatically in every session in this repo. Keep it short and true.

## Project
Hardball is a **public** research dashboard for MLB roster decisions (performance, availability/health evidence, payroll, free agents). Live: GitHub Pages at `https://mega-byte2600.github.io/hardball/dashboard/` (served from `main`).
- **Stack:** Python 3.12 (pinned deps in `requirements.txt`: pandas, numpy, scipy, scikit-learn, plotly, requests, duckdb, pyarrow). Plotly HTML dashboard. DuckDB warehouse.
- **Data platform:** ingest → `data/raw/` (immutable + `manifest.jsonl`) → `data/curated/*.parquet` → `data/hardball.duckdb` → dashboard. See `docs/DATA_PLATFORM.md`.
- **Repo is public:** everything committed is published.
- `HANDOFF.md` is a very large running log — search it (grep) for context; do not read it whole.

## Commands
| Purpose | Command |
|---|---|
| Setup | `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt` |
| Build dashboard | `./.venv/bin/python src/dashboard_p6.py` |
| Serve locally | `python3 -m http.server 8893` → `http://127.0.0.1:8893/dashboard/` |
| Data content gate (the "test suite") | `./.venv/bin/python src/verify_data.py` |
| Lake gate | `./.venv/bin/python src/verify_lake.py` |
| Dashboard freshness gate | `./.venv/bin/python src/check_freshness.py` (exit 2 = stale artifact) |
| Spelling gate | `./.venv/bin/python src/spellcheck_gate.py` |
| **Data-link health** | `./.venv/bin/python src/check_connectors.py --json` |
| Live feed refresh | `./.venv/bin/python src/refresh_live_feeds.py` |
| Warehouse build | `./.venv/bin/python src/build_warehouse.py` |

A change is not done until the gates relevant to it pass. Show their output.

## Data sources
- **Registry (source of truth):** `docs/DATA_SOURCES.md` — created and maintained by `/datalink-audit`. Until it exists, use `docs/CARPE_SCORECARD.md` (connector notes), `docs/DATA_PLATFORM.md`, and `src/keyed_sources.py`.
- Public sources: MLB Stats API, Baseball Savant, FanGraphs, ESPN, MLB transactions, Spotrac-derived cached payroll (cached only — no automated scraping), NPB.
- Key-gated sources (`src/keyed_sources.py`): Statyx (`STATYX_API_KEY`), FastballAPI (`FASTBALL_API_KEY`, ~500 credits/month — budget every call), Tank01 (`TANK01_API_KEY`, deferred), Sportradar (`SPORTRADAR_API_KEY`, do not activate without owner sign-off).
- Existing project rules to keep: **fail closed** without a key (labeled "data unavailable", no network call); **no fabricated rows, ever**; a 403/429 **stops** the call and is reported — never routed around; social posts are leads, not proof (SIGNED only when confirmed by the MLB StatsAPI transactions feed); every figure names its source.

## Engineering standards (non-negotiable)
1. **Secrets:** never read `.env*`, never print/log/commit/echo any key or token. Refer to keys by env-var name only. If one is ever seen in code, output, or history: stop, flag it, recommend rotation.
2. **Resilient data links:** timeout, bounded retry with backoff + jitter, fail-closed handling, schema/contract validation, manifest entry, and a defined fallback (secondary source → last-known-good cached snapshot with an honest "as of" stamp).
3. **Freshness is visible:** every served dataset carries its as-of date; stale data is labeled, never passed off as live.
4. **Reproducible:** cite new sources, update the method/evidence record (`docs/`, `docs/citations_ledger.json`), rebuild the dashboard after code/data changes (it is a generated artifact).
5. **Small, reviewable changes** on a branch, then a PR to `main`. No force-push, no deleting data or branches without approval.
6. Model fits are not causation; budget figures are scenarios. Keep uncertainty and retracted claims visible.

## Workflow playbook — use these automatically when the situation fits
| Situation | Use |
|---|---|
| New feature, figure, data source, or multi-file change | `/kickoff` → `/build` |
| Any code touching an API/feed client or `keyed_sources.py` | `/harden-datalink <source>` standards |
| Questions about data health, outages, API reliability | `/datalink-audit` |
| Dashboard/HTML/plotly changes or slowness | `/web-perf` |
| Before pushing a branch or opening a PR | `/review` |
| Before merging to `main` (= publishing to Pages) | `/ship` |
| Ongoing monitoring in a session | `/loop 15m /datalink-watch`, `/loop 30m` (maintenance) |

## Workflow overrides for this repo
- "Unit tests" = the gates above (`verify_data.py`, `verify_lake.py`, `check_freshness.py`, `spellcheck_gate.py`). Add checks to `verify_data.py` for new data claims.
- `/datalink-watch`: use `check_connectors.py --json` for public sources. For FastballAPI/Statyx, **do not** spend API credits on health polling — check the latest manifest entry age in `data/raw/<source>/manifest.jsonl` instead.
- `/web-perf`: the dashboard is static Plotly HTML; focus on payload size, figure count/lazy rendering, and load time — not framework tuning.
- `/ship`: "deploy" = merging to `main`. Never merge without the user's yes.
