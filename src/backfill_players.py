"""Backfill player hitting stat_lines into the lake for 2022-2024.

The persistence edge (contact r=0.90) currently rests on 80 players with
2025+2026. Backfilling earlier seasons turns it into a multi-year, 200+
player sample: many more season-pairs, and the claim survives contact with
more data. Uses the MLB Stats API (keyless, real). Archives raw to
data/raw/player_YYYY.json so it's never re-fetched.
"""
import json
import os
import sqlite3
import time

import requests

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0"}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
DB = os.path.join(DATA, "mlb_lake.db")
RAW = os.path.join(DATA, "raw")
SEASONS = [2024, 2023, 2022]
SLEEP = 0.15

TEAM = {"NYY", "HOU", "NYM", "MIL", "TB", "AZ", "DET", "LAD", "CLE", "MIA",
        "CHW", "STL", "TEX", "SEA", "SF", "BOS", "PHI", "ATL", "SD", "TOR",
        "MIN", "BAL", "LAA", "CHC", "CIN", "COL", "KC", "PIT", "WSH", "ATH"}


def team_code_map(season):
    r = requests.get(f"{BASE}/teams", params={"sportId": 1, "season": season},
                     headers=UA, timeout=60)
    m = {}
    for t in r.json().get("teams", []):
        ab = t.get("abbreviation")
        name = t.get("name")
        m[ab] = name
    m["CLE"] = "Cleveland Guardians"; m["CHW"] = "Chicago White Sox"
    m["ATH"] = "Athletics"
    return m


def fetch_qualified_hitters(season):
    """All qualified-adjacent hitters: league hitting leaders by PA desc."""
    path = os.path.join(RAW, f"player_hitting_{season}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # MLB API league leaders endpoint — pulls every regular with a season line
    rows = []
    resp = requests.get(f"{BASE}/stats/leaders",
                        params={"leaderCategories": "homeRuns,baseOnBalls,strikeOuts",
                                "season": season, "sportId": 1, "limit": 1000,
                                "stats": "season"}, headers=UA, timeout=90)
    resp.raise_for_status()
    for rec in resp.json().get("leagueLeaders", []):
        for r in rec.get("leaders", []):
            pid = r.get("person", {}).get("id")
            name = r.get("person", {}).get("fullName")
            if pid:
                rows.append({"player_id": pid, "name": name})
    # dedupe
    seen = {}
    for r in rows:
        seen[r["player_id"]] = r["name"]
    with open(path, "w") as f:
        json.dump(seen, f, indent=2)
    time.sleep(SLEEP)
    return seen


def fetch_player_season(pid, season):
    """Per-player season hitting stat_json from the API (or cache)."""
    path = os.path.join(RAW, f"player_{pid}_{season}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    r = requests.get(f"{BASE}/people/{pid}/stats",
                     params={"stats": "season", "group": "hitting",
                             "season": season, "sportId": 1}, headers=UA, timeout=60)
    try:
        stats_list = r.json().get("stats") or []
        splits = stats_list[0].get("splits", []) if stats_list else []
    except (IndexError, TypeError, ValueError):
        splits = []
    data = splits[0].get("stat", {}) if splits else {}
    with open(path, "w") as f:
        json.dump(data, f)
    time.sleep(SLEEP)
    return data


def main():
    con = sqlite3.connect(DB)
    total = 0
    for season in SEASONS:
        players = fetch_qualified_hitters(season)
        n = 0
        for pid, name in players.items():
            s = fetch_player_season(pid, season)
            # keep rows with real PA
            if not s or not s.get("plateAppearances"):
                continue
            con.execute(
                "INSERT OR REPLACE INTO stat_lines "
                "(season, group_name, player_id, name, team, stat_json, source, pulled_at) "
                "VALUES (?, 'hitting', ?, ?, ?, ?, 'mlb-api', datetime('now'))",
                (season, pid, name, "", json.dumps(s)))
            n += 1
        con.commit()
        total += n
        print(f"  {season}: {n} hitter rows stored (cache kept in raw/)")
    con.close()
    print(f"TOTAL stored: {total}")
    # verify lake now has multi-year coverage
    con = sqlite3.connect(DB)
    for season in [2022, 2023, 2024, 2025, 2026]:
        c = con.execute("SELECT COUNT(DISTINCT player_id) FROM stat_lines "
                        "WHERE season=? AND group_name='hitting'", (season,)).fetchone()[0]
        print(f"  hitting players {season}: {c}")
    # how many now have >=3 seasons (real multi-year sample)
    q = """SELECT COUNT(*) FROM (SELECT player_id FROM stat_lines
          WHERE group_name='hitting' GROUP BY player_id
          HAVING COUNT(DISTINCT season)>=3)"""
    print("players with >=3 hitting seasons:", con.execute(q).fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
