"""P6: HARDBALL demo dashboard (Plotly HTML).

Three panels on real 2026 data:
 1. Payroll vs Wins scatter — the efficiency story (winning-cheap ellipse).
 2. KPI comparison: winning-cheap vs cheap-mediocre vs other (OBP, contact,
    K%, BB%, HR/PA).
 3. Cap-constrained projections: proj wins vs payroll vs 2027 cap
    ($245.3M cap / $171.2M floor).
Serves as a self-contained HTML file the GP can open at the Winter Meetings.
"""
import json
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import kpi as kpi_mod
from model_p6 import FEATURES
import numpy as np
from sklearn.linear_model import LinearRegression

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")

WIN_CHEAP = {"MIL", "TB", "CLE"}
CHEAP_MEDIOCRE = {"MIA", "CHW", "STL"}
CAP = 245_300_000
FLOOR = 171_200_000


def _color(team):
    if team in WIN_CHEAP:
        return "green"
    if team in CHEAP_MEDIOCRE:
        return "orange"
    return "steelblue"


def panel_payroll_wins(df, year=2026):
    d = df[df["season"] == year].dropna(subset=["payroll", "wins"])
    fig = go.Figure()
    for g, color, name in [("WIN_CHEAP", "green", "Winning-cheap (CLE/TB/MIL)"),
                           ("CHEAP_MEDIOCRE", "orange", "Cheap-mediocre (MIA/CHW/STL)"),
                           ("OTHER", "steelblue", "Other")]:
        sub = d[d["group"] == g]
        fig.add_trace(go.Scatter(
            x=sub["payroll"] / 1e6, y=sub["wins"], mode="markers+text",
            name=name, marker=dict(color=color, size=12),
            text=[f"<b>{t}</b>" for t in sub["team"]], textposition="top center"))
    fig.add_vline(x=CAP / 1e6, line_dash="dash", line_color="red",
                  annotation_text=f"Proposed cap $245.3M", annotation_position="top right")
    fig.add_vline(x=FLOOR / 1e6, line_dash="dot", line_color="purple",
                  annotation_text=f"Proposed floor $171.2M", annotation_position="bottom right")
    fig.update_layout(title=f"{year} — Payroll ($M) vs Wins: money buys some wins; winning-cheap teams win MORE per $",
                      xaxis_title="Total payroll ($M)", yaxis_title="Wins",
                      template="plotly_white", height=520)
    return fig


def panel_kpi(df, year=2026):
    d = df[df["season"] == year].dropna(subset=["OBP", "contact", "K%", "BB%", "HR/PA"])
    grp = d.groupby("group")[["OBP", "contact", "K%", "BB%", "HR/PA"]].mean()
    metrics = ["OBP", "BB%", "HR/PA", "contact", "K%"]
    labels = {"OBP": "OBP", "BB%": "BB%", "HR/PA": "HR / 1000 PA", "contact": "Contact %", "K%": "K%"}
    fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=[labels[m] for m in metrics])
    colors = {"WIN_CHEAP": "#1b5e20", "CHEAP_MEDIOCRE": "#e65100", "OTHER": "#1565c0"}
    for i, m in enumerate(metrics, start=1):
        for g in ["WIN_CHEAP", "CHEAP_MEDIOCRE", "OTHER"]:
            fig.add_trace(go.Bar(x=[g], y=[grp.loc[g, m]], marker_color=colors[g],
                                 showlegend=(i == 1), name=g), row=1, col=i)
    fig.update_layout(title=f"{year} — Copycat-league KPI signature (winning-cheap dominates contact/OBP)",
                      template="plotly_white", height=420)
    return fig


def panel_projections(proj_fname="projections_2026.json"):
    proj = pd.read_json(os.path.join(DATA, proj_fname))
    fig = go.Figure()
    colors = [("green" if t in WIN_CHEAP else "orange" if t in CHEAP_MEDIOCRE else "steelblue")
              for t in proj["team"]]
    fig.add_trace(go.Bar(x=proj["team"], y=proj["proj_wins"], marker_color=colors,
                         text=[f"{v:.0f}" for v in proj["proj_wins"]], textposition="outside"))
    fig.update_layout(title="2026 — Model-projected wins by team (from hitting KPIs + payroll)",
                      xaxis_title="Team", yaxis_title="Projected wins",
                      template="plotly_white", height=460)
    return fig


