---
updated_at: 2026-07-08T00:50:19Z
updated_by: codex
session_status: closed
branch: main
last_commit: 33c1be1
---
# Handoff

## Now

Development-layout refactor was committed and pushed at `33c1be1`.
Follow-up cleanup is implemented and verified: the payload builder no
longer copies Codex hook config into the generated Claude Code plugin.
Claude output contains only Claude hooks; Codex hook config remains in
the Codex extraction tree at `dist/project-steward/codex/hooks/hooks.json`.

## In flight

- If resuming before this cleanup is committed, expect changes in
  `tools/build_plugin_payloads.py`, `tests/test_payload_builder.py`, and
  `.project-steward/`; otherwise `main` may be ahead of `origin/main`.
- Regression test red/green was performed for the Claude payload no
  longer containing `hooks/codex.hooks.json`; full verification is green.
- AGENTS.md still contains one stale non-managed prose reference to
  `plugin/references/cross-platform.md`; it was left untouched because
  the project guardrail says AGENTS.md edits stay inside managed blocks.

## Next steps

1. If this cleanup is committed but not pushed, push only with explicit
   user approval.
2. When preparing the external agent-plugins repo, copy
   `dist/project-steward/claude/` for Claude Code and
   `dist/project-steward/codex/` for Codex.
3. If the AGENTS.md guardrail is relaxed later, update the remaining
   non-managed prose reference from `plugin/references/cross-platform.md`
   to `plugin-src/references/cross-platform.md`.

## Blockers

- None for the implemented refactor.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.

## Key files

- `plugin-src/` — canonical plugin source: shared skills/references,
  Python package/templates, Claude commands/hooks, Codex prompts/hooks,
  and shared metadata.
- `tools/build_plugin_payloads.py` — generates extractable Claude and
  Codex payloads from `plugin-src/`.
- `tests/test_payload_builder.py` — pins extraction layout and Codex
  command-like companions.
- `plugin-src/src/project_steward/hooks.py` and
  `plugin-src/src/project_steward/sessions.py` — lifecycle behavior core.
- `.project-steward/DECISIONS.md` ADR 0013 — source-of-truth decision
  for generated payload layout.

## Tried and rejected

- `git mv` for tracked moves — failed because the sandbox cannot write
  `.git/index.lock`; filesystem moves were used instead.
- Keeping committed generated payload copies — rejected by the user's
  development-maintenance requirement.
- Bundling Codex lifecycle hooks into the Codex plugin — still avoided;
  Codex gets manual hooks output alongside the skills-first plugin.

## Warnings

- Do not manually edit generated `dist/project-steward/` output; rebuild
  from `plugin-src/`.
- Do not restore `plugin/` or `plugins/project-steward/` as source
  directories; they were deliberately replaced by generated payloads.
- Codex prompt files are optional command-like companions only; Codex
  skills remain the supported plugin UX.
- Current follow-up validation: focused red/green payload-builder test,
  51-test suite, `python3` compileall, self doctor 34 checks / 0
  failures, payload build, generated Codex plugin validator, and
  `git diff --check`.
