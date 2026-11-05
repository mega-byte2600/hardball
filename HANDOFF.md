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
## API CONNECTIONS — Statyx + FastballAPI LIVE (2026-11-02, Cycle 45)

**All lanes read this:** two keyed APIs were connected on
2026-11-02 and verified live. The owner directed that git itself
carry this news.

- **Statyx — CONNECTED + VERIFIED LIVE 2026-11-02** via Toby's
  Secure Vault connector (`custom.statyx`). GET
  https://api.statyx.io/v1/mlb/standings → 200; GET
  /v1/mlb/injuries → 200 with **16 live records** (status, expected
  return, type, comments; feed timestamped 2026-11-02). The free
  tier DOES include MLB injuries.
- **FastballAPI — CONNECTED + VERIFIED LIVE 2026-11-02** via
  Toby's Secure Vault connector (`custom.fastballapi`). Tools are
  POST https://mcp.fastballapi.com/v1/{tool}, key in the
  `x-api-key` header. get_standings {season: 2026} → 200, **30
  teams**; get_injuries {} → 200, **190 records dated
  2026-11-02**. Cross-checks vs the committed data: standings wins
  agree 30/30 with the MLB Stats API (zero diffs); 14 of Statyx's
  16 injuries also appear in FastballAPI's 190, all agreeing on
  status + type (docs/CARPE_SCORECARD.md, Cycle 45 addendum).
- **Access route:** the keys live in Toby's Secure Vault and are
  **NEVER committed to git** — there is no key in this repo to
  find. Other agents route Statyx/FastballAPI pulls through Toby
  (or the 6-hourly cycle). Repo-side code: `src/keyed_sources.py`
  (env-key-gated, fail-closed; FastballAPI shape corrected in
  Cycle 45). The rendered dashboard's bottom sources box lists
  both as connected, with the full source list beside them.
- **NOT yet active:** Tank01 (deferred — the owner dropped the
  RapidAPI signup for now; supplement only, nothing in the demo
  depends on it) and Sportradar (trial deliberately not started
  before mid-Nov so the 30-day window covers Dec 1). Neither
  feeds any demo data.

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
      Interim record (Cycle 60, 2026-11-02, owner-directed): v1.1.0
      published from main 7d6128c0 — a release commit atop main adds
      the built dashboard/hardball_demo.html and tag v1.1.0 points at
      it (SHA in the GitHub release + goal timeline). This is NOT the
      freeze tag; the frozen-main tag above is still owed.

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
- [ ] Price model (Cycle 61 workpaper): optimizer prices stay on
      prior-AAV anchors until a complete per-class record of FA
      signing terms lands (expired short deals included — the
      Cot's/Spotrac 2027 snapshots hold survivors only: class
      2022 keeps 24 deals, all >= 3 years). When the Sportradar
      trial opens (~Nov 15), verify its contracts coverage
      against the workpaper's readiness criteria before counting
      it as the source that unblocks PRICE-1.
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

---

## CYCLE 44 — ACCURACY STACK (2026-11-02 ~08:20 PT, owner directive: "do what takes to make accurate, optimal and professional")

Supersedes PR #21 (closed with comment): its persistence correction
is re-applied onto main 93cb55ce — OBP pooled r ≈ 0.53 (not "≈0.3"),
contact 0.84 (CI 0.81–0.87), walk 0.72, 466 players. Cot's adopted as
a second, separately labeled salary dataset (237 rows, LRP-2027
basis, `data/salaries_cots_2027.json`); the Spotrac-basis file and
forced-seller math are untouched. BRef WAR salary cross-check
reconciled and FAILED CLOSED (gap teams 71.1% within $50k vs the 80%
bar; workpaper `data/salary_recon_cycle44.json`). Platform grows:
Chadwick Register crosswalk (`dim_player_xwalk`, joins the registry
379/379) and Injury Report IL history (`fact_il_stints`, 6,632
stints 2019–2026) — 17 curated tables, parity r = 0.889/201, gate
ALL PASS. Keyed sources (Tank01 / Statyx / FastballAPI / Sportradar)
are prepped as fail-closed stubs in `src/keyed_sources.py` — no
signups, no keys; Sportradar trial must not start before mid-Nov.
Detail: docs/BML_LOG.md Cycle 44, docs/CARPE_SCORECARD.md Cycle 44.

---

## CYCLE 46 — HS-1: HAKES–SAUER PRICING SCREEN (2026-11-02, owner-approved MIT-gap programme, increment 1 of 6)

Workpaper only — no dashboard, talk-track, or exec-summary change.
`src/bml_cycle46.py` builds `data/hakes_sauer_dataset.json` (142
player rows, basis labels + exclusion cascades in the metadata) and
`data/hakes_sauer_results.json` from committed data only. Two salary
samples, bases never mixed: S = Spotrac-basis file (n = 60 after
excluding 553 pre-arb flat-$1M placeholders, 219 non-Bypassed
arbitration projections, 68 pitchers, 1 two-way, 26 incomplete —
exactly at the pre-registered n≈60 power floor, marginal); C = Cot's
LRP-2027 aggregated to player level (n = 82; CBT-AAV sensitivity
n = 76). Model: ln(salary) on Marcel 2027 OBP/SLG/K%/BB% with age,
Steamer WAR, Steamer PA controls (spec B drops WAR). Result: NO
verdict — no skill coefficient is significant in either sample, and
the descriptive OBP/SLG coefficient ratio flips sign across bases
(−1.43 vs +1.48); no in-repo run-value benchmark exists, so the
formal proportionality test is HS-2's job. The descriptive quartile
view points the thesis's way in both samples (top-quartile contact
median $/WAR ≈ half the bottom quartile's: $8.03M vs $14.98M in S,
$6.19M vs $11.64M in C) and is labeled a contrast, not a price
effect. Full method, limits, and HS-2 scope: docs/CARPE_SCORECARD.md
Cycle 46 addendum + docs/BML_LOG.md Cycle 46. Gate ALL PASS; parity
r = 0.889 / 201.

---

# HANDOFF — Cycle 47: Figure 23 rebuild (F23)

Figure 23 ("The Posted Class") rebuilt from one leaderboard panel
into a 9-panel story — "three players, three different bets": Sato
the thesis TEST, Itoh the thesis FIT, Taira the conversion GAMBLE,
framed by the posting clock. Same figure number; Explorer-only;
Story/Boardroom untouched; 23 figures total. No NPB→MLB translation
factor claimed anywhere.

## What shipped

1. **`src/bml_cycle47.py` + `data/fig23_rebuild_2026.json`** — every
   new number computed from the committed trio JSON + leaderboard
   CSV, with a printed verification table: 14/14 checks against the
   trio dataset, incl. the fee on $60M = $10.875M (Cycle 34 example).
2. **Panels** — Sato arc (BB% climbing, K% flat); Itoh arc (IP bars
   + BB% line); Taira conversion ERA bars; Taira workload bars
   (+93.8 IP annotated); leaderboard percentile dots; Sato K% vs CL
   qualified median; fee curve; Imai projected-vs-signed; posting
   clock timeline with the Dec 1 lockout pause drawn in.
3. **Computed context (2026):** Sato #1 of 19 CL bats in HR/RBI/OPS;
   Taira #1 of 11 PL arms in ERA (#1 of 13 in 2025 saves); Itoh #2
   of 11 in walk rate, #7 of 11 in ERA — fit = walks, stated plainly.
4. **Companion HTML** — trio cards kept; Imai expectation-vs-reality
   strip added; honesty box gains the computed-layer note (Itoh 2024
   BB% from leaderboard BF; small pools labeled; Taira 2024 absent,
   never backfilled).
5. **Docs** — BML_LOG Cycle 47, CARPE_SCORECARD addendum, TALKTRACK
   Japan Q&A refreshed (ranks, fee-curve checkpoints). Spellcheck
   WHITELIST += leaderboard/src/py (verified spellings).

## Verification

Platform clean (ingest 25, curate 17 tables), parity r = 0.889/201
unchanged, gate ALL PASS (Figure 23 present as Figure 23 in
Explorer; 6 chapters; 15 slides; 8 cards; footer intact), spellcheck
green. Build note: build the dashboard only with the lake present —
a lake-less build drops a panel and renumbers figures (the gate
catches it; Cycle 47 hit this once in scratch and rebuilt).

---

# HANDOFF — Cycle 48: HS-2, the Hakes–Sauer verdict exhibit (Figure 24)

Owner-approved MIT-gap programme, increment 2 of 6 (HS-2). The
verdict exhibit HS-1 promised: a run-value benchmark derived from
committed data, the formal proportionality test actually run, and
the verdict rendered as Figure 24 (Explorer-only, Check the Model).
Dashboard is now **24 figures**; figures 1–23 keep their numbers
(Figure 24 is appended last in the build order); Story 6 chapters
and Boardroom 15 slides untouched.

## What shipped

1. **`src/bml_cycle48.py` + `data/hakes_sauer_verdict.json`** — the
   benchmark attempt under pre-registered fail-closed criteria, the
   formal test, and the verdict text the dashboard renders verbatim.
2. **Benchmark — survived, labeled aggregate.** Runs/PA on OBP + SLG,
   fact_team_season, 480 unique team-seasons 2011–2026 (29 duplicated
   2026 rows deduped — payroll-cell formatting only, batting fields
   identical; curate.py unchanged). Season-FE: OBP +0.262
   (p ≈ 1.8e-26), SLG +0.278 (p ≈ 1.9e-85), within R² = 0.865,
   VIF 2.45; rho = 0.94 (95% CI 0.72–1.17). Ecological limit labeled:
   team aggregates split OBP/SLG's joint variation, so rho sits below
   event-level linear-weights values.
3. **Formal test — inconclusive by power.** HS-1 spec A refit
   reproduces HS-1's coefs/SEs exactly (asserted). Wald vs FE rho:
   S (n = 60) p = 0.42; C (n = 82) p = 0.90. Ratios neither sample
   can reject at 5% span the full scanned range [−20, +20].
4. **Verdict (exact, on the panel):** INCONCLUSIVE on mispricing.
   Defensible claim: persistent + cap-efficient + low-variance —
   not proven undervaluation. Quartile $/WAR contrast (0.54× / 0.53×)
   stays labeled descriptive.
5. **Claim hygiene:** the five owner-facing surfaces contained NO
   unqualified undervalued/mispriced assertion to replace (grep
   evidence in the PR body). Additive only: verdict + Figure 24
   cited in EXEC_SUMMARY's do-NOT-claim section, TALKTRACK honesty
   section + back-pocket, dashboard sources box. Thesis untouched.
6. **Counts 23 → 24:** dashboard source (docstring, index, button,
   Explorer), gate expectations (+ new Figure 24 and HS-2 artifact
   checks), README, TALKTRACK, EXEC_SUMMARY, ONEPAGER generator
   (regenerated). Spellcheck WHITELIST += sauer, misprices,
   mispricing, underprices, workpaper.

## Verification

Platform clean (ingest 25 datasets / 0 failures, curate 17 tables,
parquets byte-identical to committed), warehouse rebuilt, parity
r = 0.889 / 201 unchanged, gate ALL PASS (offline) including the new
Figure 24 + verdict-artifact checks, spellcheck green. Build note
(same as Cycle 47): build the dashboard only with the lake present —
a lake-less build drops a panel and renumbers figures (the gate
catches it).

## Next

OPT-1 (roster optimizer) — programme increment 3 of 6.

---
# HANDOFF — Cycle 49: OPT-1, the roster optimizer (Figure 25)

Owner-approved MIT-gap programme, increment 3 of 6. OPT-1 puts a real
optimizer next to Cycle 26's greedy scenario rosters and publishes the
comparison as **Figure 25** (Explorer-only, Build a Roster).
**25 figures total**; figures 1–24 keep their numbers; Story
(6 chapters) and Boardroom (15 slides) unchanged; Figure 16's rosters
and headline numbers unchanged. GitHub Actions ignored per the owner's
2026-11-02 directive (minutes exhausted until Dec 1) — local gate,
platform, and parity carry verification.

## What shipped

1. **`src/bml_cycle49.py` → `data/optimizer_comparison_2027.json`** —
   greedy reproduction (asserted exact against wow_scenarios.json),
   the MILP, the DH-restricted sensitivity, full rosters for both
   methods at all three budgets.
2. **Figure 25** — grouped bars (greedy / optimizer / DH-restricted)
   per budget + `_optimizer_html()` facts box (overlap, DH slots,
   15% rule), all numbers rendered from the artifact.
3. **Gate** — Figure 25 presence check + an OPT-1 artifact check
   (26-man rosters, spend <= budget, optima proven, 15% rule holds
   for both methods); talk-track reference ceiling 24 → 25.
