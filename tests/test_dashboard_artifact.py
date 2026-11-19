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


def test_research_is_a_top_level_destination():
    main = HTML.index('id="main"')
    assert HTML.index('class="evidence-entry"', main) < HTML.index('class="keybox"', main)
    assert 'class="evidence-tab" href="../docs/EVIDENCE.html"' in HTML
    assert (ROOT / "docs" / "EVIDENCE.html").exists()


def test_shared_chart_presentation_loads_before_figures():
    assert HTML.index('assets/chart-readability.js') < HTML.index('Plotly.newPlot(')
    assert (ROOT / "dashboard" / "hardball_demo.html").read_text() == HTML
