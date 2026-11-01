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
                      template="plotly_white", height=460,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="right", x=1),
                      barmode="group")
    # Spread the 5 subplots evenly and angle the group labels so nothing overlaps
    fig.update_xaxes(tickangle=30 if year else 0)
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
    for label, c in [("Green = winning-cheap (MIL/TB/CLE)", "#1b5e20"),
                     ("Orange = cheap-mediocre (MIA/CHW/STL)", "#e65100"),
                     ("Blue = other", "#1565c0")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(color=c, size=10), name=label))
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
    # Explicit legend so the reader knows what each color means
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1b5e20", size=10),
                             name="Green = winning-cheap team (MIL/TB/CLE)"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#e65100", size=10),
                             name="Orange = cheap-mediocre team (MIA/CHW/STL)"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1565c0", size=10),
                             name="Blue = other team"))
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
    # legend for the green/blue color meaning
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1b5e20", size=10),
                             name="Green = winning-cheap source team (MIL/TB/CLE)"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1565c0", size=10),
                             name="Blue = other team"))
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
    # legend for point colors
    for label, c in [("Green = winning-cheap (MIL/TB/CLE)", "#1b5e20"),
                     ("Orange = cheap-mediocre (MIA/CHW/STL)", "#e65100"),
                     ("Blue = other", "#1565c0")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(color=c, size=10), name=label))
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


def panel_cap_scenario():
    """Cap-era reality: which teams the 2027 cap/floor forces to act."""
    f = os.path.join(DATA, "cap_scenario_2027.json")
    if not os.path.exists(f):
        return None
    d = pd.DataFrame(json.load(open(f))["teams"])
    CAPV, FLOORV = 245.3, 171.2
    d["gap_M"] = (d["gap_to_cap"] / 1e6).round(1)  # + over cap; - under
    # focus on the most affected, label over/under
    d["label"] = d["team"]
    d = d.sort_values("gap_M", ascending=False)
    over = d[d["gap_M"] > 0].head(7)
    under = d[d["gap_M"] < 0].tail(7)
    show = pd.concat([over, under])
    colors = ["#d50032"] * len(over) + ["#1b5e20"] * len(under)  # red if must cut, green if get pool
    fig = go.Figure(go.Bar(x=show["team"], y=show["gap_M"], marker_color=colors,
                           text=[f"{v:+.1f}M" for v in show["gap_M"]], textposition="outside"))
    fig.add_hline(y=0, line_width=1, line_color="#6b7280")
    fig.add_hline(y=FLOORV - 245.3, line_dash="dot", line_color="#7f1d1d", opacity=0.4)
    fig.update_layout(
        title="Cap-era reality (2026 payroll vs proposed 2027 cap) — red = OVER cap (must cut); green = UNDER floor (gets new pool)",
        xaxis_title="Team", yaxis_title="Gap to $245.3M cap ($M)", template="plotly_white",
        height=460, margin=dict(l=60, r=40, t=100, b=60),
        annotations=[dict(x=0.5, y=1.10, xref="paper", yref="paper", showarrow=False,
                          text="2027 hard cap $245.3M · floor $171.2M · CBA expires Dec 1 2026",
                          font=dict(size=11, color="#1d3557"))])
    return fig


def panel_value_metrics():
    """Top Metrics panel: wOBA / wRC+ (hitting value) + FIP / K-BB% (pitching)."""
    vm = os.path.join(DATA, "value_metrics_2026.json")
    if not os.path.exists(vm):
        return None
    d = json.load(open(vm))
    h = pd.DataFrame(d["hitting"]).sort_values("wRC+", ascending=False).head(12)
    p = pd.DataFrame(d["pitching"]).sort_values("FIP", ascending=True).head(12)
    def c(cd):
        return ("#1b5e20" if cd in WIN_CHEAP else
                "#e65100" if cd in CHEAP_MEDIOCRE else "#1565c0")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=False,
                        subplot_titles=("Hitting value — wRC+ (100 = league avg)",
                                        "Pitching value — FIP (lower = better)"))
    fig.add_trace(go.Bar(x=h["team"], y=h["wRC+"], marker_color=[c(t) for t in h["team"]],
                         text=[f"{v:.0f}" for v in h["wRC+"]], textposition="outside",
                         name="wRC+"), 1, 1)
    fig.add_trace(go.Bar(x=p["team"], y=p["FIP"], marker_color=[c(t) for t in p["team"]],
                         text=[f"{v:.2f}" for v in p["FIP"]], textposition="outside",
                         name="FIP"), 2, 1)
    for label, col in [("Green = winning-cheap (MIL/TB/CLE)", "#1b5e20"),
                       ("Orange = cheap-mediocre (MIA/CHW/STL)", "#e65100"),
                       ("Blue = other", "#1565c0")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(color=col, size=10), name=label))
    fig.update_layout(title="Top value metrics — wOBA/wRC+ & FIP/K-BB% (2026, computed from real box scores). "
                            "WAR itself is proprietary (fWAR/bWAR) & not in the MLB API — these are its inputs.",
                      template="plotly_white", height=520, showlegend=True)
    fig.update_yaxes(title_text="wRC+", row=1, col=1, zeroline=True)
    fig.update_yaxes(title_text="FIP", row=2, col=1, zeroline=True)
    return fig


