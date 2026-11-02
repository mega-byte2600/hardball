#!/usr/bin/env python3
"""Key-gated sources — ready-to-activate, FAIL CLOSED without a key.

Cycle 44 prep (docs: CARPE_SCORECARD "ready-to-activate" entries).
The owner is fine supplying free keys; until a key exists in the
environment, every function here returns a labeled "data unavailable"
result and makes NO network call. No fabricated rows, ever. When a
key is provided, the same functions perform the real request and
return rows labeled with their source; any HTTP block (403/429)
stops the call and reports the block — never routed around.

Sources:
  tank01      Tank01 MLB via RapidAPI (Basic: free forever, 1,000
              hits/mo, no card). Env: TANK01_API_KEY.
              Data: injuries-by-date, rosters, ID crosswalk. NO salaries.
  statyx      Statyx (free key, 1 sport, reference data).
              Env: STATYX_API_KEY. Data: teams/players/schedules/
              standings on free; MLB injuries + WAR endpoints exist
              but free-tier inclusion is UNVERIFIED (Cycle 44 docs).
  fastballapi FastballAPI (500 free credits/mo, no card).
              Env: FASTBALL_API_KEY. Data: pitch-level 2015+, injuries
              snapshot (2 credits/call). NO salaries.
  sportradar  Sportradar MLB v8 trial — DO NOT ACTIVATE until
              mid-November 2026: the 30-day trial window must cover
              Dec 1. Env: SPORTRADAR_API_KEY. Its Player/Team Profile
              `salary` field (annual BASE salary only) is the one real
              contract field in the free-key set; license is internal
              evaluation — owner reads the trial terms at signup.
"""
import os

import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

SOURCES = {
    "tank01": {"env": "TANK01_API_KEY",
               "host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com",
               "base": "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"},
    "statyx": {"env": "STATYX_API_KEY", "base": "https://api.statyx.io/v1"},
    "fastballapi": {"env": "FASTBALL_API_KEY", "base": "https://fastballapi.com/api"},
    "sportradar": {"env": "SPORTRADAR_API_KEY",
                   "base": "https://api.sportradar.com/mlb/trial/v8/en"},
}


def _unavailable(source, reason):
    return {"source": source, "status": "data unavailable",
            "reason": reason, "rows": []}


def fetch(source, path, params=None):
    """GET one endpoint from a key-gated source, fail closed throughout."""
    cfg = SOURCES[source]
    key = os.environ.get(cfg["env"])
    if not key:
        return _unavailable(source, f"no key configured ({cfg['env']} unset)")
    headers = dict(UA)
    if source == "tank01":
        headers["X-RapidAPI-Key"] = key
        headers["X-RapidAPI-Host"] = cfg["host"]
    elif source == "sportradar":
        params = {**(params or {}), "api_key": key}
    else:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = requests.get(cfg["base"] + path, headers=headers,
                         params=params, timeout=45)
    except requests.RequestException as e:
        return _unavailable(source, f"request failed: {str(e)[:100]}")
    if r.status_code in (403, 429):
        return _unavailable(source, f"blocked HTTP {r.status_code} — stopped, not routed around")
    if r.status_code != 200:
        return _unavailable(source, f"HTTP {r.status_code}")
    try:
        body = r.json()
    except ValueError:
        return _unavailable(source, "non-JSON response")
    rows = body if isinstance(body, list) else body.get("body", body)
    return {"source": source, "status": "ok",
            "rows": rows if isinstance(rows, list) else [rows]}


if __name__ == "__main__":
    for s in SOURCES:
        print(s, "->", fetch(s, "/")["status"])
