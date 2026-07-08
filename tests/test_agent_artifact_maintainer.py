import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "publish_agent_artifact_pr.py"


def _flat(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    return " ".join(text.split())


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _git(cwd, *args):
    subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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


def test_publish_script_dry_run_copies_artifact_to_target_checkout(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "dist" / "demo-skill"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("demo skill\n", encoding="utf-8")
    target = tmp_path / "agent-skills"
    target.mkdir()
    manifest = project / "agent-artifacts.json"
    _write_json(
        manifest,
        {
            "artifacts": [
                {
                    "name": "demo-skill",
                    "kind": "skill",
                    "build_command": "",
                    "source_path": "dist/demo-skill",
                    "target_repo": "git@github.com:example/agent-skills.git",
                    "target_path": "skills/demo-skill",
                    "base_branch": "main",
                }
            ]
        },
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
    assert (target / "skills" / "demo-skill" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "demo skill\n"
    assert "DRY RUN" in result.stdout


def test_publish_script_rejects_unsafe_target_path(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "dist" / "demo-skill"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("demo skill\n", encoding="utf-8")
    target = tmp_path / "agent-skills"
    target.mkdir()
    manifest = project / "agent-artifacts.json"
    _write_json(
        manifest,
        {
            "artifacts": [
                {
                    "name": "demo-skill",
                    "kind": "skill",
                    "build_command": "",
                    "source_path": "dist/demo-skill",
                    "target_repo": "git@github.com:example/agent-skills.git",
                    "target_path": "../outside",
                    "base_branch": "main",
                }
            ]
        },
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


def test_publish_script_requires_target_repo_noninteractive(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "dist" / "demo-skill"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("demo skill\n", encoding="utf-8")
    target = tmp_path / "agent-skills"
    target.mkdir()
    manifest = project / "agent-artifacts.json"
    _write_json(
        manifest,
        {
            "artifacts": [
                {
                    "name": "demo-skill",
                    "kind": "skill",
                    "build_command": "",
                    "source_path": "dist/demo-skill",
                    "target_path": "skills/demo-skill",
                    "base_branch": "main",
                }
            ]
        },
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
    assert "target_repo" in result.stderr


def test_publish_script_skips_pr_when_copy_makes_no_changes(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "dist" / "demo-skill"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("demo skill\n", encoding="utf-8")

    origin = tmp_path / "agent-skills.git"
    _git(tmp_path, "init", "--bare", str(origin))
    target = tmp_path / "agent-skills"
    _git(tmp_path, "clone", str(origin), str(target))
    _git(target, "checkout", "-b", "main")
    _git(target, "config", "user.email", "test@example.invalid")
    _git(target, "config", "user.name", "Test User")
    existing = target / "skills" / "demo-skill"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("demo skill\n", encoding="utf-8")
    _git(target, "add", "skills/demo-skill/SKILL.md")
    _git(target, "commit", "-m", "seed demo skill")
    _git(target, "push", "-u", "origin", "main")

    manifest = project / "agent-artifacts.json"
    _write_json(
        manifest,
        {
            "artifacts": [
                {
                    "name": "demo-skill",
                    "kind": "skill",
                    "build_command": "",
                    "source_path": "dist/demo-skill",
                    "target_repo": str(origin),
                    "target_path": "skills/demo-skill",
                    "base_branch": "main",
                }
            ]
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--artifact",
            "demo-skill",
            "--target-checkout",
            str(target),
            "--branch",
            "publish/demo-skill/test",
            "--non-interactive",
        ],
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert "No changes after copy; no PR created." in result.stdout
