"""P6: HARDBALL demo dashboard (Plotly HTML) — INTEGRATED build.

Twenty figures on real data: the main lane's 13 (payroll/KPI/
projections/durability/players/pitching/health/roster/runs/
sensitivity + skill persistence, value metrics, cap scenario)
plus the CarpeData/Boardroom 7 (Steamer benchmark, Savant trait
check, MiLB pipeline, FA shopping list, animated 16-season
payroll film, pick-your-team explorer, budget-scenario rosters),
presented in eight story sections with stat cards. Builds from a
clean clone OFFLINE from committed snapshots (audit G1).
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
    """Copycat-league KPI signature. Clean: one shared legend, no repeat labels."""
    d = df[df["season"] == year].dropna(subset=["OBP", "contact", "K%", "BB%", "HR/PA"])
    grp = d.groupby("group")[["OBP", "contact", "K%", "BB%", "HR/PA"]].mean()
    metrics = ["OBP", "BB%", "HR/PA", "contact", "K%"]
    labels = {"OBP": "OBP", "BB%": "BB%", "HR/PA": "HR / 1000 PA",
              "contact": "Contact %", "K%": "K%"}
    colors = {"WIN_CHEAP": "#1b5e20", "CHEAP_MEDIOCRE": "#e65100", "OTHER": "#1565c0"}
    gname = {"WIN_CHEAP": "Winning-cheap (MIL·TB·CLE)", "CHEAP_MEDIOCRE": "Cheap-mediocre",
             "OTHER": "Other"}
    fig = make_subplots(rows=1, cols=len(metrics),
                        subplot_titles=[labels[m] for m in metrics],
                        horizontal_spacing=0.10)
    for i, m in enumerate(metrics, start=1):
        for g in ["WIN_CHEAP", "CHEAP_MEDIOCRE", "OTHER"]:
            fig.add_trace(go.Bar(x=[gname[g]], y=[grp.loc[g, m]],
                                 marker_color=colors[g], name=gname[g],
                                 showlegend=(i == 1),
                                 text=[f"{grp.loc[g, m]:.3f}" if m in ("OBP",)
                                       else f"{grp.loc[g, m]:.1f}"],
                                 textposition="outside",
                                 hovertemplate=f"{labels[m]}: %{{y:.3f}}<extra>{gname[g]}</extra>"),
                          row=1, col=i)
    fig.update_layout(title=f"{year} — Copycat-league KPI signature (winning-cheap leads contact & OBP)",
                      template="plotly_white", height=440,
                      barmode="group",
                      margin=dict(l=40, r=20, t=64, b=96))
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef1f6")
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
    labels = [f"Q{i+1}" for i in range(4)]
    qlabs = [f"Q{i+1} (${agg['lab'][g]/1e6:.0f}M)" for i, g in enumerate([0,1,2,3])]
    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        "Wins per $100M (payroll quartile, 2000-2024)",
        "Wins by payroll quartile (2000-2024)"],
        horizontal_spacing=0.18)
    colors = ["#2e7d32", "#8bc34a", "#ef6c00", "#1565c0"]
    fig.add_trace(go.Bar(x=labels, y=agg["win100"].values, marker_color=colors,
                         text=[f"{v:.0f}" for v in agg["win100"]], textposition="outside",
                         name="Wins per $100M",
                         hovertemplate="%{x}<br>" + "avg payroll %{customdata}<extra></extra>",
                         customdata=qlabs), 1, 1)
    fig.add_trace(go.Bar(x=labels, y=agg["wins"].values, marker_color=colors,
                         text=[f"{v:.0f}" for v in agg["wins"]], textposition="outside",
                         name="Wins",
                         hovertemplate="%{x}<br>" + "avg payroll %{customdata}<extra></extra>",
                         customdata=qlabs), 1, 2)
    fig.update_layout(title="25-year proof (2000-2024, 721 team-seasons): efficiency is durable — "
                             "but cheap wins per $, not wins (winning-cheap = both)",
                      template="plotly_white", height=420,
                      margin=dict(l=50, r=20, t=64, b=96))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef1f6")
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
      "Milwaukee Brewers":"MIL","Tampa Bay Rays":"TB","Arizona Diamondbacks":"ARI",
      "Detroit Tigers":"DET","Los Angeles Dodgers":"LAD","Cleveland Guardians":"CLE",
      "Miami Marlins":"MIA","Chicago White Sox":"CHW","St. Louis Cardinals":"STL",
      "Texas Rangers":"TEX","Seattle Mariners":"SEA","San Francisco Giants":"SF",
      "Boston Red Sox":"BOS","Philadelphia Phillies":"PHI","Atlanta Braves":"ATL",
      "San Diego Padres":"SD","Toronto Blue Jays":"TOR","Minnesota Twins":"MIN",
      "Baltimore Orioles":"BAL","Los Angeles Angels":"LAA","Chicago Cubs":"CHC",
      "Cincinnati Reds":"CIN","Colorado Rockies":"COL","Kansas City Royals":"KC",
      "Pittsburgh Pirates":"PIT","Washington Nationals":"WSH","Oakland Athletics":"ATH"}
    lake = os.path.join(DATA, "mlb_lake.db")
    if not os.path.exists(lake):
        return None  # lake is a local build artifact (gitignored); a clean
        # clone omits this panel instead of crashing (audit G1 class)
    con = sqlite3.connect(lake)
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
    # HORIZONTAL bars so player names stack cleanly (vertical overlapped before)
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Proposed hitting core (13) — projected OBP",
                                        "Proposed pitching core (13) — health-weighted innings"],
                        horizontal_spacing=0.30)
    h = hits.sort_values("proj_OBP", ascending=False).head(13)
    colors_h = ["#1b5e20" if str(t).upper()[:3] in WIN_CHEAP or t in
                {"Milwaukee Brewers","Tampa Bay Rays","Cleveland Guardians"}
                else "#1565c0" for t in h["team"]]
    fig.add_trace(go.Bar(y=h["name"], x=h["proj_OBP"], orientation="h",
                         marker_color=colors_h, name="Projected OBP",
                         text=[f"{v:.3f}" for v in h["proj_OBP"]], textposition="inside",
                         insidetextanchor="end"), 1, 1)
    p = pits.sort_values("proj_IP_health", ascending=False).head(13)
    colors_p = ["#1b5e20" if t in {"Milwaukee Brewers","Tampa Bay Rays","Cleveland Guardians"}
                else "#1565c0" for t in p["team"]]
    fig.add_trace(go.Bar(y=p["name"], x=p["proj_IP_health"], orientation="h",
                         marker_color=colors_p, name="Projected IP",
                         text=[f"{v:.0f}" for v in p["proj_IP_health"]], textposition="inside",
                         insidetextanchor="end"), 1, 2)
    fig.update_layout(title="Proposed 26-man winning-cheap roster (13H/13P, real projections) — "
                            "green = winning-cheap source team; blue = other",
                      template="plotly_white", height=620,
                      barmode="overlay", bargap=0.15,
                      margin=dict(l=120, r=30, t=64, b=96))
    fig.update_xaxes(showgrid=True, gridcolor="#eef1f6")
    fig.update_yaxes(showgrid=False, automargin=True)
    # legend for the green/blue color meaning
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1b5e20", size=10),
                             name="Green = winning-cheap source team (MIL/TB/CLE)", showlegend=True))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(color="#1565c0", size=10),
                             name="Blue = other team", showlegend=True))
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
    # Clean: markers only, team names on hover (labels overlapped before)
    for gname, sel in [("Winning-cheap (MIL·TB·CLE)", d26["team"].isin(WIN_CHEAP)),
                       ("Cheap-mediocre (MIA·CHW·STL)", d26["team"].isin(CHEAP_MEDIOCRE)),
                       ("Other", ~d26["team"].isin(WIN_CHEAP | CHEAP_MEDIOCRE))]:
        sub = d26[sel]
        fig.add_trace(go.Scatter(
            x=sub["RD"], y=sub["wins"], mode="markers", name=gname,
            marker=dict(color=[grp(t) for t in sub["team"]], size=13, line=dict(color="#fff", width=1)),
            text=[f"<b>{t}</b> — {rd:+.0f} RD, {w} wins" for t, rd, w in
                  zip(sub["team"], sub["RD"], sub["wins"])],
            hovertemplate="%{text}<extra></extra>"))
    # fit line (ordinal least squares) to show the run->win relation
    import numpy as _np
    b, a = _np.polyfit(d26["RD"].values, d26["wins"].values, 1)
    xs = _np.linspace(d26["RD"].min(), d26["RD"].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode="lines",
                             line=dict(color="#d50032", dash="dash", width=2),
                             name=f"fit: wins ≈ {a:.0f} + {b:.2f}·RunDiff (R² see source)"))
    fig.update_layout(title="The top lever — run differential → wins (2026, real); hover any dot for the team",
                      xaxis_title="Run differential (scored − allowed)",
                      yaxis_title="Wins", template="plotly_white", height=440,
                      xaxis_range=[-150, 350],
                      margin=dict(l=60, r=30, t=64, b=96))
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
        title="Cap-era reality (2026 payroll vs proposed 2027 cap) — red = OVER cap; green = UNDER floor",
        xaxis_title="Team", yaxis_title="Gap to $245.3M cap ($M)", template="plotly_white",
        height=460, margin=dict(l=60, r=40, t=64, b=96),
        annotations=[dict(x=0.5, y=-0.45, xref="paper", yref="paper", showarrow=False,
                          text="2027 hard cap $245.3M · floor $171.2M · CBA expires Dec 1, 2026",
                          font=dict(size=11, color="#4a5a72"))])
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
    # HORIZONTAL bars: team codes stack cleanly, no vertical-name collision
    fig = make_subplots(rows=2, cols=1, shared_xaxes=False,
                        subplot_titles=("Hitting value — wRC+ (100 = league avg)",
                                        "Pitching value — FIP (lower = better)"),
                        vertical_spacing=0.16)
    fig.add_trace(go.Bar(y=h["team"], x=h["wRC+"], orientation="h",
                         marker_color=[c(t) for t in h["team"]],
                         text=[f"{v:.0f}" for v in h["wRC+"]], textposition="outside",
                         name="wRC+"), 1, 1)
    fig.add_trace(go.Bar(y=p["team"], x=p["FIP"], orientation="h",
                         marker_color=[c(t) for t in p["team"]],
                         text=[f"{v:.2f}" for v in p["FIP"]], textposition="outside",
                         name="FIP"), 2, 1)
    fig.update_layout(title="Top value metrics — wOBA/wRC+ & FIP/K-BB% (2026; WAR is proprietary "
                            "(fWAR/bWAR) & absent from the MLB API — these are its reproducible inputs)",
                      template="plotly_white", height=640, showlegend=True,
                      margin=dict(l=60, r=40, t=64, b=96))
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(showgrid=True, gridcolor="#eef1f6", zeroline=True, zerolinecolor="#d7dde8")
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
    title = "The measurable edge: input SKILLS persist year-to-year (2025→2026, real)"
    sub = ""
    if pooled:
        title = "The measurable edge: input SKILLS persist year-to-year (pooled, real data)"
        sub = (f"Contact-rate persistence pooled r = {pooled['r']:.2f} "
               f"(95% CI {pooled['ci95'][0]:.2f}-{pooled['ci95'][1]:.2f}), "
               f"{pooled['n_pairs']} player-year pairs")
    fig.update_layout(title=title,
                      xaxis_title="Year-over-year persistence (r)",
                      xaxis_range=[0, 1.1], template="plotly_white", height=380,
                      margin=dict(l=140, t=50, b=104),
                      annotations=[
                          dict(x=0.98, y=len(order)-0.5, xref="x", yref="y",
                               showarrow=False, text="▲ contact carries",
                               font=dict(color="#1b5e20", size=11)),
                          # caption BELOW the chart (never collides with title)
                          dict(x=0.02, y=-0.55, xref="paper", yref="paper",
                               showarrow=False,
                               text=sub or "Buy the persistent inputs (contact+walks), "
                                           "not the noisy output (OBP/BA)",
                               font=dict(size=11, color="#4a5a72"), xanchor="left")])
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
                             textposition="outside", showlegend=False))
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
                      xaxis_range=[0, 1.1], template="plotly_white", height=400,
                      margin=dict(l=140, t=50, b=104),
                      bargap=0.35,
                      # caption BELOW the chart (global legend sits under that)
                      annotations=[dict(x=0.02, y=-0.62, xref="paper", yref="paper",
                                        showarrow=False, text=sub,
                                        font=dict(size=11, color="#4a5a72"), xanchor="left")])
    return fig


def panel_benchmark():
    """CarpeData: our Marcel vs FanGraphs Steamer 2027 (Cycle 22).

    Paired by MLBAM player_id == xMLBAMID only. Stats box comes from
    data/fg_benchmark_2027.json so the panel can never drift from the
    measured benchmark."""
    pj = os.path.join(DATA, "projections_2027.json")
    sj = os.path.join(DATA, "fg_steamer_2027_bat.json")
    bj = os.path.join(DATA, "fg_benchmark_2027.json")
    if not all(os.path.exists(p) for p in (pj, sj, bj)):
        return None
    proj = {r["player_id"]: r for r in json.load(open(pj))}
    bench = json.load(open(bj))
    xs, ys, names = [], [], []
    for r in json.load(open(sj)):
        mid = r.get("xMLBAMID")
        if mid in proj and r.get("OBP") is not None:
            xs.append(r["OBP"])
            ys.append(proj[mid]["proj_OBP"])
            names.append(proj[mid]["name"])
    if not xs:
        return None
    h, p = bench["hitters"], bench["pitchers"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0.26, 0.46], y=[0.26, 0.46], mode="lines",
                             line=dict(dash="dash", color="gray"),
                             name="Perfect agreement"))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", name="2027 hitters",
        marker=dict(color="#1d3557", size=8, opacity=0.75),
        text=names, hovertemplate="%{text}<br>Steamer OBP %{x:.3f}<br>Marcel OBP %{y:.3f}<extra></extra>"))
    fig.update_layout(
        title=(f"The benchmark: our Marcel vs FanGraphs Steamer 2027 — OBP r = "
               f"{h['obp']['pearson_r']}, mean |diff| {h['obp']['mean_abs_diff']}, "
               f"top-25 overlap {h['top25_obp_overlap']['overlap_n']}/25<br>"
               f"<sub>Pitchers run optimistic vs Steamer (ERA bias "
               f"{p['era']['mean_signed_diff_marcel_minus_steamer']:+.2f}) — flagged, not hidden. "
               f"Agreement stats, not accuracy: no 2027 outcomes exist yet. Source: FanGraphs API, pulled 2026-10-31.</sub>"),
        xaxis_title="Steamer projected OBP", yaxis_title="Our Marcel projected OBP",
        template="plotly_white", height=540)
    return fig

def panel_savant():
    """CarpeData: Savant trait stability vs incremental value (Cycle 20)."""
    tj = os.path.join(DATA, "savant_test.json")
    if not os.path.exists(tj):
        return None
    t = json.load(open(tj))
    stab = t.get("q2_trait_stability", {})
    labels = [("avg bat speed", "bat_speed"), ("EV50 (batted-ball quality)", "ev50"),
              ("barrel %", "barrel_pct"), ("squared-up rate", "squared_up"),
              ("actual OBP (outcome)", "outcome_OBP"), ("actual SLG (outcome)", "outcome_SLG")]
    names, vals, colors = [], [], []
    for label, key in labels:
        if key in stab:
            names.append(label)
            vals.append(stab[key]["mean_r"])
            colors.append("#8ab6ff" if key.startswith("outcome") else "#1d3557")
    if not vals:
        return None
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker=dict(color=colors),
        text=[f"r = {v:.2f}" for v in vals], textposition="outside"))
    fig.update_layout(
        title=("Savant traits are rock-stable year-to-year (dark) — far more than outcomes (light)<br>"
               "<sub>But Cycle 20 tested them honestly: adding bat speed / barrels / xwOBA luck to Marcel made "
               "out-of-sample projections WORSE. Marcel's outcome history already prices the traits — so Savant "
               "is shown here as diagnostics, not sold as a projection input. Source: Baseball Savant, 2024-2026.</sub>"),
        xaxis_title="Year-to-year correlation (player level)", xaxis_range=[0, 1.12],
        template="plotly_white", height=430, margin=dict(l=210))
    return fig

def panel_pipeline():
    """CarpeData: MiLB upper-minors pipeline index by org (Cycle 23)."""
    pj = os.path.join(DATA, "pipeline_2026.json")
    if not os.path.exists(pj):
        return None
    orgs = json.load(open(pj)).get("orgs", [])
    if not orgs:
        return None
    orgs = sorted(orgs, key=lambda o: o["index_avg100"])
    names = [f"{o['org_abbr']} — {o['n_hitters']}H / {o['n_pitchers']}P" for o in orgs]
    vals = [o["index_avg100"] for o in orgs]
    colors = ["green" if o["org_abbr"] in WIN_CHEAP else
              "orange" if o["org_abbr"] in CHEAP_MEDIOCRE else "steelblue" for o in orgs]
    hover = [f"{o['org_name']}<br>index {o['index_avg100']} (league avg = 100)<br>"
             f"under-26 AAA/AA: {o['n_hitters']} hitters (wtd OPS {o['wtd_ops']}), "
             f"{o['n_pitchers']} pitchers (wtd ERA {o['wtd_era']})<br>"
             f"top hitter: {o['top_hitter']['name']} · top pitcher: {o['top_pitcher']['name']}"
             for o in orgs]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker=dict(color=colors),
        text=[f"{v:.0f}" for v in vals], textposition="outside",
        hovertext=hover, hoverinfo="text"))
    fig.add_vline(x=100, line_dash="dash", line_color="red",
                  annotation_text="League average = 100")
    fig.update_layout(
        title=("The pipeline behind winning-cheap: under-26 upper-minors depth, 2026 (Cycle 23)<br>"
               "<sub>Qualified AAA/AA hitters (≥150 PA) and pitchers (≥40 IP), age from real birthdates, "
               "volume × quality vs league. Green = winning-cheap orgs. Upper minors only — near-MLB depth, "
               "not total farm quality. Source: MLB Stats API minor-league endpoints.</sub>"),
        xaxis_title="Pipeline index (average org = 100)",
        template="plotly_white", height=640, margin=dict(l=170))
    return fig

def panel_shopping():
    """Cycle 25: the 2027 free-agent shopping list — Steamer WAR vs the
    prior contract's AAV (a last-price anchor, never a predicted price)."""
    fj = os.path.join(DATA, "fa_shopping_2027.json")
    if not os.path.exists(fj):
        return None
    d = json.load(open(fj))
    top = d.get("top25_by_war", [])[:15]
    if not top:
        return None
    top = sorted(top, key=lambda r: r["steamer_war"])
    names = [f"{r['name']} ({r['pos']}, {r['prev_team']})" for r in top]
    vals = [r["steamer_war"] for r in top]
    colors = ["green" if r["fits_indiv_max_at_prior_aav"] else "#d50032" for r in top]
    labels = [(f"{r['steamer_war']:.1f} WAR · prior AAV ${r['prev_aav']/1e6:.1f}M"
               if r["prev_aav"] else f"{r['steamer_war']:.1f} WAR") for r in top]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker=dict(color=colors),
        text=labels, textposition="outside"))
    best = d.get("top15_value_war_per_10m", [])
    best_txt = "; ".join(f"{r['name']} {r['war_per_10m_prior_aav']}" for r in best[:3])
    fig.update_layout(
        title=("The shopping list: top 2027 free agents by projected WAR (Cycle 25)<br>"
               f"<sub>Green = prior AAV fits the 15% individual max ($36.8M) at last price. Prior AAV is an anchor, "
               f"not a predicted 2027 price. Best value (WAR per $10M of prior AAV): {best_txt}. "
               f"Sources: Spotrac FA class + 2026 salaries (24/30 team pages pulled; 6 rate-limited, logged), "
               f"FanGraphs Steamer WAR.</sub>"),
        xaxis_title="Steamer projected 2027 WAR",
        template="plotly_white", height=560, margin=dict(l=230),
        xaxis_range=[0, max(vals) * 1.45])
    return fig