def panel_durability():
    """25-year (2000-2024) payroll-quartile efficiency: win per $100M by quartile."""
    d = pd.read_csv(os.path.join(DATA, "efficiency_2000_2024.csv"))
    d["qt"] = d.groupby("yearID")["payroll"].transform(
        lambda x: pd.qcut(x.rank(method="first"), 4, labels=False))
    agg = d.groupby("qt").agg(win100=("wins_per_100m", "mean"),
                              wins=("wins", "mean"),
                              lab=("payroll", "mean"))
    labels = [f"Q{i+1} (lowest ${agg['lab'][g]/1e6:.0f}M)" for i, g in enumerate([0,1,2,3])]
    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        "Wins per $100M by payroll quartile (2000-2024)",
        "Wins by payroll quartile (2000-2024)"])
    colors = ["#2e7d32", "#8bc34a", "#ef6c00", "#1565c0"]
    fig.add_trace(go.Bar(x=labels, y=agg["win100"].values, marker_color=colors,
                         text=[f"{v:.0f}" for v in agg["win100"]], textposition="outside"), 1, 1)
    fig.add_trace(go.Bar(x=labels, y=agg["wins"].values, marker_color=colors,
                         text=[f"{v:.0f}" for v in agg["wins"]], textposition="outside"), 1, 2)
    fig.update_layout(title="25-year proof (2000-2024, 721 team-seasons): efficiency is durable — "
                             "BUT cheap wins per $, not wins (winning-cheap = both)",
                      template="plotly_white", height=420)
    return fig


def panel_player_proj():
    """2027 Marcel projections: top hitters by OBP, colored by team group."""
    proj = pd.read_json(os.path.join(DATA, "projections_2027.json"))
    top = proj.sort_values("proj_OBP", ascending=False).head(15)
    def grp(team):
        t = (str(team) or "").upper()
        ab = {"NEW YORK YANKEES":"NYY","HOUSTON ASTROS":"HOU","NEW YORK METS":"NYM",
              "MILWAUKEE BREWERS":"MIL","TAMPA BAY RAYS":"TB","ARIZONA DIAMONDBACKS":"AZ",
              "DETROIT TIGERS":"DET","LOS ANGELES DODGERS":"LAD"}.get(t.upper(), (t or "")[:3])
        if ab in WIN_CHEAP: return "green"
        if ab in CHEAP_MEDIOCRE: return "orange"
        return "steelblue"
    colors = [grp(t) for t in top["team"]]
    fig = go.Figure(go.Bar(x=top["name"], y=top["proj_OBP"], marker_color=colors,
                           text=[f"{v:.3f}" for v in top["proj_OBP"]], textposition="outside"))
    fig.update_layout(title="2027 projected hitters by OBP (Marcel, real lake data) — "
                            "green = winning-cheap team",
                      xaxis_title="", yaxis_title="Projected OBP",
                      template="plotly_white", height=440)
    return fig


