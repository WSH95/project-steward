import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "publish_agent_artifact_pr.py"


def _flat(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    return " ".join(text.split())


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load_publish_module():
    spec = importlib.util.spec_from_file_location(
        "project_steward_artifact_publisher_test", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(cwd, *args):
    return subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def _init_target(path):
    path.mkdir()
    _git(path, "init")
    _git(path, "checkout", "-b", "main")
    _git(path, "config", "user.email", "test@example.invalid")
    _git(path, "config", "user.name", "Test User")
    return path


def _manifest(project, target_path="skills/demo-skill", target_repo=None):
    manifest = project / "agent-artifacts.json"
    artifact = {
        "name": "demo-skill",
        "kind": "skill",
        "build_command": "",
        "source_path": "dist/demo-skill",
        "target_path": target_path,
        "base_branch": "main",
    }
    if target_repo is not None:
        artifact["target_repo"] = target_repo
    _write_json(manifest, {"artifacts": [artifact]})
    return manifest


def _project_with_source(tmp_path, text="demo skill new\n"):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "dist" / "demo-skill"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(text, encoding="utf-8")
    return project


def _seed_target(target, artifact_text="demo skill old\n"):
    artifact = target / "skills" / "demo-skill"
    artifact.mkdir(parents=True)
    (artifact / "SKILL.md").write_text(artifact_text, encoding="utf-8")
    (target / "unrelated.txt").write_text("unchanged\n", encoding="utf-8")
    _git(target, "add", ".")
    _git(target, "commit", "-m", "seed target")


def test_agent_artifact_maintainer_skill_contract():
    skill = _flat("plugin-src/skills/agent-artifact-maintainer/SKILL.md")

    expected_phrases = [
        "single canonical source",
        "generated dist",
        "project-local publish script",
        "target repository",
        "agent-skills",
        "agent-plugins",
        "Never push without explicit approval",
        "commit semantic changes automatically",
    ]
    for phrase in expected_phrases:
        assert phrase in skill


def test_project_artifact_manifest_points_to_generated_payload():
    manifest = json.loads(
        (ROOT / "agent-artifacts.json").read_text(encoding="utf-8")
    )
    artifacts = {item["name"]: item for item in manifest["artifacts"]}

    artifact = artifacts["project-steward-plugin"]
    assert artifact["kind"] == "plugin"
    assert artifact["source_path"] == "dist/project-steward"
    assert artifact["target_path"] == "project-steward"
    assert artifact["target_repo"] == "git@github.com:WSH95/agent-plugins.git"
    assert "tools/build_plugin_payloads.py" in artifact["build_command"]


def test_publish_script_dry_run_previews_without_mutating_target_checkout(
    tmp_path,
):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    tracked = target / "unrelated.txt"
    stat = tracked.stat()
    os.utime(
        str(tracked),
        ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000),
    )
    index = target / ".git" / "index"
    index_before = index.read_bytes()
    head_before = _git(target, "rev-parse", "HEAD")
    branch_before = _git(target, "branch", "--show-current")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert (target / "skills" / "demo-skill" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "demo skill old\n"
    assert index.read_bytes() == index_before
    assert _git(target, "rev-parse", "HEAD") == head_before
    assert _git(target, "branch", "--show-current") == branch_before
    assert "DRY RUN" in result.stdout
    assert "diff --git" in result.stdout
    assert "+demo skill new" in result.stdout


@pytest.mark.parametrize("target_path", ["../outside", ".git/task-preview"])
def test_publish_script_rejects_unsafe_target_path(tmp_path, target_path):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    (target / "README.md").write_text("target\n", encoding="utf-8")
    _git(target, "add", "README.md")
    _git(target, "commit", "-m", "seed target")
    manifest = _manifest(
        project,
        target_path=target_path,
        target_repo="git@github.com:example/agent-skills.git",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
    assert "unsafe target_path" in result.stderr


def test_publish_script_rejects_symlinked_artifact_destination(tmp_path):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    real_skills = target / "real-skills"
    existing = real_skills / "demo-skill"
    existing.mkdir(parents=True)
    note = existing / "local-note.txt"
    note.write_text("keep me\n", encoding="utf-8")
    try:
        (target / "skills").symlink_to(real_skills, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    _git(target, "add", ".")
    _git(target, "commit", "-m", "seed symlink target")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
    assert "symlink" in result.stderr
    assert note.read_text(encoding="utf-8") == "keep me\n"


def test_publish_script_requires_target_repo_noninteractive(tmp_path):
    project = _project_with_source(tmp_path, text="demo skill\n")
    target = _init_target(tmp_path / "agent-skills")
    (target / "README.md").write_text("target\n", encoding="utf-8")
    _git(target, "add", "README.md")
    _git(target, "commit", "-m", "seed target")
    manifest = _manifest(project)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
    assert "target_repo" in result.stderr


def test_publish_script_dry_run_reports_saved_repo_without_writing_manifest(
    tmp_path,
):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    manifest = _manifest(project)
    manifest_before = manifest.read_bytes()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-repo",
            "git@github.com:example/agent-skills.git",
            "--save-target-repo",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert manifest.read_bytes() == manifest_before
    assert "would save target_repo" in result.stdout


def test_publish_script_dry_run_reports_when_artifact_is_unchanged(tmp_path):
    project = _project_with_source(tmp_path, text="demo skill\n")
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target, artifact_text="demo skill\n")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert "no artifact changes proposed" in result.stdout


def test_publish_script_rejects_dirty_target_before_preview_copy(tmp_path):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    note = target / "local-note.txt"
    note.write_text("do not remove\n", encoding="utf-8")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
    assert "not clean" in result.stderr
    assert note.read_text(encoding="utf-8") == "do not remove\n"
    assert (target / "skills" / "demo-skill" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "demo skill old\n"


def test_publish_script_rejects_ignored_file_inside_artifact(
    tmp_path, monkeypatch, capsys
):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    (target / ".gitignore").write_text("*.local\n", encoding="utf-8")
    _seed_target(target)
    note = target / "skills" / "demo-skill" / "notes.local"
    note.write_text("keep me\n", encoding="utf-8")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    head_before = _git(target, "rev-parse", "HEAD")
    branch_before = _git(target, "branch", "--show-current")
    module = _load_publish_module()
    remote_calls = _mock_remote_commands(module, monkeypatch)

    result = module.main(
        [
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ]
    )

    assert result == 2
    assert "ignored local" in capsys.readouterr().err
    assert note.read_text(encoding="utf-8") == "keep me\n"
    assert _git(target, "rev-parse", "HEAD") == head_before
    assert _git(target, "branch", "--show-current") == branch_before
    assert remote_calls == []


def test_publish_script_allows_ignored_file_outside_artifact(tmp_path):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    (target / ".gitignore").write_text("*.local\n", encoding="utf-8")
    _seed_target(target)
    note = target / "notes.local"
    note.write_text("keep me\n", encoding="utf-8")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--dry-run",
            "--target-checkout",
            str(target),
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert note.read_text(encoding="utf-8") == "keep me\n"


def _mock_remote_commands(module, monkeypatch, after_add=None):
    real_run = module._run
    remote_calls = []

    def run(command, cwd, *args, **kwargs):
        if isinstance(command, list):
            if command[:2] in (["git", "pull"], ["git", "push"]):
                remote_calls.append(command)
                return ""
            if command[:3] == ["gh", "pr", "create"]:
                remote_calls.append(command)
                return ""
        result = real_run(command, cwd, *args, **kwargs)
        if (
            after_add is not None
            and isinstance(command, list)
            and command[:2] == ["git", "add"]
        ):
            after_add(module, Path(cwd))
        return result

    monkeypatch.setattr(module, "_run", run)
    return remote_calls


def test_publish_script_rejects_unrelated_staged_work_before_branch_change(
    tmp_path, monkeypatch
):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    (target / "unrelated.txt").write_text("staged local work\n", encoding="utf-8")
    _git(target, "add", "unrelated.txt")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    head_before = _git(target, "rev-parse", "HEAD")
    module = _load_publish_module()
    remote_calls = _mock_remote_commands(module, monkeypatch)

    result = module.main(
        [
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ]
    )

    assert result == 2
    assert _git(target, "branch", "--show-current") == "main"
    assert _git(target, "rev-parse", "HEAD") == head_before
    assert _git(target, "diff", "--cached", "--name-only") == "unrelated.txt"
    assert remote_calls == []


def test_publish_script_checks_index_scope_before_commit(tmp_path, monkeypatch):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    head_before = _git(target, "rev-parse", "HEAD")
    module = _load_publish_module()

    def stage_unrelated(mod, checkout):
        (checkout / "unrelated.txt").write_text(
            "injected staged work\n", encoding="utf-8"
        )
        _git(checkout, "add", "unrelated.txt")

    remote_calls = _mock_remote_commands(
        module, monkeypatch, after_add=stage_unrelated
    )

    result = module.main(
        [
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ]
    )

    assert result == 2
    assert _git(target, "rev-parse", "HEAD") == head_before
    assert "unrelated.txt" in _git(target, "diff", "--cached", "--name-only")
    assert not any(call[:2] == ["git", "push"] for call in remote_calls)
    assert not any(call[:3] == ["gh", "pr", "create"] for call in remote_calls)


def test_publish_script_commits_only_the_artifact(tmp_path, monkeypatch):
    project = _project_with_source(tmp_path)
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target)
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    module = _load_publish_module()
    _mock_remote_commands(module, monkeypatch)

    result = module.main(
        [
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ]
    )

    assert result == 0
    assert _git(target, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == (
        "skills/demo-skill/SKILL.md"
    )
    assert (target / "unrelated.txt").read_text(encoding="utf-8") == "unchanged\n"
    assert _git(target, "status", "--porcelain") == ""


def test_publish_script_skips_pr_when_copy_makes_no_changes(
    tmp_path, monkeypatch, capsys
):
    project = _project_with_source(tmp_path, text="demo skill\n")
    target = _init_target(tmp_path / "agent-skills")
    _seed_target(target, artifact_text="demo skill\n")
    manifest = _manifest(
        project, target_repo="git@github.com:example/agent-skills.git"
    )
    module = _load_publish_module()
    remote_calls = _mock_remote_commands(module, monkeypatch)

    result = module.main(
        [
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ]
    )

    assert result == 0
    assert "No changes after copy; no PR created." in capsys.readouterr().out
    assert not any(call[:2] == ["git", "push"] for call in remote_calls)
    assert not any(call[:3] == ["gh", "pr", "create"] for call in remote_calls)
