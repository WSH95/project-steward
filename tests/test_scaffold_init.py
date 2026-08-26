import pytest

from project_steward import scaffold
from project_steward.paths import state_dir
from project_steward.scaffold import TemplateError, apply_plan, plan_files


def test_init_scaffold_creates_everything(git_repo):
    plan, mapping = plan_files(git_repo, {
        "project_name": "Demo", "one_liner": "A demo.",
        "primary_language": "Python", "test_command": "pytest",
    })
    written = apply_plan(git_repo, plan, mapping)
    assert "AGENTS.md" in written and "CLAUDE.md" in written
    agents = (git_repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "PROJECT-STEWARD:BEGIN agent-session-protocol" in agents
    assert "$project_name" not in agents  # no unresolved placeholders
    assert len(agents.splitlines()) <= 50
    assert "## Project context" in agents
    assert "- Test: `pytest`" in agents
    assert "write plain, factual updates" in agents
    assert "zero-context successor" not in agents
    claude = (git_repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@AGENTS.md" in claude
    gi = (git_repo / ".gitignore").read_text(encoding="utf-8")
    assert ".project-steward/runtime/" in gi
    handoff = (state_dir(git_repo) / "HANDOFF.md").read_text(encoding="utf-8")
    assert "session_status: closed" in handoff
    assert "last_commit:" not in handoff
    assert (state_dir(git_repo) / "state.json").is_file()


def test_reinit_preserves_user_content(git_repo):
    plan, mapping = plan_files(git_repo, {"project_name": "Demo"})
    apply_plan(git_repo, plan, mapping)
    agents_path = git_repo / "AGENTS.md"
    agents_path.write_text(
        agents_path.read_text(encoding="utf-8") + "\nUSER SENTINEL LINE\n",
        encoding="utf-8")
    handoff = state_dir(git_repo) / "HANDOFF.md"
    handoff.write_text("custom handoff", encoding="utf-8")
    plan2, mapping2 = plan_files(git_repo, {"project_name": "Demo"})
    apply_plan(git_repo, plan2, mapping2)
    assert "USER SENTINEL LINE" in agents_path.read_text(encoding="utf-8")
    assert handoff.read_text(encoding="utf-8") == "custom handoff"  # skip


def test_reinit_compacts_only_managed_agents_blocks(git_repo):
    agents_path = git_repo / "AGENTS.md"
    agents_path.write_text(
        "# User instructions\n\nKeep this sentence exactly.\n\n"
        "<!-- PROJECT-STEWARD:BEGIN commands -->\n"
        "## Commands\n\n| Task | Command |\n| --- | --- |\n"
        "| Build | `old-build` |\n| Test | `old-test` |\n"
        "| Lint | `old-lint` |\n"
        "<!-- PROJECT-STEWARD:END commands -->\n\n"
        "<!-- PROJECT-STEWARD:BEGIN task-backend -->\n"
        "## Task backend\n\nold backend text\n"
        "<!-- PROJECT-STEWARD:END task-backend -->\n\n"
        "<!-- PROJECT-STEWARD:BEGIN agent-session-protocol -->\n"
        "## Agent session protocol (Project Steward)\n\n"
        "**Session start** — before other work, read everything.\n"
        "<!-- PROJECT-STEWARD:END agent-session-protocol -->\n\n"
        "USER SENTINEL LINE\n",
        encoding="utf-8",
    )
    answers = {
        "project_name": "Demo",
        "build_command": "new-build",
        "test_command": "new-test",
        "lint_command": "new-lint",
    }

    plan, mapping = plan_files(git_repo, answers)
    apply_plan(git_repo, plan, mapping)
    updated = agents_path.read_text(encoding="utf-8")

    assert updated.startswith("# User instructions\n\nKeep this sentence exactly.")
    assert updated.endswith("USER SENTINEL LINE\n")
    assert "- Build: `new-build`" in updated
    assert "## Project Steward workflow" in updated
    assert "**Session start**" not in updated

    plan2, mapping2 = plan_files(git_repo, answers)
    assert plan2["AGENTS.md"][0] == "noop"
    assert apply_plan(git_repo, plan2, mapping2) == []


def test_templates_live_inside_the_package():
    # Regression: templates outside the package never ship in wheels.
    root = scaffold._templates_root()
    assert root is not None
    assert root.parent.name == "project_steward"


def test_generated_project_docs_use_plain_working_notes(git_repo):
    plan, mapping = plan_files(git_repo, {
        "project_name": "Demo",
        "one_liner": "A demo project.",
        "primary_language": "Python",
    })
    apply_plan(git_repo, plan, mapping)

    generated = [
        (git_repo / "AGENTS.md").read_text(encoding="utf-8"),
        (git_repo / "CLAUDE.md").read_text(encoding="utf-8"),
    ]
    for name in (
        "PROJECT.md", "PLAN.md", "PROGRESS.md", "HANDOFF.md",
        "DECISIONS.md", "QUESTIONS.md", "RISKS.md", "VERIFY.md",
    ):
        generated.append(
            (state_dir(git_repo) / name).read_text(encoding="utf-8")
        )
    prose = "\n".join(generated).lower()

    for stock_phrase in (
        "zero-context successor",
        "freshly initialized",
        "serves as",
        "stands as",
        "pivotal",
        "i hope this helps",
        "let me know",
    ):
        assert stock_phrase not in prose

    handoff = generated[5]
    assert "## Now" in handoff
    assert "## Next steps" in handoff
    assert "previous chat" in handoff


def test_missing_templates_hard_error(git_repo, monkeypatch):
    # Regression: a template-less install must fail loud, not scaffold stubs.
    monkeypatch.setattr(scaffold, "_templates_root", lambda: None)
    with pytest.raises(TemplateError) as exc:
        plan_files(git_repo, {"project_name": "Demo"})
    assert ".template" in str(exc.value)
