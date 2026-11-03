# Social signals for the free-agent tracker

Social activity can provide early awareness of announcements, agent statements, rumors, and market attention. It cannot establish that a player signed.

## Source policy

| Lane | Source | Use | Confidence |
|---|---|---|---|
| Confirmed | MLB Stats API transactions | Signed, released, DFA, trade, option, and related move status | High |
| Reported | MLB.com and reputable news links | Context and attributed reporting | Medium |
| Social signal | Bluesky public search or Jetstream | Early awareness, announcement discovery, tags, and attention trends | Unverified |

The promotion rule is strict: a social signal never becomes a confirmed transaction without an MLB transaction record.

## Current implementation

src/social_signals.py reads Bluesky's public search endpoint without an account or token and emits normalized records with source, lane, confidence, author, timestamp, URI, and text. Use it for a bounded query, not an unbounded firehose:

    python src/social_signals.py --query '"free agent" MLB' --limit 25

Bluesky's public AppView supports unauthenticated reads, and its protocol also supports firehose-style streams. The current implementation uses bounded search so the dashboard remains cheap, explainable, and easy to audit.

## Sources considered but not enabled as core dependencies

- X API: recent search is available to developers, but current access is pay-per-use and requires an approved developer application. It should be an optional research connector, not a free dependency.
- Reddit Data API: OAuth is required, with rate limits and deletion/retention obligations. It can be a later opt-in source, not a silent scrape.
- MLB.com and MLBPA pages: useful first-party announcement and eligibility validation, but they are web sources rather than social APIs.
- FanGraphs tracker: excellent market reference, but not a free public API contract. Keep it as a cited comparison or cached snapshot.

## Recommended product behavior

Show social evidence in a separate Signals lane with the query, timestamp, author, link, and confidence label. Do not mix it into the confirmed ticker, do not infer a signing from hashtags, and do not score sentiment as player value without a validated research design.
