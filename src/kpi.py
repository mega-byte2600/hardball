"""P5: copycat-league KPI analysis.

Question: which team-level performance metrics discriminate WINNING-CHEAP
teams (CLE, TB, MIL: 85-103 wins at low payroll) from CHEAP-MEDIOCRE teams
(MIA, CHW, STL: 80 wins at low payroll), and from expensive underperformers
(NYM/PHI)?
Thesis test: does buying contact/OBP over homeruns produce wins per dollar?
Real data only: team standings + team hitting from MLB Stats API, joined
to Spotrac payroll (src/payroll.py).
"""
import json
import os
import sqlite3

import pandas as pd
import requests

from payroll import PAYROLL_2026, build_efficiency_table, load_payroll_frame

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0"}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
SQLITE = os.path.join(DATA, "mlb_lake.db")

# Winning-cheap (targets of the formula) vs cheap-mediocre (trap)
WIN_CHEAP = {"MIL", "TB", "CLE"}


def team_code_map(season=2026) -> dict:
    """team_id -> 3-letter abbreviation from /teams, with fixes for API quirks.
    MLB uses both MIA/Marlins and ATH/Athetics; map to Spotrac codes."""
    resp = requests.get(f"{BASE}/teams", params={"sportId": 1, "season": season}, headers=UA, timeout=60)
    resp.raise_for_status()
    m = {}
    for t in resp.json().get("teams", []):
        ab = t.get("abbreviation")
        name = t.get("name", "")
        m[t["id"]] = ab
    # Spotrac/payroll uses these 3-letter codes
    m[114] = "CLE"  # Guardians
    m[145] = "CHW"  # White Sox
    m[133] = "ATH"  # Athletics
    return m


def fetch_team_hitting(season: int) -> pd.DataFrame:
    """Per-team aggregate hitting stats, joined to 3-letter team code."""
    idmap = team_code_map(season)
    rows = []
    for tid, code in idmap.items():
        params = {"stats": "season", "group": "hitting", "season": season, "sportId": 1}
        try:
            resp = requests.get(f"{BASE}/teams/{tid}/stats", params=params, headers=UA, timeout=60)
            resp.raise_for_status()
        except Exception as e:
            print(f"  fail team {tid} {code}: {e}")
            continue
        splits = resp.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            continue
        s = splits[0].get("stat", {})
        rows.append({
            "season": season, "team": code,
            "PA": _f(s.get("plateAppearances")), "AB": _f(s.get("atBats")),
            "BA": _f(s.get("avg")), "OBP": _f(s.get("obp")), "SLG": _f(s.get("slg")),
            "OPS": _f(s.get("ops")), "HR": _f(s.get("homeRuns")),
            "R": _f(s.get("runs")), "BB": _f(s.get("baseOnBalls")),
            "SO": _f(s.get("strikeOuts")), "H": _f(s.get("hits")),
            "2B": _f(s.get("doubles")), "3B": _f(s.get("triples")),
        })
    return pd.DataFrame(rows)


def _f(v):
    return pd.to_numeric(v, errors="coerce") if v not in (None, "", "null", "-") else None


