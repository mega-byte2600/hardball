"""Build the SQLite read model needed by the dashboard from committed tables.

The full ingestion lake is intentionally not committed. Continuous integration
can reproduce the dashboard pitching panel from the committed
fact_stat_lines table without reaching out to a live service.
"""

import os
import sqlite3

import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SOURCE = os.path.join(DATA, "curated", "fact_stat_lines.parquet")
TARGET = os.path.join(DATA, "mlb_lake.db")


def main():
    frame = pd.read_parquet(SOURCE)
    required = {"season", "group_name", "stat_json", "team"}
    missing = required.difference(frame.columns)
    if missing:
        raise SystemExit(f"missing columns: {sorted(missing)}")
    with sqlite3.connect(TARGET) as connection:
        frame[["season", "team", "group_name", "stat_json"]].to_sql(
            "stat_lines", connection, if_exists="replace", index=False
        )
    print(f"built {TARGET} with {len(frame)} stat-line rows")


if __name__ == "__main__":
    main()
