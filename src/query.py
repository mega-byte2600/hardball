#!/usr/bin/env python3
"""Run a named stakeholder query against the warehouse.

Usage: python3 src/query.py persistence|cap_gaps|fa_value|benchmark_parity
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) < 2:
        names = [p.stem for p in (ROOT / "queries").glob("*.sql")]
        print("usage: query.py <name>  — available:", ", ".join(sorted(names)))
        return 1
    sql_file = ROOT / "queries" / f"{sys.argv[1]}.sql"
    if not sql_file.exists():
        print(f"no such query: {sys.argv[1]}")
        return 1
    con = duckdb.connect(str(ROOT / "data" / "hardball.duckdb"), read_only=True)
    rel = con.sql(sql_file.read_text())
    print(rel.df().to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
