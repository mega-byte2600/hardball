"""Forecast-evaluation statistics with uncertainty (shared, tested module).

The Marcel backtest (bml_cycle21.py) reported point MAEs with no interval
and no test against a naive baseline. This module adds the standard tools:

* ``bootstrap_mae_ci`` — percentile bootstrap CI for MAE (Efron & Tibshirani,
  *An Introduction to the Bootstrap*, 1993, ch. 13).
* ``paired_bootstrap_diff`` — CI for MAE(model) - MAE(baseline) resampling
  players jointly, so the shared player-difficulty component cancels.
* ``diebold_mariano`` — Diebold & Mariano (1995, JBES 13(3):253-263) test of
  equal predictive accuracy under absolute-error loss, with the
  Harvey-Leybourne-Newbold (1997, IJF 13(2):281-291) small-sample correction
  and Student-t reference. For a cross-section of players (h = 1, no serial
  correlation) it reduces to a paired t-test on the loss differential.

Run as a script to write ``data/marcel_backtest_uncertainty.json``: Marcel
(3-season, the published variant B) against two naive baselines — repeat last
season, and league mean — for each target season and pooled.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats

SEED = 20261119
N_BOOT = 5000


@dataclass(frozen=True)
class DMResult:
    n: int
    mean_loss_diff: float  # mean(|e_model| - |e_base|); < 0 means model better
    dm_stat: float
    p_value: float


def bootstrap_mae_ci(err: np.ndarray, n_boot: int = N_BOOT, alpha: float = 0.05,
                     seed: int = SEED) -> tuple[float, float, float]:
    """Return (mae, lo, hi) with a percentile bootstrap CI."""
    a = np.abs(np.asarray(err, dtype=float))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n_boot, len(a)))
    boots = a[idx].mean(axis=1)
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(a.mean()), float(lo), float(hi)


def paired_bootstrap_diff(err_model: np.ndarray, err_base: np.ndarray,
                          n_boot: int = N_BOOT, alpha: float = 0.05,
                          seed: int = SEED) -> tuple[float, float, float]:
    """(diff, lo, hi) for MAE(model) - MAE(base), resampling pairs jointly."""
    d = np.abs(np.asarray(err_model, float)) - np.abs(np.asarray(err_base, float))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    boots = d[idx].mean(axis=1)
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(d.mean()), float(lo), float(hi)


def diebold_mariano(err_model: np.ndarray, err_base: np.ndarray,
                    h: int = 1) -> DMResult:
    """Two-sided DM test with HLN correction under absolute-error loss."""
    d = np.abs(np.asarray(err_model, float)) - np.abs(np.asarray(err_base, float))
    n = len(d)
    if n < 3:
        raise ValueError("need at least 3 paired forecasts")
    dbar = d.mean()
    # long-run variance with h-1 autocovariances (h = 1 -> sample variance)
    gamma0 = np.mean((d - dbar) ** 2)
    lrv = gamma0 + 2 * sum(np.mean((d[k:] - dbar) * (d[:-k] - dbar))
                           for k in range(1, h))
    if lrv <= 0:
        return DMResult(n, float(dbar), 0.0, 1.0)
    dm = dbar / math.sqrt(lrv / n)
    hln = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = dm * hln
    p = 2 * stats.t.sf(abs(stat), df=n - 1)
    return DMResult(n, float(dbar), float(stat), float(p))


def _rd(x: float, k: int = 4) -> float:
    return round(float(x), k)


def evaluate_against_baselines(m, prev, league: dict[str, float]) -> dict:
    """m: merged Marcel frame (player_id, proj_*, actual *); prev: T-1 rates."""
    out = {}
    j = m.merge(prev, on="player_id", how="inner", suffixes=("", "_prev"))
    out["n"] = int(len(j))
    for col in ("OBP", "SLG"):
        e_marcel = (j[f"proj_{col}"] - j[col]).to_numpy(float)
        e_repeat = (j[f"{col}_prev"] - j[col]).to_numpy(float)
        e_league = (league[col] - j[col]).to_numpy(float)
        mae, lo, hi = bootstrap_mae_ci(e_marcel)
        block = {"marcel_mae": _rd(mae), "marcel_ci95": [_rd(lo), _rd(hi)]}
        for name, e_b in (("repeat_last_season", e_repeat), ("league_mean", e_league)):
            bm, blo, bhi = bootstrap_mae_ci(e_b)
            diff, dlo, dhi = paired_bootstrap_diff(e_marcel, e_b)
            dm = diebold_mariano(e_marcel, e_b)
            block[name] = {"mae": _rd(bm), "ci95": [_rd(blo), _rd(bhi)],
                           "marcel_minus_baseline": _rd(diff),
                           "diff_ci95": [_rd(dlo), _rd(dhi)],
                           "dm_hln_stat": _rd(dm.dm_stat, 3),
                           "p_value": _rd(dm.p_value, 4),
                           "marcel_better_at_5pct": bool(dhi < 0 and dm.p_value < 0.05)}
        out[col] = block
    return out


def main() -> None:
    import pandas as pd

    import bml_cycle21 as mb

    df = mb.load_hitters()
    report = {"method": ("Marcel variant B (weights 5/4/3, 300-PA regression) vs naive "
                         "baselines; percentile bootstrap (B=%d, seed %d) and "
                         "Diebold-Mariano with HLN correction, absolute-error loss."
                         % (N_BOOT, SEED)),
              "sample_note": ("Hitters with >=300 PA in the target season and >=2000 "
                              "weighted PA of history; the committed lake holds "
                              "qualified hitters only (>=502 PA), so results describe "
                              "regulars, not part-timers."),
              "targets": {}}
    pooled = []
    for target in (2025, 2026):
        m = mb.evaluate(df, target, {target - 1: 5, target - 2: 4, target - 3: 3})
        prev = df[df["season"] == target - 1][["player_id", "OBP", "SLG"]]
        report["targets"][str(target)] = evaluate_against_baselines(m, prev, mb.LEAGUE)
        pooled.append(m.merge(prev, on="player_id", suffixes=("", "_prev"))
                      .assign(target=target))
    allm = pd.concat(pooled, ignore_index=True)
    prev_all = allm[["player_id", "target", "OBP_prev", "SLG_prev"]].rename(
        columns={"OBP_prev": "OBP", "SLG_prev": "SLG"})
    m_all = allm.drop(columns=["OBP_prev", "SLG_prev"])
    # key by (player, target) so a player in both seasons stays two forecasts
    m_all["player_id"] = m_all["player_id"].astype(str) + "_" + m_all["target"].astype(str)
    prev_all["player_id"] = prev_all["player_id"].astype(str) + "_" + prev_all["target"].astype(str)
    report["pooled"] = evaluate_against_baselines(m_all, prev_all.drop(columns="target"),
                                                  mb.LEAGUE)
    path = os.path.join(mb.DATA, "marcel_backtest_uncertainty.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    p = report["pooled"]
    print(f"pooled n={p['n']}: OBP Marcel {p['OBP']['marcel_mae']} "
          f"{p['OBP']['marcel_ci95']} vs repeat {p['OBP']['repeat_last_season']}")
    print(f"pooled SLG: {p['SLG']}")
    print(f"wrote {path}")
    _ = asdict  # re-exported for callers that serialise DMResult


if __name__ == "__main__":
    main()
