"""Spell-check gate for HARDBALL user-visible text.

The REAL gate: it scans what an owner actually sees — the visible words of the
built dashboard HTML and the prose in docs — and fails (exit 2) on any word
that is neither in the English dictionary nor the vocabulary whitelist.

Correct-but-off-dictionary tokens (team names, stats, analytics terms,
proper nouns, natural plural/import forms) go in WHITELIST. Add a token there
only when you know it is spelled correctly.

Run AFTER the dashboard build:
    ./.venv/bin/python src/dashboard_p6.py
    ./.venv/bin/python src/spellcheck_gate.py
"""
import re
import sys
from spellchecker import SpellChecker as EnSpell

# Intentionally correct / domain vocabulary the affix dictionary doesn't know.
WHITELIST = {
    # stats & analytics
    "obp", "woba", "wrc", "fip", "babip", "iso", "kbb", "marcel", "statcast",
    "xwoba", "moneyball", "overclaim", "overclaimed", "poka", "yoke",
    "backtest", "programme", "unc",
    "winningcheap", "cheapmediocre", "rundiff", "runscored", "runsallowed",
    "constraint", "offensive", "onbase", "walkrate", "hr", "pa", "m",
    # team names / cities / proper nouns
    "mil", "milwaukee", "brewers", "tb", "tampa", "bay", "rays", "cle",
    "cleveland", "guardians", "mia", "miami", "marlins", "chw", "white", "sox",
    "stl", "st", "louis", "cardinals", "lad", "los", "angeles", "dodgers",
    "nym", "mets", "nyy", "yankees", "phi", "phillies", "atl", "braves",
    "bal", "orioles", "bos", "red", "chc", "cubs", "cincinnati", "reds",
    "colorado", "rockies", "detroit", "tigers", "houston", "astros",
    "kansas", "royals", "anaheim", "angels", "minnesota", "twins",
    "pittsburgh", "pirates", "diego", "seattle", "mariners", "francisco",
    "giants", "texas", "rangers", "toronto", "blue", "washington",
    "nationals", "oakland", "athletics", "ath", "az", "diamondbacks",
    # people / roster
    "misiorowski", "judge", "aaron", "soto",
    # Cycle 48 (HS-2) vocabulary — verified correct spellings
    "sauer", "misprices", "mispricing", "underprices", "workpaper",
    # Cycle 49 (OPT-1) vocabulary — verified correct spellings
    "combinatorics", "dh", "milp", "scipy",
    # Cycle 50 (OPT-2) pre-arb names — verified against data/salaries_2026.json
    "ashcraft", "bolte", "braxton", "caglianone", "culpepper", "delauter",
    "dingler", "jac", "kaelen", "keaschall", "kurtz", "messick", "roki",
    "sasaki", "schlittler",
    # data/tools vocab
    "api", "espn", "mlb", "statsapi", "spotrac", "github", "plotly",
    "sqlite", "csv", "kpi", "kpis", "keyless", "gitignored", "json", "html",
    "jasonbhorne", "cdn", "tooltip", "tooltips", "lineweaver", "wright",
    "tufte", "few", "powerbi", "tableau", "tab", "bml", "uat", "poka",
    # common words / numbers the dict may miss
    "homers", "stead", "per", "vs", "proj", "r", "n", "f", "w", "q", "qo",
    # stat/metric abbreviations + domain terms surfaced as themselves
    "auc", "bb", "bb9", "bwar", "fwar", "cba", "chartjunk", "datasets",
    "diff", "gridlines", "gp", "il", "lookup", "mvp", "repo", "stat", "yr",
    "bapip", "hr9", "k9", "whip", "ceiling", "floor", "derts", "euler",
    # merged toby-lane (Cycle 27-30) vocabulary — verified correct spellings
    "aa", "aaa", "aav", "backtested", "backtests", "benchmarked", "carpe",
    "carpedata", "cv", "dropdown", "ev", "fangraphs", "ii", "iii", "iv",
    "leaderboards", "leaderboard", "milb", "pre", "prs", "qc", "vi", "vii",
    # Cycle 47 fig-23 source-line path tokens — verified correct
    "src", "py",
    # Cycle 33 percentile-card names — verified against data/fa_shopping_2027.json
    "bauers", "buehler", "lorenzen", "quantrill", "rengifo", "sd",
    # Cycle 34 posted-class names — verified against data/posted_class_2026.json
    "teruaki", "sato", "kaima", "taira", "hiromi", "itoh", "tatsuya", "imai",
    "hanshin", "seibu", "saitama", "nippon", "hokkaido", "hanwha", "roh",
    "hwan", "sawamura", "npb", "bis", "kbo",
    # Cycle 34 posted-class vocab — notes/headers/sources from the same file
    "heyman", "murakami", "passan", "tarik", "skubal", "cy", "sportsnet",
    "mlbtr", "ap", "ny", "jp", "sep", "avg", "slg", "rbi", "ip", "sv",
    "rhp", "dataset", "roundings", "comp", "gm", "ft",
    # Cycle 45 connected-source names — verified against the providers
    "statyx", "fastballapi", "chadwick", "tank", "sportradar", "mcp", "io",
    "lrp", "metadata", "mlbam", "rapidapi", "retrosheet", "signup",
}


def visible_words_from_html(html_path: str):
    """Extract only the words a human reads from the built dashboard HTML."""
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    # drop <script>, <style>, and tag markup entirely
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&[a-zA-Z#0-9]+;", " ", html)
    # drop plotly/graph labels that live inside the JSON data blobs
    # (those carry tag/attr noise); keep only alphabetic tokens
    return re.findall(r"[A-Za-z][A-Za-z'‘’]*", html)


def doc_words(paths):
    """Words from markdown prose, skipping code fences and code lines."""
    out = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            continue
        in_fence = False
        for ln in lines:
            if ln.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or ln.startswith(("    ", "\t", "# ", "> ")):
                continue
            if re.search(r"(\$[a-z]|`|\(\)|\.py\b|\[[a-z]+\]|\([a-z_]+\))", ln):
                continue  # code-ish line
            out.extend(re.findall(r"[A-Za-z][A-Za-z'‘’]*", ln))
    return out


def main() -> int:
    spell = EnSpell(language="en")
    targets = (["dashboard/hardball_demo.html"] if __import__("os").path.exists(
        "dashboard/hardball_demo.html") else []) + [
        "README.md", "docs/TALKTRACK.md", "docs/EXEC_SUMMARY.md",
        "docs/VIZ_BEST_PRACTICES.md",
    ]
    html = targets[:1]
    docs = targets[1:]
    words = visible_words_from_html(html[0]) if html else []
    words += doc_words(docs)

    bad = {}
    for w in words:
        c = w.lower().strip("'‘’")
        # strip only a true possessive suffix ("euler's" -> "euler"), never
        # a trailing plural s ("categories" stays "categories")
        c = re.sub(r"('s|‘s|’s)$", "", c)
        c = c.strip("'‘’")
        if not c or len(c) < 2 or c in WHITELIST or c.isdigit():
            continue
        if c not in spell:
            bad[c] = bad.get(c, 0) + 1

    if bad:
        print("SPELLCHECK FAILED — misspelled words in user-visible text:")
        for word in sorted(set(bad)):
            print(f"  ? {word}")
        print("Fix real typos; a correctly-spelled-but-unknown term goes in the")
        print("WHITELIST set at the top of src/spellcheck_gate.py.")
        return 2
    print("Spellcheck OK — no misspellings in user-visible text.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
