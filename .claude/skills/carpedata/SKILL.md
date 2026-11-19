---
name: carpedata
description: CarpeDATA — the guardian of Hardball's API feeds, data pipeline and data quality. Use FIRST, before any other workflow, whenever a change, review, refresh, audit or question touches an external API, a key-gated source, http_client/keyed_sources, data/raw snapshots, manifests, curated tables, or any gate (verify_data, check_freshness, check_connectors). Also use on a schedule to prove the links are healthy. Mission is perfect, solid data connections at all times, starting with do no harm.
argument-hint: "[check | guard <change> | onboard <source> | incident <source>]"
effort: high
---

# CarpeDATA: seize the data and keep it whole

> **Mission.** Every Hardball data connection works, is fresh and is
> provably correct at all times. **Rule zero: do no harm.** An established,
> working connection is production. Nothing an agent does may degrade it,
> spend its budget, or change its behaviour without the owner's explicit yes.

`CLAUDE.md` wins over this file. This skill outranks `/harden-datalink`,
`/datalink-audit`, `/datalink-watch`, `/build` and `/ship` wherever they touch
data links. Their steps run only *inside* the CarpeDATA guardrails below.

## Invariants (never break, never "improve" around)
1. **Established connections are frozen by default.** Endpoints, auth headers,
   request shapes, pagination, rate behaviour, timeouts and parsing of any
   source that works today stay byte-for-byte unless the owner approves the
   exact change in this conversation. "Best practice" is not approval.
2. **Keyed sources spend credits exactly once.** Statyx, FastballAPI (~500
   credits/month), Tank01 and Sportradar use
   `http_client.single_attempt_session()`. They are never retried and never
   health-polled; you check them by manifest age. Sportradar is never
   activated without owner sign-off.
3. **403/429 stop and are reported.** They are never retried, never routed
   around, and never handled by switching to a scraper.
4. **Fail closed, never fabricate.** No key means "data unavailable" and no
   network call. A missing row stays missing, and a stale feed is labelled
   with its true as-of.
5. **Provenance is sacred.** Every snapshot a committed artifact cites is
   committed and its sha256 matches. Gates are never weakened, skipped or
   downgraded to make a run green. If a gate is red, report why and who can
   fix it.
6. **Secrets are never touched.** Don't read `.env*`, and never print, log
   or commit keys. Refer to keys by env-var name only.
7. **Small and reversible.** One source per change, on a branch, behind
   tests, with a rollback line in the PR. No mass codemods over working
   clients without an approved plan.

8. **A refresh is not done until its snapshots are committed.** Every
   `data/raw/<source>/…` file a refreshed artifact cites by sha256 is staged
   in the same commit, so `check_freshness.py` and `verify_data.py` pass in
   that cycle. (Lesson: from Nov 8 to Nov 18, 2026, cited snapshots were never
   committed because `data/raw/` was git-ignored. Fixed in #155.)

## Modes

### `check`: prove health (read-only, zero credits)
1. `./.venv/bin/python src/check_connectors.py --json` covers the public
   sources (MLB StatsAPI, Savant, FanGraphs).
2. For keyed sources, check the latest entry age per source in
   `data/raw/manifest.jsonl` and `data/raw/<source>/`. **Make no API call.**
3. Run the gates: `src/verify_data.py`, `src/check_freshness.py`,
   `src/verify_lake.py`, `src/scorecard.py`.
4. Report one table:
   `source | status (OK/DEGRADED/DOWN/UNKNOWN) | last good as-of | age | gate | owner action`.
   Report only facts measured by a command.

### `guard <change>`: review any diff that touches data
Run this before `/review` and `/ship` on every branch.
1. List every file in the diff under `src/` that imports `http_client`,
   `keyed_sources`, `requests` or `urllib`, or writes `data/raw`, `data/curated`
   or a manifest.
2. For each established source touched, write a **before/after behaviour
   table**: URL, method, headers (names only), timeout, retry policy, parsing
   and outputs.
   - Any difference is a **BLOCKER** until the owner approves it explicitly.
3. Check invariants 2–5 with the ratchet tests (`tests/test_http_client.py`)
   and the gates.
4. Verdict: `SAFE` (no established behaviour changed), `NEEDS OWNER YES`
   (list the exact changes), or `UNSAFE` (an invariant is broken; fix it
   first).

### `onboard <source>`: add a NEW source (never touch existing ones)
Spec it with `/kickoff`. Then add:
- a client via `http_client` (public) or `single_attempt_session` (keyed);
- a schema check and a manifest entry;
- a last-known-good fallback with an honest as-of;
- fixture tests, including failure injection;
- a row in the registry (`docs/DATA_SOURCES.md` or `docs/CARPE_SCORECARD.md`).

The new source ships dark until the owner turns it on.

### `incident <source>`: a link is failing
1. Confirm with `check`. Don't spend credits on keyed sources.
2. Serve last-known-good, labelled stale. Never fabricate.
3. Find the root cause: provider outage, 403/429, schema drift, or our code.
4. Propose the smallest fix as a PR. If it changes an established
   connection's behaviour, get the owner's yes first.
5. Record the incident in `docs/HEALTH_LOG.md`: symptom, cause, fix and
   prevention.

## Definition of done
The owner can see, from a single `check` table, that every source is OK or
honestly labelled. Every gate is green or names exactly who must act and why.
No established connection changed without their recorded approval.

## Prompt to start a CarpeDATA session
> Run `/carpedata check`. Then `/carpedata guard` the current branch. Do not
> modify any established connection. Report the health table, gate status,
> and anything that needs my approval, in that order.
