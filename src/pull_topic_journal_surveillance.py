#!/usr/bin/env python3
"""Topic-specific, journal-scoped PubMed discovery for HARDBALL's research arm.

Run manually or from a non-GitHub-Actions scheduler:
    python3 src/pull_topic_journal_surveillance.py

Complements the existing four evidence lanes and journal spotlight without
changing curated findings or treating literature as model inputs. Data are
bibliographic discovery leads only, NOT validated medical conclusions.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pull_journal_spotlight import GROUPS, esearch, efetch, parse_paper

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "topic_journal_surveillance.json"
PAUSE_S = 0.4

TOPICS = [
    {
        "id": "injury_prevention_workload",
        "label": "Injury prevention and workload",
        "term": '(("injury prevention"[tiab] OR "injury risk"[tiab] OR workload[tiab] OR "pitch count"[tiab]) AND (baseball[tiab] OR pitcher[tiab] OR pitching[tiab] OR throwing[tiab]))',
        "journals": ["The American Journal of Sports Medicine", "Journal of Shoulder and Elbow Surgery",
                     "British Journal of Sports Medicine", "Orthopaedic Journal of Sports Medicine",
                     "Journal of Athletic Training", "Sports Biomechanics"],
    },
    {
        "id": "muscle_regeneration",
        "label": "Muscle regeneration and recovery",
        "term": '(("skeletal muscle regeneration"[tiab] OR "muscle repair"[tiab] OR "satellite cells"[tiab]) AND (exercise[tiab] OR injury[tiab] OR rehabilitation[tiab] OR recovery[tiab]))',
        "journals": ["Journal of applied physiology (Bethesda, Md. : 1985)", "Frontiers in Physiology",
                     "Medicine and Science in Sports and Exercise",
                     "International Journal of Sports Physiology and Performance",
                     "Journal of Strength and Conditioning Research"],
    },
    {
        "id": "tendon_healing",
        "label": "Tendon healing and regeneration",
        "term": '((tendon[tiab] OR tendinopathy[tiab] OR ligament[tiab]) AND (healing[tiab] OR regeneration[tiab] OR rehabilitation[tiab]) AND (treatment[tiab] OR exercise[tiab] OR biologic[tiab] OR "platelet-rich plasma"[tiab]))',
        "journals": ["The American Journal of Sports Medicine", "Journal of Shoulder and Elbow Surgery",
                     "British Journal of Sports Medicine", "Orthopaedic Journal of Sports Medicine",
                     "The Journal of orthopaedic and sports physical therapy", "Sports Health"],
    },
]


def catalog_names():
    mapping = {}
    for group in GROUPS:
        for entry in group["journals"]:
            mapping[entry[2] if len(entry) > 2 else entry[0]] = entry[0]
    return mapping


def make_query(term, catalog):
    return f'({term}) AND "{catalog}"[jour]'


def build():
    catalogs = catalog_names()
    topics = []
    for topic in TOPICS:
        results = []
        for catalog in topic["journals"]:
            if catalog not in catalogs:
                raise ValueError(f"Unrecognized PubMed catalog journal: {catalog}")
            query = make_query(topic["term"], catalog)
            count, pmids = esearch(query)
            time.sleep(PAUSE_S)
            papers = []
            if pmids:
                root = efetch(pmids)
                time.sleep(PAUSE_S)
                records = {p["pmid"]: p for pa in root.findall(".//PubmedArticle")
                           if (p := parse_paper(pa))["pmid"]}
                papers = [records[p] for p in pmids if p in records]
            results.append({
                "journal": catalogs[catalog], "pubmed_catalog": catalog,
                "query": query, "found": count, "papers": papers,
            })
        topics.append({"id": topic["id"], "label": topic["label"],
                       "term": topic["term"], "journals": results})
    return {
        "metadata": {
            "source": "NCBI PubMed E-utilities", "pulled_at_utc": datetime.now(timezone.utc).isoformat(),
            "description": "Topic-by-journal discovery; unreviewed reading list, not clinical advice or a model input.",
            "selection": "Most recent two matching PubMed-indexed records per journal; no quality inference from recency.",
            "script": "src/pull_topic_journal_surveillance.py",
            "refresh": "Run via external scheduler; GitHub Actions not required.",
        },
        "topics": topics,
    }


def main():
    try:
        artifact = build()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, OUT)
        print(f"SUCCESS: {OUT} ({sum(len(j['papers']) for t in artifact['topics'] for j in t['journals'])} PubMed records)")
        return 0
    except Exception as exc:
        print(f"FAILED CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
