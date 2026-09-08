# Project Steward

**Cross-agent project stewardship for Claude Code, Codex, Grok Build, and
other coding agents.** The repository owns project continuity: durable, human-readable
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
    templates/     instruction/state templates + canonical Codex hook JSON
  claude/          Claude Code commands + bin launcher + hook config
  codex/           optional Codex prompts
  metadata.json    shared plugin/marketplace metadata
agent-artifacts.json       publish target metadata for generated artifacts
tools/
  build_plugin_payloads.py
  publish_agent_artifact_pr.py
dist/project-steward/     generated extraction output (gitignored)
  claude/          Claude marketplace + plugins/project-steward payload
  codex/           Codex marketplace + plugins/project-steward payload,
                   optional prompts, and hooks.json for manual/global setups
codex/             INSTALL.md for Codex-specific usage
tests/  .github/workflows/ci.yml   unit tests; Ubuntu/Windows/macOS CI
.project-steward/  this repo's own state (self-hosting) — never ships
```

Inside a managed project it creates `AGENTS.md` (canonical), `CLAUDE.md`
(thin `@AGENTS.md` adapter — Claude Code does not read AGENTS.md
natively), and `.project-steward/` with `WORKFLOW.md`, `PROJECT.md`, `PLAN.md`,
`PROGRESS.md`, `HANDOFF.md`, `DECISIONS.md`, `QUESTIONS.md`, `RISKS.md`,
`VERIFY.md`, `config.toml`, `state.json`, `backend.json`, plus a
gitignored `runtime/` for device-local session claims and forensics.
AGENTS.md keeps project identity, commands, and an instruction to read WORKFLOW.md;
the detailed stewardship protocol lives there. Init also prepares `.codex/`
configuration and hooks unless `--no-codex-hooks` is selected.

## Install

**CLI (recommended for terminal use and required for Codex hooks; Claude
Code plugin hooks use a bundled pure-Python launcher when Python is
available, then fall back to this installed CLI):**

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

The builder validates the output before creating, replacing, or copying files.
It accepts a new or empty directory, or an existing Project Steward payload
whose Claude and Codex manifests identify the same artifact. This permits a
payload from an earlier release to be rebuilt. Repository ancestors, Git
metadata in the requested or resolved path, source overlaps, caller-controlled
output-path symlinks, and other nonempty directories are rejected. A non-final
system alias directly below the filesystem root remains supported.

**Claude Code (generated plugin: skills + commands + hooks in one step):**

```
/plugin marketplace add /path/to/project-steward/dist/project-steward/claude
/plugin install project-steward@project-steward-marketplace
```

**Codex:** see [codex/INSTALL.md](codex/INSTALL.md) — skills go to
`~/.agents/skills/` or install from the generated Codex marketplace under
`dist/project-steward/codex` with
`codex plugin add project-steward@project-steward-marketplace`. Codex
hooks use `features.hooks`; init prepares the project-local hook files.
Codex project trust and `/hooks` review are still required.

**Grok Build (reuses the generated Claude plugin; no third payload):**

```
grok plugin marketplace add /path/to/project-steward/dist/project-steward/claude
grok plugin install project-steward --trust
```

Or add the public marketplace and install from there:

```
grok plugin marketplace add https://github.com/WSH95/agent-plugins
grok plugin install project-steward --trust
```

`--trust` is required for lifecycle hooks. Skills and commands also load
from a Claude Code install via Grok's Claude compatibility, but those
hooks stay inert until Grok trusts the plugin. Grok's built-in `/resume`
opens the native session picker — use `/session-resume` or
`/project-steward:resume` for the Project Steward recap. Prefer
`project-steward resume --agent grok`.

**Generic agents:** any tool that reads `AGENTS.md` gets the session
protocol through its required-reading pointer to WORKFLOW.md; any tool that runs shell commands can
use the CLI directly.

### Writing style

Project Steward writes project records as plain, factual working notes. Its
init, progress, resume, and handoff skills share one small writing guide. If
the agent runtime also provides a `humanizer` skill, those workflows can use
it on the prose they are already changing. Humanizer is optional, existing
history is left alone, and the Python CLI has no runtime dependency on it.

**Publish a review PR to the agent-plugins repo:**

```
python3 tools/publish_agent_artifact_pr.py \
  --artifact project-steward-plugin \
  --dry-run
```

Remove `--dry-run` only after reviewing the copied output. The script requires
a clean target checkout and refuses ignored local files within the configured
artifact path before replacing it; ignored files elsewhere in the checkout do
not block publication. Dry-run builds the source payload, copies the target
checkout to a temporary preview, and prints the proposed Git diff. It does not
change the target's files, index, branch, or commits. With
`--save-target-repo`, dry-run reports the proposed manifest update without
writing it. A publication commit is scoped to the configured artifact path;
the script opens a PR and never merges it.

**Distribution repositories:**

- `https://github.com/WSH95/agent-plugins` — public MIT repository for
  generated plugin payloads. Project Steward is published there under
  `project-steward/`; the root marketplace metadata lets users add the
  repo directly as a Claude Code or Codex marketplace.
