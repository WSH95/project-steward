---
updated_at: 2026-07-08T03:55:43Z
updated_by: codex
session_status: closed
branch: main
last_commit: HEAD
---
# Handoff

## Now

Codex hook schema fix is implemented as Project Steward 0.3.0 and has
been published to the `WSH95/agent-plugins` repo by PR:
https://github.com/WSH95/agent-plugins/pull/1. The PR branch is
`publish/project-steward-plugin-0.3.0` at target commit `eb2daf4`,
against `main`.

The canonical Codex hook template no longer has a top-level
`description`, self-doctor now rejects extra root keys in
`plugin-src/codex/hooks/hooks.json`, and tests pin both source and
generated hook root shape. Live `/home/wsh/.codex/hooks.json` was also
cleaned so Codex CLI startup no longer reports the hook parse warning.

This source repo remains the canonical Project Steward development repo
and is on `main`. Source `origin/main` already points at `a470e90`
(`fix(codex): enforce strict hook schema`) as of this session.

## In flight

- `/tmp/agent-plugins` is on branch
  `publish/project-steward-plugin-0.3.0`, tracking the pushed remote
  branch and clean after PR creation.
- `gh repo view WSH95/project-steward` reported the source repo is still
  PRIVATE during this session. The user said they will open-source it at
  `https://github.com/WSH95/project-steward.git`, but that has not
  happened yet as of the check.
- Distribution follow-up remains complete: `WSH95/agent-plugins` is
  public/MIT and synced at commit `fe6ae8d`; `WSH95/agent-skills` is
  public/MIT and intentionally contains only `LICENSE` and `README.md`.

## Next steps

1. Review/merge https://github.com/WSH95/agent-plugins/pull/1 when ready.
2. Do not push or merge further changes without explicit approval.
3. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.
4. When a standalone skill should be published, add a deliberate
   `agent-artifacts.json` skill entry targeting
   `git@github.com:WSH95/agent-skills.git` and publish by PR; do not
   upload skills ad hoc.
5. If the AGENTS.md guardrail is explicitly relaxed, update the remaining
   non-managed prose reference from
   `plugin/references/cross-platform.md` to
   `plugin-src/references/cross-platform.md`.

## Blockers

- None for the distribution repo work.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.

## Key files

- `plugin-src/` — canonical plugin source: shared skills/references,
  Python package/templates, Claude commands/hooks, Codex prompts/hooks,
  and shared metadata.
- `tools/build_plugin_payloads.py` — generates extractable Claude and
  Codex payloads from `plugin-src/`.
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
