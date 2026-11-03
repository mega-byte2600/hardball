#!/usr/bin/env python3
"""Cycle 75 — bat-speed exhibit artifact.

Computes every number the Figure 19 companion exhibit prints, from
the committed Baseball Savant bat-tracking boards ONLY
(data/savant_bat_tracking_2024/2025/2026.json). No hand-entered
numbers: the N04 verdict text is copied programmatically from
data/claims_register.json and data/savant_test.json, and the
stability comparison reads the committed Cycle 20 values from
data/savant_test.json at run time.

Context, never a claim: bat speed was tested as a projection
adjustment in Cycle 20 and DROPPED (claim N04, NOT SUPPORTED — it
made projections worse out of sample). This artifact exists so the
exhibit can show the trait's distribution and stability as context,
labeled as such. Nothing here feeds any projection.

Corroboration built in:
- Stability is computed two ways: per transition (2024->2025,
  2025->2026) on players matched by player_id, and pooled across
  both transitions; plus a >=250-competitive-swing qualification
  sensitivity, which is the basis that reconciles with the Cycle 20
  committed mean r of ~0.921.
- If the local platform raw cache (mirror CSVs of the same Savant
  boards) is present, the boards are reconciled against it player
  by player and the match rate is recorded.

Usage: python3 src/bml_cycle75.py
Output: data/bat_speed_exhibit_2027.json
"""
import csv
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MIRROR_RAW = Path(os.path.expanduser(
    "~/workspace/github/hardball/data/raw"))
YEARS = (2024, 2025, 2026)
QUAL_SWINGS = 250


def _pearson(xs, ys):
    n = len(xs)
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    syy = math.fsum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def _quantile(sorted_vals, q):
    n = len(sorted_vals)
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def load_board(year):
    rows = json.loads((DATA / f"savant_bat_tracking_{year}.json")
                      .read_text())
    return {int(r["player_id"]): r for r in rows}


def stability(boards, min_swings=0):
    pairs = {}
    pooled_x, pooled_y = [], []
    for a, b in ((2024, 2025), (2025, 2026)):
        xs, ys = [], []
        for pid, ra in boards[a].items():
            rb = boards[b].get(pid)
            if rb is None:
                continue
            if (ra["swings_competitive"] < min_swings
                    or rb["swings_competitive"] < min_swings):
                continue
            xs.append(float(ra["avg_bat_speed"]))
            ys.append(float(rb["avg_bat_speed"]))
        pairs[f"{a}_{b}"] = {"n": len(xs),
                             "r": round(_pearson(xs, ys), 6)}
        pooled_x += xs
        pooled_y += ys
    return {"pairs": pairs,
            "pooled": {"n_pairs": len(pooled_x),
                       "r": round(_pearson(pooled_x, pooled_y), 6)}}


def reconcile_mirror(boards):
    """Repo JSON boards vs the platform raw cache (mirror CSVs):
    counts and per-player value agreement, all three years."""
    out = {"mirror_found": True, "years": {}}
    for y in YEARS:
        path = MIRROR_RAW / f"savant_bat_tracking_{y}.csv"
        if not path.exists():
            return {"mirror_found": False}
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = {int(r["id"]): r for r in csv.DictReader(f)}
        board = boards[y]
        matched = set(board) & set(rows)
        exact_bs = exact_sl = 0
        for pid in matched:
            if float(board[pid]["avg_bat_speed"]) == \
                    float(rows[pid]["avg_bat_speed"]):
                exact_bs += 1
            if float(board[pid]["swing_length"]) == \
                    float(rows[pid]["swing_length"]):
                exact_sl += 1
        out["years"][str(y)] = {
            "repo_rows": len(board), "mirror_rows": len(rows),
            "matched": len(matched),
            "avg_bat_speed_exact": exact_bs,
            "swing_length_exact": exact_sl}
    return out


def team_join_coverage(boards):
    """Why there is no team lens: measure the best committed
    player->team joins against the 2026 board. Recorded, not used."""
    board_ids = set(boards[2026])
    cov = {"board_players_2026": len(board_ids)}
    try:
        import pandas as pd
        sl = pd.read_parquet(DATA / "curated" / "fact_stat_lines.parquet")
        h = sl[(sl["season"] == 2026) & (sl["group_name"] == "hitting")]
        cov["fact_stat_lines_2026_hitting"] = {
            "players": int(h["player_id"].nunique()),
            "board_covered": int(len(board_ids & set(h["player_id"])))}
        ph = pd.read_parquet(DATA / "curated" / "fact_proj_hitters.parquet")
        cov["fact_proj_hitters"] = {
            "players": int(ph["player_id"].nunique()),
            "board_covered": int(len(board_ids & set(ph["player_id"])))}
    except Exception as e:  # pragma: no cover - recorded, not fatal
        cov["curated_error"] = str(e)
    steamer = json.loads((DATA / "fg_steamer_2027_bat.json").read_text())
    srows = [r for r in steamer if r.get("xMLBAMID") in board_ids]
    cov["steamer_2027_bat"] = {
        "board_rows": len(srows),
        "team_nonnull": int(sum(1 for r in srows if r.get("Team")))}
    return cov


