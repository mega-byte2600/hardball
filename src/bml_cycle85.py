#!/usr/bin/env python3
"""Cycle 85: close the last data gap in the claims pack (N06).

BOOKKEEPING + CLAIM STATUS CHANGE — the numbers were recomputed by the
build scripts, this script only records the outcome. Spotrac's six
blocked team pages returned 200 on 2026-11-05, so data/salaries_2026.json
completed to 30/30 (1,144 rows, 1,071 ID-matched, 0 team failures; the
24-team rows are byte-identical to the committed file). Consequences,
all verified here before anything is written:

  * N06 ("salary data complete at player level for all 30 teams")
    flips NOT SUPPORTED -> SUPPORTED. It was the last honest residue.
  * S09 restated: per-player rows for all 30 teams (1,144 rows).
  * S17 restated: all 7 shed sets on Spotrac rows — CHC's Bregman at
    his $35.0M Spotrac 2026 salary (replacing the $29.5M Cot's LRP
    figure); LRP cross-validation now agrees on 6 of 7, AAV on 7 of 7.
  * Register counts move 17 supported / 7 not supported -> 18 / 6.

This script verifies those facts in the committed artifacts, updates
data/claims_register.json (statuses + counts + corrections log), and
regenerates docs/REPRODUCIBILITY.html from the updated JSONs (same
template as src/bml_cycle68.py / src/bml_cycle69.py).

Run BEFORE the dashboard rebuild (the dashboard panel reads the
register), then rebuild, then re-run the gate:

    python3 src/bml_cycle85.py
    python3 src/dashboard_p6.py
    python3 src/verify_data.py
    python3 src/spellcheck_gate.py

Exit 1 on any failed assertion: a register whose claim does not match
the shipped artifact is FLAGGED, never papered over.
"""
import html as _html
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
FAILURES = []


def check(name, ok, detail=""):
    if not ok:
        FAILURES.append(name)
        print(f"  FLAG  {name} — {detail}")
    return ok


