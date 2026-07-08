# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `PYTHONPATH=plugin-src/src python3 -m pytest -q` | 51 passed |
| Syntax sweep | `python3 -m compileall -q plugin-src/src tools` | exits 0 |
| Self health | `PYTHONPATH=plugin-src/src python3 -m project_steward doctor --self` | 0 failures |
| Payload build | `python3 tools/build_plugin_payloads.py --clean --out dist/project-steward` | exits 0 |
| JSON configs | `python3 -m json.tool plugin-src/claude/hooks/hooks.json && python3 -m json.tool plugin-src/codex/hooks/hooks.json` | valid |
| Codex plugin schema | `python3 /home/wsh/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py dist/project-steward/codex/plugins/project-steward` | exits 0 |
| Codex plugin smoke | isolated `CODEX_HOME=/tmp/project-steward-codex-impl-home` marketplace add/list/plugin add + `codex debug prompt-input` | plugin listed/installed; `project-steward:` skills visible; no `hooks/hooks.json` in prompt input |
| Packaged install | clean venv `pip install .`, then `init --yes` in a scratch repo | HANDOFF.md starts with `---` (CI job `packaged-install`) |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-07 (development layout refactor) — 51 tests,
payload build, generated Codex plugin schema validator, self doctor
(34 checks), `python3` compileall, non-editable packaged install + init
smoke, isolated Codex marketplace/plugin add + prompt-input smoke, and
`git diff --check` passed locally (`PYTHONPATH=plugin-src/src`, Python
3.8.10). Note: local `python` points at an interpreter too old for
`from __future__ import annotations`; use `python3` or a project-managed
interpreter for syntax checks here.
