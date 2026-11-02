#!/usr/bin/env python3
"""NPB official (npb.jp BIS) pull for HARDBALL Fig. 23 — the posted class.

Canonical source: https://npb.jp/bis/<year>/stats/<bat_c|bat_p|pit_c|pit_p>.html
(keyless, qualified leaderboards only — not full rosters). Names are
normalized with NFKC (BIS mixes variant kanji, e.g. Itoh's name uses
U+FA45 in 2025-26); 2024 pages parse with a one-row header offset
(positional columns). Politeness: 0.7s between requests, stop at a
403/429, never route around a block.

This is the REPRO pull. It lands raw leaderboards under data/raw/npb_bis/
(gitignored raw zone) plus a raw trio extraction. It does NOT overwrite
data/posted_class_2026.json — that file is the verified curated trio
dataset (pulled 2026-11-01, cross-checked vs AP wire reports, BIS
canonical over wire roundings: Sato .306 not .308, Itoh 34 BB not 32).
The dashboard figure reads the curated file, never this script's output.

Usage: python3 src/pull_npb_bis.py
Output: data/raw/npb_bis/npb_leaderboards_2024_2026_raw.csv
        data/raw/npb_bis/posted_trio_bis.json
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "npb_bis"
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
TARGETS = {"佐藤輝明": "Teruaki Sato", "平良海馬": "Kaima Taira", "伊藤大海": "Hiromi Itoh"}


def norm(s):
    return unicodedata.normalize("NFKC", str(s)).replace(" ", "").replace("　", "")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    found, links, frames = {}, {}, []
    for year in (2024, 2025, 2026):
        for kind in ("bat_c", "bat_p", "pit_c", "pit_p"):
            url = f"https://npb.jp/bis/{year}/stats/{kind}.html"
            r = requests.get(url, headers=H, timeout=25)
            r.encoding = "utf-8"
            if r.status_code in (403, 429):
                print(f"BLOCKED {url} -> {r.status_code}; stopping, prior state kept")
                return 1
            assert r.status_code == 200, (url, r.status_code)
            for m in re.finditer(r'href="[^"]*?/players/(\d+)\.html"[^>]*>([^<]+)</a>', r.text):
                links[norm(m.group(2))] = m.group(1)
            tables = pd.read_html(url, encoding="utf-8")
            for ti, t in enumerate(tables):
                t = t.copy()
                t["year"] = year
                t["table"] = f"{kind}[{ti}]"
                frames.append(t)
                namecol = t.columns[1]
                for _, row in t.iterrows():
                    base = re.sub(r"\(.\)$", "", norm(row[namecol]))
                    if base in TARGETS:
                        found.setdefault(TARGETS[base], []).append(
                            {"year": year, "table": f"{kind}[{ti}]",
                             **{str(k): v for k, v in row.items()}})
            time.sleep(0.7)

    pd.concat(frames, ignore_index=True).to_csv(
        OUT / "npb_leaderboards_2024_2026_raw.csv", index=False)
    ids = {v: links.get(k) for k, v in TARGETS.items()}
    json.dump({"found": found, "ids": ids}, open(OUT / "posted_trio_bis.json", "w"),
              ensure_ascii=False, indent=1)
    print("IDS:", ids)
    for name, recs in found.items():
        print(name, [(r["year"], r["table"]) for r in recs])
    print("leaderboard rows total:", sum(len(f) for f in frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
