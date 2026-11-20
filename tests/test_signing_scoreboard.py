import json

import signing_scoreboard as sb


def _tracker(*items):
    return {"items": list(items)}


def _item(tid, player, move="SFA — Signed free agent", lane="SIGNED"):
    return {"lane": lane, "statsapi_transaction_id": tid, "player": player, "team": "Minnesota Twins",
            "source_pubdate": "2026-11-18", "move_type": move, "title": f"signed {player}"}


def test_only_statsapi_confirmed_sfa_moves_count():
    t = _tracker(_item(1, "Sonny Gray"), _item(2, "X", move="DES — Designated for assignment"),
                 _item(3, "Y", lane="REPORTED"))
    assert [s["player"] for s in sb.confirmed_signings(t)] == ["Sonny Gray"]


def test_observed_log_is_append_only_and_deduped(tmp_path):
    log = tmp_path / "obs.jsonl"
    assert sb.append_observed(sb.confirmed_signings(_tracker(_item(1, "A"), _item(2, "B"))), log) == 2
    first = log.read_text()
    assert sb.append_observed(sb.confirmed_signings(_tracker(_item(2, "B"), _item(3, "C"))), log) == 1
    assert log.read_text().startswith(first) and len(sb.read_observed(log)) == 3


def test_scoreboard_reports_rank_value_and_unranked_without_inventing_prices():
    view = {"n_ranked": 2,
            "ranked": {"sonny gray": {"rank": 2, "delivered_war": 2.7, "war_p10": 1.0, "war_p90": 4.4,
                                      "price_aav_usd": 19_400_000, "price_basis": "Spotrac", "surplus_usd": 2_900_000,
                                      "fallback": "Kevin Gausman"}},
            "pool": {"sonny gray": {"name": "Sonny Gray"}, "deep arm": {"name": "Deep Arm", "delivered_war": 0.2}}}
    obs = [{"player": "Sonny Gray", "team": "MIN", "date": "2026-11-18", "statsapi_transaction_id": 1},
           {"player": "Deep Arm", "team": "DET", "date": "2026-11-17", "statsapi_transaction_id": 2},
           {"player": "Not In Pool", "team": "SD", "date": "2026-11-17", "statsapi_transaction_id": 3}]
    out = sb.build(obs, view)
    assert out["summary"] == {"signings_in_fa_pool": 2, "of_which_hardball_top10": 1,
                              "of_which_ranked": 1, "positive_surplus_signed": 1}
    gray = next(r for r in out["signings"] if r["player"] == "Sonny Gray")
    assert gray["in_top10"] and gray["fallback_now"] == "Kevin Gausman" and "#2 of 2" in gray["verdict"]
    deep = next(r for r in out["signings"] if r["player"] == "Deep Arm")
    assert deep["price_estimate_usd"] is None and "not ranked" in deep["verdict"]
    assert all(r["contract_terms"].startswith("not in the StatsAPI feed") for r in out["signings"])


def test_name_normalization_handles_accents():
    assert sb.norm("Emilio Pagán") == sb.norm("emilio pagan")


def test_committed_scoreboard_is_consistent():
    from pathlib import Path
    d = json.loads((Path(__file__).resolve().parent.parent / "data" / "signing_scoreboard_2027.json").read_text())
    assert d["summary"]["signings_in_fa_pool"] == len(d["signings"])
    assert d["summary"]["of_which_hardball_top10"] == sum(r["in_top10"] for r in d["signings"])
