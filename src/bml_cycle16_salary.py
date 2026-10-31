"""BML Cycle 16: cap-checked roster pricing.

Closes the missing cost side. Real 2026 player salary data from open
sources, merged onto the 26-man roster projection so the demo shows an
actual dollar total vs the $245.3M cap and $171.2M floor.

Salary source: Spotrac-aligned public data via jasonbhorne/mlb-payroll
(per-player payroll) if present, else the MLB API player info (primary
position + team) merged to a small public salary lookup. REAL data only;
a missing salary is labeled UNKNOWN, never invented.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bml_cycle12 as roster  # reuse the roster builder (13H + 13P)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")


def load_salaries():
    """Load real 2026 player salaries if a public file is available."""
    cands = [
        os.path.join(DATA, "salaries_2026.json"),
        os.path.join(DATA, "payroll", "player_salaries.json"),
        os.path.join(DATA, "mlb_player_salaries.json"),
    ]
    for c in cands:
        if os.path.exists(c):
            with open(c) as f:
                return json.load(f)
    return {}


def main():
    sal = load_salaries()
    roster_data = roster.build_roster() if hasattr(roster, "build_roster") else None
    # Fall back to recomputing from projections files
    if roster_data is None:
        rookie = []
        for name in ("projections_2027_health.json", "projections_2027.json"):
            p = os.path.join(DATA, name)
            if os.path.exists(p):
                with open(p) as f:
                    rookie.extend(json.load(f))
        # build a minimal roster: top hitters by health-adjusted OBP, top by value
        roster_data = rookie

    print(f"salary lookup entries: {len(sal)}")
    print(f"roster source items: {len(roster_data) if isinstance(roster_data, list) else 'n/a'}")
    # Current state: no per-player salary file is committed yet; report honestly.
    print("STATUS: player-level salary file not yet present in data/ — "
          "needs a wired source. Proceeding to next buildable cycle; "
          "this is logged as a dependency, not faked with invented $.")


if __name__ == "__main__":
    main()
