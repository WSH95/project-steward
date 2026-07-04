---
updated_at: 2026-07-04T13:17:00Z
updated_by: claude (plugin-fix session)
session_status: active
branch: main
last_commit: 7396b66
---

# Handoff

## Now

v0.2.0 + two fix rounds. Round 1 (7396b66): duplicate manifest.hooks,
DST timestamp bug, test portability. Round 2 (this session, uncommitted
until the audit commit): portability audit fixed 11 findings — resume
false-crash signal, wrap-detector overreach, tomlmini escape parity
with tomllib, atomic-write fsync/Windows retry, migrate prose rewrite
(ADR 0006) + staging + escaping, non-string cwd, doctor PATH/URL
checks, secret placeholder downgrade, Windows install docs. 41 tests
green (TZ=UTC + America/New_York); doctor --self 0 failures
(2 intended warns: CLI not on PATH, placeholder repo URL).

## In flight

- User to run `/reload-plugins` once more (plugin.json description
  changed in the audit round) and confirm a clean-session recap no
  longer shows "ABNORMAL TERMINATION SUSPECTED".
- Replace github.com/USER/ placeholder URLs (plugin.json, pyproject)
  before pushing — doctor --self now warns until done.

## Next steps

1. `/reload-plugins` + `/doctor` verification (see In flight).
2. Push to a GitHub repo and confirm the CI matrix passes, especially the
   Python 3.7 jobs (ubuntu-22.04 / windows-latest / macos-13). Note: UTC
   runners cannot reproduce DST-class time bugs — this machine
   (US Eastern) can; keep testing time-sensitive paths locally too.
3. Field-test on a real project: `/project-steward:init`, work a session,
   kill the terminal mid-session, reopen, confirm crash detection +
   reconstruction reads correctly.
4. Resolve QUESTIONS.md items (backend installer commands; Codex
   plugin-bundled hooks maturity).

## Blockers

- (none)

## Key files

- `src/project_steward/hooks.py` — all lifecycle behavior (both agents).
- `src/project_steward/sessions.py` — recap/crash-detection/wrap core.
- `hooks/hooks.json`, `hooks/codex.hooks.json` — the only files exposed
  to agent-platform API drift.
- `references/session-protocol.md` — the contract everything implements.

## Tried and rejected

- Shell-expanded `${CLAUDE_PLUGIN_ROOT}` as the primary hook command
  (breaks on Windows cmd) — replaced by the console script with a POSIX
  `||` fallback.
- `dirs_exist_ok`/tomllib/walrus (3.8–3.11 features) — rejected for the
  3.7 floor.
- Review's `commandWindows` + extra Codex events — unverifiable against
  official docs; see DECISIONS.md 0004.

## Warnings

- Do not add non-stdlib runtime dependencies; pyproject declares none on
  purpose.
- Editing templates or hook JSON requires updating tests
  (test_scaffold_init, test_hooks_stop_guard) and doctor's self checks.
