# HARDBALL topic-by-journal literature surveillance

This is an **additive discovery feed** for the existing **What the Evidence Says Now** research arm. It is not a replacement for the four PubMed evidence lanes, manually approved Finding lines, or the existing fourteen-journal spotlight.

## Scope

The script queries PubMed for **three distinct topics**, each restricted to relevant journals already enumerated in `src/pull_journal_spotlight.py`:

1. Injury prevention and workload, with a baseball/throwing context.
2. Muscle regeneration, satellite cells, repair and recovery.
3. Tendon healing, rehabilitation and biologics.

Each journal search records its exact query, total PubMed match count, and the two newest matching indexed papers (PMID, title, date and PubMed link). A title is a reading lead, **not a verified conclusion**. There is no invented summary or assertion that findings transfer to MLB athletes. PubMed indexes journals; this tool does not scrape publisher websites or bypass subscription restrictions.

## Execution (no GitHub Actions)

From the repository root:

```bash
python3 src/pull_topic_journal_surveillance.py
python3 -m pytest -q tests/test_topic_journal_surveillance.py
```

Result: `data/topic_journal_surveillance.json`. The pull writes the full JSON atomically only on success; failures preserve the previous artifact.

To automate locally, use a machine that runs continuously, e.g. `cron` (weekly Sunday 07:00 machine-local time):

```cron
0 7 * * 0 cd /absolute/path/to/hardball && /absolute/path/to/python3 src/pull_topic_journal_surveillance.py >> /absolute/path/to/hardball/topic-journal.log 2>&1
```

An external Render cron job or other scheduler may also invoke the command. **No schedule is activated by merging this code**. Committing refreshed JSON or deploying it to GitHub Pages requires a separate approved deployment workflow; local cron alone does not publish new site content.

## Quality and provenance safeguards

- NCBI E-utilities with the repository's established sequential 0.4-second pacing, avoiding more than three requests per second without an API key.
- Reuse the existing PubMed journal catalog and its catalogue-title aliases.
- Record query string and count alongside every result.
- No automatic Finding/headline generation and no changes to the dashboard's existing evidence.
- Before inclusion in curated **What the Evidence Says Now** cards, require manual review of abstract/full text, study population, design, applicability, limitations, and source citation.
- Deduplicate PMIDs across journals/topics when analyzing the consolidated feed.

**Next integration step:** after review and successful live pull, add an optional reading-list section to `src/make_evidence_page.py` using this committed artifact. Do not expose unreviewed titles as evidence summaries.
