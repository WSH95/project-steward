import os
import subprocess

import pytest

from project_steward.cli import main
from project_steward.paths import (UnsafePathError, assert_inside_root,
                                   find_project_root, state_dir)


def _git_init(path):
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True)


def _initialize(repo):
    assert main(["init", "--root", str(repo), "--yes",
                 "--no-codex-hooks"]) == 0


def test_nested_git_repository_does_not_modify_parent_project(
        git_repo, monkeypatch, capsys):
    _initialize(git_repo)
    progress = state_dir(git_repo) / "PROGRESS.md"
    before = progress.read_bytes()
    nested = git_repo / "nested"
    _git_init(nested)
    child = nested / "src"
    child.mkdir()
    monkeypatch.chdir(str(child))

    rc = main(["checkpoint", "--note", "must stay in nested repo"])

    assert rc == 1
    assert "Not a Project Steward project" in capsys.readouterr().out
    assert progress.read_bytes() == before


def test_explicit_root_can_select_managed_parent_from_nested_repository(
        git_repo, monkeypatch):
    _initialize(git_repo)
    nested = git_repo / "nested"
    _git_init(nested)
    child = nested / "src"
    child.mkdir()
    monkeypatch.chdir(str(child))

    rc = main(["checkpoint", "--root", str(git_repo),
               "--note", "intentional parent update"])

    assert rc == 0
    progress = (state_dir(git_repo) / "PROGRESS.md").read_text(
        encoding="utf-8")
    assert "intentional parent update" in progress


def test_discovery_from_managed_repository_subdirectory_finds_repository(
        git_repo):
    _initialize(git_repo)
    child = git_repo / "src" / "package"
    child.mkdir(parents=True)

    assert find_project_root(child) == git_repo


def test_assert_inside_root_accepts_normal_paths(tmp_path):
    target = tmp_path / ".project-steward" / "HANDOFF.md"
    assert assert_inside_root(tmp_path, target, "handoff") == target


def test_assert_inside_root_rejects_escape(tmp_path):
    with pytest.raises(UnsafePathError):
        assert_inside_root(tmp_path, tmp_path.parent / "elsewhere.md", "x")


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlinks")
def test_assert_inside_root_rejects_symlinked_ancestor(tmp_path):
    outside = tmp_path.parent / "outside-steward-dir"
    outside.mkdir(exist_ok=True)
    link = tmp_path / ".project-steward"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(UnsafePathError):
        assert_inside_root(tmp_path, link / "PROGRESS.md", "progress")
