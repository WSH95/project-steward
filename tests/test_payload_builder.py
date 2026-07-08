import os
import json
import re
import shutil
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
    assert not (claude_plugin / "hooks" / "codex.hooks.json").exists()
    assert not (claude_plugin / "hooks" / "scripts").exists()
    hooks_text = (claude_plugin / "hooks" / "hooks.json").read_text(
        encoding="utf-8"
    )
    assert "commandWindows" not in hooks_text
    assert "run-hook.cmd" in hooks_text
    wrapper = claude_plugin / "hooks" / "run-hook.cmd"
    assert wrapper.is_file()
    if os.name != "nt":
        assert os.access(str(wrapper), os.X_OK)
    launcher = claude_plugin / "bin" / "project-steward"
    assert launcher.is_file()
    assert "project_steward.cli" in launcher.read_text(encoding="utf-8")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [sys.executable, str(launcher), "--version"],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.returncode == 0, proc.stdout
    assert "project-steward" in proc.stdout
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
    assert set(_json(codex / "hooks" / "hooks.json")) == {"hooks"}
    assert "project-steward hook stop --agent codex" in (
        codex / "hooks" / "hooks.json"
    ).read_text(encoding="utf-8")


def test_built_wrapper_invokes_bundled_launcher(tmp_path):
    """The polyglot wrapper must reach the payload-local Python launcher.

    Asserting the payload's own version string in the output proves the
    bundled src/ ran (an installed console-script fallback could report a
    different version; a silent no-python fallback would print nothing).
    """
    out = _run_builder(tmp_path)
    plugin = out / "claude" / "plugins" / "project-steward"
    wrapper = plugin / "hooks" / "run-hook.cmd"

    version = ""
    init_text = (plugin / "src" / "project_steward" / "__init__.py").read_text(
        encoding="utf-8"
    )
    for line in init_text.splitlines():
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break
    assert version

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    if os.name == "nt":
        cmd = ["cmd", "/c", str(wrapper), "--version"]
    else:
        # Claude Code runs hook commands through a POSIX shell; a file
        # without a shebang is interpreted as a shell script.
        cmd = ["sh", str(wrapper), "--version"]
    proc = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=env,
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.returncode == 0, proc.stdout
    assert "project-steward %s" % version in proc.stdout


def test_built_wrapper_falls_back_to_installed_cli(tmp_path):
    out = _run_builder(tmp_path)
    plugin = out / "claude" / "plugins" / "project-steward"
    wrapper = plugin / "hooks" / "run-hook.cmd"
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    if os.name == "nt":
        for name in ("py.cmd", "python.cmd"):
            (fakebin / name).write_text("@echo off\r\nexit /b 7\r\n",
                                        encoding="utf-8")
        (fakebin / "project-steward.cmd").write_text(
            "@echo off\r\necho fallback-cli %*\r\nexit /b 0\r\n",
            encoding="utf-8",
        )
        cmd = ["cmd", "/c", str(wrapper), "--version"]
        path = str(fakebin) + os.pathsep + os.environ.get("PATH", "")
    else:
        shell = shutil.which("sh") or "sh"
        for name in ("python3", "python", "py"):
            script = fakebin / name
            script.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
            script.chmod(0o755)
        fallback = fakebin / "project-steward"
        fallback.write_text(
            "#!/bin/sh\nprintf 'fallback-cli %s\\n' \"$*\"\n",
            encoding="utf-8",
        )
        fallback.chmod(0o755)
        cmd = [shell, str(wrapper), "--version"]
        path = str(fakebin) + os.pathsep + os.environ.get("PATH", "")

    env = os.environ.copy()
    env["PATH"] = path
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=env,
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert proc.returncode == 0, proc.stdout
    assert "fallback-cli --version" in proc.stdout


def test_built_wrapper_tries_next_python_before_cli(tmp_path):
    out = _run_builder(tmp_path)
    plugin = out / "claude" / "plugins" / "project-steward"
    wrapper = plugin / "hooks" / "run-hook.cmd"
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()

    if os.name == "nt":
        (fakebin / "py.cmd").write_text("@echo off\r\nexit /b 7\r\n",
                                        encoding="utf-8")
        (fakebin / "python.cmd").write_text(
            "@echo off\r\necho python-ok %*\r\nexit /b 0\r\n",
            encoding="utf-8",
        )
        (fakebin / "project-steward.cmd").write_text(
            "@echo off\r\necho fallback-cli %*\r\nexit /b 0\r\n",
            encoding="utf-8",
        )
        cmd = ["cmd", "/c", str(wrapper), "--version"]
        path = str(fakebin) + os.pathsep + os.environ.get("PATH", "")
    else:
        shell = shutil.which("sh") or "sh"
        python3 = fakebin / "python3"
        python3.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        python3.chmod(0o755)
        python = fakebin / "python"
        python.write_text(
            "#!/bin/sh\nprintf 'python-ok %s\\n' \"$*\"\n",
            encoding="utf-8",
        )
        python.chmod(0o755)
        fallback = fakebin / "project-steward"
        fallback.write_text(
            "#!/bin/sh\nprintf 'fallback-cli %s\\n' \"$*\"\n",
            encoding="utf-8",
        )
        fallback.chmod(0o755)
        cmd = [shell, str(wrapper), "--version"]
        path = str(fakebin) + os.pathsep + os.environ.get("PATH", "")

    env = os.environ.copy()
    env["PATH"] = path
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=env,
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert proc.returncode == 0, proc.stdout
    assert "python-ok" in proc.stdout
    assert "fallback-cli" not in proc.stdout


def test_release_versions_are_consistent(tmp_path):
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (
        ROOT / "plugin-src" / "src" / "project_steward" / "__init__.py"
    ).read_text(encoding="utf-8")
    metadata = _json(ROOT / "plugin-src" / "metadata.json")

    pyproject_version = re.search(r'^version = "([^"]+)"',
                                  pyproject, re.MULTILINE).group(1)
    package_version = re.search(r'^__version__ = "([^"]+)"',
                                package_init, re.MULTILINE).group(1)

    out = _run_builder(tmp_path)
    claude_manifest = _json(
        out / "claude" / "plugins" / "project-steward"
        / ".claude-plugin" / "plugin.json"
    )
    codex_manifest = _json(
        out / "codex" / "plugins" / "project-steward"
        / ".codex-plugin" / "plugin.json"
    )

    assert {
        pyproject_version,
        package_version,
        metadata["version"],
        claude_manifest["version"],
        codex_manifest["version"],
    } == {package_version}


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
