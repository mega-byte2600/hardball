# Cycle 66 — the FA tracker ticker: the probe stack wired into the dashboard

Owner-directed 2026-11-02 evening (CarpeData): the probe sweep
(TRACKER_PROBE_2026-11-02.md) becomes a live wire panel, front
of Story mode — not a figure (count stays 25), not a chapter
(Story stays 6 chapters).

## What shipped

- **`src/pull_tracker_ticker.py` → `data/tracker_ticker_2026.json`**
  — one pull, all kept sources, polite rates, fail-closed per
  source. 521 items: **321 SIGNED / 200 REPORTED / 0 BUZZ**.
  SIGNED comes only from MLB StatsAPI transactions (FA codes
  SFA / DFA / TR / REL / CLW / OUT / DES, 7-day window, 705
  rows fetched) diffed against the freeAgents register
  (?season=2026, 246 players). REPORTED from MLB Trade Rumors
  (main + top-6-team + top-12-player RSS), MLB.com (top-6-team
  RSS), ESPN news + transactions (unofficial endpoints,
  cross-check), Google News RSS (generic + top-12-player
  queries; redirect links deduped on title+source), RotoWire
  (5-item free cap). Caps recorded in the artifact: 12
  players, 6 teams, 200 REPORTED stored, 10 BUZZ stored.
- **Dashboard** — `_ticker_panel_html` leads Story mode ahead
  of Chapter 1, rendered from the artifact, omitted if the
  artifact is absent. Three lanes, distinctly labeled. The
  integrity rule is the panel's headline discipline: an item
  becomes SIGNED only when the StatsAPI transactions feed
  carries it; REPORTED and BUZZ items are never labeled
  signings; DFA rows carry their exact move type ("Declared
  free agency"), so a declaration never reads as a signing.
- **BUZZ ships EMPTY, honestly.** Bluesky Jetstream is the
  only social source, and its stream read did not complete in
  this runtime (read timeout, 0 events on both pull runs).
  The lane carries a plain label saying it awaits stream
  verification — never faked, never substituted (AppView
  search 403, Reddit 403, Mastodon 0 signal stay dropped, as
  do GDELT 429, NewsAPI/GNews delayed/dev-only, X no free
  read tier).
- **Gate** — 3 new TICKER checks: **87 checks ALL PASS**;
  spellcheck green (ticker div excluded from the spellcheck
  scan — wire headlines are quoted third-party copy, verified
  by source); platform clean (17 tables rebuilt byte-identical,
  2 skipped on absent raw with committed parquets standing,
  warehouse from 19 tables, parity r = 0.889 / 201).
  Dashboard rebuilt with the lake present: 25 figures, none
  missing.
- **Caught by the gate:** one StatsAPI transaction (id 947748,
  TR) carried no description and no player name; the pull now
  skips such rows and counts them instead of rendering an
  empty bullet.

## Example items (quoted exactly from the artifact)

- SIGNED: "Detroit Tigers signed free agent RHP Jacob
  Waguespack." [SFA — Signed free agent], id 947743, 2026-11-02.
- SIGNED (declaration, not a signing): "1B Eric Wagaman
  elected free agency." [DFA — Declared free agency], id
  947676, 2026-11-02.
- REPORTED: "Milwaukee Brewers Face a Defining Decision on
  William Contreras' Future - TWSN" (Google News, William
  Contreras query).
- BUZZ: none — lane empty with the awaits-verification label.

## Not in this cycle (owner tap required)

The cron-body diff that would add the ticker pull to the
6-hourly build (alongside the already-approved item-6 wiring)
is proposed in HANDOFF under Next and is NOT applied here.
