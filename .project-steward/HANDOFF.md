---
updated_at: 2026-08-26T09:42:52Z
updated_by: cli
session_status: closed
branch: main
last_commit: 1f48279
---
# Handoff

## Now

Project Steward 0.3.3 makes the init scaffold produce a 44-line `AGENTS.md`.
It keeps the same three managed-block identifiers and uses a shorter session
workflow. The generated
project-state templates use plain, factual language. A new shared writing
guide tells init, progress, resume, and handoff skills to edit only new prose
and to use an installed `humanizer` skill when available. Humanizer is not a
runtime dependency. ADR 0022.

The user approved the exact root `AGENTS.md` diff, and only its three managed
blocks were updated. The final tree passes 81 tests, compileall, self doctor
36/0, Claude and Grok validation, the Codex plugin validator, and
`git diff --check`.

Source 0.3.3 is on `origin/main` at `b3b887c`. The generated Claude and Codex
payloads were merged through `agent-plugins` PR #10 at merge commit `c65e1a2`:
https://github.com/WSH95/agent-plugins/pull/10

## In flight

- No 0.3.3 publication work remains. PR #10 was merged on 2026-08-26.
- `dist/project-steward/` was rebuilt and remains gitignored/generated.
- The earlier Grok install documentation PR #8 is merged.

## Next steps

1. Update installed copies with the normal Claude, Codex, or Grok plugin
   update flow when ready.
2. Continue with the next open task in `.project-steward/PLAN.md`.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/scaffold.py` builds the three managed
  `AGENTS.md` blocks.
- `plugin-src/src/project_steward/templates/` contains the files created by
  init.
- `plugin-src/references/documentation-style.md` is the shared writing
  contract and optional Humanizer integration.
- `plugin-src/skills/` and `plugin-src/codex/prompts/` apply that contract
  while agents update project state.
- `tests/test_scaffold_init.py` and `tests/test_skill_text.py` cover the
  compact output, preserved user prose, and optional Humanizer behavior.

## Tried and rejected

- Bundling the full Humanizer skill was rejected. It would enlarge the
  plugin and create a versioned dependency for behavior that can remain
  optional.
- Automatically rewriting existing project history was rejected because it
  would create unrelated diffs and could flatten the project's own voice.
- Moving the full session protocol to another managed state file was
  rejected because generic agents still need the basic workflow in
  `AGENTS.md`.

## Warnings

- Do not manually edit generated `dist/project-steward/` output; rebuild
  from `plugin-src/`.
- The root `AGENTS.md` update was explicitly approved on 2026-08-26. Its
  unmarked content remains out of scope.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.
- Do not run Humanizer across historical entries or user prose. Limit it to
  text already being created or changed.
- Keep required `HANDOFF.md` headings, front matter, commands, links, and
  managed markers unchanged during a style pass.
- Do not push this source repo without explicit user approval.
