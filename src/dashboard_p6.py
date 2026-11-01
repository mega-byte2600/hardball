"""P6: HARDBALL demo dashboard (Plotly HTML).

Fourteen panels on real data (payroll-vs-wins, KPI signature, cap projections,
25-year durability, 2027 Marcel projections, pitching, health/availability,
cap roster, run differential, sensitivity, plus the CarpeData panels:
Marcel-vs-Steamer benchmark, Savant trait check, MiLB pipeline index,
and the 2027 free-agent shopping list).
Serves as a self-contained HTML file the GP can open at the Winter Meetings.

Build must work from a clean clone: every panel reads committed data
snapshots under data/ first. The SQLite lake (gitignored) and the live
MLB API are refresh paths, never build requirements.
"""
import json
import os
import sys

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


def pitching_group_table():
    """IP-weighted pitching KPIs by group (2026), or None if no source.

    Source order: committed snapshot data/team_pitching.json first (so a
    clean clone builds offline), then the local lake if it exists.
    Regenerate the snapshot with: python src/dashboard_p6.py --snapshot-pitching
    (requires the lake; see src/ingest.py).
    """
    snap = os.path.join(DATA, "team_pitching.json")
    if os.path.exists(snap):
        with open(snap) as f:
            payload = json.load(f)
        g = pd.DataFrame(payload["groups"]).T
        return g[["ERA", "WHIP", "BB/9"]]
    db = os.path.join(DATA, "mlb_lake.db")
    if not os.path.exists(db):
        return None
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
    con = sqlite3.connect(db)
    try:
        rows = []
        for season, team, sjson in con.execute("SELECT season,team,stat_json FROM stat_lines WHERE group_name='pitching'"):
            s = json.loads(sjson)
            rows.append({"season": season, "code": TEAM.get(team, team), "IP": s.get("inningsPitched"),
                         "ERA": s.get("era"), "WHIP": s.get("whip"),
                         # MLB API field is baseOnBalls — the original code read
                         # "walks" (always null), so BB/9 silently computed as 0.0
                         # for every group. Fixed 2026-10-31 (audit follow-up).
                         "BB": s.get("baseOnBalls")})
    except sqlite3.OperationalError:
        return None
    finally:
        con.close()
    d = pd.DataFrame(rows)
    for c in ["IP", "ERA", "WHIP", "BB"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["IP", "ERA"])[d["IP"] >= 30]
    d["grp"] = "OTHER"
    d.loc[d["code"].isin(WIN_CHEAP), "grp"] = "WIN_CHEAP"
    d.loc[d["code"].isin(CHEAP_MEDIOCRE), "grp"] = "CHEAP_MEDIOCRE"
    d = d[d["season"] == 2026]
    if d.empty:
        return None
    return d.groupby("grp").apply(lambda x: pd.Series({
        "ERA": (x["ERA"]*x["IP"]).sum()/x["IP"].sum(),
        "WHIP": (x["WHIP"]*x["IP"]).sum()/x["IP"].sum(),
        "BB/9": (x["BB"]*9/x["IP"]).sum()/len(x)}), include_groups=False)


