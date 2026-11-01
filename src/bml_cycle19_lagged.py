"""Cycle 19: LAGGED forecast model — the honest, use-case-correct spec.

Owner need for 2027: given a team's CURRENT profile, predict NEXT season's
wins. That is a LAGGED prediction: wins[t+1] ~ KPIs[t]. This also fixes the
collinearity flaw (predicting next year's wins from this year's KPIs avoids
the same-year RD-KPI double count).

Built and validated on the 450-row panel:
  - each team-year feature vector t predicts season t+1 win total
  - out-of-sample grouped CV (predict held-out SEASONS, never seen in train)
  - honest report: does a lagged KPI-only model beat the naive baseline?
  - the winning-cheap thesis re-tested properly: are contact/OBP
    positively predictive of NEXT year's wins across 16 years?
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

FEATS = ["OBP", "contact", "K%", "BB%", "HR/PA", "payroll"]


def load_lagged():
    df = pd.read_csv(os.path.join(DATA, "panel_2011_2026.csv"))
    df = df.sort_values(["team", "season"]).reset_index(drop=True)
    # Build t+1 wins for each team
    df["next_wins"] = df.groupby("team")["wins"].shift(-1)  # wins NEXT season
    # target: next season's run differential / wins
    df["next_wins_"] = df["next_wins"]
    # drop last season per team (no future) and rows w/o full features
    for c in FEATS + ["wins", "next_wins"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    use = df.dropna(subset=FEATS + ["next_wins"]).copy()
    return use


def main():
    df = load_lagged()
    n_rows, n_years = len(df), df["season"].nunique()
    X, y = df[FEATS].values, df["next_wins"].values
    print(f"LAGGED PANEL: {n_rows} team-yrs (predict next season), "
          f"seasons {df['season'].min()}-{df['season'].max()}")

    # --- A) Full-fit coefficients (the honest thesis test) ---
    for name, mdl in [("LinearRegression", LinearRegression()),
                      ("Ridge", Ridge(alpha=1.0))]:
        m = mdl.fit(X, y)
        print(f"\n[{name}] coefficients for predicting NEXT year's wins:")
        for f, c in zip(FEATS, m.coef_):
            print(f"    {f:>8}: {c:+.4f}")
        print(f"    in-sample R2: {r2_score(y, m.predict(X)):.3f}")

    # --- B) OUT-OF-SAMPLE: train on seasons <=2019, test on 2020-2025 ---
    #      (predict future from past = the real use-case, no leakage)
    tr = (df["season"] <= 2019).values
    te = (df["season"] >= 2020).values
    m = Ridge(alpha=1.0).fit(X[tr], y[tr])
    yp = m.predict(X[te])
    mae = mean_absolute_error(y[te], yp); r2 = r2_score(y[te], yp)
    naive = mean_absolute_error(y[te], np.full_like(y[te], y[te].mean()))
    print(f"\n[OUT-OF-SAMPLE: train<=2019, test 2020-2025]")
    print(f"    Ridge MAE {mae:.2f}  R2 {r2:.3f}  (n_test={int(te.sum())})")
    print(f"    naive (mean) MAE {naive:.2f}  -> we beat by {naive-mae:.2f}")

    # --- C) grouped CV: hold out WHOLE seasons at a time ---
    #      the gold standard for forecasting — no same-year contamination
    #      G6 (root-caused 2026-10-31): the fold keyed "2019" predicts the
    #      60-GAME 2020 season (actual win totals 22-43) with a model
    #      trained on 162-game seasons — its MAE 51.9 is a units mismatch,
    #      not model error, and it inflated the grouped-CV mean (13.0 vs
    #      ~10.2 without it). Folds whose TARGET season is 2020 are
    #      excluded from the headline mean and reported separately.
    years = sorted(df["season"].unique())
    maes, r2s = [], []
    tested_years = []
    excluded_folds = []
    for y_test in years[1:]:  # need prior year to exist
        trm = (df["season"] < y_test).values
        tem = (df["season"] == y_test).values
        if trm.sum() < 10 or tem.sum() < 10:
            continue
        mm = Ridge(alpha=1.0).fit(X[trm], y[trm])
        ypp = mm.predict(X[tem])
        fold_mae = mean_absolute_error(y[tem], ypp)
        if y_test + 1 == 2020:
            excluded_folds.append({"feature_season": int(y_test),
                                   "target_season": 2020,
                                   "mae": round(float(fold_mae), 1),
                                   "reason": "target season is the 60-game "
                                             "2020 season; win totals are "
                                             "not comparable to 162-game "
                                             "seasons (units mismatch)"})
            continue
        maes.append(fold_mae)
        r2s.append(r2_score(y[tem], ypp))
        tested_years.append(y_test)
    print("\n[GROUPED CV — train on all prior years, test each future year]")
    print(f"    MAE {np.mean(maes):.2f} ±{2*np.std(maes):.2f}  "
          f"R2 {np.mean(r2s):.3f} ±{2*np.std(r2s):.3f}")
    naive_all = mean_absolute_error(y, np.full_like(y, y.mean()))
    print(f"    naive baseline(all): {naive_all:.2f}")
    # Year-by-year detail
    print("    per-test-year (year: MAE):",
          ", ".join(f"{yr}:{e:.1f}" for yr, e in zip(tested_years, maes)))

    out = {"n_rows": int(n_rows), "features": FEATS,
           "oos_2020_2025": {"mae": round(float(mae), 2), "r2": round(float(r2), 3),
                             "beats_naive_by": round(float(naive - mae), 2)},
           "grouped_cv": {"mae_mean": round(float(np.mean(maes)), 2),
                          "r2_mean": round(float(np.mean(r2s)), 3)},
           "full_fit_in_sample_r2": round(float(r2_score(y, Ridge(alpha=1.0).fit(X, y).predict(X))), 3),
           "per_year": dict(zip([str(yr) for yr in tested_years],
                                [round(float(e), 1) for e in maes])),
           "excluded_folds": excluded_folds,
           "g6_root_cause": "The 2019 fold's target is the 60-game 2020 "
                            "season; its MAE 51.9 was a units mismatch, "
                            "not a model failure. Excluded from grouped_cv."}
    with open(os.path.join(DATA, "lagged_forecast.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote data/lagged_forecast.json")


if __name__ == "__main__":
    main()
