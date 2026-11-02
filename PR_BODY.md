# PR — Cycle 45: sources footer + API connections (Statyx & FastballAPI live)

Owner directives (2026-11-02 10:10–10:13 PT): "update repo so that
hardball shows all API sources at bottom of page when rendered! its
key for credibility! we just got two more!" and "make sure git knows
we have these apis as other agents collab on hardball project!"

## What ships
1. **Dashboard footer — ALL DATA & API SOURCES.** The rendered
   page's bottom sources box now enumerates every source with what
   it provides and an honest status label: MLB Stats API (live,
   keyless), Baseball Savant (live, keyless), ESPN (verified
   cross-validation), FanGraphs Steamer (committed snapshot),
   Spotrac (committed, 24/30), Cot's (committed labeled cross-check
   layer, 30 teams / 237 rows), Chadwick Register (committed,
   379/379), The Injury Report (committed, 6,632 stints), NPB
   official BIS (committed, keyless), Baseball-Reference WAR files
   (salary use failed closed Cycle 44 — stated on the page),
   Statyx (connected 2026-11-02, verified live), FastballAPI
   (connected 2026-11-02, verified live). Tank01 (deferred — owner
   dropped the RapidAPI signup for now) and Sportradar (trial
   starts mid-Nov) are listed explicitly as NOT yet connected.
   Presentation only: no data, figure, or claim changes.
2. **Connection record in git.** HANDOFF.md gains an "API
   CONNECTIONS — Statyx + FastballAPI LIVE (2026-11-02)" section
   and docs/DATA_PLATFORM.md the matching "API connections"
   section: what was verified, and the access route — keys live
   in Toby's Secure Vault, NEVER in this repo; other lanes route
   pulls through Toby / the 6-hourly cycle. (No AGENTS.md exists
   anywhere in this repo — checked the full tree.)
3. **src/keyed_sources.py corrected to verified reality.**
   FastballAPI: POST https://mcp.fastballapi.com/v1/{tool}, JSON
   body, x-api-key header (the Cycle 44 Bearer-at-fastballapi.com
   entry was wrong). Statyx marked ACTIVE/VERIFIED (Bearer at
   api.statyx.io was already correct). Tank01 = deferred;
   Sportradar = do not start before mid-Nov. Fail-closed verified:
   no env key → labeled "data unavailable", no network call.
4. **Cross-checks** (docs/CARPE_SCORECARD.md Cycle 45 addendum;
   FastballAPI cost 4 of 500 free monthly credits): standings vs
   committed StatsAPI data — 30/30 teams, wins 30/30, runs 30/30,
   zero diffs (losses 29/29 via curated fact_team_season);
   injuries — 14 of Statyx's 16 records also in FastballAPI's 190,
   all 14 agreeing on status + type.
5. **Gate + spellcheck**: verify_data.py gains a footer check (all
   13 source strings must render); spellcheck whitelist gains the
   Cycle 45 provider/domain terms.

## Verification
- Ingest 25 datasets, 0 failures; curate 17 tables, all contracts
  pass, byte-identical to committed; warehouse rebuilt; parity
  r = 0.889 / 201.
- Gate: ALL CHECKS PASS (offline + --live standings 30/30),
  including the new footer check. Spellcheck green.
- Dashboard rebuilt from committed snapshots: 23 figures, Story 6
  chapters, Boardroom 15 slides, Explorer all figures; footer
  confirmed below all modes by text/DOM check. No browser visual
  QA (standing rule).
- Spotrac probe not re-run (Cycle 44's 403 stands). Salaries stay
  labeled 24/30 Spotrac-basis + Cot's layer; forced-seller 6/7.
