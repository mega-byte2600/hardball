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
