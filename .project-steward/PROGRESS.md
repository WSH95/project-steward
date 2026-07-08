# Progress log

Newest first. One short entry per semantic checkpoint — not per edit.

### 2026-07-08T11:53:02Z — cli
Published Project Steward Claude launcher payload to agent-plugins PR #2 from source commit 7bf67c3.

### 2026-07-08T11:41:44Z — cli
Implemented Claude plugin bundled launcher optimization; verified tests, doctor, payload build, and plugin validation.

### 2026-07-08T03:57:15Z — codex
[auto-checkpoint] agent-plugins PR #1 is open for Project Steward 0.3.0; local steward publication commit ed214cc is pending push.

### 2026-07-08T03:55:43Z — codex
Published generated Project Steward 0.3.0 plugin payload to
`WSH95/agent-plugins` by PR:
https://github.com/WSH95/agent-plugins/pull/1. Publisher rebuilt
`dist/project-steward`, copied it to `/tmp/agent-plugins/project-steward`,
committed target branch `publish/project-steward-plugin-0.3.0` at
`eb2daf4`, pushed it, and created OPEN PR #1 against `main`.
Pre-publish verification: 59 tests, `python3` compileall, generated
Codex plugin validator, self doctor 35 checks / 0 failures, and payload
diff against `/tmp/agent-plugins/project-steward` showed expected
manifest, version, doctor, and Codex hook changes.

### 2026-07-08T03:40:31Z — codex
Prepared 0.3.0 commit for the Codex hook schema fix: bumped
`pyproject.toml`, `plugin-src/metadata.json`, and
`project_steward.__version__` to `0.3.0`; payload rebuild completed with
no tracked generated-file drift.

### 2026-07-08T03:35:17Z — codex
Fixed Codex `hooks.json` parse failure from strict root schema: removed
the top-level `description` from canonical
`plugin-src/codex/hooks/hooks.json`, updated live
`/home/wsh/.codex/hooks.json`, and added test/self-doctor coverage that
rejects extra Codex hook root keys. TDD red run failed on the bad
`description`; after the fix, 59 tests, `python3` compileall, self
doctor 35 checks / 0 failures, payload build, and `codex --version`
passed without the hook parse warning.

### 2026-07-08T03:14:19Z — codex
Closed distribution-repo follow-up: `WSH95/agent-plugins` now has root
Claude Code/Codex marketplace manifests and an agent-neutral README,
pushed through commit `fe6ae8d`. Created public MIT repo
`WSH95/agent-skills` with README template only, pushed through commit
`da79b47`; no skills uploaded. Verified both distribution checkouts clean
and synced. `gh repo view` confirmed `agent-skills` visibility PUBLIC,
license MIT, default branch `main`; `project-steward` itself remains
PRIVATE as of this check.

### 2026-07-08T01:56:43Z — codex
Created public GitHub repo `WSH95/agent-plugins` with MIT license and
README via `gh`; published generated Project Steward plugin payload under
`project-steward/` and pushed commit `c78ea23` to that repo. Updated this
repo's `agent-artifacts.json` target repo to
`git@github.com:WSH95/agent-plugins.git`. Source verification: 57 tests,
`python3` compileall, self doctor 34 checks / 0 failures, payload build,
skill quick_validate, generated Codex plugin validator, publish dry-run
to `/tmp/agent-plugins`, and `git diff --check`.

### 2026-07-08T01:23:46Z — codex
Added `agent-artifact-maintainer` skill plan implementation in progress:
new skill scaffold/content, layout reference, `agent-artifacts.json`, and
project-local `tools/publish_agent_artifact_pr.py`. TDD red/green
focused tests now pass; full verification passing locally.

### 2026-07-08T00:50:19Z — codex
Claude payload cleanup: removed the confusing generated
`hooks/codex.hooks.json` copy from the Claude Code plugin output; Codex
hook config now remains only in the Codex extraction tree. ADR 0015
recorded. TDD: focused payload-builder test failed red, then passed
after the builder change. Verification: 51 tests, `python3` compileall,
self doctor 34 checks / 0 failures, payload build, generated Codex
plugin validator, and `git diff --check`.

### 2026-07-08T00:12:43Z — codex
User requested recent-commit summary and push. Pre-commit verification
passed for the development-layout refactor: 51 tests, `python3`
compileall, self doctor 34 checks / 0 failures, payload build, generated
Codex plugin validator, and `git diff --check`.

