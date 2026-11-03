#!/usr/bin/env python3
"""Cycle 55 — production refresh for the two live feeds.

This is the path the 6-hourly 24/7 job calls to keep the census
(FastballAPI) and event layer (Statyx) current:

    python3 src/refresh_live_feeds.py [--force]

Guards (both read from data/raw/manifest.jsonl, the committed
ledger):
- Watermark: if the last successful pull is <20h old, print a SKIP
  line and exit 0. FastballAPI refreshes once daily (10:00 UTC), so
  more frequent pulls buy nothing. `--force` overrides ONLY this
  guard.
- Credit budget: month-to-date FastballAPI credits are summed from
  the manifest's `credits` fields; at >=200 credits in the current
  month the refresh hard-skips (exit 0) regardless of --force. The
  plan allows 500/month; 200 is the working cap so a runaway caller
  cannot burn the budget. (Cycle 51's pull predates the credits
  field; its 4 credits are accounted in LEGACY_CREDITS below.)

Flow on a live run: pull all four endpoints (fail closed — nothing
lands unless every call answers 200) -> land changed snapshots ->
rebuild data/il_current_live.json and data/il_events.json -> print
a one-line summary.

OFFLINE SAFETY: this script is the ONLY network path for the feeds
and is invoked explicitly. The data gate (src/verify_data.py) never
calls it and verifies committed artifacts only, so gate/CI contexts
run fully offline.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional  # 3.9: use Optional instead of PEP 604 |

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "raw" / "manifest.jsonl"

WATERMARK_HOURS = 20
MONTHLY_CREDIT_CAP = 200
# Pulls landed before the manifest carried a `credits` field.
LEGACY_CREDITS = {"2026-11": 4}  # Cycle 51 (2026-11-02): 2 calls x 2

FEED_SOURCES = ("statyx", "fastballapi")


def manifest_entries() -> list[dict]:
    return [json.loads(l) for l in MANIFEST.read_text().splitlines()
            if l.strip()]


def last_pull(entries) -> Optional[datetime]:
    ts = [e["fetched_at"] for e in entries
          if e["source"] in FEED_SOURCES
          and e.get("status") in ("ok", "ok_no_change")]
    if not ts:
        return None
    return datetime.fromisoformat(max(ts))


def month_credits(entries, month: str) -> int:
    total = LEGACY_CREDITS.get(month, 0)
    for e in entries:
        if e.get("fetched_at", "")[:7] == month:
            total += int(e.get("credits", 0))
    return total


def main() -> int:
    force = "--force" in sys.argv
    now = datetime.now(timezone.utc)
    entries = manifest_entries()

    lp = last_pull(entries)
    if lp is not None and not force:
        age_h = (now - lp).total_seconds() / 3600
        if age_h < WATERMARK_HOURS:
            print(f"SKIP: last successful pull {lp.isoformat()} is "
                  f"{age_h:.1f}h old (< {WATERMARK_HOURS}h watermark)")
            return 0

    month = now.strftime("%Y-%m")
    mtd = month_credits(entries, month)
    if mtd >= MONTHLY_CREDIT_CAP:
        print(f"SKIP: FastballAPI credit budget reached — {mtd} "
              f"credits in {month} (cap {MONTHLY_CREDIT_CAP}/month)")
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import bml_cycle55
    try:
        res = bml_cycle55.pull_and_rebuild()
    except SystemExit as e:
        print(f"REFRESH FAILED (fail closed, nothing landed): {e}")
        return 1
    art = res["artifact"]
    f = art["fa_pool_summary"]
    print(f"REFRESH OK: {res['credits']} FastballAPI credits "
          f"({mtd + res['credits']} MTD in {month}); landed "
          f"{res['landed'] or 'none (no state change)'}; FA-pool "
          f"movement: {f['new_il']} new IL, {f['returned']} returned, "
          f"{f['status_change']} status changes since "
          f"{art['metadata']['baseline_date']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
