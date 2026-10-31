"""BML Cycle 17: deep-frameworks-vs-linear EMPIRICAL comparison.

Answers the 'why no tensorflow/LGBM/MLP?' question with DATA, not assertion.
Fits several model families on the SAME 2025+2026 team data under repeated
K-fold and compares held-out error:

   1. LinearRegression (current production)        - sklearn
   2. RandomForest (shallow, calibrated)           - sklearn
   3. GradientBoosting (shallow)                   - sklearn
   4. Ridge with polynomial features               - sklearn
   5. Small MLP (neural net, 1 hidden layer)       - sklearn MLPRegressor

If the literature+our-data claim holds, linear should match or beat the
fancier families at this sample size (n=58, 9 features). The result is the
evidence line for the owner deck. Everything on the same real data.
"""
import json
import os
import sys

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import RepeatedKFold
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import PolynomialFeatures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bml_cycle15 as cv15  # reuse run_frame() + dataset build

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")


def main():
    import model_p6  # the real data builder (2025+2026 team KPIs)
    base = model_p6.build_dataset()
    runf = cv15.run_frame()
    df = base.merge(runf[["season", "team", "RD", "PythE"]], on=["season", "team"],
                    how="left", validate="1:1")
    FEATS = ["OBP", "contact", "K%", "BB%", "HR/PA", "payroll", "RD", "PythE"]
    d = df.dropna(subset=FEATS + ["wins"]).reset_index(drop=True)
    X, y = d[FEATS].values, d["wins"].values
    print(f"rows={len(d)}  features={X.shape[1]}  (same data for ALL models)")

    models = {
        "LinearRegression": LinearRegression(),
        "Ridge(alpha=1)": Ridge(alpha=1.0),
        "RandForest(depth3)": RandomForestRegressor(n_estimators=200, max_depth=3,
                                                    random_state=0, n_jobs=-1),
        "GradBoost(depth2)": GradientBoostingRegressor(n_estimators=200, max_depth=2,
                                                      learning_rate=0.05, random_state=0),
        "MLP(1x8) neural": MLPRegressor(hidden_layer_sizes=(8,), max_iter=2000,
                                        random_state=0, early_stopping=True),
    }
    # Polynomial ridge needs transformed features (can't fit inside KFold trivially);
    # do it as a separate explicit model entry
    results = {}
    rk = RepeatedKFold(n_splits=4, n_repeats=10, random_state=0)  # fewer repeats, many models
    for name, mdl in models.items():
        maes, r2s = [], []
        for tr, te in rk.split(X):
            m = mdl  # sklearn estimators are reused; .fit overwrites state, OK for split
            m.fit(X[tr], y[tr]); yp = m.predict(X[te])
            maes.append(mean_absolute_error(y[te], yp)); r2s.append(r2_score(y[te], yp))
        results[name] = {"mae_mean": round(float(np.mean(maes)), 2),
                         "mae_2sd": round(float(2*np.std(maes)), 2),
                         "r2_mean": round(float(np.mean(r2s)), 3)}
        print(f"  {name:>24}: MAE {np.mean(maes):.2f}±{2*np.std(maes):.2f}  R2 {np.mean(r2s):.3f}")

    # Polynomial ridge (explicit transform then CV inside)
    pf = PolynomialFeatures(degree=2, include_bias=False)
    maes, r2s = [], []
    for tr, te in rk.split(X):
        Xtr = pf.fit_transform(X[tr]); Xte = pf.transform(X[te])
        m = Ridge(alpha=1.0).fit(Xtr, y[tr]); yp = m.predict(Xte)
        maes.append(mean_absolute_error(y[te], yp)); r2s.append(r2_score(y[te], yp))
    results["Poly-Ridge(deg2)"] = {"mae_mean": round(float(np.mean(maes)), 2),
                                   "mae_2sd": round(float(2*np.std(maes)), 2),
                                   "r2_mean": round(float(np.mean(r2s)), 3)}
    print(f"  {'Poly-Ridge(deg2)':>24}: MAE {np.mean(maes):.2f}±{2*np.std(maes):.2f}  R2 {np.mean(r2s):.3f}")

    # verdict — lowest MAE wins; ties go to the SIMPLER model (Occam)
    best = min(results.items(), key=lambda kv: kv[1]["mae_mean"])
    print("\nVERDICT: lowest held-out MAE model =", best[0],
          f"({best[1]['mae_mean']} wins)")
    summary = {"n_rows": int(len(d)), "n_features": int(X.shape[1]),
               "models": results, "best_by_mae": best[0]}
    with open(os.path.join(DATA, "model_family_comparison.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("wrote data/model_family_comparison.json")


if __name__ == "__main__":
    main()
