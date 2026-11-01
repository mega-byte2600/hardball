"""BML Cycle 20: SAVANT at the PLAYER level — does Statcast add anything
to Marcel, or is it decoration?

Cycle 3 tested team-average xwOBA and killed it honestly (high
correlation, no usable signal; and the raw hit-rate literature it was
based on failed at team level). The player level — where the roster
tool actually works — was never tested. CarpeData wired the Savant
leaderboards in by player_id (src/carpe.py), so now it is.

Three questions, all out-of-sample:
  Q1 (luck correction): does last year's EXPECTED wOBA (xwOBA) predict
     next year's actual wOBA better than last year's ACTUAL wOBA?
     Pairs 2023->24, 2024->25, 2025->26, PA >= 250 both seasons.
  Q2 (trait stability): are bat speed / barrel% / squared-up as stable
     year-to-year as the outcomes they supposedly drive (SLG, OBP)?
     A trait that isn't stable can't project anything.
  Q3 (incremental value): fit each Savant family on one target year's
     Marcel residuals, apply to the other year (both directions).
     Baseline = the shipped Marcel (Cycle 21: 3-season + fitted age).
     Families: F1 luck gap (est_woba - woba), F2 batted ball
     (barrel%, EV50, sweet-spot%), F3 bat tracking (avg bat speed,
     squared-up/swing, blast/swing; 2024+ only), F4 all combined.

Adoption rule (declared before running): a family joins the projection
only if it improves OOS MAE in BOTH directions on its target metric.
Anything else is dropped and logged — the Cycle 2/3 discipline.

Outputs: data/savant_test.json
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

import bml_cycle21 as c21

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
AGE_SLOPE = {"OBP": 0.00158, "SLG": 0.00390}


def load_json(name):
    return pd.DataFrame(json.load(open(os.path.join(DATA, name))))


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def q1_luck():
    out = {}
    for prior, target in ((2023, 2024), (2024, 2025), (2025, 2026)):
        p = load_json(f"savant_expected_{prior}.json")
        t = load_json(f"savant_expected_{target}.json")
        m = p.merge(t, on="player_id", suffixes=("_p", "_t"))
        m = m[(m["pa_p"] >= 250) & (m["pa_t"] >= 250)]
        out[f"{prior}->{target}"] = {
            "n": len(m),
            "mae_prior_actual_woba": round(mae(m["woba_p"], m["woba_t"]), 4),
            "mae_prior_est_woba": round(mae(m["est_woba_p"], m["woba_t"]), 4),
            "r_prior_actual": round(corr(m["woba_p"], m["woba_t"]), 3),
            "r_prior_est": round(corr(m["est_woba_p"], m["woba_t"]), 3),
        }
        print(f"Q1 {prior}->{target} n={len(m)}: MAE actual "
              f"{out[f'{prior}->{target}']['mae_prior_actual_woba']} vs est "
              f"{out[f'{prior}->{target}']['mae_prior_est_woba']}")
    return out


def q2_stability(df_lake):
    out = {}
    specs = [("bat_speed", "savant_bat_tracking", "avg_bat_speed", "swings_competitive", 200),
             ("barrel_pct", "savant_batted_ball", "barrel_pct", "bbe", 150),
             ("squared_up", "savant_bat_tracking", "squared_up_per_swing", "swings_competitive", 200),
             ("ev50", "savant_batted_ball", "ev50", "bbe", 150)]
    for label, prefix, col, n_col, n_min in specs:
        rs = []
        for prior, target in ((2024, 2025), (2025, 2026)):
            try:
                p = load_json(f"{prefix}_{prior}.json")
                t = load_json(f"{prefix}_{target}.json")
            except FileNotFoundError:
                continue
            m = p.merge(t, on="player_id", suffixes=("_p", "_t"))
            m = m[(m[f"{n_col}_p"] >= n_min) & (m[f"{n_col}_t"] >= n_min)]
            if len(m) >= 30:
                rs.append(round(corr(m[f"{col}_p"], m[f"{col}_t"]), 3))
        if rs:
            out[label] = {"yoy_r_by_pair": rs, "mean_r": round(float(np.mean(rs)), 3)}
            print(f"Q2 {label}: YoY r {rs}")
    # outcome stability for comparison (lake, PA>=300 both years)
    for col in ("OBP", "SLG"):
        rs = []
        for prior, target in ((2024, 2025), (2025, 2026)):
            p = df_lake[df_lake["season"] == prior][["player_id", col]]
            t = df_lake[df_lake["season"] == target][["player_id", col]]
            m = p.merge(t, on="player_id", suffixes=("_p", "_t"))
            rs.append(round(corr(m[f"{col}_p"], m[f"{col}_t"]), 3))
        out[f"outcome_{col}"] = {"yoy_r_by_pair": rs, "mean_r": round(float(np.mean(rs)), 3)}
        print(f"Q2 outcome {col}: YoY r {rs}")
    return out


def marcel_frame(df_lake, target):
    """Shipped Marcel (3-season + fitted age) projections for `target`,
    merged with that season's Savant features from the PRIOR season."""
    m = c21.evaluate(df_lake, target, {target - 1: 5, target - 2: 4, target - 3: 3})
    m = m.dropna(subset=["age"]).copy()
    for col in ("OBP", "SLG"):
        m[f"proj_{col}"] += AGE_SLOPE[col] * (27 - m["age"])
    prior = target - 1
    exp = load_json(f"savant_expected_{prior}.json")[["player_id", "woba", "est_woba"]]
    exp["luck_gap"] = exp["est_woba"] - exp["woba"]
    m = m.merge(exp[["player_id", "luck_gap"]], on="player_id", how="left")
    bb = load_json(f"savant_batted_ball_{prior}.json")[
        ["player_id", "barrel_pct", "ev50", "sweet_spot_pct"]]
    m = m.merge(bb, on="player_id", how="left")
    try:
        bt = load_json(f"savant_bat_tracking_{prior}.json")[
            ["player_id", "avg_bat_speed", "squared_up_per_swing", "blast_per_swing"]]
        m = m.merge(bt, on="player_id", how="left")
    except FileNotFoundError:
        pass
    return m


