import numpy as np
from scipy import stats

import forecast_eval as fe


def test_dm_matches_paired_t_for_h1():
    rng = np.random.default_rng(0)
    a, b = rng.normal(0, 1, 200), rng.normal(0, 1.2, 200)
    dm = fe.diebold_mariano(a, b)
    d = np.abs(a) - np.abs(b)
    t = stats.ttest_1samp(d, 0.0)
    # HLN-corrected DM with population variance ~ paired t (n-1 variance)
    assert abs(dm.dm_stat - t.statistic) / abs(t.statistic) < 0.01
    assert dm.p_value < 0.05 and dm.mean_loss_diff < 0


def test_bootstrap_ci_brackets_point_and_is_seeded():
    e = np.linspace(-1, 1, 101)
    m1, lo1, hi1 = fe.bootstrap_mae_ci(e)
    m2, lo2, hi2 = fe.bootstrap_mae_ci(e)
    assert lo1 < m1 < hi1 and (lo1, hi1) == (lo2, hi2)


def test_identical_forecasts_are_not_different():
    e = np.array([0.1, -0.2, 0.3, 0.05])
    assert fe.diebold_mariano(e, e).p_value == 1.0
    assert fe.paired_bootstrap_diff(e, e) == (0.0, 0.0, 0.0)
