# PR — Cycle 44: accuracy stack (persistence correction + labeled salary layers + crosswalk + IL history)

Owner directive (2026-11-02 08:11 PT): "do what takes to make
accurate, optimal and professional" — authorization for this cycle,
including superseding PR #21.

## What ships
1. **Persistence correction (supersedes PR #21).** PR #21 no longer
   merged (dirty vs main after Cycles 40–43); its corrected values
   are re-applied onto current main: dashboard_p6 claim copy,
   TALKTRACK, EXEC_SUMMARY, both persistence JSONs, and its Cycle 39
   BML entry. OBP pooled r ≈ 0.53; contact 0.84 (0.81–0.87); walk
   0.72. No other claims change.
2. **Cot's as a second labeled dataset** (owner option b):
   `data/salaries_cots_2027.json`, 237 rows / 30 teams, LRP-2027
   basis labeled in metadata + per-row `source`. Built by
   `src/bml_cycle44.py`. `salaries_2026.json` and forced-seller math
   untouched.
3. **BRef WAR salary cross-check — failed closed.** Reconciled vs
   the Spotrac-basis file (195/927 matched, 28.7% within $50k —
   basis difference) and vs Cot's LRP-2026 for the gap teams (114
   matched, 71.1% < 80% bar). No BRef dataset; workpaper
   `data/salary_recon_cycle44.json` + scorecard numbers.
4. **Chadwick Register crosswalk**: ingest + `dim_player_xwalk`
   (137,320 MLBAM-keyed rows; registry joins 379/379).
5. **Injury Report IL history**: ingest + `fact_il_stints`
   (6,632 stints, 2,177 players, 2019–2026). Cycle 27 factors
   unchanged.
6. **Keyed-source prep**: `src/keyed_sources.py` fail-closed stubs
   (Tank01/Statyx/FastballAPI/Sportradar) + scorecard/platform
   ready-to-activate entries. No signups, no keys. Sportradar trial
   flagged mid-Nov.

## Verification
- Ingest 25 datasets, 0 failures; curate 17 tables, all contracts
  pass (prior 14 byte-identical); warehouse rebuilt; parity
  r = 0.889 / 201.
- Gate: ALL CHECKS PASS (offline + --live standings 30/30);
  spellcheck green. Dashboard rebuilt with corrected copy (23 figs).
- Spotrac single probe: still 403. Salaries stay labeled 24/30
  Spotrac-basis; forced-seller 6/7.
