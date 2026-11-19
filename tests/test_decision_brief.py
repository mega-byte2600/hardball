import json
from pathlib import Path

import decision_brief as db

ROOT = Path(__file__).resolve().parent.parent
UNC = json.loads((ROOT / "data" / "uncertainty_scenarios_2027.json").read_text())


def card(name, pos="C", war=3.0, price=10e6, group="hitter", vol=600):
    return {"name": name, "player_id": 1, "pos": pos, "group": group, "prev_team": "X",
            "type": "UFA", "qoi": False, "delivered_war": war, "spotrac_market_aav": price,
            "prev_aav": None, "volume": vol, "availability_used_for_delivered": 1.0,
            "availability": 1.0, "risk_flag": False}


def test_ranking_exclusions_and_fallback():
    cards = [card("A", war=4), card("B", war=2), card("Signed Guy", war=9), card("Tiny", war=0.5)]
    rows = db.build_rows(cards, UNC, 8e6, {"signed guy"}, {})
    assert [r["name"] for r in rows] == ["A", "B"]
    assert rows[0]["fallback"] == "B" and rows[1]["fallback"] == ""
    assert rows[0]["surplus_usd"] == int(4 * 8e6 - 10e6)
    assert rows[0]["war_p10"] < 4 < rows[0]["war_p90"]
    assert rows[0]["act_by"] == db.CBA_EXPIRY


def test_band_widens_with_volume():
    assert db.war_sd(card("x", vol=600), UNC) > db.war_sd(card("x", vol=300), UNC) > 0
    assert db.war_sd(card("p", group="pitcher", vol=180), UNC) > 0


def test_committed_brief_matches_builder():
    brief = json.loads((ROOT / "data" / "decision_brief_2027.json").read_text())
    assert len(brief["top"]) == db.TOP_N
    assert [r["rank"] for r in brief["top"]] == list(range(1, db.TOP_N + 1))
