"""Decision brief: the ranked, exportable "top moves" list for 2027.

Reviewers found the recommendation scattered across Figures 16, 22 and 25.
This module joins the committed artifacts into one ranked table a front
office can act on, with every column traced to an input:

* delivered WAR       — data/fa_health_cards_2027.json (Steamer x measured
                        availability + residual-bias term, Cycle 67)
* P10-P90 WAR band    — normal approximation from the measured Marcel
                        backtest error pools in data/uncertainty_scenarios_2027
                        (SD = MAE * sqrt(pi/2)), converted to WAR at delivered
                        volume with the same run-value slopes and
                        runs-to-WAR scale the roster Monte Carlo uses.
* price               — Spotrac market-value AAV estimate when present, else
                        prior-contract AAV; the basis is stated per row.
* $/WAR               — the market median in data/surplus_value_2027.json.
* availability status — SIGNED rows from the MLB StatsAPI transactions
                        tracker (data/tracker_ticker_2026.json) are excluded.
* act-by date         — Dec 1 2026 (CBA expiry, the date the proposed cap
                        regime would start governing) or, for posted NPB/KBO
                        players, the posting signing deadline.
* fallback            — the next-ranked available player at the same position.

Outputs data/decision_brief_2027.json and dashboard/decision_brief_2027.csv.
"""
from __future__ import annotations

import csv
import json
import math
import os
from typing import Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CBA_EXPIRY = "2026-12-01"
Z90 = 1.2815515655446004  # standard-normal 90th percentile
MIN_DELIVERED_WAR = 1.0
TOP_N = 10


def _load(name: str):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def war_sd(card: dict, unc: dict) -> float:
    """One-season WAR SD for a player at delivered volume."""
    k = math.sqrt(math.pi / 2)  # MAE -> SD under normal errors
    pools, scale = unc["error_pools"], unc["runs_to_war_scale"]
    vol = float(card.get("volume") or 0) * float(card.get("availability_used_for_delivered") or 0)
    if card["group"] == "hitter":
        rv = unc["run_value_slopes"]
        sd_obp = pools["hitters"]["mae_obp"] * k
        sd_slg = pools["hitters"]["mae_slg"] * k
        runs_sd = vol * math.hypot(rv["runs_per_pa_per_unit_obp"] * sd_obp,
                                   rv["runs_per_pa_per_unit_slg"] * sd_slg)
        return runs_sd * scale["hitters"]["slope_war_per_run"]
    sd_era = pools["pitchers"]["mae_era"] * k
    return vol / 9.0 * sd_era * scale["pitchers"]["slope_war_per_run"]


def signed_names(tracker: dict) -> set[str]:
    return {i["player"].strip().lower() for i in tracker.get("items", [])
            if i.get("lane") == "SIGNED" and i.get("player")}


def posting_deadlines() -> dict[str, str]:
    try:
        pc = _load("posted_class_2026.json")
    except FileNotFoundError:
        return {}
    out: dict[str, str] = {}
    players = pc.get("players") or pc.get("class") or []
    for p in players if isinstance(players, list) else []:
        if p.get("name") and p.get("signing_deadline"):
            out[p["name"].strip().lower()] = p["signing_deadline"][:10]
    return out


def build_rows(cards: Iterable[dict], unc: dict, usd_per_war: float,
               signed: set[str], deadlines: dict[str, str]) -> list[dict]:
    rows = []
    for c in cards:
        name = c["name"].strip()
        if name.lower() in signed:
            continue
        dw = float(c.get("delivered_war") or 0)
        if dw < MIN_DELIVERED_WAR:
            continue
        if c.get("spotrac_market_aav"):
            price, basis = float(c["spotrac_market_aav"]), "Spotrac market-value AAV"
        elif c.get("prev_aav"):
            price, basis = float(c["prev_aav"]), "prior-contract AAV (anchor)"
        else:
            continue
        sd = war_sd(c, unc)
        surplus = dw * usd_per_war - price
        rows.append({
            "name": name, "player_id": c["player_id"], "pos": c["pos"],
            "group": c["group"], "prev_team": c["prev_team"], "type": c["type"],
            "qualifying_offer": bool(c.get("qoi")),
            "delivered_war": round(dw, 2),
            "war_p10": round(dw - Z90 * sd, 2), "war_p90": round(dw + Z90 * sd, 2),
            "price_aav_usd": int(round(price)), "price_basis": basis,
            "surplus_usd": int(round(surplus)),
            "surplus_p10_usd": int(round((dw - Z90 * sd) * usd_per_war - price)),
            "usd_per_delivered_war": int(round(price / dw)),
            "availability": c.get("availability"),
            "health_flag": bool(c.get("risk_flag")),
            "act_by": deadlines.get(name.lower(), CBA_EXPIRY),
        })
    rows.sort(key=lambda r: (-r["surplus_usd"], r["name"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    by_pos: dict[str, list[dict]] = {}
    for r in rows:
        by_pos.setdefault(r["pos"], []).append(r)
    for r in rows:
        alts = [a["name"] for a in by_pos[r["pos"]] if a["rank"] > r["rank"]]
        r["fallback"] = alts[0] if alts else ""
    return rows


def main() -> None:
    cards = _load("fa_health_cards_2027.json")["cards"]
    unc = _load("uncertainty_scenarios_2027.json")
    sv = _load("surplus_value_2027.json")
    tracker = _load("tracker_ticker_2026.json")
    rows = build_rows(cards, unc, float(sv["market_usd_per_war"]),
                      signed_names(tracker), posting_deadlines())
    top = rows[:TOP_N]
    out = {
        "metadata": {
            "question": "Which available 2027 free agents return the most "
                        "delivered WAR per dollar, and by when must we act?",
            "rank_by": "surplus = delivered WAR x market $/WAR - price",
            "market_usd_per_war": sv["market_usd_per_war"],
            "band": "P10-P90 of one-season delivered WAR, normal approximation "
                    "to the measured Marcel error pools (correlation between "
                    "OBP and SLG errors ignored; availability held at its "
                    "measured value)",
            "excluded": "players SIGNED per the MLB StatsAPI transactions "
                        "tracker; delivered WAR < 1.0; no price on record",
            "limits": "Price is an estimate, not a predicted 2027 contract; "
                      "the Hakes-Sauer mispricing test is INCONCLUSIVE, so "
                      "surplus ranks a shopping order, not a proven edge.",
            "n_candidates": len(rows),
            "inputs": ["data/fa_health_cards_2027.json",
                       "data/uncertainty_scenarios_2027.json",
                       "data/surplus_value_2027.json",
                       "data/tracker_ticker_2026.json",
                       "data/posted_class_2026.json"],
        },
        "top": top,
    }
    with open(os.path.join(DATA, "decision_brief_2027.json"), "w") as f:
        json.dump(out, f, indent=1)
    csv_path = os.path.join(ROOT, "dashboard", "decision_brief_2027.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in top:
        print(f"{r['rank']:>2} {r['name']:<22} {r['pos']:<3} WAR {r['delivered_war']:>4} "
              f"[{r['war_p10']}, {r['war_p90']}] ${r['price_aav_usd']/1e6:.1f}M "
              f"surplus ${r['surplus_usd']/1e6:.1f}M act by {r['act_by']} "
              f"fallback {r['fallback']}")
    print(f"wrote data/decision_brief_2027.json + {csv_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
