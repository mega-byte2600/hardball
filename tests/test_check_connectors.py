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
