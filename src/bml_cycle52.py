#!/usr/bin/env python3
"""BML Cycle 52 (toby series) — SWAP: the proven-optimal rosters
become the headline scenarios.

Decision on record: OPT-1 (Cycle 49) re-solved Cycle 26's roster
problem exactly (mixed-integer programming, scipy/HiGHS) on identical
inputs and proved the optima — Floor 48.9 / Middle 52.8 / Cap 54.8 WAR
against the greedy build's 42.0 / 45.7 / 52.3. OPT-2 (Cycle 50)
stress-tested those optima. The owner approved the promotion on
2026-11-02, with the research condition that the optimizer is
headlined but never as bare numbers: the +-20% price-error range
travels with every headline figure.

What this script does (promotion only — no new solves):

- data/wow_scenarios.json `scenarios` becomes the Cycle 49 optimizer
  rosters, each carrying its Cycle 50 price-error range
  (WAR at prices x1.2 .. WAR at prices x0.8, both re-solved to proven
  optima). The Cycle 26 greedy rosters move verbatim to
  `benchmark_greedy` — Figure 25's comparison and the methods story
  depend on them.
- The Cycle 27 availability stress is recomputed on the new totals
  with Cycle 27's exact method (uniform factors from the 201-player
  health pool: unrounded mean, p25 by sorted index, products rounded
  to 0.1), including the measured-subset context over the new
  rosters. The greedy stress totals are preserved inside
  `benchmark_greedy`.

Inputs: data/wow_scenarios.json (greedy, Cycles 26/27),
data/optimizer_comparison_2027.json (Cycle 49),
data/optimizer_sensitivity_2027.json (Cycle 50),
data/projections_2027_health.json, data/fa_shopping_2027.json.
No network.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> None:
    wow = json.loads((DATA / "wow_scenarios.json").read_text())
    comp = json.loads((DATA / "optimizer_comparison_2027.json").read_text())
    sens = json.loads((DATA / "optimizer_sensitivity_2027.json").read_text())
    health_rows = json.loads((DATA / "projections_2027_health.json").read_text())
    fa = json.loads((DATA / "fa_shopping_2027.json").read_text())["class"]

    greedy_scenarios = wow["scenarios"]
    greedy_stressed = wow["availability_stress"]["stressed_totals"]
    assert [s["total_war"] for s in greedy_scenarios] == [42.0, 45.7, 52.3], \
        "input wow_scenarios.json is not the Cycle 26 greedy set"

    # price-error ranges from Cycle 50 (re-solved, proven optimal)
    ranges = {}
    for scale, key in (("x1.2", "low"), ("x0.8", "high")):
        for e in sens["price_sensitivity"][scale]:
            ranges.setdefault(e["label"], {})[key] = e["total_war"]

    scenarios = []
    for b in comp["budgets"]:
        o = b["optimizer"]
        base = sens["base_optimizer"][b["label"]]
        assert base["total_war"] == o["total_war"] and base["spend"] == o["spend"], \
            f"{b['label']}: Cycle 49/50 base mismatch"
        assert o["proven_optimal"] and o["mip_gap"] == 0
        assert len(o["roster"]) == 26 and o["spend"] <= b["budget"]
        assert abs(sum(p["war"] for p in o["roster"]) - o["total_war"]) <= 0.2
        rng = ranges[b["label"]]
        assert rng["low"] <= o["total_war"] <= rng["high"]
        scenarios.append({
            "label": b["label"],
            "budget": b["budget"],
            "spend": o["spend"],
            "total_war": o["total_war"],
            "method": "exact MILP optimizer (Cycle 49), proven optimal",
            "proven_optimal": True,
            "mip_gap": o["mip_gap"],
            "war_range_prices_pm20": {
                "low": rng["low"],
                "high": rng["high"],
                "basis": "Cycle 50: all prior-AAV anchors scaled x1.2 / "
                         "x0.8 and re-solved to proven optima",
            },
            "roster": o["roster"],
        })

    # --- Cycle 27 availability stress, recomputed on the new totals
    # (Cycle 27's method verbatim: unrounded factors, same rounding).
    av = sorted(r["avail_pct"] for r in health_rows)
    n = len(av)
    mean_av = statistics.mean(av)
    p25_av = av[n // 4]

    stressed = {}
    for s in scenarios:
        stressed[s["label"]] = {
            "raw_war": s["total_war"],
            "war_at_pool_mean_avail": round(s["total_war"] * mean_av, 1),
            "war_at_pool_p25_avail": round(s["total_war"] * p25_av, 1),
        }

    health = {r["player_id"]: r["avail_pct"] for r in health_rows}
    by_name = {r["name"]: r["player_id"] for r in fa}
    rostered = {}
    for s in scenarios:
        for p in s["roster"]:
            rostered[p["name"]] = p["war"]
    covered = {nm: (w, health[by_name[nm]]) for nm, w in rostered.items()
               if nm in by_name and by_name[nm] in health}
    cov_war = sum(w for w, _ in covered.values())
    cov_adj = sum(w * a for w, a in covered.values())

    ratio = round(scenarios[0]["total_war"] / scenarios[2]["total_war"], 3)

    wow["metadata"] = {
        "cycle": 52,
        "method": "Headline: exact mixed-integer optimization "
                  "(scipy.optimize.milp / HiGHS, Cycle 49) — binary "
                  "player-slot selection maximizing Steamer WAR under "
                  "Cycle 26 positional quotas, 26-man roster, spend <= "
                  "budget, prior AAV <= 15% of the proposed cap; optima "
                  "proven (solver gap 0). Benchmark: Cycle 26 greedy "
                  "WAR-per-dollar quota fill, preserved under "
                  "benchmark_greedy.",
        "price_basis": "prior-contract AAV (Spotrac) — a last-price "
                       "anchor, NOT a predicted 2027 price",
        "scope": "free-agent-only build from the 2027 class (Cycle 25); "
                 "pre-arb/arb players not priced here",
        "pool": 199,
        "promotion": "Owner-approved 2026-11-02 (Cycle 52): the Cycle 49 "
                     "optimizer rosters replace the greedy builds as the "
                     "headline scenarios. Headline WAR is published with "
                     "its Cycle 50 +-20% price-error range.",
    }
    wow["scenarios"] = scenarios
    wow["benchmark_greedy"] = {
        "note": "Cycle 26 greedy builds (WAR-per-dollar quota fill, then "
                "upgrades while budget holds), preserved verbatim as the "
                "benchmark for Figure 25's comparison; superseded as the "
                "headline by the Cycle 49 optimizer in Cycle 52.",
        "scenarios": greedy_scenarios,
        "availability_stress_totals": greedy_stressed,
    }
    wow["availability_stress"] = {
        "method": "Uniform stress: scenario WAR scaled by availability "
                  "factors measured from 201 real players' 2025-26 IL "
                  "records (data/projections_2027_health.json). "
                  "Per-player factors exist for only part of any roster, "
                  "so they are NOT applied player-by-player (that would "
                  "penalize the best-measured players); the subset result "
                  "is kept below for context. Recomputed on the Cycle 49 "
                  "optimizer totals in Cycle 52, Cycle 27's method "
                  "unchanged.",
        "pool": {"n_players": n, "mean_avail": round(mean_av, 3),
                 "p25_avail": round(p25_av, 3),
                 "median_avail": round(av[n // 2], 3)},
        "stressed_totals": stressed,
        "floor_cap_ratio_raw": ratio,
        "finding": "Injury risk is a level tax (~4-5 WAR at every "
                   "budget); the floor roster still captures "
                   f"~{round(ratio * 100)}% of the cap roster's WAR "
                   "after the stress.",
        "measured_subset_context": {
            "rostered_players_with_measured_avail": len(covered),
            "n_unique_rostered_players": len(rostered),
            "their_war": round(cov_war, 1),
            "their_war_avail_adjusted": round(cov_adj, 1),
            "note": "Subset of all three rosters combined; not a "
                    "per-budget figure.",
        },
    }
    (DATA / "wow_scenarios.json").write_text(json.dumps(wow, indent=1))

    for s in scenarios:
        st = stressed[s["label"]]
        print(f"{s['label']}: {s['total_war']} WAR for ${s['spend']/1e6:.1f}M "
              f"(range {s['war_range_prices_pm20']['low']}–"
              f"{s['war_range_prices_pm20']['high']}); stress mean "
              f"{st['war_at_pool_mean_avail']} / p25 {st['war_at_pool_p25_avail']}")
    d_spend = (scenarios[2]["spend"] - scenarios[0]["spend"]) / 1e6
    d_war = scenarios[2]["total_war"] - scenarios[0]["total_war"]
    print(f"floor/cap ratio {ratio}; floor->cap: last ${d_spend:.1f}M "
          f"buys {d_war:.1f} WAR; subset {len(covered)} of "
          f"{len(rostered)} rostered players measured")


if __name__ == "__main__":
    main()
