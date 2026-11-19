import pandas as pd

import payroll


def test_parsers():
    assert payroll._dollars("$245,300,000") == 245_300_000
    assert payroll._wins("97-65") == 97


def test_payroll_frame_covers_2011_2026_with_30_teams_in_2026():
    df = payroll.load_payroll_frame()
    assert df["season"].min() == 2011 and df["season"].max() == 2026
    assert df[df["season"] == 2026]["team"].nunique() == 30
    assert (df["payroll"] > 0).all()


def test_efficiency_table_math_and_order():
    df = pd.DataFrame({"season": [2026] * 3, "team": ["A", "B", "C"],
                       "wins": [90, 81, 0], "payroll": [100e6, 200e6, 50e6]})
    t = payroll.build_efficiency_table(df)
    assert list(t["team"]) == ["A", "B"]  # zero-win rows dropped, sorted by wins per $100M
    assert t.iloc[0]["wins_per_100m"] == 90 and t.iloc[0]["cost_per_win"] == 100e6 / 90
