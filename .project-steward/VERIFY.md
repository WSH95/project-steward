# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `python3 -m pytest -q` (with pytest installed) | 261 passed |
| Grok plugin manifest | `grok plugin validate dist/project-steward/claude/plugins/project-steward` | valid (optional; skip if `grok` is not on PATH) |
| Syntax sweep | `python3 -m compileall -q plugin-src/src tools` | exits 0 |
| Self health | `PYTHONPATH=plugin-src/src python3 -m project_steward doctor --self` | 0 failures |
| Payload build | `python3 tools/build_plugin_payloads.py --clean --out dist/project-steward` | exits 0 |
| Skill schema | `python3 /home/wsh/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugin-src/skills/agent-artifact-maintainer` | exits 0 |
| Publish dry-run | `python3 tools/publish_agent_artifact_pr.py --artifact project-steward-plugin --dry-run --target-checkout <clean-local-checkout> --non-interactive` | prints a temporary preview diff; target files/index/branch/commits unchanged |
| JSON configs | `python3 -m json.tool plugin-src/claude/hooks/hooks.json && python3 -m json.tool plugin-src/src/project_steward/templates/codex-hooks.json.template` | valid |
| Claude manifests | `claude plugin validate dist/project-steward/claude/plugins/project-steward --strict && claude plugin validate dist/project-steward/claude --strict` | both pass (manifest-only: hooks.json schema is covered by `doctor --self`) |
| Claude hook wrapper | `printf '' \| sh dist/project-steward/claude/plugins/project-steward/hooks/run-hook.cmd --version` | prints the payload's own version (bundled launcher ran, not a fallback) |
| Codex plugin schema | `python3 /home/wsh/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py dist/project-steward/codex/plugins/project-steward` | exits 0 |
| Codex plugin smoke | isolated `CODEX_HOME=/tmp/project-steward-codex-impl.*` marketplace add/list/plugin add + `codex debug prompt-input` | plugin listed/installed; `project-steward:` skills visible; no `hooks/hooks.json` in prompt input |
| Packaged install | clean venv `pip install .`, then `init --yes` in a scratch repo | HANDOFF.md starts with `---` (CI job `packaged-install`) |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Task 4 review correction: 2026-09-08 — two end-to-end regressions failed
against `7c3ace0`: newline normalization hid `git status\ntouch changed.txt`,
and the 200-character display limit hid a later `&& touch changed.txt`. New
versioned activity records carry classification computed from the full original
detail; legacy three-field records are classified when read. The direct set
passes 3 tests in 0.32s and all 51 session/hook tests pass in 4.07s. Self doctor
reports 40 checks, 3 existing warnings, and 0 failures; diff checks pass. The
controller will run the actual-source full suite after scoped rereview and
delivery, so the equivalent full suite was not repeated in this correction.

Task 4 verification: 2026-09-08 (ADR 0028) — the initial lifecycle batch
failed all 3 tests before implementation, covering hook start followed by CLI
resume, repeated same-ID start/compact, and A-start/B-start/A-end. The next
focused batch reproduced 6 failures for stale heartbeat ownership, Codex
`cmd`, shell tool names, and chained or redirected read-only prefixes. The
final session/hook set passed 48 tests in 4.45s, and the full suite passed 261
tests in 11.18s on Linux/Python 3.12.3. Self doctor reported 40 checks, 3
existing setup warnings, and 0 failures. Native Python 3.7 and Windows/macOS
execution were not available for this task. Independent review and delivery
are pending.

Delivered Task 3 verification: 2026-09-08 — after independent review resolved
all findings, the actual source checkout at `394d029` passed 244 tests in
12.14s on Linux/Python 3.12.3. Self doctor reported 40 checks, 3 existing setup
warnings, and 0 failures. All 106 recorded file modes and the exact 97
pre-existing mode-only differences were verified; root AGENTS.md and CLAUDE.md
remain unchanged. No push or publication occurred.

