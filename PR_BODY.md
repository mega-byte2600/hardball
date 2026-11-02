# Cycle 52 — SWAP: the optimizer rosters become the headline

Owner-approved 2026-11-02, after OPT-1 (Cycle 49) proved the
optima and OPT-2 (Cycle 50) stress-tested them. Research
condition honored throughout: the optimizer is headlined, never
as bare numbers — the ±20% price-error range and the prior-AAV
anchor label travel with every headline figure. **Figure count
stays 25.** GitHub Actions ignored per the owner's 2026-11-02
directive (minutes exhausted until Dec 1) — the local gate,
platform, and parity below carry the verification.

## What shipped

- `src/bml_cycle52.py` — promotion only, no new solves. Rewrites
  `data/wow_scenarios.json`: `scenarios` becomes the Cycle 49
  optimizer set, each entry carrying its Cycle 50 price-error
  range (`war_range_prices_pm20`); the Cycle 26 greedy set moves
  verbatim to `benchmark_greedy`, stress totals included. The
  Cycle 27 availability stress is recomputed on the new totals
  with Cycle 27's exact method.
- Dashboard (`src/dashboard_p6.py`): Figure 16 panel — title now
  reads "WAR proven-optimal (low–high across ±20% price error)";
  sub-copy updated (floor ~89% of cap WAR; last $74.1M buys
  5.9 WAR; anchor label kept). Story chapter 5 and Boardroom
  slide 12 quote the optimizer values with ranges. Figure 25,
  its facts box, the Explorer group framing and the figure index
  become "benchmark vs headline".
- Docs: README (Boardroom bullet + Figure 25 bullet),
  EXEC_SUMMARY (honesty paragraph rewritten; Cycle 52 addendum),
  TALKTRACK (figure intro, money-buys script, optimizer
  back-pocket Q&A, back-pocket numbers), ONEPAGER regenerated
  via `src/make_onepager.py` (subset counts now read from the
  artifact; the stale "~10 WAR" line corrected to 5.9),
  BML_LOG Cycle 52, CARPE_SCORECARD Cycle 52 addendum,
  HANDOFF Cycle 52 section.
- Gate (`src/verify_data.py`): two new checks — headline values
  equal the Cycle 49 artifact with Cycle 50 ranges attached and
  the greedy benchmark preserved; Story/Boardroom HTML carries
  the new headline and none of the old strings.

## The numbers

| Budget | Headline WAR (range, ±20% prices) | Spend | Stressed (mean avail.) |
|---|---|---|---|
| Floor $171.2M | **48.9** (45.0–53.2) | $171.1M | 44.6 |
| Middle $208.0M | **52.8** (48.5–55.5) | $207.8M | 48.1 |
| Cap $245.3M | **54.8** (50.4–55.9) | $245.2M | 50.0 |

Floor/cap WAR ratio 0.803 → **0.892**. Greedy benchmark
preserved: 42.0 / 45.7 / 52.3 WAR (stressed 38.3 / 41.7 / 47.7).

## Verification

Ingest 25 datasets / 0 failures · curate 18 tables, contracts
pass, all 18 parquets byte-identical to committed · warehouse
rebuilt · parity r = 0.889 / 201 · dashboard rebuilt, 25
figures · gate ALL PASS (offline + --live, standings 30/30)
incl. the new Cycle 52 checks · spellcheck green. No browser
QA (standing rule).
