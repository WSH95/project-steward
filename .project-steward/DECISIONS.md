# Decisions (ADR-lite, append-only)

## 0001 — 2026-07-04 — Rename Projectforge to Project Steward

**Context**: External review proposed the rename; the user prefers it.
**Decision**: Product "Project Steward", CLI `project-steward`, package
`project_steward`, state dir `.project-steward/`, block prefix
`PROJECT-STEWARD`. `projectforge` remains a deprecated warning alias;
`project-steward migrate` upgrades old state.
**Consequences**: One canonical name; migration path documented in
references/migration-from-projectforge.md.

## 0002 — 2026-07-04 — Python 3.7+ stdlib core replaces bash hooks

**Context**: v0.1 hooks were bash-only (broken on native Windows); review
demanded a Python core. User set the floor at 3.7 (not 3.11).
**Decision**: All hook/CLI logic in `src/project_steward/` (stdlib only);
`tomlmini` fallback replaces tomllib below 3.11; hooks call the installed
`project-steward` console script (POSIX zero-install shim as fallback).
**Consequences**: Ubuntu/Windows/macOS parity; no walrus/3.8+ APIs;
config.toml restricted to a flat subset on old Pythons.

## 0003 — 2026-07-04 — Resume must not dirty the git tree

**Context**: v0.1 wrote `session_status: active` into committed
HANDOFF.md at resume, creating dirty state before any work (review
finding, confirmed valid).
**Decision**: Active-session claims, heartbeats, and activity logs live
in gitignored `.project-steward/runtime/`; committed files change only at
checkpoints and wrap.
**Consequences**: Crash detection now combines front matter, runtime
markers, and git evidence; `resume` is read-only on committed files.

## 0004 — 2026-07-04 — Codex hooks adopted per verified docs, not review claims

**Context**: The review asserted Codex hook events including PostCompact,
SubagentStart/Stop, PermissionRequest and `commandWindows` support. The
official docs (fetched 2026-07-04) document SessionStart, PreToolUse,
PostToolUse, UserPromptSubmit, Stop — experimental, flag-gated, and
disabled on Windows; no `commandWindows` field is documented.
**Decision**: Ship codex.hooks.json with the five documented events; the
dispatcher ignores unknown events gracefully; Windows relies on the
AGENTS.md protocol. Re-verify quarterly.
**Consequences**: No dependence on undocumented behavior; INSTALL.md
states the limitations with links.

## 0005 — 2026-07-04 — Backend broker recommends; adapters stay thin

**Context**: Review requested full adapters for 8+ backends.
**Decision**: Implement detection + scoring + plain-English
recommendation + approval-gated adoption (AGENTS.md block, backend.json,
PLAN.md pointer rule); deep per-backend automation stays with the
backends themselves. Linear/Jira are honest stubs.
**Consequences**: Small, testable broker (~250 lines) that never
installs or switches silently.

## 0006 — 2026-07-04 — Migration never rewrites product names in user prose

**Context**: `migrate` ran a blanket Projectforge→Project Steward
replacement over every moved state file, contradicting the module's own
documented contract; the portability audit confirmed it corrupts
user-authored history (e.g. a DECISIONS entry comparing tools).
**Decision**: Migration converts managed-block markers and
`.projectforge/` path references only; product-name mentions in prose
are preserved (tests assert preservation).
**Consequences**: Migrated files may legitimately still say
"Projectforge" in prose; PROGRESS.md's migration entry explains the
rename.

## 0007 — 2026-07-04 — Approval gates must show the artifact in the visible transcript

**Context**: A field report: `/project-steward:init` asked "Approve this
AGENTS.md draft and the accompanying files?" without the draft ever
being shown. The skill said "show the complete draft", but nothing
forced it into the user-visible reply — an agent can compose the draft
in hidden thinking and jump straight to an AskUserQuestion dialog, and
the `--yes` apply path (Bash) renders no diff UI as a fallback.
**Decision**: Approval gates are mechanical, not exhortative: preview
with the CLI (`init --dry-run` prints the file plan + full diffs), paste
the artifact verbatim into the visible reply, and only then ask.
Thinking, subagent transcripts, question dialogs, and collapsed tool
output are not review surfaces. Applies to any future gate that writes
files the user must approve.
**Consequences**: The approved text is exactly what `--yes` writes
(kills draft/write divergence); `tests/test_skill_text.py` pins the
load-bearing phrases so edits cannot silently drop the gate.

## 0008 — 2026-07-04 — Plugin payload lives in plugin/; self-hosting state never ships

