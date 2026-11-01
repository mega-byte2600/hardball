"""BML Cycle 22: BENCHMARK the roster tool's Marcel projections against
FanGraphs Steamer 2027 — the first question an expert asks ("how does it
stack up against the public systems?") finally answered from data.

Method, in the project's own rules:
  - Join is by MLBAM player_id ONLY (repo `player_id` == FanGraphs
    `xMLBAMID`). Never by name — name-string joins are the failure class
    behind the AZ/ARI and walks bugs. Names below are display labels
    copied from the repo's own projection rows, not join keys.
  - Inputs are the committed snapshots pulled 2026-10-31
    (data/fg_steamer_2027_bat.json / _pit.json from src/carpe.py) plus
    data/projections_2027.json (200 hitters) and
    data/projections_2027_pitchers.json (76 pitchers). No live calls.
  - Hitters: paired OBP / SLG comparison (correlation, mean abs diff,
    signed bias, top-25-by-OBP overlap, biggest disagreements).
    Marcel does not project wOBA or WAR, so those are reported as
    Steamer-only values for the matched set — no paired claim is made.
  - Pitchers: the repo file carries no player_id, so ids are resolved
    through the lake `players` registry (itself MLBAM-keyed); a pitcher
    is used only if his name maps to exactly one lake id. The benchmark
    join itself is still id-to-id.
  - ZiPS: the FanGraphs API returned an empty ZiPS pull on 2026-10-31,
    so ZiPS is NOT in this benchmark. Steamer only, labeled as such.

Outputs: data/fg_benchmark_2027.json
"""
import json
import os
import sqlite3

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
LAKE = os.path.join(DATA, "mlb_lake.db")

PULL_DATE = "2026-10-31"


def _num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _paired_stats(pairs):
    """pairs: list of (marcel, steamer). Returns correlation + diff stats."""
    m = np.array([p[0] for p in pairs], dtype=float)
    s = np.array([p[1] for p in pairs], dtype=float)
    d = m - s
    return {"n": int(len(pairs)),
            "pearson_r": round(float(np.corrcoef(m, s)[0, 1]), 3),
            "mean_abs_diff": round(float(np.mean(np.abs(d))), 3),
            "mean_signed_diff_marcel_minus_steamer": round(float(np.mean(d)), 3)}


def _disagreements(rows, mkey, skey, k=10):
    """rows: matched dicts carrying marcel/steamer values under mkey/skey."""
    ranked = sorted(rows, key=lambda r: abs(r[mkey] - r[skey]), reverse=True)[:k]
    return [{"player_id": r["player_id"], "name": r["name"],
             "marcel": r[mkey], "steamer": r[skey],
             "diff_marcel_minus_steamer": round(r[mkey] - r[skey], 3)}
            for r in ranked]


def load_fg(path):
    """FanGraphs snapshot -> {xMLBAMID: row}, dropping the null-id row."""
    out = {}
    for r in json.load(open(path)):
        pid = r.get("xMLBAMID")
        if pid is None:
            continue
        out[int(pid)] = r
    return out


def hitters():
    marcel = json.load(open(os.path.join(DATA, "projections_2027.json")))
    fg = load_fg(os.path.join(DATA, "fg_steamer_2027_bat.json"))

    matched = []
    for m in marcel:
        f = fg.get(int(m["player_id"]))
        if f is None:
            continue
        matched.append({
            "player_id": int(m["player_id"]), "name": m["name"],
            "marcel_obp": _num(m.get("proj_OBP")), "steamer_obp": _num(f.get("OBP")),
            "marcel_slg": _num(m.get("proj_SLG")), "steamer_slg": _num(f.get("SLG")),
            "steamer_woba": _num(f.get("wOBA")), "steamer_war": _num(f.get("WAR")),
        })

    obp_pairs = [(r["marcel_obp"], r["steamer_obp"]) for r in matched
                 if r["marcel_obp"] is not None and r["steamer_obp"] is not None]
    slg_pairs = [(r["marcel_slg"], r["steamer_slg"]) for r in matched
                 if r["marcel_slg"] is not None and r["steamer_slg"] is not None]

    m_top = sorted(matched, key=lambda r: r["marcel_obp"], reverse=True)[:25]
    s_top = sorted(matched, key=lambda r: r["steamer_obp"], reverse=True)[:25]
    overlap_ids = sorted({r["player_id"] for r in m_top}
                         & {r["player_id"] for r in s_top})
    by_id = {r["player_id"]: r for r in matched}

    war = [r["steamer_war"] for r in matched if r["steamer_war"] is not None]
    woba = [r["steamer_woba"] for r in matched if r["steamer_woba"] is not None]
    top_war = sorted((r for r in matched if r["steamer_war"] is not None),
                     key=lambda r: r["steamer_war"], reverse=True)[:5]

    return {
        "marcel_n": len(marcel), "steamer_n_with_id": len(fg),
        "matched_n": len(matched),
        "unmatched_marcel_ids": sorted(int(m["player_id"]) for m in marcel
                                       if int(m["player_id"]) not in fg),
        "obp": _paired_stats(obp_pairs),
        "slg": _paired_stats(slg_pairs),
        "top25_obp_overlap": {
            "overlap_n": len(overlap_ids),
            "overlap": [{"player_id": pid, "name": by_id[pid]["name"],
                         "marcel_obp": by_id[pid]["marcel_obp"],
                         "steamer_obp": by_id[pid]["steamer_obp"]}
                        for pid in overlap_ids],
            "marcel_only_top25": [r["name"] for r in m_top
                                  if r["player_id"] not in overlap_ids],
            "steamer_only_top25": [r["name"] for r in s_top
                                   if r["player_id"] not in overlap_ids],
        },
        "biggest_disagreements_obp": _disagreements(matched, "marcel_obp", "steamer_obp"),
        "biggest_disagreements_slg": _disagreements(matched, "marcel_slg", "steamer_slg"),
        "steamer_only_metrics": {
            "note": "Repo Marcel projections carry no wOBA or WAR, so no paired "
                    "comparison exists; below are Steamer's values for the "
                    "matched hitters only.",
            "matched_steamer_woba_mean": round(float(np.mean(woba)), 3) if woba else None,
            "matched_steamer_war_mean": round(float(np.mean(war)), 3) if war else None,
            "top5_by_steamer_war": [{"player_id": r["player_id"], "name": r["name"],
                                     "steamer_war": r["steamer_war"],
                                     "steamer_woba": r["steamer_woba"]}
                                    for r in top_war],
        },
    }


