# Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Claude Code / Codex hook API drift | medium | medium | all hook logic behind one dispatcher; only hooks/*.json + hooks.py need touching; doctor validates configs |
| Codex hooks stay Windows-disabled | medium | low | AGENTS.md protocol + prompts + manual CLI carry the behavior (documented) |
| Python 3.7 floor untested on dev machines (3.12 here) | medium | medium | CI matrix pins 3.7 jobs; code avoids >3.7 syntax/stdlib; tomlmini fallback tested |
| Backend installers drift upstream | high | low | commands labeled "verify against upstream README"; broker never auto-installs |
| Claude Code gains native AGENTS.md support | low | low | delete CLAUDE.md adapter; everything else unchanged |
