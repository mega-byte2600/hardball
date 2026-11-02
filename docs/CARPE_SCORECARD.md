# CarpeData scorecard — HARDBALL (2026-10-31)

Every open/free source we tried for the CarpeData pass, what happened,
and the decision. Rule: paywalled/licensed sources are noted as gaps,
never pirated; a source joins the model only by passing a measured
BML cycle, not by being available.

Connector: `src/carpe.py` (keyless throughout). Snapshots committed
under `data/`; raw payloads archived under `data/raw/` (gitignored).

## KEPT — connected and in use

| Source | Endpoint form | Used for |
|---|---|---|
| MLB Stats API — historical seasons | `/stats` qualified leaders, 2023+2024 | Extended the lake 2023–2026 → enabled the Cycle 21 Marcel backtest |
| MLB Stats API — people | `/people?personIds=` batched | Real birthdates/ages for all 379 lake players (`player_ages.json`) |
| MLB Stats API — minors | `/teams?sportId=11/12`, `/stats` per affiliate | Cycle 23 pipeline index (AAA/AA under-26 depth, 30 orgs) |
| Baseball Savant — expected stats | `/expected_statistics?...&csv=true` 2023–2026 | Cycle 20 Q1: xwOBA beats actual wOBA as next-year input (all 3 pairs) |
| Baseball Savant — batted ball | `/statcast_leaderboard?...&csv=true` 2023–2026 | EV/barrels/sweet-spot; Cycle 20 Q2/Q3 |
| Baseball Savant — bat tracking | `/leaderboard/bat-tracking?dateStart=…&dateEnd=…&seasonStart=…&type=batter&csv=true` 2024–2026 | Bat speed/squared-up/blasts; Cycle 20 Q2/Q3. **Trap:** the bare `?year=` form silently ignores the year and returns the current season for every request (verified byte-identical) — only the date-range form works. No 2023 data exists (Hawk-Eye starts 2024) |
| Baseball Savant — sprint speed | `/leaderboard/sprint_speed?...&csv=true` 2023–2026 | Snapshot in repo; no cycle has needed it yet |
| Baseball Savant — arm strength | `/leaderboard/arm-strength?...&csv=true` 2026 | Snapshot in repo; fielding context, unused by cycles so far |
| FanGraphs API — Steamer projections | `/api/projections?type=steamer` (bat + pit) | Cycle 22 benchmark (Marcel vs Steamer) + WAR context |
| FanGraphs — player crosswalk | Steamer rows carry `xMLBAMID` + `playerid` | `player_xwalk.json`: covers 379/379 lake players; all CarpeData joins are by ID |

## TESTED AND DROPPED (measured, not vibes)

| Candidate | Result |
|---|---|
| Savant traits as Marcel adjustments (Cycle 20) | Bat speed is the most stable trait in the data (YoY r ≈ .92) and still made projections **worse** out-of-sample in both directions on both metrics. Barrels/squared-up/xwOBA-luck: splits or rounding-level gains. Nothing adopted; Savant stays as diagnostics/context |
| 2-season Marcel (Cycle 21) | Superseded: 3-season window ties it on accuracy, wins on coverage/fidelity; age term fitted on backtest residuals improved OOS MAE both directions (OBP .0226→.0220, SLG .0468→.0453 pooled) and was adopted |
| Name-string player joins | Replaced everywhere in CarpeData work by MLBAM-ID joins (the AZ/ARI and walks bugs were this failure class) |

## TRIED, UNAVAILABLE OR REDUNDANT (logged gaps)

| Source | Status |
|---|---|
| FanGraphs ZiPS projections | API returned an empty set on 2026-10-31. Not in the benchmark; Steamer only, labeled as such |
| Chadwick register flat file | `people.csv` 404s at its historical path. Redundant: the Steamer crosswalk covers our whole universe |
| Lahman / baseballdatabank | Repo paths restructured (404). Redundant: the MLB API itself supplies the 2023/2024 history we needed, single-source consistent with the lake |
| FanGraphs leaders endpoint (for crosswalk) | Works but paginates at 50 rows — a 1,000-row page request silently returns a subset (caught: only 30 of 379 players matched). Superseded by the Steamer crosswalk |
| Full pitch-level Statcast lake | Feasible but heavy (~25k-row response caps, ~17 MB per two weeks of games). Leaderboard-level Savant data answered every question this demo asks; the full lake is a post-Dec-1 build if a question ever needs pitch-level granularity |
| Spotrac live payroll API | No public API. Payroll stays the committed dated snapshots (already a G11 hygiene item), not a brittle scrape |
| Stathead / Inside Edge / sportsbook odds | Paid or key-gated. Noted as gaps per the rule; odds, if ever used, would be a labeled feature, never a label |

## Addendum — solutions pass (2026-10-31)

| Source | Status |
|---|---|
| Spotrac team payroll pages (per-player 2026 salaries) | KEPT with a caveat: 24/30 teams pulled (927 rows) before Spotrac rate-limited the pull (500s, then 403 — requests stopped, per policy, not routed around). Missing: ARI, BOS, CHC, MIL, TB, TEX. `bml_cycle25.py` caches successes, so any later rerun fetches only the missing six |
| Spotrac 2027 free-agents page | KEPT: full class (251 players) in one pull, before the rate limit |
| USA TODAY salary database | TRIED, BLOCKED: HTTP 402 access restricted. Logged, not circumvented |
| NPB official BIS — leaderboards + posted trio (Cycle 34) | KEPT: keyless 2024–2026 qualified leaderboards (340 rows, both leagues, bat+pit) via `src/pull_npb_bis.py`, now an `npb_bis` platform source in `src/ingest_platform.py`. Trio dataset `data/posted_class_2026.json` (Sato/Taira/Itoh, posted Nov 1, 2026) verified vs AP wire reports; BIS canonical over wire roundings (Sato .306 not .308; Itoh 34 BB not 32). Figure 23 uses BIS counting stats only — no NPB→MLB translation factor claimed. Dropped same lane: baseball-data.com (403/404), ESPN jlb API (400/404) |

---
## FULL VERIFICATION PASS — 2026-10-31 (post-merge, against main adbe2077)

Every source re-checked live or by independent recomputation. Verdicts:

