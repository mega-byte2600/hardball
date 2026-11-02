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


# Seasons main() below actually reloads. Anything outside this set that
# is already in the lake would be destroyed by init_schema()'s DROPs and
# NOT reloaded — that is exactly how the Cycle 21 backfill (2022-2024,
# 1,026 player-seasons) was wiped from the lake before Cycle 39, leaving
# the committed persistence artifacts unreproducible from the lake as
# found (Cycle 39, PR #21). The guard below makes that failure
# unrepeatable: init_schema() refuses to drop a lake holding seasons
# outside RELOAD_SEASONS instead of silently destroying them.
RELOAD_SEASONS = (2025, 2026)


def init_schema():
    conn = _connect()
    c = conn.cursor()
    # Poka-yoke (Cycle 43): fail closed rather than wipe unreloadable
    # seasons. A missing stat_lines table (fresh lake) means nothing to
    # lose, so only an existing table with rows is inspected.
    try:
        seasons = {r[0] for r in c.execute("SELECT DISTINCT season FROM stat_lines")}
    except Exception:
        seasons = set()
    doomed = sorted(seasons - set(RELOAD_SEASONS))
    if doomed:
        conn.close()
        raise RuntimeError(
            "init_schema() REFUSED: lake holds seasons %s, which main() "
            "does not reload (it reloads only %s). Dropping stat_lines "
            "would destroy them, as happened to the 2022-2024 backfill "
            "before Cycle 39. Restore/extend the reload first, or back "
            "the lake up and clear it deliberately — do not run this "
            "against a backfilled lake." % (doomed, list(RELOAD_SEASONS))
        )
    c.executescript(
        """
        DROP TABLE IF EXISTS stat_lines;
        DROP TABLE IF EXISTS players;
        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT, first TEXT, last TEXT,
            position TEXT, team_id INTEGER, team_name TEXT
        );
        CREATE TABLE stat_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER, group_name TEXT, player_id INTEGER,
            name TEXT, team TEXT, team_id INTEGER,
            stat_json TEXT, source TEXT DEFAULT 'mlb',
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
            "INSERT INTO stat_lines (season, group_name, player_id, name, team, team_id, stat_json, source, pulled_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (r["season"], r["group"], r["player_id"], r["name"], r["team"],
             r["team_id"], r["stat_json"], source, str(date.today())),
        )
        # Upsert into players table too
        conn.execute(
            "INSERT OR REPLACE INTO players (player_id, full_name, team_id, team_name)"
            " VALUES (?,?,?,?)",
            (r["player_id"], r["name"], r["team_id"], r["team"]),
        )
    conn.commit()
    conn.close()
    return df


def main():
    init_schema()
    for season in RELOAD_SEASONS:
        for group, sort in (("hitting", "homeRuns"), ("pitching", "strikeouts")):
            df = load_qualified(season, group, sort)
            print(f"{season} {group}: {len(df)} qualified players pulled")
    print(f"Lake: {DB_PATH}")


if __name__ == "__main__":
    main()
