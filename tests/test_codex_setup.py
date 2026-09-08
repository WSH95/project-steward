import json
import os

import pytest


def _codex_setup():
    try:
        from project_steward import codex_setup
    except ImportError:
        pytest.fail("project_steward.codex_setup is not implemented")
    return codex_setup


def test_fresh_project_plans_feature_config_and_canonical_hooks(tmp_path):
    codex_setup = _codex_setup()

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/config.toml"] == (
        "create", "[features]\nhooks = true\n", ""
    )
    action, text, diff = entries[".codex/hooks.json"]
    assert action == "create"
    assert diff == ""
    hooks = json.loads(text)
    assert set(hooks) == {"hooks"}
    assert set(hooks["hooks"]) == {
        "SessionStart", "PostToolUse", "UserPromptSubmit", "Stop"
    }


def test_disabled_setup_plans_no_codex_files(tmp_path):
    codex_setup = _codex_setup()

    assert codex_setup.plan_files(tmp_path, enabled=False) == ({}, [])


def _write_codex_file(root, name, text):
    codex = root / ".codex"
    codex.mkdir(exist_ok=True)
    path = codex / name
    path.write_text(text, encoding="utf-8")
    return path


def _steward_command_count(data, event, command):
    count = 0
    for group in data["hooks"].get(event, []):
        for handler in group.get("hooks", []):
            if handler.get("command") == command:
                count += 1
    return count


def test_existing_config_is_preserved_byte_for_byte(tmp_path):
    codex_setup = _codex_setup()
    config = tmp_path / ".codex" / "config.toml"
    config.parent.mkdir()
    original = b'model = "gpt-custom"\r\n# keep this formatting\r\n'
    config.write_bytes(original)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/config.toml"] == ("skip", None, "")
    assert config.read_bytes() == original
    assert entries[".codex/hooks.json"][0] == "create"


def test_existing_custom_hooks_merge_without_duplicate_steward_handler(tmp_path):
    codex_setup = _codex_setup()
    _write_codex_file(
        tmp_path, "config.toml", "[features]\nhooks = true\n"
    )
    existing = {
        "description": "keep me",
        "custom": {"enabled": True},
        "hooks": {
            "SessionStart": [{
                "matcher": "custom matcher",
                "hooks": [{
                    "type": "command",
                    "command": (
                        "project-steward hook session-start --agent codex"
                    ),
                    "timeout": 99,
                    "statusMessage": "customized",
                }],
            }],
            "Stop": [{
                "hooks": [{
                    "type": "command",
                    "command": "custom-stop",
                    "timeout": 4,
                }],
            }],
            "PreToolUse": [{"matcher": "Bash", "hooks": []}],
        },
    }
    _write_codex_file(
        tmp_path, "hooks.json", json.dumps(existing, indent=4) + "\n"
    )

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    action, text, diff = entries[".codex/hooks.json"]
    assert action == "update"
    assert "--- a/.codex/hooks.json" in diff
    assert "+++ b/.codex/hooks.json" in diff
    merged = json.loads(text)
    assert merged["description"] == "keep me"
    assert merged["custom"] == {"enabled": True}
    assert merged["hooks"]["PreToolUse"] == existing["hooks"]["PreToolUse"]
    customized = merged["hooks"]["SessionStart"][0]["hooks"][0]
    assert customized["timeout"] == 99
    assert customized["statusMessage"] == "customized"
    commands = {
        "SessionStart": "project-steward hook session-start --agent codex",
        "PostToolUse": "project-steward hook post-tool-use --agent codex",
        "UserPromptSubmit": (
            "project-steward hook user-prompt-submit --agent codex"
        ),
        "Stop": "project-steward hook stop --agent codex",
    }
    for event, command in commands.items():
        assert _steward_command_count(merged, event, command) == 1
    assert any(
        handler.get("command") == "custom-stop"
        for group in merged["hooks"]["Stop"]
        for handler in group.get("hooks", [])
    )

    (tmp_path / ".codex" / "hooks.json").write_text(
        text, encoding="utf-8"
    )
    repeated, repeated_warnings = codex_setup.plan_files(tmp_path)
    assert repeated_warnings == []
    assert repeated[".codex/hooks.json"] == ("noop", None, "")


