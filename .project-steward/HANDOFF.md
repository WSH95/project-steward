---
updated_at: 2026-09-08T10:05:34Z
updated_by: codex
session_status: closed
branch: fix/reliability-0.4.1
---
# Handoff

## Now

Tasks 1 and 2 of the approved 0.4.1 reliability plan are complete. Task 2 keeps
selected Git paths lexical through their final component, so ordinary and
dangling symlinks are committed as links while parent escapes are rejected.
Whole-index checks translate project-relative selections when an explicit
managed root is below the Git top level. Implicit discovery stops at the nearest
Git boundary, and operation detection uses `git rev-parse --git-path` for
ordinary repositories and `.git`-file layouts (ADR 0026).

The focused Git, path, and session set passes 31 tests. The full suite passes
217 tests on Python 3.12.3, and compileall exits 0. Self doctor reports 40
checks, 3 expected warnings, and 0 failures. `git diff --check` passes. The
local Task 2 commit is ready for independent review.

## In flight

- Independent Task 2 review and integration remain with the controller.
- Tasks 3-5 in `docs/plans/2026-09-08-reliability-fixes.md` are open.

## Next steps

1. Review the Task 2 commit against `task-2-brief.md` and `task-2-report.md`;
   rerun the 31 focused tests and integrate it if accepted.
2. Continue Task 3: make build and publication previews safe.

## Blockers

- None.

## Key files

- `plugin-src/src/project_steward/gitutil.py` validates lexical commit paths,
  compares index names in Git's namespace, and resolves operation metadata.
- `plugin-src/src/project_steward/paths.py` stops discovery at the nearest Git
  boundary after checking managed and legacy markers.
- `tests/test_git_commits.py`, `tests/test_paths.py`, and
  `tests/test_sessions.py` cover symlinks, index scope, repository boundaries,
  explicit roots, ordinary operation markers, and a real linked worktree merge.
- `README.md`, `plugin-src/references/security-model.md`,
  `plugin-src/references/session-protocol.md`, and
  `plugin-src/references/cross-platform.md` document the behavior.

## Tried and rejected

- Resolving the complete selected path follows its final symlink and can stage
  the target. Resolving only the parent preserves the Git entry while still
  rejecting an escaping parent.
- Comparing project-relative selections directly with Git-root-relative index
  names rejects valid staged files when the managed root is a subdirectory.
  `git rev-parse --show-prefix` supplies the comparison prefix without changing
  the literal add and commit pathspecs.
- Looking under `<root>/.git` misses operation files in linked worktrees and
  submodules because `.git` is a file there. Git's `--git-path` resolves the
  repository-specific metadata location.

## Warnings

- Root AGENTS.md/CLAUDE.md retain the supported legacy protocol. Self doctor
  warns about the absent WORKFLOW.md and local Codex hooks; those are upgrade
  notices, not failed checks. Adoption is through reviewed re-init.
- Symlink regressions skip on accounts without symlink privileges, and the
  linked-worktree regression skips when Git worktrees are unavailable. This
  Linux run exercised them without skips. Native Python 3.7 and Windows/macOS
  execution were not available for Task 2.
- No push or publication is authorized. Preserve the source checkout's
  unrelated file-mode changes during integration.
