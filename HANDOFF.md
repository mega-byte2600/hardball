# HANDOFF — toby/wow (PR #5, stacked on PR #4)

WOW pass, 2026-10-31: the Boardroom layer (Cycle 26) — built for MLB
stakeholders, still on real data only. **Stacked on `toby/finale`
(PR #4)** — merge #1 → #2 → #3 → #4 → this.

## What shipped

1. **PRESS PLAY** — payroll vs wins animated across 16 seasons
   (2011–2026 panel). Bubble size = wins per $100M; the winning-cheap
   three ride in gold and barely move while payrolls inflate around
   them. The thesis, in motion, in ten seconds.
2. **PICK YOUR TEAM** — a dropdown with all 30 clubs: each team's 2026
   signature radar indexed to league = 100 against the gold
   winning-cheap profile, with wins, payroll, cap headroom, pipeline
   rank, and top prospect in the title. Every stakeholder finds their
   own club first — that's the hook.
3. **WHAT DOES THE MONEY BUY** — full 26-man rosters bought entirely
   from the real 2027 FA class at three budgets, switchable in-panel:
   Floor $171.2M → **42.0 WAR**, Middle $208M → 45.7 WAR, Cap $245.3M →
   **52.3 WAR**. The floor build captures ~80% of the cap build's WAR;
   the last $73.6M buys ~10 WAR. Prices are prior-contract AAV anchors
   and are labeled as such on the panel; constraints (26 men, spend ≤
   budget) are asserted in `bml_cycle26_wow.py`.

Dashboard is now **17 panels / 8 sections**; clean-clone offline build
re-verified (17 plotly divs, animation frames and scenario buttons
present in the file). README + exec summary counts updated. Release
v0.9.2-demo carries the built HTML at this branch's head.

## Reviewer notes

- Cycle 26's scenario builder is deliberately simple (greedy
  WAR-per-dollar + upgrades). It is an illustration of value density
  in the FA class, and says so — not a roster-construction engine.
- No model or prior-cycle data changed in this PR.

---
## INTEGRATION (2026-10-31, PR #6 — supersedes PRs #1–#5)
Main advanced 21 commits in a parallel lane while PRs #1–#5 were open
(player persistence, cap-pool deployment, viz overhaul, TALKTRACK), so
the stack no longer merged. This branch (toby/integrate, off main
f97f268) ports all five PRs onto current main: 63 files carried over
unchanged; 5 overlaps integrated by hand — dashboard_p6.py (main lane's
Figure-N viz system + CarpeData/Boardroom panels in 8 story sections,
20 figures; also fixes main's inline AZ→ARI map and adds the G1 offline
guards for the KPI fetch and the lake-backed pitching panel),
BML_LOG.md (both cycle series preserved; numbering collision documented
in an integration note, nothing renumbered), README/EXEC_SUMMARY
(main-lane text kept, addenda appended), requirements.txt (verified
union incl. scipy). Verified: merged tree builds offline with no lake
(19 figures, pitching omits gracefully) and with lake (20 figures).
On merge, PRs #1–#5 close as superseded. Figure numbers in the merged
dashboard shift +2 vs TALKTRACK.md (Boardroom figures lead) — flagged
for the main lane.

---

## DECEMBER READINESS CHECKLIST (Cycle 36, 2026-11-02 ~01:15 PT, overnight sprint)

Backlog item (g). The demo is for the Dec 1, 2026 Winter Meetings.
Status snapshot at checklist creation (all verified this run on main
10c217c8, unmoved since Cycle 35): gate ALL PASS; benchmark parity
r = 0.889, 201 matched; curated tables byte-identical to main (no data
PR from the platform step); dashboard rebuilds with lake at 23 figures
(Story 6 chapters as default, Boardroom 15 slides, Explorer all 23 by
task, 8 percentile player cards, Figure 23 Explorer-only); salaries
24/30 (Spotrac probe still 403 this run); forced-seller coverage 6/7
(CHC uncovered). P7 UAT approval is at MVP level only — the checklist
below keeps the demo inside that approved scope: same data, no new
claims, no new thesis.

