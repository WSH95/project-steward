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
   only, no Bash-only core behavior (see references/cross-platform.md).
5. Checkpoint PROGRESS.md/HANDOFF.md at semantic boundaries; propose
   Conventional Commits; never push without approval.

<!-- PROJECT-STEWARD:BEGIN commands -->
## Commands

| Task | Command |
| --- | --- |
| Build | `python -m pip install -e .` |
| Test | `python -m pytest` |
| Lint | `python -m compileall -q src` |
<!-- PROJECT-STEWARD:END commands -->

<!-- PROJECT-STEWARD:BEGIN task-backend -->
## Task backend

Fine-grained tasks live in `.project-steward/PLAN.md` (built-in Markdown backend).
<!-- PROJECT-STEWARD:END task-backend -->

<!-- PROJECT-STEWARD:BEGIN agent-session-protocol -->
## Agent session protocol (Project Steward)

Durable project state lives in `.project-steward/` and travels via git.
Native session histories are execution details, never the source of truth.

**Session start** — before other work:
1. Read `.project-steward/HANDOFF.md`; run `project-steward resume` if the
   CLI is installed (it also detects crashed/unclosed sessions from git
   evidence and local runtime markers).
2. Give the user a short recap: last session, git state, active task,
   next step, blockers, open questions, and any abnormal-termination signs.

**During work** — at semantic boundaries (task done, plan changed, decision
made, validation run, risky step ahead), update `PLAN.md` / `PROGRESS.md` /
`DECISIONS.md` / `QUESTIONS.md` / `RISKS.md`, or run
`project-steward checkpoint --note "..."`. Propose a git commit at
meaningful checkpoints (Conventional Commits; include `.project-steward/`).
Never push without explicit approval.

**Session end** — when the user pauses, wraps up, switches tools, or leaves:
rewrite `HANDOFF.md` for a zero-context successor (state, in-flight work
cross-checked against `git status`, numbered next steps, blockers,
dead ends, warnings), append a `PROGRESS.md` entry, set
`session_status: closed`, and propose a commit. The
`project-steward wrap --summary "..."` command finalizes bookkeeping.

**Guardrails** — `AGENTS.md` and `CLAUDE.md` are high-risk files: edit only
inside `PROJECT-STEWARD` managed blocks, always show a diff and get explicit
approval first, and record the change in `DECISIONS.md`. Do not use these
files as progress logs. Keep volatile state in `.project-steward/`.
<!-- PROJECT-STEWARD:END agent-session-protocol -->
