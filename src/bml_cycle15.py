"""BML Cycle 15: rigorous, exhaustive validation of the production model.

Replaces the ad-hoc 2-split CV with:
  1. Repeated K-fold CV (K=4, repeated 20x) on all season-rows -> honest MAE/R2
     with spread (mean +- 2sd).
  2. Full per-feature elasticity table across the LEAGUE (not just MIL): for a
     realistic unit shock, how many wins does each feature move, on average.
  3. Feature-importance via permutation (drop each feature, measure R2 loss).
  4. A naive baseline (predict league-mean wins every team) to prove we beat it.
Uses ONLY real 2025+2026 data. Detailed, verifiable, not quick-and-dirty.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, RepeatedKFold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_p6  # noqa

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0"}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
E = float(np.e)


def team_code_map(season=2026):
    r = requests.get(f"{BASE}/teams", params={"sportId": 1, "season": season}, headers=UA, timeout=60)
    m = {}
    for t in r.json().get("teams", []):
        m[t["id"]] = t.get("abbreviation")
    m.update({114: "CLE", 145: "CHW", 133: "ATH"})
    return m


def run_frame():
    idm = team_code_map(2026)
    rows = []
    for season in (2025, 2026):
        r = requests.get(f"{BASE}/standings", params={"season": season,
            "standingsTypes": "regularSeason", "leagueId": "103,104"}, headers=UA, timeout=60)
        for rec in r.json().get("records", []):
            for tr in rec.get("teamRecords", []):
                code = idm.get(tr.get("team", {}).get("id"))
                if not code: continue
                RS = tr.get("runsScored"); RA = tr.get("runsAllowed")
                pyth = (RS ** E / (RS ** E + RA ** E)) if (RS and RA) else 0.5
                rows.append({"season": season, "team": code, "RD": RS - RA,
                             "PythE": round(pyth * 162, 2), "wins": tr.get("wins")})
    return pd.DataFrame(rows)


def main():
    base = model_p6.build_dataset()
    runf = run_frame()
    df = base.merge(runf[["season", "team", "RD", "PythE"]], on=["season", "team"], how="left", validate="1:1")
    FEATS = model_p6.FEATURES + ["RD", "PythE"]
    d = df.dropna(subset=FEATS + ["wins"]).reset_index(drop=True)
    X = d[FEATS].values; y = d["wins"].values
    print(f"rows={len(d)}: {X.shape[1]} features over {d['season'].nunique()} seasons")

    # 1) Repeated K-fold
    rk = RepeatedKFold(n_splits=4, n_repeats=20, random_state=0)
    maes, r2s = [], []
    for tr, te in rk.split(X):
        m = LinearRegression().fit(X[tr], y[tr])
        yp = m.predict(X[te])
        maes.append(mean_absolute_error(y[te], yp)); r2s.append(r2_score(y[te], yp))
    print(f"\n[1] Repeated K-fold (K=4 x20): MAE {np.mean(maes):.2f} ±{2*np.std(maes):.2f} "
          f"R2 {np.mean(r2s):.3f} ±{2*np.std(r2s):.3f}")

    # 2) Naive basline
    naive_mae = mean_absolute_error(y, np.full_like(y, y.mean()))
    print(f"[baseline] predict league-mean for every team: MAE {naive_mae:.2f} "
          f"(we are {naive_mae-np.mean(maes):.2f} wins better)")

    # 3) Full-league elasticity: fit on all, unit-shock each feature at each team
    m = LinearRegression().fit(X, y)
    coef = dict(zip(FEATS, m.coef_))
    shocks = {"OBP": .010, "contact": 1.0, "K%": 1.0, "BB%": 1.0, "HR/PA": 1.0,
              "ISO": .01, "payroll": 25_000_000, "RD": 25.0, "PythE": 5.0}
    print("\n[3] Elasticity (mean wins change per realistic unit shock, all teams):")
    elas = {}
    for f in FEATS:
        dW = np.mean(coef[f] * shocks[f])
        elas[f] = {"shock": shocks[f], "dWins": round(float(dW), 3)}
        print(f"   {f:>8}: {shocks[f]:>9,.0f} → {dW:+.3f} wins")

    # 4) Permutation importance
    print("\n[4] Permutation importance (decrease in R2 when feature permuted):")
    Xt, yt = X, y
    base_r2 = r2_score(yt, m.predict(Xt))
    perm = {}
    rng = np.random.default_rng(1)
    for i, f in enumerate(FEATS):
        Xp = Xt.copy(); Xp[:, i] = rng.permutation(Xp[:, i])
        r2p = r2_score(yt, m.predict(Xp))
        perm[f] = round(max(0.0, base_r2 - r2p), 4)
    for f, v in sorted(perm.items(), key=lambda kv: -kv[1]):
        print(f"   {f:>8}: {v} R2 loss")

    out = {"repeated_kfold": {"mae_mean": round(np.mean(maes), 2),
                              "mae_2sd": round(2*np.std(maes), 2),
                              "r2_mean": round(float(np.mean(r2s)), 3)},
           "naive_baseline_mae": round(float(naive_mae), 2),
           "elasticity": elas, "permutation_importance": perm}
    with open(os.path.join(DATA, "robust_validation.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote data/robust_validation.json")


if __name__ == "__main__":
    main()
