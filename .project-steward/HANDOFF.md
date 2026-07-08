---
updated_at: 2026-07-08T16:04:06Z
updated_by: claude
session_status: closed
branch: main
last_commit: 1ae1e99
---
# Handoff

## Now

Project Steward 0.3.1 has a committed Codex-side hardening pass after
the Claude Code `commandWindows` review. The Claude hook wrapper
`plugin-src/claude/hooks/run-hook.cmd` now tries every Python launcher
leg before falling back to an installed `project-steward`, so one broken
`python3`/`py` executable does not skip a working launcher. Failed
fallbacks still exit 0 silently so hooks do not break the agent loop.

Docs and decisions now separate the products accurately: Claude Code has
no `commandWindows` hook field; Codex currently documents
`commandWindows`, but Project Steward does not need it in the Codex
plugin path because the Codex companion invokes the installed CLI
directly. ADR 0020 records that distinction.

Regression tests were added for wrapper fallback behavior, release
version consistency, and stale cross-agent wording. Verification passed:
70 tests, compileall, `doctor --self`, payload build, Claude plugin and
marketplace validation, Codex plugin validation, built wrapper smoke,
isolated Codex install/prompt-input smoke, and `git diff --check`.

## In flight

- No active implementation work remains in this session.
- `dist/project-steward/` was rebuilt for validation and remains
  gitignored/generated.

## Next steps

1. Do not push or publish further changes without explicit approval.
2. On approval, release 0.3.1: push main, then open a NEW agent-plugins
   PR via `tools/publish_agent_artifact_pr.py` (PR #2 merged
   2026-07-08T11:55Z and carries the 0.3.0-era payload whose Windows
   hooks are broken); after merge, `claude plugin update
   project-steward@agent-plugins` and `pipx reinstall project-steward`.
3. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.
4. When a standalone skill should be published, add a deliberate
   `agent-artifacts.json` skill entry targeting
   `git@github.com:WSH95/agent-skills.git` and publish by PR; do not
   upload skills ad hoc.

## Blockers

- None for this implementation.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.

## Key files

- `plugin-src/` — canonical plugin source: shared skills/references,
  Python package/templates, Claude commands/hooks, Codex prompts/hooks,
  and shared metadata.
- `tools/build_plugin_payloads.py` — generates extractable Claude and
  Codex payloads from `plugin-src/`.
- `plugin-src/claude/bin/project-steward` — plugin-local Claude launcher
  into bundled `src/`.
- `plugin-src/claude/hooks/run-hook.cmd` — polyglot POSIX/cmd hook
  wrapper used by Claude Code without requiring Git Bash on Windows.
- `tools/publish_agent_artifact_pr.py` — project-local PR publishing
  script for generated agent artifacts.
- `agent-artifacts.json` — local publish manifest; currently only the
  generated Project Steward plugin artifact is configured.
- `tests/test_payload_builder.py` — pins extraction layout and Codex
  command-like companions, plus wrapper fallback and version consistency.
- `tests/test_codex_plugin.py` / `tests/test_survey_doctor_cli.py` —
  pin Codex hook root schema and self-doctor rejection of invalid
  metadata.
- `tests/test_agent_artifact_maintainer.py` — pins the artifact
  maintainer skill contract and publish-script behavior.
- `.project-steward/DECISIONS.md` ADR 0020 — Claude Code and Codex
  `commandWindows` support are separate contracts.

## Tried and rejected

- Adding a skill artifact to `agent-artifacts.json` now — rejected
  because `agent-skills` must stay empty until the user asks to publish a
  specific standalone skill.
- Editing non-managed AGENTS.md prose — still avoided because the
  project guardrail limits AGENTS.md edits to managed blocks unless the
  user explicitly relaxes that guardrail.
- Reintroducing `commandWindows` to Claude hooks — rejected because
  Claude Code does not support that field.
- Treating Codex as having the same limitation — rejected because Codex
  currently documents `commandWindows`; this project simply does not need
  to use it for Codex's installed-CLI companion path.

## Warnings

- Do not manually edit generated `dist/project-steward/` output; rebuild
  from `plugin-src/`.
- Do not restore `plugin/` or `plugins/project-steward/` as source
  directories; generated payloads are deliberately built from
  `plugin-src/`.
- Codex prompt files are optional command-like companions only; Codex
  skills remain the supported plugin UX.
- Codex hooks remain a manual companion file unless/until
  plugin-bundled Codex hooks are field-tested separately.
- Do not use AGENTS.md or CLAUDE.md as progress logs; session state
  belongs under `.project-steward/`.
- Do not push this source repo without explicit user approval.