| Source | Verdict | Evidence |
|---|---|---|
| MLB Stats API (KPI/standings/panel) | VERIFIED LIVE | All 30 teams' 2026 wins match live standings exactly (incl. D-backs 86, White Sox 84). Sampled team stats recomputed from the API match snapshots to the digit (MIL/NYY/CLE: OBP, HR, PA all exact). Panel: 509 rows / 16 seasons; the 59 payroll-incomplete rows are the documented 509-vs-450 gap, not corruption |
| Baseball Savant snapshots | VERIFIED LIVE | Live 2026 expected-stats pull compared player-by-player: 246 players, ZERO xwOBA differences > .002 vs the committed snapshot. Bat-tracking files for 2024/2025/2026 are byte-distinct (the silent-year trap from the first pull is absent). All 16 snapshot files present, counts sane (246–673 rows) |
| FanGraphs Steamer + crosswalk | VERIFIED | Crosswalk 379 entries; benchmark joins 201/201 Marcel hitters by MLBAM ID (unmatched: none); OBP r = .889 consistent between raw Steamer files and the benchmark artifact |
| ESPN cross-validation | VERIFIED (nuance) | HR counts match exactly for all 254 compared players (131 in 2025 + 123 in 2026) — the dashboard claim is HR-specific and true. The files' "mismatches: 2" per year are AVG differences of ≤ .002 on 2 players (non-HR field, scoring/rounding class), recorded here so the headline count is never misread |
| Spotrac payroll / W-L (payroll.py) | VERIFIED LIVE | All 30 records re-checked against live MLB API standings: no mismatches (the 161-game NYY/BAL totals are real) |
| Spotrac per-player salaries | STILL BLOCKED (24/30) | Completion rerun attempted 2026-10-31 ~19:45 PT — Spotrac still refusing the same 6 team pages (ARI/BOS/CHC/MIL/TB/TEX). Requests stopped, not routed around. Coverage is labeled 24/30 in the data metadata, the dashboard source box, and the release notes. `bml_cycle25.py` completes it on any later successful run (cache-aware). The FA class itself is complete: 251 players, 231 with Steamer WAR |
| MiLB pipeline (MLB minors) | VERIFIED (internal) | 30 orgs, ranks 1–30 unique, index mean exactly 100.0 by construction check, no top-hitter aged ≥26 (under-26 rule holds in the output) |
| Lake (local build artifact) | VERIFIED (local) | stat_lines 2023–2026 (743 rows), players registry 379 = crosswalk size. The 2022 backfill lives in the main lane's environment; ingest/backfill scripts regenerate the lake |
| Derived artifacts | VERIFIED | Projections 201 hitters / 102 pitchers; formula_prod.json carries the DIAGNOSTIC ONLY annotation on main; lagged_forecast.json carries the G6 exclusion (grouped MAE 10.23); efficiency file = 721 data rows (the 25-year claim); wow_scenarios constraints hold (26 men, spend ≤ budget at all three budgets) |
| Dashboard (from main) | VERIFIED | Fresh main tarball builds offline: 19 figures without the local lake (pitching omits gracefully), 20 with it; output byte-size identical to the integrated build (deterministic) |

## Addendum — Cycle 32 (2026-11-01 ~14:15 PT)

| Source | Status |
|---|---|
| FanGraphs RosterResource payroll (?season=2026 team pages) | TRIED, BLOCKED: direct pulls return HTTP 403 (Cloudflare challenge) for both requests and curl with a browser UA. Pull stopped per policy — no alternate endpoint, no automation around the challenge, no rows added. Reconcile-first guard NOT run (nothing to reconcile). Salaries remain 24/30 Spotrac; forced-seller coverage remains 6/7 (CHC uncovered). Open definition question for any future attempt: which FanGraphs column (2026 cash, 2027 cash, AAV), if any, corresponds to Spotrac's "Payroll Salary" field is not established — public snapshots show the 2026 cash column differing from the Spotrac file on top guaranteed contracts (see BML Cycle 32). Preliminary observation only, not a reconciliation result. |
| Spotrac team payroll pages (completion probe) | STILL BLOCKED: Tampa Bay page still 403 on a single probe GET. No rerun of bml_cycle25.py (it would fetch only the missing six, all still blocked). |
| Dashboard figure count (gate repair) | CORRECTED: main-lane merge had moved the dashboard to 22 figures (Cycle 8 AUC panel inserted as Figure 5) while the gate, talk-track, README, and summary still said 21. Renumbering fixed in Cycle 32; gate green. |

## Addendum — Cycle 41 (2026-11-02 ~06:20 PT): Cot's lane — reconciled, FAILED CLOSED

| Source | Status |
|---|---|
| Cot's Baseball Contracts (Baseball Prospectus) — 2026 year-end team sheets | TRIED, RECONCILED, FAILED CLOSED: all 30 team sheets pulled and reconciled against the Spotrac file under the reconcile-first guard; the bases do not line up (detail below), so **no rows were added**. Salaries remain 24/30 Spotrac; forced-seller coverage remains 6/7 (CHC uncovered). Cot's data itself verified accurate — the failure is accounting-basis incompatibility, not data quality. |

### Cycle 41 reconciliation detail

- **Access path.** legacy.baseballprospectus.com serves an Anubis anti-bot
  challenge to direct fetches (HTTP 200 challenge page, no data; pull not
  routed around). The Cot's index's per-team data lives in public Google
  Sheets ("MLB \<Team\> 26 YE" — projected 40-man year-end payrolls through
  11/1/26). All 30 sheets were exported as CSV at a polite rate (30/30 HTTP
  200) and cached in the local mirror at `data/raw/cots/` (30 team CSVs +
  parsed file), following the Spotrac cache pattern. Parsed: 2,240 payroll
  lines — 1,369 main contract rows plus 871 bonus / buyout /
  departed-player lines (kept out of roster matching).
- **Season discovery (material).** The Spotrac file's basis is the **2027**
  payroll, not 2026: the cached Spotrac pages are titled "2027 \<Team\>
  Payroll Table" — Spotrac had rolled to the upcoming season when Cycle 25
  pulled on 2026-10-31. Contracted veterans in the file match Cot's 2027
  Labor Relations Payroll (LRP) column to the dollar (ATH: Severino
  $22.000M, Rooker $14.000M, Soderstrom $6,428,571 vs Cot's $6.429M,
  Butler $5,428,571 vs $5.429M, Wilson $2,928,571 vs $2.929M). All four
  Cot's columns (LRP / CB tax × 2026 / 2027) were tested as the mapping;
  LRP 2027 is the only viable one. The file name and metadata say 2026 —
  flagged here, not silently rewritten.
- **Result vs the pass bar** (≥95% of matched players within $50k; team
  totals within ~2% on the mapped basis; all top-5 contracts per team
  within rounding) — **FAIL on every prong**:
  - Coverage: only 150 of 927 Spotrac rows (16.2%) have any Cot's LRP-2027
    counterpart. The other 777 break down as: 501 pre-arbitration rows at
    Spotrac's flat $1,000,000 placeholder, 209 arbitration projections
    (round numbers, e.g. Langeliers $7.5M), 58 names absent from the
    team's Cot's sheet (2027 assignment differences), and 9 veteran rows
    whose Cot's 2027 cell is an option/FA marker. Cot's publishes
    contract facts and A1/A2/FA markers for unsigned players — it does
    not publish projections.
  - Player agreement: 104/150 matched pairs within $50k = 69.3% (bar
    95%). Excluding option-year and deferred contracts entirely, the
    plain-contract subset is 65/76 = 85.5% — still under the bar
    (signing-bonus proration residuals).
  - Team totals on matched pairs: 16 of 24 teams differ by more than 2%
    (CLE −34.5%, MIN −18.5%, BAL −17.0%, LAD −13.0%, SD −12.9%,
    DET −10.7%, TOR −9.5%).
  - Top-5 contracts: pass for only 3 of the 17 teams with ≥5 matched
    pairs (ATH, HOU, PHI).
