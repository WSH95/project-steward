import json
import os
import subprocess
import sys
from pathlib import Path

from project_steward import doctor
from project_steward.cli import main as cli_main
from project_steward.scaffold import apply_plan, plan_files
from project_steward.survey import survey


ROOT = Path(__file__).resolve().parent.parent


def test_survey_detects_commands_and_questions(git_repo):
    (git_repo / "package.json").write_text(
        json.dumps({"name": "x", "scripts": {"test": "jest",
                                             "build": "tsc"}}),
        encoding="utf-8")
    (git_repo / "src.ts").write_text("export {}\n", encoding="utf-8")
    findings = survey(git_repo)
    assert findings["candidate_commands"]["test"] == "npm run test"
    assert findings["git"]["is_repo"] is True
    assert any("lint" in q for q in findings["open_questions"])


def test_doctor_ok_after_init_and_fails_on_secret(git_repo):
    plan, mapping = plan_files(git_repo, {"project_name": "Demo"})
    apply_plan(git_repo, plan, mapping)
    results = doctor.run_checks(git_repo)
    assert not [r for r in results if r["status"] == doctor.FAIL
                and "project-steward on PATH" not in r["name"]]
    (git_repo / ".project-steward" / "PROJECT.md").write_text(
        'api_key = "abcdef123456789012345"\n', encoding="utf-8")
    results = doctor.run_checks(git_repo)
    fails = [r for r in results if r["status"] == doctor.FAIL]
    assert any("secrets" in r["name"] for r in fails)


def test_self_doctor_rejects_codex_hook_metadata(tmp_path):
    (tmp_path / "plugin-src" / "src" / "project_steward").mkdir(parents=True)
    (tmp_path / "plugin-src" / "claude" / "hooks").mkdir(parents=True)
    (tmp_path / "plugin-src" / "codex" / "hooks").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "plugin-src" / "metadata.json").write_text(
        '{"name": "project-steward"}\n', encoding="utf-8"
    )
    (tmp_path / "plugin-src" / "claude" / "hooks" / "hooks.json").write_text(
        '{"description": "ok for Claude", "hooks": {}}\n',
        encoding="utf-8",
    )
    (tmp_path / "plugin-src" / "codex" / "hooks" / "hooks.json").write_text(
        '{"description": "not accepted by Codex", "hooks": {}}\n',
        encoding="utf-8",
    )

    results = doctor._self_checks(tmp_path)

    assert any(
        r["status"] == doctor.FAIL
        and r["name"] == "self: plugin-src/codex/hooks/hooks.json schema"
        and "unexpected root key(s): description" in r["detail"]
        for r in results
    )


def test_claude_hooks_use_cross_platform_wrapper():
    # Claude Code hooks have no per-OS command field (ADR 0019); every
    # hook must go through the polyglot wrapper next to hooks.json.
    hooks_dir = ROOT / "plugin-src" / "claude" / "hooks"
    hooks = json.loads(
        (hooks_dir / "hooks.json").read_text(encoding="utf-8")
    )
    wrapper = hooks_dir / "run-hook.cmd"
    assert wrapper.is_file()
    if os.name != "nt":
        assert os.access(str(wrapper), os.X_OK)

    # Batch cascade must use run-time idioms: cmd.exe expands %ERRORLEVEL%
    # inside a parenthesized block at parse time, and chaining into a
    # .cmd shim without `call` never returns to the wrapper.
    batch = wrapper.read_text(encoding="utf-8").split("CMDBLOCK")[1]
    assert 'call py -3 "%~dp0..\\bin\\project-steward" %*' in batch
    assert 'call python "%~dp0..\\bin\\project-steward" %*' in batch
    assert "call project-steward %*" in batch
    assert "if not errorlevel 1 exit /b 0" in batch
    assert "if %ERRORLEVEL% equ 0 exit /b 0" not in batch

    for groups in hooks["hooks"].values():
        for group in groups:
            for handler in group["hooks"]:
                assert set(handler) <= {"type", "command", "timeout"}
                command = handler["command"]
                assert '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"' in command
                assert "--agent claude" in command
                assert "python3" not in command
                assert "project_steward_hook.py" not in command


def test_self_doctor_rejects_unknown_claude_hook_fields(tmp_path):
    (tmp_path / "plugin-src" / "src" / "project_steward").mkdir(parents=True)
    (tmp_path / "plugin-src" / "claude" / "hooks").mkdir(parents=True)
    (tmp_path / "plugin-src" / "codex" / "hooks").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "plugin-src" / "metadata.json").write_text(
        '{"name": "project-steward"}\n', encoding="utf-8"
    )
    (tmp_path / "plugin-src" / "claude" / "hooks" / "hooks.json").write_text(
        json.dumps({
            "hooks": {
                "Stop": [{"hooks": [{
                    "type": "command",
                    "command": ('"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"'
                                ' hook stop --agent claude'),
                    "commandWindows": "py -3 something",
                    "timeout": 15,
                }]}],
            },
        }),
        encoding="utf-8",
    )
    (tmp_path / "plugin-src" / "codex" / "hooks" / "hooks.json").write_text(
        '{"hooks": {}}\n', encoding="utf-8"
    )

    results = doctor._self_checks(tmp_path)

    assert any(
        r["status"] == doctor.FAIL
        and r["name"] == "self: plugin-src/claude/hooks/hooks.json schema"
        and "commandWindows" in r["detail"]
        for r in results
    )


def test_cli_init_and_status(git_repo, capsys):
    rc = cli_main(["init", "--root", str(git_repo), "--project-name",
                   "Demo", "--yes"])
    assert rc == 0
    capsys.readouterr()  # flush init output
    rc = cli_main(["status", "--root", str(git_repo), "--json"])
    assert rc == 0
    recap = json.loads(capsys.readouterr().out)
    assert recap["handoff"]["session_status"] == "closed"


def test_cli_version_runs():
    # Self-sufficient on a bare checkout: the subprocess needs the package
    # on its own path (conftest's sys.path shim does not propagate).
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "plugin-src" / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "project_steward", "--version"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    assert proc.returncode == 0
    assert b"project-steward" in proc.stdout
