# Migrating from Projectforge (v0.1)

Inspect the migration before changing the project:

```text
project-steward migrate --dry-run
```

The dry run validates the legacy UTF-8 files, config values, managed-marker
structure, and every destination. It prints the planned writes, copies,
conflicts, and the `AGENTS.md` diff without writing anything. A normal
`project-steward migrate` runs the same preflight and shows the same
instruction diff before asking for confirmation. `--yes` skips that prompt;
it does not skip validation.

Each migration attempt then:

1. Creates a new
   `.project-steward/migration-backup-projectforge/attempt-*/` directory and
   makes that attempt self-ignoring before copying user data. Older attempts,
   including backups created by earlier releases, remain byte-for-byte
   unchanged.
2. Copies the raw `.projectforge/` tree into the attempt, preserving unknown
   files, binary bytes, symlinks, and the legacy journal. Original
   `AGENTS.md` and `.gitignore` files are stored beside it when migration will
   update them.
3. Writes converted PROJECT/PLAN/PROGRESS/HANDOFF/DECISIONS files under
   `.project-steward/`; converts the shell-style config to `config.toml`;
   creates `state.json` and `backend.json`; and copies the journal to
   `runtime/journal-legacy/`.
4. Replaces recognized legacy managed blocks as complete spans, converts
   other legacy markers, and uses the old Projectforge protocol heading only
   as a fallback for an unmarked section. Text outside those regions stays in
   place. The root `.gitignore` update removes only known legacy rules and
   refreshes the managed runtime block.
5. Verifies the backup, destination writes, and current legacy manifest before
   removing `.projectforge/`.

If any read, validation, backup, or write fails, the command exits nonzero and
keeps `.projectforge/`. A retry may reuse exact transformed documents and a
narrowly recognized migration-generated timestamp in machine metadata or the
single migration progress entry. Any other existing destination is a conflict;
the command retains both trees for review instead of merging task content.

Run migration before `project-steward init`. Init refuses to proceed while a
legacy tree remains, including when `.project-steward/` already exists, so the
legacy PLAN, HANDOFF, and commit policy are not hidden by placeholders or new
defaults. On a later re-init, supplying only one or two Build/Test/Lint options
updates those entries and keeps the unspecified commands and custom lines in
the managed commands block.

The deprecated `projectforge` console command remains as a warning wrapper
that delegates to `project-steward`. Claude Code users should also update the
plugin: the marketplace/plugin name is now `project-steward`, and
`/projectforge:*` commands become `/project-steward:*`.
