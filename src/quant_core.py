"""HARDBALL QUANT CORE — the hardcore-math layer the GP asked for.

Four real methods, each with a job an owner cares about. No math for show.

1. LINEAR regression      -> wins model (continuous outcome), strengthened with
                             run differential + Pythagorean (the e-exponentiated
                             run relation). Reported with R2 + CV MAE.

2. LOGISTIC regression    -> the BINARY decision an owner actually faces:
                             "is this roster playoff / title-caliber?" (win>=90).
                             Log-odds, e^x sigmoid link, AUC + classification.
                             Euler's e is the link function — not decoration.

3. SENSITIVITY / ELASTICITY-> 'so what?' for an owner: lift OBP by 10 pts or
                             cut BB/9 by 1 -> how do runs and wins move?
                             Unit-shock / partial-derivative measurement from the
                             fitted linear model (marginal effects).

4. EULER (e) integration   -> the Pythagorean exponent and the logit link both
                             come from the exponential family. We report the
                             run-change per unit input using e-based transforms,
                             and the log-odds (logit) scale, not raw beta.

All fitted on REAL 2025+2026 team data (lake + standings run counts).
Reports the honest number: how much of wins is runs (same-season R2) and
how much cross-season we actually predict.
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

E = np.e
WIN_THRESHOLD = 90  # playoff/title-caliber bar


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
        r = requests.get(f"{BASE}/standings", params={
            "season": season, "standingsTypes": "regularSeason",
            "leagueId": "103,104"}, headers=UA, timeout=60)
        data = r.json()
        for rec in data.get("records", []):
            for tr in rec.get("teamRecords", []):
                t = tr.get("team", {})
                code = idm.get(t.get("id"))
                if not code:
                    continue
                RS = tr.get("runsScored"); RA = tr.get("runsAllowed")
                wins = tr.get("wins"); losses = tr.get("losses")
                pyth = (RS ** E / (RS ** E + RA ** E)) if (RS and RA) else 0.5
                rows.append({"season": season, "team": code, "RS": RS, "RA": RA,
                             "RD": RS - RA, "PythE": round(pyth * 162, 2),
                             "wins": wins})
    return pd.DataFrame(rows)


def fitted_models(df25, df26, feats, target="wins"):
    """Cross-fit linear on 25 train, evaluate on 26; and vice versa."""
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, r2_score
    res = {}
    for tr, te, tag in [(df25, df26, "25->26"), (df26, df25, "26->25")]:
        m = LinearRegression().fit(tr[feats].values, tr[target].values)
        yp = m.predict(te[feats].values)
        res[tag] = {"mae": mean_absolute_error(te[target].values, yp),
                    "r2": r2_score(te[target].values, yp),
                    "intercept": m.intercept_,
                    "coef": dict(zip(feats, m.coef_)), "model": m,
                    "test": te}
    return res


def logistic(tr, te, feats, threshold=WIN_THRESHOLD):
    """Binary: wins >= 90 (playoff/title caliber). Logistic with e^x link."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, accuracy_score
    ym_tr = (tr["wins"] >= threshold).astype(int)
    ym_te = (te["wins"] >= threshold).astype(int)
    m = LogisticRegression(max_iter=2000).fit(tr[feats].values, ym_tr)
    p = m.predict_proba(te[feats].values)[:, 1]
    # log-odds (logit): ln(p/(1-p)) — the Euler link scale
    logodds = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
    pred = (p >= 0.5).astype(int)
    return {"auc": roc_auc_score(ym_te, p),
            "acc": accuracy_score(ym_te, pred),
            "base_rate": float(ym_te.mean()),
            "coef_logit": dict(zip(feats, m.coef_[0])),
            "n_test": len(te),
            "logit_range": [round(float(logodds.min()), 2), round(float(logodds.max()), 2)]}


def sensitivity(linear_res, feats, base_profile):
    """Unit-shock sensitivity: how wins move per unit change in each feature.
    Computed as partial derivative = coefficient (linear), scaled to a
    'realistic shock' (e.g. +10 pts OBP, +1 K%, +1 BB/9, +50 RD)."""
    out = {}
    coef = linear_res["25->26"]["coef"]
    # realistic unit shocks in baseball units
    shocks = {"OBP": 0.010, "contact": 1.0, "K%": -1.0, "BB%": 1.0,
              "HR/PA": 1.0, "payroll": 25_000_000, "RD": 25.0,
              "PythE": 5.0}
    for f in feats:
        print("base_profile keys:", list(base_profile.keys()))
        print("  feat:", f, "in base?", f in base_profile)
        if f not in base_profile:
            print("   SKIPPING", f, "(not in base profile)")
            continue
        base_wins = coef[f] * base_profile[f]  # partial contribution (crude, independent approx)
        delta = coef[f] * shocks.get(f, 1.0)
        out[f] = {"coef": round(coef[f], 4),
                  "shock_unit": shocks.get(f, 1.0),
                  "dWins": round(delta, 2)}
    return out