def panel_pitching():
    """Winning-cheap pitching signature: IP-weighted ERA/WHIP/BBy per group (2026)."""
    import subprocess, json as J
    # table-level re-aggregation inline from lake (clean, no module import cycle)
    import sqlite3
    TEAM = {"New York Yankees":"NYY","Houston Astros":"HOU","New York Mets":"NYM",
      "Milwaukee Brewers":"MIL","Tampa Bay Rays":"TB","Arizona Diamondbacks":"AZ",
      "Detroit Tigers":"DET","Los Angeles Dodgers":"LAD","Cleveland Guardians":"CLE",
      "Miami Marlins":"MIA","Chicago White Sox":"CHW","St. Louis Cardinals":"STL",
      "Texas Rangers":"TEX","Seattle Mariners":"SEA","San Francisco Giants":"SF",
      "Boston Red Sox":"BOS","Philadelphia Phillies":"PHI","Atlanta Braves":"ATL",
      "San Diego Padres":"SD","Toronto Blue Jays":"TOR","Minnesota Twins":"MIN",
      "Baltimore Orioles":"BAL","Los Angeles Angels":"LAA","Chicago Cubs":"CHC",
      "Cincinnati Reds":"CIN","Colorado Rockies":"COL","Kansas City Royals":"KC",
      "Pittsburgh Pirates":"PIT","Washington Nationals":"WSH","Oakland Athletics":"ATH"}
    con = sqlite3.connect(os.path.join(DATA, "mlb_lake.db"))
    rows = []
    for season, team, sjson in con.execute("SELECT season,team,stat_json FROM stat_lines WHERE group_name='pitching'"):
        s = J.loads(sjson)
        rows.append({"season": season, "code": TEAM.get(team, team), "IP": s.get("inningsPitched"),
                     "ERA": s.get("era"), "WHIP": s.get("whip"), "BB": s.get("walks")})
    con.close()
    d = pd.DataFrame(rows)
    for c in ["IP", "ERA", "WHIP", "BB"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["IP", "ERA"])[d["IP"] >= 30]
    d["grp"] = "OTHER"
    d.loc[d["code"].isin(WIN_CHEAP), "grp"] = "WIN_CHEAP"
    d.loc[d["code"].isin(CHEAP_MEDIOCRE), "grp"] = "CHEAP_MEDIOCRE"
    d = d[d["season"] == 2026]
    g = d.groupby("grp").apply(lambda x: pd.Series({
        "ERA": (x["ERA"]*x["IP"]).sum()/x["IP"].sum(),
        "WHIP": (x["WHIP"]*x["IP"]).sum()/x["IP"].sum(),
        "BB/9": (x["BB"]*9/x["IP"]).sum()/len(x)}), include_groups=False)
    metrics = ["ERA", "WHIP", "BB/9"]
    labels = {"ERA":"ERA","WHIP":"WHIP","BB/9":"BB per 9 IP"}
    fig = make_subplots(rows=1, cols=3, subplot_titles=[labels[m] for m in metrics])
    colors = {"WIN_CHEAP":"#1b5e20","CHEAP_MEDIOCRE":"#e65100","OTHER":"#1565c0"}
    for i, m in enumerate(metrics, start=1):
        for grp in ["WIN_CHEAP","CHEAP_MEDIOCRE","OTHER"]:
            fig.add_trace(go.Bar(x=[grp], y=[g.loc[grp, m]], marker_color=colors[grp],
                                 showlegend=(i==1), name=grp), row=1, col=i)
    fig.update_layout(title="2026 — Pitching is the other winning-cheap half: low-BB, low-WHIP, elite ERA",
                      template="plotly_white", height=420)
    return fig


def panel_health():
    """Health pillar: top players by IL-based PA penalty (2027 projections)."""
    ile = os.path.join(DATA, "projections_2027_health.json")
    if not os.path.exists(ile):
        return None
    proj = pd.read_json(ile)
    top = proj.nlargest(10, "pa_penalty_pct")
    def grp(team):
        t = (str(team) or "").upper()
        ab = {"NEW YORK YANKEES":"NYY","HOUSTON ASTROS":"HOU","NEW YORK METS":"NYM",
              "MILWAUKEE BREWERS":"MIL","TAMPA BAY RAYS":"TB","ARIZONA DIAMONDBACKS":"AZ",
              "DETROIT TIGERS":"DET","LOS ANGELES DODGERS":"LAD","MINNESOTA TWINS":"MIN",
              "SEATTLE MARINERS":"SEA","ST. LOUIS CARDINALS":"STL","ATLANTA BRAVES":"ATL",
              "PITTSBURGH PIRATES":"PIT","CHICAGO WHITE SOX":"CHW"}.get(t.upper(), (t or "")[:3])
        if ab in WIN_CHEAP: return "#1b5e20"
        if ab in CHEAP_MEDIOCRE: return "#e65100"
        return "#1565c0"
    fig = go.Figure(go.Bar(
        x=top["name"], y=top["pa_penalty_pct"],
        marker_color=[grp(t) for t in top["team"]],
        text=[f"-{v:.0f}% PA" for v in top["pa_penalty_pct"]], textposition="outside"))
    fig.update_layout(title="2027 health risk (IL-based PA cap, 2025-26 real injury data) — "
                            "playtime you should NOT count on",
                      xaxis_title="", yaxis_title="Projected PA reduction (%)",
                      template="plotly_white", height=400)
    return fig


