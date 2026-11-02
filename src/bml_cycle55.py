#!/usr/bin/env python3
"""Cycle 55 — feed architecture: census / event / validator.

Division of labor (docs/DATA_PLATFORM.md, "Feed architecture"):
- FastballAPI = CENSUS: the canonical current-IL snapshot.
- Statyx = EVENT layer: its recent-moves injuries page is diffed
  against the census baseline for movement (new IL / returned /
  status change).
- MLB Stats API remains the standings of record; FastballAPI
  standings act as validator only (Cycle 51: 30/30 agreement).
- Statyx standings were TESTED this cycle and DROPPED as a source:
  the payload's only identifier is a Statyx-internal team_id with no
  mapping to MLB teams anywhere in the repo, and it covers 25 of 30
  teams per season. The snapshot stays raw-only; the verdict and
  evidence are recorded in data/il_events.json metadata.

Default mode is an OFFLINE build from committed snapshots: it diffs
the baseline pair (Cycle 51, pulled 2026-11-02) against the newest
landed pair and writes data/il_events.json. `--pull` fetches one call
per endpoint through the vault helpers and lands whatever changed as
a new dated snapshot (state-aware dedupe: a payload that differs
only in volatile fields — Statyx stamps every record's updated_at at
page-generation time — is recorded as ok_no_change and not
re-landed). Keys never touch this repo.

The published event view (fa_pool_events) is restricted to the FA
pool (251) plus scenario-roster players; the artifact stores the
full diff as well.
"""
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"

STATYX_HELPER = Path.home() / "workspace/custom-connectors/custom.statyx/bin/statyx_get.py"
FASTBALL_HELPER = Path.home() / "workspace/custom-connectors/custom.fastballapi/bin/fastball_post.py"

BASELINE_DATE = "2026-11-02"  # Cycle 51 pull = the standing baseline
PULLS = [("fastballapi", "injuries"), ("fastballapi", "standings"),
         ("statyx", "injuries"), ("statyx", "standings")]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bml_cycle51 import newest_stem, norm_name  # noqa: E402


def payload_sha(body) -> str:
    return hashlib.sha256(json.dumps(body, indent=1,
                                     sort_keys=True).encode()).hexdigest()


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


# Fields that change without any underlying state change. Statyx
# stamps updated_at on every record of its injuries page at page
# generation time (verified Cycle 55: a same-day re-pull re-stamped
# all 50 records with zero status/type/detail changes), so the field
# carries no event information; the record's `date` field is the
# stable per-record timestamp.
VOLATILE_FIELDS = {("statyx", "injuries"): ("updated_at",)}


def state_sha(source, kind, body) -> str:
    """Payload sha with volatile fields stripped — 'did the feed
    state change', as opposed to 'did the bytes change'."""
    drop = VOLATILE_FIELDS.get((source, kind))
    if not drop or not isinstance(body, dict) \
            or not isinstance(body.get("data"), list):
        return payload_sha(body)
    stripped = [{k: v for k, v in r.items() if k not in drop}
                for r in body["data"]]
    return payload_sha({**body, "data": stripped})


def load_envelope(path: Path) -> dict:
    env = json.loads(path.read_text())
    assert payload_sha(env["payload"]) == env["sha256"], \
        f"sha mismatch on {path} — snapshot tampered"
    return env


def baseline_snapshot(source: str, kind: str) -> Path:
    p = RAW / source / f"{kind}_{BASELINE_DATE}.json"
    if not p.exists():
        raise SystemExit(f"baseline snapshot missing: {p}")
    return p


def current_snapshot(source: str, kind: str) -> Path:
    return RAW / source / (newest_stem(source, kind) + ".json")


def envelope_ref(path: Path) -> dict:
    env = load_envelope(path)
    return {"file": str(path.relative_to(ROOT)),
            "fetched_at": env["fetched_at"],
            "payload_sha256": payload_sha(env["payload"])}


def rows_of(env: dict, source: str, kind: str):
    body = env["payload"]
    if source == "statyx":
        return body["data"]
    if kind == "injuries":
        return body["data"]["injuries"]
    return body["data"]["standings"]


