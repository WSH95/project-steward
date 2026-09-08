---
updated_at: 2026-09-08T19:36:38Z
updated_by: claude
session_status: closed
branch: main
---
# Handoff

## Now

Project Steward 0.5.0 is committed as `cbf3514` and pushed to `origin/main`.
CI run 34269572496 passed all 12 jobs (Ubuntu 3.7/3.8/3.10/3.12/3.13,
Windows and macOS 3.10/3.12/3.13, plus `packaged-install`). The local suite
passes 284 tests and `doctor --self` reports 39 checks, 3 known setup
warnings, 0 failures.

The release closes a review of the shipped plugin (M6 in PLAN.md) and removes
Projectforge (ADR 0031). `git.commit_policy` is now `auto`.

## In flight

Nothing. The working tree is clean and matches `origin/main`.

## Next steps

1. Reinstall the Claude plugin from a freshly built payload if you want this
   machine to run 0.5.0 — the CLI on PATH is still the 0.3.4 plugin cache, so
   the Stop guard and recap you see locally are pre-fix. Development-time
   version skew is expected and synced manually.
2. Review the two publish-script tests changed in `cbf3514`
   (`tests/test_agent_artifact_maintainer.py`, `literal_magic_target` and
   `commits_only_the_artifact`). They asserted the target checkout is left on
   the publish branch; restoring the user's branch moves the commit to the
   branch while HEAD returns to `main`. That is a behaviour change, not just
   a test fix.
3. Optional: bump `actions/checkout@v4` and `actions/setup-python@v5` in
   `.github/workflows/ci.yml`. CI warns that Node.js 20 is deprecated. This is
   pre-existing and unrelated to 0.5.0.

## Blockers

None.

## Warnings

- `python3 -m pytest -q` does not work with the system interpreter: pytest is
  not installed anywhere on this machine. The suite was run with
  `/tmp/project-steward-venv/bin/python -m pytest -q`, which a reboot
  destroys. `AGENTS.md` now documents `pip install -e ".[dev]"` as Build.
- `migrate.py` held the only strict marker validator and the only
  symlink-ancestor containment walk. Both were ported to
  `managed_blocks.validate_blocks` and `paths.assert_inside_root` before the
  deletion. Do not reintroduce a second marker engine.
- Hooks must stay silent: unknown events are a no-op returning 0, and no hook
  may add stdout. Config diagnostics reach the agent through the SessionStart
  `additionalContext`, which is already JSON.

## Key files

- `plugin-src/src/project_steward/state.py`: atomic writes preserve mode and
  newline, and write through symlinks.
- `plugin-src/src/project_steward/managed_blocks.py`: the single marker
  engine, now validating.
- `plugin-src/claude/hooks/run-hook.cmd`: probe, then launch exactly once.
- `.project-steward/DECISIONS.md` ADR 0031; `PLAN.md` M6; `CHANGELOG.md` 0.5.0.

## Validation

284 tests; `compileall` clean; `doctor --self` 39/3/0; payload build at 0.5.0;
`init` in a fresh repo writes real state at mode 644; a symlinked
`.project-steward/` is refused with exit 1 and writes nothing outside the
repo; a CRLF HANDOFF.md survives a checkpoint; the hook wrapper emits exactly
one JSON document.
