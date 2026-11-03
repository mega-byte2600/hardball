#!/usr/bin/env python3
"""Cycle 64 — the 2027 Cap Transition ledger (slate item 3 of 6).

One row per team, all 30 teams: payroll on its labeled basis, status
against the owners' proposed 2027 system ($245.3M cap / $171.2M floor
/ 15% per-player max = $36.795M), what an over-cap team must shed,
what an under-floor team must spend, and a Cot's-basis sensitivity
shown beside the primary reading — disagreements are displayed, not
resolved.

Inputs (committed data only):
  data/cap_scenario_2027.json   Cycle 22 payroll totals (Spotrac) for
                                all 30 teams + gaps to cap/floor.
  data/forced_sellers_2027.json Cycle 30 shed sets (6 of 7 over-cap
                                teams; CHC uncovered, stated plainly).
  data/salaries_2026.json       Spotrac per-player rows (927, 24 of 30
                                teams) — MLBAM ids for the shed WAR
                                join, and the coverage record.
  data/fg_steamer_2027_{bat,pit}.json
                                Steamer 2027 WAR for the shed sets
                                (batting + pitching summed for the one
                                two-way player, Ohtani).
  data/salaries_cots_2027.json  Cot's labeled second basis: 237 rows
                                with a published LRP-2027 figure, and
                                the committed AAV field (cb_2027_aav)
                                used for the 15% per-player check.
  data/fa_shopping_2027.json    the optimizer pool (199 players with
                                Steamer WAR + prior AAV) — its price
                                distribution shapes the spend side.

Honesty rules:
  - The Cot's sensitivity sums ONLY the rows Cot's publishes a dollar
    figure for. That is a committed-contract subtotal, not a complete
    team payroll (unsigned / arbitration / option rows carry markers,
    not numbers). Its statuses are arithmetic on that subtotal and are
    labeled as such everywhere they appear.
  - Spend "equivalent signings" are arithmetic on the pool's price
    distribution, not a recommendation and not a roster plan.
  - Benefits / pre-arb-pool definition sensitivities are NOT modeled:
    no committed team-level figure separates them on either basis.
    The artifact says so in one line instead of inventing a split.
Output: data/cap_transition_2027.json
"""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CAP = 245_300_000
FLOOR = 171_200_000
PER_PLAYER_MAX = int(0.15 * CAP)  # 36,795,000
COTS_CODE = {"CHW": "CWS"}  # Cot's file codes the White Sox CWS


def load(name):
    return json.loads((DATA / name).read_text())


def status_of(payroll):
    if payroll > CAP:
        return "OVER CAP"
    if payroll < FLOOR:
        return "UNDER FLOOR"
    return "INSIDE THE BAND"


