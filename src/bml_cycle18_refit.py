"""Cycle 18: refit + re-validate the wins model on the 509-row panel.

The real statistical test. Everything learned on 58 rows gets re-tested on
509 real team-seasons (2011-2026). If the coefficients/accuracy survive a
9x larger, decade-spanning sample, the finding is real — not a 2-year
artifact. If they collapse, the 'whipping up bullshit' worry was correct
and we say so plainly.

Methods (all sklearn, all measured):
  - refit LinearRegression + Ridge on full panel, report coefs + CV
  - repeated K-fold CV (honest held-out error)
  - naive league-mean baseline for context
  - per-winning-cheap-team out-of-sample: does a model trained on the
    rest still predict MIL/TB/CLE wins well?
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import RepeatedKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

# Same feature set as production formula, now spanning 16 seasons
FEATS = ["OBP", "contact", "K%", "BB%", "HR/PA", "payroll", "RD"]
WIN_CHEAP = {"MIL", "TB", "CLE"}


def load_panel():
    df = pd.read_csv(os.path.join(DATA, "panel_2011_2026.csv"))
    for c in FEATS + ["wins"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=FEATS + ["wins"]).reset_index(drop=True)


def main():
    df = load_panel()
    n = len(df)
    X, y = df[FEATS].values, df["wins"].values
    print(f"PANEL: {n} team-seasons, {df['season'].min()}-{df['season'].max()}, "
          f"{df['team'].nunique()} teams, {df['season'].nunique()} seasons")

    # 1) Full fit + coefficients
    for name, mdl in [("LinearRegression", LinearRegression()),
                      ("Ridge(alpha=1)", Ridge(alpha=1.0))]:
        m = mdl.fit(X, y)
        print(f"\n[{name}] full-panel coefs:")
        for f, c in zip(FEATS, m.coef_):
            print(f"    {f:>8}: {c:+.4f}")
        print(f"    intercept: {m.intercept_:.2f}   in-sample R2: {r2_score(y, m.predict(X)):.3f}")

    # 2) Repeated K-fold (same rigor as before, now 9x the rows)
    rk = RepeatedKFold(n_splits=4, n_repeats=20, random_state=0)
    maes, r2s = [], []
    for tr, te in rk.split(X):
        m = Ridge(alpha=1.0).fit(X[tr], y[tr])
        yp = m.predict(X[te])
        maes.append(mean_absolute_error(y[te], yp)); r2s.append(r2_score(y[te], yp))
    naive = mean_absolute_error(y, np.full_like(y, y.mean()))
    print(f"\n[Repeated K-fold, Ridge] MAE {np.mean(maes):.2f}±{2*np.std(maes):.2f} "
          f"R2 {np.mean(r2s):.3f}±{2*np.std(r2s):.3f}")
    print(f"[naive league-mean baseline] MAE {naive:.2f}  (we beat it by {naive-np.mean(maes):.2f})")

    # 3) Out-of-sample honesty: leave each WINNING-CHEAP team completely out
    print("\n[Leave-one-wc-team-out] train on all other rows, predict held-out team:")
    oos = {}
    for wc in WIN_CHEAP:
        mask = df["team"] == wc
        m = Ridge(alpha=1.0).fit(X[~mask], y[~mask])
        yp = m.predict(X[mask])
        for i, actual in zip(df[mask].index, y[mask]):
            oos[wc] = {"n": int(mask.sum()), "mae": round(float(np.mean(np.abs(
                X[df['team'] == wc] @ m.coef_ + m.intercept_ - y[df['team'] == wc]))), 2),
                "actual_avg": round(float(y[mask].mean()), 1),
                "pred_avg": round(float(np.mean(yp)), 1)}
        print(f"    {wc}: {int(mask.sum())} seasons, pred-avg vs actual-avg = "
              f"{oos[wc]['pred_avg']} vs {oos[wc]['actual_avg']} (MAE {oos[wc]['mae']})")

    res = {"n_seasons": int(df["season"].nunique()), "n_rows": int(n),
           "features": FEATS,
           "ridge_cv": {"mae_mean": round(float(np.mean(maes)), 2),
                        "r2_mean": round(float(np.mean(r2s)), 3)},
           "naive_baseline_mae": round(float(naive), 2),
           "wc_out_of_sample": oos}
    with open(os.path.join(DATA, "panel_refit.json"), "w") as f:
        json.dump(res, f, indent=2)
    print("\nwrote data/panel_refit.json")


if __name__ == "__main__":
    main()
