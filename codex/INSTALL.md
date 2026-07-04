# Project Steward on Codex

Verified against the official Codex docs on 2026-07-04:
skills — https://developers.openai.com/codex/skills ·
plugins — https://developers.openai.com/codex/plugins ·
hooks — https://developers.openai.com/codex/hooks

## 1. CLI (recommended everywhere)

```
pipx install project-steward     # or: pip install project-steward
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
cp -r skills/* ~/.agents/skills/
```

Check with `/skills` inside Codex; invoke explicitly (`$project-init`) or
let Codex trigger them implicitly from the descriptions.

## 3. Plugin route (bundles skills in one step)

This repo ships `.codex-plugin/plugin.json` plus
`.agents/plugins/marketplace.json`, so it can be added as a plugin
marketplace:

```
codex plugin marketplace add /path/to/project-steward   # or a git URL
codex plugin install project-steward
```

Plugin-bundled hooks exist in newer Codex builds, but users must review
and trust third-party hooks before they run — the manual hooks.json route
below is the most predictable today.

## 4. Hooks (experimental — read this)

Codex lifecycle hooks are **experimental** and must be enabled in
`~/.codex/config.toml`:

```toml
[features]
codex_hooks = true
```

Then copy `hooks/codex.hooks.json` to `<your-repo>/.codex/hooks.json`
(project scope) or merge it into `~/.codex/hooks.json` (user scope).
Events wired: `SessionStart` (recap injection), `PostToolUse`
(event-based activity heartbeat), `UserPromptSubmit` (wrap-language
detector), `Stop` (stale-handoff guard).

Known limitations (from the official docs, as of 2026-07):

- **Hooks are currently disabled on Windows.** Use the fallback protocol
  below there.
- Heartbeat tracking is **event-based, not timer-based** — it advances
  when hooks fire, so long tool-free thinking stretches don't tick.
- `PostToolUse` matching currently covers `Bash` tool calls; tool
  interception is incomplete and must not be treated as an enforcement
  boundary.

## 5. Fallback protocol (no hooks — Windows, older Codex, or flag off)

Everything still works through three carriers:

1. The **Agent session protocol** managed block in your project's
   `AGENTS.md` (Codex reads AGENTS.md natively) — resume/checkpoint/wrap
   behavior rides along with the repo.
2. The prompts in `codex/prompts/` (`steward-init`, `steward-resume`,
   `steward-wrap`, `steward-checkpoint`) — copy to `~/.codex/prompts/`
   and invoke as slash commands. Each is self-contained.
3. Manual CLI habits: `project-steward resume` when you sit down,
   `project-steward checkpoint --note ...` at boundaries,
   `project-steward wrap --summary ...` before you leave. Crash
   detection in `resume` works from git evidence alone, so even a
   forgotten wrap is recoverable.
