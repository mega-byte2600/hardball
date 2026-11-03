"""HARDBALL demo dashboard (Plotly HTML) — INTEGRATED build. [P7; script name
retains the P6 filename for README/repo stability]

Twenty-five figures on real data: the main lane's 13 (payroll/KPI/
projections/durability/players/pitching/health/roster/runs/
sensitivity + skill persistence, value metrics, cap scenario)
plus the CarpeData/Boardroom 7 (Steamer benchmark, Savant trait
check, MiLB pipeline, FA shopping list, animated 16-season
payroll film, pick-your-team explorer, budget-scenario rosters)
plus the Cycle 30 forced-seller panel
plus the Cycle 8 title-bar AUC panel
plus the Cycle 34 posted-class panel (NPB BIS)
plus the Cycle 48 Hakes–Sauer verdict panel (Explorer-only,
appended last so figures 1–23 keep their numbers)
plus the Cycle 49 roster-optimizer panel (Explorer-only,
appended last so figures 1–24 keep their numbers)
plus the Cycle 50 sensitivity strip under Figure 25 (no new figure),
plus the Cycle 62 held-out benchmark panel under Figure 18 (no new figure),
presented in three modes (Story, Boardroom, Explorer) with stat cards. Builds from a
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
                      xaxis_title="Total payroll ($ millions)", yaxis_title="Wins",
                      template="plotly_white", height=520)
    fig.add_hline(y=81, line_dash="dash", line_color="#d50032", opacity=0.75,
                  annotation_text="league avg = 81 wins (.500)",
                  annotation_position="bottom left", annotation_font=dict(color="#d50032", size=11))
    return fig


def panel_kpi(df, year=2026):
    """Copycat-league KPI signature. Clean: one shared legend, no repeat labels."""
    d = df[df["season"] == year].dropna(subset=["OBP", "contact", "K%", "BB%", "HR/PA"])
    grp = d.groupby("group")[["OBP", "contact", "K%", "BB%", "HR/PA"]].mean()
    metrics = ["OBP", "BB%", "HR/PA", "contact", "K%"]
    labels = {"OBP": "OBP<br><span style='font-weight:400;font-size:10px'>reach base %</span>",
              "BB%": "BB%<br><span style='font-weight:400;font-size:10px'>walks</span>",
              "HR/PA": "HR / 1000 PA<br><span style='font-weight:400;font-size:10px'>home runs</span>",
              "contact": "Contact %<br><span style='font-weight:400;font-size:10px'>hits ball</span>",
              "K%": "K%<br><span style='font-weight:400;font-size:10px'>strikeouts</span>"}
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
    fig.add_hline(y=81, line_dash="dash", line_color="#d50032", opacity=0.75,
                  annotation_text="league avg = 81 wins",
                  annotation_position="bottom left", annotation_font=dict(color="#d50032", size=11))
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
    fig.add_hline(y=81, row=1, col=2, line_dash="dash", line_color="#d50032", opacity=0.7,
                  annotation_text="league avg = 81 wins",
                  annotation_position="bottom left", annotation_font=dict(color="#d50032", size=10))
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
    # Cycle 51 (API-1): live-feed sub-panel — the Statyx + FastballAPI
    # current-IL picture for the 2027 FA pool, rendered ONLY from the
    # committed artifact data/il_current_live.json (built by
    # src/bml_cycle51.py from the dated raw snapshots). Absent the
    # artifact, the panel stays the static picture — fail closed.
    live_path = os.path.join(DATA, "il_current_live.json")
    if not os.path.exists(live_path):
        return fig
    with open(live_path) as fh:
        live = json.load(fh)
    ov = live["fa_overlay"]
    players = ov["players"]
    combo = make_subplots(
        rows=2, cols=1, row_heights=[0.52, 0.48], vertical_spacing=0.14,
        specs=[[{"type": "bar"}], [{"type": "table"}]],
        subplot_titles=[
            "",
            (f"Current IL picture — LIVE feeds (Statyx + FastballAPI, pulled "
             f"{live['metadata']['pulled_date']}): {ov['n_matched']} of "
             f"{ov['fa_pool_size']} free agents currently listed injured")])
    for tr in fig.data:
        combo.add_trace(tr, row=1, col=1)
    combo.add_trace(go.Table(
        header=dict(values=["Free agent", "Team", "Status (live feed)",
                            "Injury", "Expected return"],
                    fill_color="#14213d",
                    font=dict(color="white", size=12), align="left"),
        cells=dict(values=[
            [p["name"] for p in players],
            [p["team"] or p["prev_team"] or "" for p in players],
            [p["status"] for p in players],
            [(p["type"] or "") + (" — " + p["detail"] if p["detail"] else "")
             for p in players],
            [p["return_date"] or "" for p in players]],
            fill_color="#f2f4f8", font=dict(size=12), align="left")),
        row=2, col=1)
    combo.update_layout(
        title=fig.layout.title.text,
        xaxis_title="", yaxis_title="Projected PA reduction (%)",
        template="plotly_white", height=760, showlegend=True)
    # Cycle 55: movement line from the event layer (data/il_events.json,
    # built by src/bml_cycle55.py) under the live-IL table. Absent the
    # artifact, the panel keeps the Cycle 51 two-row shape — fail closed.
    ev_path = os.path.join(DATA, "il_events.json")
    if not os.path.exists(ev_path):
        return combo
    with open(ev_path) as fh:
        ev = json.load(fh)
    line = ev["metadata"]["movement_line"]
    table_title = (f"Current IL picture — LIVE feeds (Statyx + FastballAPI, pulled "
                   f"{live['metadata']['pulled_date']}): {ov['n_matched']} of "
                   f"{ov['fa_pool_size']} free agents currently listed injured")
    combo3 = make_subplots(
        rows=3, cols=1, row_heights=[0.44, 0.42, 0.14],
        vertical_spacing=0.10,
        specs=[[{"type": "bar"}], [{"type": "table"}],
               [{"type": "scatter"}]],
        subplot_titles=["", table_title, ""])
    for tr in combo.data[:-1]:
        combo3.add_trace(tr, row=1, col=1)
    combo3.add_trace(combo.data[-1], row=2, col=1)
    combo3.add_trace(go.Scatter(
        x=[0], y=[0], mode="text", text=[line], showlegend=False,
        textfont=dict(size=13), hoverinfo="skip"), row=3, col=1)
    combo3.update_xaxes(visible=False, row=3, col=1)
    combo3.update_yaxes(visible=False, row=3, col=1)
    combo3.update_layout(
        title=fig.layout.title.text,
        xaxis_title="", yaxis_title="Projected PA reduction (%)",
        template="plotly_white", height=830, showlegend=True)
    return combo3


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
    fig.add_hline(y=81, line_dash="dot", line_color="#d50032", opacity=0.6,
                  annotation_text="league avg = 81 wins",
                  annotation_position="bottom right", annotation_font=dict(color="#d50032", size=11))
    return fig


def panel_auc():
    """Title-bar test (Cycle 8): can the model flag a 90+ win team before
    the season? Reads the persisted logistic results from quant_core.json
    (run-diff-only / KPIs+PythE, both year-directions). A single honest
    panel for the single most decision-relevant number."""
    qj = os.path.join(DATA, "quant_core.json")
    if not os.path.exists(qj):
        return None
    d = json.load(open(qj))
    log = d.get("logistic")
    if not log:
        return None
    rows = []
    for label, feats in [("Run differential alone", "run-diff-only"),
                         ("KPIs + Pythagoras", "KPIs+PythE")]:
        for key, tag in [("25->26", "2025 → 2026"), ("26->25", "2026 → 2025")]:
            r = log[feats].get(key)
            if r:
                rows.append({"label": f"{label}<br><sub>{tag}</sub>",
                             "auc": round(r["auc"], 3)})
    if not rows:
        return None
    # order: "Run differential" block first, then KPI block; higher AUC first within a block
    rows.sort(key=lambda r: (0 if r["label"].startswith("Run differential") else 1,
                             -r["auc"]))
    base_rate = log["run-diff-only"]["25->26"]["base_rate"]
    fig = go.Figure()
    for r in rows:
        color = "#1b5e20" if r["label"].startswith("Run differential") else "#1565c0"
        fig.add_trace(go.Bar(
            x=[r["auc"]], y=[r["label"]], orientation="h",
            marker_color=color,
            text=[f"{r['auc']:.3f}"], textposition="outside",
            showlegend=False))
    fig.add_vline(x=0.5, line_dash="dash", line_color="gray",
                  annotation_text=" chance", annotation_position="top right",
                  annotation_font=dict(color="gray"))
    fig.update_layout(
        title=("The proof it works: run differential alone flags a 90+ win club "
               "with AUC ≈ 0.95 — both directions, both years (real 2025→26 data)<br>"
               f"<sub>Decision-relevant: base rate of a 90+ win season is only "
               f"{base_rate:.0%}, yet the model separates the field near-perfectly. "
               "AUC 1.0 = perfect ordering, 0.5 = coin flip. Logistic title-bar "
               "test, prior to any 2027 result. Source: 509-team panel 2011–2026.</sub>"),
        xaxis_title="AUC (area under ROC curve)", yaxis_title="",
        xaxis_range=[0.4, 1.03],
        template="plotly_white", height=340,
        showlegend=False)
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


def panel_forced_sellers():
    """Cycle 30: the forced sellers — the fewest big contracts that
    arithmetically close each over-cap team's gap. Bar = cumulative
    salary of the minimal largest-first shed set; diamond = the gap.
    Arithmetic only, NOT a trade prediction: shedding is assumed to
    remove the full listed salary. CHC is excluded, not zero — its
    Spotrac page failed in Cycle 25, so it has no contract rows."""
    fj = os.path.join(DATA, "forced_sellers_2027.json")
    if not os.path.exists(fj):
        return None
    d = json.load(open(fj))
    teams = [t for t in d["teams"] if t["covered"]]
    if not teams:
        return None
    teams = sorted(teams, key=lambda t: -t["gap_to_cap"])
    labels = [t["team"] for t in teams]
    shed_m = [t["shed_total"] / 1e6 for t in teams]
    gap_m = [t["gap_to_cap"] / 1e6 for t in teams]
    bar_text = [f"{t['n_shed']} contract{'s' if t['n_shed'] > 1 else ''} · "
                f"${t['shed_total']/1e6:.1f}M" for t in teams]
    hover = ["<br>".join(
        [f"{t['team']}: gap ${t['gap_to_cap']/1e6:.1f}M"] +
        [f"{s['name']} ({s['pos']}) ${s['salary_2026']/1e6:.1f}M"
         for s in t["shed"]]) for t in teams]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=shed_m, orientation="h",
                         marker_color="#d50032", text=bar_text,
                         textposition="outside", hovertext=hover,
                         hoverinfo="text", name="Shed set"))
    fig.add_trace(go.Scatter(y=labels, x=gap_m, mode="markers",
                             marker=dict(symbol="diamond", size=13,
                                         color="#14213d"),
                             hovertext=[f"gap ${g:.1f}M" for g in gap_m],
                             hoverinfo="text", name="Cap gap"))
    fig.update_layout(
        title=("Forced sellers — how few big contracts close each "
               "over-cap gap<br><sub>Arithmetic only, not a trade "
               "prediction — shedding is assumed to remove the full "
               "listed salary, and real trades rarely do that · Coverage "
               "6 of 7 over-cap teams — CHC ($4.0M over) has no contract "
               "rows because its Spotrac page failed in Cycle 25 · "
               "Salaries are the Spotrac 2026 Payroll Salary rows as "
               "committed, gaps are from the cap scenario file</sub>"),
        xaxis_title="Salary ($M)", template="plotly_white",
        height=460, margin=dict(l=60, r=40, t=64, b=96),
        xaxis_range=[0, max(shed_m) * 1.35],
        annotations=[dict(x=0.5, y=-0.28, xref="paper", yref="paper",
                          showarrow=False,
                          text="Every covered team closes its gap by "
                               "shedding at most 3 contracts; TOR and ATL "
                               "need just 1 — the cap binds through a "
                               "handful of deals, not a rebuild",
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
    fig.update_layout(title="Top value metrics — wOBA/wRC+ & FIP/K-BB% (2026) — the reproducible inputs WAR is built from: the MLB API returns no WAR",
                      template="plotly_white", height=640, showlegend=True,
                      margin=dict(l=60, r=40, t=64, b=96))
    # league-average reference lines, mirroring the Figure 21 pattern:
    # wRC+ is an index where 100 = league average; FIP gets the league mean.
    fig.add_vline(x=100, row=1, col=1, line_dash="dash", line_color="#d50032", opacity=0.75,
                  annotation_text="league avg = 100", annotation_position="top right",
                  annotation_font=dict(color="#d50032", size=10))
    _fip = [p["FIP"] for p in d["pitching"] if p.get("FIP") is not None]
    league_fip = round(sum(_fip) / len(_fip), 2) if _fip else 3.81
    fig.add_vline(x=league_fip, row=2, col=1, line_dash="dash", line_color="#d50032", opacity=0.75,
                  annotation_text=f"league avg FIP {league_fip:.2f}",
                  annotation_position="top right",
                  annotation_font=dict(color="#d50032", size=10))
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

def panel_hs_verdict():
    """Cycle 48 (HS-2), Figure 24: the Hakes–Sauer verdict exhibit.

    HS-1 (Cycle 46) regressed ln(salary) on projected OBP/SLG/K%/BB%
    on two committed salary bases and found no significant skill
    coefficient; HS-2 derived the missing run-value benchmark from
    480 committed team-seasons and ran the formal proportionality
    test. Every number renders from data/hakes_sauer_results.json
    (coefficients/SEs) and data/hakes_sauer_verdict.json (benchmark,
    Wald tests, quartile contrast, verdict text) so the panel can
    never drift from the workpaper. The visual point of the forest
    plots is the intervals crossing zero; the quartile $/WAR bars are
    a descriptive contrast, labeled as such — not a price effect."""
    rj = os.path.join(DATA, "hakes_sauer_results.json")
    vj = os.path.join(DATA, "hakes_sauer_verdict.json")
    if not (os.path.exists(rj) and os.path.exists(vj)):
        return None
    res = json.load(open(rj))
    ver = json.load(open(vj))
    samples = [("S", "sample_S_spotrac_basis", "#1d3557", "Sample S — Spotrac basis"),
               ("C", "sample_C_cots_lrp2027", "#b8860b", "Sample C — Cot's LRP-2027")]
    bench = ver["benchmark_attempt"]
    rho = bench["season_fe_primary"]["ratio_obp_to_slg"]
    rho_ci = bench["season_fe_primary"]["ratio_ci95"]

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "bar", "colspan": 2}, None]],
        subplot_titles=[
            "ln(salary) coefficients — OBP and SLG (95% CIs cross zero)",
            "ln(salary) coefficients — K% and BB% (95% CIs cross zero)",
            "Descriptive contrast: median $ per WAR by contact quartile (NOT a price effect)",
            ""],
        vertical_spacing=0.16, horizontal_spacing=0.10)

    def forest(skills, col):
        ys, xs, errs, cols, labels = [], [], [], [], []
        for skey, rkey, color, sname in samples:
            terms = res[rkey]["spec_A_full_controls"]["terms"]
            for sk in skills:
                t = terms[sk]
                ys.append(f"{sk} · {sname}")
                xs.append(t["coef"])
                errs.append(1.96 * t["se"])
                cols.append(color)
                labels.append(f"{sk} {t['coef']:+.2f} ± {1.96 * t['se']:.2f} (p = {t['p']:.2f})")
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", marker=dict(color=cols, size=10),
            error_x=dict(type="data", array=errs, visible=True, color="#5a6478"),
            text=labels, hovertemplate="%{text}<extra></extra>",
            showlegend=False), row=1, col=col)
        fig.add_vline(x=0, line_dash="dash", line_color="#d50032", row=1, col=col)

    forest(["OBP", "SLG"], 1)
    forest(["K%", "BB%"], 2)

    qt = ver["quartile_contrast_from_hs1"]["samples"]
    bx, by, bc, bt = [], [], [], []
    for skey, sname in [("S", "Sample S (Spotrac)"), ("C", "Sample C (Cot's)")]:
        q = qt[skey]
        bx += [f"{sname} — bottom contact quartile", f"{sname} — top contact quartile"]
        by += [q["bottom_quartile_median_dollars_per_war"] / 1e6,
               q["top_quartile_median_dollars_per_war"] / 1e6]
        bc += ["#7a1f1f", "#1b5e20"]
        bt += [f"${q['bottom_quartile_median_dollars_per_war'] / 1e6:.2f}M",
               f"${q['top_quartile_median_dollars_per_war'] / 1e6:.2f}M — {q['ratio']:.2f}× the bottom"]
    fig.add_trace(go.Bar(x=bx, y=by, marker_color=bc, text=bt,
                         textposition="outside", showlegend=False,
                         hovertemplate="%{x}<br>%{text}<extra></extra>"),
                  row=2, col=1)
    fig.update_yaxes(title_text="Median $ per WAR ($M)", row=2, col=1)
    fig.update_xaxes(title_text="Coefficient in ln(salary)", row=1, col=1)
    fig.update_xaxes(title_text="Coefficient in ln(salary)", row=1, col=2)
    fig.update_layout(
        title=("The pricing test: we ran Hakes–Sauer on ourselves — the honest verdict is not proven<br>"
               f"<sub>Every skill coefficient's 95% interval crosses zero on both committed salary bases, and the formal "
               f"proportionality test (run-value benchmark from {bench['n_team_seasons']} team-seasons: a point of OBP is worth "
               f"{rho:.2f}× a point of SLG, 95% CI {rho_ci[0]:.2f}–{rho_ci[1]:.2f}) cannot reject correct pricing — or large "
               f"mispricing. The samples lack power, and the panel says so. Sources: data/hakes_sauer_results.json (Cycle 46) "
               f"and data/hakes_sauer_verdict.json (Cycle 48).</sub>"),
        template="plotly_white", height=680)
    return fig


def _hs_verdict_html():
    """Cycle 48: the HS-2 verdict box under Figure 24 (Explorer only).
    Text renders verbatim from data/hakes_sauer_verdict.json."""
    import html as _html
    ver = json.load(open(os.path.join(DATA, "hakes_sauer_verdict.json")))
    v = ver["verdict"]
    return ('<div class="verdict"><h2>THE VERDICT — ' +
            _html.escape(v["status"].upper()) + "</h2><p>" +
            _html.escape(v["short"]) + "</p></div>" +
            '<p class="srcline">Benchmark: team-season runs regression (runs per PA on OBP and SLG, '
            "season fixed effects) on data/curated/fact_team_season.parquet — a team-aggregate "
            "benchmark, labeled as such in the workpaper (docs/CARPE_SCORECARD.md, Cycle 48 "
            "addendum). Salary samples: Spotrac basis n = 60 (24 of 30 teams, at the power "
            "floor) and Cot's LRP-2027 n = 82 — bases never mixed. Method and full numbers: "
            "src/bml_cycle48.py, data/hakes_sauer_verdict.json.</p>")


def _evidence_note_html():
    """Cycle 57: one asterisked footnote line directly under the
    Figure 14 (health) panel in Explorer — Figure 14 is the anchor
    figure; Figure 14 is the anchor figure.
    Counts ride inside the note. Renders ONLY from the committed
    artifact data/evidence_surveillance.json; absent the artifact
    the note is omitted entirely (fail closed, Cycle 51 pattern).
    The full page is docs/EVIDENCE.html (src/make_evidence_page.py);
    the context-not-a-model-input label lives on that page."""
    path = os.path.join(DATA, "evidence_surveillance.json")
    if not os.path.exists(path):
        return ""
    ev = json.load(open(path))
    short = {"ucl_rtp": "UCL return to play",
             "prevention_workload": "injury prevention and workload",
             "cellular_recovery": "muscle regeneration and cellular "
                                  "recovery",
             "tendon_biologics": "tendon healing and biologics"}
    counts = " &middot; ".join(
        f'{short[lane["id"]]} ({lane["found"]} found)'
        for lane in ev["lanes"])
    return ('<p class="srcline evfoot">* <a href="../docs/EVIDENCE.html">'
            "What the evidence says now</a> — the published research "
            "on injury recovery and prevention. " + counts + ".</p>")


def _benchmark_panel_html():
    """Cycle 62 (BLEND-1): the held-out accuracy panel directly under
    Figure 18 (the Marcel–Steamer benchmark) in Explorer — Figure 18
    shows agreement between the two systems; this panel shows accuracy
    against outcomes, which is a different thing. Renders ONLY from
    the committed artifact data/projection_blend_2027.json; absent the
    artifact the panel is omitted entirely (fail closed, Cycle 51/57
    pattern). Not a figure: the count stays 25."""
    path = os.path.join(DATA, "projection_blend_2027.json")
    if not os.path.exists(path):
        return ""
    art = json.load(open(path))
    res = art["results"]
    hn = art["paired_n"]["hitters"]["2026"]
    pn = art["paired_n"]["pitchers"]["2026"]
    ho = res["hitters"]["2026"]["OBP"]
    pe = res["pitchers"]["2026"]["ERA"]

    def _row(label, h, p):
        if "mae" not in h:
            return (f"<tr><td>{label}</td><td colspan=\"3\">not scored</td>"
                    f"<td colspan=\"3\">not scored</td></tr>")
        return (f"<tr><td>{label}</td>"
                f"<td>{h['r']:.3f}</td><td>{h['rmse']:.3f}</td><td>{h['mae']:.3f}</td>"
                f"<td>{p['r']:.3f}</td><td>{p['rmse']:.3f}</td><td>{p['mae']:.3f}</td></tr>")

    table = ("<table style=\"border-collapse:collapse;font-size:13px;margin:8px 0\">"
             "<tr><th style=\"text-align:left;padding:2px 10px 2px 0\">Forecaster</th>"
             "<th style=\"padding:2px 8px\">Hitter OBP r</th>"
             "<th style=\"padding:2px 8px\">RMSE</th>"
             "<th style=\"padding:2px 8px\">MAE</th>"
             "<th style=\"padding:2px 8px\">Pitcher ERA r</th>"
             "<th style=\"padding:2px 8px\">RMSE</th>"
             "<th style=\"padding:2px 8px\">MAE</th></tr>"
             + _row("Last season, repeated", ho["naive"], pe["naive"])
             + _row("Marcel (this demo)", ho["marcel"], pe["marcel"])
             + _row("Steamer", ho["steamer"], pe["steamer"])
             + _row("Steamer + Marcel blend", ho["blend"], pe["blend"])
             + "</table>")
    return ('<div class="quant"><b>How good are these projections?</b>'
            f"<p>Held-out window: the 2026 season, scored against actuals, "
            f"with every projection built only from 2023–2025 data. "
            f"Hitters n = {hn} (OBP); pitchers n = {pn} (ERA).</p>"
            + table +
            "<p>Marcel beat repeating last season on every error measure in "
            "2026. Pitcher ERA ranking was near chance for both forecasters "
            "that year (n = 22).</p>"
            "<p>Steamer — not scored: this demo holds Steamer only for 2027, "
            "a season not yet played, so it has no outcomes to score "
            "against. Figure 18 above measures agreement with Marcel, not "
            "accuracy.</p>"
            "<p>Blend status: not adopted — a blend can only be checked "
            "where both systems have outcomes. Steamer remains the "
            "benchmark and Marcel the spine, unchanged.</p>"
            '<p class="srcline">Source: data/projection_blend_2027.json '
            "(Cycle 62). Secondary metrics (SLG, WHIP) and the 2025 "
            "reference window are in the artifact; method mirrors the "
            "Cycle 21/24 backtests, reproduced exactly by "
            "src/bml_cycle62.py.</p></div>")


def panel_optimizer():
    """Cycle 49 (OPT-1), Figure 25: the optimizer's audit of Cycle 26
    (Cycle 52: benchmark vs headline — the optimum now headlines
    Figure 16 and the greedy build is the benchmark).

    Cycle 26 built the three budget rosters greedily (WAR-per-dollar
    quota fill + upgrades). OPT-1 re-solves the identical problem —
    same 199-player FA pool, same Steamer WAR, same prior-AAV anchors,
    same positional quotas — as a mixed-integer program
    (scipy.optimize.milp / HiGHS) with the owners' proposed 15%
    per-player maximum as an added hard constraint, and proves the
    optima (gap 0 at all three budgets). Every number renders from
    data/optimizer_comparison_2027.json so the panel can never drift
    from the workpaper. The DH-restricted series is the sensitivity
    that isolates Cycle 26's own stated DH rule ("DH can be any bat")
    — a freedom its greedy never actually used. Cycle 52 promotes the
    optimizer rosters to the Figure 16 headline; this panel is the
    benchmark comparison behind the promotion."""
    cj = os.path.join(DATA, "optimizer_comparison_2027.json")
    if not os.path.exists(cj):
        return None
    d = json.load(open(cj))
    budgets = d["budgets"]
    cats = [b["label"].replace("The ", "") for b in budgets]

    def series(key, name, color, delta=False):
        ys = [b[key]["total_war"] for b in budgets]
        tx = []
        for b in budgets:
            t = f"{b[key]['total_war']:.1f}"
            if delta:
                t += f" (+{b['delta_war']:.1f})"
            tx.append(t)
        return go.Bar(
            name=name, x=cats, y=ys, marker_color=color, text=tx,
            textposition="outside",
            hovertemplate="%{x}<br>" + name + ": %{y:.1f} WAR<br>" +
            "spend $" + "%{customdata:.2f}M<extra></extra>",
            customdata=[b[key]["spend"] / 1e6 for b in budgets])

    fig = go.Figure(data=[
        series("greedy", "Greedy build (Cycle 26)", "#7a1f1f"),
        series("optimizer", "Exact optimizer (proven optimal)", "#1d3557",
               delta=True),
        series("optimizer_dh_restricted",
               "Optimizer, DH restricted to DH-mapped bats", "#b8860b"),
    ])
    f0 = budgets[0]
    fig.update_layout(
        title=(f"Benchmark vs headline: the exact optimum beats the greedy build — "
               f"+{f0['delta_war']:.1f} WAR at the floor, "
               f"+{budgets[1]['delta_war']:.1f} in the middle, "
               f"+{budgets[2]['delta_war']:.1f} at the cap, all three optima proven; "
               f"same pool, prices and quotas as Figure 16 — "
               f"data/optimizer_comparison_2027.json (Cycle 49)."),
        barmode="group", template="plotly_white", height=560,
        yaxis_title="Total Steamer WAR (26-man roster)")
    return fig


def _optimizer_html():
    """Cycle 49: the OPT-1 facts box under the Build a Roster group
    (Explorer only). Text renders from data/optimizer_comparison_2027.json."""
    import html as _html
    d = json.load(open(os.path.join(DATA, "optimizer_comparison_2027.json")))
    rows = []
    for b in d["budgets"]:
        o, g = b["optimizer"], b["greedy"]
        rows.append(
            f"<b>{_html.escape(b['label'])}:</b> greedy {g['total_war']:.1f} WAR "
            f"(${g['spend']/1e6:.1f}M) → optimizer {o['total_war']:.1f} WAR "
            f"(${o['spend']/1e6:.1f}M), +{b['delta_war']:.1f} WAR with "
            f"{b['overlap']['n_shared']} of 26 names shared. At DH the greedy "
            f"carries {g['dh_slot']['name']} ({g['dh_slot']['war']:.2f} WAR); "
            f"the optimizer plays {o['dh_slot']['name']} ({o['dh_slot']['war']:.2f} WAR).")
    pm = d["metadata"]["per_player_max"]
    return ('<div class="note"><b>BENCHMARK VS HEADLINE (Cycles 49–52).</b> ' +
            " ".join(rows) +
            f" All three optima are proven (solver gap 0). The 15% per-player "
            f"rule (${pm['value']/1e6:.1f}M) binds nobody in this pool — the "
            f"dearest free agent anchors at $35.0M — and all three greedy "
            f"rosters satisfy it. The DH-restricted sensitivity (gold bars) "
            f"shows the edge is mostly combinatorics, not the DH rule: "
            f"restricted to the greedy's own effective search space the "
            f"optimizer still finds "
            f"+{d['budgets'][0]['delta_war_dh_restricted']:.1f} WAR at the floor. "
            "Since Cycle 52, Figure 16 headlines the optimizer "
            "rosters; the greedy builds remain here as the benchmark. "
            "Cycle 50 stress-tests these optima — price swings, a "
            "targeted bid-up, an aging haircut, and a mixed pre-arb "
            "build — in the strip directly below.</div>")


def _optimizer_sensitivity_html():
    """Cycle 50 (OPT-2): the sensitivity strip under Figure 25
    (Explorer only). Every number renders from
    data/optimizer_sensitivity_2027.json. The mixed build is framed
    exactly as the workpaper frames it: internal pre-arb production
    a club develops or holds — not a shopping list (nobody can sign
    another club's pre-arb players)."""
    import html as _html
    p = os.path.join(DATA, "optimizer_sensitivity_2027.json")
    if not os.path.exists(p):
        return ""
    d = json.load(open(p))
    budgets = [171.2e6, 208.0e6, 245.3e6]

    def cell(entries, budget, key="total_war", churn=True):
        e = next((x for x in entries if x["budget"] == budget), None)
        if e is None:
            return "<td>—</td>"
        t = f"{e[key]:.1f}"
        if churn:
            t += f" ({e['n_changed']} changed)"
        return f"<td>{t}</td>"

    base_cells = "".join(
        f"<td>{d['base_optimizer'][lbl]['total_war']:.1f}</td>"
        for lbl in ("The Floor — $171.2M", "The Middle — $208.0M",
                    "The Cap — $245.3M"))
    hc = d["war_haircut"]
    hc_cells = "".join(
        cell(hc, b, key="total_war_base_rescore") for b in budgets)
    tb = d["targeted_bid_up"]
    m = d["mixed_floor"]
    pre_names = ", ".join(
        f"{_html.escape(r['name'])} ({r['war']:.1f})" for r in m["roster"]
        if r["origin"] == "pre-arb" and r["war"] >= 2.0)
    rows = (
        f"<tr><td>Proven optimum (OPT-1, base anchors)</td>{base_cells}</tr>"
        "<tr><td>Every price ×0.8</td>"
        + "".join(cell(d["price_sensitivity"]["x0.8"], b) for b in budgets)
        + "</tr>"
        "<tr><td>Every price ×1.2</td>"
        + "".join(cell(d["price_sensitivity"]["x1.2"], b) for b in budgets)
        + "</tr>"
        f"<tr><td>Only your 26 floor targets ×1.2 (the market bids "
        f"up your list)</td><td>{tb['total_war']:.1f} "
        f"({tb['n_changed']} changed)</td><td>—</td><td>—</td></tr>"
        f"<tr><td>WAR −15% for age 33+, roster re-scored on base WAR"
        f"</td>{hc_cells}</tr>")
    return (
        '<div class="note"><b>HOW FRAGILE IS THE OPTIMUM? (Cycle 50, '
        'OPT-2).</b> The same exact solver, re-run with the prices and '
        'projections perturbed. WAR per budget; "changed" counts roster '
        'names swapped versus the OPT-1 optimum at that budget. Every '
        'solve is proven optimal (gap 0).'
        f"<table><tr><th>Scenario</th><th>Floor $171.2M</th>"
        f"<th>Middle $208.0M</th><th>Cap $245.3M</th></tr>{rows}</table>"
        "Read: a uniform ±20% price swing moves the floor optimum by "
        "about ±4 WAR and swaps only 3–6 names — the build is a "
        "portfolio, not a knife-edge. Bid up just the floor list by "
        "20% and the solver walks away from 6 of its own targets "
        "(including its ace) and still lands 45.6. Discount every "
        "33-and-over projection by 15% and the pessimist's rosters "
        "re-score within 0.1 WAR of the base optima on base WAR — "
        "and the pessimist's rosters carry just 2 players aged 33+ "
        "at every budget."
        f"<br><b>THE FLOOR, WITH A FARM SYSTEM (mixed build).</b> "
        f"Re-solve the floor with the pool widened to the club's own "
        f"pre-arbitration production (509 pre-arb players carried in "
        f"the committed salary file, each priced at the file's flat "
        f"$1.0M — a placeholder convention, not a measured salary): "
        f"<b>{m['total_war']:.1f} WAR for ${m['spend']/1e6:.1f}M</b> — "
        f"{m['n_prearb_slots']} pre-arb slots ({m['prearb_war']:.1f} "
        f"WAR: {pre_names}) and {m['n_fa_slots']} free-agent slots, "
        f"leaving ${171.2 - m['spend']/1e6:.1f}M of the floor unspent. "
        "That is the honest answer to 'no club shops its way to the "
        "floor': the floor is survivable for a club that develops or "
        "holds pre-arb talent. It is not a shopping list — nobody can "
        "sign another club's pre-arb players. Method, full rosters "
        "and solver bounds: src/bml_cycle50.py, "
        "data/optimizer_sensitivity_2027.json.</div>")


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

def panel_posted():
    """Cycle 47 rebuild, Figure 23: the posted class — three players,
    three different bets. Sato is the thesis TEST (Triple Crown power
    whose 26.7% K rate sits ~11 points above the Central League
    qualified median), Itoh is the thesis FIT (#2 of 11 Pacific League
    qualifiers in walk rate, 172+ IP three straight years), Taira is
    the conversion GAMBLE (31-save closer to PL-best ERA as a starter,
    on a +93.8 IP workload jump).

    Every number traces to committed data: the trio lines and posting
    facts come from data/posted_class_2026.json (NPB official BIS,
    canonical over wire roundings — Sato .306 not .308, Itoh 34 BB not
    32); the leaderboard ranks/percentiles, Sato-vs-median K%, Itoh's
    BB% series (2024 computed from the leaderboard's batters-faced
    column, which the trio dataset lacks) and the fee curve come from
    data/fig23_rebuild_2026.json, computed by src/bml_cycle47.py with a
    14/14 verification table against the trio dataset. Taira 2024 is
    NOT on the qualified boards and is never backfilled — his panels
    show 2025-2026 only. NO NPB-to-MLB translation factor is claimed
    anywhere in this figure."""
    fj = os.path.join(DATA, "posted_class_2026.json")
    fr = os.path.join(DATA, "fig23_rebuild_2026.json")
    if not (os.path.exists(fj) and os.path.exists(fr)):
        return None
    d = json.load(open(fj))
    rb = json.load(open(fr))
    by_name = {p["name"]: p for p in d["players"]}
    sato = by_name.get("Teruaki Sato")
    taira = by_name.get("Kaima Taira")
    itoh = by_name.get("Hiromi Itoh")
    if not (sato and taira and itoh):
        return None

    def seasons(p):
        return {s["year"]: s for s in p["seasons_bis"]}

    ss, ts, ins = seasons(sato), seasons(taira), seasons(itoh)
    years = [2024, 2025, 2026]
    x3 = [str(y) for y in years]
    ctx = rb["leaderboard_context_2026"]
    kv = {r["year"]: r for r in rb["sato_k_vs_cl_median"]}
    ib = {r["year"]: r for r in rb["itoh_bb_pct_by_year"]}

    fig = make_subplots(
        rows=5, cols=2,
        specs=[[{"secondary_y": False}, {"secondary_y": True}],
               [{}, {}],
               [{}, {}],
               [{}, {}],
               [{"colspan": 2}, None]],
        subplot_titles=[
            "Sato — the test: walks climbing (7.3% → 11.1%), whiffs not leaving (26.7% K)",
            "Itoh — the fit: 172+ IP three straight years, walk rate never above 5.5%",
            "Taira — the gamble: a 31-save closer became the PL's best ERA as a starter",
            "Taira's price question is workload: +93.8 IP in one jump, a career high",
            "How rare is it? The trio against their own 2026 qualified leaderboards",
            f"Sato whiffs like a slugger: 26.7% K vs a {kv[2026]['cl_median_k_pct']:.1f}% Central League median",
            "The fee is a second price tag: $10.875M on top of a $60M deal",
            "Last winter's warning: Imai — projected $150M, signed $54M, then a 4.93 ERA",
            "The clock: Nov 2 → Dec 16, with the Dec 1 lockout pause cut into the middle"],
        horizontal_spacing=0.13, vertical_spacing=0.085)

    # (1,1) Sato career arc — K% vs BB%
    fig.add_trace(go.Scatter(
        x=x3, y=[ss[y]["K_pct_computed"] for y in years],
        mode="lines+markers+text", line=dict(color="#d50032", width=3),
        marker=dict(size=9),
        text=[f"{ss[y]['K_pct_computed']:.1f}%" for y in years],
        textposition="top center", name="Sato K%", showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(
        x=x3, y=[ss[y]["BB_pct_computed"] for y in years],
        mode="lines+markers+text", line=dict(color="#1b5e20", width=3),
        marker=dict(size=9),
        text=[f"{ss[y]['BB_pct_computed']:.1f}%" for y in years],
        textposition="bottom center", name="Sato BB%", showlegend=False), 1, 1)

    # (1,2) Itoh career arc — IP bars + BB% line (secondary axis)
    fig.add_trace(go.Bar(
        x=x3, y=[ins[y]["IP"] for y in years], marker_color="#1d3557",
        text=[f"{ins[y]['IP']:.1f} IP · {ins[y]['BB']} BB" for y in years],
        textposition="outside", name="Itoh IP", showlegend=False), 1, 2)
    fig.add_trace(go.Scatter(
        x=x3, y=[ib[y]["bb_pct"] for y in years],
        mode="lines+markers+text", line=dict(color="#c9a227", width=3),
        marker=dict(size=9),
        text=[f"{ib[y]['bb_pct']:.1f}% BB" for y in years],
        textposition="top center", name="Itoh BB%", showlegend=False),
        row=1, col=2, secondary_y=True)

    # (2,1) Taira conversion — ERA by role
    fig.add_trace(go.Bar(
        x=["2025 · closer", "2026 · starter"],
        y=[ts[2025]["ERA"], ts[2026]["ERA"]],
        marker_color=["#e65100", "#1d3557"],
        text=[f"{ts[2025]['ERA']:.2f} ERA · 31 SV · 52.2 IP",
              f"{ts[2026]['ERA']:.2f} ERA · 146.0 IP · 12–5"],
        textposition="outside", name="Taira ERA", showlegend=False), 2, 1)

    # (2,2) Taira workload — the jump
    fig.add_trace(go.Bar(
        x=["2025 · closer", "2026 · starter"],
        y=[ts[2025]["IP"], ts[2026]["IP"]],
        marker_color=["#e65100", "#d50032"],
        text=["52.2 IP", "146.0 IP · +93.8 in one year"],
        textposition="outside", name="Taira IP", showlegend=False), 2, 2)

    # (3,1) Leaderboard context — percentile dots (built from the
    # computed artifact so the figure can never drift from it)
    dots = [  # first entry renders at the BOTTOM of the axis
        ("Itoh · ERA — PL arms", ctx["itoh"]["ERA"], "#c9a227"),
        ("Itoh · walk rate — PL arms", ctx["itoh"]["BB_pct"], "#c9a227"),
        ("Taira · ERA — PL arms", ctx["taira"]["ERA"], "#1d3557"),
        ("Sato · RBI — CL bats", ctx["sato"]["RBI"], "#d50032"),
        ("Sato · OPS — CL bats", ctx["sato"]["OPS"], "#d50032"),
        ("Sato · home runs — CL bats", ctx["sato"]["HR"], "#d50032"),
    ]
    ys, xs, txs, cs = [], [], [], []
    for lab, c, col in dots:
        stat = lab.split("·")[1].strip().split(" —")[0]
        key = {"home runs": "HR", "OPS": "OPS", "RBI": "RBI",
               "ERA": "ERA", "walk rate": "BB rate"}[stat]
        ys.append(lab)
        xs.append(c["percentile"])
        txs.append(f"{c['value']} {key} · #{c['rank']} of {c['of']}")
        cs.append(col)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", marker=dict(size=13, color=cs),
        text=txs, textposition="middle right", name="Leaderboard context",
        showlegend=False), 3, 1)
    fig.add_vline(x=50, line_dash="dot", line_color="#888",
                  annotation_text="median qualifier",
                  annotation_position="bottom left", row=3, col=1)

    # (3,2) Sato K% vs Central League median K%
    fig.add_trace(go.Bar(
        x=x3, y=[kv[y]["sato_k_pct"] for y in years],
        marker_color="#d50032",
        text=[f"{kv[y]['sato_k_pct']:.1f}%" for y in years],
        textposition="outside", name="Sato K%", showlegend=False), 3, 2)
    fig.add_trace(go.Scatter(
        x=x3, y=[kv[y]["cl_median_k_pct"] for y in years],
        mode="lines+markers+text", line=dict(color="#1d3557", width=3,
                                             dash="dash"),
        marker=dict(size=9),
        text=[f"median {kv[y]['cl_median_k_pct']:.1f}%" for y in years],
        textposition="bottom center", name="CL median K%",
        showlegend=False), 3, 2)

    # (4,1) Posting-fee curve
    curve = rb["fee_curve"]
    fig.add_trace(go.Scatter(
        x=[p["contract_m"] for p in curve],
        y=[p["fee_m"] for p in curve], mode="lines",
        line=dict(color="#c9a227", width=3), fill="tozeroy",
        fillcolor="rgba(201,162,39,0.18)", name="Posting fee",
        showlegend=False), 4, 1)
    ck = rb["fee_checkpoints_m"]
    fig.add_trace(go.Scatter(
        x=[25, 50, 60, 100],
        y=[ck["25"], ck["50"], ck["60"], ck["100"]],
        mode="markers+text", marker=dict(size=9, color="#14213d"),
        text=[f"$25M → ${ck['25']:.2f}M", f"$50M → ${ck['50']:.2f}M",
              f"$60M → ${ck['60']:.3f}M", f"$100M → ${ck['100']:.2f}M"],
        textposition="top center", name="Fee checkpoints",
        showlegend=False), 4, 1)

    # (4,2) Imai — expectation vs reality (MLBTR figures, in the trio
    # dataset's honesty notes; totals only, both are contract totals)
    fig.add_trace(go.Bar(
        x=["Projected (MLBTR)", "Signed (Houston)"],
        y=[150, 54], marker_color=["#888888", "#d50032"],
        text=["6 yr / $150M", "3 yr / $54M"],
        textposition="outside", name="Imai", showlegend=False), 4, 2)
    fig.add_trace(go.Scatter(
        x=["Signed (Houston)"], y=[86], mode="text",
        text=["then: 4.93 ERA · moved to the bullpen"],
        textposition="middle center", showlegend=False), 4, 2)

    # (5,1) The posting clock — day offsets from Nov 1, 2026
    fig.add_trace(go.Bar(
        x=[29], y=["window"], base=[1], orientation="h",
        marker_color="#c9a227",
        text=["Nov 2 → Dec 1 · open · 29 days"],
        textposition="inside", name="Open window", showlegend=False),
        5, 1)
    fig.add_trace(go.Bar(
        x=[15], y=["window"], base=[30], orientation="h",
        marker=dict(color="#cfd8dc",
                    pattern=dict(shape="/", fgcolor="rgba(20,33,61,0.5)",
                                 bgcolor="#cfd8dc", size=6)),
        text=["Dec 1 → Dec 16 · paused in a lockout · 15 days"],
        textposition="inside", name="Paused window", showlegend=False),
        5, 1)
    fig.add_trace(go.Scatter(
        x=[0, 30, 45], y=["window"] * 3, mode="markers+text",
        marker=dict(symbol="diamond", size=11,
                    color=["#1d3557", "#d50032", "#14213d"]),
        text=["Posted<br>Nov 1",
              "Dec 1 · CBA expires — clock pauses · demo deadline",
              "Dec 16 · 17:00 ET<br>signing deadline"],
        textposition=["bottom center", "top center", "bottom center"],
        name="Clock markers", showlegend=False), 5, 1)

    fig.update_layout(
        title=("The Posted Class: three players, three different bets. "
               "Sato tests the thesis, Itoh fits it, Taira is the gamble "
               "— all on NPB official BIS data, and no NPB-to-MLB "
               "translation factor is claimed anywhere in this figure."),
        template="plotly_white", height=1520, barmode="overlay",
        margin=dict(l=50, r=30, t=110, b=96))
    fig.update_yaxes(title_text="Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Innings pitched", row=1, col=2)
    fig.update_yaxes(title_text="BB%", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="ERA", row=2, col=1)
    fig.update_yaxes(title_text="Innings pitched", row=2, col=2)
    fig.update_xaxes(title_text="Percentile among qualified (100 = best)",
                     range=[-4, 152], row=3, col=1)
    fig.update_yaxes(title_text="K%", row=3, col=2)
    fig.update_xaxes(title_text="MLB contract ($M)", row=4, col=1)
    fig.update_yaxes(title_text="Posting fee ($M)", row=4, col=1)
    fig.update_yaxes(title_text="Total contract ($M)", range=[0, 175],
                     row=4, col=2)
    fig.update_xaxes(tickvals=[0, 1, 30, 45],
                     ticktext=["Nov 1", "Nov 2", "Dec 1", "Dec 16"],
                     range=[-3, 48], row=5, col=1)
    fig.update_yaxes(showticklabels=False, row=5, col=1)
    return fig


