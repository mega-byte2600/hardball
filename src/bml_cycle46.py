#!/usr/bin/env python3
"""Cycle 46 — HS-1: Hakes–Sauer market test, dataset + first pricing screen.

Question (Hakes & Sauer 2006, JEP): in today's contract market, are the
thesis skills (contact/K-avoidance, OBP, walk discipline, availability)
priced below their run value? HS regressed ln(salary) of newly signed
free agents on performance and compared the OBP and SLG coefficients.

HS-1 is a WORKPAPER, not a verdict and not a dashboard change:
- Salary anchors are ACTIVE 2027 contracts from committed repo data
  (not newly signed FA contracts — no signing-date field exists in the
  committed data), so this is a cross-sectional pricing screen.
- Two salary samples, bases never mixed:
    Sample S — data/salaries_2026.json (Spotrac basis; Cycle 41 showed
      the cached pages are the 2027 payroll, despite the file name).
    Sample C — data/salaries_cots_2027.json (Cot's LRP-2027 basis;
      player-team obligation rows aggregated to player level by sum —
      a player paid by two clubs is paid the sum; bases are not mixed,
      only obligations within the same Cot's basis are added).
- Skills are EXPECTED 2027 skills: Marcel projections
  (data/projections_2027.json: OBP, SLG, K%, BB%), because the salary
  year is 2027 and Marcel is the repo's expectation engine fitted on
  prior seasons. Realized 2026 skills (fact_stat_lines, qualified
  hitters only) are carried as a descriptive sensitivity.
- Controls: age (dim_player.current_age), Steamer 2027 WAR and Steamer
  projected PA (fact_steamer_bat) — overall quality + availability.
  Marcel proj_PA is a constant 500 for all 201 hitters and cannot be
  used as an availability proxy; Steamer PA varies and is used.
- No OBP-vs-SLG run-value benchmark exists in the repo docs/data
  (checked docs/LITERATURE_SPINE.md, docs/CARPE_SCORECARD.md,
  data/value_metrics_2026.json — its wOBA weights are event weights,
  not OBP/SLG marginal run values). HS-1 therefore reports the raw
  coefficients and a clearly labeled DESCRIPTIVE coefficient ratio;
  the formal proportionality test is deferred to HS-2.
- Pitchers are out of scope (HS priced batting skills). Two-way
  players (salary prices pitching + batting) are excluded.
- OLS is implemented with numpy (no statsmodels in the venv):
  classical standard errors, t p-values via scipy.

Outputs: data/hakes_sauer_dataset.json, data/hakes_sauer_results.json.
Prints its own summary. Committed data only; no network.
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MIN_N = 60  # fail-closed power floor from the Cycle 46 brief


def norm_name(s):
    """Cycle 44 normalization: NFKD, strip accents/punct, drop suffixes."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", " ").replace(",", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(t for t in s.split() if t not in {"jr", "sr", "ii", "iii", "iv"})


def ols(y, X, names):
    """OLS with classical SEs. Returns per-term dict + fit stats + VIFs."""
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
    adj_r2 = 1 - (1 - r2) * (len(y) - 1) / dof
    terms = {lab: {"coef": round(float(b), 4), "se": round(float(s), 4),
                   "t": round(float(t), 3), "p": round(float(p), 4)}
             for lab, b, s, t, p in zip(labels, beta, se, tvals, pvals)}
    vifs = {}
    for i, nm in enumerate(names):
        Xo = np.column_stack([np.ones(len(y))] + [X[:, j] for j in range(X.shape[1]) if j != i])
        b, *_ = np.linalg.lstsq(Xo, X[:, i], rcond=None)
        pr = Xo @ b
        denom = float(((X[:, i] - X[:, i].mean()) ** 2).sum())
        r2v = 1 - float(((X[:, i] - pr) ** 2).sum()) / denom if denom > 0 else 0.0
        vifs[nm] = round(1.0 / (1.0 - r2v), 2) if r2v < 1 else None
    return {"n": int(len(y)), "r2": round(float(r2), 4), "adj_r2": round(float(adj_r2), 4),
            "terms": terms, "vif": vifs}


def quartile_table(rows, skill_key, salary_key="salary", war_key="steamer_war"):
    """Median $/WAR by skill quartile. $/WAR is defined only for WAR > 0;
    players with WAR <= 0 are excluded and counted, never silently."""
    usable = [r for r in rows if r[war_key] is not None and r[war_key] > 0]
    excluded = len(rows) - len(usable)
    if len(usable) < 8:
        return {"n_usable": len(usable), "excluded_war_le_0": excluded,
                "note": "too few WAR>0 players for quartiles"}
    vals = np.array([r[skill_key] for r in usable], dtype=float)
    q1, q3 = np.quantile(vals, [0.25, 0.75])
    bottom = [r for r in usable if r[skill_key] <= q1]
    top = [r for r in usable if r[skill_key] >= q3]

    def summ(group):
        dpw = [r[salary_key] / r[war_key] for r in group]
        return {"n": len(group), "median_salary": float(np.median([r[salary_key] for r in group])),
                "median_war": round(float(np.median([r[war_key] for r in group])), 3),
                "median_dollars_per_war": round(float(np.median(dpw)), 0)}
    return {"skill": skill_key, "q1_cut": round(float(q1), 3), "q3_cut": round(float(q3), 3),
            "n_usable": len(usable), "excluded_war_le_0": excluded,
            "bottom_quartile": summ(bottom), "top_quartile": summ(top),
            "top_to_bottom_median_dpw_ratio": round(
                summ(top)["median_dollars_per_war"] / summ(bottom)["median_dollars_per_war"], 3)}


def main():
    # ---------- shared performance layer ----------
    proj = json.loads((DATA / "projections_2027.json").read_text())
    proj_by_id = {r["player_id"]: r for r in proj}
    name_counts = Counter(norm_name(r["name"]) for r in proj)
    proj_by_name = {norm_name(r["name"]): r for r in proj if name_counts[norm_name(r["name"])] == 1}

    steam = pd.read_parquet(DATA / "curated" / "fact_steamer_bat.parquet")
    steamer = {int(r.xMLBAMID): {"war": float(r.WAR), "pa": float(r.PA)}
               for _, r in steam.iterrows()
               if pd.notna(r.xMLBAMID) and pd.notna(r.WAR) and pd.notna(r.PA)}

    dim = pd.read_parquet(DATA / "curated" / "dim_player.parquet")
    age_by_id = {int(r.player_id): int(r.current_age) for _, r in dim.iterrows()}

    # realized 2026 skills (qualified hitters only in fact_stat_lines)
    stat_lines = pd.read_parquet(DATA / "curated" / "fact_stat_lines.parquet")
    actual26 = {}
    for _, r in stat_lines[(stat_lines.group_name == "hitting") & (stat_lines.season == 2026)].iterrows():
        st = json.loads(r.stat_json)
        pa = st.get("plateAppearances") or 0
        if pa:
            actual26[int(r.player_id)] = {
                "pa": pa, "games": st.get("gamesPlayed"), "age": st.get("age"),
                "obp": float(st["obp"]), "slg": float(st["slg"]),
                "k_pct": round(100 * st["strikeOuts"] / pa, 2),
                "bb_pct": round(100 * st["baseOnBalls"] / pa, 2)}

    def performance(pid):
        """Complete-case performance bundle or None."""
        pr = proj_by_id.get(pid)
        if pr is None or pid not in steamer or pid not in age_by_id:
            return None
        return {"player_id": pid, "name": pr["name"],
                "proj_obp": pr["proj_OBP"], "proj_slg": pr["proj_SLG"],
                "proj_k_pct": pr["proj_K%"], "proj_bb_pct": pr["proj_BB%"],
                "contact_pct": round(100 - pr["proj_K%"], 2),
                "age": age_by_id[pid],
                "steamer_war": steamer[pid]["war"], "steamer_pa": steamer[pid]["pa"],
                "actual_2026": actual26.get(pid)}

    # ---------- Sample S: Spotrac-basis file ----------
    sal_s = json.loads((DATA / "salaries_2026.json").read_text())
    casc_s = Counter()
    rows_s = []
    for r in sal_s["players"]:
        casc_s["start_rows"] += 1
        status = r["status"]
        if status == "Pre-Arbitration" and r["salary_2026"] == 1_000_000:
            casc_s["excluded_prearb_placeholder_flat_1m"] += 1
            continue
        if "Arbitration" in status and "Bypassed" not in status:
            casc_s["excluded_arbitration_projection"] += 1
            continue
        casc_s["real_contract_rows"] += 1
        compact_pos = r["pos"].replace(" ", "")  # file carries e.g. "SP  /DH"
        if compact_pos in {"SP", "RP", "P"}:
            casc_s["excluded_pitcher_position"] += 1
            continue
        if compact_pos == "SP/DH":
            casc_s["excluded_two_way_salary_attribution"] += 1
            continue
        pr = None
        if r.get("player_id") and int(r["player_id"]) in proj_by_id:
            pr = proj_by_id[int(r["player_id"])]
        elif norm_name(r["name"]) in proj_by_name:
            pr = proj_by_name[norm_name(r["name"])]
        if pr is None:
            casc_s["excluded_no_marcel_projection"] += 1
            continue
        perf = performance(pr["player_id"])
        if perf is None:
            casc_s["excluded_incomplete_controls"] += 1
            continue
        rows_s.append({**perf, "sample": "S", "team": r["team"], "salary_pos": r["pos"],
                       "contract_status": status, "salary": r["salary_2026"],
                       "salary_field": "salary_2026 (Spotrac-basis file; 2027 payroll per Cycle 41)"})
    casc_s["final_players"] = len(rows_s)

    # ---------- Sample C: Cot's LRP-2027, aggregated to player level ----------
    sal_c = json.loads((DATA / "salaries_cots_2027.json").read_text())
    casc_c = Counter()
    agg = {}
    for r in sal_c["players"]:
        casc_c["start_rows_player_team"] += 1
        pr = proj_by_name.get(norm_name(r["name"]))
        if pr is None:
            casc_c["rows_without_marcel_projection"] += 1
            continue
        pid = pr["player_id"]
        a = agg.setdefault(pid, {"rows": [], "lrp": 0, "aav": 0.0, "aav_complete": True, "pos": None})
        a["rows"].append(r)
        a["lrp"] += r["salary_lrp_2027"]
        if r.get("cb_2027_aav") is None:
            a["aav_complete"] = False
        else:
            a["aav"] += r["cb_2027_aav"]
        if r.get("pos"):
            a["pos"] = r["pos"]
    casc_c["unique_players_matched_to_marcel"] = len(agg)
    rows_c, rows_c_aav = [], []
    for pid, a in agg.items():
        if a["pos"] and ("rhp" in a["pos"] or "lhp" in a["pos"]):
            casc_c["excluded_pitcher_or_two_way_label"] += 1
            continue
        perf = performance(pid)
        if perf is None:
            casc_c["excluded_incomplete_controls"] += 1
            continue
        base = {**perf, "sample": "C",
                "team": a["rows"][0]["team"], "salary_pos": a["pos"],
                "contract_status": "Cot's published LRP figure(s), aggregated over "
                                   f"{len(a['rows'])} player-team row(s)",
                "n_cots_rows_aggregated": len(a["rows"])}
        rows_c.append({**base, "salary": a["lrp"],
                       "salary_field": "salary_lrp_2027 summed over the player's Cot's rows (LRP-2027 basis)"})
        if a["aav_complete"]:
            rows_c_aav.append({**base, "salary": int(a["aav"]),
                               "salary_field": "cb_2027_aav summed over the player's Cot's rows (CBT AAV)"})
    casc_c["final_players_lrp"] = len(rows_c)
    casc_c["final_players_aav_sensitivity"] = len(rows_c_aav)

    # ---------- regressions ----------
    FEATURES = ["proj_obp", "proj_slg", "proj_k_pct", "proj_bb_pct", "age", "steamer_war", "steamer_pa"]
    LABELS = ["OBP", "SLG", "K%", "BB%", "age", "WAR", "PA"]

    def run(rows, salary_note):
        y = np.log(np.array([r["salary"] for r in rows], dtype=float))
        X = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
        full = ols(y, X, LABELS)
        keep = [0, 1, 2, 3, 4, 6]  # spec B: no WAR control (HS-faithful sensitivity)
        spec_b = ols(y, X[:, keep], [LABELS[i] for i in keep])
        obp, slg = full["terms"]["OBP"]["coef"], full["terms"]["SLG"]["coef"]
        return {"salary_basis": salary_note, "n": len(rows),
                "powered_at_min_n": len(rows) >= MIN_N,
                "spec_A_full_controls": full, "spec_B_no_war_control": spec_b,
                "obp_to_slg_coef_ratio_descriptive": (round(obp / slg, 3) if slg else None),
                "ratio_note": "DESCRIPTIVE ONLY: no OBP/SLG run-value benchmark exists in-repo; "
                              "the formal Hakes-Sauer proportionality test is deferred to HS-2."}

    results = {
        "cycle": 46, "study": "HS-1 Hakes-Sauer pricing screen (workpaper only; no dashboard claim change)",
        "method": {
            "dependent_variable": "ln(2027 salary anchor), field defined per sample in the dataset metadata",
            "skills": "Marcel 2027 projections (data/projections_2027.json): proj_OBP, proj_SLG, proj_K%, proj_BB%",
            "controls": "age (dim_player.current_age), Steamer 2027 WAR, Steamer projected PA (fact_steamer_bat)",
            "spec_B": "sensitivity without the WAR control (Hakes-Sauer controlled playing time/experience, not WAR)",
            "run_value_benchmark": "none found in repo docs/data — descriptive coefficient ratio only; formal test deferred to HS-2",
            "scope": "hitters only; pitchers out of scope; two-way players excluded (salary prices both roles)",
            "design_limit": "cross-sectional screen on ACTIVE 2027 contracts, not HS's newly-signed-FA design; "
                            "associations are not causal price effects",
            "min_n_rule": f"samples below n={MIN_N} are reported as underpowered descriptives only",
        },
        "sample_S_spotrac_basis": run(rows_s, "Spotrac-basis file data/salaries_2026.json, salary_2026 field "
                                              "(2027 payroll basis per Cycle 41)"),
        "sample_C_cots_lrp2027": run(rows_c, "Cot's LRP-2027, player-aggregated salary_lrp_2027"),
        "sample_C_cots_aav_sensitivity": run(rows_c_aav, "Cot's CBT AAV (cb_2027_aav), player-aggregated; "
                                                         "only players with an AAV on every Cot's row"),
        "quartile_tables": {},
        "actual_2026_sensitivity": {},
    }
    for key, rows in [("sample_S_spotrac_basis", rows_s), ("sample_C_cots_lrp2027", rows_c)]:
        results["quartile_tables"][key] = {
            "by_contact_pct": quartile_table(rows, "contact_pct"),
            "by_proj_obp": quartile_table(rows, "proj_obp"),
        }
        sub = [r for r in rows if r["actual_2026"]]
        entry = {"n_with_qualified_2026_actuals": len(sub),
                 "note": "fact_stat_lines carries qualified hitters only (all PA >= 502); "
                         "descriptive medians only — no regression on this subset"}
        if len(sub) >= 8:
            entry["median_actual_obp"] = round(float(np.median([r["actual_2026"]["obp"] for r in sub])), 3)
            entry["median_actual_slg"] = round(float(np.median([r["actual_2026"]["slg"] for r in sub])), 3)
            entry["spearman_salary_vs_actual_obp"] = round(
                float(stats.spearmanr([r["salary"] for r in sub],
                                      [r["actual_2026"]["obp"] for r in sub]).statistic), 3)
            entry["spearman_salary_vs_actual_slg"] = round(
                float(stats.spearmanr([r["salary"] for r in sub],
                                      [r["actual_2026"]["slg"] for r in sub]).statistic), 3)
        results["actual_2026_sensitivity"][key] = entry

    dataset = {
        "metadata": {
            "cycle": 46, "generated_by": "src/bml_cycle46.py",
            "samples": {
                "S": {"source_file": "data/salaries_2026.json",
                      "basis": "Spotrac team payroll pages; Cycle 41 established the cached pages are the "
                               "2027 payroll (file name/metadata still say 2026 — flagged, not rewritten)",
                      "salary_field": "salary_2026",
                      "exclusion_cascade": dict(casc_s),
                      "exclusion_reconciliation": "Cycle 41's 501 pre-arb / 209 arb counts described the subset "
                                                  "of Spotrac rows with no Cot's LRP-2027 counterpart (777 rows). "
                                                  "HS-1's reproducible whole-file rule is broader and more "
                                                  "conservative: it excludes every Pre-Arbitration row at the "
                                                  "flat $1,000,000 (553) and every non-Bypassed Arbitration "
                                                  "row (219) as placeholders/projections."},
                "C": {"source_file": "data/salaries_cots_2027.json",
                      "basis": "Cot's Baseball Contracts (Baseball Prospectus) Labor Relations Payroll 2027: "
                               "deferred money at present value; option years at the guaranteed buyout",
                      "salary_field": "salary_lrp_2027, summed over a player's player-team rows (obligations "
                                      "to the same player from multiple clubs are one player's pay)",
                      "exclusion_cascade": dict(casc_c)},
            },
            "performance_fields": {
                "proj_obp/proj_slg/proj_k_pct/proj_bb_pct": "data/projections_2027.json (Marcel 2027)",
                "steamer_war/steamer_pa": "data/curated/fact_steamer_bat.parquet (FanGraphs Steamer 2027)",
                "age": "data/curated/dim_player.parquet current_age",
                "actual_2026": "data/curated/fact_stat_lines.parquet, 2026 hitting (qualified hitters only)",
            },
            "limits": ["active-contract cross-section, not newly signed FA contracts",
                       "skills are 2027 projections (expectations), with realized-2026 descriptives as sensitivity",
                       "pitchers out of scope; two-way players excluded",
                       "Sample S covers 24 of 30 teams (Spotrac snapshot); Sample C covers 30 teams but only "
                       "players with published Cot's dollar figures who also sit in the Marcel 201"],
        },
        "rows": rows_s + rows_c,
    }
    (DATA / "hakes_sauer_dataset.json").write_text(json.dumps(dataset, indent=1))
    (DATA / "hakes_sauer_results.json").write_text(json.dumps(results, indent=1))

    # ---------- printed summary ----------
    print("HS-1 (Cycle 46) — Hakes-Sauer pricing screen, workpaper only")
    print(f"Sample S cascade: {dict(casc_s)}")
    print(f"Sample C cascade: {dict(casc_c)}")
    for key in ["sample_S_spotrac_basis", "sample_C_cots_lrp2027", "sample_C_cots_aav_sensitivity"]:
        r = results[key]
        t = r["spec_A_full_controls"]["terms"]
        print(f"\n{key}: n={r['n']} powered={r['powered_at_min_n']} R2={r['spec_A_full_controls']['r2']}")
        for lab in LABELS:
            print(f"  {lab:>4}: coef {t[lab]['coef']:>8}  se {t[lab]['se']:>7}  p {t[lab]['p']}")
        print(f"  OBP/SLG descriptive coef ratio: {r['obp_to_slg_coef_ratio_descriptive']}")
        if key in results["quartile_tables"]:
            q = results["quartile_tables"][key]["by_contact_pct"]
            print(f"  contact quartile median $/WAR: top {q['top_quartile']['median_dollars_per_war']:,.0f} "
                  f"(n={q['top_quartile']['n']}) vs bottom {q['bottom_quartile']['median_dollars_per_war']:,.0f} "
                  f"(n={q['bottom_quartile']['n']}); ratio {q['top_to_bottom_median_dpw_ratio']}")
    print("\nWrote data/hakes_sauer_dataset.json + data/hakes_sauer_results.json")


if __name__ == "__main__":
    main()
