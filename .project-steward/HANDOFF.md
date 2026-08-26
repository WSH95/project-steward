---
updated_at: 2026-08-26T10:15:06Z
updated_by: cli
session_status: closed
branch: main
---
# Handoff

## Now

Project Steward 0.3.4 removes the self-referential `last_commit` field from
`HANDOFF.md`. Resume derives the handoff anchor from Git history and keeps the
existing JSON key for compatibility. A clean clone no longer treats its own
handoff commit as unexplained work. ADR 0023.

The Stop guard now handles each activity batch once. If no project state
changed, the agent leaves tracked files alone instead of creating another
checkpoint. The full release suite passes: 85 tests, compileall, self doctor
36/0, payload build, publication dry-run, skill schema, Claude, Codex, and
Grok validators, launcher smoke, and `git diff --check`.

Source 0.3.4 is on `origin/main` at `4750e38`. The generated payload is in
`agent-plugins` PR #11 at `13fc90f`:
https://github.com/WSH95/agent-plugins/pull/11

## In flight

- `agent-plugins` PR #11 is open with a clean merge state and no reported
  status checks. It awaits review or merge.
- `dist/project-steward/` was rebuilt at 0.3.4 and remains gitignored.

## Next steps

1. Review and merge https://github.com/WSH95/agent-plugins/pull/11 when ready.
2. Update installed copies with the normal Claude, Codex, or Grok plugin
   update flow after the PR merges.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/sessions.py` derives the handoff anchor and
  removes legacy metadata during lifecycle writes.
- `plugin-src/src/project_steward/gitutil.py` provides path-specific Git
  history and dirty-state checks.
- `plugin-src/src/project_steward/hooks.py` tracks handled Stop-guard batches.
- `tests/test_sessions.py` and `tests/test_hooks_stop_guard.py` cover the two
  regressions.

## Tried and rejected

- Embedding the containing commit's SHA in a tracked file cannot converge:
  changing the file changes the commit hash.
- Renaming the resume JSON key was rejected because deriving its value fixes
  the bug without breaking consumers.
- A runtime-only acknowledgement command was unnecessary. The Stop guard can
  remember the handled activity batch and tell the agent not to write files.

## Warnings

- Do not manually edit generated `dist/project-steward/` output; rebuild
  from `plugin-src/`.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.
- Do not push this source repo without explicit user approval.
