# Cycle 67 — player health cards in the FA shopping list (slate item 4)

Owner-approved slate, in order. The shopping list stops ranking by
headline WAR alone: every one of the 251 free agents now carries a
health card — measured availability, delivered-WAR expectation,
risk flag, current-IL status, anchor price with delivered WAR per
$10M, and an evidence link.

## What shipped

- **`src/bml_cycle67.py` → `data/fa_health_cards_2027.json`** —
  251 cards. Measured availability = max(0, 1 − days/364), days =
  sum of committed days_in_season across the player's 2025–26
  stints in curated fact_il_stints (Cycle 9 denominator, 2 × 182
  days). Coverage: **166 measured / 65 no IL record / 20 not
  matched** (no player_id in the shopping file — the NPB posted
  class plus Spotrac name-parsing fragments; no name-only join
  was attempted, because a name-only join risks false
  attribution). No-record players read "no IL record in
  committed data", never 100%.
- **Delivered WAR** = the Cycle 56 formula at player level:
  headline Steamer WAR × the player's own measured factor (else
  the UNC-2 pool mean: hitters 0.912, pitchers 0.807) + the
  measured residual-bias term at delivered volume (Steamer 2027
  PA/IP; all 231 players with Steamer WAR have a PA/IP row).
  Per-player intervals are NOT derived — a pool-draw interval
  would present pool variance as player risk, so intervals stay
  scenario-level only (Cycle 56). Stated in the artifact.
- **Risk flag** = measured availability below the UNC-2 pool p25
  (hitters 0.890, pitchers 0.629); 76 flagged. The flag fires
  often by construction — the comparison pool includes players
  with no IL time while the flagged set is conditioned on having
  IL history — and the panel says so.
- **Evidence link** from the dominant injury by keyword only:
  73 linked to a lane (UCL 29, muscle 41, tendon 2, workload 1),
  178 to the page top. `docs/EVIDENCE.html` gained the four lane
  anchors (id attributes only; headings, counts, PMIDs
  untouched).
- **Current IL** by exact-name match against curated
  fact_il_current: 13, matching the Cycle 51 count.
- **Prices stay anchors** (Cycle 61 left them untouched):
  delivered WAR per $10M is arithmetic on the same prior AAV.
- **Dashboard** — `_health_cards_panel_html` in the Explorer
  "Shop the FA Class" group, sortable by delivered WAR, 251 rows
  + header. Panel, not a figure (count stays 25); Explorer only
  (Story stays 6 chapters, Boardroom stays 15 slides).

## The difference it makes

- By headline WAR: Skubal 5.66, Contreras 4.29, Rasmussen 3.74,
  Trevor Rogers 3.04, Sonny Gray 2.97.
- By delivered WAR: Skubal 4.86, Contreras 3.79, Rasmussen 2.91,
  Sonny Gray 2.73, Luis Arraez 2.55. Rogers falls to 6th (2.41)
  — 64 IL days at 0.82 availability on a 3.04 headline. That
  drop is the buying tool working.

## Verification

- Gate: **89 checks ALL PASS** (87 + 2 new HEALTH checks:
  artifact consistency with availability + delivered WAR
  recomputed from artifact fields and delivered ranks 1..231
  unique and ordered; panel renders in Explorer with title,
  Delivered WAR column, top delivered name and a lane link,
  and not in Story; evidence page carries all four lane
  anchors).
- Spellcheck green — 161 player-name tokens and position codes
  added to the whitelist, each verified against
  data/fa_shopping_2027.json.
- Platform clean: curate rebuilt 17 tables byte-identical, 2
  skipped on absent raw with committed parquets standing;
  all 19 parquets byte-identical to main; warehouse rebuilt
  from 19 tables; parity r = 0.889 / 201. Dashboard rebuilt
  with the lake present: 25 figures, none missing.
- Release v1.1.5 follows per the Cycle 60 pattern (release
  commit atop main carrying only the rebuilt dashboard file;
  published file read back from the release tarball and
  probed).
