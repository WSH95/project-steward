---
updated_at: 2026-07-04T13:45:00Z
updated_by: claude (plugin-fix session)
session_status: closed
branch: main
last_commit: a06d206
---

# Handoff

## Now

v0.2.0 plus two committed fix rounds: 7396b66 (duplicate manifest.hooks
ref, DST timestamp bug, test portability) and a06d206 (11-finding
portability audit: resume false-crash signal, wrap-detector overreach,
tomlmini escape parity with tomllib, atomic-write fsync/Windows retry,
migrate prose rewrite per ADR 0006 + staging + escaping, non-string
cwd, doctor PATH/URL checks, secret placeholder downgrade, Windows
install docs). The wrap commit adds the user's real author name and
repo URLs (github.com/WSH95/project-steward) in plugin.json,
marketplace.json, and pyproject.toml. Plugin installed from the local
marketplace, reloaded cleanly, dogfooding in Claude Code. 41 tests
green under TZ=UTC and TZ=America/New_York; doctor --self 0 failures
(1 expected warn: CLI not on PATH — shim fallback covers hooks).

## In flight

- (none — the wrap commit includes the manifest URL/author updates;
  tree is clean after it)

## Next steps

1. Push (needs explicit user approval; never push unprompted):
   `git remote add origin git@github.com:WSH95/project-steward.git &&
   git push -u origin main`. Expect the 3-OS CI matrix to run; the
   Python 3.7 jobs (ubuntu-22.04 / windows-latest / macos-13) are the
   ones to watch. Note: UTC runners cannot reproduce DST-class time
   bugs — a DST-zone machine (e.g. US Eastern) can; keep running
   time-sensitive tests locally too.
2. Field-test in a scratch repo: `/project-steward:init`, work, then
   kill the terminal mid-session and reopen — a genuinely crashed
   session must show "ABNORMAL TERMINATION SUSPECTED"; a cleanly
   wrapped one must NOT (regression for the a06d206 resume fix).
3. Resolve QUESTIONS.md items (backend installer commands; Codex
   plugin-bundled hooks maturity; Codex PostToolUse matcher syntax;
   auto_handoff_min_edits default).

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