def test_merge_removes_duplicate_steward_command_but_keeps_first_settings(
        tmp_path):
    codex_setup = _codex_setup()
    fresh, _warnings = codex_setup.plan_files(tmp_path)
    existing = json.loads(fresh[".codex/hooks.json"][1])
    command = "project-steward hook session-start --agent codex"
    existing["hooks"]["SessionStart"].insert(0, {
        "matcher": "user matcher",
        "hooks": [{
            "type": "command",
            "command": command,
            "timeout": 77,
            "statusMessage": "keep first",
        }],
    })
    _write_codex_file(tmp_path, "config.toml", "[features]\nhooks = true\n")
    _write_codex_file(
        tmp_path, "hooks.json", json.dumps(existing, indent=2) + "\n"
    )

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/hooks.json"][0] == "update"
    merged = json.loads(entries[".codex/hooks.json"][1])
    assert _steward_command_count(merged, "SessionStart", command) == 1
    kept = merged["hooks"]["SessionStart"][0]["hooks"][0]
    assert kept["timeout"] == 77
    assert kept["statusMessage"] == "keep first"


@pytest.mark.parametrize("bad_text", [
    "{broken json",
    '{"hooks": {}, "invalid": NaN}',
    json.dumps({"hooks": []}),
    json.dumps({"hooks": {"Stop": {"hooks": []}}}),
])
def test_malformed_or_unmergeable_hooks_skip_all_codex_setup(
        tmp_path, bad_text):
    codex_setup = _codex_setup()
    _write_codex_file(tmp_path, "hooks.json", bad_text)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert entries == {
        ".codex/config.toml": ("skip", None, ""),
        ".codex/hooks.json": ("skip", None, ""),
    }
    assert len(warnings) == 1
    assert ".codex/hooks.json" in warnings[0]
    assert "skipped" in warnings[0].lower()


@pytest.mark.parametrize("config_text", [
    "[hooks]\nmanaged_dir = '/opt/hooks'\n",
    "[[hooks.Stop]]\n",
    "[[\"hooks\".Stop.hooks]]\ntype = 'command'\n",
    "hooks.Stop = []\n",
    "'hooks'.Stop = []\n",
    "hooks = { Stop = [] }\n",
])
def test_inline_hook_forms_skip_all_codex_setup(tmp_path, config_text):
    codex_setup = _codex_setup()
    config = _write_codex_file(tmp_path, "config.toml", config_text)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(value == ("skip", None, "") for value in entries.values())
    assert len(warnings) == 1
    assert "inline" in warnings[0].lower() or (
        codex_setup._tomllib is None
        and "cannot safely validate" in warnings[0].lower()
    )
    assert config.read_text(encoding="utf-8") == config_text


def test_feature_hook_keys_are_not_mistaken_for_inline_hooks(tmp_path):
    codex_setup = _codex_setup()
    config_text = (
        "[features]\n"
        "hooks = true\n"
        "# hooks = { this comment is ignored }\n"
        "label = 'hooks = { inside a string }'\n"
    )
    _write_codex_file(tmp_path, "config.toml", config_text)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/config.toml"] == ("skip", None, "")
    assert entries[".codex/hooks.json"][0] == "create"


def test_native_parser_ignores_toml_like_prose_in_multiline_string(tmp_path):
    codex_setup = _codex_setup()
    if codex_setup._tomllib is None:
        pytest.skip("Native TOML validation requires Python 3.11+")
    config_text = (
        'instructions = """\n'
        "[hooks]\n"
        "Stop = []\n"
        "[features]\n"
        "hooks = false\n"
        '"""\n'
    )
    config = _write_codex_file(tmp_path, "config.toml", config_text)
    before = config.read_bytes()

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/config.toml"] == ("skip", None, "")
    assert entries[".codex/hooks.json"][0] == "create"
    assert config.read_bytes() == before


