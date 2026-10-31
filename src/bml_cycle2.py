"""BML Cycle 2: does team health (injury proxy) improve the wins model?

Pulls all player transactions for 2025+2026 from MLB Stats API, builds a
per-team, per-season health proxy from IL placements + rehab assignments,
joins it to the hitting model, and MEASURES whether adding health lowers
cross-validated MAE vs hitting-only.
"""
import json
import os
import sys
from collections import defaultdict

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_p6  # noqa

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0"}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw")

# full team name -> 3-letter code (as in payroll)
TEAM_NAME_CODE = {
    "Arizona Diamondbacks": "AZ", "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL", "Detroit Tigers": "DET",
    "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "ATH",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH",
}


def team_code(desc, to_team):
    if to_team and isinstance(to_team, dict) and to_team.get("abbreviation"):
        return to_team["abbreviation"]
    if desc:
        first = desc.split(" ")[0].upper()
        if first in TEAM_NAME_CODE.values():
            return first
        for name, code in TEAM_NAME_CODE.items():
            if desc.startswith(name):
                return code
    return None


def pull_transactions(season):
    all_tx = []
    for month in range(1, 13):
        start = f"{season}-{month:02d}-01"
        endmonth = month + 1
        endy, endm = (season, endmonth) if endmonth <= 12 else (season + 1, 1)
        end = f"{endy}-{endm:02d}-01"
        try:
            r = requests.get(f"{BASE}/transactions",
                             params={"sportId": 1, "startDate": start, "endDate": end},
                             headers=UA, timeout=90)
            r.raise_for_status()
            all_tx += r.json().get("transactions", [])
        except Exception as e:
            print(f"  fail {season}-{month}: {e}")
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, f"transactions_{season}.json")
    with open(path, "w") as f:
        json.dump(all_tx, f)
    return all_tx


def build_health_df():
    rows = []
    for season in (2025, 2026):
        path = os.path.join(RAW, f"transactions_{season}.json")
        tx = json.load(open(path)) if os.path.exists(path) else pull_transactions(season)
        proxy = defaultdict(lambda: {"il": 0, "rehab": 0})
        for t in tx:
            desc = t.get("description") or ""
            code = team_code(desc, t.get("toTeam"))
            if not code:
                continue
            low = desc.lower()
            # il placement vs activation
            if ("placed" in low or "placed on" in low) and "il" in low:
                proxy[code]["il"] += 1
            elif "injured list" in low:
                proxy[code]["il"] += 1
            elif "rehab" in low:
                proxy[code]["rehab"] += 1
        for code, p in proxy.items():
            rows.append({"season": season, "team": code,
                         "il_count": p["il"], "rehab_count": p["rehab"]})
    return pd.DataFrame(rows)


def main():
    df = build_health_df()
    print(f"health rows: {len(df)}, teams/season: "
          f"{df.groupby('season')['team'].nunique().to_dict()}")
    print(df.groupby("season").agg(il=("il_count", "sum"),
                                   rehab=("rehab_count", "sum")).to_string())

    base = model_p6.build_dataset().merge(df, on=["season", "team"], how="left").fillna(0)
    base["health"] = base["il_count"] + base["rehab_count"]

    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error

    d25 = base[base["season"] == 2025]
    d26 = base[base["season"] == 2026]

    for label, feats in [
        ("hitting-only", model_p6.FEATURES),
        ("hitting+health", model_p6.FEATURES + ["health"]),
    ]:
        maes = []
        for tr, te in [(d25, d26), (d26, d25)]:
            m = LinearRegression().fit(tr[feats].values, tr["wins"].values)
            maes.append(mean_absolute_error(te["wins"].values, m.predict(te[feats].values)))
        avg = sum(maes) / 2
        print(f"{label:>16}: CV MAE = {avg:.2f} wins  ({[round(x, 2) for x in maes]})")

    # save health frame for the dashboard layer
    out = os.path.join(DATA, "health_2025_2026.json")
    df.to_json(out, orient="records", indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
