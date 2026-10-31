"""ESPN validation connector: cross-checks MLB API numbers (CarpeData redundancy).

Endpoint (verified live): site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/
statistics/byathlete?category=batting&season=&seasontype=2&sort=batting.homeRuns:desc

ESPN returns each player's batting stats as an ordered `totals[]` array with NO
field names, so we decode positions by correlation: for each array index we
correlate the column across all players against the corresponding MLB API
column we already trust in the lake. The highest-correlation MLB field wins.
This is data-driven decoding — no hardcoded assumption about endpoint order.
"""
import json
import os
import sqlite3

import requests
from numpy import corrcoef
from pandas import DataFrame, isna

UA = {"User-Agent": "Mozilla/5.0 (HARDBALL)"}
ESPN = "https://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/statistics/byathlete"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def fetch_espn_batting(season: int, pages: int = 3):
    """Pull full batting leaderboard (paginated) from ESPN. Returns flat row list."""
    players = []
    for page in range(1, pages + 1):
        params = {
            "region": "us", "lang": "en", "contentorigin": "espn",
            "category": "batting", "season": season, "seasontype": 2,
            "sort": "batting.homeRuns:desc", "limit": 50, "page": page,
        }
        r = requests.get(ESPN, params=params, headers=UA, timeout=60)
        r.raise_for_status()
        data = r.json()
        for a in data.get("athletes", []):
            ath = a.get("athlete", {})
            totals = None
            for cat in a.get("categories", []):
                if cat.get("name") == "batting":
                    totals = cat.get("totals", [])
                    break
            players.append({
                "espn_id": ath.get("id"),
                "name": ath.get("displayName"),
                "team": (ath.get("teams") or [{}])[0].get("displayName")
                        if ath.get("teams") else ath.get("teamName"),
                "position": ath.get("position", {}).get("abbreviation"),
                "totals": totals,
            })
    fname = f"espn_batting_{season}.json"
    with open(os.path.join(RAW_DIR, fname), "w") as f:
        json.dump(players, f)
    return players


def load_mlb_rows(season: int):
    conn = sqlite3.connect(os.path.join(REPO, "data", "mlb_lake.db"))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT player_id, name, team, stat_json FROM stat_lines "
        "WHERE season=? AND group_name='hitting'", (season,)
    ).fetchall()
    return [{"player_id": r["player_id"], "name": r["name"], "team": r["team"],
             "stat": json.loads(r["stat_json"])} for r in rows]


def _key(name, team):
    return (team or "", (name or "").split()[-1][:6].lower())


def decode_and_validate(season: int):
    espn = fetch_espn_batting(season)
    mlb = load_mlb_rows(season)
    mlb_map = {_key(m["name"], m["team"]): m for m in mlb}

    matches = []
    for p in espn:
        m = mlb_map.get(_key(p["name"], p["team"]))
        if m and p["totals"]:
            matches.append((p["totals"], m["stat"]))

    mlb_fields = [
        "gamesPlayed", "atBats", "runs", "hits", "avg", "doubles", "triples",
        "homeRuns", "rbi", "totalBases", "baseOnBalls", "strikeOuts", "stolenBases",
        "obp", "slg", "ops",
    ]
    labels = {}
    ncols = len(matches[0][0]) if matches else 0
    for idx in range(ncols):
        col = [float(m[0][idx]) for m in matches
               if idx < len(m[0]) and str(m[0][idx]) not in ("", "null")]
        if len(col) < 5:
            labels[idx] = None
            continue
        best, bestf = -1.0, None
        for f in mlb_fields:
            vals = [m[1].get(f) for m in matches]
            paired = [(c, v) for c, v in zip(col, vals)
                      if v is not None and not isna(v) and not isna(c)]
            if len(paired) < 5:
                continue
            cs = [x[0] for x in paired]
            vs = [float(x[1]) for x in paired]
            if len(set(cs)) > 1 and len(set(vs)) > 1:
                r = float(corrcoef(cs, vs)[0][1])
                if r > best:
                    best, bestf = r, f
        labels[idx] = bestf if best > 0.85 else None

    print(f"[{season}] decoded ESPN totals[{0}..{ncols-1}]:")
    print("   ", {i: f for i, f in labels.items()})

    report = []
    for t, s in matches:
        row = {"decoded_hr": None, "mlb_hr": None, "decoded_avg": None,
               "mlb_avg": None, "mismatch": []}
        hr_idx = next((i for i, f in labels.items() if f == "homeRuns"), None)
        avg_idx = next((i for i, f in labels.items() if f == "avg"), None)
        if hr_idx is not None:
            row["decoded_hr"] = t[hr_idx]
            row["mlb_hr"] = s.get("homeRuns")
            if row["decoded_hr"] is not None and row["mlb_hr"] is not None \
               and str(row["decoded_hr"]) != str(row["mlb_hr"]):
                row["mismatch"].append("HR")
        if avg_idx is not None:
            row["decoded_avg"] = t[avg_idx]
            row["mlb_avg"] = s.get("avg")
            if row["decoded_avg"] is not None and row["mlb_avg"] is not None \
               and abs(float(row["decoded_avg"]) - float(row["mlb_avg"])) > 0.0005:
                row["mismatch"].append("AVG")
        report.append(row)

    mm = [r for r in report if r["mismatch"]]
    out = os.path.join(REPO, "data", f"validation_{season}.json")
    obj = {"season": season, "players_compared": len(report), "mismatches": len(mm),
           "decoded_labels": labels, "players": report}
    with open(out, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[{season}] players compared: {len(report)}, mismatches: {len(mm)}")
    print(f"  wrote {out}")
    return obj


if __name__ == "__main__":
    for s in (2025, 2026):
        decode_and_validate(s)
