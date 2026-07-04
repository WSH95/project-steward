# Open questions

Questions an agent could not answer from the repository and must not
guess. Check off with the answer inline once resolved.

- [ ] Do the pinned backend install commands (backlog.md, task-master-ai,
  spec-kit uvx) still match upstream READMEs? Verify before recommending
  installs to users.
- [ ] Codex plugin-bundled hooks: stable enough to prefer over manual
  `.codex/hooks.json`? Re-check https://developers.openai.com/codex/hooks
  and /codex/plugins/build.
- [ ] Should `auto_handoff_min_edits` default higher (5 -> 8) for
  code-heavy sessions? Needs field data.
- [ ] Codex `PostToolUse` hook `matcher: "*"`: confirm the matcher syntax
  (wildcard vs regex vs omit-for-match-all) at the ADR-0004 quarterly
  re-verification of https://developers.openai.com/codex/hooks.
- [ ] Does Codex's plugin route support subdirectory plugin sources
  (`.agents/plugins/marketplace.json` source.path "./plugin", set by ADR
  0008)? https://developers.openai.com/codex/plugins doesn't say
  (checked 2026-07-04). Manual skills-copy fallback is unaffected either
  way; verify on a Codex install before recommending the plugin route.