### 2026-07-08T00:04:22Z — codex
User approved AGENTS.md edit; updated only the `PROJECT-STEWARD`
managed commands block to use `plugin-src/src`, `python3`, and the new
payload builder command. ADR 0014 recorded. Verification: self doctor
34 checks / 0 failures, focused managed-block+doctor tests 8 passed, and
`git diff --check` passed.

### 2026-07-07T23:35:27Z — codex
Development layout refactor implemented: canonical plugin source moved to
`plugin-src/`; `tools/build_plugin_payloads.py` generates clean Claude
and Codex extraction trees under `dist/project-steward`; Codex gets
skills-first plugin output plus optional prompts/manual hooks; ADR 0013
recorded. Verification: 51 tests, generated Codex plugin validator,
source doctor, `python3` compileall, non-editable packaged install +
init smoke, isolated Codex marketplace/plugin add + prompt-input smoke,
and diff whitespace check passed.

### 2026-07-07T22:32:41Z — codex
Codex plugin fix implemented: root marketplace now uses the full Codex
entry shape and points to a skills-only `plugins/project-steward/`
payload; Claude `plugin/` keeps hooks; Codex docs now use
`codex plugin add` + `features.hooks`; ADR 0012 recorded; 3 Codex
questions resolved; 51 tests + plugin validator + isolated Codex smoke
green.

### 2026-07-05T13:41:29Z — cli
0.2.3 released: templates ship inside the package (silent stub-scaffold bug from field report fixed, TemplateError hard-fail, CI packaged-install job, recap count scoped); PyPI install docs corrected (ADR 0010); pushed @ 60be5c6, CI 14/14 green, plugin+pipx redistributed from GitHub

### 2026-07-05T13:36:42Z — cli
[auto-checkpoint] 0.2.3 released: commit 60be5c6 pushed, CI 14/14 green incl. new packaged-install job; plugin updated + pipx reinstalled from GitHub; acceptance verified in 3 clean installs; HANDOFF body refreshed

### 2026-07-05T13:31:52Z — cli
0.2.3: templates moved into the package (pip installs shipped none — silent stub scaffolds, field report); TemplateError hard-fail; doctor templates self-check; CI non-editable install job; recap open-task count scoped to named milestone (ADR 0011)

### 2026-07-05T13:08:57Z — cli
pipx-from-PyPI failure diagnosed (package never published, name unclaimed); ADR 0010: defer PyPI, docs rewritten to checkout/git installs (README x2, codex/INSTALL.md, cross-platform.md); CLI installed via pipx from git+ssh (0.2.2, doctor green); hooks/ crutch removed; 43 tests green

### 2026-07-04T18:49:14Z — cli
Distribution session: 0.2.1 init-gate fix (ADR 0007), 0.2.2 payload isolation in plugin/ (ADR 0008), published to GitHub, marketplace switched to git SSH source, 0.2.2 installed+verified from GitHub, first fully green CI (ADR 0009 dropped retired macOS/3.7 runner)

### 2026-07-04T18:40:54Z — cli
GitHub distribution live: c20f0ea pushed, CI run 28715861017 fully green (13 jobs, 3 OS, 3.7-3.13), 0.2.2 installed from git SSH source and cache-verified; memory notes updated. Steward files re-dirtied by this checkpoint — fold into next commit

### 2026-07-04T18:36:18Z — cli
Published to GitHub (d27ad32 pushed, user-approved); marketplace re-registered from git@github.com SSH source; 0.2.2 installed from GitHub, cache verified payload-only at d27ad32. CI: 13/13 runnable jobs green incl. both 3.7 floors; macOS/3.7 dropped (macos-13 runner retired, ADR 0009); 3 wedged runs cancelled

### 2026-07-04T18:18:09Z — cli
0.2.2: plugin payload isolated under plugin/ (ADR 0008) — installs no longer ship .project-steward//tests/.github; marketplace sources ./plugin; dev harness re-pointed; 43 tests + doctor + validate green

### 2026-07-04T17:42:27Z — cli
0.2.1: init approval gate made mechanical (dry-run draft pasted in visible reply before approval; ADR 0007) after field report of sight-unseen approval; +2 regression tests (43 green with PYTHONPATH; test_cli_version_runs env-dependent pre-existing)

### 2026-07-04T16:55:02Z — cli
Machine-local fix: re-pointed Claude Code marketplace from stale ~/Downloads copy to this repo, reinstalled plugin (cache now at 4290a62); answered plugin-update + real-world-usage questions; no repo changes

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
