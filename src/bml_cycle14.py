"""BML Cycle 14: promote run-differential model to PRODUCTION + runs panel.

The quant core showed run differential is the missing lever (MAE 7.29 ->
4.00, R2 0.39 -> 0.80). This cycle:
  1. Makes the run+differential wins model the COMMITTED production formula
     (data/formula_prod.json), not just an exploration script.
  2. Adds a 'run differential vs wins' panel to the dashboard so the top
     lever is visible, in the MLB theme.

Measures: recompute and record the production model's CV MAE/R2 to the
formula artifact, and confirm the panel renders.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpi  # noqa
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


def run_differential_frame():
    idm = team_code_map(2026)
    rows = []
    for season in (2025, 2026):
        r = requests.get(f"{BASE}/standings", params={
            "season": season, "standingsTypes": "regularSeason", "leagueId": "103,104"},
            headers=UA, timeout=60)
        for rec in r.json().get("records", []):
            for tr in rec.get("teamRecords", []):
                code = idm.get(tr.get("team", {}).get("id"))
                if not code:
                    continue
                RS = tr.get("runsScored"); RA = tr.get("runsAllowed")
                wins = tr.get("wins"); losses = tr.get("losses")
                pyth = (RS ** E / (RS ** E + RA ** E)) if (RS and RA) else 0.5
                rows.append({"season": season, "team": code, "RS": RS, "RA": RA,
                             "RD": RS - RA, "PythE": round(pyth * 162, 2), "wins": wins})
    return pd.DataFrame(rows)


def main():
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, r2_score

    base = model_p6.build_dataset()
    runf = run_differential_frame()
    df = base.merge(runf[["season", "team", "RS", "RA", "RD", "PythE"]],
                    on=["season", "team"], how="left", validate="1:1")
    d25 = df[(df.season == 2025)].dropna(subset=model_p6.FEATURES + ["RD", "wins"])
    d26 = df[(df.season == 2026)].dropna(subset=model_p6.FEATURES + ["RD", "wins"])

    FEATS = model_p6.FEATURES + ["RD", "PythE"]
    # fit production model on BOTH seasons (the committed formula)
    m = LinearRegression().fit(df.dropna(subset=FEATS + ["wins"])[FEATS].values,
                               df.dropna(subset=FEATS + ["wins"])["wins"].values)
    coefs = {f: round(float(c), 4) for f, c in zip(FEATS, m.coef_)}

    # CV across both splits
    maes, r2s = [], []
    for tr, te in [(d25, d26), (d26, d25)]:
        m2 = LinearRegression().fit(tr[FEATS].values, tr["wins"].values)
        yp = m2.predict(te[FEATS].values)
        maes.append(mean_absolute_error(te["wins"].values, yp))
        r2s.append(r2_score(te["wins"].values, yp))
    cv_mae = sum(maes) / 2; cv_r2 = sum(r2s) / 2

    formula = {"features": FEATS, "coefs": coefs, "intercept": round(float(m.intercept_), 2),
               "cv_mae": round(cv_mae, 2), "cv_r2": round(cv_r2, 3),
               "pythag_exponent": E,
               "cap_2027": 245_300_000, "floor_2027": 171_200_000,
               # G8 annotation (2026-10-31): the cv_mae/cv_r2 above are a
               # TWO-SEASON (2025<->2026) same-year cross-fit of a spec
               # containing same-year RD/PythE — a diagnostic, not a
               # forecast. Cycles 18-19 showed this family does not
               # generalize on the 2011-2026 panel (lagged OOS MAE 14.05,
               # worse than naive). Do not cite 4.3/0.764 as predictive
               # accuracy. Coefficients are retained for the Cycle 16
               # allocation exercise, which is how they are used.
               "status": "DIAGNOSTIC ONLY — same-year fit; not a forecast "
                         "(see Cycles 18-19 retraction in docs/BML_LOG.md)",
               "cv_scope": "two-season cross-fit (2025<->2026), same-year "
                           "features incl. RD and PythE"}
    out = os.path.join(DATA, "formula_prod.json")
    with open(out, "w") as f:
        json.dump(formula, f, indent=2)
    print(f"PRODUCTION FORMULA -> {out}")
    print(f"  CV MAE {cv_mae:.2f}, R2 {cv_r2:.3f} (from 7.29/0.39 raw-KPI baseline)")
    print("  coefs:", {k: v for k, v in coefs.items() if k in ("RD", "PythE", "OBP", "p_ERA")})

    # runs panel data
    runf.to_json(os.path.join(DATA, "runs_panel.json"), orient="records", indent=2)
    print(f"  runs panel data -> data/runs_panel.json ({len(runf)} rows)")


if __name__ == "__main__":
    main()
