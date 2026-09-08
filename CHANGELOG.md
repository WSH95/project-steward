# Changelog

## 0.5.0 — 2026-09-08

- Remove the Projectforge migration path. The `migrate` subcommand, the
  deprecated `projectforge` console alias, `.projectforge/` detection, legacy
  `PROJECTFORGE` marker conversion, and the migration reference are gone.
  Projects created by Project Steward are unaffected; nothing else changes.
- Preserve file permissions when writing state. Atomic writes carried
  `mkstemp`'s owner-only mode onto the destination, so every checkpoint
  narrowed HANDOFF.md, PROGRESS.md, and init-written AGENTS.md/CLAUDE.md/
  .gitignore to 0600. Existing modes are now kept and new files are 0644.
- Refuse to destroy unreadable state. `append_progress` replaced PROGRESS.md
  with a fresh template on any read error, and `checkpoint`/`wrap` overwrote an
  unparseable `state.json` with defaults. Both now fail with a message and
  exit 1 instead of writing.
- Report health honestly. `doctor` reported "no secrets in committed steward
  files" when it could not read them, and raised an unhandled error on an
  unreadable AGENTS.md or HANDOFF.md. Unreadable files are now named in a
  warning.
- Tolerate trailing whitespace on managed markers, and refuse duplicated,
  nested, or unclosed blocks instead of appending a second copy. Managed blocks
  now follow the file's first line ending rather than switching to CRLF
  whenever any CRLF is present.

## 0.4.2 — 2026-09-08

- Parameterize the migration backup regression with explicit LF and CRLF
  `.gitignore` bytes and compare copied originals byte-for-byte. The generated
  backup ignore file remains LF. Runtime migration behavior is unchanged.
- Set the supported Windows and macOS minimum to Python 3.10. CI now requests
  Python 3.10, 3.12, and 3.13 on Ubuntu, Windows, and macOS, plus Python 3.8 on
  `ubuntu-latest` and Python 3.7 on `ubuntu-22.04`, for 11 matrix jobs. The
  package and shared core retain their Python 3.7 floor; supported use below
  Python 3.10 is on Ubuntu.

## 0.4.1 — 2026-09-08

- Make Projectforge migration preflight complete and retries lossless. Migration
  now preserves raw state and instruction originals, detects destination races,
  and removes legacy data only after verified writes.
- Keep Git operations inside the selected repository and managed root, including
  symlink entries, nested repositories, subdirectory projects, and linked
  worktrees.
- Validate payload destinations before cleanup and run publication previews in
  temporary clones, preserving target files, index state, branch, and commits.
- Keep the current runtime session owner-aware across repeated or overlapping
  hook events. Codex shell activity and mutating command chains now reach the
  Stop guard without treating a live marker alone as a crash.
- Normalize Project Steward configuration through one runtime/doctor path.
  Invalid sections, types, enums, and negative numeric values use safe defaults
  with diagnostics; valid unrelated settings and the legacy `ask` fallback are
  preserved. Booleans are not accepted as integers.
- Use parsed Codex TOML for inline-hook and `features.hooks` checks. Multiline
  string content is ignored as prose, escaped quoted keys are recognized, and
  existing configuration bytes remain unchanged. Older Python keeps the
  conservative supported subset without a new dependency.
- Make `backend.json` the sole authoritative task-backend identity. New config
  files no longer duplicate the backend name; effective status config derives
  it from `backend.json`, and backend adoption does not copy tasks into PLAN.md.

## 0.4.0 — 2026-09-08

- Move generated stewardship instructions into `.project-steward/WORKFLOW.md`.
  AGENTS.md retains project context, commands, and a required-reading pointer.
  Reviewed re-init preserves user prose and existing project records.
- Default new projects to agent-chosen milestone commits covering verified code
  and project records. Add `init --commit-policy auto|ask|never`; existing
  policies and the conservative legacy fallback remain unchanged. Hooks never
  commit. `wrap --commit` rejects unrelated staged changes and returns Git errors.
- Give external task backends a focused milestone/task overview and substantive
  init/handoff guidance. Recaps identify the task backend and avoid presenting
  Markdown checkbox counts as external task totals.
- Configure project-local Codex hooks during init, with `--no-codex-hooks` to
  opt out. Preserve existing configuration and custom hooks; report unsupported
  setup without overwriting it. Init and payloads share one packaged hook source.
  Codex project trust and `/hooks` review are still required.

## 0.3.4 — 2026-08-26

