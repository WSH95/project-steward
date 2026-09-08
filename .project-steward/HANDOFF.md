---
updated_at: 2026-09-08T09:14:31Z
updated_by: codex
session_status: closed
branch: fix/reliability-0.4.1
---
# Handoff

## Now

Task 1 of the approved 0.4.1 reliability plan is complete (ADR 0025). Migration
now preflights all inputs and destinations, preserves every raw attempt, rejects
conflicting retries, and verifies the live legacy tree before removal. Init
waits for migration, and partial Build/Test/Lint updates retain other command
rows and custom managed-block lines.

Validation passed: 199 tests on Python 3.12.3, focused preservation and init
regressions, `git diff --check`, and self doctor with 40 checks, 3 expected
upgrade warnings, and 0 failures. Native Python 3.7 and Windows/macOS execution
were not available in this task.

## In flight

- The controller's independent Task 1 review and integration remain.
- Tasks 2-5 in `docs/plans/2026-09-08-reliability-fixes.md` are still open.

## Next steps

1. Review and integrate the local Task 1 commit without touching the source
   checkout's unrelated file-mode differences.
2. Continue with Task 2: respect Git paths, repository boundaries, and
   worktrees.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/migrate.py` contains the preflight, plan, raw
  backup, verified apply, and narrow retry rules; `cli.py` exposes dry-run and
  blocks init while legacy state remains.
- `plugin-src/src/project_steward/managed_blocks.py` and `scaffold.py` preserve
  CRLF user prose and partial command settings.
- `tests/test_migrate.py` and `tests/test_scaffold_init.py` cover conflicts,
  malformed markers, failures, retries, backups, and re-init preservation.
- `plugin-src/references/migration-from-projectforge.md` documents the recovery
  and retry behavior.

## Tried and rejected

- Reusing the shared backup root can modify or obscure an older flat backup.
  Each new attempt carries its own ignore file before raw copying starts.
- Treating any pre-existing task document as a completed retry can discard
  changed legacy tasks. Documents must match the current transformed legacy
  bytes; only generated metadata timestamps have narrow equivalence rules.

## Warnings

- Root AGENTS.md/CLAUDE.md retain the supported legacy protocol. Self doctor
  warns about the absent WORKFLOW.md and local Codex hooks; those are upgrade
  notices, not failed checks. Adoption is through reviewed re-init.
- No push or publication is authorized. Preserve the source checkout's
  unrelated file-mode changes during integration.