4. **Counts 24 → 25** — dashboard source, README, TALKTRACK
   (+ back-pocket Q&A), EXEC_SUMMARY, ONEPAGER (regenerated).

## The numbers (all three optima proven, HiGHS gap 0)

- Floor $171.2M: greedy 42.0 → optimizer **48.9 WAR** (+6.9);
  Middle $208M: 45.7 → **52.8** (+7.1); Cap $245.3M: 52.3 → **54.8**
  (+2.5). Overlap 16 / 17 / 21 of 26 names.
- DH-restricted sensitivity: +5.5 / +5.2 / +0.4 — floor/middle edge is
  mostly combinatorics; the cap edge is mostly the DH rule (greedy
  carries Dominic Smith, 0.01 WAR, at DH everywhere; optimizer plays
  Brandon Lowe, 2.32).
- 15% per-player rule ($36.795M): binds nobody in the pool (max
  anchor $35.0M); all greedy rosters satisfy it; enforced in the MILP.

## Verification

Platform clean (ingest 25 datasets / 0 failures, curate 17 tables,
parquets byte-identical to committed), warehouse rebuilt, parity
r = 0.889 / 201 unchanged, gate ALL PASS (offline) including the new
Figure 25 + OPT-1 artifact checks, spellcheck green. Build note
(same as Cycles 47/48): build the dashboard only with the lake
present — a lake-less build drops a panel and renumbers figures
(the gate catches it).

## Next

OPT-2 (optimizer sensitivity + mixed pre-arb+FA floor roster) —
programme increment 4 of 6. Whether optimizer rosters ever REPLACE
the greedy ones in Figure 16 is an owner call, queued there.

---

## Cycle 50 — OPT-2: optimizer sensitivity + mixed pre-arb/FA floor (PR pending)

Programme increment 4 of 6. Explorer/workpaper layer only — Figure
16, Story and Boardroom untouched; replacing the greedy rosters with
optimizer rosters remains an OWNER decision, not part of this cycle.

1. **`src/bml_cycle50.py` → `data/optimizer_sensitivity_2027.json`** —
   Cycle 49's MILP imported unchanged; a base re-solve reproduces
   OPT-1 exactly (asserted) before any scenario runs. All solves
   proven optimal (gap 0), each with dual bound on record.
2. **Sensitivity strip under Figure 25** — scenario table (base /
   prices x0.8 / prices x1.2 / targeted bid-up / aging haircut) with
   WAR + roster churn per budget, plus the mixed-build block; every
   number rendered from the artifact.
3. **Gate** — new OPT-2 artifact check (scenario rosters 26-man,
   proven, spend within budget, mixed split sums to 26, pre-arb
   slots all at the $1M placeholder).

## The numbers

- Prices x0.8: 53.2 / 55.5 / 55.9 WAR (churn 6/6/4); x1.2: 45.0 /
  48.5 / 50.4 (churn 3/4/4) vs base optima 48.9 / 52.8 / 54.8. At
  x1.2 the 15% rule excludes Rendon and Skubal at scaled prices.
- Targeted bid-up (your 26 floor targets x1.2): 45.6 WAR, churn 6 —
  the solver drops 6 of its own targets, ace included.
- Aging haircut (WAR x0.85 at 33+): pessimist rosters re-score
  48.8 / 52.8 / 54.8 on base WAR — within 0.1 of the optima.
- Mixed floor (FA pool + 509 pre-arb at the $1M placeholder):
  **74.8 WAR for $96.2M**, 19 pre-arb / 7 FA slots. Framing: what
  the floor buys a club that develops or holds pre-arb talent —
  internal production, NOT a shopping list.

## Verification

Platform clean (ingest 25 datasets / 0 failures, curate 17 tables,
parquets byte-identical to committed), warehouse rebuilt, parity
r = 0.889 / 201 unchanged, gate ALL PASS (offline and --live,
standings 30/30) including the new OPT-2 check, spellcheck green,
DOM checks confirm the strip renders inside Figure 25's Explorer
block with figures 1-25 intact.

## Next

UNC-1 (availability-cap backtest, out-of-sample 2022-24 FA classes)
— programme increment 5 of 6. The Story/Boardroom roster question
(greedy vs optimizer) stays queued for the owner.

## Cycle 51 — API-1: Statyx + FastballAPI wired in and serving (PR pending)

The two keyed feeds stop being decoration: they now feed a curated
table and a dashboard panel. Collaborating lanes: pulls still route
through Toby's vault connectors (keys never in git); the committed
snapshots under `data/raw/{statyx,fastballapi}/` are the offline
source of truth, rebuilt by `src/bml_cycle51.py`.

1. **Snapshots (2026-11-02, all HTTP 200)** — Statyx injuries first
   page (50) + standings (50 rows, no team names, raw only);
   FastballAPI injuries (190) + standings (30 teams). FastballAPI
   credits spent: 4 of 500/mo; Statyx free. Manifest entries in
   `data/raw/manifest.jsonl`.
2. **`fact_il_current`** — 196-row union of the two injury feeds,
   registered in `src/curate.py`; all 17 prior tables reproduce
   byte-identical. Artifact: `data/il_current_live.json`.
3. **Consumer** — health figure gains a "Current IL picture — LIVE
   feeds" sub-panel: **13 of 251 FAs currently listed injured**,
   with status/injury/return. One live-only finding: Garrett
   Whitlock (static stints all closed; live: Out, leg fracture,
   return 2027-02-01), flagged in the artifact. Standings
   cross-check re-proven: FastballAPI vs kpi_2026, 30/30 wins+runs.
4. **Footer + gate** — both feeds now read SERVING in the sources
   footer; `src/verify_data.py` gained API-1 checks (artifact
   consistency + live panel present). Figure count stays 25.

## Cycle 52 — SWAP: optimizer rosters become the headline (PR pending)

The owner-approved promotion. Figure 16's rosters are now the
Cycle 49 proven-optimal builds; the greedy builds are the
benchmark. Figure count stays 25; no new solves.

1. **`src/bml_cycle52.py` → `data/wow_scenarios.json`** —
   `scenarios` = optimizer set with Cycle 50 price-error ranges;
   greedy set preserved verbatim under `benchmark_greedy`;
   Cycle 27 stress recomputed on the new totals (44.6 / 48.1 /
   50.0 at the mean factor; floor/cap ratio 0.892).
2. **Surfaces** — Figure 16 title/sub-copy, Story chapter 5,
   Boardroom slide 12 (all with ranges attached), Figure 25 and
   Explorer framing now "benchmark vs headline", README,
   EXEC_SUMMARY, TALKTRACK, ONEPAGER (regenerated). The
   prior-AAV anchor label stays on the scenario exhibits.
3. **Gate** — new checks pin the headline to the Cycle 49
   artifact + ranges, and the Story/Boardroom HTML to the new
   numbers.

## The numbers

- Floor $171.2M: **48.9 WAR** for $171.1M (45.0–53.2 across
  ±20% price error); Middle $208.0M: **52.8** for $207.8M
  (48.5–55.5); Cap $245.3M: **54.8** for $245.2M (50.4–55.9).
- Money story: the floor captures ~89% of the cap roster's WAR
  for ~70% of the money; the last $74.1M buys 5.9 WAR. Methods
  note kept: the optimizer's floor (48.9) beats the greedy's
  middle (45.7) outright.

## Verification

Platform clean (ingest 25 datasets / 0 failures, curate 18
tables, parquets byte-identical to committed), warehouse
rebuilt, parity r = 0.889 / 201 unchanged, gate ALL PASS
(offline and --live, standings 30/30) including the two new
Cycle 52 checks, spellcheck green, DOM checks confirm the new
headline in Story, Boardroom and the Figure 16 panel with no
stale greedy headline strings.

## Next

UNC-1 (availability-cap backtest, out-of-sample 2022-24 FA
classes) — next programme increment.

---
## CYCLE 53 — FIG-QA: FIGURES 1–25 TRACED AND GATED (2026-11-02, owner-directed)

Full QA audit of the dashboard: every figure's rendered numbers
traced to committed artifacts (trace table = CARPE_SCORECARD
Cycle 53 addendum), conventions applied, numbering/titles
reconciled across dashboard, Explorer, README, TALKTRACK,
EXEC_SUMMARY and ONEPAGER. Seven number/label edits, no claim
changes (detail in BML_LOG Cycle 53). The gate now carries one
artifact-tied check per figure (FIG-QA 1–25 in
`src/verify_data.py`, expected values computed from the
artifacts at gate time): **65 checks offline / 66 --live, ALL
PASS** (was 40/41). Platform clean: ingest 25 datasets /
0 failures, curate 18 tables, warehouse rebuilt, parity
r = 0.889 / 201, spellcheck green.

**Owner item:** Figure 9 (projections_2026) is in-sample fitted
values under a "Model-projected wins" title with no in-sample
label — disclosure is a claim call, left for the owner.

## Next

Feed-architecture cycle (FastballAPI = census, Statyx = event
layer, ≤1 pull/day, credit ledger) per the owner's 2026-11-02
design direction; then UNC-1 (availability-cap backtest).
## Cycle 54 — UNC-1: availability-cap backtest (workpaper only)

Numbered 54 because the parallel lane took 53 (FIG-QA, PR #35) mid-run;
this cycle rebased onto main 8b604edf before shipping. Verdict: NOT
SUPPORTED as a point-forecast improvement — pooled n=39 qualified FA
regulars from the 2022–24 classes (5,153 signings screened): flat MAE
95.1 → 132.3 capped; Marcel MAE 46.2 → 61.1 capped. The cap wins on
Marcel only in 2022 and on flat in no class. Why: the cap is a
one-directional penalty and the baselines already undershoot or sit
unbiased (flat bias −95.1 PA; Marcel bias +9.8); on the 20 players
where Marcel overshot, the cap helped 65% — it is a downside
adjustment, not a point correction. That is the UNC-2 input. NO demo
number, figure, or 2027 cap changed; script `src/bml_cycle54.py` →
`data/unc1_availability_backtest.json`; gate gains a UNC-1
consistency check. Platform + gate on the final tree: ingest 25/0,
curate 18 tables byte-identical, parity r = 0.889 / 201, dashboard
25 figures, gate ALL PASS.

## Next

UNC-2 (uncertainty layer — intervals on scenario WAR + projection
error bands) — final programme increment.
## CYCLE 55 — API-2: FEED ARCHITECTURE, CENSUS / EVENT / VALIDATOR (2026-11-02, owner-directed)

FastballAPI is now the **census** (canonical current-IL snapshot),
Statyx the **event layer** (recent moves compared against the
Cycle 51 baseline), StatsAPI stays standings of record and
FastballAPI standings the validator. **Statyx standings tested and
DROPPED** — only a Statyx-internal team_id (1794–1823), no
name/code fields, no crosswalk in the repo, 25 of 30 teams per
season; the snapshot stays raw-only (verdict + evidence in
`data/il_events.json` metadata). First event comparison (fresh
pull, 4 FastballAPI credits, all endpoints 200): **0 events** —
payloads state-identical to baseline; the Statyx page differed
only in every record's `updated_at` (re-stamped at page
generation, hand-verified), so landing is state-aware
(`ok_no_change` in the manifest, no re-land). New outputs:
`data/il_events.json` + curated `fact_il_events`; the health
figure carries the movement line under the live-IL table (figure
count stays 25). Production refresh = `src/refresh_live_feeds.py`
(20h watermark, 200-credit monthly hard cap from the manifest
ledger, fail closed; the gate never calls it). Platform: ingest
25/0, curate **19 tables**, parity r = 0.889 / 201, gate **67
checks ALL PASS**, spellcheck green.

## Next

