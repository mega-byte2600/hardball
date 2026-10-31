"""BML Cycle 24: PITCHER Marcel backtest — where does the optimism live?

Cycle 22 found the pitcher Marcel runs -0.324 ERA / -0.093 WHIP versus
Steamer. That is a disagreement, not yet an error: Steamer might be the
pessimistic one. This cycle judges the shipped method against ACTUAL
outcomes (targets 2025 + 2026, history shifted back, Cycle 11's math
mirrored exactly) and tests the same variants that Cycle 21 tested for
hitters:

  A = shipped: {T-1: 5, T-2: 4}, league targets ERA 4.00 / WHIP 1.28
  B = + 3rd season {T-3: 3}
  C = B + age term, slope cross-fitted on the other target year's
      residuals (never a borrowed constant), ages from the lake's own
      per-season pitching payloads

Diagnostics, printed either way: signed bias (projected - actual) by
variant, and variant A's bias split by prior-season ERA band and by age
band — optimism concentrated in old arms is a different disease than
optimism concentrated in good arms (weak regression).

Adoption rule (declared before running): adopt the variant with the
lower pooled MAE on BOTH ERA and WHIP; if the winner is C, its shipped
slopes are refit on both years pooled, exactly as Cycle 21 did. If A
wins, the method stays and the Steamer gap is reported as Steamer-side
conservatism, with the evidence.

Outputs: data/pitcher_backtest.json
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")
LEAGUE = {"ERA": 4.00, "WHIP": 1.28}


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def load_pitchers():
    con = sqlite3.connect(LAKE)
    rows = []
    for season, pid, name, sjson in con.execute(
            "SELECT season, player_id, name, stat_json FROM stat_lines "
            "WHERE group_name='pitching'"):
        s = json.loads(sjson)
        try:
            ip = float(s.get("inningsPitched"))
        except (TypeError, ValueError):
            continue
        if ip < 40:
            continue
        rows.append({"season": season, "player_id": pid, "name": name, "IP": ip,
                     "ERA": _num(s.get("era")), "WHIP": _num(s.get("whip")),
                     "age": s.get("age")})
    con.close()
    df = pd.DataFrame(rows)
    return df.dropna(subset=["ERA", "WHIP"])


def marcel_rate(col, g, lg):
    """Cycle 11's marcel_rate, verbatim."""
    w = g["w"]
    raw = (g[col] * w).sum() / w.sum()
    tot_ip = (g["IP"] * w).sum()
    reg = tot_ip / 300.0
    return (raw * tot_ip + lg * reg) / (tot_ip + reg)


def project(df, weights):
    hist = df[df["season"].isin(weights)].copy()
    hist["w"] = hist["season"].map(weights)
    out = []
    for pid, g in hist.groupby("player_id"):
        if (g["IP"] * g["w"]).sum() < 300:
            continue
        out.append({"player_id": pid,
                    "proj_ERA": marcel_rate("ERA", g, LEAGUE["ERA"]),
                    "proj_WHIP": marcel_rate("WHIP", g, LEAGUE["WHIP"])})
    return pd.DataFrame(out)


def evaluate(df, target, weights):
    proj = project(df, weights)
    actual = df[df["season"] == target][["player_id", "ERA", "WHIP", "age"]]
    return proj.merge(actual, on="player_id", how="inner")


def stats(m, col):
    d = m[f"proj_{col}"] - m[col]
    return {"n": len(m), "mae": round(float(np.mean(np.abs(d))), 3),
            "bias_proj_minus_actual": round(float(np.mean(d)), 3)}


