#!/usr/bin/env python3
"""Cycle 90 — PubMed journal spotlight pull for the HARDBALL evidence page.

Owner-directed (2026-11-07): a "Go deeper" reading resource at the
end of docs/EVIDENCE.html. For each journal behind the page's topics
(14 journals in 3 groups), pull its 2 most recent pitching/baseball
papers from PubMed via NCBI E-utilities (keyless, free):

    python3 src/pull_journal_spotlight.py

Per journal: esearch with
    ("baseball" OR "pitching" OR "pitchers") AND "<journal>"[jour]
sorted by publication date, retmax=2; efetch returns the records.
Three journals are indexed by PubMed under a catalog title that
differs from their display name ("The American Journal of Sports
Medicine", "The Journal of orthopaedic and sports physical
therapy", "Journal of applied physiology (Bethesda, Md. : 1985)")
— for those the query uses the catalog title and the artifact
records the exact query run. An esearch warning that the quoted
journal phrase was not found in the index aborts the pull (fail
closed) rather than recording a false zero.
The artifact stores ONLY what PubMed returns — verbatim title,
publication date as given, PMID, and the PubMed URL built from that
PMID. No summaries, no Finding lines, no claims: this section is a
reading list, and it stays outside the evidence lanes' fail-closed
Finding rule in src/pull_evidence_surveillance.py.

The journal heading link is the journal's official homepage ONLY if
it answers HTTP 200 during this build; otherwise the heading links
the PubMed journal-filtered search for that journal. The artifact
records which link was used (link_kind) and the homepage status.

Discipline (same as the surveillance pull): tool=hardball on every
E-utilities call, sequential requests with a pause. On any
E-utilities error the pull aborts and writes NOTHING (fail closed).
A journal with zero hits is recorded with an empty paper list — the
page prints a plain no-papers line; no paper is ever substituted.

Output: data/journal_spotlight.json
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "journal_spotlight.json"

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "hardball-journal-spotlight/1.0 (research demo)"}
BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
                            "10_15_7) AppleWebKit/537.36 (KHTML, "
                            "like Gecko) Chrome/126.0 Safari/537.36"}
PAUSE_S = 0.4
PAPERS_PER_JOURNAL = 2

TOPIC_TERM = '("baseball" OR "pitching" OR "pitchers")'

GROUPS = [
    {
        "id": "velocity_biomechanics",
        "heading": "Throwing velocity & biomechanics",
        "journals": [
            ("American Journal of Sports Medicine",
             "https://journals.sagepub.com/home/ajs",
             "The American Journal of Sports Medicine"),
            ("Journal of Applied Biomechanics",
             "https://journals.humankinetics.com/view/journals/jab/"
             "jab-overview.xml"),
            ("Sports Biomechanics",
             "https://www.tandfonline.com/journals/rspb20"),
            ("Journal of Strength and Conditioning Research",
             "https://journals.lww.com/nsca-jscr"),
        ],
    },
    {
        "id": "wear_workload",
        "heading": "Arm wear, use & workload",
        "journals": [
            ("Journal of Shoulder and Elbow Surgery",
             "https://www.jshoulderelbow.org/"),
            ("British Journal of Sports Medicine",
             "https://bjsm.bmj.com/"),
            ("Orthopaedic Journal of Sports Medicine",
             "https://journals.sagepub.com/home/ojs"),
            ("Journal of Athletic Training",
             "https://meridian.allenpress.com/jat"),
        ],
    },
    {
        "id": "recovery",
        "heading": "Recovery",
        "journals": [
            ("Medicine and Science in Sports and Exercise",
             "https://journals.lww.com/acsm-msse"),
            ("International Journal of Sports Physiology and Performance",
             "https://journals.humankinetics.com/view/journals/ijspp/"
             "ijspp-overview.xml"),
            ("Journal of Orthopaedic & Sports Physical Therapy",
             "https://www.jospt.org/",
             "The Journal of orthopaedic and sports physical therapy"),
            ("Sports Health",
             "https://journals.sagepub.com/home/sph"),
            ("Journal of Applied Physiology",
             "https://journals.physiology.org/journal/jappl",
             "Journal of applied physiology (Bethesda, Md. : 1985)"),
            ("Frontiers in Physiology",
             "https://www.frontiersin.org/journals/physiology"),
        ],
    },
]

MONTH_ABBR = {i + 1: m for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
MONTH_NUM = {m.lower(): i for i, m in MONTH_ABBR.items()}


def http_get(url, headers=UA, timeout=45):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url[:90]}")
        return resp.status, resp.read()


def homepage_status(url):
    """HTTP status of the journal homepage, or None on any error.
    One retry when the first attempt fails without an HTTP status
    (timeout / connection drop), so a transient network error does
    not by itself decide the link kind."""
    for attempt in range(2):
        try:
            status, _ = http_get(url, headers=BROWSER_UA, timeout=30)
            return status
        except Exception as e:
            code = getattr(e, "code", None)
            if isinstance(code, int):
                return code
            if attempt == 0:
                time.sleep(1.0)
    return None


def esearch(query):
    params = {"db": "pubmed", "term": query, "retmode": "json",
              "retmax": PAPERS_PER_JOURNAL, "sort": "pub_date",
              "tool": "hardball"}
    url = BASE + "/esearch.fcgi?" + urllib.parse.urlencode(params)
    _, body = http_get(url)
    data = json.loads(body)
    r = data["esearchresult"]
    if r.get("errorlist"):
        raise RuntimeError(f"esearch error for {query!r}: {r['errorlist']}")
    notfound = (r.get("warninglist") or {}).get("quotedphrasesnotfound")
    if notfound:
        raise RuntimeError(
            f"esearch: journal phrase not in the PubMed index for "
            f"{query!r}: {notfound} — refusing to record a false zero")
    return int(r["count"]), [str(i) for i in r["idlist"]]


def efetch(pmids):
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml",
              "tool": "hardball"}
    url = BASE + "/efetch.fcgi?" + urllib.parse.urlencode(params)
    _, body = http_get(url)
    return ET.fromstring(body)


def txt(el):
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def pub_date_display(article):
    """Publication date 'as PubMed gives it': '2026 Nov 3', '2026 Nov',
    or '2026' — built only from the record's own PubDate fields."""
    pd = article.find(".//Journal/JournalIssue/PubDate")
    year = month = day = None
    if pd is not None:
        y = txt(pd.find("Year"))
        year = int(y) if y.isdigit() else None
        m = txt(pd.find("Month"))
        if m:
            month = MONTH_NUM.get(m[:3].lower()) or \
                (int(m) if m.isdigit() else None)
        d = txt(pd.find("Day"))
        day = int(d) if d.isdigit() else None
        if year is None:
            md = txt(pd.find("MedlineDate"))
            mm = re.search(r"(19|20)\d{2}", md)
            year = int(mm.group(0)) if mm else None
            if month is None:
                for name, num in MONTH_NUM.items():
                    if name in md.lower():
                        month = num
                        break
    if year is None:
        ad = article.find(".//ArticleDate")
        if ad is not None and txt(ad.find("Year")).isdigit():
            year = int(txt(ad.find("Year")))
            m = txt(ad.find("Month"))
            month = int(m) if m.isdigit() else None
            d = txt(ad.find("Day"))
            day = int(d) if d.isdigit() else None
    if year is None:
        return ""
    out = str(year)
    if month:
        out += f" {MONTH_ABBR[month]}"
        if day:
            out += f" {day}"
    return out


