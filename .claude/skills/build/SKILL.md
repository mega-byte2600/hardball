---
name: build
description: Use after /kickoff, or for any approved implementation task. Implements an approved spec/plan task-by-task with test-driven development, small commits, and verification after every step.
argument-hint: "[path to spec, or a short task]"
effort: high
---

# /build — Test-driven implementation

> **Repo rules win.** `CLAUDE.md` (and any `SOUL.md` / `AGENTS.md` it imports) overrides anything in this workflow, including its "Workflow overrides" section.

Input: **$ARGUMENTS**

## Ground rules
- Follow `CLAUDE.md` standards exactly, especially secrets and external-call resilience rules.
- If the input is a spec file, follow its plan in order. If it's a short task with no spec and it touches more than ~3 files or any data source, stop and suggest `/kickoff` first.
- Never work on `main`/`master`. Create a branch using the convention in `CLAUDE.md` (default `feat/<slug>`).
- Use the task list so progress is visible.

## Loop for each task
1. **Red** — write the smallest failing test that captures the acceptance criterion. Run it; confirm it fails for the right reason.
2. **Green** — write the minimum code to pass. Reuse existing patterns and data-source clients.
3. **Refactor** — clean names, remove duplication, keep functions small. Tests stay green.
4. **Verify** — run the project's test, type-check, and lint commands from `CLAUDE.md`. Show the summary output.
5. **Commit** — one conventional commit per task (`feat:`, `fix:`, `test:`, `refactor:`). Never commit `.env*`, keys, or generated secrets; check `git diff --cached` before committing.

## Any code that calls an external API must include
timeout · retries with backoff + jitter (idempotent only) · circuit breaker or failure counter · response schema validation · fallback path · structured log line (no secrets, no full payloads) · a test that simulates the provider failing.
Update the data registry (see `CLAUDE.md` → Data sources) if a data link changed.

## When stuck
If the same failure persists after 3 genuine attempts, stop, summarize what was tried and what you suspect, and ask.

## Finish
Report: tasks done, test/type-check results, commits made, anything deferred. Suggest `/review` next.