def panel_animation():
    """Cycle 26: 16 seasons of payroll vs wins, animated. Press play —
    the cap era arrives and the gold dots (MIL/TB/CLE) never move."""
    p = os.path.join(DATA, "panel_2011_2026.csv")
    if not os.path.exists(p):
        return None
    import pandas as pd
    d = pd.read_csv(p)
    for c in ("payroll", "wins"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["payroll", "wins"])
    d["payroll_m"] = d["payroll"] / 1e6
    d["eff"] = d["wins"] / d["payroll_m"] * 100  # wins per $100M

    def color(r):
        if r["team"] in ("MIL", "TB", "CLE"):
            return "#c9a227"
        if r["payroll_m"] > 260:
            return "#d50032"
        return "#14213d"

    seasons = sorted(d["season"].unique())
    frames, base = [], None
    for s in seasons:
        sub = d[d["season"] == s]
        tr = go.Scatter(
            x=sub["payroll_m"], y=sub["wins"], mode="markers+text",
            text=sub["team"], textposition="top center",
            marker=dict(size=(sub["eff"] * 9).clip(6, 30),
                        color=[color(r) for _, r in sub.iterrows()],
                        opacity=0.82, line=dict(width=1, color="white")),
            hovertemplate="%{text}: %{y} wins on $%{x:.0f}M<extra></extra>",
            showlegend=False)
        if base is None:
            base = tr
        frames.append(go.Frame(data=[tr], name=str(s)))
    fig = go.Figure(data=[base], frames=frames)
    fig.update_layout(
        title=("PRESS PLAY: 16 seasons of payroll vs wins (2011–2026)<br>"
               "<sub>Bubble size = wins per $100M. Gold = the winning-cheap three (MIL/TB/CLE); "
               "red = $260M+ payrolls. The gold barely moves — that is the whole thesis in motion. "
               "Source: MLB Stats API panel + Spotrac payrolls (data/panel_2011_2026.csv).</sub>"),
        xaxis=dict(title="Team payroll ($M)", range=[0, 370]),
        yaxis=dict(title="Wins", range=[38, 118]),
        template="plotly_white", height=600,
        updatemenus=[dict(type="buttons", direction="left", x=0.0, y=-0.14,
                          buttons=[dict(label="▶ Play", method="animate",
                                        args=[None, dict(frame=dict(duration=850, redraw=True),
                                                         fromcurrent=True)]),
                                   dict(label="❚❚ Pause", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                            mode="immediate")])])],
        sliders=[dict(steps=[dict(method="animate", label=str(s),
                                  args=[[str(s)], dict(frame=dict(duration=0, redraw=True),
                                                       mode="immediate")])
                              for s in seasons],
                      x=0.08, len=0.9, y=-0.14,
                      currentvalue=dict(prefix="Season: "))])
    return fig