# ---------------------------------------------------------------------
# Statyx standings test: can the payload join the platform?
# ---------------------------------------------------------------------
def standings_test() -> dict:
    env = load_envelope(baseline_snapshot("statyx", "standings"))
    rows = rows_of(env, "statyx", "standings")
    fields = set()
    for r in rows:
        fields.update(r.keys())
    seasons = sorted({r.get("season") for r in rows})
    per_season = {s: len([r for r in rows if r.get("season") == s])
                  for s in seasons}
    team_ids = {r.get("team_id") for r in rows}
    id_like = sorted(f for f in fields
                     if f == "team_id" or f.endswith(("_id", "_code"))
                     or f in ("team", "team_name", "name",
                              "abbreviation"))
    return {
        "verdict": "dropped",
        "reason": ("Statyx standings carries no joinable team "
                   "identifier: the only identifier field is "
                   "'team_id' (Statyx-internal values "
                   f"{min(team_ids)}..{max(team_ids)}), there are no "
                   "team name/abbreviation/code fields, and no "
                   "crosswalk from Statyx team_id to MLB teams "
                   "exists in the repo (the Chadwick register is "
                   "player-level; dim_team keys on StatsAPI "
                   "IDs/abbreviations). Coverage is also partial: "
                   f"{per_season} rows per season vs 30 platform "
                   "teams. The snapshot stays raw-only; nothing "
                   "curates from it."),
        "evidence": {
            "rows": len(rows),
            "seasons": seasons,
            "rows_per_season": {str(k): v
                                for k, v in per_season.items()},
            "distinct_team_ids": len(team_ids),
            "identifier_fields_present": id_like,
            "all_fields": sorted(fields),
        },
        "disposition": "raw snapshot retained for provenance; "
                       "standings of record remain MLB Stats API "
                       "with FastballAPI as validator (Cycle 51).",
    }


# ---------------------------------------------------------------------
# Event layer: census baseline vs current, per player state
# ---------------------------------------------------------------------
def player_state(env_sx, env_fb) -> dict:
    """norm_name -> merged IL state across the two feeds."""
    state = {}
    for r in rows_of(env_fb, "fastballapi", "injuries"):
        state[norm_name(r["name"])] = {
            "player_name": r["name"],
            "status": r.get("status"), "type": r.get("type"),
            "detail": r.get("detail"), "date": None,
            "return_date": (r.get("return_date") or "")[:10] or None,
            "feeds": ["fastballapi"], "statyx_commentary": None}
    for r in rows_of(env_sx, "statyx", "injuries"):
        k = norm_name(r["player_name"])
        commentary = r.get("long_comment") or r.get("short_comment")
        if k in state:
            state[k]["feeds"].append("statyx")
            state[k]["statyx_commentary"] = commentary
            state[k]["date"] = (r.get("date") or "")[:10] or None
        else:
            state[k] = {
                "player_name": r["player_name"],
                "status": r.get("status"), "type": r.get("type"),
                "detail": r.get("detail"),
                "date": (r.get("date") or "")[:10] or None,
                "return_date": (r.get("return_date") or "")[:10]
                               or None,
                "feeds": ["statyx"], "statyx_commentary": commentary}
    return state


def _fa_and_roster() -> tuple[dict, dict]:
    fa = json.loads((DATA / "fa_shopping_2027.json").read_text())
    fa_by_norm = {norm_name(p["name"]): p["player_id"]
                  for p in fa["class"]}
    wow = json.loads((DATA / "wow_scenarios.json").read_text())
    roster = {}
    for sc in wow["scenarios"]:
        for p in sc["roster"]:
            roster.setdefault(norm_name(p["name"]),
                              []).append(sc["label"])
    return fa_by_norm, roster


def diff_states(base: dict, cur: dict, base_date: str,
                cur_date: str) -> list[dict]:
    fa_by_norm, roster = _fa_and_roster()
    events = []

    def mk(k, etype, frm, to):
        src = to or frm
        events.append({
            "event_id": f"{cur_date}:{etype}:{src['player_name']}",
            "player_name": src["player_name"],
            "event_type": etype,
            "feeds": src["feeds"],
            "status_from": (frm or {}).get("status"),
            "status_to": (to or {}).get("status"),
            "type_from": (frm or {}).get("type"),
            "type_to": (to or {}).get("type"),
            "detail": src.get("detail"),
            "il_date": src.get("date"),
            "return_date": src.get("return_date"),
            "statyx_commentary": src.get("statyx_commentary"),
            "in_fa_pool": k in fa_by_norm,
            "fa_player_id": fa_by_norm.get(k),
            "scenario_rosters": roster.get(k, []),
            "baseline_date": base_date,
            "current_date": cur_date})

    for k in sorted(set(cur) - set(base)):
        mk(k, "new_il", None, cur[k])
    for k in sorted(set(base) - set(cur)):
        mk(k, "returned", base[k], None)
    for k in sorted(set(base) & set(cur)):
        b, c = base[k], cur[k]
        if (b["status"], b["type"]) != (c["status"], c["type"]):
            mk(k, "status_change", b, c)
    return events


