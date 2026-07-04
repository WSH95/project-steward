# Plan

Milestones and tasks. Built-in Markdown backend owns tasks.

## M1: v0.2 hardening

- [x] Python core (CLI, hooks dispatcher, tests) replacing bash hooks
- [x] Runtime/durable state split (resume never dirties git)
- [x] Backend broker (detect/score/recommend/adopt) + skill
- [x] Migration from .projectforge/ + deprecated `projectforge` alias
- [x] Codex hooks config + plugin manifests (verified against 2026-07 docs)
- [x] Self-hosting state + doctor --self
- [ ] Run CI on a real GitHub repo (3-OS matrix incl. Python 3.7 jobs)
- [ ] Verify backend install commands against upstream READMEs
- [ ] Field-test Stop-guard thresholds in daily use; tune defaults

## M2: post-0.2

- [ ] Codex plugin-bundled hooks path once stabilized upstream
- [ ] `sessions/*.md` per-session logs (optional verbosity tier)
- [ ] GitHub Issues adapter beyond detection (create/close via gh)
- [ ] Windows-native Codex hook support when upstream re-enables it