def panel_team_explorer():
    """Cycle 26: pick your team — its 2026 signature vs the winning-cheap
    profile, with payroll, cap headroom, and pipeline rank."""
    fj = os.path.join(DATA, "team_explorer.json")
    if not os.path.exists(fj):
        return None
    d = json.load(open(fj))
    raw_axes = ["OBP", "contact", "K%", "BB%", "HR/PA_raw"]
    labels = d["metadata"]["axes"]
    cheap = d["metadata"]["winning_cheap_idx"]
    traces, buttons = [], []
    n = len(d["teams"])
    for i, t in enumerate(d["teams"]):
        vals = [t["signature_idx"][c] for c in raw_axes]
        vals.append(vals[0])
        traces.append(go.Scatterpolar(
            r=vals, theta=labels + [labels[0]], fill="toself",
            name=t["team"], visible=(i == 0),
            line=dict(color="#14213d", width=2),
            fillcolor="rgba(20,33,61,0.18)"))
    cheap_vals = [cheap[l] for l in labels]
    cheap_vals.append(cheap_vals[0])
    traces.append(go.Scatterpolar(
        r=cheap_vals, theta=labels + [labels[0]], name="Winning-cheap profile",
        line=dict(color="#c9a227", width=3), fill="toself",
        fillcolor="rgba(201,162,39,0.13)"))
    traces.append(go.Scatterpolar(
        r=[100] * 6, theta=labels + [labels[0]], name="League = 100",
        line=dict(color="#9aa3b2", width=1, dash="dot")))
    for i, t in enumerate(d["teams"]):
        vis = [j == i for j in range(n)] + [True, True]
        title = (f"{t['team']} — {t['wins']} wins · payroll ${t['payroll']/1e6:.0f}M · "
                 f"cap headroom ${t['cap_headroom_m']:.0f}M · pipeline #{t['pipeline_rank']} "
                 f"(top prospect: {t['top_prospect']})<br>"
                 "<sub>Signature indexed to league = 100; higher = more winning-cheap-like on every axis "
                 "(K% and HR rate inverted). Gold = MIL/TB/CLE average profile. Sources: MLB Stats API 2026 KPIs, "
                 "Spotrac payroll, Cycle 23 pipeline index. Pick your team:</sub>")
        buttons.append(dict(label=t["team"], method="update",
                            args=[{"visible": vis}, {"title": {"text": title}}]))
    t0 = d["teams"][0]
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=f"{t0['team']} — pick your team<br><sub>Use the dropdown: every club's 2026 signature vs the winning-cheap profile.</sub>",
        polar=dict(radialaxis=dict(visible=True, range=[55, 135])),
        updatemenus=[dict(buttons=buttons, direction="down", x=0.0, y=1.12,
                          showactive=True, active=0)],
        template="plotly_white", height=560,
        legend=dict(orientation="h", y=-0.08))
    return fig

