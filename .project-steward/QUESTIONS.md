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
