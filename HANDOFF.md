# HANDOFF — toby/solutions (PR #3, stacked on PR #2)

Solutions pass, 2026-10-31: the three items the owner picked from the
research frontier — pitcher-bias fix, real salaries + FA shopping list,
P7 packaging. **Stacked on `toby/carpe-data` (PR #2)** — merge PR #1,
then PR #2, then this.

## What shipped

1. **Cycle 24 — pitcher bias root-caused and fixed.** Judged against
   ACTUALS, the shipped pitcher Marcel was optimistic on its own
   (pooled bias −0.208 ERA), concentrated in older arms (≥32: −0.301).
   Adopted the tested fix into `bml_cycle11.py`: explicit 3-season
   window + fitted age slopes (ERA −0.03552, WHIP −0.00905 per yr from
   27; cross-fit directions agreed −0.039/−0.033). Pool 76 → 102
   pitchers. Vs Steamer after the fix: ERA bias −0.324 → **−0.250**,
   MAD .556 → .524. Residual gap stays printed on the dashboard.
2. **Cycle 25 — real salaries + the shopping list.** Spotrac wired
   (Cycle 16's declared dependency): `data/salaries_2026.json`
   (927 rows, 864 ID-matched) and `data/fa_shopping_2027.json`
   (251 FAs, 231 with Steamer WAR). Dashboard panel 14. Prior AAV is
   labeled a last-price anchor everywhere. **Coverage caveat:** Spotrac
   rate-limited 6 team pages mid-pull (ARI/BOS/CHC/MIL/TB/TEX); the
   script caches, so a later rerun completes only those six. USA TODAY
   returned 402 — logged in the scorecard, not circumvented.
3. **P7 packaging.** README.md (quickstart, honesty rules, repo map),
   EXEC_SUMMARY rewritten (it still described 5 panels and the
   retracted formula family), dashboard at 14 panels, clean-clone
   offline build re-verified. A prerelease tag with the built demo
   HTML attached follows this PR on the branch head.

## Reviewer notes

- Pitcher projections changed on purpose (Cycle 24 adoption); roster
  and benchmark regenerated in the same pass. Hitter projections
  untouched this round.
- `bml_cycle16_salary.py` is unchanged: it was a stub awaiting the
  salary file, which now exists at the first path it checks
  (`data/salaries_2026.json`, list-of-records format with player_id —
  its loader returns the parsed JSON as-is).
- Still open from the audit: G6 (2019 anomaly), G7 (log backfill
  14/16/17), G8 (formula_prod annotation), G11 (minors). The 6 missing
  salary pages self-heal on the next cycle25 rerun after the Spotrac
  limit cools off.