Wire `src/refresh_live_feeds.py` into the 6-hourly job so the
census stays current untouched (parent lane); then UNC-2.
(Numbered Cycle 55: the parallel lane's UNC-1 took Cycle 54,
PR #36, while this cycle was in build.)

---
## CYCLE 56 — UNC-2: THE UNCERTAINTY LAYER (2026-11-02, owner-approved programme)

The final MIT-gap increment. The headline scenario WAR (48.9 / 52.8 /
54.8, optimizer rosters since Cycle 52) now carries a delivered-WAR
range beside its ±20% price-error range, on Figure 16 (default title
+ all three budget buttons), Story chapter 5, Boardroom slide 12,
and the one-pager's scenario table. **Delivered WAR (10th–90th
percentile): Floor 33.0–46.9 (median 39.8); Middle 36.0–50.7 (43.2);
Cap 37.6–52.4 (44.9).** Method: seeded Monte Carlo, 20,000 draws
(`src/bml_cycle56.py` → `data/uncertainty_scenarios_2027.json`;
re-runs reproduce the artifact byte for byte) over measured
projection error — the shipped Marcel's variant-C backtest
residuals, replayed by importing the Cycle 21/24 scripts and
asserted against the committed artifacts (hitters n=196, pitchers
n=59) — and measured player availability (2025–26 IL pools:
hitters n=201 mean 0.912, pitchers n=102 mean 0.807). Per UNC-1,
availability shapes the distribution only; the points are
unchanged and are labeled the full-availability projections
wherever the ranges render. The median gap decomposes exactly
(availability level −6.8/−7.2/−7.5; measured residual bias
−2.2/−2.3/−2.3); Cycle 52 stress totals fall inside all three
intervals. Gate: **71 checks offline / 72 --live, ALL PASS** (3 new
UNC-2 checks pin the artifact and every rendered interval);
platform clean (ingest 25/0, curate 19 tables, parity
r = 0.889 / 201); spellcheck green; figure count stays 25.

**Programme complete:** HS-1, HS-2, OPT-1, OPT-2, UNC-1, UNC-2.

## Next

Wire `src/refresh_live_feeds.py` into the 6-hourly job (parent
lane). Figure 9 disclosure remains an owner item. Sportradar
trial ~Nov 15. Final release cut before Dec 1.

---
## CYCLE 57 — EVIDENCE SURVEILLANCE: PUBMED BEHIND FIGURE 14 (2026-11-02, owner-directed)

The APE PFAC toolkit's "What the evidence says now" pattern,
applied to the injury literature behind the availability edge.
**Anchor: Figure 14** (2027 health risk — playtime you should NOT
count on). The dashboard carries ONE asterisked footnote line
directly under the Figure 14 panel ("* What the evidence says
now — the published research on injury recovery and
prevention."), with the four lane counts inside it and a link to
the standalone page
**`docs/EVIDENCE.html`** (generated by `src/make_evidence_page.py`
from the committed artifact only, one-pager pattern).

Source: PubMed / NCBI E-utilities, keyless, via
`src/pull_evidence_surveillance.py` (standalone serving pull, NOT
a platform ingest source; 6-day staleness guard; fail closed on
any non-200). Four lanes, queries + counts as run 2026-11-02,
recorded verbatim in `data/evidence_surveillance.json`: UCL
return to play **157**; baseball injury prevention & workload
**426**; cellular recovery / muscle regeneration **404**; tendon
healing & biologics (SR/MA in query) **119**. Deterministic
selection: SR/MA first, then most recent, 3 cards per lane;
abstracts stored per card; plain Finding per card drawn ONLY from
its abstract (overlay `data/evidence_plain_lines.json`, merged by
the pull; page build fails closed if a selected card lacks one).
Claim hygiene: the page is labeled "Literature surveillance —
context, not a model input"; no paper feeds any figure or model.
Flagged in the scorecard, not fixed: the biologics evidence is
weak (two RCT meta-analyses find no PROM benefit for platelet
concentrates/PRP). The owner's data-driven intro line (costliest
body part by IL days) was CHECKED AND NOT SHIPPED:
`fact_il_stints` has no body-part field and its free-text injury
strings leave ≈25% of IL days unclassifiable — no clean split,
not forced (detail in the scorecard). Gate: **75 checks offline,
ALL PASS** (4 new evidence checks); platform clean (ingest 25/0,
curate 19 tables, parity r = 0.889 / 201); spellcheck green;
figure count stays 25.

## Next

Wire `src/refresh_live_feeds.py` AND
`src/pull_evidence_surveillance.py` (6-day guard) into the
6-hourly job — one pending cron-wiring decision (parent lane).
Figure 9 disclosure remains an owner item. Sportradar trial
~Nov 15. Final release cut before Dec 1.

---

## CYCLE 58 — RECORD BOOKS & ALMANACS SWEEP (2026-11-02, owner standing directive)

The record-book class, probed under CarpeData discipline (403/429
= stop; paywalled = logged gap; every verdict from a page actually
retrieved 2026-11-02 or a prior cycle's recorded verdict; full
table in the scorecard's Cycle 58 addendum). **Baseball Almanac**:
robots 200 + homepage 200, but the record-book path `/recbooks/`
returned 403 → stopped; HTML-only, no API/CSV — REFERENCE-ONLY.
**Official MLB Record Book**: a print object kept by the league's
statistician — the latest edition located is the 2021 "Elias Book
of Baseball Records" (cited as current in a Retrosheet research
paper retrieved this cycle); MLB's own branded book is 2013 print;
no machine-readable edition on MLB properties; the Baseball
America Almanac 2026 digital edition is password-protected
(paywalled gap). **Elias Sports Bureau**: no public API, download,
or data product (curl to the homepage dropped by the server —
HTTP 000, empty reply; a text fetch refused 403)
— official-by-citation only, now verified rather than assumed.
**SABR**: homepage 200 (110,244 bytes); nothing separately wired
— its data role is already counted (it publishes Lahman). **Hall of Fame**: homepage 200, editorial
site — REFERENCE-ONLY. Historical layer re-confirmed in one place:
Retrosheet (adopted-solid historical), Lahman via SABR (solid
historical; Salaries end 2016), Chadwick (ADOPTED, in platform),
The Baseball Cube (cross-check only; homepage 200).

**Nothing new wired — on evidence.** The candidate job was a
records cross-check; a repo-wide grep shows the demo states **no
canonical historical records**, so there was nothing to cross-check
and no surface was invented. Citation rule set instead: any record
stated in the demo cites the Elias record book / MLB official
publications, by hand. Dashboard footer unchanged (no source became
active); figure count stays 25; claims unchanged. Health lens: the
record-book class adds no IL/workload data (Retrosheet never
tracked the injured list; Lahman = durability context only) —
Figure 14's layer stays measured IL data. Gate: **75 checks
offline, ALL PASS**; platform clean (ingest 25/0, curate 19
tables, parity r = 0.889 / 201); spellcheck green.

---

## CYCLE 59 — CYCLE 58 PROBE-EVIDENCE CORRECTION (2026-11-02, docs only)

Two evidence lines in the Cycle 58 section above were wrong as
shipped and are corrected in place (also in the scorecard,
DATA_PLATFORM, BML_LOG; PR_BODY carries an errata note).
**SABR**: printed "homepage 429 → stopped" — the homepage
answers 200 (110,244 bytes; re-probed on the record this
cycle). Nothing separately wired: its role is Lahman, already
counted. **Elias**: printed "200 via curl, 35,678 bytes" —
curl to the homepage is dropped by the server (HTTP 000,
empty reply; re-probed this cycle); the no-public-route
verdict stands on that refusal plus the text fetch's 403.
Cause: the Cycle 58 probe batch's in-flow result disagreed
with its own completion record; the completion record and the
re-probes govern. No verdicts, numbers, or wiring changed.

---

## CYCLE 60 — PUBLISH THE CURRENT DASHBOARD: RELEASE v1.1.0 (2026-11-02, owner-directed)

The owner reported the health API feed was not visible on the
site, and he was right: `dashboard/hardball_demo.html` is
gitignored on main and only enters the repo at release cuts, and
the newest release tag was **v1.0.1 (2026-11-01)** — a dashboard
from before Cycles 51–59, with none of the live-IL panel, the
feed movement line, the optimizer headlines, the UNC-2 ranges,
or the Figure 14 evidence footnote. Cycle 60 publishes the
current build.

**Release v1.1.0** = this docs merge, plus a release commit atop
main adding the one generated file
`dashboard/hardball_demo.html` (5,539,972 bytes, built offline
from committed snapshots off main 7d6128c0); tag `v1.1.0` points
at that release commit, same pattern as the v1.0.1 tree. Built
file verified by content, in the scratch build and again in the
published tag tree: 25 figures; "Current IL picture — LIVE feeds
(Statyx + FastballAPI, pulled 2026-11-02)"; the Cycle 55
movement line; optimizer headlines 48.9 / 52.8 / 54.8 WAR with
their ±20% price ranges (floor 45.0–53.2, middle 48.5–55.5, cap
50.4–55.9); UNC-2 delivered-WAR intervals (floor 10th–90th
33.0–46.9, middle 36.0–50.7, cap 37.6–52.4); the Figure 14
footnote in its exact wording with href `../docs/EVIDENCE.html`
(resolves from `dashboard/` to `docs/EVIDENCE.html`); sources
footer naming Statyx, FastballAPI, PubMed. No source fix was
needed — the footnote href already resolved and the Cycle 57
gate check already pins it. Gate on the publish tree: **75
checks offline, ALL PASS**; spellcheck green; warehouse parity
r = 0.889 / 201. This is an interim publish, not the December
freeze: the freeze tag is still owed (readiness checklist §1).

## Next

Wire `src/refresh_live_feeds.py` AND
`src/pull_evidence_surveillance.py` (6-day guard) into the
6-hourly job — one pending cron-wiring decision (parent lane).
Figure 9 disclosure remains an owner item. Sportradar trial
~Nov 15. Final freeze release cut before Dec 1 (v1.1.0 interim
publish done, Cycle 60).

## CYCLE 61 — PRICE-1: PREDICTED-PRICE MODEL, INVENTORY FIRST (2026-11-02, slate item 1 of 6)

Owner-approved elite/asset slate, item 1: replace the
optimizer's prior-AAV anchors with model-predicted prices —
only if the model earns the switch in backtest (pre-committed
bar: train 2022 + 2023, test held-out 2024, held-out MAE at
least 10% below the anchor baseline's on the same players).

**Verdict: NOT RUN — TRAINING DATA ABSENT. Anchors stay.**
Step 0 (inventory before modeling, fail closed) found no
usable training set of actual signed FA contracts in the
repo. The signing census exists (StatsAPI transactions via
Cycle 54: 1,645 / 1,849 / 1,659 signings for classes
2022–2024) but carries no terms. The only signed terms
anywhere — Cot's contract strings, 153 parseable — are
survivors on 2027 payrolls: class 2022 keeps 24 deals, all
>= 3 years; class 2023 keeps 18, all >= 3 years; class 2024
keeps 35, none 1-year; spans mix extensions with FA
signings. Training or testing on survivors certifies long
deals only and prices a class full of short deals — not run.
No contracts invented; Spotrac / FanGraphs FA trackers stand
403 and were not touched.

Shipped: `src/bml_cycle61.py` (the reproducible audit) and
`data/price_model_workpaper_2027.json` — inventory,
survivorship table, the exact missing source with readiness
criteria, and the pre-registered model design (target,
features, form, split, baselines, the 10% bar, switch
mechanics) so the fit runs unchanged the day terms land.
Gate gains 3 PRICE-1 checks (workpaper on record;
survivorship recomputes from the Cot's strings; incumbent
anchor basis untouched): **78 checks ALL PASS**; spellcheck
green; warehouse 19 tables; parity r = 0.889 / 201. No
dashboard change, so **no release cut** (Cycle 60 rule: a
release is part of a user-visible change; there is none).

## Next

Slate item 2: projection blend + honest benchmark page.
Sportradar trial ~Nov 15 gains a second job: verify whether
its contracts coverage includes expired historical deals —
that, not current salaries alone, is what unblocks PRICE-1
(readiness criteria in the workpaper). Cron wiring for both
refresh scripts is approved as slate item 6. Figure 9
disclosure remains an owner item. Final freeze release cut
before Dec 1.

## CYCLE 62 — BLEND-1: PROJECTION BLEND + BENCHMARK PAGE (2026-11-02, slate item 2 of 6)

Owner-approved slate, item 2: a Steamer + Marcel blend,
adopted only if it beats both parents on held-out actuals
(pre-committed bar: weights fit on 2025 only, judged on
2026 only; hitter primary MAE beats both parents, pitcher
no worse than the best parent), plus the honest benchmark
page either way.

**Verdict: blend NOT ADOPTED — it cannot be scored.**
Step 0 found no paired set containing Steamer: the repo
holds Steamer only for 2027 (a season not yet played); the
FanGraphs API ignores its season parameter (probed
2026-11-02 — the "2026" response is the current set);
Steamer's pre-season archive ends at 2024 and the Marcel
inputs for those targets (2020–2022 player lines) are not
committed. No weights were fit and no shadow run was made
(both adoption-gated). Steamer remains the published 2027
projection set and Marcel the spine, unchanged.

What shipped: `src/bml_cycle62.py` +
`data/projection_blend_2027.json` — the paired benchmark
that CAN be run, built from the curated warehouse with the
Cycles 21/24 loaders mirrored (hitters PA >= 300, pitchers
IP >= 40; paired n: hitters 88/80, pitchers 23/22 for
2025/2026), opening with a reproduction assertion: the
variant-B backtests regenerate from fact_stat_lines and
match the committed artifacts exactly. Judge window 2026:
hitter OBP — naive r .298 / MAE .0265, Marcel r .410 /
MAE .0237; pitcher ERA — naive r −.086 / MAE 1.0177,
Marcel r −.020 / MAE .9394 (ranking near chance for both,
n = 22; stated on the panel, not hidden). Dashboard: the
benchmark panel "How good are these projections?" under
Figure 18 in Explorer (not a figure; count stays 25),
rendering the table from the artifact with Steamer and the
blend shown as not scored, with the reason. Gate gains 3
BLEND-1 checks: **81 checks ALL PASS**; spellcheck green;
platform clean (17 tables rebuilt byte-identical, 2
skipped on absent raw with committed parquets standing;
warehouse 19 tables; parity r = 0.889 / 201). Dashboard
changed, so **release v1.1.2** is cut on the merged tree
per the Cycle 60 pattern and the published copy probed
from the release tarball.

Recommendation on record (artifact + scorecard): do NOT
rewire the stack onto a blend now; the first honest test
arrives after the 2027 season, when the committed Steamer
2027 set can be scored against 2027 actuals on this same
paired design.

## Next

Slate item 3: the 2027 Cap Transition ledger as the lead
decision surface. Sportradar trial ~Nov 15 (PRICE-1
contracts-coverage check rides along). Cron wiring for
both refresh scripts is approved as slate item 6. Figure 9
disclosure remains an owner item. Final freeze release cut
before Dec 1.

---

# HANDOFF — Cycle 64: the 2027 Cap Transition ledger (slate item 3)

`data/cap_transition_2027.json` (builder `src/bml_cycle64.py`)
puts all 30 teams on one decision surface for the proposed
2027 system ($245.3M cap / $171.2M floor / 15% per-player
max = $36.795M), built from committed artifacts only:
cap scenarios (Cycle 22), forced-seller shed sets
(Cycle 30), Cot's labeled cross-check, Steamer 2027 WAR,
and the optimizer pool (Cycle 44).

- Primary basis (Spotrac payroll totals, 30/30 teams):
  7 OVER CAP ($358,157,578), 15 UNDER FLOOR
  ($807,838,582), 8 INSIDE THE BAND. Shed sets cover 6
  of 7 over-cap teams and clear their gaps (WAR cost:
  NYM 12.68, LAD 8.91, NYY 7.85, PHI 6.59, ATL 5.15,
  TOR 3.55). CHC (over by $4,019,956) shows "shed set
  not covered — payroll basis gap" — no contract rows,
  Spotrac page failed in Cycle 25.
- Under-floor rows: spend gap + equivalent signings at
  the pool median prior salary ($4,500,000, n = 199) —
  labeled arithmetic, not a recommendation.
- 15% check on Cot's `cb_2027_aav` (only committed AAV
  field): 8 contracts above $36,795,000 on 5 teams.
  Spotrac salary was deliberately not used (it flags
  deals whose AAV is below the maximum).
