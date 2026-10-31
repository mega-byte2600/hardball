"""MLB data lake: connectors + SQLite store.

Sources (CarpeData):
- MLB Stats API: primary, classic stats.
- ESPN: validation/redundancy for classic stats.
- (Statcast advanced layer added separately in statcast_ingest.py)

Every pull is written to disk (raw JSON archive) so we never lose data
we already fetched — our own local backup, no third-party dependence.
"""
import json
import os
import sqlite3
import time
from datetime import date

import pandas as pd
import requests

BASE = "https://statsapi.mlb.com/api/v1"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"
UA = {"User-Agent": "nutweet-data-lake/1.0"}

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
DB_PATH = os.path.join(DATA_DIR, "mlb_lake.db")
os.makedirs(RAW_DIR, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    return conn


def _archive(source: str, key: str, obj) -> str:
    """Write raw JSON payload to disk (our own backup) and return path."""
    fname = f"{source}_{key}.json"
    path = os.path.join(RAW_DIR, fname)
    with open(path, "w") as f:
        json.dump(obj, f)
    return path


def init_schema():
    conn = _connect()
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT, first TEXT, last TEXT,
            position TEXT, team_id INTEGER, team_name TEXT
        );
        CREATE TABLE IF NOT EXISTS stat_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER, group_name TEXT, player_id INTEGER,
            team_id INTEGER, stat_json TEXT, source TEXT DEFAULT 'mlb',
            pulled_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def load_qualified(season: int, group: str, sort_stat: str, order: str = "desc",
                  source: str = "mlb") -> pd.DataFrame:
    """Pull qualified season leaders from MLB API. Returns DataFrame of stats + identity."""
    params = {
        "stats": "season", "group": group, "season": season,
        "sportId": 1, "playerPool": "qualified",
        "sortStat": sort_stat, "order": order, "limit": 300,
    }
    resp = requests.get(f"{BASE}/stats", params=params, headers=UA, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    _archive(source, f"{season}_{group}_{sort_stat}", data)

    rows = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        p = split.get("player", {})
        t = split.get("team", {})
        rows.append({
            "season": season,
            "group": group,
            "player_id": p.get("id"),
            "name": p.get("fullName"),
            "position": split.get("position", {}).get("abbreviation"),
            "team_id": t.get("id"),
            "team": t.get("name"),
            "stat_json": json.dumps(split.get("stat", {})),
        })
    df = pd.DataFrame(rows)

    # Persist
    conn = _connect()
    for _, r in df.iterrows():
        conn.execute(
            "INSERT INTO stat_lines (season, group_name, player_id, team_id, stat_json, source, pulled_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (r["season"], r["group"], r["player_id"], r["team_id"],
             r["stat_json"], source, str(date.today())),
        )
    conn.commit()
    conn.close()
    return df


def main():
    init_schema()
    for season in (2025, 2026):
        for group, sort in (("hitting", "homeRuns"), ("pitching", "strikeouts")):
            df = load_qualified(season, group, sort)
            print(f"{season} {group}: {len(df)} qualified players pulled")
    print(f"Lake: {DB_PATH}")


if __name__ == "__main__":
    main()
