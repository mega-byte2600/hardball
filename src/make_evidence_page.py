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

Cycle 91 (owner-directed design pass, 2026-11-07) adds a
presentation-only navigation layer, all of it generated here: a
sticky "On this page" contents bar under the intro, a navy/red
header band and an artifact-computed counts line on the spotlight
section, anchor ids per spotlight group, one pointer line at the
end of each lane ("The journals behind this lane", only when the
spotlight is present), back-to-top links, and back-to-dashboard
links. No content changes: every lane word, paper title, date, and
link renders exactly as before.

Usage: python3 src/make_evidence_page.py
Output: docs/EVIDENCE.html (print-clean, single document, no
external assets)
"""
import html
import json
import sys
from datetime import datetime
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

    # The lane -> spotlight pointer is emitted only when the
    # spotlight section will exist, so the page never carries a
    # dead #go-deeper anchor (Cycle 91).
    spot_exists = (DATA / "journal_spotlight.json").exists()

    def lane_html(lane):
        cards = ""
        for c in lane["cards"]:
            cards += f"""
    <article class="paper">
      <h3>{html.escape(c['headline'])}</h3>
      <p class="finding"><span class="flab">Finding.</span> {html.escape(c['finding'])}</p>
      <p class="cite">{html.escape(c['citation'])} <a href="{html.escape(c['pubmed_url'])}">PubMed</a></p>
    </article>"""
        ptr = ""
        if spot_exists:
            ptr = """
    <p class="laneptr"><a href="#go-deeper">The journals behind this lane &rarr;</a></p>"""
        return f"""
  <section class="lane" id="{LANE_ANCHORS[lane['id']]}">
    <h2>{html.escape(lane['heading'])}</h2>
    <p class="meta">{html.escape(lane['label'])} &middot; {lane['found']} FOUND &middot; PULLED {html.escape(md['run_date'])}</p>
    <p class="intro">{html.escape(LANE_INTROS[lane['id']])}</p>
    <p class="query">PubMed query: <span class="q">{html.escape(lane['query'])}</span></p>{cards}{ptr}
    <p class="totop navonly"><a href="#top">Back to top &uarr;</a></p>
  </section>"""

    lanes_html = "".join(lane_html(l) for l in lanes)

    # --- "Go deeper" journal spotlight (Cycle 90) ------------------
    # Optional section: a missing artifact omits it, never breaks
    # the page. Titles/dates/links render verbatim from the
    # artifact; nothing is summarized or reworded here.
    spotlight_html = ""
    spotlight_foot = ""
    toc_spot = ""
    spot_path = DATA / "journal_spotlight.json"
    if spot_path.exists():
        spot = json.loads(spot_path.read_text())
        smd = spot["metadata"]
        # Cycle 91: stable group anchor ids, assigned by position
        # (the pull writes exactly these three groups, in order).
        GROUP_IDS = ["journals-velocity", "journals-workload",
                     "journals-recovery"]
        group_ids = [GROUP_IDS[i] if i < len(GROUP_IDS)
                     else f"journals-group-{i + 1}"
                     for i in range(len(spot["groups"]))]
        # Header-band meta, computed from the artifact — never
        # hardcoded: journal count, paper count, pull month.
        n_journals = sum(len(g["journals"]) for g in spot["groups"])
        n_papers = sum(len(j["papers"]) for g in spot["groups"]
                       for j in g["journals"])
        stamp = smd.get("pulled_at") or smd.get("pulled_date_pt") or ""
        month_year = stamp
        for fmt in ("%Y-%m-%d %H:%M %Z", "%Y-%m-%d"):
            try:
                month_year = datetime.strptime(
                    stamp.strip(), fmt).strftime("%b %Y")
                break
            except ValueError:
                pass
        spot_meta = (f"{n_journals} journals &middot; {n_papers} papers"
                     f" &middot; updated {html.escape(month_year)}")
        groups_html = ""
        for gi, g in enumerate(spot["groups"]):
            journals_html = ""
            for j in g["journals"]:
                if j["papers"]:
                    papers_html = "".join(f"""
      <p class="spot"><a href="{html.escape(p['url'])}">{html.escape(p['title'])}</a><span class="smeta">&middot; {html.escape(p['date'])}</span></p>"""
                        for p in j["papers"])
                else:
                    papers_html = """
      <p class="spot">No pitching-specific papers in the current index.</p>"""
                journals_html += f"""
    <div class="jblock">
      <h4 class="journal"><a href="{html.escape(j['link'])}">{html.escape(j['name'])}</a></h4>{papers_html}
    </div>"""
            groups_html += f"""
    <h3 class="group" id="{group_ids[gi]}">{html.escape(g['heading'])}</h3>{journals_html}"""
        spotlight_html = f"""
  <section class="spotlight" id="go-deeper">
    <h2>Go deeper — the journals behind this page</h2>
    <p class="meta">{spot_meta}</p>
    <p class="intro">Every lane above draws on the journals below.
    Their most recent pitching papers, newest first.</p>
    <p class="intro">A reading resource, not an evidence claim. Under
    each journal: its two most recent PubMed matches for pitching or
    baseball, titles as published, pulled {html.escape(smd['pulled_date_pt'])}.
    Journal names link to the journal's own site where it answered
    during the build, otherwise to that journal's listing on
    PubMed.</p>{groups_html}
    <p class="totop navonly"><a href="#top">Back to top &uarr;</a></p>
  </section>"""
        toc_spot = ('<span class="tsep">&middot;</span>'
                    '<a href="#go-deeper">Go deeper: the journals</a>'
                    + "".join(
                        f'<a href="#{group_ids[gi]}">'
                        f'{html.escape(g["heading"])}</a>'
                        for gi, g in enumerate(spot["groups"])))
        spotlight_foot = (f" Journal spotlight: "
            f"data/journal_spotlight.json, pulled "
            f"{html.escape(smd['pulled_date_pt'])} by "
            f"src/pull_journal_spotlight.py (Cycle 90); paper titles "
            f"verbatim from PubMed.")

    # Contents bar (Cycle 91): lane links from the artifact, in
    # lane order, then the spotlight links when the section exists.
    toc_lanes = "".join(
        f'<a href="#{LANE_ANCHORS[l["id"]]}">'
        f'{html.escape(l["heading"])}</a>' for l in lanes)
    toc_html = (f'<nav class="toc navonly"><span class="tlab">'
                f'On this page:</span>{toc_lanes}{toc_spot}</nav>')

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>HARDBALL — What the Evidence Says Now</title>
<style>
  @page {{ size: letter; margin: 0.6in; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #141414;
         margin: 0.6in auto; max-width: 7.3in; font-size: 12pt; line-height: 1.45; }}
  h1 {{ font-size: 22pt; margin: 0 0 4pt; color: #041E42; }}
  h2 {{ font-size: 15pt; margin: 26pt 0 2pt; border-bottom: 2px solid #041E42;
        padding-bottom: 3pt; color: #041E42; }}
  h3 {{ font-size: 12.5pt; margin: 0 0 3pt; }}
  .sub {{ font-size: 10.5pt; color: #444; margin: 0 0 10pt; }}
  .label {{ background: #eef2f7; border-left: 4px solid #041E42;
            padding: 8pt 12pt; font-size: 11pt; margin: 12pt 0 4pt; }}
  .backlink {{ font-size: 10pt; margin: 0 0 8pt; }}
  .backlink a {{ color: #041E42; text-decoration: none; }}
  .backlink a:hover {{ text-decoration: underline; }}
  .bback {{ margin: 10pt 0 0; }}
  .toc {{ position: sticky; top: 0; background: #fff; z-index: 10;
          border-bottom: 2px solid #041E42; padding: 7pt 2pt 5pt;
          margin: 10pt 0 2pt; font-size: 10pt; line-height: 1.7;
          display: flex; flex-wrap: wrap; align-items: baseline;
          column-gap: 10pt; row-gap: 1pt; }}
  .toc .tlab {{ font-weight: bold; color: #041E42; }}
  .toc a {{ color: #041E42; text-decoration: none;
            white-space: nowrap; }}
  .toc a:hover {{ text-decoration: underline; }}
  .toc .tsep {{ color: #666; }}
  section[id], h3.group[id] {{ scroll-margin-top: 78pt; }}
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
  .cite a {{ color: #041E42; }}
  .laneptr {{ font-size: 10pt; margin: 10pt 0 0; }}
  .laneptr a {{ color: #041E42; }}
  .totop {{ font-size: 9.5pt; margin: 6pt 0 0; text-align: right; }}
  .totop a {{ color: #041E42; text-decoration: none; }}
  .totop a:hover {{ text-decoration: underline; }}
  .spotlight {{ border-top: 3px solid #BF0D3E; margin-top: 30pt;
                padding-top: 2pt; }}
  .spotlight h2 {{ margin-top: 10pt; }}
  .spotlight h3.group {{ background: #092C5C; color: #fff;
        border-left: 5px solid #BF0D3E; font-size: 12.5pt;
        margin: 18pt 0 4pt; padding: 5pt 9pt; }}
  .jblock {{ page-break-inside: avoid; }}
  .journal {{ font-weight: bold; font-size: 12pt; margin: 13pt 0 2pt;
              color: #092C5C; }}
  .journal a {{ color: #092C5C; text-decoration: none; }}
  .journal a:hover {{ text-decoration: underline; }}
  .spot {{ font-size: 10.5pt; margin: 0 0 6pt 12pt; line-height: 1.4; }}
  .spot a {{ color: #041E42; }}
  .spot .smeta {{ display: block; color: #666; font-size: 9pt;
                  letter-spacing: 0.04em; margin-top: 1pt; }}
  .foot {{ border-top: 1.5px solid #111; margin-top: 26pt; padding-top: 6pt;
           font-size: 9.5pt; color: #444; }}
  @media (max-width: 640px) {{ body {{ margin: 18pt 14pt; max-width: none; }}
        .toc {{ column-gap: 8pt; }}
        section[id], h3.group[id] {{ scroll-margin-top: 132pt; }} }}
  @media print {{ body {{ margin: 0 auto; }} a {{ color: #141414; text-decoration: none; }}
        .navonly {{ display: none; }} }}
</style></head>
<body>
<p class="backlink navonly"><a href="../dashboard/hardball_demo.html">&larr; Back to the dashboard</a></p>
<h1 id="top">What the Evidence Says Now</h1>
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
{toc_html}
{lanes_html}{spotlight_html}
<div class="foot">Source: PubMed / NCBI E-utilities (esearch + efetch),
data/evidence_surveillance.json, pulled {html.escape(md['run_date'])} by
src/pull_evidence_surveillance.py (Cycle 57). Selection rule:
{html.escape(md['selection_rule'])} Citations in AMA style as returned by
PubMed.{spotlight_foot} Page generated by src/make_evidence_page.py — no external assets,
print-clean.</div>
<p class="backlink bback navonly"><a href="../dashboard/hardball_demo.html">&larr; Back to the dashboard</a></p>
</body></html>
"""
    OUT.write_text(doc)
    print(f"evidence page written: {OUT} ({len(doc)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