- **Why they differ — conventions, not errors.** (1) Option years: Cot's
  LRP books the guaranteed buyout; Spotrac books the full option salary
  as exercised — Robert Jr. $2.0M vs $20.0M, Jansen $2.0M vs $12.0M,
  Clase $2.0M vs $10.0M, Acuña Jr. $10.0M vs $17.0M. (2) Deferred money:
  Cot's LRP is present-value; Spotrac is nominal — Ohtani $28.216M PV vs
  $70.0M nominal; the LAD deferred cluster (Snell, Betts, Freeman,
  Yamamoto, T. Hernández, Edman, Scott, Smith, Díaz) drives LAD's −13.0%.
  (3) Signing-bonus proration residuals up to ~$1.7M on otherwise plain
  contracts (Merrill −$1.000M exactly; Weaver, Hoffman, Senga).
- **Cot's quality spot-checks pass.** CHC (a gap team): Swanson CB/AAV
  $25,285,714, Imanaga LRP $22,025,000, Happ CB/AAV $20,333,333 — all
  match independently researched values; every plain escalator contract
  on the 24 known teams matches Spotrac to Cot's $1k rounding.
- **Verdict.** FAIL CLOSED under the reconcile-first guard. Filling the 6
  teams on the Cot's LRP basis would mix present-value / buyout
  accounting into a nominal / exercised-option column and silently
  distort the forced-seller shed math. A future fill requires either a
  full-file basis conversion (all 30 teams from Cot's, losing Spotrac's
  arb / pre-arb estimates) or a second, separately labeled Cot's dataset
  — owner's call, not taken here. Raw pulls and the full reconciliation
  workbook (recon tables) are preserved in the mirror cache and the
  Cycle 41 workpapers.

## Addendum — Cycle 44 (2026-11-02 ~08:20 PT): accuracy stack — persistence correction landed, Cot's adopted as labeled dataset, BRef cross-check failed closed

Owner directive (2026-11-02 08:11 PT): "do what takes to make accurate,
optimal and professional." That resolved the two open calls: PR #21's
persistence correction lands (re-applied onto current main — the PR
itself no longer merged cleanly after Cycles 40–43, and is closed as
superseded by this cycle), and Cot's is adopted under option (b): a
second, separately labeled dataset. Nothing below changes the
Spotrac-basis file, forced-seller math, or any roster math.

