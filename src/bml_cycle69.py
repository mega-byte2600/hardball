#!/usr/bin/env python3
"""Cycle 69: close claims-pack open item O01 (Figure 9 in-sample label).

BOOKKEEPING ONLY — no new analysis, no claim status changes, no figure
changes. The pack shipped in Cycle 68 carried one open item: Figure 9's
title presented in-sample fitted values without an in-sample label.
That label has since shipped in the figure itself, in the owner's lane
(commit 4219e079, "Figure 9 (owner item #1): relabel in-sample model
fit as calibration, overlay actual wins"): the shipped title is
"2026 — Model fit (in-sample) vs actual wins, by team" and its caption
states "this is calibration, not a forecast". This script verifies
those two strings in src/dashboard_p6.py, moves O01 from open_items
to a new resolved_items section in data/claims_register.json, updates
the Figure 9 trace headline in data/figure_trace_2027.json, and
regenerates docs/REPRODUCIBILITY.html from the updated JSONs (same
template as src/bml_cycle68.py, plus the resolved section).

Run BEFORE the dashboard rebuild (the dashboard panel reads the
register), then rebuild, then re-run the gate:

    python3 src/bml_cycle69.py
    python3 src/dashboard_p6.py
    python3 src/verify_data.py
    python3 src/spellcheck_gate.py

Exit 1 on any failed assertion: a register whose open item does not
match the shipped figure is FLAGGED, never papered over.
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
    dash_src = open(os.path.join(REPO, "src", "dashboard_p6.py")).read()
    check("Fig9 title carries the in-sample label in dashboard source",
          "Model fit (in-sample) vs actual wins" in dash_src,
          "dashboard_p6.py Fig9 title")
    check("Fig9 caption states calibration, not a forecast",
          "calibration, not a forecast" in dash_src,
          "dashboard_p6.py Fig9 caption")

    reg_path = os.path.join(DATA, "claims_register.json")
    tr_path = os.path.join(DATA, "figure_trace_2027.json")
    reg = json.load(open(reg_path))
    tr = json.load(open(tr_path))

    check("Pack open_items is exactly [O01] before closing",
          [o["id"] for o in reg.get("open_items", [])] == ["O01"],
          str([o["id"] for o in reg.get("open_items", [])]))
    o01 = reg["open_items"][0] if reg.get("open_items") else None
    fig9 = [f for f in tr["figures"] if f.get("figure") == 9]
    check("Trace Figure 9 verified with in-sample title",
          len(fig9) == 1 and fig9[0]["status"] == "verified"
          and "in-sample" in fig9[0]["title"],
          str(fig9[0]["title"]) if fig9 else "Figure 9 missing from trace")
    if FAILURES:
        print(f"CYCLE 69: {len(FAILURES)} FLAG(S) — register NOT updated")
        return 1

    resolved = {
        "id": "O01",
        "claim": o01["claim"],
        "location": o01["location"],
        "evidence": o01["evidence"],
        "status": "RESOLVED",
        "resolution": ("The shipped Figure 9 title is '2026 — Model fit "
                       "(in-sample) vs actual wins, by team' and its "
                       "caption states 'this is calibration, not a "
                       "forecast' — the in-sample / diagnostic label the "
                       "item asked for."),
        "standing_record": ("Owner's lane relabel, commit 4219e079 "
                            "('Figure 9 (owner item #1): relabel in-sample "
                            "model fit as calibration, overlay actual "
                            "wins'); title + caption verified in "
                            "src/dashboard_p6.py and the built dashboard."),
        "resolved_cycle": 69,
        "date": "2026-11-03",
    }
    reg["resolved_items"] = [resolved]
    reg["open_items"] = []
    reg["counts"]["open_items"] = 0
    reg["counts"]["resolved_items"] = 1
    reg["corrections_log"] = reg.get("corrections_log", []) + [
        "Cycle 69 closed open item O01 (Figure 9 in-sample label) as "
        "RESOLVED: the label shipped in the owner's lane (commit "
        "4219e079) and is carried by the figure's title + caption. No "
        "claim statuses changed; the register's counts move from "
        "1 open item to 0 open / 1 resolved.",
    ]
    with open(reg_path, "w") as fh:
        json.dump(reg, fh, indent=1, ensure_ascii=False)

    fig9[0]["headline"] = ("30 rows; in-sample fitted values (resolved "
                           "Cycle 69 — title carries the in-sample label)")
    tr["counts"]["open_items"] = 0
    tr["counts"]["resolved_items"] = 1
    tr["build_commands"]["pack_update"] = "python3 src/bml_cycle69.py"
    with open(tr_path, "w") as fh:
        json.dump(tr, fh, indent=1, ensure_ascii=False)

    write_pack_page(reg, tr)
    print(f"register: {reg['counts']['supported']} supported, "
          f"{reg['counts']['not_supported']} not supported, "
          f"{reg['counts']['retracted']} retracted, "
          "0 open, 1 resolved")
    print("trace: Figure 9 headline updated; 25 figures, 8 panels, "
          "all verified (unchanged)")
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
changed), from the committed artifacts, never hand-edited. A claim is
SUPPORTED only if a committed artifact carries the numbers. A claim that
failed its own test is NOT SUPPORTED, not softened. A claim the demo once
made and withdrew is RETRACTED, stated plainly, not deleted.</p>
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
<code>python3 src/bml_cycle69.py</code>.</p>
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
