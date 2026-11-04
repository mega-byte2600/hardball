import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln
from scipy.stats import beta


def read(path):
    return json.loads(path.read_text())


output = {}
for season in (2026,):
    roster_ids = {r["person"]["id"] for p in Path().glob(f"roster-{season}-*.json")
                  for r in read(p)["roster"]}
    people = [r for p in Path().glob(f"people-{season}-*.json") for r in read(p)["people"]]
    assert len(list(Path().glob(f"roster-{season}-*.json"))) == 30
    assert len(people) == len(roster_ids) and {r["id"] for r in people} == roster_ids
    groups = defaultdict(list)
    for person in people:
        positions = defaultdict(list)
        for group in person.get("stats", []):
            for split in group.get("splits", []):
                if split.get("position") and split["season"] == str(season):
                    positions[split["position"]["abbreviation"]].append(split)
        for position, splits in positions.items():
            stints = [s for s in splits if s.get("team")]
            aggregate = [s for s in splits if not s.get("team")]
            assert len(aggregate) <= 1
            assert len({s["team"]["id"] for s in stints}) == len(stints)
            for s in splits:
                stat = s["stat"]
                assert stat["chances"] == stat["assists"] + stat["putOuts"] + stat["errors"]
            if aggregate and stints:
                assert all(aggregate[0]["stat"][k] == sum(s["stat"][k] for s in stints)
                           for k in ("errors", "chances")), (season, person["id"], position)
            chosen = aggregate or stints
            errors, chances = (sum(s["stat"][k] for s in chosen) for k in ("errors", "chances"))
            if chances and position in ("P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"):
                groups[position].append([person["fullName"], errors, chances])
    output[season] = {}
    for pos, rows in sorted(groups.items()):
        _, errors, chances = zip(*rows)
        e, n = np.array(errors), np.array(chances)
        mean = e.sum() / n.sum()
        def objective(log_params):
            a, b = np.exp(log_params)
            return -(betaln(a+e, b+n-e) - betaln(a, b)).sum()
        result = minimize(objective, np.log([mean*100, (1-mean)*100]),
                          method="L-BFGS-B", bounds=[(-7, 12), (-7, 12)])
        assert result.success, (season, pos, result.message)
        a, b = np.exp(result.x)
        est = 100 * (a+e) / (a+b+n)
        lo, hi = beta.ppf([[.025], [.975]], a+e, b+n-e) * 100
        ranked = [row + [round(float(x), 4) for x in (m, l, h)]
                  for row, m, l, h in zip(rows, est, lo, hi)]
        output[season][pos] = {"average": round(100*mean, 4), "rows": ranked}
        print(season, pos, len(rows), int(e.sum()), int(n.sum()))
    teams = read(Path(f"f{season}.json"))["stats"][0]["splits"]
    assert len({row["team"]["id"] for row in teams}) == 30
    for index, field in ((1, "errors"), (2, "chances")):
        assert sum(row[index] for group in output[season].values() for row in group["rows"]) == sum(
            row["stat"][field] for row in teams
        ), (season, field)
Path(sys.argv[1]).write_text(json.dumps(output, separators=(",", ":")) + "\n")