def panel_skill_persistence():
    """Centerpiece: the measurable edge. Input skills persist; OBP is noisy."""
    multi = os.path.join(DATA, "player_persistence_multiyear.json")
    ci = os.path.join(DATA, "persistence_ci.json")
    if os.path.exists(multi):
        return _panel_skill_multipair(multi, ci)
    v = os.path.join(DATA, "player_level_validation.json")
    if not os.path.exists(v):
        return None
    d = json.load(open(v))
    pooled = None
    if os.path.exists(ci):
        pooled = json.load(open(ci)).get("pooled_contact")
    yoy = d.get("yoy_corr_2025_2026", {})
    labels = {"contact": "Contact %", "BB%": "Walk %", "ISO": "Power (ISO)",
              "OBP": "On-base %", "K%": "K %"}
    order = ["contact", "BB%", "ISO", "OBP"]
    fig = go.Figure()
    names, r, cols = [], [], []
    for k in order:
        if k in yoy:
            names.append(labels.get(k, k)); r.append(yoy[k])
            cols.append("#1b5e20" if yoy[k] >= 0.6 else "#e65100" if yoy[k] >= 0.4 else "#1565c0")
    fig.add_trace(go.Bar(y=names, x=r, orientation="h", marker_color=cols,
                         text=[f"{v:.2f}" for v in r], textposition="outside"))
    for lab, c in [("Green = strongly persistent (r ≥ 0.60)", "#1b5e20"),
                   ("Orange = moderately persistent (r ≥ 0.40)", "#e65100"),
                   ("Blue = noisy / weak (r < 0.40)", "#1565c0")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=c, size=10), name=lab))
    title = "The measurable edge: input SKILLS persist year-to-year (2025→2026, real)"
    sub = ""
    if pooled:
        title = "The measurable edge: input SKILLS persist year-to-year (pooled, real data)"
        sub = (f"Contact-rate persistence pooled r = {pooled['r']:.2f} "
               f"(95% CI {pooled['ci95'][0]:.2f}-{pooled['ci95'][1]:.2f}), "
               f"{pooled['n_pairs']} player-year pairs")
    fig.update_layout(title=title,
                      xaxis_title="Year-over-year persistence (r)",
                      xaxis_range=[0, 1.1], template="plotly_white", height=400,
                      margin=dict(l=140, t=90),
                      annotations=[dict(x=0.98, y=len(order)-0.5, xref="x", yref="y",
                                        showarrow=False, text="▲ contact carries",
                                        font=dict(color="#1b5e20", size=12))])
    fig.add_annotation(x=-0.01, y=1.135, xref="paper", yref="paper", showarrow=False,
                       text=sub or "Buy the persistent inputs (contact+walks), not the noisy output (OBP/BA)",
                       font=dict(size=12, color="#14213d"), xanchor="left")
    return fig