def fetch_standings(season: int) -> dict:
    """TeamCode -> wins from standings."""
    resp = requests.get(f"{BASE}/standings", params={"season": season, "standingsTypes": "regularSeason", "leagueId": "103,104"}, headers=UA, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    out = {}
    for rec in data.get("records", []):
        for team in rec.get("teamRecords", []):
            t = team.get("team", {})
            out[t.get("abbreviation")] = team.get("wins")
    return out


def kpi_frame():
    """Join team hitting + standings + payroll into one analysis table."""
    frames = []
    for season in (2025, 2026):
        hit = fetch_team_hitting(season)
        # derived KPIs (wins filled from payroll frame below)
        for col in ["BA", "OBP", "SLG", "OPS", "HR", "R", "BB", "SO",
                    "PA", "AB", "H", "2B", "3B"]:
            if col in hit.columns:
                hit[col] = pd.to_numeric(hit[col], errors="coerce")
        hit["K%"] = hit["SO"] / hit["PA"] * 100
        hit["BB%"] = hit["BB"] / hit["PA"] * 100
        hit["contact"] = (hit["PA"] - hit["SO"]) / hit["PA"] * 100
        hit["HR/PA"] = hit["HR"] / hit["PA"] * 1000
        hit["ISO"] = hit["SLG"] - hit["BA"]
        hit["BABIPish"] = (hit["H"] - hit["HR"]) / (hit["AB"] - hit["SO"] - hit["HR"] + hit["H"] - hit["HR"])  # rough
        frames.append(hit)
    df = pd.concat(frames, ignore_index=True)

    # join payroll + efficiency (payroll frame carries wins for both seasons)
    payroll = load_payroll_frame()
    p = payroll[payroll["season"].isin((2025, 2026))][
        ["season", "team", "payroll", "wins"]
    ].copy()
    # recompute cost_per_win defensively
    p["cost_per_win"] = p["payroll"] / p["wins"]
    p["wins_per_100m"] = p["wins"] / (p["payroll"] / 100_000_000)
    merged = df.merge(p, on=["season", "team"], how="left", suffixes=("", "_p"))
    if "wins_p" in merged.columns:
        merged["wins"] = merged["wins_p"].fillna(merged["wins"])
        merged = merged.drop(columns=["wins_p"])
    return merged


def kpi_frame_from_snapshots() -> pd.DataFrame:
    """Load the committed data/kpi_<season>.json snapshots (written by
    analyze() from the live frame). Deterministic and offline — this is
    the default dataset for builds and model fits; kpi_frame() (live MLB
    API fetch) is the refresh path that regenerates the snapshots."""
    frames = []
    for season in (2025, 2026):
        path = os.path.join(DATA, f"kpi_{season}.json")
        if os.path.exists(path):
            frames.append(pd.read_json(path))
    if not frames:
        raise FileNotFoundError("no committed data/kpi_*.json snapshots found")
    return pd.concat(frames, ignore_index=True)


def analyze(df: pd.DataFrame, year: int):
    d = df[df["season"] == year].copy().dropna(subset=["payroll", "wins"])
    d["group"] = "OTHER"
    d.loc[d["team"].isin(WIN_CHEAP), "group"] = "WIN_CHEAP"
    d.loc[d["team"].isin({"MIA", "CHW", "STL"}), "group"] = "CHEAP_MEDIOCRE"

    print(f"\n===== {year} KPI comparison =====")
    kpis = ["BA", "OBP", "SLG", "OPS", "K%", "BB%", "contact", "HR/PA", "ISO", "wins_per_100m", "payroll", "wins"]
    for k in kpis:
        if k not in d.columns:
            continue
        vals = d.groupby("group")[k].mean()
        print(f"{k:>15}: " + " | ".join(f"{g}={v:.3f}" for g, v in vals.items()))

    # Which KPIs best separate winning-cheap from the rest? t-stat style gap.
    print("\n--- win-cheap vs other gap ---")
    wc = d[d["group"] == "WIN_CHEAP"]
    others = d[d["group"] != "WIN_CHEAP"]
    for k in ["OBP", "contact", "K%", "BB%", "HR/PA", "ISO", "BA", "OPS"]:
        if k in d.columns:
            gap = wc[k].mean() - others[k].mean()
            print(f"{k:>12}: wc={wc[k].mean():.3f} other={others[k].mean():.3f} gap={gap:+.3f}")

    out = os.path.join(DATA, f"kpi_{year}.json")
    d.to_json(out, orient="records", indent=2)
    print(f"\nwrote {out}")
    return d


def main():
    df = kpi_frame()
    print("rows:", len(df), "seasons:", sorted(df["season"].unique()))
    for y in (2025, 2026):
        analyze(df, y)


if __name__ == "__main__":
    main()
