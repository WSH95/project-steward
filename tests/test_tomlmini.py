import pytest

from project_steward.tomlmini import TomlMiniError, load_toml_text, loads


def test_sections_values_comments():
    cfg = loads(
        "# top comment\n"
        "[session]\n"
        'auto_handoff_mode = "block"  # trailing\n'
        "auto_handoff_cooldown_min = 45\n"
        "[git]\n"
        "never_push = true\n"
        "ratio = 1.5\n"
        '[a.b]\nkey = "v"\n'
    )
    assert cfg["session"]["auto_handoff_mode"] == "block"
    assert cfg["session"]["auto_handoff_cooldown_min"] == 45
    assert cfg["git"]["never_push"] is True
    assert cfg["git"]["ratio"] == 1.5
    assert cfg["a"]["b"]["key"] == "v"


def test_hash_inside_string_kept():
    assert loads('k = "a#b"')["k"] == "a#b"


def test_errors():
    with pytest.raises(TomlMiniError):
        loads("bad line without equals")
    with pytest.raises(TomlMiniError):
        loads('k = [1, 2]')


def test_basic_string_escapes_match_tomllib():
    assert loads('k = "a\\tb"')["k"] == "a\tb"
    assert loads('k = "say \\"hi\\""')["k"] == 'say "hi"'
    assert loads('k = "\\u0041Z"')["k"] == "AZ"
    with pytest.raises(TomlMiniError):
        loads('k = "C:\\Users\\bob"')


def test_windows_paths_use_literal_strings_on_all_pythons():
    # load_toml_text picks tomllib on 3.11+ and the mini reader below;
    # these inputs must behave identically on both.
    with pytest.raises(ValueError):
        load_toml_text('k = "C:\\Users\\bob"')
    assert load_toml_text("k = 'C:\\Users\\bob'")["k"] == "C:\\Users\\bob"
    assert load_toml_text('k = "a\\tb"')["k"] == "a\tb"