def movement_line(art: dict) -> str:
    fa = art["fa_pool_summary"]
    md = art["metadata"]
    if fa["events_total"] == 0:
        return (f"Movement since {md['baseline_date']}: no movement in "
                f"the FA pool since the baseline pull — census "
                f"(FastballAPI) pulled {md['census_pulled_date']}, "
                f"moves (Statyx) pulled {md['moves_pulled_date']}.")
    return (f"Movement since {md['baseline_date']}: {fa['new_il']} new "
            f"IL, {fa['returned']} returned, {fa['status_change']} "
            f"status changes (FA pool) — census (FastballAPI) pulled "
            f"{md['census_pulled_date']}, moves (Statyx) pulled "
            f"{md['moves_pulled_date']}.")


def build(baseline_pair=None, current_pair=None) -> dict:
    """Assemble data/il_events.json from two snapshot pairs.

    A pair is (statyx_injuries_path, fastballapi_injuries_path).
    Defaults: baseline = Cycle 51 pull; current = newest landed."""
    if baseline_pair is None:
        baseline_pair = (baseline_snapshot("statyx", "injuries"),
                         baseline_snapshot("fastballapi", "injuries"))
    if current_pair is None:
        current_pair = (current_snapshot("statyx", "injuries"),
                        current_snapshot("fastballapi", "injuries"))
    b_sx = load_envelope(baseline_pair[0])
    b_fb = load_envelope(baseline_pair[1])
    c_sx = load_envelope(current_pair[0])
    c_fb = load_envelope(current_pair[1])
    base_date = b_fb["fetched_at"][:10]
    cur_date = c_fb["fetched_at"][:10]
    events = diff_states(player_state(b_sx, b_fb),
                         player_state(c_sx, c_fb), base_date, cur_date)

    def counts(evs):
        return {"events_total": len(evs),
                "new_il": sum(e["event_type"] == "new_il" for e in evs),
                "returned": sum(e["event_type"] == "returned"
                                for e in evs),
                "status_change": sum(e["event_type"] == "status_change"
                                     for e in evs)}

    fa_events = [e for e in events
                 if e["in_fa_pool"] or e["scenario_rosters"]]
    art = {
        "metadata": {
            "cycle": 55,
            "architecture": "FastballAPI = census (canonical IL "
                            "snapshot); Statyx = event layer (recent "
                            "moves); MLB Stats API = standings of "
                            "record; FastballAPI standings = validator",
            "baseline_date": base_date,
            "current_date": cur_date,
            "census_pulled_date": c_fb["fetched_at"][:10],
            "moves_pulled_date": c_sx["fetched_at"][:10],
            "baseline": {
                "statyx_injuries": envelope_ref(baseline_pair[0]),
                "fastballapi_injuries": envelope_ref(baseline_pair[1])},
            "current": {
                "statyx_injuries": envelope_ref(current_pair[0]),
                "fastballapi_injuries": envelope_ref(current_pair[1])},
            "published_view": "FA pool (251) + scenario-roster "
                              "players; the full diff is stored in "
                              "'events'",
            "statyx_standings_test": standings_test(),
        },
        "summary": counts(events),
        "fa_pool_summary": counts(fa_events),
        "events": events,
        "fa_pool_events": fa_events,
    }
    art["metadata"]["movement_line"] = movement_line(art)
    (DATA / "il_events.json").write_text(json.dumps(art, indent=1))
    return art