def test_native_parser_recognizes_escaped_quoted_inline_hooks_key(tmp_path):
    codex_setup = _codex_setup()
    if codex_setup._tomllib is None:
        pytest.skip("Native TOML validation requires Python 3.11+")
    config_text = r'"\u0068ooks" = { Stop = [] }' + "\n"
    config = _write_codex_file(tmp_path, "config.toml", config_text)
    before = config.read_bytes()

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert len(warnings) == 1
    assert "inline" in warnings[0].lower()
    assert config.read_bytes() == before


def test_malformed_existing_codex_config_skips_setup_and_fails_inspection(
        tmp_path):
    codex_setup = _codex_setup()
    malformed = 'model = "unterminated\n[features]\nhooks = true\n'
    config = _write_codex_file(tmp_path, "config.toml", malformed)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert entries == {
        ".codex/config.toml": ("skip", None, ""),
        ".codex/hooks.json": ("skip", None, ""),
    }
    assert len(warnings) == 1
    assert "malformed" in warnings[0].lower()
    assert config.read_text(encoding="utf-8") == malformed
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    activation = results["Codex hooks activation"]
    assert activation["status"] == "fail"
    assert "malformed" in activation["detail"].lower()


def test_valid_rich_codex_toml_is_preserved_and_allows_hook_plan(tmp_path):
    codex_setup = _codex_setup()
    rich = (
        'model = "gpt-custom"\n'
        'features = { hooks = true, multi_agent = true }\n'
        '[mcp_servers.example]\n'
        'command = "python"\n'
        'args = ["-m", "example"]\n'
    )
    config = _write_codex_file(tmp_path, "config.toml", rich)
    before = config.read_bytes()

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert entries[".codex/config.toml"] == ("skip", None, "")
    if codex_setup._tomllib is None:
        assert entries[".codex/hooks.json"][0] == "skip"
        assert "cannot safely validate" in warnings[0].lower()
    else:
        assert warnings == []
        assert entries[".codex/hooks.json"][0] == "create"
    assert config.read_bytes() == before


def test_older_python_skips_rich_config_when_validation_is_unavailable(
        tmp_path, monkeypatch):
    codex_setup = _codex_setup()
    _write_codex_file(
        tmp_path, "config.toml",
        'model = "gpt-custom"\ninclude = ["rich", "toml"]\n',
    )
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert len(warnings) == 1
    assert "cannot safely validate" in warnings[0].lower()
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    activation = results["Codex hooks activation"]
    assert activation["status"] == "warn"
    assert "cannot safely validate" in activation["detail"].lower()


def test_older_python_validates_supported_config_and_merges_hooks(
        tmp_path, monkeypatch):
    codex_setup = _codex_setup()
    config = _write_codex_file(
        tmp_path, "config.toml",
        'model = "gpt-custom"\n[features]\nhooks = true\n',
    )
    before = config.read_bytes()
    _write_codex_file(
        tmp_path, "hooks.json",
        '{"description": "custom", "hooks": {}}\n',
    )
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert warnings == []
    assert entries[".codex/config.toml"] == ("skip", None, "")
    assert entries[".codex/hooks.json"][0] == "update"
    assert json.loads(entries[".codex/hooks.json"][1])[
        "description"
    ] == "custom"
    assert config.read_bytes() == before


def test_older_python_rejects_clearly_malformed_supported_toml(
        tmp_path, monkeypatch):
    codex_setup = _codex_setup()
    _write_codex_file(tmp_path, "config.toml", 'model = "unterminated\n')
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert "malformed" in warnings[0].lower()
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    assert results["Codex hooks activation"]["status"] == "fail"


