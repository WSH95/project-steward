import json
import os
import subprocess
from pathlib import Path

import pytest

from project_steward import migrate as migrate_module
from project_steward.cli import main
from project_steward.managed_blocks import find_legacy_blocks
from project_steward.migrate import (apply_migration, migrate,
                                     parse_legacy_config, plan_migration,
                                     render_config_toml)
from project_steward.paths import state_dir
from project_steward.scaffold import apply_plan, plan_files
from project_steward.tomlmini import loads


def _make_legacy(repo):
    legacy = repo / ".projectforge"
    (legacy / "journal").mkdir(parents=True)
    (legacy / "PLAN.md").write_text(
        "# Plan (Projectforge)\n- [ ] task in .projectforge/PLAN.md\n",
        encoding="utf-8")
    (legacy / "HANDOFF.md").write_text(
        "---\nsession_status: closed\nlast_commit: old123\n---\n\n"
        "# Handoff\n\n## Now\nok\n",
        encoding="utf-8")
    (legacy / "config").write_text(
        'AUTO_HANDOFF_MODE=remind\nAUTO_HANDOFF_COOLDOWN_MIN=30\n'
        'COMMIT_POLICY=ask\n', encoding="utf-8")
    (legacy / "journal" / "heartbeat").write_text("123", encoding="utf-8")
    (legacy / "unknown.bin").write_bytes(b"\x00\xfflegacy\r\n")
    try:
        os.symlink("PLAN.md", str(legacy / "plan-link"))
    except OSError:
        # Windows test accounts may not have symlink privileges.
        pass
    (repo / "AGENTS.md").write_text(
        "# Proj\n\nUser prose.\n\n"
        "## Agent session protocol (Projectforge)\n\nold protocol text\n\n"
        "## Other user section\nkeep me\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".projectforge/journal/\n",
                                     encoding="utf-8")


def _visible_tree(root):
    """Capture fixture state without Git internals or filesystem metadata."""
    captured = {}
    for path in sorted(Path(root).rglob("*")):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == ".git":
            continue
        key = rel.as_posix()
        if path.is_symlink():
            captured[key] = ("link", os.readlink(str(path)))
        elif path.is_dir():
            captured[key] = ("dir", None)
        else:
            captured[key] = ("file", path.read_bytes())
    return captured


def _backup_attempts(repo):
    backup_root = state_dir(repo) / "migration-backup-projectforge"
    if not backup_root.is_dir():
        return []
    return sorted(
        path for path in backup_root.iterdir()
        if path.is_dir() and path.name.startswith("attempt-")
    )


