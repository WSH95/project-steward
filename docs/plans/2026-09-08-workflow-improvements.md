# Project Steward 0.4.0 workflow improvements

Approved by the user on 2026-09-08. Python 3.7+, standard-library-only
runtime, Windows/macOS/Linux support, and legacy Projectforge compatibility
remain requirements. No publishing or pushing is authorized.

## Deliverables

1. Move stewardship instructions into `.project-steward/WORKFLOW.md`.
   AGENTS.md keeps project context, commands, and a required-reading pointer.
   Preserve user prose, existing state, and compatibility on reviewed re-init.
2. New projects default to agent-chosen local milestone commits, including
   verified code and supporting project records. Add init --commit-policy
   auto|ask|never; preserve existing policies and the legacy ask fallback.
   Hooks never commit. Harden wrap --commit against unrelated staged work
   and return Git failures.
3. External backends own task truth. PLAN.md retains milestones and a focused
   dated overview with active/blocked/next/recent tasks and IDs. Init and
   session skills populate and refresh document bodies. Unavailable backends
   retain a clearly qualified last verified overview. Recap adds task_backend
   and suppresses misleading Markdown counts in external-backend text.
4. Init configures Codex for every project, with --no-codex-hooks opt-out.
   Create config with [features] hooks = true only when absent; preserve
   existing config. Merge hook JSON idempotently, retaining custom handlers.
   Unsupported inline hooks and malformed files skip Codex setup with an
   explanation while unrelated initialization proceeds. Use one packaged
   hook source for init and payloads. Doctor distinguishes installation from
   trust/activation; trust stays in Codex /hooks.
5. Release as 0.4.0; synchronize package/plugin metadata and changelog.

## Validation

Test fresh/repeated init, upgrades, legacy migration, policies, Git index
scope/failures, external-backend documents/recaps, and Codex merge/opt-out/
malformed/packaged cases. Run pytest, compileall, doctor, payload tests,
packaged-install smoke and platform-compatible checks. Review skill scenarios
for task completion, blocking, unavailable backend, and handoff.

## Implementation ownership

- Controller: scaffolding/templates, backend adoption, recap/doctor/CLI
  integration, Git safety, release and state records.
- Codex setup task: codex_setup module, packaged hook resource, payload
  builder/CI source references, dedicated tests; no scaffold or CLI edits.
- Instruction task: skills, shared references, fallback prompts and commands,
  README/install guide; no Python production code or root AGENTS.md edits.

New code interfaces: codex_setup.plan_files(root, enabled=True) returns
(scaffold_entries, warnings); inspect_setup(root) returns doctor-compatible
status/name/detail dictionaries. CLI displays mapping['_warnings'].