def pitchers():
    marcel = json.load(open(os.path.join(DATA, "projections_2027_pitchers.json")))
    fg = load_fg(os.path.join(DATA, "fg_steamer_2027_pit.json"))

    # projections_2027_pitchers.json has no player_id: resolve ids via the
    # lake players registry (MLBAM-keyed). Unique mapping or excluded.
    con = sqlite3.connect(LAKE)
    id_by_name = {}
    for pid, name in con.execute("SELECT player_id, full_name FROM players"):
        id_by_name.setdefault(name, []).append(pid)
    con.close()

    matched, unresolved = [], []
    for m in marcel:
        ids = id_by_name.get(m["name"], [])
        if len(ids) != 1:
            unresolved.append(m["name"])
            continue
        pid = int(ids[0])
        f = fg.get(pid)
        if f is None:
            unresolved.append(m["name"])
            continue
        matched.append({
            "player_id": pid, "name": m["name"],
            "marcel_era": _num(m.get("proj_ERA")), "steamer_era": _num(f.get("ERA")),
            "marcel_whip": _num(m.get("proj_WHIP")), "steamer_whip": _num(f.get("WHIP")),
        })

    era_pairs = [(r["marcel_era"], r["steamer_era"]) for r in matched
                 if r["marcel_era"] is not None and r["steamer_era"] is not None]
    whip_pairs = [(r["marcel_whip"], r["steamer_whip"]) for r in matched
                  if r["marcel_whip"] is not None and r["steamer_whip"] is not None]

    return {
        "marcel_n": len(marcel), "steamer_n_with_id": len(fg),
        "matched_n": len(matched),
        "id_resolution": "projections_2027_pitchers.json carries no player_id; "
                         "ids resolved through the lake players registry, "
                         "unique name->id mapping required",
        "unresolved_or_unmatched": unresolved,
        "era": _paired_stats(era_pairs),
        "whip": _paired_stats(whip_pairs),
        "biggest_disagreements_era": _disagreements(matched, "marcel_era", "steamer_era"),
        "biggest_disagreements_whip": _disagreements(matched, "marcel_whip", "steamer_whip"),
    }


def main():
    out = {
        "metadata": {
            "cycle": 22,
            "generated_by": "src/bml_cycle22.py",
            "benchmark": "FanGraphs Steamer 2027 projections",
            "source_pull_date": PULL_DATE,
            "sources": ["data/fg_steamer_2027_bat.json", "data/fg_steamer_2027_pit.json",
                        "data/projections_2027.json", "data/projections_2027_pitchers.json",
                        "data/mlb_lake.db (players registry, pitcher id resolution only)"],
            "join": "MLBAM player_id == FanGraphs xMLBAMID only; never by name",
            "zips": "ZiPS via the FanGraphs API returned empty on 2026-10-31 "
                    "and is therefore not included in this benchmark.",
            "scope_note": "Agreement-with-Steamer statistics, not accuracy: "
                          "neither system has 2027 outcomes yet. This measures "
                          "how far the repo's Marcel sits from the public "
                          "benchmark, and where they disagree most.",
        },
        "hitters": hitters(),
        "pitchers": pitchers(),
    }
    path = os.path.join(DATA, "fg_benchmark_2027.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    h, p = out["hitters"], out["pitchers"]
    print(f"HITTERS: matched {h['matched_n']} of {h['marcel_n']} Marcel "
          f"(Steamer pool {h['steamer_n_with_id']})")
    print(f"  OBP  r={h['obp']['pearson_r']}  MAD={h['obp']['mean_abs_diff']}  "
          f"bias={h['obp']['mean_signed_diff_marcel_minus_steamer']:+.3f}")
    print(f"  SLG  r={h['slg']['pearson_r']}  MAD={h['slg']['mean_abs_diff']}  "
          f"bias={h['slg']['mean_signed_diff_marcel_minus_steamer']:+.3f}")
    print(f"  top-25 OBP overlap: {h['top25_obp_overlap']['overlap_n']}/25")
    print(f"PITCHERS: matched {p['matched_n']} of {p['marcel_n']} Marcel "
          f"(Steamer pool {p['steamer_n_with_id']})")
    print(f"  ERA  r={p['era']['pearson_r']}  MAD={p['era']['mean_abs_diff']}  "
          f"bias={p['era']['mean_signed_diff_marcel_minus_steamer']:+.3f}")
    print(f"  WHIP r={p['whip']['pearson_r']}  MAD={p['whip']['mean_abs_diff']}  "
          f"bias={p['whip']['mean_signed_diff_marcel_minus_steamer']:+.3f}")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
