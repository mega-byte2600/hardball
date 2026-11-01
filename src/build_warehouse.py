#!/usr/bin/env python3
"""Build the analytical warehouse: DuckDB over curated Parquet.

data/hardball.duckdb is a BUILD ARTIFACT (gitignored, like the lake):
rebuild any time with `python3 src/build_warehouse.py`. Every curated
table lands as a same-named DuckDB table; stakeholder queries live in
queries/*.sql and run via src/query.py.
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CUR = ROOT / "data" / "curated"
DB = ROOT / "data" / "hardball.duckdb"


def main():
    if not CUR.exists():
        print("no curated layer — run src/curate.py first")
        return 1
    con = duckdb.connect(str(DB))
    tables = sorted(p.stem for p in CUR.glob("*.parquet"))
    for t in tables:
        con.execute(f"CREATE OR REPLACE TABLE {t} AS "
                    f"SELECT * FROM read_parquet('{CUR / (t + '.parquet')}')")
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} rows")
    con.close()
    print(f"WAREHOUSE: {DB.name} built from {len(tables)} curated tables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
