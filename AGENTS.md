# HARDBALL Codex guide

HARDBALL is a public MLB roster decision dashboard. Committed files are public.
`src/` and `data/` are authoritative; `dashboard/index.html` is generated from
them. Read `docs/EDITORIAL_VISUAL_DIRECTION.md`, `docs/VIZ_BEST_PRACTICES.md`,
and the relevant source/data contract before changing a public figure.

## Working loop

For the full Codex adaptation of the repository's Claude workflow kit, see
`docs/CODEX_WORKFLOWS.md`.

1. For a multi-file change, write testable acceptance criteria before editing.
   Search for an existing implementation and reuse it.
2. Make one small, reviewable change on a task branch. For bug fixes, add a
   failing regression check first when practical.
3. Verify the specific user behavior, then run the applicable project gates:
   `python src/verify_data.py`, `python src/spellcheck_gate.py`, and
   `python src/check_freshness.py`. Rebuild the dashboard after source/data
   changes with `HARDBALL_OFFLINE_BUILD=1 python src/dashboard_p6.py` and keep
   `dashboard/index.html` and `dashboard/hardball_demo.html` byte-identical.
4. For dashboard changes, run `python src/verify_dashboard_layout.py` and
   inspect Story, Boardroom, and Explorer at phone, tablet, and desktop widths.
   Install the pinned browser once with `python -m playwright install chromium`;
   set `CHROMIUM_PATH` only when intentionally testing another compatible build.
5. Review the diff against `main`, verify every finding against the source, and
   report the measured result, remaining gaps, and exact commands run.

## Product and data rules

- Use plain baseball language first. Put evidence, source, unit, date, and
  uncertainty beside the decision-relevant view.
- A reported item is not a confirmed transaction. Treat social posts as leads;
  use the MLB Stats API transaction feed for SIGNED status.
- Payroll and cap values are scenarios with named source/basis. The proposed
  $245.3M cap is not an MLB salary cap.
- A model relationship is not causation or a forecast. Preserve limitations,
  withdrawn claims, and validation context.
- Never fabricate rows or values. Missing data is visibly unavailable.
- Do not read, print, log, or commit `.env*`, keys, tokens, or credentials.

## Review and release boundary

- A user-requested fix for broken or incorrect existing behavior is required
  work. Implement it, run the applicable checks, commit it, and push the fix
  branch without waiting for another approval. If a required check is blocked,
  still push the reviewable fix branch and clearly record the blocked gate.
- A feature or scope expansion is optional work; get the owner's approval
  before implementing it unless already authorized in the conversation.
- Before commit or push, review correctness, null states, public copy, source
  semantics, responsive behavior, accessibility, and regression coverage.
- Do not force-push or delete data/branches. A requested fix authorizes a
  branch push, not a merge or deployment. Do not merge to `main` or deploy to
  GitHub Pages without the owner's explicit yes; merge to `main` publishes the
  site.
- Do not add recurring jobs, live-data polling, or paid/credit-consuming API
  calls as a side effect of a dashboard task.

## Project skills

- Dashboard, chart, responsive layout, or visual-score requests:
  `.agents/skills/hardball-dashboard-quality/SKILL.md`.
- A user-requested routine repository health pass:
  `.agents/skills/hardball-maintenance-loop/SKILL.md`.
- Any repository-specific rule in this file takes precedence over generic
  workflow defaults.
