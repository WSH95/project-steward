---
updated_at: 2026-07-04T18:49:14Z
updated_by: cli
session_status: closed
branch: main
last_commit: c20f0ea
---
# Handoff

## Now

v0.2.2, published and distributed. Three commits this session, all pushed
to github.com/WSH95/project-steward (private, main @ c20f0ea):
b683877 made the init approval gate mechanical — `init --dry-run`, paste
the full AGENTS.md draft in the visible reply, only then ask (ADR 0007,
regression-pinned by tests/test_skill_text.py); d27ad32 isolated the
installable payload under `plugin/` so installs stop shipping
`.project-steward/`/tests/.github (ADR 0008 — Claude Code has no ignore
mechanism, subdir source is the idiom); c20f0ea dropped the CI
macOS/3.7 job because GitHub retired the macos-13 runner (ADR 0009).
First fully green CI run: 28715861017 (13 jobs, 3 OS, Python 3.7–3.13,
including editable install of the plugin/ layout). On this machine the
plugin is installed at user scope from the git SSH source
(`git@github.com:WSH95/project-steward.git`), cache verified
payload-only at d27ad32. 43 tests green locally (via
`PYTHONPATH=plugin/src`; the package is NOT pip-installed here —
test_cli_version_runs fails under bare `python3 -m pytest`, expected).

## In flight

- (none — only this wrap's own steward-file updates are uncommitted;
  the wrap commit includes them)
- Untracked `hooks/` at repo root: a session-local delegate created
  because the running session's hooks predated the plugin/ move. NOT
  committed, must not be. Delete after Claude Code restarts:
  `rm -r hooks/`.

## Next steps

1. After restart: `rm -r hooks/` (the untracked crutch), then confirm
   the restarted session shows the steward recap (hooks now run from the
   GitHub-sourced 0.2.2 cache).
2. Field-test in a scratch repo: `/project-steward:init` end-to-end —
   the agent must paste the full dry-run AGENTS.md draft BEFORE asking
   approval (ADR 0007 regression); then kill the terminal mid-session
   and reopen — a crashed session must show "ABNORMAL TERMINATION
   SUSPECTED", a cleanly wrapped one must NOT.
3. Release flow from now on: bump version in
   `plugin/.claude-plugin/plugin.json` + `plugin/.codex-plugin/plugin.json`
   + `.claude-plugin/marketplace.json` + `pyproject.toml` +
   `plugin/src/project_steward/__init__.py`, commit, push (explicit user
   approval required), then
   `claude plugin update project-steward@project-steward-marketplace`
   (bare-name update does NOT resolve). `claude plugin tag` can create
   release tags.
4. Decide whether to make the GitHub repo public (installs then work
   without SSH auth: `/plugin marketplace add WSH95/project-steward`).
5. Resolve QUESTIONS.md items (backend installer commands; Codex
   plugin-bundled hooks maturity; Codex PostToolUse matcher syntax;
   auto_handoff_min_edits default; NEW — does Codex's plugin route
   support subdir sources per ADR 0008? verify before recommending it).

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