**Context**: Installing the plugin copied the whole repo into the user's
plugin cache — including `.project-steward/` (even gitignored `runtime/`
session forensics, since directory-source installs copy the raw working
tree), `tests/`, `.github/`, and the repo's own AGENTS.md. Claude Code
has no ignore/allowlist mechanism (docs verified 2026-07-04); the copy
unit is always the plugin source directory, and the supported idiom is a
subdirectory source.
**Decision**: The installable payload (`skills/ commands/ hooks/ src/
templates/ references/` + `.claude-plugin/plugin.json` +
`.codex-plugin/`) lives under `plugin/`; both marketplace catalogs stay
at repo root and point `source` at `./plugin`. Development artifacts and
self-hosting state stay at repo root and never ship. The payload moves
as one unit — the hook shim and `_templates_root()` resolve paths
relative to their own files, so intra-payload geometry is preserved.
**Consequences**: pyproject `packages.find.where`, tests, doctor --self,
CI, and docs reference `plugin/…` paths. AGENTS.md commands-block edit
approved by user (this session). Residual: local *directory-source*
installs still copy untracked junk inside `plugin/` (e.g. `__pycache__`);
git-based installs ship tracked files only. Also approved: bare-name
`claude plugin update` doesn't resolve — use
`project-steward@project-steward-marketplace`.

## 0009 — 2026-07-04 — CI drops macOS/3.7: the runner no longer exists

**Context**: First real CI runs (repo published to GitHub today) showed
every run wedged in "queued": 13/14 jobs pass in ~1 minute, but
`test (macos-13, 3.7)` waits forever — GitHub retired the macos-13
hosted runner (the last x64 macOS image), and arm64 images ship no
CPython 3.7 builds. Observed on three consecutive runs (two queued
4h40m+).
**Decision**: Remove the macOS/3.7 matrix entry. The 3.7 floor stays
CI-enforced on ubuntu-22.04 and windows-latest (both green, including
against the plugin/ layout at d27ad32); macOS coverage continues at
3.8–3.13. Revisit only if a self-hosted x64 mac appears.
**Consequences**: macOS+3.7 is best-effort (stdlib-only code, low risk).
Watch ubuntu-22.04's own retirement date — when it goes, the 3.7 floor
loses its last Linux runner and the floor itself should be re-debated.

## 0010 — 2026-07-05 — PyPI publishing deferred; docs must not advertise unpublished channels

**Context**: `pipx install project-steward` fails with "no matching
distribution" — the package has never been uploaded to PyPI (index
returns 404; the name is unclaimed as of 2026-07-05). Yet README (Install
+ Troubleshooting), codex/INSTALL.md, and
plugin/references/cross-platform.md all instructed users to run exactly
that command. Publishing now would also make the source public (sdist)
while the GitHub repo is still private, and the README's Homepage link
would 404 for outsiders — entangled with the open repo-visibility
question (HANDOFF next steps).
**Decision**: Do not publish to PyPI yet. All install docs describe only
channels that actually work today: `pipx install .` / `pip install .`
from a checkout, or `pipx install git+ssh://…` with repo access. General
rule: docs never advertise an install channel before it exists. Revisit
publishing together with the make-repo-public decision (tracked in
QUESTIONS.md).
**Consequences**: Four doc locations rewritten (CHANGELOG.md's historical
packaging note left untouched). On this machine the CLI is now installed
via `pipx install git+ssh://git@github.com/WSH95/project-steward.git`
(0.2.2); after future releases it needs `pipx reinstall project-steward`
— pipx does not auto-detect git updates. When PyPI publishing happens,
revert the doc wording and claim the name promptly.

## 0011 — 2026-07-05 — Templates live inside the package; missing templates fail loud

**Context**: Field report (paperforge): pip-installed CLIs scaffolded
one-line stub state files — HANDOFF.md literally `# HANDOFF.md` — and
`resume` showed "unknown by unknown". Templates lived at
`plugin/templates/`, outside `plugin/src/project_steward/`, with no
package-data declaration, so wheels shipped none; `_templates_root()`
walked up from `__file__` expecting the repo layout and found nothing
under site-packages; scaffold.py then silently substituted stubs in
three places. CI installed only editably (`pip install -e`), which keeps
the repo layout and masked all of it.
**Decision**: Templates move into the package
(`plugin/src/project_steward/templates/`, declared via
`[tool.setuptools.package-data]`) and resolve `__file__`-relative —
one path valid in repo checkout, plugin cache, and site-packages alike
(3.7-safe; no importlib.resources). A missing template raises
`TemplateError` (CLI exits 2); silent degradation of state files is
forbidden — it contradicts the project's own durability guarantees.
Doctor gains "self: templates ship inside the package"; CI gains a
non-editable-install job asserting `init` writes real front matter.
**Consequences**: The plugin payload still contains the templates (they
remain under `plugin/`); the walk-up lookup stays only as a fallback for
pre-0.2.3 layouts. Released as 0.2.3. General packaging rule going
forward: every install channel (editable, wheel, plugin cache) must be
exercised by CI or doctor before release.