def main():
    cap = load("cap_scenario_2027.json")
    assert cap["cap_2027"] == CAP and cap["floor_2027"] == FLOOR
    forced = {t["team"]: t for t in load("forced_sellers_2027.json")["teams"]}
    sal = load("salaries_2026.json")
    sal_by_key = {}
    sal_rows_by_team = {}
    for p in sal["players"]:
        sal_by_key[(p["team"], p["salary_2026"])] = p
        sal_rows_by_team[p["team"]] = sal_rows_by_team.get(p["team"], 0) + 1
    # the forced-seller file mangles one name ("Jr. Vladimir Guerrero
    # Jr."); the (team, salary) key is the reliable join.
    xwalk = {r["name"]: r["mlbam_id"] for r in load("player_xwalk.json")}
    war_by_id = {}
    for f in ("fg_steamer_2027_bat.json", "fg_steamer_2027_pit.json"):
        for r in load(f):
            mid = r.get("xMLBAMID")
            if mid and r.get("WAR") is not None:
                war_by_id[mid] = war_by_id.get(mid, 0.0) + r["WAR"]

    cots = load("salaries_cots_2027.json")["players"]
    cots_subtotal, cots_rows, cots_flags = {}, {}, {}
    for p in cots:
        t = p["team"]
        cots_subtotal[t] = cots_subtotal.get(t, 0) + p["salary_lrp_2027"]
        cots_rows[t] = cots_rows.get(t, 0) + 1
        aav = p.get("cb_2027_aav")
        if aav is not None and aav > PER_PLAYER_MAX:
            cots_flags.setdefault(t, []).append(
                {"name": p["name"], "contract": p["contract"], "aav": aav})

    fa = load("fa_shopping_2027.json")["class"]
    pool_prices = sorted(p["prev_aav"] for p in fa
                         if p.get("prev_aav") and p.get("steamer_war") is not None)
    assert len(pool_prices) == 199, len(pool_prices)
    def _pct(sorted_vals, q):
        pos = (len(sorted_vals) - 1) * q
        lo, hi = math.floor(pos), math.ceil(pos)
        if lo == hi:
            return sorted_vals[int(pos)]
        return int(round(sorted_vals[lo] * (hi - pos)
                         + sorted_vals[hi] * (pos - lo)))

    pool = {
        "n": len(pool_prices),
        "price_field": "prev_aav (prior-contract AAV anchor, Spotrac FA class)",
        "min": pool_prices[0],
        "p25": _pct(pool_prices, 0.25),
        "median": int(statistics.median(pool_prices)),
        "mean": round(statistics.mean(pool_prices), 2),
        "p75": _pct(pool_prices, 0.75),
        "max": pool_prices[-1],
    }
    mixed = load("optimizer_sensitivity_2027.json")["mixed_floor"]

    rows = []
    for t in sorted(cap["teams"], key=lambda r: -r["gap_to_cap"]):
        team = t["team"]
        payroll = int(round(CAP + t["gap_to_cap"]))
        status = status_of(payroll)
        row = {
            "team": team,
            "payroll": payroll,
            "payroll_basis": "Spotrac payroll total",
            "payroll_source": "data/cap_scenario_2027.json",
            "status": status,
            "gap_to_cap": t["gap_to_cap"],
            "gap_to_floor": t["gap_to_floor"],
            "spotrac_contract_rows": sal_rows_by_team.get(team, 0),
        }
        if status == "OVER CAP":
            fs = forced[team]
            if fs["covered"]:
                contracts = []
                war_total = 0.0
                for s in fs["shed"]:
                    sp = sal_by_key[(team, s["salary_2026"])]
                    pid = (sp.get("player_id") or xwalk.get(s["name"])
                           or xwalk.get(s["name"].removeprefix("Jr. ")))
                    w = war_by_id.get(pid)
                    assert w is not None, (team, s["name"], pid)
                    war_total += w
                    contracts.append({
                        "name": s["name"], "pos": s["pos"],
                        "salary_2026": s["salary_2026"],
                        "steamer_war_2027": round(w, 2)})
                row["action"] = {
                    "type": "shed", "covered": True,
                    "contracts": contracts,
                    "n_contracts": fs["n_shed"],
                    "shed_total": fs["shed_total"],
                    "shed_war_total": round(war_total, 2),
                    "payroll_after_shed": payroll - fs["shed_total"],
                    "method": fs.get("method") or
                    "minimal largest-first contract prefix covering the "
                    "cap gap (Cycle 30)"}
            else:
                row["action"] = {
                    "type": "shed", "covered": False, "contracts": [],
                    "statement": "shed set not covered — payroll basis gap",
                    "reason": fs["reason"]}
        elif status == "UNDER FLOOR":
            short = int(round(t["gap_to_floor"]))
            row["action"] = {
                "type": "spend", "shortfall": short,
                "equivalent_signings_at_pool_median":
                    math.ceil(short / pool["median"]),
                "equivalent_signings_at_pool_p75":
                    math.ceil(short / pool["p75"]),
                "note": "Arithmetic only: the shortfall divided by the "
                        "optimizer pool's price points. Not a roster "
                        "plan and not a recommendation."}
        else:
            below_cap = CAP - payroll
            above_floor = payroll - FLOOR
            row["action"] = {
                "type": "none",
                "distance_to_cap": below_cap,
                "distance_to_floor": above_floor,
                "nearest_boundary": ("cap" if below_cap <= above_floor
                                     else "floor"),
                "statement": "Inside the band on the primary basis."}
        code = COTS_CODE.get(team, team)
        sub = cots_subtotal.get(code, 0)
        cstatus = status_of(sub)
        row["per_player_max_check"] = {
            "basis": "Cot's CBT AAV (cb_2027_aav) — the committed AAV field",
            "threshold": PER_PLAYER_MAX,
            "flags": sorted(cots_flags.get(code, []),
                            key=lambda r: -r["aav"]),
            "count": len(cots_flags.get(code, []))}
        row["cots_sensitivity"] = {
            "basis": "Cot's published LRP-2027 rows (committed-contract "
                     "subtotal, not a complete payroll)",
            "team_code": code,
            "published_rows": cots_rows.get(code, 0),
            "published_lrp_subtotal": sub,
            "status_on_subtotal": cstatus,
            "amount_over_cap": max(sub - CAP, 0),
            "amount_under_floor": max(FLOOR - sub, 0),
            "agrees_with_primary": cstatus == status}
        rows.append(row)

    def _summary(key_status, key_amount_over, key_amount_under):
        out = {}
        for label in ("OVER CAP", "UNDER FLOOR", "INSIDE THE BAND"):
            sel = [r for r in rows if key_status(r) == label]
            out[label] = {"count": len(sel),
                          "teams": [r["team"] for r in sel]}
            if label == "OVER CAP":
                out[label]["total_over"] = int(round(
                    sum(key_amount_over(r) for r in sel)))
            if label == "UNDER FLOOR":
                out[label]["total_under"] = int(round(
                    sum(key_amount_under(r) for r in sel)))
        return out

    primary = _summary(lambda r: r["status"],
                       lambda r: max(r["gap_to_cap"], 0),
                       lambda r: max(r["gap_to_floor"], 0))
    cots_summary = _summary(lambda r: r["cots_sensitivity"]["status_on_subtotal"],
                            lambda r: r["cots_sensitivity"]["amount_over_cap"],
                            lambda r: r["cots_sensitivity"]["amount_under_floor"])
    changed = [r["team"] for r in rows
               if not r["cots_sensitivity"]["agrees_with_primary"]]

    out = {
        "metadata": {
            "cycle": 64,
            "title": "2027 Cap Transition ledger",
            "system": {"cap": CAP, "floor": FLOOR,
                       "per_player_max": PER_PLAYER_MAX,
                       "per_player_pct": 0.15,
                       "status": "owners' proposed system; not law"},
            "inputs": [
                "data/cap_scenario_2027.json (Cycle 22 Spotrac payroll "
                "totals, all 30 teams)",
                "data/forced_sellers_2027.json (Cycle 30 shed sets, 6 of "
                "7 over-cap teams)",
                "data/salaries_2026.json (Spotrac per-player rows, 927, "
                "24 of 30 teams)",
                "data/fg_steamer_2027_bat.json + "
                "data/fg_steamer_2027_pit.json (Steamer 2027 WAR)",
                "data/salaries_cots_2027.json (Cot's LRP-2027 rows, 237, "
                "30 teams; CBT AAV field)",
                "data/fa_shopping_2027.json (optimizer pool, 199 players)",
                "data/optimizer_sensitivity_2027.json (Cycle 50 mixed "
                "floor frame)"],
            "primary_basis": "Payroll totals are the Spotrac totals in "
                             "cap_scenario_2027.json (all 30 teams). "
                             "Per-player Spotrac contract rows exist for "
                             "24 of 30 teams; the six without rows are "
                             "ARI, BOS, CHC, MIL, TB, TEX (Spotrac page "
                             "failures, logged in salaries_2026.json).",
            "cots_sensitivity_basis": "Sum of the 237 rows for which "
                                      "Cot's publishes an LRP-2027 dollar "
                                      "figure — a committed-contract "
                                      "subtotal, not a complete team "
                                      "payroll. Rows for unsigned, "
                                      "arbitration and option players "
                                      "carry markers, not numbers, in "
                                      "Cot's. Statuses on this basis are "
                                      "arithmetic on the subtotal.",
            "shed_war_method": "Steamer 2027 WAR joined by MLBAM id from "
                               "salaries_2026.json (player_xwalk.json for "
                               "the one row with no id); batting + "
                               "pitching WAR summed for the one two-way "
                               "player (Ohtani).",
            "spend_shape_method": "Shortfall divided by the optimizer "
                                  "pool's prior-AAV price points (median "
                                  "and 75th percentile). Arithmetic "
                                  "only.",
            "mixed_floor_frame": {
                "source": "data/optimizer_sensitivity_2027.json "
                          "(Cycle 50)",
                "total_war": mixed["total_war"],
                "spend": mixed["spend"],
                "n_prearb_slots": mixed["n_prearb_slots"],
                "n_fa_slots": mixed["n_fa_slots"],
                "note": "League-level frame, not team-specific: a "
                        "26-man floor roster reaches 74.8 WAR for "
                        "$96.2M when 19 slots are internal pre-arb "
                        "production at the $1.0M placeholder. A club "
                        "cannot sign another club's pre-arb players; "
                        "the frame shows the floor is survivable with "
                        "internal production, not a shopping list."},
            "definition_sensitivity": "Not modeled: no committed "
                                      "team-level figure separates "
                                      "benefits or the pre-arb pool on "
                                      "either basis, so no split is "
                                      "shown.",
        },
        "pool_price_distribution": pool,
        "summary": {
            "primary": primary,
            "cots_published_rows": cots_summary,
            "status_changes_between_bases": {"count": len(changed),
                                             "teams": changed},
            "per_player_flags_total": sum(
                r["per_player_max_check"]["count"] for r in rows),
        },
        "teams": rows,
    }
    (DATA / "cap_transition_2027.json").write_text(json.dumps(out, indent=1))
    print(f"primary: over {primary['OVER CAP']['count']} "
          f"(${primary['OVER CAP']['total_over']/1e6:.1f}M), "
          f"under {primary['UNDER FLOOR']['count']} "
          f"(${primary['UNDER FLOOR']['total_under']/1e6:.1f}M), "
          f"in band {primary['INSIDE THE BAND']['count']}")
    print(f"Cot's subtotal: over {cots_summary['OVER CAP']['count']}, "
          f"under {cots_summary['UNDER FLOOR']['count']}, "
          f"in band {cots_summary['INSIDE THE BAND']['count']}; "
          f"status changes {len(changed)}: {changed}")
    print(f"15% flags: {out['summary']['per_player_flags_total']}")
    print("wrote data/cap_transition_2027.json")


if __name__ == "__main__":
    main()
