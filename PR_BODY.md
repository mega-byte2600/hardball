# Cycle 55 — API-2: feed architecture (census / event / validator)

Owner-directed 2026-11-02 ("design and architect to use in way
thats best for us and adds value — carpedata"). **Figure count
stays 25. No claim changes.** GitHub Actions ignored per the
owner's 2026-11-02 directive (minutes exhausted until Dec 1) —
the local gate, platform, and parity below carry the
verification.

## What shipped

- **Fixed feed roles:** FastballAPI = CENSUS (canonical current-IL
  snapshot); Statyx = EVENT layer (recent moves); MLB Stats API
  stays standings of record; FastballAPI standings stay validator.
  Documented in docs/DATA_PLATFORM.md ("Feed architecture") and
  labeled in the dashboard's sources footer.
- **Statyx standings test — DROPPED.** The payload's only
  identifier is a Statyx-internal `team_id` (1794–1823, 25
  distinct); no team name/abbreviation/code fields exist, no
  crosswalk to MLB teams exists in the repo, and coverage is 25 of
  30 teams per season (2025, 2026). Snapshot stays raw-only;
  verdict + field-level evidence recorded in
  `data/il_events.json` metadata and the CARPE_SCORECARD Cycle 55
  addendum. No code curates from it.
- **Event layer:** `src/bml_cycle55.py` compares the Cycle 51
  baseline snapshots against the newest landed pair and writes
  `data/il_events.json` (full comparison stored; published view
  restricted to the FA pool + scenario-roster players), curated as
  append-only `fact_il_events`. Fresh pull this cycle (one call
  per endpoint, all HTTP 200, 4 FastballAPI credits): **0 events —
  the correct result.** Standings and FastballAPI injuries were
  byte-identical to baseline; the Statyx page carried the same 50
  players/statuses/types/details/returns, differing only in every
  record's `updated_at`, which Statyx re-stamps at page-generation
  time (hand-verified). Landing is therefore state-aware: volatile
  fields are stripped before the change test, and an unchanged
  payload is logged `ok_no_change` in the manifest, not re-landed.
- **Refresh:** `src/refresh_live_feeds.py` — the production path
  the 6-hourly job will call. Watermark guard (skip if the last
  successful pull is <20h old, exit 0), credit ledger from the
  manifest with a hard skip at 200 FastballAPI credits/month,
  fail-closed pull (nothing lands unless all four endpoints
  answer 200), then rebuild of both artifacts and a one-line
  summary. `--force` overrides the watermark only. The gate never
  calls it — gate/CI contexts stay fully offline.
- **Consumer:** the health figure gains a movement line under the
  live-IL table, rendered from `il_events.json` (zero state reads
  "no movement in the FA pool since the baseline pull", with both
  layers' pull dates shown). `src/bml_cycle51.py` now resolves the
  newest landed snapshot stem per (source, kind); its rebuild of
  `il_current_live.json` is byte-identical (md5 da5e995f…).

## Verification

Platform: ingest 25 datasets / 0 failures; curate 19 tables
(18 → 19, `fact_il_events` new at 0 rows), all contracts pass,
all prior parquets byte-identical; warehouse rebuilt; parity
r = 0.889 / 201. Gate ALL PASS offline (68 checks, was 66 — two
new API-2 checks: il_events consistency incl. snapshot sha
verification, and the movement line in the rendered HTML).
Spellcheck green. No browser visual QA (standing rule).
Credits: 4 spent this cycle; 8 of 500 for November.
