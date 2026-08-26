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


def test_writing_skills_share_optional_humanizer_contract():
    guide = _flat("plugin-src/references/documentation-style.md")
    assert "plain" in guide
    assert "Do not invent facts" in guide
    assert "humanizer" in guide
    assert "do not install it automatically" in guide

    for name in (
        "project-init",
        "progress-tracking",
        "session-handoff",
        "session-resume",
    ):
        skill = _flat("plugin-src/skills/%s/SKILL.md" % name)
        assert "documentation-style.md" in skill
        assert "humanizer" in skill


def test_init_guidance_pins_compact_agents_output():
    skill = _flat("plugin-src/skills/project-init/SKILL.md")
    prompt = _flat("plugin-src/codex/prompts/steward-init.md")
    for text in (skill, prompt):
        assert "40-45 lines" in text
        assert "below 50" in text


def test_handoff_guidance_does_not_require_a_noop_checkpoint():
    handoff = _flat("plugin-src/skills/session-handoff/SKILL.md")
    protocol = _flat("plugin-src/references/session-protocol.md")
    assert "leave tracked files unchanged" in handoff
    assert "Do not create a checkpoint only" in handoff
    assert "last changed `HANDOFF.md`" in protocol
    assert "self-referential" in protocol
