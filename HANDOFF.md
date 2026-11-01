# HANDOFF — toby/wow (PR #5, stacked on PR #4)

WOW pass, 2026-10-31: the Boardroom layer (Cycle 26) — built for MLB
stakeholders, still on real data only. **Stacked on `toby/finale`
(PR #4)** — merge #1 → #2 → #3 → #4 → this.

## What shipped

1. **PRESS PLAY** — payroll vs wins animated across 16 seasons
   (2011–2026 panel). Bubble size = wins per $100M; the winning-cheap
   three ride in gold and barely move while payrolls inflate around
   them. The thesis, in motion, in ten seconds.
2. **PICK YOUR TEAM** — a dropdown with all 30 clubs: each team's 2026
   signature radar indexed to league = 100 against the gold
   winning-cheap profile, with wins, payroll, cap headroom, pipeline
   rank, and top prospect in the title. Every stakeholder finds their
   own club first — that's the hook.
3. **WHAT DOES THE MONEY BUY** — full 26-man rosters bought entirely
   from the real 2027 FA class at three budgets, switchable in-panel:
   Floor $171.2M → **42.0 WAR**, Middle $208M → 45.7 WAR, Cap $245.3M →
   **52.3 WAR**. The floor build captures ~80% of the cap build's WAR;
   the last $73.6M buys ~10 WAR. Prices are prior-contract AAV anchors
   and are labeled as such on the panel; constraints (26 men, spend ≤
   budget) are asserted in `bml_cycle26_wow.py`.

Dashboard is now **17 panels / 8 sections**; clean-clone offline build
re-verified (17 plotly divs, animation frames and scenario buttons
present in the file). README + exec summary counts updated. Release
v0.9.2-demo carries the built HTML at this branch's head.

## Reviewer notes

- Cycle 26's scenario builder is deliberately simple (greedy
  WAR-per-dollar + upgrades). It is an illustration of value density
  in the FA class, and says so — not a roster-construction engine.
- No model or prior-cycle data changed in this PR.
