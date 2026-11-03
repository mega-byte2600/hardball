#!/usr/bin/env python3
"""Cycle 66 — MLB free-agency tracker ticker pull (CarpeData).

One pull, all kept sources, polite rates, fail-closed per source: a
source that blocks (403/429) or errors is logged and skipped, never
retried around the block. No keys, no signups, no login scraping.

    python3 src/pull_tracker_ticker.py

Writes data/tracker_ticker_2026.json:
  metadata: pulled_at, window, caps, per-source status, class
      register count, Jetstream verdict
  items: flat list, each {pulled_at, lane, source, title, link,
      player, team, statsapi_transaction_id (CONFIRMED only),
      source_pubdate, move_type (CONFIRMED only)}

Lanes (the integrity rule is structural):
  SIGNED   — CONFIRMED moves only: MLB StatsAPI transactions, FA
             codes SFA / DFA / TR / REL / CLW / OUT / DES. DFA in
             StatsAPI codes means DECLARED free agency, so a DFA item
             is titled as a declaration, never as a signing; the
             per-item move_type carries the exact code.
  REPORTED — newswire/rumor: MLB Trade Rumors RSS (main + capped
             per-team + capped per-player feeds), MLB.com per-team
             RSS (capped), ESPN news + transactions (unofficial
             public endpoints, cross-check), Google News RSS
             (generic query + capped per-player queries), RotoWire
             RSS (free tier = 5 items). REPORTED items are deduped
             on title+source; Google News links are redirects, so
             dedupe never uses the redirect URL.
  BUZZ     — Bluesky Jetstream ONLY, and only if a real stream read
             succeeds in this runtime. If the stream read fails, the
             lane ships EMPTY with the reason on record. Never fake
             buzz items; never substitute AppView search (403),
             Reddit (403), or Mastodon (0 signal) — all dropped.

Caps (recorded in the artifact, so a build stays cheap):
  Google News per-player queries: top 12 by Steamer WAR.
  MLBTR / MLB.com per-team feeds: top 6 teams by class count.
  MLBTR per-player feeds: top 12 by Steamer WAR.
  Stored REPORTED items: newest 200 by pubdate. BUZZ: newest 10.

OFFLINE SAFETY: the data gate never calls this script; it verifies
the committed artifact only.
"""
import base64
import html as htmlmod
import json
import os
import re
import socket
import ssl
import struct
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "tracker_ticker_2026.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; HARDBALL-tracker/1.0)"}
SLEEP = 0.4
TIMEOUT = 20

FA_CODES = ("SFA", "DFA", "TR", "REL", "CLW", "OUT", "DES")
FA_CODE_LABEL = {
    "SFA": "Signed free agent",
    "DFA": "Declared free agency",
    "TR": "Traded",
    "REL": "Released",
    "CLW": "Cleared waivers",
    "OUT": "Outrighted",
    "DES": "Designated for assignment",
}
FA_RE = re.compile(
    r"\b(free agent|free-agent|sign|signed|signing|signs|contract|"
    r"extension|trade|traded|option|qualifying offer|tender|non-tender|"
    r"designat\w*|dfa|releas\w*|claim\w*|waiver\w*|agree\w*|deal|"
    r"interest\w*|reportedly|rumor\w*|pursu\w*|checked in)\b",
    re.IGNORECASE)