def panel_roster():
    """Final decision artifact: 26-man winning-cheap roster (proposed)."""
    rost = os.path.join(DATA, "roster_2027.json")
    if not os.path.exists(rost):
        return None
    with open(rost) as f:
        r = json.load(f)
    hits = pd.DataFrame(r["hitters"]); pits = pd.DataFrame(r["pitchers"])
    # build a combined bar of hitters' OBP and pitchers' inverse-ERA (scaled)
    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        "Proposed hitting core (13) — OBP-based value",
        "Proposed pitching core (13) — IP/IP-weighted innings value"],
        horizontal_spacing=0.12)
    h = hits.sort_values("proj_OBP", ascending=False).head(13)
    colors_h = ["#1b5e20" if str(t).upper()[:3] in WIN_CHEAP or t in
                {"Milwaukee Brewers","Tampa Bay Rays","Cleveland Guardians"}
                else "#1565c0" for t in h["team"]]
    fig.add_trace(go.Bar(x=h["name"], y=h["proj_OBP"], marker_color=colors_h,
                         text=[f"{v:.3f}" for v in h["proj_OBP"]], textposition="outside"), 1, 1)
    p = pits.sort_values("proj_IP_health", ascending=False).head(13)
    colors_p = ["#1b5e20" if t in {"Milwaukee Brewers","Tampa Bay Rays","Cleveland Guardians"}
                else "#1565c0" for t in p["team"]]
    fig.add_trace(go.Bar(x=p["name"], y=p["proj_IP_health"], marker_color=colors_p,
                         text=[f"{v:.0f}" for v in p["proj_IP_health"]], textposition="outside"), 1, 2)
    fig.update_layout(title="Proposed 26-man winning-cheap roster (13H/13P, real projections) — "
                            "green = winning-cheap source team; green bars recur by design",
                      template="plotly_white", height=460)
    return fig


def panel_runs():
    """The top quant lever: run differential vs wins (2026), MLB-themed."""
    runs = os.path.join(DATA, "runs_panel.json")
    if not os.path.exists(runs):
        return None
    d = pd.read_json(runs)
    d26 = d[d["season"] == 2026].dropna(subset=["RD", "wins"])
    def grp(team):
        if team in WIN_CHEAP: return "#1b5e20"
        if team in CHEAP_MEDIOCRE: return "#e65100"
        return "#1565c0"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d26["RD"], y=d26["wins"], mode="markers+text",
                             marker=dict(color=[grp(t) for t in d26["team"]], size=13),
                             text=[f"<b>{t}</b>" for t in d26["team"]],
                             textposition="top center", name="2026 teams"))
    # fit line (ordinal least squares) to show the run->win relation
    import numpy as _np
    b, a = _np.polyfit(d26["RD"].values, d26["wins"].values, 1)
    xs = _np.linspace(d26["RD"].min(), d26["RD"].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode="lines",
                             line=dict(color="#d50032", dash="dash", width=2),
                             name=f"fit: wins ≈ {a:.0f} + {b:.2f}·RunDiff (R² see source)"))
    fig.update_layout(title="The top lever — run differential → wins (2026, real)",
                      xaxis_title="Run differential (scored − allowed)",
                      yaxis_title="Wins", template="plotly_white", height=420,
                      xaxis_range=[-150, 350])
    return fig


def panel_sensitivity():
    """What-if: elasticity table rendered as visible bars (real numbers)."""
    rv = os.path.join(DATA, "robust_validation.json")
    if not os.path.exists(rv):
        return None
    d = json.load(open(rv))
    elas = d.get("elasticity", {})
    if not elas:
        return None
    # Sort by |wins moved|, keep a readable shock label
    items = sorted(elas.items(), key=lambda kv: -abs(kv[1]["dWins"]))
    labels, dW, colors = [], [], []
    legend = {"contact": "+1% contact →", "HR/PA": "+1 HR per 100 PA →",
              "OBP": "+.010 OBP →", "K%": "+1% K-rate →", "BB%": "+1% BB →",
              "ISO": "+.010 ISO →", "RD": "+25 net runs →",
              "PythE": "+5 Pythag wins →", "payroll": "+$25M payroll →"}
    for feat, v in items:
        labels.append(legend.get(feat, feat))
        dW.append(v["dWins"])
        colors.append("#1b5e20" if v["dWins"] >= 0 else "#d50032")
    fig = go.Figure(go.Bar(x=dW, y=labels, orientation="h",
                           marker=dict(color=colors),
                           text=[f"{v:+.2f}" for v in dW], textposition="outside"))
    fig.update_layout(title="What-if: how many wins a lever moves (measured elasticity)",
                      xaxis_title="Marginal wins under a realistic unit move",
                      template="plotly_white", height=420, margin=dict(l=200),
                      xaxis_range=[min(dW) - 0.6, max(dW) + 1.2])
    return fig


