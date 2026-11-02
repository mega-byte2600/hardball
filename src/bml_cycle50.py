"""Cycle 50 (OPT-2): optimizer sensitivity + the mixed pre-arb/FA floor.

OPT-1 (Cycle 49) proved the exact optima of Cycle 26's roster problem
at prior-AAV anchors: Floor 48.9, Middle 52.8, Cap 54.8 WAR. OPT-2
stress-tests those optima and answers the Kleinbard rebuttal — "no
club builds a floor roster from free agents alone" — in the Explorer /
workpaper layer only. Figure 16 and the Story/Boardroom decks are
untouched; whether optimizer rosters ever replace the greedy ones
stays an owner decision.

Four computations, all with Cycle 49's own solver (imported, not
re-implemented), all re-anchored by ASSERTING that a base-case
re-solve reproduces OPT-1's three rosters exactly before anything is
varied:

  1. PRICE SENSITIVITY — every anchor scaled x0.8 and x1.2 uniformly,
     all three budgets re-solved. The owners' 15% per-player maximum
     is applied to the SCALED prices (at x1.2 two anchors cross it —
     Rendon $35.0M -> $42.0M and Skubal $32.0M -> $38.4M — and the
     rule excludes both).
  2. TARGETED BID-UP — only the 26 players on OPT-1's floor roster
     get x1.2 anchors ("the market bids up your targets"); the floor
     is re-solved. Everyone else keeps base anchors.
  3. WAR SENSITIVITY — Steamer WAR haircut -15% for players aged 33+
     (ages from the FA class file; all 199 pool players carry one),
     base prices, all three budgets. Each roster is reported twice:
     its value under the haircut it was chosen under, and re-scored
     on base WAR — the roster pessimism picks, priced in the base
     case's currency.
  4. MIXED PRE-ARB + FA FLOOR — the FA pool plus the repo's pre-arb
     pool: players whose Spotrac status is exactly "Pre-Arbitration"
     in data/salaries_2026.json (553 rows, every one at the file's
     flat $1,000,000), with a committed ID and a Steamer WAR, priced
     at $1.0M — the repo's pre-arb PLACEHOLDER convention (Cycles 41 /
     46), not a measured salary. Positions from the same file via
     Cycle 26's POSMAP. Floor budget only, identical quotas.

     Framing, stated wherever the result is used: a real club cannot
     sign another club's pre-arb players. The mixed solve answers
     "what does the floor buy a club that develops or holds pre-arb
     talent" — the floor is survivable with internal pre-arb
     production. It is NOT a shopping list.

Solver honesty: scipy.optimize.milp (HiGHS) via Cycle 49's solve();
every solve publishes status, MIP gap, dual bound, and a
proven-optimal flag. Optimality is claimed only at gap 0.

Run: python src/bml_cycle50.py   ->  data/optimizer_sensitivity_2027.json
"""
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

FLOOR = 171.2e6
PREARB_PRICE = 1_000_000  # repo placeholder convention, NOT a salary
HAIRCUT_AGE = 33
HAIRCUT_FACTOR = 0.85


