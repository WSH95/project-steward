# Progress log

Newest first. One short entry per semantic checkpoint — not per edit.

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