Task 3 verification: 2026-09-08 (ADR 0027) — 234 tests passed on Python
3.12.3 in 9.59s. The focused builder and publisher set passed 31 tests in
2.80s after the initial 28-test RED run reproduced 13 failures. Coverage
includes repository ancestors, source overlaps, Git metadata, symlinks,
unrecognized and older generated outputs, dirty and staged target work,
temporary preview immutability, dry-run manifest reporting, and commit scope.
The existing default payload rebuilt with and without `--clean`.

A local dry-run printed a 98-file proposed diff from
`/tmp/project-steward-reliability-publish-target`. Before and after the run,
the target remained on `main` at `65d18fc`; its index SHA-256 remained
`12525d40003f5d0d5b62dc2426bc63a507b5cc4f0291d3c8a3188d9ab65d09c6`,
and its only worktree file remained `README.md`. No pull, push, PR, or other
network operation ran. Compileall and `git diff --check` exited 0. Self doctor
reported 40 checks, 3 expected warnings, and 0 failures. The skill schema
validator passed under `/usr/bin/python3` with the existing system PyYAML; no
dependency was installed. Native Python 3.7 and Windows/macOS execution was not
available.

Task 3 review correction: 2026-09-08 — the initial direct batch reproduced all
five cases: an ignored file inside the artifact was accepted, and parent
symlinks plus external `.git` ancestors were accepted in clean and non-clean
builds. The final direct set passed 7 tests, including path-alias coverage and
an ignored file outside the artifact. The full payload-builder and
publisher set passed 38 tests in 3.17s. The default ignored payload rebuilt
successfully from its earlier generated version, and the modified
artifact-maintainer skill passed schema validation. Self doctor reported 40
checks, 3 expected warnings, and 0 failures; tracked and staged diff checks
passed. The correction used focused checks; the full suite passed in the actual
source checkout after review and integration, as recorded above.

Task 3 review correction round 2: 2026-09-08 — two direct regressions failed
against `3c5f043`: shared-ancestor inference accepted a caller-controlled link
to the repository's parent and rejected the simulated macOS layout of a
repository under `/Users` with output through `/tmp -> /private/tmp`. After
that initial RED, two clean-mode regressions showed that an allowed root alias
could conceal resolved `.git` ancestry. Replacing the heuristic with
filesystem-root alias recognition and checking canonical ancestors made the
direct set pass 8 tests; the complete builder/publisher set passed 41 tests in
3.32s. The default payload rebuild and skill schema validator passed; self
doctor reported 40 checks, 3 expected warnings, and 0 failures, and diff checks
passed. The full suite was reserved for post-review source integration.

Task 2 verification: 2026-09-08 (ADR 0026) — 217 tests passed on Python
3.12.3. The 31 focused Git path, root discovery, and session tests cover
ordinary and dangling final symlinks, literal pathspecs, parent escapes,
unrelated index entries, managed roots below the Git top level, nested
repository boundaries, explicit roots, ordinary operation markers, and an
actual linked-worktree merge conflict. Compileall exited 0. Native Python 3.7
and Windows/macOS execution was not available for this task. Self doctor
reported 40 checks, 3 expected warnings, and 0 failures. `git diff --check`
passed. No remote operation was performed.

Fix-round verification: 2026-09-08 (Task 1 independent review) — all six direct
covering tests passed in 0.23s and `tests/test_migrate.py` passed 31 tests in
1.36s. Regressions cover the distinct original-instruction backup directory,
ignore behavior after originals are copied, structured runtime-file conflicts,
preflight rejection of a symlinked runtime parent, and the same parent changing
after preflight. Self doctor reported 40 checks / 3 warnings / 0 failures, and
`git diff --check` passed. The full suite was not repeated by controller
instruction.

Previous entry: 2026-09-08 (0.4.1 reliability Task 1, ADR 0025) — 199 tests on
Python 3.12.3; focused migration/init/managed-block/workflow checks passed,
including fault injection for backup-copy and mid-write legacy changes;
`git diff --check`; self doctor 40 checks / 3 warnings / 0 failures. The warnings
are the supported source repo's missing WORKFLOW.md and unconfigured local Codex
hooks/activation. Native Python 3.7 and Windows/macOS execution was not available
for this task. No remote operation was performed.