@pytest.mark.parametrize("config_text", [
    "model = 1\vother = 2\n",
    "\u00a0model = 1\n",
    "#\x00 invalid comment\n[features]\nhooks = true\n",
    "model = 1\rother = 2\n",
])
@pytest.mark.parametrize("use_fallback", [True, False])
def test_config_validation_does_not_normalize_invalid_toml_whitespace(
        tmp_path, monkeypatch, config_text, use_fallback):
    codex_setup = _codex_setup()
    if not use_fallback and codex_setup._tomllib is None:
        pytest.skip("Native TOML validation requires Python 3.11+")
    config = _write_codex_file(tmp_path, "config.toml", config_text)
    before = config.read_bytes()
    if use_fallback:
        monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert len(warnings) == 1
    expected_warning = "cannot safely validate" if use_fallback else "malformed"
    assert expected_warning in warnings[0].lower()
    assert config.read_bytes() == before


@pytest.mark.parametrize("config_text", [
    'model = "first"\nmodel = "second"\n',
    "invalid key = true\n",
    "hooks = TRUE\n",
    "model = 'a' 'b'\n",
])
def test_older_python_does_not_accept_permissive_mini_parser_cases(
        tmp_path, monkeypatch, config_text):
    codex_setup = _codex_setup()
    _write_codex_file(tmp_path, "config.toml", config_text)
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert "malformed" in warnings[0].lower()
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    assert results["Codex hooks activation"]["status"] == "fail"


@pytest.mark.parametrize("config_text", [
    "a.b = 1\na = 2\n",
    "a = 1\n" + r'"\u0061" = 2' + "\n",
    r'"\q" = 1' + "\n",
    "é = 1\n",
    "a. = 1\n",
    "[a.b]\nx = 1\n[a]\nb = 2\n",
    "model = " + r'"line\nbreak"' + "\n",
    "model = " + r'"\uD800"' + "\n",
    'model = "control \x01"\n',
])
def test_older_python_treats_ambiguous_toml_as_unsupported(
        tmp_path, monkeypatch, config_text):
    codex_setup = _codex_setup()
    _write_codex_file(tmp_path, "config.toml", config_text)
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert len(warnings) == 1
    assert "cannot safely validate" in warnings[0].lower()
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    assert results["Codex hooks activation"]["status"] == "warn"


@pytest.mark.parametrize("config_text", [
    "a.b = 1\na = 2\n",
    "a = 1\n" + r'"\u0061" = 2' + "\n",
    r'"\q" = 1' + "\n",
    "é = 1\n",
    "a. = 1\n",
    "[a.b]\nx = 1\n[a]\nb = 2\n",
    "model = " + r'"\uD800"' + "\n",
    'model = "control \x01"\n',
])
def test_native_tomllib_rejects_malformed_review_repros(
        tmp_path, config_text):
    codex_setup = _codex_setup()
    if codex_setup._tomllib is None:
        pytest.skip("tomllib is unavailable")
    _write_codex_file(tmp_path, "config.toml", config_text)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert "malformed" in warnings[0].lower()
    results = {
        item["name"]: item for item in codex_setup.inspect_setup(tmp_path)
    }
    assert results["Codex hooks activation"]["status"] == "fail"


@pytest.mark.parametrize("config_text", [
    "a = 1\na = 2\n",
    "[a]\nx = 1\n[a]\ny = 2\n",
    "a = 1\n[a]\nx = 2\n",
    "[a]\nx = 1\nx = 2\n",
])
def test_older_python_rejects_narrow_subset_key_conflicts(
        tmp_path, monkeypatch, config_text):
    codex_setup = _codex_setup()
    _write_codex_file(tmp_path, "config.toml", config_text)
    monkeypatch.setattr(codex_setup, "_tomllib", None)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(entry == ("skip", None, "") for entry in entries.values())
    assert "malformed" in warnings[0].lower()


@pytest.mark.skipif(os.name == "nt", reason="symlink creation varies on Windows")
def test_symlink_escape_skips_all_codex_setup(tmp_path):
    codex_setup = _codex_setup()
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (tmp_path / ".codex").symlink_to(outside, target_is_directory=True)

    entries, warnings = codex_setup.plan_files(tmp_path)

    assert all(value == ("skip", None, "") for value in entries.values())
    assert len(warnings) == 1
    assert "outside" in warnings[0].lower()
    assert not (outside / "config.toml").exists()
    assert not (outside / "hooks.json").exists()