- Sensitivity: the Cot's second basis is the sum of
  published LRP-2027 dollar rows — a committed-contract
  SUBTOTAL, labeled everywhere, never a payroll:
  1 over / 6 in band / 23 under. 13 teams change status
  between bases; both readings are shown. Definition
  sensitivity (benefits, pre-arb pool) not modeled —
  no committed team-level figure separates them.
- Surface: the ledger panel leads Boardroom (rendered
  from the artifact, fail-closed if absent); not a
  figure (25), not a slide (15).
- Gate: 84 checks ALL PASS (3 new CAPLEDGER checks);
  spellcheck green; platform clean (17 rebuilt
  byte-identical, parity r = 0.889 / 201). Released as
  v1.1.3 per the Cycle 60 pattern.

## Next

Slate item 4: player-level health cards fused into the
FA shopping list. Slate item 5: reproducibility & claims
pack. Slate item 6: wire both refresh scripts into the
6h cron + visible "data as of" stamp. Sportradar trial
~Nov 15 (PRICE-1 contracts-coverage check rides along).
Final freeze release cut before Dec 1.

## Cycle 65 — December readiness checklist refresh (2026-11-02 ~20:13 PT)

Backlog item (g), refreshed — the Cycle 36 checklist below is still
the structure; this section brings its status current. Verified this
run on main 46a2ea44 (release v1.1.3, Cycle 64 ledger live).

### Platform + gate this run (no data PR — nothing moved)
- Spotrac probe: single GET, 403 (same block page). Logged, moved on.
  Salaries stay 24/30; forced-seller stays 6/7, CHC uncovered.
- Ingest: 25 datasets, 0 failures. Savant expected 651-673/season,
  bat-tracking 595-619, sprint 489-506 — all inside known-good bands.
  Transactions raw 120,553 (+198 on the watermark since the prior run,
  live free-agency period); raw-zone only, nothing curated from it.
- Curate: 19 tables, all contracts pass; build report byte-identical
  to committed (no curated PR). Warehouse from 19 tables. Parity
  r = 0.889 / 201 matched, exact. Gate: 84 checks ALL PASS.
  Spellcheck green. Dashboard rebuilds offline from committed
  snapshots with all 25 figures (Story 6 chapters default, Boardroom
  15 slides, Explorer all 25 by task).

### Checklist status, refreshed
- Freeze / final refresh: still targeted Nov 30; freeze tag still
  owed. v1.1.3 (main 46a2ea44) is the current published release,
  NOT the freeze tag.
- Demo package: 25 figures verified this run; Fig. 23 re-verified
  via gate (BIS canonical lines); one-pager regenerates clean from
  committed artifacts (only the generation timestamp differs —
  headlines 48.9 / 52.8 / 54.8, ledger 7 over / 15 under, salaries
  24/30, parity r = 0.889 / 201); TALKTRACK refs <= 25 per gate.
- Print pack: still day-before items — TALKTRACK printed, one-pager
  printed, README "Presenting in 5 minutes" loaded (three modes +
  Fig. 23 as the live-market closer, already in README).
