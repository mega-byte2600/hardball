"""Cycle 49 (OPT-1): a real roster optimizer next to the Cycle 26 greedy.

Cycle 26 built the three budget-scenario rosters GREEDILY (WAR-per-dollar
quota fill, then WAR upgrades while the budget holds). OPT-1 asks the
question a skeptical room will ask: how much WAR did the greedy leave
on the table? It formulates the SAME roster problem as a mixed-integer
program and solves it to proven optimality (or reports the incumbent
and the dual bound honestly if a solve ever hits its time limit).

Identical inputs, by construction — this script imports Cycle 26's
own pool builder inputs and greedy builder and REPRODUCES its three
rosters exactly (asserted against data/wow_scenarios.json) before
optimizing anything:

  - pool: 2027 FA class (data/fa_shopping_2027.json), players with a
    Steamer WAR and a prior-contract AAV — 199 players;
  - prices: prior-contract AAV, a last-price anchor, NOT a predicted
    2027 salary (same label as Cycle 26);
  - quotas: C2 1B2 2B1 3B1 SS2 OF4 DH1 SP5 RP8 = 26 (Cycle 26 QUOTAS,
    positions mapped by Cycle 26 POSMAP).

The optimization adds the owners' proposed per-player maximum as a
hard constraint — no player may cost more than 15% of the $245.3M cap
($36.795M). On this pool at prior-AAV anchors the constraint binds
nobody (the dearest FA, at $35.0M, is under it); it is enforced and
reported, and the greedy rosters are checked against it too.

DH eligibility follows Cycle 26's own stated rule — "DH can be any
bat". (Cycle 26's greedy never actually used that freedom: with two
DH-mapped players in the pool its fallback never triggered, so all
three greedy rosters carry a ~0-WAR DH-mapped bat at DH.) A DH-
restricted sensitivity — DH slot open only to DH-mapped players,
exactly the greedy's effective search space — is solved alongside, so
the comparison can say how much of any optimizer edge is the DH rule
and how much is combinatorics.

Solver: scipy.optimize.milp (HiGHS), binary selection variables,
maximize total Steamer WAR subject to quotas, budget, one-slot-per-
player. Optimality is claimed only when HiGHS proves it (gap 0);
otherwise the incumbent and bound are published as-is.

Run: python src/bml_cycle49.py   ->  data/optimizer_comparison_2027.json
"""
import importlib.util
import json
import os
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

CAP = 245.3e6
PER_PLAYER_MAX = 0.15 * CAP  # $36.795M — owners' proposed 15% rule
BUDGETS = [("The Floor — $171.2M", 171.2e6),
           ("The Middle — $208.0M", 208.0e6),
           ("The Cap — $245.3M", CAP)]
TIME_LIMIT_S = 600


