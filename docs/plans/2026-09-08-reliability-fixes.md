# Project Steward 0.4.1 reliability fixes

Approved in conversation on 2026-09-08. Implement the audited fixes while
retaining the task, handoff, and resume workflow. This plan is the execution
specification; the user approved the design before implementation.

## Global constraints

- Python 3.7+ and standard library only. Preserve Linux, Windows, and macOS
  support, `.projectforge/` migration, legacy markers, and the `projectforge`
  alias.
- Preserve user data and unrelated work. Root AGENTS.md and CLAUDE.md are
  user-owned and are not part of this repository's planned edits. Generated
  files and migration fixtures may exercise their managed blocks.
- Keep existing task/handoff/resume reminders; repair their bookkeeping
  without adding a broader session manager.
- Implement and make corrections using `gpt-5.6-sol` with `max` reasoning.
  Use one implementer at a time, followed by independent task review.
- Write regression tests before behavior changes. Use isolated temporary
  repositories with explicit roots; mock remote publication operations.
- Update relevant documentation and `.project-steward/` records at semantic
  checkpoints, and commit using Conventional Commits. No push, publication,
  backend installation, or unrelated features are authorized.
- The original checkout has 97 pre-existing file-mode changes. Preserve them
  during integration; all implementation happens in the isolated checkout.
- Final release version is 0.4.1 in every authoritative package/plugin source.

## Validation and delivery

Run focused regressions during each task and the full suite before the task's
commit. Run doctor before and after changes. At release completion, verify the
forced older-Python Codex fallback, compileall, Python 3.7 syntax, payload
builds, installed-wheel behavior, and available plugin validators. Report
native platforms/Python versions that were not executed locally. Integrate
verified commits into the user's checkout, preserve its unrelated modes, and
repeat final checks against that actual checkout. Keep release artifacts local.

## Task 1: Preserve migration data and partial init settings

Primary scope: migrate.py, CLI migration/init entry points, scaffold command
updates, tests/test_migrate.py, tests/test_scaffold_init.py, relevant CLI tests,
migration documentation, and project records.

1. Preflight every required read, marker validation, target conflict, and
   proposed write before migration mutates files. Add `migrate --dry-run` to
   show planned changes and conflicts without writing. Normal migration runs
   the same preflight before its existing confirmation. `--yes` bypasses only
   confirmation, never validation. Fail with a clear nonzero report rather
   than an uncaught decoding/config/marker error.
2. Replace recognized legacy managed blocks as complete spans. Use the old
   heading fallback only for unmarked sections. Validate malformed, duplicate,
   and nested marker structures before writes. Preserve user-owned prose
   outside recognized spans. The reproduced failure puts the old protocol
   heading inside a PROJECTFORGE block followed by user prose: migration must
   retain balanced markers and the prose, including after a later re-init.
3. Every writing attempt gets a unique fresh backup under the already ignored
   `.project-steward/migration-backup-projectforge/` directory. Preserve the raw
   legacy tree and original touched instruction files (including AGENTS.md
   and .gitignore where applicable); never overwrite older backups. Verify
   preservation and writes before deleting `.projectforge/`. An interrupted
   attempt and retry must not lose newly added legacy tasks. Reject conflicts
   while retaining both trees instead of choosing a winner or merging tasks.
4. Reuse an existing destination only if it matches intended migrated content;
   otherwise preflight fails. Preserve valid retry behavior for generated
   machine metadata and the migration progress entry. Unknown legacy files
   and the legacy journal must be preserved in the backup.
5. Refuse init whenever `.projectforge/` remains, even if `.project-steward/`
   already exists. Successful migration must precede initialization so real
   PLAN/HANDOFF content and policies such as `never` cannot be masked by new
   placeholders or the `auto` default.
6. A partial command update during re-init replaces only explicitly supplied
   Build/Test/Lint entries. Retain unspecified commands and custom block lines.
7. Cover malformed markers, user prose, invalid UTF-8/no-write preflight,
   interrupted migration/retry with new data, destination conflicts, dry-run
   immutability, init-before-migrate policy preservation, and partial commands
   with observable regression tests. Existing migration/alias behavior remains.
8. Record this plan, milestone progress, focused and full-suite evidence, and
   migration behavior in project documentation; commit the reviewed task.

## Task 2: Respect Git paths, repository boundaries, and worktrees

Primary scope: gitutil.py, paths.py, Git/root tests, relevant documentation,
and project records. Migration/init changes from Task 1 are already present.

1. Stage and commit lexical Git pathnames, preserving a final symlink as a
   symlink instead of resolving and committing its target. The reproduced
   fixture is `notes.md -> unrelated.txt`; the commit must contain notes.md
   and leave the target untouched. Cover `AGENTS.md -> shared-context.md` in
   the scoped wrap path too. Reject outside traversal and escaping parent
   paths while retaining literal pathspec safety, unrelated-index rejection,
   and useful error propagation.
2. Stop implicit project-root discovery at the nearest Git boundary after
   checking the current directory's managed/legacy markers. An independent
   nested Git repository must not use or modify the parent's project state.
   Preserve intentional explicit `--root` selection and discovery from a
   subdirectory inside a managed repository.
