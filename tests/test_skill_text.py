from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _flat(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    return " ".join(text.split())


def test_init_skill_approval_gate_shows_dry_run_draft():
    skill = _flat("plugin-src/skills/project-init/SKILL.md")
    assert "--dry-run" in skill
    assert "not review surfaces" in skill
    assert "verbatim in the visible conversation" in skill
    # preview must come before apply in the generate phase
    assert skill.index("--dry-run") < skill.index("--yes")


def test_init_command_mirrors_the_gate():
    cmd = _flat("plugin-src/claude/commands/init.md")
    assert "--dry-run" in cmd
    assert "BEFORE asking approval" in cmd
    assert "not review surfaces" in cmd
    assert cmd.index("--dry-run") < cmd.index("--yes")
