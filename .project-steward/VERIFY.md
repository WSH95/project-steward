# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `PYTHONPATH=plugin-src/src python3 -m pytest -q` | 59 passed |
| Syntax sweep | `python3 -m compileall -q plugin-src/src tools` | exits 0 |
| Self health | `PYTHONPATH=plugin-src/src python3 -m project_steward doctor --self` | 0 failures |
| Payload build | `python3 tools/build_plugin_payloads.py --clean --out dist/project-steward` | exits 0 |
| Skill schema | `python3 /home/wsh/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugin-src/skills/agent-artifact-maintainer` | exits 0 |
| Publish dry-run | `python3 tools/publish_agent_artifact_pr.py --artifact project-steward-plugin --target-repo git@github.com:WSH95/agent-plugins.git --dry-run --target-checkout /tmp/project-steward-artifact-publish-dry-run --non-interactive` | copies artifact; no commit/push/PR |
| JSON configs | `python3 -m json.tool plugin-src/claude/hooks/hooks.json && python3 -m json.tool plugin-src/codex/hooks/hooks.json` | valid |
| Codex plugin schema | `python3 /home/wsh/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py dist/project-steward/codex/plugins/project-steward` | exits 0 |
| Codex plugin smoke | isolated `CODEX_HOME=/tmp/project-steward-codex-impl-home` marketplace add/list/plugin add + `codex debug prompt-input` | plugin listed/installed; `project-steward:` skills visible; no `hooks/hooks.json` in prompt input |
| Packaged install | clean venv `pip install .`, then `init --yes` in a scratch repo | HANDOFF.md starts with `---` (CI job `packaged-install`) |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-08 (Codex hook schema fix, 0.3.0 bump) — 59 tests,
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