def parse_paper(pa):
    art = pa.find(".//Article")
    pmid = txt(pa.find(".//MedlineCitation/PMID"))
    return {
        "title": txt(art.find("ArticleTitle")),
        "date": pub_date_display(art),
        "pmid": pmid,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }


def pubmed_search_link(journal):
    q = urllib.parse.quote(f'"{journal}"[jour]')
    return f"https://pubmed.ncbi.nlm.nih.gov/?term={q}"


def build_artifact():
    groups = []
    for group in GROUPS:
        journals = []
        for entry in group["journals"]:
            name, homepage = entry[0], entry[1]
            catalog = entry[2] if len(entry) > 2 else name
            query = f'{TOPIC_TERM} AND "{catalog}"[jour]'
            count, pmids = esearch(query)
            time.sleep(PAUSE_S)
            papers = []
            if pmids:
                root = efetch(pmids)
                time.sleep(PAUSE_S)
                by_pmid = {}
                for pa in root.findall(".//PubmedArticle"):
                    paper = parse_paper(pa)
                    by_pmid[paper["pmid"]] = paper
                papers = [by_pmid[p] for p in pmids if p in by_pmid]
            status = homepage_status(homepage)
            if status == 200:
                link, link_kind = homepage, "official"
            else:
                link, link_kind = pubmed_search_link(name), "pubmed_search"
            journals.append({
                "name": name,
                "query": query,
                "found": count,
                "link": link,
                "link_kind": link_kind,
                "homepage": homepage,
                "homepage_status": status,
                "papers": papers,
            })
            print(f"{group['id']} / {name}: found={count} "
                  f"papers={len(papers)} link={link_kind} "
                  f"(homepage HTTP {status})")
        groups.append({"id": group["id"], "heading": group["heading"],
                       "journals": journals})
    return {
        "metadata": {
            "source": "PubMed / NCBI E-utilities (esearch + efetch)",
            "source_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "keyless": True,
            "tool_param": "hardball",
            "pulled_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"),
            "pulled_date_pt": datetime.now(
                ZoneInfo("America/Los_Angeles")).date().isoformat(),
            "selection_rule": "Per journal: 2 most recent PubMed "
                              "records matching (baseball OR pitching "
                              "OR pitchers) in that journal, sorted by "
                              "publication date. Titles and dates "
                              "verbatim from PubMed; no summaries.",
            "papers_per_journal": PAPERS_PER_JOURNAL,
            "link_rule": "Journal heading links its official "
                         "homepage only when it answered HTTP 200 "
                         "during this build; otherwise the PubMed "
                         "journal-filtered search.",
            "pull_script": "src/pull_journal_spotlight.py",
        },
        "groups": groups,
    }


def main():
    try:
        artifact = build_artifact()
    except Exception as e:
        print(f"PULL FAILED (fail closed, nothing written): {e}")
        return 1
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(artifact, indent=1) + "\n")
    tmp.replace(OUT)
    n = sum(len(j["papers"]) for g in artifact["groups"]
            for j in g["journals"])
    print(f"PULL OK: {OUT} papers={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