- Known gaps carried, unchanged: salaries 24/30 (Spotrac 403;
  FanGraphs retry only on a 200 probe, under the Cycle 32
  reconcile-first guard); forced-seller 6/7; PRICE-1 blocked pending
  complete per-class signing terms (Sportradar trial ~Nov 15 —
  verify coverage against the workpaper's criteria first);
  persistence recompute on record from Cycle 63.

### Remaining build queue
- FA tracker ticker wiring (owner-directed 2026-11-02 evening;
  probe on record: StatsAPI transactions + freeAgents register,
  MLBTR/MLB.com/ESPN/Google News RSS probed live; BUZZ via Bluesky
  Jetstream reachability-only, stream unverified in sandbox;
  integrity rule: REPORTED/BUZZ never displays as a signing until
  StatsAPI transactions confirms it).
- Slate 4: player health cards in the FA shopping list. Slate 5:
  reproducibility & claims pack. Slate 6: wire both refresh scripts
  into the 6h cron + visible "data as of" stamp. Sportradar trial
  ~Nov 15. Final frozen-main release cut before Dec 1.

## Cycle 66 — FA tracker ticker: the probe stack wired into the dashboard (2026-11-03, owner-directed CarpeData)

The probe sweep (~/workspace/hardball/TRACKER_PROBE_2026-11-02.md,
probed live 2026-11-02 18:03–18:15 PST) is now the dashboard's
front wire panel. Placement: front of Story mode (the default
view), ahead of Chapter 1 — a wire panel, not a chapter (Story
stays 6 chapters) and not a figure (count stays 25).

### The pull: src/pull_tracker_ticker.py -> data/tracker_ticker_2026.json

One pull, all kept sources, polite rates (0.4s between calls),
fail-closed per source (a block is logged and skipped, never
retried around). Pulled 2026-11-03 ~06:07 UTC. Items carry
{pulled_at, lane, source, title, link, player, team,
statsapi_transaction_id (CONFIRMED only), source_pubdate,
move_type (CONFIRMED only)}.

CONFIRMED (SIGNED lane): MLB StatsAPI transactions, 7-day window
2026-10-27..2026-11-03, FA codes only (SFA / DFA / TR / REL /
CLW / OUT / DES — winter-ball ASG assignments excluded):
705 rows fetched, 321 kept. Breakdown: DFA declared free agency
192, OUT 49, REL 28, CLW 20, TR 15, DES 9, SFA signed 9. One
FA-code row (transaction id 947748, TR) carried no description
and no player name; it is skipped and counted in the
per-source note, not rendered as an empty bullet — the gate
caught it on the first build. Class register
(freeAgents?season=2026) returned 246 players and is recorded
as the state table only; moves come from transactions, never
from the register. ?season=2027 returns empty, as probed.

REPORTED lane (newest 200 stored by pubdate): ESPN news 6
fetched / 1 kept (FA-keyword filtered, unofficial endpoint);
ESPN transactions page 1 of 134, 25 kept (cross-check only);
MLB Trade Rumors main 15/7 + per-team feeds for the top 6
teams by class count (SD, CHC, TEX, ARI, ATL, TOR) 15 each,
6/8/2/5/4/3 kept (FA-keyword filtered); MLBTR per-player
feeds for the top 12 by Steamer WAR, 15 each, 14–15 kept
(channel title verified to carry the player's last name);
MLB.com per-team RSS for the same 6 teams, 25 each, 4/2/0/1/
1/1 kept (FA-keyword filtered; Arizona's feed titles itself
"D-backs News", carried as an explicit fragment exception);
RotoWire 5/5 (free-tier cap, as observed); Google News RSS
generic "MLB free agency when:1d" 100/99 + per-player
queries (top 12, "when:3d") 11–100 each — links are Google
redirects, deduped on title+source, never on the redirect
URL. Caps recorded in the artifact: 12 players, 6 teams,
200 REPORTED stored, 10 BUZZ stored.

BUZZ lane: Bluesky Jetstream ONLY. Verdict: the stream read
did NOT complete in this runtime — the stdlib WebSocket
client's read timed out on both pull runs (TimeoutError, 0
events), and a standalone probe session was lost to runtime
instability before returning a result, so it contributes no
verdict either way. The lane therefore ships EMPTY with a
plain label ("BUZZ awaits stream verification ... ships
empty rather than filled with substitutes"). Never faked,
never substituted: AppView search (403), Reddit (403),
Mastodon (0 signal) stay dropped, as do GDELT (429),
NewsAPI/GNews (delayed, dev-only) and X (no free read tier).

### The panel: _ticker_panel_html, front of Story

Renders ONLY from the committed artifact; absent the artifact
it is omitted entirely (fail closed). Three lanes rendered
distinctly: SIGNED — confirmed by MLB StatsAPI (each item
carries its exact move type, so a DFA declaration reads as a
declaration, never as a signing); REPORTED — newswire and
rumor; BUZZ — social (empty with the label above). The
panel states the integrity rule in one line: "An item
becomes SIGNED only when the MLB StatsAPI transactions
feed carries it. REPORTED and BUZZ items are never labeled
signings." Rendered: newest 12 SIGNED, 20 REPORTED, 10 BUZZ.

### Verification

- Gate: 87 checks ALL PASS (84 + 3 new TICKER checks:
  artifact consistency incl. every SIGNED item carrying a
  StatsAPI transaction id and no REPORTED/BUZZ item carrying
  one; panel leads Story before Chapter 1 with all three lane
  labels + integrity line + pull date; SIGNED discipline with
  exact move types rendered). Freshness note: the gate pins
  pulled_at present-and-parseable, NOT "today" — a "today"
  pin would fail every later cron gate run on a committed
  artifact, and the ticker pull is not yet a cron step (see
  proposed diff below); the panel itself displays the pull
  date for the reader.
- Spellcheck green. Note: the spellcheck gate now excludes
  the ticker div from its scan (src/spellcheck_gate.py) —
  wire headlines are quoted third-party copy, verified by
  source, not by spelling; the gate still checks all of our
  own prose elsewhere. Without the exclusion, every player
  surname on the wire would need a whitelist entry.
- Platform clean: curate rebuilt 17 tables byte-identical,
  2 skipped on absent raw with committed parquets standing
  (the Cycle 64 pattern); all 19 parquets byte-identical to
  main; warehouse rebuilt from 19 tables; parity r = 0.889 /
  201 matched. Dashboard rebuilt with the lake present:
  25 figures, none missing.
- Release: v1.1.4 per the Cycle 60 pattern (release commit
  atop main carrying only the rebuilt
  dashboard/hardball_demo.html; lightweight tag; GitHub
  release via API; no asset uploads). Published file read
  back from the release tarball and probed (ticker title,
  all three lane labels, 25 figures, live-IL panel,
  benchmark panel, ledger panel, evidence footnote).

## Next

- PROPOSED (owner tap required — NOT applied in this cycle):
  add the ticker pull to the 6-hourly build, alongside the
  already-owner-approved item-6 wiring of the two refresh
  scripts. Exact diff to the cron job body:
    ... existing steps (Spotrac probe, platform, backlog item) ...
    + # Cycle 66 ticker (proposed): keep the wire current
    + python3 src/pull_tracker_ticker.py
    + python3 src/dashboard_p6.py        # rebuild with the lake present
    + python3 src/verify_data.py         # gate must pass before any push
    + # commit data/tracker_ticker_2026.json + dashboard/hardball_demo.html
    + # only if the gate passes; on gate failure, last good
    + # dashboard stays live and the failure is reported
  The parent presents this; it is not applied here.
- Slate 5 DONE (Cycle 68, below). Slate 6: wire both refresh scripts into the 6h
  cron + visible "data as of" stamp. Sportradar trial ~Nov 15.
  Final frozen-main release cut before Dec 1.

## Cycle 67 — player health cards in the FA shopping list (slate item 4)

The shopping list stops ranking by headline WAR alone. Every one
of the 251 free agents now carries a health card in the Explorer
"Shop the FA Class" group: measured availability, delivered-WAR
expectation, risk flag, current-IL status, anchor price with
delivered WAR per $10M, and an evidence link. Panel, not a
figure (count stays 25); Explorer only (Story stays 6 chapters,
Boardroom stays 15 slides).

### The cards: src/bml_cycle67.py -> data/fa_health_cards_2027.json

- Measured availability: the player's 2025-26 IL days = the sum
  of committed days_in_season across his stints in curated
  fact_il_stints; availability = max(0, 1 - days/364), 364 the
  repo's own Cycle 9 denominator (2 x 182 days). Checked: for
  every FA player the summed days never exceed the calendar-day
  union of his stint ranges, so overlaps do not inflate the sum.
  3 players sum above 364 (Rendon, Jimenez, Graterol) and are
  floored at 0. Coverage: 166 measured / 65 no IL record /
  20 not matched (no player_id in the shopping file — the
  NPB posted class plus Spotrac name-parsing fragments like
  "Robert Jr." — no name-only join was attempted, because a
  name-only join risks false attribution). No-record players
  read "no IL record in committed data", never 100%.
- Delivered-WAR expectation: the Cycle 56 formula at player
  level. UNC-2 simulated rosters with pool availability draws
  plus residual draws; the player-level point estimate replaces
  the draws with their centers: the player's own measured
  factor where one exists, else the UNC-2 pool mean for his
  group (hitters 0.912, pitchers 0.807), and the measured mean
  residuals (OBP +0.0008, SLG -0.0078, ERA +0.078) converted
  with the Cycle 48 slopes and Steamer's own fitted runs-to-WAR
  slopes at delivered volume (Steamer 2027 PA/IP by xMLBAMID;
  all 231 players with Steamer WAR have a PA/IP row).
  Per-player intervals are NOT derived: a pool-draw interval
  would present pool variance as player risk, so intervals stay
  scenario-level only (Cycle 56). Stated in the artifact.
- Risk flag: measured availability below the UNC-2 pool p25
  for the group (hitters 0.890, pitchers 0.629). 76 flagged
  (45 of 65 measured hitters, 31 of 101 measured pitchers).
  Selection note, stated in the panel: the comparison pool
  includes players with no IL time while the flagged set is
  conditioned on having IL history, so the flag fires often —
  it marks below-quartile availability, not a prediction of
  future injury.
- Evidence link: the dominant injury (most 2025-26 IL days)
  classified by keyword only — 73 linked to a lane (UCL 29,
  muscle 41, tendon 2, workload 1), 178 to the page top.
  docs/EVIDENCE.html gained the four lane anchors (id only;
  headings, counts, PMIDs untouched — the Cycle 57 gate checks
  still pass). Current IL: exact-name match against curated
  fact_il_current, 13 matches, no duplicate names, matching
  the Cycle 51 count.
- Prices stay anchors (Cycle 61 left them untouched):
  delivered WAR per $10M is arithmetic on the same prior AAV.

### The difference it makes (top 5)

- By headline WAR: Skubal 5.66, Contreras 4.29, Rasmussen
  3.74, Trevor Rogers 3.04, Sonny Gray 2.97.
- By delivered WAR: Skubal 4.86, Contreras 3.79, Rasmussen
  2.91, Sonny Gray 2.73, Luis Arraez 2.55. Rogers falls to
  6th (2.41) — 64 IL days at 0.82 availability on a 3.04
  headline. That drop is the buying tool working.
- Example card, quoted exactly: Garrett Whitlock (RP, BOS) —
  headline 0.83 WAR, 34 IL days, availability 0.91, delivered
  0.71 WAR; dominant injury "Right elbow inflammation"
  (UCL & elbow lane); currently Out with a leg fracture,
  return 2027-02-01 (live snapshot 2026-11-02).

### Verification

- Gate: 89 checks ALL PASS (87 + 2 new HEALTH checks:
  artifact consistency with availability + delivered WAR
  recomputed from artifact fields and delivered ranks 1..231
  unique and ordered; panel renders in Explorer with the
  title, Delivered WAR column, top delivered name and a lane
  link, and not in Story; evidence page carries all four lane
  anchors). Spellcheck green — 161 player-name tokens and
  position codes added to the whitelist, each verified
  against data/fa_shopping_2027.json (accented names split at
  the accent: berr = Berrios, garc = Garcia, nchez = Sanchez,
  rez = Perez, rquez = Marquez).
- Platform clean: curate rebuilt 17 tables byte-identical, 2
  skipped on absent raw with committed parquets standing (the
  Cycle 64 pattern); all 19 parquets byte-identical to main;
  warehouse rebuilt from 19 tables; parity r = 0.889 / 201.
  Dashboard rebuilt with the lake present: 25 figures, none
  missing; health table renders 251 rows + header.
- Release: v1.1.5 per the Cycle 60 pattern (release commit
  atop main carrying only the rebuilt
  dashboard/hardball_demo.html; lightweight tag; GitHub
  release via API; no asset uploads). Published file read
  back from the release tarball and probed (card section
  title, delivered-WAR field, evidence link, 25 figures,
  ticker panel, ledger panel, benchmark panel, footnote).

## Cycle 68 — reproducibility & claims pack (slate item 5)

The audit trail a league office can check. Assembly + verification,
no new analysis: every material claim the demo makes now sits in one
register with its artifact, and every figure and panel is traced to
its artifact with headline values recomputed at build time.

### The pack: src/bml_cycle68.py -> data/claims_register.json + data/figure_trace_2027.json + docs/REPRODUCIBILITY.html

- Register counts: **16 SUPPORTED, 7 NOT SUPPORTED, 3 RETRACTED,
  1 open item**. A claim is SUPPORTED only if a committed artifact
  carries the numbers; a claim that failed its own test is NOT
  SUPPORTED, not softened.
- Supported includes the optimizer headlines (48.9/52.8/54.8, gap
  0.0), the ±20% ranges (45.0-53.2 / 48.5-55.5 / 50.4-55.9), the
  UNC-2 intervals (33.0-46.9 / 36.0-50.7 / 37.6-52.4), the HS-2 live
  claim (persistent + cap-efficient + low-variance, NOT proven
  undervaluation), Marcel-Steamer agreement (r=0.889), held-out
  Marcel accuracy (OBP MAE 0.0237 vs naive 0.0265, n=80), the
  salary basis (24/30 Spotrac rows + Cot's cross-check, 13/30
  change status between bases), health cards (166/65/20), the
  posted class with no translation factor, the ticker lanes with
  the integrity rule, the evidence counts as run, and the live-IL
  picture (13 of 251).
- Not supported, stated plainly: prior-AAV anchors as predicted
  prices (Cycle 61, training data absent), the Steamer+Marcel
  blend (Cycle 62, unscorable), Steamer out-of-sample accuracy
  (not scoreable), Savant trait adjustments (worse out-of-sample),
  BRef salary corroboration (71.1% < 80% bar), player-level salary
  completeness for all 30 teams (24/30), and the proposed cap
  system as certain law (it is a proposal; CBA expires Dec 1).
- Retracted, stated plainly, not deleted: (R01) the team-wins
  R-squared 0.80 claim (Cycles 18-19 — favorable 2-year window;
  full-panel refit R-squared 0.534, lagged OOS MAE 14.05 vs naive
  9.76); (R02) availability-capped point forecasts (UNC-1, Cycle
  54 — pooled MAE 46.2 -> 61.1 capped; the cap is a downside
  adjustment only); (R03) the OBP persistence figure as first
  published (Cycle 39 recomputation; Cycle 44 shipped the
  corrected stack, PR #21 itself never merged).
- Open item O01 (NOT decided here): Figure 9's "Model-projected
  wins" title presents in-sample fitted values without an
  in-sample/diagnostic label — still the owner's call. The trace
  verifies Figure 9's artifact and panel agree; it does not
  endorse the title.
- Trace: **25/25 figures + 8/8 panels verified** — headline values
  recomputed from artifacts and matched against the built HTML
  (FIG-QA method, Cycle 53). Two build-time catches, both fixed
  before shipping: the register's evidence parser split artifact
  strings on "+" and broke on parenthetical section notes
  (fixed with a path regex, in the builder and the gate), and the
  evidence-footnote marker assumed the footnote title was one
  literal string when it renders as a link (checked as its two
  halves). No figure trace failed; nothing was papered over.
- The surface: a "Claims & reproducibility" panel closes Explorer
  (appendix, not a figure — count stays 25; Story stays 6
  chapters, Boardroom stays 15 slides), rendering the counts, the
  three retracted claims in full, and the link to the pack page.
  The panel fails closed: absent the pack artifacts it renders
  nothing, so the dashboard build runs in two passes (build,
  pack, rebuild, re-pack).

### Verification

- Gate: **93 checks ALL PASS** (89 + 4 new Cycle 68 checks:
  register completeness + evidence existence + counts reconcile;
  trace coverage 25 + 8, all verified; panel renders in Explorer
  and not in Story; pack page carries the counts and retracted
  claims). Spellcheck green.
- Platform clean: curate rebuilt 17 tables, contracts pass, 2
  skipped on absent raw with committed parquets standing (the
  Cycle 64/67 pattern — data/curated/_build_report.json restored
  from main so the committed report does not regress); all 19
  parquets byte-identical to main; warehouse rebuilt from 19
  tables; parity r = 0.889 / 201. Dashboard rebuilt with the lake
  present: 25 figures, none missing. kpi.py md5-verified pristine.
- Release: v1.1.6 per the Cycle 60 pattern (release commit atop
  main carrying only the rebuilt dashboard/hardball_demo.html;
  lightweight tag; GitHub release via API; no asset uploads).
  Published file read back from the release tarball and probed
  (claims panel title, retracted-claims string, 25 figures,
  ticker panel, ledger panel, benchmark panel, health cards,
  footnote).

## Cycle 69 — claims-pack open item O01 resolved (2026-11-03)

Bookkeeping only: the Cycle 68 pack's one open item is closed, not
decided around. Figure 9's in-sample label shipped in the owner's
lane (commit 4219e079); the register now records O01 as RESOLVED
(16 SUPPORTED / 7 NOT SUPPORTED / 3 RETRACTED unchanged, 0 open,
1 resolved), the Figure 9 trace headline updated, the pack page
regenerated with a Resolved items section, and the dashboard panel
paragraph replaced. Gate 93 checks ALL PASS (checks updated, none
added); spellcheck green; platform clean (ingest 25/0 failures,
curated byte-identical, parity r = 0.889 / 201); dashboard rebuilt
(25 figures). Spotrac 403 + FanGraphs 403 (single probes, stopped
per rule) — salaries stay 24/30, forced-seller 6/7. Release v1.1.7
per the Cycle 60 pattern. Next: Sportradar trial ~mid-Nov; final
frozen-main release cut before Dec 1.

## Cycle 70 — live cadence wired + "data as of" stamp (slate item 6, final)

The slate closes. Two parts:

- Stamp: the dashboard crest now carries one line — "Data as of
  Nov 3, 2026 · tracker Nov 3 · injured list Nov 2 · evidence
  Nov 2" — each date read at build time from its own committed
  feed artifact (data/tracker_ticker_2026.json pulled_at,
  data/il_current_live.json pulled_at,
  data/evidence_surveillance.json run_date); the head date is the
  newest of the three. No date is typed by hand; a missing
  artifact renders "not yet pulled" for that feed. New gate check
  (Cycle 70) recomputes the exact stamp string from the artifacts
  and requires it verbatim in the built HTML, so the stamp cannot
  drift from the feeds it names.
- Cadence: cron hardball-247-build gained step 2b — each run now
  executes src/refresh_live_feeds.py (20h watermark + 200-credit
  monthly Fastball cap, both enforced inside the script),
  src/pull_evidence_surveillance.py (6-day guard; docs/EVIDENCE.html
  regenerated by src/make_evidence_page.py, and if that build
  fails closed on an unwritten Finding line the run keeps the
  previous evidence artifact and reports it), and
  src/pull_tracker_ticker.py — the Cycle 66 proposed diff,
  applied on the owner's "finish" direction 2026-11-03.
  Refreshed artifacts + a rebuilt dashboard are PR'd and merged
  only when the gate passes; on failure nothing is committed and
  the last good dashboard stays live.

- Gate: 94 checks ALL PASS (93 + the Cycle 70 stamp check).
  Platform: warehouse rebuilt from 19 curated tables, parity
  r = 0.889 / 201. Dashboard rebuilt with the lake present:
  25 figures, stamp rendered as above. kpi.py md5-verified
  pristine (snapshot-forcing edit is scratch-only, never pushed).
- Release: v1.1.8 per the Cycle 60 pattern (release commit atop
  main carrying only the rebuilt dashboard/hardball_demo.html;
  lightweight tag; GitHub release via API; no asset uploads).
  Published file read back from the release tree and probed
  (stamp, 25 figures, ticker panel, ledger panel, health cards,
  claims panel, evidence footnote).
- Slate status: all six items shipped (61 PRICE-1 closed
  negative, 62 BLEND-1 not adopted + benchmark panel, 64 cap
  ledger, 67 health cards, 68 claims pack, 70 live cadence).
  Remaining before Dec 1: Sportradar trial ~Nov 15 (salaries
  24/30, forced-seller 6/7, CHC shed set uncovered until then);
  final frozen-main release cut.

## Cycle 72 — tracker refresh + Cycle 24 drift re-run (2026-11-03, 24/7 job)

- Tracker ticker refreshed (pulled 2026-11-03 16:15 UTC, window
  Oct 27–Nov 3): 535 items (335 SIGNED via StatsAPI transactions,
  200 REPORTED); Google News 503 + Bluesky timeout failed closed.
  Live feeds otherwise SKIP on their guards (20h watermark, 6d
  evidence guard) — normal, not failures. Spotrac probe still 403;
  salaries 24/30.
- Platform green: ingest 25/25, curate 19 tables, parity r = 0.889 /
  201 matched. Cycle 24 pitcher backtest re-run: artifact
  identical — no drift.
- Dashboard rebuilt from committed snapshots; crest stamp "Data as
  of Nov 3, 2026 · tracker Nov 3 · injured list Nov 2 · evidence
  Nov 2". Gate ALL PASS + spellcheck green; PR merged.
- Remaining before Dec 1: Sportradar trial ~Nov 15 (salaries 24/30,
  forced-seller 6/7); final frozen-main release cut.

## Cycle 75 — bat-speed exhibit under Figure 19 (2026-11-03)

The Cycle 73 TODO handoff, executed as product framing only. A
companion exhibit now sits directly under Figure 19 in Explorer:
the 2026 bat-speed distribution and the trait's year-to-year
stability, labeled context only. Bat speed stays OUT of every
projection — Cycle 20 tested it as an adjustment and dropped it
(claim N04, NOT SUPPORTED); the exhibit quotes the register claim
verbatim and carries the NOT SUPPORTED status on its face.
Figure count stays 25; Story stays 6 chapters; no headline
anywhere changes.

- Artifact: src/bml_cycle75.py -> data/bat_speed_exhibit_2027.json.
  Every printed number is computed from the committed Savant
  bat-tracking boards; no hand-entered values (the N04 text is
  copied from the register by the script).
- Corroboration (owner directive: all math validated, two
  sources): the repo boards reconcile EXACTLY against the
  platform raw cache — 595/619/619 players, avg_bat_speed and
  swing_length identical for every player, all three years.
  Stability computed two ways: per transition r = 0.908
  (2024->2025, n = 490) and 0.905 (2025->2026, n = 487); pooled
  r = 0.907 (977 pairs). The Cycle 20 committed 0.921 reconciles
  as a qualification difference: with a >=250-competitive-swing
  minimum in both years the same boards give 0.922 / 0.929.
- Team lens CUT: no committed player-to-team join covers the
  board (fact_stat_lines 2026 hitting covers 135 of 619, a
  selected subset; the Steamer 2027 file carries no team for any
  board player). The panel states this in one line instead of
  printing a selected-sample split. Attack angle / swing tilt
  are not in the committed data and are not shown.
- Gate: 97 checks ALL PASS (94 + 3 new Cycle 75 checks: the
  artifact recomputes from the boards in the gate itself; the
  panel renders in Explorer only with the N04 label and the
  verbatim register claim; no projection-claim wording).
  Spellcheck green. Platform: curate 19 tables, parity
  r = 0.889 / 201.
- Release: per the Cycle 60 pattern (release commit atop main
  carrying only the rebuilt dashboard; lightweight tag taken at
  cut time; GitHub release via API). Published file read back
  from the tag tree and probed (exhibit + N04 label, 25 figures,
  crest stamp).

## Cycle 74 — salary completion: Cot's full parse, reconciliation, CHC shed set (2026-11-03)

- The salary gap closed on a second basis (owner's "hackathon"
  framing; Sportradar trial declined 2026-11-03, superseded by this
  cycle). src/bml_cycle74.py parses ALL 30 cached Cot's sheets into
  data/salaries_cots_full_2027.json: 2,240 rows (players + the
  sheets' non-player charges), 2026 LRP dollars, 2027 LRP figure
  where printed, status marker (A1–A4 / FA / opt) where the sheet
  prints a marker instead — never an invented figure. The 237
  figure rows are identical to the Cycle 44 dataset, and the parse
  cross-validates against the independent Cycle 41 parse to the
  dollar on every team. Sheet-internal residuals are reported, not
  adjusted: 24/30 sheets reconcile within $100; the six larger ones
  (ATH, BOS, CLE, COL −$7.75M, STL, TB) are the sheets' own —
  printed totals net out rows for mid-season-traded players.
- Reconciliation (data/salary_reconciliation_2027.json, recomputed
  from the raw sheets inside the build): Cot's printed totals vs
  Spotrac totals — mean abs diff 0.63%, worst SD +3.07%, 26/30
  within 2%. Three-basis shed sets: NYM/NYY/PHI/TOR/ATL pick
  identical players on Spotrac, Cot's LRP 2027 and Cot's CBT AAV;
  LAD agrees on Spotrac + AAV (Ohtani+Tucker) and differs on LRP
  (Glasnow+Tucker) — Ohtani's deferral at present value vs nominal.
  USA TODAY's final-2026 LRD list corroborates as a different
  basis + later snapshot (context only, never merged): the five
  named anchors agree within ~0.5%; largest full-list deviations
  WSH −11.2%, MIN −5.4%, CHW −5.2% (deadline sellers — reported,
  not reconciled away). Player-level: Guerrero Jr. $40,214,286
  matches USA TODAY's published figure to the dollar. Summary in
  docs/CARPE_SCORECARD.md.
- CHC shed set filled, source-labeled (basis cots_lrp_2027): Alex
  Bregman, $29,527,000 — the sheet itself confirms he is CHC's
  largest 2027 guarantee (Swanson $28,000,000 second); gap
  arithmetic pinned in the artifact: $249,319,956 − $245,300,000 =
  $4,019,956. Forced-seller coverage 7/7; the other six sets are
  byte-identical. Cap ledger regenerated — only CHC's action
  changed (covered; payroll after shed $219,792,956; Bregman 3.26
  Steamer WAR). Claim S17 added (SUPPORTED — register now 17/7/3,
  0 open, 1 resolved); N06's evidence corrected, claim stands NOT
  SUPPORTED (no single-basis per-player file covers all 30 teams).
- Dashboard: Figure 11 renders CHC (bar, hover and Boardroom
  ledger all carry the Cot's basis label); the coverage copy
  states both bases with the reconciliation headline. Figure
  count stays 25.
- Platform: curate 20 tables (new fact_salaries_cots_full, 2,240
  rows), contracts pass; parity r = 0.889 / 201.
- Gate: 102 checks ALL PASS (97 + 5 new CYCLE74 checks recompute
  the parse identity, the reconciliation, the three-basis sets,
  the CHC set and the USA TODAY block from the committed salary
  files) + spellcheck green.
- Coordination: Cycle 75 landed on main mid-work (7cdd4bb9,
  release v1.1.9); this branch was rebuilt on the new head and the
  full chain re-verified there. Release: v1.1.10 per the Cycle 60
  pattern.
- Remaining before Dec 1: final frozen-main release cut. The
  standing "Sportradar trial ~Nov 15" item is CLOSED — declined
  by the owner; the gap it was meant to close is closed above.

## Cycle 76 — visual redesign: MLB colors + Rays secondary (2026-11-03)

Presentation only (Cycle 33 rule): same data, same numbers, same
claims. Owner-directed palette, superseding the earlier brass
draft: MLB Navy #041E42 ground, MLB Red #BF0D3E the single accent
(crest rule, chapter rules, cap-line/negative semantics), white
text, Rays Navy #092C5C panels, Columbia Blue #8FBCE6 as dim text
+ links + the "other" group color, Rays Gold #F5D130 sparingly
(data-as-of stamp, section/slide numerals, the posting-fee line).
No #c9a227 anywhere in the build — gate-checked.

- Tokens at :root in the page template; component CSS uses var()
  throughout. Type: Google Fonts (Fraunces display, Inter body,
  IBM Plex Mono numerals) with local fallbacks; figure titles set
  in Fraunces via one central Plotly template applied in _number()
  (transparent grounds, white-8% gridlines, Columbia ticks/legend,
  ink hover labels, in-family colorway). Trace colors changed only
  where they carry group semantics: #1b5e20 -> #43b581,
  #e65100 -> #e08a3c, #1565c0 -> #8FBCE6, cap red #d50032 ->
  #BF0D3E; the color key swatches carry the same hexes (gate
  asserts key == traces). Two figure subtitles that named the old
  animation gold now say "Green" — the winning-cheap bubbles and
  radar profile are green, matching the key.
- Data integrity: every figure's trace data arrays (x/y/text/
  customdata) extracted from the pre- and post-redesign builds —
  identical on all 25 figures. Boardroom print forces light
  slides + ink text (incl. SVG text fill) under @media print.
- WCAG contrasts computed from the tokens: white/#041E42 16.54,
  #8FBCE6/#041E42 8.27, #F5D130/#041E42 11.06, white/#092C5C
  13.76, #8FBCE6/#092C5C 6.88, #F5D130/#092C5C 9.20, white/
  #BF0D3E 6.28 — all text pairs pass 4.5:1. MLB Red on navy
  (2.63) appears only as non-text chrome (rules, borders); text
  on red is white.
- Gate: 107 checks ALL PASS (102 + 5 new Cycle 76 checks: token
  palette, brass/old-bg absence, key == trace hexes, contrast
  minimums recomputed in-gate, type wiring). No existing check
  was edited — none pinned an old presentational string.
  Spellcheck green; platform parity r = 0.889 / 201, warehouse
  20 tables. Dashboard 5,645,837 -> 5,402,333 bytes.
- Release: v1.1.11 per the Cycle 60 pattern. Remaining before
  Dec 1: final frozen-main release cut (its dashboard-footer
  Sportradar line edit rides along there).

## Cycle 77 — live refresh (Nov 3) + gate alignment to the owner's polish lane (2026-11-03)

Spotrac probe: 403 (browser UA, single GET) — logged, moved on, per
standing rule. The salary gap stays closed on the Cycle 74 Cot's basis;
no new Spotrac pull was attempted around the block.

Live refresh (Cycle 70 cadence): FastballAPI + Statyx pulled Nov 3
(20h watermark passed; 16 Fastball credits MTD, cap 200). IL union
196 -> 182 (Fastball 190 -> 175, Statyx page 50 -> 16, overlap 9);
FA-pool movement since Nov 2: 1 new IL, 7 returned, 3 status
changes. Tracker re-pulled Nov 3 22:23 UTC: 535 -> 562 items
(StatsAPI transactions ok, 362 SIGNED kept; MLBTR/MLB.com/ESPN/
RotoWire ok; Google News 503 across all queries — logged and
skipped per source, never routed around; Bluesky Jetstream timed
out, so BUZZ ships empty per design). Evidence: SKIP (artifact
Nov 2, inside the 6-day guard). Crest stamp now "Data as of
Nov 3, 2026 · tracker Nov 3 · injured list Nov 3 · evidence Nov 2".
Manifest committed feed-only (16 lines); this run's platform-ingest
entries reference local-only raw files and were left out of the
committed ledger.

Gate alignment (mechanical, owner's own wording): the owner's
parallel-lane polish commit f85f308f5b retitled three panels
without updating the gate, so a fresh build from main head failed
3 title-string checks while every other assertion in those checks
passed and the committed dashboard still carried the old titles.
This cycle adopts the owner's titles verbatim in verify_data.py
(ticker "Free-agent market activity", health-cards
"Availability-adjusted player value: measured contribution after
availability", Fig 22 "Free-agent decision lens: projected
contribution versus market cost") and whitelists the owner's Nov 3
README/About vocabulary in spellcheck_gate.py (auditable,
workflow, Bluesky, hashtag, LinkedIn, PFAC, QA, http, txt, venv,
i'm — each verified in context; the pre-existing spellcheck
failure on the committed dashboard is likewise from that lane,
not from this refresh). No other gate assertion changed.
Gate: ALL PASS; spellcheck green; platform clean (ingest 25/0,
curate 20 tables, parity r = 0.889 / 201).

Backlog (step 4h — items a–g all done or superseded by the owner's
lane): Cycle 24 pitcher backtest re-run — artifact identical, no
drift (pooled A MAE ERA 0.744 / WHIP 0.122, unchanged).

Remaining before Dec 1: final frozen-main release cut (its
dashboard-footer Sportradar line edit rides along there); the
owner's open PR #56 (badge removal) is his lane's, untouched.
- Shipped as PR #57 (toby/cycle77-live-refresh), merged when gate +
  rebuild verified.

## Cycle 78 — Figure 25 (optimizer audit) restored to Explorer (2026-11-03, owner-directed)

Diagnosis: the panel was never removed from src/dashboard_p6.py.
The committed dashboard had been built without data/mlb_lake.db,
so the pitching panel returned None, dropped out of numbering,
and Figures 14–25 each shifted down one in the artifact: the
optimizer chart shipped as "Figure 24" in the wrong Explorer
group while the Figure 25 slot showed the lake-fallback text.
Fix: rebuilt dashboard/hardball_demo.html from current main
source WITH the lake (KPI forced to committed snapshots); no
source or data change. Verified by DOM/data checks (the
verify_data.py gate crash against the new build is a separate
pending alignment item): Explorer 24 → 25 unique panels,
data-figure="25" restored with values recomputed from
data/optimizer_comparison_2027.json (+6.9/+7.1/+2.5 WAR),
Story/Boardroom memberships unchanged, stamp intact.
Note for Codex / the dashboard lane is in the PR body and on
PR #58: builds that get committed must run with the lake
present — a lake-less build renumbers silently.

## Cycle 80 — December readiness checklist refresh (2026-11-04 ~02:15 PT, 24/7 job)

Backlog item (g), refreshed — the Cycle 36 checklist above is still
the structure; this section brings its status current. Verified this
run on main 84e50bda (PR #84 merged: Figure 14 evidence link
relabeled; release v1.1.12 current, Cycle 78's restore).

### Platform + gate this run (ticker + dashboard + gate fix shipped)
- Spotrac probe: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the
  Spotrac basis (927 rows, 6 team failures ARI/BOS/CHC/MIL/TB/TEX
  in the artifact metadata) + Cot's second basis (Cycle 74, 7/7
  shed sets). FanGraphs not re-probed: item (c) stays failed-closed
  per its guard; retry only on a 200 probe.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull Nov 3 22:23 UTC,
  11.9h old, < 20h watermark); pull_evidence_surveillance.py SKIP
  (artifact Nov 2, 2d old, < 6d guard). Both SKIP lines are normal
  outcomes, not failures. No new evidence artifact, so
  docs/EVIDENCE.html is untouched.
- TICKER: pull_tracker_ticker.py OK — window still
  2026-10-28..2026-11-04 (today is Nov 4), SIGNED 367 -> 369,
  REPORTED 200, BUZZ 0, total 567 -> 569. The 2 new SIGNED items
  are Nov 3 winter-ball releases (Navegantes del Magallanes RHP
  Jesus Mosquera, RHP Jose Ramirez, both REL via StatsAPI
  transactions); nothing removed. Bluesky Jetstream handshake 403
  is the script's designed fail-closed behavior (logged, skipped,
  never routed around); Google News answered 200 this run after
  Cycle 79's 503s, so REPORTED churned on fresh links under the
  200 cap — the lanes shipped exactly as the script records.
- PLATFORM: ingest_platform.py 25 datasets, 0 failures; Savant
  expected 651-673/season, bat-tracking 595-619, sprint 489-506 —
  all inside the known-good bands, no silent-source move.
  Transactions raw 121,411 (+2, the two releases above; raw-zone
  only). curate.py 20 tables, all contracts pass; counts match the
  Cycle 79 run exactly, so no curated table changed materially and
  none is shipped. build_warehouse.py rebuilt; query.py
  benchmark_parity r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1 (committed snapshots forced). Census:
  25 unique figures, zero data-figure-missing markers; Story 6
  chapters (gate-verified), Boardroom <=15 slides, Explorer all 25
  by task, 8 percentile player cards. Crest stamp now reads "Data
  as of Nov 4, 2026 · tracker Nov 4 · injured list Nov 3 ·
  evidence Nov 2". dashboard/hardball_demo.html kept as a
  byte-identical copy of dashboard/index.html (the #81 sync
  invariant).
- GATE FIX (mechanical, in this PR): the rebuilt dashboard failed
  verify_data.py on exactly one check — the Figure 14 evidence
  footnote. Cause was on main, not in this rebuild: PR #84
  relabeled the footnote ("Figure 14 evidence: What the evidence
  says now — PubMed research on injury recovery and prevention")
  without updating the gate's expected strings, so the gate still
  demanded the old wording. Fix aligns the three expected strings
  in src/verify_data.py to the shipped #84 wording; the footnote's
  link, all four lane counts (157/426/404/119 found), and its
  position between Figures 14 and 15 were verified present before
  the edit. No claim, figure, or data changed. Gate now 107 checks
  ALL PASS. Spellcheck green.

### Checklist status, refreshed
- Freeze / final refresh: still targeted Nov 30; freeze tag still
  owed. v1.1.12 (Cycle 78 restore) is the current published
  release, NOT the freeze tag.
- Demo package: 25 figures verified this run; Fig. 23 re-verified
  via gate (BIS canonical lines); one-pager and talk-track
  unchanged this run (gate checks talk-track refs <= 25);
  README "Presenting in 5 minutes" current (Cycle 79).
- Print pack: still day-before items — TALKTRACK printed,
  one-pager printed, README "Presenting in 5 minutes" loaded.
- Known gaps carried, unchanged: salaries 24/30 (Spotrac 403;
  FanGraphs retry only on a 200 probe, under the Cycle 32
  reconcile-first guard); forced-seller 6/7 on the Spotrac basis,
  7/7 on Cot's second basis; PRICE-1 blocked pending complete
  per-class signing terms (Sportradar trial DECLINED by the owner
  2026-11-03 — do not raise it again; the dashboard footer line
  that still says the trial starts mid-November is corrected at
  the freeze cut, per the Cycle 77 note); persistence recompute
  on record from Cycle 63.
- Open PRs left untouched: #57 (Cycle 77 live refresh, predates
  the Cycle 78 restore and the current main) and #58
  (parallel-lane ticker trigger).

### Remaining build queue
- Final frozen-main release cut before Dec 1 (with the Sportradar
  footer-line correction riding along). After Dec 1 the deadline
  guard fires and this job goes silent.

## Cycle 81 — tracker refresh + December checklist refresh (2026-11-04 ~08:15 PT, 24/7 job)

### Base
- Main b11702eb (Cycle 80 merge) unmoved at run start. Note on
  method: the API tarball download 404'd on the codeload redirect
  (surrogate bearer does not carry across the redirect), so the
  base was verified another way — the Cycle 80 work tree's tracked
  files were compared blob-by-blob against main's recursive tree
  via the API: all 234 blobs identical, no missing files. That
  verified tree is the base for this cycle's branch.

### Platform + gate this run (ticker + dashboard shipped)
- Spotrac probe: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the
  Spotrac basis (6 team failures ARI/BOS/CHC/MIL/TB/TEX in the
  artifact metadata) + Cot's second basis (Cycle 74, 7/7 shed
  sets). FanGraphs not re-probed: item (c) stays failed-closed
  per its guard; retry only on a 200 probe.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull Nov 3 22:23
  UTC, 17.9h old, < 20h watermark); pull_evidence_surveillance.py
  SKIP (artifact Nov 2, 2d old, < 6d guard). Both SKIP lines are
  normal outcomes, not failures. No new evidence artifact, so
  docs/EVIDENCE.html is untouched.
- TICKER: pull_tracker_ticker.py OK — window still
  2026-10-28..2026-11-04, SIGNED 369 -> 805, REPORTED 200, BUZZ 0,
  total 569 -> 1005. The +436 SIGNED rows were investigated
  before shipping, not just counted: every one is dated Nov 2-4,
  none of the old 369 was lost, and the increase is the
  post-season DFA wave (DFA declarations 234 -> 659; the rest
  Nov 3-4 releases and new signings, e.g. Many Ramirez SFA Nov 4).
  The 5 duplicate transaction ids are unchanged from Cycle 80 —
  the known bilateral-trade rows (one row per side of a trade),
  not a new defect. Bluesky Jetstream handshake 403 is the
  script's designed fail-closed behavior (logged, skipped, never
  routed around); Google News answered 200 this run.