def main():
    df = load_pitchers()
    results = {"targets": {}}
    frames = {}
    for target in (2025, 2026):
        wA = {target - 1: 5, target - 2: 4}
        wB = {target - 1: 5, target - 2: 4, target - 3: 3}
        mA, mB = evaluate(df, target, wA), evaluate(df, target, wB)
        frames[target] = (mA, mB)
        results["targets"][target] = {
            "A_2season": {"ERA": stats(mA, "ERA"), "WHIP": stats(mA, "WHIP")},
            "B_3season": {"ERA": stats(mB, "ERA"), "WHIP": stats(mB, "WHIP")}}
        print(f"target {target}: A ERA {stats(mA, 'ERA')} WHIP {stats(mA, 'WHIP')}")
        print(f"target {target}: B ERA {stats(mB, 'ERA')} WHIP {stats(mB, 'WHIP')}")

    # C: cross-fitted age slopes on variant B.
    c_rows = {}
    for fit_t, test_t in ((2025, 2026), (2026, 2025)):
        m_fit, m_test = frames[fit_t][1].copy(), frames[test_t][1].copy()
        slopes = {}
        for col in ("ERA", "WHIP"):
            x = (27 - m_fit["age"]).to_numpy(dtype=float)
            y = (m_fit[col] - m_fit[f"proj_{col}"]).to_numpy(dtype=float)
            slopes[col] = float((x @ y) / (x @ x))
            m_test[f"proj_{col}"] += slopes[col] * (27 - m_test["age"])
        c_rows[test_t] = {"fit_on": fit_t,
                          "slopes": {k: round(v, 5) for k, v in slopes.items()},
                          "ERA": stats(m_test, "ERA"), "WHIP": stats(m_test, "WHIP")}
        print(f"C fit {fit_t} -> {test_t}: slopes {c_rows[test_t]['slopes']} "
              f"ERA {c_rows[test_t]['ERA']} WHIP {c_rows[test_t]['WHIP']}")
    results["C_age_crossfit"] = {str(k): v for k, v in c_rows.items()}

    # Diagnostics on variant A (the shipped method): where is the bias?
    diag = {}
    allA = pd.concat([frames[t][0] for t in frames])
    band_rows = []
    for target in (2025, 2026):
        mA = frames[target][0]
        p = df[df["season"] == target - 1][["player_id", "ERA"]].rename(
            columns={"ERA": "prior_ERA"})
        m = mA.merge(p, on="player_id", how="left")
        for label, lo, hi in (("<3.50", 0, 3.5), ("3.50-4.50", 3.5, 4.5), (">=4.50", 4.5, 99)):
            sub = m[(m["prior_ERA"] >= lo) & (m["prior_ERA"] < hi)]
            if len(sub):
                band_rows.append({"target": target, "prior_era_band": label,
                                  "n": len(sub),
                                  "era_bias": round(float(np.mean(sub["proj_ERA"] - sub["ERA"])), 3)})
    diag["bias_by_prior_era_band"] = band_rows
    age_rows = []
    for label, lo, hi in (("age <=27", 0, 27), ("age 28-31", 28, 31), ("age >=32", 32, 99)):
        sub = allA[(allA["age"] >= lo) & (allA["age"] <= hi)]
        if len(sub):
            age_rows.append({"age_band": label, "n": len(sub),
                             "era_bias": round(float(np.mean(sub["proj_ERA"] - sub["ERA"])), 3),
                             "whip_bias": round(float(np.mean(sub["proj_WHIP"] - sub["WHIP"])), 3)})
    diag["bias_by_age_band"] = age_rows
    results["diagnostics_variant_A"] = diag
    print(f"\nA bias by age band: {age_rows}")
    print(f"A bias by prior-ERA band: {band_rows}")

    pooled = {}
    for label, idx in (("A_2season", 0), ("B_3season", 1)):
        e = sum(stats(frames[t][idx], "ERA")["mae"] * len(frames[t][idx]) for t in frames)
        w_ = sum(stats(frames[t][idx], "WHIP")["mae"] * len(frames[t][idx]) for t in frames)
        eb = sum(stats(frames[t][idx], "ERA")["bias_proj_minus_actual"] * len(frames[t][idx]) for t in frames)
        n = sum(len(frames[t][idx]) for t in frames)
        pooled[label] = {"mae_era": round(e / n, 3), "mae_whip": round(w_ / n, 3),
                         "bias_era": round(eb / n, 3)}
    ce = sum(c_rows[t]["ERA"]["mae"] * c_rows[t]["ERA"]["n"] for t in c_rows) / sum(c_rows[t]["ERA"]["n"] for t in c_rows)
    cw = sum(c_rows[t]["WHIP"]["mae"] * c_rows[t]["WHIP"]["n"] for t in c_rows) / sum(c_rows[t]["WHIP"]["n"] for t in c_rows)
    cb = sum(c_rows[t]["ERA"]["bias_proj_minus_actual"] * c_rows[t]["ERA"]["n"] for t in c_rows) / sum(c_rows[t]["ERA"]["n"] for t in c_rows)
    pooled["C_age_crossfit"] = {"mae_era": round(ce, 3), "mae_whip": round(cw, 3),
                                "bias_era": round(cb, 3)}
    results["pooled"] = pooled
    print(f"\nPOOLED: {pooled}")

    path = os.path.join(DATA, "pitcher_backtest.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