def panel_scenarios():
    """Cycle 26: what does the money buy? Full 26-man rosters built from
    the real FA class at the floor, the middle, and the cap."""
    fj = os.path.join(DATA, "wow_scenarios.json")
    if not os.path.exists(fj):
        return None
    d = json.load(open(fj))
    traces, buttons = [], []
    for i, s in enumerate(d["scenarios"]):
        r = s["roster"]
        traces.append(go.Table(
            header=dict(values=["Pos", "Player", "From", "Steamer WAR", "Prior AAV"],
                        fill_color="#14213d", font=dict(color="white", size=12),
                        align="left"),
            cells=dict(values=[[x["pos"] for x in r], [x["name"] for x in r],
                               [x["prev_team"] for x in r],
                               [x["war"] for x in r],
                               [f"${x['prev_aav']/1e6:.1f}M" for x in r]],
                       fill_color="rgba(244,241,234,0.6)", align="left",
                       font=dict(size=11.5), height=19),
            visible=(i == 0)))
        title = (f"What does the money buy? {s['label']}: {s['total_war']} WAR for "
                 f"${s['spend']/1e6:.1f}M<br>"
                 "<sub>A full 26-man roster bought entirely from the real 2027 free-agent class "
                 "(greedy WAR-per-dollar by position, then upgrades — Cycle 26). Prices are prior-contract "
                 "AAVs: last-price anchors, not predicted 2027 salaries. The floor roster captures "
                 "~80% of the cap roster's WAR — the last $73M buys ~10 WAR. Switch budget:</sub>")
        buttons.append(dict(label=s["label"], method="update",
                            args=[{"visible": [j == i for j in range(len(d["scenarios"]))]},
                                  {"title": {"text": title}}]))
    s0 = d["scenarios"][0]
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=(f"What does the money buy? {s0['label']}: {s0['total_war']} WAR for "
               f"${s0['spend']/1e6:.1f}M<br><sub>Switch budget below the chart.</sub>"),
        updatemenus=[dict(buttons=buttons, direction="right", x=0.0, y=-0.03,
                          showactive=True, active=0)],
        template="plotly_white", height=700, margin=dict(t=110, b=60))
    return fig

