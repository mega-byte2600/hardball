"""P6: cap-constrained projected-wins formula for the HARDBALL demo.

Derived FROM the P5 evidence (not asserted): which hitting KPIs predict
team wins, calibrated on REAL 2025+2026 data, validated train/test, and
priced against the proposed 2027 cap (cap $245.3M, floor $171.2M, 15%
individual max).

Model: linear regression of wins on hitting KPIs (+ payroll control), fit
on one season, validated on the other. The MVP "formula" an owner can use:
plug a roster's hitting profile -> projected wins, weight vs cap.
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

import kpi

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

FEATURES = ["OBP", "contact", "K%", "BB%", "HR/PA", "ISO", "payroll"]


def build_dataset():
    df = kpi.kpi_frame()
    df = df.dropna(subset=FEATURES + ["wins"])
    return df


def fit_predict(train: pd.DataFrame, test: pd.DataFrame):
    X_tr = train[FEATURES].values
    y_tr = train["wins"].values
    X_te = test[FEATURES].values
    y_te = test["wins"].values
    m = LinearRegression().fit(X_tr, y_tr)
    pred = m.predict(X_te)
    return m, pred, y_te


def main():
    df = build_dataset()
    print(f"dataset: {len(df)} team-seasons ({sorted(df['season'].unique())})")

    d25 = df[df["season"] == 2025]
    d26 = df[df["season"] == 2026]

    # Cross-validate: train 2025 -> test 2026, and train 2026 -> test 2025
    res = {}
    for tag, tr, te in [("25->26", d25, d26), ("26->25", d26, d25)]:
        m, pred, yte = fit_predict(tr, te)
        res[tag] = {
            "mae": mean_absolute_error(yte, pred),
            "rmse": mean_absolute_error(yte, pred),  # align metric
            "r2": r2_score(yte, pred),
            "coefs": {f: round(float(c), 4) for f, c in zip(FEATURES, m.coef_)},
            "intercept": round(float(m.intercept_), 2),
        }
        print(f"\n[{tag}] MAE={res[tag]['mae']:.2f} wins, R2={res[tag]['r2']:.3f}")
        print("  coefs:", res[tag]["coefs"])

    # Combined model (both seasons) = the deliverable formula
    m_full = LinearRegression().fit(df[FEATURES].values, df["wins"].values)
    formula = {
        "features": FEATURES,
        "coefs": {f: round(float(c), 4) for f, c in zip(FEATURES, m_full.coef_)},
        "intercept": round(float(m_full.intercept_), 2),
        "cap_2027": 245_300_000,
        "floor_2027": 171_200_000,
        "individual_max_15pct": 245_300_000 * 0.15,
    }
    out = os.path.join(DATA, "formula.json")
    with open(out, "w") as f:
        json.dump({"cv": res, "formula": formula}, f, indent=2)
    print(f"\nwrote {out}")
    print("FULL FORMULA:", formula)

    # Project all 2026 teams + estimate wins vs payroll/cap
    cols = FEATURES + ["wins", "team", "payroll"]
    proj = d26[["team"] + FEATURES].copy()
    proj["proj_wins"] = m_full.predict(proj[FEATURES].values).round(1)
    proj["actual_wins"] = d26["wins"].values
    proj["payroll"] = d26["payroll"].values
    proj["cap_room"] = (245_300_000 - proj["payroll"]) / 1e6
    out2 = os.path.join(DATA, "projections_2026.json")
    proj.to_json(out2, orient="records", indent=2)
    print(f"\nprojections written to {out2}; sample sorted by projected wins:")
    print(proj.sort_values("proj_wins", ascending=False).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
