# Plan

Milestones and tasks. Built-in Markdown backend owns tasks.

## M4: 0.4.1 reliability fixes

- [x] Preserve Projectforge migration data across preflight, backup, failure,
      and retry; refuse init until migration completes; preserve partial
      command settings during re-init.
- [x] Respect Git paths, repository boundaries, and worktrees, including
      scoped commits from a managed root below the Git top level.
- [ ] Make build and publication previews safe.
- [ ] Correct handoff hook bookkeeping and edit detection.
- [ ] Validate configuration and release 0.4.1.

## M3: 0.4.0 workflow improvements

- [x] Move generated stewardship instructions into WORKFLOW.md with a
      concise required-reading pointer in AGENTS.md; preserve legacy projects.
- [x] Default new projects to agent-selected milestone commits; retain
      explicit policies and protect unrelated staged work in wrap --commit.
- [x] Keep external task backends authoritative and maintain useful,
      dated PLAN/HANDOFF overviews through the session skills.
- [x] Configure project-local Codex hooks during init with an opt-out,
      custom-hook preservation, one packaged source, and activation diagnostics.
- [x] Bump package and plugin versions to 0.4.0; update docs and changelog.
- [x] Resolve release-review edge cases and finish package validation.

## M1: v0.2 hardening

- [x] Python core (CLI, hooks dispatcher, tests) replacing bash hooks
- [x] Runtime/durable state split (resume never dirties git)
- [x] Backend broker (detect/score/recommend/adopt) + skill
- [x] Migration from .projectforge/ + deprecated `projectforge` alias
- [x] Codex hooks config + plugin manifests (verified against 2026-07 docs)
- [x] Self-hosting state + doctor --self
- [x] Init approval gate shows the dry-run draft in the visible reply
      (0.2.1, ADR 0007 — from field report)
- [x] Plugin payload isolated in plugin/ — installs no longer ship
      .project-steward//tests/.github (0.2.2, ADR 0008 — from field report)
- [x] Run CI on a real GitHub repo (3-OS matrix incl. Python 3.7 jobs)
      — 13/13 runnable jobs green at d27ad32; macOS/3.7 dropped, runner
      retired (ADR 0009)
- [x] Ship templates inside the package + hard-error on missing; CI
      non-editable install job; recap task count scoped to the named
      milestone (0.2.3, ADR 0011 — from field report)
- [x] Replace duplicated Claude/Codex payload source trees with
      canonical `plugin-src/` + generated extraction payloads
      (ADR 0013)
- [x] Add agent artifact maintenance skill + project-local PR publish
      script for agent-skills/agent-plugins workflows
      (ADR 0016)
- [x] Make init-generated project docs concise and natural; add optional
      Humanizer guidance without a runtime dependency (0.3.3, ADR 0022)
- [x] Derive the handoff commit from Git and stop no-op checkpoint loops
      (0.3.4, ADR 0023)
- [ ] Verify backend install commands against upstream READMEs
- [ ] Field-test Stop-guard thresholds in daily use; tune defaults

## M2: post-0.2

- [x] Grok Build compatibility on the Claude payload (0.3.2, ADR 0021)
      — dual-contract hook stdin, additive Grok tool names, no third
      payload; `grok plugin install … --trust` uses the existing Claude
      marketplace
- [ ] Codex plugin-bundled hooks path once stabilized upstream
- [ ] `sessions/*.md` per-session logs (optional verbosity tier)
- [ ] GitHub Issues adapter beyond detection (create/close via gh)
- [ ] Windows-native Codex hook support when upstream re-enables it

- [x] Preserve unspecified existing commands during partial re-init command updates
      (completed in the 0.4.1 reliability work, Task 1).
