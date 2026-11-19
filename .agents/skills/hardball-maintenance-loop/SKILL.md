---
name: hardball-maintenance-loop
description: Use when the user asks for a routine HARDBALL maintenance or health pass. Continue unfinished work first, then review status, run local gates, check data freshness, and make at most one small hygiene fix.
metadata:
  short-description: Run a bounded HARDBALL health loop
---

# Bounded maintenance loop

Run this loop only when requested. Do not schedule a recurring task or poll
external services in the background.

Work in order and stop after the first item that needs a real fix:

1. **Unfinished work:** continue the current task or repair a failing gate.
2. **PR/review:** inspect available checks and review comments; fix concrete
   failures with a regression check. For a user-requested repair, push the fix
   branch after implementation and checks without asking again; report any
   blocked checks. Features and scope expansions still need authorization.
3. **Local health:** run the documented data, spelling, freshness, and relevant
   dashboard layout gates. Diagnose failures before changing code.
4. **Data health:** check public connector status and cached as-of ages. Do not
   spend API credits or invoke a paid/key-gated source for routine monitoring.
5. **One hygiene item:** only if 1–4 are clean, fix one small TODO, missing
   regression case, lint issue, or dead import.

Do not add features, upgrade dependencies, delete data/branches, force-push,
merge, deploy, or start recurring automation in this loop. If all checks are
clean, report the exact gates and the as-of time in one concise status.
