---
updated_at: 2026-09-08T11:08:51Z
updated_by: codex
session_status: closed
branch: fix/reliability-0.4.1
---
# Handoff

## Now

Tasks 1 and 2 are independently approved and delivered to the source checkout's
`feat/workflow-improvements` branch at `904f239`. Actual-source validation
passed 217 tests and self doctor reported 40 checks, 3 expected warnings, and 0
failures.

Task 3 and its first independent-review correction are complete on the separate
`fix/reliability-0.4.1` implementation branch (ADR 0027). Payload builds
validate every destination before mutation, including parent symlinks and
external `.git` ancestors, while preserving platform path aliases. Publication
rejects ignored local files within the artifact destination before replacement,
uses an isolated temporary preview for dry-run, and verifies commit scope.

The pre-review full suite passed 234 tests on Python 3.12.3. The correction's
five direct regressions failed before implementation; its final direct set
passes 7 tests and the full builder/publisher set passes 38. The existing
payload rebuild and the artifact-maintainer skill schema check pass. The local
98-file preview and compileall remain valid; post-correction self doctor reports
40 checks, 3 expected warnings, and 0 failures, and diff checks pass. No remote
operation ran.

## In flight

- Scoped Task 3 re-review and integration remain with the controller.
- Tasks 4 and 5 in `docs/plans/2026-09-08-reliability-fixes.md` are open.

## Next steps

1. Review the Task 3 correction commit and `task-3-report.md`, then integrate
   it if accepted. Equivalent worker checks need not be repeated for review.
2. Continue Task 4: correct handoff hook bookkeeping and edit detection.

## Blockers

- None.

## Key files

- `tools/build_plugin_payloads.py` validates output identity and path safety
  through relevant ancestors before cleanup or copying.
- `tools/publish_agent_artifact_pr.py` protects target state, builds temporary
  previews, preserves ignored local artifact files by refusing replacement,
  prints diffs, and restricts publication commits by path.
- `tests/test_payload_builder.py` and
  `tests/test_agent_artifact_maintainer.py` cover the Task 3 contract.
- `README.md` and `plugin-src/skills/agent-artifact-maintainer/` document the
  build and preview rules.

## Tried and rejected

- Matching the current payload version would block rebuilding a valid older
  generated release. Stable manifest identity distinguishes the artifact while
  allowing version changes.
- Copying a dry-run directly into a supplied checkout cannot provide a safe
  preview. A temporary local clone isolates the files, index, branch, and
  commits while retaining Git diff behavior.
- Ordinary `git status` may refresh index stat data after a tracked file is
  touched. `GIT_OPTIONAL_LOCKS=0` keeps target inspection byte-preserving.

## Warnings

- Root AGENTS.md/CLAUDE.md retain the supported legacy protocol. Self doctor
  warns about the absent WORKFLOW.md and local Codex hooks; those are upgrade
  notices, not failed checks. Adoption is through reviewed re-init.
- The skill schema validator passes with the existing system PyYAML; no
  dependency was installed. Native Python 3.7 and Windows/macOS execution were
  not available for Task 3.
- No push or publication is authorized. Preserve the source checkout's 97
  unrelated file-mode changes during integration.
