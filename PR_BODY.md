# Cycle 58 — Record books & almanacs sweep

Owner standing directive (2026-11-02): "use almanacs, record
books, APIs, open data — it's all about data, the numbers don't
lie, get them." Source work only: **no claims added, no demo
numbers changed, figure count stays 25.** Every verdict below is
from a live probe on 2026-11-02 or a prior cycle's recorded
verdict; 403/429 stopped the source for the cycle; paywalls are
logged gaps, never routed around.

## The sweep (full table + evidence in the scorecard addendum)

| Source | Verdict |
|---|---|
| Baseball Almanac | REFERENCE-ONLY — homepage/robots 200, record-book path `/recbooks/` **403** (stopped); HTML-only, no API/CSV |
| Official MLB Record Book | REFERENCE-ONLY (print) — Elias's book; latest edition located **2021**; no machine-readable edition on MLB properties |
| Elias Sports Bureau | NO PUBLIC ROUTE — no API/download/data product; official-by-citation only (verified, not assumed) |
| Retrosheet | ADOPTED-SOLID, historical (prior evaluation; one-line re-confirmation) |
| Lahman (via SABR) | SOLID, historical (prior evaluation; Salaries end 2016) |
| Chadwick Register | ADOPTED, in platform (Cycle 44) |
| The Baseball Cube | EVALUATED, cross-check only (homepage re-probed 200) |
| SABR (extra) | NOT PROBED FURTHER — homepage **429**, stopped per rule; role already counted via Lahman |
| Hall of Fame (extra) | REFERENCE-ONLY — homepage 200; museum/editorial site, no data product |

Also logged: the Baseball America Almanac 2026 digital edition
is password-protected for buyers — a paywalled gap.

## Wiring decision — nothing new, on evidence

The candidate job was a records cross-check. Repo-wide grep
(record language + canonical totals across docs, src, data):
**the demo states no canonical historical records** — nothing
to cross-check, and no surface was invented for one. What the
cycle settles instead:

- **Citation rule:** any record stated in the demo from now on
  cites the Elias record book or MLB's official publications,
  by hand. Record books here are citation authority, not ingest.
- **Dashboard footer unchanged** — it lists active sources
  only, and none of these became active.
- **Health & availability lens** (one line per source in the
  scorecard): the record-book class adds no IL/workload data —
  Retrosheet never tracked the injured list, Lahman gives
  durability context only. Figure 14's layer stays measured IL
  data.
- One sourced caveat worth knowing: the Retrosheet paper that
  cites the 2021 Elias book notes a record it establishes was
  "not even included" in the most recent Elias or Sporting News
  record books — even the official book is not exhaustive,
  which is exactly why this project cites records rather than
  copying them.

## Verification

- Platform: ingest 25 datasets / 0 failures; curate 19 tables,
  all contracts pass; warehouse rebuilt; parity
  **r = 0.889 / 201**.
- Gate: **75 checks offline, ALL PASS** (unchanged — no new
  rendered pins); spellcheck green; dashboard rebuilds at 25
  figures from committed snapshots. No browser visual QA
  (standing rule). GitHub Actions ignored per the owner's
  blackout directive (until Dec 1).

## Docs

`docs/CARPE_SCORECARD.md` (Cycle 58 addendum: the complete
record-book layer in one table, probe evidence, wiring
decision), `docs/DATA_PLATFORM.md` (reference-layer section),
`docs/BML_LOG.md`, `HANDOFF.md` (Next unchanged: the pending
cron-wiring decision, Figure 9 owner item, Sportradar ~Nov 15,
final release cut).
