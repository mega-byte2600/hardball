# Cycle 47 — Figure 23 rebuild: three players, three different bets (F23)

Owner-approved plan, executed 2026-11-02. Figure 23's single
leaderboard panel becomes a 9-panel data story inside the same
figure number — Sato the thesis **test**, Itoh the thesis **fit**,
Taira the conversion **gamble** — with the posting clock as the
ticking frame. Explorer-only; Story (6 chapters) and Boardroom
(15 slides) unchanged; **23 figures total**; no NPB→MLB translation
factor claimed anywhere.

## What changed

- **`src/bml_cycle47.py`** (new) computes every rendered number into
  **`data/fig23_rebuild_2026.json`** (new) from the committed trio
  dataset + 340-row NPB leaderboard CSV, and prints a verification
  table: **14/14 checks** — all trio rows re-derived from the CSV
  match the canonical dataset; fee on $60M = **$10.875M** (Cycle 34
  worked example) reproduced exactly.
- **`panel_posted()` rebuilt** — career arcs (Sato BB% 7.3→11.1 vs
  K% 26.7; Itoh IP 176.1/196.2/172.2 with BB% 5.5/3.6/4.7; Taira
  closer→starter ERA bars), Taira workload (+93.8 IP jump),
  leaderboard percentile dots, Sato K% vs CL qualified median
  (26.7% vs 16.0%), fee curve ($25M→$5.0M, $50M→$9.375M,
  $100M→$16.875M), Imai projected-vs-signed ($150M → $54M), and the
  posting-clock timeline (Nov 2→Dec 1 open; Dec 1→Dec 16 paused in
  a lockout; Dec 16 17:00 ET deadline).
- **Computed leaderboard context (2026):** Sato **#1 of 19** CL bats
  in HR (39), RBI (106) and OPS (.992); Taira **#1 of 11** PL arms
  in ERA (1.36), #1 of 13 in 2025 saves (31); Itoh **#2 of 11** in
  walk rate (4.7%) but #7 of 11 in ERA — the fit is walk
  suppression, and the figure says so.
- Companion HTML: trio cards kept, Imai expectation-vs-reality strip
  added, honesty box updated (Itoh 2024 BB% computed from
  leaderboard batters-faced — labeled; Taira 2024 absent from
  qualified boards — never backfilled; small pools labeled).
- Docs: BML_LOG Cycle 47, CARPE_SCORECARD addendum, TALKTRACK Japan
  Q&A refreshed. Spellcheck WHITELIST += leaderboard/src/py.

## Verification

- Platform: ingest 25 sources, curate 17 tables, warehouse built.
- Parity: **r = 0.889 / n = 201** (unchanged).
- Gate: **ALL CHECKS PASS** — Figure 23 present as Figure 23 in
  Explorer, footer sources intact, posted-class facts intact.
- Spellcheck: green.