# Team maps (abbr -> nickname fragment used to verify a feed is really
# that team's feed; MLBTR slug; MLB.com slug). Only the top teams by
# class count are pulled per build; the full map keeps the choice
# data-driven instead of hardcoded.
NICK = {
    "ARI": "Diamondbacks", "ATL": "Braves", "BAL": "Orioles",
    "BOS": "Red Sox", "CHC": "Cubs", "CHW": "White Sox",
    "CIN": "Reds", "CLE": "Guardians", "COL": "Rockies",
    "DET": "Tigers", "HOU": "Astros", "KC": "Royals",
    "LAA": "Angels", "LAD": "Dodgers", "MIA": "Marlins",
    "MIL": "Brewers", "MIN": "Twins", "NYM": "Mets",
    "NYY": "Yankees", "ATH": "Athletics", "PHI": "Phillies",
    "PIT": "Pirates", "SD": "Padres", "SF": "Giants",
    "SEA": "Mariners", "STL": "Cardinals", "TB": "Rays",
    "TEX": "Rangers", "TOR": "Blue Jays", "WSH": "Nationals",
}
MLBTR_SLUG = {
    "ARI": "arizona-diamondbacks", "ATL": "atlanta-braves",
    "BAL": "baltimore-orioles", "BOS": "boston-red-sox",
    "CHC": "chicago-cubs", "CHW": "chicago-white-sox",
    "CIN": "cincinnati-reds", "CLE": "cleveland-guardians",
    "COL": "colorado-rockies", "DET": "detroit-tigers",
    "HOU": "houston-astros", "KC": "kansas-city-royals",
    "LAA": "los-angeles-angels", "LAD": "los-angeles-dodgers",
    "MIA": "miami-marlins", "MIL": "milwaukee-brewers",
    "MIN": "minnesota-twins", "NYM": "new-york-mets",
    "NYY": "new-york-yankees", "ATH": "athletics",
    "PHI": "philadelphia-phillies", "PIT": "pittsburgh-pirates",
    "SD": "san-diego-padres", "SF": "san-francisco-giants",
    "SEA": "seattle-mariners", "STL": "st-louis-cardinals",
    "TB": "tampa-bay-rays", "TEX": "texas-rangers",
    "TOR": "toronto-blue-jays", "WSH": "washington-nationals",
}
MLBCOM_SLUG = {
    "ARI": "dbacks", "ATL": "braves", "BAL": "orioles",
    "BOS": "redsox", "CHC": "cubs", "CHW": "whitesox",
    "CIN": "reds", "CLE": "guardians", "COL": "rockies",
    "DET": "tigers", "HOU": "astros", "KC": "royals",
    "LAA": "angels", "LAD": "dodgers", "MIA": "marlins",
    "MIL": "brewers", "MIN": "twins", "NYM": "mets",
    "NYY": "yankees", "ATH": "athletics", "PHI": "phillies",
    "PIT": "pirates", "SD": "padres", "SF": "giants",
    "SEA": "mariners", "STL": "cardinals", "TB": "rays",
    "TEX": "rangers", "TOR": "bluejays", "WSH": "nationals",
}

CAP_PLAYERS = 12
CAP_TEAMS = 6
CAP_REPORTED_STORED = 200
CAP_BUZZ_STORED = 10