def build():
    os.makedirs(os.path.join(REPO, "dashboard"), exist_ok=True)
    # G1 (audit): offline fallback — a clean clone with no network must
    # still build from the committed KPI snapshots.
    try:
        df = kpi_mod.kpi_frame()
    except Exception as e:
        print(f"kpi live fetch failed ({e}); using committed data/kpi_*.json snapshots")
        df = kpi_mod.kpi_frame_from_snapshots()
    df["group"] = "OTHER"
    df.loc[df["team"].isin(WIN_CHEAP), "group"] = "WIN_CHEAP"
    df.loc[df["team"].isin(CHEAP_MEDIOCRE), "group"] = "CHEAP_MEDIOCRE"

    fig_payroll = panel_payroll_wins(df, 2026)
    fig_kpi = panel_kpi(df, 2026)
    fig_proj = panel_projections()
    fig_dur = panel_durability()
    fig_hit = panel_player_proj()
    fig_pit = panel_pitching()
    fig_health = panel_health()
    fig_roster = panel_roster()
    fig_runs = panel_runs()
    fig_sens = panel_sensitivity()
    fig_persist = panel_skill_persistence()
    fig_value = panel_value_metrics()
    fig_capscen = panel_cap_scenario()
    fig_anim = panel_animation()
    fig_team = panel_team_explorer()
    fig_bench = panel_benchmark()
    fig_savant = panel_savant()
    fig_pipe = panel_pipeline()
    fig_shop = panel_shopping()
    fig_scen = panel_scenarios()

    SECTIONS = [
        ("★", "The Boardroom", "Sixteen seasons in motion, and every "
         "club's signature — find yours.", [fig_anim, fig_team]),
        ("I", "The Proof", "Skills persist, run differential describes "
         "wins — and payroll alone doesn't buy them.",
         [fig_persist, fig_runs, fig_payroll]),
        ("II", "The Signature", "Winning-cheap teams look different: more "
         "contact, more OBP, fewer strikeouts — for 25 straight years.",
         [fig_kpi, fig_dur]),
        ("III", "The Cap", "The owners' proposed 2027 cap, priced team "
         "by team.", [fig_proj, fig_capscen]),
        ("IV", "The Players", "Backtested Marcel projections, "
         "health-capped — the actual shopping-grade numbers.",
         [fig_hit, fig_pit, fig_health]),
        ("V", "The Roster", "A 26-man roster that fits the cap, what "
         "moves the win needle — and what the money buys at three budgets.",
         [fig_roster, fig_scen, fig_sens]),
        ("VI", "The Check", "Benchmarked against Steamer, Statcast and "
         "value metrics — including where we disagree and by how much.",
         [fig_bench, fig_savant, fig_value]),
        ("VII", "The Future", "The pipelines feeding the cheap winners, "
         "and the free-agent list to shop from.", [fig_pipe, fig_shop]),
    ]
    flat = [f for _, _, _, figs in SECTIONS for f in figs if f is not None]

    def _number(figs):
        """Executive polish + 'Figure N — ' prefix (main-lane viz pass).

        Legend BELOW the chart, title alone on top, subtle gridlines.
        Boardroom panels keep their full titles (their caveats live in
        them); other titles are shortened as before.
        """
        out = []
        for i, fig in enumerate(figs, 1):
            old = (fig.layout.title.text or "").replace("<b>", "").replace("</b>", "")
            short = old
            if not (old.startswith("PRESS PLAY") or
                    old.startswith("What does the money buy")):
                if ";" in short:
                    short = short.split(";")[0] + "; see source footer."
                elif ". " in short:
                    parts = short.split(". ")
                    short = ". ".join(parts[:2]) + "."
            fig.update_layout(title_text=f"<b>Figure {i}</b> — {short}")
            fig.update_layout(
                template="plotly_white",
                font=dict(family="system-ui, sans-serif", size=13, color="#14213d"),
                title_font=dict(size=15, color="#14213d"),
                title_x=0.0, title_xanchor="left",
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=70, r=30, t=64, b=96),
                height=max(fig.layout.height or 420, 420),
                legend=dict(orientation="h", yanchor="top", y=-0.32,
                            xanchor="center", x=0.5, font=dict(size=11),
                            bgcolor="rgba(255,255,255,0.7)"),
                xaxis=dict(gridcolor="#e8ecf3", zerolinecolor="#d6dcea"),
                yaxis=dict(gridcolor="#e8ecf3", zerolinecolor="#d6dcea"))
            out.append(fig)
        return out

    numbered = iter(_number(flat))
    # Self-contained offline demo: inline plotly from the installed
    # package if no cached bundle (never fetch at build time — G1).
    bundle = os.path.join(REPO, "dashboard", "plotly.min.js")
    if os.path.exists(bundle):
        with open(bundle) as f:
            plotly_js = f.read()
    else:
        from plotly.offline import get_plotlyjs
        plotly_js = get_plotlyjs()
        with open(bundle, "w") as f:
            f.write(plotly_js)
    js_include = f"<script>{plotly_js}</script>"

    def _count(fname):
        p = os.path.join(DATA, fname)
        return len(json.load(open(p))) if os.path.exists(p) else 0
    n_hit = _count("projections_2027.json")
    n_pit = _count("projections_2027_pitchers.json")
    cards = (
        '<div class="cards">'
        '<div class="card"><div class="num">$245.3M</div><div class="lab">proposed 2027 cap · floor $171.2M</div></div>'
        '<div class="card"><div class="num">509</div><div class="lab">team-seasons measured, 2011–2026</div></div>'
        f'<div class="card"><div class="num">{n_hit + n_pit}</div><div class="lab">players projected for 2027 ({n_hit} hitters · {n_pit} pitchers)</div></div>'
        '<div class="card"><div class="num">r = .889</div><div class="lab">hitter OBP agreement vs Steamer</div></div>'
        '<div class="card"><div class="num">100%</div><div class="lab">real data — every panel sourced</div></div>'
        '</div>')

    html = ""
    for num, name, take, figs in SECTIONS:
        figs = [f for f in figs if f is not None]
        if not figs:
            continue
        html += (f'<div class="sec"><span class="secnum">{num}</span>'
                 f'<div><h3>{name}</h3><p>{take}</p></div></div>')
        for _f in figs:
            fig = next(numbered)
            html += ('<div class="panel">' +
                     fig.to_html(full_html=False, include_plotlyjs=False) +
                     "</div>")

    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>HARDBALL — Cap-Era Moneyball Demo (P6)</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#14213d}}
