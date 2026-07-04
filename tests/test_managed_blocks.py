from project_steward.managed_blocks import (convert_legacy_markers,
                                            find_legacy_blocks, get_block,
                                            list_blocks, upsert_block)


def test_upsert_appends_then_replaces_idempotently():
    text = "# Title\n\nUser prose stays.\n"
    v1 = upsert_block(text, "commands", "## Commands\nfoo")
    assert "User prose stays." in v1
    assert get_block(v1, "commands") == "## Commands\nfoo"
    v2 = upsert_block(v1, "commands", "## Commands\nbar")
    assert get_block(v2, "commands") == "## Commands\nbar"
    assert v2.count("PROJECT-STEWARD:BEGIN commands") == 1
    assert upsert_block(v2, "commands", "## Commands\nbar") == v2  # idempotent


def test_user_text_outside_blocks_untouched():
    text = "before\n\n<!-- PROJECT-STEWARD:BEGIN x -->\nold\n" \
           "<!-- PROJECT-STEWARD:END x -->\n\nafter\n"
    out = upsert_block(text, "x", "new")
    assert out.startswith("before") and out.rstrip().endswith("after")
    assert "old" not in out and "new" in out


def test_hash_style_and_listing():
    out = upsert_block("", "runtime-state", "a/\nb/", style="hash")
    assert "# PROJECT-STEWARD:BEGIN runtime-state" in out
    assert list_blocks(out) == ["runtime-state"]


def test_legacy_conversion():
    text = "<!-- PROJECTFORGE:BEGIN proto -->\nbody\n<!-- PROJECTFORGE:END proto -->"
    assert find_legacy_blocks(text) == ["proto"]
    converted = convert_legacy_markers(text)
    assert find_legacy_blocks(converted) == []
    assert get_block(converted, "proto") == "body"
