#!/usr/bin/env python3
"""Cycle 51 (API-1) — wire Statyx + FastballAPI into the platform.

Until this cycle the two keyed feeds were CONNECTED + VERIFIED LIVE
(Cycle 45) but served nothing: no figure or model read from them.
This cycle lands dated raw snapshots of both feeds, curates them
into fact_il_current (src/curate.py), and gives the layer a real
consumer — the dashboard health panel's live-IL sub-panel, rendered
from data/il_current_live.json (this script's artifact).

Modes:
  --pull   Call the Secure Vault connector helpers on this machine
           (~/workspace/custom-connectors/custom.statyx/bin/statyx_get.py,
           .../custom.fastballapi/bin/fastball_post.py) ONCE per
           endpoint, land immutable raw snapshots under data/raw/
           (platform convention: data/raw/<source>/<dataset>.json +
           append-only data/raw/manifest.jsonl entries carrying
           sha256/rows/status), then build the artifact.
           FastballAPI credit budget: standings + injuries = 2 calls
           x 2 credits = 4 of 500 free monthly credits. Statyx: free.
  (none)   Offline build: read the committed raw snapshots and
           rebuild data/il_current_live.json deterministically.
           This is the path the gate uses — no keys, no network.

Keys NEVER appear here: the helpers inject the vault credential
themselves. If a helper fails, --pull fails closed and writes
nothing feed-dependent.

Reconciliation (all published in the artifact):
  * feed overlap (FastballAPI full IL list vs Statyx recent-moves
    page) by normalized player name;
  * the 2027 FA pool (data/fa_shopping_2027.json) matched against
    the live union — the availability-relevant set — with each
    matched player's static-file picture (fact_il_stints, The
    Injury Report) compared: a player the live feeds list as
    currently injured whose 2026 static stints all closed (or who
    has no 2026 stint) is flagged `differs`;
  * FastballAPI 2026 standings vs the committed kpi_2026.json
    (wins + runs scored, 30 teams).
"""
import hashlib
import importlib.util
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PULLED_DATE = "2026-11-02"

STATYX_HELPER = Path.home() / "workspace/custom-connectors/custom.statyx/bin/statyx_get.py"
FASTBALL_HELPER = Path.home() / "workspace/custom-connectors/custom.fastballapi/bin/fastball_post.py"

SNAPSHOTS = [  # (source dir, dataset stem)
    ("statyx", f"injuries_{PULLED_DATE}"),
    ("statyx", f"standings_{PULLED_DATE}"),
    ("fastballapi", f"injuries_{PULLED_DATE}"),
    ("fastballapi", f"standings_{PULLED_DATE}"),
]


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _load_helper(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def land(source, dataset, body, rows, endpoint):
    """Write one raw snapshot envelope + manifest entry (platform style)."""
    payload = json.dumps(body, indent=1, sort_keys=True).encode()
    envelope = {"source": source, "dataset": dataset, "endpoint": endpoint,
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "rows": rows, "sha256": hashlib.sha256(payload).hexdigest(),
                "payload": body}
    content = json.dumps(envelope, indent=1).encode()
    d = RAW / source
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{dataset}.tmp"
    tmp.write_bytes(content)
    tmp.replace(d / f"{dataset}.json")
    entry = {"source": source, "dataset": dataset,
             "fetched_at": envelope["fetched_at"], "sha256": sha16(content),
             "bytes": len(content), "rows": rows, "status": "ok"}
    with open(RAW / "manifest.jsonl", "a") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"  landed raw/{source}/{dataset}.json ({rows} rows)")
    return envelope