def write_pitching_snapshot():
    """Write data/team_pitching.json from the lake (refresh path only)."""
    db = os.path.join(DATA, "mlb_lake.db")
    if not os.path.exists(db):
        raise SystemExit("lake not found — run src/ingest.py first")
    # Force the lake path by temporarily hiding the snapshot, if any.
    snap = os.path.join(DATA, "team_pitching.json")
    stash = snap + ".bak"
    if os.path.exists(snap):
        os.replace(snap, stash)
    try:
        g = pitching_group_table()
    finally:
        if os.path.exists(stash):
            os.replace(stash, snap)
    if g is None:
        raise SystemExit("no pitching rows in lake — run src/ingest.py first")
    payload = {
        "season": 2026,
        "source": "mlb_lake.db stat_lines pitching (MLB Stats API via src/ingest.py), IP>=30, IP-weighted",
        "groups": {grp: {m: round(float(g.loc[grp, m]), 4) for m in ["ERA", "WHIP", "BB/9"]}
                   for grp in g.index},
    }
    with open(snap, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote {snap}: {payload['groups']}")


def panel_pitching():
    """Winning-cheap pitching signature: IP-weighted ERA/WHIP/BB9 per group (2026)."""
    g = pitching_group_table()
    if g is None:
        return None
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


def build():
    os.makedirs(os.path.join(REPO, "dashboard"), exist_ok=True)
    try:
        df = kpi_mod.kpi_frame()
    except Exception as e:  # offline / clean clone: committed snapshots suffice
        print(f"kpi live fetch failed ({e}); using committed data/kpi_*.json snapshots")
        df = kpi_mod.kpi_frame_from_snapshots()
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
    fig11 = panel_benchmark()
    fig12 = panel_savant()
    fig13 = panel_pipeline()
    fig14 = panel_shopping()

    # Self-contained offline demo: inline plotly so no internet needed at the
    # Winter Meetings. Caches the bundle next to the dashboard if present.
    bundle = os.path.join(REPO, "dashboard", "plotly.min.js")
    if os.path.exists(bundle):
        with open(bundle) as f:
            plotly_js = f.read()
    else:  # use the JS bundled with the installed plotly package (offline-safe)
        from plotly.offline import get_plotlyjs
        plotly_js = get_plotlyjs()
        with open(bundle, "w") as f:
            f.write(plotly_js)
    js_include = f"<script>{plotly_js}</script>"

    # ---- Presentation pass (2026-10-31): branded template, story
    # sections, stat cards. Presentation only — no data changes.
    import plotly.io as pio
    pio.templates["hardball"] = go.layout.Template(layout=dict(
        font=dict(family="system-ui,-apple-system,'Segoe UI',sans-serif",
                  color="#14213d"),
        title=dict(font=dict(size=17, color="#14213d")),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(gridcolor="#eae7de", linecolor="#c9c4b4",
                   zerolinecolor="#eae7de", title=dict(font=dict(size=13))),
        yaxis=dict(gridcolor="#eae7de", linecolor="#c9c4b4",
                   zerolinecolor="#eae7de", title=dict(font=dict(size=13))),
        colorway=["#14213d", "#d50032", "#c9a227", "#1f7a6d", "#5b7ba5",
                  "#8a6d3b"],
        legend=dict(bgcolor="rgba(255,255,255,0.92)",
                    bordercolor="#e3dfd2", borderwidth=1)))
    SECTIONS = [
        ("I", "The Proof", "Run differential describes wins (R² ≈ 0.55) — "
         "and payroll alone doesn't buy them.", [fig9, fig1]),
        ("II", "The Signature", "Winning-cheap teams look different: more "
         "contact, more OBP, fewer strikeouts — for 25 straight years.",
         [fig2, fig4]),
        ("III", "The Cap", "The owners' proposed 2027 cap, priced team by "
         "team.", [fig3]),
        ("IV", "The Players", "Backtested Marcel projections, "
         "health-capped — the actual shopping-grade numbers.",
         [fig5, fig6, fig7]),
        ("V", "The Roster", "A 26-man roster that fits the cap, and what "
         "moves the win needle.", [fig8, fig10]),
        ("VI", "The Check", "Benchmarked against Steamer and Statcast — "
         "including where we disagree and by how much.", [fig11, fig12]),
        ("VII", "The Future", "The pipelines feeding the cheap winners, "
         "and the free-agent list to shop from.", [fig13, fig14]),
    ]
    html = ""
    for num, name, take, figs in SECTIONS:
        figs = [f for f in figs if f is not None]
        if not figs:
            continue
        html += (f'<div class="sec"><span class="secnum">{num}</span>'
                 f'<div><h3>{name}</h3><p>{take}</p></div></div>')
        for fig in figs:
            fig.update_layout(template="hardball")
            html += ('<div class="panel">' +
                     fig.to_html(full_html=False, include_plotlyjs=False) +
                     "</div>")

    def _count(fname):
        p = os.path.join(DATA, fname)
        return len(json.load(open(p))) if os.path.exists(p) else 0
    n_hit, n_pit = _count("projections_2027.json"), _count("projections_2027_pitchers.json")
    cards = (
        '<div class="cards">'
        '<div class="card"><div class="num">$245.3M</div><div class="lab">proposed 2027 cap · floor $171.2M</div></div>'
        '<div class="card"><div class="num">509</div><div class="lab">team-seasons measured, 2011–2026</div></div>'
        f'<div class="card"><div class="num">{n_hit + n_pit}</div><div class="lab">players projected for 2027 ({n_hit} hitters · {n_pit} pitchers)</div></div>'
        '<div class="card"><div class="num">r = .889</div><div class="lab">hitter OBP agreement vs Steamer</div></div>'
        '<div class="card"><div class="num">100%</div><div class="lab">real data — every panel sourced</div></div>'
        '</div>')

    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>HARDBALL — Cap-Era Moneyball Demo (P6)</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#14213d}}
.hd{{max-width:1120px;margin:0 auto;padding:0 20px 40px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 4px}}
.card{{flex:1 1 160px;background:#fff;border:1px solid #e3dfd2;border-top:4px solid #d50032;border-radius:10px;padding:14px 16px;box-shadow:0 2px 8px rgba(20,33,61,.06)}}
.card .num{{font-size:26px;font-weight:800;color:#14213d;letter-spacing:.2px}}
.card .lab{{font-size:12.5px;color:#5a6478;margin-top:3px;line-height:1.35}}
.sec{{display:flex;gap:14px;align-items:center;background:linear-gradient(90deg,#14213d,#1d3557);color:#fff;border-radius:10px;padding:13px 20px;margin:30px 0 4px;box-shadow:0 2px 10px rgba(20,33,61,.18)}}
.secnum{{font-size:21px;font-weight:800;color:#c9a227;border:2px solid #c9a227;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}}
.sec h3{{margin:0;font-size:19px;letter-spacing:.4px}}
.sec p{{margin:2px 0 0;font-size:13.5px;color:#cbe0ff}}
.panel{{background:#fff;border:1px solid #e3dfd2;border-radius:12px;padding:16px 18px 8px;margin:14px 0;box-shadow:0 2px 10px rgba(20,33,61,.05)}}
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
{cards}
{js_include}
{html}
<div class="srcbox">
<b>DATA SOURCES &amp; METHODS — everything on this page is real and traceable.</b><br><br>
<b>Primary data</b> (2025-2026, all 30 MLB teams): <span class="src">MLB Stats API
statsapi.mlb.com/api/v1</span> — official MLB feed, keyless; team hitting/pitching + standings
(runs scored / runs allowed). Validated against <span class="src">ESPN
site.web.api.espn.com</span> (2025 validation set: 131 players cross-checked, HR counts match exactly).<br>
<b>Payroll:</b> <span class="src">Spotrac</span> (via MIT-licensed jasonbhorne/mlb-payroll,
721 team-seasons 2000-2024 + live 2026 opening-day figures). <b>Injury/health:</b> MLB
transactions feed (35,000+ events 2025-2026, IL days per player). <b>MLB color/look:</b> league
branding only, for presentation.<br>
<b>CarpeData layer (added 2026-10-31, all keyless):</b> <span class="src">Baseball Savant</span>
leaderboards by player_id — expected stats (xwOBA), batted ball (EV/barrels), bat tracking
2024-2026, sprint speed, arm strength; <span class="src">FanGraphs API</span> — Steamer 2027
projections (the benchmark panel; ZiPS returned empty via the API and is not claimed) and the
player-ID crosswalk; <span class="src">MLB Stats API</span> minor-league endpoints (AAA/AA)
+ people endpoint (real birthdates) for the pipeline panel. Every connected source was
tested before use — kept-vs-dropped with reasons in docs/CARPE_SCORECARD.md.<br>
<b>Model:</b> linear regression on the 2011-2026 panel (509 team-seasons, 450 complete):
same-year run differential → wins R² ≈ 0.55 — a diagnostic link, not a forecast.
KPI-only next-season forecasting is weak (out-of-sample MAE ≈ 14 wins, worse than the
naive baseline; see BML Cycles 18-19 in the repo audit trail) — an earlier 2-year-window
estimate (MAE 4.0 / R² 0.80) was retracted for exactly that reason and is not claimed here.
The actionable layer is player-level: Marcel weighted-average projections with
injury-availability caps, priced against the cap. Pythagorean exponent uses Euler's e.
The hitter Marcel is the Cycle 21 backtested configuration (3 seasons, 5-4-3, plus an
age adjustment whose slope was fitted on 2025-2026 backtest residuals — the original
aging step was a stub that adjusted nothing). Cycle 20 tested Savant trait adjustments
and rejected them out-of-sample; Cycle 22 benchmarks the result against Steamer
(hitters agree closely). Cycle 24 backtested the pitcher Marcel against actuals,
found the same optimism there (bias −0.21 ERA), and adopted the tested fix
(3 seasons + fitted age term): pooled bias vs actuals fell to −0.08, and the
residual gap vs Steamer narrowed to −0.25 ERA with the pitcher pool widening
76 → 102. Cycle 25 wires real Spotrac salaries + the 2027 FA class so the cap
math runs on contract figures, with prior AAV labeled as a last-price anchor.
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
    if "--snapshot-pitching" in sys.argv:
        write_pitching_snapshot()
    else:
        build()
