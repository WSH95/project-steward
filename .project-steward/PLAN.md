# Plan

Milestones and tasks. Built-in Markdown backend owns tasks.

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
- [ ] Verify backend install commands against upstream READMEs
- [ ] Field-test Stop-guard thresholds in daily use; tune defaults

## M2: post-0.2

- [ ] Codex plugin-bundled hooks path once stabilized upstream
- [ ] `sessions/*.md` per-session logs (optional verbosity tier)
- [ ] GitHub Issues adapter beyond detection (create/close via gh)
- [ ] Windows-native Codex hook support when upstream re-enables it
