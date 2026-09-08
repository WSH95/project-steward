import json

import pytest

from project_steward import backend_broker, doctor, sessions
from project_steward.cli import main
from project_steward.managed_blocks import has_block, upsert_block
from project_steward.scaffold import apply_plan, plan_files
from project_steward.state import load_backend, load_config


def initialize(repo, **answers):
    plan, mapping = plan_files(repo, answers)
    apply_plan(repo, plan, mapping)
    return plan, mapping


def test_fresh_init_routes_to_workflow_and_preserves_project_commands(git_repo):
    initialize(git_repo, project_name="Delivery", test_command="pytest tests")
    agents = (git_repo / "AGENTS.md").read_text(encoding="utf-8")
    workflow = (git_repo / ".project-steward/WORKFLOW.md").read_text(encoding="utf-8")
    assert ".project-steward/WORKFLOW.md" in agents
    assert "pytest tests" in agents
    assert len(agents.splitlines()) < 35
    assert not has_block(agents, "task-backend")
    assert "HANDOFF.md" in workflow and "commit_policy" in workflow
    assert has_block(workflow, "task-backend")
    assert load_config(git_repo)["git"]["commit_policy"] == "auto"


@pytest.mark.parametrize("policy", ["auto", "ask", "never"])
def test_init_policy_flag_and_reinit_preserve_existing_config(git_repo, policy):
    assert main(["init", "--root", str(git_repo), "--yes",
                 "--commit-policy", policy]) == 0
    config = git_repo / ".project-steward/config.toml"
    before = config.read_bytes()
    assert load_config(git_repo)["git"]["commit_policy"] == policy
    initialize(git_repo, commit_policy="auto")
    assert config.read_bytes() == before


def test_legacy_missing_config_keeps_ask_default(git_repo):
    (git_repo / ".project-steward").mkdir()
    initialize(git_repo)
    assert load_config(git_repo)["git"]["commit_policy"] == "ask"


def test_init_commit_suggestion_includes_only_changed_codex_files(git_repo, capsys):
    args = ["init", "--root", str(git_repo), "--yes"]
    assert main(args) == 0
    suggestion = next(line for line in capsys.readouterr().out.splitlines()
                      if line.startswith("Suggested commit:"))
    assert '".codex/config.toml"' in suggestion
    assert '".codex/hooks.json"' in suggestion

    assert main(args) == 0
    repeated = next(line for line in capsys.readouterr().out.splitlines()
                    if line.startswith("Suggested commit:"))
    assert ".codex/" not in repeated


def test_init_never_policy_suppresses_commit_suggestions(git_repo, capsys):
    assert main(["init", "--root", str(git_repo), "--yes",
                 "--commit-policy", "never"]) == 0
    assert "Suggested commit:" not in capsys.readouterr().out


def test_reinit_preserves_user_text_workflow_backend_and_commands(git_repo):
    initialize(git_repo, backend_name="beads", test_command="custom-test")
    agents_path = git_repo / "AGENTS.md"
    old = agents_path.read_text(encoding="utf-8")
    agents_path.write_text("User preface.\n" + upsert_block(
        old, "task-backend", "old managed backend rules") + "\nUser ending.\n",
        encoding="utf-8")
    workflow = git_repo / ".project-steward/WORKFLOW.md"
    workflow.write_text(workflow.read_text(encoding="utf-8") + "\nCustom advice.\n",
                        encoding="utf-8")
    before = workflow.read_bytes()
    initialize(git_repo)
    updated = agents_path.read_text(encoding="utf-8")
    assert updated.startswith("User preface.\n")
    assert updated.endswith("\nUser ending.\n")
    assert "custom-test" in updated
    assert not has_block(updated, "task-backend")
    assert workflow.read_bytes() == before
    assert load_backend(git_repo)["name"] == "beads"


def test_reinit_uses_existing_backend_when_flag_conflicts(git_repo):
    initialize(git_repo, backend_name="markdown")
    workflow = git_repo / ".project-steward/WORKFLOW.md"
    workflow.unlink()

    plan, mapping = plan_files(git_repo, {"backend_name": "beads"})

    assert mapping["backend_name"] == "markdown"
    assert plan[".project-steward/backend.json"] == ("skip", None, "")
    assert plan[".project-steward/WORKFLOW.md"][0] == "create"
    assert "built-in Markdown backend" in plan[
        ".project-steward/WORKFLOW.md"
    ][1]
    assert "beads owns detailed tasks" not in plan[
        ".project-steward/WORKFLOW.md"
    ][1]
    assert any(
        "backend adopt" in warning and "beads" in warning
        for warning in mapping["_warnings"]
    )


