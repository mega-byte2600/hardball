"""Offline contract checks for the additive topic-by-journal PubMed research pull."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pull_topic_journal_surveillance import TOPICS, catalog_names, make_query


def test_three_expected_topics():
    assert {t["id"] for t in TOPICS} == {
        "injury_prevention_workload", "muscle_regeneration", "tendon_healing"
    }


def test_all_journals_are_in_existing_verified_catalog():
    catalog = catalog_names()
    assert all(t["journals"] for t in TOPICS)
    assert all(j in catalog for t in TOPICS for j in t["journals"])


def test_topic_and_journal_are_both_scoped():
    for topic in TOPICS:
        assert "[tiab]" in topic["term"]
        for journal in topic["journals"]:
            query = make_query(topic["term"], journal)
            assert topic["term"] in query
            assert f'"{journal}"[jour]' in query


def test_unique_topic_ids_and_no_empty_queries():
    assert len({t["id"] for t in TOPICS}) == len(TOPICS)
    assert all(t["term"].strip() for t in TOPICS)
