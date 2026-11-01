"""P6: cap-constrained projected-wins formula for the HARDBALL demo.

Derived FROM the P5 evidence (not asserted): which hitting KPIs predict
team wins, calibrated on REAL 2025+2026 data, validated train/test, and
priced against the proposed 2027 cap (cap $245.3M, floor $171.2M, 15%
individual max).

Model: linear regression of wins on hitting KPIs (+ payroll control), fit
on one season, validated on the other. The MVP "formula" an owner can use:
plug a roster's hitting profile -> projected wins, weight vs cap.

Reproducibility (audit G3, 2026-10-31): the default dataset is the
committed KPI snapshots (data/kpi_2025.json + data/kpi_2026.json), not a
live API fetch — same input, same formula, every run, offline. Refresh
the snapshots with src/kpi.py, or fit live with `python src/model_p6.py
--live`. Dependencies are pinned in requirements.txt.

Feature notes:
- "contact" is NOT a feature — it is exactly 100 − K% (contact =
  (PA−SO)/PA·100), so including both made the design matrix singular
  and the coefficient split between them arbitrary across environments
  (the original committed fit had K% −1.13 / contact +1.13, a cancelling
  pair). No information is lost by dropping it; contact% remains a
  display KPI in the dashboard and the P5 analysis.
- Payroll enters as payroll_m (dollars in millions). With raw dollars
  (~1e8) beside OBP (~0.3), the least-squares solver's rank cutoff
  silently zeroed every hitting coefficient in newer scipy versions —
  the audit's rerun produced an all-zero formula (intercept + payroll
  only, in-sample R² 0.16) where the author's environment produced the
  real fit. Scaled, the fit is stable: in-sample R² 0.57, cross-year
  MAE ≈ 6.9–7.1. This was the actual G3 reproducibility root cause.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import kpi

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

FEATURES = ["OBP", "K%", "BB%", "HR/PA", "ISO", "payroll_m"]


def build_dataset(live: bool = False):
    df = kpi.kpi_frame() if live else kpi.kpi_frame_from_snapshots()
    df = df.copy()
    df["payroll_m"] = df["payroll"] / 1e6  # $M — see scaling note above
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
    live = "--live" in sys.argv
    df = build_dataset(live=live)
    print(f"dataset: {len(df)} team-seasons ({sorted(df['season'].unique())})"
          f" source={'live MLB API' if live else 'committed KPI snapshots'}")

    d25 = df[df["season"] == 2025]
    d26 = df[df["season"] == 2026]

    # Cross-validate: train 2025 -> test 2026, and train 2026 -> test 2025
    res = {}
    for tag, tr, te in [("25->26", d25, d26), ("26->25", d26, d25)]:
        m, pred, yte = fit_predict(tr, te)
        res[tag] = {
            "mae": mean_absolute_error(yte, pred),
            "rmse": float(np.sqrt(mean_squared_error(yte, pred))),
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
        json.dump({
            "dataset": {
                "source": "live MLB API via kpi.kpi_frame()" if live else
                          "committed snapshots data/kpi_2025.json + data/kpi_2026.json",
                "n_team_seasons": int(len(df)),
                "seasons": [int(s) for s in sorted(df["season"].unique())],
            },
            "cv": res, "formula": formula}, f, indent=2)
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
