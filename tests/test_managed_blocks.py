import pytest

from project_steward import StewardError
from project_steward.managed_blocks import (MarkerError, get_block,
                                            has_block, list_blocks,
                                            upsert_block)


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


def test_trailing_whitespace_after_marker_is_tolerated():
    text = ("# doc\n<!-- PROJECT-STEWARD:BEGIN commands --> \n"
            "old body\n<!-- PROJECT-STEWARD:END commands -->\t\n")
    assert has_block(text, "commands")
    out = upsert_block(text, "commands", "new body")
    assert out.count("PROJECT-STEWARD:BEGIN commands") == 1
    assert get_block(out, "commands") == "new body"


def test_duplicate_block_is_refused_not_silently_half_updated():
    block = ("<!-- PROJECT-STEWARD:BEGIN x -->\nbody\n"
             "<!-- PROJECT-STEWARD:END x -->\n")
    text = block + "\nprose\n" + block
    with pytest.raises(MarkerError):
        upsert_block(text, "x", "new")


def test_unclosed_block_is_refused():
    text = "<!-- PROJECT-STEWARD:BEGIN x -->\nbody without an end\n"
    with pytest.raises(MarkerError):
        upsert_block(text, "y", "new")


def test_newline_follows_the_first_line_ending_not_any_crlf():
    mixed = "line1\nline2\r\nline3\n"
    out = upsert_block(mixed, "runtime-state", "a\nb", style="hash")
    added = out[len(mixed):]
    assert "\r\n" not in added, added

    crlf = "line1\r\nline2\r\n"
    out = upsert_block(crlf, "runtime-state", "a\nb", style="hash")
    assert "\r\n" in out[len(crlf):]


def test_marker_error_is_a_steward_error():
    assert issubclass(MarkerError, StewardError)
