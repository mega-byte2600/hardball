# Cycle 64 — the 2027 Cap Transition ledger (slate item 3)

Slate item 3 of 6 (owner-approved elite/asset slate,
2026-11-02): all 30 teams on one decision surface for
the proposed 2027 system ($245.3M cap / $171.2M floor /
15% per-player max = $36.795M) — who must shed, who
must spend, and by how much.

## What shipped

- **`src/bml_cycle64.py` → `data/cap_transition_2027.json`** —
  one row per team, all 30, built from committed
  artifacts only: cap scenarios (Cycle 22), forced-seller
  shed sets (Cycle 30), Cot's labeled cross-check, the
  FA optimizer pool (Cycle 44), Steamer 2027 WAR.
  Each row: payroll with its basis label, status and
  distance, the shed set or spend gap, the 15%
  per-player check, and the Cot's-basis sensitivity
  with an agrees/disagrees flag.
- **Dashboard** — the ledger panel leads the Boardroom
  view (`_cap_transition_panel_html`, rendered from the
  artifact, omitted if the artifact is absent). Not a
  figure (count stays 25) and not a slide (Boardroom
  stays 15 slides).
- **Gate** — 3 new CAPLEDGER checks: **84 checks ALL
  PASS**; spellcheck green (verified ledger names and
  team codes whitelisted); platform clean (17 tables
  rebuilt byte-identical, 2 skipped on absent raw with
  committed parquets standing, warehouse from 19
  tables, parity r = 0.889 / 201).

## Headline numbers

Primary basis (Spotrac payroll totals, all 30 teams):
**7 over cap ($358,157,578), 15 under floor
($807,838,582), 8 inside the band.**

- Shed sets cover 6 of 7 over-cap teams and clear their
  gaps: NYM $133.6M of contracts (12.68 Steamer WAR),
  LAD $125.0M (8.91), NYY $76.5M (7.85), PHI $75.0M
  (6.59), ATL $27.0M (5.15), TOR $40.2M (3.55). CHC,
  over by $4,019,956, has no shed set — the row reads
  "shed set not covered — payroll basis gap" (no
  contract rows; Spotrac page failed in Cycle 25).
- Under-floor rows carry the spend gap and the
  equivalent count of optimizer-pool signings at the
  pool's median prior salary ($4,500,000, n = 199) —
  labeled arithmetic, not a roster plan.
- 15% per-player check uses Cot's `cb_2027_aav` (the
  only committed AAV field): 8 contracts above
  $36,795,000 on 5 teams. Spotrac salary was not used
  — it flags deals whose AAV is below the maximum
  (Valdez, Trout, Machado).

## Sensitivity — and what it is not

The Cot's file carries no team payroll totals, so the
second basis is the sum of the LRP-2027 rows Cot's
publishes a dollar figure for: a committed-contract
subtotal, labeled as such in the artifact, the panel,
and this body — never called a payroll. On that
subtotal: 1 over cap, 6 inside the band, 23 under
floor. **13 teams change status between the two
bases** (NYM, NYY, PHI, TOR, ATL, CHC, HOU, BOS, DET,
ARI, TEX, SF, LAA). The ledger shows both readings
rather than picking one. Definition sensitivity
(benefits, pre-arb pool) is not modeled — no committed
team-level figure separates them on either basis; the
artifact states that in one line instead of inventing
a split.

## Verification

Gate ALL PASS on the scratch tree (84 checks);
spellcheck green; curated parquets byte-identical;
parity r = 0.889 / 201. Dashboard changed, so release
v1.1.3 is cut on the merged tree per the Cycle 60
pattern and the published copy probed from the release
tarball (ledger title, summary counts, 25 figures,
live-IL panel, benchmark panel, Figure 14 footnote).
GitHub Actions ignored per the owner's 2026-11-02
directive (minutes exhausted until Dec 1).
