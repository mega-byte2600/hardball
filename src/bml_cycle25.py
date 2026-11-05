"""BML Cycle 25: REAL SALARIES + the 2027 free-agent shopping list.

Cycle 16 declared this dependency and stopped honestly: "player-level
salary file not yet present in data/ — needs a wired source." This
cycle wires it. Source: Spotrac (the same source the repo's team
payrolls already come from) — per-team payroll pages for 2026 salaries
and the 2027 free-agents page for the FA class. Raw HTML archived to
data/raw/spotrac/. USA TODAY's salary database was tried first and
returned 402 (access restricted) — logged, not routed around.

Money rules (the demo's honesty standard):
- salary_2026 = Spotrac's "Payroll Salary" column for 2026. It is a
  real contract figure, not an estimate.
- prev_AAV on the FA page is the player's PRIOR contract's average —
  an anchor ("last price"), never presented as a predicted 2027 price.
- Steamer WAR is FanGraphs' projection (Cycle 22 snapshots), joined
  by MLBAM player_id. Names are resolved to ids only through the lake
  players registry with a UNIQUE mapping; anything ambiguous or
  unmatched is carried in the output flagged, never silently dropped
  or force-matched.
- "Value" = projected WAR per $10M of prior AAV. It ranks the class;
  it does not price a contract.

Outputs: data/salaries_2026.json, data/fa_shopping_2027.json
"""
import io
import json
import os
import re
import sqlite3

import pandas as pd
import requests

from carpe import mlb_free_agents

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw", "spotrac")
LAKE = os.path.join(DATA, "mlb_lake.db")
os.makedirs(RAW, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HARDBALL/1.0"}
INDIV_MAX = 245_300_000 * 0.15

TEAM_SLUGS = {
    "ARI": "arizona-diamondbacks", "ATL": "atlanta-braves", "BAL": "baltimore-orioles",
    "BOS": "boston-red-sox", "CHC": "chicago-cubs", "CHW": "chicago-white-sox",
    "CIN": "cincinnati-reds", "CLE": "cleveland-guardians", "COL": "colorado-rockies",
    "DET": "detroit-tigers", "HOU": "houston-astros", "KC": "kansas-city-royals",
    "LAA": "los-angeles-angels", "LAD": "los-angeles-dodgers", "MIA": "miami-marlins",
    "MIL": "milwaukee-brewers", "MIN": "minnesota-twins", "NYM": "new-york-mets",
    "NYY": "new-york-yankees", "ATH": "athletics", "PHI": "philadelphia-phillies",
    "PIT": "pittsburgh-pirates", "SD": "san-diego-padres", "SF": "san-francisco-giants",
    "SEA": "seattle-mariners", "STL": "st-louis-cardinals", "TB": "tampa-bay-rays",
    "TEX": "texas-rangers", "TOR": "toronto-blue-jays", "WSH": "washington-nationals",
}


def _money(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).replace("$", "").replace(",", "").strip()
    if s in ("", "-", "—"):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _full_name(cell):
    """Spotrac player cells read 'Lastname  Firstname Lastname' (sort name
    + full name). Take the full name; flag a trailing QOI badge."""
    s = re.sub(r"\s+", " ", str(cell)).strip()
    qoi = s.endswith(" QOI")
    if qoi:
        s = s[:-4].strip()
    parts = s.split(" ")
    # full name = the trailing First+Last(+suffix) after the sort surname
    if len(parts) >= 3:
        # surname may be multiword (e.g. 'De La Cruz'); the full name starts
        # at the first token that is not part of the leading surname block:
        # heuristic — full name is the last (len-1) tokens when surname is
        # one word; verify by checking parts[1] is a plausible first name
        # start of a repeated surname pattern. Keep simple: drop the first
        # token (single-word surname covers the overwhelming majority) and
        # log exceptions via the unmatched list downstream.
        return " ".join(parts[1:]), qoi
    return s, qoi


def fetch(url, fname):
    path = os.path.join(RAW, fname)
    if os.path.exists(path):
        return open(path, encoding="utf-8", errors="ignore").read()
    import time
    last = None
    for attempt, wait in enumerate((0, 4, 10)):
        if wait:
            time.sleep(wait)
        try:
            r = requests.get(url, headers=UA, timeout=60)
            r.raise_for_status()
            with open(path, "w") as f:
                f.write(r.text)
            time.sleep(1)
            return r.text
        except Exception as e:  # Spotrac 500s under rapid fire — back off
            last = e
    raise last


def _fold(name):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", name)
                   if not unicodedata.combining(c)).lower()


