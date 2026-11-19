"""Contract tests on the committed, served dashboard artifact."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "dashboard" / "index.html").read_text()


def test_plotly_is_vendored_and_pinned():
    assert 'src="vendor/plotly-2.35.2.min.js"' in HTML
    vendored = ROOT / "dashboard" / "vendor" / "plotly-2.35.2.min.js"
    assert vendored.exists() and "plotly.js v2.35.2" in vendored.read_text()[:200]


def test_accessibility_basics():
    assert re.search(r'<html lang="en">', HTML)
    assert 'role="main"' in HTML
    assert 'role="figure" aria-label="' in HTML


def test_build_is_deterministic():
    # random UUID div ids made every rebuild a diff; ids are now stable
    assert not re.search(r'id="[0-9a-f]{8}-[0-9a-f]{4}-', HTML)


def test_no_secrets_in_artifact():
    assert not re.search(r"(?i)(x-api-key|api_key)\s*[:=]\s*['\"][A-Za-z0-9]{16,}", HTML)
