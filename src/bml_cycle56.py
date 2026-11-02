"""BML Cycle 56: UNC-2 — the uncertainty layer on the scenario rosters.

Why this cycle exists: the Cycle 49 optimizer rosters headline as point
WAR (48.9 / 52.8 / 54.8) with Cycle 50 +-20% PRICE-error ranges. Price
error is only one of the two ways the headline can miss. This cycle adds
the second layer: how far the DELIVERED WAR can land from the Steamer
point once measured projection error and measured player availability
are priced in — so the headline is never a bare number.

Method (every input measured in this repo; nothing borrowed):
  - Rate-error pools: the shipped Marcel's own out-of-sample residuals,
    recomputed here by importing src/bml_cycle21.py (hitters) and
    src/bml_cycle24.py (pitchers) and replaying their variant-C
    cross-fitted construction exactly (age slope fit on one target
    year, applied to the other; targets 2025 + 2026). The replay is
    asserted against the committed backtest artifacts before any
    simulation runs — a mismatch aborts the cycle, no artifact.
    Hitters contribute paired (actual - projected) OBP/SLG residuals;
    pitchers contribute ERA residuals. These are the only
    projection-vs-actual residuals measured in the repo. Steamer
    itself has no in-repo outcome history (its 2027 outcomes do not
    exist yet), so the interval prices the error of this class of
    projection system as the repo measured it on its own spine.
  - Availability pools: the measured 2025-26 IL factors committed in
    data/projections_2027_health.json (hitters, n=201, Cycle 27) and
    data/projections_2027_pitchers.json (pitchers, n=102). Per UNC-1
    (Cycle 54, verdict NOT SUPPORTED), availability is a downside
    adjustment, not a point correction: it enters the simulated
    distribution only. The headline points are NOT re-centered.
  - Rate error -> WAR: a hitter's residual pair is converted to runs
    with the repo's own run-value slopes (Cycle 48 season fixed-effects
    benchmark in data/hakes_sauer_verdict.json: runs per PA per unit
    OBP / SLG; team-aggregate, ecological limit as labeled there), and
    a pitcher's ERA residual to runs directly (-dERA x IP / 9). Runs
    are converted to WAR on the scale Steamer itself uses, fit here
    from Steamer's committed pool: WAR regressed on rate-implied runs
    above the pool's rate-weighted league line, separately for
    hitters and pitchers. No outside runs-per-win constant is used.
  - Aggregation: seeded Monte Carlo, 20,000 draws. Each rostered
    player's delivered WAR = Steamer WAR x availability draw + rate
    delta at delivered volume (PA or IP x the same availability draw).
    Draws are independent across players and components (stated
    assumption; correlated team-wide injury shocks are not modeled).
    Roster totals give the 10/20/50/80/90 percentiles per scenario.

Sanity checks recorded in the artifact:
  (a) simulated median vs headline point. A gap is EXPECTED and is
      not an error: the point is the full-availability Steamer
      projection, the distribution is delivered WAR. The gap is
      decomposed exactly into the availability level effect (roster
      WAR split by the two pools' mean factors) and the measured
      residual-bias effect (the backtest pools are not zero-mean:
      the shipped Marcel ran optimistic on SLG and ERA out of
      sample, and the bootstrap keeps that measured mean rather
      than assuming it away). The analytic delivered mean must
      reproduce the simulated mean within MC noise.
  (b) the Cycle 52 uniform availability-stress totals (point x 0.912,
      the hitter-pool mean applied to the whole roster) should fall
      inside the 10-90 interval. UNC-2 samples pitchers from their
      own pool (mean 0.807), so the simulated median sits below the
      uniform-stress line by construction; the check is on the
      interval, not the median.

Outputs: data/uncertainty_scenarios_2027.json (deterministic: fixed
seed, no timestamps; re-runs reproduce it byte for byte).
"""
import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bml_cycle21  # hitter Marcel backtest (Cycle 21) — mirrored, not copied
import bml_cycle24  # pitcher Marcel backtest (Cycle 24) — mirrored, not copied

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

