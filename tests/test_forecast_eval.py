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


def test_dm_rejects_tiny_samples_and_detects_no_difference():
    import pytest
    with pytest.raises(ValueError):
        fe.diebold_mariano(np.array([1.0, 2.0]), np.array([1.0, 2.0]))
    rng = np.random.default_rng(7)
    a = rng.normal(0, 1, 400)
    b = a + rng.normal(0, 1e-3, 400)
    assert fe.diebold_mariano(a, b).p_value > 0.05


def test_paired_bootstrap_ci_contains_true_difference():
    rng = np.random.default_rng(11)
    base = rng.normal(0, 1, 500)
    model = base * 0.8  # model errors 20% smaller in absolute terms
    d, lo, hi = fe.paired_bootstrap_diff(model, base)
    assert lo < d < hi < 0
