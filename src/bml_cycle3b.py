"""Cycle 3 (final attempt): team xwOBA from pitch CSV using home/away logic.

Statcast pitch rows carry 'home_team'/'away_team' (3-letter codes). For the
BATTING side we cannot tell home vs away from the row alone, so we use the
batter's PRIMARY team is not in-row. Instead: aggregate xwOBA by VENUE team is
wrong. So we fall back to the DEFENSIVE proxy: use 'away_team' as the batting
team when we can't know. To avoid a wrong result, we ONLY report the per-player
leaderboard route result if roster mapping succeeded; otherwise state N/A.
"""
import sys, os
import pandas as pd
base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base)
import model_p6  # noqa

def main():
    csv = os.path.join(base, "..", "data", "raw", "statcast_2026.csv")
    df = pd.read_csv(csv, low_memory=False)
    print("total pitch rows:", len(df))
    teams = sorted(set([c for c in df.columns if 'Team' in c]))
    print("team columns:", teams)
    print("xwoba present:", 'xwoba' in df.columns,
          "rows dropna xwoba:", df['xwoba'].notna().sum() if 'xwoba' in df.columns else 0)
    # If a batting-team field doesn't exist, we cannot attribute honestly.
    if not any('atter' in c or c in ('home_team','away_team') for c in df.columns):
        print("NO reliable batting-team field -> team attribution not possible here; "
              "use per-player leaderboard + roster route instead.")
    else:
        print("field present; would aggregate.")

if __name__ == "__main__":
    main()
