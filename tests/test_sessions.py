import json
import os
import subprocess
import time

import pytest

from project_steward import sessions
from project_steward import gitutil
from project_steward.paths import runtime_dir, state_dir
from project_steward.scaffold import apply_plan, plan_files
from project_steward.state import (parse_front_matter, update_front_matter,
                                   write_json_atomic)


def _init(repo):
    plan, mapping = plan_files(repo, {"project_name": "Demo"})
    apply_plan(repo, plan, mapping)


def _commit_all(repo, message):
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-q", "-m", message],
                   cwd=str(repo), check=True)


def _run_git(repo, *args):
    return subprocess.run(
        ["git"] + list(args), cwd=str(repo), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)


def test_resume_never_dirties_committed_files(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    before = handoff.read_text(encoding="utf-8")
    sessions.claim_session(git_repo, "test")
    recap = sessions.build_recap(git_repo)
    assert handoff.read_text(encoding="utf-8") == before
    assert recap["handoff"]["session_status"] == "closed"
    assert (runtime_dir(git_repo) / "session.json").is_file()


def test_plan_open_tasks_scoped_to_first_milestone(git_repo):
    _init(git_repo)
    (state_dir(git_repo) / "PLAN.md").write_text(
        "# Plan\n\n"
        "## M1: done milestone\n\n- [x] shipped\n- [x] also shipped\n\n"
        "## Later\n\n- [ ] someday\n- [ ] maybe\n- [ ] eventually\n",
        encoding="utf-8")
    milestone, open_tasks = sessions._plan_current(git_repo)
    assert milestone == "M1: done milestone"
    assert open_tasks == 0


def test_live_runtime_marker_is_advisory_while_activity_is_a_crash_signal(
        git_repo):
    _init(git_repo)
    sessions.claim_session(git_repo, "test")
    # Simulate work after the handoff was last written.
    handoff = state_dir(git_repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    sessions.record_activity(git_repo, "Edit", "train.py")
    recap = sessions.build_recap(git_repo)

    assert not any("runtime marker" in item
                   for item in recap["crash_signals"])
    assert any("runtime marker" in item for item in recap["runtime_notes"])
    assert any("AFTER the last HANDOFF.md" in item
               for item in recap["crash_signals"])


def test_crash_detection_ignores_read_only_activity(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    sessions.record_activity(git_repo, "Bash", "git status --short")
    sessions.record_activity(git_repo, "Bash", "sed -n '1,40p' README.md")
    sessions.record_activity(git_repo, "Bash", "python3 -m pytest -q")
    sessions.record_activity(
        git_repo, "Bash",
        "PYTHONPATH=plugin-src/src python3 -m project_steward doctor --self"
    )
    sessions.record_activity(git_repo, "Bash", "project-steward resume")

    signals = sessions.detect_crash_signals(git_repo)

    assert not any("AFTER the last HANDOFF.md" in s for s in signals)


def test_handoff_relevant_activity_count_filters_read_only(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    sessions.record_activity(git_repo, "Bash", "git status --short")
    sessions.record_activity(git_repo, "Bash", "rg -n 'handoff' tests")
    sessions.record_activity(
        git_repo, "Edit", "plugin-src/src/project_steward/hooks.py"
    )
    sessions.record_activity(git_repo, "Bash", "git commit -m 'change'")
    sessions.record_activity(git_repo, "Bash", "git branch -D old-topic")

    count = sessions.handoff_relevant_activity_count_since(
        git_repo, handoff.stat().st_mtime
    )

    assert count == 3


def test_grok_tool_names_are_handoff_relevant():
    assert sessions.activity_is_handoff_relevant(
        "search_replace", "src/a.py")
    assert sessions.activity_is_handoff_relevant(
        "run_terminal_command", "git commit -m 'change'")
    assert not sessions.activity_is_handoff_relevant(
        "run_terminal_command", "git status --short --branch")
    assert not sessions.activity_is_handoff_relevant(
        "run_terminal_command", "python3 -m pytest -q")


@pytest.mark.parametrize("tool", ["exec_command", "shell_command"])
def test_codex_shell_tool_names_preserve_read_only_commands(tool):
    assert not sessions.activity_is_handoff_relevant(
        tool, "git status --short --branch")
    assert not sessions.activity_is_handoff_relevant(
        tool, "sed -n '1,40p' README.md")


@pytest.mark.parametrize(
    ("tool", "command"),
    [
        ("exec_command", "cat README.md > copy.txt"),
        ("shell_command", "git status && touch changed.txt"),
        ("Bash", "git log --oneline | tee log.txt"),
        ("run_terminal_command", "rg -n TODO . ; touch changed.txt"),
    ],
)
def test_shell_control_operators_make_read_only_prefixes_relevant(
        tool, command):
    assert sessions.activity_is_handoff_relevant(tool, command)


@pytest.mark.parametrize(
    "command",
    [
        "rg -n 'todo|fixme' tests",
        "sed -n '/one;two/p' README.md",
    ],
)
def test_quoted_shell_metacharacters_preserve_read_only_commands(command):
    assert not sessions.activity_is_handoff_relevant(
        "exec_command", command)


def test_clean_resume_reports_no_false_crash(git_repo):
    _init(git_repo)
    sessions.claim_session(git_repo, "test")
    sessions.wrap(git_repo, "clean end", "test")
    previous, _record = sessions.claim_session(git_repo, "test")
    recap = sessions.build_recap(git_repo, runtime_record=previous)
    assert not any("active session" in s for s in recap["crash_signals"])


def test_legacy_idless_runtime_record_remains_usable(git_repo):
    _init(git_repo)
    legacy = {
        "status": "active",
        "agent": "claude",
        "host": "legacy-host",
        "pid": 42,
        "started_at": "2026-09-08T11:00:00Z",
        "updated_at": "2026-09-08T11:00:00Z",
    }
    write_json_atomic(runtime_dir(git_repo, create=True) / "session.json",
                      legacy)

    recap = sessions.build_recap(git_repo)
    assert any("runtime marker" in item for item in recap["runtime_notes"])
    assert not any("runtime marker" in item
                   for item in recap["crash_signals"])

    sessions.record_activity(git_repo, "Edit", "src/legacy.py")
    active = sessions.load_runtime_session(git_repo)
    assert "session_id" not in active
    assert active["updated_at"] != legacy["updated_at"]

    assert sessions.close_runtime_session(
        git_repo, "ended", session_id=None)
    ended = sessions.load_runtime_session(git_repo)
    assert ended["status"] == "ended"
    assert "session_id" not in ended


@pytest.mark.parametrize("operation", ["wrap", "close"])
def test_project_level_close_operations_close_owned_current_marker(
        git_repo, operation):
    _init(git_repo)
    sessions.claim_session(git_repo, "codex", session_id="hook-a")

    if operation == "wrap":
        sessions.wrap(git_repo, "wrapped", "codex")
    else:
        sessions.close_only(git_repo, "codex")

    record = sessions.load_runtime_session(git_repo)
    assert record["status"] == "closed"
    assert record["session_id"] == "hook-a"


@pytest.mark.parametrize(
    ("marker", "label", "is_directory"),
    [
        ("MERGE_HEAD", "merge", False),
        ("rebase-merge", "rebase", True),
        ("CHERRY_PICK_HEAD", "cherry-pick", False),
    ],
)
def test_operation_metadata_in_ordinary_repository(
        git_repo, marker, label, is_directory):
    metadata = subprocess.check_output(
        ["git", "rev-parse", "--git-path", marker], cwd=str(git_repo)
    ).decode("utf-8").strip()
    path = git_repo / metadata
    if is_directory:
        path.mkdir(parents=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("in progress\n", encoding="utf-8")

    assert gitutil.in_progress_operation(git_repo) == label


def test_merge_conflict_in_linked_worktree_is_reported(git_repo):
    conflict = git_repo / "conflict.txt"
    conflict.write_text("base\n", encoding="utf-8")
    _commit_all(git_repo, "base")
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=str(git_repo)
    ).decode("utf-8").strip()
    subprocess.run(["git", "branch", "topic"], cwd=str(git_repo), check=True)

    conflict.write_text("main\n", encoding="utf-8")
    _commit_all(git_repo, "main change")

    linked = git_repo.parent / (git_repo.name + "-linked")
    created = _run_git(git_repo, "worktree", "add", "-q", str(linked),
                       "topic")
    if created.returncode:
        pytest.skip(
            "git worktree unavailable: %s"
            % created.stderr.decode("utf-8", "replace").strip())
    assert (linked / ".git").is_file()

    linked_conflict = linked / "conflict.txt"
    linked_conflict.write_text("topic\n", encoding="utf-8")
    _commit_all(linked, "topic change")
    merged = _run_git(linked, "merge", "--no-edit", branch)
    assert merged.returncode != 0
    marker = subprocess.check_output(
        ["git", "rev-parse", "--git-path", "MERGE_HEAD"], cwd=str(linked)
    ).decode("utf-8").strip()
    marker_path = linked / marker
    assert marker_path.exists()

    assert gitutil.in_progress_operation(linked) == "merge"


def test_handoff_commit_is_derived_without_a_checkpoint_loop(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    update_front_matter(handoff, {"last_commit": "stale123"})
    _commit_all(git_repo, "initial handoff")

    initial_head = gitutil.head_sha(git_repo)
    recap = sessions.build_recap(git_repo)
    assert recap["handoff"]["last_commit"] == initial_head
    assert not any("commit(s) exist" in s for s in recap["crash_signals"])

    (git_repo / "work.txt").write_text("done\n", encoding="utf-8")
    _commit_all(git_repo, "later work")
    signals = sessions.detect_crash_signals(git_repo)
    assert any("commit(s) exist" in s for s in signals)

    sessions.checkpoint(git_repo, "covered later work", "test")
    meta, _body = parse_front_matter(
        handoff.read_text(encoding="utf-8"))
    assert "last_commit" not in meta
    signals = sessions.detect_crash_signals(git_repo)
    assert not any("commit(s) exist" in s for s in signals)

    _commit_all(git_repo, "checkpoint")
    recap = sessions.build_recap(git_repo)
    assert recap["handoff"]["last_commit"] == gitutil.head_sha(git_repo)
    assert not any("commit(s) exist" in s for s in recap["crash_signals"])


def test_wrap_and_close_remove_legacy_last_commit(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"

    update_front_matter(handoff, {"last_commit": "legacy"})
    sessions.wrap(git_repo, "wrapped", "test")
    meta, _body = parse_front_matter(handoff.read_text(encoding="utf-8"))
    assert "last_commit" not in meta

    update_front_matter(handoff, {"last_commit": "legacy"})
    sessions.close_only(git_repo, "test")
    meta, _body = parse_front_matter(handoff.read_text(encoding="utf-8"))
    assert "last_commit" not in meta


def test_wrap_closes_and_flags_unmentioned_dirty(git_repo):
    _init(git_repo)
    sessions.claim_session(git_repo, "test")
    (git_repo / "mystery.py").write_text("x = 1\n", encoding="utf-8")
    report = sessions.wrap(git_repo, "did things", "test")
    assert any("mystery.py" in w for w in report["warnings"])
    meta, _, _ = sessions.handoff_meta(git_repo)
    assert meta["session_status"] == "closed"
    progress = (state_dir(git_repo) / "PROGRESS.md").read_text(encoding="utf-8")
    assert "did things" in progress
    runtime = json.loads((runtime_dir(git_repo) / "session.json")
                         .read_text(encoding="utf-8"))
    assert runtime.get("status") == "closed"


def test_progress_is_newest_first(git_repo):
    _init(git_repo)
    sessions.append_progress(git_repo, "entry-one", "t")
    sessions.append_progress(git_repo, "entry-two", "t")
    text = (state_dir(git_repo) / "PROGRESS.md").read_text(encoding="utf-8")
    assert text.index("entry-two") < text.index("entry-one")
