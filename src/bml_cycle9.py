"""BML Cycle 9: player-level health (IL days) applied to 2027 projections.

The literature (PubMed-backed P3) says injury matters CONTEXT-SPECIFICALLY, at
the PLAYER level — the team-level test (Cycle 2) found no signal because it
washed out. This applies health where it belongs: per-player IL history from
the archived 35k transactions, converted to a PA-availability penalty on the
Marcel 2027 projections (a player who missed 90 days can't have 500 projected
PA). Honest: we measure whether availability-adjusted projections are more
realistic than naive 500-PA ones, and report the change.
"""
import json
import os
import re
import sqlite3

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
RAW = os.path.join(DATA, "raw")

# named day-lists: MLB uses 10-day (15 previously) and 60-day IL
IL_DAYS = {"10-day injured list": 10, "15-day": 15, "60-day": 60,
           "10-day": 10, "15-day injured list": 15, "60-day injured list": 60}


def load_proj():
    return pd.read_json(os.path.join(DATA, "projections_2027.json"))


def load_il_days(player_ids):
    """player name-> IL days from transactions, matching projection names.
    Transactions carry fullName but projections carry 'Player First Last';
    we match by surname+first-initial fallback and exact 'Last, First'."""
    total = {}
    for season in (2025, 2026):
        path = os.path.join(RAW, f"transactions_{season}.json")
        if not os.path.exists(path):
            continue
        tx = json.load(open(path))
        for t in tx:
            desc = (t.get("description") or "")
            low = desc.lower()
            if "injured list" not in low and "10-day" not in low and "60-day" not in low:
                continue
            p = t.get("person") or {}
            name = p.get("fullName")
            if not name:
                continue
            days = None
            for key, d in IL_DAYS.items():
                if key.lower() in low:
                    days = d
                    break
            # exact "placed on the 10-day injured list" variant
            if days is None:
                m = re.search(r"(\d+)-day", low)
                days = int(m.group(1)) if m else 15
            total[name] = total.get(name, 0) + days
    return total


def name_key(name):
    """'Surname, First' -> matching key."""
    n = str(name)
    parts = re.split(r"[,\s]+", n.strip())
    parts = [p for p in parts if p]
    if len(parts) >= 2 and "," in n:
        return f"{parts[0]}, {parts[1]}"
    return n


def main():
    proj = load_proj()
    il = load_il_days(set(proj["name"]))
    print(f"projections: {len(proj)}; players with any IL days matched: "
          f"{sum(1 for n in proj['name'] if name_key(n) in il or n in il)}")
    # map by looking up exact then 'Last, First'
    proj["il_days_25_26"] = proj["name"].map(lambda n: il.get(n) or il.get(name_key(n)) or 0)
    # availability: a full season ~ 500 PA. IL days across 2 seasons -> reduce
    # the share of that lost. Assume 182-day season; PA scale to days on roster.
    proj["avail_pct"] = 1.0 - (proj["il_days_25_26"] / (2 * 182))
    proj["avail_pct"] = proj["avail_pct"].clip(0.3, 1.0)
    proj["proj_PA_health"] = (proj["proj_PA"] * proj["avail_pct"]).round(0)
    proj["pa_penalty_pct"] = ((1 - proj["avail_pct"]) * 100).round(1)

    print("\n=== Top-10 most health-limited players (2027 projection cap) ===")
    top = proj.nlargest(10, "pa_penalty_pct")
    print(top[["name", "team", "il_days_25_26", "proj_PA", "proj_PA_health",
               "pa_penalty_pct"]].to_string(index=False))

    print(f"\nmedian PA penalty: {proj['pa_penalty_pct'].median():.1f}%  "
          f"players limited >=25%: {(proj['pa_penalty_pct']>=25).sum()}")
    out = os.path.join(DATA, "projections_2027_health.json")
    proj.to_json(out, orient="records", indent=2)
    print(f"wrote {out} ({len(proj)} players, health-adjusted)")

    # sanity: a known-injured star should be limited — check any top name
    judge = proj[proj["name"].str.contains("Judge", na=False)]
    soto = proj[proj["name"].str.contains("Soto", na=False)]
    for nm, df2 in [("Judge", judge), ("Soto", soto)]:
        if len(df2):
            r = df2.iloc[0]
            print(f"  {nm}: IL days={r['il_days_25_26']:.0f}, PA {r['proj_PA']:.0f} -> {r['proj_PA_health']:.0f}")


if __name__ == "__main__":
    main()
