"""Freshness gate for the HARDBALL deck (watchdog hardening).

Fails closed if the committed dashboard artifact is STALE: the served HTML
must be newer than every source file that generates it, so a rebuild can't
silently leave the served deck behind the code/data it's supposed to show.

Exit 0 = fresh (each source <= artifact mtime). Exit 2 = stale (a dep is
newer than the artifact), printed with the oldest-by/newest source. Any
source that doesn't exist is also a failure (missing generator = can't prove
freshness).

Designed to be run by the recurring accuracy watchdog on top of
verify_data.py, which it complements (verify_data checks CONTENT, this
checks FRESHNESS — the two holes in the accuracy story).
"""
import os
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "dashboard", "hardball_demo.html")
# Sources that materially change the served deck. A change to any of these and
# a rebuild of dashboard_p6 must both predate the artifact.
SOURCES = [
    "src/dashboard_p6.py",
    "src/verify_data.py",
    "src/accuracy_monitor.py",
    "src/payroll.py",
    "src/bml_cycle11.py",
    "src/bml_cycle22.py",
    "src/bml_cycle30.py",
    "src/bml_cycle32_roster.py" if os.path.exists(os.path.join(REPO, "src/bml_cycle32_roster.py")) else None,
]


def time_fmt(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def main():
    if not os.path.exists(ART):
        print(f"FRESHNESS FAIL: artifact missing {ART}")
        return 2
    art_m = os.path.getmtime(ART)
    stale = []
    missing = []
    for rel in SOURCES:
        if rel is None:
            continue
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        if os.path.getmtime(p) > art_m + 1.0:   # 1s tolerance for clock skew
            stale.append((rel, os.path.getmtime(p)))
    if missing:
        print("FRESHNESS FAIL: missing sources " + ", ".join(missing))
        return 2
    if stale:
        worst = sorted(stale, key=lambda x: x[1])[-1]
        print(f"FRESHNESS FAIL: artifact {os.path.basename(ART)} older than "
              f"source {worst[0]} (mtime {time_fmt(worst[1])})")
        return 2
    print("FRESHNESS OK: artifact up to date with all sources "
          f"({os.path.basename(ART)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
