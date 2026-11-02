#!/usr/bin/env python3
"""Key-gated sources — fail closed without a key.

Cycle 44 shipped these as ready-to-activate stubs. Cycle 45
(2026-11-02): Statyx and FastballAPI are CONNECTED and VERIFIED LIVE
via the owner's Secure Vault connectors (custom.statyx /
custom.fastballapi) — see HANDOFF.md "API connections" and
docs/DATA_PLATFORM.md. The keys themselves live in that vault and
are NEVER committed to this repo; in repo context the same code
paths read keys from the environment instead. Until a key exists,
every function here returns a labeled "data unavailable" result
and makes NO network call. No fabricated rows, ever. Any HTTP block
(403/429) stops the call and reports the block — never routed
around.

Sources:
  statyx      Statyx — ACTIVE, VERIFIED LIVE 2026-11-02.
              Base: https://api.statyx.io/v1, key as Bearer header.
              Env: STATYX_API_KEY.
              Verified: GET /mlb/standings -> 200; GET /mlb/injuries
              -> 200 with 16 live records (status, expected return,
              type, comments). The free tier DOES include MLB
              injuries (Cycle 44's UNVERIFIED question, settled).
              NO MLB salaries (contracts endpoint is NBA only).
  fastballapi FastballAPI — ACTIVE, VERIFIED LIVE 2026-11-02.
              Tools are POST https://mcp.fastballapi.com/v1/{tool}
              with a JSON body; the key rides in the x-api-key
              header (per the provider's own Python client). The
              Cycle 44 entry (Bearer at fastballapi.com/api) was
              WRONG and is corrected here. Env: FASTBALL_API_KEY.
              Verified: get_standings {season: 2026} -> 200, 30
              teams; get_injuries {} -> 200, 190 records dated
              2026-11-02. 500 free credits/mo, no card; standings
              and injuries cost 2 credits per call. NO salaries.
  tank01      Tank01 MLB via RapidAPI — DEFERRED by the owner
              2026-11-02 (RapidAPI signup dropped for now;
              supplement only, nothing in the demo depends on it).
              Basic: free forever, 1,000 hits/mo, no card. Key as
              X-RapidAPI-Key header at the RapidAPI host below.
              Env: TANK01_API_KEY.
              Data: injuries-by-date, rosters, ID crosswalk.
              NO salaries.
  sportradar  Sportradar MLB v8 trial — DO NOT ACTIVATE until
              mid-November 2026: the 30-day trial window must cover
              Dec 1. Env: SPORTRADAR_API_KEY. Its Player/Team
              Profile `salary` field (annual BASE salary only) is
              the one real contract field in the free-key set;
              license is internal evaluation — owner reads the
              trial terms at signup.
"""
import os

import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

SOURCES = {
    "tank01": {"env": "TANK01_API_KEY",
               "host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com",
               "base": "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"},
    "statyx": {"env": "STATYX_API_KEY", "base": "https://api.statyx.io/v1"},
    "fastballapi": {"env": "FASTBALL_API_KEY",
                    "base": "https://mcp.fastballapi.com/v1"},
    "sportradar": {"env": "SPORTRADAR_API_KEY",
                   "base": "https://api.sportradar.com/mlb/trial/v8/en"},
}


def _unavailable(source, reason):
    return {"source": source, "status": "data unavailable",
            "reason": reason, "rows": []}


def _finish(source, r):
    if r.status_code in (403, 429):
        return _unavailable(source, f"blocked HTTP {r.status_code} — stopped, not routed around")
    if r.status_code != 200:
        return _unavailable(source, f"HTTP {r.status_code}")
    try:
        body = r.json()
    except ValueError:
        return _unavailable(source, "non-JSON response")
    if isinstance(body, dict) and isinstance(body.get("data"), (dict, list)):
        body = body["data"]  # FastballAPI wraps payloads in "data"
    if isinstance(body, dict):
        for v in body.values():
            if isinstance(v, list):
                return {"source": source, "status": "ok", "rows": v}
        return {"source": source, "status": "ok", "rows": [body]}
    return {"source": source, "status": "ok",
            "rows": body if isinstance(body, list) else [body]}


def fetch(source, path, params=None):
    """Call one endpoint from a key-gated source, fail closed throughout.

    GET sources (statyx, tank01, sportradar): `path` is the URL path
    (e.g. "/mlb/injuries"), `params` the query dict.
    FastballAPI: `path` is the tool name (e.g. "get_injuries") and
    `params` is the JSON body — tools are POST /v1/{tool}.
    """
    cfg = SOURCES[source]
    key = os.environ.get(cfg["env"])
    if not key:
        return _unavailable(source, f"no key configured ({cfg['env']} unset)")
    headers = dict(UA)
    try:
        if source == "fastballapi":
            headers["x-api-key"] = key
            headers["Content-Type"] = "application/json"
            r = requests.post(cfg["base"] + "/" + path.lstrip("/"),
                              headers=headers, json=params or {}, timeout=45)
            return _finish(source, r)
        if source == "tank01":
            headers["X-RapidAPI-Key"] = key
            headers["X-RapidAPI-Host"] = cfg["host"]
        elif source == "sportradar":
            params = {**(params or {}), "api_key": key}
        else:  # statyx — Bearer, verified live 2026-11-02
            headers["Authorization"] = f"Bearer {key}"
        r = requests.get(cfg["base"] + path, headers=headers,
                         params=params, timeout=45)
    except requests.RequestException as e:
        return _unavailable(source, f"request failed: {str(e)[:100]}")
    return _finish(source, r)


if __name__ == "__main__":
    for s in SOURCES:
        probe = "get_standings" if s == "fastballapi" else "/"
        arg = {"season": 2026} if s == "fastballapi" else None
        print(s, "->", fetch(s, probe, arg)["status"])