- `https://github.com/WSH95/agent-skills` — public MIT repository for
  future standalone skills. It currently contains only a README template
  and license; no Project Steward skills are published there yet.

## Quickstart flow

```
project-steward init          # full interview: /project-steward:init
# Optional: --commit-policy ask (or never), --no-codex-hooks
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
   boundaries, local milestone commits per `commit_policy`, and hard guardrails:
   AGENTS.md/CLAUDE.md are edited only inside `PROJECT-STEWARD` managed
   blocks, with diffs, explicit approval, and a DECISIONS.md audit trail.
3. **Crash-resilient cross-tool resume** — wrap writes a
   stranger-executable `HANDOFF.md`; resume recaps in ≤15 lines and
   detects abnormal termination from five independent signals (front
   matter, runtime claim, post-handoff activity, unexplained
   dirty/commits, in-progress git ops), then reconstructs from git
   evidence with every claim labeled *(inferred)*. Hooks add automatic
   recap injection, a wrap-language detector, and a Stop guard that
   requests one brief auto-checkpoint when the handoff goes stale and leaves
   tracked files alone when nothing material changed
   (bounded worst-case loss: one cooldown window). **Resuming never
   dirties the git tree** — claims live in gitignored runtime files.

Resume derives the handoff's Git anchor from the commit that last changed
`HANDOFF.md`. The file does not try to store the hash of the commit that
contains it.

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
the WORKFLOW.md task-backend block (AGENTS.md for legacy projects) and
backend.json. One system owns detailed tasks. PLAN.md retains milestone goals
and a dated overview of active, blocked, next, and recent work with task IDs;
HANDOFF.md retains full context and validation evidence. Update the backend
first, then these summaries. If access fails, preserve and qualify the last
verified overview. Installs are assisted,
never silent. Linear/Jira are honest stubs. Details:
[plugin-src/references/backend-selection.md](plugin-src/references/backend-selection.md).

## Cross-platform

Ubuntu, Windows, and macOS are first-class: the core is Python 3.7+
standard library only (pathlib/subprocess/json; `tomllib` on 3.11+ with a
bundled flat-TOML fallback below that decodes strings identically). Claude
Code plugin hooks run one polyglot `hooks/run-hook.cmd` wrapper (a valid
shell script and cmd.exe batch file at once — Claude Code hooks have no
per-OS command field) that prefers the bundled pure-Python
`bin/project-steward` launcher, then falls back to an installed
`project-steward` console script; Codex hooks still use the
console script because Codex does not install the Claude payload. Writes
are atomic, fsynced, and UTF-8/`\n`-normalized, and CI runs a 3-OS matrix
including Python 3.7 jobs. Details and the deliberate 3.7-floor
compromises:
[plugin-src/references/cross-platform.md](plugin-src/references/cross-platform.md).

## Security, git policy, hook trust

Safe-init never executes project scripts; `.env`-like files are flagged
but never read; doctor fails on secret patterns in committed steward
files; risky commands (installs, pushes, `curl | sh`, ...) always require
explicit approval. The CLI **never pushes**; commits happen only via
`wrap --commit` under a permitting `commit_policy`; agents use ordinary Git
commands for feature commits. New projects default to `auto`: after relevant
checks pass, the agent commits coherent code, tests, task artifacts, and project
records together using reviewed paths/hunks. `ask` proposes before committing;
`never` skips commits and nudges. Existing policies remain unchanged, and missing
or invalid legacy policies fall back to `ask`. The wrap helper retains its
stewardship-file scope, rejects unrelated staged changes, and returns Git errors.
Hooks never commit. They always exit 0,
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

- **Hooks do nothing** → Claude Code needs Python available to run the
  bundled launcher, or the installed `project-steward` CLI as fallback.
  Codex hooks need `project-steward` on PATH, `features.hooks = true`,
  and trust in `/hooks`; some clients do not support hooks. Grok needs
  `grok plugin install project-steward --trust` (Claude-cache discovery
  loads skills only). The WORKFLOW.md protocol still works through AGENTS.md.
  `project-steward doctor` reports installation and CLI availability separately
  from activation. Existing disabled settings stay disabled; unsupported inline
  hooks or malformed files are preserved and reported during init.
- **"Not a Project Steward project"** → run `init` in the current Git
  repository, or pass an intentional `--root`. Implicit discovery stops at the
  nearest Git boundary, so a nested repository does not inherit parent state.
- **Legacy `.projectforge/` warnings** → `project-steward migrate`.
- **Windows hooks do nothing** → the `run-hook.cmd` wrapper needs the
  Python Launcher (`py -3`) or `python` on PATH, or the CLI installed
  from a checkout with `pipx install .` (not yet on PyPI); it exits
  silently when none exist.
- **Stop guard too eager/quiet** → tune `[session]` in
  `.project-steward/config.toml` (`block`/`remind`/`off`, cooldown,
  min edits).

MIT license.