def pull():
    sg = _load_helper(STATYX_HELPER, "statyx_get")
    fp = _load_helper(FASTBALL_HELPER, "fastball_post")
    calls = []
    status, body = sg.get("/v1/mlb/injuries")
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: statyx injuries HTTP {status}")
    calls.append(land("statyx", f"injuries_{PULLED_DATE}", body,
                      len(body["data"]), "GET /v1/mlb/injuries"))
    status, body = sg.get("/v1/mlb/standings")
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: statyx standings HTTP {status}")
    calls.append(land("statyx", f"standings_{PULLED_DATE}", body,
                      len(body["data"]), "GET /v1/mlb/standings"))
    status, body = fp.post("get_injuries", {})
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: fastball get_injuries HTTP {status}")
    calls.append(land("fastballapi", f"injuries_{PULLED_DATE}", body,
                      len(body["data"]["injuries"]), "POST /v1/get_injuries"))
    status, body = fp.post("get_standings", {"season": 2026})
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: fastball get_standings HTTP {status}")
    calls.append(land("fastballapi", f"standings_{PULLED_DATE}", body,
                      len(body["data"]["standings"]), "POST /v1/get_standings"))
    print("PULL: 4 endpoints, all HTTP 200; FastballAPI credits spent: 4")
    return calls


def norm_name(name):
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace(".", " ").replace("'", "")
    parts = [p for p in s.split() if p not in ("jr", "sr", "ii", "iii", "iv")]
    return " ".join(parts)


def read_snapshot(source, dataset):
    p = RAW / source / f"{dataset}.json"
    env = json.loads(p.read_text())
    payload = env["payload"]
    digest = hashlib.sha256(
        json.dumps(payload, indent=1, sort_keys=True).encode()).hexdigest()
    assert digest == env["sha256"], f"sha mismatch on {p} — snapshot tampered"
    return env