- PLATFORM: ingest_platform.py 25 datasets, 0 failures; Savant
  expected 651-673/season, bat-tracking 595-619, sprint 489-506 —
  all inside the known-good bands, no silent-source move.
  Transactions raw 121,411 -> 121,908 (the ticker wave above;
  raw-zone only). curate.py 20 tables, all contracts pass;
  _build_report.json identical to main's, so no curated table
  changed materially and none is shipped. Routine ingest manifest
  appends were restored, not shipped, matching Cycle 80 practice.
  build_warehouse.py rebuilt; query.py benchmark_parity
  r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1 (committed snapshots forced). Census:
  25 unique figures, zero data-figure-missing markers; Story 6
  chapters, Boardroom <=15 slides, Explorer all 25 by task, 8
  percentile player cards. Crest stamp reads "Data as of Nov 4,
  2026 · tracker Nov 4 · injured list Nov 3 · evidence Nov 2".
  dashboard/hardball_demo.html kept as a byte-identical copy of
  dashboard/index.html (the #81 sync invariant).
- GATE: src/verify_data.py 107 checks ALL PASS on the first run
  (no gate fix needed this cycle); spellcheck green.

### Checklist status, refreshed
- Freeze / final refresh: still targeted Nov 30; freeze tag still
  owed. v1.1.12 (Cycle 78 restore) is the current published
  release, NOT the freeze tag.
- Demo package: 25 figures verified this run; Fig. 23 re-verified
  via gate (BIS canonical lines); one-pager and talk-track
  unchanged this run (gate checks talk-track refs <= 25);
  README "Presenting in 5 minutes" current (Cycle 79).
- Print pack: still day-before items — TALKTRACK printed,
  one-pager printed, README "Presenting in 5 minutes" loaded.
- Known gaps carried, unchanged: salaries 24/30 (Spotrac 403;
  FanGraphs retry only on a 200 probe, under the Cycle 32
  reconcile-first guard); forced-seller 6/7 on the Spotrac basis,
  7/7 on Cot's second basis; PRICE-1 blocked pending complete
  per-class signing terms (Sportradar trial DECLINED by the owner
  2026-11-03 — do not raise it again; the dashboard footer line
  that still says the trial starts mid-November is corrected at
  the freeze cut, per the Cycle 77 note); persistence recompute
  on record from Cycle 63.
- Open PRs left untouched: #57 (Cycle 77 live refresh, predates
  the Cycle 78 restore and the current main) and #58
  (parallel-lane ticker trigger).

