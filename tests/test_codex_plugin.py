import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_skill_resource_paths_are_relative_to_skill_directories():
    project_init = (
        ROOT / "plugin-src" / "skills" / "project-init" / "SKILL.md"
    ).read_text(encoding="utf-8")
    backend = (
        ROOT / "plugin-src" / "skills" / "backend-broker" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "../../references/security-model.md" in project_init
    assert "../../src/project_steward/templates/" in project_init
    assert "../../references/backend-selection.md" in backend
    assert "see references/" not in project_init
    assert "see references/" not in backend


def test_codex_install_docs_match_current_cli_and_hook_feature():
    docs = [
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / "codex" / "INSTALL.md").read_text(encoding="utf-8"),
        (ROOT / "plugin-src" / "codex" / "hooks" / "hooks.json").read_text(
            encoding="utf-8"
        ),
    ]
    joined = "\n".join(docs)
    assert "codex plugin add project-steward@project-steward-marketplace" in joined
    assert "codex plugin install" not in joined
    assert "codex_hooks = true" not in joined
    assert "features.hooks" in joined


def test_docs_keep_claude_and_codex_commandwindows_claims_separate():
    docs = "\n".join([
        (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
        (ROOT / ".project-steward" / "DECISIONS.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "codex" / "INSTALL.md").read_text(encoding="utf-8"),
    ])

    assert "same fiction ADR 0004 had already rejected on the Codex side" not in docs
    assert "commandWindows` as undocumented on the Codex side" not in docs
    assert "Claude Code has no `commandWindows` hook field" in docs
    assert "Codex currently documents `commandWindows`" in docs


def test_codex_hooks_json_uses_strict_root_schema():
    hooks = json.loads(
        (ROOT / "plugin-src" / "codex" / "hooks" / "hooks.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(hooks) == {"hooks"}
    assert set(hooks["hooks"]) == {
        "SessionStart",
        "PostToolUse",
        "UserPromptSubmit",
        "Stop",
    }
