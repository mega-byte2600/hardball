"""Payroll analysis: 30-team efficiency (wins per dollar).

Loads 2011-2025 payroll (Spotrac CSV from jasonbhorne/mlb-payroll) plus
2026 payroll (Spotrac live), joins wins, computes cost-per-win and an
efficiency score, and frames the small-market-vs-big-spender problem.
Real data only. Payroll archives are gitignored (regenerable external data).
"""
import json
import os
import re
import sqlite3

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
PAY = os.path.join(DATA, "payroll")

# 2026 payroll from Spotrac live table (30 teams, total payroll allocations)
# {team_code: (team_name, record, R, RA, payroll)}
PAYROLL_2026 = {
    "NYM": ("New York Mets", "74-88", "$346,736,805"),
    "LAD": ("Los Angeles Dodgers", "100-62", "$339,319,244"),
    "NYY": ("New York Yankees", "93-68", "$308,336,780"),
    "PHI": ("Philadelphia Phillies", "88-74", "$291,951,676"),
    "TOR": ("Toronto Blue Jays", "79-83", "$276,130,679"),
    "ATL": ("Atlanta Braves", "94-68", "$263,462,438"),
    "CHC": ("Chicago Cubs", "89-73", "$249,319,956"),
    "HOU": ("Houston Astros", "81-81", "$239,763,783"),
    "SD": ("San Diego Padres", "91-71", "$218,252,715"),
    "BOS": ("Boston Red Sox", "87-75", "$207,988,016"),
    "DET": ("Detroit Tigers", "76-86", "$202,081,991"),
    "ARI": ("Arizona Diamondbacks", "86-76", "$192,670,027"),
    "TEX": ("Texas Rangers", "80-82", "$191,262,798"),
    "SF": ("San Francisco Giants", "65-97", "$190,174,131"),
    "LAA": ("Los Angeles Angels", "62-100", "$182,509,023"),
    "SEA": ("Seattle Mariners", "76-86", "$170,071,014"),
    "BAL": ("Baltimore Orioles", "79-82", "$167,039,211"),
    "KC": ("Kansas City Royals", "69-93", "$150,429,892"),
    "MIL": ("Milwaukee Brewers", "103-59", "$146,706,320"),
    "CIN": ("Cincinnati Reds", "75-87", "$128,223,748"),
    "COL": ("Colorado Rockies", "58-104", "$121,526,751"),
    "MIN": ("Minnesota Twins", "77-85", "$115,748,036"),
    "PIT": ("Pittsburgh Pirates", "82-80", "$106,728,501"),
    "CHW": ("Chicago White Sox", "84-78", "$103,330,141"),
    "WSH": ("Washington Nationals", "77-85", "$101,639,888"),
    "ATH": ("Athletics", "64-98", "$98,948,812"),
    "STL": ("St. Louis Cardinals", "77-85", "$96,396,498"),
    "TB": ("Tampa Bay Rays", "98-64", "$95,615,469"),
    "MIA": ("Miami Marlins", "80-82", "$83,298,123"),
    "CLE": ("Cleveland Guardians", "85-77", "$74,459,014"),
}


def _dollars(s):
    return int(s.replace("$", "").replace(",", ""))


def _wins(rec):
    return int(rec.split("-")[0])


def load_payroll_frame():
    """Concatenate 2011-2025 CSVs + 2026 dict into one tidy frame."""
    frames = []
    for fname in ("payroll_2011_2018.csv", "payroll_2019_2025.csv"):
        p = os.path.join(PAY, fname)
        if os.path.exists(p):
            frames.append(pd.read_csv(p, encoding="utf-8-sig"))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    rows = []
    for code, (name, rec, pay) in PAYROLL_2026.items():
        wins = _wins(rec)
        rows.append({
            "season": 2026, "team": code, "record": rec, "wins": wins,
            "avg_age": None, "payroll": _dollars(pay),
        })
    df26 = pd.DataFrame(rows)
    # normalize wins (some historical rows may lack wins, e.g. '-' in record)
    if "wins" not in df.columns:
        df["wins"] = pd.to_numeric(
            df["record"].astype(str).str.split("-").str[0], errors="coerce"
        )
    df = pd.concat([df, df26], ignore_index=True)
    df["payroll"] = pd.to_numeric(df["payroll"])
    df["wins"] = pd.to_numeric(df["wins"])
    return df


def build_efficiency_table(df, season=2026):
    """Cost per win and efficiency score for the given season."""
    cur = df[df["season"] == season].copy()
    cur = cur[cur["wins"] > 0]
    cur["cost_per_win"] = cur["payroll"] / cur["wins"]
    # Efficiency: wins per $100M
    cur["wins_per_100m"] = cur["wins"] / (cur["payroll"] / 100_000_000)
    cur = cur.sort_values("wins_per_100m", ascending=False)
    return cur


def main():
    df = load_payroll_frame()
    print(f"payroll rows loaded: {len(df)} (seasons {df['season'].min()}-{df['season'].max()})")
    t = build_efficiency_table(df, 2026)
    print(f"\n=== 2026 efficiency (wins per $100M) top 10 ===")
    cols = ["team", "record", "payroll", "wins", "cost_per_win", "wins_per_100m"]
    print(t[cols].head(10).to_string(index=False))
    print(f"\n=== bottom 5 (worst efficiency) ===")
    print(t[cols].tail(5).to_string(index=False))

    # Archive the 2026 efficiency table
    out = os.path.join(DATA, "efficiency_2026.json")
    t[cols].to_json(out, orient="records", indent=2)
    print(f"\nwrote {out}")
    return df, t


if __name__ == "__main__":
    main()