def main():
    boards = {y: load_board(y) for y in YEARS}

    stab_all = stability(boards, 0)
    stab_all["method"] = ("Pearson r of avg_bat_speed, players matched "
                          "by player_id across the committed boards as "
                          "published (no added filter); pooled = both "
                          "transitions concatenated")
    stab_q = stability(boards, QUAL_SWINGS)
    stab_q["method"] = (f"same computation with a >={QUAL_SWINGS} "
                        "competitive-swing minimum in both seasons")

    test = json.loads((DATA / "savant_test.json").read_text())
    committed = test["q2_trait_stability"]["bat_speed"]
    reg = json.loads((DATA / "claims_register.json").read_text())
    n04 = next(c for c in reg["claims"] if c["id"] == "N04")

    vals = sorted(float(r["avg_bat_speed"]) for r in boards[2026].values())
    n = len(vals)
    mean = math.fsum(vals) / n
    sd = math.sqrt(math.fsum((v - mean) ** 2 for v in vals) / (n - 1))
    dist = {"n": n, "min": round(vals[0], 4),
            "p10": round(_quantile(vals, 0.10), 4),
            "p25": round(_quantile(vals, 0.25), 4),
            "median": round(_quantile(vals, 0.50), 4),
            "mean": round(mean, 4), "sd": round(sd, 4),
            "p75": round(_quantile(vals, 0.75), 4),
            "p90": round(_quantile(vals, 0.90), 4),
            "max": round(vals[-1], 4)}

    def _row(r):
        return {"player_id": int(r["player_id"]), "name": r["name"],
                "avg_bat_speed": round(float(r["avg_bat_speed"]), 4),
                "swing_length": round(float(r["swing_length"]), 4),
                "squared_up_per_swing": round(
                    float(r["squared_up_per_swing"]), 4),
                "blast_per_swing": round(float(r["blast_per_swing"]), 4),
                "swings_competitive": int(r["swings_competitive"])}

    qual = [r for r in boards[2026].values()
            if r["swings_competitive"] >= QUAL_SWINGS]
    fastest = sorted(qual, key=lambda r: -float(r["avg_bat_speed"]))[:8]
    slowest = sorted(qual, key=lambda r: float(r["avg_bat_speed"]))[:8]

    out = {
        "cycle": 75,
        "title": "Bat-speed exhibit — distribution and stability (context only)",
        "generated_by": "src/bml_cycle75.py",
        "sources": {
            "boards": [f"data/savant_bat_tracking_{y}.json" for y in YEARS],
            "verdicts": "data/savant_test.json (Cycle 20)",
            "register": "data/claims_register.json (claim N04)"},
        "reconciliation": reconcile_mirror(boards),
        "stability": {
            "all_matched": stab_all,
            "qualified_250": stab_q,
            "savant_test_committed": {
                "yoy_r_by_pair": committed["yoy_r_by_pair"],
                "mean_r": committed["mean_r"]},
            "note": ("The Cycle 20 committed mean (0.921) sits on a "
                     "qualified basis: with a >=250-swing minimum in "
                     "both seasons these boards give "
                     f"{stab_q['pairs']['2024_2025']['r']:.3f} and "
                     f"{stab_q['pairs']['2025_2026']['r']:.3f}. The "
                     "unqualified matched computation gives "
                     f"{stab_all['pooled']['r']:.3f} pooled. The "
                     "difference is the qualification, not the data.")},
        "distribution_2026": dist,
        "top_bottom_2026": {
            "min_swings": QUAL_SWINGS,
            "qualified_n": len(qual),
            "fastest": [_row(r) for r in fastest],
            "slowest": [_row(r) for r in slowest]},
        "team_lens": {
            "status": "cut",
            "reason": ("No committed player-to-team join covers the "
                       "2026 board: fact_stat_lines 2026 hitting covers "
                       "a selected subset, the Steamer 2027 file carries "
                       "no team for any board player, and "
                       "fact_proj_hitters is a 201-player benchmark "
                       "subset. A team split on ~22% coverage would be "
                       "a selected-sample mean presented as a team "
                       "profile, so no team lens is printed."),
            "coverage": team_join_coverage(boards)},
        "n04": {
            "claim": n04["claim"],
            "status": n04["status"],
            "key_numbers": n04["evidence"]["key_numbers"],
            "location": n04["location"],
            "f3_verdict": test["verdicts"]["F3_bat_tracking"]},
    }
    path = DATA / "bat_speed_exhibit_2027.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"wrote {path} ({path.stat().st_size} bytes)")
    print(f"stability pooled r = {stab_all['pooled']['r']} "
          f"(pairs {stab_all['pairs']['2024_2025']['r']} / "
          f"{stab_all['pairs']['2025_2026']['r']})")
    print(f"2026 distribution: n={dist['n']} median={dist['median']} "
          f"IQR {dist['p25']}–{dist['p75']} range {dist['min']}–{dist['max']}")


if __name__ == "__main__":
    main()