def test_external_backend_init_has_honest_useful_context(git_repo):
    initialize(git_repo, project_name="Delivery", one_liner="Parcel tracking.",
               first_milestone="M1: shipment search", backend_name="beads")
    plan = (git_repo / ".project-steward/PLAN.md").read_text(encoding="utf-8")
    handoff = (git_repo / ".project-steward/HANDOFF.md").read_text(encoding="utf-8")
    assert "beads" in plan and "M1: shipment search" in plan
    assert "Active" in plan and "Blocked" in plan and "Next" in plan
    assert "Last reviewed" in plan
    assert "- [ ]" not in plan
    assert "Parcel tracking." in handoff and "M1: shipment search" in handoff
    assert "beads" in handoff
    assert "No project work has started" not in handoff
    config_text = (
        git_repo / ".project-steward/config.toml"
    ).read_text(encoding="utf-8")
    assert "[backend]" not in config_text
    assert load_config(git_repo)["backend"]["name"] == "beads"
    recap = sessions.build_recap(git_repo)
    assert recap["task_backend"] == "beads"
    assert recap["current_milestone"] == "M1: shipment search"
    assert recap["open_tasks"] == 0
    assert "0 open task" not in sessions.format_recap(recap)


def test_adopt_updates_workflow_without_recreating_agents_block(git_repo):
    initialize(git_repo)
    agents = (git_repo / "AGENTS.md").read_bytes()
    report = backend_broker.adopt(git_repo, "beads", assume_yes=True)
    assert report["ok"]
    assert (git_repo / "AGENTS.md").read_bytes() == agents
    assert "beads" in (git_repo / ".project-steward/WORKFLOW.md").read_text(encoding="utf-8")
    assert "overview" in report["pointer_note"]
    assert load_backend(git_repo)["name"] == "beads"


