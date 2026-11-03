#!/usr/bin/env python3
"""Cycle 71: ARBITRAGE — surplus-value layer (Moneyball 2.0). Closing.

Front-office framing (Miami Marlins VP of Baseball Systems, Posit Data
Science Hangout Aug 2025): the operative number is SURPLUS VALUE =
projected future value (dollars) MINUS contract obligations. A player
traded or signed only when what you think they're worth exceeds what
the market will cost you. This is not a new analysis — it is the
Marlins' operating metric computed from numbers this repo already
commits, so the arbitrage claim is real, not invented.

What this cycle adds to the committed DAO:
  data/surplus_value_2027.json — per-free-agent surplus:
      value_usd  = steamer_war * market_usd_per_war
      cost_aav   = spotrac_market_aav (what the market is expected to
                   pay in 2027, NOT the prior-AAV last-price anchor)
      surplus_usd = value_usd - cost_aav
  plus the skill-split arbitrage from the committed Hakes–Sauer run:
      top-quartile CONTACT hitters cost ~$8.0M/WAR vs bottom-quartile
      ~$15.0M/WAR (median_dollars_per_war, data/hakes_sauer_results.json)
      -> buying contact/OBP skill is buying dollars-per-win ~half of
         buying a power lottery ticket. THAT is the arbitrage window.

Inputs (both committed, never synthesized):
  data/fa_shopping_2027.json     — steamer_war, spotrac_market_aav,
                                   prev_aav, pos, age, type, player_id
  data/hakes_sauer_results.json  — median_dollars_per_war by quartile
                                   (the defensible market $/WAR frame)

Exit 1 + FLAG if any free agent in the contracted rate set is missing
surplus computation (fail-closed): never ship a partial arbitrage list.
"""
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, "data")
OUT = os.path.join(DATA, "surplus_value_2027.json")

# Defensible market value rate. The Hakes–Sauer committed run gives the
# FRAME: overall median dollars per WAR across contract rate quartiles.
# Take the overall median of the FA class's OWN implied market rate
# (spotrac_market_aav / steamer_war) as the value-assignment rate — a
# market-implied rate from the same committed source we already trust,
# not an external invented figure. Never invent a rate not in the data.
def market_rate(rows):
    implied = []
    for r in rows:
        if r.get("steamer_war") and r.get("spotrac_market_aav") and r["steamer_war"] > 0:
            implied.append(r["spotrac_market_aav"] / r["steamer_war"])
    if not implied:
        raise SystemExit(1)
    return statistics.median(implied)


def main():
    fj = os.path.join(DATA, "fa_shopping_2027.json")
    hj = os.path.join(DATA, "hakes_sauer_results.json")
    d = json.load(open(fj))
    h = json.load(open(hj))
    rows = d.get("top25_by_war", [])
    if not rows:
        raise SystemExit("FLAG: no free agents in fa_shopping_2027.json")
    rate = market_rate(rows)

    hs = h.get("quartile_tables", {}).get("sample_S_spotrac_basis", {}).get("by_contact_pct", {})
    q_rate_top = hs.get("top_quartile", {}).get("median_dollars_per_war")
    q_rate_bot = hs.get("bottom_quartile", {}).get("median_dollars_per_war")
    ratio = hs.get("top_to_bottom_median_dpw_ratio")

    surplus = []
    missing = []
    for r in rows:
        war = r.get("steamer_war")
        market = r.get("spotrac_market_aav")
        if war is None or market is None:
            missing.append(r.get("name"))
            continue
        value = war * rate
        layout = {
            "name": r["name"], "player_id": r["player_id"], "pos": r["pos"],
            "age": r.get("age"), "type": r.get("type"), "prev_team": r.get("prev_team"),
            "steamer_war": round(war, 3),
            "market_usd_per_war": round(rate),
            "value_usd": round(value),
            "cost_aav": round(market),
            "surplus_usd": round(value - market),
            "surplus_pct": round(100.0 * (value - market) / market, 1) if market else None,
            "prev_aav": r.get("prev_aav"),
            "qoi": r.get("qoi"),
        }
        surplus.append(layout)
    if missing:
        raise SystemExit(f"FLAG: no market AAV / WAR for: {', '.join(missing)}")
    surplus.sort(key=lambda x: x["surplus_usd"], reverse=True)

    # The skill-split arbitrage: contact hitters cost half per WAR.
    arb = None
    if q_rate_top and q_rate_bot and ratio is not None:
        arb = {
            "contact_arbitrage_text": (
                f"Top-quartile CONTACT hitters cost ~${q_rate_top/1e6:.1f}M "
                f"per WAR vs ~${q_rate_bot/1e6:.1f}M for the bottom quartile "
                f"(~{ratio*100:.0f}% of the cost) — committed Hakes–Sauer run, "
                "data/hakes_sauer_results.json. Buying contact/OBP skill is "
                "buying wins at roughly half the dollars-per-win of a power "
                "lottery ticket. Descriptive contrast, not a proven price "
                "effect (the Hakes–Sauer test was INCONCLUSIVE on mispricing); "
                "the surplus value below uses one market-implied $/WAR for ALL "
                "players, so skill differences show as the market sees them."
            ),
            "top_quartile_contact_usd_per_war": q_rate_top,
            "bottom_quartile_contact_usd_per_war": q_rate_bot,
            "top_to_bottom_ratio": ratio,
        }

    out = {
        "cycle": 71,
        "question": "Which 2027 free agents carry positive surplus value — projected dollars of wins vs expected market cost — and does the committed contact-per-WAR discount surface as an arbitrage?",
        "method": (
            "For every free agent with both Steamer WAR and a Spotrac market AAV: "
            "value_usd = steamer_war * market_usd_per_war, where market_usd_per_war "
            "is the MEDIAN of the class's own implied rate (spotrac_market_aav / "
            "steamer_war). surplus_usd = value_usd - cost_aav. This mirrors the "
            "Marlins' front-office surplus-value framework. The market $/WAR and "
            "costs are all from committed data; no rates invented."
        ),
        "caveat": (
            "Surplus value is a VALUATION, not a settled mispricing. It answers "
            "'at the market's own median dollars-per-win, is this player priced "
            "below that?' It does NOT prove the market is wrong on any one player "
            "— a cheap player may be cheap because of injury, age, or role risk. "
            "Use it to arrange the shopping list by arbitrage, then weigh the "
            "bummers manually. The Hakes–Sauer mispricing test stayed INCONCLUSIVE, "
            "so this is the framework the operator decides on, not a theorem."
        ),
        "market_usd_per_war": round(rate),
        "n": len(surplus),
        "n_surplus_positive": sum(1 for s in surplus if s["surplus_usd"] > 0),
        "top_surplus": surplus[:10],
        "contact_skill_arbitrage": arb,
        "sources": [
            "data/fa_shopping_2027.json (Spotrac FA class + FanGraphs Steamer WAR)",
            "data/hakes_sauer_results.json (Cycle 46, committed $/WAR by contact quartile, quartile_tables/sample_S_spotrac_basis)",
        ],
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}: {len(surplus)} free agents, market $/WAR ${rate/1e6:.2f}M, "
          f"{out['n_surplus_positive']} surplus-positive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
