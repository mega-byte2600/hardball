#!/usr/bin/env python3
"""HARDBALL platform ingestion — parallel batch + watermark micro-batch.

Data-engineering standard (docs/DATA_PLATFORM.md): land raw data
immutably, with a manifest entry per object (source, URL, fetched_at,
sha256, bytes, rows, status). Bounded concurrency (6 workers) across
independent partitions; per-source politeness; failures degrade the
run report, never prior state. (src/ingest.py remains the SQLite lake
loader; this is the platform raw-zone ingestion.)

Sources (all keyless):
  mlb_api      standings + team list (batch)
  savant       expected / batted-ball / sprint / bat-tracking CSVs,
               2023-2026 (batch, parallel by family x season)
  fangraphs    Steamer 2027 bat/pit via the FG API (batch)
  transactions MLB transactions, WATERMARK micro-batch: only events
               after data/raw/_watermarks.json's last date are pulled,
               in monthly partitions; the watermark advances on success
  npb_bis      NPB official BIS leaderboards (bat_c/bat_p/pit_c/pit_p,
               2024-2026, keyless) — the Fig. 23 raw zone. The verified
               curated trio lives in data/posted_class_2026.json; this
               task only lands the raw leaderboard CSV, never rewrites it
  chadwick     Chadwick Bureau Register people shards (keyless CSV,
               ODC-BY) — the player ID crosswalk (Cycle 44)
  injury_report The Injury Report IL stints CSV 2019-2026 (keyless,
               built from MLB IL transactions) — availability history
               cross-checks (Cycle 44)
  bref_war     Baseball-Reference WAR daily downloads (keyless txt);
               the salary column is a labeled cross-check ONLY — it
               failed the Cycle 44 credibility bar for a dataset, so it
               lands raw and is never curated into a salary table
  spotrac      serial, cache-first (local mirror cache), stops at the
               first block; status recorded either way

Usage: python3 src/ingest_platform.py [--only mlb_api,savant] [--workers 6]
Output: data/raw/<source>/<dataset>.json|csv, data/raw/manifest.jsonl
        (append-only), data/raw/_watermarks.json
"""
import argparse
import hashlib
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def get(url, tries=3):
    last = None
    for a in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=45)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
            if r.status_code in (403, 429):
                break  # rate-limit class: stop, don't hammer
        except requests.RequestException as e:
            last = str(e)[:80]
        time.sleep(2 * a + 1)
    raise RuntimeError(last or "fetch failed")


def land(source, dataset, content: bytes, rows, ext="json"):
    d = RAW / source
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{dataset}.tmp"
    tmp.write_bytes(content)
    tmp.replace(d / f"{dataset}.{ext}")  # atomic replace: idempotent
    return {"source": source, "dataset": dataset, "fetched_at": NOW,
            "sha256": sha(content), "bytes": len(content), "rows": rows,
            "status": "ok"}


def t_mlb_standings():
    r = get("https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"
            "&season=2026&standingsTypes=regularSeason")
    n = sum(len(rec["teamRecords"]) for rec in r.json()["records"])
    return [land("mlb_api", "standings_2026", r.content, n)]


def t_mlb_teams():
    r = get("https://statsapi.mlb.com/api/v1/teams?sportId=1")
    return [land("mlb_api", "teams", r.content, len(r.json()["teams"]))]


def savant_url(kind, year):
    """URLs mirrored EXACTLY from src/carpe.py (proven 2026-10-31).
    Warning (carpe's docstring, re-learned by this module's first run):
    the bat-tracking endpoint only honors the date-range form; a
    ?year= parameter is silently ignored and returns the current
    season for every year. Bat tracking exists only from 2024."""
    base = "https://baseballsavant.mlb.com"
    if kind == "expected":
        return (base + f"/expected_statistics?type=batter&year={year}"
                "&position=&team=&min=25&csv=true")
    if kind == "batted_ball":
        return (base + f"/statcast_leaderboard?year={year}&abs=25"
                "&type=batter&min=q&csv=true")
    if kind == "sprint":
        return (base + f"/leaderboard/sprint_speed?year={year}"
                "&position=&team=&min=25&csv=true")
    if kind == "bat_tracking":
        return (base + f"/leaderboard/bat-tracking?dateStart={year}-03-01"
                f"&dateEnd={year}-11-01&gameType=Regular&minSwings=25"
                f"&minGroupSwings=1&seasonStart={year}&seasonEnd={year}"
                "&type=batter&csv=true")
    raise ValueError(kind)


