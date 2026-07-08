---
updated_at: 2026-07-08T01:23:46Z
updated_by: codex
session_status: closed
branch: main
last_commit: b99966c
---
# Handoff

## Now

Agent artifact maintenance skill work is in progress on top of
`b99966c`. The new skill lives at
`plugin-src/skills/agent-artifact-maintainer/` and teaches agents to keep
skill/plugin development repos organized, maintain generated dist
scripts, and publish artifacts to review PRs in agent-skills or
agent-plugins repos. This repo now also has `agent-artifacts.json` and
`tools/publish_agent_artifact_pr.py` as the project-local publishing
implementation.

## In flight

- Uncommitted changes are expected in the new skill, publish script,
  `agent-artifacts.json`, tests, README, and `.project-steward/`.
- TDD red/green was performed for the new skill contract and publish
  script dry-run behavior; focused and full tests pass.
- AGENTS.md still contains one stale non-managed prose reference to
  `plugin/references/cross-platform.md`; it was left untouched because
  the project guardrail says AGENTS.md edits stay inside managed blocks.

## Next steps

1. Re-run final verification if additional edits happen.
2. Commit with a Conventional Commit, e.g.
   `feat(skills): add agent artifact maintainer`.
3. Push only with explicit user approval.
4. If the AGENTS.md guardrail is relaxed later, update the remaining
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
- `tools/publish_agent_artifact_pr.py` — project-local PR publishing
  script for generated agent artifacts.
- `agent-artifacts.json` — local publish manifest; target repo is blank
  until first publish.
- `tests/test_payload_builder.py` — pins extraction layout and Codex
  command-like companions.
- `tests/test_agent_artifact_maintainer.py` — pins the new skill
  contract and publish-script dry-run behavior.
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
- Current validation: focused red/green tests, 57-test suite, skill
  quick_validate, payload build, publish dry-run, generated Codex plugin
  validator, self doctor, `python3` compileall, and `git diff --check`.
- Do not run `tools/publish_agent_artifact_pr.py` without `--dry-run`
  until the target repo and copied output are reviewed.
