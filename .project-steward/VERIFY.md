# Verification

| Check | Command | Expected |
| --- | --- | --- |
| Install | `python -m pip install -e ".[dev]"` | exits 0 |
| Tests | `python -m pytest` | 41 passed |
| Syntax sweep | `python -m compileall -q src` | exits 0 |
| Self health | `project-steward doctor --self` | 0 failures |
| Hook configs | `python -m json.tool hooks/hooks.json hooks/codex.hooks.json` | valid |
| E2E smoke | init + resume + checkpoint + wrap + migrate in a scratch repo | see PROGRESS.md |

Last verified: 2026-07-04 (audit session) — tests/compileall/doctor green
on Python 3.8.10, under both TZ=UTC and TZ=America/New_York (DST
regression coverage); 3.7 floor is CI-covered, not locally executed.
