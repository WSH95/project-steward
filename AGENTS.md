# Project Steward

Cross-agent project stewardship toolkit: durable repo-resident project memory, handoff/resume, and progress tracking for Claude Code, Codex, and other coding agents.

Primary language/stack: Python 3.7+ (stdlib only).

## Source of truth

- Project charter: `.project-steward/PROJECT.md`
- Milestones and tasks: `.project-steward/PLAN.md` (see the Task backend
  block below if an external backend owns tasks)
- Current state and next steps: `.project-steward/HANDOFF.md`
- History: `.project-steward/PROGRESS.md`; decisions: `DECISIONS.md`;
  open questions: `QUESTIONS.md`; risks: `RISKS.md`;
  validation: `VERIFY.md`

## Conventions

- Keep this file concise (< 300 lines). It is instructions, not a log.
- Volatile state belongs under `.project-steward/`, never here.

## Git policy

- Commit at semantic boundaries using Conventional Commits; include
  `.project-steward/` in the same commit.
- Never push, force-push, or rewrite published history without explicit
  user approval.

## Maintaining Project Steward (for future agents)

1. Read `.project-steward/HANDOFF.md`, then run `project-steward resume`.
2. Run `project-steward doctor --self` before and after changes; keep
   `python -m pytest` green (update tests when templates, hooks, the CLI
   surface, or the state schema change).
3. Preserve migration compatibility: `.projectforge/` detection, marker
   conversion, and the deprecated `projectforge` alias.
4. Keep Ubuntu/Windows/macOS support and the Python 3.7 floor — stdlib
   only, no Bash-only core behavior (see plugin-src/references/cross-platform.md).
5. Checkpoint PROGRESS.md/HANDOFF.md at semantic boundaries; propose
   Conventional Commits; never push without approval.

<!-- PROJECT-STEWARD:BEGIN commands -->
## Commands

- Build: `python -m pip install -e .`
- Test: `python3 -m pytest -q`
- Lint: `python3 -m compileall -q plugin-src/src tools`
- Payloads: `python3 tools/build_plugin_payloads.py --clean --out dist/project-steward`
<!-- PROJECT-STEWARD:END commands -->

<!-- PROJECT-STEWARD:BEGIN task-backend -->
## Task backend

Use `.project-steward/PLAN.md` for detailed tasks (built-in Markdown backend).
<!-- PROJECT-STEWARD:END task-backend -->

<!-- PROJECT-STEWARD:BEGIN agent-session-protocol -->
## Project Steward workflow

- Start by reading `.project-steward/HANDOFF.md`. Run `project-steward resume`
  when available, then recap the current task, next step, blockers, open
  questions, git state, and any crash signals.
- At meaningful checkpoints, write plain, factual updates to the relevant
  files in `.project-steward/` or run `project-steward checkpoint --note "..."`.
- Before pausing or switching agents, leave `HANDOFF.md` ready for someone
  without this chat. Run `project-steward wrap --summary "..."` when available.
- Propose Conventional Commits that include `.project-steward/`. Never push,
  force-push, or rewrite published history without explicit approval.
- Treat `AGENTS.md` and `CLAUDE.md` as user-owned files. Change only
  `PROJECT-STEWARD` managed blocks, show the diff first, and record the
  approved change in `.project-steward/DECISIONS.md`.
<!-- PROJECT-STEWARD:END agent-session-protocol -->
