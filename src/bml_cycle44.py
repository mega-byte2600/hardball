#!/usr/bin/env python3
"""Cycle 44 — accuracy stack: Cot's as a second labeled salary dataset,
BRef WAR salary cross-check, and the reconciliations behind both.

Rules (owner, 2026-11-02: "do what takes to make accurate, optimal
and professional"; Cycle 41 reconcile-first discipline):
  - data/salaries_2026.json (Spotrac-basis file) is NEVER touched and
    forced-seller math is NEVER changed here. Every new dataset is
    separately labeled with its own source + basis.
  - Cot's dataset = Cot's published 2027 Labor Relations Payroll (LRP)
    dollar figures only (players whose Cot's cell is a marker — FA /
    A1 / option — carry no number and are not rows). Basis: LRP books
    deferred money at present value and option years at the guaranteed
    buyout. Cross-check / coverage layer only.
  - BRef WAR salary column: the literal string "NULL" means missing.
    Reconciled BEFORE any use: vs the Spotrac-basis file (24 teams)
    and vs Cot's for the 6 gap teams (ARI/BOS/CHC/MIL/TB/TEX), on both
    Cot's LRP-2026 (same season) and LRP-2027 (the Spotrac file's
    basis). The BRef dataset ships only if the gap-team same-season
    agreement clears the bar set below; otherwise this script writes
    the reconciliation workpaper and fails closed (no dataset).

Inputs (mirror caches, Spotrac pattern — see ingest_platform.run_spotrac):
  ~/workspace/github/hardball/data/raw/cots/cots_parsed.csv
  ~/workspace/github/hardball/data/raw/bref_war/war_daily_{bat,pitch}.txt
Outputs:
  data/salaries_cots_2027.json      (always, if the Cot's cache parses)
  data/salary_recon_cycle44.json    (the reconciliation workpaper)
  data/salaries_bref_war_2026.json  (only on a credible gap-team pass)
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MIRROR = Path.home() / "workspace/github/hardball/data/raw"
GAP_TEAMS = ["ARI", "BOS", "CHC", "MIL", "TB", "TEX"]
TEAM_MAP_BREF = {"TBR": "TB"}  # BRef codes -> repo codes
AGREE_TOL = 50_000
GAP_PASS_BAR = 0.80  # >=80% of gap-team matched pairs within $50k (LRP-2026)


def norm_name(raw):
    """'Last, First*' / 'First Last' -> comparable lowercase key."""
    s = str(raw).replace("*", "").strip()
    if "," in s:  # Cot's format
        last, first = [p.strip() for p in s.split(",", 1)]
        s = f"{first} {last}"
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace(".", " ").replace("-", " ")
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"\s+", " ", s).strip()


def build_cots():
    src = MIRROR / "cots" / "cots_parsed.csv"
    c = pd.read_csv(src)
    rows = []
    for _, r in c.iterrows():
        if pd.isna(r["lrp_2027"]):
            continue  # marker cell (FA / arb / option): no published figure
        name = str(r["name_raw"]).replace("*", "").strip()
        if "," in name:
            last, first = [p.strip() for p in name.split(",", 1)]
            name = f"{first} {last}"
        rows.append({
            "name": name,
            "team": r["team"],
            "pos": r["pos"] if isinstance(r["pos"], str) else None,
            "contract": r["contract"] if isinstance(r["contract"], str) else None,
            "salary_lrp_2027": int(r["lrp_2027"]),
            "lrp_2026": None if pd.isna(r["lrp_2026"]) else int(r["lrp_2026"]),
            "cb_2027_aav": None if pd.isna(r["cb_2027"]) else int(r["cb_2027"]),
            "source": "cots_baseball_prospectus",
        })
    rows.sort(key=lambda x: (x["team"], -x["salary_lrp_2027"]))
    out = {
        "metadata": {
            "source": "Cot's Baseball Contracts (Baseball Prospectus), "
                      "per-team Google Sheets exports pulled 2026-11-02 (Cycle 41)",
            "basis": "Cot's Labor Relations Payroll (LRP) 2027 — projected "
                     "40-man year-end; deferred money at present value; "
                     "option years at the guaranteed buyout. NOT the "
                     "Spotrac-basis basis of data/salaries_2026.json; "
                     "never mix the two in one sum.",
            "field": "LRP 2027 dollar figure (rows exist only where Cot's "
                     "publishes a figure; unsigned players carry FA/arb/"
                     "option markers, not numbers)",
            "rows": len(rows),
            "teams": len({r["team"] for r in rows}),
            "role": "Labeled cross-check / coverage layer ONLY. Does not "
                    "feed forced-seller math or any roster math.",
        },
        "players": rows,
    }
    (DATA / "salaries_cots_2027.json").write_text(json.dumps(out, indent=1))
    return out, c


def load_bref():
    frames = []
    for kind in ("bat", "pitch"):
        f = MIRROR / "bref_war" / f"war_daily_{kind}.txt"
        d = pd.read_csv(f, low_memory=False)
        d["kind"] = kind
        frames.append(d)
    b = pd.concat(frames, ignore_index=True)
    b = b[b["year_ID"] == 2026].copy()
    b["salary_num"] = pd.to_numeric(b["salary"], errors="coerce")
    b = b[b["salary_num"].notna()]
    b["team"] = b["team_ID"].replace(TEAM_MAP_BREF)
    b["key"] = [norm_name(n) for n in b["name_common"]]
    # a player can appear in both files (and in 2 stints): keep one row
    # per (player, team); flag salary conflicts inside a (player, team)
    conflicts = 0
    keep = {}
    for _, r in b.iterrows():
        k = (int(r["mlb_ID"]), r["team"])
        if k in keep and keep[k]["salary_num"] != r["salary_num"]:
            conflicts += 1
            continue
        keep[k] = r
    out = pd.DataFrame(keep.values())
    return out, conflicts


def reconcile(bref, cots_df):
    sal = json.loads((DATA / "salaries_2026.json").read_text())
    spot = pd.DataFrame(sal["players"])
    spot["key"] = [norm_name(n) for n in spot["name"]]
    spot["salary_num"] = spot["salary_2026"]
    bref24 = bref[bref["team"].isin(set(spot["team"]))]
    m = spot.rename(columns={"salary_num": "salary_spot"}).merge(
        bref24[["key", "team", "salary_num"]].rename(
            columns={"salary_num": "salary_bref"}), on=["key", "team"])
    agree = (m["salary_spot"] - m["salary_bref"]).abs() <= AGREE_TOL
    vs_spotrac = {
        "spotrac_rows_24_teams": len(spot),
        "bref_rows_24_teams": len(bref24),
        "matched_name_team": len(m),
        "coverage_of_spotrac_rows_pct": round(100 * len(m) / len(spot), 1),
        "agree_within_50k": int(agree.sum()),
        "agree_pct_of_matched": round(100 * agree.mean(), 1) if len(m) else 0,
        "note": "Expected to disagree on escalators: the Spotrac-basis "
                "file is on a 2027 basis (Cycle 41 discovery); BRef is "
                "the 2026 season's salary.",
    }
    # Cot's: pivot parsed rows to name/team keys for both LRP columns
    cots = cots_df.copy()
    cots["key"] = [norm_name(n) for n in cots["name_raw"]]
    cots["team"] = cots["team"]
    res = {}
    for basis, col in (("lrp_2026_same_season", "lrp_2026"),
                       ("lrp_2027_spotrac_basis", "lrp_2027")):
        # Cot's sheets carry extra bonus/buyout/departed lines per player;
        # the contract row is the largest figure for a (player, team)
        cb = (cots[cots[col].notna()].sort_values(col, ascending=False)
              .drop_duplicates(["key", "team"])[["key", "team", col]])
        for scope, teams in (("gap6", GAP_TEAMS), ("all30", None)):
            bb = bref if teams is None else bref[bref["team"].isin(teams)]
            cc = cb if teams is None else cb[cb["team"].isin(teams)]
            mm = bb.merge(cc, on=["key", "team"], suffixes=("", "_cots"))
            ag = (mm["salary_num"] - mm[col]).abs() <= AGREE_TOL
            res[f"{basis}_{scope}"] = {
                "bref_rows": len(bb), "cots_rows_with_figure": len(cc),
                "matched_name_team": len(mm),
                "agree_within_50k": int(ag.sum()),
                "agree_pct_of_matched": round(100 * ag.mean(), 1) if len(mm) else 0,
            }
    return vs_spotrac, res


def main():
    if not (MIRROR / "cots" / "cots_parsed.csv").exists():
        print("FAIL CLOSED: Cot's mirror cache absent in this environment")
        return 1
    cots_out, cots_df = build_cots()
    print(f"COT'S DATASET: {cots_out['metadata']['rows']} rows, "
          f"{cots_out['metadata']['teams']} teams -> data/salaries_cots_2027.json")
    if not (MIRROR / "bref_war" / "war_daily_bat.txt").exists():
        print("FAIL CLOSED: BRef WAR cache absent; reconciliation skipped")
        return 1
    bref, conflicts = load_bref()
    print(f"BREF 2026: {len(bref)} player-team rows with a real salary "
          f"({conflicts} conflicting duplicates dropped)")
    vs_spotrac, vs_cots = reconcile(bref, cots_df)
    gap = vs_cots["lrp_2026_same_season_gap6"]
    print("VS SPOTRAC FILE (24 teams):", vs_spotrac)
    print("VS COT'S:", json.dumps(vs_cots, indent=1))
    ship = bool(gap["agree_pct_of_matched"] >= GAP_PASS_BAR * 100
                and gap["matched_name_team"] >= 30)
    recon = {
        "generated": "Cycle 44 (2026-11-02)",
        "bref_rows_2026_with_salary": len(bref),
        "bref_conflicting_duplicates_dropped": conflicts,
        "vs_spotrac_basis_file": vs_spotrac,
        "vs_cots": vs_cots,
        "gap_pass_bar": f">={int(GAP_PASS_BAR*100)}% of matched gap-team pairs "
                        f"within $50k on Cot's LRP-2026 (same season), >=30 matched",
        "bref_dataset_shipped": ship,
    }
    (DATA / "salary_recon_cycle44.json").write_text(json.dumps(recon, indent=1))
    if ship:
        rows = [{"name": r["name_common"], "player_id": int(r["mlb_ID"]),
                 "team": r["team"], "salary_2026": int(r["salary_num"]),
                 "source": "baseball_reference_war"}
                for _, r in bref.sort_values(["team", "name_common"]).iterrows()]
        out = {"metadata": {
                   "source": "Baseball-Reference WAR daily downloads "
                             "(war_daily_bat.txt / war_daily_pitch.txt), "
                             "pulled 2026-11-02",
                   "basis": "Actual 2026 season salary as published in "
                            "BRef's WAR files. Coverage is PARTIAL: the "
                            "salary column is populated for only ~30% of "
                            "2025-26 players (the rest are the literal "
                            "string NULL in the source).",
                   "rows": len(rows),
                   "teams": len({r["team"] for r in rows}),
                   "role": "Third, separately labeled cross-check layer. "
                           "Does not feed forced-seller or roster math.",
                   "reconciliation": "docs/CARPE_SCORECARD.md Cycle 44; "
                                     "data/salary_recon_cycle44.json"},
               "players": rows}
        (DATA / "salaries_bref_war_2026.json").write_text(json.dumps(out, indent=1))
        print(f"BREF DATASET SHIPPED: {len(rows)} rows (gap-team pass)")
    else:
        print("BREF DATASET: FAIL CLOSED — gap-team reconciliation under "
              "the bar; docs-only (see data/salary_recon_cycle44.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
