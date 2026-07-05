---
updated_at: 2026-07-05T13:41:29Z
updated_by: cli
session_status: closed
branch: main
last_commit: 60be5c6
---
# Handoff

## Now

v0.2.3, released and distributed (2026-07-05). Two commits this session,
pushed to main @ 60be5c6: 29f0038 stopped docs advertising the
nonexistent PyPI install (ADR 0010 — not published; name unclaimed);
60be5c6 fixed the field-reported packaging bug — templates now live
INSIDE the package (`plugin/src/project_steward/templates/`, declared
package data), missing templates raise TemplateError (CLI exits 2)
instead of silently scaffolding stubs, doctor gained a templates
self-check, CI gained a non-editable `pip install .` + init front-matter
regression job, and the recap's open-task count is scoped to the named
milestone's PLAN.md section (ADR 0011). CI run 28742494281: 14/14 jobs
green. Distribution on this machine: plugin updated 0.2.2→0.2.3
(restart Claude Code to apply to hooks), CLI pipx-installed 0.2.3 from
the git+ssh source (`pipx reinstall project-steward` after each release
— pipx does not auto-detect git updates). Acceptance verified in three
clean installs (local checkout venv, GitHub-source venv, pipx): init
writes real front matter, resume reports a real handoff. 46 tests green
via `PYTHONPATH=plugin/src python3 -m pytest`; `rm -r hooks/` crutch
cleanup done.

## In flight

- (none — only this checkpoint's steward-file updates are uncommitted)

## Next steps

1. Restart Claude Code so plugin 0.2.3 hooks take effect; confirm the
   steward recap still appears (and shows M1's scoped task count).
2. Field-test in a scratch repo: `/project-steward:init` end-to-end —
   the agent must paste the full dry-run AGENTS.md draft BEFORE asking
   approval (ADR 0007 regression); then kill the terminal mid-session
   and reopen — a crashed session must show "ABNORMAL TERMINATION
   SUSPECTED", a cleanly wrapped one must NOT.
3. Release flow: bump version in the five sites (plugin.json ×2,
   marketplace.json, pyproject.toml, __init__.py), commit, push (explicit
   user approval), then
   `claude plugin update project-steward@project-steward-marketplace`
   AND `pipx reinstall project-steward`. `claude plugin tag` can create
   release tags.
4. Decide whether to make the GitHub repo public (installs then work
   without SSH auth) — and with it, whether to publish to PyPI
   (ADR 0010 / QUESTIONS.md).
5. Resolve QUESTIONS.md items (backend installer commands; Codex
   plugin-bundled hooks maturity; Codex PostToolUse matcher syntax;
   auto_handoff_min_edits default; Codex subdir plugin sources per
   ADR 0008; PyPI publish timing).

## Blockers

- (none)

## Key files

- `plugin/src/project_steward/hooks.py` — all lifecycle behavior (both
  agents).
- `plugin/src/project_steward/sessions.py` — recap/crash-detection/wrap
  core.
- `plugin/hooks/hooks.json`, `plugin/hooks/codex.hooks.json` — the only
  files exposed to agent-platform API drift.
- `plugin/references/session-protocol.md` — the contract everything
  implements. (Payload moved to plugin/ in 0.2.2, ADR 0008.)
- `.claude-plugin/marketplace.json` — repo-root catalog; plugin source
  is `./plugin`. The dev repo is NOT the install source anymore; GitHub
  is.

## Tried and rejected

- Shell-expanded `${CLAUDE_PLUGIN_ROOT}` as the primary hook command
  (breaks on Windows cmd) — replaced by the console script with a POSIX
  `||` fallback.
- `dirs_exist_ok`/tomllib/walrus (3.8–3.11 features) — rejected for the
  3.7 floor.
- Review's `commandWindows` + extra Codex events — unverifiable against
  official docs; see DECISIONS.md 0004.
- An ignore/exclude file for plugin packaging — Claude Code has none
  (docs verified 2026-07-04); the subdir payload is the only supported
  exclusion mechanism (ADR 0008).
- Keeping macOS/3.7 in CI — impossible on hosted runners (macos-13
  retired, arm64 has no 3.7 builds); ADR 0009.

## Warnings

- Do not add non-stdlib runtime dependencies; pyproject declares none on
  purpose.
- Editing templates or hook JSON requires updating tests
  (test_scaffold_init, test_hooks_stop_guard) and doctor's self checks;
  editing skill/command prose may trip tests/test_skill_text.py — that
  is intentional (ADR 0007), update the test only with the gate intact.
- Directory-source plugin installs copy the raw working tree (untracked
  junk included) — the GitHub channel ships tracked files only; never
  re-register the marketplace from a local path for real use.
- `~/Downloads/project-steward` may still exist; it is stale — advised
  deleted, never trust it.
- Watch ubuntu-22.04's retirement: when it goes, the 3.7 floor loses its
  last Linux runner and the floor itself should be re-debated (ADR 0009).
