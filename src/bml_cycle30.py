#!/usr/bin/env python3
"""Cycle 30 — FORCED-SELLER PANEL.

Question: under the proposed 2027 cap, what does compliance cost the
over-cap teams — in contracts, not just dollars?

Method (arithmetic only, no trade prediction):
  * over-cap teams come from data/cap_scenario_2027.json (gap_to_cap > 0).
  * each team's contracts come from data/salaries_2026.json (Spotrac
    2026 Payroll Salary column, as committed in Cycle 25).
  * for each team present in the salaries file, rank its contracts
    largest-first and take the minimal prefix whose cumulative salary
    covers the cap gap. That prefix is the "shed set".
  * teams absent from the salaries file are reported uncovered, never
    as zero — CHC was over cap by $4.0M but its Spotrac page failed in
    Cycle 25, so no shed set existed for it until the page unblocked
    in Cycle 85 (2026-11-05) and the file completed to 30/30.

Honesty caveats (carried into the JSON metadata and the panel):
  * shedding a contract is assumed to remove its full listed salary.
    Real trades, releases and retained-salary deals rarely do that, so
    the shed count is a lower bound on the arithmetic, not a plan.
  * the listed contracts for a team need not sum to that team's
    cap-scenario payroll total (different payroll definitions and
    roster timing between the two committed sources) — the shed count
    uses individual contract values against the cap gap, never the
    listed sum.
  * 2026 salaries are measured against a 2027 cap gap; the panel is a
    compliance illustration, not a 2027 payroll forecast.

Output: data/forced_sellers_2027.json. Fails closed on a missing input,
a moved cap/floor, a non-minimal shed set, or a coverage change.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAP = 245_300_000
FLOOR = 171_200_000


def main() -> int:
    cap = json.loads((DATA / "cap_scenario_2027.json").read_text())
    assert cap["cap_2027"] == CAP and cap["floor_2027"] == FLOOR, \
        "cap/floor moved — re-derive before shipping"
    sal = json.loads((DATA / "salaries_2026.json").read_text())
    meta = sal["metadata"]
    failures = {f["team"] for f in meta["team_failures"]}

    by_team = {}
    for p in sal["players"]:
        assert p["salary_2026"] > 0, f"non-positive salary: {p}"
        by_team.setdefault(p["team"], []).append(p)

    teams = []
    for t in cap["teams"]:
        if t["gap_to_cap"] <= 0:
            continue
        team = t["team"]
        rows = sorted(by_team.get(team, []),
                      key=lambda r: -r["salary_2026"])
        if not rows:
            teams.append({"team": team, "payroll_M": t["payroll_M"],
                          "gap_to_cap": t["gap_to_cap"],
                          "covered": False,
                          "reason": "no contract rows in salaries_2026.json"
                                    + (" (Spotrac page failed in Cycle 25)"
                                       if team in failures else ""),
                          "n_listed": 0, "shed": []})
            continue
        cum, shed = 0, []
        for r in rows:
            cum += r["salary_2026"]
            shed.append({"name": r["name"], "pos": r["pos"],
                         "salary_2026": r["salary_2026"]})
            if cum >= t["gap_to_cap"]:
                break
        # minimality: dropping the last contract must fall short
        assert cum >= t["gap_to_cap"], f"{team}: contracts do not cover gap"
        assert cum - shed[-1]["salary_2026"] < t["gap_to_cap"], \
            f"{team}: shed set not minimal"
        teams.append({"team": team, "payroll_M": t["payroll_M"],
                      "gap_to_cap": t["gap_to_cap"], "covered": True,
                      "n_listed": len(rows),
                      "sum_listed": sum(r["salary_2026"] for r in rows),
                      "n_shed": len(shed), "shed_total": cum,
                      "shed": shed})

    covered = [t for t in teams if t["covered"]]
    uncovered = [t["team"] for t in teams if not t["covered"]]
    assert len(teams) == cap["n_over_cap"] == 7, \
        f"over-cap teams: {len(teams)} (file says {cap['n_over_cap']})"
    assert len(covered) == 7 and uncovered == [], \
        f"coverage changed: covered={len(covered)} uncovered={uncovered}"

    out = {
        "metadata": {
            "method": "minimal largest-first contract prefix covering the "
                      "cap gap; arithmetic only, not a trade prediction",
            "cap_2027": CAP, "floor_2027": FLOOR,
            "sources": ["data/cap_scenario_2027.json (gaps)",
                        "data/salaries_2026.json (Spotrac 2026 Payroll "
                        "Salary column, Cycle 25)"],
            "coverage": "7 of 7 over-cap teams on Spotrac per-player "
                        "rows (Cycle 25, completed to 30/30 in Cycle 85 "
                        "when the six blocked pages unblocked)",
            "salaries_rows": meta["rows"],
            "salaries_team_failures": sorted(failures),
            "caveats": [
                "Shedding is assumed to remove the full listed salary; "
                "real trades/releases rarely do that, so each shed count "
                "is an arithmetic lower bound, not a plan.",
                "A team's listed contracts need not sum to its "
                "cap-scenario payroll total (different payroll "
                "definitions / roster timing); the shed count uses "
                "individual contract values against the gap.",
                "2026 salaries measured against a 2027 cap gap: a "
                "compliance illustration, not a 2027 payroll forecast.",
            ],
        },
        "teams": teams,
    }
    (DATA / "forced_sellers_2027.json").write_text(json.dumps(out, indent=1))
    for t in teams:
        if t["covered"]:
            names = ", ".join(f"{s['name']} ${s['salary_2026']/1e6:.1f}M"
                              for s in t["shed"])
            print(f"{t['team']}: gap ${t['gap_to_cap']/1e6:.1f}M -> "
                  f"shed {t['n_shed']} ({names}) = ${t['shed_total']/1e6:.1f}M")
        else:
            print(f"{t['team']}: gap ${t['gap_to_cap']/1e6:.1f}M -> "
                  f"UNCOVERED ({t['reason']})")
    print(f"FORCED SELLERS: {len(covered)}/7 over-cap teams covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
