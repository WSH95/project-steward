from project_steward.paths import state_dir
from project_steward.scaffold import apply_plan, plan_files


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
    claude = (git_repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@AGENTS.md" in claude
    gi = (git_repo / ".gitignore").read_text(encoding="utf-8")
    assert ".project-steward/runtime/" in gi
    handoff = (state_dir(git_repo) / "HANDOFF.md").read_text(encoding="utf-8")
    assert "session_status: closed" in handoff
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
