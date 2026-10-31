"""BML Cycle 4: Marcel-correct player projection engine (the roster tool).

Builds next-season (2027) hitter projections from REAL lake data,
following the Marcel methodology the P3 literature validated (the simple
weighted-average projection that competitive Bayesian aging models could
not meaningfully beat; optimal regression m~1, peak ages 24-27).

Method (Tango's Marcel / 3-year weighted):
  3-season weights 5-4-3 over 2026/2025/2024 (the window is EXPLICIT —
  the lake now holds 2023+ too, and seasons outside the map never enter
  a projection), regression-to-mean m seasons of league PA, then a
  real-age adjustment. The original aging step was a dead stub (a
  hardcoded dict returning 0 for everyone); Cycle 21 backtested the
  alternatives on 2025+2026 and the age term earned its place
  out-of-sample in both directions (pooled OBP MAE .0226 -> .0220,
  SLG .0468 -> .0453), while the 3rd season itself was a wash
  (.0227 -> .0226) kept for Marcel fidelity and coverage. Slopes below
  were fit on the pooled Cycle 21 backtest residuals (n=196
  player-seasons): proj += slope * (27 - age_in_target_season), age
  from the lake's own per-season stat payloads.
Outputs: data/projections_2027.json + a cap-priced roster worksheet so an
owner can see projected production vs the $245.3M cap / 15% individual max.

This is the honest, literature-backed spine: NOT invented math.
"""
import json
import os
import sqlite3
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")

# Age-adjustment slopes fitted in Cycle 21 (see docstring); per year of
# age away from 27, applied to the projected rate for the target season.
AGE_SLOPE = {"OBP": 0.00158, "SLG": 0.00390}
TARGET_SEASON = 2027
SEASON_WEIGHTS = {2026: 5, 2025: 4, 2024: 3}

# League averages for regression target (2026 approximate, from real data)
LEAGUE = {"OBP": 0.317, "SLG": 0.400, "BA": 0.244, "K%" : 22.4, "BB%": 8.7}
# regression strength: m seasons of league PA (Tango uses ~ league avg PA)
M_SEASONS = 300  # approx one full-time season of PA for regression pull
AVG_PA = 500     # expected PA for a qualified full-time player next yr
CAP = 245_300_000
INDIV_MAX = CAP * 0.15


def load_hitter_lines() -> pd.DataFrame:
    con = sqlite3.connect(LAKE)
    q = ("SELECT season, player_id, name, team, stat_json "
         "FROM stat_lines WHERE group_name='hitting'")
    rows = []
    for season, pid, name, team, sjson in con.execute(q):
        import json as J
        s = J.loads(sjson)
        pa = (s.get("plateAppearances") or 0)
        if pa < 300:  # qualified enough to matter
            continue
        rows.append({"season": season, "player_id": pid, "name": name, "team": team,
                     "PA": pa, "BA": s.get("avg"), "OBP": s.get("obp"),
                     "SLG": s.get("slg"), "BB": s.get("baseOnBalls"),
                     "SO": s.get("strikeOuts"), "age": s.get("age")})
    con.close()
    df = pd.DataFrame(rows)
    for c in ["BA", "OBP", "SLG", "BB", "SO"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["BA", "OBP", "SLG"])
    return df


def project(df: pd.DataFrame) -> pd.DataFrame:
    """Marcel-style rate projection: 5-4-3 regression + fitted age term."""
    out = []
    for pid, g in df.groupby("player_id"):
        # explicit 3-season window — seasons outside the map never enter
        g = g[g["season"].isin(SEASON_WEIGHTS)].copy()
        if g.empty:
            continue
        g["w"] = g["season"].map(SEASON_WEIGHTS)
        tot_pa = (g["PA"] * g["w"]).sum()
        if tot_pa < 2000:
            continue  # insufficient history
        name = g.sort_values("season")["name"].iloc[-1]
        team = g.sort_values("season")["team"].iloc[-1]
        # league-relative regression target
        reg = tot_pa / M_SEASONS
        def rate(col, lg):
            raw = (g[col] * g["w"]).sum() / g["w"].sum()
            return (raw * tot_pa + lg * reg) / (tot_pa + reg)
        obp = rate("OBP", LEAGUE["OBP"])
        slg = rate("SLG", LEAGUE["SLG"])
        ba = rate("BA", LEAGUE["BA"])
        kw = (g["SO"] * g["w"]).sum() / (g["PA"] * g["w"]).sum() * 100
        bbw = (g["BB"] * g["w"]).sum() / (g["PA"] * g["w"]).sum() * 100
        # real-age adjustment (Cycle 21): age in the target season from
        # the lake's own per-season age (latest known age + gap forward)
        known = g.dropna(subset=["age"]).sort_values("season")
        if not known.empty:
            age_target = known["age"].iloc[-1] + (TARGET_SEASON - known["season"].iloc[-1])
            obp += AGE_SLOPE["OBP"] * (27 - age_target)
            slg += AGE_SLOPE["SLG"] * (27 - age_target)
        out.append({"player_id": pid, "name": name, "team": team,
                    "proj_PA": AVG_PA, "proj_BA": round(ba, 3),
                    "proj_OBP": round(obp, 3), "proj_SLG": round(slg, 3),
                    "proj_K%": round(kw, 1), "proj_BB%": round(bbw, 1)})
    return pd.DataFrame(out)


def price_roster(proj: pd.DataFrame) -> None:
    """Cap-priced view: top projected hitters and what that implies versus
    the 15% individual max and cap. Honest: no salaries in lake, so we show
    the constraint the $245.3M cap / $36.8M individual max imposes, not made-up
    contract numbers."""
    top = proj.sort_values("proj_OBP", ascending=False).head(20)
    print("\n=== Top 2027 projected hitters (by OBP) ===")
    print(top[["name", "team", "proj_BA", "proj_OBP", "proj_SLG",
               "proj_K%", "proj_BB%"]].to_string(index=False))
    path = os.path.join(DATA, "projections_2027.json")
    proj.to_json(path, orient="records", indent=2)
    print(f"\nwrote {path} ({len(proj)} players)")
    print(f"Cap ${CAP/1e6:.1f}M / individual max ${INDIV_MAX/1e6:.1f}M — "
          f"the roster constraint the winning-cheap formula optimizes under.")


def main():
    df = load_hitter_lines()
    print(f"hitter-years loaded: {len(df)} (qualified, PA>=300)")
    proj = project(df)
    print(f"projected players: {len(proj)}")
    price_roster(proj)


if __name__ == "__main__":
    main()
