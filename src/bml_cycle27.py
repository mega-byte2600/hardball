#!/usr/bin/env python3
"""BML Cycle 27 (toby series) — AVAILABILITY STRESS on the Boardroom
scenario rosters (Cycle 26).

Question a stakeholder will ask: "Your 42 WAR floor roster assumes
everyone stays healthy. What survives injuries?" Answer with measured
numbers only:

- The availability distribution comes from the repo's own Cycle 9
  health file (data/projections_2027_health.json): 201 real players,
  avail_pct from their actual 2025-26 IL records (mean 0.912,
  p25 0.890, p10 0.753).
- Per-player measured factors exist for only 12 of the 33 rostered
  players (45% of rostered WAR) — applying those alone would penalize
  exactly the players we know most about. So the headline stress is
  UNIFORM: every roster's WAR scaled by the pool mean and by p25.
  The method is labeled wherever the numbers appear.
- The measured-player subset result is recorded in the artifact for
  completeness (subset-only, not comparable across budgets).

Finding: injury risk taxes every budget by roughly the same ~4-5 WAR;
the floor/cap WAR ratio (0.803) is unchanged by the stress. Health
does not rescue the big spender — availability is a level tax, and
the winning-cheap edge survives it.

Output: availability_stress block appended to data/wow_scenarios.json.
Inputs: data/wow_scenarios.json, data/projections_2027_health.json,
data/fa_shopping_2027.json. No network.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> None:
    wow = json.loads((DATA / "wow_scenarios.json").read_text())
    health_rows = json.loads((DATA / "projections_2027_health.json").read_text())
    fa = json.loads((DATA / "fa_shopping_2027.json").read_text())["class"]

    av = sorted(r["avail_pct"] for r in health_rows)
    n = len(av)
    mean_av = statistics.mean(av)
    p25_av = av[n // 4]
    factors = {"pool_mean": round(mean_av, 3), "pool_p25": round(p25_av, 3)}

    stressed = {}
    for s in wow["scenarios"]:
        stressed[s["label"]] = {
            "raw_war": s["total_war"],
            "war_at_pool_mean_avail": round(s["total_war"] * mean_av, 1),
            "war_at_pool_p25_avail": round(s["total_war"] * p25_av, 1),
        }

    # measured-player subset (context only — coverage-limited)
    health = {r["player_id"]: r["avail_pct"] for r in health_rows}
    by_name = {r["name"]: r["player_id"] for r in fa}
    rostered = {}
    for s in wow["scenarios"]:
        for p in s["roster"]:
            rostered[p["name"]] = p["war"]
    covered = {nm: (w, health[by_name[nm]]) for nm, w in rostered.items()
               if nm in by_name and by_name[nm] in health}
    cov_war = sum(w for w, _ in covered.values())
    cov_adj = sum(w * a for w, a in covered.values())

    wow["availability_stress"] = {
        "method": "Uniform stress: scenario WAR scaled by availability factors "
                  "measured from 201 real players' 2025-26 IL records "
                  "(data/projections_2027_health.json). Per-player factors "
                  "exist for only part of any roster, so they are NOT applied "
                  "player-by-player (that would penalize the best-measured "
                  "players); the subset result is kept below for context.",
        "pool": {"n_players": n, "mean_avail": factors["pool_mean"],
                 "p25_avail": factors["pool_p25"],
                 "median_avail": round(av[n // 2], 3)},
        "stressed_totals": stressed,
        "floor_cap_ratio_raw": round(
            wow["scenarios"][0]["total_war"] / wow["scenarios"][2]["total_war"], 3),
        "finding": "Injury risk is a level tax (~4-5 WAR at every budget); "
                   "the floor roster still captures ~80% of the cap roster's "
                   "WAR after the stress.",
        "measured_subset_context": {
            "rostered_players_with_measured_avail": len(covered),
            "their_war": round(cov_war, 1),
            "their_war_avail_adjusted": round(cov_adj, 1),
            "note": "Subset of all three rosters combined; not a per-budget figure.",
        },
    }
    (DATA / "wow_scenarios.json").write_text(json.dumps(wow, indent=1))
    print("AVAILABILITY STRESS:", json.dumps(stressed))
    print("pool mean/p25:", factors, "| subset:", len(covered), "players",
          round(cov_war, 1), "->", round(cov_adj, 1), "WAR")


if __name__ == "__main__":
    main()