def test_adopt_preserves_config_and_plan_and_status_uses_backend_identity(
        git_repo, capsys):
    initialize(git_repo)
    config_path = git_repo / ".project-steward/config.toml"
    plan_path = git_repo / ".project-steward/PLAN.md"
    config_before = config_path.read_bytes()
    plan_before = plan_path.read_bytes()

    report = backend_broker.adopt(git_repo, "beads", assume_yes=True)
    assert report["ok"]
    assert config_path.read_bytes() == config_before
    assert plan_path.read_bytes() == plan_before

    assert main(["status", "--root", str(git_repo), "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["task_backend"] == "beads"
    assert status["backend"]["name"] == "beads"
    assert status["config"]["backend"]["name"] == "beads"


def test_adopt_declined_preserves_all_files(git_repo):
    initialize(git_repo)
    before = {p: p.read_bytes() for p in (git_repo / ".project-steward").glob("*")
              if p.is_file()}
    report = backend_broker.adopt(git_repo, "beads", confirm=lambda diff: False)
    assert not report["ok"]
    assert {p: p.read_bytes() for p in before} == before


def test_doctor_distinguishes_legacy_inline_and_broken_workflow_pointer(git_repo):
    initialize(git_repo)
    workflow = git_repo / ".project-steward/WORKFLOW.md"
    workflow.unlink()
    results = doctor.run_checks(git_repo)
    assert any(r["status"] == "fail" and "workflow" in r["name"].lower()
               for r in results)
    agents = git_repo / "AGENTS.md"
    agents.write_text(upsert_block("# Old project\n", "agent-session-protocol",
                                  "Read HANDOFF.md; resume, checkpoint, wrap."),
                      encoding="utf-8")
    assert not any(r["status"] == "fail" for r in doctor.run_checks(git_repo))


def test_cli_preview_shows_new_files_without_writing(git_repo, capsys):
    assert main(["init", "--root", str(git_repo), "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "WORKFLOW.md" in output and ".codex/hooks.json" in output
    assert "hooks = true" in output
    assert not (git_repo / ".project-steward").exists()
    assert not (git_repo / ".codex").exists()


def test_cli_codex_optout_preserves_existing_files(git_repo):
    codex = git_repo / ".codex"
    codex.mkdir()
    hook_file = codex / "hooks.json"
    hook_file.write_text('{"hooks": {}}\n', encoding="utf-8")
    assert main(["init", "--root", str(git_repo), "--yes", "--no-codex-hooks"]) == 0
    assert not (codex / "config.toml").exists()
    assert json.loads(hook_file.read_text(encoding="utf-8")) == {"hooks": {}}


def test_reinit_honors_saved_codex_optout(git_repo):
    main(["init", "--root", str(git_repo), "--yes", "--no-codex-hooks"])
    main(["init", "--root", str(git_repo), "--yes"])
    assert not (git_repo / ".codex").exists()


@pytest.mark.parametrize("text", ["[git]\ncommit_policy = 'unknown'\n",
                                  "git = 'invalid'\n", "[git\n"])
def test_invalid_legacy_commit_policy_falls_back_to_ask(git_repo, text):
    state = git_repo / ".project-steward"
    state.mkdir()
    (state / "config.toml").write_text(text, encoding="utf-8")
    assert load_config(git_repo)["git"]["commit_policy"] == "ask"


def test_invalid_config_fields_use_safe_defaults_and_preserve_valid_values(
        git_repo):
    state = git_repo / ".project-steward"
    state.mkdir()
    (state / "config.toml").write_text(
        """\
[session]
auto_handoff_mode = "later"
auto_handoff_cooldown_min = true
auto_handoff_min_edits = -1
custom_session_value = "keep"

[git]
commit_policy = "auto"
never_push = "yes"

[init]
run_project_scripts = true
codex_hooks = "disabled"

[custom]
label = "keep this too"
""",
        encoding="utf-8",
    )
    before = (state / "config.toml").read_bytes()

    config = load_config(git_repo)

    assert config["session"] == {
        "auto_handoff_mode": "block",
        "auto_handoff_cooldown_min": 45,
        "auto_handoff_min_edits": 5,
        "custom_session_value": "keep",
    }
    assert config["git"]["commit_policy"] == "auto"
    assert config["git"]["never_push"] is True
    assert config["init"]["run_project_scripts"] is True
    assert config["init"]["codex_hooks"] is True
    assert config["custom"] == {"label": "keep this too"}

    config_check = next(
        check for check in doctor.run_checks(git_repo)
        if check["name"] == "config.toml parses"
    )
    assert config_check["status"] == "fail"
    for field in (
        "session.auto_handoff_mode",
        "session.auto_handoff_cooldown_min",
        "session.auto_handoff_min_edits",
        "git.never_push",
        "init.codex_hooks",
    ):
        assert field in config_check["detail"]
    assert (state / "config.toml").read_bytes() == before


def test_zero_session_limits_are_valid(git_repo):
    state = git_repo / ".project-steward"
    state.mkdir()
    (state / "config.toml").write_text(
        "[session]\n"
        "auto_handoff_cooldown_min = 0\n"
        "auto_handoff_min_edits = 0\n",
        encoding="utf-8",
    )

    config = load_config(git_repo)
    config_check = next(
        check for check in doctor.run_checks(git_repo)
        if check["name"] == "config.toml parses"
    )

    assert config["session"]["auto_handoff_cooldown_min"] == 0
    assert config["session"]["auto_handoff_min_edits"] == 0
    assert config_check["status"] == "ok"


@pytest.mark.parametrize("text", [
    'init = "invalid"\n',
    "init = true\n",
    "init = []\n",
])
def test_wrong_shaped_init_config_uses_safe_default_and_doctor_fails(
        git_repo, text):
    state = git_repo / ".project-steward"
    state.mkdir()
    (state / "config.toml").write_text(text, encoding="utf-8")

    plan, mapping = plan_files(git_repo)

    assert mapping["codex_hooks"] == "true"
    assert plan[".codex/hooks.json"][0] == "create"
    apply_plan(git_repo, plan, mapping)
    assert isinstance(load_config(git_repo)["init"], dict)
    checks = doctor.run_checks(git_repo)
    config_checks = [
        check for check in checks if check["name"] == "config.toml parses"
    ]
    assert len(config_checks) == 1
    assert config_checks[0]["status"] == "fail"
    assert "init" in config_checks[0]["detail"].lower() or (
        "unsupported value" in config_checks[0]["detail"].lower()
    )


def test_legacy_migration_creates_target_for_workflow_pointer(git_repo):
    from project_steward.migrate import migrate
    legacy = git_repo / ".projectforge"
    legacy.mkdir()
    (git_repo / "AGENTS.md").write_text(
        "# Project\n\n## Agent session protocol (Projectforge)\n\nOld instructions.\n",
        encoding="utf-8")
    assert migrate(git_repo)["ok"]
    assert ".project-steward/WORKFLOW.md" in (git_repo / "AGENTS.md").read_text(encoding="utf-8")
    assert (git_repo / ".project-steward/WORKFLOW.md").is_file()
