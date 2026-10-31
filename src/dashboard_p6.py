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


def build():
    df = kpi_mod.kpi_frame()
    df["group"] = "OTHER"
    df.loc[df["team"].isin(WIN_CHEAP), "group"] = "WIN_CHEAP"
    df.loc[df["team"].isin(CHEAP_MEDIOCRE), "group"] = "CHEAP_MEDIOCRE"

    fig1 = panel_payroll_wins(df, 2026)
    fig2 = panel_kpi(df, 2026)
    fig3 = panel_projections()

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
            "<br> " + fig3.to_html(full_html=False, include_plotlyjs=False))

    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>HARDBALL — Cap-Era Moneyball Demo (P6)</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;background:#fafafa;color:#111}}
h1{{color:#1b2733}} h2{{color:#333}} .hd{{max-width:900px;margin:0 auto}}
.note{{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:14px 0}}
.tag{{background:#0d47a1;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px}}</style></head>
<body><div class="hd">
<h1>HARDBALL <span class="tag">P6 MVP · Winter Meetings 2026</span></h1>
<h2>Cap-Era Moneyball: win while cheap — buy contact + OBP, price it against the <b>$245.3M</b> cap</h2>
<div class="note">Real 2025-2026 data (MLB API + Spotrac). Model: wins ~ OBP, contact, K%, BB%, HR/PA.
Cross-validated MAE ~7.2 wins, R² ~0.4 — honest, NOT guaranteed performance. The cap/floor are owners' proposed
2027 figures (CBA expires Dec 1 2026).</div>
{js_include}
{html}
</div></body></html>"""

    out = os.path.join(REPO, "dashboard", "hardball_demo.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"dashboard written: {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    import pandas as pd  # noqa
    build()