def _install_planned_codex_files(root):
    codex_setup = _codex_setup()
    entries, warnings = codex_setup.plan_files(root)
    assert warnings == []
    for relative, (action, text, _diff) in entries.items():
        if action in ("create", "update"):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")


def test_inspection_separates_installation_trust_and_cli(tmp_path, monkeypatch):
    codex_setup = _codex_setup()
    _install_planned_codex_files(tmp_path)
    monkeypatch.setattr(codex_setup.shutil, "which", lambda _name: None)

    results = {
        result["name"]: result for result in codex_setup.inspect_setup(tmp_path)
    }

    assert results["Codex hooks installed"]["status"] == "ok"
    assert "4 Project Steward" in results["Codex hooks installed"]["detail"]
    activation = results["Codex hooks activation"]
    assert activation["status"] == "warn"
    assert "trust unknown" in activation["detail"].lower()
    assert "/hooks" in activation["detail"]
    cli = results["Codex hook CLI on PATH"]
    assert cli["status"] == "warn"
    assert "project-steward" in cli["detail"]


@pytest.mark.parametrize("config_text", [
    "[features]\nhooks = false\n",
    "features.hooks = false\n",
    "features = { hooks = false, multi_agent = true }\n",
])
def test_inspection_identifies_known_disabled_hook_feature(
        tmp_path, monkeypatch, config_text):
    codex_setup = _codex_setup()
    _install_planned_codex_files(tmp_path)
    (tmp_path / ".codex" / "config.toml").write_text(
        config_text, encoding="utf-8"
    )
    monkeypatch.setattr(
        codex_setup.shutil, "which", lambda _name: "/usr/bin/project-steward"
    )

    results = {
        result["name"]: result for result in codex_setup.inspect_setup(tmp_path)
    }

    assert results["Codex hooks installed"]["status"] == "ok"
    assert results["Codex hooks activation"]["status"] == "warn"
    activation_detail = results["Codex hooks activation"]["detail"].lower()
    if codex_setup._tomllib is None and not config_text.startswith("[features]"):
        assert "cannot safely validate" in activation_detail
    else:
        assert "disabled" in activation_detail
    assert results["Codex hook CLI on PATH"]["status"] == "ok"


def test_native_inspection_recognizes_escaped_quoted_feature_key(
        tmp_path, monkeypatch):
    codex_setup = _codex_setup()
    if codex_setup._tomllib is None:
        pytest.skip("Native TOML validation requires Python 3.11+")
    _install_planned_codex_files(tmp_path)
    config = tmp_path / ".codex" / "config.toml"
    config_text = "[features]\n" + r'"\u0068ooks" = false' + "\n"
    config.write_text(config_text, encoding="utf-8")
    before = config.read_bytes()
    monkeypatch.setattr(
        codex_setup.shutil, "which", lambda _name: "/usr/bin/project-steward"
    )

    results = {
        result["name"]: result for result in codex_setup.inspect_setup(tmp_path)
    }

    activation = results["Codex hooks activation"]
    assert activation["status"] == "warn"
    assert "disabled" in activation["detail"].lower()
    assert config.read_bytes() == before


def test_inspection_reports_missing_and_malformed_hook_installations(tmp_path):
    codex_setup = _codex_setup()

    missing = {
        result["name"]: result for result in codex_setup.inspect_setup(tmp_path)
    }
    assert missing["Codex hooks installed"]["status"] == "warn"
    assert "missing" in missing["Codex hooks installed"]["detail"].lower()

    _write_codex_file(tmp_path, "hooks.json", "{not json")
    malformed = {
        result["name"]: result for result in codex_setup.inspect_setup(tmp_path)
    }
    assert malformed["Codex hooks installed"]["status"] == "warn"
    assert "malformed" in malformed["Codex hooks installed"]["detail"].lower()
