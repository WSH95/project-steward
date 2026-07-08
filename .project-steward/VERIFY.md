# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `python3 -m pytest -q` (bare checkout works; no install needed) | 70 passed |
| Syntax sweep | `python3 -m compileall -q plugin-src/src tools` | exits 0 |
| Self health | `PYTHONPATH=plugin-src/src python3 -m project_steward doctor --self` | 0 failures |
| Payload build | `python3 tools/build_plugin_payloads.py --clean --out dist/project-steward` | exits 0 |
| Skill schema | `python3 /home/wsh/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugin-src/skills/agent-artifact-maintainer` | exits 0 |
| Publish dry-run | `python3 tools/publish_agent_artifact_pr.py --artifact project-steward-plugin --target-repo git@github.com:WSH95/agent-plugins.git --dry-run --target-checkout /tmp/project-steward-artifact-publish-dry-run --non-interactive` | copies artifact; no commit/push/PR |
| JSON configs | `python3 -m json.tool plugin-src/claude/hooks/hooks.json && python3 -m json.tool plugin-src/codex/hooks/hooks.json` | valid |
| Claude manifests | `claude plugin validate dist/project-steward/claude/plugins/project-steward --strict && claude plugin validate dist/project-steward/claude --strict` | both pass (manifest-only: hooks.json schema is covered by `doctor --self`) |
| Claude hook wrapper | `printf '' \| sh dist/project-steward/claude/plugins/project-steward/hooks/run-hook.cmd --version` | prints the payload's own version (bundled launcher ran, not a fallback) |
| Codex plugin schema | `python3 /home/wsh/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py dist/project-steward/codex/plugins/project-steward` | exits 0 |
| Codex plugin smoke | isolated `CODEX_HOME=/tmp/project-steward-codex-impl.*` marketplace add/list/plugin add + `codex debug prompt-input` | plugin listed/installed; `project-steward:` skills visible; no `hooks/hooks.json` in prompt input |
| Packaged install | clean venv `pip install .`, then `init --yes` in a scratch repo | HANDOFF.md starts with `---` (CI job `packaged-install`) |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-08 (0.3.1 release publication, Windows batch
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
