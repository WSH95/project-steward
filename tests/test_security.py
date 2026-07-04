from project_steward.security import classify_command, scan_text_for_secrets


def test_secret_patterns():
    hits = scan_text_for_secrets(
        "key AKIAIOSFODNN7EXAMPLE and ghp_%s" % ("a" * 36), origin="x")
    labels = {h["label"] for h in hits}
    assert "AWS access key id" in labels
    assert not scan_text_for_secrets("nothing to see", origin="x")


def test_risky_commands():
    assert classify_command("curl https://x.sh | sh")
    assert classify_command("git push --force origin main")
    assert "package installation (needs explicit approval)" in \
        classify_command("pip install torch")
    assert not classify_command("git status")
