import json
import os
import time

from project_steward import sessions
from project_steward.paths import runtime_dir, state_dir
from project_steward.scaffold import apply_plan, plan_files


def _init(repo):
    plan, mapping = plan_files(repo, {"project_name": "Demo"})
    apply_plan(repo, plan, mapping)


def test_resume_never_dirties_committed_files(git_repo):
    _init(git_repo)
    handoff = state_dir(git_repo) / "HANDOFF.md"
    before = handoff.read_text(encoding="utf-8")
    sessions.claim_session(git_repo, "test")
    recap = sessions.build_recap(git_repo)
    assert handoff.read_text(encoding="utf-8") == before
    assert recap["handoff"]["session_status"] == "closed"
    assert (runtime_dir(git_repo) / "session.json").is_file()


def test_crash_detection_from_activity_and_runtime(git_repo):
    _init(git_repo)
    sessions.claim_session(git_repo, "test")
    # Simulate work after the handoff was last written.
    handoff = state_dir(git_repo) / "HANDOFF.md"
    past = time.time() - 3600
    os.utime(str(handoff), (past, past))
    sessions.record_activity(git_repo, "Edit", "train.py")
    signals = sessions.detect_crash_signals(git_repo)
    assert any("active session" in s for s in signals)
    assert any("AFTER the last HANDOFF.md" in s for s in signals)


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