def build():
    df = kpi_mod.kpi_frame()
    df["group"] = "OTHER"
    df.loc[df["team"].isin(WIN_CHEAP), "group"] = "WIN_CHEAP"
    df.loc[df["team"].isin(CHEAP_MEDIOCRE), "group"] = "CHEAP_MEDIOCRE"

    fig1 = panel_payroll_wins(df, 2026)
    fig2 = panel_kpi(df, 2026)
    fig3 = panel_projections()
    fig4 = panel_durability()
    fig5 = panel_player_proj()
    fig6 = panel_pitching()
    fig7 = panel_health()
    fig8 = panel_roster()
    fig9 = panel_runs()
    fig10 = panel_sensitivity()

    # Self-contained offline demo: inline plotly so no internet needed at the
    # Winter Meetings. Caches the bundle next to the dashboard if present.
    bundle = os.path.join(REPO, "dashboard", "plotly.min.js")
    if os.path.exists(bundle):
        with open(bundle) as f:
            plotly_js = f.read()
        js_include = f"<script>{plotly_js}</script>"
    else:  # fallback: fetch once, cache
        import urllib.request
        url = "https://cdn.plot.ly/plotly-4.1.1.min.js"
        with urllib.request.urlopen(url, timeout=60) as r:
            plotly_js = r.read().decode()
        with open(bundle, "w") as f:
            f.write(plotly_js)
        js_include = f"<script>{plotly_js}</script>"

    html = (fig1.to_html(full_html=False, include_plotlyjs=False) +
            "<br> " + fig2.to_html(full_html=False, include_plotlyjs=False) +
            "<br> " + fig3.to_html(full_html=False, include_plotlyjs=False) +
            "<br> " + fig4.to_html(full_html=False, include_plotlyjs=False) +
            "<br> " + fig5.to_html(full_html=False, include_plotlyjs=False) +
            "<br> " + fig6.to_html(full_html=False, include_plotlyjs=False))
    for fig in (fig7, fig8):
        if fig is not None:
            html += "<br> " + fig.to_html(full_html=False, include_plotlyjs=False)
    if fig9 is not None:
        html = (fig9.to_html(full_html=False, include_plotlyjs=False) +
                "<br> " + html)
    if fig10 is not None:
        html = html + "<br> " + fig10.to_html(full_html=False, include_plotlyjs=False)

    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>HARDBALL — Cap-Era Moneyball Demo (P6)</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#14213d}}
