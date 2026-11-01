# HARDBALL — Meeting Talk-Track (10 minutes, Figure-by-Figure)
*For the GP to present to an owner. Every number is real and measured; every
honesty caveat is already inside the pitch so it survives a skeptical room.
Figure numbers match the merged 22-figure dashboard (main, v1.0.0-mvp).*

**Weapons:** the dashboard, opened on Figure 1. This page tells you what to
say and in what order. Don't read it — talk it.

---

## HOWDY + THE FILM — Figure 1 (1:00)
Press play before you say a word. Sixteen seasons of payroll vs wins animate;
the cheap winners stay gold the whole time. *Then:* "The owners want a hard
cap. So the question isn't 'who spends the most' — that game is over. The
question is: **which team deploys a constrained budget better than the teams
it competes against?** And the answer is measurable."

## THE EDGE — Figure 3 (2:00)
Point at the bars. "Here's the single most important chart in the room.
We tracked real players year over year. What a player *does* that's a *skill*
— making contact, drawing walks — **carries. Across four real season pairs,
contact rate persists at r ≈ 0.8-0.9.** But the *output* owners are
tempted to buy — on-base percentage — is mostly luck, and it does **not**
carry (r ≈ 0.3)."

**The line:** "You don't pay for the OBP. You pay for the skill that produces
it. That's a measurable edge."

## WHY THIS ISN'T A GAMBLE — Figures 4-6 (1:30)
Fig 4 (run diff): "Better teams score more than they allow — that's real,
but it describes *this* season; it doesn't predict next."
Fig 5 (title-bar test): "Run differential alone flags a 90+ win club with
AUC ≈ 0.95 — both directions, both years. That's separation, not a forecast."
Fig 6 (payroll vs wins): "Money buys some wins. But the winning-cheap teams —
Milwaukee, Tampa, Cleveland — win ~95 at a third to a quarter the payroll.
**They're the ones who've discovered the edge we're showing you.**"

## HOW THE WINNERS ARE BUILT — Figures 7, 13-15 (2:30)
Quick sweep: "Winning-cheap teams dominate contact, OBP, and walks (Fig 7);
they field control-walking arms (Fig 13); their health is priced in, not
hoped for (Fig 14). The 2027 roster (Fig 15) is built from real projections
on exactly those inputs." Don't linger — the charts carry it.

## THE CAP IS THE OPPORTUNITY — Figures 10 + 11 + 20 (1:30)
Fig 10 (cap reality): "Here's the kicker. Seven teams are over the cap and
MUST cut — the Mets $101M, the Dodgers $94M. And fifteen — **including
Cleveland (+$97M) and Tampa (+$76M)** — are under the floor and forced to
add. The cap makes the rich cut; the floor hands the disciplined winners
real money to deploy. **The system is now engineered to reward exactly the
teams that waste the least.**"
Fig 11 (forced sellers): "And it doesn't take a rebuild. Every over-cap
team closes its gap by shedding at most three big contracts — Toronto and
Atlanta need just one. The cap binds through a handful of deals. That is
arithmetic, not a prediction that anyone trades those players — but it
sizes the negotiation exactly."

Fig 20 (value metrics): "This is what we compute instead of faking WAR —
wOBA, wRC+, FIP. Real, reproducible."

## WHAT THE MONEY BUYS — Figures 16 + 22 (1:30)
"We built the actual free-agent rosters at each budget — real players, real
prices. The floor roster — $171M — buys **42 wins above replacement**. The
cap roster at $245M buys 52. **A disciplined floor team captures 80% of the
cap team's talent for 70% of the money.** The shopping list (Fig 22) is the
class ranked by projected value — every name priced off last year's real
contract anchor."

## PICK YOUR TEAM — Figure 2 (the interactive close, 1:00)
Hand them the dropdown. "Name your club — its 2026 signature against the
winning-cheap profile, its cap headroom, its farm pipeline, its top
prospect. Thirty clubs, same treatment. **Give us your team and we'll show
you which contact/walk players and control arms to buy.**"

## HONESTY — what we will NOT claim (1:00)
"This is where we're different. We do **not** tell you we can predict team
wins — forecasting is genuinely weak (about 9-13 wins off), and saying
otherwise would be a lie that gets exposed. WAR is proprietary and absent
from public data — we surface its real inputs instead. Our projections were
benchmarked against FanGraphs' Steamer in public (Fig 18): hitter agreement
r = .889. What we *can* show, measured over four years: skills persist,
luck doesn't. **That's the edge you can act on.**"

---

### Back-pocket numbers (for questions)
- Pooled contact persistence r = 0.84 (95% CI 0.78-0.88); dashboard panel:
  4 season pairs, 457 players.
- Contact next-year prediction error cut 38-57% per season pair.
- MIL/TB/CLE: ~95 wins at ~1/3-1/4 big-market payroll.
- Cap cuts: NYM $101.4M, LAD $94.0M, NYY $63.0M over. Floor adds: CLE
  +$96.7M, TB +$75.6M (7 over cap / 15 under floor).
- Scenario rosters: Floor $171.2M → 42.0 WAR; Middle $208.3M → 45.7 WAR;
  Cap $245.3M → 52.3 WAR (real FA class, prior-AAV price anchors).
- Benchmark: Marcel vs Steamer hitter OBP r = .889 (201 matched by ID);
  pitcher bias corrected in public (Steamer -0.250 ERA, ours -0.208 pre-fix).
- Value metrics surfaced instead of fake WAR: wOBA, wRC+, FIP, K-BB%.
- Honest limit: cross-year team-wins forecasting MAE ≈ 10.2 grouped CV
  (2020 fold excluded — it predicts the 60-game season; stated on page).
- Data QC: every source re-verified 2026-10-31 (see CARPE_SCORECARD);
  salaries 24/30 teams (Spotrac blocks 6 pages — labeled on the dashboard).