### Remaining build queue
- Final frozen-main release cut before Dec 1 (with the Sportradar
  footer-line correction riding along). After Dec 1 the deadline
  guard fires and this job goes silent.

## Cycle 82 — live refresh (Nov 4) + December checklist refresh (2026-11-04 ~14:15 PT, 24/7 job)

### Base
- Main 9c52a75d at run start (Cycle 81 merge 7304d342 plus the
  parallel lane's PR #87 "Give Hardball Story one clear opening",
  merged 2026-11-04T21:20:36Z — Story verdict rewritten as the
  question "Where did lower-payroll winners find value?").
  Tarball download 404'd on the codeload redirect again, so the
  base was verified another way: the Cycle 81 work tree's tracked
  files were compared against main's recursive tree via the API
  using git blob hashes, after syncing PR #87's
  src/dashboard_p6.py — zero diffs, i.e. the tree is main
  9c52a75d exactly (the two built HTMLs were synced from main's
  blobs in the same pass and are regenerated by this run's
  rebuild anyway).

### Platform + gate this run (live refresh + dashboard shipped)
- Spotrac probe: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the
  Spotrac basis + Cot's second basis (Cycle 74, 7/7 shed sets).
  FanGraphs not re-probed: item (c) stays failed-closed per its
  guard; retry only on a 200 probe.