def fetch(url):
    """Returns (status, bytes) — 403/429 are data, not exceptions."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # timeout, DNS, reset: source skipped
        return 0, str(e).encode()


def get_json(url):
    status, raw = fetch(url)
    if status != 200:
        return status, None
    try:
        return status, json.loads(raw.decode(errors="replace"))
    except Exception:
        return 0, None


def parse_rss(raw):
    """Returns (channel_title, [(title, link, pubdate_iso_or_raw)]) or None."""
    try:
        root = ET.fromstring(raw)
    except Exception:
        return None
    chan = root.find("channel")
    if chan is None:
        return None
    title_el = chan.find("title")
    chan_title = (title_el.text or "") if title_el is not None else ""
    items = []
    for it in chan.findall("item"):
        t = it.find("title")
        l = it.find("link")
        p = it.find("pubDate")
        title = htmlmod.unescape((t.text or "").strip()) if t is not None else ""
        link = (l.text or "").strip() if l is not None else ""
        pub = (p.text or "").strip() if p is not None else ""
        iso = ""
        if pub:
            try:
                iso = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
            except Exception:
                iso = pub
        if title:
            items.append((title, link, iso))
    return chan_title, items


def fa_relevant(text):
    return bool(FA_RE.search(text or ""))


def slugify(name):
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s


def jetstream_read(window_s=20, max_events=300):
    """One real stream read, stdlib only. Returns (status, events, items).

    status: 'stream_ok' | 'stream_failed'. items are BUZZ items only
    when a post matches the FA keywords and names a class player.
    Proxy credentials are used, never printed.
    """
    host = "jetstream2.us-west.bsky.network"
    path = "/subscribe?wantedCollections=app.bsky.feed.post"
    keywords = ("free agent", "free-agent", "signing", "signed",
                "agrees", "trade", "contract")
    proxy = None
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if os.environ.get(var):
            proxy = urlparse(os.environ[var])
            break
    if not proxy:
        return "stream_failed", 0, [], "no egress proxy configured"

    def read_http_headers(f):
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = f.read(1)
            if not chunk:
                break
            buf += chunk
        return buf.decode(errors="replace")

    def read_frame(sock, deadline):
        def recvn(n):
            data = b""
            while len(data) < n:
                if time.time() > deadline:
                    raise TimeoutError("frame deadline")
                chunk = sock.recv(n - len(data))
                if not chunk:
                    raise ConnectionError("stream closed")
                data += chunk
            return data
        h = recvn(2)
        opcode = h[0] & 0x0F
        ln = h[1] & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", recvn(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", recvn(8))[0]
        if h[1] & 0x80:
            mask = recvn(4)
            payload = bytearray(recvn(ln))
            for i in range(len(payload)):
                payload[i] ^= mask[i % 4]
            payload = bytes(payload)
        else:
            payload = recvn(ln)
        return opcode, payload

    try:
        raw = socket.create_connection((proxy.hostname, proxy.port), timeout=15)
        raw.settimeout(20)
        f = raw.makefile("rwb", buffering=0)
        auth = ""
        if proxy.username:
            token = base64.b64encode(
                f"{proxy.username}:{proxy.password or ''}".encode()).decode()
            auth = f"Proxy-Authorization: Basic {token}\r\n"
        f.write(f"CONNECT {host}:443 HTTP/1.1\r\nHost: {host}:443\r\n"
                f"{auth}Connection: close\r\n\r\n".encode())
        resp = read_http_headers(f)
        if " 200 " not in resp:
            return "stream_failed", 0, [], f"CONNECT: {resp.splitlines()[0] if resp else 'empty'}"
        ctx = ssl.create_default_context()
        tls = ctx.wrap_socket(raw, server_hostname=host)
        key = base64.b64encode(os.urandom(16)).decode()
        tls.sendall(
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n".encode())
        buf = b""
        tls.settimeout(15)
        while b"\r\n\r\n" not in buf:
            chunk = tls.recv(4096)
            if not chunk:
                break
            buf += chunk
        hs = buf.decode(errors="replace")
        if " 101 " not in hs:
            return "stream_failed", 0, [], f"handshake: {hs.splitlines()[0] if hs else 'empty'}"
        deadline = time.time() + window_s
        events, matches = 0, []
        tls.settimeout(max(1, int(deadline - time.time())))
        while time.time() < deadline and events < max_events:
            opcode, payload = read_frame(tls, deadline)
            if opcode == 9:
                tls.sendall(b"\x8a\x00")
                continue
            if opcode == 8:
                break
            if opcode != 1:
                continue
            try:
                ev = json.loads(payload.decode())
            except Exception:
                continue
            events += 1
            commit = ev.get("commit", {}) if isinstance(ev, dict) else {}
            rec = commit.get("record", {}) if isinstance(commit, dict) else {}
            text = rec.get("text", "") if isinstance(rec, dict) else ""
            if not text or not any(k in text.lower() for k in keywords):
                continue
            uri = commit.get("uri", "") if isinstance(commit, dict) else ""
            link = ""
            m = re.match(r"at://([^/]+)/app\.bsky\.feed\.post/(.+)$", uri)
            if m:
                link = f"https://bsky.app/profile/{m.group(1)}/post/{m.group(2)}"
            matches.append({"title": text[:280], "link": link,
                            "author_did": commit.get("repo", "")})
        return "stream_ok", events, matches, ""
    except Exception as e:
        return "stream_failed", 0, [], f"{type(e).__name__}: {e}"


def main():
    now = datetime.now(timezone.utc)
    pulled_at = now.isoformat()
    today = now.date()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()

    fa = json.loads((DATA / "fa_shopping_2027.json").read_text())
    cls = fa["class"]
    by_war = sorted([r for r in cls if r.get("steamer_war") is not None],
                    key=lambda r: -r["steamer_war"])
    top_players = by_war[:CAP_PLAYERS]
    from collections import Counter
    team_counts = Counter(r.get("prev_team") for r in cls)
    top_teams = [t for t, _ in team_counts.most_common(CAP_TEAMS)]

    per_source = []

    def record(source, status, fetched, kept, note=""):
        per_source.append({"source": source, "status": status,
                           "fetched": fetched, "kept": kept, "note": note})
        time.sleep(SLEEP)

    signed, reported = [], []

    # --- CONFIRMED: StatsAPI transactions, FA codes only -----------
    status, txj = get_json(
        "https://statsapi.mlb.com/api/v1/transactions"
        f"?startDate={start}&endDate={end}")
    if status == 200 and txj is not None:
        kept = 0
        skipped_empty = 0
        for t in txj.get("transactions", []):
            code = t.get("typeCode")
            if code not in FA_CODES:
                continue
            # A row with no description and no player name carries
            # nothing readable to display; skip it and count it
            # rather than rendering an empty bullet.
            if not (t.get("description") or "").strip() \
                    and not ((t.get("person") or {}).get("fullName")):
                skipped_empty += 1
                continue
            person = t.get("person") or {}
            to_team = t.get("toTeam") or {}
            signed.append({
                "pulled_at": pulled_at, "lane": "SIGNED",
                "source": "MLB StatsAPI transactions",
                "title": t.get("description", ""),
                "link": "",
                "player": person.get("fullName", ""),
                "team": to_team.get("name", ""),
                "statsapi_transaction_id": t.get("id"),
                "source_pubdate": t.get("date", ""),
                "move_type": f"{code} — {FA_CODE_LABEL.get(code, t.get('typeDesc', ''))}",
            })
            kept += 1
        signed.sort(key=lambda i: i["source_pubdate"], reverse=True)
        record("MLB StatsAPI transactions", "ok",
               len(txj.get("transactions", [])), kept,
               f"window {start}..{end}, FA codes {','.join(FA_CODES)}; "
               f"{skipped_empty} FA-code row(s) skipped with no "
               f"description and no player name")
    else:
        record("MLB StatsAPI transactions",
               "blocked" if status in (403, 429) else "error",
               0, 0, f"HTTP {status}")

    # --- Class register (state table, not ticker items) ------------
    status, faj = get_json(
        "https://statsapi.mlb.com/api/v1/people/freeAgents?season=2026")
    register_count = 0
    if status == 200 and faj is not None:
        register_count = len(faj.get("freeAgents", []))
        record("MLB StatsAPI freeAgents?season=2026", "ok",
               register_count, 0, "class register only; moves come "
               "from transactions, never from the register")
    else:
        record("MLB StatsAPI freeAgents?season=2026",
               "blocked" if status in (403, 429) else "error",
               0, 0, f"HTTP {status}")

    seen_reported = set()

    def add_reported(source, title, link, pub, player="", team=""):
        key = (title.strip().lower(), source)
        if key in seen_reported:
            return False
        seen_reported.add(key)
        reported.append({
            "pulled_at": pulled_at, "lane": "REPORTED", "source": source,
            "title": title, "link": link, "player": player, "team": team,
            "statsapi_transaction_id": None, "source_pubdate": pub,
        })
        return True

    # --- REPORTED: ESPN news (unofficial public endpoint) -----------
    status, ej = get_json(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news")
    if status == 200 and ej is not None:
        kept = 0
        for a in ej.get("articles", []):
            head = a.get("headline", "")
            desc = ""
            if isinstance(a.get("description"), str):
                desc = a["description"]
            if not fa_relevant(head + " " + desc):
                continue
            links = a.get("links", {}) or {}
            web = links.get("web", {}) or {}
            href = web.get("href", "") if isinstance(web, dict) else ""
            if add_reported("ESPN news", head, href, a.get("published", "")):
                kept += 1
        record("ESPN news", "ok", len(ej.get("articles", [])), kept,
               "unofficial public endpoint; FA-keyword filtered")
    else:
        record("ESPN news", "blocked" if status in (403, 429) else "error",
               0, 0, f"HTTP {status}")

    # --- REPORTED: ESPN transactions, page 1 (cross-check) ---------
    status, et = get_json(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/transactions")
    if status == 200 and et is not None:
        kept = 0
        for t in et.get("transactions", []):
            desc = t.get("description", "")
            team = t.get("team") or {}
            team_name = team.get("displayName", "") if isinstance(team, dict) else ""
            if add_reported("ESPN transactions", desc, "",
                             t.get("date", ""), "", team_name):
                kept += 1
        record("ESPN transactions", "ok", len(et.get("transactions", [])),
               kept, "unofficial public endpoint, page 1 of "
               f"{et.get('pageCount', '?')} (cross-check only)")
    else:
        record("ESPN transactions",
               "blocked" if status in (403, 429) else "error",
               0, 0, f"HTTP {status}")

    # --- REPORTED: MLB Trade Rumors, main + capped team/player -----
    def pull_rss(url, source, team="", player="", require_fragment="",
                 keyword_filter=True):
        status, raw = fetch(url)
        if status != 200:
            record(source, "blocked" if status in (403, 429) else "error",
                   0, 0, f"HTTP {status}")
            return
        parsed = parse_rss(raw)
        if parsed is None:
            record(source, "error", 0, 0, "unparseable RSS")
            return
        chan_title, items = parsed
        if require_fragment and require_fragment.lower() not in chan_title.lower():
            record(source, "error", 0, 0,
                   f"channel title mismatch: {chan_title[:80]!r}")
            return
        kept = 0
        for title, link, pub in items:
            if keyword_filter and not fa_relevant(title):
                continue
            if add_reported(source, title, link, pub, player, team):
                kept += 1
        record(source, "ok", len(items), kept, "")

    pull_rss("https://www.mlbtraderumors.com/feed", "MLB Trade Rumors (main)")
    for abbr in top_teams:
        pull_rss(f"https://www.mlbtraderumors.com/{MLBTR_SLUG[abbr]}/feed",
                 f"MLB Trade Rumors ({abbr})", team=NICK[abbr],
                 require_fragment=NICK[abbr])
    for p in top_players:
        slug = slugify(p["name"])
        last = p["name"].split()[-1]
        pull_rss(f"https://www.mlbtraderumors.com/players/{slug}/feed",
                 f"MLB Trade Rumors ({p['name']})", player=p["name"],
                 require_fragment=last, keyword_filter=False)

    # --- REPORTED: MLB.com per-team news RSS (capped) ---------------
    # MLB.com's Arizona feed titles itself "D-backs News", not
    # "Diamondbacks" — the fragment map carries that exception.
    mlbcom_fragment = dict(NICK)
    mlbcom_fragment["ARI"] = "D-backs"
    for abbr in top_teams:
        pull_rss(f"https://www.mlb.com/{MLBCOM_SLUG[abbr]}/feeds/news/rss.xml",
                 f"MLB.com ({abbr})", team=NICK[abbr],
                 require_fragment=mlbcom_fragment[abbr])

    # --- REPORTED: RotoWire (free tier = 5 items) -------------------
    pull_rss("https://www.rotowire.com/rss/news.php?sport=MLB",
             "RotoWire")

    # --- REPORTED: Google News RSS (generic + capped per-player) ---
    def pull_gnews(query, source, player=""):
        from urllib.parse import quote
        url = ("https://news.google.com/rss/search?q="
               f"{quote(query)}&hl=en-US&gl=US&ceid=US:en")
        status, raw = fetch(url)
        if status != 200:
            record(source, "blocked" if status in (403, 429) else "error",
                   0, 0, f"HTTP {status}")
            return
        parsed = parse_rss(raw)
        if parsed is None:
            record(source, "error", 0, 0, "unparseable RSS")
            return
        _, items = parsed
        kept = 0
        for title, link, pub in items:
            if add_reported(source, title, link, pub, player):
                kept += 1
        record(source, "ok", len(items), kept,
               "links are Google redirects; deduped on title+source")

    pull_gnews("MLB free agency when:1d", "Google News (MLB free agency)")
    for p in top_players:
        pull_gnews(f"{p['name']} MLB free agency when:3d",
                   f"Google News ({p['name']})", player=p["name"])

    # --- BUZZ: Bluesky Jetstream only ------------------------------
    js_status, js_events, js_matches, js_err = jetstream_read()
    buzz = []
    if js_status == "stream_ok":
        last_names = {p["name"].split()[-1].lower(): p["name"]
                      for p in top_players}
        for m in js_matches:
            text = m["title"]
            low = text.lower()
            named = [full for last, full in last_names.items()
                     if last in low]
            if "free agent" not in low and "free-agent" not in low and not named:
                continue
            buzz.append({
                "pulled_at": pulled_at, "lane": "BUZZ",
                "source": "Bluesky Jetstream",
                "title": text, "link": m["link"],
                "player": named[0] if named else "",
                "team": "", "statsapi_transaction_id": None,
                "source_pubdate": pulled_at,
            })
        buzz = buzz[:CAP_BUZZ_STORED]
    record("Bluesky Jetstream",
           "ok" if js_status == "stream_ok" else "stream_failed",
           js_events, len(buzz), js_err)

    reported.sort(key=lambda i: i["source_pubdate"], reverse=True)
    reported = reported[:CAP_REPORTED_STORED]
    items = signed + reported + buzz

    artifact = {
        "metadata": {
            "pulled_at": pulled_at,
            "window": {"transactions_start": start, "transactions_end": end},
            "caps": {
                "google_news_players": CAP_PLAYERS,
                "mlbtr_teams": CAP_TEAMS,
                "mlbcom_teams": CAP_TEAMS,
                "mlbtr_players": CAP_PLAYERS,
                "reported_stored": CAP_REPORTED_STORED,
                "buzz_stored": CAP_BUZZ_STORED,
            },
            "top_players_by_steamer_war": [p["name"] for p in top_players],
            "top_teams_by_class_count": top_teams,
            "class_register": {"source": "MLB StatsAPI freeAgents?season=2026",
                               "count": register_count},
            "jetstream": {"status": js_status, "events_seen": js_events,
                          "error": js_err},
            "per_source": per_source,
            "counts": {"signed": len(signed), "reported": len(reported),
                       "buzz": len(buzz), "total": len(items)},
            "integrity": ("Items promote to SIGNED only when the MLB "
                          "StatsAPI transactions feed carries them. "
                          "REPORTED and BUZZ items are never labeled "
                          "signings."),
        },
        "items": items,
    }
    OUT.write_text(json.dumps(artifact, indent=1))
    c = artifact["metadata"]["counts"]
    print(f"TICKER OK: signed={c['signed']} reported={c['reported']} "
          f"buzz={c['buzz']} total={c['total']} "
          f"jetstream={js_status} ({js_events} events)")
    for s in per_source:
        print(f"  {s['source']}: {s['status']} fetched={s['fetched']} "
              f"kept={s['kept']} {s['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