def load_cycle26():
    spec = importlib.util.spec_from_file_location(
        "bml_cycle26_wow", os.path.join(REPO, "src", "bml_cycle26_wow.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_pool(c26):
    """Cycle 26's pool, byte-for-byte its construction in main()."""
    fa = json.load(open(os.path.join(DATA, "fa_shopping_2027.json")))["class"]
    pool = []
    for r in fa:
        if r.get("steamer_war") is None or not r.get("prev_aav"):
            continue
        pool.append({"name": r["name"], "player_id": r["player_id"],
                     "pos": c26.POSMAP.get(r["pos"], r["pos"]),
                     "prev_team": r["prev_team"], "prev_aav": r["prev_aav"],
                     "steamer_war": round(r["steamer_war"], 2)})
    return pool


def solve(pool, quotas, budget, dh_any_bat):
    """MILP: maximize WAR s.t. quotas, budget, one slot per player.

    Returns (status_dict, roster list with slot assignments)."""
    slots = list(quotas)
    is_bat = lambda p: p["pos"] not in ("SP", "RP")
    pairs = []  # (player_idx, slot)
    for i, p in enumerate(pool):
        pairs.append((i, p["pos"]))
        if dh_any_bat and is_bat(p) and p["pos"] != "DH":
            pairs.append((i, "DH"))
    n = len(pairs)
    war = np.array([pool[i]["steamer_war"] for i, _ in pairs])
    cost = np.array([pool[i]["prev_aav"] for i, _ in pairs], dtype=float)

    rows, lb, ub = [], [], []
    # one slot per player
    by_player = {}
    for j, (i, _) in enumerate(pairs):
        by_player.setdefault(i, []).append(j)
    for i, js in by_player.items():
        r = lil_matrix((1, n)); r[0, js] = 1.0
        rows.append(r); lb.append(0.0); ub.append(1.0)
    # quota per slot (exact)
    by_slot = {}
    for j, (_, s) in enumerate(pairs):
        by_slot.setdefault(s, []).append(j)
    for s in slots:
        r = lil_matrix((1, n)); r[0, by_slot[s]] = 1.0
        rows.append(r); lb.append(float(quotas[s])); ub.append(float(quotas[s]))
    # budget
    r = lil_matrix((1, n)); r[0, :] = cost
    rows.append(r); lb.append(0.0); ub.append(float(budget))

    from scipy.sparse import vstack
    A = vstack(rows).tocsc()
    res = milp(c=-war, constraints=LinearConstraint(A, lb, ub),
               integrality=np.ones(n), bounds=Bounds(0.0, 1.0),
               options={"time_limit": TIME_LIMIT_S, "disp": False})
    info = {"solver_status": int(res.status), "solver_message": res.message,
            "mip_gap": (None if res.mip_gap is None else float(res.mip_gap)),
            "dual_bound_war": (None if res.mip_dual_bound is None
                               else float(-res.mip_dual_bound)),
            "proven_optimal": bool(res.status == 0 and
                                   (res.mip_gap is not None and res.mip_gap <= 1e-9))}
    if res.x is None:
        return info, None
    roster = []
    for j, (i, s) in enumerate(pairs):
        if res.x[j] > 0.5:
            p = pool[i]
            roster.append({"pos": s, "name": p["name"],
                           "player_id": p["player_id"],
                           "prev_team": p["prev_team"],
                           "war": p["steamer_war"], "prev_aav": p["prev_aav"]})
    roster.sort(key=lambda x: (slots.index(x["pos"]), -x["war"]))
    return info, roster


def roster_summary(roster):
    return {"total_war": round(sum(r["war"] for r in roster), 1),
            "spend": round(sum(r["prev_aav"] for r in roster)),
            "n": len(roster),
            "max_aav": max(r["prev_aav"] for r in roster),
            "satisfies_15pct_rule": bool(
                max(r["prev_aav"] for r in roster) <= PER_PLAYER_MAX),
            "dh_slot": next(({"name": r["name"], "war": r["war"]}
                             for r in roster if r["pos"] == "DH"), None)}


def main():
    import scipy
    c26 = load_cycle26()
    quotas = dict(c26.QUOTAS)
    assert sum(quotas.values()) == 26
    pool = build_pool(c26)
    print(f"FA pool (WAR + prior AAV): {len(pool)}")
    over = [p for p in pool if p["prev_aav"] > PER_PLAYER_MAX]
    print(f"per-player max ${PER_PLAYER_MAX/1e6:.3f}M: "
          f"{len(over)} pool players over it (excluded from optimization)")

    wow = json.load(open(os.path.join(DATA, "wow_scenarios.json")))
    wow_by_budget = {s["budget"]: s for s in wow["scenarios"]}

    out_budgets = []
    for label, budget in BUDGETS:
        # --- greedy, reproduced with Cycle 26's own builder ----------
        g_roster, g_spent = c26.build_roster(pool, budget)
        g_roster = [{"pos": r["pos"], "name": r["name"],
                     "player_id": r["player_id"], "prev_team": r["prev_team"],
                     "war": r["steamer_war"], "prev_aav": r["prev_aav"]}
                    for r in sorted(g_roster,
                                    key=lambda x: (list(quotas).index(x["pos"]),
                                                   -x["steamer_war"]))]
        g_sum = roster_summary(g_roster)
        w = wow_by_budget[budget]
        assert len(g_roster) == 26 and g_sum["spend"] == w["spend"], \
            (label, g_sum["spend"], w["spend"])
        assert abs(g_sum["total_war"] - w["total_war"]) <= 0.05, \
            (label, g_sum["total_war"], w["total_war"])
        assert sorted(r["name"] for r in g_roster) == \
               sorted(x["name"] for x in w["roster"]), label
        print(f"{label}: greedy reproduced exactly — {g_sum['total_war']} WAR, "
              f"${g_sum['spend']/1e6:.1f}M, 15% rule: {g_sum['satisfies_15pct_rule']}")

        # --- optimizer, both DH rules ---------------------------------
        elig_pool = [p for p in pool if p["prev_aav"] <= PER_PLAYER_MAX]
        info, o_roster = solve(elig_pool, quotas, budget, dh_any_bat=True)
        o_sum = roster_summary(o_roster)
        assert len(o_roster) == 26 and o_sum["spend"] <= budget
        info_r, o_roster_r = solve(elig_pool, quotas, budget, dh_any_bat=False)
        o_sum_r = roster_summary(o_roster_r)
        assert len(o_roster_r) == 26 and o_sum_r["spend"] <= budget

        g_ids = {r["player_id"] for r in g_roster}
        o_ids = {r["player_id"] for r in o_roster}
        by_id = {p["player_id"]: p["name"] for p in pool}
        rec = {
            "label": label, "budget": budget,
            "greedy": {**g_sum, "roster": g_roster},
            "optimizer": {**info, **o_sum, "roster": o_roster},
            "optimizer_dh_restricted": {**info_r, **o_sum_r,
                                        "roster": o_roster_r},
            "overlap": {
                "n_shared": len(g_ids & o_ids),
                "greedy_only": sorted(by_id[i] for i in g_ids - o_ids),
                "optimizer_only": sorted(by_id[i] for i in o_ids - g_ids)},
            "delta_war": round(o_sum["total_war"] - g_sum["total_war"], 1),
            "delta_war_pct_of_greedy": round(
                100.0 * (o_sum["total_war"] - g_sum["total_war"])
                / g_sum["total_war"], 1),
            "delta_war_dh_restricted": round(
                o_sum_r["total_war"] - g_sum["total_war"], 1),
        }
        print(f"{label}: optimizer {o_sum['total_war']} WAR "
              f"(optimal={info['proven_optimal']}, gap={info['mip_gap']}), "
              f"DH-restricted {o_sum_r['total_war']} WAR; "
              f"delta {rec['delta_war']:+.1f} WAR, overlap {rec['overlap']['n_shared']}/26")
        out_budgets.append(rec)

    out = {"metadata": {
               "cycle": 49,
               "method": "mixed-integer programming (scipy.optimize.milp / "
                         "HiGHS): binary player-slot selection maximizing "
                         "total Steamer WAR subject to Cycle 26 positional "
                         "quotas (exact), 26-man roster, spend <= budget, "
                         "one slot per player, and prior AAV <= 15% of the "
                         "proposed cap per player",
               "solver": f"scipy {scipy.__version__} milp (HiGHS)",
               "price_basis": "prior-contract AAV (Spotrac) — a last-price "
                              "anchor, NOT a predicted 2027 price (same "
                              "basis and label as Cycle 26)",
               "scope": "free-agent-only build from the 2027 class; "
                        "pre-arb/arb players not priced here (same as "
                        "Cycle 26)",
               "pool": len(pool),
               "quotas": quotas,
               "per_player_max": {
                   "value": PER_PLAYER_MAX,
                   "rule": "15% of the proposed $245.3M cap",
                   "pool_players_over": len(over),
                   "binding_on_this_pool": bool(over),
                   "greedy_rosters_satisfy": all(
                       b["greedy"]["satisfies_15pct_rule"]
                       for b in out_budgets)},
               "dh_rule_primary": "DH slot open to any bat — Cycle 26's "
                                  "own stated rule ('DH can be any bat')",
               "dh_rule_sensitivity": "optimizer_dh_restricted: DH slot "
                                      "open only to DH-mapped players — "
                                      "the greedy builder's effective "
                                      "search space, since its any-bat "
                                      "fallback never triggers with two "
                                      "DH-mapped players in the pool",
               "greedy_reproduction": "Cycle 26 build_roster re-run on the "
                                      "identical pool reproduces "
                                      "data/wow_scenarios.json exactly "
                                      "(spend to the dollar, WAR to 0.05, "
                                      "identical 26 player IDs per budget) "
                                      "— asserted in code before optimizing",
           },
           "budgets": out_budgets}
    with open(os.path.join(DATA, "optimizer_comparison_2027.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote data/optimizer_comparison_2027.json")


if __name__ == "__main__":
    main()