.hd{{max-width:1120px;margin:0 auto;padding:0 20px 40px}}
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
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 4px}}
.card{{flex:1 1 160px;background:#fff;border:1px solid #e3dfd2;border-top:4px solid #d50032;border-radius:10px;padding:14px 16px;box-shadow:0 2px 8px rgba(20,33,61,.06)}}
.card .num{{font-size:26px;font-weight:800;color:#14213d;letter-spacing:.2px}}
.card .lab{{font-size:12.5px;color:#5a6478;margin-top:3px;line-height:1.35}}
.sec{{display:flex;gap:14px;align-items:center;background:linear-gradient(90deg,#14213d,#1d3557);color:#fff;border-radius:10px;padding:13px 20px;margin:30px 0 4px;box-shadow:0 2px 10px rgba(20,33,61,.18)}}
.secnum{{font-size:19px;font-weight:800;color:#c9a227;border:2px solid #c9a227;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}}
.sec h3{{margin:0;font-size:19px;letter-spacing:.4px}}
.sec p{{margin:2px 0 0;font-size:13.5px;color:#cbe0ff}}
.panel{{background:#fff;border:1px solid #e3dfd2;border-radius:12px;padding:16px 18px 8px;margin:14px 0;box-shadow:0 2px 10px rgba(20,33,61,.05)}}
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
shown here. We explicitly do not claim a forward-looking team-wins model: cross-year accuracy
is roughly 9-13 wins, and we present that number honestly.</div>
<div class="note">Data: MLB Stats API + Spotrac, 2011-2026 (509 team-seasons). The 2027 cap
($245.3M) and floor ($171.2M) are the owners' proposal; the CBA expires Dec 1, 2026 and the
figures are not yet law. No performance guarantee is implied.</div>
{cards}
<div class="keybox"><b>COLOR KEY (used on every chart below):</b>
<span class="k"><span class="sw" style="background:#1b5e20"></span> green = <b>winning-cheap</b> (MIL · TB · CLE — the target teams: &gt;85 wins at low payroll)</span>
<span class="k"><span class="sw" style="background:#e65100"></span> orange = <b>cheap-mediocre</b> (MIA · CHW · STL — the trap: frugal but ~78 wins)</span>
<span class="k"><span class="sw" style="background:#1565c0"></span> blue = <b>other</b> (all remaining teams)</span>
<span class="k"><span class="sw" style="background:#d50032"></span> red = cap line / negative signal</span>
<span class="k"><span class="sw" style="background:#0d47a1"></span> navy = many-color charts (retention, sensitivity)</span></div>
{js_include}
<div class="figidx"><b>FIGURE INDEX — the story at a glance (all 20 real-data charts below)</b><br>
<span>1</span> Press play: 16 seasons of payroll vs wins &nbsp;·&nbsp;
<span>2</span> Pick your team &nbsp;·&nbsp;
<span>3</span> The measurable edge — skills persist (contact r=.90) &nbsp;·&nbsp;
<span>4</span> Run differential → wins &nbsp;·&nbsp;
<span>5</span> Payroll vs wins &nbsp;·&nbsp;
<span>6</span> KPI signature &nbsp;·&nbsp;
<span>7</span> 25-yr durability &nbsp;·&nbsp;
<span>8</span> Projected wins at the cap &nbsp;·&nbsp;
<span>9</span> Cap-era reality &nbsp;·&nbsp;
<span>10</span> 2027 hitters &nbsp;·&nbsp;
<span>11</span> Pitching &nbsp;·&nbsp;
<span>12</span> Health &nbsp;·&nbsp;
<span>13</span> 2027 roster &nbsp;·&nbsp;
<span>14</span> What does the money buy (3 budgets) &nbsp;·&nbsp;
<span>15</span> Sensitivity &nbsp;·&nbsp;
<span>16</span> Marcel vs Steamer benchmark &nbsp;·&nbsp;
<span>17</span> Savant trait check &nbsp;·&nbsp;
<span>18</span> Value metrics &nbsp;·&nbsp;
<span>19</span> MiLB pipeline index &nbsp;·&nbsp;
<span>20</span> The 2027 shopping list</div>
{html}
<div class="srcbox">
<b>DATA SOURCES &amp; METHODS — everything on this page is real and traceable.</b><br><br>
<b>Primary data</b> (2025-2026, all 30 MLB teams): <span class="src">MLB Stats API
statsapi.mlb.com/api/v1</span> — official MLB feed, keyless; team hitting/pitching + standings
(runs scored / runs allowed). Validated against <span class="src">ESPN
site.web.api.espn.com</span> (2025 validation set: 131 players cross-checked, HR counts match exactly).<br>
<b>Payroll:</b> <span class="src">Spotrac</span> (via MIT-licensed jasonbhorne/mlb-payroll,
721 team-seasons 2000-2024 + live 2026 opening-day figures; per-player 2026 salaries and the
2027 free-agent class pulled directly from Spotrac team/FA pages — 24 of 30 team pages before
a rate limit, logged in data/salaries_2026.json). <b>Injury/health:</b> MLB
transactions feed (35,000+ events 2025-2026, IL days per player). <b>MLB color/look:</b> league
branding only, for presentation.<br>
<b>CarpeData layer (2026-10-31, all keyless):</b> <span class="src">Baseball Savant</span>
leaderboards by player_id — expected stats (xwOBA), batted ball (EV/barrels), bat tracking
2024-2026, sprint speed, arm strength; <span class="src">FanGraphs API</span> — Steamer 2027
projections (the benchmark panel; ZiPS returned empty via the API and is not claimed) and the
player-ID crosswalk; <span class="src">MLB Stats API</span> minor-league endpoints (AAA/AA)
for the pipeline index. Every source tried is logged kept-vs-dropped in docs/CARPE_SCORECARD.md.<br>
<b>Models &amp; honest capability:</b> same-year run-differential → wins R² ≈ 0.55 (diagnostic,
not a forecast — a same-year production formula once recorded CV MAE 4.3 / R² 0.764 on a
two-season window; on the full 2011-2026 panel it does not generalize, and it is labeled
diagnostic-only in data/formula_prod.json). KPI-only next-year forecasting: out-of-sample
MAE ≈ 14.1 wins, worse than the naive baseline; grouped CV MAE 10.2 (a fold predicting the
60-game 2020 season is excluded as a units mismatch — see BML Cycle 19). Player projections:
backtested Marcel (3-season 5-4-3 + fitted age terms; Cycles 21/24), health-capped, benchmarked
against Steamer (hitter OBP r = .889; pitcher ERA bias −0.25 after the Cycle 24 fix, disclosed
on the panel). The product is player-level acquisition, not a team-wins formula.<br><br>
<b>Project repo:</b> github.com/mega-byte2600/hardball (private) · audit trail in docs/BML_LOG.md
(two cycle series converged on 2026-10-31 — see the integration note at the top of the log)
</div>
</div></body></html>"""

    out = os.path.join(REPO, "dashboard", "hardball_demo.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"dashboard written: {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    import pandas as pd  # noqa
    build()

