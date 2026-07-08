---
updated_at: 2026-07-08T03:40:31Z
updated_by: codex
session_status: closed
branch: main
last_commit: HEAD
---
# Handoff

## Now

Codex hook schema fix is implemented and prepared as Project Steward
0.3.0. The canonical Codex hook template no longer has a top-level
`description`, self-doctor now rejects extra root keys in
`plugin-src/codex/hooks/hooks.json`, and tests pin both source and
generated hook root shape. Live `/home/wsh/.codex/hooks.json` was also
cleaned so Codex CLI startup no longer reports the hook parse warning.

This source repo remains the canonical Project Steward development repo
and is on `main`. After the requested commit, it is expected to be ahead
of `origin/main` by 2 commits and clean.

## In flight

- Current HEAD should contain the 0.3.0 Codex hook-schema fix once the
  requested commit is made: hook template cleanup, doctor schema
  enforcement, regression tests, version bump, and steward state updates.
- `gh repo view WSH95/project-steward` reported the source repo is still
  PRIVATE during this session. The user said they will open-source it at
  `https://github.com/WSH95/project-steward.git`, but that has not
  happened yet as of the check.
- Distribution follow-up remains complete: `WSH95/agent-plugins` is
  public/MIT and synced at commit `fe6ae8d`; `WSH95/agent-skills` is
  public/MIT and intentionally contains only `LICENSE` and `README.md`.

## Next steps

1. Do not push without explicit approval.
2. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.
3. When a standalone skill should be published, add a deliberate
   `agent-artifacts.json` skill entry targeting
   `git@github.com:WSH95/agent-skills.git` and publish by PR; do not
   upload skills ad hoc.
4. If the AGENTS.md guardrail is explicitly relaxed, update the remaining
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