| Source | Status |
|---|---|
| Cot's Baseball Contracts — adopted as second labeled dataset | SHIPPED as `data/salaries_cots_2027.json` (built by `src/bml_cycle44.py` from the Cycle 41 mirror cache): **237 rows, 30 teams** — every player for whom Cot's publishes a 2027 LRP dollar figure, each row labeled `source=cots_baseball_prospectus`. Basis stated in the file metadata: LRP 2027 (projected 40-man year-end; deferred money at present value; option years at the guaranteed buyout). Unsigned players carry FA/arb/option markers in Cot's, not numbers, so they are not rows. Curated as `fact_salaries_cots` — a cross-check / coverage layer ONLY, never summed with `fact_salaries`. Salaries for the demo's own math remain 24/30 Spotrac-basis; forced-seller stays 6/7 (CHC uncovered). |
| Baseball-Reference WAR daily downloads — salary cross-check | RECONCILED, FAILED CLOSED for dataset use. The `salary` column is real (literal "NULL" = missing): 2026 has **495 player-team rows** with a value (~30% of players; ~70% in 2024). Against the Spotrac-basis file (24 teams): 195 of 927 rows matched by name+team (21.0% coverage), 28.7% of matched within $50k — expected: BRef is the 2026 season's salary, the Spotrac file is on a 2027 basis (Cycle 41), so escalators disagree by construction. Against Cot's on the same season (LRP-2026), the credibility test for the 6 gap teams: 114 matched, **71.1% within $50k — under the 80% bar**, so NO BRef salary dataset ships (workpaper: `data/salary_recon_cycle44.json`). The disagreements are convention gaps, not errors: for traded players Cot's books the acquiring club's share of the season while BRef books the full-season figure (e.g. Suárez BOS $7.6M Cot's vs $26.0M BRef; Gausman CHC $6.89M vs $23.0M), plus deferred/PV cases (Gray BOS $31.0M vs $35.0M). Plain single-team contracts agree exactly (Anthony $2.625M, Ashby $5.7M, Assad $1.8M). The WAR files still land in the raw zone (`bref_war`) for WAR cross-checks. |
| Chadwick Bureau Register (GitHub, keyless, ODC-BY) | ADOPTED: ingest lands all 16 people shards (**527,990 person rows**); curated `dim_player_xwalk` keeps the **137,320** rows carrying an MLBAM key (Retro / BRef / BRef-minors / FanGraphs / NPB / Wikidata keys). Join proof: **379/379 of the demo's registry players match (100%)** — 370 with FanGraphs IDs, 379 with BRef + Retro IDs, 17 with NPB keys. This is now the platform's conformed ID crosswalk. |
| The Injury Report (Seehafer) — IL stints CSV | ADOPTED: keyless CSV (built from MLB's own IL transactions) lands in the raw zone and curates to `fact_il_stints`: **6,632 stints, 2,177 players, seasons 2019–2026**. Note: the site's headline count is 6,651 injuries; its downloadable CSV parses to 6,632 stints — the CSV is what we count. Availability cross-check layer only; Cycle 27 availability factors unchanged. |
| Spotrac team payroll pages (completion probe) | STILL BLOCKED: single probe of the CHC page this cycle still 403. No rerun of `bml_cycle25.py`. |
| Ready-to-activate keyed sources (prep only — NO signups, NO keys exist yet) | `src/keyed_sources.py` ships env-key-gated, fail-closed stubs (no key → labeled "data unavailable", no network call; a 403/429 stops, never routed around). **Tank01** (RapidAPI Basic, free forever, 1,000 hits/mo, no card): injuries-by-date, roster history, ID crosswalk — no salaries. **Statyx** (free key): reference data free; MLB injuries + WAR endpoints exist but free-tier inclusion UNVERIFIED. **FastballAPI** (500 credits/mo free, no card): pitch-level 2015+, injuries snapshot at 2 credits/call — no salaries. **Sportradar MLB v8 trial: DO NOT START before mid-November** — its 30-day window must cover Dec 1; trial carries the one real contract field in the set (annual BASE salary in Player/Team Profile), internal-evaluation license — owner reads the trial terms at signup. |

## Addendum — Cycle 45 (2026-11-02 ~10:20 PT): Statyx + FastballAPI CONNECTED and cross-checked; full source list now renders in the dashboard footer

Owner directives: "update repo so that hardball shows all API sources
at bottom of page when rendered! its key for credibility! we just got
two more!" and "make sure git knows we have these apis as other
agents collab on hardball project!" Both are executed here: the
rendered dashboard's bottom sources box now enumerates every data/API
source with its status, and the connection record is committed in
HANDOFF.md + docs/DATA_PLATFORM.md where collaborating lanes read.

| Source | Status |
|---|---|
| Statyx (api.statyx.io) | CONNECTED 2026-11-02 via the owner's Secure Vault connector (custom.statyx); the key is NEVER in this repo. VERIFIED LIVE by Toby: GET /v1/mlb/standings -> 200; GET /v1/mlb/injuries -> 200 with **16 live records** (status, expected return, injury type, comments; feed timestamped 2026-11-02). The free tier DOES include MLB injuries — Cycle 44's UNVERIFIED question is settled. Repo-side path: `src/keyed_sources.py` (Bearer at api.statyx.io — that entry was already correct). No MLB salaries (contracts endpoint is NBA only). |
| FastballAPI (mcp.fastballapi.com) | CONNECTED 2026-11-02 via the owner's Secure Vault connector (custom.fastballapi); the key is NEVER in this repo. VERIFIED LIVE by Toby: tools are POST /v1/{tool} with the key in the x-api-key header — the Cycle 44 stub's Bearer-at-fastballapi.com shape was WRONG and `src/keyed_sources.py` is corrected in this cycle. get_standings {season: 2026} -> 200, **30 teams**; get_injuries {} -> 200, **190 records dated 2026-11-02** (player, team, status, type, detail, return_date). Cross-checks below. Free tier: 500 credits/mo; standings + injuries cost 2 credits per call. No salaries. |
| Tank01 (RapidAPI) | DEFERRED by the owner 2026-11-02 (RapidAPI signup dropped for now — "forget it for now"). Supplement only; nothing in the demo depends on it (Chadwick already covers the ID-crosswalk job at 379/379). Not a source of any demo data; listed as deferred in the dashboard footer and the connection record, never as connected. The secure-entry link exists if the owner ever revives it. |
| Sportradar MLB v8 trial | STILL NOT STARTED, deliberately: trial starts mid-November so the 30-day window covers Dec 1. |

### Cycle 45 cross-checks (run 2026-11-02 ~10:15 PT, fresh pulls)

- **FastballAPI 2026 standings vs the platform's committed standings
  (MLB StatsAPI-derived).** One fresh get_standings call (2 credits).
  Against `data/kpi_2026.json`: **30/30 teams matched; wins agree
  30/30; runs scored agree 30/30; zero diffs.** Against curated
  `fact_team_season` (which carries losses; the KPI file does not):
  29/29 comparable teams agree on wins, losses, AND runs allowed —
  the 30th (Arizona) is keyed "AZ" in the curated table vs "ARI" at
  FastballAPI, an abbreviation artifact, and its wins/runs already
  agree via the KPI comparison. Verdict: FastballAPI's standings are
  an exact match to the official feed on every field both files
  carry. [VERIFIED]
- **Injury-feed overlap, Statyx vs FastballAPI.** One fresh Statyx
  injuries call (free) + the FastballAPI injuries pull above (2
  credits), matched by normalized player name: **14 of Statyx's 16
  records also appear in FastballAPI's 190 (87.5%)**, and all 14
  agree on status AND injury type (e.g. Cal Raleigh — Out /
  Shoulder at both; Zack Kelly — 60-Day-IL / Elbow at both). The 2
  Statyx-only names are Brooks Kriske and Jalen Beeks — consistent
  with Statyx carrying a recent-transactions-style feed (16 current
  moves) against FastballAPI's full daily IL snapshot (190); the
  feeds are complementary, not contradictory. [VERIFIED]
- **What did NOT change:** neither feed feeds any figure, model, or
  roster math in this cycle. They are connected, verified, and
  cross-checked; wiring them into the availability layer is a future
  cycle's measured decision, not a silent swap. Spotrac probe this
  cycle: not re-run (Cycle 44's 403 stands; salaries remain 24/30
  Spotrac-basis + the labeled Cot's layer).

## Addendum — Cycle 46 (2026-11-02): HS-1, the Hakes–Sauer pricing screen (workpaper only — no dashboard claim change)

Owner-approved MIT-gap programme, increment 1 of 6 (2026-11-02 12:57 PT).
Hakes & Sauer (2006) regressed ln(salary) of newly signed free agents on
performance and showed OBP was underpriced relative to SLG before ~2004
and correctly priced after. HS-1 asks HARDBALL's version on today's
market: are the thesis skills (contact/K-avoidance, OBP, walk discipline,
availability) priced below their run value? Build:
`src/bml_cycle46.py`; dataset `data/hakes_sauer_dataset.json`; full
coefficient tables `data/hakes_sauer_results.json`. Committed data only.

**Method.** Two salary samples, bases never mixed. Sample S:
`data/salaries_2026.json` (Spotrac basis; Cycle 41 established the file
is the 2027 payroll despite its name), salary field as committed.
Sample C: `data/salaries_cots_2027.json` (Cot's LRP-2027 basis),
player-team obligation rows summed to player level (a player paid by
two clubs is paid the sum; obligations within one basis only). Skills
are expected 2027 skills — Marcel projections (OBP, SLG, K%, BB%) —
because the salary year is 2027; controls are age (dim_player),
Steamer 2027 WAR, and Steamer projected PA (Marcel's proj_PA is a
constant 500 for all 201 hitters and cannot proxy availability).
Realized 2026 skills are carried as a descriptive sensitivity.
Regression: ln(salary) on OBP, SLG, K%, BB%, age, WAR, PA (spec A),
plus an HS-faithful spec B without the WAR control. OLS via numpy with
classical standard errors (no statsmodels in the venv). Pitchers are
out of scope; two-way players are excluded (their salary prices both
roles — the Spotrac file stores the case as "SP  /DH", which the
exclusion matches on the space-stripped position).

**Exclusion cascades.** Sample S: 927 rows → 553 Pre-Arbitration rows
at Spotrac's flat $1,000,000 excluded as placeholders and 219
non-Bypassed Arbitration rows excluded as projections → 155 real
contract rows → 68 pitcher positions and 1 two-way row excluded → 26
without a Marcel projection or complete controls → **n = 60**, exactly
at the pre-registered n≈60 power floor (marginal; read accordingly).
Reconciliation: Cycle 41's 501/209 counts described the subset of
Spotrac rows with no Cot's counterpart (777 rows); HS-1's whole-file
rule (553/219) is broader and more conservative. Sample C: 237
player-team rows → 90 rows match a Marcel hitter (83 unique players)
→ 1 two-way label excluded → **n = 82** on LRP-2027 (n = 76 on the
CBT-AAV sensitivity, which requires an AAV on every Cot's row).

**Headline numbers (spec A).** Sample S (n = 60, R² = 0.359): OBP
−3.91 (SE 6.49, p = .549), SLG +2.73 (SE 2.23, p = .226), K% −0.005
(p = .798), BB% +0.032 (p = .519); age is the only significant term
(+0.102, p < .001). Sample C (n = 82, R² = 0.302): OBP +3.31 (SE 7.52,
p = .661), SLG +2.23 (SE 2.71, p = .414), K% +0.026 (p = .260), BB%
−0.018 (p = .751); age (+0.111, p < .001) and Steamer PA (+0.0026,
p = .014) significant. Spec B (no WAR control) tells the same story in
both samples. The descriptive OBP/SLG coefficient ratio is −1.43 in
Sample S and +1.48 in Sample C — it flips sign across bases, and no
OBP/SLG run-value benchmark exists in the repo docs/data (the
value_metrics wOBA weights are event weights, not OBP/SLG marginal
values), so HS-1 reports the ratio as descriptive only and defers the
formal proportionality test to HS-2. OBP's standard errors are large
by construction: OBP VIF is 7.5 / 6.4 (S / C) against BB% and WAR.

**Non-parametric cross-view ($/WAR by skill quartile).** $/WAR is
salary ÷ Steamer WAR, defined for WAR > 0 only (no sample player was
excluded on that rule). Top-quartile contact hitters (lowest K%) cost
about half as much per WAR as bottom-quartile contact hitters, in
both samples: Sample S median $/WAR $8.03M (n = 15) vs $14.98M
(n = 15), ratio 0.536; Sample C $6.19M (n = 21) vs $11.64M (n = 21),
ratio 0.532. The same pattern holds, weaker, for OBP quartiles
(ratios 0.77 / 0.70). This is a descriptive contrast, not a price
effect: quartile medians do not control for age, position, or
contract timing.

**Limits — what HS-1 is not.** (1) HS's design used newly signed FA
contracts; the committed data carries active 2027 contracts with no
signing-date field, so this is a cross-sectional pricing screen —
many of these salaries were set in earlier markets. (2) Skills are
projections, not realized performance; the realized-2026 sensitivity
covers qualified hitters only (fact_stat_lines carries PA ≥ 502
hitters: 42 of Sample S, 55 of Sample C) and is reported as
descriptives only — no regression was run on it. (3) Sample S sits
exactly at the power floor and covers 24 of 30 teams. (4) No skill
coefficient is statistically distinguishable from zero in either
sample, so HS-1 returns NO verdict on "undervalued": the screen is
consistent with the thesis direction on the quartile view and
uninformative on the regression view. Both statements stay in the
workpaper; neither touches the dashboard.

**What HS-2 adds.** A run-value benchmark for OBP vs SLG (from run
expectancy on committed play data or a cited literature value, labeled
as such), the formal coefficient-proportionality test, and — if the
data can support it — a newly signed contract subset so the design
matches Hakes–Sauer's. Only then, and only if the verdict supports
it, does any headline change.

## Cycle 47 addendum — computed context layer for Figure 23 (2026-11-02)

- **New computed artifact:** `data/fig23_rebuild_2026.json`, produced
  by `src/bml_cycle47.py` from two already-committed sources (the
  posted-class trio JSON + the 340-row NPB leaderboard CSV). No new
  external source was needed — the value is computation over data
  already in the repo, guarded by a printed 14/14 verification table
  against the canonical trio dataset (incl. the $60M fee checkpoint
  reproducing Cycle 34's $10.875M exactly).
- **What it adds:** 2026 leaderboard ranks/percentiles (Sato #1 of 19
  CL bats in HR/RBI/OPS; Taira #1 of 11 PL arms in ERA and #1 of 13
  on the 2025 saves board; Itoh #2 of 11 in walk rate, #7 of 11 in
  ERA), Sato K% vs the CL qualified median by year, Itoh's BB% series
  (2024 computed from leaderboard batters-faced), and the posting-fee
  curve with checkpoints ($25M→$5.0M, $50M→$9.375M, $60M→$10.875M,
  $100M→$16.875M).
- **Kept honest:** small qualified-only pools labeled in the honesty
  box; no NPB→MLB translation factor anywhere; Taira 2024 not
  backfilled (absent from the qualified boards).

## Cycle 48 addendum — HS-2: run-value benchmark, formal test, verdict (2026-11-02)

**The missing piece HS-1 named.** HS-1 deferred the formal
Hakes–Sauer proportionality test because no OBP/SLG marginal
run-value benchmark existed in the repo. HS-2 builds one from
committed data only (`src/bml_cycle48.py`, artifact
`data/hakes_sauer_verdict.json`), under defensibility criteria fixed
before the regression was run: both FE coefficients positive, both
p < 0.10, VIF < 10, ratio CI finite and excluding 0 — else the
attempt publishes as failed and no test runs.

**Benchmark (survived, labeled aggregate).** Team-season regression
of runs per PA on OBP and SLG over `fact_team_season` — 480 unique
team-seasons, 2011–2026 (the committed table carries 29 duplicated
2026 rows differing only in the payroll cell's formatting; batting
fields are identical across copies, verified in-build, deduped).
Season fixed effects (primary): OBP +0.262 (SE 0.023, p ≈ 1.8e-26),
SLG +0.278 (SE 0.011, p ≈ 1.9e-85), within R² = 0.865; pooled OLS
sensitivity: OBP +0.199, SLG +0.304, R² = 0.823. VIF 2.45 both;
corr(OBP, SLG) = 0.77. Benchmark ratio rho = 0.94 (delta-method 95%
CI 0.72–1.17); pooled ratio 0.66 (0.44–0.88); per-season ratios
median 1.00. In plain terms: +0.010 of OBP ≈ +15.7 runs per 6,000 PA,
+0.010 of SLG ≈ +16.7. **Ecological limit, stated wherever the
benchmark is used:** team aggregates split OBP/SLG's joint variation
(they co-move through batting average), so this aggregate ratio sits
below what event-level linear-weights analyses of individual plate
appearances imply. It is the ratio this repo's committed data
supports — not an event-level run value.

**Formal test (ran; inconclusive by power).** HS-1 spec A refit from
the committed dataset reproduces HS-1's published coefficients and
SEs exactly (max abs deviation < 0.01, asserted in code — the
covariance matrix is only trusted because the refit matches). Wald
test of beta_OBP − rho·beta_SLG = 0 against the FE benchmark:
Sample S (Spotrac basis, n = 60): contrast −6.49, SE 8.05, p = 0.42.
Sample C (Cot's LRP-2027, n = 82): contrast +1.21, SE 9.43,
p = 0.90. Against the pooled benchmark: p = 0.45 / 0.84. And the
power statement is the finding: **the set of pricing ratios neither
sample can reject at 5% spans the entire scanned range [−20, +20]** —
the test cannot distinguish correct proportional pricing from large
mispricing in either direction at these samples.

**Verdict (rendered verbatim in Figure 24's verdict box).**
INCONCLUSIVE on mispricing. The defensible claim is persistence +
cap-efficiency + low variance — not proven undervaluation. The
descriptive quartile contrast stands as HS-1 left it (top-quartile
contact median $/WAR 0.54× / 0.53× the bottom quartile's, both
bases) and stays labeled a contrast, not a price effect. Design
limit unchanged: active-contract cross-section, not newly-signed
free agents; skills are projections; Sample S at the n = 60 floor.

**Claim hygiene (the five owner-facing surfaces).** Grep of the
dashboard source, EXEC_SUMMARY, TALKTRACK, README, and ONEPAGER for
unqualified "undervalued" / "mispriced" / "underpriced" assertions
about contact/OBP found **none** — the surfaces already carry the
measured language (persistence, cap-efficiency). Hygiene action was
therefore additive, not corrective: the verdict is now stated where
a reader could go looking for the stronger claim — EXEC_SUMMARY's
"do NOT claim" section and TALKTRACK's honesty section both carry
the inconclusive verdict citing Figure 24, and the dashboard's
sources box states the tested status of the pricing claim.

## Cycle 49 addendum — OPT-1: exact optimizer vs the Cycle 26 greedy (2026-11-02)

**The question.** Cycle 26's scenario rosters (Figure 16) are greedy
builds — WAR-per-dollar quota fill, then WAR upgrades while the budget
holds. OPT-1 asks how much WAR that heuristic leaves on the table, by
re-solving the identical problem exactly (`src/bml_cycle49.py`,
artifact `data/optimizer_comparison_2027.json`).

**Identical inputs, asserted in code.** The script imports Cycle 26's
own builder and re-runs it on the identically constructed pool (2027
FA class, Steamer WAR + prior-contract AAV: 199 players; POSMAP and
QUOTAS imported, not copied). Reproduction of
`data/wow_scenarios.json` is exact — spend to the dollar, WAR to 0.05,
identical 26 names per budget — and asserted before anything is
optimized. Prices stay labeled prior-AAV anchors, not predictions.

**Method.** Mixed-integer programming, `scipy.optimize.milp` (HiGHS):
binary player-slot variables maximizing total Steamer WAR subject to
exact positional quotas, 26-man roster, spend <= budget, one slot per
player, and the owners' proposed per-player maximum (prior AAV <= 15%
of the $245.3M cap = $36.795M) as a hard constraint. All three solves
prove optimality (MIP gap 0; dual bounds 48.87 / 52.80 / 54.82 against
incumbents 48.9 / 52.8 / 54.8 after rounding).

**Results (greedy -> optimizer, same budgets).**
Floor $171.2M: 42.0 -> 48.9 WAR (+6.9, +16.4%), spend $171.0M ->
$171.1M, 16 of 26 names shared. Middle $208M: 45.7 -> 52.8 (+7.1,
+15.5%), $207.3M -> $207.8M, 17 shared. Cap $245.3M: 52.3 -> 54.8
(+2.5, +4.8%), $244.6M -> $245.2M, 21 shared. The optimizer's floor
roster beats the greedy's middle roster outright.

**Decomposition (DH sensitivity).** Cycle 26's code states "DH can be
any bat", but with two DH-mapped players in the pool its fallback
never triggers — all three greedy rosters carry Dominic Smith
(0.01 WAR) at DH. The optimizer's primary run applies the stated rule
(Brandon Lowe, 2.32 WAR, at DH in all three optima). A DH-restricted
sensitivity — DH open only to DH-mapped players, exactly the greedy's
effective search space — still finds +5.5 / +5.2 / +0.4 WAR, so most
of the edge at the floor and middle is combinatorics; at the cap the
edge is mostly the DH slot (+2.1 of +2.5), the greedy upgrade pass
having nearly saturated the rest of the roster.

**The 15% rule.** Binds nobody in this pool at prior-AAV anchors (the
dearest free agent anchors at $35.0M < $36.795M), and all three greedy
rosters satisfy it (max AAV $22.0M / $32.0M / $32.0M). It is enforced
in the optimizer regardless, and the checks are on the record in the
artifact and in the gate.

**Scope kept.** Figure 16's rosters and every Story/Boardroom number
are unchanged. Figure 25 (Explorer, Build a Roster) publishes the
comparison; whether the optimizer rosters replace the greedy ones is
OPT-2 / owner territory.

## Cycle 50 addendum — OPT-2: how fragile is the optimum, and the floor with a farm system (2026-11-02)

**The questions.** OPT-1 proved the optima at one set of anchors.
OPT-2 asks (a) how much of that proof survives when the anchors and
projections move, and (b) the Kleinbard rebuttal — a real club does
not build a floor roster from free agents alone. Same solver
(`src/bml_cycle50.py` imports Cycle 49's MILP unchanged), same quotas,
artifact `data/optimizer_sensitivity_2027.json`. Every solve proven
optimal (HiGHS gap 0), and a base-case re-solve reproduces OPT-1's
three rosters exactly — identical IDs, WAR to 0.05, spend to the
dollar — asserted in code before any scenario runs.

**Price sensitivity (uniform scaling of every prior-AAV anchor).**
x0.8: Floor 48.9 -> 53.2 WAR (churn 6 of 26), Middle 52.8 -> 55.5 (6),
Cap 54.8 -> 55.9 (4). x1.2: Floor -> 45.0 (3), Middle -> 48.5 (4),
Cap -> 50.4 (4). A uniform ±20% price swing moves the floor optimum
by about ±4 WAR and swaps at most 6 names — the optimum is a
portfolio, not a knife-edge. The 15% per-player maximum is applied
to the prices in force: at x1.2 two anchors cross it (Rendon
$35.0M -> $42.0M, Skubal $32.0M -> $38.4M) and are excluded.

**Targeted bid-up ("the market bids up your targets").** Only the
26 players on OPT-1's floor roster are scaled x1.2; the floor is
re-solved. Optimum: 45.6 WAR (spend $171.2M at scenario prices) with
6 of the 26 targets swapped out — including the roster's ace (Skubal)
— replaced from the rest of the class at base anchors. Losing the
bidding war on your own list costs 3.3 WAR against the base optimum,
not the build.

**WAR sensitivity (aging haircut).** Steamer WAR x0.85 for players
aged 33+ (93 of the 199 pool players; ages from the FA class file),
base prices. Chosen-under-pessimism values: 48.6 / 52.6 / 54.6.
Re-scored on base WAR, the same rosters are worth 48.8 /
52.8 / 54.8 — within 0.1 WAR of the base optima at every budget
(the middle roster does not change at all), and each carries just
2 players aged 33+. The optima barely lean on old players.

**Mixed pre-arb + FA floor (the rebuttal test).** Pool: the 199 FAs
plus the repo's pre-arb pool — `data/salaries_2026.json` rows with
Spotrac status exactly "Pre-Arbitration" (553 rows, every one at the
file's flat $1,000,000), of which 509 are usable (42 carry no
committed player ID, 1 duplicate ID, 1 has no Steamer WAR; 0 are in
the FA class). Each is priced at $1.0M — the repo's pre-arb
PLACEHOLDER convention (Cycles 41/46), not a measured salary — with
Steamer WAR and positions from the same committed files. Solved at
the floor only, identical quotas: **74.8 WAR for $96.2M**, 19 pre-arb
slots (53.0 WAR — Kurtz 4.46, Wood 4.37, Schlittler 4.36, Ashcraft
3.80, Messick 3.58, Dingler 3.58, Keaschall 3.30, Rice 3.26,
Jensen 3.22, ...) and 7 FA slots, $75.0M of the floor unspent.
Framing, on the record wherever this is used: a real club cannot
sign another club's pre-arb players — this answers what the floor
buys a club that develops or holds pre-arb talent. The floor is
survivable with internal pre-arb production; the mixed roster is
not a shopping list.

**Scope kept.** Explorer/workpaper layer only: Figure 25 gains a
sensitivity strip + the mixed-build result under its facts box
(figure count stays 25); Figure 16, Story and Boardroom are
unchanged, and replacing greedy rosters with optimizer rosters
remains an owner decision.

## Cycle 51 addendum — API-1: Statyx + FastballAPI wired in and SERVING (2026-11-02)

Cycles 44–45 connected and cross-checked the two keyed feeds but no
figure or model read from them — the owner called that out, and this
cycle closes it. One pull per endpoint on 2026-11-02 (all HTTP 200):
Statyx injuries (first page, 50 recent-move records) and standings
(50 rows, no team names — snapshot kept raw only); FastballAPI
get_injuries (190 records) and get_standings 2026 (30 teams).
FastballAPI credits spent: **4 of 500** free monthly credits
(2 calls × 2). Statyx: free.

**Snapshots.** Dated raw envelopes under `data/raw/statyx/` and
`data/raw/fastballapi/` (payload sha256 in each envelope), with
entries in `data/raw/manifest.jsonl` (sha256/rows/status, platform
style). `src/bml_cycle51.py --pull` reproduces the landing via the
vault connector helpers; the default offline build consumes the
committed snapshots and asserts their sha256 before use.

**Curation.** New curated table **fact_il_current** (196 rows,
grain: one row per currently listed injured player) — the union of
the two feeds by normalized name: 190 FastballAPI + 50 Statyx page
records, **44 in both feeds**, 6 Statyx-only (recent moves the full
list has not picked up, e.g. Adolis García), 146 FastballAPI-only.
All 17 prior curated tables reproduce byte-identical.

**Reconciliation.** (a) FA pool: **13 of the 251** players in the
2027 FA class are currently listed injured (García, Quantrill,
Whitlock, Lux, Harvey, Berríos, Giolito, Severino, Laureano, Wick,
Mountcastle, Thompson, Austin). (b) Against the static layer
(fact_il_stints, The Injury Report): 12 of the 13 were on the IL at
the 2026 season end (static file agrees). **1 differs — Garrett
Whitlock**: his two 2026 stints both closed (activated Jun 9 and
Aug 29), but FastballAPI lists him Out — leg fracture, expected
return 2027-02-01. That is a post-season development the static
file cannot know; it is the live layer's first unique contribution
and it is flagged `differs_from_static` in the artifact, not
smoothed over. (c) Standings: FastballAPI 2026 vs committed
kpi_2026 — **30/30 teams agree on wins and runs scored**, zero
diffs (the Cycle 45 result, re-proven on the committed snapshot).

**Serving.** The consumer is the dashboard health figure: a new
"Current IL picture — LIVE feeds" sub-panel (table of the 13 FA-pool
players with status/injury/return, rendered from
`data/il_current_live.json`) under the existing IL-based PA-cap
chart. Figure count stays 25. The sources footer now reads SERVING
for both feeds and names the layer they feed.

## Cycle 52 addendum — SWAP: the optimizer rosters headline (2026-11-02)

Promotion, not new science: `src/bml_cycle52.py` moves the Cycle 49
proven-optimal rosters into `data/wow_scenarios.json` as the
headline `scenarios` (Floor 48.9 WAR / $171.1M, Middle 52.8 /
$207.8M, Cap 54.8 / $245.2M), each with its Cycle 50 ±20%
price-error range attached (Floor 45.0–53.2, Middle 48.5–55.5,
Cap 50.4–55.9). The Cycle 26 greedy rosters are preserved verbatim
under `benchmark_greedy`, stress totals included — Figure 25's
comparison now reads benchmark vs headline. The Cycle 27 uniform
availability stress, recomputed on the new totals by Cycle 27's
exact method: **44.6 / 48.1 / 50.0 WAR** at the pool-mean factor
(0.912), 43.5 / 47.0 / 48.8 at p25; floor/cap ratio **0.892**
(was 0.803). New gate checks pin the headline to the Cycle 49
artifact so the panel cannot drift from the workpaper. Owner
approval on record (2026-11-02); presentation pass per the owner's
standard — short declarative copy, caveats stated once.

## Cycle 53 addendum — FIG-QA: every figure traced, gated (2026-11-02)

Full audit of Figures 1–25: every rendered number traced to a
committed artifact, conventions applied (WAR 1 decimal in panels,
whole-win bands in prose, percentile ranks labeled as ranks, no
undervalued/mispriced assertion outside the Figure 24 verdict,
scenario figures carry Cycle 52 values with ±20% ranges and the
prior-AAV anchor label), and numbering/titles reconciled across
dashboard, Explorer, README, TALKTRACK, EXEC_SUMMARY and ONEPAGER.
The gate now carries one artifact-tied check per figure (FIG-QA
1–25, expected values computed from the artifacts at gate time):
**40 → 65 offline checks (41 → 66 with --live), ALL PASS.**

| Fig | Source artifact(s) | Check method |
|---|---|---|
| 1 | panel_2011_2026.csv | seasons exactly 2011–2026; title in HTML |
| 2 | team_explorer.json | 30 teams; panel present |
| 3 | persistence_ci.json (+ multiyear) | caption pooled r and 457 pairs computed from artifact |
| 4 | runs_panel.json | 2026 slice = 30 rows; title in HTML |
| 5 | quant_core.json | run-diff-only AUC rounds to the titled 0.95 |
| 6 | kpi_2026.json | cap/floor lines + title in HTML; KPI sanity checks |
| 7 | kpi_2026.json | 30 teams, contact/K% non-null; title in HTML |
| 8 | efficiency_2000_2024.csv | file rows = titled 721 team-seasons |
| 9 | projections_2026.json | 30 rows; title in HTML (see owner item) |
| 10 | cap_scenario_2027.json | over-cap count recomputed = 7 |
| 11 | forced_sellers_2027.json | 6 covered; CHC the only uncovered team |
| 12 | projections_2027.json | top-OBP name from artifact leads the panel |
| 13 | mlb_lake.db (local lake) | title present with lake; omission disclosed without |
| 14 | il_current_live.json (+ health) | live counts + pull date rendered from artifact |
| 15 | roster_2027.json | 13 hitters + 13 pitchers |
| 16 | wow_scenarios.json | floor ±20% range in title; SWAP check pins totals to Cycle 49/50 artifacts |
| 17 | robust_validation.json | ≥5 elasticity levers; title in HTML |
| 18 | fg_benchmark_2027.json | title carries artifact r = 0.889 and top-25 overlap 18/25 |
| 19 | savant_test.json | ≥6 trait stabilities; title in HTML |
| 20 | value_metrics_2026.json | hitting/pitching tables ≥12 rows each |
| 21 | pipeline_2026.json | 30 orgs; title in HTML |
| 22 | fa_shopping_2027.json | top-25 list present; title in HTML |
| 23 | posted_class_2026.json + fig23_rebuild_2026.json | $60M fee checkpoint = $10.875M exact; no-translation label shown |
| 24 | hakes_sauer_verdict.json (+ results) | 480 team-seasons in title; HS-2 verdict check |
| 25 | optimizer_comparison_2027.json (+ sensitivity) | floor delta +6.9 WAR in title; OPT artifact checks |

**Defects fixed (7 edits).** Stale numbers (2): the Story stat
card read "r = .83 (pooled, 422 pairs)" — artifacts say pooled
r = 0.843 over 457 pairs → card now .84 / 457; EXEC_SUMMARY's P7
line still said UAT PENDING — corrected to the owner's recorded
MVP-level approval (2026-10-31). Untraceable as stated (2
passages, 3 values): the Story appendix quoted the single latest
season pair (contact r = .90, walk r = .66) as the general result
→ now pooled contact .84 and walk .66–.77 across the four pairs;
EXEC_SUMMARY's "walk discipline at pooled r = 0.72" has no pooled
walk value in any artifact → now the per-pair range 0.66–0.77.
Conventions (4): player-card Steamer WAR printed at 2 decimals →
1; Figure 16 roster-table WAR printed raw (2 dp) → 1; the
bottom-line "roughly half payroll" contradicted the traced
fraction (win-cheap payroll averages ~ a third of the biggest)
→ reworded with both win averages sourced (trio 95.3 vs
rest-of-league 79.4, computed from kpi_2026.json); Story chapter
5 now gives the floor's full ±20% range (45.0–53.2), not only the
low bound. Count mismatches: none open — 25-figure counts agree
in every current doc (the "23 figures" line sits inside the
dated 2026-10-31 integration addendum and is superseded in-file
by the Cycle 52 addendum; left as a dated record).

**Owner item (not changed — claim presentation).** Figure 9's
`projections_2026.json` is written by `src/model_p6.py` as
in-sample fitted values (2025+2026 fit applied to 2026 teams);
the panel title "Model-projected wins by team" carries no
in-sample/diagnostic label, while the demo elsewhere disclaims
team-wins forecasting (formula_prod is gate-annotated DIAGNOSTIC
ONLY). Adding the disclosure is the owner's call.

## Cycle 55 addendum — feed architecture: census / event / validator (2026-11-02)

Owner-directed ("design and architect to use in way thats best for
us and adds value — carpedata"). The two live APIs get fixed roles:
**FastballAPI = census** (canonical current-IL snapshot),
**Statyx = event layer** (recent moves), MLB Stats API stays
standings of record, FastballAPI standings stay validator.

**Statyx standings test — verdict: DROPPED.** The committed
snapshot (50 rows) was inspected for any identifier that joins
deterministically to the platform's team table. The payload's only
identifier field is `team_id` — Statyx-internal values 1794–1823,
25 distinct — with no team name, abbreviation, or code fields
(full field list recorded in `data/il_events.json` metadata). No
crosswalk from Statyx team_id to MLB teams exists anywhere in the
repo (the Chadwick register is player-level; `dim_team` keys on
StatsAPI IDs/abbreviations). Coverage is also partial: 25 rows per
season (2025 and 2026) against 30 platform teams. Disposition:
snapshot retained raw-only for provenance; nothing curates from
it; no code pretends otherwise.

**First event comparison — baseline vs fresh pull: 0 events.**
One fresh call per endpoint (all HTTP 200; 4 FastballAPI credits,
8 of 500 for November including Cycle 51). Standings and
FastballAPI injuries payloads were byte-identical to the baseline.
The Statyx injuries page carried the same 50 players with the same
statuses, types, details, and return dates; the ONLY difference
was every record's `updated_at`, re-stamped to the page-generation
time (20:00:25Z → 22:32:02Z) — verified by hand, field by field.
Statyx therefore timestamps the page, not the move; the stable
per-record field is `date`. Zero movement events is the correct
result and ships as such: `data/il_events.json` records the
baseline pair, the comparison (0 new IL / 0 returned / 0 status
changes, full set and FA-pool view), and the standings verdict.
Landing is state-aware from here on: a payload unchanged after
stripping volatile fields (`updated_at`) is recorded in the
manifest as `ok_no_change` and not re-landed.

**Consumer:** the health figure gains a third row under the live-IL
table — the movement line, rendered from `il_events.json` ("no
movement in the FA pool since the baseline pull", with both
layers' pull dates). Figure count stays 25. The gate gains two
API-2 checks (artifact consistency incl. snapshot sha verification,
and the movement line in the rendered HTML): **65 → 67 offline
checks, ALL PASS**; curated tables **18 → 19** (`fact_il_events`,
0 rows at baseline, contracts pass; all prior parquets
byte-identical). Parity r = 0.889 / 201.

## Cycle 56 addendum — UNC-2: the uncertainty layer (2026-11-02)

Final increment of the owner-approved MIT-gap programme (HS-1 → UNC-2
complete). The headline scenario WAR — 48.9 / 52.8 / 54.8 since the
Cycle 52 swap — carried only its Cycle 50 ±20% price-error range. This
cycle adds the second error layer: delivered WAR under measured
projection error and measured player availability, so the headline is
never a bare number.

**Method (all inputs measured in this repo).** Seeded Monte Carlo,
20,000 draws (`src/bml_cycle56.py`, seed 20261102, artifact reproduces
byte-for-byte on re-run). Error pools: the shipped Marcel's own
out-of-sample residuals, recomputed by importing the Cycle 21 / 24
backtest scripts and replaying their variant-C cross-fitted
construction — hitters: paired (OBP, SLG) residuals, n=196 (targets
2025+2026; pooled MAE 0.0220 / 0.0453); pitchers: ERA residuals, n=59
(MAE 0.711). The replay is asserted against the committed backtest
artifacts before any simulation runs. Availability pools: measured
2025–26 IL factors, hitters n=201 (mean 0.912, Cycle 27) and pitchers
n=102 (mean 0.807). Rate residuals convert to WAR with the Cycle 48
run-value slopes and Steamer's own fitted runs-to-WAR scale (hitters
0.1132 WAR/run, R² 0.482, n=309; pitchers 0.0837, R² 0.215, n=557) —
no outside runs-per-win constant. Per UNC-1's verdict, availability
shapes the distribution only; no point is re-centered.

**Results (delivered WAR, 10th–90th percentile).** Floor 48.9 →
33.0–46.9, median 39.8. Middle 52.8 → 36.0–50.7, median 43.2. Cap
54.8 → 37.6–52.4, median 44.9. The median gap decomposes exactly:
availability level effect −6.8 / −7.2 / −7.5 WAR plus measured
residual bias −2.2 / −2.3 / −2.3 (the backtest pools are not
zero-mean: SLG bias −0.0078, ERA bias +0.078 actual-minus-projected);
the analytic delivered mean reproduces the simulated mean within
0.05 WAR on all three rosters. The Cycle 52 uniform-stress totals
(44.6 / 48.1 / 50.0) fall inside all three intervals. Limits, stated
in the artifact: draws are independent (correlated injury waves
would widen the ranges); Steamer has no in-repo outcome history, so
the pools price the error this repo has measured for this class of
projection (the Marcel spine tracks Steamer at OBP r = 0.889);
non-availability playing-time error is not separately simulated.

**Consumers:** Figure 16 titles (default + all three budget buttons),
Story chapter 5, Boardroom slide 12, and the executive one-pager's
scenario table now carry the intervals; Figure count stays 25.
The gate gains three UNC-2 checks (artifact consistency incl. pool
ties to the committed backtests, rendered intervals on all three
dashboard surfaces, one-pager): **68 → 71 offline checks, ALL PASS**
(72 with --live); platform clean (ingest 25/0, curate 19 tables,
parity r = 0.889 / 201); spellcheck green.