def load(mod_name):
    spec = importlib.util.spec_from_file_location(
        mod_name, os.path.join(REPO, "src", f"{mod_name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def churn(base_roster, roster, by_id):
    b = {r["player_id"] for r in base_roster}
    n = {r["player_id"] for r in roster}
    return {"n_changed": 26 - len(b & n),
            "out_names": sorted(by_id[i] for i in b - n),
            "in_names": sorted(by_id[i] for i in n - b)}


def solve_checked(c49, pool, quotas, budget):
    """Cycle 49's eligibility rule (15% max on the prices in force)
    + solve, with the standard roster asserts."""
    elig = [p for p in pool if p["prev_aav"] <= c49.PER_PLAYER_MAX]
    info, roster = c49.solve(elig, quotas, budget, dh_any_bat=True)
    assert roster is not None and len(roster) == 26, info
    spend = sum(r["prev_aav"] for r in roster)
    assert spend <= budget + 1, (spend, budget)
    return info, roster, len(pool) - len(elig)


def main():
    import scipy
    c26 = load("bml_cycle26_wow")
    c49 = load("bml_cycle49")
    quotas = dict(c26.QUOTAS)
    assert sum(quotas.values()) == 26

    # --- base pool + ages, asserted identical to OPT-1's pool ------
    pool = c49.build_pool(c26)
    fa_rows = json.load(open(os.path.join(
        DATA, "fa_shopping_2027.json")))["class"]
    age_by_id = {r["player_id"]: r.get("age") for r in fa_rows}
    assert all(age_by_id.get(p["player_id"]) is not None for p in pool), \
        "every pool player must carry an FA-class age for the haircut"
    for p in pool:
        p["age"] = age_by_id[p["player_id"]]
    by_id = {p["player_id"]: p["name"] for p in pool}
    base_war = {p["player_id"]: p["steamer_war"] for p in pool}
    base_aav = {p["player_id"]: p["prev_aav"] for p in pool}

    opt1 = json.load(open(os.path.join(
        DATA, "optimizer_comparison_2027.json")))
    opt1_by_budget = {b["budget"]: b for b in opt1["budgets"]}

    # --- anchor: re-solve the base case, must reproduce OPT-1 ------
    base = {}
    for label, budget in c49.BUDGETS:
        info, roster, n_over = solve_checked(c49, pool, quotas, budget)
        ref = opt1_by_budget[budget]["optimizer"]
        assert sorted(r["player_id"] for r in roster) == \
            sorted(r["player_id"] for r in ref["roster"]), label
        assert abs(sum(r["war"] for r in roster)
                   - ref["total_war"]) <= 0.05, label
        assert sum(r["prev_aav"] for r in roster) == ref["spend"], label
        assert info["proven_optimal"], (label, info)
        base[budget] = roster
        print(f"base re-solve {label}: reproduces OPT-1 exactly — "
              f"{ref['total_war']} WAR, ${ref['spend']/1e6:.1f}M")
    print(f"FA pool: {len(pool)} "
          f"({sum(1 for p in pool if p['age'] >= HAIRCUT_AGE)} aged "
          f"{HAIRCUT_AGE}+)")

    # --- 1. uniform price sensitivity -------------------------------
    price_sens = {}
    for scale in (0.8, 1.2):
        spool = [{**p, "prev_aav": round(p["prev_aav"] * scale)}
                 for p in pool]
        entries = []
        for label, budget in c49.BUDGETS:
            info, roster, n_over = solve_checked(
                c49, spool, quotas, budget)
            entries.append({
                "label": label, "budget": budget, **info,
                "pool_players_over_15pct_at_scaled_prices": n_over,
                "total_war": round(sum(r["war"] for r in roster), 1),
                "spend_scenario_prices": sum(r["prev_aav"] for r in roster),
                "spend_base_prices": sum(base_aav[r["player_id"]]
                                         for r in roster),
                **churn(base[budget], roster, by_id),
                "roster": roster})
            e = entries[-1]
            print(f"price x{scale} {label}: {e['total_war']} WAR, "
                  f"spend ${e['spend_scenario_prices']/1e6:.1f}M scenario / "
                  f"${e['spend_base_prices']/1e6:.1f}M base, "
                  f"churn {e['n_changed']}/26, optimal={info['proven_optimal']}")
        price_sens[f"x{scale}"] = entries

    # --- 2. targeted bid-up on the floor roster ---------------------
    targets = {r["player_id"] for r in base[FLOOR]}
    tpool = [{**p, "prev_aav": (round(p["prev_aav"] * 1.2)
                                if p["player_id"] in targets
                                else p["prev_aav"])}
             for p in pool]
    info, roster, n_over = solve_checked(c49, tpool, quotas, FLOOR)
    targeted = {"label": "The Floor — $171.2M", "budget": FLOOR, **info,
                "n_targets": len(targets),
                "pool_players_over_15pct_at_scaled_prices": n_over,
                "total_war": round(sum(r["war"] for r in roster), 1),
                "spend_scenario_prices": sum(r["prev_aav"] for r in roster),
                "spend_base_prices": sum(base_aav[r["player_id"]]
                                         for r in roster),
                **churn(base[FLOOR], roster, by_id),
                "roster": roster}
    print(f"targeted bid-up (floor roster x1.2, n={len(targets)}): "
          f"{targeted['total_war']} WAR, spend "
          f"${targeted['spend_scenario_prices']/1e6:.1f}M scenario / "
          f"${targeted['spend_base_prices']/1e6:.1f}M base, churn "
          f"{targeted['n_changed']}/26, optimal={info['proven_optimal']}")

    # --- 3. WAR haircut, age 33+ -------------------------------------
    hpool = [{**p, "steamer_war": (round(p["steamer_war"] * HAIRCUT_FACTOR, 2)
                                   if p["age"] >= HAIRCUT_AGE
                                   else p["steamer_war"])}
             for p in pool]
    haircut = []
    for label, budget in c49.BUDGETS:
        info, roster, n_over = solve_checked(c49, hpool, quotas, budget)
        for r in roster:
            r["war_base"] = base_war[r["player_id"]]
            r["age"] = age_by_id[r["player_id"]]
        haircut.append({
            "label": label, "budget": budget, **info,
            "total_war_haircut": round(sum(r["war"] for r in roster), 1),
            "total_war_base_rescore": round(
                sum(r["war_base"] for r in roster), 1),
            "spend": sum(r["prev_aav"] for r in roster),
            "n_haircut_players_on_roster": sum(
                1 for r in roster if r["age"] >= HAIRCUT_AGE),
            **churn(base[budget], roster, by_id),
            "roster": roster})
        e = haircut[-1]
        print(f"haircut 33+ {label}: {e['total_war_haircut']} WAR under "
              f"haircut, {e['total_war_base_rescore']} re-scored on base "
              f"WAR, churn {e['n_changed']}/26, "
              f"optimal={info['proven_optimal']}")

    # --- 4. mixed pre-arb + FA floor ---------------------------------
    sal = json.load(open(os.path.join(DATA, "salaries_2026.json")))
    pre_rows = [r for r in sal["players"]
                if r["status"] == "Pre-Arbitration"]
    assert all(r["salary_2026"] == PREARB_PRICE for r in pre_rows)
    bat = {r["xMLBAMID"]: r for r in json.load(open(os.path.join(
        DATA, "fg_steamer_2027_bat.json"))) if r.get("xMLBAMID")}
    pit = {r["xMLBAMID"]: r for r in json.load(open(os.path.join(
        DATA, "fg_steamer_2027_pit.json"))) if r.get("xMLBAMID")}
    fa_class_ids = {r["player_id"] for r in fa_rows}
    pre_pool, excluded = [], {"no_player_id": 0, "in_fa_class": 0,
                              "no_steamer_war": 0, "unmappable_pos": 0,
                              "duplicate_id": 0}
    seen = set()
    for r in pre_rows:
        pid = r.get("player_id")
        if not pid:
            excluded["no_player_id"] += 1
            continue
        if pid in seen:
            excluded["duplicate_id"] += 1
            continue
        seen.add(pid)
        if pid in fa_class_ids:
            excluded["in_fa_class"] += 1
            continue
        pos = c26.POSMAP.get(r["pos"], r["pos"])
        if pos not in quotas:
            excluded["unmappable_pos"] += 1
            continue
        src = pit.get(pid) if pos in ("SP", "RP") else bat.get(pid)
        if src is None or src.get("WAR") is None:
            excluded["no_steamer_war"] += 1
            continue
        pre_pool.append({"name": r["name"], "player_id": pid, "pos": pos,
                         "prev_team": r["team"], "prev_aav": PREARB_PRICE,
                         "steamer_war": round(src["WAR"], 2)})
    print(f"pre-arb pool: {len(pre_rows)} Pre-Arbitration rows -> "
          f"{len(pre_pool)} usable (excluded: {excluded})")
    assert len(pre_pool) >= 100, "pre-arb pool too thin to be meaningful"
    by_pos = {}
    for p in pre_pool:
        by_pos.setdefault(p["pos"], 0)
        by_pos[p["pos"]] += 1
    for pos, n in quotas.items():
        avail = by_pos.get(pos, 0) + (len(pre_pool) if pos == "DH" else 0)
        assert avail >= n, f"pre-arb pool cannot fill quota {pos}"

    mixed_pool = [{**p, "origin": "fa"} for p in pool] + \
                 [{**p, "origin": "pre-arb"} for p in pre_pool]
    origin = {p["player_id"]: p["origin"] for p in mixed_pool}
    info, roster, n_over = solve_checked(c49, mixed_pool, quotas, FLOOR)
    for r in roster:
        r["origin"] = origin[r["player_id"]]
    n_pre = sum(1 for r in roster if r["origin"] == "pre-arb")
    ref = opt1_by_budget[FLOOR]["optimizer"]
    mixed = {"label": "The Floor — $171.2M", "budget": FLOOR, **info,
             "total_war": round(sum(r["war"] for r in roster), 1),
             "spend": sum(r["prev_aav"] for r in roster),
             "n_prearb_slots": n_pre, "n_fa_slots": 26 - n_pre,
             "prearb_war": round(sum(r["war"] for r in roster
                                     if r["origin"] == "pre-arb"), 1),
             "fa_war": round(sum(r["war"] for r in roster
                                 if r["origin"] == "fa"), 1),
             "delta_war_vs_fa_only_optimizer": round(
                 sum(r["war"] for r in roster) - ref["total_war"], 1),
             "roster": roster}
    print(f"mixed floor: {mixed['total_war']} WAR "
          f"({mixed['delta_war_vs_fa_only_optimizer']:+.1f} vs FA-only "
          f"{ref['total_war']}), spend ${mixed['spend']/1e6:.1f}M, "
          f"{n_pre} pre-arb / {26 - n_pre} FA slots, "
          f"optimal={info['proven_optimal']}")

    out = {"metadata": {
               "cycle": 50,
               "method": "Cycle 49's exact MILP (scipy.optimize.milp / "
                         "HiGHS, imported from src/bml_cycle49.py) "
                         "re-solved under price and WAR perturbations "
                         "and on an expanded mixed pool; identical "
                         "positional quotas (Cycle 26 QUOTAS/POSMAP) "
                         "and DH rule (any bat) throughout",
               "solver": f"scipy {scipy.__version__} milp (HiGHS)",
               "base_anchor": "base-case re-solve reproduces "
                              "data/optimizer_comparison_2027.json "
                              "(OPT-1) exactly at all three budgets — "
                              "identical 26 player IDs, WAR to 0.05, "
                              "spend to the dollar — asserted in code "
                              "before any scenario runs",
               "price_basis": "prior-contract AAV (Spotrac) — a "
                              "last-price anchor, NOT a predicted 2027 "
                              "price (same basis and label as Cycles "
                              "26/49); scenario prices are uniform or "
                              "targeted scalings of that anchor",
               "per_player_max": "15% of the proposed $245.3M cap "
                                 "($36.795M), applied to the prices in "
                                 "force in each scenario (at x1.2 two "
                                 "anchors cross it — Rendon $35.0M -> "
                                 "$42.0M, Skubal $32.0M -> $38.4M — and "
                                 "are excluded; the count is recorded "
                                 "per scenario)",
               "scenarios": {
                   "price_x0.8 / price_x1.2": "all anchors scaled "
                       "uniformly; all three budgets; WAR objective "
                       "unchanged (base Steamer WAR)",
                   "targeted_bid_up_x1.2": "only the 26 players on "
                       "OPT-1's proven-optimal floor roster scaled "
                       "x1.2; floor budget only",
                   "war_haircut_33plus": "Steamer WAR x0.85 for "
                       "players aged 33+ (FA-class ages; 93 of 199 "
                       "pool players), base prices; each roster also "
                       "re-scored on unhaircut WAR",
                   "mixed_prearb_fa_floor": "FA pool + pre-arb pool "
                       "at the floor budget only"},
               "prearb_pool": {
                   "definition": "data/salaries_2026.json rows with "
                       "Spotrac status exactly 'Pre-Arbitration' and "
                       "a committed player_id, not in the 2027 FA "
                       "class, with a Steamer 2027 WAR (fg_steamer_"
                       "2027_bat/pit by ID), position from the same "
                       "file via Cycle 26 POSMAP",
                   "rows_in_file": len(pre_rows),
                   "excluded": excluded,
                   "pool_size": len(pre_pool),
                   "by_position": by_pos,
                   "price": PREARB_PRICE,
                   "price_label": "$1.0M is the repo's pre-arb "
                       "PLACEHOLDER convention (Spotrac lists every "
                       "such player at a flat $1,000,000; Cycles 41/46 "
                       "document the placeholder rows) — it is NOT a "
                       "measured salary",
                   "framing": "a real club cannot sign another club's "
                       "pre-arb players; this solve answers what the "
                       "floor buys a club that develops or holds "
                       "pre-arb talent — the floor is survivable with "
                       "internal pre-arb production. NOT a shopping "
                       "list"}},
           "base_optimizer": {
               b["label"]: {"budget": b["budget"],
                            "total_war": b["optimizer"]["total_war"],
                            "spend": b["optimizer"]["spend"]}
               for b in opt1["budgets"]},
           "price_sensitivity": price_sens,
           "targeted_bid_up": targeted,
           "war_haircut": haircut,
           "mixed_floor": mixed}
    with open(os.path.join(DATA, "optimizer_sensitivity_2027.json"),
              "w") as f:
        json.dump(out, f, indent=1)
    print("wrote data/optimizer_sensitivity_2027.json")


if __name__ == "__main__":
    main()