### 1. Freeze and final refresh (targets, not yet done)
- [ ] 24/7 cycle keeps running to Dec 1 (6h cadence after the overnight
      sprint ends Mon morning); every run still does the Spotrac probe
      (once), the platform, and the gate — never skip the gate.
- [ ] Final full platform refresh in the last cycle before the freeze
      (target: Nov 30): ingest, curate, warehouse, parity r = 0.889 /
      201, gate ALL PASS. Any drift is investigated, never papered over.
- [ ] Freeze: after the final refresh, no new claims, figures, or data
      sources. Later cycles re-verify only, and report drift if any.
- [ ] Release tag cut from the frozen main (owner call — no tag exists
      yet). Record the tag + SHA here when cut.

### 2. Demo package (verify from the frozen main, DOM/data checks only)
- [ ] Dashboard rebuilds offline with the lake: 23 figures, no
      duplicates, no missing figure; Story is the default landing;
      Boardroom prints at <=15 slides; Explorer holds every figure.
- [ ] Figure 23 re-verified against data/posted_class_2026.json (BIS
      canonical: Sato .306, Itoh 34 BB); every printed line recomputed,
      none hand-typed.
- [ ] One-pager regenerates clean: `python3 src/make_onepager.py`
      produces docs/ONEPAGER.html from committed artifacts only.
- [ ] Talk-track figure references all <= 23 (gate checks this);
      docs/TALKTRACK.md "What about Japan?" Q&A still matches Fig. 23.

### 3. Print pack (print from the frozen main, day-before)
- [ ] docs/TALKTRACK.md printed.
- [ ] docs/ONEPAGER.html printed (print-clean, single page).
- [ ] README "Presenting in 5 minutes" section loaded (Story in 5
      minutes, Boardroom for the room, Explorer for questions, Fig. 23
      as the live-market closer).

### 4. Known gaps — carry honestly, do not hide or fix by invention
- [ ] Salaries 24/30: Spotrac still 403 (this run, single probe). Retry
      the probe each cycle; on a 200 only, rerun src/bml_cycle25.py
      (cache-aware: fetches only ARI/BOS/CHC/MIL/TB/TEX) and PR the
      completion. FanGraphs lane retries ONLY if a single probe returns
      200, and only under the Cycle 32 reconcile-first guard (24 known
      teams first; ship for the 6 only if it lines up, with
      source=fangraphs_rosterresource per row).
- [ ] Forced-seller panel stays labeled 6/7 until salaries complete;
      CHC uncovered is stated on the panel, not smoothed over.
- [ ] Persistence figures re-verified before Dec 1: EXEC_SUMMARY quotes
      contact r = 0.84 and OBP r = 0.30 — recompute both from HARDBALL's
      own player-year-over-year computation and confirm r vs R^2
      labeling in any literature comparison (flagged 2026-11-01, not
      yet confirmed in HARDBALL's own sample). Do not pitch
      OBP/contact as "undervalued" without HARDBALL's own
      Hakes-Sauer-style test on 2024-26 contracts.
- [ ] Retracted claims stay retracted: team-wins formula does NOT
      forecast next-year wins (Cycles 18-19, OOS MAE 14.05, R^2 -0.89);
      formula_prod.json stays annotated DIAGNOSTIC ONLY.

### 5. Dec 1 day-of
- [ ] Morning-of gate re-run on the frozen main (gate ALL PASS) and a
      fresh offline dashboard rebuild from that tree.
- [ ] Re-check the posted trio's status: the window runs Nov 2 -> Dec 16
      17:00 ET with the clock pausing at the Dec 1 lockout. If any of
      Sato / Taira / Itoh signs before Dec 1, add a dated update note
      to the Fig. 23 exhibit — do not silently rewrite its posted
      framing or its BIS numbers.
- [ ] Standing rules still bind on the day: real data only, no browser
      visual QA (owner called it off), never force-push, never route
      around a source block, anything changing claims/thesis/design
      direction goes to the owner, not into main.

### 6. After Dec 1
- [ ] This job's deadline guard fires (today after 2026-12-01): no
      builds, one report that the window closed, then silence. Disable
      the `hardball-247-build` schedule at that point.
