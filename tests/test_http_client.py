from http_client import RETRY_STATUSES, build_retry, session


def test_retry_policy_is_bounded_and_idempotent_only():
    r = build_retry()
    assert r.total == 4
    assert set(r.status_forcelist) == set(RETRY_STATUSES)
    assert 429 in r.status_forcelist
    assert r.allowed_methods == frozenset({"GET", "HEAD"})
    assert r.respect_retry_after_header


def test_session_is_shared_and_identifies_itself():
    s1, s2 = session(), session()
    assert s1 is s2
    assert s1.headers["User-Agent"].startswith("HARDBALL/")
    assert s1.get_adapter("https://statsapi.mlb.com").max_retries.total == 4
