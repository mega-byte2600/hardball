# HARDBALL Data Platform — architecture

*Role: data engineering. Standard: the professional canon — Reis &
Housley's lifecycle, Kleppmann's storage/processing trade-offs,
Kimball's dimensional modeling, Akidau's streaming vocabulary, Moses
et al.'s data observability. This document states what the platform
is, why each choice fits this scale, and what was deliberately NOT
built.*

## The problem with the pre-platform state
Research cycles wrote one-off JSON files straight from APIs. That
worked — and it produced real failures: a silent year-copy in a
Savant pull (caught by hand), figure references rotting after a
merge, quality verified by a heroic manual pass instead of a gate.
Files are not a pipeline. This platform makes the flow explicit:
**ingest → raw → curated → warehouse → serving**, every stage
rerunnable, every number traceable.

## Layers (medallion, right-sized)

| Layer | Location | Rule |
|---|---|---|
| Raw | `data/raw/<source>/<dataset>` + `manifest.jsonl` | Immutable, as-received (JSON/CSV/HTML). Never edited, never read by dashboards. Every object carries a manifest entry: source, URL, fetched_at, sha256, bytes, rows, status |
| Curated | `data/curated/*.parquet` + `_build_report.json` | Schema-enforced, deduplicated, ID-joined (MLBAM only, never names). Each table declares its grain. Build fails closed on any contract violation |
| Warehouse | `data/hardball.duckdb` (built, gitignored) | DuckDB analytical store built from curated Parquet. Stakeholder questions live as named SQL in `queries/` |
| Serving | dashboard + one-pager + queries | Reads curated/warehouse only |

## Ingestion — batch, parallel, and one honest micro-batch
`src/ingest_platform.py` runs source tasks (the original `src/ingest.py` remains the SQLite lake loader) on a **bounded thread pool (6
workers)** — parallel across independent partitions (source × season
× team), never unbounded fan-out against a rate-limited host. Each
task retries with backoff, checksums its payload, and appends its
manifest entry; a failed source degrades the run report, never the
stored state (idempotent: re-running replaces dataset files
atomically, manifests are append-only history).

- **Batch** (daily-class cadence): MLB Stats API standings + team
  season stats, Baseball Savant leaderboards (4 families × 4
  seasons), FanGraphs Steamer, MLB minors aggregates.
- **Micro-batch streaming pattern** (Akidau's terms, honestly
  applied): MLB **transactions** are the one true event stream here.
  Ingestion is watermark-driven — `_watermarks.json` records the
  max event date landed; each run pulls only events after the
  watermark, in monthly partitions, and advances the watermark.
  That is incremental stream ingestion at this scale's cadence,
  not a Kafka costume.
- **Blocked-source lane**: Spotrac is serial, cache-first, and stops
  at the first 403 (recorded in the manifest as `blocked`). No
  routing around blocks, ever.
- **Cycle 44 sources** (all keyless, same manifest discipline):
  Chadwick Register people shards (the ID crosswalk), The Injury
  Report IL-stints CSV, and Baseball-Reference WAR daily files. The
  BRef files land raw ONLY — their salary column failed the Cycle 44
  credibility bar for dataset use (see CARPE_SCORECARD), so no
  curated salary table is built from them; fail closed, on record.
- **Key-gated sources (prepared, not active)**: `src/keyed_sources.py`
  holds env-key-gated, fail-closed stubs for Tank01, Statyx,
  FastballAPI, and Sportradar. Without a key they return a labeled
  "data unavailable" and make no network call. Sportradar's trial is
  deliberately NOT started before mid-November (30-day window must
  cover Dec 1).

## Structured and unstructured
Structured sources (APIs, CSVs) land as JSON/CSV in raw and curate
into typed tables. Unstructured sources (Spotrac HTML pages) land
as **raw blobs with metadata** and are parsed by a versioned parser
(`bml_cycle25.py`) into the structured salaries table — the blob is
kept, so a parser fix can re-derive history without re-fetching.

## Analytical database — why DuckDB
The serving questions are analytical (scans, joins, window
functions over seasons), so they belong on an OLAP engine, not on
the SQLite lake (which stays what it is: the app's transactional
store). DuckDB is the right-sized lakehouse choice (Reese): embedded,
zero-ops, reads Parquet natively, full SQL. Spark/Kafka-class
machinery at this data volume (~10⁵ rows) would be architecture
theatre; the doc says so plainly so the choice is auditable.
`src/build_warehouse.py` rebuilds the .duckdb from curated Parquet
in seconds; `src/query.py <name>` runs the named stakeholder
queries in `queries/`.

## Dimensional model (Kimball)
- `dim_player` — grain: one row per player (MLBAM id PK), conformed
  across every fact. Team affiliation is NOT a player attribute in
  facts' grain — it lives on the fact rows (SCD-aware: history is
  never rewritten when a player changes teams).
- `dim_team` — grain: one row per club (30).
- `fact_stat_lines` — grain: player × season (hitting lines).
- `fact_team_season` — grain: team × season (the 2011–2026 panel).
- `fact_projections_*` — grain: player × projection season.
- `fact_savant_expected` — grain: player × season.
- `fact_salaries` — grain: player × team × season.
- `fact_fa_class` — grain: player (2027 class).
- `fact_pipeline` — grain: organization (2026).
- `fact_health` — grain: team × season (IL counts).
- `dim_player_xwalk` — grain: one row per person carrying an MLBAM key
  (Cycle 44; Chadwick Bureau Register, ODC-BY): the conformed ID
  crosswalk (Retro / BRef / FanGraphs / NPB / Wikidata). 137,320 rows;
  joins `dim_player` 379/379.
- `fact_il_stints` — grain: one IL stint (Cycle 44; The Injury Report,
  from MLB IL transactions): 6,632 stints, 2,177 players, 2019–2026.
  Availability-history cross-checks only — it does not feed the
  Cycle 27 availability factors.
- `fact_salaries_cots` — grain: player × team (Cycle 44; Cot's LRP
  2027 basis, 237 rows, every row labeled
  `source=cots_baseball_prospectus`). A separately labeled cross-check
  layer: its basis (present-value deferrals, buyout option years)
  differs from `fact_salaries` (Spotrac-basis) BY DESIGN — the two
  are never summed or mixed.

## Data quality & observability (Moses et al.'s five signals)
- **Freshness**: manifest fetched_at per dataset; the 24/7 cycle
  alerts by report when a source exceeds its cadence.
- **Volume**: curated build report records row counts per table;
  the gate checks them against floors and against the prior report.
- **Schema**: curated contracts (columns, dtypes, nullability,
  ranges) enforced at build; violations fail the build.
- **Distribution**: range checks live in the gate (wins 40–115,
  OBP .28–.37, WAR sums, scenario constraints).
- **Lineage**: every curated table names its raw inputs in the
  build report; every dashboard figure names its source; every
  warehouse answer names its query.

## What runs it
The 24/7 build cycle (cron `hardball-247-build`, every 6h) runs:
probe blocked sources → ingest → curate → build warehouse → parity
checks → `src/verify_data.py` gate → ship/backlog. A red gate stops
the line: no merges off a failing build.

## Deliberately not built (and why)
- **Kafka / Spark / Airflow**: wrong scale; a bounded thread pool +
  cron + manifests deliver the same guarantees here (Kleppmann:
  choose boring technology at the scale you actually have).
- **Cloud warehouse (Snowflake/BigQuery)**: the demo must run
  offline from a clone; DuckDB preserves that property.
- **Real-time streaming**: no source emits sub-minute events that
  change a decision; transactions are watermark micro-batch.
