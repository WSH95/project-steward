---
updated_at: 2026-09-08T12:44:31Z
updated_by: codex
session_status: closed
branch: feat/workflow-improvements
---
# Handoff

## Now

Tasks 1–4 of the approved 0.4.1 reliability plan are independently reviewed and
delivered to `/home/wsh/Documents/project-steward` through `69bb309` (Task 4
code through `0ad0306`). Task 5 is implemented in
`/tmp/project-steward-reliability` on
`fix/reliability-0.4.1`. Shared config normalization, parsed Codex TOML
semantics, backend.json identity, and all three 0.4.1 version sources are ready
for independent review.

The isolated source passes 271 tests in 10.94s on Linux/Python 3.12.3. Self
doctor reports 40 checks, 3 existing setup warnings, and 0 failures. The
installed-release smoke script is prepared at
`/tmp/project-steward-reliability-package-smoke.py`; it has passed a syntax
check but has not run against the pending wheel. Nothing was pushed or
published.

## In flight

- Task 5 code, tests, release metadata, changelog, relevant docs, and project
  records are the current isolated-branch changes awaiting review.
- Task 5 scope is limited to the source/test/doc/record changes in its report;
  `/tmp/project-steward-reliability-package-smoke.py` is an external review
  artifact and
  `.superpowers/sdd/2026-09-08-reliability-fixes/task-5-report.md` is ignored
  task evidence.
- The controller owns independent Task 5 and whole-branch review, release
  payload/wheel/plugin/fallback validation, installed smoke, and local delivery.
- The source delivery target remains `feat/workflow-improvements`.

## Next steps

1. Review the Task 5 commit against
   `.superpowers/sdd/2026-09-08-reliability-fixes/task-5-brief.md`; record and
   correct any Critical or Important findings before release validation.
2. Run the controller-owned payload, forced older-Python fallback, syntax,
   plugin, offline wheel, and installed-release checks from
   `.superpowers/sdd/2026-09-08-reliability-fixes/validation-checklist.md`.
   Execute `/tmp/project-steward-reliability-package-smoke.py` with the clean
   wheel venv path after installing 0.4.1.
3. Complete the whole-branch review, then use the preservation helper to
   fast-forward the reviewed commits into `feat/workflow-improvements`. Record
   the real actual-source suite, doctor, mode, and instruction-file evidence.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/state.py` owns config normalization and the
  backend-derived effective config identity.
- `plugin-src/src/project_steward/doctor.py` reports state-layer config
  diagnostics instead of maintaining a second validator.
- `plugin-src/src/project_steward/codex_setup.py` uses parsed TOML mappings for
  native semantic checks and retains the conservative older-Python fallback.
- `plugin-src/src/project_steward/templates/project-steward/config.toml.template`
  no longer emits backend.name.
- `tests/test_workflow_init.py`, `tests/test_hooks_stop_guard.py`, and
  `tests/test_codex_setup.py` contain the Task 5 regressions.

## Tried and rejected

- Keeping separate runtime and doctor config validators allowed their behavior
  to drift; the state layer now returns normalized config and diagnostics to
  both callers.
- Scanning native Codex TOML after parsing misread string contents and escaped
  keys. Semantic decisions now use the parsed mapping; only the conservative
  older-Python syntax check still scans its supported subset.
- Rewriting legacy config during backend adoption would violate byte
  preservation. The compatibility field is derived in memory from backend.json.

## Warnings

- Self doctor warnings are the existing absent WORKFLOW.md and unconfigured
  local Codex hooks/activation; they are upgrade notices, not failures.
- Native Python 3.7 and Windows/macOS execution were not available for Task 5.
- The existing dist payload is still 0.4.0 by design. The controller must
  rebuild and validate it after review. The 0.4.1 wheel and smoke have not run.
- No push or publication is authorized. Preserve the source checkout's 97
  unrelated file-mode changes and root AGENTS.md/CLAUDE.md during integration.