def t_savant(kind, year):
    r = get(savant_url(kind, year))
    rows = len(pd.read_csv(io.StringIO(r.text)))
    return [land("savant", f"{kind}_{year}", r.content, rows, ext="csv")]


def t_fangraphs(which):
    url = ("https://www.fangraphs.com/api/projections?type=steamer"
           f"&stats={which}&pos=all&players=0&lg=all")
    r = get(url)
    return [land("fangraphs", f"steamer_2027_{which}", r.content, len(r.json()))]


def month_chunks(start, end):
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-28"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def t_transactions_month(a, b):
    r = get("https://statsapi.mlb.com/api/v1/transactions"
            f"?startDate={a}&endDate={b}")
    return r.json().get("transactions", [])


def run_transactions():
    wm_path = RAW / "_watermarks.json"
    wm = json.loads(wm_path.read_text()) if wm_path.exists() else {}
    last = wm.get("transactions", "2024-12-31")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    chunks = list(month_chunks(last, today))
    all_txns = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(t_transactions_month, a, b) for a, b in chunks]
        for f in as_completed(futs):
            all_txns.extend(f.result())
    seen, uniq = set(), []
    for t in all_txns:  # dedupe on transaction id: idempotent re-runs
        if t["id"] not in seen:
            seen.add(t["id"])
            uniq.append(t)
    path = RAW / "transactions"
    path.mkdir(parents=True, exist_ok=True)
    cur = path / "transactions.json"
    existing = json.loads(cur.read_text()) if cur.exists() else []
    merged = {t["id"]: t for t in existing} | {t["id"]: t for t in uniq}
    out = sorted(merged.values(), key=lambda t: t["date"])
    entries = [land("transactions", "transactions", json.dumps(out).encode(), len(out))]
    new_wm = max(t["date"] for t in out) if out else last
    wm["transactions"] = new_wm
    wm_path.write_text(json.dumps(wm, indent=1))
    entries[0]["watermark_advanced_to"] = new_wm
    entries[0]["new_events"] = len(uniq)
    return entries


def t_npb_bis():
    """NPB official BIS leaderboards, 2024-2026 (see src/pull_npb_bis.py
    for the standalone repro pull with trio extraction). Lands one raw
    CSV; the curated posted-class dataset is never rewritten here."""
    frames = []
    for year in (2024, 2025, 2026):
        for kind in ("bat_c", "bat_p", "pit_c", "pit_p"):
            url = f"https://npb.jp/bis/{year}/stats/{kind}.html"
            r = get(url)  # raises (and stops) on 403/429; single fetch
            r.encoding = "utf-8"
            for ti, t in enumerate(pd.read_html(io.StringIO(r.text))):
                t = t.copy()
                t["year"] = year
                t["table"] = f"{kind}[{ti}]"
                frames.append(t)
            time.sleep(0.7)
    out = pd.concat(frames, ignore_index=True)
    return [land("npb_bis", "leaderboards_2024_2026",
                 out.to_csv(index=False).encode(), len(out), ext="csv")]


def t_chadwick():
    """Chadwick Bureau Register: 16 sharded people CSVs on GitHub,
    keyless, ODC-BY licence. Landed concatenated; curation keeps the
    rows carrying an MLBAM key."""
    frames = []
    shards = [str(i) for i in range(10)] + list("abcdef")
    for s in shards:
        r = get("https://raw.githubusercontent.com/chadwickbureau/"
                f"register/master/data/people-{s}.csv")
        frames.append(pd.read_csv(io.StringIO(r.text), low_memory=False))
    out = pd.concat(frames, ignore_index=True)
    return [land("chadwick", "people", out.to_csv(index=False).encode(),
                 len(out), ext="csv")]