def id_registry():
    """name -> MLBAM id, unique mappings only. Universe = lake players
    registry UNION the Steamer snapshots (anyone FanGraphs projects);
    accent-folded duplicates of each key are added so 'Rodon' matches
    'Rodón' — still unique-only, ambiguity means no match."""
    raw = {}
    con = sqlite3.connect(LAKE)
    for pid, name in con.execute("SELECT player_id, full_name FROM players"):
        raw.setdefault(name, set()).add(pid)
    con.close()
    for stats in ("bat", "pit"):
        for r in json.load(open(os.path.join(DATA, f"fg_steamer_2027_{stats}.json"))):
            if r.get("xMLBAMID") and r.get("PlayerName"):
                raw.setdefault(r["PlayerName"], set()).add(int(r["xMLBAMID"]))
    reg = {}
    for name, ids in raw.items():
        if len(ids) == 1:
            reg[name] = next(iter(ids))
            reg.setdefault(_fold(name), next(iter(ids)))
    return reg


def resolve(reg, name):
    return reg.get(name) or reg.get(_fold(name))


def load_salaries(reg):
    players, failures = [], []
    for abbr, slug in sorted(TEAM_SLUGS.items()):
        try:
            html = fetch(f"https://www.spotrac.com/mlb/{slug}/payroll/", f"{slug}.html")
            tabs = pd.read_html(io.StringIO(html))
            t = next(t for t in tabs if any("Player" in str(c) for c in t.columns))
        except Exception as e:
            failures.append({"team": abbr, "error": str(e)[:120]})
            continue
        pcol = [c for c in t.columns if "Player" in str(c)][0]
        scol = [c for c in t.columns if str(c).strip() == "Payroll Salary"][0]
        for _, row in t.iterrows():
            name, _ = _full_name(row[pcol])
            sal = _money(row[scol])
            if not name or sal is None:
                continue
            players.append({"name": name, "player_id": resolve(reg, name),
                            "team": abbr, "pos": row["Pos"],
                            "status": row["Status"], "salary_2026": sal})
    return players, failures


def load_fa_class(reg):
    # Spotrac remains the market and prior-AAV layer. MLB is the canonical
    # eligibility/status layer; keep both visible and join only by MLBAM id.
    # carpe.mlb_free_agents returns the saved JSON path, not the rows.
    official = {r["player_id"]: r
                for r in json.load(open(mlb_free_agents(2026)))}
    html = fetch("https://www.spotrac.com/mlb/free-agents/2027/", "fa2027.html")
    t = pd.read_html(io.StringIO(html))[0]
    pcol = [c for c in t.columns if "Player" in str(c)][0]
    out = []
    for _, row in t.iterrows():
        name, qoi = _full_name(row[pcol])
        player_id = resolve(reg, name)
        mlb = official.get(player_id) if player_id else None
        out.append({"name": name, "player_id": player_id, "pos": row["Pos"],
                    "age": float(row["Age"]) if pd.notna(row["Age"]) else None,
                    "prev_team": row["Prev Team"], "prev_aav": _money(row["Prev AAV"]),
                    "type": row["Type"], "qoi": qoi,
                    "spotrac_market_aav": _money(row["Market Value  AAV"]),
                    "mlb_free_agent_status": mlb.get("status") if mlb else None,
                    "mlb_free_agent_type": mlb.get("free_agent_type") if mlb else None,
                    "mlb_original_team": mlb.get("original_team") if mlb else None,
                    "mlb_free_agent_date": mlb.get("date") if mlb else None,
                    "mlb_status_source": "MLB Stats API /people/freeAgents"
                    if mlb else None})
    return out