def build():
    envs = {(s, d): read_snapshot(s, d) for s, d in SNAPSHOTS}
    fb_inj = envs[("fastballapi", f"injuries_{PULLED_DATE}")]["payload"]["data"]
    fb_std = envs[("fastballapi", f"standings_{PULLED_DATE}")]["payload"]["data"]
    sx_inj = envs[("statyx", f"injuries_{PULLED_DATE}")]["payload"]["data"]
    sx_std = envs[("statyx", f"standings_{PULLED_DATE}")]["payload"]["data"]
    pulled_at = max(e["fetched_at"] for e in envs.values())

    # --- union of the two injury feeds, one row per player ---------------
    rows = {}
    for r in fb_inj["injuries"]:
        rows[norm_name(r["name"])] = {
            "player_name": r["name"], "team": r.get("team"),
            "position": r.get("position"), "status": r.get("status"),
            "statyx_status": None, "type": r.get("type"),
            "detail": r.get("detail"), "side": None,
            "return_date": (r.get("return_date") or "")[:10] or None,
            "in_fastball": True, "in_statyx": False, "pulled_at": PULLED_DATE}
    n_overlap = 0
    for r in sx_inj:
        k = norm_name(r["player_name"])
        if k in rows:
            n_overlap += 1
            row = rows[k]
            row["in_statyx"] = True
            if r.get("status") and r["status"] != row["status"]:
                row["statyx_status"] = r["status"]
            row["side"] = r.get("side") or row["side"]
            if not row["detail"]:
                row["detail"] = r.get("detail")
        else:
            rows[k] = {
                "player_name": r["player_name"], "team": None,
                "position": None, "status": r.get("status"),
                "statyx_status": None, "type": r.get("type"),
                "detail": r.get("detail"), "side": r.get("side"),
                "return_date": (r.get("return_date") or "")[:10] or None,
                "in_fastball": False, "in_statyx": True,
                "pulled_at": PULLED_DATE}
    union = sorted(rows.values(), key=lambda r: r["player_name"])

    # --- FA pool overlay + static-file comparison -------------------------
    fa = json.loads((DATA / "fa_shopping_2027.json").read_text())["class"]
    fa_by_norm = {norm_name(p["name"]): p for p in fa}
    stints = pd.read_parquet(DATA / "curated" / "fact_il_stints.parquet")
    st26 = stints[stints["season"] == 2026]
    overlay = []
    for row in union:
        p = fa_by_norm.get(norm_name(row["player_name"]))
        if p is None:
            continue
        mine = st26[st26["player_id"] == p["player_id"]]
        if len(mine) == 0:
            static, differs = "no 2026 IL stint in The Injury Report file", True
        elif bool(mine["on_il_at_season_end"].any()):
            static, differs = "on IL at 2026 season end (static file agrees)", False
        else:
            static, differs = ("2026 IL stint(s) in static file, all closed "
                               "before season end", True)
        overlay.append({
            "name": p["name"], "player_id": int(p["player_id"]),
            "pos": p.get("pos"), "prev_team": p.get("prev_team"),
            "team": row["team"], "status": row["status"],
            "statyx_status": row["statyx_status"], "type": row["type"],
            "detail": row["detail"], "return_date": row["return_date"],
            "feeds": [f for f, on in (("fastballapi", row["in_fastball"]),
                                      ("statyx", row["in_statyx"])) if on],
            "static_picture": static, "differs_from_static": differs})
    overlay.sort(key=lambda r: r["name"])
    n_differs = sum(1 for r in overlay if r["differs_from_static"])

    # --- standings cross-check: FastballAPI vs committed kpi_2026 ---------
    kpi = {r["team"]: r for r in json.loads((DATA / "kpi_2026.json").read_text())}
    mism = []
    for r in fb_std["standings"]:
        k = kpi.get(r["abbrev"])
        if k is None or int(k["wins"]) != r["wins"] or int(k["R"]) != r["runs_scored"]:
            mism.append({"team": r["abbrev"],
                         "fastball_wins": r["wins"], "kpi_wins": None if k is None else int(k["wins"]),
                         "fastball_runs": r["runs_scored"], "kpi_runs": None if k is None else int(k["R"])})
    standings_check = {"teams_compared": len(fb_std["standings"]),
                       "wins_and_runs_agree": len(fb_std["standings"]) - len(mism),
                       "mismatches": mism}

    artifact = {
        "metadata": {
            "cycle": 51, "pulled_at": pulled_at, "pulled_date": PULLED_DATE,
            "sources": {
                "fastballapi": {"injuries_records": len(fb_inj["injuries"]),
                                "standings_teams": len(fb_std["standings"]),
                                "credits_spent_this_cycle": 4,
                                "snapshot_files": [f"data/raw/fastballapi/injuries_{PULLED_DATE}.json",
                                                   f"data/raw/fastballapi/standings_{PULLED_DATE}.json"]},
                "statyx": {"injuries_records": len(sx_inj),
                           "standings_rows": len(sx_std),
                           "note": "injuries = first page (limit 50) of the recent-moves feed; "
                                   "standings rows carry no team names, snapshot kept raw only",
                           "credits_spent_this_cycle": 0,
                           "snapshot_files": [f"data/raw/statyx/injuries_{PULLED_DATE}.json",
                                              f"data/raw/statyx/standings_{PULLED_DATE}.json"]}},
            "grain": "one row per currently listed injured player (union of the two feeds)",
            "consumer": "dashboard health panel live-IL sub-panel + curated fact_il_current"},
        "rows": union,
        "fa_overlay": {"fa_pool_size": len(fa), "n_matched": len(overlay),
                       "n_differs_from_static": n_differs, "players": overlay},
        "reconciliation": {
            "fastball_injuries": len(fb_inj["injuries"]),
            "statyx_injuries_page": len(sx_inj),
            "overlap_both_feeds": n_overlap,
            "union_players": len(union),
            "standings_check_fastball_vs_kpi_2026": standings_check}}
    out = DATA / "il_current_live.json"
    out.write_text(json.dumps(artifact, indent=1))
    print(f"ARTIFACT: {out.name} — union {len(union)} players "
          f"(fastball {len(fb_inj['injuries'])}, statyx page {len(sx_inj)}, "
          f"overlap {n_overlap}); FA overlay {len(overlay)}/{len(fa)} "
          f"({n_differs} differ from static file); standings agree "
          f"{standings_check['wins_and_runs_agree']}/{standings_check['teams_compared']}")
    return artifact


if __name__ == "__main__":
    if "--pull" in sys.argv:
        pull()
    build()
