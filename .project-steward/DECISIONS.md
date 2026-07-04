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
