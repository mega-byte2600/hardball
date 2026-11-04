import json
import sys
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from scipy import stats


def load(prefix, season):
    cached = Path(f"{prefix}{season}.json")
    if cached.exists():
        return json.loads(cached.read_text())
    base = "https://statsapi.mlb.com/api/v1/"
    if prefix == "s":
        endpoint = f"standings?leagueId=103,104&season={season}&standingsTypes=regularSeason"
    else:
        group = {"f": "fielding", "p": "pitching"}[prefix]
        endpoint = f"teams/stats?stats=season&group={group}&sportIds=1&season={season}&gameType=R&limit=100"
    with urlopen(base + endpoint, timeout=30) as response:
        return json.load(response)


records = []
names = []
for year in range(2011, 2026):
    field = load("f", year)["stats"][0]["splits"]
    standings = [row for division in load("s", year)["records"]
                 for row in division["teamRecords"]]
    by_id = {row["team"]["id"]: row for row in standings}
    pitching = {row["team"]["id"]: row["stat"]
                for row in load("p", year)["stats"][0]["splits"]}
    assert len(field) == len(standings) == len(by_id) == 30
    assert set(by_id) == {row["team"]["id"] for row in field}
    assert set(by_id) == set(pitching)
    for row in field:
        club = row["team"]["id"]
        f, s = row["stat"], by_id[club]
        games = s["wins"] + s["losses"]
        assert f["gamesPlayed"] - games in (0, 1), (year, club, games, f["gamesPlayed"])
        if games != f["gamesPlayed"]:
            print("fielding includes extra game without standings decision", year, club)
        assert f["chances"] == f["putOuts"] + f["assists"] + f["errors"]
        p = pitching[club]
        names.append(row["team"]["name"])
        records.append((year, club, games, 162*s["wins"]/games,
                        162*f["errors"]/f["gamesPlayed"]/10, 100*f["errors"]/f["chances"],
                        s["runsScored"]/f["gamesPlayed"],
                        *(p[k]/p["battersFaced"] for k in
                          ("strikeOuts", "baseOnBalls", "homeRuns"))))

d = pd.DataFrame(records, columns=["season", "club", "games", "wins162",
                                   "errors10", "rate", "offense", "k", "bb", "hr"])


def fit(frame, predictor, scale=1, controls=()):
    indicators = pd.get_dummies(frame[["season", "club"]].astype(str), drop_first=True)
    x = np.column_stack([np.ones(len(frame)), frame[predictor],
                         frame[list(controls)], indicators]).astype(float)
    y = frame.wins162.to_numpy()
    coef = np.linalg.lstsq(x, y, rcond=None)[0]
    bread = np.linalg.inv(x.T @ x)
    scores = x * (y - x @ coef)[:, None]

    def cluster(keys):
        grouped = pd.DataFrame(scores).groupby(keys.to_numpy()).sum().to_numpy()
        g = len(grouped)
        n, k = x.shape
        return (grouped.T @ grouped) * (g/(g-1)) * ((n-1)/(n-k))

    club = cluster(frame.club)
    season = cluster(frame.season)
    cell = cluster(pd.Series(np.arange(len(frame))))
    cov = bread @ (club + season - cell) @ bread
    se = np.sqrt(cov[1, 1])
    dof = min(frame.club.nunique(), frame.season.nunique()) - 1
    delta = -scale * coef[1]
    half = scale * stats.t.ppf(.975, dof) * se
    return np.round([delta, delta-half, delta+half], 3).tolist()


print("coverage", len(d), d.season.nunique(), d.club.nunique())
for predictor in ("errors10", "rate"):
    print(predictor, "Pearson", stats.pearsonr(d[predictor], d.wins162).statistic,
          "Spearman", stats.spearmanr(d[predictor], d.wins162).statistic)
print("10 fewer errors", fit(d, "errors10"))
print("exclude 2020", fit(d[d.season != 2020], "errors10"))
print("0.2 fewer errors per 100 chances", fit(d, "rate", .2))
print("2011–2019", fit(d[d.season < 2020], "errors10"))
print("2021–2025", fit(d[d.season > 2020], "errors10"))
controls = ("offense", "k", "bb", "hr")
print("adjusted", fit(d, "errors10", controls=controls))
print("adjusted, excluding 2020", fit(d[d.season != 2020], "errors10", controls=controls))
print("adjusted, per 100 chances", fit(d, "rate", .2, controls=controls))
if len(sys.argv) > 1:
    trend = np.polyfit(d.errors10 * 10, d.wins162, 1)
    payload = {
        "clubs": names,
        "points": [[int(y), round(x*10, 2), round(w, 2)]
                   for y, x, w in zip(d.season, d.errors10, d.wins162)],
        "trend": trend.tolist(),
        "models": [
            ["Club and season", fit(d, "errors10")],
            ["Add offense and pitching", fit(d, "errors10", controls=controls)],
            ["Also exclude 2020", fit(d[d.season != 2020], "errors10", controls=controls)],
        ],
    }
    Path(sys.argv[1]).write_text(json.dumps(payload, separators=(",", ":")) + "\n")
