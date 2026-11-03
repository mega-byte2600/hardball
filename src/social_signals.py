"""Low-risk social signal reader for Hardball's free-agent tracker.

Bluesky is the only social source enabled by default. Its public search API
supports unauthenticated reads. Results are *signals*, never transaction
facts: the ticker must keep them separate from MLB-confirmed moves.

Usage:
    python src/social_signals.py --query '"free agent" MLB' --limit 25
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import requests

ENDPOINT = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
UA = {"User-Agent": "HARDBALL/1.0 social-signals"}
TIMEOUT = 30


def search_bluesky(query, limit=25, since=None, until=None):
    params = {"q": query, "limit": min(max(int(limit), 1), 100)}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    response = requests.get(ENDPOINT, params=params, headers=UA, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    signals = []
    for post in payload.get("posts", []):
        record = post.get("record") or {}
        author = post.get("author") or {}
        signals.append({
            "source": "Bluesky",
            "lane": "SOCIAL_SIGNAL",
            "confidence": "unverified",
            "uri": post.get("uri"),
            "indexed_at": post.get("indexedAt"),
            "author": author.get("handle"),
            "text": record.get("text"),
            "author_did": author.get("did"),
        })
    return signals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--since")
    parser.add_argument("--until")
    args = parser.parse_args()
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "query": args.query,
        "signals": search_bluesky(args.query, args.limit, args.since, args.until),
        "promotion_rule": "Never promote SOCIAL_SIGNAL to SIGNED without an MLB transaction record.",
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
