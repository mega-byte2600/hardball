"""Headless layout and interaction gate for the generated HARDBALL dashboard.

Usage: python src/verify_dashboard_layout.py [--screenshot-dir /tmp/hardball-qa]
Requires requirements-dev.txt and Chromium (see AGENTS.md).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = (320, 375, 390, 768, 1024, 1440, 2048)
MODES = ("story", "boardroom", "explorer")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--screenshot-dir", type=Path,
        default=Path("/tmp/hardball-dashboard-qa"),
        help="Write visual review screenshots here (default: /tmp/hardball-dashboard-qa)",
    )
    args = parser.parse_args()
    page_file = ROOT / "dashboard" / "index.html"
    if not page_file.is_file():
        print(f"FAIL: generated dashboard missing: {page_file}")
        return 1

    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/dashboard/"
    for _ in range(50):
        try:
            with urlopen(url, timeout=0.5):
                break
        except Exception:
            if server.poll() is not None:
                print("FAIL: local dashboard server exited before serving the page")
                return 1
            time.sleep(0.1)
    else:
        server.terminate()
        print("FAIL: local dashboard server did not become ready")
        return 1

    failures: list[str] = []
    browser_errors: list[str] = []
    checked = []
    team_choices_checked = 0
    args.screenshot_dir.mkdir(parents=True, exist_ok=True)
    # Prefer Playwright's pinned browser. System Chromium may be a wrapper or
    # run under a sandbox that blocks its process-singleton socket. Set
    # CHROMIUM_PATH only when intentionally using a compatible local build.
    executable = os.environ.get("CHROMIUM_PATH")
    try:
        with sync_playwright() as playwright:
            launch_args = {"headless": True}
            if executable:
                launch_args["executable_path"] = executable
            browser = playwright.chromium.launch(**launch_args)
            page = browser.new_page(viewport={"width": 1440, "height": 1000},
                                    device_scale_factor=1)
            page.on("pageerror", lambda error: browser_errors.append(str(error)))
            page.on("console", lambda message: browser_errors.append(message.text)
                    if message.type == "error" else None)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function(
                "window.Plotly && document.querySelectorAll('.plotly-graph-div').length >= 20",
                timeout=60000,
            )
            page.wait_for_function(
                "[...document.querySelectorAll('.plotly-graph-div')].filter(g => g.data).length >= 20",
                timeout=60000,
            )

            for width in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": 960})
                for mode in MODES:
                    page.locator(f"#btn-{mode}").click()
                    page.wait_for_function(
                        "mode => { const m=document.querySelector('#mode-'+mode); "
                        "return m && getComputedStyle(m).display !== 'none' && "
                        "[...m.querySelectorAll('.plotly-graph-div')].every(g => g.data); }",
                        arg=mode,
                        timeout=30000,
                    )
                    metrics = page.evaluate(
                        """mode => {
                          const root = document.documentElement;
                          const section = document.querySelector('#mode-' + mode);
                          const panels = [...section.querySelectorAll('[data-figure]')];
                          const overflows = panels.map(panel => {
                            const graph = panel.querySelector('.plotly-graph-div');
                            const p = panel.getBoundingClientRect();
                            const g = graph && graph.getBoundingClientRect();
                            return {
                              figure: panel.dataset.figure,
                              scroll: panel.scrollWidth - panel.clientWidth,
                              left: g ? Math.round(g.left - p.left) : 0,
                              right: g ? Math.round(p.right - g.right) : 0,
                            };
                          });
                          const controls = [...section.querySelectorAll('[data-figure="2"] .team-explorer-select')];
                          const controlGraph = controls.map(select => {
                            const panel = select.closest('[data-figure="2"]');
                            const chart = panel.querySelector('.plotly-graph-div');
                            const c = select.getBoundingClientRect();
                            const g = chart.getBoundingClientRect();
                            return {controlBottom: c.bottom, chartTop: g.top};
                          });
                          return {
                            viewport: innerWidth,
                            documentWidth: root.scrollWidth,
                            panels: panels.length,
                            overflows,
                            controlGraph,
                            visibleCharts: [...section.querySelectorAll('.plotly-graph-div')]
                              .filter(g => g.getBoundingClientRect().width > 0).length,
                          };
                        }""",
                        mode,
                    )
                    if metrics["documentWidth"] > width:
                        failures.append(f"{width}px/{mode}: document overflow {metrics['documentWidth']}px")
                    if metrics["panels"] < 20 or metrics["visibleCharts"] < 20:
                        failures.append(
                            f"{width}px/{mode}: only {metrics['panels']} panels, "
                            f"{metrics['visibleCharts']} visible plots")
                    for panel in metrics["overflows"]:
                        if panel["scroll"] > 2 or panel["left"] < -2 or panel["right"] < -2:
                            failures.append(
                                f"{width}px/{mode}/fig{panel['figure']}: panel/chart overflow {panel}")
                    for positions in metrics["controlGraph"]:
                        if positions["controlBottom"] > positions["chartTop"] + 1:
                            failures.append(
                                f"{width}px/{mode}/fig2: selector overlaps chart {positions}")
                    checked.append({"width": width, "mode": mode,
                                    "panels": metrics["panels"],
                                    "document_width": metrics["documentWidth"]})

                    if width in (390, 1440, 2048):
                        page.locator(f"#mode-{mode} [data-figure='2']").first.scroll_into_view_if_needed()
                        page.screenshot(path=str(args.screenshot_dir / f"{mode}-{width}.png"),
                                        full_page=False)

            # Exercise all 30 selections, including the two teams without an
            # AA/AAA index row, and prove the same selection reaches each mode.
            page.locator("#btn-explorer").click()
            selector = page.locator("#team-selector-explorer")
            option_count = selector.locator("option").count()
            if option_count != 30:
                failures.append(f"team selector has {option_count} options, expected 30")
            for index in range(option_count):
                team_choices_checked += 1
                option = selector.locator(f"option[value='{index}']")
                team_name = option.get_attribute("data-facts")
                facts = json.loads(team_name or "{}")
                selector.select_option(str(index))
                page.wait_for_function(
                    "index => { const controls=[...document.querySelectorAll('[data-figure=\"2\"] .team-explorer-select')]; "
                    "return controls.length===3 && controls.every(c=>c.value===String(index)) && "
                    "controls.every(c=>c.closest('[data-figure=\"2\"]').querySelector('[data-team-fact=\"team\"]').textContent===JSON.parse(c.selectedOptions[0].dataset.facts).team); }",
                    arg=index,
                    timeout=10000,
                )
                state = page.evaluate(
                    """index => {
                      const selectors=[...document.querySelectorAll('[data-figure="2"] .team-explorer-select')];
                      const expected=JSON.parse(selectors[0].selectedOptions[0].dataset.facts);
                      const panels=selectors.map(s=>s.closest('[data-figure="2"]'));
                      const graphs=panels.map(p=>p.querySelector('.plotly-graph-div'));
                      return {
                        team: expected.team,
                        titles: graphs.map(g=>g.layout && g.layout.title && g.layout.title.text),
                        selectedVisible: graphs.map(g=>g.data[index].visible !== false),
                        summary: panels.map(p=>p.querySelector('[data-team-fact="pipeline"]').textContent),
                        missing: panels.map(p=>p.querySelector('[data-team-fact="hitter"]').textContent),
                      };
                    }""",
                    index,
                )
                if not all(state["selectedVisible"]):
                    failures.append(f"{facts.get('team')}: selected radar trace is hidden")
                if not all(title == f"{facts.get('team')} · 2026 team profile" for title in state["titles"]):
                    failures.append(f"{facts.get('team')}: chart titles did not synchronize: {state['titles']}")
                if facts.get("pipeline") == "Not ranked" and not all(
                        text == "Not ranked" for text in state["summary"]):
                    failures.append(f"{facts.get('team')}: missing pipeline rank not labeled")
            browser.close()
    except Exception as error:
        message = str(error)
        if "Executable doesn't exist" in message or "playwright install" in message.lower():
            message += " (install the pinned browser with: python -m playwright install chromium)"
        failures.append(f"browser run failed: {message}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

    if browser_errors:
        failures.extend(f"browser error: {message}" for message in browser_errors)
    print(json.dumps({"viewports_modes_checked": len(checked),
                      "team_choices_checked": team_choices_checked,
                      "screenshots": str(args.screenshot_dir),
                      "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
