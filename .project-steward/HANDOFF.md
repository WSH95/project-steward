---
updated_at: 2026-07-04T12:05:00Z
updated_by: claude (build session)
session_status: closed
branch:
last_commit:
---

# Handoff

## Now

v0.2.0 is feature-complete in this working tree: renamed to Project
Steward, Python 3.7+ stdlib core (CLI + hook dispatcher), runtime/durable
state split, backend broker, migration from Projectforge, Codex
hooks/plugin support per verified docs, self-hosting state, 33 passing
tests, 3-OS CI workflow written (not yet executed on GitHub).

## In flight

- (none — tree is consistent; not yet a git repository)

## Next steps

1. `git init && git add -A && git commit -m "feat: Project Steward v0.2.0"`.
2. Push to a GitHub repo and confirm the CI matrix passes, especially the
   Python 3.7 jobs (ubuntu-22.04 / windows-latest / macos-13).
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
