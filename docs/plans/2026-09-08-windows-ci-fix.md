# Windows CI correction and version 0.4.2

Approved in conversation on 2026-09-08. Baseline: df6a7cc.

## Global Constraints

- Implement with gpt-5.6-sol at max effort; one implementation worker and an
  independent review. The controller owns integration, push, and GitHub checks.
- Windows/macOS supported minimum is Python 3.10. Ubuntu retains Python 3.7.
  Core remains standard-library only with Python 3.7 syntax and packaging floor.
- Preserve migration byte-for-byte raw backups. No public API/schema changes,
  runtime blocking checks, or Windows Python 3.7 resolver changes.
- Root AGENTS.md and CLAUDE.md are unchanged. Preserve the original checkout's
  97 permission-only differences and all 108 saved file modes during delivery.
- Version is 0.4.2 in every authoritative package/plugin source and steward state.
- Local Conventional Commits, merging to main, and pushing to GitHub are already
  authorized. The worker must not merge, push, or create remote messages.
- Completion requires all 11 requested matrix jobs and packaged-install green
  on the pushed commit. Local Linux success is not cross-platform completion.

## Task 1: Correct Windows CI coverage and newline regression

1. Set the workflow base matrix to ubuntu-latest/windows-latest/macos-latest
   and Python 3.10, 3.12, 3.13. Include ubuntu-latest/Python 3.8 and
   ubuntu-22.04/Python 3.7, with no excludes or Windows 3.7/3.8 entries.
   Keep fail-fast false, triggers, all test steps, and packaged-install intact.
2. Parameterize test_backup_stays_ignored_after_original_instructions_are_copied
   in tests/test_migrate.py with explicit LF and CRLF .gitignore bytes written
   using write_bytes. First show the current LF-only assertion fails for CRLF;
   then compare the backup with the original bytes captured before migration.
   Retain the checks that the generated backup ignore file is exactly b"*\n",
   the simulated destination-write failure is reported, the legacy tree stays,
   and no backup files appear in git status. Do not normalize backup bytes or
   skip the regression on Windows. Existing migration implementation is correct.
3. Update README, the cross-platform reference, and the project charter with
   the supported OS minimums and exact tested combinations. Clarify that
   generated text uses LF while raw backups retain original bytes. Keep
   pyproject requires-python >=3.7 and shared fallback/parser code unchanged.
4. Bump pyproject.toml, plugin-src/metadata.json, the package __version__, and
   .project-steward/state.json to 0.4.2. Add a precise changelog entry describing
   the test correction and CI/support change, without claiming a runtime
   migration fix. Record the approved policy in DECISIONS.md and update
   PLAN/PROGRESS/HANDOFF/VERIFY at meaningful checkpoints. Leave external CI
   completion pending for the controller; retain older historical records.
5. Run doctor before/after, the two newline regressions, all migration tests,
   and one full local suite with an absolute source PYTHONPATH. Verify the
   expanded matrix has exactly 11 requested pairs. Build payloads and verify
   version metadata consistency. Inspect the diff and make one scoped commit.
   Report commands, actual red/green evidence, commit, and limitations in the
   private report. Do not spawn agents or repeat controller release checks.

## Controller validation and delivery

- Independently review the entire change against Task 1 and Global Constraints.
- Build the wheel and validate installed version/template availability and
  payload manifests; use a fresh temporary venv to avoid stale same-version
  installs. No global plugin installation or marketplace publication.
- Fast-forward reviewed commits into source main, preserving saved modes and
  root instructions. Push main without force and verify remote commit identity.
- Monitor GitHub until all 11 matrix jobs plus packaged-install pass; handle
  concrete remaining failures before completion. Record actual CI run evidence
  in durable project records and keep the user-visible TODO current.