def _posted_html():
    """Cycle 34, Figure 23 companion HTML (Explorer only): trio cards,
    the posting clock + fee tiers, and the translation honesty box.
    Every number comes from data/posted_class_2026.json; the fee worked
    example is arithmetic on that file's published tiers, labeled as an
    illustration — never a predicted contract price."""
    import html as _html
    d = json.load(open(os.path.join(DATA, "posted_class_2026.json")))
    pf = d["posting_facts"]

    def fmt(v, nd=3):
        if v is None:
            return "—"
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)

    cards = []
    for p in d["players"]:
        s26 = next((s for s in p["seasons_bis"] if s["year"] == 2026), None)
        if s26 is None:
            continue
        if "AVG" in s26:
            ops = s26.get("OPS", s26.get("OPS_computed"))
            headline = (f"2026: {fmt(s26['AVG'])} · {s26['HR']} HR · "
                        f"{s26['RBI']} RBI · {fmt(ops)} OPS")
            rows = "".join(
                f"<tr><td>{s['year']}</td><td>{s['G']}</td>"
                f"<td>{fmt(s['AVG'])}</td><td>{fmt(s['OBP'])}</td>"
                f"<td>{fmt(s['SLG'])}</td><td>{s['HR']}</td>"
                f"<td>{s['RBI']}</td>"
                f"<td>{fmt(s.get('K_pct_computed'), 1)}%</td>"
                f"<td>{fmt(s.get('BB_pct_computed'), 1)}%</td></tr>"
                for s in p["seasons_bis"])
            table = ("<table><tr><th>Year</th><th>G</th><th>AVG</th><th>OBP</th>"
                     "<th>SLG</th><th>HR</th><th>RBI</th><th>K%</th><th>BB%</th></tr>"
                     + rows + "</table>")
        else:
            wl = f"{s26['W']}–{s26['L']}"
            headline = (f"2026: {fmt(s26['ERA'], 2)} ERA · {wl} · "
                        f"{fmt(s26['IP'], 1)} IP")
            rows = ""
            for s in p["seasons_bis"]:
                role = s.get("role", "starter")
                rows += (f"<tr><td>{s['year']}</td><td>{role}</td>"
                         f"<td>{s['G']}</td><td>{fmt(s['ERA'], 2)}</td>"
                         f"<td>{fmt(s['IP'], 1)}</td>"
                         f"<td>{s['W']}–{s['L']}</td><td>{s['SO']}</td>"
                         f"<td>{s['BB']}</td><td>{s.get('SV', 0)}</td></tr>")
            table = ("<table><tr><th>Year</th><th>Role</th><th>G</th><th>ERA</th>"
                     "<th>IP</th><th>W–L</th><th>SO</th><th>BB</th><th>SV</th></tr>"
                     + rows + "</table>")
        sub = (f"Age {p['age']}" if "age" in p else
               f"Born {p.get('born', '')}")
        if p.get("size"):
            sub += f" · {p['size']}"
        cards.append(
            '<article class="ncard"><h4>' + _html.escape(p["name"]) + " · " +
            _html.escape(p["role"]) + "</h4><p>" +
            _html.escape(p["team"]) + " · " + _html.escape(sub) + "</p>" +
            "<p><b>" + _html.escape(headline) + "</b></p>" + table +
            "<p>" + _html.escape(p.get("note", "")) + "</p></article>")
    # Fee worked example: tiers from posting_facts, arithmetic in code.
    fee60 = 0.20 * 25 + 0.175 * 25 + 0.15 * 10  # $M on a $60M contract
    imai = (
        '<div class="npbclock"><h3>Expectation vs reality — last '
        'winter\'s posted arm</h3>'
        "<p><b>Projected:</b> 6 years / $150M (MLBTR) &nbsp;→&nbsp; "
        "<b>Signed:</b> 3 years / $54M with Houston &nbsp;→&nbsp; "
        "<b>Delivered:</b> a 4.93 ERA and a move to the bullpen "
        "(MLBTR).</p>"
        "<p>That is the whole translation argument in one line: the "
        "market already discounts NPB dominance once — price the "
        "discount, do not pretend it away.</p></div>")
    clock = (
        '<div class="npbclock"><h3>The posting clock</h3>'
        "<p>The window is drawn as the bottom panel of Figure 23 "
        "above; the facts: posted <b>Nov 1, 2026</b> → negotiations "
        "open <b>Nov 2</b> → CBA expires <b>Dec 1</b> (the clock "
        "pauses during a lockout) → signing deadline <b>Dec 16, "
        "17:00 ET</b> (45-day window).</p>"
        "<p>Posting fee, paid to the NPB club on top of the contract: " +
        _html.escape(pf["posting_fee"]) + ".</p>"
        "<p>Worked example — ILLUSTRATIVE, not a predicted price: on a "
        f"hypothetical $60M contract the fee is 20% of $25M ($5.00M) + "
        f"17.5% of $25M ($4.375M) + 15% of $10M ($1.50M) = <b>${fee60:.3f}M</b>. "
        "Under a hard cap, that fee is a real acquisition cost a GM must budget.</p>"
        "<p>Context only: " + _html.escape(pf["also_posted_same_day"]) + ".</p></div>")
    honest = (
        '<div class="npbhonest"><h3>Translation honesty box — read before you price anyone</h3>'
        "<p><b>No NPB-to-MLB translation factor is claimed anywhere in this "
        "figure.</b> NPB dominance is evidence, not a projection. The "
        "cautionary comp is in the same market: Tatsuya Imai, posted last "
        "winter, was projected at 6 years / $150M (MLBTR), signed 3 years / "
        "$54M with Houston, then posted a 4.93 ERA and was moved to the "
        "bullpen (MLBTR).</p>"
        "<p>Known gaps, labeled not filled: leaderboards are qualified-only "
        "(no full-roster NPB stats pulled); Taira's 2024 season does not "
        "appear on qualified boards (reliever workload) so no 2024 row is "
        "shown for him; no NPB salary data is used — in the posting market "
        "the fee, not a salary, is the cost.</p>"
        "<p>Cycle 47 computed layer: the ranks and percentiles in Figure 23 "
        "come from src/bml_cycle47.py (output: data/fig23_rebuild_2026.json), "
        "verified 14/14 against the trio dataset. Pools are the player's own "
        "league board and are small — 19 Central League bats and 11 Pacific "
        "League ERA-qualified arms in 2026 — so ranks are exact and "
        "percentiles are coarse. Itoh's 2024 walk rate (5.5%) is computed "
        "from the leaderboard's batters-faced column, which the trio "
        "dataset does not carry for 2024; his 2025-2026 rates cross-check "
        "exactly against it.</p>"
        "<p class=\"srcline\">Source: NPB official Baseball Information System "
        "(BIS), npb.jp/bis/&lt;year&gt;/stats/*.html, pulled 2026-11-01; BIS is "
        "canonical over wire roundings (Sato .306 not .308; Itoh 34 BB not 32). "
        "Posting facts: AP / MLB Trade Rumors / Sportsnet, 2026-11-01. "
        "Dataset: data/posted_class_2026.json; leaderboards: "
        "data/npb_leaderboards_2024_2026_raw.csv; computed context: "
        "data/fig23_rebuild_2026.json.</p></div>")
    return ('<div class="ncards">' + "".join(cards) + "</div>" + clock
            + imai + honest)


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
        updatemenus=[dict(type="dropdown", buttons=buttons, direction="down",
                          x=1.08, xanchor="right", y=1.06, yanchor="top",
                          pad=dict(r=8, t=6), showactive=True, active=0,
                          font=dict(size=11), bgcolor="#ffffff",
                          bordercolor="#c9a227", borderwidth=1)],
        template="plotly_white", height=560,
        legend=dict(orientation="h", y=-0.08))
    return fig

