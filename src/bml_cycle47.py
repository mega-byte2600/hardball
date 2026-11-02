"""Cycle 47 — Figure 23 rebuild computations.

Computes every NEW number the rebuilt Figure 23 renders, from committed
data only, so each rendered number is reproducible:

- Leaderboard context: the posted trio's ranks / percentiles on the
  2026 qualified NPB leaderboards (data/npb_leaderboards_2024_2026_raw.csv,
  NPB official BIS pull, Cycle 34). Batting context is the player's own
  league board (Central for Sato, Pacific for the two pitchers); the
  pitching context board is the ERA-qualified board (pit_*[0]).
- Sato's K% against the Central League qualified median K%, 2024-2026.
- Itoh's BB% for all three years, computed as BB / batters faced from
  the leaderboards (the trio dataset carries BB% only for 2025-2026;
  the 2024 leaderboard row carries BF = 710, so 2024 is computable —
  2025/2026 are cross-checked against the trio dataset's values).
- The posting-fee curve from the published tiers in
  data/posted_class_2026.json (20% of first $25M, 17.5% of next $25M,
  15% above $50M).

Every trio row used is cross-checked against data/posted_class_2026.json
(BIS canonical) and the checks are printed as a verification table and
stored in the output JSON. No NPB-to-MLB translation factor is computed
or claimed anywhere.

Output: data/fig23_rebuild_2026.json
"""
import json
import os
import re
import unicodedata

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

TRIO = {
    "Teruaki Sato": "佐藤輝明",
    "Kaima Taira": "平良海馬",
    "Hiromi Itoh": "伊藤大海",
}

# ---------------------------------------------------------------- CSV parse
# The raw leaderboard CSV is the Cycle 34 BIS pull concatenated from
# per-page read_html frames, so it carries TWO layouts:
#   layout A (2024 pages): positional columns "0".."26"
#   layout B (2025/2026):   Japanese-named columns
# Batting boards: bat_c[0] / bat_p[0]. Pitching ERA boards: pit_*[0];
# saves board pit_*[1] (Taira's 2025 closer context only).

BAT_POS = ["rank", "name", "team", "AVG", "G", "PA", "AB", "R", "H",
           "2B", "3B", "HR", "TB", "RBI", "SB", "CS", "SH", "SF", "BB",
           "IBB", "HBP", "SO", "GIDP", "SLG", "OBP"]
PIT_POS = ["rank", "name", "team", "ERA", "G", "W", "L", "SV", "HLD",
           "HP", "CG", "SHO", "noBB", "WPct", "BF", "IPw", "IPf", "H",
           "HR", "BB", "IBB", "HBP", "SO", "WP", "BK", "R", "ER"]
BAT_JP = {"順位": "rank", "選手": "name", "打率": "AVG", "試合": "G",
          "打席": "PA", "打数": "AB", "得点": "R", "安打": "H",
          "二塁打": "2B", "三塁打": "3B", "本塁打": "HR", "塁打": "TB",
          "打点": "RBI", "盗塁": "SB", "盗塁刺": "CS", "犠打": "SH",
          "犠飛": "SF", "四球": "BB", "故意四": "IBB", "死球": "HBP",
          "三振": "SO", "併殺打": "GIDP", "長打率": "SLG", "出塁率": "OBP"}
PIT_JP = {"順位": "rank", "投手": "name", "防御率": "ERA", "登板": "G",
          "勝利": "W", "敗北": "L", "セーブ": "SV", "ホールド": "HLD",
          "ＨＰ": "HP", "完投": "CG", "完封勝": "SHO", "無四球": "noBB",
          "勝率": "WPct", "打者": "BF", "投球回": "IP", "安打": "H",
          "本塁打": "HR", "四球": "BB", "故意四": "IBB", "死球": "HBP",
          "三振": "SO", "暴投": "WP", "ボーク": "BK", "失点": "R",
          "自責点": "ER"}


def _norm_name(raw):
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = unicodedata.normalize("NFKC", str(raw))
    s = re.sub(r"\([^)]*\)\s*$", "", s)          # team suffix "(神)"
    s = re.sub(r"\s+", "", s)
    if not s or s in ("選手", "投手", "順位"):
        return None
    return s


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_boards():
    raw = pd.read_csv(os.path.join(
        DATA, "npb_leaderboards_2024_2026_raw.csv"), dtype=str)
    bat, pit, saves = [], [], []
    for _, row in raw.iterrows():
        table = str(row.get("table") or "")
        year = int(row["year"])
        kind = ("bat" if table.startswith("bat") else
                "pit" if table.startswith("pit") else None)
        if kind is None:
            continue
        if kind == "bat" and not table.endswith("[0]"):
            continue
        if kind == "pit" and table.endswith("[2]"):
            continue  # holds board — not used
        rec = {"year": year, "table": table}
        if pd.notna(row.get("選手")) or pd.notna(row.get("投手")):
            mapping = BAT_JP if kind == "bat" else PIT_JP
            for jp, key in mapping.items():
                rec[key] = row.get(jp)
        elif pd.notna(row.get("1")):
            pos = BAT_POS if kind == "bat" else PIT_POS
            for i, key in enumerate(pos):
                rec[key] = row.get(str(i))
            if kind == "pit":
                ipw, ipf = _num(rec.pop("IPw")), _num(rec.pop("IPf"))
                rec["IP"] = (ipw or 0) + (ipf or 0)
        else:
            continue
        rec["name_norm"] = _norm_name(rec.get("name"))
        if rec["name_norm"] is None:
            continue
        for k in list(rec):
            if k not in ("name", "name_norm", "table"):
                rec[k] = _num(rec[k])
        if rec.get("PA") is None and rec.get("BF") is None:
            continue  # footnote / header residue
        (bat if kind == "bat" else saves if table.endswith("[1]")
         else pit).append(rec)
    return bat, pit, saves


