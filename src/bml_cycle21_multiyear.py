"""Cycle 21: MULTI-YEAR player persistence — the edge, re-tested at scale.

The 2025->2026 persistence result (contact r=0.90) rested on 80 players.
After the backfill (2022-2024 added) this re-tests the SAME claim across
every adjacent season pair in the lake, raising n to potentially hundreds
and checking the result is stable across seasons, not one lucky window.

Only runs meaningfully once backfill has populated earlier seasons. Uses
REAL data only; reports n and each pair.
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
DB = os.path.join(DATA, "mlb_lake.db")

MIN_PA = 200
FEATS = {"OBP": "obp", "BB%": "baseOnBalls", "contact": "strikeOuts", "ISO": "slg"}


def all_hitter_rows():
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT season, player_id, name, stat_json FROM stat_lines "
                       "WHERE group_name='hitting'").fetchall()
    con.close()
    out = []
    for season, pid, name, j in rows:
        s = json.loads(j)
        PA = float(s.get("plateAppearances") or 0)
        if PA == 0:
            continue
        obp = float(s.get("obp") or 0)
        bb = float(s.get("baseOnBalls") or 0) / PA * 100
        contact = (PA - float(s.get("strikeOuts") or 0)) / PA * 100
        iso = float(s.get("slg") or 0) - float(s.get("avg") or 0)
        out.append({"season": int(season), "pid": int(pid), "name": name,
                    "PA": PA, "OBP": obp, "BB%": bb, "contact": contact, "ISO": iso})
    return pd.DataFrame(out)


def main():
    df = all_hitter_rows()
    seasons = sorted(df["season"].unique())
    print(f"lake now: {len(df)} player-seasons, seasons {seasons}, "
          f"{df['pid'].nunique()} players")

    pairs = [(s, s+1) for s in seasons if s+1 in seasons]
    summaries = {}
    all_contact = {"x": [], "y": []}
    for a, b in pairs:
        pa = df[df["season"] == a].set_index("pid")
        pb = df[df["season"] == b].set_index("pid")
        common = pa.index.intersection(pb.index)
        ok = [p for p in common if (pa.loc[p, "PA"] >= MIN_PA and pb.loc[p, "PA"] >= MIN_PA)]
        if len(ok) < 10:
            print(f"  {a}->{b}: n={len(ok)} skipped")
            continue
        r_c = np.corrcoef(pa.loc[ok, "contact"], pb.loc[ok, "contact"])[0, 1]
        r_o = np.corrcoef(pa.loc[ok, "OBP"], pb.loc[ok, "OBP"])[0, 1]
        r_bb = np.corrcoef(pa.loc[ok, "BB%"], pb.loc[ok, "BB%"])[0, 1]
        # contact prediction vs naive
        xc = pa.loc[ok, "contact"].values; yc = pb.loc[ok, "contact"].values
        m = LinearRegression().fit(xc.reshape(-1, 1), yc)
        mae = mean_absolute_error(yc, m.predict(xc.reshape(-1, 1)))
        naive = mean_absolute_error(yc, np.full_like(yc, yc.mean()))
        redux = (1 - mae/naive) * 100
        r2 = r2_score(yc, m.predict(xc.reshape(-1, 1)))
        summaries[f"{a}->{b}"] = {"n": len(ok), "contact_r": round(float(r_c), 3),
                                  "BB_r": round(float(r_bb), 3), "OBP_r": round(float(r_o), 3),
                                  "contact_mae": round(float(mae), 2),
                                  "contact_err_redux_pct": round(float(redux), 1),
                                  "contact_r2": round(float(r2), 3)}
        all_contact["x"].extend(xc.tolist()); all_contact["y"].extend(yc.tolist())
        print(f"  {a}->{b}: n={len(ok)}  contact r={r_c:.3f} (err -{redux:.1f}%, R2 {r2:.3f}) "
              f"BB r={r_bb:.3f} OBP r={r_o:.3f}")

    # pooled persistence across ALL pairs (every valid player-year)
    pooled_r = np.corrcoef(all_contact["x"], all_contact["y"])[0, 1] if all_contact["y"] else None
    print(f"\nPOOLED contact persistence across all {sum(s['n'] for s in summaries.values())} player-years: ")
    result = {"seasons": seasons, "per_pair": summaries,
              "total_player_seasons": int(len(df)),
              "n_players": int(df["pid"].nunique())}
    if pooled_r is not None:
        result["pooled_contact_r"] = round(float(pooled_r), 3)
        print(f"  pooled contact r = {pooled_r:.3f}")

    # verdict on stability
    rs = [v["contact_r"] for v in summaries.values()]
    if rs and all(r >= 0.6 for r in rs):
        result["verdict"] = "STABLE: contact persists r>=0.6 in EVERY season pair tested"
    elif rs:
        result["verdict"] = f"VARIABLE: ranges {min(rs):.2f}-{max(rs):.2f}; see per-pair"
    else:
        result["verdict"] = "INSUFFICIENT DATA: backfill earlier seasons first"
    print("VERDICT:", result["verdict"])

    with open(os.path.join(DATA, "player_persistence_multiyear.json"), "w") as f:
        json.dump(result, f, indent=2)
    print("wrote data/player_persistence_multiyear.json")


if __name__ == "__main__":
    main()
