# Progress log

Newest first. One short entry per semantic checkpoint — not per edit.

### 2026-07-04T13:45:00Z — claude (wrap)
Session wrapped: fix rounds 7396b66 + a06d206 committed; user set real
author + repo URLs (github.com/WSH95/project-steward) across
plugin.json / marketplace.json / pyproject.toml; plugin reloaded
cleanly. Next: push and watch the 3-OS CI matrix.

### 2026-07-04T13:17:00Z — claude (portability audit + fixes)
3-agent audit + line verification: 11 confirmed findings fixed — resume
false-crash signal (claim-before-detect), wrap-detector overreach
(bare "handoff" + harness-injected text), tomlmini/tomllib escape
divergence, atomic-write fsync + Windows replace retry, migrate prose
rewrite (ADR 0006) + commit staging + config escaping, non-string cwd
drop, doctor PATH/placeholder-URL checks, secret-scan placeholder
downgrade, Windows install docs. Declined with reasons: Codex event
set (ADR 0004), ±1s activity fuzz, plugin shipping own state dir.
41 tests green under TZ=UTC and America/New_York; doctor --self 0
failures (2 intended warns).

### 2026-07-04T12:41:00Z — claude (auto-checkpoint)
[auto-checkpoint] Fix session state saved: commit 7396b66 landed;
HANDOFF refreshed; awaiting user /reload-plugins verification.

### 2026-07-04T12:36:00Z — claude (fix session)
Plugin manifest: dropped duplicate hooks ref (hooks/hooks.json is
auto-loaded; manifest.hooks is for additional files only) — clears the
/doctor load error. Fixed DST bug in activity-timestamp parsing
(mktime − time.timezone → calendar.timegm) that silently disabled the
Stop-guard and crash detection on DST machines. Tests: "python" →
sys.executable; test_hooks_never_fail now chdirs to tmp_path (it was
hitting the real repo once timestamp counting worked). 33 tests green
under TZ=UTC and TZ=America/New_York; doctor --self clean.

### 2026-07-04T12:05:00Z — claude (build session)
v0.2.0 built: rename, Python core, runtime-state split, broker, migrate,
Codex hooks (doc-verified), self-hosting, 33 tests green, CI written.
Platform assumptions re-verified against developers.openai.com on
2026-07-04; deviations from the external review recorded in DECISIONS.md.

### 2026-07-04T11:58:00Z — project-steward init
Project initialized as a Project Steward managed project (dogfood).

