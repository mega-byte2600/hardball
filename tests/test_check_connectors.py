from datetime import date

import check_connectors as cc


def test_transaction_window_is_rolling():
    w = cc.transaction_window(date(2026, 11, 19))
    assert w == {"startDate": "2026-11-12", "endDate": "2026-11-19", "sportId": "1"}


def test_check_reports_error_text_on_network_failure(monkeypatch):
    import requests

    def boom(*a, **k):
        raise requests.ConnectionError("proxy refused")

    monkeypatch.setattr(cc, "get", boom)
    res = cc.check("x", "https://example.invalid")
    assert res["ok"] is False and "proxy refused" in res["error"]


def test_failed_check_never_marks_validated(monkeypatch):
    class R:
        url, status_code, ok = "u", 503, False
    monkeypatch.setattr(cc, "get", lambda *a, **k: R())
    res = cc.check("x", "https://example.invalid", validator=lambda r: {"validated": True})
    assert res["ok"] is False and "validated" not in res


def test_validator_runs_on_success(monkeypatch):
    class R:
        url, status_code, ok = "u", 200, True
    monkeypatch.setattr(cc, "get", lambda *a, **k: R())
    res = cc.check("x", "https://example.invalid", validator=lambda r: {"validated": True, "records": 3})
    assert res["ok"] and res["records"] == 3