SEED = 20261102
SIMS = 20000
TARGETS = (2025, 2026)


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------- pools
def hitter_residuals():
    """Variant-C cross-fitted (actual - projected) OBP/SLG residual
    pairs, pooled over targets 2025 + 2026, replaying bml_cycle21."""
    df = bml_cycle21.load_hitters()
    frames = {}
    for t in TARGETS:
        wB = {t - 1: 5, t - 2: 4, t - 3: 3}
        frames[t] = bml_cycle21.evaluate(df, t, wB)
    pairs, per_year = [], {}
    for fit_t, test_t in ((2025, 2026), (2026, 2025)):
        m_fit = frames[fit_t].dropna(subset=["age"]).copy()
        m_test = frames[test_t].dropna(subset=["age"]).copy()
        for col in ("OBP", "SLG"):
            x = (27 - m_fit["age"]).to_numpy(dtype=float)
            y = (m_fit[col] - m_fit[f"proj_{col}"]).to_numpy(dtype=float)
            slope = float((x @ y) / (x @ x))
            m_test[f"proj_{col}"] = (m_test[f"proj_{col}"]
                                     + slope * (27 - m_test["age"]))
        res = np.column_stack([m_test["OBP"] - m_test["proj_OBP"],
                               m_test["SLG"] - m_test["proj_SLG"]])
        pairs.append(res)
        per_year[str(test_t)] = {
            "n": int(len(m_test)),
            "mae_obp": round(float(np.mean(np.abs(res[:, 0]))), 4),
            "mae_slg": round(float(np.mean(np.abs(res[:, 1]))), 4)}
    pooled = np.vstack(pairs)
    return pooled, per_year


def pitcher_residuals():
    """Variant-C cross-fitted (actual - projected) ERA residuals,
    pooled over targets 2025 + 2026, replaying bml_cycle24."""
    df = bml_cycle24.load_pitchers()
    frames = {}
    for t in TARGETS:
        wB = {t - 1: 5, t - 2: 4, t - 3: 3}
        frames[t] = bml_cycle24.evaluate(df, t, wB)
    res_all, per_year = [], {}
    for fit_t, test_t in ((2025, 2026), (2026, 2025)):
        m_fit, m_test = frames[fit_t].copy(), frames[test_t].copy()
        for col in ("ERA", "WHIP"):
            x = (27 - m_fit["age"]).to_numpy(dtype=float)
            y = (m_fit[col] - m_fit[f"proj_{col}"]).to_numpy(dtype=float)
            slope = float((x @ y) / (x @ x))
            m_test[f"proj_{col}"] += slope * (27 - m_test["age"])
        res = (m_test["ERA"] - m_test["proj_ERA"]).to_numpy(dtype=float)
        res_all.append(res)
        per_year[str(test_t)] = {
            "n": int(len(m_test)),
            "mae_era": round(float(np.mean(np.abs(res))), 3),
            "bias_actual_minus_proj": round(float(np.mean(res)), 3)}
    return np.concatenate(res_all), per_year


