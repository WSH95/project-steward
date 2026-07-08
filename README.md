# Project Steward

**Cross-agent project stewardship for Claude Code, Codex, and other coding
agents.** The repository owns project continuity: durable, human-readable
state lives in `.project-steward/` and travels via git, so any agent on
any device can initialize, track, hand off, and resume work — even after
a crash. Agents are execution surfaces; native session histories are
never the source of truth.

Formerly **Projectforge** (v0.1). See
[plugin-src/references/migration-from-projectforge.md](plugin-src/references/migration-from-projectforge.md).

## What problem this solves

Multi-session agent work fails in predictable ways: the next session
starts cold, a switch from Claude Code to Codex (or laptop to
workstation) loses everything, a crashed terminal leaves no handoff, docs
drift from reality, and task lists fragment across tools. Project Steward
fixes all five with one skill set + one small Python CLI + optional
lifecycle hooks.

## Layout

```
plugin-src/        canonical source for plugin development
  skills/          6 portable Agent Skills (Claude Code + Codex)
  references/      session-protocol, security-model, backend-selection,
                   cross-platform, self-hosting, migration docs
  src/project_steward/   Python 3.7+ stdlib-only CLI + hook dispatcher
    templates/     AGENTS.md, CLAUDE.md adapter, and 11 state templates
  claude/          Claude Code commands + auto-loaded hook config
  codex/           optional Codex prompts + manual Codex hook config
  metadata.json    shared plugin/marketplace metadata
agent-artifacts.json       publish target metadata (target repo filled on first publish)
tools/
  build_plugin_payloads.py
  publish_agent_artifact_pr.py
dist/project-steward/     generated extraction output (gitignored)
  claude/          Claude marketplace + plugins/project-steward payload
  codex/           Codex marketplace + plugins/project-steward payload,
                   optional prompts, and manual hooks.json
codex/             INSTALL.md for Codex-specific usage
tests/  .github/workflows/ci.yml   unit tests; Ubuntu/Windows/macOS CI
.project-steward/  this repo's own state (self-hosting) — never ships
```

Inside a managed project it creates `AGENTS.md` (canonical), `CLAUDE.md`
(thin `@AGENTS.md` adapter — Claude Code does not read AGENTS.md
natively), and `.project-steward/` with `PROJECT.md`, `PLAN.md`,
`PROGRESS.md`, `HANDOFF.md`, `DECISIONS.md`, `QUESTIONS.md`, `RISKS.md`,
`VERIFY.md`, `config.toml`, `state.json`, `backend.json`, plus a
gitignored `runtime/` for device-local session claims and forensics.

## Install

**CLI (required for hooks on native Windows; recommended elsewhere — on
POSIX hosts the plugin's hooks fall back to a bundled python3 shim):**

```
# Not yet on PyPI — install from a checkout:
pipx install .                      # or: pip install .
# or, with repo access, straight from GitHub:
pipx install git+ssh://git@github.com/WSH95/project-steward.git
```

**Build extractable plugin payloads from this development repo:**

```
python3 tools/build_plugin_payloads.py --clean --out dist/project-steward
```

**Claude Code (generated plugin: skills + commands + hooks in one step):**

```
/plugin marketplace add /path/to/project-steward/dist/project-steward/claude
/plugin install project-steward@project-steward-marketplace
```

**Codex:** see [codex/INSTALL.md](codex/INSTALL.md) — skills go to
`~/.agents/skills/` or install from the generated Codex marketplace under
`dist/project-steward/codex` with
`codex plugin add project-steward@project-steward-marketplace`. Codex
hooks use `features.hooks` and remain a manual `hooks.json` install.

**Generic agents:** any tool that reads `AGENTS.md` gets the session
protocol from its managed block; any tool that runs shell commands can
use the CLI directly.

**Publish a review PR to an agent-plugins repo:**

```
python3 tools/publish_agent_artifact_pr.py \
  --artifact project-steward-plugin \
  --target-repo git@github.com:USER/agent-plugins.git \
  --dry-run
```

Remove `--dry-run` only after reviewing the copied output. The script
opens a PR and never merges it.

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
[plugin-src/references/backend-selection.md](plugin-src/references/backend-selection.md).

## Cross-platform

Ubuntu, Windows, and macOS are first-class: the core is Python 3.7+
standard library only (pathlib/subprocess/json; `tomllib` on 3.11+ with a
bundled flat-TOML fallback below that decodes strings identically), hooks
prefer the `project-steward` console script and fall back to a bundled
`python3` shim — the fallback's `${CLAUDE_PLUGIN_ROOT}` expansion is
POSIX-only, so **native Windows needs the CLI installed** (a fresh macOS
may also lack `python3` until the Xcode Command Line Tools are present).
Writes are atomic, fsynced, and UTF-8/`\n`-normalized, and CI runs a 3-OS
matrix including Python 3.7 jobs. Details and the deliberate 3.7-floor
compromises:
[plugin-src/references/cross-platform.md](plugin-src/references/cross-platform.md).

## Security, git policy, hook trust

Safe-init never executes project scripts; `.env`-like files are flagged
but never read; doctor fails on secret patterns in committed steward
files; risky commands (installs, pushes, `curl | sh`, ...) always require
explicit approval. The CLI **never pushes**; commits happen only via
`wrap --commit` under a permitting `commit_policy`. Hooks always exit 0,
touch no network, and are ~250 auditable lines — review them before
trusting, like any hook. Details:
[plugin-src/references/security-model.md](plugin-src/references/security-model.md).

## Self-hosting

This repository manages itself: see the root `AGENTS.md`, `CLAUDE.md`,
and `.project-steward/` (real plan, handoff, decisions — including where
this design deviates from its external review and why). Future agents:
start with `.project-steward/HANDOFF.md` and `project-steward doctor
--self`. Details:
[plugin-src/references/self-hosting.md](plugin-src/references/self-hosting.md).

## Composition

Plays well with [Superpowers](https://github.com/obra/superpowers)
(project-init defers empty-project ideation to a `brainstorming` skill if
present), and with any backend above. Claude Code's `/init` or Codex's
built-in init output can seed the survey; Project Steward owns the final
interview, files, and git policy. The [AGENTS.md](https://agents.md)
standard is the canonical instruction carrier.

## Troubleshooting

- **Hooks do nothing** → `project-steward` not on PATH (install from a
  checkout: `pipx install .` — not yet on PyPI), or on Codex hooks are
  disabled by `features.hooks = false`, not trusted in `/hooks`, or
  unavailable in that client. The AGENTS.md protocol still works.
  `project-steward doctor` reports CLI availability.
- **"Not a Project Steward project"** → run `init`, or `--root` points
  elsewhere.
- **Legacy `.projectforge/` warnings** → `project-steward migrate`.
- **Windows + Claude Code fallback command fails** → expected; the
  `${CLAUDE_PLUGIN_ROOT}` shim is POSIX-only. Install the CLI.
- **Stop guard too eager/quiet** → tune `[session]` in
  `.project-steward/config.toml` (`block`/`remind`/`off`, cooldown,
  min edits).

MIT license.
