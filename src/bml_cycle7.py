"""BML Cycle 7: folds team pitching KPIs into the wins model.

Adds IP-weighted team pitching features (ERA, WHIP, BB/9, K/9, contact%) to
the hitting-KPI model and MEASURES whether CV MAE drops vs hitting-only.
Real: pitchers aggregated from lake pitching stat-lines, IP-weighted, joined
by team+season. Honest: reports the new number whether better or worse.
"""
import json
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_p6  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")

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


def team_pitching():
    con = sqlite3.connect(LAKE)
    rows = []
    for season, name, team, sjson in con.execute(
            "SELECT season,name,team,stat_json FROM stat_lines "
            "WHERE group_name='pitching'"):
        s = json.loads(sjson)
        rows.append({"season": season, "name": name, "team": team,
                     "IP": s.get("inningsPitched"), "ERA": s.get("era"),
                     "WHIP": s.get("whip"), "K": s.get("strikeOuts"),
                     "BB": s.get("walks"), "HR": s.get("homeRuns"),
                     "BF": s.get("battersFaced") or s.get("battersFaced")})
    con.close()
    df = pd.DataFrame(rows)
    for c in ["IP", "ERA", "WHIP", "K", "BB", "HR"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["IP", "ERA"])
    df = df[df["IP"] >= 30]
    # K/9, BB/9, HR/9 per pitcher
    df["K9"] = df["K"] * 9 / df["IP"]
    df["BB9"] = df["BB"] * 9 / df["IP"]
    df["HR9"] = df["HR"] * 9 / df["IP"]
    df["code"] = df["team"].map(TEAM)
    # IP-weighted team aggregates
    g = df.groupby(["season", "code"]).apply(
        lambda x: pd.Series({
            "p_ERA": (x["ERA"] * x["IP"]).sum() / x["IP"].sum(),
            "p_WHIP": (x["WHIP"] * x["IP"]).sum() / x["IP"].sum(),
            "p_K9": (x["K9"] * x["IP"]).sum() / x["IP"].sum(),
            "p_BB9": (x["BB9"] * x["IP"]).sum() / x["IP"].sum(),
            "p_HR9": (x["HR9"] * x["IP"]).sum() / x["IP"].sum(),
        }), include_groups=False).reset_index()
    g.columns = ["season", "team", "p_ERA", "p_WHIP", "p_K9", "p_BB9", "p_HR9"]
    return g


def main():
    pitch = team_pitching()
    print(f"team pitching rows: {len(pitch)}")
    base = model_p6.build_dataset().merge(pitch, on=["season", "team"], how="left")

    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error

    d25 = base[base["season"] == 2025]; d26 = base[base["season"] == 2026]
    PFEAT = ["p_ERA", "p_WHIP", "p_BB9", "p_K9", "p_HR9"]

    results = {
        "hitting-only (baseline)": model_p6.FEATURES,
        "hitting+pitching": model_p6.FEATURES + PFEAT,
        "pitching-only": PFEAT,
    }
    print("\nCV MAE (avg of 25->26 and 26->25):")
    for label, feats in results.items():
        maes = []
        for tr, te in [(d25, d26), (d26, d25)]:
            tr2 = tr.dropna(subset=feats + ["wins"]); te2 = te.dropna(subset=feats + ["wins"])
            if len(tr2) < 5 or len(te2) < 5:
                maes.append(float("nan")); continue
            m = LinearRegression().fit(tr2[feats].values, tr2["wins"].values)
            maes.append(mean_absolute_error(te2["wins"].values,
                                            m.predict(te2[feats].values)))
        ok = [x for x in maes if x == x]
        avg = sum(ok) / len(ok) if ok else float("nan")
        print(f"  {label:>24}: MAE = {avg:.2f} wins  ({[round(x,2) for x in maes]})")

    # combined model coefs on full data (the deliverable formula with pitching)
    m = LinearRegression().fit(base.dropna(subset=model_p6.FEATURES + PFEAT + ["wins"])
                               [model_p6.FEATURES + PFEAT].values,
                               base.dropna(subset=model_p6.FEATURES + PFEAT + ["wins"])["wins"].values)
    coefs = dict(zip(model_p6.FEATURES + PFEAT,
                     [round(c, 3) for c in m.coef_]))
    out = os.path.join(DATA, "formula_pitching.json")
    json.dump({"coefs": coefs, "intercept": round(float(m.intercept_), 2),
               "note": "combined hitting+pitching wins model"},
              open(out, "w"), indent=2)
    print(f"\ncombined coefs saved -> {out}")
    print("pitching coefs sign check (ERA lower=better, BB9 lower=better):")
    for k in ["p_ERA", "p_WHIP", "p_BB9", "p_HR9", "p_K9"]:
        print(f"  {k}: {coefs.get(k)}")


if __name__ == "__main__":
    main()
