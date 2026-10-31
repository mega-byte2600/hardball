"""BML Cycle 21: BACKTEST the Marcel spine — 2 seasons vs 3, and does a
real-age adjustment earn its place?

Why this cycle exists: Cycle 4's Marcel shipped with only 2025+2026 in
the lake, using weights 5:4 "on what we have" — the docstring always
said the classic Marcel is 5-4-3 over three seasons. CarpeData extended
the lake to 2023+2024 (same MLB API), so the question is now testable
instead of assumable. Cycle 4's aging step is also a dead stub (a
hardcoded dict lookup that returns 0 for everyone); the lake's own
stat payloads carry each player's age per season, so a real age term
can be tested too.

Method — mirror Cycle 4's math exactly, shift the window back:
  - Variant A (shipped): history {T-1: 5, T-2: 4}
  - Variant B (classic): history {T-1: 5, T-2: 4, T-3: 3}
  - Variant C: B + age term. The age slope is NOT a borrowed constant:
    it is fit on one target year's residuals (actual - B) against
    (27 - age) and applied to the OTHER year, both directions, so the
    reported gain is out-of-sample.
  Targets T = 2025 and 2026; evaluation set = players with actual
  target-season PA >= 300 whom the variant projects. Metrics: MAE on
  OBP and SLG. League regression constants are Cycle 4's, held fixed
  across variants so the comparison is about history/age, not targets.

Adoption rule (declared before running): the variant with the lower
pooled MAE on BOTH OBP and SLG becomes the shipped method; a split
decision keeps the simpler variant and logs the split.

Outputs: data/marcel_backtest.json
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")

LEAGUE = {"OBP": 0.317, "SLG": 0.400}
M_SEASONS = 300


def load_hitters():
    con = sqlite3.connect(LAKE)
    rows = []
    for season, pid, name, sjson in con.execute(
            "SELECT season, player_id, name, stat_json FROM stat_lines "
            "WHERE group_name='hitting'"):
        s = json.loads(sjson)
        pa = s.get("plateAppearances") or 0
        if pa < 300:
            continue
        rows.append({"season": season, "player_id": pid, "name": name,
                     "PA": pa, "OBP": s.get("obp"), "SLG": s.get("slg"),
                     "age": s.get("age")})
    con.close()
    df = pd.DataFrame(rows)
    for c in ["OBP", "SLG"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["OBP", "SLG"])


def project(df, target, weights):
    """Cycle 4's project() math, parameterized by target + season weights."""
    hist = df[df["season"].isin(weights)].copy()
    hist["w"] = hist["season"].map(weights)
    out = []
    for pid, g in hist.groupby("player_id"):
        tot_pa = (g["PA"] * g["w"]).sum()
        if tot_pa < 2000:
            continue
        reg = tot_pa / M_SEASONS

        def rate(col, lg):
            raw = (g[col] * g["w"]).sum() / g["w"].sum()
            return (raw * tot_pa + lg * reg) / (tot_pa + reg)

        out.append({"player_id": pid,
                    "proj_OBP": rate("OBP", LEAGUE["OBP"]),
                    "proj_SLG": rate("SLG", LEAGUE["SLG"])})
    return pd.DataFrame(out)


def age_at(df, target):
    """Age during the target season: the lake's own per-season age when
    the player appears that year, else prior-season age + gap."""
    ages = {}
    for pid, g in df.groupby("player_id"):
        g = g.sort_values("season")
        known = g.dropna(subset=["age"])
        if known.empty:
            continue
        row = known.iloc[-1]
        ages[pid] = row["age"] + (target - row["season"])
    return ages


def evaluate(df, target, weights):
    proj = project(df, target, weights)
    actual = df[df["season"] == target][["player_id", "OBP", "SLG"]]
    m = proj.merge(actual, on="player_id", how="inner")
    ages = age_at(df, target)
    m["age"] = m["player_id"].map(ages)
    return m


def mae(m, col_proj, col_actual):
    return float(np.mean(np.abs(m[col_proj] - m[col_actual])))