def test_full_migration(git_repo):
    _make_legacy(git_repo)
    original_agents = (git_repo / "AGENTS.md").read_bytes()
    original_gitignore = (git_repo / ".gitignore").read_bytes()
    old_backup = state_dir(git_repo) / "migration-backup-projectforge/old-attempt"
    old_backup.mkdir(parents=True)
    (old_backup / "sentinel").write_text("older backup", encoding="utf-8")
    report = migrate(git_repo, project_name="Demo")
    assert report["ok"]
    sdir = state_dir(git_repo)
    assert not (git_repo / ".projectforge").exists()
    attempts = _backup_attempts(git_repo)
    assert len(attempts) == 1
    backup = attempts[0]
    assert (backup / ".projectforge/PLAN.md").is_file()
    assert (backup / ".projectforge/unknown.bin").read_bytes() == b"\x00\xfflegacy\r\n"
    if (backup / ".projectforge/plan-link").exists():
        assert (backup / ".projectforge/plan-link").is_symlink()
        assert os.readlink(str(backup / ".projectforge/plan-link")) == "PLAN.md"
    originals = backup / "original-instructions"
    assert (backup / ".gitignore").read_bytes() == b"*\n"
    assert (originals / "AGENTS.md").read_bytes() == original_agents
    assert (originals / ".gitignore").read_bytes() == original_gitignore
    assert (old_backup / "sentinel").read_text(encoding="utf-8") == "older backup"
    plan = (sdir / "PLAN.md").read_text(encoding="utf-8")
    assert ".project-steward/" in plan
    assert ".projectforge/" not in plan
    assert "Projectforge" in plan  # product names in user prose survive
    cfg = loads((sdir / "config.toml").read_text(encoding="utf-8"))
    assert cfg["session"]["auto_handoff_mode"] == "remind"
    assert cfg["session"]["auto_handoff_cooldown_min"] == 30
    agents = (git_repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Agent session protocol (Projectforge)" not in agents
    assert "PROJECT-STEWARD:BEGIN agent-session-protocol" in agents
    assert "keep me" in agents and "User prose." in agents
    assert find_legacy_blocks(agents) == []
    gi = (git_repo / ".gitignore").read_text(encoding="utf-8")
    assert ".projectforge" not in gi
    assert ".project-steward/runtime/" in gi
    assert (sdir / "runtime" / "journal-legacy" / "heartbeat").is_file()
    handoff = (sdir / "HANDOFF.md").read_text(encoding="utf-8")
    assert "last_commit:" not in handoff
    assert any("obsolete HANDOFF.md" in note for note in report["notes"])


def test_marked_protocol_is_replaced_as_a_span_and_user_prose_survives_reinit(
        git_repo):
    _make_legacy(git_repo)
    agents_path = git_repo / "AGENTS.md"
    agents_path.write_text(
        "# Project\n\nUser preface.\n\n"
        "<!-- PROJECTFORGE:BEGIN legacy-session -->\n"
        "## Agent session protocol (Projectforge)\n\n"
        "Old generated protocol.\n"
        "<!-- PROJECTFORGE:END legacy-session -->\n\n"
        "User prose after the managed block.\n",
        encoding="utf-8",
    )

    report = migrate(git_repo)
    assert report["ok"], report
    migrated = agents_path.read_text(encoding="utf-8")
    assert migrated.count(
        "<!-- PROJECT-STEWARD:BEGIN agent-session-protocol -->") == 1
    assert migrated.count(
        "<!-- PROJECT-STEWARD:END agent-session-protocol -->") == 1
    assert "Old generated protocol." not in migrated
    assert "User preface." in migrated
    assert "User prose after the managed block." in migrated

    scaffold_plan, mapping = plan_files(git_repo)
    apply_plan(git_repo, scaffold_plan, mapping)
    reinitialized = agents_path.read_text(encoding="utf-8")
    assert "User preface." in reinitialized
    assert "User prose after the managed block." in reinitialized
    assert reinitialized.count(
        "<!-- PROJECT-STEWARD:BEGIN agent-session-protocol -->") == 1
    assert reinitialized.count(
        "<!-- PROJECT-STEWARD:END agent-session-protocol -->") == 1


def test_unmarked_protocol_fallback_preserves_following_managed_block(
        git_repo):
    _make_legacy(git_repo)
    agents_path = git_repo / "AGENTS.md"
    agents_path.write_text(
        "# Project\n\n"
        "## Agent session protocol (Projectforge)\n\nOld protocol.\n\n"
        "<!-- PROJECTFORGE:BEGIN commands -->\n"
        "## Commands\n\n- Test: `custom-test`\n"
        "<!-- PROJECTFORGE:END commands -->\n\n"
        "## User section\n\nKeep this prose.\n",
        encoding="utf-8",
    )

    report = migrate(git_repo)

    assert report["ok"], report
    migrated = agents_path.read_text(encoding="utf-8")
    assert "<!-- PROJECT-STEWARD:BEGIN commands -->" in migrated
    assert "- Test: `custom-test`" in migrated
    assert "Keep this prose." in migrated


def test_migration_and_reinit_preserve_crlf_user_prose_bytes(git_repo):
    _make_legacy(git_repo)
    agents_path = git_repo / "AGENTS.md"
    agents_path.write_bytes(
        b"# Project\r\n\r\nUser preface.\r\n\r\n"
        b"<!-- PROJECTFORGE:BEGIN agent-session-protocol -->\r\n"
        b"## Agent session protocol (Projectforge)\r\n\r\n"
        b"Old generated protocol.\r\n"
        b"<!-- PROJECTFORGE:END agent-session-protocol -->\r\n\r\n"
        b"User prose after the managed block.\r\n"
    )

    report = migrate(git_repo)
    assert report["ok"], report
    migrated = agents_path.read_bytes()
    assert b"# Project\r\n\r\nUser preface.\r\n" in migrated
    assert b"\r\nUser prose after the managed block.\r\n" in migrated

    scaffold_plan, mapping = plan_files(git_repo)
    apply_plan(git_repo, scaffold_plan, mapping)
    reinitialized = agents_path.read_bytes()
    assert b"# Project\r\n\r\nUser preface.\r\n" in reinitialized
    assert b"\r\nUser prose after the managed block.\r\n" in reinitialized


@pytest.mark.parametrize("agents_text", [
    "<!-- PROJECTFORGE:BEGIN agent-session-protocol -->\nmissing end\n",
    (
        "<!-- PROJECTFORGE:BEGIN commands -->\none\n"
        "<!-- PROJECTFORGE:END commands -->\n"
        "<!-- PROJECTFORGE:BEGIN commands -->\ntwo\n"
        "<!-- PROJECTFORGE:END commands -->\n"
    ),
    (
        "<!-- PROJECTFORGE:BEGIN commands -->\n"
        "<!-- PROJECTFORGE:BEGIN agent-session-protocol -->\nnested\n"
        "<!-- PROJECTFORGE:END agent-session-protocol -->\n"
        "<!-- PROJECTFORGE:END commands -->\n"
    ),
])
def test_malformed_duplicate_or_nested_markers_fail_before_writes(
        git_repo, agents_text):
    _make_legacy(git_repo)
    (git_repo / "AGENTS.md").write_text(agents_text, encoding="utf-8")
    before = _visible_tree(git_repo)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "marker" in report["error"].lower()
    assert _visible_tree(git_repo) == before


def test_invalid_utf8_fails_preflight_without_writing(git_repo):
    _make_legacy(git_repo)
    (git_repo / ".projectforge/PLAN.md").write_bytes(b"plan\xff")
    before = _visible_tree(git_repo)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "utf-8" in report["error"].lower()
    assert _visible_tree(git_repo) == before


@pytest.mark.parametrize("config_text", [
    "AUTO_HANDOFF_COOLDOWN_MIN=not-a-number\n",
    "COMMIT_POLICY=sometimes\n",
])
def test_invalid_legacy_config_fails_preflight_without_writing(
        git_repo, config_text):
    _make_legacy(git_repo)
    (git_repo / ".projectforge/config").write_text(
        config_text, encoding="utf-8")
    before = _visible_tree(git_repo)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "config" in report["error"].lower()
    assert _visible_tree(git_repo) == before


def test_conflicting_destination_retains_legacy_and_steward_trees(git_repo):
    _make_legacy(git_repo)
    destination = state_dir(git_repo) / "PLAN.md"
    destination.parent.mkdir()
    destination.write_text("# Different plan\n\n- [ ] keep me\n", encoding="utf-8")
    before = _visible_tree(git_repo)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "conflict" in report["error"].lower()
    assert _visible_tree(git_repo) == before


@pytest.mark.parametrize("name, contents", [
    ("WORKFLOW.md", "# Existing custom workflow\n"),
    ("PROGRESS.md", "# Existing unrelated progress\n\nCustom entry.\n"),
])
def test_unrecognized_existing_generated_destination_is_a_conflict(
        git_repo, name, contents):
    _make_legacy(git_repo)
    target = state_dir(git_repo) / name
    target.parent.mkdir()
    target.write_text(contents, encoding="utf-8")
    before = _visible_tree(git_repo)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "conflict" in report["error"].lower()
    assert name in report["error"]
    assert _visible_tree(git_repo) == before


def test_apply_rechecks_preflight_inputs_before_starting_backup(git_repo):
    _make_legacy(git_repo)
    migration_plan = plan_migration(git_repo)
    assert migration_plan.ok
    legacy_plan = git_repo / ".projectforge/PLAN.md"
    legacy_plan.write_text("# Changed after preflight\n", encoding="utf-8")

    report = apply_migration(migration_plan)

    assert not report["ok"]
    assert "changed after preflight" in report["error"]
    assert legacy_plan.is_file()
    assert _backup_attempts(git_repo) == []


def test_apply_rechecks_destination_created_after_fresh_backup(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    destination = state_dir(git_repo) / "PLAN.md"
    concurrent_text = "# Concurrent plan\n\n- [ ] preserve me\n"
    real_fresh_backup = migrate_module._fresh_backup

    def create_destination_after_backup(plan):
        backup = real_fresh_backup(plan)
        destination.write_text(concurrent_text, encoding="utf-8")
        return backup

    monkeypatch.setattr(
        migrate_module, "_fresh_backup", create_destination_after_backup)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "changed after backup" in report["error"]
    assert (git_repo / ".projectforge").is_dir()
    assert destination.read_text(encoding="utf-8") == concurrent_text
    backup = _backup_attempts(git_repo)[0]
    assert (backup / ".projectforge/PLAN.md").is_file()


def test_apply_rechecks_destination_changed_after_fresh_backup(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    destination = state_dir(git_repo) / "PLAN.md"
    destination.parent.mkdir()
    destination.write_text(
        "# Plan (Projectforge)\n"
        "- [ ] task in .project-steward/PLAN.md\n",
        encoding="utf-8",
    )
    concurrent_text = "# Concurrent replacement\n\n- [ ] preserve me\n"
    real_fresh_backup = migrate_module._fresh_backup

    def change_destination_after_backup(plan):
        backup = real_fresh_backup(plan)
        destination.write_text(concurrent_text, encoding="utf-8")
        return backup

    monkeypatch.setattr(
        migrate_module, "_fresh_backup", change_destination_after_backup)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "changed after backup" in report["error"]
    assert (git_repo / ".projectforge").is_dir()
    assert destination.read_text(encoding="utf-8") == concurrent_text
    assert len(_backup_attempts(git_repo)) == 1


def test_apply_rechecks_destination_ancestor_after_fresh_backup(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    external = git_repo.parent / "late-backup-runtime"
    external.mkdir()
    runtime = state_dir(git_repo) / "runtime"
    real_fresh_backup = migrate_module._fresh_backup

    def link_runtime_after_backup(plan):
        backup = real_fresh_backup(plan)
        try:
            os.symlink(str(external), str(runtime), target_is_directory=True)
        except OSError:
            pytest.skip("test account cannot create directory symlinks")
        return backup

    monkeypatch.setattr(
        migrate_module, "_fresh_backup", link_runtime_after_backup)

    report = migrate(git_repo)

    assert not report["ok"]
    assert "changed after backup" in report["error"]
    assert (git_repo / ".projectforge").is_dir()
    assert list(external.iterdir()) == []
    assert len(_backup_attempts(git_repo)) == 1


def test_partial_backup_is_self_ignored_before_raw_copy(git_repo, monkeypatch):
    _make_legacy(git_repo)
    real_copytree = migrate_module.shutil.copytree

    def fail_during_backup(source, target, *args, **kwargs):
        target_path = Path(target)
        if target_path.name == ".projectforge" \
                and target_path.parent.name.startswith("attempt-"):
            target_path.mkdir(parents=True)
            (target_path / "partially-copied-secret").write_text(
                "raw legacy bytes", encoding="utf-8")
            raise OSError("simulated backup copy failure")
        return real_copytree(source, target, *args, **kwargs)

    monkeypatch.setattr(migrate_module.shutil, "copytree", fail_during_backup)

    report = migrate(git_repo)

    assert not report["ok"]
    assert (git_repo / ".projectforge").is_dir()
    status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=str(git_repo), check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    assert "migration-backup-projectforge" not in status


def test_backup_stays_ignored_after_original_instructions_are_copied(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    real_write = migrate_module.write_text_atomic
    first_destination = state_dir(git_repo) / "PLAN.md"

    def fail_before_destination_writes(path, text):
        if Path(path) == first_destination:
            raise OSError("simulated destination write failure")
        return real_write(path, text)

    monkeypatch.setattr(
        migrate_module, "write_text_atomic", fail_before_destination_writes)

    report = migrate(git_repo)

    assert not report["ok"]
    assert (git_repo / ".projectforge").is_dir()
    backup = _backup_attempts(git_repo)[0]
    assert (backup / ".gitignore").read_bytes() == b"*\n"
    assert (backup / "original-instructions/.gitignore").read_bytes() == \
        b".projectforge/journal/\n"
    status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=str(git_repo), check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    assert "migration-backup-projectforge" not in status


def test_fresh_backup_does_not_modify_existing_flat_backup_bytes(git_repo):
    _make_legacy(git_repo)
    backup_root = state_dir(git_repo) / "migration-backup-projectforge"
    (backup_root / "journal").mkdir(parents=True)
    (backup_root / ".gitignore").write_bytes(
        b"# raw legacy ignore\r\n.projectforge/journal/\r\n")
    (backup_root / "PLAN.md").write_bytes(b"# old raw plan\r\n")
    (backup_root / "journal/heartbeat").write_bytes(b"old-heartbeat\x00")
    old_snapshot = _visible_tree(backup_root)

    report = migrate(git_repo)

    assert report["ok"], report
    current = _visible_tree(backup_root)
    for rel, snapshot in old_snapshot.items():
        assert current[rel] == snapshot


def test_legacy_change_during_destination_writes_prevents_removal(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    real_write = migrate_module.write_text_atomic
    changed = {"done": False}

    def change_legacy_after_destination_write(path, text):
        real_write(path, text)
        if Path(path).name == "state.json" and not changed["done"]:
            changed["done"] = True
            legacy_plan = git_repo / ".projectforge/PLAN.md"
            legacy_plan.write_text(
                legacy_plan.read_text(encoding="utf-8")
                + "- [ ] task added during migration\n",
                encoding="utf-8",
            )

    monkeypatch.setattr(
        migrate_module, "write_text_atomic",
        change_legacy_after_destination_write,
    )

    report = migrate(git_repo)

    assert not report["ok"]
    assert (git_repo / ".projectforge").is_dir()
    assert "task added during migration" in (
        git_repo / ".projectforge/PLAN.md").read_text(encoding="utf-8")
    backup_plan = _backup_attempts(git_repo)[0] / ".projectforge/PLAN.md"
    assert "task added during migration" not in backup_plan.read_text(
        encoding="utf-8")


def test_gitignore_preserves_unrelated_crlf_lines_and_blank_space(git_repo):
    _make_legacy(git_repo)
    gitignore = git_repo / ".gitignore"
    original = (
        b"# User note mentioning .projectforge stays\r\n"
        b"custom/.projectforge/cache\r\n\r\n\r\n"
        b".projectforge/journal/\r\n"
    )
    gitignore.write_bytes(original)

    report = migrate(git_repo)

    assert report["ok"], report
    updated = gitignore.read_bytes()
    assert updated.startswith(
        b"# User note mentioning .projectforge stays\r\n"
        b"custom/.projectforge/cache\r\n\r\n\r\n"
    )
    assert b".projectforge/journal/" not in updated
    backup = _backup_attempts(git_repo)[0]
    assert (backup / "original-instructions/.gitignore").read_bytes() == original


def test_dry_run_reports_runtime_file_conflict_without_changes(
        git_repo, capsys):
    _make_legacy(git_repo)
    runtime = state_dir(git_repo) / "runtime"
    runtime.parent.mkdir()
    runtime.write_bytes(b"user runtime file\x00")
    before = _visible_tree(git_repo)

    assert main([
        "migrate", "--root", str(git_repo), "--dry-run", "--json",
    ]) == 1

    report = json.loads(capsys.readouterr().out)
    assert not report["ok"]
    assert "runtime" in report["error"]
    assert _visible_tree(git_repo) == before


def test_migration_rejects_symlinked_runtime_parent_without_external_write(
        git_repo):
    _make_legacy(git_repo)
    external = git_repo.parent / "external-runtime"
    external.mkdir()
    runtime = state_dir(git_repo) / "runtime"
    runtime.parent.mkdir()
    try:
        os.symlink(str(external), str(runtime), target_is_directory=True)
    except OSError:
        pytest.skip("test account cannot create directory symlinks")

    report = migrate(git_repo)

    assert not report["ok"]
    assert "symlink" in report["error"].lower()
    assert (git_repo / ".projectforge").is_dir()
    assert list(external.iterdir()) == []
    assert _backup_attempts(git_repo) == []


def test_apply_rechecks_runtime_parent_before_copying_journal(git_repo):
    _make_legacy(git_repo)
    state_dir(git_repo).mkdir()
    migration_plan = plan_migration(git_repo)
    assert migration_plan.ok, migration_plan.report()
    external = git_repo.parent / "late-external-runtime"
    external.mkdir()
    try:
        os.symlink(
            str(external), str(state_dir(git_repo) / "runtime"),
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("test account cannot create directory symlinks")

    report = apply_migration(migration_plan)

    assert not report["ok"]
    assert "changed after preflight" in report["error"]
    assert (git_repo / ".projectforge").is_dir()
    assert list(external.iterdir()) == []
    assert _backup_attempts(git_repo) == []


def test_interrupted_migration_retries_matching_outputs_once(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    real_rmtree = migrate_module.shutil.rmtree
    failed = {"once": False}

    def fail_legacy_removal_once(path):
        if Path(path) == git_repo / ".projectforge" and not failed["once"]:
            failed["once"] = True
            raise OSError("simulated interrupted removal")
        return real_rmtree(path)

    monkeypatch.setattr(migrate_module.shutil, "rmtree", fail_legacy_removal_once)
    first = migrate(git_repo)
    assert not first["ok"]
    assert (git_repo / ".projectforge").is_dir()
    assert len(_backup_attempts(git_repo)) == 1

    second = migrate(git_repo)
    assert second["ok"], second
    assert not (git_repo / ".projectforge").exists()
    assert len(_backup_attempts(git_repo)) == 2
    progress = (state_dir(git_repo) / "PROGRESS.md").read_text(encoding="utf-8")
    assert progress.count("Migrated Projectforge state to Project Steward") == 1


def test_interrupted_migration_rejects_new_conflicting_legacy_tasks(
        git_repo, monkeypatch):
    _make_legacy(git_repo)
    real_rmtree = migrate_module.shutil.rmtree

    def fail_legacy_removal(path):
        if Path(path) == git_repo / ".projectforge":
            raise OSError("simulated interrupted removal")
        return real_rmtree(path)

    monkeypatch.setattr(migrate_module.shutil, "rmtree", fail_legacy_removal)
    first = migrate(git_repo)
    assert not first["ok"]
    legacy_plan = git_repo / ".projectforge/PLAN.md"
    legacy_plan.write_text(
        legacy_plan.read_text(encoding="utf-8") + "- [ ] newly added task\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(migrate_module.shutil, "rmtree", real_rmtree)

    second = migrate(git_repo)

    assert not second["ok"]
    assert "conflict" in second["error"].lower()
    assert "newly added task" in legacy_plan.read_text(encoding="utf-8")
    assert "newly added task" not in (
        state_dir(git_repo) / "PLAN.md").read_text(encoding="utf-8")
    assert len(_backup_attempts(git_repo)) == 1


def test_cli_migrate_dry_run_reports_plan_and_changes_nothing(git_repo, capsys):
    _make_legacy(git_repo)
    before = _visible_tree(git_repo)

    assert main([
        "migrate", "--root", str(git_repo), "--dry-run",
    ]) == 0

    output = capsys.readouterr().out
    assert "migration plan" in output.lower()
    assert "AGENTS.md changes" in output
    assert ".projectforge/" in output
    assert _visible_tree(git_repo) == before


def test_cli_migrate_dry_run_reports_conflicts_with_other_planned_changes(
        git_repo, capsys):
    _make_legacy(git_repo)
    destination = state_dir(git_repo) / "PLAN.md"
    destination.parent.mkdir()
    destination.write_text("# Conflicting plan\n", encoding="utf-8")
    before = _visible_tree(git_repo)

    assert main([
        "migrate", "--root", str(git_repo), "--dry-run",
    ]) == 1

    output = capsys.readouterr().out
    assert "migration plan" in output.lower()
    assert "conflict" in output.lower()
    assert ".project-steward/HANDOFF.md" in output
    assert _visible_tree(git_repo) == before


def test_cli_migrate_preflights_and_shows_instruction_diff_before_confirmation(
        git_repo, monkeypatch, capsys):
    _make_legacy(git_repo)
    seen = {}

    def decline(_prompt):
        seen["output"] = capsys.readouterr().out
        return False

    monkeypatch.setattr("project_steward.cli._confirm", decline)
    before = _visible_tree(git_repo)

    assert main(["migrate", "--root", str(git_repo)]) == 1

    assert "AGENTS.md changes" in seen["output"]
    assert _visible_tree(git_repo) == before


def test_cli_yes_cannot_bypass_invalid_migration_preflight(
        git_repo, capsys):
    _make_legacy(git_repo)
    (git_repo / "AGENTS.md").write_text(
        "<!-- PROJECTFORGE:BEGIN commands -->\nbroken\n", encoding="utf-8")
    before = _visible_tree(git_repo)

    assert main([
        "migrate", "--root", str(git_repo), "--yes",
    ]) == 1

    assert "error:" in capsys.readouterr().out.lower()
    assert _visible_tree(git_repo) == before


def test_init_refuses_partial_steward_state_until_migration_preserves_policy(
        git_repo, capsys):
    _make_legacy(git_repo)
    legacy = git_repo / ".projectforge"
    (legacy / "config").write_text("COMMIT_POLICY=never\n", encoding="utf-8")
    (legacy / "PLAN.md").write_text(
        "# Real legacy plan\n\n- [ ] ship the real task\n", encoding="utf-8")
    partial = state_dir(git_repo)
    partial.mkdir()
    (partial / "interrupted-sentinel").write_text("keep", encoding="utf-8")
    before = _visible_tree(git_repo)

    assert main(["init", "--root", str(git_repo), "--yes"]) == 1
    assert "migrate" in capsys.readouterr().out.lower()
    assert _visible_tree(git_repo) == before

    assert main(["migrate", "--root", str(git_repo), "--yes"]) == 0
    assert main(["init", "--root", str(git_repo), "--yes"]) == 0
    assert "ship the real task" in (partial / "PLAN.md").read_text(
        encoding="utf-8")
    assert loads((partial / "config.toml").read_text(
        encoding="utf-8"))["git"]["commit_policy"] == "never"


def test_parse_legacy_config():
    values = parse_legacy_config('# c\nA=1\nB="two"\n\nbad\n')
    assert values == {"A": "1", "B": "two"}


def test_render_config_escapes_quotes_and_backslashes():
    text = render_config_toml({"COMMIT_POLICY": 'a"b\\c'})
    assert loads(text)["git"]["commit_policy"] == 'a"b\\c'
