"""Cycle 26: the BOARDROOM layer — stakeholder-facing scenario data.

Two artifacts, all from committed real data:
  1. data/wow_scenarios.json — "what does the money buy?" Build a 26-man
     roster ENTIRELY from the real 2027 free-agent class (Cycle 25:
     Spotrac class + Steamer WAR + prior-contract AAV anchors) at three
     budgets: the proposed floor ($171.2M), a mid budget ($208M), and
     the proposed cap ($245.3M). Method: fill positional quotas greedily
     by WAR per dollar of prior AAV, then spend what remains on WAR
     upgrades at the same positions while the budget holds. Prior AAV
     is a last-price anchor, NOT a predicted 2027 price — labeled so
     everywhere the output is used. This is an illustration of value
     density in the class, not a full roster plan (pre-arb/arb players
     are not in the FA pool).
  2. data/team_explorer.json — per-team 2026 signature indexed to the
     league (100), payroll + cap headroom, and pipeline rank, for the
     pick-your-team dashboard panel.

Run: python src/bml_cycle26_wow.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

CAP, FLOOR = 245.3e6, 171.2e6
QUOTAS = {"C": 2, "1B": 2, "2B": 1, "3B": 1, "SS": 2, "OF": 4, "DH": 1,
          "SP": 5, "RP": 8}
POSMAP = {"RF": "OF", "CF": "OF", "LF": "OF", "OF": "OF", "P": "RP"}


def build_roster(pool, budget):
    by_pos = {}
    for r in pool:
        by_pos.setdefault(r["pos"], []).append(r)
    for v in by_pos.values():
        v.sort(key=lambda r: -(r["steamer_war"] / (r["prev_aav"] / 1e6)))
    roster, spent = [], 0.0
    used = set()
    for pos, n in QUOTAS.items():
        cands = by_pos.get(pos, [])
        if pos == "DH" and len(cands) < n:  # DH can be any bat
            cands = sorted((r for r in pool if r["pos"] not in ("SP", "RP")
                            and r["player_id"] not in used),
                           key=lambda r: -(r["steamer_war"] / (r["prev_aav"] / 1e6)))
        for r in cands:
            if len([x for x in roster if x["pos"] == pos]) >= n:
                break
            if r["player_id"] in used:
                continue
            roster.append({**r, "pos": pos})
            used.add(r["player_id"])
            spent += r["prev_aav"]
    # upgrade passes: swap in a higher-WAR player at the same position
    # while the budget holds
    improved = True
    while improved:
        improved = False
        for i, cur in enumerate(roster):
            best = None
            for r in by_pos.get(cur["pos"], []):
                if r["player_id"] in used or r["steamer_war"] <= cur["steamer_war"]:
                    continue
                delta = r["prev_aav"] - cur["prev_aav"]
                if spent + delta <= budget and (best is None or
                        r["steamer_war"] > best["steamer_war"]):
                    best = r
            if best is not None:
                spent += best["prev_aav"] - cur["prev_aav"]
                used.discard(cur["player_id"])
                used.add(best["player_id"])
                roster[i] = {**best, "pos": cur["pos"]}
                improved = True
    return roster, spent


def main():
    fa = json.load(open(os.path.join(DATA, "fa_shopping_2027.json")))["class"]
    pool = []
    for r in fa:
        if r.get("steamer_war") is None or not r.get("prev_aav"):
            continue
        pool.append({"name": r["name"], "player_id": r["player_id"],
                     "pos": POSMAP.get(r["pos"], r["pos"]),
                     "prev_team": r["prev_team"], "prev_aav": r["prev_aav"],
                     "steamer_war": round(r["steamer_war"], 2)})
    print(f"FA pool (WAR + prior AAV): {len(pool)}")
    scenarios = []
    for label, budget in [("The Floor — $171.2M", FLOOR),
                          ("The Middle — $208.0M", 208.0e6),
                          ("The Cap — $245.3M", CAP)]:
        roster, spent = build_roster(pool, budget)
        assert len(roster) == 26, (label, len(roster))
        assert spent <= budget, (label, spent, budget)
        war = round(sum(r["steamer_war"] for r in roster), 1)
        print(f"{label}: 26 men, spend ${spent/1e6:.1f}M of ${budget/1e6:.1f}M, "
              f"total Steamer WAR {war}")
        scenarios.append({
            "label": label, "budget": budget, "spend": round(spent),
            "total_war": war,
            "roster": [{"pos": r["pos"], "name": r["name"],
                        "prev_team": r["prev_team"], "war": r["steamer_war"],
                        "prev_aav": r["prev_aav"]}
                       for r in sorted(roster,
                                       key=lambda x: (list(QUOTAS).index(x["pos"]),
                                                      -x["steamer_war"]))]})
    out = {"metadata": {
               "method": "greedy WAR-per-dollar quota fill, then WAR "
                         "upgrades while budget holds; deterministic",
               "price_basis": "prior-contract AAV (Spotrac) — a last-price "
                              "anchor, NOT a predicted 2027 price",
               "scope": "free-agent-only build from the 2027 class "
                        "(Cycle 25); pre-arb/arb players not priced here",
               "pool": len(pool)},
           "scenarios": scenarios}
    with open(os.path.join(DATA, "wow_scenarios.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote data/wow_scenarios.json")

    # ---- team explorer ----
    import kpi as kpi_mod
    from payroll import PAYROLL_2026
    df = kpi_mod.kpi_frame_from_snapshots()
    d26 = df[df["season"] == 2026].copy()
    d26["HR/PA_raw"] = d26["HR/PA"]
    league = {c: float(d26[c].mean()) for c in
              ("OBP", "contact", "K%", "BB%", "HR/PA_raw")}
    cheap = d26[d26["team"].isin(["MIL", "TB", "CLE"])]
    cheap_idx = {c: round(100 * float(cheap[c].mean()) / league[c], 1)
                 for c in league}
    # invert K% and HR/PA so higher = more winning-cheap-like everywhere
    def idx(team_row, c):
        v = 100 * float(team_row[c]) / league[c]
        return round(200 - v, 1) if c in ("K%", "HR/PA_raw") else round(v, 1)
    pipe = {o["org_abbr"]: o for o in
            json.load(open(os.path.join(DATA, "pipeline_2026.json")))["orgs"]}
    teams = []
    for _, r in d26.sort_values("team").iterrows():
        t = r["team"]
        pay = None
        if t in PAYROLL_2026:
            pay = float(PAYROLL_2026[t][2].replace("$", "").replace(",", ""))
        o = pipe.get(t, {})
        teams.append({
            "team": t, "wins": int(r["wins"]),
            "signature_idx": {c: idx(r, c) for c in league},
            "payroll": pay,
            "cap_headroom_m": round((CAP - pay) / 1e6, 1) if pay else None,
            "pipeline_rank": o.get("rank"),
            "pipeline_index": o.get("index_avg100"),
            "top_prospect": (o.get("top_hitter") or {}).get("name")})
    axes = ["OBP", "contact", "K%", "BB%", "HR/PA_raw"]
    labels = {"OBP": "OBP", "contact": "Contact", "K%": "Fewer K",
              "BB%": "Walks", "HR/PA_raw": "Less power-chasing"}
    out2 = {"metadata": {
                "basis": "2026 team KPIs indexed to league = 100; K% and "
                         "HR/PA inverted so higher always means more "
                         "winning-cheap-like",
                "winning_cheap_idx": {labels[c]: (round(200 - cheap_idx[c], 1)
                                        if c in ("K%", "HR/PA_raw")
                                        else cheap_idx[c]) for c in axes},
                "axes": [labels[c] for c in axes]},
            "teams": teams}
    with open(os.path.join(DATA, "team_explorer.json"), "w") as f:
        json.dump(out2, f, indent=1)
    print(f"wrote data/team_explorer.json ({len(teams)} teams)")


if __name__ == "__main__":
    main()