def main():
    sal = json.load(open(os.path.join(DATA, "salaries_2026.json")))
    check("Salaries complete: 1,144 rows, 0 team failures, 30 teams",
          sal["metadata"]["rows"] == 1144
          and sal["metadata"]["team_failures"] == []
          and len(sal["players"]) == 1144
          and len({p["team"] for p in sal["players"]}) == 30,
          str(sal["metadata"]))
    fs = {t["team"]: t for t in
          json.load(open(os.path.join(DATA, "forced_sellers_2027.json")))["teams"]}
    chc_fs = fs["CHC"]
    check("Forced sellers: 7/7 covered, CHC on Spotrac (Bregman $35.0M)",
          all(t["covered"] for t in fs.values())
          and [s["name"] for s in chc_fs["shed"]] == ["Alex Bregman"]
          and chc_fs["shed_total"] == 35000000
          and "basis" not in chc_fs,
          str(chc_fs))
    recon = json.load(open(os.path.join(DATA, "salary_reconciliation_2027.json")))
    cross = recon["shed_cross_validation"]
    lrp_agree = sum(1 for c in cross if c["lrp_matches_spotrac"])
    aav_agree = sum(1 for c in cross if c["aav_matches_spotrac"])
    chc_cv = next(c for c in cross if c["team"] == "CHC")
    check("Recon: CHC cross-validates on both Cot's bases; LRP 6/7, AAV 7/7",
          chc_cv["lrp_matches_spotrac"] is True
          and chc_cv["aav_matches_spotrac"] is True
          and lrp_agree == 6 and aav_agree == 7,
          f"lrp={lrp_agree}/7 aav={aav_agree}/7")
    led = {t["team"]: t for t in
           json.load(open(os.path.join(DATA, "cap_transition_2027.json")))["teams"]}
    chc_led = led["CHC"]["action"]
    check("Ledger: CHC action on Spotrac (Bregman $35.0M, no Cot's basis)",
          chc_led["covered"] is True
          and chc_led["shed_total"] == 35000000
          and "basis" not in chc_led
          and chc_led["contracts"][0]["salary_2026"] == 35000000,
          str(chc_led))

    reg_path = os.path.join(DATA, "claims_register.json")
    tr_path = os.path.join(DATA, "figure_trace_2027.json")
    reg = json.load(open(reg_path))
    tr = json.load(open(tr_path))
    by_id = {c["id"]: c for c in reg["claims"]}
    check("Register pre-state: N06 NOT SUPPORTED, S09/S17 SUPPORTED, 17/7",
          by_id["N06"]["status"] == "NOT SUPPORTED"
          and by_id["S09"]["status"] == "SUPPORTED"
          and by_id["S17"]["status"] == "SUPPORTED"
          and reg["counts"]["supported"] == 17
          and reg["counts"]["not_supported"] == 7,
          str(reg["counts"]))
    if FAILURES:
        print(f"CYCLE 85: {len(FAILURES)} FLAG(S) — register NOT updated")
        return 1

    by_id["S09"]["claim"] = (
        "The salary basis is: Spotrac payroll totals for all 30 teams, "
        "with per-player contract rows for all 30 teams (1,144 rows); "
        "Cot's LRP-2027 as a second, labeled basis (237 rows, 30 teams). "
        "On the Spotrac basis 7 teams are over the cap ($358.2M over) "
        "and 15 under the floor ($807.8M short); 13 of 30 teams change "
        "status between the two bases.")
    by_id["S09"]["evidence"]["key_numbers"] = (
        "Spotrac per-player rows now cover all 30 teams (1,144 rows, "
        "1,071 ID-matched, 0 team failures; pulled 2026-10-31 + "
        "2026-11-05); Cot's basis is a committed-contract subtotal, "
        "not a complete payroll")
    by_id["S09"]["cycle"] = 85
    by_id["S09"]["date"] = "2026-11-05"

    by_id["S17"]["claim"] = (
        "Forced-seller shed sets cover all 7 over-cap teams, all "
        "computed on Spotrac per-player rows (Alex Bregman, $35.0M, "
        "covers CHC's $4,019,956 gap), the sets cross-validated on "
        "Cot's LRP 2027 (identical players for 6 of 7; LAD's LRP "
        "difference is Ohtani's deferral at present value vs nominal) "
        "and on Cot's CBT-AAV (identical players for 7 of 7), with "
        "Cot's printed team totals reconciling to Spotrac's (mean abs "
        "0.63%, worst 3.07%).")
    by_id["S17"]["evidence"]["key_numbers"] = (
        "CHC gap $4,019,956 = $249,319,956 \u2212 $245,300,000; Bregman "
        "$35,000,000 is his Spotrac 2026 payroll salary (his largest "
        "2027 guarantee on Cot's LRP is $29,527,000; Swanson "
        "$28,000,000 second); totals reconcile mean abs 0.63%, worst "
        "SD 3.07%, 26 of 30 within 2%; USA TODAY's final-2026 LRD list "
        "corroborates the Spotrac totals on a different basis (NYM "
        "+0.02%, LAD \u22120.39%, CLE \u22120.35%)")
    by_id["S17"]["cycle"] = 85
    by_id["S17"]["date"] = "2026-11-05"

    by_id["N06"]["status"] = "SUPPORTED"
    by_id["N06"]["evidence"]["key_numbers"] = (
        "Spotrac per-player rows for all 30 teams (1,144 rows, 1,071 "
        "ID-matched, 0 team failures); pulled 2026-10-31 (24 teams) + "
        "2026-11-05 (ARI/BOS/CHC/MIL/TB/TEX). Team payroll totals "
        "exist for all 30. Corrected Cycle 85: the gap closed when "
        "Spotrac's six blocked pages returned 200 \u2014 the claim now "
        "holds on the single Spotrac basis.")
    by_id["N06"]["cycle"] = 85
    by_id["N06"]["date"] = "2026-11-05"

    reg["counts"]["supported"] = 18
    reg["counts"]["not_supported"] = 6
    reg["corrections_log"] = reg.get("corrections_log", []) + [
        "Cycle 85 closed the last data gap (N06 now SUPPORTED): "
        "Spotrac's six blocked team pages returned 200 on 2026-11-05, "
        "so data/salaries_2026.json completed to 30/30 (1,144 rows, "
        "1,071 ID-matched, 0 team failures; the 24-team rows are "
        "byte-identical to the committed file). S09 restated (30/30, "
        "1,144 rows); S17 restated (all 7 shed sets on Spotrac \u2014 "
        "CHC's Bregman $35.0M Spotrac 2026 salary replaces the "
        "$29.5M Cot's LRP figure; LRP cross-validation now agrees on "
        "6 of 7, AAV on 7 of 7). The Cot's LRP basis remains a labeled "
        "cross-check, never merged. Register counts move from 17 "
        "supported / 7 not supported to 18 / 6.",
    ]
    with open(reg_path, "w") as fh:
        json.dump(reg, fh, indent=1, ensure_ascii=False)

    write_pack_page(reg, tr)
    print("register: 18 supported, 6 not supported, 3 retracted, "
          "0 open, 1 resolved")
    print("pack page written: docs/REPRODUCIBILITY.html")
    return 0