Previous entry: 2026-09-08 (0.4.0 workflow defaults, ADR 0024) — 174 tests on
Python 3.12.3; 48 Codex setup tests with the older-Python fallback forced (12
native-parser cases skipped); compileall; Python 3.7 grammar check on all 20
runtime/tool Python files; self doctor 40 checks / 3 warnings / 0 failures;
payload build; wheel build and non-editable install; fresh external-backend
init, preview-only init, repeated-init byte stability, read-only resume, doctor,
and projectforge alias from the installed wheel. Claude plugin/marketplace
strict validation, Codex plugin schema, Grok validation, all five changed
skill schemas, bundled launcher, local publication dry-run, and diff whitespace
checks pass. The three self-doctor warnings are the supported legacy repo's
missing WORKFLOW.md and unconfigured local Codex hooks/activation. Native
Python 3.7 and Windows/macOS CI execution was not available in this session.
No remote publication was performed.

Previous entry: 2026-08-26 (0.3.4 handoff anchor and Stop-guard batch fix, ADR
0023) — 85 tests via bare `python3 -m pytest -q`, compileall, self doctor
(36 checks / 0 failures), payload build, publish dry-run, skill schema check,
`grok plugin validate`, Claude plugin and marketplace validation with
`--strict`, generated Codex plugin validation, launcher smoke, and
`git diff --check`. Regression tests cover a clean clone, later commits, a
dirty handoff, legacy metadata cleanup, and handled Stop-guard batches.

Distribution publish (2026-08-26): source `4750e38` was pushed to
`WSH95/project-steward` `main`; generated payload commit `13fc90f` was pushed
to `WSH95/agent-plugins` branch `publish/project-steward-plugin-0.3.4`; PR #11
was merged as `f969829` on 2026-08-26 at 10:19:01 UTC:
https://github.com/WSH95/agent-plugins/pull/11

Previous entry: 2026-08-26 (0.3.3 compact, humanized init documentation, ADR
0022) — 81 tests via bare `python3 -m pytest -q`, compileall, self doctor
(36 checks / 0 failures), payload build, `grok plugin validate`, Claude
plugin and marketplace validation with `--strict`, generated Codex plugin
validation, and `git diff --check`. A representative fresh `AGENTS.md` is
44 lines. The user approved the exact root `AGENTS.md` diff; its three managed
blocks were updated, then the full tests, compileall, self doctor, and
`git diff --check` passed again.

Distribution publish (2026-08-26): source `b3b887c` was pushed to
`WSH95/project-steward` `main`; the publish dry-run passed; generated payload
commit `6f026f0` was pushed to `WSH95/agent-plugins` branch
`publish/project-steward-plugin-0.3.3`; PR #10 was merged as `c65e1a2` on
2026-08-26: https://github.com/WSH95/agent-plugins/pull/10

Earlier entry: 2026-08-16 (0.3.2 Grok dual-contract, ADR 0021) — 77
tests via bare `python3 -m pytest -q`, compileall, self doctor (36
checks / 0 failures), payload build, `grok plugin validate` on the
Claude plugin dir (valid, version 0.3.2), `git diff --check`. Claude
`hooks.json` and `plugin-src/codex/` diffs empty. Not re-run this
session: `claude plugin validate --strict`, isolated Codex
marketplace/prompt-input smoke, or `agent-plugins` publish.

Earlier entry: 2026-07-08 (0.3.1 release publication, Windows batch
cascade hardening) — 70 tests via bare `python3 -m pytest -q`,
compileall, self doctor (36 checks / 0 failures), payload build,
`claude plugin validate --strict` (plugin + marketplace), generated
Codex plugin validator, built wrapper smoke printed 0.3.1, `git diff
--check`, isolated `CODEX_HOME=/tmp/project-steward-codex-publish.QrqsK4`
marketplace add/plugin add/list plus `codex debug prompt-input`, current
Codex manual spot-check for hooks/`commandWindows`, source push to
`WSH95/project-steward` through `fc84687`, and `agent-plugins` PR #5:
https://github.com/WSH95/agent-plugins/pull/5

