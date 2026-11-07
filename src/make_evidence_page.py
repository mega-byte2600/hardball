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

The page ends with a "Go deeper" journal spotlight (Cycle 90,
owner-directed 2026-11-07): the journals behind the page's topics,
each with its 2 most recent pitching/baseball papers from PubMed —
verbatim titles, dates, and PubMed links only, rendered from
data/journal_spotlight.json (src/pull_journal_spotlight.py). It is
a reading resource, not an evidence claim: no summaries, no Finding
lines. If the spotlight artifact is missing the page still builds,
without the section.

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

# Lane anchor ids — the dashboard deep-links into the page with
# ../docs/EVIDENCE.html#lane-<slug> (Cycle 67, gate-checked in
# src/verify_data.py), so the generator must emit them.
LANE_ANCHORS = {
    "ucl_rtp": "lane-ucl",
    "prevention_workload": "lane-workload",
    "cellular_recovery": "lane-muscle",
    "tendon_biologics": "lane-tendon",
}

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
        assert lane["id"] in LANE_ANCHORS, f"{lane['id']}: no anchor id"
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
  <section class="lane" id="{LANE_ANCHORS[lane['id']]}">
    <h2>{html.escape(lane['heading'])}</h2>
    <p class="meta">{html.escape(lane['label'])} &middot; {lane['found']} FOUND &middot; PULLED {html.escape(md['run_date'])}</p>
    <p class="intro">{html.escape(LANE_INTROS[lane['id']])}</p>
    <p class="query">PubMed query: <span class="q">{html.escape(lane['query'])}</span></p>{cards}
  </section>"""

    lanes_html = "".join(lane_html(l) for l in lanes)

    # --- "Go deeper" journal spotlight (Cycle 90) ------------------
    # Optional section: a missing artifact omits it, never breaks
    # the page. Titles/dates/links render verbatim from the
    # artifact; nothing is summarized or reworded here.
    spotlight_html = ""
    spotlight_foot = ""
    spot_path = DATA / "journal_spotlight.json"
    if spot_path.exists():
        spot = json.loads(spot_path.read_text())
        smd = spot["metadata"]
        groups_html = ""
        for g in spot["groups"]:
            journals_html = ""
            for j in g["journals"]:
                if j["papers"]:
                    papers_html = "".join(f"""
      <p class="spot"><a href="{html.escape(p['url'])}">{html.escape(p['title'])}</a> <span class="sdate">&middot; {html.escape(p['date'])}</span></p>"""
                        for p in j["papers"])
                else:
                    papers_html = """
      <p class="spot">No pitching-specific papers in the current index.</p>"""
                journals_html += f"""
    <p class="journal"><a href="{html.escape(j['link'])}">{html.escape(j['name'])}</a></p>{papers_html}"""
            groups_html += f"""
    <h3 class="group">{html.escape(g['heading'])}</h3>{journals_html}"""
        spotlight_html = f"""
  <section class="spotlight">
    <h2>Go deeper — the journals behind this page</h2>
    <p class="intro">A reading resource, not an evidence claim. Under
    each journal: its two most recent PubMed matches for pitching or
    baseball, titles as published, pulled {html.escape(smd['pulled_date_pt'])}.
    Journal names link to the journal's own site where it answered
    during the build, otherwise to that journal's listing on
    PubMed.</p>{groups_html}
  </section>"""
        spotlight_foot = (f" Journal spotlight: "
            f"data/journal_spotlight.json, pulled "
            f"{html.escape(smd['pulled_date_pt'])} by "
            f"src/pull_journal_spotlight.py (Cycle 90); paper titles "
            f"verbatim from PubMed.")

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
  .spotlight h3.group {{ font-size: 13pt; margin: 16pt 0 0; }}
  .journal {{ font-weight: bold; font-size: 11.5pt; margin: 12pt 0 2pt; }}
  .journal a {{ color: #1d3557; text-decoration: none; }}
  .spot {{ font-size: 10.5pt; margin: 0 0 4pt 12pt; line-height: 1.4; }}
  .spot a {{ color: #1d3557; }}
  .spot .sdate {{ color: #666; }}
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
{lanes_html}{spotlight_html}
<div class="foot">Source: PubMed / NCBI E-utilities (esearch + efetch),
data/evidence_surveillance.json, pulled {html.escape(md['run_date'])} by
src/pull_evidence_surveillance.py (Cycle 57). Selection rule:
{html.escape(md['selection_rule'])} Citations in AMA style as returned by
PubMed.{spotlight_foot} Page generated by src/make_evidence_page.py — no external assets,
print-clean.</div>
</body></html>
"""
    OUT.write_text(doc)
    print(f"evidence page written: {OUT} ({len(doc)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
