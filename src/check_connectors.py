"""Repeatable live-source smoke check for the Hardball data layer.

This checks only public endpoints that the pipeline is allowed to use. It does
not treat Spotrac HTML as an API: Spotrac remains a cached market-value source
because it publishes no stable public API and rate-limits automated pulls.

Usage:
    python src/check_connectors.py
    python src/check_connectors.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import requests

UA = {"User-Agent": "HARDBALL/1.0 connector-health"}
TIMEOUT = 30


def check(name, url, params=None, validator=None):
    try:
        response = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
        result = {
            "name": name,
            "url": response.url,
            "http_status": response.status_code,
            "ok": response.ok,
        }
        if response.ok and validator:
            result.update(validator(response))
        return result
    except requests.RequestException as exc:
        return {"name": name, "url": url, "http_status": None, "ok": False,
                "error": str(exc)}


def _mlb_free_agents(response):
    payload = response.json()
    rows = payload.get("freeAgents", [])
    return {"records": len(rows), "validated": bool(rows)}


def _json_nonempty(response):
    payload = response.json()
    if isinstance(payload, dict):
        nonempty = bool(payload)
    else:
        nonempty = bool(payload)
    return {"records": len(payload) if hasattr(payload, "__len__") else None,
            "validated": nonempty}


def _csv_nonempty(response):
    return {"bytes": len(response.content),
            "validated": len(response.content) > 100}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    checks = [
        check(
            "MLB free-agent eligibility",
            "https://statsapi.mlb.com/api/v1/people/freeAgents",
            {"season": "2026"},
            _mlb_free_agents,
        ),
        check(
            "MLB transactions",
            "https://statsapi.mlb.com/api/v1/transactions",
            {"startDate": "2026-11-01", "endDate": "2026-11-03", "sportId": "1"},
            _json_nonempty,
        ),
        check(
            "Baseball Savant expected statistics CSV",
            "https://baseballsavant.mlb.com/expected_statistics",
            {"type": "batter", "year": "2026", "position": "",
             "team": "", "min": "25", "csv": "true"},
            _csv_nonempty,
        ),
        check(
            "FanGraphs Steamer projections",
            "https://www.fangraphs.com/api/projections",
            {"type": "steamer", "stats": "bat", "pos": "all",
             "team": "0", "players": "0", "lg": "all"},
            _json_nonempty,
        ),
    ]
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "required_sources": checks,
        "spotrac": {
            "status": "cached_html_only",
            "reason": "No stable public API; market pulls remain rate-limited.",
        },
    }
    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        for item in checks:
            state = "PASS" if item["ok"] and item.get("validated", True) else "FAIL"
            print(f"{state:4} {item['name']}: HTTP {item['http_status']} "
                  f"({item.get('records', item.get('bytes', 'n/a'))})")
        print("Spotrac: CACHED HTML ONLY (not a public API)")
    raise SystemExit(0 if all(x["ok"] and x.get("validated", True) for x in checks) else 1)


if __name__ == "__main__":
    main()
