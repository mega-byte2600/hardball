import json
from datetime import date

import check_freshness as cf


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