### Fixed
- `HANDOFF.md` no longer stores the SHA of the commit that is supposed to
  contain it. Resume derives the handoff commit from Git history, so a clean
  clone does not report its own checkpoint commit as unexplained work.
- The Stop guard handles each activity batch once. When project state has not
  changed, its prompt now tells the agent to leave tracked files alone instead
  of creating a bookkeeping-only checkpoint.

## 0.3.3 — 2026-08-26

### Changed
- `project-steward init` now produces a shorter `AGENTS.md` and uses clearer,
  more natural wording across the project-state templates.
- Skills that write project documentation now share a plain-language writing
  guide and can use an installed `humanizer` skill as an optional final pass.
  Existing history is not rewritten, and the CLI has no new dependency.

## 0.3.2 — 2026-08-16

### Added
- **Grok Build compatibility on the existing Claude payload** (no third
  plugin tree). The shared hook dispatcher accepts Grok's camelCase
  stdin (`toolName`, `toolInput`, `stopHookActive`) while still preferring
  Claude/Codex snake_case keys. Stop-guard activity now counts
  `search_replace` and `run_terminal_command` the same way as
  `Edit`/`Write`/`Bash`. Grok session-teardown Stops (`reason`
  `shutdown` / `channel_closed`) are ignored. When Grok injects
  `GROK_SESSION_ID` / `GROK_HOOK_EVENT`, a Claude-wrapper `--agent
  claude` claim is recorded as `grok`. Install:
  `grok plugin marketplace add` on the Claude marketplace directory,
  then `grok plugin install project-steward --trust`. Use
  `/session-resume` or `/project-steward:resume` — Grok's bare `/resume`
  is the native session picker.

### Unchanged
- Claude Code hooks.json, Codex hooks.json, marketplace shapes, Stop
  `decision: block` JSON, and remind-mode `systemMessage` output.

## 0.3.1 — 2026-07-08

### Fixed
- **0.3.0's Claude hook "Windows command variants" never worked**: the
  generated hooks carried a `commandWindows` field that does not exist
  in Claude Code's hook schema. Claude Code ignored it silently, and on
  Windows without Git Bash the POSIX command string hit a PowerShell
  parse error on every hook event. Codex currently documents
  `commandWindows`, so this rejection is Claude Code-specific. Every
  Claude hook now runs one polyglot `hooks/run-hook.cmd` wrapper — a
  valid POSIX shell script and cmd.exe batch file at once — that prefers
  the bundled launcher via `python3`/`python`/`py` (POSIX) or
  `py -3`/`python` (Windows), falls back to an installed
  `project-steward` CLI, and exits 0 silently when neither exists
  (ADR 0019). `doctor --self` now schema-checks the Claude hooks file,
  so unsupported hook fields fail CI, and the payload test suite
  executes the built wrapper on every CI OS.
- `python3 -m pytest -q` now passes on a bare checkout:
  `test_cli_version_runs` no longer requires the package to be installed
  in the test interpreter.

## 0.3.0 — 2026-07-08

### Changed
- Claude Code plugin hooks now run through a plugin-local pure-Python
  `bin/project-steward` launcher before falling back to an installed CLI,
  with explicit POSIX and Windows command variants. The old POSIX-only
  hook shim is no longer shipped in generated payloads.

## 0.2.3 — 2026-07-05

### Fixed
- **pip-installed CLIs silently scaffolded stub state files** (field
  report): templates lived at `plugin/templates/`, outside the package,
  so wheels shipped none; `init` then fell back — without any warning —
  to one-line stubs (`# HANDOFF.md`, no front matter) and `resume`
  reported "unknown by unknown". Templates now live inside the package
  (`project_steward/templates/`, declared as package data) and resolve
  `__file__`-relative in every layout; a missing template is now a hard
  `TemplateError` (CLI exits 2) instead of silent degradation
  (ADR 0011). New CI job installs NON-editably and asserts `init`
  output has real front matter — editable installs had masked the bug.
- Session-start recap counted unchecked `- [ ]` boxes from *all* PLAN.md
  sections into the first milestone's "open task(s)" figure; the count
  is now scoped to the named milestone's own section.

## 0.2.2 — 2026-07-04

