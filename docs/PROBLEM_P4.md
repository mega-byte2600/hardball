# HARDBALL — Problem Definition (P4) — REVISED for salary cap

## The one-sentence problem

Owners are about to impose a hard salary cap (proposed $245.3M cap / $171.2M
floor for 2027; CBA expires Dec 1 2026, lockout expected Dec 2 [29][30]),
force-crashing every team toward a bounded payroll band. The question is no
longer "does money buy wins" — that's already done, answer known (money
buys some wins, inefficiently). The question is:

  **How does a team maximize wins at a MID-tier, cap-constrained payroll —
  deploy money like the Rays/Brewers/Guardians, who reach competitive-plus
  results (85-103 wins) at a fraction of big-market cost?**

The demo's job: give an owner the *construction playbook* — the KPI set, the
data, and a formula — to win inside the cap.

## Why this is NOT redoing what already exists

| Already done (descriptive) | Not yet done (what we build) |
|---|---|
| "Does payroll buy wins?" — cost-per-win tables; jasonbhorne/mlb-payroll and many show money->wins is real but weak [27] | **Constraint optimization under a hard cap**: given cap $245M and a 15% individual max, what *mix* of production maximizes wins — not "spend less" but "spend THIS way" |
| "Small markets can be efficient" — retrospective praise of Rays/Brewers | **A forward-looking formula**: which KPIs discriminate winning-cheap teams from cheap-but-mediocre (MIA/CHW/STL won 80-84 cheap — that's NOT the goal), and how to buy that production |
| Injury/aging/Statcast academic studies | **A deployable projection + roster-builder**: Marcel baseline + Statcast refinement + health adjustment + payroll-constrained mix — an owner tool, not a study |

The trap we avoid: raw "cheap wins per dollar" rewards cheap mediocrity. Our
edge is *winning while cheap* — CLE/TB/MIL (85-103 wins) at 1/3 to 1/4 of
big-three cost. The cap makes this the survivable strategy for ALL 30 teams.

## Value-add for owners facing the cap (the pitch)

1. **The cap doesn't just cap rich teams — it raises floor for everyone.**
   Floor ~$171M means small markets get a budget increase they must not
   waste. The demo shows where to deploy new dollars for wins (the reverse-
   Moneyball: don't burn the new floor on one generational bat). [29]
2. **Rich teams must CUT ~40-50%** (Dodgers CBT ~$433M -> ~$245M). They can't
   buy their way out. The demo shows which spend is redundant (power-heavy,
   low-marginal-ROI) vs which underpriced production (contact+OBP, health,
   cheap WAR) survives a haircut.
3. **Individual salary caps (15% max, ~$265M FA) break the "one $300M+
   superstar + depth" model.** Roster construction must shift from concentrated
   star-dollars to *spread, high-value production* — exactly contact/OBP/
   defense the cheap winners already prove. [29]
4. **Moneyball for the cap era**: when all 30 owners chase the same 11-12
   proven bats under a cap, those bats inflate; the underpriced resource is
   contact hitters, healthy arms, efficient mid-tier payroll — the
   Rays/Brewers formula, now every owner's edge.

## Hypothesis to test with real data (not asserted)

Buy contact + OBP + affordable production, not homeruns alone. Under a cap
the marginal value of a cheap OBP/contact bat exceeds a marginal dollar on a
power bat. Must be SHOWN from 2025-2026 team + player data, including the
counter-case (does it actually win?).

## Guardrails (GP standing)
- Findings stated as *capability* with evidence, never guaranteed performance.
- Show the counter-evidence honestly (incl. if contact-over-power does NOT win).
- Real data only (MLB API, ESPN, Spotrac payroll, Statcast), self-archived,
  cross-validated. NO Kaggle.

## Positioning vs demo date
The CBA expires Dec 1 = the Winter Meetings. The demo is *the* timely,
revenue-relevant artifact: owners arriving need a cap-era strategy, and
HARDBALL hands them the construction formula with real 2025-26 evidence.

## Status
P4 REVISED for cap reality. Next: P5 captures the KPI discriminators on real
team data (which metrics separate winning-cheap from cheap-mediocre), then
P6 builds the formula + dashboard. [29][30]
