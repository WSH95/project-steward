from project_steward.state import (parse_front_matter, render_front_matter,
                                   utcnow_iso)


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
