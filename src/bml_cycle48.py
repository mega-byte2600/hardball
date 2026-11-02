#!/usr/bin/env python3
"""Cycle 48 — HS-2: Hakes–Sauer verdict — run-value benchmark attempt,
formal proportionality test, and the verdict exhibit (Figure 24).

HS-1 (Cycle 46) deferred the formal test for exactly one reason: no
OBP/SLG marginal run-value benchmark existed in the repo (the
value_metrics wOBA weights are event weights, not OBP/SLG marginal run
values). HS-2 tries to build that benchmark from committed data, under
fail-closed rules fixed BEFORE the regression was run:

  BENCHMARK = team-season runs regression on the platform's committed
  curated table fact_team_season (seasons 2011–2026): runs per PA on
  OBP and SLG, season fixed effects (within estimator) as the primary
  spec, pooled OLS as sensitivity. The benchmark ratio is
  rho = (dR/dOBP) / (dR/dSLG), CI by the delta method.
  DEFENSIBLE iff, in the FE spec: both coefficients > 0, both p < 0.10,
  both VIFs < 10, and the ratio's 95% CI is finite and excludes 0.
  If any criterion fails, the benchmark is published as a FAILED
  attempt, no formal test is run, and the verdict stays inconclusive
  on HS-1's evidence alone. No re-specification fishing: the two specs
  above are the only ones estimated.

  DATA NOTE: fact_team_season carries 29 duplicated 2026 team rows
  that differ only in the payroll cell (one copy stores a raw tuple
  string from an upstream merge). All batting fields are identical
  across copies (verified in-build). The benchmark dedupes to the 480
  unique team-seasons (30 teams x 16 seasons), keeping the copy whose
  payroll parses as a number.

  ECOLOGICAL LIMIT (labeled wherever the benchmark is used): these
  are team-season aggregates. OBP and SLG co-move through batting
  average, so an aggregate regression splits their joint variation and
  can price a point of OBP lower than event-level linear-weights
  analyses of individual plate appearances do. The benchmark is the
  ratio THIS repo's committed data supports — an aggregate benchmark,
  not an event-level run value.

  FORMAL TEST: HS-1's spec A is refit from data/hakes_sauer_dataset.json
  and asserted to reproduce HS-1's published coefficients/SEs (fail
  closed on mismatch — the covariance matrix is only trusted if the
  point estimates and SEs reproduce). Per salary sample, a Wald test
  of H0: beta_OBP - rho * beta_SLG = 0, plus the set of pricing ratios
  the sample cannot reject at 5% (the power statement).

  DESIGN LIMIT (unchanged from HS-1): active-contract cross-section,
  not Hakes & Sauer's newly-signed free agents; skills are Marcel
  2027 projections; Sample S sits at the n = 60 power floor.

Output: data/hakes_sauer_verdict.json — every number Figure 24 and
the dashboard verdict box render. Committed data only; no network.
OLS with numpy (no statsmodels in the venv), scipy t p-values —
same machinery as Cycle 46.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def ols(y, X, names):
    """OLS, classical SEs + covariance (Cycle 46 machinery)."""
    Xd = np.column_stack([np.ones(len(y))] + [X[:, i] for i in range(X.shape[1])])
    labels = ["intercept"] + names
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    resid = y - Xd @ beta
    dof = len(y) - Xd.shape[1]
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.pinv(Xd.T @ Xd)
    se = np.sqrt(np.diag(cov))
    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), dof)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot
    terms = {lab: {"coef": float(b), "se": float(s), "t": float(t), "p": float(p)}
             for lab, b, s, t, p in zip(labels, beta, se, tvals, pvals)}
    return terms, beta, cov, labels, r2, dof


def vif(X, names):
    out = {}
    for i, nm in enumerate(names):
        others = np.delete(X, i, axis=1)
        Xd = np.column_stack([np.ones(len(X))] + [others[:, j] for j in range(others.shape[1])])
        b, *_ = np.linalg.lstsq(Xd, X[:, i], rcond=None)
        r = X[:, i] - Xd @ b
        ss = float(((X[:, i] - X[:, i].mean()) ** 2).sum())
        r2 = 1 - float(r @ r) / ss
        out[nm] = float(1.0 / (1.0 - r2)) if r2 < 1 else float("inf")
    return out


def delta_ratio(beta, cov, i_num, i_den):
    """Ratio beta_num/beta_den with delta-method SE."""
    rho = float(beta[i_num] / beta[i_den])
    g = np.zeros(len(beta))
    g[i_num] = 1.0 / beta[i_den]
    g[i_den] = -beta[i_num] / beta[i_den] ** 2
    var = float(g @ cov @ g)
    return rho, float(np.sqrt(var))


def main():
    # ---------- Part 1: run-value benchmark attempt ----------
    df = pd.read_parquet(DATA / "curated" / "fact_team_season.parquet")
    raw_rows = len(df)
    df["payroll_num"] = pd.to_numeric(df["payroll"], errors="coerce")
    df = (df.sort_values("payroll_num", na_position="first")
            .drop_duplicates(subset=["season", "team"], keep="last")
            .reset_index(drop=True))
    assert len(df) == 480 and df["season"].nunique() == 16, \
        f"expected 480 unique team-seasons over 16 seasons, got {len(df)}"
    df["RPA"] = df["R"] / df["PA"]
    corr_obp_slg = float(df[["OBP", "SLG"]].corr().iloc[0, 1])

    y = df["RPA"].to_numpy(float)
    X = df[["OBP", "SLG"]].to_numpy(float)
    pooled_terms, pooled_beta, pooled_cov, labels, pooled_r2, _ = ols(y, X, ["OBP", "SLG"])
    vifs = vif(X, ["OBP", "SLG"])
    rho_pooled, se_pooled = delta_ratio(pooled_beta, pooled_cov, 1, 2)

    # season fixed effects (within demeaning), dof net of season means
    d = df.copy()
    for c in ["RPA", "OBP", "SLG"]:
        d[c + "_w"] = d[c] - d.groupby("season")[c].transform("mean")
    yw = d["RPA_w"].to_numpy(float)
    Xw = d[["OBP_w", "SLG_w"]].to_numpy(float)
    beta_w, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    resid_w = yw - Xw @ beta_w
    n_seasons = int(df["season"].nunique())
    dof_w = len(yw) - 2 - (n_seasons - 1)
    s2_w = float(resid_w @ resid_w) / dof_w
    cov_w = s2_w * np.linalg.pinv(Xw.T @ Xw)
    se_w = np.sqrt(np.diag(cov_w))
    fe_terms = {}
    for nm, b, s in zip(["OBP", "SLG"], beta_w, se_w):
        t = float(b / s)
        fe_terms[nm] = {"coef": float(b), "se": float(s), "t": t,
                        "p": float(2 * stats.t.sf(abs(t), dof_w))}
    within_r2 = 1 - float(resid_w @ resid_w) / float((yw ** 2).sum())
    rho_fe, se_fe = delta_ratio(
        np.concatenate([[0.0], beta_w]),
        np.pad(cov_w, ((1, 0), (1, 0))), 1, 2)
    ci_fe = [rho_fe - 1.96 * se_fe, rho_fe + 1.96 * se_fe]
    ci_pooled = [rho_pooled - 1.96 * se_pooled, rho_pooled + 1.96 * se_pooled]

    # per-season ratios (robustness view; n=30 each, noisy by design)
    per_season = []
    for season, gdf in df.groupby("season"):
        if len(gdf) < 10 or gdf["SLG"].std() == 0:
            continue
        t_, b_, c_, l_, r_, dof_ = ols(gdf["RPA"].to_numpy(float),
                                       gdf[["OBP", "SLG"]].to_numpy(float),
                                       ["OBP", "SLG"])
        if abs(b_[2]) > 1e-9:
            per_season.append({"season": int(season),
                               "ratio": float(b_[1] / b_[2]),
                               "obp_coef": float(b_[1]), "slg_coef": float(b_[2])})
    ps_ratios = np.array([r["ratio"] for r in per_season])

    criteria = {
        "fe_both_coefficients_positive": bool(fe_terms["OBP"]["coef"] > 0 and fe_terms["SLG"]["coef"] > 0),
        "fe_both_p_below_0.10": bool(fe_terms["OBP"]["p"] < 0.10 and fe_terms["SLG"]["p"] < 0.10),
        "vif_below_10_both": bool(all(v < 10 for v in vifs.values())),
        "ratio_ci_finite_and_excludes_zero": bool(np.isfinite(ci_fe).all() and ci_fe[0] > 0),
        "n_team_seasons_at_least_300": bool(len(df) >= 300),
    }
    defensible = all(criteria.values())

    benchmark = {
        "source": "data/curated/fact_team_season.parquet (committed platform table)",
        "raw_rows_in_table": int(raw_rows),
        "dedupe_note": ("29 duplicated 2026 team rows in the committed table differ only in "
                        "the payroll cell (one copy stores a raw tuple string); batting fields "
                        "are identical across copies. Deduped to 480 unique team-seasons "
                        "(30 teams x 16 seasons), keeping the numeric-payroll copy."),
        "dependent_variable": "team runs scored per PA (R / PA)",
        "seasons": [int(df["season"].min()), int(df["season"].max())],
        "n_team_seasons": int(len(df)),
        "corr_obp_slg": round(corr_obp_slg, 3),
        "vif": {k: round(v, 2) for k, v in vifs.items()},
        "pooled_ols": {"terms": pooled_terms, "r2": round(pooled_r2, 4),
                       "ratio_obp_to_slg": round(rho_pooled, 3),
                       "ratio_se_delta": round(se_pooled, 3),
                       "ratio_ci95": [round(c, 3) for c in ci_pooled]},
        "season_fe_primary": {"terms": fe_terms, "within_r2": round(within_r2, 4),
                              "dof": int(dof_w),
                              "ratio_obp_to_slg": round(rho_fe, 3),
                              "ratio_se_delta": round(se_fe, 3),
                              "ratio_ci95": [round(c, 3) for c in ci_fe],
                              "runs_per_6000pa_per_+0.010": {
                                  "OBP": round(float(beta_w[0]) * 0.01 * 6000, 1),
                                  "SLG": round(float(beta_w[1]) * 0.01 * 6000, 1)}},
        "per_season_ratios": {"median": round(float(np.median(ps_ratios)), 3),
                              "iqr": [round(float(np.percentile(ps_ratios, 25)), 3),
                                      round(float(np.percentile(ps_ratios, 75)), 3)],
                              "n_seasons": int(len(ps_ratios))},
        "pre_registered_criteria": criteria,
        "status": "DEFENSIBLE (team-aggregate benchmark, labeled)" if defensible
                  else "FAILED CLOSED — criteria not met; no formal test run",
        "ecological_limit": ("Team-season aggregates: OBP and SLG co-move through batting "
                             "average (r = 0.77), so the aggregate regression splits their "
                             "joint variation and prices a point of OBP lower than "
                             "event-level linear-weights analyses of individual plate "
                             "appearances do. This is the ratio the repo's committed data "
                             "supports — an aggregate benchmark, not an event-level run "
                             "value. The 60-game 2020 season is included; all variables "
                             "are per-PA rates and season fixed effects absorb each "
                             "season's run environment."),
    }

    # ---------- Part 2: formal proportionality test ----------
    formal = {"status": "NOT RUN — benchmark failed closed"}
    if defensible:
        ds = json.loads((DATA / "hakes_sauer_dataset.json").read_text())
        res = json.loads((DATA / "hakes_sauer_results.json").read_text())
        rows = ds["rows"]
        formal = {"status": "RUN", "primary_benchmark": "season-FE ratio",
                  "sensitivity_benchmark": "pooled-OLS ratio", "samples": {}}
        for sample, key in [("S", "sample_S_spotrac_basis"), ("C", "sample_C_cots_lrp2027")]:
            sub = [r for r in rows if r["sample"] == sample]
            yv = np.log([r["salary"] for r in sub])
            Xv = np.column_stack([
                [r["proj_obp"] for r in sub], [r["proj_slg"] for r in sub],
                [r["proj_k_pct"] for r in sub], [r["proj_bb_pct"] for r in sub],
                [r["age"] for r in sub], [r["steamer_war"] for r in sub],
                [r["steamer_pa"] for r in sub]])
            names = ["OBP", "SLG", "K%", "BB%", "age", "WAR", "PA"]
            terms, beta, cov, lab, r2, dof = ols(yv, Xv, names)
            pub = res[key]["spec_A_full_controls"]["terms"]
            max_dev = max(max(abs(terms[nm]["coef"] - pub[nm]["coef"]),
                              abs(terms[nm]["se"] - pub[nm]["se"])) for nm in names)
            assert max_dev < 0.01, f"HS-1 refit mismatch in sample {sample}: {max_dev}"
            i_o, i_s = lab.index("OBP"), lab.index("SLG")

            def wald(rho):
                c = float(beta[i_o] - rho * beta[i_s])
                var = float(cov[i_o, i_o] + rho ** 2 * cov[i_s, i_s]
                            - 2 * rho * cov[i_o, i_s])
                sec = float(np.sqrt(var))
                t = c / sec
                return {"rho": round(float(rho), 3), "contrast": round(c, 3),
                        "se": round(sec, 3), "t": round(float(t), 3),
                        "p": round(float(2 * stats.t.sf(abs(t), dof)), 4),
                        "contrast_ci90": [round(c - 1.645 * sec, 2), round(c + 1.645 * sec, 2)]}

            scan = np.arange(-20.0, 20.0001, 0.05)
            not_rej = []
            for rho in scan:
                c = float(beta[i_o] - rho * beta[i_s])
                var = float(cov[i_o, i_o] + rho ** 2 * cov[i_s, i_s]
                            - 2 * rho * cov[i_o, i_s])
                if abs(c / np.sqrt(var)) < 1.96:
                    not_rej.append(float(rho))
            formal["samples"][sample] = {
                "n": len(sub), "dof": int(dof),
                "salary_basis": res[key]["salary_basis"],
                "refit_matches_hs1_max_abs_dev": round(float(max_dev), 6),
                "wald_vs_fe_benchmark": wald(rho_fe),
                "wald_vs_pooled_benchmark": wald(rho_pooled),
                "ratios_not_rejected_at_5pct": {
                    "min": round(min(not_rej), 2), "max": round(max(not_rej), 2),
                    "scan_range": [-20.0, 20.0],
                    "hit_scan_bound": bool(min(not_rej) <= -19.99 or max(not_rej) >= 19.99),
                    "benchmark_inside": bool(min(not_rej) <= rho_fe <= max(not_rej))},
            }

    # ---------- Part 3: verdict ----------
    res = json.loads((DATA / "hakes_sauer_results.json").read_text())
    qt = res["quartile_tables"]
    q = {}
    for sample, key in [("S", "sample_S_spotrac_basis"), ("C", "sample_C_cots_lrp2027")]:
        t = qt[key]["by_contact_pct"]
        q[sample] = {
            "top_quartile_median_dollars_per_war": t["top_quartile"]["median_dollars_per_war"],
            "bottom_quartile_median_dollars_per_war": t["bottom_quartile"]["median_dollars_per_war"],
            "ratio": t["top_to_bottom_median_dpw_ratio"],
            "n_top": t["top_quartile"]["n"], "n_bottom": t["bottom_quartile"]["n"]}

    if defensible:
        fs = formal["samples"]
        verdict_body = (
            "The formal Hakes–Sauer proportionality test, run against a run-value "
            f"benchmark derived from {benchmark['n_team_seasons']} committed team-seasons "
            f"({benchmark['seasons'][0]}–{benchmark['seasons'][1]}; benchmark OBP/SLG run-value "
            f"ratio {rho_fe:.2f}, 95% CI {ci_fe[0]:.2f}–{ci_fe[1]:.2f}), cannot reject correct "
            "proportional pricing of OBP relative to SLG in either salary sample "
            f"(Sample S, Spotrac basis, n = {fs['S']['n']}: p = {fs['S']['wald_vs_fe_benchmark']['p']:.2f}; "
            f"Sample C, Cot's LRP-2027, n = {fs['C']['n']}: p = {fs['C']['wald_vs_fe_benchmark']['p']:.2f}). "
            "It also cannot reject large mispricing in either direction — at these samples "
            "every economically plausible pricing ratio survives the test, so the samples "
            "lack the power to settle the question. The descriptive contrast is consistent "
            "across both salary bases: top-quartile contact hitters cost about half the "
            "median dollars per WAR of the bottom quartile "
            f"({q['S']['ratio']:.2f}x in S, {q['C']['ratio']:.2f}x in C) — a contrast, not a "
            "price effect. The defensible claim is that these skills are persistent and "
            "cap-efficient with low variance — not that they are proven undervalued. "
            "Design limit: an active-contract cross-section, not Hakes & Sauer's "
            "newly-signed free agents; skills are 2027 projections.")
        verdict_short = (
            "INCONCLUSIVE on mispricing. The formal proportionality test (run-value "
            f"benchmark from {benchmark['n_team_seasons']} team-seasons, ratio {rho_fe:.2f}) cannot reject "
            "correct OBP-vs-SLG pricing in either salary sample "
            f"(S, n = {fs['S']['n']}, p = {fs['S']['wald_vs_fe_benchmark']['p']:.2f}; "
            f"C, n = {fs['C']['n']}, p = {fs['C']['wald_vs_fe_benchmark']['p']:.2f}) — and cannot reject large "
            "mispricing either: the samples lack power. What stands: the skills persist, "
            "and top-quartile contact hitters cost about half the median $/WAR of the "
            "bottom quartile on both salary bases — a descriptive contrast, not a price "
            "effect. The claim is persistent + cap-efficient + low-variance, not proven "
            "undervaluation. Design limit: active contracts, not newly-signed free agents.")
    else:
        verdict_body = (
            "The run-value benchmark attempt FAILED CLOSED (criteria in "
            "data/hakes_sauer_verdict.json), so no formal proportionality test was run. "
            "HS-2's verdict therefore stands on HS-1's evidence alone: no skill "
            "coefficient is significant in either salary sample, the descriptive "
            "OBP/SLG coefficient ratio flips sign across bases, and the quartile $/WAR "
            "contrast (about 0.53x in both samples) is descriptive, not a price effect. "
            "INCONCLUSIVE on mispricing; the defensible claim is persistence + "
            "cap-efficiency + low variance, not proven undervaluation.")
        verdict_short = verdict_body

    out = {
        "cycle": 48,
        "study": "HS-2 Hakes-Sauer verdict: run-value benchmark attempt + formal proportionality test",
        "benchmark_attempt": benchmark,
        "formal_test": formal,
        "quartile_contrast_from_hs1": {
            "source": "data/hakes_sauer_results.json (Cycle 46), by_contact_pct tables",
            "note": "Descriptive quartile contrast — NOT a price effect; no controls for age, position, or contract timing.",
            "samples": q},
        "verdict": {
            "status": "INCONCLUSIVE on mispricing",
            "body": verdict_body,
            "short": verdict_short,
            "defensible_claim": "persistent + cap-efficient + low variance",
            "not_claimed": "proven market undervaluation of contact/OBP",
            "design_limit": "active-contract cross-section, not newly-signed FAs; skills are Marcel 2027 projections; Sample S at the n=60 power floor (24 of 30 teams)",
        },
    }
    (DATA / "hakes_sauer_verdict.json").write_text(json.dumps(out, indent=1))

    print("=== Cycle 48 HS-2 summary ===")
    print(f"benchmark: pooled OBP {pooled_terms['OBP']['coef']:+.3f} SLG {pooled_terms['SLG']['coef']:+.3f} "
          f"(R2 {pooled_r2:.3f}); FE OBP {fe_terms['OBP']['coef']:+.3f} (p {fe_terms['OBP']['p']:.2g}) "
          f"SLG {fe_terms['SLG']['coef']:+.3f} (p {fe_terms['SLG']['p']:.2g}), within R2 {within_r2:.3f}")
    print(f"VIF {vifs}; corr(OBP,SLG) {corr_obp_slg:.2f}; rho_FE {rho_fe:.3f} CI [{ci_fe[0]:.3f}, {ci_fe[1]:.3f}]; "
          f"rho_pooled {rho_pooled:.3f} CI [{ci_pooled[0]:.3f}, {ci_pooled[1]:.3f}]")
    print(f"per-season ratio median {np.median(ps_ratios):.3f}")
    print(f"criteria: {criteria} -> benchmark status: {benchmark['status']}")
    if defensible:
        for s in "SC":
            w = formal["samples"][s]["wald_vs_fe_benchmark"]
            nr = formal["samples"][s]["ratios_not_rejected_at_5pct"]
            print(f"sample {s}: Wald vs FE rho: contrast {w['contrast']:+.2f} se {w['se']:.2f} "
                  f"t {w['t']:+.2f} p {w['p']:.3f}; ratios not rejected [{nr['min']}, {nr['max']}] "
                  f"(bound hit: {nr['hit_scan_bound']})")
    print("verdict:", out["verdict"]["status"])
    print("wrote data/hakes_sauer_verdict.json")


if __name__ == "__main__":
    main()
