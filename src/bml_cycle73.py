#!/usr/bin/env python3
"""Cycle 73: PREDICTION TRANSPARENCY — the conviction layer (RBP-style).

The MIT relevance-based prediction literature (Czasonis/Kritzman et al.,
"Prediction with Transparency: Offensive Value in Baseball", 2025) makes
the defensible point a black-box model cannot: say HOW TRUSTWORTHY each
prediction is BEFORE it is acted on. Their method reports per-prediction
reliability (high-conviction predictions spread far less than
low-conviction ones). We adopt that transparency goal, computed HONESTLY
from committed data rather than reimplementing the Mahalanobis machinery:

  For every 2027 projection (201 hitters), conviction is driven by the
  STABILITY of the committed PRIOR-SEASON persistent inputs (contact %,
  BB %) - the repo's own thesis (inputs persist, outputs don't). The
  player's projected playing time (proj_PA) is NOT used: in this
  committed artifact it is a uniform 500-PA default across all 201 (a
  projection assumption, not a real workload signal), so feeding it in
  would be an invented differentiator - the exact opacity this layer
  exists to remove.

  Labels:
    conviction=HIGH   : 2+ committed prior seasons, contact AND BB tight
    conviction=MEDIUM : 2+ committed prior seasons, one input tight
    conviction=LOW    : 2+ committed prior seasons, neither input tight
    conviction=NO_PRIOR: no committed 2-season prior record (121 players).
                        Honest gap, never inflated - these cap below HIGH.

Inputs (both committed):
  data/projections_2027.json  - proj_PA, proj_OBP, proj_BA (for join).
  data/player_yoy.json        - per-player PRIOR-season contact% / BB%.

Design note: the 80 players with committed prior records are the ones we
can say something about; the 121 without get an honest label instead of a
guessed high score. A HIGH/MEDIUM is a confidence LABEL, not an outcome
guarantee. Exit 1 + FLAG on any projection missing a label.
"""
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, "data")
OUT = os.path.join(DATA, "prediction_conviction_2027.json")


def input_stability(records):
    """Stability of persistent inputs (contact %, BB%) across 2+ committed
    seasons. HIGH / MEDIUM / LOW; NO_RECORD when <2 committed samples."""
    if not records or len(records) < 2:
        return "NO_RECORD"
    contacts = [r.get("contact") for r in records if r.get("contact") is not None]
    bbs = [r.get("BB%") for r in records if r.get("BB%") is not None]
    if len(contacts) < 2 or len(bbs) < 2:
        return "NO_RECORD"
    c_lo, c_hi = min(contacts), max(contacts)
    b_lo, b_hi = min(bbs), max(bbs)
    c_stable = (c_hi - c_lo) < 5.0   # contact tight (< 5 pts spread)
    b_stable = (b_hi - b_lo) < 3.0   # walks tight (< 3 pts spread)
    if c_stable and b_stable:
        return "HIGH"
    if c_stable or b_stable:
        return "MEDIUM"
    return "LOW"


def main():
    proj = json.load(open(os.path.join(DATA, "projections_2027.json")))
    yoy = json.load(open(os.path.join(DATA, "player_yoy.json")))
    by_pid = defaultdict(list)
    for r in yoy:
        by_pid[r["pid"]].append(r)

    out_rows = []
    for p in proj:
        pid = p["player_id"]
        stab = input_stability(by_pid.get(pid, []))
        conv = stab  # conviction == input stability (no invented work axis)
        out_rows.append({
            "player_id": pid,
            "name": p["name"],
            "team": p["team"],
            "proj_PA": p.get("proj_PA"),
            "proj_OBP": p.get("proj_OBP"),
            "proj_BA": p.get("proj_BA"),
            "prior_seasons": len(by_pid.get(pid, [])),
            "input_stability": stab,
            "conviction": conv,
        })

    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NO_PRIOR": 3}
    for r in out_rows:
        if r["conviction"] == "NO_RECORD":
            r["conviction"] = "NO_PRIOR"
        r["input_stability"] = r["conviction"]
    out_rows.sort(key=lambda r: (rank[r["conviction"]],
                                 -(r["proj_OBP"] or 0)))
    counts = Counter(r["conviction"] for r in out_rows)
    if len(out_rows) != len(proj):
        raise SystemExit("FLAG: row count mismatch")
    if any(r["conviction"] not in rank for r in out_rows):
        raise SystemExit("FLAG: unlabeled projection present")

    def top(k):
        return [r for r in out_rows if r["conviction"] == k][:8]

    out = {
        "cycle": 73,
        "question": "For every 2027 projection, how trustworthy is it BEFORE you act on it?",
        "method": (
            "Transparency (RBP conversation: per-prediction reliability) from "
            "committed PRIOR-season data only. input_stability = spread of "
            "committed prior-season contact% (tight if <5.0 pts) and BB% "
            "(tight if <3.0 pts) across 2+ seasons; HIGH=BOTH tight, "
            "MEDIUM=one, LOW=neither, NO_PRIOR=no committed 2-season record. "
            "projected PA (proj_PA) is deliberately NOT used because in this "
            "committed artifact it is a uniform 500-PA default for all 201 — "
            "an invented workload axis would reproduce the opacity this "
            "layer exists to remove."
        ),
        "caveat": (
            "A HIGH/MEDIUM is a confidence LABEL from committed inputs, not a "
            "guaranteed outcome. The 121 players with no committed 2-season "
            "record are honestly labeled NO_PRIOR (cap below HIGH), because "
            "guessing high for a player we have no history on would be the "
            "black-box behavior this layer is built to stop."
        ),
        "counts": dict(counts),
        "n": len(out_rows),
        "n_with_prior_record": counts["HIGH"] + counts["MEDIUM"] + counts["LOW"],
        "high_top": top("HIGH"),
        "medium_top": top("MEDIUM"),
        "no_prior_top": top("NO_PRIOR"),
        "rows": out_rows,
        "sources": [
            "data/projections_2027.json (Marcel, 201 hitters)",
            "data/player_yoy.json (committed prior-season contact/BB%)",
            "MIT RBP: Prediction with Transparency — Offensive Value in Baseball (2025), docs/LITERATURE_SPINE.md [18]",
        ],
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}: {len(out_rows)} projections — " +
          ", ".join(f"{k}={v}" for k, v in sorted(counts.items(),
                                                  key=lambda kv: rank[kv[0]])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
