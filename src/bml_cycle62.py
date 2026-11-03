"""BML Cycle 62 (slate item 2, BLEND-1): can a Steamer + Marcel blend be
validated honestly — and what does the honest benchmark table look like?

DESIGN, stated before results (mirrors the Cycle 61 pre-registration):

Paired evaluation sets, built from the curated warehouse table
fact_stat_lines (the same player-season actuals Cycles 21/24 backtested
against), with the Cycles 21/24 loaders mirrored exactly:
  - hitters: PA >= 300 in every season used; targets 2025 and 2026
  - pitchers: IP >= 40 in every season used; targets 2025 and 2026
A player enters a window's paired set only with a Marcel projection, a
target-season actual, AND a prior-season actual (the naive's input) —
naive and Marcel are scored on the identical set.

Forecasters:
  - NAIVE: the player's prior-season (T-1) actual line, repeated.
  - MARCEL: the shipped method (Cycles 4/11): 5-4-3 weighted history,
    regression to the shipped league constants, plus the age term —
    with the age slopes CROSS-FITTED (fit on the other window's
    residuals, applied to the judged window), exactly as Cycles 21/24
    evaluated it. Nothing about the judged window is fit on it.
  - STEAMER: scoreable only where a Steamer projection and the
    season's outcomes both exist.
  - BLEND: convex combination of Steamer and Marcel; weights may be
    fit ONLY on the 2025 window and judged ONLY on 2026.

Windows: 2025 = training/reference window; 2026 = held-out judge
window. Metrics per forecaster per group: Pearson r, RMSE, MAE on the
primary metric (hitters OBP, pitchers ERA) and the secondary (SLG,
WHIP).

THE BAR (pre-committed): the blend is adopted as a published 2027
projection set ONLY if its 2026 primary-metric MAE beats BOTH parents
for hitters and is no worse than the best parent for pitchers. An
unscoreable blend cannot meet the bar.

Reproduction anchor: before any new number is computed, this script
regenerates the Cycles 21/24 variant-B backtests from the curated
table and asserts they match the committed artifacts
(data/marcel_backtest.json, data/pitcher_backtest.json). If they do
not, the script aborts and no benchmark is published.

Outputs: data/projection_blend_2027.json
"""
import json
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
CURATED = os.path.join(DATA, "curated", "fact_stat_lines.parquet")

HIT_LEAGUE = {"OBP": 0.317, "SLG": 0.400}
PIT_LEAGUE = {"ERA": 4.00, "WHIP": 1.28}
M_SEASONS = 300


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def load_stat_lines():
    df = pd.read_parquet(CURATED)
    df["stat"] = df["stat_json"].map(json.loads)
    return df


def load_hitters(df):
    rows = []
    for r in df[df["group_name"] == "hitting"].itertuples():
        s = r.stat
        pa = s.get("plateAppearances") or 0
        if pa < 300:
            continue
        rows.append({"season": r.season, "player_id": r.player_id,
                     "name": r.name, "PA": pa, "OBP": _num(s.get("obp")),
                     "SLG": _num(s.get("slg")), "age": s.get("age")})
    out = pd.DataFrame(rows)
    return out.dropna(subset=["OBP", "SLG"])


def load_pitchers(df):
    rows = []
    for r in df[df["group_name"] == "pitching"].itertuples():
        s = r.stat
        ip = _num(s.get("inningsPitched"))
        if ip is None or ip < 40:
            continue
        rows.append({"season": r.season, "player_id": r.player_id,
                     "name": r.name, "IP": ip, "ERA": _num(s.get("era")),
                     "WHIP": _num(s.get("whip")), "age": s.get("age")})
    out = pd.DataFrame(rows)
    return out.dropna(subset=["ERA", "WHIP"])


def hit_project(df, target, weights):
    """Cycle 21 project(), verbatim math (variant weights passed in)."""
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
                    "proj_OBP": rate("OBP", HIT_LEAGUE["OBP"]),
                    "proj_SLG": rate("SLG", HIT_LEAGUE["SLG"])})
    return pd.DataFrame(out)