# ---------------------------------------------------------------------
# Fresh pull (network; only via --pull or refresh_live_feeds)
# ---------------------------------------------------------------------
def _load_helper(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch_all() -> dict:
    """One call per endpoint through the vault helpers. Returns
    {(source, kind): fetched dict}. Raises on any failure BEFORE
    anything is landed (fail closed)."""
    sg = _load_helper(STATYX_HELPER, "statyx_get")
    fp = _load_helper(FASTBALL_HELPER, "fastball_post")
    out = {}
    status, body = sg.get("/v1/mlb/injuries")
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: statyx injuries HTTP {status}")
    out[("statyx", "injuries")] = {
        "endpoint": "GET /v1/mlb/injuries", "payload": body,
        "rows": len(body["data"]), "credits": 0}
    status, body = sg.get("/v1/mlb/standings")
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: statyx standings HTTP {status}")
    out[("statyx", "standings")] = {
        "endpoint": "GET /v1/mlb/standings", "payload": body,
        "rows": len(body["data"]), "credits": 0}
    status, body = fp.post("get_injuries", {})
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: fastball get_injuries "
                         f"HTTP {status}")
    out[("fastballapi", "injuries")] = {
        "endpoint": "POST /v1/get_injuries", "payload": body,
        "rows": len(body["data"]["injuries"]), "credits": 2}
    status, body = fp.post("get_standings", {"season": 2026})
    if status != 200:
        raise SystemExit(f"FAIL CLOSED: fastball get_standings "
                         f"HTTP {status}")
    out[("fastballapi", "standings")] = {
        "endpoint": "POST /v1/get_standings", "payload": body,
        "rows": len(body["data"]["standings"]), "credits": 2}
    return out


def land_fetched(fetched: dict) -> list[dict]:
    """Land fetched envelopes with state-aware dedupe. A payload
    whose state is unchanged vs the newest committed snapshot is NOT
    re-landed; its manifest entry records ok_no_change instead.
    Envelope + manifest formats mirror src/bml_cycle51.py land().
    Returns the manifest entries written."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    today = now[:10]
    entries = []
    with (RAW / "manifest.jsonl").open("a") as mf:
        for (source, kind) in PULLS:
            f = fetched[(source, kind)]
            prev = load_envelope(current_snapshot(source, kind))
            changed = (state_sha(source, kind, f["payload"])
                       != state_sha(source, kind, prev["payload"]))
            entry = {"source": source, "dataset": f"{kind}_{today}",
                     "fetched_at": now,
                     "payload_sha256": payload_sha(f["payload"]),
                     "state_sha256": state_sha(source, kind,
                                               f["payload"]),
                     "rows": f["rows"], "credits": f["credits"],
                     "endpoint": f["endpoint"]}
            if changed:
                envelope = {"source": source,
                            "dataset": f"{kind}_{today}",
                            "endpoint": f["endpoint"],
                            "fetched_at": now, "rows": f["rows"],
                            "sha256": payload_sha(f["payload"]),
                            "payload": f["payload"]}
                content = json.dumps(envelope, indent=1).encode()
                d = RAW / source
                name = f"{kind}_{today}.json"
                n = 2
                while (d / name).exists():
                    name = f"{kind}_{today}_r{n}.json"
                    n += 1
                tmp = d / f".{kind}_{today}.tmp"
                tmp.write_bytes(content)
                tmp.replace(d / name)
                entry.update({"file": name, "status": "ok",
                              "sha256": sha16(content),
                              "bytes": len(content)})
            else:
                entry.update({"status": "ok_no_change",
                              "sha256": payload_sha(f["payload"])[:16],
                              "bytes": 0})
            mf.write(json.dumps(entry) + "\n")
            entries.append(entry)
    return entries


def rebuild_current() -> dict:
    """Rebuild il_current_live.json from the newest landed snapshots
    (Cycle 51 builder, newest-stem driven)."""
    import bml_cycle51
    return bml_cycle51.build()


def pull_and_rebuild() -> dict:
    fetched = fetch_all()          # raises before anything lands
    entries = land_fetched(fetched)
    rebuild_current()
    art = build()
    credits = sum(e["credits"] for e in entries)
    landed = [e["dataset"] for e in entries if e["status"] == "ok"]
    return {"credits": credits, "landed": landed, "artifact": art}


def main() -> None:
    if "--pull" in sys.argv:
        res = pull_and_rebuild()
        art = res["artifact"]
        print(f"pull complete: {res['credits']} FastballAPI credits, "
              f"landed {res['landed'] or 'nothing (no state change)'}")
    else:
        art = build()
    s, f = art["summary"], art["fa_pool_summary"]
    print(f"il_events.json: {s['events_total']} events total "
          f"({s['new_il']} new IL, {s['returned']} returned, "
          f"{s['status_change']} status changes); FA-pool view: "
          f"{f['events_total']} events")
    print("movement:", art["metadata"]["movement_line"])


if __name__ == "__main__":
    main()
