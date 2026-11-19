# Independent review rounds

Each round: an independent reviewer (a separate agent with no access to the
fixer's reasoning) scores six dimensions 1-10; everything below 9 is fixed
against primary sources and the fix is saved as a tagged version
(`review-rN`). The loop stops when every score is 9 or higher.

## Score history

| Round | Version | Code quality | API & data health | UI/UX | Insight | Rigor | Actionability |
|---|---|---|---|---|---|---|---|
| 1 (baseline, pre-fix) | `review-r1` | 3 | 4 | 5 | 6 | 6 | 7 |
| 2 (after r1 fixes) | `review-r2` | 5 | 4 | 6 | 7 | 7 | 7 |

## Round 1 — fixes shipped in `review-r1`

**Code quality (3)**
- Added `pyproject.toml` (ruff + pytest config), `tests/` (16 tests), and
  `.github/workflows/ci.yml`. CI runs lint, the tests, an offline rebuild,
  a check that the rebuilt artifact matches the committed one, the content
  gate, the freshness/provenance gate and the spellcheck.
- Cleared all 53 pyflakes errors in `src/`.
- Builds are deterministic now: Plotly div ids were random UUIDs, so every
  rebuild produced a diff.

**API & data health (4)**
- `src/http_client.py`: one shared session with bounded retries,
  exponential backoff with jitter, `Retry-After` handling and retries only
  on idempotent verbs, following Google SRE *Handling Overload*.
- `check_connectors.py`: the transaction window rolls instead of being
  hard-coded, and errors are printed instead of `HTTP None`.
- `check_freshness.py`: rewritten to check content rather than file times.
  It enforces provenance (every `data/...` path a committed JSON cites must be
  committed), checks that the demo copy is byte-identical, and reports feed
  age.
- `verify_lake.py` now prints a clear message instead of crashing. The lake
  read model now carries `player_id` and `name`.
- `requirements.txt` now pins `pyspellchecker`.
- `.gitignore` now un-ignores keyed-feed snapshot folders, so they can be
  committed and re-hashed.
- **Owner action required:** run `git add -f` on
  `data/raw/{statyx,fastballapi}/injuries_2026-11-18.json` and
  `data/raw/statyx/standings_2026-11-17.json` from the machine that pulled
  them. They are cited by sha256 but were never committed, so gate API-2 and
  the provenance check fail, correctly, until they are.

**UI/UX (5)**
- Plotly 2.35.2 is vendored in `dashboard/vendor/`, with the CDN as a
  fallback only. Rendered offline: 48 of 48 charts, 0 console errors (it was
  0 of 48 with the CDN blocked).
- Accessibility: `lang="en"`, a main landmark, `role="figure"` with an
  `aria-label` on each panel, and a visible navy swatch border.
- A decision brief now sits above the fold, before the glossary.

**Insight / Rigor / Actionability (6 / 6 / 7)**
- `src/forecast_eval.py`: percentile bootstrap CIs, a paired bootstrap, and
  a Diebold–Mariano test with the Harvey–Leybourne–Newbold correction for
  Marcel against naive baselines.
  - **Finding:** Marcel's edge over "repeat last season" is not significant
    at 5% (OBP p = 0.093, SLG p = 0.055, n = 168). This is logged as claim
    N08, NOT SUPPORTED.
- `src/decision_brief.py`: a ranked top-10 of available free agents, with
  delivered WAR, a P10–P90 band from the measured error pools, price and its
  basis, surplus, an act-by date and a same-position fallback.
  - SIGNED players are excluded, and the full list exports to CSV.
  - **Finding:** only one move (Contreras, +$16.6M) clears +$5M surplus at
    market $/WAR. This is logged as claim S25.

## Round 2 — status

Scored by a fresh reviewer after the round-1 fixes. The loop was **paused at the ~500K-token budget** before a round-2 fix pass; see the final session report for the open items and owner decisions.
