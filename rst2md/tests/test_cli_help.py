import subprocess
import sys
import os

import pytest

TEST_ENV = {**os.environ, "PYTHONPATH": "rst2md"}


@pytest.mark.parametrize("command,expected", [
    ("s-class", "query"),
    ("s-tutorial", "query"),
    ("s-engine", "query"),
    ("diagnostics", "--db"),
])
def test_cli_help_commands(command, expected):
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", command, "--help"],
        text=True,
        capture_output=True,
        env=TEST_ENV,
    )
    assert result.returncode == 0
    assert expected in result.stdout