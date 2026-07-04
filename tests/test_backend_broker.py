from project_steward import backend_broker
from project_steward.paths import state_dir
from project_steward.scaffold import apply_plan, plan_files
from project_steward.state import load_backend, write_text_atomic


def _init(repo):
    plan, mapping = plan_files(repo, {"project_name": "Demo"})
    apply_plan(repo, plan, mapping)


def test_markdown_wins_for_small_solo(git_repo):
    _init(git_repo)
    scores, _ = backend_broker.score(git_repo)
    assert scores["markdown"] >= max(
        v for k, v in scores.items() if k != "markdown")


def test_beads_wins_with_blockers_and_artifacts(git_repo):
    _init(git_repo)
    (git_repo / ".beads").mkdir()
    handoff = state_dir(git_repo) / "HANDOFF.md"
    write_text_atomic(handoff,
        "---\nsession_status: closed\n---\n\n# H\n\n## Now\nx\n\n"
        "## Next steps\n1. x\n\n## Blockers\n- a\n- b\n- c\n- d\n- e\n")
    scores, _ = backend_broker.score(git_repo)
    assert scores["beads"] > scores["markdown"]
    ranked = backend_broker.recommend(git_repo)["ranked"]
    assert ranked[0]["name"] == "beads"


def test_adopt_updates_agents_and_backend_json(git_repo):
    _init(git_repo)
    report = backend_broker.adopt(git_repo, "beads", assume_yes=True)
    assert report["ok"]
    agents = (git_repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "owned by **beads" in agents.replace("(bd)**", "**")
    assert load_backend(git_repo)["name"] == "beads"
    stub = backend_broker.adopt(git_repo, "jira", assume_yes=True)
    assert not stub["ok"]
