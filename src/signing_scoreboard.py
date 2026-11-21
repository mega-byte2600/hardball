"""Signing Scoreboard: every confirmed free-agent signing vs. what Hardball said.

Closes the loop on the decision brief. For each signing CONFIRMED by the MLB
StatsAPI transactions feed (move type SFA, lane SIGNED in
data/tracker_ticker_2026.json), it records what Hardball's model said about
that player BEFORE excluding signed players: rank among priced candidates,
delivered WAR with its P10-P90 band, price estimate and basis, and surplus.
For a top-10 signing it names the fallback the brief now points to.

Rules (CLAUDE.md / CarpeDATA):
* No new API calls. Signings come from the committed tracker; history is kept
  in an append-only log (data/signings_observed.jsonl) because the tracker is
  a rolling 7-day window. `--backfill-git` replays committed tracker versions.
* Social posts and reports never count: only StatsAPI-confirmed SFA moves.
* Contract terms are NOT in the feed and are never scraped; the scoreboard
  says so instead of guessing a price.

Outputs: data/signings_observed.jsonl (append-only) and
data/signing_scoreboard_2027.json (deterministic summary for the dashboard).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

import decision_brief as db

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OBSERVED = DATA / "signings_observed.jsonl"
OUT = DATA / "signing_scoreboard_2027.json"
TRACKER = "data/tracker_ticker_2026.json"


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace(".", "").replace("-", " ").split())


def confirmed_signings(tracker: Mapping) -> List[Dict]:
    """StatsAPI-confirmed free-agent signings only (move type SFA)."""
    out = []
    for i in tracker.get("items", []):
        if i.get("lane") == "SIGNED" and str(i.get("move_type", "")).startswith("SFA") and i.get("player"):
            out.append({"statsapi_transaction_id": i.get("statsapi_transaction_id"), "player": i["player"],
                        "team": i.get("team"), "date": i.get("source_pubdate"), "title": i.get("title"),
                        "source": "MLB StatsAPI transactions"})
    return out


def read_observed(path: Path = OBSERVED) -> List[Dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def append_observed(new: Iterable[Mapping], path: Path = OBSERVED) -> int:
    seen = {r["statsapi_transaction_id"] for r in read_observed(path)}
    rows = [dict(r) for r in new if r.get("statsapi_transaction_id") not in seen]
    rows.sort(key=lambda r: (r.get("date") or "", r["statsapi_transaction_id"] or 0))
    if rows:
        with path.open("a") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
    return len(rows)


def git_tracker_versions() -> List[Mapping]:
    """Committed versions of the tracker (offline: local git history only)."""
    try:
        shas = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H", "--", TRACKER],
                              check=True, capture_output=True, text=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return []
    out = []
    for sha in reversed(shas):
        try:
            out.append(json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:{TRACKER}"],
                                                 check=True, capture_output=True, text=True).stdout))
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            continue
    return out


def model_view() -> Dict[str, Dict]:
    """What Hardball said about every priced FA, ranked WITHOUT excluding signings."""
    cards = db._load("fa_health_cards_2027.json")["cards"]
    unc = db._load("uncertainty_scenarios_2027.json")
    sv = db._load("surplus_value_2027.json")
    rows = db.build_rows(cards, unc, float(sv["market_usd_per_war"]), set(), db.posting_deadlines())
    view = {norm(r["name"]): r for r in rows}
    pool = {norm(c["name"]): c for c in cards}
    return {"ranked": view, "pool": pool, "n_ranked": len(rows)}


def build(observed: List[Mapping], view: Mapping) -> Dict:
    ranked, pool, n = view["ranked"], view["pool"], view["n_ranked"]
    rows = []
    for s in observed:
        k = norm(s["player"])
        r, card = ranked.get(k), pool.get(k)
        if not card:
            continue  # not in the 2027 FA class Hardball tracks (minor-league depth, etc.)
        if r:
            verdict = (f"Hardball had him #{r['rank']} of {n} "
                       f"({'top 10' if r['rank'] <= 10 else 'outside the top 10'}): "
                       f"{r['delivered_war']:.1f} delivered WAR (P10-P90 {r['war_p10']:.1f}-{r['war_p90']:.1f}), "
                       f"estimated price ${r['price_aav_usd'] / 1e6:.1f}M, surplus {r['surplus_usd'] / 1e6:+.1f}M.")
        else:
            verdict = ("In the FA pool but not ranked: under 1.0 delivered WAR or no price on record "
                       f"(delivered WAR {float(card.get('delivered_war') or 0):.2f}).")
        rows.append({
            "player": s["player"], "team": s.get("team"), "date": s.get("date"),
            "statsapi_transaction_id": s.get("statsapi_transaction_id"),
            "hardball_rank": r["rank"] if r else None, "in_top10": bool(r and r["rank"] <= 10),
            "delivered_war": r["delivered_war"] if r else card.get("delivered_war"),
            "war_p10": r["war_p10"] if r else None, "war_p90": r["war_p90"] if r else None,
            "price_estimate_usd": r["price_aav_usd"] if r else None,
            "price_basis": r["price_basis"] if r else None,
            "surplus_usd": r["surplus_usd"] if r else None,
            "fallback_now": r["fallback"] if r and r["rank"] <= 10 else None,
            "health_flag": bool(card.get("risk_flag")),
            "contract_terms": "not in the StatsAPI feed; not scraped",
            "verdict": verdict,
        })
    rows.sort(key=lambda x: (x["date"] or "", x["hardball_rank"] or 10**6))
    top10 = [x for x in rows if x["in_top10"]]
    return {
        "metadata": {
            "question": "When a free agent signs, what did Hardball say about him beforehand?",
            "source": "MLB StatsAPI transactions (SFA moves) via data/tracker_ticker_2026.json; "
                      "model view from data/decision_brief_2027.json inputs (signings not excluded)",
            "observed_log": "data/signings_observed.jsonl (append-only; tracker is a rolling 7-day window)",
            "limits": "Contract terms are not in the feed and are never scraped, so price accuracy "
                      "cannot be scored yet; only who signed vs. Hardball's ranking and value view.",
            "candidates_ranked": n,
        },
        "summary": {
            "signings_in_fa_pool": len(rows),
            "of_which_hardball_top10": len(top10),
            "of_which_ranked": sum(1 for x in rows if x["hardball_rank"]),
            "positive_surplus_signed": sum(1 for x in rows if (x["surplus_usd"] or 0) > 0),
        },
        "signings": rows,
    }


def main(argv: List[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    added = 0
    if "--backfill-git" in argv:
        for t in git_tracker_versions():
            added += append_observed(confirmed_signings(t))
    added += append_observed(confirmed_signings(json.loads((DATA / "tracker_ticker_2026.json").read_text())))
    out = build(read_observed(), model_view())
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    s = out["summary"]
    print(f"observed +{added}; FA-pool signings {s['signings_in_fa_pool']} "
          f"(Hardball top 10: {s['of_which_hardball_top10']}, ranked: {s['of_which_ranked']}) -> {os.path.relpath(OUT, ROOT)}")
    for x in out["signings"]:
        print(f"  {x['date']} {x['player']} -> {x['team']}: {x['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
