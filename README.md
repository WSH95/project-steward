# Project Steward

**Cross-agent project stewardship for Claude Code, Codex, and other coding
agents.** The repository owns project continuity: durable, human-readable
state lives in `.project-steward/` and travels via git, so any agent on
any device can initialize, track, hand off, and resume work — even after
a crash. Agents are execution surfaces; native session histories are
never the source of truth.

Formerly **Projectforge** (v0.1). See
[references/migration-from-projectforge.md](references/migration-from-projectforge.md).

## What problem this solves

Multi-session agent work fails in predictable ways: the next session
starts cold, a switch from Claude Code to Codex (or laptop to
workstation) loses everything, a crashed terminal leaves no handoff, docs
drift from reality, and task lists fragment across tools. Project Steward
fixes all five with one skill set + one small Python CLI + optional
lifecycle hooks.

## Layout

```
skills/            5 portable Agent Skills (identical files work in
                   Claude Code and Codex): project-init, session-resume,
                   session-handoff, progress-tracking, backend-broker
src/project_steward/   Python 3.7+ stdlib-only core: CLI + hook dispatcher
hooks/             hooks.json (Claude Code, auto-loaded by the plugin)
                   codex.hooks.json (copy to <repo>/.codex/hooks.json)
commands/          /project-steward:init|resume|wrap|checkpoint|audit|backend
codex/             INSTALL.md + self-contained steward-* prompts
templates/         AGENTS.md, CLAUDE.md adapter, and 11 state templates
references/        session-protocol, security-model, backend-selection,
                   cross-platform, self-hosting, migration docs
.claude-plugin/ .codex-plugin/ .agents/plugins/   plugin packaging
tests/  .github/workflows/ci.yml   33 unit tests; Ubuntu/Windows/macOS CI
```

Inside a managed project it creates `AGENTS.md` (canonical), `CLAUDE.md`
(thin `@AGENTS.md` adapter — Claude Code does not read AGENTS.md
natively), and `.project-steward/` with `PROJECT.md`, `PLAN.md`,
`PROGRESS.md`, `HANDOFF.md`, `DECISIONS.md`, `QUESTIONS.md`, `RISKS.md`,
`VERIFY.md`, `config.toml`, `state.json`, `backend.json`, plus a
gitignored `runtime/` for device-local session claims and forensics.

## Install

**CLI (all platforms; required for hooks):**

```
pipx install project-steward        # or: pip install .   (from a checkout)
```

**Claude Code (plugin: skills + commands + hooks in one step):**

```
/plugin marketplace add /path/to/project-steward
/plugin install project-steward@project-steward-marketplace
```

**Codex:** see [codex/INSTALL.md](codex/INSTALL.md) — skills go to
`~/.agents/skills/` (or install as a plugin), hooks are experimental
(`[features] codex_hooks = true`, currently disabled on Windows), and a
hook-free fallback protocol is included.

**Generic agents:** any tool that reads `AGENTS.md` gets the session
protocol from its managed block; any tool that runs shell commands can
use the CLI directly.

## Quickstart flow

```
project-steward init          # or /project-steward:init for the full interview
project-steward resume        # session start: recap + crash detection
project-steward checkpoint --note "..."      # semantic boundaries
project-steward wrap --summary "..."         # session end (+ --commit)
project-steward doctor        # health checks
project-steward backend recommend            # task-backend broker
project-steward migrate       # upgrade legacy .projectforge/
```

`survey`, `status`, `close`, and `hook` (internal dispatcher) complete
the surface; `--json` and `--dry-run` are available where they matter.

## The three guarantees

1. **Interactive init** — read-only survey (never executes project
   scripts), load-bearing-questions-only interview (empty directories get
   a discovery interview instead), then AGENTS.md/CLAUDE.md/state
   generation behind an approval gate. Git init is offered, never forced.
2. **Real-time progress tracking** — event-table updates at semantic
   boundaries, commit nudges per `commit_policy`, and hard guardrails:
   AGENTS.md/CLAUDE.md are edited only inside `PROJECT-STEWARD` managed
   blocks, with diffs, explicit approval, and a DECISIONS.md audit trail.
