"""Cycle 22: 2027 CAP-SCENARIO — what the hard cap forces on every team.

Given real 2026 payroll (Spotrac) and the owners' proposed 2027 hard cap
($245.3M) / floor ($171.2M) / 15% individual max, compute for each team:
  - cap_overage: how much payroll exceeds the cap (must cut)
  - to_cap: the cut required if over; headroom if under
  - to_floor: how far under the floor (must spend up - matters for small-market)
Flags the rich teams that must cut 30-50% and the poor ones forced to spend.

Tells the Moneyball story: the cap converts "win cheaply" from an option
to a necessity for the middle, while the floor forces the floor teams to
spend the new dollars wisely (not on one star). Real data only.
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from payroll import PAYROLL_2026, load_payroll_frame

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
CAP, FLOOR = 245_300_000, 171_200_000


def main():
    # real 2026 payrolls (Spotrac opening day, live-fetched). PAYROLL_2026
    # maps code -> (team_name, record, '$payroll_string').
    def _money(v):
        if isinstance(v, tuple):
            v = v[2]  # the '$x,xxx,xxx' string
        return float(str(v).replace("$", "").replace(",", ""))

    rows = [{"team": t, "payroll_2026": _money(v)} for t, v in PAYROLL_2026.items()]
    d = pd.DataFrame(rows).drop_duplicates("team")
    d["payroll_2026"] = pd.to_numeric(d["payroll_2026"], errors="coerce")
    d = d.dropna(subset=["payroll_2026"])
    d["cap_2027"] = CAP
    d["floor_2027"] = FLOOR
    d["over_cap"] = (d["payroll_2026"] > CAP).values
    d["gap_to_cap"] = d["payroll_2026"] - CAP   # + = over (must cut); - = headroom
    d["gap_to_floor"] = FLOOR - d["payroll_2026"]  # + = under floor (must spend up)
    d["cut_pct_if_over"] = (d["gap_to_cap"] / d["payroll_2026"] * 100).clip(lower=0)
    d["payroll_M"] = (d["payroll_2026"] / 1e6).round(1)

    print("=== who is FORCED to cut under the 2027 cap (2026 payroll) ===")
    over = d[d["over_cap"]].sort_values("gap_to_cap", ascending=False)
    for _, r in over.head(8).iterrows():
        print(f"  {r['team']:>4} ${r['payroll_M']:>6.1f}M  over by ${r['gap_to_cap']/1e6:>6.1f}M "
              f"= cut {r['cut_pct_if_over']:.0f}%")
    print("\n=== who is FORCED to spend up to the floor (2026 payroll) ===")
    under = d[d["gap_to_floor"] > 0].sort_values("gap_to_floor", ascending=False)
    for _, r in under.head(8).iterrows():
        print(f"  {r['team']:>4} ${r['payroll_M']:>6.1f}M  below floor by ${r['gap_to_floor']/1e6:>6.1f}M "
              f"(must add ${r['gap_to_floor']/1e6:.1f}M)")

    n_over, n_under = int(over.shape[0]), int(under.shape[0])
    print(f"\nsummary: {n_over} teams over cap must cut; {n_under} under floor must spend up")
    print("cap savings pool: the cap forces sophisticated deployment, not simple cuts")

    # keep it rich for the demo
    out = {"cap_2027": CAP, "floor_2027": FLOOR,
           "n_over_cap": n_over, "n_under_floor": n_under,
           "teams": d[["team", "payroll_M", "gap_to_cap", "gap_to_floor"]]
                    .to_dict(orient="records")}
    with open(os.path.join(DATA, "cap_scenario_2027.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote data/cap_scenario_2027.json")


if __name__ == "__main__":
    main()
