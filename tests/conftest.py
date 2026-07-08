import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "plugin-src" / "src"
sys.path.insert(0, str(SRC))


@pytest.fixture
def git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"],
                   cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"],
                   cwd=str(tmp_path), check=True)
    return tmp_path