### Changed
- **Plugin payload moved to `plugin/`** (marketplace sources now point at
  `./plugin`). Installing the plugin previously copied the entire repo —
  including this project's own `.project-steward/` state (with gitignored
  `runtime/` session forensics on directory-source installs), `tests/`,
  and `.github/` — because Claude Code has no ignore mechanism and always
  copies the whole plugin source directory (ADR 0008). Only
  `skills/ commands/ hooks/ src/ templates/ references/` + manifests ship
  now. No behavior change; hook shim and template lookup are
  relative-path safe. Dev-harness paths (pyproject, tests, doctor --self,
  CI, docs) updated accordingly.

## 0.2.1 — 2026-07-04

### Fixed
- Init approval gate could ask "Approve this AGENTS.md draft?" without
  the draft ever appearing on screen (field report). The project-init
  skill and `/project-steward:init` command now make the gate mechanical:
  run `project-steward init … --dry-run` (prints the file plan plus full
  AGENTS.md/CLAUDE.md/.gitignore diffs, writes nothing), paste the draft
  verbatim into the visible reply, and only then ask for approval —
  dialogs, hidden thinking, subagent transcripts, and collapsed tool
  output are not review surfaces (ADR 0007). This also guarantees the
  approved text is exactly what `--yes` writes. Regression test:
  `tests/test_skill_text.py`.

## 0.2.0 — 2026-07-04

Renamed **Projectforge → Project Steward** (product "Project Steward",
CLI `project-steward`, package `project_steward`, state dir
`.project-steward/`, managed-block prefix `PROJECT-STEWARD`). The
`projectforge` command remains as a deprecated warning alias, and
`project-steward migrate` upgrades legacy state (backup, file moves,
config→TOML conversion, marker/heading conversion, .gitignore refresh).

### Added
- Python 3.7+ standard-library core (`src/project_steward/`): CLI with
  `survey`, `init`, `status`, `resume`, `checkpoint`, `wrap`, `close`,
  `doctor [--self]`, `migrate`, `backend {detect,recommend,adopt,status}`,
  `hook`; `--json`/`--dry-run`/`--yes` conventions; atomic UTF-8 writes.
- Cross-agent hook dispatcher replacing the v0.1 bash scripts; Claude
  Code config (`hooks/hooks.json`, plugin-auto-loaded) and Codex config
  (`hooks/codex.hooks.json`) both call the same console script. New
  UserPromptSubmit wrap-language detector.
- Codex support per current official docs: Agent Skills locations
  (`.agents/skills/`, `~/.agents/skills/`), plugin packaging
  (`.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json`), and
  experimental hooks (SessionStart/PostToolUse/UserPromptSubmit/Stop;
  flag-gated; disabled on Windows upstream) with a documented hook-free
  fallback protocol.
- Backend broker (skill + CLI): detection, signal-based scoring,
  plain-English recommendations, approval-gated adoption, migration
  thresholds; adapters for Markdown/Backlog.md/beads/CCPM/Taskmaster/
  Spec Kit/GitHub Issues detection; Linear/Jira as explicit stubs.
- New state files: `QUESTIONS.md`, `RISKS.md`, `VERIFY.md`,
  `state.json`, `backend.json`, `config.toml` (flat-TOML fallback parser
  for Python < 3.11).
- Managed blocks (`PROJECT-STEWARD:BEGIN/END`) for idempotent, diffable
  edits to AGENTS.md/CLAUDE.md/.gitignore; user prose is never touched.
- `doctor` health checks (state, schemas, gitignore, handoff staleness,
  managed blocks, hook JSON, secret scan) and `doctor --self` for this
  repo; self-hosting state committed (dogfooding).
- Test suite (33 tests) and a 3-OS GitHub Actions matrix including
  Python 3.7 floor jobs; packaging via pyproject (`pipx install`).

### Changed
- **Resume no longer dirties the git tree**: active-session claims,
  heartbeats, and activity logs moved to gitignored
  `.project-steward/runtime/`; committed files change only at semantic
  checkpoints and wrap (fixes a v0.1 design flaw).
- Codex prompts renamed `pf-*` → `steward-*`; commands namespaced
  `/project-steward:*`; new `/project-steward:backend`.
- Stop guard, crash detection, and snapshots reimplemented in Python with
  identical semantics (block/remind/off modes, cooldown, loop guard).

### Removed
- Bash hook scripts (`hooks/scripts/*.sh`) — replaced by the dispatcher
  plus a POSIX zero-install shim (`project_steward_hook.py`).

## 0.1.0 — 2026-07-04

Initial release as **Projectforge**: 4 skills, 5 commands, bash lifecycle
hooks (Claude Code only), 8 templates, Codex prompts, README.