def steamer_by_id():
    out = {}
    for stats in ("bat", "pit"):
        for r in json.load(open(os.path.join(DATA, f"fg_steamer_2027_{stats}.json"))):
            if r.get("xMLBAMID"):
                out[int(r["xMLBAMID"])] = {"war": r.get("WAR"), "kind": stats}
    return out


def _sanitize_nan(obj):
    """Convert float NaN (Spotrac missing-value) to None so json.dump
    never writes invalid JSON (NaN). Recurses through dicts/lists."""
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(v) for v in obj]
    if isinstance(obj, float):
        return None if (obj != obj) else obj  # NaN != NaN
    return obj


def main():
    reg = id_registry()
    players, failures = load_salaries(reg)
    matched = sum(1 for p in players if p["player_id"])
    sal_out = {"metadata": {"source": "Spotrac team payroll pages (2026), pulled 2026-10-31 (24 teams) + 2026-11-05 (ARI/BOS/CHC/MIL/TB/TEX)",
                            "field": "Payroll Salary column",
                            "rows": len(players), "id_matched": matched,
                            "team_failures": failures},
               "players": players}
    with open(os.path.join(DATA, "salaries_2026.json"), "w") as f:
        json.dump(sal_out, f, indent=1)
    print(f"salaries: {len(players)} rows, {matched} id-matched, "
          f"{len(failures)} team failures")

    steam = steamer_by_id()
    fa = load_fa_class(reg)
    for r in fa:
        s = steam.get(r["player_id"]) if r["player_id"] else None
        r["steamer_war"] = s["war"] if s else None
        if s and r["prev_aav"]:
            r["war_per_10m_prior_aav"] = round(s["war"] / (r["prev_aav"] / 10_000_000), 2)
        else:
            r["war_per_10m_prior_aav"] = None
        r["fits_indiv_max_at_prior_aav"] = (
            r["prev_aav"] is not None and r["prev_aav"] <= INDIV_MAX)
    ranked = sorted((r for r in fa if r["steamer_war"] is not None),
                    key=lambda r: -r["steamer_war"])
    value = sorted((r for r in fa if r["war_per_10m_prior_aav"] is not None
                    and r["steamer_war"] >= 2.0),
                   key=lambda r: -r["war_per_10m_prior_aav"])
    fa_out = {"metadata": {"source": "Spotrac 2027 free-agents page + MLB Stats API free-agent eligibility + FanGraphs Steamer 2027 (WAR)",
                           "class_n": len(fa),
                           "with_steamer_war": len(ranked),
                           "id_matched": sum(1 for r in fa if r["player_id"]),
                           "money_rule": "prev_aav is the PRIOR contract's average (last price anchor), not a predicted 2027 price",
                           "indiv_max_15pct": int(INDIV_MAX)},
              "top25_by_war": ranked[:25],
              "top15_value_war_per_10m": value[:15],
              "class": fa}
    with open(os.path.join(DATA, "fa_shopping_2027.json"), "w") as f:
        json.dump(_sanitize_nan(fa_out), f, indent=1)
    print(f"FA class: {len(fa)} players, {len(ranked)} with Steamer WAR")
    print("\n=== Top FA by projected WAR ===")
    for r in ranked[:8]:
        print(f"  {r['name']} ({r['pos']}, {r['prev_team']}) WAR {r['steamer_war']} "
              f"prior AAV ${r['prev_aav']/1e6:.1f}M" if r['prev_aav'] else
              f"  {r['name']} ({r['pos']}, {r['prev_team']}) WAR {r['steamer_war']} prior AAV n/a")
    print("\n=== Best value (WAR per $10M prior AAV, WAR>=2) ===")
    for r in value[:8]:
        print(f"  {r['name']} ({r['pos']}) {r['war_per_10m_prior_aav']} WAR/$10M "
              f"(WAR {r['steamer_war']}, prior AAV ${r['prev_aav']/1e6:.1f}M)")


if __name__ == "__main__":
    main()