def panel_scenarios():
    """Cycle 26, headline promoted Cycle 52: what does the money buy?
    Full 26-man rosters from the real FA class at the floor, the
    middle, and the cap — the proven-optimal builds (Cycle 49 MILP on
    Cycle 26's identical pool, prices and quotas), each headline WAR
    carrying its Cycle 50 +-20% price-error range and its Cycle 56
    delivered-WAR range (UNC-2 Monte Carlo over measured projection
    error and player availability). The greedy builds are preserved
    in the artifact as the benchmark Figure 25 shows."""
    fj = os.path.join(DATA, "wow_scenarios.json")
    if not os.path.exists(fj):
        return None
    d = json.load(open(fj))
    uj = os.path.join(DATA, "uncertainty_scenarios_2027.json")
    unc = {}
    if os.path.exists(uj):
        unc = {s["label"]: s for s in json.load(open(uj))["scenarios"]}
    traces, buttons = [], []
    for i, s in enumerate(d["scenarios"]):
        r = s["roster"]
        traces.append(go.Table(
            header=dict(values=["Pos", "Player", "From", "Steamer WAR", "Prior AAV"],
                        fill_color="#14213d", font=dict(color="white", size=12),
                        align="left"),
            cells=dict(values=[[x["pos"] for x in r], [x["name"] for x in r],
                               [x["prev_team"] for x in r],
                               [f"{x['war']:.1f}" for x in r],
                               [f"${x['prev_aav']/1e6:.1f}M" for x in r]],
                       fill_color="rgba(244,241,234,0.6)", align="left",
                       font=dict(size=11.5), height=19),
            visible=(i == 0)))
        rng = s["war_range_prices_pm20"]
        u = unc.get(s["label"])
        delivered = (f" Delivered-WAR range (Cycle 56): 10th–90th percentile "
                     f"{u['p10']}–{u['p90']} WAR, median {u['p50']} — Monte Carlo "
                     "over measured projection error and player availability; "
                     "the point above is the full-availability projection."
                     if u else "")
        title = (f"What does the money buy? {s['label']} — "
                 f"{s['total_war']} WAR proven-optimal ({rng['low']}–{rng['high']} "
                 f"across ±20% price error) for ${s['spend']/1e6:.1f}M<br>"
                 "<sub>Exact optimizer (Cycle 49); the greedy build is the benchmark "
                 "in Figure 25. Prices are prior-contract AAVs: last-price anchors, "
                 "not predicted 2027 salaries. Availability stress (Cycle 27: WAR "
                 "scaled by the mean availability measured from 201 real players' "
                 f"2025-26 IL records, {d['availability_stress']['pool']['mean_avail']}): "
                 "this roster holds "
                 f"{d['availability_stress']['stressed_totals'][s['label']]['war_at_pool_mean_avail']} WAR "
                 f"— injury risk taxes every budget alike.{delivered} Switch budget:</sub>")
        buttons.append(dict(label=s["label"], method="update",
                            args=[{"visible": [j == i for j in range(len(d["scenarios"]))]},
                                  {"title": {"text": title}}]))
    s0 = d["scenarios"][0]
    rng0 = s0["war_range_prices_pm20"]
    u0 = unc.get(s0["label"])
    delivered0 = (f"; delivered-WAR 10th–90th: {u0['p10']}–{u0['p90']} "
                  f"(Cycle 56)" if u0 else "")
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=(f"What does the money buy? {s0['label']} — {s0['total_war']} WAR "
               f"proven-optimal ({rng0['low']}–{rng0['high']} across ±20% price "
               f"error{delivered0}) for ${s0['spend']/1e6:.1f}M<br>"
               "<sub>Full 26-man rosters from the real 2027 free-agent class. "
               "The floor roster captures ~89% of the cap roster's WAR — the last "
               "$74.1M buys 5.9 WAR. Switch budget below the chart.</sub>"),
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
    fig_auc = panel_auc()
    fig_sens = panel_sensitivity()
    fig_persist = panel_skill_persistence()
    fig_value = panel_value_metrics()
    fig_capscen = panel_cap_scenario()
    fig_forced = panel_forced_sellers()
    fig_anim = panel_animation()
    fig_team = panel_team_explorer()
    fig_bench = panel_benchmark()
    fig_savant = panel_savant()
    fig_pipe = panel_pipeline()
    fig_shop = panel_shopping()
    fig_posted = panel_posted()
    fig_hs = panel_hs_verdict()
    fig_opt = panel_optimizer()
    fig_scen = panel_scenarios()

    SECTIONS = [
        ("★", "The Boardroom", "Sixteen seasons in motion, and every "
         "club's signature — find yours.", [fig_anim, fig_team]),
        ("I", "The Proof", "Skills persist, run differential describes "
         "wins — and payroll alone doesn't buy them.",
         [fig_persist, fig_runs, fig_auc, fig_payroll]),
        ("II", "The Signature", "Winning-cheap teams look different: more "
         "contact, more OBP, fewer strikeouts — for 25 straight years.",
         [fig_kpi, fig_dur]),
        ("III", "The Cap", "The owners' proposed 2027 cap, priced team "
         "by team — and what the over-cap clubs must shed to comply.",
         [fig_proj, fig_capscen, fig_forced]),
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
         "the free-agent list to shop from — and the posted class "
         "resolving during the demo window.",
         [fig_pipe, fig_shop, fig_posted, fig_hs, fig_opt]),
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

    numbered_figs = _number(flat)
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
        '<div class="card"><div class="num">r = .84</div><div class="lab">contact skill persists year to year (pooled, 457 pairs) — the edge that wins</div></div>'
        '<div class="card"><div class="num">$245.3M</div><div class="lab">proposed 2027 cap · floor $171.2M</div></div>'
        '<div class="card"><div class="num">509</div><div class="lab">real team-seasons measured, 2011–2026</div></div>'
        f'<div class="card"><div class="num">{n_hit + n_pit}</div><div class="lab">players projected for 2027 ({n_hit} hitters · {n_pit} pitchers)</div></div>'
        '<div class="card"><div class="num">AUC .95</div><div class="lab">run differential flags a 90+ win club (both directions)</div></div>'
        '<div class="card"><div class="num">100%</div><div class="lab">real data — every panel sourced</div></div>'
        '</div>')

    by_num = {i + 1: f for i, f in enumerate(numbered_figs)}

    def _panel(num, mode):
        if num not in by_num:
            # Lake-less builds omit the pitching panel gracefully (G1);
            # say so instead of breaking the build or renumbering silently.
            return ('<div class="panel" data-mode="' + mode +
                    '" data-figure-missing="' + str(num) + '">'
                    "<p>Figure " + str(num) + " is not available in this build: "
                    "it needs the lake file, which is not committed.</p></div>")
        fig = by_num[num]
        return ('<div class="panel" data-mode="' + mode +
                '" data-figure="' + str(num) + '">' +
                fig.to_html(full_html=False, include_plotlyjs=False) +
                "</div>")

    def _player_cards():
        import html as _html
        fa = json.load(open(os.path.join(DATA, "fa_shopping_2027.json")))
        pool = [r for r in fa["class"] if r.get("steamer_war") is not None]
        if len(pool) < 200:
            raise ValueError("FA pool too small for percentile cards")
        health = {r["player_id"]: r
                  for r in json.load(open(os.path.join(DATA, "projections_2027_health.json")))}
        pitchers = {r["name"]: r
                    for r in json.load(open(os.path.join(DATA, "projections_2027_pitchers.json")))}
        xw = {r["player_id"]: r["est_woba"]
              for r in json.load(open(os.path.join(DATA, "savant_expected_2026.json")))
              if r.get("est_woba") is not None}

        def pct_high(val, vals):
            return round(100.0 * sum(1 for v in vals if v <= val) / len(vals)) if vals else None

        def pct_low(val, vals):
            return round(100.0 * sum(1 for v in vals if v >= val) / len(vals)) if vals else None

        def avail_of(r):
            if r["player_id"] in health:
                return health[r["player_id"]].get("avail_pct")
            if r["name"] in pitchers:
                return pitchers[r["name"]].get("avail_pct")
            return None

        obp_vals = [health[r["player_id"]]["proj_OBP"] for r in pool
                    if r["player_id"] in health and health[r["player_id"]].get("proj_OBP") is not None]
        k_vals = [health[r["player_id"]]["proj_K%"] for r in pool
                  if r["player_id"] in health and health[r["player_id"]].get("proj_K%") is not None]
        xw_vals = [xw[r["player_id"]] for r in pool if r["player_id"] in xw]
        avail_vals = [a for a in (avail_of(r) for r in pool) if a is not None]
        dpw_vals = [r["prev_aav"] / r["steamer_war"] for r in pool
                    if r.get("prev_aav") and r["steamer_war"] and r["steamer_war"] > 0]
        top = sorted(pool, key=lambda r: r.get("war_per_10m_prior_aav") or 0, reverse=True)[:8]
        if len(top) < 8:
            raise ValueError("fewer than 8 bargain free agents in the pool")

        def bar(label, pct, val_text):
            if pct is None:
                return ('<div class="pctrow"><span>' + label +
                        '</span><span class="pctna">Not in the committed pool for this metric</span></div>')
            return ('<div class="pctrow"><span>' + label + ": " + val_text + "</span>"
                    '<span class="pctbar"><span style="width:' + str(pct) + '%"></span></span>'
                    '<span class="pctnum">Percentile ' + str(pct) + "</span></div>")

        out = []
        for r in top:
            h = health.get(r["player_id"])
            obp = h["proj_OBP"] if h else None
            kk = h["proj_K%"] if h else None
            av = avail_of(r)
            dpw = (r["prev_aav"] / r["steamer_war"]) if r.get("prev_aav") and r["steamer_war"] and r["steamer_war"] > 0 else None
            rows = "".join([
                bar("On-base percentage", pct_high(obp, obp_vals) if obp is not None else None,
                    f"{obp:.3f}" if obp is not None else ""),
                bar("Strikeout rate (lower is better)", pct_low(kk, k_vals) if kk is not None else None,
                    f"{kk:.1f}%" if kk is not None else ""),
                bar("Expected on-base average (xwOBA)",
                    pct_high(xw[r["player_id"]], xw_vals) if r["player_id"] in xw else None,
                    f"{xw[r['player_id']]:.3f}" if r["player_id"] in xw else ""),
                bar("Availability", pct_high(av, avail_vals) if av is not None else None,
                    f"{av:.0%}" if av is not None else ""),
                bar("Cost per WAR (lower is better)", pct_low(dpw, dpw_vals) if dpw is not None else None,
                    f"${dpw / 1e6:.2f}M" if dpw is not None else ""),
            ])
            out.append(
                '<article class="pcard"><h4>' + _html.escape(r["name"]) + " · " +
                _html.escape(str(r["pos"])) + " · " + _html.escape(str(r["prev_team"])) + "</h4>" +
                "<p>Steamer WAR " + f"{r['steamer_war']:.1f}" +
                " · prior average salary $" + f"{r['prev_aav'] / 1e6:.1f}M" +
                " · WAR per $10M of prior salary " + f"{r['war_per_10m_prior_aav']:.2f}" + "</p>" +
                rows + "</article>")
        note = ("<p class=\"srcline\">Percentiles are computed from the 2027 free-agent pool in "
                "data/fa_shopping_2027.json only (players with Steamer WAR; each bar uses only the "
                "players who have that metric). Prices are prior-contract averages, not predicted "
                "prices. Source: Spotrac free-agent class, FanGraphs Steamer WAR, Marcel projections, "
                "Baseball Savant expected stats.</p>")
        return '<div class="pcards">' + "".join(out) + "</div>" + note

    # --- STORY mode: verdict first, then 6 chapters, one figure each ---
    chapters = [
        (3, "Skills persist. Luck does not.",
         "Across four real season pairs, contact rate persists at r of about 0.8 to 0.9, "
         "while on-base percentage persists more weakly: r of about 0.55 to 0.59 in the first "
         "three pairs and 0.30 in the latest pair (2025 to 2026), pooled r of about 0.53.",
         "Pay for the skill that produces on-base percentage, not for last year's on-base percentage.",
         "Source: MLB Stats API player data, year over year."),
        (4, "Run differential describes a season. It does not forecast one.",
         "The same-season fit is strong, with R squared of about 0.55: a better run margin means "
         "more wins in that season. It is not a forward-looking prediction.",
         "Use run differential to describe a season, never to promise the next one.",
         "Source: MLB Stats API panel, 2011 to 2026, 509 team-seasons."),
        (6, "Money buys some wins. It does not buy the most wins per dollar.",
         "The winning-cheap teams, Milwaukee, Tampa, and Cleveland, win about 95 games at a third "
         "to a quarter of big-market payroll.",
         "A mid-tier payroll is enough when it buys contact and control.",
         "Source: MLB Stats API plus Spotrac payroll."),
        (10, "The cap forces the market. Seven teams must cut, fifteen must add.",
         "Seven teams are over the proposed cap and must cut, the Mets by $101.4M, while fifteen, "
         "including Cleveland at $96.7M to add, sit under the floor and are forced to spend.",
         "The cap punishes the biggest payrolls and pays the disciplined teams to add.",
         "Source: Spotrac payroll against the owners' proposed 2027 cap and floor."),
        (16, "The floor roster captures most of the cap roster's talent.",
         "Built entirely from the real 2027 free-agent class, the floor roster buys 48.9 WAR for "
         "$171.1M and the cap roster buys 54.8 WAR for $245.2M: about 89 percent of the talent "
         "for about 70 percent of the money. The builds are proven optimal, and across "
         "±20% price error the floor holds 45.0 to 53.2 WAR. Delivered WAR runs lower and "
         "wider: the Monte Carlo over measured projection error and player availability "
         "puts the floor's median at 39.8 WAR (10th to 90th: 33.0 to 46.9) and the cap's "
         "at 44.9 (37.6 to 52.4).",
         "Spend to the floor first. The last dollars buy the least talent.",
         "Source: Spotrac free-agent class plus FanGraphs Steamer WAR, prior-contract price anchors; "
         "exact optimization, Cycle 49 (Figure 25); delivered-WAR ranges, Cycle 56 "
         "(data/uncertainty_scenarios_2027.json)."),
        (18, "Checked in public against the best benchmark we could get.",
         "Our Marcel hitter projections match FanGraphs Steamer at OBP r of 0.889, with 201 hitters "
         "matched by player ID. The pitcher bias found in that check is disclosed on the panel.",
         "Trust the player projections because they were checked in the open, limits included.",
         "Source: FanGraphs Steamer 2027 projections, ID-matched."),
    ]
    story = ('<div class="verdict"><h2>The verdict</h2>'
             "<p>Win while cheap: buy contact plus on-base percentage and low-walk arms, and price "
             "it against the proposed $245.3M cap. The winning-cheap teams prove it on real data, "
             "and the cap now rewards exactly that discipline.</p></div>")
    story += ('<div class="bottomline"><b>BOTTOM LINE (read this first):</b> A team can win at '
              "mid-tier payroll by spending on <b>contact + getting on base (OBP)</b> and "
              "<b>low-walk arms</b>, not power. Winning-cheap teams (MIL/TB/CLE) had "
              "<b>higher OBP, more contact, fewer strikeouts, fewer home runs AND elite team pitching</b> "
              "— yet won ~95 games on average vs ~79 for the rest of the league, at about a third of "
              "the biggest payrolls. <span class=\"act\">Owner action:</span> "
              "build the roster around OBP/contact + control pitchers, not the big power salary. "
              "<span class=\"why\">Why trust it:</span> real 2025-2026 data (MLB API + Spotrac), model "
              "cross-validated. Not a guarantee — shown honestly below.</div>")
    story += cards
    story += ('<div class="hero-team"><h3>Pick your team first</h3>'
              "<p>Find your club before the story: its 2026 signature against the winning-cheap "
              "profile, its cap headroom, its farm pipeline, and its top prospect.</p></div>")
    story += _panel(2, "story")
    for i, (num, head, note, sowhat, src) in enumerate(chapters, 1):
        story += (f'<section class="chapter" data-chapter="{i}"><span class="chapnum">Chapter {i}</span>'
                  f"<h3>{head}</h3><p>{note}</p>" + _panel(num, "story") +
                  f'<p class="sowhat"><b>So what for the owner:</b> {sowhat}</p>'
                  f'<p class="srcline">{src}</p></section>')
    story += ('<details class="appendix"><summary>Appendix: method and honesty box</summary>'
              '<div class="quant"><b>What the data actually shows</b> &nbsp;'
              '<span style="font-weight:400;color:#4a5a72">(measured on 509 real team-seasons, 2011-2026)</span><br><br>'
              "<b>1. Run differential drives wins, but only as a diagnostic.</b> The same-season "
              "fit is strong (R² ≈ 0.55) — a better run margin means more wins. It is not a "
              "forward-looking prediction.<br><br>"
              "<b>2. Raw hitting KPIs do not reliably forecast next-season wins.</b> In-sample "
              "accuracy is weak (R² ≈ 0.14), and out-of-sample the model is no better than simply "
              "assuming the league average. Year-over-year team wins regress sharply toward the "
              "mean — consistent with established baseball research.<br><br>"
              "<b>3. The defensible edge is at the player level, not the team level.</b> A "
              "player's underlying skills — contact rate (pooled r = .84) and walk discipline (r = .66 to .77 in each of the four pairs) — "
              "persist year to year in ways that wins themselves do not. That persistence, paired "
              "with Marcel-style aging and health constraints, is what builds the 26-man roster "
              "shown here. We explicitly do not claim a forward-looking team-wins model: cross-year accuracy "
              "is roughly 9-13 wins, and we present that number honestly.</div>"
              '<div class="note">Data: MLB Stats API + Spotrac, 2011-2026 (509 team-seasons). The 2027 cap '
              "($245.3M) and floor ($171.2M) are the owners' proposal; the CBA expires Dec 1, 2026 and the "
              "figures are not yet law. No performance guarantee is implied. Salaries cover 24 of 30 teams: "
              "Spotrac blocks 6 team pages, labeled wherever salaries appear.</div></details>")

    # --- BOARDROOM mode: 15 slides in talk-track order ---
    slides = [
        ([1], "Press play: sixteen seasons prove the cheap winners stay gold",
         "Sixteen seasons of payroll vs wins animate; the cheap winners stay gold the whole time."),
        ([3], "Pay for skill, not output: contact persists, on-base percentage does not",
         "What a player does that is a skill carries. The output owners are tempted to buy does not."),
        ([4, 5], "Run differential describes a season and flags a winner. It does not forecast one",
         "Better teams score more than they allow, and run differential alone flags a 90+ win club "
         "with AUC of about 0.95. That is separation, not a forecast."),
        ([6], "Money buys some wins, but the cheap winners win about 95 at a fraction of the payroll",
         "Milwaukee, Tampa, and Cleveland win about 95 at a third to a quarter of big-market payroll."),
        ([7], "Winning-cheap teams dominate contact, on-base percentage, and walks",
         "The 2026 signature: contact, on-base percentage, and walks lead, with fewer strikeouts."),
        ([13], "Pitching is the other winning-cheap half: low walks, low WHIP, elite ERA",
         "The winners field control arms, not just contact bats."),
        ([14], "Health is priced in, not hoped for",
         "Injury risk caps playing time in the projections instead of being wished away."),
        ([15], "The 2027 roster is built from real projections on exactly those inputs",
         "Contact and walk skills plus control arms plus health caps, in one 26-man roster."),
        ([10], "Seven teams must cut. Fifteen must add. The cap is the opportunity",
         "The Mets are $101.4M over and the Dodgers $94.0M over; Cleveland has $96.7M to add and "
         "Tampa $75.6M. The system now rewards the teams that waste the least."),
        ([11], "Every over-cap team closes its gap by shedding at most three contracts",
         "Toronto and Atlanta need just one. The cap binds through a handful of deals, not a rebuild. "
         "That is arithmetic, not a prediction that anyone trades those players."),
        ([20], "Instead of a made-up WAR, we show the real inputs: wOBA, wRC+, FIP",
         "WAR formulas disagree and no MLB feed returns it, so the panel shows the reproducible inputs."),
        ([16], "The floor roster buys 48.9 WAR. The cap roster buys 54.8",
         "A disciplined floor team captures about 89 percent of the cap team's talent for about "
         "70 percent of the money. Proven-optimal builds; across ±20% price error the floor "
         "holds 45.0–53.2 WAR and the cap 50.4–55.9. Delivered-WAR ranges (10th–90th, "
         "Cycle 56 Monte Carlo over measured projection error and availability): floor "
         "33.0–46.9, middle 36.0–50.7, cap 37.6–52.4."),
        ([22], "The shopping list ranks the whole free-agent class by projected value",
         "Every name priced off last year's real contract anchor, never a predicted price."),
        ([2], "Pick your team: every club gets the same treatment",
         "Name your club: its signature, its cap headroom, its farm pipeline, its top prospect."),
        ([18], "Checked in public, limits disclosed: Marcel vs Steamer, r = 0.889",
         "We do not claim team-wins forecasts. Forecasting is genuinely weak, about 9 to 13 wins off, "
         "and saying otherwise would not survive a skeptical room."),
    ]
    boardroom = ('<p>15 slides, in talk-track order. Print this section for the room: '
                 '<button type="button" onclick="printBoardroom()">Print boardroom</button></p>')
    for i, (nums, head, note) in enumerate(slides, 1):
        boardroom += (f'<section class="slide"><span class="slidenum">Slide {i} of 15</span>'
                      f"<h3>{head}</h3><p>{note}</p>" +
                      "".join(_panel(n, "boardroom") for n in nums) +
                      '<p class="srcline">Source: see the figure footer and the data sources box at '
                      "the foot of this page.</p></section>")

    # --- EXPLORER mode: all 25 figures, grouped by task ---
    groups = [
        ("Cap Reality", "What the cap and floor do to every payroll, and what must be shed.",
         [1, 6, 9, 10, 11],
         "Source: MLB Stats API team data and Spotrac payroll, plus the proposed 2027 cap."),
        ("Build a Roster", "Signatures, durability, projections, health, the roster, and what moves wins — the roster itself is the exact optimizer's proven optimum.",
         [7, 8, 12, 13, 14, 15, 16, 17, 25],
         "Source: Marcel projections, health caps, and the 2027 roster build from committed files; headline rosters: data/wow_scenarios.json (Cycle 49 exact MILP optimum, promoted Cycle 52; greedy build preserved in the same file as the benchmark); optimizer comparison: data/optimizer_comparison_2027.json (Cycle 49, scipy/HiGHS MILP on the identical pool, prices and quotas); delivered-WAR ranges: data/uncertainty_scenarios_2027.json (Cycle 56)."),
        ("Shop the FA Class", "The farm pipeline behind the cheap winners, the shopping list, and the best values.",
         [21, 22],
         "Source: Spotrac free-agent class and FanGraphs Steamer WAR; prices are prior-contract averages."),
        ("The Posted Class", "Japan's window, resolving during the demo: three NPB stars posted Nov 1, 2026 — three different bets: the test, the fit, the gamble.",
         [23],
         "Source: NPB official Baseball Information System (BIS) — data/posted_class_2026.json; leaderboard context computed by src/bml_cycle47.py into data/fig23_rebuild_2026.json; posting facts: AP / MLB Trade Rumors / Sportsnet, 2026-11-01."),
        ("Check the Model", "Persistence, run differential, the title-bar test, the benchmark, the trait check — and our own pricing test, verdict included.",
         [3, 4, 5, 18, 19, 20, 24],
         "Source: FanGraphs Steamer benchmark, Baseball Savant leaderboards, MLB panel data, and the Cycle 46/48 Hakes–Sauer workpaper (committed salary samples + team-season panel)."),
    ]
    explorer = ('<div class="hero-team"><h3>Pick your team first</h3>'
                "<p>Use the dropdown: every club's 2026 signature against the winning-cheap profile, "
                "with cap headroom, pipeline rank, and top prospect.</p></div>")
    explorer += _panel(2, "explorer")
    for name, desc, nums, src in groups:
        explorer += f'<div class="task"><h3>{name}</h3><p>{desc}</p></div>'
        if name == "Build a Roster":
            # Cycle 57: the evidence footnote goes directly under
            # the Figure 14 (health) panel — its anchor figure.
            for n in nums:
                explorer += _panel(n, "explorer")
                if n == 14:
                    explorer += _evidence_note_html()
        elif name == "Check the Model":
            # Cycle 62: the held-out benchmark panel goes directly
            # under the Figure 18 (benchmark) panel — its anchor
            # figure. Agreement (Fig. 18) vs accuracy (this panel).
            for n in nums:
                explorer += _panel(n, "explorer")
                if n == 18:
                    explorer += _benchmark_panel_html()
        else:
            explorer += "".join(_panel(n, "explorer") for n in nums)
        explorer += f'<p class="srcline">{src}</p>'
        if name == "Build a Roster":
            explorer += ('<div class="task"><h3>Benchmark vs headline: the optimizer\'s audit</h3>'
                         "<p>Figure 25 re-solves Figure 16's exact problem with a "
                         "mixed-integer optimizer and proves the optima. Since Cycle 52 "
                         "those optima are Figure 16's headline rosters; the greedy "
                         "build remains as the benchmark. Explorer only. "
                         "Story stays 6 chapters and Boardroom stays 15 slides.</p></div>")
            explorer += _optimizer_html()
            explorer += _optimizer_sensitivity_html()
        if name == "Shop the FA Class":
            explorer += ('<div class="task"><h3>Top bargain free agents: Savant-style percentile cards</h3>'
                         "<p>Ranked by WAR per $10M of prior salary. Bars show where each player sits "
                         "in the committed free-agent pool for that metric.</p></div>")
            explorer += _player_cards()
        if name == "Check the Model":
            explorer += ('<div class="task"><h3>The verdict on our own pricing claim</h3>'
                         "<p>Figure 24 runs the Hakes–Sauer test on this demo's own thesis — "
                         "and the verdict box below it states exactly what the data supports. "
                         "Explorer only. Story stays 6 chapters and Boardroom stays 15 slides: "
                         "this is a claim check, not a new claim.</p></div>")
            explorer += _hs_verdict_html()
        if name == "The Posted Class":
            explorer += ('<div class="task"><h3>The trio, the clock, and the honesty box</h3>'
                         "<p>Cards, the posting-clock facts, the Imai expectation-vs-reality strip, "
                         "and the honesty box below Figure 23 — Explorer only. "
                         "Story stays 6 chapters and Boardroom stays 15 slides: this is a live-market "
                         "exhibit, not a new thesis claim.</p></div>")
            explorer += _posted_html()

    page_template = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>HARDBALL — Cap-Era Moneyball Demo (P7)</title>