def hit_age_at(df, target):
    ages = {}
    for pid, g in df.groupby("player_id"):
        g = g.sort_values("season")
        known = g.dropna(subset=["age"])
        if known.empty:
            continue
        row = known.iloc[-1]
        ages[pid] = row["age"] + (target - row["season"])
    return ages


def hit_frame(df, target, weights):
    proj = hit_project(df, target, weights)
    actual = df[df["season"] == target][["player_id", "OBP", "SLG"]]
    m = proj.merge(actual, on="player_id", how="inner")
    ages = hit_age_at(df, target)
    m["age"] = m["player_id"].map(ages)
    return m


def pit_project(df, weights):
    """Cycle 24 project()/marcel_rate(), verbatim math."""
    hist = df[df["season"].isin(weights)].copy()
    hist["w"] = hist["season"].map(weights)
    out = []
    for pid, g in hist.groupby("player_id"):
        if (g["IP"] * g["w"]).sum() < 300:
            continue

        def rate(col, lg):
            w = g["w"]
            raw = (g[col] * w).sum() / w.sum()
            tot_ip = (g["IP"] * w).sum()
            reg = tot_ip / 300.0
            return (raw * tot_ip + lg * reg) / (tot_ip + reg)

        out.append({"player_id": pid,
                    "proj_ERA": rate("ERA", PIT_LEAGUE["ERA"]),
                    "proj_WHIP": rate("WHIP", PIT_LEAGUE["WHIP"])})
    return pd.DataFrame(out)


def pit_frame(df, target, weights):
    proj = pit_project(df, weights)
    actual = df[df["season"] == target][["player_id", "ERA", "WHIP", "age"]]
    return proj.merge(actual, on="player_id", how="inner")


def metrics(pred, actual):
    pred = np.asarray(pred, dtype=float)
    actual = np.asarray(actual, dtype=float)
    err = pred - actual
    r = float(np.corrcoef(pred, actual)[0, 1]) if len(pred) > 2 else None
    return {"n": int(len(pred)),
            "r": round(r, 3) if r is not None else None,
            "rmse": round(float(np.sqrt(np.mean(err ** 2))), 4),
            "mae": round(float(np.mean(np.abs(err))), 4)}


def crossfit_slopes(m_fit, cols):
    slopes = {}
    for col in cols:
        x = (27 - m_fit["age"]).to_numpy(dtype=float)
        y = (m_fit[col] - m_fit[f"proj_{col}"]).to_numpy(dtype=float)
        slopes[col] = float((x @ y) / (x @ x))
    return slopes


def apply_slopes(m, slopes):
    m = m.copy()
    for col, s in slopes.items():
        m[f"proj_{col}"] = m[f"proj_{col}"] + s * (27 - m["age"])
    return m


def paired(frame, df, target, naive_cols):
    """Intersect the Marcel frame with prior-season actual availability
    and attach the naive (T-1 actual) columns."""
    prior = df[df["season"] == target - 1][["player_id"] + naive_cols].copy()
    prior = prior.rename(columns={c: f"naive_{c}" for c in naive_cols})
    return frame.merge(prior, on="player_id", how="inner")


NOT_SCORED = {"status": "not_scored",
              "reason": "no Steamer projections exist for a completed season "
                        "(see steamer_status); a blend of an unscored parent "
                        "cannot be scored either"}


def score_window(frame, group_cols):
    out = {}
    for col in group_cols:
        out[col] = {
            "naive": metrics(frame[f"naive_{col}"], frame[col]),
            "marcel": metrics(frame[f"proj_{col}"], frame[col]),
            "steamer": dict(NOT_SCORED),
            "blend": dict(NOT_SCORED),
        }
    return out


