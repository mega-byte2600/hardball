"""Change-trigger watch for HARDBALL (owner request 2026-11-03).

Fingerprints every committed artifact that feeds a dashboard output and
every live feed artifact; when an input variable changes enough to move a
downstream output, it (1) writes a dated CHANGE entry to docs/HEALTH_LOG.md
and (2) exits non-zero so the cron that hosts it can trigger a rebuild +
redeploy of the public site. Deliberately deterministic and timestamp-free:
only the input VALUES that can change an output are hashed, never a pull
timestamp that would make every tick look "changed" (the product-price-monitor
suppress-duplicates rule, applied to a data pipeline).

The dashboard serves the public site at mega-byte2600.github.io/hardball/,
so "the site updates" is the alert the room (and the owner's inbox via the
caller) gets. When the owner wires a messaging target, this script's exit
code is the single trigger for push delivery too.

Design:
- fail closed: any artifact that feeds an output but is missing -> hashed as a
  sentinel so a dropped file is a change (treated as a break, reporting it is
  correct), NEVER silently skipped to "pass".
- freshness is NOT double-counted: the accuracy monitor already gates served-vs-
  source age; this watch gates VALUE drift that would change a rendered number.
- cycles are recorded so a change can be seen but not re-fired on every tick.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HEALTH = os.path.join(ROOT, "docs", "HEALTH_LOG.md")
STATE = os.path.join(DATA, ".change_watch_state.json")

# Every committed artifact that can move a shown output, keyed by what it feeds.
# Values are never the whole file (huge); they are the STRICT subset that changes
# a rendered number. Use a stable, reproducible extract fn per artifact.
WATCHED = {
    # Free-agency wire -> ticker panel + shopping list health cards.
    "tracker_ticker": {
        "path": "tracker_ticker_2026.json",
        "extract": lambda d: sorted(
            (i["player"], i["lane"], i.get("move_type"), i["source_pubdate"])
            for i in d["items"]
        ),
    },
    # Surplus-value panel (Cycle 71) + shopping list.
    "surplus_value": {
        "path": "surplus_value_2027.json",
        "extract": lambda d: sorted(
            (r["name"], r.get("surplus_usd"), r.get("steamer_war"))
            for r in d.get("top_surplus", [])
        ),
    },
    # Conviction layer (Cycle 73) on Figure 12.
    "prediction_conviction": {
        "path": "prediction_conviction_2027.json",
        "extract": lambda d: sorted(
            (r["name"], r.get("conviction")) for r in d.get("rows", [])
        ),
    },
    # Projections drive Figures 9-19, roster optimizer, benchmark.
    "projections": {
        "path": "projections_2027.json",
        "extract": lambda d: sorted(
            (r["name"], round(r.get("proj_OBP", 0), 4), round(r.get("proj_SLG", 0), 4))
            for r in d
        ),
    },
    # Live IL picture -> health figure.
    "il_current": {
        "path": "il_current_live.json",
        "extract": lambda d: sorted(
            (r.get("player") or r.get("name"), r.get("status"), r.get("return_date"))
            for r in d
        ),
    },
    # Evidence surveillance -> Figure 14 footnote.
    "evidence": {
        "path": "evidence_surveillance.json",
        "extract": lambda d: sorted(
            (c.get("finding") or c.get("title")) for lane in d.values() if isinstance(lane, list) for c in lane
        ),
    },
}


def _hash(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _extract(cfg):
    """Reproducible hash of the values that change an output. Fail closed."""
    path = os.path.join(DATA, cfg["path"])
    if not os.path.exists(path):
        return "ABSENT:" + cfg["path"]  # dropped artifact is a change -> reported
    try:
        data = json.load(open(path))
    except Exception as e:  # corrupt artifact -> change -> reported (fail closed)
        return "CORRUPT:" + cfg["path"] + ":" + str(e)
    try:
        return _hash(cfg["extract"](data))
    except Exception:
        # extractor that fails must not silently pass; treat as changed sentinel
        return "EXTRACT_FAIL:" + cfg["path"]


def _load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE))
        except Exception:
            return {"first_seen": {}, "last_change": None}
    return {"first_seen": {}, "last_change": None}


def main():
    now = datetime.now(timezone.utc)
    state = _load_state()
    current = {name: _extract(cfg) for name, cfg in WATCHED.items()}
    first_seen = state.get("first_seen", {})
    changed = []
    for name, h in current.items():
        if name not in first_seen:
            first_seen[name] = h  # baseline on first run; NOT a change
            continue
        if first_seen[name] != h:
            changed.append(name)
            first_seen[name] = h

    state["first_seen"] = first_seen
    state["last_check"] = now.isoformat()

    if changed:
        state["last_change"] = now.isoformat()
        state["changed_at"] = {c: now.isoformat() for c in changed}
        json.dump(state, open(STATE, "w"))
        line = (
            f"### {now.strftime('%Y-%m-%d %H:%M:%S')} UTC — CHANGE-TRIGGER: "
            f"inputs moved, outputs to rebuild: {', '.join(sorted(changed))}"
        )
        with open(HEALTH, "a") as f:
            f.write("\n" + line + "\n")
        print(f"CHANGE: {', '.join(sorted(changed))}")
        sys.exit(3)  # non-zero -> cron re-runs the affected build + redeploy
    else:
        json.dump(state, open(STATE, "w"))
        print("NO CHANGE")
        sys.exit(0)


if __name__ == "__main__":
    main()
