"""Measure: do winning-cheap teams ALSO have a distinct pitching signature?

Uses real 2025+2026 pitching stat-lines already in the lake. Key question:
do MIL/TB/CLE's results rest on contact-hitting ALONE, or do they also get
IP/ERA/K/BB/HR contributions that separate them from cheap-mediocre AND from
expensive teams? Turns GP's 'pitching depth is critical' into evidence.
"""
import json
import sqlite3

import pandas as pd

LAKE = "data/mlb_lake.db"
TEAM = {
    "New York Yankees": "NYY", "Houston Astros": "HOU", "New York Mets": "NYM",
    "Milwaukee Brewers": "MIL", "Tampa Bay Rays": "TB", "Arizona Diamondbacks": "AZ",
    "Detroit Tigers": "DET", "Los Angeles Dodgers": "LAD",
    "Cleveland Guardians": "CLE", "Miami Marlins": "MIA",
    "Chicago White Sox": "CHW", "St. Louis Cardinals": "STL",
    "Texas Rangers": "TEX", "Seattle Mariners": "SEA",
    "San Francisco Giants": "SF", "Boston Red Sox": "BOS",
    "Philadelphia Phillies": "PHI", "Atlanta Braves": "ATL",
    "San Diego Padres": "SD", "Toronto Blue Jays": "TOR",
    "Minnesota Twins": "MIN", "Baltimore Orioles": "BAL",
    "Los Angeles Angels": "LAA", "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN", "Colorado Rockies": "COL",
    "Kansas City Royals": "KC", "Pittsburgh Pirates": "PIT",
    "Washington Nationals": "WSH", "Oakland Athletics": "ATH",
}
WIN = {"MIL", "TB", "CLE"}
BAD = {"MIA", "CHW", "STL"}


def load():
    con = sqlite3.connect(LAKE)
    rows = []
    for season, pid, name, team, sjson in con.execute(
            "SELECT season,player_id,name,team,stat_json FROM stat_lines "
            "WHERE group_name='pitching'"):
        s = json.loads(sjson)
        rows.append({"season": season, "name": name, "team": team,
                     "IP": s.get("inningsPitched"), "ERA": s.get("era"),
                     "WHIP": s.get("whip"), "K": s.get("strikeOuts"),
                     "BB": s.get("walks"), "HR": s.get("homeRuns"),
                     "SO9": s.get("strikeoutsPer9Inn"), "BB9": s.get("walksPer9Inn")})
    con.close()
    df = pd.DataFrame(rows)
    for c in ["IP", "ERA", "WHIP", "K", "BB", "HR", "SO9", "BB9"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["IP"])
    df = df[df["IP"] >= 40]
    df["code"] = df["team"].map(TEAM)
    df["grp"] = "OTHER"
    df.loc[df["code"].isin(WIN), "grp"] = "WIN_CHEAP"
    df.loc[df["code"].isin(BAD), "grp"] = "CHEAP_MEDIOCRE"
    return df


def main():
    df = load()
    print(f"pitcher-seasons (IP>=40): {len(df)}, teams: {df['code'].nunique()}")
    for y in (2025, 2026):
        d = df[df["season"] == y].dropna(subset=["ER", "WHIP", "SO9", "BB9"] if False else ["ERA", "WHIP", "SO9", "BB9"])
        g = d.groupby("grp").apply(
            lambda x: pd.Series({
                "n": len(x),
                "IP": x["IP"].sum(),
                "ERA": (x["ERA"] * x["IP"]).sum() / x["IP"].sum(),
                "WHIP": (x["WHIP"] * x["IP"]).sum() / x["IP"].sum(),
                "K/9": (x["SO9"] * x["IP"]).sum() / x["IP"].sum(),
                "BB/9": (x["BB9"] * x["IP"]).sum() / x["IP"].sum(),
                "HR/CONTACT": (x["HR"].sum() * 9 / x["IP"].sum()),
            }), include_groups=False)
        print(f"\n=== {y} pitching (IP-weighted) ===")
        print(g.round(2).to_string())


if __name__ == "__main__":
    main()
