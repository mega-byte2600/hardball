"""BML Cycle 11: add PITCHER projections to the roster tool (currently hitter-only).

Builds Marcel-style 2027 pitcher projections from REAL 2025+2026 lake data
(IP, ERA, K/9, BB/9, WHIP), regression-to-mean, IP-availability scaling.
Prometheus FF: completes the roster tool so an owner sees BOTH halves of
the winning-cheap formula — contact/OBP bats AND low-walk arms.
Outputs: data/projections_2027_pitchers.json + health-adjusted version.
"""
import json
import os
import re
import sqlite3

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")
RAW = os.path.join(DATA, "raw")

LEAGUE = {"ERA": 4.00, "WHIP": 1.28, "K9": 8.8, "BB9": 3.1}
IL_DAYS = {"10-day injured list": 10, "60-day": 60, "15-day injured list": 15,
           "10-day": 10, "15-day": 15, "60-day injured list": 60}


def load_pitchers():
    con = sqlite3.connect(LAKE)
    rows = []
    for season, name, team, sjson in con.execute(
            "SELECT season,name,team,stat_json FROM stat_lines WHERE group_name='pitching'"):
        s = json.loads(sjson)
        ip = s.get("inningsPitched")
        try:
            ip = float(ip)
        except (TypeError, ValueError):
            continue
        if ip < 40:
            continue
        rows.append({"season": season, "name": name, "team": team, "IP": ip,
                     "ERA": _num(s.get("era")), "WHIP": _num(s.get("whip")),
                     "K": _num(s.get("strikeOuts")), "BB": _num(s.get("walks")),
                     "HR": _num(s.get("homeRuns"))})
    con.close()
    return pd.DataFrame(rows)


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def load_il_days():
    total = {}
    for season in (2025, 2026):
        path = os.path.join(RAW, f"transactions_{season}.json")
        if not os.path.exists(path):
            continue
        for t in json.load(open(path)):
            desc = t.get("description") or ""
            low = desc.lower()
            if "injured list" not in low and "10-day" not in low and "60-day" not in low:
                continue
            p = t.get("person") or {}
            name = p.get("fullName")
            if not name:
                continue
            days = next((d for k, d in IL_DAYS.items() if k.lower() in low), None)
            if days is None:
                m = re.search(r"(\d+)-day", low)
                days = int(m.group(1)) if m else 15
            total[name] = total.get(name, 0) + days
    return total


def name_key(name):
    n = str(name)
    parts = [p for p in re.split(r"[,\s]+", n.strip()) if p]
    if len(parts) >= 2 and "," in n:
        return f"{parts[0]}, {parts[1]}"
    return n


def marcel_rate(col, g, lg):
    w = g["w"]
    raw = (g[col] * w).sum() / w.sum()
    tot_ip = (g["IP"] * w).sum()
    reg = tot_ip / 300.0
    return (raw * tot_ip + lg * reg) / (tot_ip + reg)


def main():
    df = load_pitchers()
    il = load_il_days()
    print(f"pitcher-seasons: {len(df)}")

    rows = []
    for pid, g in df.groupby("name"):
        g = g.copy()
        g["w"] = g["season"].map({2026: 5, 2025: 4}).fillna(3)
        tot_ip = (g["IP"] * g["w"]).sum()
        if tot_ip < 300:
            continue
        team = g.sort_values("season")["team"].iloc[-1]
        era = marcel_rate("ERA", g, LEAGUE["ERA"])
        whip = marcel_rate("WHIP", g, LEAGUE["WHIP"])
        k9 = (g["K"] * g["w"]).sum() / tot_ip * 9
        bb9 = (g["BB"] * g["w"]).sum() / tot_ip * 9
        ip_proj = min(200.0, tot_ip * 0.9)
        rows.append({"name": pid, "team": team, "proj_IP": round(ip_proj, 1),
                     "proj_ERA": round(era, 2), "proj_WHIP": round(whip, 2),
                     "proj_K9": round(k9, 1), "proj_BB9": round(bb9, 1)})
    proj = pd.DataFrame(rows)
    print(f"projected pitchers: {len(proj)}")

    proj["il_days_25_26"] = proj["name"].map(lambda n: il.get(n) or il.get(name_key(n)) or 0)
    proj["avail_pct"] = (1.0 - proj["il_days_25_26"] / (2 * 182)).clip(0.3, 1.0)
    proj["proj_IP_health"] = (proj["proj_IP"] * proj["avail_pct"]).round(1)

    out = os.path.join(DATA, "projections_2027_pitchers.json")
    proj.to_json(out, orient="records", indent=2)
    print(f"wrote {out} ({len(proj)} pitchers)")
    print("\n=== Top projected pitchers by ERA ===")
    print(proj.sort_values("proj_ERA").head(8)[
        ["name", "team", "proj_IP", "proj_ERA", "proj_WHIP", "proj_K9", "proj_BB9",
         "proj_IP_health"]].to_string(index=False))


if __name__ == "__main__":
    main()
