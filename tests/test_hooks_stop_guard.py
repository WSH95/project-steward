import io
import json
import os
import sys
import time

from project_steward import hooks, sessions
from project_steward.paths import runtime_dir, state_dir
from project_steward.scaffold import apply_plan, plan_files
from project_steward.state import write_text_atomic


def _init(repo):
    plan, mapping = plan_files(repo, {"project_name": "Demo"})
    apply_plan(repo, plan, mapping)


def _run_hook(argv, payload, capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    rc = hooks.main(argv)
    out = capsys.readouterr().out
    return rc, (json.loads(out) if out.strip() else {})


def _make_stale(repo, edits=6):
    handoff = state_dir(repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    for i in range(edits):
        sessions.record_activity(repo, "Edit", "f%d.py" % i)


def _make_stale_with_activity(repo, activities):
    handoff = state_dir(repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    for tool, detail in activities:
        sessions.record_activity(repo, tool, detail)


def test_stop_blocks_once_then_cooldown(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale(git_repo)
    payload = {"cwd": str(git_repo), "stop_hook_active": False}
    rc, out = _run_hook(["stop", "--agent", "claude"], payload, capsys,
                        monkeypatch)
    assert rc == 0 and out.get("decision") == "block"
    assert "auto-checkpoint" in out.get("reason", "")
    assert "handoff-relevant actions" in out.get("reason", "")
    assert "project-steward checkpoint" in out.get("reason", "")
    assert "refreshes checkpoint metadata" in out.get("reason", "")
    # Second stop inside the cooldown window: silent.
    rc, out = _run_hook(["stop", "--agent", "claude"], payload, capsys,
                        monkeypatch)
    assert rc == 0 and out == {}


def test_stop_ignores_read_only_activity(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale_with_activity(git_repo, [
        ("Bash", "git status --short --branch"),
        ("Bash", "git log --oneline -5"),
        ("Bash", "PYTHONPATH=plugin-src/src python3 -m pytest -q"),
        ("Bash", "CODEX_HOME=/tmp/codex codex --version"),
        ("Bash", "project-steward resume"),
        ("Bash", "python3 -m project_steward doctor --self"),
        ("Bash", "rg -n 'auto_handoff' plugin-src tests"),
        ("Bash", "python3 -m compileall -q plugin-src/src tools"),
    ])

    rc, out = _run_hook(
        ["stop", "--agent", "codex"],
        {"cwd": str(git_repo), "stop_hook_active": False},
        capsys,
        monkeypatch,
    )

    assert rc == 0
    assert out == {}


def test_stop_counts_mutating_activity(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale_with_activity(git_repo, [
        ("Bash", "git status --short --branch"),
        ("Edit", "src/a.py"),
        ("apply_patch", "*** Begin Patch"),
        ("Write", "src/b.py"),
        ("Bash", "python3 -m compileall -q plugin-src/src tools"),
        ("Bash", "git commit -m 'change'"),
        ("Bash",
         "python3 tools/build_plugin_payloads.py --clean --out "
         "dist/project-steward"),
    ])

    rc, out = _run_hook(
        ["stop", "--agent", "codex"],
        {"cwd": str(git_repo), "stop_hook_active": False},
        capsys,
        monkeypatch,
    )

    assert rc == 0
    assert out.get("decision") == "block"


def test_stop_loop_guard(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale(git_repo)
    payload = {"cwd": str(git_repo), "stop_hook_active": True}
    rc, out = _run_hook(["stop", "--agent", "claude"], payload, capsys,
                        monkeypatch)
    assert rc == 0 and out == {}


def test_stop_remind_mode(git_repo, capsys, monkeypatch):
    _init(git_repo)
    cfg = state_dir(git_repo) / "config.toml"
    write_text_atomic(cfg, '[session]\nauto_handoff_mode = "remind"\n')
    _make_stale(git_repo)
    payload = {"cwd": str(git_repo), "stop_hook_active": False}
    rc, out = _run_hook(["stop", "--agent", "codex"], payload, capsys,
                        monkeypatch)
    assert rc == 0 and "systemMessage" in out and "decision" not in out


def test_session_start_injects_recap(git_repo, capsys, monkeypatch):
    _init(git_repo)
    payload = {"cwd": str(git_repo)}
    rc, out = _run_hook(["session-start", "--agent", "codex"], payload,
                        capsys, monkeypatch)
    assert rc == 0
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "session recap" in ctx and "ACTION REQUIRED" in ctx


def test_wrap_language_detector(git_repo, capsys, monkeypatch):
    _init(git_repo)
    payload = {"cwd": str(git_repo),
               "prompt": "ok let's wrap up for today, thanks"}
    rc, out = _run_hook(["user-prompt-submit", "--agent", "claude"], payload,
                        capsys, monkeypatch)
    assert "session-handoff" in out["hookSpecificOutput"]["additionalContext"]
    rc, out = _run_hook(["user-prompt-submit", "--agent", "claude"],
                        {"cwd": str(git_repo), "prompt": "add a test"},
                        capsys, monkeypatch)
    assert out == {}


def test_wrap_detector_accepts_grok_user_prompt_field(git_repo, capsys,
                                                      monkeypatch):
    _init(git_repo)
    rc, out = _run_hook(
        ["user-prompt-submit", "--agent", "claude"],
        {"cwd": str(git_repo), "userPrompt": "ok, switch to grok now"},
        capsys, monkeypatch,
    )
    assert "session-handoff" in out["hookSpecificOutput"]["additionalContext"]


def test_wrap_detector_ignores_harness_text_and_prose(git_repo, capsys,
                                                      monkeypatch):
    _init(git_repo)
    blob = ("<task-notification>agent finished; it rewrote the handoff "
            "and wants to wrap up</task-notification>")
    rc, out = _run_hook(["user-prompt-submit", "--agent", "claude"],
                        {"cwd": str(git_repo), "prompt": blob}, capsys,
                        monkeypatch)
    assert rc == 0 and out == {}
    rc, out = _run_hook(["user-prompt-submit", "--agent", "claude"],
                        {"cwd": str(git_repo),
                         "prompt": "the handoff template needs edits"},
                        capsys, monkeypatch)
    assert rc == 0 and out == {}


def test_hook_tolerates_non_string_cwd(git_repo, capsys, monkeypatch):
    _init(git_repo)
    monkeypatch.chdir(git_repo)
    rc, out = _run_hook(["session-start", "--agent", "claude"],
                        {"cwd": 123}, capsys, monkeypatch)
    assert rc == 0
    assert "session recap" in out["hookSpecificOutput"]["additionalContext"]


def test_hooks_never_fail(tmp_path, capsys, monkeypatch):
    # Not a steward project, garbage stdin: still exit 0, no output.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    rc = hooks.main(["stop", "--agent", "claude"])
    assert rc == 0 and capsys.readouterr().out == ""


def test_grok_camelcase_post_tool_use_counts_toward_stop(
        git_repo, capsys, monkeypatch):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    for path in ("src/a.py", "src/b.py", "src/c.py", "src/d.py", "src/e.py"):
        rc, out = _run_hook(
            ["post-tool-use", "--agent", "claude"],
            {
                "cwd": str(git_repo),
                "toolName": "search_replace",
                "toolInput": {"file_path": path},
            },
            capsys,
            monkeypatch,
        )
        assert rc == 0 and out == {}
    rc, out = _run_hook(
        ["post-tool-use", "--agent", "claude"],
        {
            "cwd": str(git_repo),
            "toolName": "run_terminal_command",
            "toolInput": {"command": "git status --short --branch"},
        },
        capsys,
        monkeypatch,
    )
    assert rc == 0 and out == {}

    activity = (runtime_dir(git_repo) / "activity.log").read_text(
        encoding="utf-8")
    assert "search_replace" in activity
    assert "src/a.py" in activity
    assert "run_terminal_command" in activity

    rc, out = _run_hook(
        ["stop", "--agent", "claude"],
        {"cwd": str(git_repo), "stopHookActive": False, "reason": "end_turn"},
        capsys,
        monkeypatch,
    )
    assert rc == 0
    assert out.get("decision") == "block"


def test_grok_camelcase_stop_loop_guard(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale(git_repo)
    rc, out = _run_hook(
        ["stop", "--agent", "claude"],
        {"cwd": str(git_repo), "stopHookActive": True, "reason": "end_turn"},
        capsys,
        monkeypatch,
    )
    assert rc == 0 and out == {}


def test_grok_session_end_stop_does_not_block(git_repo, capsys, monkeypatch):
    _init(git_repo)
    _make_stale(git_repo)
    for reason in ("shutdown", "channel_closed"):
        rc, out = _run_hook(
            ["stop", "--agent", "claude"],
            {
                "cwd": str(git_repo),
                "stopHookActive": False,
                "reason": reason,
            },
            capsys,
            monkeypatch,
        )
        assert rc == 0 and out == {}, reason


def test_grok_env_claims_agent_as_grok(git_repo, capsys, monkeypatch):
    _init(git_repo)
    monkeypatch.setenv("GROK_SESSION_ID", "sess-grok-1")
    rc, out = _run_hook(
        ["session-start", "--agent", "claude"],
        {"cwd": str(git_repo)},
        capsys,
        monkeypatch,
    )
    assert rc == 0
    assert "session recap" in out["hookSpecificOutput"]["additionalContext"]
    record = json.loads(
        (runtime_dir(git_repo) / "session.json").read_text(encoding="utf-8")
    )
    assert record.get("agent") == "grok"