## 0012 — 2026-07-07 — Codex plugin payload is skills-only; hooks stay manual

**Context**: Current Codex CLI (`0.142.5`) accepted the repo marketplace
source but listed zero available plugins with the old entry shape
(`source.path` only), and `codex plugin install` is not a valid command
(`codex plugin add` is). Current Codex docs also make `features.hooks`
the canonical hook feature key and state that plugins can load default
`hooks/hooks.json`; Project Steward's shared `plugin/` payload uses that
filename for Claude Code hooks.
**Decision**: Split the Codex install route from the Claude Code payload:
the root marketplace points at `plugins/project-steward/`, a Codex
skills-only plugin that carries skills, references, and templates but no
`hooks/hooks.json`. Claude Code continues to use `plugin/` and its
auto-loaded hooks. Codex hooks remain manual via
`plugin/hooks/codex.hooks.json` until plugin-bundled hooks are separately
field-tested.
**Consequences**: Codex plugin installs expose skills as
`project-steward:<skill>` without accidentally loading Claude hook
commands. Tests now pin marketplace shape, plugin payload sync, docs
command spelling, and hook-feature wording. ADR 0008 remains true for
Claude Code payload isolation but is superseded for the Codex marketplace
source path.

## 0013 — 2026-07-07 — Plugin development source is canonical; payloads are generated

**Context**: The repo had become a poor development workspace: Claude Code
and Codex install payloads duplicated the same skills, references, and
templates across `plugin/` and `plugins/project-steward/`. Tests enforced
copy-sync, but day-to-day edits still required maintaining generated-like
folders by hand. The user clarified this repo is a plugin development
project, not the final install repository; release payloads will be
collected later into a separate agent-plugins repository.
**Decision**: Move canonical authoring to `plugin-src/` and generate clean
Claude/Codex extraction folders with
`tools/build_plugin_payloads.py --clean --out dist/project-steward`.
Claude output includes skills, commands, hooks, references, and full
Python source for the POSIX hook shim. Codex output is skills-first
(`.codex-plugin` + skills/references/templates), with optional prompts and
manual hooks emitted alongside the plugin, not bundled into it.
**Consequences**: `plugin/`, root `.claude-plugin/`, root `.agents/plugins/`,
`codex/prompts/`, and `plugins/project-steward/` are no longer source
directories. `pyproject.toml`, tests, CI, and doctor point to
`plugin-src/`. ADR 0008 and ADR 0012 remain historical distribution
context but are superseded for development layout.

## 0014 — 2026-07-07 — AGENTS.md commands block tracks plugin-src layout

**Context**: ADR 0013 moved canonical source from `plugin/src` to
`plugin-src/src` and added generated payload extraction, but AGENTS.md's
managed commands block still referenced the old lint path. The user
explicitly approved editing AGENTS.md.
**Decision**: Update only the `PROJECT-STEWARD` managed commands block:
tests use `python3 -m pytest -q`, lint uses `python3 -m compileall -q
plugin-src/src tools`, and payload generation is listed as a first-class
command.
**Consequences**: Future agents have the right verification and payload
build commands without relying on stale `plugin/` paths. Non-managed
AGENTS.md prose remains untouched.

## 0015 — 2026-07-08 — Codex hook config stays out of the Claude payload

**Context**: The generated Claude Code plugin included
`hooks/codex.hooks.json` as a convenience copy of the Codex manual hook
config. Claude Code does not need it, Codex does not discover it from the
Claude plugin folder, and the extra file made the extracted payload
layout confusing.
**Decision**: Generate Codex hook config only under the Codex extraction
tree (`dist/project-steward/codex/hooks/hooks.json`). The Claude plugin
payload contains only Claude Code hooks.
**Consequences**: Extraction folders are platform-specific and easier to
reason about. Codex hooks remain a manual companion file unless/until
plugin-bundled Codex hooks are field-tested separately.
