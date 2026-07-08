---
updated_at: 2026-07-08T03:14:19Z
updated_by: codex
session_status: closed
branch: main
last_commit: HEAD
---
# Handoff

## Now

Distribution follow-up is complete. `WSH95/agent-plugins` is public,
MIT-licensed, and synced at commit `fe6ae8d`; it contains the generated
Project Steward plugin under `project-steward/`, root Claude Code/Codex
marketplace metadata, and an agent-neutral README. `WSH95/agent-skills`
is public, MIT-licensed, and synced at commit `da79b47`; it intentionally
contains only `LICENSE` and a README template, with no skills uploaded.

This source repo remains the canonical Project Steward development repo.
`agent-artifacts.json` targets `git@github.com:WSH95/agent-plugins.git`
for the generated plugin payload. No `agent-skills` artifact entry exists
yet because the user explicitly asked not to upload skills for now.

## In flight

- Local source changes in this repo are Project Steward close-out
  bookkeeping and source README maintenance only.
- `gh repo view WSH95/project-steward` reported the source repo is still
  PRIVATE during this session. The user said they will open-source it at
  `https://github.com/WSH95/project-steward.git`, but that has not
  happened yet as of the check.
- The stale pre-session handoff pointed at `addfe39`; this handoff uses
  `last_commit: HEAD` so a successor does not get a false "commits after
  handoff" warning from the commit that contains the handoff itself.

## Next steps

1. If the user asks, push this source repo after verifying and committing
   the close-out bookkeeping.
2. When `project-steward` is made public, update install docs that still
   say "with repo access" or use SSH-only examples where public HTTPS is
   more appropriate.
3. When a standalone skill should be published, add a deliberate
   `agent-artifacts.json` skill entry targeting
   `git@github.com:WSH95/agent-skills.git` and publish by PR; do not
   upload skills ad hoc.
4. If the AGENTS.md guardrail is explicitly relaxed, update the remaining
   non-managed prose reference from
   `plugin/references/cross-platform.md` to
   `plugin-src/references/cross-platform.md`.

## Blockers

- None for the distribution repo work.
- Local `python` points to an interpreter too old for
  `from __future__ import annotations`; use `python3` here.

## Key files

- `plugin-src/` — canonical plugin source: shared skills/references,
  Python package/templates, Claude commands/hooks, Codex prompts/hooks,
  and shared metadata.
- `tools/build_plugin_payloads.py` — generates extractable Claude and
  Codex payloads from `plugin-src/`.
- `tools/publish_agent_artifact_pr.py` — project-local PR publishing
  script for generated agent artifacts.
- `agent-artifacts.json` — local publish manifest; currently only the
  generated Project Steward plugin artifact is configured.
- `tests/test_payload_builder.py` — pins extraction layout and Codex
  command-like companions.
- `tests/test_agent_artifact_maintainer.py` — pins the artifact
  maintainer skill contract and publish-script behavior.
- `.project-steward/DECISIONS.md` ADR 0018 — root distribution repo
  install entry-point decision.

## Tried and rejected

- Adding a skill artifact to `agent-artifacts.json` now — rejected
  because `agent-skills` must stay empty until the user asks to publish a
  specific standalone skill.
- Editing non-managed AGENTS.md prose — still avoided because the
  project guardrail limits AGENTS.md edits to managed blocks unless the
  user explicitly relaxes that guardrail.

## Warnings

- Do not manually edit generated `dist/project-steward/` output; rebuild
  from `plugin-src/`.
- Do not restore `plugin/` or `plugins/project-steward/` as source
  directories; generated payloads are deliberately built from
  `plugin-src/`.
- Codex prompt files are optional command-like companions only; Codex
  skills remain the supported plugin UX.
- Codex hooks remain a manual companion file unless/until
  plugin-bundled Codex hooks are field-tested separately.
- Do not push this source repo without explicit user approval.
