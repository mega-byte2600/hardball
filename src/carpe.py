"""CarpeData connectors for HARDBALL (2026-10-31).

One module, every open/free source we actually use, each fetcher writing
its raw payload to data/raw/ (gitignored) and a slim committed snapshot
to data/. Keyless throughout. Sources probed 2026-10-31; the kept/dropped
scorecard lives in docs/CARPE_SCORECARD.md.

Sources:
- Baseball Savant leaderboards (CSV): expected stats (xwOBA), batted
  ball (EV / barrels / sweet spot), bat tracking (bat speed / squared-up
  / blasts — Hawk-Eye, 2024+ only, and ONLY via the date-range parameter
  form; the bare ?year= form silently returns the current season for
  every year), sprint speed, arm strength. Savant player_id IS the
  MLBAM id, so joins are by id, never by name.
- FanGraphs API (JSON): Steamer projections (benchmark + WAR). The
  Steamer rows carry xMLBAMID <-> FanGraphs playerid for every player,
  which makes them our crosswalk source (the Chadwick register's flat
  file 404s at its old path, and the FG leaders endpoint paginates at
  50 rows; Steamer covers 100% of the lake universe).
- MLB Stats API people endpoint: real birthdates/ages for every player
  in the lake (Marcel's aging step was a stub reading a hardcoded dict).
"""
import csv
import io
import json
import os

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw")
os.makedirs(RAW, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (HARDBALL/1.0 carpe-data)"}
SAVANT = "https://baseballsavant.mlb.com"
FG = "https://www.fangraphs.com/api"
MLB = "https://statsapi.mlb.com/api/v1"

def mlb_free_agents(season):
    """Fetch MLB's official free-agent eligibility list for a completed season.

    This is the roster-status layer for the free-agent tracker. It is kept
    separate from Spotrac market estimates: MLB supplies eligibility,
    original club, and status; Spotrac supplies prior AAV and market value.
    The join key is MLBAM player_id, never a name string.
    """
    r = requests.get(
        f"{MLB}/people/freeAgents",
        params={"season": str(season)},
        headers=UA,
        timeout=60,
    )
    r.raise_for_status()
    rows = []
    for item in r.json().get("freeAgents", []):
        player = item.get("player") or {}
        original = item.get("originalTeam") or {}
        if not player.get("id"):
            continue
        rows.append({
            "player_id": int(player["id"]),
            "name": player.get("fullName"),
            "original_team_id": original.get("id"),
            "original_team": original.get("name"),
            "status": item.get("status"),
            "free_agent_type": item.get("type"),
            "date": item.get("date"),
        })
    rows.sort(key=lambda row: (row.get("name") or "").lower())
    return _save_json(f"mlb_free_agents_{season}.json", rows)


def _save_raw(name, text):
    with open(os.path.join(RAW, name), "w") as f:
        f.write(text)


def _save_json(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
    print(f"wrote {path} ({len(obj)} rows)")
    return path


def _savant_csv(url, raw_name):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    _save_raw(raw_name, r.text)
    rows = list(csv.DictReader(io.StringIO(r.text.lstrip("\ufeff"))))
    return rows


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def savant_expected(season):
    rows = _savant_csv(
        f"{SAVANT}/expected_statistics?type=batter&year={season}&position=&team=&min=25&csv=true",
        f"savant_expected_{season}.csv")
    out = [{"player_id": int(r["player_id"]), "name": r["last_name, first_name"],
            "pa": _num(r["pa"]), "woba": _num(r["woba"]), "est_woba": _num(r["est_woba"]),
            "est_ba": _num(r["est_ba"]), "est_slg": _num(r["est_slg"])}
           for r in rows if r.get("player_id")]
    return _save_json(f"savant_expected_{season}.json", out)


def savant_bat_tracking(season):
    """Bat tracking exists only from 2024 (Hawk-Eye). The endpoint ONLY
    honors the date-range parameter form; ?year= is silently ignored and
    returns the current season for every requested year (verified
    2026-10-31: four 'yearly' pulls came back byte-identical)."""
    if season < 2024:
        print(f"bat tracking: no {season} data (Hawk-Eye starts 2024) — skipped")
        return None
    rows = _savant_csv(
        f"{SAVANT}/leaderboard/bat-tracking?dateStart={season}-03-01"
        f"&dateEnd={season}-11-01&gameType=Regular&minSwings=25"
        f"&minGroupSwings=1&seasonStart={season}&seasonEnd={season}"
        f"&type=batter&csv=true",
        f"savant_bat_tracking_{season}.csv")
    out = [{"player_id": int(r["id"]), "name": r["name"],
            "swings_competitive": _num(r["swings_competitive"]),
            "avg_bat_speed": _num(r["avg_bat_speed"]),
            "hard_swing_rate": _num(r["hard_swing_rate"]),
            "squared_up_per_swing": _num(r["squared_up_per_swing"]),
            "squared_up_per_bat_contact": _num(r["squared_up_per_bat_contact"]),
            "blast_per_swing": _num(r["blast_per_swing"]),
            "blast_per_bat_contact": _num(r["blast_per_bat_contact"]),
            "swing_length": _num(r["swing_length"])}
           for r in rows if r.get("id")]
    return _save_json(f"savant_bat_tracking_{season}.json", out)


def savant_batted_ball(season):
    """Exit velocity / barrels leaderboard (the statcast_leaderboard CSV)."""
    rows = _savant_csv(
        f"{SAVANT}/statcast_leaderboard?year={season}&abs=25&type=batter&min=q&csv=true",
        f"savant_batted_ball_{season}.csv")
    out = [{"player_id": int(r["player_id"]), "name": r["last_name, first_name"],
            "bbe": _num(r["attempts"]), "avg_ev": _num(r["avg_hit_speed"]),
            "ev50": _num(r["ev50"]), "ev95_pct": _num(r["ev95percent"]),
            "max_ev": _num(r["max_hit_speed"]),
            "sweet_spot_pct": _num(r["anglesweetspotpercent"]),
            "barrels": _num(r["barrels"]), "barrel_pct": _num(r["brl_percent"]),
            "barrel_pa": _num(r["brl_pa"])}
           for r in rows if r.get("player_id")]
    return _save_json(f"savant_batted_ball_{season}.json", out)


def savant_sprint(season):
    rows = _savant_csv(
        f"{SAVANT}/leaderboard/sprint_speed?year={season}&position=&team=&min=25&csv=true",
        f"savant_sprint_{season}.csv")
    out = [{"player_id": int(r["player_id"]), "name": r["last_name, first_name"],
            "age": _num(r["age"]), "sprint_speed": _num(r["sprint_speed"]),
            "hp_to_1b": _num(r["hp_to_1b"])}
           for r in rows if r.get("player_id")]
    return _save_json(f"savant_sprint_{season}.json", out)


def savant_arm(season):
    rows = _savant_csv(
        f"{SAVANT}/leaderboard/arm-strength?year={season}&position=&team=&min=25&csv=true",
        f"savant_arm_{season}.csv")
    out = [{"player_id": int(r["player_id"]), "name": r["fielder_name"],
            "arm_strength": _num(r["arm_strength_max"] if "arm_strength_max" in r else r.get("max_arm_strength"))}
           for r in rows if r.get("player_id")]
    return _save_json(f"savant_arm_{season}.json", out)


def fg_steamer(stats="bat"):
    r = requests.get(f"{FG}/projections",
                     params={"type": "steamer", "stats": stats, "pos": "all",
                             "team": 0, "players": 0, "lg": "all"},
                     headers=UA, timeout=90)
    r.raise_for_status()
    _save_raw(f"fg_steamer_2027_{stats}.json", r.text)
    rows = r.json()
    keep = ["playerid", "xMLBAMID", "PlayerName", "Team", "PA", "IP", "OBP", "SLG",
            "AVG", "wOBA", "wRC+", "WAR", "ERA", "WHIP", "K/9", "BB/9"]
    out = [{k: row.get(k) for k in keep if k in row} for row in rows]
    return _save_json(f"fg_steamer_2027_{stats}.json", out)


def player_xwalk_and_ages(lake_ids):
    """Crosswalk (MLBAM <-> FanGraphs) built from the Steamer snapshots
    (every row carries both ids; coverage of the lake universe verified
    379/379 on 2026-10-31), and real ages/birthdates from the MLB people
    endpoint. Run fg_steamer() first."""
    xwalk = {}
    for stats in ("bat", "pit"):
        path = os.path.join(DATA, f"fg_steamer_2027_{stats}.json")
        for row in json.load(open(path)):
            mid = row.get("xMLBAMID")
            if mid:
                xwalk[int(mid)] = {"mlbam_id": int(mid),
                                   "name": row.get("PlayerName"),
                                   "fg_id": row.get("playerid")}
    _save_json("player_xwalk.json",
               [xwalk[k] for k in sorted(xwalk) if k in lake_ids])

    ages = {}
    ids = sorted(lake_ids)
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        r = requests.get(f"{MLB}/people",
                         params={"personIds": ",".join(str(x) for x in chunk)},
                         headers=UA, timeout=60)
        r.raise_for_status()
        for p in r.json().get("people", []):
            ages[p["id"]] = {"mlbam_id": p["id"], "name": p.get("fullName"),
                             "birth_date": p.get("birthDate"),
                             "current_age": p.get("currentAge")}
    _save_json("player_ages.json", [ages[k] for k in sorted(ages)])
    return xwalk, ages


def main():
    import sqlite3
    con = sqlite3.connect(os.path.join(DATA, "mlb_lake.db"))
    lake_ids = {r[0] for r in con.execute(
        "SELECT DISTINCT player_id FROM stat_lines WHERE player_id IS NOT NULL")}
    con.close()
    print(f"lake player universe: {len(lake_ids)} ids")
    for season in (2023, 2024, 2025, 2026):
        savant_expected(season)
        savant_batted_ball(season)
        savant_bat_tracking(season)
        savant_sprint(season)
    savant_arm(2026)
    fg_steamer("bat")
    fg_steamer("pit")
    player_xwalk_and_ages(lake_ids)
    mlb_free_agents(2026)


if __name__ == "__main__":
    main()
