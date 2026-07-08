---
updated_at: 2026-07-08T14:38:53Z
updated_by: claude
session_status: closed
branch: main
last_commit: 55ee35a
---
# Handoff

## Now

Claude plugin runtime packaging has been optimized for Project Steward
0.3.0. The generated Claude payload now ships a plugin-local
`bin/project-steward` pure-Python launcher, hook commands prefer that
launcher before falling back to an installed CLI, Windows hooks have
explicit `commandWindows` variants, and the old POSIX-only hook shim is
removed from generated payloads.

Docs, metadata, `doctor`, payload builder, changelog, and regression tests
were updated to describe and enforce the new launcher behavior. Full
verification passed: pytest, compileall, `doctor --self`, payload build,
Codex plugin validation, `git diff --check`, and built Claude launcher
smoke test.

The source implementation is committed as `7bf67c3`
(`feat(claude): bundle plugin launcher for hooks`). The user-level pipx
CLI was force-reinstalled from this checkout and reports
`project-steward 0.3.0`. The generated plugin payload was published to
`WSH95/agent-plugins` as PR #2:
https://github.com/WSH95/agent-plugins/pull/2

## In flight

- Local stewardship publication record needs a commit after this handoff
  refresh.
- `dist/project-steward/` was rebuilt for validation and remains
  gitignored/generated.

## Next steps

1. Commit this publication checkpoint with `.project-steward/` updates
   included.
2. Do not push or publish further changes without explicit approval.
3. Review/merge https://github.com/WSH95/agent-plugins/pull/2 when ready.
4. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.
5. When a standalone skill should be published, add a deliberate
   `agent-artifacts.json` skill entry targeting
   `git@github.com:WSH95/agent-skills.git` and publish by PR; do not
   upload skills ad hoc.
6. If the AGENTS.md guardrail is explicitly relaxed, update the remaining
   non-managed prose reference from
   `plugin/references/cross-platform.md` to
   `plugin-src/references/cross-platform.md`.

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
- `tools/publish_agent_artifact_pr.py` — project-local PR publishing
  script for generated agent artifacts.
- `agent-artifacts.json` — local publish manifest; currently only the
  generated Project Steward plugin artifact is configured.
- `tests/test_payload_builder.py` — pins extraction layout and Codex
  command-like companions.
- `tests/test_codex_plugin.py` / `tests/test_survey_doctor_cli.py` —
  pin Codex hook root schema and self-doctor rejection of invalid
  metadata.
- `tests/test_agent_artifact_maintainer.py` — pins the artifact
  maintainer skill contract and publish-script behavior.
- `.project-steward/DECISIONS.md` ADR 0018 — root distribution repo
  install entry-point decision.

## Tried and rejected

- Adding a skill artifact to `agent-artifacts.json` now — rejected
  because `agent-skills` must stay empty until the user asks to publish a
  specific standalone skill.
- Editing non-managed AGENTS.md prose — still avoided because the
  project guardrail limits AGENTS.md edits to managed blocks unless the
  user explicitly relaxes that guardrail.

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
- Do not push this source repo without explicit user approval.
