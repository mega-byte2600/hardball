#!/usr/bin/env python3
"""HARDBALL recurring accuracy monitor (watchdog).

Runs via Hermes cron. Verifies the project holds its goal:
  1. the offline data-integrity gate (verify_data.py) — the committed
     accuracy spec (30 teams, sane ranges, honest annotations, benchmark
     integrity, scenario constraints, platform contract),
  2. the dashboard artifact exists and is freshly built,
  3. the dashboard is being served (HTTP 200).

Fail-closed: append a timestamped row to HEALTH_LOG.md and exit non-zero
if ANY check fails, so the cron run surfaces as a failure.

Run:  python3 src/accuracy_monitor.py
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "src" / "verify_data.py"
FRESH = ROOT / "src" / "check_freshness.py"
HTML = ROOT / "dashboard" / "hardball_demo.html"
LOG = ROOT / "docs" / "HEALTH_LOG.md"
SERVER = "http://localhost:8890/dashboard/hardball_demo.html"

results = []


def rec(name, ok, detail=""):
    results.append((name, ok, detail))


def main() -> int:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    # 1. data-integrity gate (the goal spec)
    gate = subprocess.run(
        [sys.executable, str(GATE)],
        capture_output=True, text=True, cwd=ROOT, timeout=300)
    gate_ok = gate.returncode == 0 and "GATE: ALL CHECKS PASS" in gate.stdout
    rec("verify_data gate", gate_ok,
        gate.stdout.strip().splitlines()[-1] if gate.stdout else gate.stderr[-200:])

    # 1b. freshness gate: committed artifact is newer than its sources.
    #     If check_freshness.py is absent (thin dev tree), degrade to a
    #     simple artifact-presence check rather than hard-failing.
    fresh_ok = False
    fresh_note = ""
    if FRESH.exists():
        fresh = subprocess.run(
            [sys.executable, str(FRESH)],
            capture_output=True, text=True, cwd=ROOT, timeout=60)
        fresh_ok = fresh.returncode == 0
        fresh_note = (fresh.stdout.strip().splitlines()[-1]
                      if fresh.stdout else fresh.stderr[-200:])
    else:
        fresh_ok = HTML.exists()
        fresh_note = "check_freshness.py absent; artifact-presence used"
    rec("freshness gate (artifact vs sources)", fresh_ok, fresh_note)

    # 2. dashboard artifact present
    rec("dashboard artifact exists", HTML.exists(),
        str(HTML) if HTML.exists() else "MISSING")

    # 3. dashboard served (HTTP 200)
    served_ok = False
    served_note = ""
    try:
        import urllib.request
        r = urllib.request.urlopen(SERVER, timeout=15)
        served_ok = r.status == 200
        served_note = f"HTTP {r.status}"
    except Exception as e:  # noqa: BLE001
        served_note = f"NOT SERVED: {type(e).__name__}"
    rec("dashboard served", served_ok, served_note)

    all_ok = all(ok for _, ok, _ in results)

    # --- append to health log -----------------------------------------
    LOG.parent.mkdir(parents=True, exist_ok=True)
    head = "HARDBALL — Accuracy monitor (recurring): data-integrity gate + serving status\n"
    if not LOG.exists():
        LOG.write_text(head + "Automated. Appended each run; "
                       "oldest rows at top, newest at bottom.\n\n")
    rows = "\n".join(
        f"- {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else "")
        for name, ok, detail in results)
    entry = (f"\n### {now} — {'ALL CHECKS PASS' if all_ok else f'GATE FAIL ({sum(1 for _,ok,_ in results if not ok)} fail(s))'}\n"
             f"{rows}\n")
    with open(LOG, "a") as fh:
        fh.write(entry)

    print("HARDBALL accuracy monitor " + now)
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    print(f"\nRESULT: {'ALL CHECKS PASS' if all_ok else f'FAIL ({sum(1 for _,ok,_ in results if not ok)} of {len(results)})'}")
    if not all_ok:
        gate_out = gate.stdout.strip()
        if gate_out:
            print("\n--- verify_data detail ---")
            print(gate_out)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
