#!/usr/bin/env python3
"""HARDBALL data-quality gate (poka-yoke).

Encodes the full verification pass of 2026-10-31 as structural checks
that run offline in seconds. Every check corresponds to a failure that
either happened or was hunted that day:

- the silent Savant year-copy trap (bat-tracking files must differ),
- the retracted team-wins claim (formula_prod must stay annotated),
- the 2020-fold units bug (lagged forecast must keep its exclusion),
- ESPN validation misread (HR must match exactly, player by player),
- AZ/ARI-class identity slips (30 teams everywhere teams are counted),
- scenario builders drifting from their constraints (26 men, budget),
- figure references rotting after merges (glossary + talk track).

Run:  python3 src/verify_data.py          (offline gate; exit 1 on fail)
      python3 src/verify_data.py --live   (adds MLB API standings check)

No writes. No network unless --live.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FAIL = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAIL.append(name)


def load(name):
    return json.loads((DATA / name).read_text())


def main() -> int:
    live = "--live" in sys.argv

    # --- required artifacts exist -------------------------------
    required = ["kpi_2025.json", "kpi_2026.json", "panel_2011_2026.csv",
                "projections_2027.json", "projections_2027_pitchers.json",
                "projections_2027_health.json", "fg_benchmark_2027.json",
                "formula_prod.json", "lagged_forecast.json", "wow_scenarios.json",
                "salaries_2026.json", "fa_shopping_2027.json", "pipeline_2026.json",
                "team_explorer.json", "validation_2025.json", "validation_2026.json",
                "cap_scenario_2027.json", "roster_2027.json"]
    missing = [f for f in required if not (DATA / f).exists()]
    check("required artifacts present", not missing, f"missing: {missing}")

    # --- KPI snapshots: 30 teams, sane ranges -------------------
    for yr in (2025, 2026):
        rows = load(f"kpi_{yr}.json")
        ok = (len(rows) == 30
              and all(40 <= r["wins"] <= 115 for r in rows)
              and all(0.28 <= r["OBP"] <= 0.37 for r in rows)
              and len({r["team"] for r in rows}) == 30)
        check(f"kpi_{yr}: 30 unique teams, sane wins/OBP", ok)

    # --- panel --------------------------------------------------
    with open(DATA / "panel_2011_2026.csv") as fh:
        panel = list(csv.DictReader(fh))
    seasons = {r["season"] for r in panel}
    check("panel: >=500 rows, seasons 2011-2026",
          len(panel) >= 500 and len(seasons) == 16,
          f"rows={len(panel)} seasons={len(seasons)}")

    # --- projections --------------------------------------------
    check("projections: >=190 hitters, >=95 pitchers",
          len(load("projections_2027.json")) >= 190
          and len(load("projections_2027_pitchers.json")) >= 95)

    # --- benchmark integrity ------------------------------------
    b = load("fg_benchmark_2027.json")
    h = b["hitters"]
    check("benchmark: all Marcel hitters ID-matched to Steamer",
          h["matched_n"] == h["marcel_n"] and not h.get("unmatched_marcel_ids"),
          f"matched {h['matched_n']}/{h['marcel_n']}")
    check("benchmark: OBP r in [0.80, 0.95]", 0.80 <= h["obp"]["pearson_r"] <= 0.95)

    # --- honesty annotations stay on ----------------------------
    fp = load("formula_prod.json")
    check("formula_prod annotated DIAGNOSTIC ONLY",
          "DIAGNOSTIC ONLY" in str(fp.get("status", "")))
    lf = load("lagged_forecast.json")
    excl = lf.get("excluded_folds", [])
    excl_years = {e.get("feature_season") if isinstance(e, dict) else e for e in excl}
    check("lagged forecast: 2020 fold excluded, grouped MAE < 11",
          2019 in excl_years and lf["grouped_cv"]["mae_mean"] < 11)

    # --- ESPN validation: HR exact, player by player ------------
    for yr in (2025, 2026):
        v = load(f"validation_{yr}.json")
        bad = [p for p in v["players"] if str(p["mlb_hr"]) != str(p["decoded_hr"])]
        check(f"ESPN {yr}: HR exact for all {v['players_compared']} players", not bad,
              f"{len(bad)} HR mismatches")

    # --- Savant: no silent year copies ---------------------------
    hashes = {}
    for y in (2024, 2025, 2026):
        hashes[y] = hashlib.md5((DATA / f"savant_bat_tracking_{y}.json").read_bytes()).hexdigest()
    check("Savant bat-tracking year files all distinct",
          len(set(hashes.values())) == 3)

    # --- scenarios obey their constraints ------------------------
    wow = load("wow_scenarios.json")
    ok = len(wow["scenarios"]) == 3
    for s in wow["scenarios"]:
        ok = ok and len(s["roster"]) == 26 and s["spend"] <= s["budget"]
        ok = ok and abs(sum(p["war"] for p in s["roster"]) - s["total_war"]) <= 0.2
    check("scenarios: 3 budgets, 26 men each, spend <= budget, WAR sums hold", ok)
    check("scenarios: availability stress present (Cycle 27)",
          "availability_stress" in wow)

    # --- SWAP: headline scenarios are the proven-optimal rosters --
    optc = load("optimizer_comparison_2027.json")
    sens = load("optimizer_sensitivity_2027.json")
    opt_by_label = {b["label"]: b["optimizer"] for b in optc["budgets"]}
    rng_by_label = {}
    for scale, key in (("x1.2", "low"), ("x0.8", "high")):
        for e in sens["price_sensitivity"][scale]:
            rng_by_label.setdefault(e["label"], {})[key] = e["total_war"]
    ok = wow["metadata"].get("cycle") == 52
    for s in wow["scenarios"]:
        o = opt_by_label[s["label"]]
        ok = ok and s["total_war"] == o["total_war"] and s["spend"] == o["spend"]
        ok = ok and s.get("proven_optimal") and s.get("mip_gap") == 0
        ok = ok and s["war_range_prices_pm20"]["low"] == rng_by_label[s["label"]]["low"]
        ok = ok and s["war_range_prices_pm20"]["high"] == rng_by_label[s["label"]]["high"]
        st = wow["availability_stress"]["stressed_totals"][s["label"]]
        ok = ok and st["raw_war"] == s["total_war"]
    greedy_bench = {s["label"]: s["total_war"]
                    for s in wow["benchmark_greedy"]["scenarios"]}
    ok = ok and greedy_bench == {"The Floor — $171.2M": 42.0,
                                 "The Middle — $208.0M": 45.7,
                                 "The Cap — $245.3M": 52.3}
    check("SWAP: headline scenarios are the Cycle 49 proven-optimal rosters "
          "with Cycle 50 price-error ranges; greedy preserved as benchmark "
          "(Cycle 52)", ok)

    # --- salaries honesty ----------------------------------------
    sal = load("salaries_2026.json")
    check("salaries: metadata consistent, failures labeled",
          sal["metadata"]["rows"] == len(sal["players"])
          and isinstance(sal["metadata"].get("team_failures"), list))

    # --- FA class -------------------------------------------------
    fa = load("fa_shopping_2027.json")
    with_war = sum(1 for r in fa["class"] if r.get("steamer_war") is not None)
    check("FA class: >=240 players, >=220 with Steamer WAR",
          len(fa["class"]) >= 240 and with_war >= 220,
          f"class={len(fa['class'])} war={with_war}")

    # --- pipeline internal consistency ----------------------------
    pl = load("pipeline_2026.json")
    ranks = sorted(o["rank"] for o in pl["orgs"])
    check("pipeline: 30 orgs, unique ranks 1-30", ranks == list(range(1, 31)))

    # --- payroll.py W-L table parses to 30 rows -------------------
    src = (ROOT / "src" / "payroll.py").read_text()
    rows = re.findall(r'"[A-Z]{2,3}": \("[^"]+", "\d+-\d+"', src)
    check("payroll.py: 30 team W-L rows", len(rows) == 30, f"found {len(rows)}")

    # --- committed dashboard is the current build -----------------
    html = (ROOT / "dashboard" / "hardball_demo.html").read_text(errors="ignore")

    def _mode_figs(mode):
        seg = html.split(f'id="mode-{mode}"', 1)[1]
        seg = re.split(r'id="mode-|<div class="srcbox"', seg)[0]
        return [int(n) for n in re.findall(r'data-mode="' + mode + r'" data-figure="(\d+)"', seg)]

    all_figs = sorted({int(n) for n in re.findall(r'data-figure="(\d+)"', html)})
    n_chapters = len(re.findall(r'class="chapter"', html))
    n_slides = len(re.findall(r'class="slide"', html))
    n_cards = len(re.findall(r'class="pcard"', html))
    explorer_figs = sorted(set(_mode_figs("explorer")))
    check("dashboard HTML: PRESS PLAY present, 25-chart index intact",
          "PRESS PLAY" in html and "all 25 real-data charts" in html)
    check("dashboard HTML: no stale figure references",
          "see Figure 12)" not in html)
    check("dashboard modes: story has exactly 6 chapters",
          n_chapters == 6, f"chapters={n_chapters}")
    check("dashboard modes: boardroom has <=15 slides",
          1 <= n_slides <= 15, f"slides={n_slides}")
    check("dashboard modes: explorer holds every figure the build produced",
          explorer_figs == all_figs and len(all_figs) >= 21,
          f"explorer={explorer_figs} all={all_figs}")
    check("dashboard modes: 8 percentile player cards",
          n_cards == 8, f"cards={n_cards}")
    check("dashboard modes: explorer holds Figure 23 with BIS source label",
          23 in explorer_figs and "NPB official" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: explorer holds Figure 24 with HS verdict box",
          24 in explorer_figs and "INCONCLUSIVE ON MISPRICING" in html
          and "Hakes" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: explorer holds Figure 25 with optimizer audit",
          25 in explorer_figs and "optimizer" in html.lower()
          and "proven optimal" in html,
          f"explorer={explorer_figs}")
    check("dashboard modes: story/boardroom headline the optimizer rosters "
          "(Cycle 52)",
          "floor roster buys 48.9 WAR" in html
          and "The floor roster buys 48.9 WAR" in html
          and "48.9 WAR proven-optimal" in html
          and "floor roster buys 42.0 WAR" not in html
          and "cap roster buys 52.3" not in html)

    # --- Cycle 70: "data as of" stamp traces to the feed artifacts --
    _tk_p = DATA / "tracker_ticker_2026.json"
    _il_p = DATA / "il_current_live.json"
    _ev_p = DATA / "evidence_surveillance.json"
    if _tk_p.exists() and _il_p.exists() and _ev_p.exists():
        _MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        def _md70(iso):
            _y, _m, _d = iso[:10].split("-")
            return f"{_MON[int(_m) - 1]} {int(_d)}"

        _tk_d = json.loads(_tk_p.read_text())["metadata"]["pulled_at"][:10]
        _il_d = json.loads(_il_p.read_text())["metadata"]["pulled_at"][:10]
        _ev_d = json.loads(_ev_p.read_text())["metadata"]["run_date"][:10]
        _head70 = max(_tk_d, _il_d, _ev_d)
        _stamp70 = (f"Data as of {_md70(_head70)}, {_head70[:4]} · "
                    f"tracker {_md70(_tk_d)} · injured list {_md70(_il_d)}"
                    f" · evidence {_md70(_ev_d)}")
        check("Cycle 70: crest data-as-of stamp, every date traced to "
              "its feed artifact", _stamp70 in html,
              f"want: {_stamp70}")
    else:
        check("Cycle 70: crest data-as-of stamp, every date traced to "
              "its feed artifact", False, "a feed artifact is missing")

    # --- Cycle 75: bat-speed exhibit (context only, claim N04) -----
    _bs_path = DATA / "bat_speed_exhibit_2027.json"
    if _bs_path.exists():
        import math as _math

        def _pearson75(xs, ys):
            _n = len(xs)
            _mx = _math.fsum(xs) / _n
            _my = _math.fsum(ys) / _n
            _sxy = _math.fsum((x - _mx) * (y - _my)
                              for x, y in zip(xs, ys))
            _sxx = _math.fsum((x - _mx) ** 2 for x in xs)
            _syy = _math.fsum((y - _my) ** 2 for y in ys)
            return _sxy / _math.sqrt(_sxx * _syy)

        def _quant75(vals, q):
            _sv = sorted(vals)
            _pos = q * (len(_sv) - 1)
            _lo = int(_math.floor(_pos))
            _hi = min(_lo + 1, len(_sv) - 1)
            return _sv[_lo] * (1 - (_pos - _lo)) + _sv[_hi] * (_pos - _lo)

        _bs = json.loads(_bs_path.read_text())
        _boards75 = {}
        for _y in (2024, 2025, 2026):
            _boards75[_y] = {int(r["player_id"]): r for r in json.loads(
                (DATA / f"savant_bat_tracking_{_y}.json").read_text())}
        _px, _py, _pair_r, _pair_n = [], [], {}, {}
        for _a, _b in ((2024, 2025), (2025, 2026)):
            _ids = [p for p in _boards75[_a] if p in _boards75[_b]]
            _xs = [float(_boards75[_a][p]["avg_bat_speed"]) for p in _ids]
            _ys = [float(_boards75[_b][p]["avg_bat_speed"]) for p in _ids]
            _pair_r[f"{_a}_{_b}"] = _pearson75(_xs, _ys)
            _pair_n[f"{_a}_{_b}"] = len(_ids)
            _px += _xs
            _py += _ys
        _pool_r = _pearson75(_px, _py)
        _stab = _bs["stability"]["all_matched"]
        _ok_stab = (
            abs(_pair_r["2024_2025"] - _stab["pairs"]["2024_2025"]["r"])
            < 1e-4
            and abs(_pair_r["2025_2026"]
                    - _stab["pairs"]["2025_2026"]["r"]) < 1e-4
            and abs(_pool_r - _stab["pooled"]["r"]) < 1e-4
            and _stab["pairs"]["2024_2025"]["n"] == _pair_n["2024_2025"]
            and _stab["pairs"]["2025_2026"]["n"] == _pair_n["2025_2026"]
            and _stab["pooled"]["n_pairs"] == len(_px))
        _vals26 = [float(r["avg_bat_speed"])
                   for r in _boards75[2026].values()]
        _dist = _bs["distribution_2026"]
        _ok_dist = (_dist["n"] == len(_vals26) and all(
            abs(_quant75(_vals26, q) - _dist[k]) < 1e-3
            for q, k in ((0.0, "min"), (0.25, "p25"), (0.5, "median"),
                         (0.75, "p75"), (1.0, "max"))))
        _minsw = _bs["top_bottom_2026"]["min_swings"]
        _qual75 = [r for r in _boards75[2026].values()
                   if r["swings_competitive"] >= _minsw]
        _fast = sorted(_qual75,
                       key=lambda r: -float(r["avg_bat_speed"]))[:8]
        _slow = sorted(_qual75,
                       key=lambda r: float(r["avg_bat_speed"]))[:8]
        _ok_tb = (
            [r["name"] for r in _fast]
            == [r["name"] for r in _bs["top_bottom_2026"]["fastest"]]
            and [r["name"] for r in _slow]
            == [r["name"] for r in _bs["top_bottom_2026"]["slowest"]]
            and _bs["top_bottom_2026"]["qualified_n"] == len(_qual75))
        check("Cycle 75: exhibit artifact recomputes from the "
              "committed boards (stability per-pair + pooled, "
              "distribution, top/bottom)",
              _ok_stab and _ok_dist and _ok_tb,
              f"stab={_ok_stab} dist={_ok_dist} tb={_ok_tb} "
              f"pooled r recomputed {_pool_r:.6f} vs artifact "
              f"{_stab['pooled']['r']}")
        _ex75 = html.split('id="mode-explorer"', 1)[1]
        _ex75 = re.split(r'id="mode-|<div class="srcbox"', _ex75)[0]
        _st75 = html.split('id="mode-story"', 1)[1]
        _st75 = _st75.split('id="mode-boardroom"', 1)[0]
        _mi = _ex75.find("Bat speed, up close")
        _seg = ""
        if _mi >= 0:
            _rest = _ex75[_mi:]
            _cut = _rest.find('class="panel"')
            _seg = _rest[:_cut] if _cut > 0 else _rest[:8000]
        _reg75 = json.loads((DATA / "claims_register.json").read_text())
        _n04 = next(c for c in _reg75["claims"] if c["id"] == "N04")
        check("Cycle 75: exhibit renders under Figure 19 in Explorer "
              "only, N04 label present, register claim quoted "
              "verbatim, rendered stats match the artifact",
              _mi >= 0 and "Bat speed, up close" not in _st75
              and "Context only — bat speed was tested as a "
              "projection adjustment and dropped" in _seg
              and "NOT SUPPORTED" in _seg
              and _n04["claim"] in _seg
              and f"{_stab['pooled']['r']:.3f}" in _seg
              and f"{_dist['median']:.1f}" in _seg
              and _bs["top_bottom_2026"]["fastest"][0]["name"] in _seg
              and _bs["top_bottom_2026"]["slowest"][0]["name"] in _seg,
              "panel present in explorer" if _mi >= 0
              else "panel missing from explorer")
        check("Cycle 75: exhibit carries no projection-claim "
              "wording for bat speed",
              _mi >= 0
              and "improves projection" not in _seg.lower()
              and "improve projections" not in _seg.lower()
              and "better projection" not in _seg.lower()
              and "boosts projection" not in _seg.lower(),
              "banned wording found in the exhibit segment")
    else:
        check("Cycle 75: exhibit artifact recomputes from the "
              "committed boards (stability per-pair + pooled, "
              "distribution, top/bottom)", False,
              "bat_speed_exhibit_2027.json missing")
        check("Cycle 75: exhibit renders under Figure 19 in Explorer "
              "only, N04 label present, register claim quoted "
              "verbatim, rendered stats match the artifact", False,
              "bat_speed_exhibit_2027.json missing")
        check("Cycle 75: exhibit carries no projection-claim "
              "wording for bat speed", False,
              "bat_speed_exhibit_2027.json missing")

    # --- Cycle 76: noir record-book theme (presentation only) -------
    _root76 = dict(re.findall(r"--(ink|panel|paper|paper-dim|accent|gold)"
                              r":\s*(#[0-9A-Fa-f]{6})", html))
    _want76 = {"ink": "#041e42", "panel": "#092c5c", "paper": "#ffffff",
               "paper-dim": "#8fbce6", "accent": "#bf0d3e",
               "gold": "#f5d130"}
    check("Cycle 76: :root carries the MLB + Rays token palette",
          {k: v.lower() for k, v in _root76.items()} == _want76,
          f"tokens={_root76}")
    check("Cycle 76: no brass, no old page bg, no old ink in the build",
          "#c9a227" not in html.lower() and "#f4f1ea" not in html.lower()
          and "#14213d" not in html.lower())
    _sw76 = [h.lower() for h in re.findall(
        r'class="sw" style="background:(#[0-9A-Fa-f]{6})"', html)][:4]
    _grp76 = ["#43b581", "#e08a3c", "#8fbce6", "#bf0d3e"]
    check("Cycle 76: color-key swatches equal the group trace hexes",
          _sw76 == _grp76
          and all(g in html.lower() for g in _grp76),
          f"swatches={_sw76}")

    def _lum76(hexs):
        _h = hexs.lstrip("#")
        _rgb = [int(_h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        _f = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
              for c in _rgb]
        return 0.2126 * _f[0] + 0.7152 * _f[1] + 0.0722 * _f[2]

    def _cr76(a, b):
        _la, _lb = _lum76(a), _lum76(b)
        return (max(_la, _lb) + 0.05) / (min(_la, _lb) + 0.05)

    if {k: v.lower() for k, v in _root76.items()} == _want76:
        _pairs76 = [(_cr76("#ffffff", _want76["ink"]), 4.5, "paper/ink"),
                    (_cr76("#8fbce6", _want76["ink"]), 4.5, "dim/ink"),
                    (_cr76("#ffffff", _want76["panel"]), 4.5, "paper/panel"),
                    (_cr76("#8fbce6", _want76["panel"]), 4.5, "dim/panel"),
                    (_cr76("#ffffff", _want76["accent"]), 4.5, "paper/accent"),
                    (_cr76("#f5d130", _want76["ink"]), 3.0, "gold/ink")]
        _bad76 = [f"{n}={r:.2f}" for r, m, n in _pairs76 if r < m]
        check("Cycle 76: WCAG contrast minimums met on the token pairs",
              not _bad76, f"failing: {_bad76}")
    else:
        check("Cycle 76: WCAG contrast minimums met on the token pairs",
              False, "token palette mismatch")
    check("Cycle 76: record-book type wired (fonts + Fraunces titles + "
          "transparent figure ground)",
          "fonts.googleapis.com" in html and "Fraunces" in html
          and '"paper_bgcolor":"rgba(0,0,0,0)"' in html)

    # --- HS-2 verdict artifact: status + benchmark on record -------
    hs_path = DATA / "hakes_sauer_verdict.json"
    if hs_path.exists():
        hs = json.loads(hs_path.read_text())
        check("HS-2: verdict artifact present, inconclusive, benchmark recorded",
              hs["verdict"]["status"] == "INCONCLUSIVE on mispricing"
              and hs["benchmark_attempt"]["n_team_seasons"] == 480
              and hs["benchmark_attempt"]["status"].startswith("DEFENSIBLE")
              and hs["formal_test"]["status"] == "RUN",
              f"status={hs.get('verdict', {}).get('status')}")
    else:
        check("HS-2: verdict artifact present, inconclusive, benchmark recorded",
              False, "data/hakes_sauer_verdict.json missing")
    footer_sources = ["MLB Stats API", "Baseball Savant", "ESPN", "Steamer",
                      "Spotrac", "Cot's", "Chadwick", "Injury Report",
                      "NPB official BIS", "Baseball-Reference", "Statyx",
                      "FastballAPI", "ALL DATA &amp; API SOURCES"]
    missing_src = [s for s in footer_sources if s not in html]
    check("dashboard footer: all data & API sources listed (Cycle 45)",
          not missing_src, f"missing: {missing_src}")

    # --- posted class: trio dataset present and verified ----------
    posted = DATA / "posted_class_2026.json"
    if posted.exists():
        pj = json.loads(posted.read_text())
        names = {p["name"] for p in pj["players"]}
        check("posted class: trio JSON present, 3 players + posting facts",
              len(pj["players"]) == 3
              and names == {"Teruaki Sato", "Kaima Taira", "Hiromi Itoh"}
              and pj["posting_facts"]["signing_deadline"] == "2026-12-16 17:00 ET"
              and "BIS" in str(pj["canonical_source"]["name"]),
              f"players={sorted(names)}")
    else:
        check("posted class: trio JSON present, 3 players + posting facts", False,
              "data/posted_class_2026.json missing")

    # --- talk track references exist in the merged deck -----------
    tt = (ROOT / "docs" / "TALKTRACK.md").read_text()
    refs = {int(n) for n in re.findall(r"Figure (\d+)", tt)}
    check("talk track: all figure references <= 25", refs and max(refs) <= 25,
          f"refs: {sorted(refs)}")

    # --- OPT-1 optimizer artifact: comparison on record -----------
    opt_path = DATA / "optimizer_comparison_2027.json"
    if opt_path.exists():
        opt = json.loads(opt_path.read_text())
        ok = len(opt["budgets"]) == 3
        for b in opt["budgets"]:
            ok = ok and len(b["greedy"]["roster"]) == 26
            ok = ok and len(b["optimizer"]["roster"]) == 26
            ok = ok and b["greedy"]["spend"] <= b["budget"]
            ok = ok and b["optimizer"]["spend"] <= b["budget"]
            ok = ok and b["optimizer"]["total_war"] >= b["greedy"]["total_war"]
            ok = ok and b["optimizer"]["proven_optimal"]
            ok = ok and b["optimizer"]["mip_gap"] == 0
            ok = ok and b["greedy"]["satisfies_15pct_rule"]
            ok = ok and b["optimizer"]["satisfies_15pct_rule"]
        check("OPT-1: 3 budgets, 26-man rosters, spend <= budget, optima "
              "proven, 15% rule holds for greedy and optimizer", ok)
    else:
        check("OPT-1: 3 budgets, 26-man rosters, spend <= budget, optima "
              "proven, 15% rule holds for greedy and optimizer", False,
              "data/optimizer_comparison_2027.json missing")

    # --- OPT-2 sensitivity artifact: scenarios on record ----------
    sens_path = DATA / "optimizer_sensitivity_2027.json"
    if sens_path.exists():
        s = json.loads(sens_path.read_text())
        ok = True
        for scale in ("x0.8", "x1.2"):
            entries = s["price_sensitivity"][scale]
            ok = ok and len(entries) == 3
            for e in entries:
                ok = ok and len(e["roster"]) == 26
                ok = ok and e["spend_scenario_prices"] <= e["budget"] + 1
                ok = ok and e["proven_optimal"] and e["mip_gap"] == 0
                ok = ok and 0 <= e["n_changed"] <= 26
        tb = s["targeted_bid_up"]
        ok = ok and len(tb["roster"]) == 26 and tb["proven_optimal"]
        ok = ok and tb["spend_scenario_prices"] <= tb["budget"] + 1
        for e in s["war_haircut"]:
            ok = ok and len(e["roster"]) == 26 and e["proven_optimal"]
            ok = ok and e["spend"] <= e["budget"] + 1
            # re-scored on base WAR, a haircut roster cannot beat the
            # proven base optimum and cannot score below its own
            # haircut value
            ok = ok and e["total_war_haircut"] <= \
                e["total_war_base_rescore"] + 0.05
        base_floor = s["base_optimizer"]["The Floor — $171.2M"]
        for e in s["war_haircut"]:
            ref = s["base_optimizer"][e["label"]]["total_war"]
            ok = ok and e["total_war_base_rescore"] <= ref + 0.05
        m = s["mixed_floor"]
        ok = ok and len(m["roster"]) == 26
        ok = ok and m["n_prearb_slots"] + m["n_fa_slots"] == 26
        ok = ok and m["spend"] <= m["budget"] + 1
        ok = ok and m["proven_optimal"] and m["mip_gap"] == 0
        ok = ok and m["total_war"] >= base_floor["total_war"]
        ok = ok and all(r["prev_aav"] == 1000000 for r in m["roster"]
                        if r["origin"] == "pre-arb")
        ok = ok and s["metadata"]["prearb_pool"]["pool_size"] >= 100
        check("OPT-2: price/targeted/haircut scenarios proven, mixed "
              "floor 26-man with $1M-placeholder pre-arb slots, spend "
              "within budget", ok)
    else:
        check("OPT-2: price/targeted/haircut scenarios proven, mixed "
              "floor 26-man with $1M-placeholder pre-arb slots, spend "
              "within budget", False,
              "data/optimizer_sensitivity_2027.json missing")

    # --- API-1 live-feed layer: artifact on record -----------------
    ilc_path = DATA / "il_current_live.json"
    if ilc_path.exists():
        ilc = json.loads(ilc_path.read_text())
        ov = ilc["fa_overlay"]
        sc = ilc["reconciliation"]["standings_check_fastball_vs_kpi_2026"]
        check("API-1: live-IL artifact consistent (union >= 150, FA "
              "overlay counts hold, Fastball standings agree 30/30)",
              len(ilc["rows"]) >= 150
              and ov["n_matched"] == len(ov["players"])
              and ov["n_differs_from_static"]
              == sum(1 for p in ov["players"] if p["differs_from_static"])
              and sc["teams_compared"] == 30
              and sc["wins_and_runs_agree"] == 30,
              f"rows={len(ilc['rows'])} matched={ov['n_matched']} "
              f"agree={sc['wins_and_runs_agree']}")
        check("API-1: health figure carries the live-IL picture (Cycle 51)",
              "Current IL picture" in html and "fact_il_current" in html)
    else:
        check("API-1: live-IL artifact consistent (union >= 150, FA "
              "overlay counts hold, Fastball standings agree 30/30)",
              False, "data/il_current_live.json missing")

    # --- UNC-1 availability-cap backtest: artifact on record -----
    unc1_path = DATA / "unc1_availability_backtest.json"
    if unc1_path.exists():
        u = json.loads(unc1_path.read_text())
        rows = u["rows"]
        pooled = u["pooled"]
        ok = (u["verdict"] in ("SUPPORTED", "MIXED", "NOT SUPPORTED")
              and set(u["per_class"]) == {"2022", "2023", "2024"}
              and len(rows) == pooled["n"] >= 30
              and all(r["target_season"] in (2022, 2023, 2024) for r in rows)
              and all(0.3 <= r["avail_pct"] <= 1.0 for r in rows))
        # pooled MAEs recomputed from rows must match the artifact
        for key in ("flat500", "flat500_capped", "marcel_pa", "marcel_pa_capped"):
            mae = sum(abs(r[key] - r["actual_pa"]) for r in rows) / len(rows)
            ok = ok and abs(mae - pooled[f"mae_{key}"]) < 0.2
        # verdict must follow its declared rule on the pooled MAEs
        flat_win = pooled["mae_flat500_capped"] < pooled["mae_flat500"]
        marcel_win = pooled["mae_marcel_pa_capped"] < pooled["mae_marcel_pa"]
        expect = ("SUPPORTED" if (flat_win and marcel_win)
                  else "MIXED" if (flat_win or marcel_win) else "NOT SUPPORTED")
        ok = ok and u["verdict"] == expect
        check("UNC-1: backtest artifact consistent (3 FA classes, pooled "
              "MAEs recompute, verdict follows declared rule)",
              ok, f"verdict={u['verdict']} n={pooled['n']}")
    else:
        check("UNC-1: backtest artifact consistent (3 FA classes, pooled "
              "MAEs recompute, verdict follows declared rule)",
              False, "data/unc1_availability_backtest.json missing")

    # --- PRICE-1 price-model workpaper (Cycle 61) -----------------
    pm_path = DATA / "price_model_workpaper_2027.json"
    if pm_path.exists():
        pm = json.loads(pm_path.read_text())
        ok = (pm["verdict"] == "NOT RUN — TRAINING DATA ABSENT"
              and pm["bar"]["threshold_fraction"] == 0.10
              and "UNTESTED" in pm["bar"]["status"]
              and "2024" in pm["model_design_preregistered"]["validation"]
              and len(pm["missing_source"]["readiness_criteria"]) >= 3
              and pm["dashboard_change"] == "none")
        check("PRICE-1: workpaper on record (verdict NOT RUN — "
              "training data absent, bar pre-committed at 10%, "
              "design pre-registered)", ok,
              f"verdict={pm.get('verdict')}")
        # survivorship table recomputes from the Cot's strings
        cots = load("salaries_cots_2027.json")["players"]
        pat = re.compile(r"^(\d+)\s*y/\$([\d.]+)M\s*\((\d+)-(\d+)\)")
        spans = {}
        for r in cots:
            m = pat.match(r.get("contract") or "")
            if m:
                spans.setdefault(2000 + int(m.group(3)), []).append(
                    int(m.group(1)))
        sv = pm["survivorship"]
        ok = (sv["parseable_contracts"] == sum(len(v)
                                               for v in spans.values()))
        for cls, span in (("2022", 2023), ("2023", 2024),
                          ("2024", 2025)):
            got = spans.get(span, [])
            rec = sv["classes"][cls]
            ok = (ok and rec["n_terms_recoverable"] == len(got)
                  and rec["min_years"] == (min(got) if got else None)
                  and rec["one_year_deals"]
                  == sum(1 for y in got if y == 1))
        check("PRICE-1: survivorship table recomputes from Cot's "
              "contract strings (24 / 18 / 35, no 1-year deals)",
              ok)
        # the incumbent anchor basis must be untouched by the cycle
        opt = load("optimizer_comparison_2027.json")
        fa_rows = load("fa_shopping_2027.json")["class"]
        ok = ("last-price anchor" in opt["metadata"]["price_basis"]
              and len(fa_rows) == pm["incumbent"]["fa_class_n"] == 251
              and sum(1 for r in fa_rows if r.get("prev_aav"))
              == pm["incumbent"]["prev_aav_coverage"])
        check("PRICE-1: incumbent anchor basis unchanged (optimizer "
              "still prior-AAV, 251-class coverage intact)", ok)
    else:
        check("PRICE-1: workpaper on record (verdict NOT RUN — "
              "training data absent, bar pre-committed at 10%, "
              "design pre-registered)",
              False, "data/price_model_workpaper_2027.json missing")
        check("PRICE-1: survivorship table recomputes from Cot's "
              "contract strings (24 / 18 / 35, no 1-year deals)",
              False, "data/price_model_workpaper_2027.json missing")
        check("PRICE-1: incumbent anchor basis unchanged (optimizer "
              "still prior-AAV, 251-class coverage intact)",
              False, "data/price_model_workpaper_2027.json missing")

    # --- BLEND-1 projection benchmark (Cycle 62) ------------------
    bl_path = DATA / "projection_blend_2027.json"
    if bl_path.exists():
        bl = json.loads(bl_path.read_text())
        ok = (bl["verdict"].startswith("NOT ADOPTED")
              and bl["blend"]["weights"] is None
              and bl["blend"]["blended_2027_projections"] is None
              and bl["shadow_run"] is None
              and bl["steamer_status"]["status"].startswith("NOT SCOREABLE"))
        for grp, mets in (("hitters", ("OBP", "SLG")),
                          ("pitchers", ("ERA", "WHIP"))):
            for win in ("2025", "2026"):
                for met in mets:
                    cell = bl["results"][grp][win][met]
                    for fc in ("naive", "marcel"):
                        m = cell[fc]
                        ok = ok and m["n"] == bl["paired_n"][grp][win] > 0 \
                            and m["r"] is not None and m["rmse"] > 0 \
                            and m["mae"] > 0
                    for fc in ("steamer", "blend"):
                        ok = ok and cell[fc]["status"] == "not_scored"
        check("BLEND-1: benchmark artifact complete (four forecasters x "
              "both groups x both windows, paired n consistent, blend "
              "not adopted, no weights fit)", ok,
              f"verdict={bl.get('verdict', '')[:40]}")
        # the recorded reproduction anchor must equal the committed
        # Cycles 21/24 variant-B backtests, cell for cell
        ra = bl["design"]["reproduction_anchor"]
        mb, pb = load("marcel_backtest.json"), load("pitcher_backtest.json")
        ok = all(ra[f"hitters_{t}"] == mb["targets"][str(t)]["B_3season"]
                 and ra[f"pitchers_{t}"] == pb["targets"][str(t)]["B_3season"]
                 for t in (2025, 2026))
        # and on the 2026 judge window Marcel must beat the naive on
        # both primary MAEs, as the panel states
        ok = ok and bl["results"]["hitters"]["2026"]["OBP"]["marcel"]["mae"] \
            < bl["results"]["hitters"]["2026"]["OBP"]["naive"]["mae"]
        ok = ok and bl["results"]["pitchers"]["2026"]["ERA"]["marcel"]["mae"] \
            < bl["results"]["pitchers"]["2026"]["ERA"]["naive"]["mae"]
        check("BLEND-1: reproduction anchor matches committed backtests; "
              "Marcel beats naive on both 2026 primary MAEs", ok)
        hn = bl["paired_n"]["hitters"]["2026"]
        pn = bl["paired_n"]["pitchers"]["2026"]
        check("BLEND-1: dashboard panel under Figure 18 (title, table, "
              "not-scored rows, blend status verbatim)",
              "How good are these projections?" in html
              and "Last season, repeated" in html
              and "Steamer + Marcel blend" in html
              and "not scored" in html
              and "Blend status: not adopted" in html
              and f"Hitters n = {hn}" in html
              and f"pitchers n = {pn}" in html)
    else:
        check("BLEND-1: benchmark artifact complete (four forecasters x "
              "both groups x both windows, paired n consistent, blend "
              "not adopted, no weights fit)", False,
              "data/projection_blend_2027.json missing")
        check("BLEND-1: reproduction anchor matches committed backtests; "
              "Marcel beats naive on both 2026 primary MAEs", False,
              "data/projection_blend_2027.json missing")
        check("BLEND-1: dashboard panel under Figure 18 (title, table, "
              "not-scored rows, blend status verbatim)", False,
              "data/projection_blend_2027.json missing")

    # --- Cap Transition ledger (Cycle 64) -------------------------
    ctl_path = DATA / "cap_transition_2027.json"
    if ctl_path.exists():
        import math as _math
        ctl = json.loads(ctl_path.read_text())
        rows64 = ctl["teams"]
        cap64 = {t["team"]: t
                 for t in load("cap_scenario_2027.json")["teams"]}
        summ64 = ctl["summary"]
        check("CAPLEDGER: artifact complete (30 rows, basis labeled on "
              "every row, both summaries reconcile)",
              len(rows64) == 30
              and {r["team"] for r in rows64} == set(cap64)
              and all(r["payroll_basis"] == "Spotrac payroll total"
                      for r in rows64)
              and all(r["cots_sensitivity"]["basis"].startswith(
                          "Cot's published") for r in rows64)
              and summ64["primary"]["OVER CAP"]["count"] == 7
              and summ64["primary"]["UNDER FLOOR"]["count"] == 15
              and summ64["primary"]["INSIDE THE BAND"]["count"] == 8
              and summ64["cots_published_rows"]["OVER CAP"]["count"] == 1
              and summ64["status_changes_between_bases"]["count"]
                  == sum(1 for r in rows64
                         if not r["cots_sensitivity"]
                                    ["agrees_with_primary"])
              and summ64["per_player_flags_total"]
                  == sum(r["per_player_max_check"]["count"]
                         for r in rows64),
              f"rows={len(rows64)}")
        fa64 = load("fa_shopping_2027.json")["class"]
        prices64 = sorted(p["prev_aav"] for p in fa64
                          if p.get("prev_aav")
                          and p.get("steamer_war") is not None)
        median64 = prices64[len(prices64) // 2]
        flags64 = {}
        for p in load("salaries_cots_2027.json")["players"]:
            if p.get("cb_2027_aav") and p["cb_2027_aav"] > 36795000:
                flags64.setdefault(p["team"], set()).add(p["name"])
        ok64 = len(prices64) == 199 and median64 == 4500000
        for r in rows64:
            t = cap64[r["team"]]
            st = ("OVER CAP" if t["gap_to_cap"] > 0 else
                  "UNDER FLOOR" if t["gap_to_floor"] > 0 else
                  "INSIDE THE BAND")
            a = r["action"]
            ok64 = ok64 and r["payroll"] == int(round(245300000
                                                      + t["gap_to_cap"])) \
                and r["status"] == st
            if st == "OVER CAP" and a["covered"]:
                ok64 = ok64 and a["shed_total"] >= t["gap_to_cap"] \
                    and a["shed_total"] == sum(
                        c.get("salary_2026",
                              c.get("salary_cots_lrp_2027"))
                        for c in a["contracts"])
                if r["team"] == "CHC":
                    # Cycle 74: CHC's set is on the Cot's basis.
                    ok64 = ok64 and "Cot's LRP 2027" in a["basis"] \
                        and a["shed_total"] == 29527000 \
                        and a["contracts"][0]["name"] == "Alex Bregman"
            if st == "OVER CAP" and not a["covered"]:
                # Cycle 74: every over-cap team is covered now.
                ok64 = False
            if st == "UNDER FLOOR":
                ok64 = ok64 and a["equivalent_signings_at_pool_median"] \
                    == _math.ceil(t["gap_to_floor"] / median64)
            code = "CWS" if r["team"] == "CHW" else r["team"]
            ok64 = ok64 and {f["name"] for f in
                             r["per_player_max_check"]["flags"]} \
                == flags64.get(code, set())
        check("CAPLEDGER: status arithmetic recomputes from committed "
              "payrolls (shed sets cover their gaps, CHC covered on "
              "Cot's LRP 2027, spend counts at the pool median, AAV "
              "flags recompute)",
              ok64)
        board64 = (html.split('id="mode-boardroom"', 1)[1]
                   if 'id="mode-boardroom"' in html else "")
        strip64 = ("Primary basis (Spotrac payroll totals): 7 over cap "
                   "($358.2M over) · 15 under floor ($807.8M short) · "
                   "8 inside the band.")
        check("CAPLEDGER: ledger panel leads Boardroom (title, summary "
              "strip, CHC Bregman line, disagreement count verbatim)",
              "2027 Cap Transition ledger" in board64
              and strip64 in board64
              and "Alex Bregman ($29.5M" in board64
              and "salary basis: Cot's LRP 2027 (Cycle 74)" in board64
              and "shed set not covered" not in board64
              and "Status differs from the primary basis for 13 teams"
                  in board64
              and -1 < board64.find("2027 Cap Transition ledger")
                  < board64.find("Slide 1 of 15"))
    else:
        check("CAPLEDGER: artifact complete (30 rows, basis labeled on "
              "every row, both summaries reconcile)", False,
              "data/cap_transition_2027.json missing")
        check("CAPLEDGER: status arithmetic recomputes from committed "
              "payrolls (shed sets cover their gaps, CHC covered on "
              "Cot's LRP 2027, spend counts at the pool median, AAV "
              "flags recompute)",
              False, "data/cap_transition_2027.json missing")
        check("CAPLEDGER: ledger panel leads Boardroom (title, summary "
              "strip, CHC line, disagreement count verbatim)", False,
              "data/cap_transition_2027.json missing")

    # --- Cycle 74: salary completion (Cot's full parse, reconciliation) ----
    _c74_names = [
        "CYCLE74: full Cot's parse committed (2,240 rows, 30 teams) "
        "and its 237 figure rows are identical to the Cycle 44 file",
        "CYCLE74: reconciliation recomputes (Spotrac totals == ledger "
        "payrolls, Cot's row sums match, mean 0.63% / worst SD 3.07% / "
        "26 of 30 within 2%, CHC gap $4,019,956 pinned)",
        "CYCLE74: three-basis shed sets recompute from the committed "
        "salary files and match the artifact; CHC set is Bregman "
        "alone on the Cot's LRP basis",
        "CYCLE74: USA TODAY corroboration present as a different-basis "
        "snapshot (not a merge source) with the Guerrero Jr. player "
        "check exact",
        "CYCLE74: dashboard carries the 7-of-7 coverage copy with the "
        "reconciliation result and the CHC set"]
    if (DATA / "salaries_cots_full_2027.json").exists() \
            and (DATA / "salary_reconciliation_2027.json").exists():
        cf74 = load("salaries_cots_full_2027.json")
        recon74 = load("salary_reconciliation_2027.json")
        rows74 = cf74["players"]
        fig74 = [r for r in rows74 if r["lrp_2027"] is not None]

        def _n74(team, name, val):
            return ("CHW" if team in ("CWS", "CHW") else team), name, val
        check(_c74_names[0],
              len(rows74) == cf74["metadata"]["rows"] == 2240
              and len({r["team"] for r in rows74}) == 30
              and sorted(_n74(r["team"], r["name"], r["lrp_2027"])
                         for r in fig74)
                  == sorted(_n74(r["team"], r["name"],
                                 r["salary_lrp_2027"])
                            for r in load("salaries_cots_2027.json")
                            ["players"])
              and all(r["source"] == "cots_baseball_prospectus"
                      for r in rows74),
              f"rows={len(rows74)} figures={len(fig74)}")
        led74 = {t["team"]: t["payroll"]
                 for t in load("cap_transition_2027.json")["teams"]}
        sums74 = {}
        for r in rows74:
            sums74[r["team"]] = sums74.get(r["team"], 0) \
                + (r["lrp_2026"] or 0)
        ok74 = len(recon74["team_totals"]) == 30
        diffs74 = []
        for t in recon74["team_totals"]:
            d = round(100.0 * (t["cots_sheet_total"] - t["spotrac_total"])
                      / t["spotrac_total"], 2)
            diffs74.append(abs(d))
            ok74 = ok74 and t["spotrac_total"] == led74[t["team"]] \
                and t["sheet_rows_sum_2026"] == sums74[t["team"]] \
                and t["diff_pct"] == d
        summ74 = recon74["totals_summary"]
        ok74 = ok74 \
            and summ74["mean_abs_diff_pct"] \
                == round(sum(diffs74) / len(diffs74), 2) == 0.63 \
            and summ74["worst_abs_diff_pct"] == max(diffs74) == 3.07 \
            and summ74["worst_team"] == "SD" \
            and summ74["within_2pct"] \
                == sum(1 for d in diffs74 if d <= 2.0) == 26 \
            and recon74["chc"]["gap_to_cap"] == 4019956 \
            and recon74["chc"]["payroll_spotrac_total"] \
                - recon74["chc"]["cap"] == 4019956 \
            and recon74["chc"]["largest_2027_guarantee"]["name"] \
                == "Alex Bregman" \
            and recon74["chc"]["largest_2027_guarantee"]["lrp_2027"] \
                == 29527000
        check(_c74_names[1], ok74)

        def _prefix74(pairs, gap):
            out, tot = [], 0.0
            for nm, amt in sorted(pairs, key=lambda x: -x[1]):
                if tot >= gap:
                    break
                out.append(nm)
                tot += amt
            return sorted(out)

        def _nkey74(name):
            # same normalization as src/bml_cycle74.py name_key
            toks = re.sub(r"[^a-z ]", "", name.lower()).split()
            return " ".join(t for t in toks if t != "jr")
        sal74 = load("salaries_2026.json")["players"]
        fs74 = {t["team"]: t
                for t in load("forced_sellers_2027.json")["teams"]}
        ok74b = True
        for cv in recon74["shed_cross_validation"]:
            team = cv["team"]
            gap = fs74[team]["gap_to_cap"]
            spot = _prefix74([(r["name"], r["salary_2026"])
                              for r in sal74 if r["team"] == team], gap)
            lrp = _prefix74([(r["name"], r["lrp_2027"])
                             for r in fig74 if r["team"] == team], gap)
            aav = _prefix74([(r["name"], r["cb_2027_aav"])
                             for r in rows74 if r["team"] == team
                             and r["cb_2027_aav"]], gap)
            ok74b = ok74b \
                and sorted(s["name"] for s in cv["spotrac"]["players"]) \
                    == spot \
                and sorted(s["name"]
                           for s in cv["cots_lrp_2027"]["players"]) \
                    == lrp \
                and sorted(s["name"]
                           for s in cv["cots_aav_2027"]["players"]) \
                    == aav \
                and cv["lrp_matches_spotrac"] == (
                    [_nkey74(n) for n in lrp]
                    == [_nkey74(n) for n in spot]) \
                and cv["aav_matches_spotrac"] == (
                    [_nkey74(n) for n in aav]
                    == [_nkey74(n) for n in spot])
            if team != "CHC":
                ok74b = ok74b and sorted(
                    s["name"] for s in fs74[team]["shed"]) == spot
        ok74b = ok74b and fs74["CHC"]["covered"] \
            and fs74["CHC"]["basis"] == "cots_lrp_2027" \
            and [s["name"] for s in fs74["CHC"]["shed"]] \
                == ["Alex Bregman"] \
            and fs74["CHC"]["shed_total"] == 29527000
        check(_c74_names[2], ok74b)
        ut74 = recon74["usa_today_corroboration"]
        guer74 = next(r["salary_2026"] for r in sal74
                      if r["team"] == "TOR" and "Guerrero" in r["name"])
        utrows74 = {r["team"]: r for r in ut74["rows"]}
        ok74c = "Different basis" in ut74["basis_label"] \
            and "never merged" in ut74["basis_label"] \
            and ut74["player_check"]["demo_spotrac_row_2027_basis"] \
                == 40214286 \
            and ut74["player_check"]["usa_today_2026"] == 40214286 \
            and ut74["player_check"]["exact_match"] is True \
            and guer74 == 40214286 \
            and len(utrows74) == 30 \
            and ut74["named_checks"]["within_half_pct"] \
                == ["NYM", "LAD", "CLE", "ATH", "MIA"] \
            and ut74["named_checks"]["within_3pct"] \
                == ["NYY", "MIL", "TB"]
        for _t74 in ("NYM", "LAD", "CLE", "ATH", "MIA"):
            ok74c = ok74c and abs(utrows74[_t74]["diff_pct"]) <= 0.5 \
                and utrows74[_t74]["spotrac_total"] == led74[_t74]
        check(_c74_names[3], ok74c, f"guerrero={guer74}")
        check(_c74_names[4],
              "7 of 7 over-cap teams" in html
              and "0.63% on average, worst 3.07%" in html
              and "Alex Bregman" in html
              and "(Cot's LRP 2027)" in html)
    else:
        for _nm74 in _c74_names:
            check(_nm74, False, "Cycle 74 artifacts missing")

    # --- UNC-2 uncertainty layer (Cycle 56) -----------------------
    unc2_path = DATA / "uncertainty_scenarios_2027.json"
    if unc2_path.exists():
        u2 = json.loads(unc2_path.read_text())
        u2_by = {s["label"]: s for s in u2["scenarios"]}
        ep, ap = u2["error_pools"], u2["availability_pools"]
        ok = (u2["sims"] >= 10000 and len(u2["scenarios"]) == 3)
        ok = ok and ep["hitters"]["n"] == sum(
            v["n"] for v in ep["hitters"]["per_target"].values())
        ok = ok and ep["pitchers"]["n"] == sum(
            v["n"] for v in ep["pitchers"]["per_target"].values())
        ok = ok and ep["hitters"]["n"] >= 150 and ep["pitchers"]["n"] >= 40
        ok = ok and ap["hitters"]["n"] == len(load("projections_2027_health.json"))
        ok = ok and ap["pitchers"]["n"] == len(
            load("projections_2027_pitchers.json"))
        ok = ok and abs(ep["hitters"]["mae_obp"]
                        - load("marcel_backtest.json")
                        ["pooled"]["C_age_crossfit"]["mae_obp"]) < 0.0015
        ok = ok and abs(ep["pitchers"]["mae_era"]
                        - load("pitcher_backtest.json")
                        ["pooled"]["C_age_crossfit"]["mae_era"]) < 0.0015
        for s in wow["scenarios"]:
            u = u2_by[s["label"]]
            st = wow["availability_stress"]["stressed_totals"][s["label"]]
            a = u["sanity_median_vs_point"]
            ok = ok and u["point_war"] == s["total_war"]
            ok = ok and (u["p10"] <= u["p20"] <= u["p50"]
                         <= u["p80"] <= u["p90"])
            ok = ok and u["sanity_cycle52_stress_inside_interval"][
                "stressed_total"] == st["war_at_pool_mean_avail"]
            ok = ok and u["sanity_cycle52_stress_inside_interval"][
                "inside_p10_p90"] == (
                    u["p10"] <= st["war_at_pool_mean_avail"] <= u["p90"])
            ok = ok and abs(a["analytic_delivered_mean"]
                            - (u["point_war"]
                               + a["availability_level_effect"]
                               + a["measured_residual_bias_effect"])) <= 0.15
            ok = ok and abs(a["simulated_mean_minus_analytic"]) <= 0.1
        check("UNC-2: uncertainty artifact consistent (pools tie to "
              "committed backtests + availability files, points tie to "
              "wow_scenarios, gap decomposition closes, Cycle 52 stress "
              "inside intervals)",
              ok, f"sims={u2['sims']} pools H{ep['hitters']['n']}/"
                  f"P{ep['pitchers']['n']}")
        fl, md, cp = (u2_by["The Floor — $171.2M"],
                      u2_by["The Middle — $208.0M"],
                      u2_by["The Cap — $245.3M"])
        # Plotly serializes figure JSON with \uXXXX escapes; normalize
        # (same treatment as the FIG-QA section below).
        html_u2 = re.sub(r"\\+u([0-9a-fA-F]{4})",
                         lambda m: chr(int(m.group(1), 16)), html)
        ok = all(f"10th–90th percentile {u['p10']}–{u['p90']} WAR, "
                 f"median {u['p50']}" in html_u2
                 for u in (fl, md, cp))
        ok = ok and f"delivered-WAR 10th–90th: {fl['p10']}–{fl['p90']}" in html_u2
        ok = ok and (f"floor's median at {fl['p50']} WAR (10th to 90th: "
                     f"{fl['p10']} to {fl['p90']})" in html_u2)
        ok = ok and f"cap's at {cp['p50']} ({cp['p10']} to {cp['p90']})" in html_u2
        ok = ok and (f"floor {fl['p10']}–{fl['p90']}, middle "
                     f"{md['p10']}–{md['p90']}, cap {cp['p10']}–{cp['p90']}"
                     in html_u2)
        check("UNC-2: dashboard renders the delivered-WAR intervals "
              "(Figure 16 titles, Story ch. 5, Boardroom slide 12)", ok)
        one = (ROOT / "docs" / "ONEPAGER.html").read_text(errors="ignore")
        ok = all(f"{u['point_war']:.1f} ({u['p10']:.1f}&ndash;{u['p90']:.1f})"
                 in one for u in (fl, md, cp))
        check("UNC-2: one-pager scenario table carries the intervals", ok)
    else:
        check("UNC-2: uncertainty artifact consistent (pools tie to "
              "committed backtests + availability files, points tie to "
              "wow_scenarios, gap decomposition closes, Cycle 52 stress "
              "inside intervals)",
              False, "data/uncertainty_scenarios_2027.json missing")
        check("UNC-2: dashboard renders the delivered-WAR intervals "
              "(Figure 16 titles, Story ch. 5, Boardroom slide 12)",
              False, "data/uncertainty_scenarios_2027.json missing")
        check("UNC-2: one-pager scenario table carries the intervals",
              False, "data/uncertainty_scenarios_2027.json missing")

    # --- data platform: curated layer contracts ------------------
    rep_path = DATA / "curated" / "_build_report.json"
    check("platform: curated build report present, no failures",
          rep_path.exists() and not json.loads(rep_path.read_text())["failures"]
          if rep_path.exists() else False)
    if rep_path.exists():
        rep = json.loads(rep_path.read_text())
        import pyarrow.parquet as pq
        bad = []
        for t, meta in rep["tables"].items():
            f = DATA / "curated" / f"{t}.parquet"
            if not f.exists() or pq.read_metadata(f).num_rows != meta["rows"]:
                bad.append(t)
        check("platform: every curated table matches its build report",
              not bad, f"mismatch: {bad}")
        check("platform: >=13 curated tables", len(rep["tables"]) >= 13,
              f"tables={len(rep['tables'])}")

    # --- FIG-QA (Cycle 53): one artifact-tied check per figure -----
    # Every figure gets a check whose expected value is computed from
    # its committed source artifact at gate time, so a wrong number in
    # any figure turns the gate red even if the panel code is edited.
    def _fig(n, name, ok, detail=""):
        check(f"FIG-QA fig {n}: {name}", ok, detail)

    # Plotly serializes figure JSON with \uXXXX escapes; normalize a
    # copy so title/annotation text checks see the rendered characters.
    html_qa = re.sub(r"\\+u([0-9a-fA-F]{4})",
                     lambda m: chr(int(m.group(1), 16)), html)

    panel_seasons = sorted({int(r["season"]) for r in panel})
    _fig(1, "animation panel covers 2011-2026, title in HTML",
         panel_seasons == list(range(2011, 2027))
         and "16 seasons of payroll vs wins" in html_qa,
         f"seasons={panel_seasons}")
    te = load("team_explorer.json")
    _fig(2, "team explorer: 30 teams in artifact and panel",
         len(te["teams"]) == 30 and "pick your team" in html_qa,
         f"teams={len(te['teams'])}")
    pci = load("persistence_ci.json")["pooled_contact"]
    _fig(3, "persistence caption carries pooled contact r + pair count",
         f"pooled r={pci['r']:.2f}" in html_qa
         and f"{pci['n_pairs']} player-year pairs" in html_qa,
         f"pooled={pci}")
    runs26 = [r for r in load("runs_panel.json") if r["season"] == 2026]
    _fig(4, "runs panel: 30 teams in 2026 slice, title in HTML",
         len(runs26) == 30 and "run differential → wins" in html_qa,
         f"rows26={len(runs26)}")
    qc = load("quant_core.json")["logistic"]["run-diff-only"]["25->26"]
    _fig(5, "AUC panel: artifact AUC rounds to the titled 0.95",
         round(qc["auc"], 2) == 0.95 and "AUC ≈ 0.95" in html_qa,
         f"auc={qc['auc']}")
    _fig(6, "payroll-vs-wins panel with cap/floor lines in HTML",
         "Payroll ($M) vs Wins" in html_qa and "Proposed cap $245.3M" in html_qa
         and "Proposed floor $171.2M" in html_qa)
    k26 = load("kpi_2026.json")
    _fig(7, "KPI signature: 30 teams with contact/K% in snapshot, panel in HTML",
         len(k26) == 30
         and all(r.get("contact") is not None and r.get("K%") is not None
                 for r in k26)
         and "Copycat-league KPI signature" in html_qa)
    with open(DATA / "efficiency_2000_2024.csv") as fh:
        n_eff = sum(1 for _ in fh) - 1
    _fig(8, "durability: efficiency file row count matches titled 721",
         n_eff == 721 and "721 team-seasons" in html_qa, f"rows={n_eff}")
    _fig(9, "projected-wins panel: 30 rows in projections_2026, in-sample disclosure + actual-wins trace in HTML",
         len(load("projections_2026.json")) == 30
         and "Model fit (in-sample) vs actual wins" in html_qa
         and "In-sample fit" in html_qa
         and "Actual wins" in html_qa)
    cap_teams = load("cap_scenario_2027.json")["teams"]
    n_over = sum(1 for t in cap_teams if t["gap_to_cap"] > 0)
    _fig(10, "cap scenario: over-cap count from artifact is 7, panel in HTML",
         n_over == 7 and "Cap-era reality" in html_qa, f"over={n_over}")
    fs = load("forced_sellers_2027.json")["teams"]
    covered = [t["team"] for t in fs if t["covered"]]
    uncovered = [t["team"] for t in fs if not t["covered"]]
    chc74 = next(t for t in fs if t["team"] == "CHC")
    _fig(11, "forced sellers: 7 covered, none uncovered (CHC on "
             "Cot's LRP 2027, Cycle 74)",
         len(covered) == 7 and uncovered == []
         and chc74.get("basis") == "cots_lrp_2027"
         and "Forced sellers" in html_qa,
         f"covered={covered} uncovered={uncovered}")
    proj27 = load("projections_2027.json")
    top_name = max(proj27, key=lambda r: r["proj_OBP"])["name"]
    _fig(12, "hitter projections: top-OBP name leads + conviction layer (Cycle 73)",
         top_name in html_qa and "projected hitters by OBP" in html_qa
         and "conviction" in html_qa
         and "no prior record" in html_qa,
         f"top={top_name}")
    if (DATA / "mlb_lake.db").exists():
        _fig(13, "pitching panel built from the lake, title in HTML",
             "Pitching is the other winning-cheap half" in html_qa)
    else:
        _fig(13, "pitching panel absent without lake, omission disclosed",
             'data-figure-missing="13"' in html_qa)
    ilc = load("il_current_live.json")
    ov = ilc["fa_overlay"]
    _fig(14, "health panel: live-IL counts and pull date from the artifact",
         f"{ov['n_matched']} of {ov['fa_pool_size']} free agents "
         "currently listed injured" in html_qa
         and ilc["metadata"]["pulled_date"] in html_qa,
         f"matched={ov['n_matched']}")
    rost = load("roster_2027.json")
    _fig(15, "roster panel: 13 hitters + 13 pitchers in artifact",
         len(rost["hitters"]) == 13 and len(rost["pitchers"]) == 13
         and "Proposed 26-man winning-cheap roster" in html_qa,
         f"H={len(rost['hitters'])} P={len(rost['pitchers'])}")
    wow0 = wow["scenarios"][0]["war_range_prices_pm20"]
    _fig(16, "scenario panel: floor title carries its +-20% price range",
         f"{wow0['low']}–{wow0['high']}" in html_qa
         and "across ±20% price error" in html_qa,
         f"range={wow0}")
    rv = load("robust_validation.json")
    _fig(17, "sensitivity panel: elasticity table present in artifact",
         len(rv.get("elasticity", {})) >= 5 and "measured elasticity" in html_qa,
         f"levers={len(rv.get('elasticity', {}))}")
    hb = load("fg_benchmark_2027.json")["hitters"]
    _fig(18, "benchmark panel: title carries artifact r and top-25 overlap",
         f"OBP r = {hb['obp']['pearson_r']}" in html_qa
         and f"{hb['top25_obp_overlap']['overlap_n']}/25" in html_qa,
         f"r={hb['obp']['pearson_r']}")
    st = load("savant_test.json").get("q2_trait_stability", {})
    _fig(19, "Savant panel: >=6 trait stabilities in artifact, title in HTML",
         len(st) >= 6 and "Savant traits are rock-stable" in html_qa,
         f"traits={len(st)}")
    vm = load("value_metrics_2026.json")
    _fig(20, "value metrics: hitting and pitching tables present",
         len(vm["hitting"]) >= 12 and len(vm["pitching"]) >= 12
         and "Top value metrics" in html_qa,
         f"H={len(vm['hitting'])} P={len(vm['pitching'])}")
    _fig(21, "pipeline panel title in HTML, 30 orgs behind it",
         "under-26 upper-minors depth" in html_qa
         and len(load("pipeline_2026.json")["orgs"]) == 30)
    _fig(22, "surplus-value arbitrage panel: artifact lists 25, title in HTML",
         len(load("surplus_value_2027.json").get("top_surplus", [])) == 10
         and "Free-agent decision lens" in html_qa
         and "surplus value vs expected market cost" in html_qa,
         f"surplus_n={len(load('surplus_value_2027.json').get('top_surplus', []))}")
    f23 = load("fig23_rebuild_2026.json")
    _fig(23, "posted class: fee checkpoint exact, no-translation label shown",
         f23["fee_checkpoints_m"]["60"] == 10.875
         and "No NPB-to-MLB translation factor is claimed" in html_qa,
         f"fee60={f23['fee_checkpoints_m']['60']}")
    hsv = load("hakes_sauer_verdict.json")
    _fig(24, "HS panel: benchmark team-season count in the rendered title",
         f"{hsv['benchmark_attempt']['n_team_seasons']} team-seasons" in html_qa,
         f"n={hsv['benchmark_attempt']['n_team_seasons']}")
    d0 = optc["budgets"][0]["delta_war"]
    _fig(25, "optimizer panel: floor delta from artifact in the title",
         f"+{d0:.1f} WAR at the floor" in html_qa, f"delta={d0}")

    # --- API-2 feed architecture: event layer (Cycle 55) -----------
    ile_path = DATA / "il_events.json"
    if ile_path.exists():
        ile = json.loads(ile_path.read_text())
        ev, summ, fap = ile["events"], ile["summary"], ile["fa_pool_summary"]
        md = ile["metadata"]
        by_type = lambda lst, t: sum(1 for e in lst
                                     if e["event_type"] == t)
        snaps_ok = True
        for side in ("baseline", "current"):
            for key in ("fastballapi_injuries", "statyx_injuries"):
                ref = md[side][key]
                p = ROOT / ref["file"]
                if not p.exists():
                    snaps_ok = False
                    break
                env = json.loads(p.read_text())
                digest = hashlib.sha256(json.dumps(
                    env["payload"], indent=1, sort_keys=True
                ).encode()).hexdigest()
                if digest != ref["payload_sha256"]:
                    snaps_ok = False
        check("API-2: il_events.json consistent (counts reconcile, "
              "snapshots on disk match recorded shas, standings-test "
              "verdict on record)",
              summ["events_total"] == len(ev)
              and summ["new_il"] == by_type(ev, "new_il")
              and summ["returned"] == by_type(ev, "returned")
              and summ["status_change"] == by_type(ev, "status_change")
              and fap["events_total"] == len(ile["fa_pool_events"])
              and fap["new_il"] == by_type(ile["fa_pool_events"], "new_il")
              and all(e["in_fa_pool"] or e["scenario_rosters"]
                      for e in ile["fa_pool_events"])
              and md["statyx_standings_test"]["verdict"] in
                  ("dropped", "curated")
              and snaps_ok,
              f"events={len(ev)} fa_events={len(ile['fa_pool_events'])} "
              f"verdict={md['statyx_standings_test']['verdict']}")
        if fap["events_total"] == 0:
            frag = "no movement in the FA pool since the baseline pull"
        else:
            frag = (f"{fap['new_il']} new IL, {fap['returned']} returned, "
                    f"{fap['status_change']} status changes (FA pool)")
        check("API-2: health figure carries the FA-pool movement line "
              "(Cycle 55)",
              f"Movement since {md['baseline_date']}" in html_qa
              and frag in html_qa
              and f"census (FastballAPI) pulled "
                  f"{md['census_pulled_date']}" in html_qa
              and f"moves (Statyx) pulled {md['moves_pulled_date']}"
                  in html_qa,
              f"frag={frag!r}")
    else:
        check("API-2: il_events.json consistent (counts reconcile, "
              "snapshots on disk match recorded shas, standings-test "
              "verdict on record)", False, "data/il_events.json missing")
        check("API-2: health figure carries the FA-pool movement line "
              "(Cycle 55)", False, "data/il_events.json missing")

    # --- Evidence surveillance: PubMed panel (Cycle 57) ------------
    ev_path = DATA / "evidence_surveillance.json"
    ev_page = ROOT / "docs" / "EVIDENCE.html"
    if ev_path.exists() and ev_page.exists():
        ev = json.loads(ev_path.read_text())
        evh = ev_page.read_text(errors="ignore")
        # the page HTML-escapes text (apostrophes -> &#x27;); compare
        # against the unescaped rendering
        evh = (evh.replace("&#x27;", "'").replace("&#39;", "'")
               .replace("&amp;", "&"))
        lanes = ev["lanes"]
        cards = [c for lane in lanes for c in lane["cards"]]
        check("Evidence: artifact has 4 lanes x 3 cards, counts and "
              "abstracts recorded (Cycle 57)",
              len(lanes) == 4
              and all(len(lane["cards"]) == 3 for lane in lanes)
              and all(isinstance(lane["found"], int) and lane["found"] >= 3
                      for lane in lanes)
              and all(c.get("abstract") and c.get("pmid")
                      for c in cards)
              and ev["metadata"].get("run_date")
              and all(lane.get("query") for lane in lanes),
              f"lanes={len(lanes)} cards={len(cards)}")
        check("Evidence: EVIDENCE.html renders every card (lane counts, "
              "PMID, DOI, Finding) from the artifact (Cycle 57)",
              all(f"{lane['found']} FOUND" in evh
                  and lane["heading"] in evh for lane in lanes)
              and all(c["pmid"] in evh and c["finding"] in evh
                      and c["headline"] in evh
                      and (not c.get("doi") or c["doi"] in evh)
                      for c in cards)
              and "context, not a model input" in evh,
              f"cards={len(cards)}")
        _ev_seg = html.split('id="mode-explorer"', 1)[1]
        _ev_seg = re.split(r'id="mode-|<div class="srcbox"', _ev_seg)[0]
        _p14 = _ev_seg.find('data-mode="explorer" data-figure="14"')
        _pnote = _ev_seg.find(
            "What the evidence says now</a> — the published research "
            "on injury recovery and prevention.")
        _p15 = _ev_seg.find('data-mode="explorer" data-figure="15"')
        check("Evidence: dashboard footnote under Figure 14 matches "
              "artifact (exact note text, lane counts, page link) "
              "(Cycle 57)",
              '* <a href="../docs/EVIDENCE.html">What the evidence '
              "says now</a>" in html
              and "— the published research on injury recovery and "
                  "prevention." in html
              and all(f"({lane['found']} found)" in html for lane in lanes)
              and -1 < _p14 < _pnote < _p15,
              f"lanes={len(lanes)} p14={_p14} note={_pnote} p15={_p15}")
        check("Evidence: dashboard footer names PubMed / NCBI "
              "E-utilities (Cycle 57)",
              "PubMed / NCBI E-utilities" in html
              and "evidence_surveillance.json" in html)
    else:
        check("Evidence: artifact has 4 lanes x 3 cards, counts and "
              "abstracts recorded (Cycle 57)", False,
              "data/evidence_surveillance.json or docs/EVIDENCE.html "
              "missing")
        check("Evidence: EVIDENCE.html renders every card (lane counts, "
              "PMID, DOI, Finding) from the artifact (Cycle 57)", False,
              "evidence artifact or page missing")
        check("Evidence: dashboard footnote under Figure 14 matches "
              "artifact (exact note text, lane counts, page link) "
              "(Cycle 57)", False, "evidence artifact or page missing")
        check("Evidence: dashboard footer names PubMed / NCBI "
              "E-utilities (Cycle 57)", False,
              "evidence artifact or page missing")

    # --- Tracker ticker: free-agency wire (Cycle 66) ----------------
    tk_path = DATA / "tracker_ticker_2026.json"
    if tk_path.exists():
        tk = json.loads(tk_path.read_text())
        tk_md, tk_items = tk["metadata"], tk["items"]
        tk_signed = [i for i in tk_items if i["lane"] == "SIGNED"]
        tk_reported = [i for i in tk_items if i["lane"] == "REPORTED"]
        tk_buzz = [i for i in tk_items if i["lane"] == "BUZZ"]
        try:
            from datetime import datetime as _dt
            _pulled = _dt.fromisoformat(tk_md["pulled_at"])
            _pulled_ok = _pulled.tzinfo is not None
        except Exception:
            _pulled_ok = False
        # Freshness note: the gate must stay green on later runs, so
        # it pins pulled_at present-and-parseable, not "today" — the
        # panel itself displays the pull date for the reader.
        check("Ticker: artifact consistent (counts reconcile, every "
              "SIGNED item carries a StatsAPI transaction id, no "
              "REPORTED/BUZZ item carries one, lanes are the three "
              "known lanes) (Cycle 66)",
              _pulled_ok
              and tk_md["counts"]["signed"] == len(tk_signed)
              and tk_md["counts"]["reported"] == len(tk_reported)
              and tk_md["counts"]["buzz"] == len(tk_buzz)
              and tk_md["counts"]["total"] == len(tk_items)
              and all(i.get("statsapi_transaction_id") is not None
                      for i in tk_signed)
              and all(i.get("statsapi_transaction_id") is None
                      for i in tk_reported + tk_buzz)
              and all(i["lane"] in ("SIGNED", "REPORTED", "BUZZ")
                      and i.get("title") and i.get("source")
                      for i in tk_items),
              f"signed={len(tk_signed)} reported={len(tk_reported)} "
              f"buzz={len(tk_buzz)} pulled={tk_md.get('pulled_at')}")
        _story = html.split('id="mode-story"', 1)[1]
        _story = _story.split('id="mode-boardroom"', 1)[0]
        _tk = _story.find("Free-agent market activity")
        _ch1 = _story.find('data-chapter="1"')
        check("Ticker: panel leads Story mode before Chapter 1, all "
              "three lane labels + integrity line + pull date "
              "rendered (Cycle 66)",
              -1 < _tk < _ch1
              and "SIGNED — confirmed by MLB StatsAPI" in _story
              and "REPORTED — newswire and rumor" in _story
              and "BUZZ — social" in _story
              and "An item becomes SIGNED only when the MLB StatsAPI "
                  "transactions feed carries it. REPORTED and BUZZ items "
                  "are never labeled signings." in _story
              and tk_md["pulled_at"][:10] in _story,
              f"panel={_tk} ch1={_ch1}")
        _signed12 = tk_signed[:12]
        check("Ticker: SIGNED discipline — every rendered SIGNED item "
              "carries its exact move type, so a DFA declaration "
              "cannot read as a signing (Cycle 66)",
              all(f"[{i['move_type']}]" in _story for i in _signed12)
              and (not any(i["move_type"].startswith("DFA")
                           for i in _signed12)
                   or "Declared free agency" in _story),
              f"rendered={len(_signed12)}")
    else:
        check("Ticker: artifact consistent (counts reconcile, every "
              "SIGNED item carries a StatsAPI transaction id, no "
              "REPORTED/BUZZ item carries one, lanes are the three "
              "known lanes) (Cycle 66)", False,
              "data/tracker_ticker_2026.json missing")
        check("Ticker: panel leads Story mode before Chapter 1, all "
              "three lane labels + integrity line + pull date "
              "rendered (Cycle 66)", False,
              "data/tracker_ticker_2026.json missing")
        check("Ticker: SIGNED discipline — every rendered SIGNED item "
              "carries its exact move type, so a DFA declaration "
              "cannot read as a signing (Cycle 66)", False,
              "data/tracker_ticker_2026.json missing")

    # --- Health cards: FA shopping list, delivered WAR (Cycle 67) --
    hc_path = DATA / "fa_health_cards_2027.json"
    if hc_path.exists():
        hc = json.loads(hc_path.read_text())
        hc_cards, hc_md = hc["cards"], hc["metadata"]["counts"]
        shop_names = sorted(c["name"]
                            for c in load("fa_shopping_2027.json")["class"])
        card_names = sorted(c["name"] for c in hc_cards)
        _re_av = all(
            c["il_days_2025_26"] is None
            or abs(c["availability"]
                   - round(max(0.0, 1.0 - c["il_days_2025_26"] / 364), 4)) <= 0.001
            for c in hc_cards)
        _re_del = all(
            c["delivered_war"] is None
            or abs(c["delivered_war"]
                   - (c["headline_war"]
                      * c["availability_used_for_delivered"]
                      + (c["residual_term_war"] or 0.0))) <= 0.01
            for c in hc_cards)
        _ranks = sorted(c["rank_by_delivered_war"] for c in hc_cards
                        if c["delivered_war"] is not None)
        _by_rank = sorted((c for c in hc_cards
                           if c["delivered_war"] is not None),
                          key=lambda c: c["rank_by_delivered_war"])
        _del_sorted = [c["delivered_war"] for c in _by_rank]
        check("Health cards: 251 cards, names match the class 1:1, "
              "counts reconcile, availability + delivered WAR recompute "
              "from artifact fields, delivered ranks 1..N unique and "
              "ordered (Cycle 67)",
              len(hc_cards) == 251 and card_names == shop_names
              and hc_md["with_measured_availability"]
              + hc_md["no_il_record"]
              + hc_md["not_matched_no_player_id"] == 251
              and hc_md["delivered_war_computed"]
              + hc_md["no_steamer_war"] == 251
              and hc_md["classified_lane"] + hc_md["page_top_link"] == 251
              and _re_av and _re_del
              and _ranks == list(range(1, len(_ranks) + 1))
              and _del_sorted == sorted(_del_sorted, reverse=True),
              f"cards={len(hc_cards)} recompute_av={_re_av} "
              f"recompute_del={_re_del} ranked={len(_ranks)}")
        _ex_seg = html.split('id="mode-explorer"', 1)[1]
        _ex_seg = re.split(r'id="mode-|<div class="srcbox"', _ex_seg)[0]
        _st_seg = html.split('id="mode-story"', 1)[1]
        _st_seg = _st_seg.split('id="mode-boardroom"', 1)[0]
        _top_name = max((c for c in hc_cards
                         if c["delivered_war"] is not None),
                        key=lambda c: c["delivered_war"])["name"]
        check("Health cards: panel renders in Explorer (title, "
              "Delivered WAR column, top delivered name, a lane link) "
              "and NOT in Story; evidence page carries all four lane "
              "anchors (Cycle 67)",
              "Health cards: the whole class, ranked by what each player"
              in _ex_seg
              and "Delivered WAR" in _ex_seg
              and _top_name in _ex_seg
              and "../docs/EVIDENCE.html#lane-ucl" in _ex_seg
              and "Health cards: the whole class" not in _st_seg
              and all(a in (ROOT / "docs" / "EVIDENCE.html").read_text(
                  errors="ignore")
                      for a in ('id="lane-ucl"', 'id="lane-workload"',
                                'id="lane-muscle"', 'id="lane-tendon"')),
              f"top={_top_name}")
    else:
        check("Health cards: 251 cards, names match the class 1:1, "
              "counts reconcile, availability + delivered WAR recompute "
              "from artifact fields, delivered ranks 1..N unique and "
              "ordered (Cycle 67)", False,
              "data/fa_health_cards_2027.json missing")
        check("Health cards: panel renders in Explorer (title, "
              "Delivered WAR column, top delivered name, a lane link) "
              "and NOT in Story; evidence page carries all four lane "
              "anchors (Cycle 67)", False,
              "data/fa_health_cards_2027.json missing")

    # --- Claims & reproducibility pack (Cycle 68) ------------------
    reg_path = DATA / "claims_register.json"
    tr_path = DATA / "figure_trace_2027.json"
    if reg_path.exists() and tr_path.exists():
        reg = json.loads(reg_path.read_text())
        tr = json.loads(tr_path.read_text())
        _ids = {c["id"] for c in reg["claims"]}
        _need = {"S01", "S02", "S03", "S04", "S06", "S07", "S09", "S10",
                 "S11", "S12", "N01", "N02", "N03", "N06"}
        _ev_ok = True
        for c in (reg["claims"] + reg["open_items"]
                  + reg.get("resolved_items", [])):
            # Artifact strings may carry parenthetical section notes;
            # pull the file paths out with a regex, don't split on "+".
            for art in re.findall(r"data/[a-z0-9_./]+\.(?:json|csv)",
                                  c["evidence"]["artifact"]):
                _ev_ok = _ev_ok and (ROOT / art).exists()
        _ret_ids = {r["id"] for r in reg["retracted"]}
        _ret_text = json.dumps(reg["retracted"])
        check("Claims pack: register present, all required claim ids, "
              "retracted section incl. R01 (R-squared 0.80) + R02 "
              "(UNC-1 point-forecast), every evidence artifact exists, "
              "O01 (Figure 9) resolved not open, counts reconcile "
              "(Cycle 68, O01 resolved Cycle 69)",
              _need <= _ids and _ev_ok
              and {"R01", "R02", "R03"} <= _ret_ids
              and "R-squared 0.80" in _ret_text
              and "point forecasts" in _ret_text
              and reg["open_items"] == []
              and any(o["id"] == "O01"
                      for o in reg.get("resolved_items", []))
              and reg["counts"]["open_items"] == 0
              and reg["counts"]["resolved_items"] == len(
                  reg.get("resolved_items", []))
              and reg["counts"]["supported"] == sum(
                  1 for c in reg["claims"] if c["status"] == "SUPPORTED")
              and reg["counts"]["not_supported"] == sum(
                  1 for c in reg["claims"] if c["status"] == "NOT SUPPORTED")
              and reg["counts"]["retracted"] == len(reg["retracted"]),
              f"claims={len(reg['claims'])} retracted={len(reg['retracted'])} "
              f"ev_ok={_ev_ok}")
        _figs = tr["figures"]
        _pans = tr["panels"]
        check("Claims pack: trace covers all 25 figures + the 8 named "
              "panels, every trace verified (Cycle 68)",
              len(_figs) == 25
              and all(f["status"] == "verified" for f in _figs)
              and len(_pans) == 8
              and all(p["status"] == "verified" for p in _pans),
              f"figs={len(_figs)} panels={len(_pans)}")
        _ex2 = html.split('id="mode-explorer"', 1)[1]
        _ex2 = re.split(r'id="mode-|<div class="srcbox"', _ex2)[0]
        _st2 = html.split('id="mode-story"', 1)[1]
        _st2 = _st2.split('id="mode-boardroom"', 1)[0]
        check("Claims pack: panel renders in Explorer (title, counts "
              "line, retracted list, pack link) and NOT in Story "
              "(Cycle 68)",
              "Claims &amp; reproducibility — what this demo asserts, "
              "and what it withdrew" in _ex2
              and "../docs/REPRODUCIBILITY.html" in _ex2
              and "Retracted — stated plainly:" in _ex2
              and "No items are open" in _ex2
              and "One item is still open" not in _ex2
              and "R01" in _ex2
              and "Claims &amp; reproducibility — what this demo asserts"
              not in _st2,
              "panel present in explorer" if "Claims &amp; reproducibility"
              in _ex2 else "panel missing from explorer")
        check("Claims pack: pack page exists and carries the register "
              "counts + the retracted claims (Cycle 68, O01 resolved "
              "Cycle 69)",
              (ROOT / "docs" / "REPRODUCIBILITY.html").exists()
              and "R-squared 0.80" in (ROOT / "docs" / "REPRODUCIBILITY.html"
                                       ).read_text(errors="ignore")
              and "Figure 9" in (ROOT / "docs" / "REPRODUCIBILITY.html"
                                 ).read_text(errors="ignore")
              and "Resolved items" in (ROOT / "docs" / "REPRODUCIBILITY.html"
                                       ).read_text(errors="ignore")
              and "O01" in (ROOT / "docs" / "REPRODUCIBILITY.html"
                            ).read_text(errors="ignore"),
              "page present")
    else:
        check("Claims pack: register present, all required claim ids, "
              "retracted section incl. R01 (R-squared 0.80) + R02 "
              "(UNC-1 point-forecast), every evidence artifact exists, "
              "O01 (Figure 9) resolved not open, counts reconcile "
              "(Cycle 68, O01 resolved Cycle 69)", False,
              "claims_register.json or figure_trace_2027.json missing")
        check("Claims pack: trace covers all 25 figures + the 8 named "
              "panels, every trace verified (Cycle 68)", False,
              "figure_trace_2027.json missing")
        check("Claims pack: panel renders in Explorer (title, counts "
              "line, retracted list, pack link) and NOT in Story "
              "(Cycle 68)", False, "pack artifacts missing")
        check("Claims pack: pack page exists and carries the register "
              "counts + the retracted claims (Cycle 68)", False,
              "pack artifacts missing")

    # --- optional live check ---------------------------------------
    if live:
        import requests
        r = requests.get("https://statsapi.mlb.com/api/v1/standings",
                         params={"leagueId": "103,104", "season": 2026,
                                 "standingsTypes": "regularSeason"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        api = {}
        for rec in r.json()["records"]:
            for tr in rec["teamRecords"]:
                api[tr["team"]["name"]] = tr["wins"]
        snap = {row["team"]: row["wins"] for row in load("kpi_2026.json")}
        # repo abbr -> standings short name (the standings endpoint uses
        # short names; this exact map passed 30/30 on 2026-10-31)
        short = {"NYM": "Mets", "LAD": "Dodgers", "NYY": "Yankees",
                 "PHI": "Phillies", "TOR": "Blue Jays", "ATL": "Braves",
                 "CHC": "Cubs", "HOU": "Astros", "SD": "Padres",
                 "BOS": "Red Sox", "DET": "Tigers", "ARI": "D-backs",
                 "TEX": "Rangers", "SF": "Giants", "LAA": "Angels",
                 "SEA": "Mariners", "BAL": "Orioles", "KC": "Royals",
                 "MIL": "Brewers", "CIN": "Reds", "COL": "Rockies",
                 "MIN": "Twins", "PIT": "Pirates", "CHW": "White Sox",
                 "WSH": "Nationals", "ATH": "Athletics", "STL": "Cardinals",
                 "TB": "Rays", "MIA": "Marlins", "CLE": "Guardians"}
        bad = []
        for abbr, w in snap.items():
            key = short.get(abbr, "")
            if api.get(key) != w:
                bad.append((abbr, key, w, api.get(key)))
        check("LIVE: kpi_2026 wins match MLB API standings (30/30)", not bad,
              f"mismatch: {bad}")

    print()
    if FAIL:
        print(f"GATE: FAIL ({len(FAIL)} check(s)): {', '.join(FAIL)}")
        return 1
    print("GATE: ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
