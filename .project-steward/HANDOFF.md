---
updated_at: 2026-07-08T00:12:43Z
updated_by: codex
session_status: closed
branch: main
last_commit: 3f11ead
---
# Handoff

## Now

Development-layout refactor is implemented, freshly verified, and being
committed/pushed at the user's request. Canonical plugin authoring now
lives under `plugin-src/`; clean extraction payloads are generated with
`python3 tools/build_plugin_payloads.py --clean --out
dist/project-steward`. The old checked-in payload source directories
(`plugin/`, `plugins/project-steward/`, root `.agents/plugins/`, root
`.claude-plugin/`, and `codex/prompts/`) were removed from the
development tree. `dist/` is gitignored and contains the latest generated
Claude and Codex output for local inspection/extraction. AGENTS.md's
managed commands block was updated after explicit user approval; ADR 0014
records the high-risk-file edit.

## In flight

- Commit/push workflow for the source-layout refactor is in progress in
  this session. If resuming mid-flight, run `git status --short --branch`
  and push `main` if it is ahead of `origin/main`.
- Before staging, `git status` showed many deletes under the old payload
  paths and untracked `plugin-src/`/`tools/` additions. This was expected
  until staging; the sandbox could not use `git mv` because `.git/index.lock`
  was read-only, so Git had not yet recognized renames in status output.
- AGENTS.md still contains one stale non-managed prose reference to
  `plugin/references/cross-platform.md`; it was left untouched because
  the project guardrail says AGENTS.md edits stay inside managed blocks.

## Next steps

1. If this handoff is read before the user-requested push completes,
   finish the push from `main` after confirming tests remain green.
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
- Fresh pre-commit validation passed locally: 51 tests, payload build,
  generated Codex plugin validator, self doctor, `python3` compileall,
  and `git diff --check`. Earlier smoke coverage also included
  non-editable packaged install + init and isolated Codex
  marketplace/plugin add + prompt-input.
