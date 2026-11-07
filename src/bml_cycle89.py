#!/usr/bin/env python3
"""Cycle 89: sync the claims-pack trace counts to the authoritative register.

BOOKKEEPING ONLY — no new analysis, no claim status changes, no figure
changes. The faculty quantitative audit (2026-11-07) found one
documentation inconsistency: data/figure_trace_2027.json still carries
its Cycle 68 counts block (17 supported / 7 not supported) while
data/claims_register.json — updated by Cycle 85 when N06 flipped to
SUPPORTED — counts 18 supported / 6 not supported by direct count.
The register is authoritative and self-consistent (the gate verifies
its counts reconcile); the trace file's counts block is a stale copy
of the same dict (both were computed together in Cycle 68, and Cycle
85's register update never wrote the trace copy back). The dashboard
already prints the register's numbers, so nothing rendered changes.

This script asserts the register reconciles by direct count, asserts
the trace's figure/panel counts are unchanged (25/25, 8/8), then syncs
tr["counts"] from reg["counts"] — the Cycle 69 precedent for patching
the trace file in place. Exit 1 on any failed assertion: a register
that does not reconcile is FLAGGED, never papered over.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
FAILURES = []


def check(name, ok, detail=""):
    if not ok:
        FAILURES.append(name)
        print(f"  FLAG  {name} — {detail}")
    return ok


def main():
    reg_path = os.path.join(DATA, "claims_register.json")
    tr_path = os.path.join(DATA, "figure_trace_2027.json")
    reg = json.load(open(reg_path))
    tr = json.load(open(tr_path))

    claims = reg["claims"]
    direct = {
        "supported": sum(1 for c in claims if c["status"] == "SUPPORTED"),
        "not_supported": sum(1 for c in claims if c["status"] == "NOT SUPPORTED"),
        "retracted": len(reg["retracted"]),
        "open_items": len(reg["open_items"]),
        "resolved_items": len(reg.get("resolved_items", [])),
    }
    check("Register counts reconcile by direct count (18/6/3/0/1)",
          reg["counts"]["supported"] == direct["supported"] == 18
          and reg["counts"]["not_supported"] == direct["not_supported"] == 6
          and reg["counts"]["retracted"] == direct["retracted"] == 3
          and reg["counts"]["open_items"] == direct["open_items"] == 0
          and reg["counts"]["resolved_items"] == direct["resolved_items"] == 1,
          str(reg["counts"]))
    check("Trace figures/panels unchanged (25/25, 8/8)",
          tr["counts"]["figures_traced"] == 25
          and tr["counts"]["figures_verified"] == 25
          and tr["counts"]["panels_traced"] == 8
          and tr["counts"]["panels_verified"] == 8
          and len(tr["figures"]) == 25 and len(tr["panels"]) == 8,
          str(tr["counts"]))
    check("Trace counts block is the stale pre-Cycle-85 copy (17/7)",
          tr["counts"]["supported"] == 17
          and tr["counts"]["not_supported"] == 7,
          str(tr["counts"]))
    if FAILURES:
        print(f"CYCLE 89: {len(FAILURES)} FLAG(S) — trace NOT updated")
        return 1

    tr["counts"] = dict(reg["counts"])
    tr["build_commands"]["pack_update_cycle89"] = "python3 src/bml_cycle89.py"
    with open(tr_path, "w") as fh:
        json.dump(tr, fh, indent=1, ensure_ascii=False)
    print(f"trace counts synced: {tr['counts']['supported']} supported, "
          f"{tr['counts']['not_supported']} not supported, "
          f"{tr['counts']['retracted']} retracted, "
          f"{tr['counts']['open_items']} open, "
          f"{tr['counts']['resolved_items']} resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
