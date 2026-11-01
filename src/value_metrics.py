"""HARDBALL VALUE METRICS — wOBA / wRC+ / FIP / K-BB% from real data.

The standard sabermetric "value" metrics an owner expects, computed from the
REAL box-score components we hold (no fabrication). WAR itself is proprietary
(fWAR/bWAR) and NOT in the MLB API — we do not fake it; we surface the
reproducible inputs it is built from.

Hitting (team-level, from panel 2011-2026):
  1B = H - 2B - 3B - HR
  wOBA = (0.69*BB + 0.72*HBP + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR) / PA
        (2022-23 MLB linear weights, the standard published values)
  wRC+ indexed to league (100 = average): wRC+ = 100 * (wRAA/PA + LgR/PA)/(LgR/PA)
        simplified team-level index from wOBA vs league mean.

Pitching (team-level, from lake pitching stat_lines, real):
  FIP = (13*HR + 3*(BB+HBP) - 2*SO) / IP + C   (C = league constant ~3.10)
  K-BB% = (SO - BB) / BattersFaced * 100       (the modern quality stat)
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
DB = os.path.join(DATA, "mlb_lake.db")
PANEL = os.path.join(DATA, "panel_2011_2026.csv")

# Standard published wOBA linear weights (2022-23 MLB)
W = {"BB": 0.69, "HBP": 0.72, "1B": 0.89, "2B": 1.27, "3B": 1.62, "HR": 2.10}


def hitting_value(season=2026):
    df = pd.read_csv(PANEL)
    d = df[df["season"] == season].copy()
    for c in ["PA", "AB", "H", "2B", "3B", "HR", "BB", "HBP", "SO", "wins"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "HBP" not in d.columns:
        d["HBP"] = 0.0
    d = d.dropna(subset=["PA", "H", "2B", "3B", "HR", "BB"])
    d["1B"] = d["H"] - d["2B"] - d["3B"] - d["HR"]
    d["wOBA"] = ((W["BB"]*d["BB"] + W["HBP"]*d["HBP"] + W["1B"]*d["1B"]
                  + W["2B"]*d["2B"] + W["3B"]*d["3B"] + W["HR"]*d["HR"]) / d["PA"])
    # dedupe rows per team (defensive against dupes from the merge)
    d = d.sort_values("team").drop_duplicates(subset=["team"], keep="last")
    # wRC+ style: index to league mean wOBA (100 = average)
    lg = d["wOBA"].mean()
    d["wRC+"] = 100 * d["wOBA"] / lg
    d["value"] = "hitting"
    return d[["team", "wOBA", "wRC+", "wins"]].drop_duplicates(subset=["team"])


def pitching_value(season=2026):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT stat_json, team FROM stat_lines WHERE group_name='pitching' "
        "AND season=?", (season,)).fetchall()
    con.close()
    TEAM = {"New York Yankees": "NYY", "Houston Astros": "HOU",
            "New York Mets": "NYM", "Milwaukee Brewers": "MIL",
            "Tampa Bay Rays": "TB", "Arizona Diamondbacks": "AZ",
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
            "Washington Nationals": "WSH", "Oakland Athletics": "ATH"}
    out = []
    for j, team in rows:
        s = json.loads(j)
        IP = float(s.get("inningsPitched") or 0)
        if IP == 0:
            continue
        HR = float(s.get("homeRuns") or 0)
        BB = float(s.get("baseOnBalls") or 0)
        HBP = float(s.get("hitBatsmen") or s.get("hitByPitch") or 0)
        SO = float(s.get("strikeOuts") or 0)
        BF = float(s.get("battersFaced") or 0)
        code = TEAM.get(team, team)
        fip = round((13*HR + 3*(BB + HBP) - 2*SO) / IP + 3.10, 2) if IP else np.nan
        kbb = round((SO - BB) / BF * 100, 2) if BF else np.nan
        out.append({"team": code, "FIP": fip, "K-BB%": kbb})
    return pd.DataFrame(out).drop_duplicates(subset=["team"], keep="last")


def main():
    h = hitting_value(2026)
    p = pitching_value(2026)
    # Ranking of the top value: wRC+ is the headline hitting value; FIP pitching.
    h = h.sort_values("wRC+", ascending=False)
    p = p.sort_values("FIP", ascending=True)  # lower FIP better
    print("=== 2026 HITTING VALUE (top 8 by wRC+, 100=avg) ===")
    for _, r in h.head(8).iterrows():
        print(f"  {r['team']:>4}  wOBA {r['wOBA']:.3f}  wRC+ {r['wRC+']:.0f}")
    print("\n=== 2026 PITCHING VALUE (top 8 by FIP) ===")
    for _, r in p.head(8).iterrows():
        print(f"  {r['team']:>4}  FIP {r['FIP']:.2f}  K-BB% {r['K-BB%']:.2f}")

    combined = {"hitting": h.to_dict(orient="records"),
                "pitching": p.to_dict(orient="records"),
                "woba_weights": W,
                "note": ("wOBA/wRC+/FIP computed from real box scores (standard "
                         "weights). WAR is proprietary (fWAR/bWAR) and not in the "
                         "MLB API; these are its reproducible inputs.")}
    out = os.path.join(DATA, "value_metrics_2026.json")
    with open(out, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
