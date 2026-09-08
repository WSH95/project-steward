# Project Steward on Codex

Hook configuration rechecked on 2026-09-08; skills/plugin installation
references last checked on 2026-07-08:
skills — https://developers.openai.com/codex/skills ·
plugins — https://developers.openai.com/codex/plugins ·
hooks — https://developers.openai.com/codex/hooks

## 1. CLI (recommended everywhere)

```
# Not yet on PyPI — install from a checkout:
pipx install .                   # or: pip install .
# or, with repo access, straight from GitHub:
pipx install git+ssh://git@github.com/WSH95/project-steward.git
project-steward --version
```

The CLI powers hooks, deterministic init/wrap/resume bookkeeping, doctor,
and migration. Skills degrade gracefully without it, but hooks require it.

## 2. Skills

Codex reads Agent Skills (same `SKILL.md` format as Claude Code) from:

- `.agents/skills/` in the repo (project scope; walked up to the repo root)
- `~/.agents/skills/` (user scope) — some installer tooling still uses the
  legacy `~/.codex/skills/`, which also works
- `/etc/codex/skills` (admin scope)

Install by copying:

```
mkdir -p ~/.agents/skills
cp -r plugin-src/skills/* ~/.agents/skills/
```

Check with `/skills` inside Codex; invoke explicitly (`$project-init`) or
let Codex trigger them implicitly from the descriptions.

## 3. Plugin route (bundles skills in one step)

This development repo generates a Codex skills-only plugin plus a
marketplace file. Build the payload first:

```
python tools/build_plugin_payloads.py --clean --out dist/project-steward
```

Then add the generated Codex marketplace:

```
codex plugin marketplace add /path/to/project-steward/dist/project-steward/codex
codex plugin add project-steward@project-steward-marketplace
```

Installed skills appear with the `project-steward:` prefix, for example
`$project-steward:session-resume`.

The plugin exposes skills; `project-steward init` sets up project-local
hooks. Plugin installation alone does not configure or trust project hooks.

## 4. Automatic project hook setup

Project Steward 0.4.0 includes Codex setup in every `project-steward init`.
Preview it with `--dry-run`; the normal approval/apply step covers these files:

- `.codex/config.toml`: created when absent with `[features] hooks = true`.
  Existing configuration stays byte-for-byte unchanged.
- `.codex/hooks.json`: created or merged with existing hooks. Custom handlers
  and settings are preserved, and repeated init does not duplicate Steward hooks.

Use `--no-codex-hooks` to opt out. This preference is saved for later re-init;
existing hook files are retained. Unsupported inline hooks, malformed TOML or JSON,
and paths escaping the project are preserved and reported; unrelated project
initialization still proceeds. Fix the reported issue before retrying setup.

Python 3.11+ validates existing Codex TOML with the standard-library parser.
On Python 3.7-3.10, automatic merging accepts a narrow subset of simple scalar
settings and tables. Richer configuration is left untouched with a warning;
use Python 3.11+ for setup or merge the exported hooks manually. Fresh projects
can create the default configuration on every supported Python version.

The installed `project-steward` CLI must be on PATH. Review and trust the project
and the new hooks through Codex `/hooks`. Hooks are enabled by default in current
Codex builds; `features.hooks` is the canonical setting and `codex_hooks` is a
deprecated alias. Existing disabled settings and administrative restrictions
remain in force. File creation does not prove activation. See the
[official hook documentation](https://learn.chatgpt.com/docs/hooks).

Events wired: SessionStart (recap), PostToolUse (activity heartbeat),
UserPromptSubmit (wrap-language detector), and Stop (stale-handoff guard).
`project-steward doctor` reports installed definitions, known disabled settings,
CLI availability, and the remaining activation check. Hooks never commit.

For a manual or user-wide installation, the builder still exports
`dist/project-steward/codex/hooks/hooks.json`. Merge it into `~/.codex/hooks.json`
and use `--no-codex-hooks` for projects that should rely on that global setup.
Codex loads hooks from multiple sources, so avoid registering the same Steward
handlers both globally and locally. The one canonical source is now
`plugin-src/src/project_steward/templates/codex-hooks.json.template`; it ships
inside the Python package and also supplies the distribution payload.

Codex currently documents `commandWindows` for Windows-specific commands;
Steward uses its cross-platform CLI directly. Heartbeats advance when hook events
fire. Treat these lifecycle helpers as bookkeeping, not a security boundary.

## 5. Fallback protocol (no hooks — Windows, older Codex, or flag off)

Everything still works through three carriers:

1. The **Agent session protocol** managed block in your project's
   `AGENTS.md` requires reading `.project-steward/WORKFLOW.md` for
   resume/checkpoint/wrap and commit behavior. Older projects keep the inline
   protocol until reviewed re-init.
2. Deprecated custom prompts in
   `dist/project-steward/codex/prompts/` (`steward-init`,
   `steward-resume`, `steward-wrap`, `steward-checkpoint`,
   `steward-audit`, `steward-backend`) — copy to `~/.codex/prompts/`
   only as a fallback when skills or plugins are not available. Each is
   self-contained. Canonical sources live in `plugin-src/codex/prompts/`.
3. Manual CLI habits: `project-steward resume` when you sit down,
   `project-steward checkpoint --note ...` at boundaries,
   `project-steward wrap --summary ...` before you leave. Crash
   detection in `resume` works from git evidence alone, so even a
   forgotten wrap is recoverable.
