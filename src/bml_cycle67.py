#!/usr/bin/env python3
"""BML Cycle 67 (toby series) — SLATE ITEM 4: player health cards
fused into the FA shopping list.

One card per 2027 free agent (all 251 class entries): what the player
will actually give you, not just his headline number.

Method (every field traces to a committed input, stated in the
artifact's metadata):
- Measured availability: the player's 2025-26 IL days = the SUM of
  committed days_in_season across his stints in curated
  fact_il_stints; availability = max(0, 1 - days/364), where 364 is
  the repo's own Cycle 9 denominator (2 x 182 days). Checked: for
  every FA player the summed days never exceed the calendar-day
  union of his stint ranges, so overlapping stints do not inflate
  the sum; 3 players sum above 364 and are floored at 0.
  Players with a player_id but no 2025-26 stint rows read "no IL
  record in committed data" — never 100% by assumption. The 20
  class entries with no player_id in the shopping file are not
  joined at all (name-only joins risk false attribution).
- Delivered-WAR expectation: the Cycle 56 (UNC-2) formula adapted
  to player level. UNC-2 simulated rosters with availability
  draws from the measured pools plus Marcel-backtest residual
  draws; at player level the point estimate replaces the draws
  with their centers: the player's own measured availability
  factor where one exists, else the UNC-2 pool mean for his
  group (hitters 0.912, pitchers 0.807), and the measured mean
  residuals (OBP +0.0008, SLG -0.0078, ERA +0.078) converted
  with the Cycle 48 run-value slopes (OBP 0.2617, SLG 0.2778)
  and Steamer's own fitted runs-to-WAR slopes (hitters 0.1132,
  pitchers 0.0837), at delivered volume (Steamer 2027 PA or IP
  x the availability used). Per-player INTERVALS are not
  derived: a pool-draw interval would present pool variance as
  player risk, so intervals stay scenario-level only (Cycle 56).
- Risk flag: measured availability below the UNC-2 pool's 25th
  percentile for the player's group (hitters 0.890, pitchers
  0.629). Players without a measured factor are not flagged.
- Evidence link: the dominant injury (the stint carrying the
  most 2025-26 IL days; ties broken by latest start) classified
  by keyword only. Clean classifications link to that lane of
  docs/EVIDENCE.html; everything else links to the page top —
  never to a guessed lane. Keyword rules (lowercased injury
  text, first match wins): elbow/ucl/ulnar/tommy john -> UCL
  lane; tendon/achilles/patellar/rotator cuff/acl -> tendon
  lane; hamstring/calf/calif/adductor/quadriceps/quad /groin/
  oblique/muscle/lat strain/latissimus -> muscle lane;
  workload/fatigue/stress reaction -> workload lane.
  ("calif" is the committed injury text's own spelling of one
  calf strain; "adductor" is a muscle group.)
- Current IL status: exact normalized-name match against
  curated fact_il_current (the 2026-11-02 Statyx + FastballAPI
  snapshot); 13 matches, no duplicate names, matching the
  Cycle 51 count.
- Prices stay anchors (Cycle 61 left them untouched): the card
  keeps prev_aav, spotrac_market_aav and war_per_10m_prior_aav,
  and adds delivered_war_per_10m_prior_aav = delivered WAR
  per $10M of the SAME prior AAV — arithmetic on the anchor
  price, labeled as such.

Output: data/fa_health_cards_2027.json. No network.
"""
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

DENOMINATOR = 364  # Cycle 9: 2 x 182 days
PITCHER_POS = {"SP", "RP", "P"}

LANE_RULES = [
    ("lane-ucl", ("elbow", "ucl", "ulnar", "tommy john")),
    ("lane-tendon", ("tendon", "achilles", "patellar", "rotator cuff", "acl")),
    ("lane-muscle", ("hamstring", "calf", "calif", "adductor", "quadriceps",
                     "quad ", "groin", "oblique", "muscle", "lat strain",
                     "latissimus")),
    ("lane-workload", ("workload", "fatigue", "stress reaction")),
]
LANE_NAMES = {
    "lane-ucl": "UCL & elbow",
    "lane-workload": "Workload & prevention",
    "lane-muscle": "Muscle recovery",
    "lane-tendon": "Tendon & biologics",
}


