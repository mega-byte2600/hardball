#!/usr/bin/env python3
"""HARDBALL evidence page (Cycle 57).

Generates docs/EVIDENCE.html from the COMMITTED artifact
data/evidence_surveillance.json ONLY — no network, no invented
content. Pattern: src/make_onepager.py. The build FAILS CLOSED if
the artifact is missing, a lane does not carry exactly 3 cards, or
any card lacks its abstract, AMA citation, plain headline, or
Finding line (plain lines are merged into the artifact by
src/pull_evidence_surveillance.py from
data/evidence_plain_lines.json — a refresh that selects a paper
with no written Finding stops the page build, by design).

Register: executive plain language for front-office readers. Each
Finding restates only what the paper's abstract reports or
concludes. The page is literature context for the availability
thesis — it is NOT a model input, and says so on the page.

Usage: python3 src/make_evidence_page.py
Output: docs/EVIDENCE.html (print-clean, single document, no
external assets)
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "docs" / "EVIDENCE.html"

LANE_INTROS = {
    "ucl_rtp": (
        "The ulnar collateral ligament (UCL) is the ligament on the "
        "inside of the elbow — the one repaired in Tommy John "
        "surgery. How often players return, and how long it takes, "
        "sets the real cost of a pitcher's roster spot."),
    "prevention_workload": (
        "Most pitching injuries build over time rather than arriving "
        "on one pitch. This topic tracks the workload and "
        "body-mechanics research a club can act on before an arm "
        "breaks down."),
    "cellular_recovery": (
        "Muscle repair runs on satellite cells — the muscle's "
        "resident stem cells — and the immune signals that switch "
        "them on. This is the recovery science underneath every "
        "rehab timeline the club plans around."),
    "tendon_biologics": (
        "Tendons and ligaments heal slowly. Biologics such as "
        "platelet-rich plasma (PRP) — a concentrate of the "
        "patient's own blood platelets — are offered as a way to "
        "speed that healing; this topic keeps score of what the "
        "trials actually show."),
}


def load(name):
    p = DATA / name
    if not p.exists():
        raise SystemExit(f"EVIDENCE FAIL: missing committed artifact {name}")
    return json.loads(p.read_text())


def main():
    ev = load("evidence_surveillance.json")
    md = ev["metadata"]
    lanes = ev["lanes"]

    # --- contracts (fail closed) ------------------------------------
    assert len(lanes) == 4, f"expected 4 lanes, got {len(lanes)}"
    for lane in lanes:
        assert isinstance(lane["found"], int) and lane["found"] >= 3, \
            f"{lane['id']}: bad found count {lane.get('found')}"
        assert len(lane["cards"]) == md["cards_per_lane"] == 3, \
            f"{lane['id']}: expected 3 cards, got {len(lane['cards'])}"
        assert lane["id"] in LANE_INTROS, f"{lane['id']}: no intro written"
        for c in lane["cards"]:
            for field in ("pmid", "citation", "abstract", "headline",
                          "finding", "pubmed_url"):
                assert c.get(field), \
                    f"{lane['id']} PMID {c.get('pmid')}: missing {field}"

    def lane_html(lane):
        cards = ""
        for c in lane["cards"]:
            cards += f"""
    <article class="paper">
      <h3>{html.escape(c['headline'])}</h3>
      <p class="finding"><span class="flab">Finding.</span> {html.escape(c['finding'])}</p>
      <p class="cite">{html.escape(c['citation'])} <a href="{html.escape(c['pubmed_url'])}">PubMed</a></p>
    </article>"""
        return f"""
  <section class="lane">
    <h2>{html.escape(lane['heading'])}</h2>
    <p class="meta">{html.escape(lane['label'])} &middot; {lane['found']} FOUND &middot; PULLED {html.escape(md['run_date'])}</p>
    <p class="intro">{html.escape(LANE_INTROS[lane['id']])}</p>
    <p class="query">PubMed query: <span class="q">{html.escape(lane['query'])}</span></p>{cards}
  </section>"""

    lanes_html = "".join(lane_html(l) for l in lanes)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>HARDBALL — What the Evidence Says Now</title>
<style>
  @page {{ size: letter; margin: 0.6in; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #141414;
         margin: 0.6in auto; max-width: 7.3in; font-size: 12pt; line-height: 1.45; }}
  h1 {{ font-size: 22pt; margin: 0 0 4pt; }}
  h2 {{ font-size: 15pt; margin: 26pt 0 2pt; border-bottom: 2px solid #8a6d1f;
        padding-bottom: 3pt; }}
  h3 {{ font-size: 12.5pt; margin: 0 0 3pt; }}
  .sub {{ font-size: 10.5pt; color: #444; margin: 0 0 10pt; }}
  .label {{ background: #f7f3e8; border-left: 4px solid #8a6d1f;
            padding: 8pt 12pt; font-size: 11pt; margin: 12pt 0 4pt; }}
  .meta {{ font-size: 9pt; letter-spacing: 0.06em; color: #666;
           text-transform: uppercase; margin: 0 0 6pt; }}
  .intro {{ margin: 0 0 4pt; }}
  .query {{ font-size: 9.5pt; color: #666; margin: 0 0 10pt; }}
  .query .q {{ font-family: ui-monospace, monospace; font-size: 9pt; }}
  .paper {{ border-top: 1px solid #ddd; padding: 10pt 0 2pt; margin-top: 8pt;
            page-break-inside: avoid; }}
  .finding {{ margin: 0 0 5pt; }}
  .flab {{ font-weight: bold; }}
  .cite {{ font-size: 9.5pt; color: #555; margin: 0; line-height: 1.4; }}
  .cite a {{ color: #1d3557; }}
  .foot {{ border-top: 1.5px solid #111; margin-top: 26pt; padding-top: 6pt;
           font-size: 9.5pt; color: #444; }}
  @media print {{ body {{ margin: 0 auto; }} a {{ color: #141414; text-decoration: none; }} }}
</style></head>
<body>
<h1>What the Evidence Says Now</h1>
<p class="sub">Figure 14 of the HARDBALL dashboard measures the playtime
injuries take away — the projected playing time a club should not count
on, built from real 2025–26 injured-list data. This page is the other
half of that measurement: what the medical literature says about those
injuries, how players recover from them, and how clubs keep arms and
muscles working. Pulled {html.escape(md['run_date'])} from PubMed (NCBI
E-utilities, keyless); each topic shows three papers — systematic
reviews and meta-analyses first, then the most recent work.</p>
<div class="label"><b>Literature surveillance — context, not a model input.</b>
Nothing on this page feeds any figure, projection, or roster in the demo.
Each Finding restates only what the paper's own abstract reports or
concludes; the full abstract is stored with the citation in the project
data file.</div>
{lanes_html}
<div class="foot">Source: PubMed / NCBI E-utilities (esearch + efetch),
data/evidence_surveillance.json, pulled {html.escape(md['run_date'])} by
src/pull_evidence_surveillance.py (Cycle 57). Selection rule:
{html.escape(md['selection_rule'])} Citations in AMA style as returned by
PubMed. Page generated by src/make_evidence_page.py — no external assets,
print-clean.</div>
</body></html>
"""
    OUT.write_text(doc)
    print(f"evidence page written: {OUT} ({len(doc)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
