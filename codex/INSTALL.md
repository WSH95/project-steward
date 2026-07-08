# Project Steward on Codex

Verified against the official Codex docs on 2026-07-07:
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

This plugin intentionally does not bundle lifecycle hooks yet. Use the
manual hooks.json route below until plugin-bundled hooks are field-tested.

## 4. Hooks (experimental — read this)

Codex lifecycle hooks are enabled by default in current Codex builds. If
your config or admin policy disables them, use the canonical feature key
in `~/.codex/config.toml`:

```toml
[features]
hooks = true
```

`codex_hooks` still exists only as a deprecated alias. Then copy the
generated `dist/project-steward/codex/hooks/hooks.json` to
`<your-repo>/.codex/hooks.json` (project scope) or merge it into
`~/.codex/hooks.json` (user scope). The canonical source is
`plugin-src/codex/hooks/hooks.json`. Events wired: `SessionStart`
(recap injection), `PostToolUse`
(event-based activity heartbeat), `UserPromptSubmit` (wrap-language
detector), `Stop` (stale-handoff guard).

Known limitations (from the official docs, as of 2026-07):

- Non-managed hooks must be reviewed and trusted in `/hooks` before they
  run.
- Heartbeat tracking is **event-based, not timer-based** — it advances
  when hooks fire, so long tool-free thinking stretches don't tick.
- `PostToolUse` matching covers the current supported tool names
  documented by Codex, but Project Steward hooks must not be treated as a
  security enforcement boundary.

## 5. Fallback protocol (no hooks — Windows, older Codex, or flag off)

Everything still works through three carriers:

1. The **Agent session protocol** managed block in your project's
   `AGENTS.md` (Codex reads AGENTS.md natively) — resume/checkpoint/wrap
   behavior rides along with the repo.
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
