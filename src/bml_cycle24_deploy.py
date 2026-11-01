"""Cycle 24: DEPLOY THE CAP POOL — how the floor's forced spending buys the edge.

The 2027 cap+floor hands disciplined winners (CLE +$96.7M, TB +$75.6M) real
money. This computes an ALLOCATION strategy for that pool from our measured
value metrics (wOBA/FIP/contact), NOT per-player salary (which is not in any
public API and we refuse to fabricate). It answers the owner question:
"if I MUST spend up to the floor, what do I buy?" -> persistent-skill
players and control arms at the margin, not one star's pricetag.

Honest labeling: this is a value logic, not a contract simulator.
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from value_metrics import hitting_value, pitching_value

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")


def main():
    # current-year value ranking (wOBA-based hitting value, FIP-based pitching)
    h = hitting_value(2026).drop_duplicates("team")
    p = pitching_value(2026).drop_duplicates("team")
    # leverage value_dollar: wOBA above league average == skill worth paying for
    lg_woba = h["wOBA"].mean()
    h["value_edge"] = h["wOBA"] - lg_woba          # points above league-avg hitter
    # pitching: low FIP = good arm; invert so higher = better value
    p["fip_edge"] = (p["FIP"].max() + 1.0) - p["FIP"]
    # joining clean codes
    # normalize both edges to league z-scores so the split is comparable
    # (raw scales differ wildly: wOBA deltas ~0.001 vs FIP range ~1.0)
    # robust z-scale (MAD) so near-median teams don't flip on a tiny denominator
    def robust_z(s):
        med = s.median()
        mad = (s - med).abs().median()
        if mad and mad > 0:
            return (s - med) / (1.4826 * mad)
        return s * 0
    hz = robust_z(h["value_edge"]); pz = robust_z(p["fip_edge"])
    hd = dict(zip(h["team"], hz))
    pd_ = dict(zip(p["team"], pz))

    # floor pools: teams forced to add (from cap scenario)
    cs = json.load(open(os.path.join(DATA, "cap_scenario_2027.json")))
    pools = {t["team"]: max(t["gap_to_floor"], 0) for t in cs["teams"]}
    pools = {k: v for k, v in pools.items() if v > 0}

    print("=== how each forced-spender should allocate its floor pool ===\n")
    rows = []
    for team, pool in sorted(pools.items(), key=lambda kv: -kv[1]):
        hEdge = hd.get(team, 0.0)
        pEdge = pd_.get(team, 0.0)
        # allocation: lean into whichever side has the bigger value gap
        tot = hEdge + pEdge
        if tot <= 0:
            alloc = "rebuild: neither side is above league value"
            hit_pct = pitch_pct = 0
        else:
            hit_pct = round(hEdge / tot * 100, 1)
            pitch_pct = round(pEdge / tot * 100, 1)
            alloc = (f"spend {hit_pct:.0f}% on persistent contact/walk hitters "
                     f"+ {pitch_pct:.0f}% on control arms "
                     f"(guided by measured wOBA/FIP edge, not one star)")
        rows.append({"team": team, "pool_M": round(pool/1e6, 1),
                     "hit_pct": hit_pct, "pitch_pct": pitch_pct,
                     "allocation": alloc})
        print(f"  {team:>4}  pool ${pool/1e6:>6.1f}M  ->  {alloc}")

    out = {"note": "Allocation logic: for each team forced to spend up to the 2027 floor, "
                   "split the pool toward where it currently has measured relative strength "
                   "(robust-MAD z of team wOBA vs FIP), NOT per-player salary (no public API "
                   "publishes it; nothing fabricated). Read as talent-allocation, "
                   "not a contract simulator.",
           "teams": rows}
    with open(os.path.join(DATA, "cap_pool_deployment.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote data/cap_pool_deployment.json")


if __name__ == "__main__":
    main()
