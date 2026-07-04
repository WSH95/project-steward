import pytest

from project_steward.tomlmini import TomlMiniError, loads


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