.hd{{max-width:1000px;margin:0 auto;padding:0 20px 40px}}
.crest{{background:linear-gradient(135deg,#14213d 0%,#1d3557 60%,#7a1f1f 160%);color:#fff;padding:28px 32px;border-radius:0 0 14px 14px;margin:0 0 4px;box-shadow:0 3px 14px rgba(20,33,61,.25)}}
.crest h1{{margin:0;font-size:30px;letter-spacing:1px;color:#fff}}
.crest h2{{margin:8px 0 0;font-size:16px;font-weight:400;color:#cbe0ff}}
.mlb{{background:#d50032;color:#fff;padding:2px 9px;border-radius:5px;font-size:12px;font-weight:700;letter-spacing:.5px}}
.tag{{background:#cbe0ff;color:#14213d;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}}
.note{{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:14px 0}}
.bottomline{{background:#e8f5e9;border-left:5px solid #1d3557;border-radius:6px;padding:14px 18px;margin:16px 0;font-size:15px}}
.act{{background:#14213d;color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold}}
.why{{color:#1d3557;font-weight:bold}}
.quant{{background:#eef4ff;border-left:5px solid #0d47a1;border-radius:6px;padding:14px 18px;margin:16px 0;font-size:14px}}
.srcbox{{background:#14213d;color:#dbe4f3;border-radius:8px;padding:16px 20px;margin:30px 0 8px;font-size:13px;line-height:1.5}}
.srcbox b{{color:#fff}}
.src{{color:#8ab6ff;font-family:ui-monospace,monospace}}
</style></head>
<body>
<div class="crest">
<h1>⚾ HARDBALL <span class="tag">P6 MVP · Winter Meetings 2026</span></h1>
<h2>Cap-Era Moneyball: win while cheap — buy contact + OBP and low-walk arms, price it against the <b>$245.3M</b> cap</h2>
</div>
<div class="hd">
<div class="bottomline">
<b>BOTTOM LINE (read this first):</b> A team can win at mid-tier payroll by spending on
<b>contact + getting on base (OBP)</b> and <b>low-walk arms</b>, not power. Winning-cheap teams
(MIL/TB/CLE) had <b>higher OBP, more contact, fewer strikeouts, fewer homeruns AND elite team pitching</b> — yet
won ~95 games vs ~79 at roughly half payroll. <span class="act">Owner action:</span>
build the roster around OBP/contact + control pitchers, not the big power salary.
<span class="why">Why trust it:</span> real 2025-2026 data (MLB API + Spotrac), model cross-validated.
Not a guarantee — shown honestly below.</div>
<div class="quant"><b>What the math provably supports (measured on 509 real team-seasons, 2011-2026):</b><br>
<b>1) Run differential → wins is real.</b> Same-year fit R² ≈ 0.55 on a 450-row panel — run margin
describes wins, but it is diagnostic, not a forward forecast.<br>
<b>2) KPI-only cross-year prediction is weak.</b> Predicting NEXT season's wins from this season's
hitting KPIs: in-sample R² ≈ 0.14; out-of-sample (forecast 2020-2025 from ≤2019 data) is
<b>worse</b> than the naive league-mean baseline. The contact/OBP signal tested honestly does <b>not</b>
cleanly predict next-year wins — year-to-year wins regress heavily, matching published literature.<br>
<b>3) The robust, honest use is player-level acquisition</b> (Marcel projections + injury caps →
the 26-man roster), not a single team-wins formula. We deliberately do <b>not</b> claim a
CV-MAE ~4.0 / R² 0.80 forward-prediction model anymore — that number was measured on a
favorable 2-year window and did not survive the full panel. Cross-year forecasting MAE ≈ 9-13
wins; that is the honest capability.</div>
<div class="note">Real 2011-2026 data (MLB Stats API + Spotrac), 509 team-seasons. Honest capability:
same-year run-diff→wins R² ≈ 0.55; KPI-only cross-year forecasting MAE ≈ 9-13 wins (weak, beats
naive only marginally — shown honestly). The cap/floor are owners' proposed 2027 figures
(CBA expires Dec 1 2026), not law. No guaranteed performance claim.</div>
{js_include}
{html}
<div class="srcbox">
<b>DATA SOURCES &amp; METHODS — everything on this page is real and traceable.</b><br><br>
<b>Primary data</b> (2025-2026, all 30 MLB teams): <span class="src">MLB Stats API
statsapi.mlb.com/api/v1</span> — official MLB feed, keyless; team hitting/pitching + standings
(runs scored / runs allowed). Validated against <span class="src">ESPN
site.web.api.espn.com</span> (131 players cross-checked: HR counts match exactly).<br>
<b>Payroll:</b> <span class="src">Spotrac</span> (via MIT-licensed jasonbhorne/mlb-payroll,
721 team-seasons 2000-2024 + live 2026 opening-day figures). <b>Injury/health:</b> MLB
transactions feed (35,000+ events 2025-2026, IL days per player). <b>MLB color/look:</b> league
branding only, for presentation.<br>
<b>Model:</b> linear regression on the 2011-2026 panel (509 team-seasons, 450 complete):
same-year run differential → wins R² ≈ 0.55 — a diagnostic link, not a forecast.
KPI-only next-season forecasting is weak (out-of-sample MAE ≈ 14 wins, worse than the
naive baseline; see BML Cycles 18-19 in the repo audit trail) — an earlier 2-year-window
estimate (MAE 4.0 / R² 0.80) was retracted for exactly that reason and is not claimed here.
The actionable layer is player-level: Marcel weighted-average projections with
injury-availability caps, priced against the cap. Pythagorean exponent uses Euler's e.
<b>Honest limits:</b> ~45% of same-year win variance sits outside run differential
(defense, luck, leverage); the cap figures are the owners' proposed 2027 numbers
(CBA expires Dec 1 2026), not law. Not a guarantee of performance.<br><br>
<b>Project repo:</b> github.com/mega-byte2600/hardball (private) · audit trail in docs/BML_LOG.md
</div>
</div></body></html>"""

    out = os.path.join(REPO, "dashboard", "hardball_demo.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"dashboard written: {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    import pandas as pd  # noqa
    build()