def write_pack_page(register, trace):
    def esc(s):
        return _html.escape(str(s))
    rows = ""
    for c in register["claims"]:
        rows += ("<tr><td><b>" + esc(c["id"]) + "</b></td><td>" + esc(c["claim"]) +
                 "</td><td>" + esc(c["location"]) + "</td><td>" +
                 esc(c["evidence"]["artifact"]) + "<br>" +
                 esc(c["evidence"]["key_numbers"]) + "</td><td><b>" +
                 esc(c["status"]) + "</b><br>Cycle " + esc(c["cycle"]) +
                 ", " + esc(c["date"]) + "</td></tr>\n")
    ret = ""
    for r in register["retracted"]:
        ret += ("<tr><td><b>" + esc(r["id"]) + "</b></td><td>" + esc(r["claim"]) +
                "</td><td>" + esc(r["retraction"]) + "</td><td>Cycle " +
                esc(r["retracted_cycle"]) + ", " + esc(r["date"]) +
                "<br>" + esc(r["standing_record"]) + "</td></tr>\n")
    res = ""
    for o in register.get("resolved_items", []):
        res += ("<tr><td><b>" + esc(o["id"]) + "</b></td><td>" + esc(o["claim"]) +
                "</td><td>" + esc(o["location"]) + "</td><td>" +
                esc(o["resolution"]) + "<br>" + esc(o["standing_record"]) +
                "</td><td><b>" + esc(o["status"]) + "</b><br>Cycle " +
                esc(o["resolved_cycle"]) + ", " + esc(o["date"]) +
                "</td></tr>\n")
    opn = ""
    for o in register["open_items"]:
        opn += ("<tr><td><b>" + esc(o["id"]) + "</b></td><td>" + esc(o["claim"]) +
                "</td><td>" + esc(o["location"]) + "</td><td>" +
                esc(o["status"]) + "</td></tr>\n")
    if not opn:
        opn = ("<tr><td colspan=\"4\">None — no open items.</td></tr>\n")
    figs = ""
    for f in trace["figures"]:
        figs += ("<tr><td>Figure " + str(f["figure"]) + "</td><td>" +
                 esc(f["title"]) + "</td><td>" +
                 ", ".join(esc(a) for a in f["artifacts"]) + "</td><td>" +
                 esc(f["headline"]) + "</td><td>" + esc(f["status"]) +
                 "</td></tr>\n")
    pans = ""
    for p in trace["panels"]:
        pans += ("<tr><td>" + esc(p["panel"]) + "</td><td>" +
                 ", ".join(esc(a) for a in p["artifacts"]) + "</td><td>" +
                 esc(p["headline"]) + "</td><td>" + esc(p["status"]) +
                 "</td></tr>\n")
    corr = "".join("<li>" + esc(x) + "</li>\n" for x in register["corrections_log"])
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>HARDBALL — Claims &amp; reproducibility</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#14213d}}
.hd{{max-width:1120px;margin:0 auto;padding:0 20px 40px}}
h1{{font-size:26px}}h2{{font-size:20px;margin-top:32px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{border:1px solid #d6dcea;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#14213d;color:#fff}}
.note{{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:14px 0}}
</style></head><body><div class="hd">
<h1>Claims &amp; reproducibility — the audit trail</h1>
<p>Generated by <b>src/bml_cycle68.py</b>, updated Cycle 69 by
<b>src/bml_cycle69.py</b> (open item O01 resolved; no claim statuses
changed), updated Cycle 85 by <b>src/bml_cycle85.py</b> (N06 now
SUPPORTED — Spotrac salaries complete 30/30; S09/S17 restated on the
completed file), from the committed artifacts, never hand-edited. A claim
is SUPPORTED only if a committed artifact carries the numbers. A claim
that failed its own test is NOT SUPPORTED, not softened. A claim the demo
once made and withdrew is RETRACTED, stated plainly, not deleted.</p>
<p><b>Counts:</b> {register["counts"]["supported"]} supported ·
{register["counts"]["not_supported"]} not supported ·
{register["counts"]["retracted"]} retracted ·
{register["counts"]["open_items"]} open item(s) ·
{register["counts"]["resolved_items"]} resolved item(s) ·
{register["counts"]["figures_verified"]}/{register["counts"]["figures_traced"]} figures traced and verified ·
{register["counts"]["panels_verified"]}/{register["counts"]["panels_traced"]} panels traced and verified.</p>
<h2>Claims register</h2>
<table><tr><th>ID</th><th>Claim (one sentence)</th><th>Where it appears</th>
<th>Evidence artifact + key numbers</th><th>Status</th></tr>
{rows}</table>
<h2>Retracted claims — the process working, not hidden</h2>
<table><tr><th>ID</th><th>Claim as once made</th><th>Why it was withdrawn</th>
<th>Standing record</th></tr>
{ret}</table>
<h2>Resolved items — formerly open, now closed on the record</h2>
<table><tr><th>ID</th><th>Item</th><th>Where</th><th>Resolution + standing record</th>
<th>Status</th></tr>
{res}</table>
<h2>Open items — decisions still with the owner</h2>
<table><tr><th>ID</th><th>Item</th><th>Where</th><th>Status</th></tr>
{opn}</table>
<h2>Figure trace — every figure to its artifact</h2>
<p>Lineage for every figure: ingest (data/raw + manifest.jsonl, local) →
curated Parquet (data/curated, 19 tables, schema-enforced) → warehouse
(data/hardball.duckdb, built, gitignored) → serving (the dashboard reads
committed JSON artifacts and curated tables; the lake feeds Figure 13 only).</p>
<p>Build commands: ingest <code>python3 src/ingest_platform.py</code> ·
curate <code>python3 src/curate.py</code> · warehouse
<code>python3 src/build_warehouse.py</code> · dashboard
<code>python3 src/dashboard_p6.py</code> · gate
<code>python3 src/verify_data.py</code> · spellcheck
<code>python3 src/spellcheck_gate.py</code> · this pack
<code>python3 src/bml_cycle68.py</code> · pack update
<code>python3 src/bml_cycle69.py</code> · pack update
<code>python3 src/bml_cycle85.py</code>.</p>
<table><tr><th>Figure</th><th>Title</th><th>Artifact(s)</th><th>Headline value, recomputed</th><th>Trace</th></tr>
{figs}</table>
<h2>Panel trace — the surfaces that are not figures</h2>
<table><tr><th>Panel</th><th>Artifact(s)</th><th>Headline value, recomputed</th><th>Trace</th></tr>
{pans}</table>
<h2>Corrections log</h2>
<ul>{corr}</ul>
<p class="note">Figure 9's trace verifies that its artifact and panel agree; its
title now carries the in-sample label — resolved item O01 above.</p>
</div></body></html>
"""
    with open(os.path.join(REPO, "docs", "REPRODUCIBILITY.html"), "w") as fh:
        fh.write(page)


if __name__ == "__main__":
    sys.exit(main())
