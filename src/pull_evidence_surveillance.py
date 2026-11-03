#!/usr/bin/env python3
"""Cycle 57 — PubMed evidence surveillance pull for HARDBALL.

Owner-directed (2026-11-02): the same surveillance pattern as the APE
PFAC toolkit's "What the evidence says now" panel, applied to the
injury literature behind HARDBALL's availability edge. Four fixed
lanes, queried on PubMed via NCBI E-utilities (keyless, free):

    python3 src/pull_evidence_surveillance.py [--force] [--merge-only]

- esearch (one call per lane) returns the lane COUNT — the "N FOUND"
  shown everywhere is the count of the exact query recorded in the
  artifact — plus a candidate pool sorted by publication date.
- efetch (one batched call per lane) returns the candidate records.
- Deterministic card rule: systematic reviews / meta-analyses first
  (lane 3 also prefers other reviews), then most recent by
  publication date; 3 cards per lane. Every card stores its abstract
  so the plain-language Finding line on the evidence page is
  traceable to the paper itself.
- Plain-language headlines / Finding lines live in the committed
  overlay data/evidence_plain_lines.json (keyed by PMID) and are
  MERGED into the artifact here. A selected paper with no overlay
  entry keeps headline/finding = null, and the page generator
  (src/make_evidence_page.py) then fails closed — a refresh can
  never silently publish an unwritten summary. `--merge-only`
  re-applies the overlay to the existing artifact with no network.

Etiquette / failure discipline: tool=hardball on every call,
sequential requests with a pause (<=3/sec), one efetch batch per
lane. On any non-200 or network error the pull aborts and writes
NOTHING (fail closed — no partial artifact). Staleness guard: if
the artifact is <6 days old, print SKIP and exit 0 unless --force
(same discipline as src/refresh_live_feeds.py).

Output: data/evidence_surveillance.json
This is a standalone serving pull (like src/pull_npb_bis.py), NOT a
platform ingest source; the dashboard and the evidence page render
from the committed artifact only.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evidence_surveillance.json"
OVERLAY = ROOT / "data" / "evidence_plain_lines.json"

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "hardball-evidence-surveillance/1.0 (research demo)"}
PAUSE_S = 0.4
STALE_DAYS = 6
CANDIDATES = 60
CARDS_PER_LANE = 3

SRMA = {"Systematic Review", "Meta-Analysis"}

LANES = [
    {
        "id": "ucl_rtp",
        "label": "RETURN TO PLAY · UCL & THE ELBOW",
        "heading": "Return to Play After UCL Reconstruction",
        "query": '"ulnar collateral ligament" AND reconstruction AND '
                 '"return to play"',
        "review_tier": False,
    },
    {
        "id": "prevention_workload",
        "label": "INJURY PREVENTION & WORKLOAD · BASEBALL",
        "heading": "Injury Prevention and Workload",
        "query": 'baseball AND ("injury prevention" OR workload)',
        "review_tier": False,
    },
    {
        "id": "cellular_recovery",
        "label": "CELLULAR RECOVERY · MUSCLE REGENERATION",
        "heading": "Muscle Regeneration and Cellular Recovery",
        "query": '("skeletal muscle regeneration" OR "satellite cells") '
                 'AND (injury OR exercise) AND recovery',
        "review_tier": True,
    },
    {
        "id": "tendon_biologics",
        "label": "TENDON HEALING & BIOLOGICS",
        "heading": "Tendon Healing and Biologics",
        "query": '(tendon OR ligament) AND (healing OR regeneration) AND '
                 '("platelet-rich plasma" OR "growth factors" OR '
                 '"stem cells") AND (systematic review[pt] OR '
                 'meta-analysis[pt])',
        "review_tier": False,
    },
]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}


def http_get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url[:90]}")
        return resp.read()


def esearch(query):
    params = {"db": "pubmed", "term": query, "retmode": "json",
              "retmax": CANDIDATES, "sort": "pub_date", "tool": "hardball"}
    url = BASE + "/esearch.fcgi?" + urllib.parse.urlencode(params)
    data = json.loads(http_get(url))
    r = data["esearchresult"]
    if r.get("errorlist"):
        raise RuntimeError(f"esearch error for {query!r}: {r['errorlist']}")
    return int(r["count"]), [str(i) for i in r["idlist"]]


def efetch(pmids):
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml",
              "tool": "hardball"}
    url = BASE + "/efetch.fcgi?" + urllib.parse.urlencode(params)
    return ET.fromstring(http_get(url))


def txt(el):
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def pub_date_tuple(article):
    pd = article.find(".//Journal/JournalIssue/PubDate")
    year = month = day = None
    if pd is not None:
        y = txt(pd.find("Year"))
        year = int(y) if y.isdigit() else None
        m = txt(pd.find("Month"))
        if m:
            month = MONTHS.get(m[:3].lower()) or (int(m) if m.isdigit() else None)
        d = txt(pd.find("Day"))
        day = int(d) if d.isdigit() else None
        if year is None:
            md = txt(pd.find("MedlineDate"))
            mm = re.search(r"(19|20)\d{2}", md)
            year = int(mm.group(0)) if mm else None
    if year is None:
        ad = article.find(".//ArticleDate")
        if ad is not None and txt(ad.find("Year")).isdigit():
            year = int(txt(ad.find("Year")))
    return (year or 0, month or 1, day or 1)


def parse_article(pa):
    art = pa.find(".//Article")
    pmid = txt(pa.find(".//MedlineCitation/PMID"))
    authors, display = [], []
    for a in art.findall(".//AuthorList/Author"):
        coll = txt(a.find("CollectiveName"))
        if coll:
            authors.append(coll)
            display.append(coll)
            continue
        last, init = txt(a.find("LastName")), txt(a.find("Initials"))
        if last:
            authors.append(f"{last} {init}".strip())
            display.append(f"{last} {init}".strip())
    if len(display) > 6:
        authors_display = ", ".join(display[:3]) + ", et al."
    else:
        authors_display = ", ".join(display)
    journal = txt(art.find(".//Journal/Title"))
    abbr = txt(art.find(".//Journal/ISOAbbreviation"))
    ji = art.find(".//Journal/JournalIssue")
    volume = txt(ji.find("Volume")) if ji is not None else ""
    issue = txt(ji.find("Issue")) if ji is not None else ""
    pages = txt(art.find(".//Pagination/MedlinePgn"))
    doi = ""
    for el in art.findall(".//ELocationID"):
        if el.get("EIdType") == "doi":
            doi = txt(el)
    if not doi:
        for el in pa.findall(".//PubmedData/ArticleIdList/ArticleId"):
            if el.get("IdType") == "doi":
                doi = txt(el)
    abstract_parts = []
    for ab in art.findall(".//Abstract/AbstractText"):
        t = txt(ab)
        if t:
            label = ab.get("Label")
            abstract_parts.append(f"{label}: {t}" if label else t)
    abstract = " ".join(abstract_parts)
    pubtypes = [txt(p) for p in art.findall(
        ".//PublicationTypeList/PublicationType")]
    y, m, d = pub_date_tuple(art)
    # AMA citation: Authors. Title. JournalAbbr. Year;vol(issue):pages. doi:…
    title = txt(art.find("ArticleTitle"))
    sep = " " if authors_display.endswith("et al.") else ". "
    cite = f"{authors_display}{sep}{title} {abbr or journal}."
    tail = str(y or "")
    if volume:
        tail += f";{volume}"
        if issue:
            tail += f"({issue})"
    if pages:
        tail += f":{pages}"
    cite += f" {tail}." if tail else ""
    if doi:
        cite += f" doi:{doi}"
    return {
        "pmid": pmid,
        "authors": authors,
        "authors_display": authors_display,
        "title": title,
        "journal": journal,
        "journal_abbr": abbr,
        "year": y or None,
        "volume": volume or None,
        "issue": issue or None,
        "pages": pages or None,
        "doi": doi or None,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "pub_types": pubtypes,
        "pub_date": f"{y:04d}-{m:02d}-{d:02d}" if y else None,
        "abstract": abstract,
        "abstract_present": bool(abstract),
        "citation": cite,
        "headline": None,
        "finding": None,
    }


def tier_of(card, review_tier):
    pts = set(card["pub_types"])
    if pts & SRMA:
        return 0
    if review_tier and "Review" in pts:
        return 1
    return 2 if review_tier else 1


def apply_overlay(artifact):
    overlay = {}
    if OVERLAY.exists():
        overlay = json.loads(OVERLAY.read_text()).get("by_pmid", {})
    n = 0
    for lane in artifact["lanes"]:
        for card in lane["cards"]:
            o = overlay.get(card["pmid"])
            if o:
                card["headline"] = o["headline"]
                card["finding"] = o["finding"]
                n += 1
    artifact["metadata"]["plain_lines_merged"] = n
    return artifact


def build_artifact():
    run_date = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    lanes = []
    for lane in LANES:
        count, pmids = esearch(lane["query"])
        time.sleep(PAUSE_S)
        if len(pmids) < CARDS_PER_LANE:
            raise RuntimeError(
                f"lane {lane['id']}: only {len(pmids)} candidates")
        root = efetch(pmids)
        time.sleep(PAUSE_S)
        by_pmid = {}
        for pa in root.findall(".//PubmedArticle"):
            card = parse_article(pa)
            by_pmid[card["pmid"]] = card
        cards = [by_pmid[p] for p in pmids if p in by_pmid]
        # deterministic: tier asc, then pub date desc (stable — esearch
        # already returns pub-date order for equal keys)
        cards.sort(key=lambda c: (
            tier_of(c, lane["review_tier"]),
            tuple(-v for v in (int(x) for x in
                               (c["pub_date"] or "0000-00-00").split("-")))))
        selected = cards[:CARDS_PER_LANE]
        if len(selected) < CARDS_PER_LANE:
            raise RuntimeError(
                f"lane {lane['id']}: only {len(selected)} selectable")
        lanes.append({
            "id": lane["id"],
            "label": lane["label"],
            "heading": lane["heading"],
            "query": lane["query"],
            "found": count,
            "cards": selected,
        })
        print(f"lane {lane['id']}: found={count} "
              f"selected={[c['pmid'] for c in selected]}")
    artifact = {
        "metadata": {
            "source": "PubMed / NCBI E-utilities (esearch + efetch)",
            "source_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "keyless": True,
            "tool_param": "hardball",
            "run_date": run_date.isoformat(),
            "generated_at_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"),
            "selection_rule": "Per lane: systematic reviews / "
                              "meta-analyses first (cellular-recovery "
                              "lane also prefers other reviews), then "
                              "most recent by publication date; "
                              f"{CARDS_PER_LANE} cards per lane.",
            "cards_per_lane": CARDS_PER_LANE,
            "context_label": "Literature surveillance — context, "
                             "not a model input.",
            "refresh_guard_days": STALE_DAYS,
            "pull_script": "src/pull_evidence_surveillance.py",
        },
        "lanes": lanes,
    }
    return apply_overlay(artifact)


def main():
    force = "--force" in sys.argv
    merge_only = "--merge-only" in sys.argv
    if merge_only:
        if not OUT.exists():
            print("FAIL: no existing artifact to merge into")
            return 1
        artifact = apply_overlay(json.loads(OUT.read_text()))
        OUT.write_text(json.dumps(artifact, indent=1) + "\n")
        print(f"MERGE-ONLY OK: {artifact['metadata']['plain_lines_merged']} "
              "plain lines merged")
        return 0
    if OUT.exists() and not force:
        try:
            prev = json.loads(OUT.read_text())
            prev_date = date.fromisoformat(prev["metadata"]["run_date"])
            age = (datetime.now(ZoneInfo("America/Los_Angeles")).date()
                   - prev_date).days
            if age < STALE_DAYS:
                print(f"SKIP: artifact from {prev_date} is {age}d old "
                      f"(< {STALE_DAYS}d guard); use --force to re-pull")
                return 0
        except Exception:
            pass  # unreadable artifact: fall through and re-pull
    try:
        artifact = build_artifact()
    except Exception as e:
        print(f"PULL FAILED (fail closed, nothing written): {e}")
        return 1
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(artifact, indent=1) + "\n")
    tmp.replace(OUT)
    print(f"PULL OK: {OUT} run_date={artifact['metadata']['run_date']} "
          f"plain lines merged={artifact['metadata']['plain_lines_merged']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
