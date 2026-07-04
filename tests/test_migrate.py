from project_steward.managed_blocks import find_legacy_blocks
from project_steward.migrate import (migrate, parse_legacy_config,
                                     render_config_toml)
from project_steward.paths import state_dir
from project_steward.tomlmini import loads


def _make_legacy(repo):
    legacy = repo / ".projectforge"
    (legacy / "journal").mkdir(parents=True)
    (legacy / "PLAN.md").write_text(
        "# Plan (Projectforge)\n- [ ] task in .projectforge/PLAN.md\n",
        encoding="utf-8")
    (legacy / "HANDOFF.md").write_text(
        "---\nsession_status: closed\n---\n\n# Handoff\n\n## Now\nok\n",
        encoding="utf-8")
    (legacy / "config").write_text(
        'AUTO_HANDOFF_MODE=remind\nAUTO_HANDOFF_COOLDOWN_MIN=30\n'
        'COMMIT_POLICY=ask\n', encoding="utf-8")
    (legacy / "journal" / "heartbeat").write_text("123", encoding="utf-8")
    (repo / "AGENTS.md").write_text(
        "# Proj\n\nUser prose.\n\n"
        "## Agent session protocol (Projectforge)\n\nold protocol text\n\n"
        "## Other user section\nkeep me\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".projectforge/journal/\n",
                                     encoding="utf-8")


def test_full_migration(git_repo):
    _make_legacy(git_repo)
    report = migrate(git_repo, project_name="Demo")
    assert report["ok"]
    sdir = state_dir(git_repo)
    assert not (git_repo / ".projectforge").exists()
    assert (sdir / "migration-backup-projectforge" / "PLAN.md").is_file()
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


def test_parse_legacy_config():
    values = parse_legacy_config('# c\nA=1\nB="two"\n\nbad\n')
    assert values == {"A": "1", "B": "two"}


def test_render_config_escapes_quotes_and_backslashes():
    text = render_config_toml({"COMMIT_POLICY": 'a"b\\c'})
    assert loads(text)["git"]["commit_policy"] == 'a"b\\c'
