# Changelog

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