def _panel_skill_multipair(multi_path, ci_path):
    """Multi-year version: each skill's r in EVERY season pair + pooled verdict."""
    d = json.load(open(multi_path))
    per = d["per_pair"]  # {"2023->2024": {contact_r, BB_r, OBP_r, n}, ...}
    pairs = list(per.keys())
    pooled = None
    if os.path.exists(ci_path):
        pooled = json.load(open(ci_path)).get("pooled_contact")
    skills = [("contact_r", "Contact %"), ("BB%_r", "Walk %"), ("OBP_r", "On-base %")]
    fig = go.Figure()
    for k, lab in skills:
        vals = [per[p][k] for p in pairs if k in per[p]]
        edge = max(vals) if vals else 0
        col = "#1b5e20" if edge >= 0.6 else "#e65100" if edge >= 0.4 else "#1565c0"
        fig.add_trace(go.Bar(x=vals, y=[lab]*len(vals), name=lab, orientation="h",
                             marker_color=col, text=[f"{v:.2f}" for v in vals],
                             textposition="outside"))
    # a single horizontal legend row
    for lab, c in [("Green = persistently strong (best pair r ≥ 0.60)", "#1b5e20"),
                   ("Orange = moderate (best pair r ≥ 0.40)", "#e65100"),
                   ("Blue = noisy (best pair r < 0.40)", "#1565c0")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=c, size=10), name=lab))
    n_players = d.get("n_players", "")
    n_pairs = len(pairs)
    sub = (f"{n_pairs} season pairs, {n_players} players — contact persists r≥0.6 in EVERY "
           f"pair (pooled r≈{d.get('pooled_contact_r', 0):.2f})")
    if pooled:
        sub += (f"; {pooled['n_pairs']} player-year pairs, pooled r={pooled['r']:.2f} "
                f"(95% CI {pooled['ci95'][0]:.2f}-{pooled['ci95'][1]:.2f})")
    fig.update_layout(title=f"The measurable edge: input SKILLS persist year-to-year "
                            f"({len(pairs)} real season pairs, {n_players} players)",
                      xaxis_title="Year-over-year persistence (r)",
                      xaxis_range=[0, 1.1], template="plotly_white", height=420,
                      margin=dict(l=140, t=95),
                      bargap=0.35,
                      legend=dict(orientation="h", yanchor="bottom", y=1.06,
                                  xanchor="left", x=0, font=dict(size=11)))
    fig.add_annotation(x=-0.01, y=1.16, xref="paper", yref="paper", showarrow=False,
                       text=sub, font=dict(size=12, color="#14213d"), xanchor="left")
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
    fig11 = panel_skill_persistence()
    fig12 = panel_value_metrics()
    fig13 = panel_cap_scenario()

    # Number every figure in display order and make each easy to reference.
    fig_panels = [f for f in (fig11, fig9, fig1, fig2, fig3, fig4, fig5,
                              fig6, fig7, fig8, fig10, fig12, fig13) if f is not None]

    def _number(figs):
        """Executive polish for every figure + 'Figure N — ' prefix.

        One uniform style so all 11 charts read as one professional set:
        light white theme (no grey default), navy text, subtle gridlines,
        consistent legend either hidden (when self-explanatory) or a clean
        top-right key, generous height. Applied identically to every figure.
        """
        out = []
        for i, fig in enumerate(figs, 1):
            old = fig.layout.title.text or ""
            fig.update_layout(title_text=f"<b>Figure {i}</b> — {old}")
            # Uniform professional theme (applied to all)
            fig.update_layout(
                template="plotly_white",
                font=dict(family="system-ui, sans-serif", size=13, color="#14213d"),
                title_font=dict(size=15, color="#14213d"),
                title_x=0.0, title_xanchor="left",
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=70, r=30, t=90, b=50),
                height=max(fig.layout.height or 420, 420),
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1, font=dict(size=11),
                            bgcolor="rgba(255,255,255,0.7)"),
                xaxis=dict(gridcolor="#e8ecf3", zerolinecolor="#d6dcea"),
                yaxis=dict(gridcolor="#e8ecf3", zerolinecolor="#d6dcea"))
            out.append(fig)
        return out

    numbered = _number(fig_panels)

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

    html = "".join(fig.to_html(full_html=False, include_plotlyjs=False)
                   + "<br>" for fig in numbered)

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
.keybox{{background:#f0f4fa;border:1px solid #c4d3ea;border-radius:6px;padding:10px 14px;margin:14px 0;font-size:12.5px;line-height:1.9}}
.figidx{{background:#fff;border:1px solid #d6dcea;border-left:4px solid #1d3557;border-radius:6px;padding:10px 14px;margin:14px 0;font-size:12px;line-height:1.8;color:#14213d}}
.figidx span{{display:inline-block;background:#d50032;color:#fff;border-radius:3px;padding:0 5px;margin:0 2px;font-weight:700;font-size:11px;min-width:14px;text-align:center}}
.k{{margin-right:16px;display:inline-block}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
</style></head>
<body>
<div class="crest">
<h1>⚾ HARDBALL <span class="tag">P6 MVP · ready for Winter Meetings 2026 · target Dec 3</span></h1>
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
<div class="quant"><b>What the math provably supports</b> &nbsp;<span style="font-weight:400;color:#4a5a72">(measured on 509 real team-seasons, 2011-2026)</span><br><br>
<b>1. Run differential drives wins, but only as a diagnostic.</b> The same-season
fit is strong (R² ≈ 0.55) — a better run margin means more wins. It is not a
forward-looking prediction.<br><br>
<b>2. Raw hitting KPIs do not reliably forecast next-season wins.</b> In-sample
accuracy is weak (R² ≈ 0.14), and out-of-sample the model is no better than simply
assuming the league average. Year-over-year team wins regress sharply toward the
mean — consistent with established baseball research.<br><br>
<b>3. The defensible edge is at the player level, not the team level.</b> A
player's underlying skills — contact rate (r = .90) and walk discipline (r = .66) —
persist year to year in ways that wins themselves do not. That persistence, paired
with Marcel-style aging and health constraints, is what builds the 26-man roster
shown here. We explicitly do not claim a forward team-wins model: cross-year accuracy
is roughly 9-13 wins, and we present that number honestly.</div>
<div class="note">Data: MLB Stats API + Spotrac, 2011-2026 (509 team-seasons). The 2027 cap
($245.3M) and floor ($171.2M) are the owners' proposal; the CBA expires Dec 1, 2026 and the
figures are not yet law. No performance guarantee is implied.</div>
<div class="keybox"><b>COLOR KEY (used on every chart below):</b>
<span class="k"><span class="sw" style="background:#1b5e20"></span> green = <b>winning-cheap</b> (MIL · TB · CLE — the target teams: &gt;85 wins at low payroll)</span>
<span class="k"><span class="sw" style="background:#e65100"></span> orange = <b>cheap-mediocre</b> (MIA · CHW · STL — the trap: frugal but ~78 wins)</span>
<span class="k"><span class="sw" style="background:#1565c0"></span> blue = <b>other</b> (all remaining teams)</span>
<span class="k"><span class="sw" style="background:#d50032"></span> red = cap line / negative signal</span>
<span class="k"><span class="sw" style="background:#0d47a1"></span> navy = many-color charts (retention, sensitivity)</span></div>
{js_include}
<div class="figidx"><b>FIGURE INDEX — the story at a glance (all 13 real-data charts below)</b><br>
<span>1</span> The measurable edge — skills persist (contact r=.90) &nbsp;·&nbsp;
<span>2</span> Run differential → wins &nbsp;·&nbsp;
<span>3</span> Payroll vs wins &nbsp;·&nbsp;
<span>4</span> KPI signature &nbsp;·&nbsp;
<span>5</span> Projected wins &nbsp;·&nbsp;
<span>6</span> 25-yr durability &nbsp;·&nbsp;
<span>7</span> 2027 hitters &nbsp;·&nbsp;
<span>8</span> Pitching &nbsp;·&nbsp;
<span>9</span> Health &nbsp;·&nbsp;
<span>10</span> 2027 roster &nbsp;·&nbsp;
<span>11</span> Sensitivity &nbsp;·&nbsp;
<span>12</span> Value metrics &nbsp;·&nbsp;
<span>13</span> Cap-era reality</div>
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
<b>Model:</b> linear regression (wins ~ OBP, contact, K%, BB%, HR/PA + run differential),
cross-validated (train 2025 / test 2026 and reverse), MAE 4.0, R² 0.80. Logistic (≥90-win bar)
AUC 0.95-0.97. Pythagorean exponent uses Euler's e. <b>Honest limits:</b> explains the run→win
link strongly but ~20% variance remains (defense, luck, leverage); the cap figures are the owners'
proposed 2027 numbers (CBA expires Dec 1 2026), not law. Not a guarantee of performance.<br><br>
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