FAMILIES = {
    "F1_luck": ["luck_gap"],
    "F2_batted_ball": ["barrel_pct", "ev50", "sweet_spot_pct"],
    "F3_bat_tracking": ["avg_bat_speed", "squared_up_per_swing", "blast_per_swing"],
    "F4_all": ["luck_gap", "barrel_pct", "ev50", "sweet_spot_pct",
               "avg_bat_speed", "squared_up_per_swing", "blast_per_swing"],
}


def q3_incremental(df_lake):
    frames = {t: marcel_frame(df_lake, t) for t in (2025, 2026)}
    out = {}
    for fam, feats in FAMILIES.items():
        fam_out = {}
        for metric in ("OBP", "SLG"):
            deltas = []
            for fit_t, test_t in ((2025, 2026), (2026, 2025)):
                fit = frames[fit_t].dropna(subset=feats)
                test = frames[test_t].dropna(subset=feats)
                if len(fit) < 40 or len(test) < 40:
                    continue
                mu, sd = fit[feats].mean(), fit[feats].std().replace(0, 1)
                model = LinearRegression().fit(
                    (fit[feats] - mu) / sd, fit[metric] - fit[f"proj_{metric}"])
                adj = model.predict((test[feats] - mu) / sd)
                base = mae(test[f"proj_{metric}"], test[metric])
                new = mae(test[f"proj_{metric}"] + adj, test[metric])
                deltas.append({"fit_on": fit_t, "test_on": test_t,
                                "n_test": len(test), "base_mae": round(base, 4),
                                "adj_mae": round(new, 4),
                                "delta": round(new - base, 4)})
            if deltas:
                fam_out[metric] = deltas
                print(f"Q3 {fam} {metric}: " + " | ".join(
                    f"{d['fit_on']}->{d['test_on']} {d['base_mae']}->{d['adj_mae']} "
                    f"({d['delta']:+.4f})" for d in deltas))
        if fam_out:
            out[fam] = fam_out
    return out


VERDICTS = {
    "q1": "xwOBA is the better INPUT: prior est_woba beat prior actual wOBA "
          "at predicting next-year wOBA in all 3 pairs (MAE gaps .0025/.0004/"
          ".0020). Real, modest, literature-consistent. Noted for a future "
          "cycle that tests est-stats AS Marcel inputs (not tested here).",
    "q2": "The traits are real: bat speed YoY r ~.92, EV50 ~.90, barrel% "
          "and squared-up ~.80 — far more stable than OBP/SLG outcomes "
          "themselves (.30-.59). Stability, however, is not the same as "
          "incremental projection value (see Q3).",
    "F1_luck": "DROPPED. OBP improved both directions but by .0001-.0003 "
               "MAE (rounding-level), and SLG split (+.0012 one way). "
               "Directionally sensible, materially zero.",
    "F2_batted_ball": "DROPPED. Split decisions on both metrics.",
    "F3_bat_tracking": "DROPPED. Worsened OOS MAE in BOTH directions on "
                       "BOTH metrics despite being the most stable trait "
                       "family — Marcel's outcome history already prices "
                       "bat speed. The literature spine's open question is "
                       "answered: no, bat speed does not improve this "
                       "projection.",
    "F4_all": "DROPPED. Split decisions; combining families does not "
              "rescue them.",
    "adoption": "No Savant family joins the projection. Savant data stays "
                "in the product as context/diagnostics (and the Q1 input "
                "finding), not as projection adjustments.",
}


def main():
    df_lake = c21.load_hitters()
    results = {"q1_luck_correction": q1_luck(),
               "q2_trait_stability": q2_stability(df_lake),
               "q3_incremental_over_marcel": q3_incremental(df_lake),
               "verdicts": VERDICTS}
    path = os.path.join(DATA, "savant_test.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
