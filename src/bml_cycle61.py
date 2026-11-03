#!/usr/bin/env python3
"""BML Cycle 61 — PRICE-1: predicted-price model, inventory first.

Slate item 1 of 6 (owner approved the full elite/asset slate
2026-11-02, run in order). The 2027 prices the demo hangs on —
optimizer rosters, $/WAR, forced sellers — are prior-contract AAV
anchors (data/optimizer_comparison_2027.json, Cycle 49 metadata:
"prior-contract AAV (Spotrac) — a last-price anchor, NOT a
predicted 2027 price"). This cycle builds the model that replaces
them — but only if it earns the switch in backtest.

Design (declared before running; the bar is pre-committed):
- STEP 0, INVENTORY BEFORE MODELING, FAIL CLOSED. A price model
  needs a training set of ACTUAL signed free-agent contracts:
  per signing — player, class, years, total $, signed AAV — for
  complete historical classes, joined to features known BEFORE
  signing. This script audits every committed repo source for
  that data and states what the training set IS. If complete-class
  signed terms are not in the repo in usable form, NO model is
  fit, NO numbers are invented, NO blocked source is scraped
  (Spotrac / FanGraphs stand 403), and the cycle ships as a
  workpaper: the inventory verdict, the exact missing source,
  and the model design ready to run when it lands.
- THE BAR (fixed before any fit): train on classes 2022 + 2023,
  test on held-out class 2024. The model replaces anchors as the
  optimizer input ONLY if its held-out MAE on signed AAV is at
  least 10% lower than the prior-AAV anchor baseline's MAE on the
  same test players. Otherwise anchors stay and the model ships
  as a labeled workpaper with the reason.
- MODEL DESIGN, PRE-REGISTERED HERE so a future cycle runs it
  unchanged when the data lands — see the artifact's
  model_design_preregistered block (target ln(signed AAV);
  features: pre-signing projected WAR, age, position group,
  prior AAV as a FEATURE not the answer; ridge first, gradient
  boosting only if it clearly wins the same backtest; baselines:
  prior-AAV anchor and class-median $/WAR).

Output: data/price_model_workpaper_2027.json. Offline, read-only
against committed artifacts; writes only its own artifact.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CONTRACT_RE = re.compile(r"^(\d+)\s*y/\$([\d.]+)M\s*\((\d+)-(\d+)\)")
TERMS_FIELD_NAMES = ("signed_aav", "contract_years", "signed_years",
                     "deal_years", "total_value", "signing_aav")


def load(name):
    return json.loads((DATA / name).read_text())


def main() -> int:
    # --- the incumbent: what the optimizer prices on today -----
    opt = load("optimizer_comparison_2027.json")
    price_basis = opt["metadata"]["price_basis"]
    fa = load("fa_shopping_2027.json")["class"]
    n_class = len(fa)
    n_prev_aav = sum(1 for r in fa if r.get("prev_aav"))
    n_market_aav = sum(1 for r in fa if r.get("spotrac_market_aav"))

    # --- signing census: identity + dates exist, terms do not -
    unc1 = load("unc1_availability_backtest.json")
    census = {yr: unc1["classes"][yr]["n_signed"]
              for yr in ("2022", "2023", "2024")}

    # --- survivor terms: Cot's contract strings ----------------
    cots = load("salaries_cots_2027.json")["players"]
    parsed = []
    for r in cots:
        m = CONTRACT_RE.match(r.get("contract") or "")
        if m:
            yrs, tot = int(m.group(1)), float(m.group(2))
            parsed.append({"span_start": 2000 + int(m.group(3)),
                           "years": yrs, "total_m": tot,
                           "aav_m": tot / yrs})
    by_span = Counter(p["span_start"] for p in parsed)
    class_terms = {}
    for cls, span in (("2022", 2023), ("2023", 2024), ("2024", 2025)):
        rows = [p for p in parsed if p["span_start"] == span]
        class_terms[cls] = {
            "span_start": span,
            "n_terms_recoverable": len(rows),
            "min_years": min((p["years"] for p in rows), default=None),
            "one_year_deals": sum(1 for p in rows if p["years"] == 1),
            "two_year_deals": sum(1 for p in rows if p["years"] == 2),
        }

    # --- no committed artifact carries signing-terms fields ----
    terms_artifacts = []
    for path in sorted(DATA.glob("*.json")):
        text = path.read_text(errors="replace")
        if any(f'"{f}"' in text for f in TERMS_FIELD_NAMES):
            terms_artifacts.append(path.name)

    # --- Spotrac file: active-contract snapshot, same shape ----
    spotrac = load("salaries_2026.json")["players"]

    inventory = [
        {"source": "MLB Stats API transactions, as committed in "
                   "data/unc1_availability_backtest.json (Cycle 54)",
         "holds": "Signing census: player + signing date for every "
                  "'Signed as Free Agent' transaction, classes "
                  "2022-2024 (n_signed 1645 / 1849 / 1659; 5,153 "
                  "total screened)",
         "usable_as_training": False,
         "reason": "Identity and dates only — the transactions feed "
                   "carries no contract terms (no years, no dollars). "
                   "It defines the classes; it cannot price them."},
        {"source": "data/salaries_cots_2027.json contract strings "
                   "(Cot's, Cycle 41)",
         "holds": f"{len(parsed)} parseable signed-contract strings "
                  f"('6 y/$210M (25-30)') with cb_2027_aav, out of "
                  f"{len(cots)} player rows on 2027 payrolls",
         "usable_as_training": False,
         "reason": "Survivors only: a contract appears only if it "
                   "still touches a 2027 payroll. Class 2022 keeps "
                   "24 deals, ALL >= 3 years — every 1-2 year deal "
                   "signed for 2023-24 expired before this snapshot "
                   "and is invisible. Class 2024 keeps 35, none of "
                   "them 1-year. Spans also mix extensions with FA "
                   "signings (no signing-type field). Training or "
                   "testing on survivors validates the model on "
                   "long deals only, then applies it to a 251-man "
                   "class full of short-deal candidates — a known "
                   "selection mechanism, not a sample."},
        {"source": "data/salaries_2026.json (Spotrac-basis, 2027 "
                   "payroll)",
         "holds": f"{len(spotrac)} active-contract salary rows",
         "usable_as_training": False,
         "reason": "Same snapshot shape as Cot's: active 2027 "
                   "contracts, no signing dates, no expired deals. "
                   "It is the incumbent anchor source, not a "
                   "training set."},
        {"source": "data/hakes_sauer_dataset.json (HS-1, Cycle 46)",
         "holds": "142 hitters: ACTIVE 2027 contract salaries vs "
                  "2027 projections",
         "usable_as_training": False,
         "reason": "Its own design limit, recorded at build: "
                   "anchors are active contracts, 'not newly "
                   "signed FA contracts — no signing-date field "
                   "exists in the repo.' Cross-section, not "
                   "signings."},
        {"source": "data/fa_shopping_2027.json (the 2027 class)",
         "holds": f"{n_class} FAs; prev_aav on {n_prev_aav}; "
                  f"spotrac_market_aav on {n_market_aav}",
         "usable_as_training": False,
         "reason": "This is the class TO BE priced. prev_aav is "
                   "the incumbent anchor; spotrac_market_aav is "
                   "Spotrac's own unbacktested estimate — another "
                   "model's output is not training data."},
        {"source": "repo-wide scan for signing-terms fields",
         "holds": f"artifacts carrying any of {list(TERMS_FIELD_NAMES)}: "
                  f"{terms_artifacts if terms_artifacts else 'NONE'}",
         "usable_as_training": False,
         "reason": "No committed artifact records historical FA "
                   "signing terms."},
    ]

    artifact = {
        "cycle": "61 — PRICE-1 (elite slate item 1 of 6)",
        "question": "Can a model predict 2027 FA signed AAV better "
                    "than the prior-AAV anchors the optimizer "
                    "prices on today — proven in backtest before "
                    "any switch?",
        "verdict": "NOT RUN — TRAINING DATA ABSENT",
        "bar": {
            "rule": "Model replaces anchors as the optimizer input "
                    "only if held-out MAE on signed AAV (train "
                    "classes 2022+2023, test class 2024) is at "
                    "least 10% lower than the prior-AAV anchor "
                    "baseline's MAE on the same test players.",
            "threshold_fraction": 0.10,
            "status": "UNTESTED — no fit was run; anchors remain "
                      "the optimizer input, unchanged.",
        },
        "incumbent": {
            "price_basis": price_basis,
            "optimizer_pool": opt["metadata"]["pool"],
            "fa_class_n": n_class,
            "prev_aav_coverage": n_prev_aav,
            "spotrac_market_aav_coverage": n_market_aav,
        },
        "signing_census": {
            "source": "MLB Stats API transactions via Cycle 54 "
                      "(data/unc1_availability_backtest.json)",
            "n_signed": census,
            "n_total": sum(census.values()),
            "carries_terms": False,
        },
        "survivorship": {
            "source": "data/salaries_cots_2027.json contract "
                      "strings, parsed by this script",
            "cots_rows": len(cots),
            "parseable_contracts": len(parsed),
            "by_span_start": dict(sorted(by_span.items())),
            "classes": class_terms,
            "bias": "Terms are recoverable ONLY for contracts "
                    "still touching a 2027 payroll: class 2022 "
                    "keeps 24 of ~1,645 signings, all >= 3 years; "
                    "class 2023 keeps 18, all >= 3 years; class "
                    "2024 keeps 35, none 1-year — against a census "
                    "dominated by short deals. A backtest on "
                    "survivors cannot certify predictions for the "
                    "full 2027 class.",
        },
        "inventory": inventory,
        "missing_source": {
            "what": "A complete per-class record of FA signing "
                    "terms — player (MLBAM id), signing date / "
                    "class, years, total $, signed AAV — covering "
                    "expired short deals as well as live long ones.",
            "readiness_criteria": [
                ">= 90% of each class's StatsAPI signing census "
                "matched to terms, per class, 2022-2024",
                "1- and 2-year deals present in proportion (the "
                "survivor test: class min_years == 1)",
                "extensions separable from FA signings "
                "(signing-type field or transaction join)",
                "AAV stated or computable as total $ / years "
                "from the same record",
            ],
            "candidate_routes": [
                {"route": "Sportradar MLB v8 trial (owner plan, "
                          "~Nov 15)",
                 "status": "NOT YET OPENED — when it lands, "
                           "verify FIRST whether its contracts "
                           "coverage includes expired historical "
                           "deals or only current rosters; current-"
                           "roster-only does not close this gap."},
                {"route": "Spotrac free-agent tracker archives",
                 "status": "BLOCKED — 403 (standing probe "
                           "result); never routed around."},
                {"route": "FanGraphs free-agent tracker",
                 "status": "BLOCKED — 403 Cloudflare (Cycle 32); "
                           "never routed around."},
                {"route": "MLBTR free-agent tracker archives",
                 "status": "UNPROBED — editorial tracker tables; "
                           "scraping method is an owner call, not "
                           "taken unilaterally."},
            ],
        },
        "model_design_preregistered": {
            "target": "ln(signed AAV)",
            "features": [
                "pre-signing projected WAR (the projection the "
                "repo holds for that class year; if a class year's "
                "projections are not held, prior-season actual "
                "performance — and the artifact says which)",
                "age at signing",
                "position group",
                "prior AAV (a feature, never the answer)",
                "contract-market year (class fixed effect)",
            ],
            "form": "Ridge regression on ln(AAV) first — simple, "
                    "inspectable; gradient boosting runs only if "
                    "it beats ridge clearly on the same backtest.",
            "validation": "Train classes 2022 + 2023 -> test "
                          "held-out class 2024, exact class split, "
                          "no shuffling across classes.",
            "baselines": [
                "prior-AAV anchor on the same test players",
                "class-median $/WAR x projected WAR (naive)",
            ],
            "metrics": "Held-out MAE in $M and %, model vs each "
                       "baseline, on identical players.",
            "switch_mechanics_if_bar_met": [
                "Write data/price_model_2027.json (per-player "
                "predicted AAV for the 251, spec, backtest table)",
                "Re-run the Cycle 49 MILP on predicted prices "
                "(same pools / quotas / constraints)",
                "Re-run Cycle 50 +/-20% sensitivity on the "
                "predicted prices",
                "UNC-2 intervals stay attached to the anchor-"
                "priced run until re-derived on predicted prices "
                "— no re-derivation shortcuts",
                "Dashboard headlines switch with a visible "
                "'prices: model-predicted' label; anchor-priced "
                "results preserved as a labeled sensitivity "
                "(Cycle 52 swap pattern)",
                "Dashboard change ships with its own release cut "
                "(Cycle 60 lesson)",
            ],
        },
        "dashboard_change": "none",
        "release": "none — dashboard unchanged",
    }

    out = DATA / "price_model_workpaper_2027.json"
    out.write_text(json.dumps(artifact, indent=1) + "\n")
    print(f"wrote {out}")
    print(f"verdict: {artifact['verdict']}")
    print(f"census: {census} (total {sum(census.values())})")
    print(f"survivor terms by class: "
          f"{ {k: v['n_terms_recoverable'] for k, v in class_terms.items()} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
