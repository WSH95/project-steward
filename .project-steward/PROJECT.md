# Project Steward — project charter

Cross-agent project stewardship toolkit: durable repo-resident project
memory, handoff/resume, and progress tracking for Claude Code, Codex, and
other coding agents.

- Created: 2026-07-04 (Project Steward 0.2.0; renamed from Projectforge v0.1)
- Primary language/stack: Python 3.7+ (standard library only)

## Goals

- The repository owns project continuity; agents are execution surfaces.
- One skill set + one CLI serve Claude Code and Codex identically.
- Resume must survive crashes, tool switches, and device switches.
- Ubuntu, Windows, and macOS are all first-class.

## Non-goals

- Replacing task backends (beads/CCPM/Backlog.md/...): the broker selects
  and delegates to them instead.
- Cloud sync or server components: git is the transport.
- Full Linear/Jira adapters (explicit stubs until demanded).

## Users / stakeholders

Developers and researchers running multi-session, multi-tool agent
workflows on their own repositories.

## Constraints

- Python 3.7 floor (EOL upstream, but lab machines/Jetsons still run it):
  tomllib fallback parser, no walrus, no dirs_exist_ok.
- Hooks must never fail loudly (always exit 0) and never dirty the git
  tree at session start.
- AGENTS.md/CLAUDE.md edits only inside managed blocks, diff + approval.
