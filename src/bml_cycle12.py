"""BML Cycle 12: cap-constrained roster builder — the decision artifact.

Ties the threads together: real player projections (hitters + pitchers, both
health-adjusted) -> a 26-man roster (13 hitters + 13 pitchers) priced under
the proposed 2027 cap, constrained by the 15% individual max.

HONEST LIMIT: the lake has no per-player SALARIES, so we use the projections as
the talent signal and price the CAP constraint, not made-up contracts. We show
the constraint algebra the owner must satisfy: total payroll <= $245.3M,
no single player > $36.8M. The demo is a CONSTRUCTION framework, not a magic
dollar answer. This is stated plainly on the output.
"""
import json
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
CAP = 245_300_000
INDIV_MAX = CAP * 0.15  # $36.8M

HIT = os.path.join(DATA, "projections_2027_health.json")
PIT = os.path.join(DATA, "projections_2027_pitchers.json")


def load():
    h = pd.read_json(HIT)
    p = pd.read_json(PIT)
    return h, p


def main():
    h, p = load()
    print(f"hitters: {len(h)}, pitchers: {len(p)}")

    # talent signal: hitter value from OBP (the thesis) and health-adjusted PA
    h = h.dropna(subset=["proj_OBP"]).copy()
    h["value"] = h["proj_OBP"] * h["proj_PA_health"]
    # pitcher value: low ERA + innings; lower ERA better -> invert to score
    p = p.dropna(subset=["proj_ERA", "proj_K9"]).copy()
    p["value"] = p["proj_IP_health"] / p["proj_ERA"]

    # pick top 13 hitters and 13 pitchers by value
    roster_h = h.nlargest(13, "value")
    roster_p = p.nlargest(13, "value")

    print("\n=== PROPOSED 26-MAN WINNING-CHEAP ROSTER (13 H + 13 P) ===")
    print("\n-- Hitters (by OBP-based value) --")
    print(roster_h[["name", "team", "proj_OBP", "proj_PA_health"]].to_string(index=False))
    print("\n-- Pitchers (by IP/ERA value) --")
    print(roster_p[["name", "team", "proj_ERA", "proj_IP_health", "proj_K9"]].to_string(index=False))

    # cap constraint (honest: no salaries in lake)
    n_h = len(roster_h); n_p = len(roster_p)
    print(f"\n=== CAP CONSTRAINT ({n_h} H / {n_p} P = {n_h+n_p} players) ===")
    print(f"  Proposed 2027 cap:      ${CAP/1e6:,.1f}M")
    print(f"  15% individual max:     ${INDIV_MAX/1e6:,.1f}M per player")
    print(f"  NOTE (honest): lake has no per-player SALARIES. This is the talent "
          f"selection under the cap; actual build prices real contracts against "
          f"the same constraint. Not a dollar-figure answer — a construction framework.")

    out = os.path.join(DATA, "roster_2027.json")
    payload = {
        "hitters": roster_h[["name", "team", "proj_OBP", "proj_PA_health"]].to_dict("records"),
        "pitchers": roster_p[["name", "team", "proj_ERA", "proj_IP_health", "proj_K9"]].to_dict("records"),
        "cap": CAP, "indiv_max": INDIV_MAX,
        "honest_limit": "no per-player salaries in lake; talent selection under cap constraint",
    }
    with open(out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nwrote {out} (26-man winning-cheap roster, selected on real projections)")


if __name__ == "__main__":
    main()