- LIVE FEEDS: refresh_live_feeds.py OK (last pull Nov 3 22:23
  UTC, ~24h old, past the 20h watermark) — 4 FastballAPI credits
  (20 MTD in November, inside the 200-credit cap); new raw
  snapshots injuries_2026-11-04 (Fastball 145 records, Statyx
  first page 50). Union 164 players (Fastball 145, Statyx 50,
  overlap 31); standings agree 30/30 with the KPI snapshot.
  FA overlay 9/251 (1 differs from the static file). Script's
  FA-pool movement line: 0 new IL, 4 returned, 3 status changes
  since Nov 2. pull_evidence_surveillance.py SKIP (artifact
  Nov 2, 2d old, < 6d guard) — normal, not a failure; no new
  evidence artifact, so docs/EVIDENCE.html is untouched.
- IL UNION 182 -> 164, INVESTIGATED before shipping: Fastball
  injuries 175 -> 145, Statyx page 16 -> 50, overlap 9 -> 31.
  30 names left the union (25 Fastball-only, 4 Statyx-only,
  1 both) and 12 Statyx-only names joined — the shape of
  post-season IL clearing, not a source break: both feeds
  answered 200, no 403/429, standings check 30/30. Substantive
  status changes are few (e.g. Angel Zerpa 60-Day-IL -> Out,
  Romy Gonzalez Day-To-Day -> Out); most of the 152 changed
  rows are pulled_at refreshes and Statyx enrichment
  (statyx_status/side filled in). fact_il_events 123 -> 133
  (append-only diff log) corroborates real movement.
- TICKER: pull_tracker_ticker.py OK — window still
  2026-10-28..2026-11-04, SIGNED 805 -> 849 (+44, none lost),
  REPORTED 200, BUZZ 0, total 1005 -> 1049. REPORTED rotated
  119/200: by design, REPORTED stores the newest 200 by
  pubdate, so a fresh RSS pull displaces older items; the
  SIGNED lane (StatsAPI transactions, the authoritative lane)
  lost nothing. Bluesky Jetstream handshake 403 is the
  script's designed fail-closed behavior (logged, skipped,
  never routed around); Google News answered 200 this run.
- PLATFORM: ingest_platform.py 0 failures; Savant bands hold
  (expected 651-673/season, bat-tracking 595-619, sprint
  489-506), no silent-source move. Transactions raw 121,908
  -> 122,135 (raw-zone only). curate.py 20 tables, all
  contracts pass; _build_report.json changed ONLY in
  fact_il_current (182 -> 164 rows) and fact_il_events
  (123 -> 133 rows), so those two parquets + the report ship
  and no other curated table does. Routine ingest manifest
  appends were restored, not shipped, matching Cycle 80/81
  practice — the shipped manifest is main's 68 lines plus
  this run's 4 refresh entries only. build_warehouse.py
  rebuilt; query.py benchmark_parity r = 0.889, 201 matched —
  exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1 (committed snapshots forced). Census:
  25 unique figures, zero data-figure-missing markers; Story 6
  chapters, Boardroom <=15 slides, Explorer all 25 by task, 8
  percentile player cards. Crest stamp reads "Data as of Nov 4,
  2026 · tracker Nov 4 · injured list Nov 4 · evidence Nov 2"
  (injured list moved Nov 3 -> Nov 4 with this refresh).
  dashboard/hardball_demo.html kept as a byte-identical copy of
  dashboard/index.html (the #81 sync invariant).
- GATE: src/verify_data.py 107 checks ALL PASS on the first run
  (no gate fix needed this cycle); spellcheck green.

### Checklist status, refreshed
- Freeze / final refresh: still targeted Nov 30; freeze tag still
  owed. v1.1.12 (Cycle 78 restore) is the current published
  release, NOT the freeze tag.
- Demo package: 25 figures verified this run; Fig. 23 re-verified
  via gate (BIS canonical lines); one-pager and talk-track
  unchanged this run (gate checks talk-track refs <= 25);
  README "Presenting in 5 minutes" current (Cycle 79).
- Print pack: still day-before items — TALKTRACK printed,
  one-pager printed, README "Presenting in 5 minutes" loaded.
- Known gaps carried, unchanged: salaries 24/30 (Spotrac 403;
  FanGraphs retry only on a 200 probe, under the Cycle 32
  reconcile-first guard); forced-seller 6/7 on the Spotrac basis,
  7/7 on Cot's second basis; PRICE-1 blocked pending complete
  per-class signing terms (Sportradar trial DECLINED by the owner
  2026-11-03 — do not raise it again; the dashboard footer line
  that still says the trial starts mid-November is corrected at
  the freeze cut, per the Cycle 77 note); persistence recompute
  on record from Cycle 63.
- Open PRs left untouched: #57 (Cycle 77 live refresh, predates
  the Cycle 78 restore and the current main) and #58
  (parallel-lane ticker trigger).

### Remaining build queue
- Final frozen-main release cut before Dec 1 (with the Sportradar
  footer-line correction riding along). After Dec 1 the deadline
  guard fires and this job goes silent.

### Rebase note (same run)
- While PR #90 was open, main moved three times (PR #88 About
  portrait, PR #89 Story team fielding errors, PR #91 Explorer
  individual fielding errors — all three touch dashboard_p6.py
  and the built HTMLs), so merging #90 would have reverted
  those features from the built dashboard. Per shared-repo
  discipline the branch was rebuilt twice from the then-new
  main (first ad069f3d, then fe34029f): only the #88/#89/#91
  files were synced in, the Cycle 82 data/curated/manifest/
  docs changes above were kept (their bases are unchanged in
  the new main, verified by blob hash), and the dashboard was
  rebuilt from the new code + Cycle 82 data and re-gated
  before merging. PR #90 was closed as superseded by the
  rebased PR.

### Spellcheck fix in this PR (mechanical, script-sanctioned)
- The rebased rebuild surfaced one spellcheck failure: "sabr"
  from the parallel lane's fielding panel ("SABR Defensive
  Index", Rawlings Gold Glove criteria, cited in-panel). SABR
  is the Society for American Baseball Research — a correct
  term, not a typo — so per the script's own rule it was added
  to the WHITELIST in src/spellcheck_gate.py with a Cycle 82
  comment. No panel wording changed. Spellcheck green after.

## Cycle 83 — tracker refresh (Nov 4) + December checklist refresh (2026-11-04 ~20:13 PT, 24/7 job)

### Base
- Main e1801d20 at run start (Cycle 82 merge 505f2eac plus the
  parallel lane's PR #93 buzz empty state, #94 provider-note
  removal, #95 animation-control contrast, #96 Figure 24 label
  spacing, #97 fielding shortcuts, #98 roster-positioning line,
  #99 fielding visual hierarchy). Tarball download 404'd on the
  codeload redirect again, so the base was verified another way:
  the Cycle 82 work tree's tracked files were compared against
  main's recursive tree via the API using git blob hashes —
  only dashboard_p6.py and the two built HTMLs differed, and
  those three blobs were synced from main before any work, after
  which the tree matched main e1801d20 exactly (zero diffs).

### Platform + gate this run (tracker refresh + dashboard shipped)
- Spotrac probe: single GET of the Rays 2026 payroll page -> 403
  (browser UA). Logged, moved on; salaries stay 24/30 on the
  Spotrac basis + Cot's second basis (Cycle 74, 7/7 shed sets).
  FanGraphs not re-probed: item (c) stays failed-closed per its
  guard; retry only on a 200 probe.
- LIVE FEEDS: refresh_live_feeds.py SKIP (last pull Nov 4
  22:17 UTC, 5.9h old, < 20h watermark) — normal, not a failure;
  no FastballAPI credits spent. pull_evidence_surveillance.py
  SKIP (artifact Nov 2, 2d old, < 6d guard) — normal; no new
  evidence artifact, so docs/EVIDENCE.html is untouched.
- TICKER: pull_tracker_ticker.py OK — window rolled
  2026-10-28..2026-11-04 -> 2026-10-29..2026-11-05, SIGNED
  849 -> 846, REPORTED 200, BUZZ 0, total 1049 -> 1046. The
  SIGNED move is window aging by design, not loss: the four
  Oct 28 transactions fell out of the 7-day window (Romero,
  Padilla, Macuare, Santos) and one Nov 4 transaction joined
  (Zak Kent released by Washington); every other SIGNED item
  is unchanged. REPORTED rotated 80/200 under the newest-200
  cap, by design. Bluesky Jetstream handshake 403 is the
  script's designed fail-closed behavior (logged, skipped,
  never routed around); Google News answered 200 this run.
- PLATFORM: ingest_platform.py 0 failures; Savant bands hold
  (expected 651-673/season, bat-tracking 595-619, sprint
  489-506), no silent-source move. Transactions raw 122,135
  -> 122,163 (raw-zone only). curate.py 20 tables, all
  contracts pass; _build_report.json byte-identical to
  committed (no curated change ships). Routine ingest manifest
  appends were restored, not shipped, matching Cycle 80-82
  practice — the shipped manifest is main's 72 lines.
  build_warehouse.py rebuilt; query.py benchmark_parity
  r = 0.889, 201 matched — exact.
- DASHBOARD: rebuilt with the lake present and
  HARDBALL_OFFLINE_BUILD=1 (committed snapshots forced) from
  the synced parallel-lane code (#93-#99 features included).
  Census: 25 unique figures, zero data-figure-missing markers;
  Story 6 chapters, Boardroom <=15 slides, Explorer all 25 by
  task, 8 percentile player cards. Crest stamp reads "Data as
  of Nov 5, 2026 · tracker Nov 5 · injured list Nov 4 ·
  evidence Nov 2" (tracker moved Nov 4 -> Nov 5 with this
  pull; the pull landed Nov 4 20:14 PT / Nov 5 04:14 UTC).
  dashboard/hardball_demo.html kept as a byte-identical copy of
  dashboard/index.html (the #81 sync invariant).
- GATE: src/verify_data.py 107 checks ALL PASS on the first run
  (no gate fix needed this cycle); spellcheck green.

### Checklist status, refreshed
- Freeze / final refresh: still targeted Nov 30; freeze tag still
  owed. v1.1.12 (Cycle 78 restore) is the current published
  release, NOT the freeze tag.
- Demo package: 25 figures verified this run; Fig. 23 re-verified
  via gate (BIS canonical lines); one-pager and talk-track
  unchanged this run (gate checks talk-track refs <= 25);
  README "Presenting in 5 minutes" current (Cycle 79).
- Print pack: still day-before items — TALKTRACK printed,
  one-pager printed, README "Presenting in 5 minutes" loaded.
- Known gaps carried, unchanged: salaries 24/30 (Spotrac 403;
  FanGraphs retry only on a 200 probe, under the Cycle 32
  reconcile-first guard); forced-seller 6/7 on the Spotrac basis,
  7/7 on Cot's second basis; PRICE-1 blocked pending complete
  per-class signing terms (Sportradar trial DECLINED by the owner
  2026-11-03 — do not raise it again; the dashboard footer line
  that still says the trial starts mid-November is corrected at
  the freeze cut, per the Cycle 77 note); persistence recompute
  on record from Cycle 63.
- Open PRs left untouched: #57 (Cycle 77 live refresh, predates
  the Cycle 78 restore and the current main) and #58
  (parallel-lane ticker trigger).

### Remaining build queue
- Final frozen-main release cut before Dec 1 (with the Sportradar
  footer-line correction riding along). After Dec 1 the deadline
  guard fires and this job goes silent.
