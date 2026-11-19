"""Shared HTTP session for every Hardball puller.

One place for timeouts, retries and identification, following the
retry-with-exponential-backoff-and-jitter guidance in Google's SRE book
("Handling Overload" / "Addressing Cascading Failures") and the
`urllib3.util.Retry` contract:

* retries only idempotent verbs (GET/HEAD) on connect/read errors and on
  500/502/503/504 (never 403/429: those stop and are reported);
* honours ``Retry-After`` on 503;
* bounded: ``total`` attempts, capped backoff, always a timeout.

Usage::

    from http_client import get
    resp = get("https://statsapi.mlb.com/api/v1/teams", params={"sportId": 1})
"""
from __future__ import annotations

from typing import Any, Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "HARDBALL/1.0 (+https://github.com/mega-byte2600/hardball)"
DEFAULT_TIMEOUT = (10, 30)  # (connect, read) seconds
# 429/403 are NOT retried: project rule (CLAUDE.md) — a rate limit or refusal
# stops the call and is reported, never routed around. Only transient 5xx
# and connection/read errors are retried.
RETRY_STATUSES = (500, 502, 503, 504)

_SESSION: requests.Session | None = None


def build_retry(total: int = 4, backoff_factor: float = 0.5) -> Retry:
    """Return the retry policy used by the shared session."""
    return Retry(
        total=total,
        connect=total,
        read=total,
        status=total,
        backoff_factor=backoff_factor,
        backoff_max=30,
        backoff_jitter=0.25,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )


def session() -> requests.Session:
    """Process-wide session with connection pooling and retries."""
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        adapter = HTTPAdapter(max_retries=build_retry(), pool_maxsize=8)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.headers.update({"User-Agent": USER_AGENT})
        _SESSION = s
    return _SESSION


def get(url: str, params: Mapping[str, Any] | None = None,
        timeout: float | tuple[float, float] = DEFAULT_TIMEOUT,
        **kwargs: Any) -> requests.Response:
    """GET with the shared retry policy and a mandatory timeout."""
    return session().get(url, params=params, timeout=timeout, **kwargs)
