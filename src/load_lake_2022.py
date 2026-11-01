"""Load cached raw player season-lines (2022) into the lake.

The backfill fetched 2022 raw but appeared to end before the lake upsert.
This idempotent loader reads any player_hitting_<season>.json leaders list
plus per-player cached files and upserts them, so Cycle 21 can use 4 pairs.
"""
import json
import os
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "raw")
DB = os.path.join(REPO, "data", "mlb_lake.db")

SEASONS = [2022]  # 2023/2024 already in lake


def load_season(season):
    # player ids to load: from cache file names + leaders list
    leader = os.path.join(RAW, f"player_hitting_{season}.json")
    ids = set()
    if os.path.exists(leader):
        for rec in json.load(open(leader)) or []:
            pid = rec.get("person") or rec.get("player_id")
            if pid:
                ids.add(pid)
    # also any cached per-player files
    import glob
    for f in glob.glob(os.path.join(RAW, f"player_*_{season}.json")):
        base = os.path.basename(f)
        if base == f"player_hitting_{season}.json":
            continue
        # player_<id>_<season>.json
        try:
            pid = int(base.split("_")[1])
            ids.add(pid)
        except Exception:
            pass

    con = sqlite3.connect(DB)
    n = 0
    for pid in sorted(ids):
        p = os.path.join(RAW, f"player_{pid}_{season}.json")
        if not os.path.exists(p):
            continue
        try:
            stat = json.load(open(p))
        except Exception:
            continue
        if not stat:
            continue
        name = stat.get("person", {}).get("fullName", "") if isinstance(stat.get("person"), dict) else ""
        con.execute(
            "INSERT OR REPLACE INTO stat_lines "
            "(season, player_id, name, group_name, stat_json) VALUES (?,?,?,?,?)",
            (season, int(pid), name, "hitting", json.dumps(stat)))
        n += 1
    con.commit()
    con.close()
    print(f"season {season}: loaded {n} hitters into lake")


if __name__ == "__main__":
    for s in SEASONS:
        load_season(s)
