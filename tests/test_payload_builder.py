import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "tools" / "build_plugin_payloads.py"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run_builder(tmp_path):
    out = tmp_path / "payloads"
    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--clean",
            "--out",
            str(out),
        ],
        cwd=str(ROOT),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return out


def test_builder_emits_extractable_claude_and_codex_payloads(tmp_path):
    out = _run_builder(tmp_path)

    claude = out / "claude"
    claude_plugin = claude / "plugins" / "project-steward"
    claude_manifest = _json(
        claude_plugin / ".claude-plugin" / "plugin.json"
    )
    assert claude_manifest["commands"] == "./commands"
    assert claude_manifest["skills"] == "./skills"
    assert (claude_plugin / "commands" / "init.md").is_file()
    assert (claude_plugin / "hooks" / "hooks.json").is_file()
    assert (claude_plugin / "hooks" / "codex.hooks.json").is_file()
    assert (claude_plugin / "src" / "project_steward" / "cli.py").is_file()

    claude_marketplace = _json(claude / ".claude-plugin" / "marketplace.json")
    assert claude_marketplace["plugins"][0]["source"] == "./plugins/project-steward"

    codex = out / "codex"
    codex_plugin = codex / "plugins" / "project-steward"
    codex_manifest = _json(codex_plugin / ".codex-plugin" / "plugin.json")
    assert codex_manifest["skills"] == "./skills/"
    assert "hooks" not in codex_manifest
    assert (codex_plugin / "skills" / "project-init" / "SKILL.md").is_file()
    assert (codex_plugin / "references" / "session-protocol.md").is_file()
    assert (
        codex_plugin
        / "src"
        / "project_steward"
        / "templates"
        / "AGENTS.md.template"
    ).is_file()
    assert not (codex_plugin / "hooks" / "hooks.json").exists()

    codex_marketplace = _json(codex / ".agents" / "plugins" / "marketplace.json")
    assert codex_marketplace["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/project-steward",
    }


def test_builder_outputs_codex_command_like_companions(tmp_path):
    out = _run_builder(tmp_path)
    codex = out / "codex"

    expected_prompts = {
        "steward-audit.md",
        "steward-backend.md",
        "steward-checkpoint.md",
        "steward-init.md",
        "steward-resume.md",
        "steward-wrap.md",
    }
    assert {
        path.name for path in (codex / "prompts").glob("*.md")
    } == expected_prompts
    assert (codex / "hooks" / "hooks.json").is_file()
    assert "project-steward hook stop --agent codex" in (
        codex / "hooks" / "hooks.json"
    ).read_text(encoding="utf-8")


def test_builder_clean_replaces_previous_output(tmp_path):
    out = tmp_path / "payloads"
    stale = out / "claude" / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(BUILDER), "--clean", "--out", str(out)],
        cwd=str(ROOT),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert not stale.exists()
    assert (out / "claude" / "plugins" / "project-steward").is_dir()
