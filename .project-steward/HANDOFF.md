---
updated_at: 2026-08-16T14:13:33Z
updated_by: grok
session_status: closed
branch: main
last_commit: ed88bad
---
# Handoff

## Now

Project Steward 0.3.2 on `main` adds Grok Build
compatibility without forking a third plugin. Grok installs the existing
Claude payload (`grok plugin marketplace add` on
`dist/project-steward/claude` or `https://github.com/WSH95/agent-plugins`,
then `grok plugin install project-steward --trust`). The shared hook
dispatcher accepts Grok camelCase stdin after Claude/Codex snake_case
keys, counts `search_replace` / `run_terminal_command` as mutating/shell
activity, skips Grok teardown Stops (`shutdown` / `channel_closed`), and
records agent `grok` when `GROK_SESSION_ID` / `GROK_HOOK_EVENT` is set
even though the frozen Claude `hooks.json` still passes `--agent
claude`. ADR 0021.

Claude `hooks.json`, Codex hooks/marketplace, Stop `decision: block`
JSON, and remind `systemMessage` output are unchanged. 77 tests,
compileall, `doctor --self` 36/0, `grok plugin validate` on the Claude
plugin dir, and `git diff --check` passed. `claude plugin validate` and
isolated Codex smoke were not re-run this session.

User approved commit, push of this source repo, and an
`agent-plugins` publish PR for the 0.3.2 payload. `agent-plugins` PR #5
is the 0.3.1 payload and may still be open.

## In flight

- Source 0.3.2 commit/push and `agent-plugins` publish PR in progress.
- `dist/project-steward/` was rebuilt for 0.3.2 and remains
  gitignored/generated.

## Next steps

1. After origin push, publish
   `project-steward-plugin` to `WSH95/agent-plugins` (new PR; do not
   merge it).
2. Grok users: `grok plugin install project-steward --trust`. Use
   `/session-resume` or `/project-steward:resume`, not bare `/resume`.
3. After the payload PR merges, run `claude plugin update
   project-steward@agent-plugins` and `pipx reinstall project-steward`
   where this plugin/CLI should be updated.
4. Do not add a sibling `.grok-plugin/marketplace.json` next to
   `.claude-plugin/` without re-checking for a double listing.
5. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.

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
- `.project-steward/DECISIONS.md` ADR 0021 — Grok reuses the Claude
  payload; hook stdin is dual-contract; no third tree.

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
- A third `plugin-src/grok/` payload or sibling `.grok-plugin/`
  marketplace index — rejected (ADR 0021): Grok already lists one
  `project-steward` from the Claude marketplace file.

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