def assert_backtests(h_res, h_years, p_res, p_years):
    """Fail closed unless the replay reproduces the committed backtest
    artifacts (data/marcel_backtest.json, data/pitcher_backtest.json)."""
    mb, pb = load("marcel_backtest.json"), load("pitcher_backtest.json")
    for yr, got in h_years.items():
        want = mb["C_age_crossfit"][yr]
        assert got["n"] == want["n"], f"hitter C n {yr}: {got['n']} != {want['n']}"
        assert abs(got["mae_obp"] - want["mae_obp"]) < 0.0015, (yr, got, want)
        assert abs(got["mae_slg"] - want["mae_slg"]) < 0.0015, (yr, got, want)
    mae_o = float(np.mean(np.abs(h_res[:, 0])))
    mae_s = float(np.mean(np.abs(h_res[:, 1])))
    assert abs(mae_o - mb["pooled"]["C_age_crossfit"]["mae_obp"]) < 0.0015
    assert abs(mae_s - mb["pooled"]["C_age_crossfit"]["mae_slg"]) < 0.0015
    for yr, got in p_years.items():
        want = pb["C_age_crossfit"][yr]["ERA"]
        assert got["n"] == want["n"], f"pitcher C n {yr}: {got['n']} != {want['n']}"
        assert abs(got["mae_era"] - want["mae"]) < 0.0015, (yr, got, want)
        # artifact bias is proj - actual; residuals here are actual - proj
        assert abs(got["bias_actual_minus_proj"]
                   + want["bias_proj_minus_actual"]) < 0.0015, (yr, got, want)
    mae_e = float(np.mean(np.abs(p_res)))
    assert abs(mae_e - pb["pooled"]["C_age_crossfit"]["mae_era"]) < 0.0015
    print(f"backtest replay verified: hitter residuals n={len(h_res)} "
          f"(MAE OBP {mae_o:.4f} / SLG {mae_s:.4f}), pitcher residuals "
          f"n={len(p_res)} (MAE ERA {mae_e:.3f}) — match committed artifacts")


# ------------------------------------------------------- Steamer scales
def steamer_scales(beta_obp, beta_slg):
    """Fit WAR ~ a + s x runs on Steamer's own committed pool, so rate
    residuals convert to WAR on the projection system's own scale."""
    bat = [r for r in load("fg_steamer_2027_bat.json")
           if r.get("xMLBAMID") is not None and (r.get("PA") or 0) >= 300]
    pa = np.array([r["PA"] for r in bat], dtype=float)
    obp = np.array([r["OBP"] for r in bat], dtype=float)
    slg = np.array([r["SLG"] for r in bat], dtype=float)
    war_h = np.array([r["WAR"] for r in bat], dtype=float)
    lg_obp = float((pa * obp).sum() / pa.sum())
    lg_slg = float((pa * slg).sum() / pa.sum())
    runs_h = pa * (beta_obp * (obp - lg_obp) + beta_slg * (slg - lg_slg))
    s_h, a_h, r2_h = _ols(war_h, runs_h)

    pit = [r for r in load("fg_steamer_2027_pit.json")
           if r.get("xMLBAMID") is not None and (r.get("IP") or 0) >= 40]
    ip = np.array([r["IP"] for r in pit], dtype=float)
    era = np.array([r["ERA"] for r in pit], dtype=float)
    war_p = np.array([r["WAR"] for r in pit], dtype=float)
    lg_era = float((ip * era).sum() / ip.sum())
    runs_p = (lg_era - era) * ip / 9.0
    s_p, a_p, r2_p = _ols(war_p, runs_p)
    print(f"Steamer scale fits: hitters n={len(bat)} slope={s_h:.4f} "
          f"WAR/run (R2 {r2_h:.3f}); pitchers n={len(pit)} slope={s_p:.4f} "
          f"(R2 {r2_p:.3f})")
    return ({"n": len(bat), "slope_war_per_run": round(s_h, 4),
             "intercept": round(a_h, 3), "r2": round(r2_h, 3),
             "league_obp": round(lg_obp, 4), "league_slg": round(lg_slg, 4)},
            {"n": len(pit), "slope_war_per_run": round(s_p, 4),
             "intercept": round(a_p, 3), "r2": round(r2_p, 3),
             "league_era": round(lg_era, 3)}), s_h, s_p


def _ols(y, x):
    xm, ym = x.mean(), y.mean()
    s = float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())
    a = float(ym - s * xm)
    ss_res = float(((y - (a + s * x)) ** 2).sum())
    ss_tot = float(((y - ym) ** 2).sum())
    return s, a, 1.0 - ss_res / ss_tot


