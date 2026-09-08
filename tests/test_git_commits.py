import subprocess

from project_steward import gitutil
from project_steward.cli import main


def git(repo, *args):
    return subprocess.check_output(["git"] + list(args), cwd=str(repo))


def test_commit_refuses_unrelated_index_without_changing_it(git_repo):
    (git_repo / "feature.py").write_text("user work\n", encoding="utf-8")
    (git_repo / "notes.md").write_text("agent notes\n", encoding="utf-8")
    git(git_repo, "add", "feature.py")
    before = git(git_repo, "diff", "--cached", "--binary")
    rc, message = gitutil.stage_and_commit(git_repo, "chore: notes", ["notes.md"])
    assert rc != 0
    assert "feature.py" in message and "staged" in message
    assert git(git_repo, "diff", "--cached", "--binary") == before
    assert gitutil.head_sha(git_repo) == ""


def test_commit_refuses_both_sides_of_unrelated_staged_rename(git_repo):
    (git_repo / "old.md").write_text("user work\n", encoding="utf-8")
    git(git_repo, "add", "old.md")
    git(git_repo, "commit", "-qm", "initial")
    git(git_repo, "mv", "old.md", "new.md")
    before = gitutil.head_sha(git_repo)
    rc, _ = gitutil.stage_and_commit(git_repo, "chore: notes", ["new.md"])
    assert rc != 0
    assert gitutil.head_sha(git_repo) == before


def test_commit_uses_literal_paths_and_preserves_unstaged_work(git_repo):
    (git_repo / "notes[1].md").write_text("agent notes\n", encoding="utf-8")
    (git_repo / "notes1.md").write_text("user notes\n", encoding="utf-8")
    rc, message = gitutil.stage_and_commit(git_repo, "chore: notes", ["notes[1].md"])
    assert rc == 0, message
    assert git(git_repo, "ls-tree", "--name-only", "HEAD") == b"notes[1].md\n"
    assert (git_repo / "notes1.md").read_text(encoding="utf-8") == "user notes\n"


def test_commit_skips_absent_optional_paths(git_repo):
    (git_repo / "notes.md").write_text("agent notes\n", encoding="utf-8")
    rc, message = gitutil.stage_and_commit(git_repo, "chore: notes",
                                          ["notes.md", "absent.md"])
    assert rc == 0, message


def test_wrap_returns_commit_failure(git_repo, monkeypatch, capsys):
    main(["init", "--root", str(git_repo), "--yes"])
    git(git_repo, "config", "user.name", "")
    git(git_repo, "config", "user.email", "")
    for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME",
                 "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(name, raising=False)
    rc = main(["wrap", "--root", str(git_repo), "--summary", "ready", "--commit"])
    assert rc != 0
    output = capsys.readouterr().out
    assert "commit failed" in output.lower()
    assert gitutil.head_sha(git_repo) == ""


def test_auto_policy_does_not_make_cli_commit_implicitly(git_repo):
    main(["init", "--root", str(git_repo), "--yes"])
    main(["checkpoint", "--root", str(git_repo), "--note", "work"])
    main(["wrap", "--root", str(git_repo), "--summary", "ready"])
    assert gitutil.head_sha(git_repo) == ""