Previous entry: 2026-07-08 (Claude/Codex `commandWindows` distinction
and wrapper fallback hardening, ADR 0020) — 70 tests via bare
`python3 -m pytest -q`, compileall, self doctor (36 checks /
0 failures), payload build, `claude plugin validate --strict` (plugin +
marketplace), generated Codex plugin validator, built wrapper smoke
printed 0.3.1, `git diff --check`, and isolated
`CODEX_HOME=/tmp/project-steward-codex-final.bnY6db` marketplace
add/plugin add/list plus `codex debug prompt-input`.

Earlier entry: 2026-07-08 (0.3.1 polyglot hook wrapper, ADR 0019) — 66
tests via bare `python3 -m pytest -q`, self doctor (36 checks /
0 failures, incl. the new Claude hooks schema check), compileall,
payload build, `claude plugin validate --strict` (plugin + marketplace),
wrapper smoke on all three legs (bundled launcher printed 0.3.1;
PATH-restricted fallback used the installed 0.3.0 CLI; no-Python run
exited 0 silently), end-to-end SessionStart recap through the built
wrapper in a scratch project, generated Codex plugin validator, Codex
regression gate (`plugin-src/codex` + `hooks.py` diff empty; Codex
payload tree diff vs pre-change build = version string + corrected
shared cross-platform.md only), and `git diff --check`.

Earlier entry: 2026-07-08 (Codex hook schema fix, 0.3.0 bump) — 59 tests,
self doctor (35 checks / 0 failures), `python3` compileall, payload
build, `git diff --check`, and `codex --version` passed locally
(`PYTHONPATH=plugin-src/src`, Python 3.8.10). `codex --version` no
longer reports the hook parse warning after live
`/home/wsh/.codex/hooks.json` was cleaned; it still reports the
sandbox's pre-existing read-only PATH alias warning. Earlier
smoke coverage also included agent-artifact-maintainer quick_validate,
publish dry-run, generated Codex plugin schema validator,
non-editable packaged install + init, and isolated Codex
marketplace/plugin add + prompt-input. Note: local `python` points at an
interpreter too old for `from __future__ import annotations`; use
`python3` or a project-managed interpreter for syntax checks here.

Distribution repo check (2026-07-08): `gh repo view WSH95/agent-plugins`
reported visibility PUBLIC, license MIT, default branch `main`; target
checkout `/tmp/agent-plugins` was clean after pushing Project Steward
payload commit `c78ea23`.

Distribution repo follow-up (2026-07-08): `/tmp/agent-plugins` clean and
synced at `fe6ae8d` after README/root-marketplace updates; `/tmp/agent-skills`
clean and synced at `da79b47` with only `LICENSE` and `README.md`.
`gh repo view WSH95/agent-skills` reported visibility PUBLIC, license
MIT, default branch `main`.

Publish-target manifest update (2026-07-08): 57 tests, `python3`
compileall, self doctor, payload build, skill quick_validate, generated
Codex plugin validator, publish dry-run to `/tmp/agent-plugins`, and
`git diff --check` passed.

Agent-plugins publish (2026-07-08): `python3
tools/publish_agent_artifact_pr.py --artifact project-steward-plugin
--target-checkout /tmp/agent-plugins --branch
publish/project-steward-plugin-0.3.0 ... --non-interactive` rebuilt the
payload, committed `eb2daf4` in `/tmp/agent-plugins`, pushed the branch,
and created OPEN PR https://github.com/WSH95/agent-plugins/pull/1.
Pre-publish checks: 59 tests, `python3` compileall, self doctor
35 checks / 0 failures, generated Codex plugin validator, and payload
diff showed expected 0.3.0/Codex hook-schema changes.