3. **Crash-resilient cross-tool resume** — wrap writes a
   stranger-executable `HANDOFF.md`; resume recaps in ≤15 lines and
   detects abnormal termination from five independent signals (front
   matter, runtime claim, post-handoff activity, unexplained
   dirty/commits, in-progress git ops), then reconstructs from git
   evidence with every claim labeled *(inferred)*. Hooks add automatic
   recap injection, a wrap-language detector, and a Stop guard that
   forces one brief auto-checkpoint when the handoff goes stale
   (bounded worst-case loss: one cooldown window). **Resuming never
   dirties the git tree** — claims live in gitignored runtime files.

## Backend broker

You should not need to already know
[Backlog.md](https://github.com/MrLesk/Backlog.md),
[beads](https://github.com/steveyegge/beads),
[CCPM](https://github.com/automazeio/ccpm),
[Taskmaster](https://github.com/eyaltoledano/claude-task-master),
[Spec Kit](https://github.com/github/spec-kit), or the
[gh CLI](https://cli.github.com). `backend recommend` detects what is
installed/in use, scores candidates from project signals, and explains in
plain English; `backend adopt <name>` is approval-gated and rewrites only
the AGENTS.md task-backend block. One system owns fine-grained tasks at a
time — PLAN.md degrades to milestones + a pointer. Installs are assisted,
never silent. Linear/Jira are honest stubs. Details:
[references/backend-selection.md](references/backend-selection.md).

## Cross-platform

Ubuntu, Windows, and macOS are first-class: the core is Python 3.7+
standard library only (pathlib/subprocess/json; `tomllib` on 3.11+ with a
bundled flat-TOML fallback below), hooks invoke the `project-steward`
console script (no bash, no `${VAR}` shell expansion), writes are atomic
and UTF-8/`\n`-normalized, and CI runs a 3-OS matrix including Python 3.7
jobs. Details and the deliberate 3.7-floor compromises:
[references/cross-platform.md](references/cross-platform.md).

## Security, git policy, hook trust

Safe-init never executes project scripts; `.env`-like files are flagged
but never read; doctor fails on secret patterns in committed steward
files; risky commands (installs, pushes, `curl | sh`, ...) always require
explicit approval. The CLI **never pushes**; commits happen only via
`wrap --commit` under a permitting `commit_policy`. Hooks always exit 0,
touch no network, and are ~250 auditable lines — review them before
trusting, like any hook. Details:
[references/security-model.md](references/security-model.md).

## Self-hosting

This repository manages itself: see the root `AGENTS.md`, `CLAUDE.md`,
and `.project-steward/` (real plan, handoff, decisions — including where
this design deviates from its external review and why). Future agents:
start with `.project-steward/HANDOFF.md` and `project-steward doctor
--self`. Details:
[references/self-hosting.md](references/self-hosting.md).

## Composition

Plays well with [Superpowers](https://github.com/obra/superpowers)
(project-init defers empty-project ideation to a `brainstorming` skill if
present), and with any backend above. Claude Code's `/init` or Codex's
built-in init output can seed the survey; Project Steward owns the final
interview, files, and git policy. The [AGENTS.md](https://agents.md)
standard is the canonical instruction carrier.

## Troubleshooting

- **Hooks do nothing** → `project-steward` not on PATH (`pipx install
  project-steward`), or on Codex the `codex_hooks` flag is off / you are
  on Windows (hooks disabled upstream — the AGENTS.md protocol still
  works). `project-steward doctor` reports this.
- **"Not a Project Steward project"** → run `init`, or `--root` points
  elsewhere.
- **Legacy `.projectforge/` warnings** → `project-steward migrate`.
- **Windows + Claude Code fallback command fails** → expected; the
  `${CLAUDE_PLUGIN_ROOT}` shim is POSIX-only. Install the CLI.
- **Stop guard too eager/quiet** → tune `[session]` in
  `.project-steward/config.toml` (`block`/`remind`/`off`, cooldown,
  min edits).

MIT license.
