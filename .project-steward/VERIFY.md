# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `python -m pytest` | 43 passed |
| Syntax sweep | `python -m compileall -q plugin/src` | exits 0 |
| Self health | `project-steward doctor --self` | 0 failures |
| Hook configs | `python -m json.tool plugin/hooks/hooks.json plugin/hooks/codex.hooks.json` | valid |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-04 (distribution session) — 43 tests + compileall
+ doctor green locally (PYTHONPATH=plugin/src, Python 3.8.10), and the
full CI matrix green on GitHub for the first time (run 28715861017 @
c20f0ea: 13 jobs, 3 OS, Python 3.7–3.13, editable install of the
plugin/ layout). Note: the local `pip install -e .` route is unverified
on this machine (no python3-venv); CI covers it.
