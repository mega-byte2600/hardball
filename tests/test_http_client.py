from http_client import RETRY_STATUSES, build_retry, session


def test_retry_policy_is_bounded_and_idempotent_only():
    r = build_retry()
    assert r.total == 4
    assert set(r.status_forcelist) == set(RETRY_STATUSES)
    # project rule: 403/429 stop and are reported, never retried
    assert 429 not in r.status_forcelist and 403 not in r.status_forcelist
    assert r.allowed_methods == frozenset({"GET", "HEAD"})
    assert r.respect_retry_after_header


def test_session_is_shared_and_identifies_itself():
    s1, s2 = session(), session()
    assert s1 is s2
    assert s1.headers["User-Agent"].startswith("HARDBALL/")
    assert s1.get_adapter("https://statsapi.mlb.com").max_retries.total == 4


def test_every_external_fetch_uses_the_shared_client():
    """Ratchet: no module may open its own HTTP connection. The only allowed
    exception is the local dashboard probe (not an external data source)."""
    import re
    from pathlib import Path
    allow = {"http_client.py", "accuracy_monitor.py"}
    offenders = []
    for p in sorted((Path(__file__).resolve().parent.parent / "src").glob("*.py")):
        if p.name in allow:
            continue
        src = p.read_text()
        if re.search(r"requests\.(get|post|request)\(|urlopen\(", src):
            offenders.append(p.name)
    assert offenders == [], f"use http_client.get: {offenders}"


def test_keyed_sources_are_single_attempt_never_retried():
    """CarpeDATA invariant: credit-budgeted keyed sources spend each call once."""
    from pathlib import Path
    from http_client import single_attempt_session
    s = single_attempt_session()
    assert s.get_adapter("https://api.statyx.io").max_retries.total == 0
    src = (Path(__file__).resolve().parent.parent / "src" / "keyed_sources.py").read_text()
    assert "single_attempt_session" in src and "http_get(" not in src