def main():
    df = load_hitters()
    results = {"method": "Cycle 4 Marcel math mirrored; A={T-1:5,T-2:4}, "
                         "B adds {T-3:3}; C = B + cross-fitted age slope",
               "targets": {}}
    frames = {}
    for target in (2025, 2026):
        wA = {target - 1: 5, target - 2: 4}
        wB = {target - 1: 5, target - 2: 4, target - 3: 3}
        mA = evaluate(df, target, wA)
        mB = evaluate(df, target, wB)
        frames[target] = (mA, mB)
        results["targets"][target] = {
            "A_2season": {"n": len(mA), "mae_obp": round(mae(mA, "proj_OBP", "OBP"), 4),
                          "mae_slg": round(mae(mA, "proj_SLG", "SLG"), 4)},
            "B_3season": {"n": len(mB), "mae_obp": round(mae(mB, "proj_OBP", "OBP"), 4),
                          "mae_slg": round(mae(mB, "proj_SLG", "SLG"), 4)},
        }
        print(f"target {target}: A n={len(mA)} OBP MAE "
              f"{results['targets'][target]['A_2season']['mae_obp']} SLG "
              f"{results['targets'][target]['A_2season']['mae_slg']} | B n={len(mB)} OBP MAE "
              f"{results['targets'][target]['B_3season']['mae_obp']} SLG "
              f"{results['targets'][target]['B_3season']['mae_slg']}")

    # Variant C: fit age slope on one year's B residuals, apply to the other.
    c_rows = {}
    for fit_t, test_t in ((2025, 2026), (2026, 2025)):
        m_fit = frames[fit_t][1].dropna(subset=["age"]).copy()
        m_test = frames[test_t][1].dropna(subset=["age"]).copy()
        slopes = {}
        for col in ("OBP", "SLG"):
            x = (27 - m_fit["age"]).to_numpy(dtype=float)
            y = (m_fit[col] - m_fit[f"proj_{col}"]).to_numpy(dtype=float)
            slopes[col] = float((x @ y) / (x @ x))
            m_test[f"proj_{col}"] = m_test[f"proj_{col}"] + slopes[col] * (27 - m_test["age"])
        c_rows[test_t] = {"fit_on": fit_t, "slopes": {k: round(v, 5) for k, v in slopes.items()},
                          "n": len(m_test),
                          "mae_obp": round(mae(m_test, "proj_OBP", "OBP"), 4),
                          "mae_slg": round(mae(m_test, "proj_SLG", "SLG"), 4)}
        print(f"C (slope fit on {fit_t}) -> {test_t}: slopes {c_rows[test_t]['slopes']} "
              f"OBP MAE {c_rows[test_t]['mae_obp']} SLG MAE {c_rows[test_t]['mae_slg']} "
              f"(B was {results['targets'][test_t]['B_3season']['mae_obp']} / "
              f"{results['targets'][test_t]['B_3season']['mae_slg']})")
    results["C_age_crossfit"] = {str(k): v for k, v in c_rows.items()}

    # Pooled verdicts (player-weighted).
    pooled = {}
    for label, idx in (("A_2season", 0), ("B_3season", 1)):
        eo = sum(mae(frames[t][idx], "proj_OBP", "OBP") * len(frames[t][idx]) for t in frames)
        es = sum(mae(frames[t][idx], "proj_SLG", "SLG") * len(frames[t][idx]) for t in frames)
        n = sum(len(frames[t][idx]) for t in frames)
        pooled[label] = {"mae_obp": round(eo / n, 4), "mae_slg": round(es / n, 4)}
    co = sum(c_rows[t]["mae_obp"] * c_rows[t]["n"] for t in c_rows) / sum(c_rows[t]["n"] for t in c_rows)
    cs = sum(c_rows[t]["mae_slg"] * c_rows[t]["n"] for t in c_rows) / sum(c_rows[t]["n"] for t in c_rows)
    pooled["C_age_crossfit"] = {"mae_obp": round(co, 4), "mae_slg": round(cs, 4)}
    results["pooled"] = pooled
    print(f"\nPOOLED: {pooled}")

    path = os.path.join(DATA, "marcel_backtest.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