def main():
    raw = load_stat_lines()
    hit = load_hitters(raw)
    pit = load_pitchers(raw)

    # ---- Reproduction anchor: variant B vs the committed backtests ----
    mb = json.load(open(os.path.join(DATA, "marcel_backtest.json")))
    pb = json.load(open(os.path.join(DATA, "pitcher_backtest.json")))
    repro = {}
    for target in (2025, 2026):
        wB = {target - 1: 5, target - 2: 4, target - 3: 3}
        m = hit_frame(hit, target, wB)
        got = {"n": len(m),
               "mae_obp": round(float(np.mean(np.abs(m["proj_OBP"] - m["OBP"]))), 4),
               "mae_slg": round(float(np.mean(np.abs(m["proj_SLG"] - m["SLG"]))), 4)}
        want = mb["targets"][str(target)]["B_3season"]
        assert got == want, f"hitter reproduction failed for {target}: {got} != {want}"
        repro[f"hitters_{target}"] = got
        mp = pit_frame(pit, target, wB)
        gotp = {}
        for col in ("ERA", "WHIP"):
            d = mp[f"proj_{col}"] - mp[col]
            gotp[col] = {"n": len(mp), "mae": round(float(np.mean(np.abs(d))), 3),
                         "bias_proj_minus_actual": round(float(np.mean(d)), 3)}
        wantp = pb["targets"][str(target)]["B_3season"]
        assert gotp == wantp, f"pitcher reproduction failed for {target}: {gotp} != {wantp}"
        repro[f"pitchers_{target}"] = gotp
    print("REPRODUCTION: variant-B backtests match the committed artifacts exactly.")

    # ---- Paired frames with cross-fitted age term (the shipped Marcel) ----
    results = {"hitters": {}, "pitchers": {}}
    paired_n = {"hitters": {}, "pitchers": {}}
    hit_frames, pit_frames = {}, {}
    for target in (2025, 2026):
        wB = {target - 1: 5, target - 2: 4, target - 3: 3}
        hit_frames[target] = hit_frame(hit, target, wB)
        pit_frames[target] = pit_frame(pit, target, wB)
    for fit_t, test_t in ((2025, 2026), (2026, 2025)):
        hs = crossfit_slopes(hit_frames[fit_t].dropna(subset=["age"]), ("OBP", "SLG"))
        ps = crossfit_slopes(pit_frames[fit_t].dropna(subset=["age"]), ("ERA", "WHIP"))
        hf = apply_slopes(hit_frames[test_t].dropna(subset=["age"]), hs)
        pf = apply_slopes(pit_frames[test_t].dropna(subset=["age"]), ps)
        hf = paired(hf, hit, test_t, ["OBP", "SLG"])
        pf = paired(pf, pit, test_t, ["ERA", "WHIP"])
        results["hitters"][str(test_t)] = score_window(hf, ("OBP", "SLG"))
        results["pitchers"][str(test_t)] = score_window(pf, ("ERA", "WHIP"))
        paired_n["hitters"][str(test_t)] = int(len(hf))
        paired_n["pitchers"][str(test_t)] = int(len(pf))
        results["hitters"][str(test_t)]["_age_slopes_fit_on"] = fit_t
        results["pitchers"][str(test_t)]["_age_slopes_fit_on"] = fit_t
        print(f"window {test_t}: hitters paired n={len(hf)}, pitchers paired n={len(pf)}")
        for col in ("OBP", "SLG"):
            print(f"  HIT {col}: naive {results['hitters'][str(test_t)][col]['naive']} "
                  f"marcel {results['hitters'][str(test_t)][col]['marcel']}")
        for col in ("ERA", "WHIP"):
            print(f"  PIT {col}: naive {results['pitchers'][str(test_t)][col]['naive']} "
                  f"marcel {results['pitchers'][str(test_t)][col]['marcel']}")

    artifact = {
        "cycle": "62 — BLEND-1 (elite slate item 2 of 6)",
        "question": "Does a Steamer + Marcel blend beat both parents on held-out "
                    "actuals — and what is the honest accuracy table for the "
                    "projections this demo publishes?",
        "design": {
            "paired_sets": ("fact_stat_lines (curated warehouse), Cycles 21/24 "
                            "loaders mirrored: hitters PA>=300 in every season "
                            "used; pitchers IP>=40 in every season used. A player "
                            "enters a window only with a Marcel projection, a "
                            "target-season actual, and a prior-season actual."),
            "windows": ("2025 = training/reference window (where blend weights "
                        "would have been fit); 2026 = held-out judge window."),
            "forecasters": {
                "naive": "prior-season (T-1) actual line, repeated",
                "marcel": ("shipped method (Cycles 4/11): 5-4-3 weights, shipped "
                           "league constants, age term with slopes cross-fitted "
                           "on the other window only"),
                "steamer": "scoreable only where a Steamer projection and the "
                           "season's outcomes both exist",
                "blend": "convex Steamer/Marcel combination; weights fit on "
                         "2025 only, judged on 2026 only",
            },
            "metrics": "Pearson r, RMSE, MAE; primary = hitter OBP, pitcher ERA; "
                       "secondary = SLG, WHIP",
            "bar": ("Adopt the blend as a published 2027 projection set ONLY if "
                    "its 2026 primary-metric MAE beats BOTH parents for hitters "
                    "and is no worse than the best parent for pitchers. An "
                    "unscoreable blend cannot meet the bar."),
            "reproduction_anchor": repro,
        },
        "paired_n": paired_n,
        "results": results,
        "steamer_status": {
            "status": "NOT SCOREABLE — no held-out Steamer outcomes exist",
            "evidence": [
                "The repo holds Steamer only for 2027 (data/fg_steamer_2027_bat.json "
                "+ fg_steamer_2027_pit.json, FanGraphs API pull 2026-10-31): a "
                "season not yet played, so no outcomes exist to score it against.",
                "FanGraphs API probed 2026-11-02 with season=2026 and season=2025: "
                "the season parameter is ignored — the response is the current "
                "(2027) set (4,166 rows; 4,164 MLBAM IDs in common with the "
                "committed 2027 file, differing only at update-noise level).",
                "steamerprojections.com's pre-season archive lists downloads only "
                "through 2024; the Marcel inputs for 2023/2024 targets (2020-2022 "
                "player lines) are not committed — fact_stat_lines begins 2023 — "
                "so no earlier paired window can be built either. Its "
                "historical-weekly-logs page returned no usable content.",
            ],
            "agreement_not_accuracy": ("What exists for Steamer is agreement with "
                                       "Marcel on 2027 (OBP r = 0.889, mean |diff| "
                                       "0.010, n = 201 — data/fg_benchmark_2027.json), "
                                       "already shown on Figure 18 and labeled there "
                                       "as agreement, not accuracy."),
        },
        "blend": {
            "weights": None,
            "weights_status": "NOT FIT — fitting requires Steamer projections for "
                              "a completed season; none exist (see steamer_status).",
            "blended_2027_projections": None,
        },
        "verdict": "NOT ADOPTED — the blend cannot be scored, so the pre-committed "
                   "bar cannot be met. Steamer remains the published 2027 "
                   "projection set and Marcel the in-house spine, unchanged. No "
                   "optimizer shadow run (adoption-gated).",
        "recommendation": "Do not rewire the stack onto a blend now; the first "
                          "honest test arrives after the 2027 season, when the "
                          "committed Steamer 2027 set can be scored against 2027 "
                          "actuals on this same paired design.",
        "dashboard_change": "New benchmark panel under Figure 18 (Explorer, Check "
                            "the Model): the held-out accuracy table for the "
                            "scoreable forecasters, with Steamer and the blend "
                            "shown as not scored, with the reason.",
        "shadow_run": None,
    }
    path = os.path.join(DATA, "projection_blend_2027.json")
    with open(path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