# ------------------------------------------------------------- simulate
def simulate(wow, h_res, p_res, h_avail, p_avail, s_h, s_p,
             beta_obp, beta_slg):
    bat = {r["xMLBAMID"]: r for r in load("fg_steamer_2027_bat.json")
           if r.get("xMLBAMID") is not None}
    pit = {r["xMLBAMID"]: r for r in load("fg_steamer_2027_pit.json")
           if r.get("xMLBAMID") is not None}
    rng = np.random.default_rng(SEED)
    out = []
    for s in wow["scenarios"]:
        roster = s["roster"]
        n = len(roster)
        ai_h = rng.integers(0, len(h_avail), size=(SIMS, n))
        ai_p = rng.integers(0, len(p_avail), size=(SIMS, n))
        ri_h = rng.integers(0, len(h_res), size=(SIMS, n))
        ri_p = rng.integers(0, len(p_res), size=(SIMS, n))
        totals = np.zeros(SIMS)
        h_war = p_war = 0.0
        for j, pl in enumerate(roster):
            war = float(pl["war"])
            if pl["pos"] in ("SP", "RP", "P"):
                p_war += war
                a = p_avail[ai_p[:, j]]
                ip_d = float(pit[pl["player_id"]]["IP"]) * a
                totals += war * a - p_res[ri_p[:, j]] * (ip_d / 9.0) * s_p
            else:
                h_war += war
                a = h_avail[ai_h[:, j]]
                pa_d = float(bat[pl["player_id"]]["PA"]) * a
                d = h_res[ri_h[:, j]]
                totals += (war * a + pa_d * (beta_obp * d[:, 0]
                                             + beta_slg * d[:, 1]) * s_h)
        pct = {q: round(float(np.percentile(totals, q)), 1)
               for q in (10, 20, 50, 80, 90)}
        point = float(s["total_war"])
        stressed = wow["availability_stress"]["stressed_totals"][
            s["label"]]["war_at_pool_mean_avail"]
        # Exact gap decomposition (independence makes the analytic
        # mean of the simulated total computable in closed form):
        # availability level effect + measured residual-bias effect.
        ma_h, ma_p = float(h_avail.mean()), float(p_avail.mean())
        avail_effect = -(h_war * (1 - ma_h) + p_war * (1 - ma_p))
        md_obp, md_slg = (float(h_res[:, 0].mean()),
                          float(h_res[:, 1].mean()))
        md_era = float(p_res.mean())
        bias_effect = 0.0
        for pl in roster:
            if pl["pos"] in ("SP", "RP", "P"):
                ip_d = float(pit[pl["player_id"]]["IP"]) * ma_p
                bias_effect += -md_era * (ip_d / 9.0) * s_p
            else:
                pa_d = float(bat[pl["player_id"]]["PA"]) * ma_h
                bias_effect += (pa_d * (beta_obp * md_obp
                                        + beta_slg * md_slg) * s_h)
        analytic_mean = point + avail_effect + bias_effect
        sim_mean = float(totals.mean())
        out.append({
            "label": s["label"],
            "point_war": point,
            "spend": s["spend"],
            "hitter_war": round(h_war, 1),
            "pitcher_war": round(p_war, 1),
            "p10": pct[10], "p20": pct[20], "p50": pct[50],
            "p80": pct[80], "p90": pct[90],
            "simulated_mean": round(sim_mean, 1),
            "point_percentile_in_simulated_distribution":
                round(float((totals < point).mean() * 100), 1),
            "sanity_median_vs_point": {
                "median_minus_point": round(pct[50] - point, 1),
                "availability_level_effect": round(avail_effect, 1),
                "measured_residual_bias_effect": round(bias_effect, 1),
                "analytic_delivered_mean": round(analytic_mean, 1),
                "simulated_mean_minus_analytic":
                    round(sim_mean - analytic_mean, 2),
                "note": "The point is the full-availability Steamer "
                        "projection; the simulated distribution is "
                        "delivered WAR. The median sits below the "
                        "point for two measured reasons: the "
                        "availability level effect (hitter pool mean "
                        f"{ma_h:.3f}, pitcher pool mean {ma_p:.3f}, "
                        "each applied to its pool's WAR share) and "
                        "the residual pools' measured bias (Marcel "
                        "ran optimistic out of sample: SLG bias "
                        f"{md_slg:+.4f}, ERA bias {md_era:+.3f} "
                        "actual-minus-projected). The remainder is "
                        "median-vs-mean skew. Nothing is re-centered: "
                        "the headline points are unchanged."},
            "sanity_cycle52_stress_inside_interval": {
                "stressed_total": stressed,
                "inside_p10_p90": bool(pct[10] <= stressed <= pct[90]),
                "note": "Cycle 52 stress applies the hitter-pool mean "
                        "factor (0.912) uniformly; UNC-2 samples "
                        "pitchers from their own pool (mean "
                        f"{float(p_avail.mean()):.3f}), so the simulated "
                        "median sits below the uniform-stress line by "
                        "construction. The check is on the interval."},
        })
        print(f"{s['label']}: point {point} | p10 {pct[10]} p20 {pct[20]} "
              f"p50 {pct[50]} p80 {pct[80]} p90 {pct[90]} | stress "
              f"{stressed} inside: {pct[10] <= stressed <= pct[90]}")
    return out