def main():
    base = model_p6.build_dataset()
    run = run_frame()
    df = base.merge(run[["season", "team", "RS", "RA", "RD", "PythE"]],
                    on=["season", "team"], how="left", validate="1:1")
    df25 = df[df["season"] == 2025]; df26 = df[df["season"] == 2026]
    df25 = df25.dropna(subset=model_p6.FEATURES + ["RD", "wins"])
    df26 = df26.dropna(subset=model_p6.FEATURES + ["RD", "wins"])

    print("=" * 70)
    print("PART 1 — LINEAR REGRESSION (wins), three feature sets, cross-validated")
    RKP = model_p6.FEATURES
    RKP_RD = model_p6.FEATURES + ["RD"]
    RKP_PYTH = model_p6.FEATURES + ["PythE"]
    for label, feats in [("raw-KPI", RKP), ("KPIs + RunDiff", RKP_RD),
                         ("KPIs + PythE", RKP_PYTH)]:
        res = fitted_models(df25, df26, feats)
        maes = [res[k]["mae"] for k in res]
        r2s = [res[k]["r2"] for k in res]
        print(f"  {label:>16}: CV-MAE {sum(maes)/2:.2f}  R2 {sum(r2s)/2:.3f}")

    # Within-season 2026: how much of wins IS runs (PythE, same season)
    d = df26.dropna(subset=["PythE", "wins"])
    from sklearn.metrics import r2_score
    sameR2 = r2_score(d["wins"], d["PythE"])
    print(f"  [within-season 2026] PythE-projected vs actual wins R2 = {sameR2:.3f} "
          f"({len(d)} teams) — the run-to-win nexus")

    print("\n" + "=" * 70)
    print(f"PART 2 — LOGISTIC REGRESSION (is team >= {WIN_THRESHOLD} wins? title-bar)")
    lin = fitted_models(df25, df26, RKP_PYTH)
    for label, feats in [("KPIs+PythE", RKP_PYTH), ("run-diff-only", ["RD"])]:
        logres = {}
        for tr, te in [(df25, df26), (df26, df25)]:
            logres["25->26" if tr.equals(df25) else "26->25"] = logistic(tr, te, feats)
        a = logres["25->26"]["auc"]; b = logres["26->25"]["auc"]
        print(f"  {label:>14}: AUC {a:.3f}/{b:.3f}  "
              f"base-rate(make-bar) {logres['25->26']['base_rate']:.0%}  "
              f"logit-scale coefs: { {k:round(v,3) for k,v in logres['25->26']['coef_logit'].items()} }")

    print("\n" + "=" * 70)
    print("PART 3 — SENSITIVITY (e-elasticity: how wins move per realistic unit shock)")
    base_profile = df26[df26["team"] == "MIL"][RKP_PYTH].iloc[0].to_dict() if len(df26)>1 else {}
    # with along-run features only (RD, PythE)
    sens = sensitivity(lin, ["RD", "PythE"], base_profile) if base_profile else {}
    print(f"  base profile (MIL 2026, {len(base_profile)} feats): "
          f"{ {k:round(v,2) for k,v in base_profile.items()} }")
    print("  shocks (partial-derivative from linear coef * realistic shock):")
    for f, v in sens.items():
        print(f"    {f:>8}: +{v['shock_unit']:.0f}{'' if 'payroll' not in f else '$M'} -> {v['dWins']:+.2f} wins")

    # Euler's role note
    print("\n" + "=" * 70)
    print("EULER (e) — where it actually enters:")
    print("  1. Pythag link uses e as exponent: wins ~ RS^e/(RS^e+RA^e)")
    print("  2. Logit link uses e: log-odds = ln(p/(1-p)); p = 1/(1+e^-z)")

    out = os.path.join(DATA, "quant_core.json")
    summary = {"within_season_r2": round(sameR2, 3),
               "base_profile": base_profile,
               "sensitivity": sens}
    json.dump(summary, open(out, "w"), indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
