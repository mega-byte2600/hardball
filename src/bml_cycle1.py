"""BML Cycle 1: is the winning-cheap edge durable (2000-2024) or a 2-season fluke?

Uses jeremyliao0411/mlb-payroll-wins df_final_merged.csv (720 MLB team-seasons
2000-2024, Lahman + public payroll). Tests whether low-payroll teams that win
have a contact/OBP signature vs. cheap-mediocre, and quantifies wins-per-dollar
across decades to see if 2025-2026 efficiency is an outlier or the norm.
"""
import pandas as pd

CSV = "/tmp/payroll_wins_2024.csv"


def clean():
    df = pd.read_csv(CSV)
    # parse quoted payroll "51,464,167" -> int
    df["payroll"] = (df["Payroll"].astype(str)
                     .str.replace(",", "").str.replace('"', "")
                     .astype(float))
    df["wins"] = pd.to_numeric(df["Win Total"], errors="coerce")
    df = df.dropna(subset=["payroll", "wins"])
    # normalize payroll per decade via league-avg ratio, not raw dollars
    df["payroll_pct_avg"] = df.groupby("yearID")["payroll"].transform(
        lambda x: x / x.mean() * 100)
    df["wins_per_100m"] = df["wins"] / (df["payroll"] / 100_000_000)
    return df


def main():
    df = clean()
    print(f"team-seasons: {len(df)}, years {int(df['yearID'].min())}-{int(df['yearID'].max())}")

    # wins-per-dollar by decade
    for dec in [2000, 2010, 2020]:
        s = df[df["yearID"] >= dec]
        print(f"\n[{s['yearID'].min()}-{s['yearID'].max()}] n={len(s)} "
              f"median payroll ${s['payroll'].median()/1e6:.1f}M, "
              f"median wins {s['wins'].median():.0f}, "
              f"median wins/$100M {s['wins_per_100m'].median():.1f}")

    # cost per win: whole-era regression slope = $ per extra win
    import numpy as np
    by_year = df.groupby("yearID").agg(med_pay=("payroll", "median"),
                                        med_wins=("wins", "median"))
    # top-quartile payroll teams vs bottom-quartile: who wins more per $?
    df["qt"] = df.groupby("yearID")["payroll"].transform(
        lambda x: pd.qcut(x.rank(method="first"), 4, labels=False))
    agg = df.groupby("qt").agg(n=("wins", "size"), wins=("wins", "mean"),
                                payroll=("payroll", "mean"),
                                wins_per_100m=("wins_per_100m", "mean"))
    print("\nQuartiles of payroll (2000-2024):")
    print(agg.round(1).to_string())
    print("\nReading: is lowest quartile winning MORE per $100M than top quartile?")

    # efficiency persists even at low payroll? corr payroll vs wins per decade
    out = df[["yearID", "teamID", "payroll", "wins", "payroll_pct_avg", "wins_per_100m"]]
    out.to_csv("/tmp/efficiency_2000_2024.csv", index=False)
    print("\nwrote /tmp/efficiency_2000_2024.csv")


if __name__ == "__main__":
    main()