def t_injury_report():
    """The Injury Report (Seehafer): every MLB IL stint 2019-2026,
    built from MLB's own IL transactions. Keyless CSV download."""
    url = ("https://lucasseehafer.github.io/the-injury-report/downloads/"
           "mlb_injured_list_stints_2019-2026.csv")
    r = get(url)
    rows = len(pd.read_csv(io.StringIO(r.text)))
    return [land("injury_report", "il_stints_2019_2026", r.content,
                 rows, ext="csv")]


def t_bref_war(kind):
    r = get(f"https://www.baseball-reference.com/data/war_daily_{kind}.txt")
    rows = len(pd.read_csv(io.StringIO(r.text), low_memory=False))
    return [land("bref_war", f"war_daily_{kind}", r.content, rows, ext="txt")]


def run_spotrac():
    cache = Path.home() / "workspace/github/hardball/data/raw/spotrac"
    if cache.exists():
        pages = sorted(cache.glob("*.html"))
        e = land("spotrac", "_cache_index",
                 json.dumps([p.name for p in pages]).encode(), len(pages))
        e["status"] = "cache_present"
        e["note"] = "HTML blobs live in the local mirror cache; parsed by bml_cycle25.py"
        return [e]
    return [{"source": "spotrac", "dataset": "_cache_index", "fetched_at": NOW,
             "status": "no_cache", "rows": 0,
             "note": "no local cache in this environment; salaries curated from committed artifact"}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    RAW.mkdir(parents=True, exist_ok=True)

    tasks = []
    if not only or "mlb_api" in only:
        tasks += [("mlb standings", t_mlb_standings), ("mlb teams", t_mlb_teams)]
    if not only or "savant" in only:
        for kind in ("expected", "batted_ball", "sprint", "bat_tracking"):
            years = (2024, 2025, 2026) if kind == "bat_tracking" else (2023, 2024, 2025, 2026)
            for year in years:
                tasks.append((f"savant {kind} {year}",
                              (lambda k, y: lambda: t_savant(k, y))(kind, year)))
    if not only or "fangraphs" in only:
        tasks += [("fg steamer bat", lambda: t_fangraphs("bat")),
                  ("fg steamer pit", lambda: t_fangraphs("pit"))]
    if not only or "npb_bis" in only:
        tasks += [("npb bis leaderboards", t_npb_bis)]
    if not only or "chadwick" in only:
        tasks += [("chadwick register", t_chadwick)]
    if not only or "injury_report" in only:
        tasks += [("injury report il stints", t_injury_report)]
    if not only or "bref_war" in only:
        tasks += [("bref war bat", lambda: t_bref_war("bat")),
                  ("bref war pitch", lambda: t_bref_war("pitch"))]

    entries, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fn): label for label, fn in tasks}
        for f in as_completed(futs):
            label = futs[f]
            try:
                entries.extend(f.result())
            except Exception as e:  # degrade the report, not the state
                failures.append({"task": label, "error": str(e)[:120]})
                print(f"  FAIL {label}: {e}")
    if not only or "transactions" in only:
        try:
            entries.extend(run_transactions())
        except Exception as e:
            failures.append({"task": "transactions", "error": str(e)[:120]})
            print(f"  FAIL transactions: {e}")
    if not only or "spotrac" in only:
        entries.extend(run_spotrac())

    with open(RAW / "manifest.jsonl", "a") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    ok = sum(1 for e in entries if e["status"] == "ok")
    print(f"INGEST: {ok} datasets landed, {len(entries)} entries, "
          f"{len(failures)} failures")
    for e in entries:
        print(f"  {e['source']}/{e['dataset']}: {e['rows']} rows [{e['status']}]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
