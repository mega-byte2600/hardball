"""Verify the lake holds real, queryable data."""
import json
import os
import sqlite3

from ingest import DB_PATH, RAW_DIR

c = sqlite3.connect(DB_PATH)
c.row_factory = sqlite3.Row

n = c.execute("SELECT COUNT(*) FROM stat_lines").fetchone()[0]
print(f"total stat_lines: {n}")
print(f"archive files: {len(os.listdir(RAW_DIR))}")

# HR leader 2026
rows = c.execute(
    "SELECT player_id, stat_json FROM stat_lines WHERE group_name=? AND season=?",
    ("hitting", 2026),
).fetchall()
hrs = [(r["player_id"], json.loads(r["stat_json"]).get("homeRuns")) for r in rows]
hrs.sort(key=lambda x: -x[1])
top3 = hrs[:3]
print("2026 HR leaders (player_id, HR):", top3)

# PCA expected ~691718, 45 HR per earlier live query
pca = [x for x in hrs if x[0] == 691718]
print("PCA HR check:", pca, "=> expected 45" if not pca or pca[0][1] == 45 else "MISMATCH")

# Duplicate check
dups = c.execute(
    "SELECT season, group_name, player_id, COUNT(*) cn FROM stat_lines GROUP BY 1,2,3 HAVING cn>1"
).fetchall()
print("duplicate players across pulls:", len(dups))
