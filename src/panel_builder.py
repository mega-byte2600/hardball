"""HARDBALL PANEL BUILDER: many-season team dataset (2011-2026).

The real fix for '58 rows is thin': expand from 2 seasons to a proper
panel of ~480 real team-seasons. MLB Stats API serves team hitting +
standings back to 2008; Spotrac payroll (via load_payroll_frame) covers
2011-2025; 2026 live payroll is in PAYROLL_2026.

Builds a long, tidy panel where an owner-facing model is actually
statistically grounded, and writes it to data/panel_2011_2026.csv (+ the
same KPIs each cycle used). RATE-LIMITED friendly: caches per-season JSON
to data/raw/panel/ so it only hits the API once per season ever.
"""
import json
import os
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpi import _f, team_code_map
from payroll import PAYROLL_2026, load_payroll_frame

BASE = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "HARDBALL/1.0"}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw", "panel")

SEASONS = list(range(2011, 2027))  # 2011-2026 inclusive; payroll starts 2011
SLEEP = 0.25  # polite delay between team calls


def _cache(season, kind, fn):
    """Hit the API once per (season, kind); reuse cached JSON afterward."""
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, f"{season}_{kind}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    data = fn()
    with open(path, "w") as f:
        json.dump(data, f)
    time.sleep(SLEEP)
    return data


def hitting_season(season):
    def _fetch():
        idmap = team_code_map(season)
        rows = []
        for tid, code in idmap.items():
            try:
                r = requests.get(f"{BASE}/teams/{tid}/stats",
                                 params={"stats": "season", "group": "hitting",
                                         "season": season, "sportId": 1},
                                 headers=UA, timeout=60)
                splits = r.json().get("stats", [{}])[0].get("splits", [])
            except Exception as e:
                print(f"  ERR {code} {season}: {e}"); continue
            if not splits:
                continue
            s = splits[0].get("stat", {})
            rows.append({"season": season, "team": code,
                         "PA": _f(s.get("plateAppearances")), "AB": _f(s.get("atBats")),
                         "BA": _f(s.get("avg")), "OBP": _f(s.get("obp")),
                         "SLG": _f(s.get("slg")), "OPS": _f(s.get("ops")),
                         "HR": _f(s.get("homeRuns")), "R": _f(s.get("runs")),
                         "BB": _f(s.get("baseOnBalls")), "SO": _f(s.get("strikeOuts")),
                         "H": _f(s.get("hits")), "2B": _f(s.get("doubles")),
                         "3B": _f(s.get("triples"))})
            time.sleep(SLEEP)
        return rows
    return _cache(season, "hitting", _fetch)


def standings_season(season):
    def _fetch():
        idmap = team_code_map(season)
        rows = []
        r = requests.get(f"{BASE}/standings",
                         params={"season": season, "standingsTypes": "regularSeason",
                                 "leagueId": "103,104"}, headers=UA, timeout=60)
        for rec in r.json().get("records", []):
            for tr in rec.get("teamRecords", []):
                code = idmap.get(tr.get("team", {}).get("id"))
                if not code:
                    continue
                rows.append({"season": season, "team": code,
                             "wins": tr.get("wins"), "losses": tr.get("losses"),
                             "RS": tr.get("runsScored"), "RA": tr.get("runsAllowed")})
        return rows
    return _cache(season, "standings", _fetch)


def build_panel():
    all_rows = []
    for season in SEASONS:
        hit = pd.DataFrame(hitting_season(season))
        sta = pd.DataFrame(standings_season(season))
        if hit.empty or sta.empty:
            print(f"  skip {season}: no data"); continue
        m = hit.merge(sta, on=["season", "team"], how="left")
        all_rows.append(m)
        print(f"  {season}: {len(m)} teams")
    df = pd.concat(all_rows, ignore_index=True)

    # derived KPIs
    for col in ["BA", "OBP", "SLG", "OPS", "HR", "R", "BB", "SO", "PA", "AB", "H"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["K%"] = df["SO"] / df["PA"] * 100
    df["BB%"] = df["BB"] / df["PA"] * 100
    df["contact"] = (df["PA"] - df["SO"]) / df["PA"] * 100
    df["HR/PA"] = df["HR"] / df["PA"] * 1000
    df["ISO"] = df["SLG"] - df["BA"]
    df["RD"] = df["RS"] - df["RA"]

    # payroll (2011-2025 from Spotrac files; 2026 live)
    payroll = load_payroll_frame()
    p = payroll[payroll["season"].isin(SEASONS)][["season", "team", "payroll"]].copy()
    p26 = pd.DataFrame([{"season": 2026, "team": t, "payroll": v}
                        for t, v in PAYROLL_2026.items()])
    p = pd.concat([p, p26], ignore_index=True)
    df = df.merge(p, on=["season", "team"], how="left")

    out = os.path.join(DATA, "panel_2011_2026.csv")
    df.to_csv(out, index=False)
    print(f"\nPANEL: {len(df)} team-seasons {sorted(df['season'].unique())} -> {out}")
    return df


if __name__ == "__main__":
    build_panel()