def main():
    if not os.path.exists(os.path.join(DATA, "mlb_lake.db")):
        raise SystemExit("FAIL: data/mlb_lake.db missing (copy the local "
                         "lake in, as the platform step does); no artifact")
    wow = load("wow_scenarios.json")
    verdict = load("hakes_sauer_verdict.json")
    fe = verdict["benchmark_attempt"]["season_fe_primary"]["terms"]
    beta_obp, beta_slg = fe["OBP"]["coef"], fe["SLG"]["coef"]

    h_res, h_years = hitter_residuals()
    p_res, p_years = pitcher_residuals()
    assert_backtests(h_res, h_years, p_res, p_years)

    h_avail = np.array([r["avail_pct"] for r in
                        load("projections_2027_health.json")], dtype=float)
    p_avail = np.array([r["avail_pct"] for r in
                        load("projections_2027_pitchers.json")], dtype=float)
    scales, s_h, s_p = steamer_scales(beta_obp, beta_slg)
    scenarios = simulate(wow, h_res, p_res, h_avail, p_avail,
                         s_h, s_p, beta_obp, beta_slg)

    artifact = {
        "cycle": 56,
        "study": "UNC-2 — uncertainty layer on the Cycle 49 optimizer "
                 "scenario rosters (headline since Cycle 52)",
        "method": "Seeded Monte Carlo over measured projection error "
                  "and measured player availability. Each rostered "
                  "player's delivered WAR = Steamer WAR x an "
                  "availability draw from the measured 2025-26 IL "
                  "pools, plus a rate-error delta: a paired Marcel-"
                  "backtest (OBP, SLG) residual converted to runs with "
                  "the Cycle 48 run-value slopes and to WAR on "
                  "Steamer's own fitted runs-to-WAR scale (hitters), "
                  "or a Marcel-backtest ERA residual converted at "
                  "delivered IP on the same fitted scale (pitchers).",
        "seed": SEED,
        "sims": SIMS,
        "percentiles": "10/20/50/80/90 of the simulated delivered-WAR "
                       "totals, rounded to 0.1 WAR for rendering",
        "error_pools": {
            "hitters": {
                "source": "Marcel variant-C cross-fitted residuals "
                          "(actual - projected), targets 2025 + 2026, "
                          "replayed from src/bml_cycle21.py against "
                          "the lake and asserted equal to "
                          "data/marcel_backtest.json",
                "n": int(len(h_res)),
                "per_target": h_years,
                "mae_obp": round(float(np.mean(np.abs(h_res[:, 0]))), 4),
                "mae_slg": round(float(np.mean(np.abs(h_res[:, 1]))), 4),
                "bias_actual_minus_proj_obp":
                    round(float(np.mean(h_res[:, 0])), 4),
                "bias_actual_minus_proj_slg":
                    round(float(np.mean(h_res[:, 1])), 4),
                "note": "Residual pairs are drawn together, keeping "
                        "the measured OBP/SLG error correlation."},
            "pitchers": {
                "source": "Marcel variant-C cross-fitted ERA residuals "
                          "(actual - projected), targets 2025 + 2026, "
                          "replayed from src/bml_cycle24.py against "
                          "the lake and asserted equal to "
                          "data/pitcher_backtest.json",
                "n": int(len(p_res)),
                "per_target": p_years,
                "mae_era": round(float(np.mean(np.abs(p_res))), 3),
                "bias_actual_minus_proj_era":
                    round(float(np.mean(p_res)), 3)}},
        "availability_pools": {
            "hitters": {"source": "data/projections_2027_health.json "
                                  "(Cycle 27 measured 2025-26 IL "
                                  "factors)",
                        "n": int(len(h_avail)),
                        "mean": round(float(h_avail.mean()), 3),
                        "median": round(float(np.median(h_avail)), 3),
                        "p25": round(float(np.percentile(h_avail, 25)), 3)},
            "pitchers": {"source": "data/projections_2027_pitchers.json "
                                   "(measured 2025-26 IL factors)",
                         "n": int(len(p_avail)),
                         "mean": round(float(p_avail.mean()), 3),
                         "median": round(float(np.median(p_avail)), 3),
                         "p25": round(float(np.percentile(p_avail, 25)), 3)},
            "unc1_governance": "UNC-1 (Cycle 54) verdict NOT SUPPORTED: "
                               "the availability cap is a downside "
                               "adjustment, not a point correction. It "
                               "therefore shapes this distribution "
                               "only; no headline point is shifted."},
        "run_value_slopes": {
            "source": "data/hakes_sauer_verdict.json, Cycle 48 season "
                      "fixed-effects benchmark (480 team-seasons)",
            "runs_per_pa_per_unit_obp": round(beta_obp, 4),
            "runs_per_pa_per_unit_slg": round(beta_slg, 4),
            "limit": "Team-aggregate slopes applied at player level; "
                     "the ecological limit labeled in Cycle 48 "
                     "applies here."},
        "runs_to_war_scale": {
            "method": "OLS of Steamer WAR on rate-implied runs above "
                      "the Steamer pool's rate-weighted league line, "
                      "fit on Steamer's committed 2027 pool (hitters "
                      "PA >= 300; pitchers IP >= 40). Only the slope "
                      "is used: it converts a run delta to a WAR delta "
                      "on the projection system's own scale. No "
                      "outside runs-per-win constant is used.",
            "hitters": scales[0],
            "pitchers": scales[1]},
        "scenarios": scenarios,
        "assumptions": [
            "Player draws are independent across players and across "
            "components; correlated shocks (a team-wide injury wave, "
            "a league-wide run-environment shift) are not modeled, "
            "so the intervals are narrower than a correlated world "
            "would give.",
            "The error pools are the repo Marcel's measured residuals "
            "(targets 2025-2026, regulars only: hitters PA >= 300, "
            "pitchers IP >= 40 in the target season). Steamer has no "
            "in-repo outcome history; the pools price the projection "
            "error this repo has actually measured for this class of "
            "system, whose hitter rates track Steamer at r = 0.889 "
            "(Cycle 22 benchmark).",
            "Availability draws come from the 2025-26 measured pools "
            "and are applied to playing time and WAR alike; a "
            "player's own measured factor is not used, because "
            "factors exist for only part of any roster (Cycle 27 "
            "method note in data/wow_scenarios.json).",
            "Non-availability playing-time error (benching, role "
            "change) is not separately simulated; UNC-1 measured the "
            "total Marcel PA error on the FA pool at MAE 46.2 PA "
            "(n=39), which is the scale of what is left out.",
            "The runs-to-WAR scale fits are Steamer's own and are "
            "noisy — the pitcher fit especially (its R2 is recorded "
            "in runs_to_war_scale): Steamer pitcher WAR carries role "
            "and replacement effects a single ERA line cannot hold. "
            "Each slope is the pooled best-linear conversion for a "
            "run delta, and the intervals inherit that noise.",
        ],
    }
    path = os.path.join(DATA, "uncertainty_scenarios_2027.json")
    with open(path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