def norm_name(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def classify(injury):
    if injury is None or (isinstance(injury, float) and pd.isna(injury)):
        return None, "dominant stint carries no injury description"
    text = str(injury).lower()
    for lane, keys in LANE_RULES:
        if any(k in text for k in keys):
            return lane, None
    return None, "dominant injury does not classify cleanly"


def main():
    unc = json.loads((DATA / "uncertainty_scenarios_2027.json").read_text())
    pools = unc["availability_pools"]
    beta_obp = unc["run_value_slopes"]["runs_per_pa_per_unit_obp"]
    beta_slg = unc["run_value_slopes"]["runs_per_pa_per_unit_slg"]
    s_h = unc["runs_to_war_scale"]["hitters"]["slope_war_per_run"]
    s_p = unc["runs_to_war_scale"]["pitchers"]["slope_war_per_run"]
    md_obp = unc["error_pools"]["hitters"]["bias_actual_minus_proj_obp"]
    md_slg = unc["error_pools"]["hitters"]["bias_actual_minus_proj_slg"]
    md_era = unc["error_pools"]["pitchers"]["bias_actual_minus_proj_era"]
    pool_mean = {"hitter": pools["hitters"]["mean"],
                 "pitcher": pools["pitchers"]["mean"]}
    pool_p25 = {"hitter": pools["hitters"]["p25"],
                "pitcher": pools["pitchers"]["p25"]}

    shop = json.loads((DATA / "fa_shopping_2027.json").read_text())
    cls = shop["class"]

    stints = pd.read_parquet(DATA / "curated" / "fact_il_stints.parquet")
    s2526 = stints[stints["season"].isin([2025, 2026])].copy()
    s2526["il_start"] = pd.to_datetime(s2526["il_start"])
    days = s2526.groupby("player_id")["days_in_season"].sum().to_dict()

    def dominant_injury(pid):
        g = s2526[s2526["player_id"] == pid]
        if g.empty:
            return None, None
        g = g.sort_values(["days_in_season", "il_start"])
        row = g.iloc[-1]
        inj = row["injury"]
        return (None if pd.isna(inj) else str(inj)), int(row["days_in_season"])

    current = pd.read_parquet(DATA / "curated" / "fact_il_current.parquet")
    cur_by_name = {}
    for _, r in current.iterrows():
        cur_by_name[norm_name(r["player_name"])] = r

    bat = {r["xMLBAMID"]: r
           for r in json.loads((DATA / "fg_steamer_2027_bat.json").read_text())
           if r.get("xMLBAMID")}
    pit = {r["xMLBAMID"]: r
           for r in json.loads((DATA / "fg_steamer_2027_pit.json").read_text())
           if r.get("xMLBAMID")}

    cards = []
    counts = {"with_measured_availability": 0, "no_il_record": 0,
              "not_matched_no_player_id": 0, "classified_lane": 0,
              "page_top_link": 0, "current_il": 0, "risk_flagged": 0,
              "delivered_war_computed": 0, "no_steamer_war": 0}
    for c in cls:
        pid = c.get("player_id")
        group = "pitcher" if c["pos"] in PITCHER_POS else "hitter"
        if pid is None:
            il_days, avail, basis = None, None, (
                "not matched — the shopping file carries no player_id "
                "for this entry, so no IL join was attempted (name-only "
                "joins risk false attribution)")
            counts["not_matched_no_player_id"] += 1
            dom_inj, dom_days = None, None
        elif pid not in days:
            il_days, avail, basis = None, None, (
                "no IL record in committed data — no 2025-26 stint rows "
                "for this player_id")
            counts["no_il_record"] += 1
            dom_inj, dom_days = None, None
        else:
            il_days = int(days[pid])
            avail = max(0.0, 1.0 - il_days / DENOMINATOR)
            basis = ("measured — sum of committed days_in_season across "
                     f"2025-26 stints / {DENOMINATOR}")
            counts["with_measured_availability"] += 1
            dom_inj, dom_days = dominant_injury(pid)
        a_used = avail if avail is not None else pool_mean[group]

        lane, lane_note = (None, None)
        if dom_inj is not None:
            lane, lane_note = classify(dom_inj)
        if lane is not None:
            counts["classified_lane"] += 1
            link = f"../docs/EVIDENCE.html#{lane}"
        else:
            counts["page_top_link"] += 1
            link = "../docs/EVIDENCE.html"

        cur = cur_by_name.get(norm_name(c["name"]))
        cur_obj = None
        if cur is not None:
            counts["current_il"] += 1
            cur_obj = {
                "status": str(cur["status"]),
                "type": (None if pd.isna(cur["type"]) else str(cur["type"])),
                "detail": (None if pd.isna(cur["detail"])
                           else str(cur["detail"])),
                "side": (None if pd.isna(cur["side"]) else str(cur["side"])),
                "return_date": (None if pd.isna(cur["return_date"])
                                else str(cur["return_date"])),
                "pulled_at": str(cur["pulled_at"]),
            }

        war = c.get("steamer_war")
        delivered, vol, vol_kind, resid, del_note = None, None, None, None, None
        if war is None:
            counts["no_steamer_war"] += 1
            del_note = "no Steamer WAR in committed data"
        else:
            if group == "pitcher":
                row = pit.get(pid)
                vol_kind = "IP"
                vol = float(row["IP"]) if row else None
                resid = (-md_era * (vol * a_used / 9.0) * s_p) if vol else 0.0
            else:
                row = bat.get(pid)
                vol_kind = "PA"
                vol = float(row["PA"]) if row else None
                resid = (vol * a_used * (beta_obp * md_obp
                                         + beta_slg * md_slg) * s_h) if vol else 0.0
            if vol is None:
                del_note = (f"residual term omitted — no Steamer {vol_kind} "
                            "row for this player_id")
            delivered = round(war * a_used + resid, 3)
            counts["delivered_war_computed"] += 1

        if avail is not None and avail < pool_p25[group]:
            risk, risk_basis = True, (
                f"below pool p25 ({pool_p25[group]}) for {group}s")
            counts["risk_flagged"] += 1
        elif avail is not None:
            risk, risk_basis = False, (
                f"at or above pool p25 ({pool_p25[group]}) for {group}s")
        else:
            risk, risk_basis = None, (
                "not assessed — no measured availability factor")

        prev_aav = c.get("prev_aav")
        del_per_10m = None
        if delivered is not None and prev_aav:
            del_per_10m = round(delivered / (prev_aav / 1e7), 2)

        cards.append({
            "name": c["name"], "player_id": pid, "pos": c["pos"],
            "prev_team": c["prev_team"], "type": c["type"], "qoi": c["qoi"],
            "group": group,
            "headline_war": war,
            "il_days_2025_26": il_days,
            "availability": (round(avail, 4) if avail is not None else None),
            "availability_basis": basis,
            "availability_used_for_delivered": round(a_used, 4),
            "dominant_injury": dom_inj,
            "dominant_injury_days": dom_days,
            "evidence_lane": lane,
            "evidence_lane_name": LANE_NAMES.get(lane),
            "evidence_link": link,
            "evidence_note": lane_note,
            "current_il": cur_obj,
            "delivered_war": delivered,
            "delivered_war_note": del_note,
            "volume_kind": vol_kind,
            "volume": vol,
            "residual_term_war": (round(resid, 4) if resid is not None else None),
            "risk_flag": risk, "risk_basis": risk_basis,
            "prev_aav": prev_aav,
            "spotrac_market_aav": c.get("spotrac_market_aav"),
            "war_per_10m_prior_aav": c.get("war_per_10m_prior_aav"),
            "delivered_war_per_10m_prior_aav": del_per_10m,
        })

    ranked = sorted((x for x in cards if x["delivered_war"] is not None),
                    key=lambda x: -x["delivered_war"])
    for i, x in enumerate(ranked, 1):
        x["rank_by_delivered_war"] = i
    for x in cards:
        x.setdefault("rank_by_delivered_war", None)
    hranked = sorted((x for x in cards if x["headline_war"] is not None),
                     key=lambda x: -x["headline_war"])
    for i, x in enumerate(hranked, 1):
        x["rank_by_headline_war"] = i
    for x in cards:
        x.setdefault("rank_by_headline_war", None)

    out = {
        "metadata": {
            "cycle": 67,
            "study": "Slate item 4 — player health cards in the FA shopping list",
            "method": (
                "Measured availability = max(0, 1 - days/364), days = sum "
                "of committed days_in_season across the player's 2025-26 "
                "stints in curated fact_il_stints (Cycle 9 denominator, "
                "2 x 182 days). Delivered-WAR expectation = headline "
                "Steamer WAR x availability used + the Cycle 56 "
                "residual-bias term at delivered volume (hitters: PA x "
                "availability x (0.2617 x +0.0008 + 0.2778 x -0.0078) x "
                "0.1132; pitchers: -0.078 x (IP x availability / 9) x "
                "0.0837). Availability used = the player's own measured "
                "factor where one exists, else the UNC-2 pool mean for "
                "his group (hitters 0.912, pitchers 0.807). Per-player "
                "intervals are NOT derived: a pool-draw interval would "
                "present pool variance as player risk, so intervals "
                "stay scenario-level only (Cycle 56). Risk flag = "
                "measured availability below the UNC-2 pool p25 for "
                "the group (hitters 0.890, pitchers 0.629). Evidence "
                "lane from the dominant injury by keyword only; "
                "unclassified injuries link to the evidence page top. "
                "Prices stay prior-contract anchors (Cycle 61 left "
                "them untouched); delivered WAR per $10M is arithmetic "
                "on the same anchor price."),
            "sources": {
                "shopping_class": "data/fa_shopping_2027.json (251 entries)",
                "il_history": "data/curated/fact_il_stints.parquet (2025-26 stints)",
                "current_il": "data/curated/fact_il_current.parquet "
                              "(Statyx + FastballAPI snapshot, pulled 2026-11-02)",
                "volume": "data/fg_steamer_2027_bat.json (PA) / "
                          "data/fg_steamer_2027_pit.json (IP), by xMLBAMID",
                "constants": "data/uncertainty_scenarios_2027.json (Cycle 56)",
                "evidence_page": "docs/EVIDENCE.html (Cycle 57; lane anchors "
                                "added Cycle 67)",
            },
            "counts": counts,
            "pools": {"hitter": {"mean": pool_mean["hitter"],
                                 "p25": pool_p25["hitter"]},
                      "pitcher": {"mean": pool_mean["pitcher"],
                                  "p25": pool_p25["pitcher"]}},
            "denominator_days": DENOMINATOR,
            "capped_at_zero": [x["name"] for x in cards
                               if x["il_days_2025_26"] is not None
                               and x["il_days_2025_26"] > DENOMINATOR],
        },
        "cards": cards,
    }
    (DATA / "fa_health_cards_2027.json").write_text(json.dumps(out, indent=1))
    print("cards:", len(cards), "| counts:", json.dumps(counts))
    print("TOP 5 by delivered WAR:")
    for x in ranked[:5]:
        print(f"  {x['rank_by_delivered_war']}. {x['name']} ({x['pos']}): "
              f"headline {x['headline_war']:.2f} -> delivered "
              f"{x['delivered_war']:.2f} (avail "
              f"{x['availability_used_for_delivered']})")
    print("TOP 5 by headline WAR:")
    for x in hranked[:5]:
        print(f"  {x['rank_by_headline_war']}. {x['name']} ({x['pos']}): "
              f"headline {x['headline_war']:.2f} -> delivered "
              f"{x['delivered_war']}")
    print("capped at zero:", out["metadata"]["capped_at_zero"])


if __name__ == "__main__":
    main()
