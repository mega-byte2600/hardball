import json
from datetime import date

import check_freshness as cf

cf._orig_feed_dates = cf.feed_dates


def test_referenced_paths_and_dates(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({
        "metadata": {"current_date": "2026-11-01",
                     "current": {"file": "data/raw/x/snap.json"}}}))
    refs = cf.referenced_paths(tmp_path)
    assert refs == {"data/raw/x/snap.json": {"a.json"}}
    assert cf.feed_dates(tmp_path) == {"a.json": "2026-11-01"}


def test_repo_gate_runs_and_reports(monkeypatch):
    rep = cf.run(date(2026, 11, 19), max_age_days=10_000, strict_age=False)
    assert set(rep) >= {"missing_references", "stale_feeds", "artifact_ok", "ok"}
    assert rep["artifact_ok"], "dashboard/index.html and hardball_demo.html must match"


def test_age_check_is_strict_only_when_requested(tmp_path, monkeypatch):
    (tmp_path / "x.json").write_text(json.dumps({"metadata": {"as_of": "2026-01-01"}}))
    monkeypatch.setattr(cf, "feed_dates", lambda data_dir=None: cf.__dict__["_orig_feed_dates"](tmp_path))
    monkeypatch.setattr(cf, "referenced_paths", lambda data_dir=None: {})
    lenient = cf.run(date(2026, 11, 19), max_age_days=14, strict_age=False)
    strict = cf.run(date(2026, 11, 19), max_age_days=14, strict_age=True)
    assert "x.json" in lenient["stale_feeds"]
    assert "age: stale feeds" in strict["failures"] and "age: stale feeds" not in lenient["failures"]


def test_untracked_reference_is_a_provenance_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "referenced_paths", lambda data_dir=None: {"data/raw/none.json": {"a.json"}})
    monkeypatch.setattr(cf, "feed_dates", lambda data_dir=None: {})
    rep = cf.run(date(2026, 11, 19), 14, False)
    assert "data/raw/none.json" in rep["missing_references"]
    assert not rep["ok"]
