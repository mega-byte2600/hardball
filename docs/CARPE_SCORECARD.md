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
