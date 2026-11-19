"""Content-based freshness and provenance gate for the HARDBALL deck.

Replaces the earlier mtime comparison, which was meaningless in a fresh clone
(every file gets the checkout time) and watched only seven source files.

Checks (all content-based, so they give the same answer on any clone):

1. PROVENANCE: every ``data/...`` path referenced from a committed JSON
   artifact exists in the repository. A dashboard stamp that cites a snapshot
   nobody can re-hash is a reproducibility failure (the Cycle 135 regression).
2. ARTIFACT: the served deck exists and the demo copy is byte-identical to it.
3. AGE: the feed dates stamped in the artifacts (``current_date``,
   ``as_of``, ``fetched_at``) are no older than ``--max-age-days`` relative
   to ``--today`` (default: UTC today). Stale data is reported, and fails the
   gate only with ``--strict-age`` because CI cannot refresh keyed feeds.

Exit codes: 0 = OK, 2 = failure. ``--json`` prints a machine-readable report.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
ART = REPO / "dashboard" / "index.html"
DEMO = REPO / "dashboard" / "hardball_demo.html"
REF_RE = re.compile(r'"(data/[A-Za-z0-9_./-]+\.(?:json|jsonl|csv|parquet))"')
DATE_KEYS = ("current_date", "as_of", "asof", "census_pulled_date",
             "moves_pulled_date", "pulled_date")
ISO_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def tracked_files(repo: Path = REPO) -> set[str]:
    """Paths in the git index; falls back to the working tree outside git."""
    try:
        out = subprocess.run(["git", "-C", str(repo), "ls-files"],
                             check=True, capture_output=True, text=True).stdout
        return set(out.splitlines())
    except (OSError, subprocess.CalledProcessError):
        return {str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file()}


def referenced_paths(data_dir: Path = DATA) -> dict[str, set[str]]:
    """Map each referenced data path to the artifacts that cite it."""
    refs: dict[str, set[str]] = {}
    for f in sorted(data_dir.glob("*.json")):
        for m in REF_RE.finditer(f.read_text(errors="replace")):
            refs.setdefault(m.group(1), set()).add(f.name)
    return refs


def _walk_dates(obj, out: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in DATE_KEYS and isinstance(v, str) and ISO_DATE.match(v):
                out.append(ISO_DATE.match(v).group(1))
            elif isinstance(v, (dict, list)):
                _walk_dates(v, out)
    elif isinstance(obj, list):
        for v in obj[:50]:  # metadata lives near the top; bound the walk
            _walk_dates(v, out)


def feed_dates(data_dir: Path = DATA) -> dict[str, str]:
    """Newest stamped feed date per artifact that declares one."""
    stamps: dict[str, str] = {}
    for f in sorted(data_dir.glob("*.json")):
        try:
            obj = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        found: list[str] = []
        _walk_dates(obj.get("metadata", obj) if isinstance(obj, dict) else obj,
                    found)
        if found:
            stamps[f.name] = max(found)
    return stamps


def run(today: date, max_age_days: int, strict_age: bool) -> dict:
    tracked = tracked_files()
    missing = {p: sorted(src) for p, src in referenced_paths().items()
               if p not in tracked and not (REPO / p).exists()}
    untracked = {p: sorted(src) for p, src in referenced_paths().items()
                 if p not in tracked and (REPO / p).exists()}
    stale = {}
    for name, d in feed_dates().items():
        age = (today - date.fromisoformat(d)).days
        if age > max_age_days:
            stale[name] = {"date": d, "age_days": age}
    artifact_ok = ART.exists() and (not DEMO.exists()
                                     or DEMO.read_bytes() == ART.read_bytes())
    failures = []
    if missing:
        failures.append("provenance: referenced data files missing")
    if untracked:
        failures.append("provenance: referenced data files not committed")
    if not artifact_ok:
        failures.append("artifact: dashboard missing or demo copy differs")
    if stale and strict_age:
        failures.append("age: stale feeds")
    return {"today": today.isoformat(), "max_age_days": max_age_days,
            "missing_references": missing, "untracked_references": untracked,
            "stale_feeds": stale, "artifact_ok": artifact_ok,
            "failures": failures, "ok": not failures}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--today", type=date.fromisoformat,
                    default=datetime.now(timezone.utc).date())
    ap.add_argument("--max-age-days", type=int, default=14)
    ap.add_argument("--strict-age", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)
    rep = run(args.today, args.max_age_days, args.strict_age)
    if args.as_json:
        print(json.dumps(rep, indent=2))
    else:
        for p, src in {**rep["missing_references"],
                       **rep["untracked_references"]}.items():
            print(f"PROVENANCE FAIL: {p} (cited by {', '.join(src)}) is not "
                  "committed — `git add -f` it from the machine that pulled it")
        for name, s in rep["stale_feeds"].items():
            level = "FAIL" if args.strict_age else "WARN"
            print(f"AGE {level}: {name} stamped {s['date']} "
                  f"({s['age_days']}d > {rep['max_age_days']}d)")
        if not rep["artifact_ok"]:
            print("ARTIFACT FAIL: dashboard/index.html missing or "
                  "hardball_demo.html differs — rerun src/dashboard_p6.py")
        print("FRESHNESS OK" if rep["ok"] else
              "FRESHNESS FAIL: " + "; ".join(rep["failures"]))
    return 0 if rep["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