3. Resolve merge/rebase/cherry-pick operation metadata through Git's
   `rev-parse --git-path`, so ordinary repositories, linked worktrees, and
   submodule-style .git files are supported. Test an actual temporary linked
   worktree with a merge conflict; keep portable skip behavior when needed.
4. Run relevant regressions/full suite, update docs/project records, and commit.

## Task 3: Make build and publication previews safe

Primary scope: tools/build_plugin_payloads.py,
tools/publish_agent_artifact_pr.py, their tests, artifact-maintainer
documentation, and project records. Scripts remain standalone and stdlib-only.

1. Validate build output destinations before all mutations, including builds
   without `--clean`. Reject repository ancestors, Git metadata, source-tree
   overlaps, and unrecognized nonempty directories. Accept new/empty locations
   or existing generated outputs recognized by the expected Claude and Codex
   payload manifests matching artifact metadata. The current default generated
   dist layout must remain rebuildable.
2. Existing publication target checkouts must be clean before branch changes
   or copying. Validate target paths and reject unsafe/symlinked artifact
   destinations. Never remove an uncommitted local note or include an unrelated
   staged file in a release commit. Stage/commit only the artifact, with an
   explicit scope check, and keep clear failure reports.
3. `--dry-run` creates a temporary preview and reports the proposed diff. The
   target checkout's files, index, branch, and commits remain untouched.
   Ignored generated payloads in the source checkout may be regenerated.
   `--save-target-repo` during dry-run reports the proposed manifest update
   instead of writing it. Explain this behavior in CLI help and docs.
4. Tests use temporary repositories and mocked network/pull/push/PR commands.
   Test unsafe paths without actually deleting user/source directories, dirty
   target protection, scoped publication, preview immutability, and default
   payload build compatibility. Run full suite, update records, and commit.

## Task 4: Correct handoff hook bookkeeping and edit detection

Primary scope: sessions.py, hooks.py, CLI resume, runtime/hook tests,
session protocol and skill documentation, and project records.

1. Carry hook session IDs through claims, heartbeats, and automated closes.
   Repeated starts for the same ID are idempotent. Stale events from one hook
   session cannot update or close another session's current marker. Continue
   reading legacy runtime records with no IDs.
2. CLI resume reuses the current marker, including a hook-created marker.
   Explicit CLI wrap/close remain deliberate project-level handoff operations.
   Keep one lightweight current marker; do not build an independent registry
   or broader multi-session management feature.
3. A live marker by itself is advisory information, not abnormal-termination
   evidence. Add `runtime_notes` to recap JSON while preserving existing keys.
   Keep meaningful unfinished-handoff, Git-operation, and activity evidence
   for recovery reminders. Cover hook start followed by CLI resume, repeated
   start/compact, and A-start/B-start/A-end without corrupting B's record.
4. Recognize Codex `exec_command` and `shell_command` tools and both `cmd` and
   `command` payload fields. Preserve existing Claude/Grok tool support.
   Treat shell redirection or chaining conservatively as potentially modifying
   so a read-only prefix such as `cat > file` or `git status && edit` cannot
   hide edits. Preserve actual read-only command behavior and Stop cooldowns.
5. Run focused/full tests, update documentation and project records, and commit.

## Task 5: Validate configuration and release 0.4.1

Primary scope: state.py, doctor.py, codex_setup.py, backend config templates
and consumers, config/backend/Codex tests, authoritative versions, changelog,
release docs, and project records.

1. Centralize Project Steward configuration normalization and validation for
   both doctor and runtime. Validate section shapes, known field types, enums,
   and numeric bounds, distinguishing booleans from integers. Invalid fields
   get safe defaults and useful diagnostics; preserve valid unrelated fields
   and the legacy `ask` fallback. Malformed session config must not silently
   disable the Stop guard while doctor reports OK.
2. Reuse the mapping produced by native Codex TOML parsing for semantic checks
   (inline hooks and features.hooks). Remove redundant hand-written semantic
   line scans. TOML-looking text inside multiline strings is not configuration;
   an escaped quoted key that parses as `hooks` must be recognized. Preserve
   existing bytes/settings, and keep the conservative older-Python fallback
   for supported simple syntax; unsupported config stays untouched with a
   diagnostic. Do not add runtime dependencies.
3. Keep backend.json as the sole task-backend identity. Stop generating the
   duplicate config `[backend].name` field; preserve existing config file bytes.
   For compatibility, effective config JSON may retain the field but derives
   its value from the active backend. Test adoption of Beads and consistent
   status/backend/config identities without exporting tasks into Markdown.
4. Bump every authoritative package/plugin version from 0.4.0 to 0.4.1. Update
   CHANGELOG and relevant instructions for the final behavior of all tasks.
5. Run regressions/full suite and self doctor. Controller coordinates final
   payload/wheel/plugin validation and whole-branch review, with any resulting
   implementation corrections also performed by gpt-5.6-sol at max effort.
   Finish PLAN/PROGRESS/HANDOFF/VERIFY with real evidence and commit; no remote
   publication. Do not claim unexecuted native OS/Python tests passed.
