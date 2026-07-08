---
updated_at: 2026-07-08T01:56:43Z
updated_by: codex
session_status: closed
branch: main
last_commit: addfe39
---
# Handoff

## Now

`agent-artifact-maintainer` is implemented and committed at `addfe39`.
The public plugin distribution repository now exists at
`https://github.com/WSH95/agent-plugins` with MIT license and README.
Generated Project Steward plugin payload was published there under
`project-steward/` and pushed as `c78ea23`. This repo's
`agent-artifacts.json` now points at
`git@github.com:WSH95/agent-plugins.git` for future publishes.

## In flight

- Uncommitted local changes are expected only for recording the
  `agent-plugins` target repo in `agent-artifacts.json`, its test
  expectation, and this Project Steward state update; verification is
  complete.
- Target repo state was verified with `gh repo view`: visibility PUBLIC,
  license MIT, default branch `main`.
- AGENTS.md still contains one stale non-managed prose reference to
  `plugin/references/cross-platform.md`; it was left untouched because
  the project guardrail says AGENTS.md edits stay inside managed blocks.

## Next steps

1. Commit with a Conventional Commit, e.g.
   `chore(publish): record agent-plugins target`.
2. Push this source repo only with explicit user approval.
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
- Current `agent-plugins` validation: repo metadata verified public/MIT;
  target checkout clean after push; copied Codex plugin validator passed
  before commit.
- Current source-repo validation for the manifest update: 57 tests,
  `python3` compileall, self doctor, payload build, skill
  quick_validate, generated Codex plugin validator, publish dry-run to
  `/tmp/agent-plugins`, and `git diff --check`.
- Do not run `tools/publish_agent_artifact_pr.py` without `--dry-run`
  until the target repo and copied output are reviewed.
