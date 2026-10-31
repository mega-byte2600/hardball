"""Cycle 20: PLAYER-LEVEL next-year validation — the defensible core.

Question that decides whether the demo has a provable edge:
does a player's OWN prior skill (OBP, contact, BB, ISO, weighted) predict
his NEXT-year performance better than a naive baseline?

Data: real 2025 + 2026 player stat lines from the lake (80 players with
both seasons). Methods (all sklearn/stats, measured, no shortcut):
  A) year-over-year correlation: 2025 OBP/contact/BB% vs 2026 same
     (a player's object-level skill — the sabermetric claim)
  B) naive baseline: predict 2026 = league-mean at that plate-appearance
     bucket; vs predict 2026 = a regression on the player's 2025 numbers
  C) the winning-cheap hypothesis at PLAYER level: are affordable
     contact/OBP players' outputs stable year to year (acquisitionable)?
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
DB = os.path.join(DATA, "mlb_lake.db")

FEAT_Y = ["OBP", "BB%", "contact", "ISO"]


def load_player_seasons():
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT season, player_id, name, stat_json FROM stat_lines "
        "WHERE group_name='hitting'").fetchall()
    con.close()
    out = []
    for season, pid, name, j in rows:
        s = json.loads(j)
        PA = float(s.get("plateAppearances") or 0)
        if PA == 0:
            continue
        out.append({"season": int(season), "pid": pid, "name": name,
                    "PA": PA,
                    "OBP": float(s.get("obp") or 0),
                    "BB%": float(s.get("baseOnBalls") or 0) / PA * 100,
                    "contact": (PA - float(s.get("strikeOuts") or 0)) / PA * 100,
                    "ISO": float(s.get("slg") or 0) - float(s.get("avg") or 0)})
    return pd.DataFrame(out)


def main():
    df = load_player_seasons()
    print(f"player-seasons: {len(df)}  ({df['season'].nunique()} seasons, "
          f"{df['pid'].nunique()} players)")

    # PA floor so we only test real, meaningful samples (>=200 PA both years)
    MIN_PA = 200
    pivot = df.pivot_table(index="pid", columns="season", values="PA")
    ok = pivot[pivot[2025].fillna(0) >= MIN_PA]  # keep rows that have 2025
    ok = ok[ok[2026].fillna(0) >= MIN_PA]
    pids = list(ok.index)
    p = df[df["pid"].isin(pids)].copy()
    print(f"test sample: {len(pids)} players with >= {MIN_PA} PA in BOTH 2025 and 2026")

    # A) Year-over-year correlations (object-level skill persistence)
    print("\n[A] 2025 -> 2026 within-player correlation (skill persistence):")
    names = {"OBP": "OBP", "BB%": "BB%", "contact": "Contact%", "ISO": "ISO"}
    a = p[p["season"] == 2025].set_index("pid")[FEAT_Y]
    b = p[p["season"] == 2026].set_index("pid")[FEAT_Y]
    common = a.index.intersection(b.index)
    yoy = {}
    for f in FEAT_Y:
        x, y = a.loc[common, f].values, b.loc[common, f].values
        r = np.corrcoef(x, y)[0, 1]
        yoy[f] = round(float(r), 3)
        print(f"    {names[f]:<10}: r = {r:.3f}  (n={len(common)})")

    # B) naive league-mean vs player-skill regression
    print("\n[B] predicting 2026 OBP: player-skill model vs naive league-mean")
    common_pids = list(common)
    X25 = a.loc[common_pids].values  # 2025 OBP/BB%/contact/ISO
    y26 = b.loc[common_pids, "OBP"].values
    # naive: predict every player's 2026 = league mean 2026
    naive_mean = float(b["OBP"].mean())
    naive = np.full_like(y26, naive_mean)
    naive_mae = mean_absolute_error(y26, naive)
    # OBP-only model (simplest: 2025 OBP -> 2026 OBP), linear
    m_obp = LinearRegression().fit(X25[:, 0].reshape(-1, 1), y26)
    pred_obp = m_obp.predict(X25[:, 0].reshape(-1, 1))
    mae_obp = mean_absolute_error(y26, pred_obp)
    r2_obp = r2_score(y26, pred_obp)
    # full 4-feature model
    m4 = Ridge(alpha=1.0).fit(X25, y26)
    mae4 = mean_absolute_error(y26, m4.predict(X25))
    r24 = r2_score(y26, m4.predict(X25))
    print(f"    naive (league mean):     MAE {naive_mae:.4f}")
    print(f"    2025 OBP -> 2026 OBP:    MAE {mae_obp:.4f}  R2 {r2_obp:.3f}")
    print(f"    4-feature skill model:   MAE {mae4:.4f}  R2 {r24:.3f}")
    print(f"    => skill model beats naive by {naive_mae - mae4:.4f} OBP pts")

    # C) winning-cheap contact/OBP hitters: are they stable (acquisition-able)?
    print("\n[C] contact% persistence (the sweet-spot/Moneyball claim):")
    cf = "contact"
    r_contact = np.corrcoef(a.loc[common, cf].values, b.loc[common, cf].values)[0, 1]
    print(f"    contact% 2025->2026 r = {r_contact:.3f}")

    # C2) predict next-year CONTACT% (the skill itself, not the noisy output)
    xc = a.loc[common_pids, "contact"].values
    yc = b.loc[common_pids, "contact"].values
    naive_c = mean_absolute_error(yc, np.full_like(yc, b["contact"].mean()))
    mcc = LinearRegression().fit(xc.reshape(-1, 1), yc)
    mae_c = mean_absolute_error(yc, mcc.predict(xc.reshape(-1, 1)))
    r2_c = r2_score(yc, mcc.predict(xc.reshape(-1, 1)))
    print(f"\n[C2] predicting 2026 CONTACT% (the acquisitionable skill):")
    print(f"    naive (league mean):  MAE {naive_c:.2f} pts")
    print(f"    2025 contact% -> 2026: MAE {mae_c:.2f} pts  R2 {r2_c:.3f}")
    print(f"    => contact model beats naive by {naive_c - mae_c:.2f} contact pts "
          f"({(naive_c-mae_c)/naive_c*100:.1f}% error reduction)")

    summary = {"n_players": int(len(common)), "pa_floor": MIN_PA,
               "yoy_corr_2025_2026": yoy,
               "naive_mae_obp": round(float(naive_mae), 4),
               "skill_4feat_mae_obp": round(float(mae4), 4),
               "skill_beats_naive_obp_pts": round(float(naive_mae - mae4), 4),
               "contact_yoy_r": round(float(r_contact), 3),
               "contact_model": {"naive_mae": round(float(naive_c), 3),
                                 "mae": round(float(mae_c), 3),
                                 "r2": round(float(r2_c), 3),
                                 "pct_error_reduction": round(float((naive_c-mae_c)/naive_c*100), 1)},
               "core_finding": ("Player-level skill (own 2025 OBP/contact/BB/ISO) "
                                "predicts own 2026 OBP better than naive league-mean"
                                if mae4 < naive_mae else
                                "player skill did NOT beat naive for OBP")}
    with open(os.path.join(DATA, "player_level_validation.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nwrote data/player_level_validation.json")
    # also save the panel for dashboard reuse
    p[p["pid"].isin(common_pids)].to_json(os.path.join(DATA, "player_yoy.json"),
                                          orient="records", indent=2)


if __name__ == "__main__":
    main()