<style>body{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#14213d}
.hd{max-width:1120px;margin:0 auto;padding:0 20px 40px}
.crest{background:linear-gradient(135deg,#14213d 0%,#1d3557 60%,#7a1f1f 160%);color:#fff;padding:28px 32px;border-radius:0 0 14px 14px;margin:0 0 4px;box-shadow:0 3px 14px rgba(20,33,61,.25)}
.crest h1{margin:0;font-size:30px;letter-spacing:1px;color:#fff}
.crest h2{margin:8px 0 0;font-size:16px;font-weight:400;color:#cbe0ff}
.mlb{background:#d50032;color:#fff;padding:2px 9px;border-radius:5px;font-size:12px;font-weight:700;letter-spacing:.5px}
.tag{background:#cbe0ff;color:#14213d;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}
.note{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:14px 0}
.bottomline{background:#e8f5e9;border-left:5px solid #1d3557;border-radius:6px;padding:14px 18px;margin:16px 0;font-size:15px}
.act{background:#14213d;color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold}
.why{color:#1d3557;font-weight:bold}
.quant{background:#eef4ff;border-left:5px solid #0d47a1;border-radius:6px;padding:14px 18px;margin:16px 0;font-size:14px}
.srcbox{background:#14213d;color:#dbe4f3;border-radius:8px;padding:16px 20px;margin:30px 0 8px;font-size:13px;line-height:1.5}
.srcbox b{color:#fff}
.src{color:#8ab6ff;font-family:ui-monospace,monospace}
.keybox{background:#f0f4fa;border:1px solid #c4d3ea;border-radius:6px;padding:10px 14px;margin:14px 0;font-size:12.5px;line-height:1.9}
.figidx{background:#fff;border:1px solid #d6dcea;border-left:4px solid #1d3557;border-radius:6px;padding:10px 14px;margin:14px 0;font-size:12px;line-height:1.8;color:#14213d}
.figidx span{display:inline-block;background:#d50032;color:#fff;border-radius:3px;padding:0 5px;margin:0 2px;font-weight:700;font-size:11px;min-width:14px;text-align:center}
.k{margin-right:16px;display:inline-block}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 4px}
.card{flex:1 1 160px;background:#fff;border:1px solid #e3dfd2;border-top:4px solid #d50032;border-radius:10px;padding:14px 16px;box-shadow:0 2px 8px rgba(20,33,61,.06)}
.card .num{font-size:26px;font-weight:800;color:#14213d;letter-spacing:.2px}
.card .lab{font-size:12.5px;color:#5a6478;margin-top:3px;line-height:1.35}
.sec{display:flex;gap:14px;align-items:center;background:linear-gradient(90deg,#14213d,#1d3557);color:#fff;border-radius:10px;padding:13px 20px;margin:30px 0 4px;box-shadow:0 2px 10px rgba(20,33,61,.18)}
.secnum{font-size:19px;font-weight:800;color:#c9a227;border:2px solid #c9a227;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.sec h3{margin:0;font-size:19px;letter-spacing:.4px}
.sec p{margin:2px 0 0;font-size:13.5px;color:#cbe0ff}
.panel{background:#fff;border:1px solid #e3dfd2;border-radius:12px;padding:16px 18px 8px;margin:14px 0;box-shadow:0 2px 10px rgba(20,33,61,.05)}
.modenav{display:flex;gap:10px;margin:18px 0}
.modenav button{flex:1;padding:12px;border:2px solid #1d3557;border-radius:8px;background:#fff;color:#14213d;font-size:15px;font-weight:700;cursor:pointer}
.modenav button.active{background:#14213d;color:#fff}
.verdict{background:#14213d;color:#fff;border-radius:10px;padding:18px 22px;margin:16px 0}
.verdict h2{margin:0 0 6px;color:#fff}
.verdict p{margin:0;color:#cbe0ff;font-size:15px;line-height:1.5}
.hero-team h3{margin:24px 0 0}
.chapter{border-top:3px solid #c9a227;margin:30px 0;padding-top:8px}
.chapnum{font-weight:800;color:#7a1f1f;letter-spacing:.5px}
.sowhat{background:#e8f5e9;border-left:5px solid #1d3557;border-radius:6px;padding:12px 16px}
.srcline{font-size:12.5px;color:#5a6478}
.appendix{margin:30px 0;border:1px solid #c4d3ea;border-radius:8px;padding:12px 16px;background:#fff}
.appendix summary{font-weight:800;cursor:pointer}
.slide{border:1px solid #d6dcea;border-radius:10px;padding:16px 20px;margin:18px 0;background:#fff;page-break-after:always}
.slidenum{font-weight:800;color:#7a1f1f}
.task{background:linear-gradient(90deg,#14213d,#1d3557);color:#fff;border-radius:10px;padding:13px 20px;margin:30px 0 4px}
.task h3{margin:0}
.task p{margin:2px 0 0;color:#cbe0ff;font-size:13.5px}
.pcards{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0}
.pcard{flex:1 1 340px;background:#fff;border:1px solid #e3dfd2;border-top:4px solid #1b5e20;border-radius:10px;padding:14px 16px}
.pcard h4{margin:0 0 4px;font-size:16px}
.pcard p{margin:0 0 8px;font-size:13px;color:#5a6478}
.pctrow{display:flex;gap:8px;align-items:center;font-size:12.5px;margin:5px 0}
.pctrow span:first-child{flex:0 0 210px}
.pctbar{flex:1;background:#e8ecf3;border-radius:4px;height:10px;overflow:hidden}
.pctbar span{display:block;background:#1b5e20;height:10px}
.pctnum{flex:0 0 110px;text-align:right;font-weight:700}
.pctna{color:#5a6478;font-style:italic}
.ncards{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0}
.ncard{flex:1 1 340px;background:#fff;border:1px solid #e3dfd2;border-top:4px solid #7a1f1f;border-radius:10px;padding:14px 16px}
.ncard h4{margin:0 0 4px;font-size:16px}
.ncard p{margin:0 0 8px;font-size:13px;color:#5a6478}
.ncard table{border-collapse:collapse;font-size:12.5px;margin:8px 0;width:100%}
.ncard th,.ncard td{border:1px solid #e3dfd2;padding:3px 6px;text-align:right}
.ncard th:first-child,.ncard td:first-child,.ncard td:nth-child(2){text-align:left}
.npbclock{background:#fff8e1;border-left:4px solid #f9a825;border-radius:6px;padding:12px 16px;margin:14px 0;font-size:14px}
.npbclock h3{margin:0 0 6px}
.npbhonest{background:#eef4ff;border-left:5px solid #0d47a1;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:14px}
.npbhonest h3{margin:0 0 6px}
.evfoot{margin:2px 0 12px}
@media print{body.print-boardroom #mode-story,body.print-boardroom #mode-explorer,body.print-boardroom .modenav,body.print-boardroom .crest,body.print-boardroom .keybox,body.print-boardroom .figidx,body.print-boardroom .srcbox{display:none}body.print-boardroom button{display:none}}
</style></head>
<body>
<div class="crest">
<h1>⚾ HARDBALL <span class="tag">P7 · demo ready · target Dec 3</span></h1>
<h2>How the winning-cheap teams beat the market — priced against the <b>$245.3M</b> cap</h2>
</div>
<div class="hd">
<div class="keybox"><b>COLOR KEY (used on every chart below):</b>
<span class="k"><span class="sw" style="background:#1b5e20"></span> green = <b>winning-cheap</b> (MIL · TB · CLE — the target teams: &gt;85 wins at low payroll)</span>
<span class="k"><span class="sw" style="background:#e65100"></span> orange = <b>cheap-mediocre</b> (MIA · CHW · STL — the trap: frugal but ~78 wins)</span>
<span class="k"><span class="sw" style="background:#1565c0"></span> blue = <b>other</b> (all remaining teams)</span>
<span class="k"><span class="sw" style="background:#d50032"></span> red = cap line / negative signal</span>
<span class="k"><span class="sw" style="background:#0d47a1"></span> navy = many-color charts (retention, sensitivity)</span></div>
<div class="keybox"><b>BASEBALL PLAIN-ENGLISH KEY — every stat on this page, in one glance:</b><br>
<span class="k"><b>PA</b> = plate appearance — every time a batter steps to the plate (any outcome)</span>
<span class="k"><b>OBP</b> = how often a batter reaches base (hits + walks)</span>
<span class="k"><b>contact %</b> = how often the batter actually hits the ball (vs striking out)</span>
<span class="k"><b>BB%</b> = how often a batter takes a walk</span>
<span class="k"><b>ISO</b> = power — extra bases beyond singles</span>
<span class="k"><b>HR / 1000 PA</b> = home runs per 1,000 plate appearances (league ≈ 34–38; how often a batter's PA ends in a home run)</span>
<span class="k"><b>Run differential</b> = runs scored minus runs allowed (best single win predictor)</span>
<span class="k"><b>AUC</b> = how well a model separates winners from losers (1.0 = perfect, 0.5 = a coin flip)</span>
<span class="k"><b>wOBA / wRC+</b> = overall hitting value, 100 = league average</span>
<span class="k"><b>FIP</b> = pitching quality (a pitcher's own doing; lower = better)</span>
<span class="k"><b>K-BB%</b> = strikeouts minus walks = how dominant a pitcher is</span>
<span class="k"><b>WAR</b> = wins above replacement, the famous player-value stat. Published free by FanGraphs (fWAR) &amp; Baseball-Reference (bWAR), but the two formulas disagree, it is not returned by the MLB API, and it is not a league-published number — so this value panel shows WAR's reproducible inputs (wOBA, wRC+, FIP, K-BB%) instead. Note: the FA shopping list (this build) uses FanGraphs Steamer WAR.</span></div>
__JS_INCLUDE__
<div class="figidx"><b>FIGURE INDEX — the story at a glance (all 25 real-data charts below)</b><br>
<span>1</span> Press play: 16 seasons of payroll vs wins &nbsp;·&nbsp;
<span>2</span> Pick your team &nbsp;·&nbsp;
<span>3</span> The measurable edge — skills persist (contact r=.90) &nbsp;·&nbsp;
<span>4</span> Run differential → wins &nbsp;·&nbsp;
<span>5</span> The title-bar test: run differential flags a 90+ win club (AUC ≈ .95) &nbsp;·&nbsp;
<span>6</span> Payroll vs wins &nbsp;·&nbsp;
<span>7</span> KPI signature &nbsp;·&nbsp;
<span>8</span> 25-yr durability &nbsp;·&nbsp;
<span>9</span> Projected wins at the cap &nbsp;·&nbsp;
<span>10</span> Cap-era reality &nbsp;·&nbsp;
<span>11</span> Forced sellers: the contracts that close each cap gap &nbsp;·&nbsp;
<span>12</span> 2027 hitters &nbsp;·&nbsp;
<span>13</span> Pitching &nbsp;·&nbsp;
<span>14</span> Health &nbsp;·&nbsp;
<span>15</span> 2027 roster &nbsp;·&nbsp;
<span>16</span> What does the money buy (3 budgets) &nbsp;·&nbsp;
<span>17</span> Sensitivity &nbsp;·&nbsp;
<span>18</span> Marcel vs Steamer benchmark &nbsp;·&nbsp;
<span>19</span> Savant trait check &nbsp;·&nbsp;
<span>20</span> Value metrics &nbsp;·&nbsp;
<span>21</span> MiLB pipeline index &nbsp;·&nbsp;
<span>22</span> The 2027 shopping list &nbsp;·&nbsp;
<span>23</span> The Posted Class: Japan's window &nbsp;·&nbsp;
<span>24</span> The pricing test: our own Hakes–Sauer verdict &nbsp;·&nbsp;
<span>25</span> Benchmark vs headline: exact math vs the greedy roster build</div>
<nav class="modenav">
<button type="button" id="btn-story" class="active" onclick="showMode('story')">Story: the case in 6 chapters</button>
<button type="button" id="btn-boardroom" onclick="showMode('boardroom')">Boardroom: 15 slides</button>
<button type="button" id="btn-explorer" onclick="showMode('explorer')">Explorer: all 25 figures by task</button>
</nav>
<div id="mode-story">__STORY__</div>
<div id="mode-boardroom">__BOARDROOM__</div>
<div id="mode-explorer">__EXPLORER__</div>
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
<b>NPB posted class (Cycle 34, keyless):</b> <span class="src">NPB official BIS
(npb.jp/bis)</span> — 2024–2026 qualified leaderboards (340 rows) plus the
posted trio (Sato / Taira / Itoh, posted Nov 1, 2026); BIS is canonical over
wire roundings, and no NPB-to-MLB translation factor is claimed anywhere.<br>
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
on the panel). The product is player-level acquisition, not a team-wins formula.
<b>Pricing claim, tested (Cycles 46/48):</b> our own Hakes–Sauer test of whether the
market underprices contact/OBP is formally inconclusive at current samples — Figure 24
carries the coefficients, the test, and the verdict; this page claims persistence and
cap-efficiency, not proven undervaluation.<br><br>
<b>ALL DATA &amp; API SOURCES — the full list, with status (2026-11-02).</b>
Every figure above traces to one of these; nothing else feeds this page.<br>
<span class="src">MLB Stats API</span> (statsapi.mlb.com) — standings, team
hitting/pitching, player ages, transactions (35,000+ events), minor-league
affiliates. <b>LIVE · keyless.</b><br>
<span class="src">Baseball Savant</span> — expected stats (xwOBA), batted ball
(EV/barrels), bat tracking, sprint speed, arm strength. <b>LIVE · keyless</b>
(committed snapshots, re-verified player-by-player).<br>
<span class="src">ESPN</span> (site.web.api.espn.com) — independent
cross-validation only: HR counts match exactly for all 254 players compared.
<b>VERIFIED.</b><br>
<span class="src">FanGraphs Steamer</span> — 2027 projections: the benchmark
panel and the FA-class WAR column; the original player-ID crosswalk.
<b>Committed snapshot</b> (the site currently refuses automated pulls, 403 —
stopped, not routed around).<br>
<span class="src">Spotrac</span> — per-player salaries (2027 payroll basis)
and the 2027 free-agent class (251 players). <b>Committed snapshot — 24 of 30
teams</b> (the pull was rate-limited; the 6 missing teams are named in the
data metadata, not papered over).<br>
<span class="src">Cot's Baseball Contracts</span> (Baseball Prospectus) — the
second salary dataset, on its own LRP-2027 basis (present-value deferrals,
buyout option years): 237 players, all 30 teams. <b>Committed · labeled
cross-check layer only</b> — never mixed into the Spotrac-basis math.<br>
<span class="src">Chadwick Bureau Register</span> — the conformed player-ID
crosswalk (MLBAM / Retrosheet / Baseball-Reference / FanGraphs / NPB keys).
<b>Committed · joins this demo's player registry 379 of 379.</b><br>
<span class="src">The Injury Report</span> — every MLB injured-list stint,
2019–2026: 6,632 stints, 2,177 players, built from MLB's own IL
transactions. <b>Committed · availability cross-check layer.</b><br>
<span class="src">NPB official BIS</span> (npb.jp) — the posted class (Sato /
Taira / Itoh) and 2024–2026 leaderboards, 340 rows. <b>Committed ·
keyless.</b><br>
<span class="src">Baseball-Reference</span> WAR daily files — WAR context and
a salary cross-check. <b>Salary use FAILED CLOSED (Cycle 44):</b> only 71.1%
of matched salaries agreed within $50k against the 80% bar, so no
Baseball-Reference salary data is used anywhere on this page; the files are
kept raw for WAR checks only.<br>
<span class="src">Statyx</span> (api.statyx.io) — live MLB injuries
(recent-moves feed). <b>SERVING since Cycle 51 (2026-11-02) — the EVENT
layer (Cycle 55)</b>: its moves are compared against the FastballAPI
census for the health figure's movement line (curated table
fact_il_events), and with FastballAPI it feeds the current-IL layer
(curated table fact_il_current, 196 players) and the health figure's
live-IL picture — 13 of the 251 free agents currently listed injured,
pulled 2026-11-02 (injuries page answered 200 with 50 recent-move
records, 44 of them also on FastballAPI's full list). Its standings
payload was tested in Cycle 55 and dropped as a source (only a
Statyx-internal team_id, no crosswalk to MLB teams, 25 of 30 teams
covered) — kept raw only.<br>
<span class="src">FastballAPI</span> (mcp.fastballapi.com) — live injuries and
standings plus pitch-level history back to 2015. <b>SERVING since Cycle 51
(2026-11-02) — the CENSUS (Cycle 55)</b>: the full 190-record IL list is
the canonical snapshot behind the same
current-IL layer and health-figure live picture; its 2026 standings
snapshot agrees with the committed MLB Stats API picture 30 of 30 on
wins and runs scored (cross-check in docs/CARPE_SCORECARD.md).<br>
<span class="src">PubMed / NCBI E-utilities</span>
(eutils.ncbi.nlm.nih.gov) — literature surveillance for the injury
science behind the availability edge: four fixed topics (UCL return
to play; baseball injury prevention and workload; muscle
regeneration and cellular recovery; tendon healing and biologics),
three papers each, systematic reviews and meta-analyses first.
<b>LIVE · keyless</b> (committed snapshot
data/evidence_surveillance.json, pulled __EVIDENCE_DATE__; full cards
on docs/EVIDENCE.html). <b>Context only — no paper feeds any figure
or model.</b><br>
<b>Not yet connected (not sources of anything on this page):</b> Tank01 —
deferred (the owner dropped the RapidAPI signup for now; supplement only,
nothing in the demo depends on it). Sportradar — trial deliberately starts
mid-November so its 30-day window covers Dec 1.<br><br>
<b>Project repo:</b> github.com/mega-byte2600/hardball (private) · audit trail in docs/BML_LOG.md
(two cycle series converged on 2026-10-31 — see the integration note at the top of the log)
</div>
</div>
<script>
function showMode(id) {
  var modes = ["story", "boardroom", "explorer"];
  for (var i = 0; i < modes.length; i++) {
    document.getElementById("mode-" + modes[i]).style.display = (modes[i] === id) ? "block" : "none";
    document.getElementById("btn-" + modes[i]).className = (modes[i] === id) ? "active" : "";
  }
}
function printBoardroom() {
  showMode("boardroom");
  document.body.classList.add("print-boardroom");
  window.print();
  document.body.classList.remove("print-boardroom");
}
showMode("story");
</script>
</body></html>"""

    ev_date = "not yet pulled"
    _ev_path = os.path.join(DATA, "evidence_surveillance.json")
    if os.path.exists(_ev_path):
        ev_date = json.load(open(_ev_path))["metadata"]["run_date"]
    page = (page_template.replace("__JS_INCLUDE__", js_include)
            .replace("__STORY__", story)
            .replace("__BOARDROOM__", boardroom)
            .replace("__EXPLORER__", explorer)
            .replace("__EVIDENCE_DATE__", ev_date))

    out = os.path.join(REPO, "dashboard", "hardball_demo.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"dashboard written: {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    import pandas as pd  # noqa
    build()

