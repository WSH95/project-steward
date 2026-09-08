---
updated_at: 2026-09-08T07:00:51Z
updated_by: codex
session_status: closed
branch: feat/workflow-improvements
---
# Handoff

## Now

Project Steward 0.4.0 implements the approved workflow improvements in
`docs/plans/2026-09-08-workflow-improvements.md` (ADR 0024). Generated AGENTS.md
points to WORKFLOW.md; new projects default to local milestone commits;
external task backends retain task ownership with readable PLAN/HANDOFF
context; init configures project-local Codex hooks with an opt-out.

Validation passed: 174 tests, 48 tests under the simulated older-Python Codex
fallback (12 native-parser cases skipped), compileall, Python 3.7 syntax checks,
self doctor with zero failures, payload build, installed-wheel smoke, local
publication dry-run, Claude/Codex/Grok manifests, changed skill schemas, and the
bundled launcher. Full native OS/Python CI was not run in this session.

## In flight

- No 0.4.0 implementation tasks remain. The changes are ready for local review;
  no publication or push was requested.
- The checkout's pre-existing file-mode-only differences are unrelated to this
  implementation and must stay out of its commits.

## Next steps

1. Review the local 0.4.0 change and use the normal release workflow if the user
   requests publication. Rebuild payloads with the command in AGENTS.md.
2. For future development, continue the open backlog in PLAN.md: verify backend
   install commands against upstream documentation, then field-test thresholds.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/scaffold.py` and packaged templates implement
  the new documents, defaults, and reviewed re-init behavior.
- `plugin-src/src/project_steward/codex_setup.py` plans and checks local hook
  setup. `plugin-src/src/project_steward/templates/codex-hooks.json.template`
  supplies both installed wheels and generated payloads.
- `plugin-src/src/project_steward/gitutil.py` checks the staged scope and makes
  literal path-scoped commits; CLI init suggestions include new Codex files.
- `plugin-src/src/project_steward/backend_broker.py` and `sessions.py` keep
  workflow instructions and recaps aligned with backend.json.
- `plugin-src/skills/` contains the agent workflows that maintain document
  bodies and choose semantic commits; the CLI does not make those judgments.

## Tried and rejected

- Exporting every external task into Markdown would create a second task
  store. Keep a focused, dated overview with backend IDs instead.
- A permissive TOML subset reader cannot validate arbitrary Codex settings.
  Python 3.11+ uses tomllib; older runtimes auto-merge only a narrow, unambiguous
  subset and explain when manual merging or a newer Python is needed.
- Codex project files cannot establish trust or approve execution. Setup and
  doctor leave those steps to Codex's project and /hooks UI.

## Warnings

- Existing configurations keep their commit policy. This repo still uses ask;
  the user's session Git instructions authorize the local implementation commit.
- Root AGENTS.md/CLAUDE.md retain the supported legacy protocol. Self doctor
  warns about the absent WORKFLOW.md and local Codex hooks; those are upgrade
  notices, not failed checks. Adoption is through reviewed re-init.
- Generated `dist/project-steward/` output is ignored; rebuild from plugin-src.
- No push or publication is authorized. Preserve unrelated working-tree edits.
