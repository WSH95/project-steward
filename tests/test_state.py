import os
import stat

import pytest

from project_steward import StewardError
from project_steward.state import (load_state, parse_front_matter,
                                   update_front_matter, render_front_matter,
                                   utcnow_iso, write_text_atomic)


def test_front_matter_roundtrip():
    body = "# Handoff\n\n## Now\nthings\n"
    text = render_front_matter({"session_status": "closed", "branch": "main"},
                               body)
    meta, parsed_body = parse_front_matter(text)
    assert meta["session_status"] == "closed"
    assert parsed_body.strip() == body.strip()


def test_missing_front_matter_tolerated():
    meta, body = parse_front_matter("# no fm\n")
    assert meta == {} and body.startswith("# no fm")


def test_utcnow_format():
    assert utcnow_iso().endswith("Z") and "T" in utcnow_iso()


def test_write_text_atomic_retries_transient_lock(tmp_path, monkeypatch):
    target = tmp_path / "out.txt"
    real_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] < 3:
            raise PermissionError("locked")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)
    write_text_atomic(target, "data")
    assert calls["n"] == 3
    assert target.read_text(encoding="utf-8") == "data"


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_write_text_atomic_preserves_existing_mode(tmp_path):
    target = tmp_path / "HANDOFF.md"
    target.write_text("before\n", encoding="utf-8")
    os.chmod(str(target), 0o644)
    write_text_atomic(target, "after\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o644

    os.chmod(str(target), 0o664)
    write_text_atomic(target, "again\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o664


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_write_text_atomic_new_file_is_not_owner_only(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_text_atomic(target, "new\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o644


def test_load_state_refuses_corrupt_file(tmp_path):
    sdir = tmp_path / ".project-steward"
    sdir.mkdir()
    corrupt = sdir / "state.json"
    corrupt.write_text('{"project_name": "Demo",,,', encoding="utf-8")
    with pytest.raises(StewardError):
        load_state(tmp_path)
    assert corrupt.read_text(encoding="utf-8") == '{"project_name": "Demo",,,'


def test_load_state_defaults_when_absent(tmp_path):
    (tmp_path / ".project-steward").mkdir()
    assert load_state(tmp_path)["schema_version"] == 1


def test_front_matter_update_preserves_crlf(tmp_path):
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_bytes(b"---\r\nupdated_at: old\r\n---\r\n\r\n"
                        b"# Handoff\r\n\r\n## Now\r\nbody\r\n")
    update_front_matter(handoff, {"updated_at": "new"})
    raw = handoff.read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")   # no bare LF left behind
    assert b"updated_at: new" in raw


def test_front_matter_update_leaves_lf_files_alone(tmp_path):
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_bytes(b"---\nupdated_at: old\n---\n\n# Handoff\n")
    update_front_matter(handoff, {"updated_at": "new"})
    assert b"\r" not in handoff.read_bytes()


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlinks")
def test_write_text_atomic_writes_through_a_symlink(tmp_path):
    real = tmp_path / "shared-context.md"
    real.write_text("original\n", encoding="utf-8")
    link = tmp_path / "AGENTS.md"
    link.symlink_to(real)
    write_text_atomic(link, "updated\n")
    assert link.is_symlink(), "the link itself must survive"
    assert real.read_text(encoding="utf-8") == "updated\n"
