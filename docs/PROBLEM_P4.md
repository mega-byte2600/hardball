# HARDBALL — Problem Definition (P4)

## The problem (as GP framed it)

Rank all 30 MLB teams by annual payroll. The top spenders (Dodgers,
Yankees, Mets) outspend the bottom (Rays, Brewers, Guardians) by a wide
margin — yet the cheap teams keep producing *more wins per dollar*. The
market price of *power* is now efficient (everyone chases homeruns/barrels);
the underpriced resource is **contact + on-base + affordable production**.

So the demo answer to: **"how do we identify the key metrics, KPIs, data,
and variables, and derive a formula to help a team copy Brewers/Rays
success?"** is not "compute more stats." It is a **value+construction
playbook**: spend like the Rays, win like the Dodgers, by buying the cheap
winning ingredients instead of the expensive ones.

Core thesis, to be tested against real data (not asserted):
  get on base with contact hits — NOT homeruns alone.

## Questions P6 must answer with real data (per team, 2025 + 2026)

1. Payroll (total rank + $ per team) vs wins/WAR — the efficiency table.
2. Which performance KPIs discriminate efficient small-market teams from
   the field (OBP, K%, BB%, contact rate, hard-hit, HR/PA, BA-on-contact,
   defensive runs, speed?) — the "variable identification."
3. Is contact+OBP genuinely cheaper per WAR than power?  (The buy-cheap-
   ingredients claim — must be shown, not assumed.)
4. A candidate formula: predicted wins per $100M = f(OBP, contact, K%,
   BB%, avoided-HR-dependence, defense, ...) — an implementable model.
5. Player-level: which individual cheap players outperform their payroll
   (the "undervalued list" the market misprices).

## Data requirements (CarpeData, real only)

- Team payroll 2025 + 2026 (new source to acquire)
- Team + player performance (have: MLB API + ESPN; need Statcast layer)
- Injury/recovery risk (have: MLB API injuries endpoint + literature)
- All pulled to disk, cross-validated, self-archived. NO Kaggle.

## Guardrail (GP, standing)
State findings as *capability* ("the formula ranks teams this way, and
here's the evidence"), never as guaranteed performance. The demo must be
honest about what the data shows — including if contact-over-power does NOT
win, so we show the counter-evidence. That honesty is the credibility.

## Status
P4 defined, in progress. Next: acquire payroll data source.