def rank_of(pool, value, lower_better=False):
    """Competition rank (1 = best, ties share the best rank) and a
    percentile on the same convention: pct = 100*(n-rank)/(n-1)."""
    if lower_better:
        better = sum(1 for v in pool if v < value)
    else:
        better = sum(1 for v in pool if v > value)
    rank = better + 1
    n = len(pool)
    pct = round(100 * (n - rank) / (n - 1)) if n > 1 else 100
    return rank, pct


def main():
    posted = json.load(open(os.path.join(DATA, "posted_class_2026.json")))
    by_name = {p["name"]: p for p in posted["players"]}
    bat, pit, saves = load_boards()
    verify = []

    def check(item, rendered, source, ok):
        verify.append({"item": item, "rendered": rendered,
                       "source": source, "match": bool(ok)})

    def trio_row(rows, player, year):
        want = unicodedata.normalize("NFKC", TRIO[player]).replace(" ", "")
        for r in rows:
            if r["name_norm"] == want and r["year"] == year:
                return r
        return None

    # ---- cross-check every trio leaderboard row against the trio dataset
    for name in ("Teruaki Sato",):
        for s in by_name[name]["seasons_bis"]:
            r = trio_row(bat, name, s["year"])
            ok = (r is not None and r["PA"] == s["PA"] and r["AB"] == s["AB"]
                  and r["HR"] == s["HR"] and r["RBI"] == s["RBI"]
                  and r["BB"] == s["BB"] and r["SO"] == s["SO"]
                  and abs(r["AVG"] - s["AVG"]) < 0.0005)
            check(f"Sato {s['year']} leaderboard row == trio dataset",
                  "PA/HR/RBI/BB/SO/AVG match" if ok else "MISMATCH",
                  "npb_leaderboards_2024_2026_raw.csv vs posted_class_2026.json",
                  ok)
    for name in ("Kaima Taira", "Hiromi Itoh"):
        for s in by_name[name]["seasons_bis"]:
            rows = saves if s.get("role") == "closer" else pit
            r = trio_row(rows, name, s["year"])
            ok = (r is not None and abs(r["ERA"] - s["ERA"]) < 0.005
                  and abs(r["IP"] - s["IP"]) < 0.001
                  and r["SO"] == s["SO"] and r["BB"] == s["BB"]
                  and r["SV"] == s.get("SV", 0))
            check(f"{name.split()[1]} {s['year']} leaderboard row == trio dataset",
                  "ERA/IP/SO/BB/SV match" if ok else "MISMATCH",
                  "npb_leaderboards_2024_2026_raw.csv vs posted_class_2026.json",
                  ok)

    # ---- 2026 leaderboard context
    def board(rows, table, year=2026):
        return [r for r in rows if r["table"] == table and r["year"] == year]

    cl_bat26 = board(bat, "bat_c[0]")
    pl_pit26 = board(pit, "pit_p[0]")
    sato26 = trio_row(bat, "Teruaki Sato", 2026)
    itoh26 = trio_row(pit, "Hiromi Itoh", 2026)
    taira26 = trio_row(pit, "Kaima Taira", 2026)
    taira25sv = trio_row(saves, "Kaima Taira", 2025)

    def ctx(rows_pool, value, lower_better, fmt):
        rank, pct = rank_of([v for v in rows_pool], value, lower_better)
        return {"value": fmt(value), "rank": rank, "of": len(rows_pool),
                "percentile": pct}

    sato_ops = sato26["OBP"] + sato26["SLG"]
    context = {
        "pools": {
            "central_batting_2026": len(cl_bat26),
            "pacific_pitching_era_2026": len(pl_pit26),
            "pacific_saves_2025": len(board(saves, "pit_p[1]", 2025)),
        },
        "sato": {
            "HR": ctx([r["HR"] for r in cl_bat26], sato26["HR"], False,
                      lambda v: f"{v:.0f}"),
            "RBI": ctx([r["RBI"] for r in cl_bat26], sato26["RBI"], False,
                       lambda v: f"{v:.0f}"),
            "OPS": ctx([r["OBP"] + r["SLG"] for r in cl_bat26], sato_ops,
                       False, lambda v: f"{v:.3f}"),
        },
        "taira": {
            "ERA": ctx([r["ERA"] for r in pl_pit26], taira26["ERA"], True,
                       lambda v: f"{v:.2f}"),
            "SV_2025": ctx([r["SV"] for r in board(saves, "pit_p[1]", 2025)],
                           taira25sv["SV"], False, lambda v: f"{v:.0f}"),
        },
        "itoh": {
            "ERA": ctx([r["ERA"] for r in pl_pit26], itoh26["ERA"], True,
                       lambda v: f"{v:.2f}"),
            "BB_pct": ctx([100 * r["BB"] / r["BF"] for r in pl_pit26
                           if r["BF"]],
                          100 * itoh26["BB"] / itoh26["BF"], True,
                          lambda v: f"{v:.1f}%"),
        },
    }

    # ---- Sato K% vs Central League median K%, 2024-2026
    k_vs = []
    for y in (2024, 2025, 2026):
        pool = [100 * r["SO"] / r["PA"] for r in board(bat, "bat_c[0]", y)
                if r["PA"]]
        med = float(pd.Series(pool).median())
        row = trio_row(bat, "Teruaki Sato", y)
        sk = 100 * row["SO"] / row["PA"]
        posted_k = next(s["K_pct_computed"] for s in
                        by_name["Teruaki Sato"]["seasons_bis"]
                        if s["year"] == y)
        check(f"Sato K% {y}: leaderboard {sk:.1f} == trio dataset {posted_k}",
              f"{sk:.1f}%", "SO/PA from leaderboard vs K_pct_computed",
              abs(sk - posted_k) < 0.051)
        k_vs.append({"year": y, "sato_k_pct": round(sk, 1),
                     "cl_median_k_pct": round(med, 1), "n": len(pool)})

    # ---- Itoh BB% by year from leaderboard BF (2024 is new: the trio
    # dataset has no BF for 2024, the leaderboard does)
    itoh_bb = []
    for y in (2024, 2025, 2026):
        row = trio_row(pit, "Hiromi Itoh", y)
        bb_pct = 100 * row["BB"] / row["BF"]
        posted_row = next(s for s in by_name["Hiromi Itoh"]["seasons_bis"]
                          if s["year"] == y)
        posted_bb = posted_row.get("BB_pct_computed")
        if posted_bb is not None:
            check(f"Itoh BB% {y}: leaderboard {bb_pct:.1f} == trio dataset "
                  f"{posted_bb}", f"{bb_pct:.1f}%",
                  "BB/BF from leaderboard vs BB_pct_computed",
                  abs(bb_pct - posted_bb) < 0.051)
        itoh_bb.append({"year": y, "bb": int(row["BB"]),
                        "bf": int(row["BF"]), "bb_pct": round(bb_pct, 1),
                        "posted_bb_pct": posted_bb})

    # ---- posting-fee curve (tiers from posted_class_2026.json)
    def fee(v):  # contract value $M -> fee $M
        return (0.20 * min(v, 25) + 0.175 * min(max(v - 25, 0), 25)
                + 0.15 * max(v - 50, 0))

    curve = [{"contract_m": v, "fee_m": round(fee(v), 3)}
             for v in range(10, 101, 5)]
    check("Fee on $60M == $10.875M (Cycle 34 worked example)",
          f"${fee(60):.3f}M", "tier formula 20/17.5/15 on $25M bands",
          abs(fee(60) - 10.875) < 1e-9)

    out = {
        "built_by": "src/bml_cycle47.py",
        "sources": [
            "data/posted_class_2026.json (NPB official BIS trio dataset)",
            "data/npb_leaderboards_2024_2026_raw.csv (NPB official BIS "
            "qualified leaderboards, 340 rows, 2024-2026)",
        ],
        "percentile_convention": "rank 1 = best (ties share the best "
                                 "rank); percentile = 100*(n-rank)/(n-1) "
                                 "within the player's own league board",
        "leaderboard_context_2026": context,
        "sato_k_vs_cl_median": k_vs,
        "itoh_bb_pct_by_year": itoh_bb,
        "fee_curve": curve,
        "fee_checkpoints_m": {str(v): round(fee(v), 3)
                              for v in (10, 25, 50, 60, 100)},
        "verification": verify,
    }
    with open(os.path.join(DATA, "fig23_rebuild_2026.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print("=== Cycle 47 verification table ===")
    bad = 0
    for v in verify:
        print(("OK  " if v["match"] else "FAIL"), v["item"], "->",
              v["rendered"])
        bad += 0 if v["match"] else 1
    print(f"=== {len(verify) - bad}/{len(verify)} checks match ===")
    print("pools:", context["pools"])
    print("context:", json.dumps(context, ensure_ascii=False))
    print("sato K vs CL median:", k_vs)
    print("itoh BB%:", itoh_bb)
    print("fee checkpoints:", out["fee_checkpoints_m"])
    if bad:
        raise SystemExit(f"{bad} verification checks FAILED")


if __name__ == "__main__":
    main()
