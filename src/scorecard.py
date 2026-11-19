"""Automated scorecard against docs/SCORING_RUBRIC.md.

Runs every machine-checkable rubric item in seconds so each fix is verified
immediately; a full independent review is only needed to confirm a 9.

    python src/scorecard.py            # table
    python src/scorecard.py --json     # machine-readable
Exit 0 when every [auto] item passes, 1 otherwise.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def checks() -> list[dict]:
    out: list[dict] = []

    def add(dim: str, item: str, ok: bool, detail: str = "") -> None:
        out.append({"dimension": dim, "item": item, "pass": bool(ok), "detail": detail})

    rc, txt = _run(["ruff", "check", "src", "tests", "-q"])
    add("Code quality", "ruff clean", rc == 0, txt.strip()[:120])
    rc, txt = _run([PY, "-m", "pytest", "-q", "-o", "addopts="])
    m = re.search(r"(\d+) passed", txt)
    n_pass = int(m.group(1)) if m else 0
    add("Code quality", "tests pass (>=25)", rc == 0 and n_pass >= 25, f"{n_pass} passed")
    tests = {p.stem for p in (ROOT / "tests").glob("test_*.py")}
    need = ["http_client", "check_freshness", "forecast_eval", "decision_brief", "check_connectors"]
    missing = [n for n in need if f"test_{n}" not in tests]
    add("Code quality", "shared modules have tests", not missing, ",".join(missing))
    ci = (ROOT / ".github/workflows/ci.yml")
    ci_txt = ci.read_text() if ci.exists() else ""
    add("Code quality", "CI runs lint+tests+gates",
        all(k in ci_txt for k in ("ruff", "pytest", "verify_data", "check_freshness")))
    html = (ROOT / "dashboard/index.html").read_text()
    add("Code quality", "deterministic build", not re.search(r'id="[0-9a-f]{8}-[0-9a-f]{4}-', html))

    offenders = [p.name for p in (ROOT / "src").glob("*.py")
                 if p.name not in {"http_client.py", "accuracy_monitor.py", "scorecard.py"}
                 and re.search(r"requests\.(get|post|request)\(|urlopen\(", p.read_text())]
    add("API & data health", "0 fetches bypass http_client", not offenders, ",".join(offenders))
    hc = (ROOT / "src/http_client.py").read_text()
    add("API & data health", "403/429 never retried",
        "RETRY_STATUSES = (500, 502, 503, 504)" in hc)
    rc, txt = _run([PY, "src/verify_data.py"])
    fails = re.findall(r"^FAIL\s+(.{0,70})", txt, re.M)
    add("API & data health", "verify_data gate", rc == 0, "; ".join(fails)[:160])
    rc, txt = _run([PY, "src/check_freshness.py"])
    add("API & data health", "freshness/provenance gate", rc == 0, txt.strip().splitlines()[-1][:120] if txt else "")
    cc = (ROOT / "src/check_connectors.py").read_text()
    add("API & data health", "rolling connector window", "transaction_window()" in cc)

    add("UI/UX", "plotly vendored", 'src="vendor/plotly-2.35.2.min.js"' in html
        and (ROOT / "dashboard/vendor/plotly-2.35.2.min.js").exists())
    add("UI/UX", "a11y landmarks", '<html lang="en">' in html and 'role="main"' in html
        and 'role="figure" aria-label="' in html)
    add("UI/UX", "decision brief above colour key",
        0 <= html.find('class="dbrief"') < html.find("COLOR KEY"))

    brief = ROOT / "data/decision_brief_2027.json"
    b = json.loads(brief.read_text()) if brief.exists() else {}
    top = b.get("top", [])
    add("Insight", "ranked priced brief", len(top) >= 10 and all("surplus_usd" in r for r in top))
    unc = ROOT / "data/marcel_backtest_uncertainty.json"
    u = json.loads(unc.read_text()) if unc.exists() else {}
    add("Rigor", "CI + Diebold-Mariano vs baselines",
        "dm_hln_stat" in json.dumps(u) and "ci95" in json.dumps(u))
    reg = json.loads((ROOT / "data/claims_register.json").read_text())
    c = reg["counts"]
    add("Rigor", "claims register reconciles",
        c["supported"] == sum(x["status"] == "SUPPORTED" for x in reg["claims"])
        and c["not_supported"] == sum(x["status"] == "NOT SUPPORTED" for x in reg["claims"]))
    add("Actionability", "brief: act-by, band, basis, fallback, CSV",
        bool(top) and all(k in top[0] for k in ("act_by", "war_p10", "war_p90", "price_basis", "fallback"))
        and (ROOT / "dashboard/decision_brief_2027.csv").exists())
    return out


def main() -> int:
    rows = checks()
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1))
    else:
        dims: dict[str, list[dict]] = {}
        for r in rows:
            dims.setdefault(r["dimension"], []).append(r)
        print("| Dimension | Auto checks passing | Failing |\n|---|---|---|")
        for d, rs in dims.items():
            bad = [f"{r['item']} ({r['detail']})" if r["detail"] else r["item"] for r in rs if not r["pass"]]
            print(f"| {d} | {sum(r['pass'] for r in rs)}/{len(rs)} | {'; '.join(bad) or '—'} |")
    return 0 if all(r["pass"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
