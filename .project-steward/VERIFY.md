# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `python -m pytest` | 46 passed |
| Syntax sweep | `python -m compileall -q plugin/src` | exits 0 |
| Self health | `project-steward doctor --self` | 0 failures (35 checks) |
| Hook configs | `python -m json.tool plugin/hooks/hooks.json plugin/hooks/codex.hooks.json` | valid |
| Packaged install | clean venv `pip install .`, then `init --yes` in a scratch repo | HANDOFF.md starts with `---` (CI job `packaged-install`) |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-05 (0.2.3 packaging-fix session) — 46 tests +
compileall + doctor (35 checks) green locally (PYTHONPATH=plugin/src,
Python 3.8.10); full CI matrix green (run 28742494281 @ 60be5c6: 14
jobs incl. the new non-editable `packaged-install` job); acceptance in
three clean installs (checkout venv, git+ssh venv, pipx 0.2.3): `init`
writes real front matter, `resume` reports a real handoff.
