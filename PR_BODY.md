# Cycle 51 — API-1: Statyx + FastballAPI wired in and serving

The owner called out that the two keyed APIs were connected and in
the sources footer but served no figure. This cycle wires them
into the platform end to end: raw snapshots → curated table → a
real dashboard consumer. **Figure count stays 25.** GitHub Actions
ignored per the owner's 2026-11-02 directive (minutes exhausted
until Dec 1) — the local gate, platform, and parity below carry
the verification.

## Pulls (2026-11-02, one call per endpoint, all HTTP 200)

Via the Secure Vault connector helpers (keys never in repo):
Statyx injuries first page (50 recent-move records) + standings
(50 rows — no team names, kept raw only); FastballAPI
get_injuries (190 records) + get_standings 2026 (30 teams).
FastballAPI credits spent: **4 of 500** free monthly credits.
Statyx: free.

## What shipped

- `src/bml_cycle51.py` — `--pull` lands dated raw snapshot
  envelopes (`data/raw/{statyx,fastballapi}/*_2026-11-02.json`,
  payload sha256 in each envelope) + `data/raw/manifest.jsonl`
  entries; the default offline build asserts the snapshot hashes
  and rebuilds `data/il_current_live.json` (the gate's path).
- `fact_il_current` — new curated table in `src/curate.py`
  (declared grain + contract): **196 players**, the union of the
  two feeds (44 in both, 6 Statyx-only, 146 FastballAPI-only).
  All 17 prior curated tables reproduce byte-identical.
- Consumer — the health figure gains a **"Current IL picture —
  LIVE feeds"** sub-panel rendered from the artifact: **13 of the
  251 free agents currently listed injured**, with status, injury
  and expected return.
- Footer: Statyx + FastballAPI lines now read **SERVING** and
  name the layer they feed; `src/keyed_sources.py` statuses
  updated; gate gained API-1 artifact + panel checks.

## Reconciliation (all in the artifact)

- FA overlay: 13/251 matched by normalized name against the
  committed FA class.
- Vs the static layer (fact_il_stints): 12 of the 13 were on the
  IL at the 2026 season end (agreement). **1 differs — Garrett
  Whitlock**: both 2026 stints closed (activated), live feed says
  Out — leg fracture, return 2027-02-01. Flagged, not smoothed.
- Standings: FastballAPI vs committed kpi_2026 — **30/30 teams
  agree on wins and runs scored**, zero diffs.

## Verification

Ingest 25 datasets / 0 failures · curate 18 tables, contracts
pass, prior parquets byte-identical · warehouse rebuilt (18
tables) · parity r = 0.889 / 201 · dashboard rebuilt, 25 figures ·
gate ALL PASS (offline + --live) incl. new API-1 checks ·
spellcheck green. No browser QA (standing rule).
