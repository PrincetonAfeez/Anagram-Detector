"""Test the CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    return subprocess.run(
        [sys.executable, "-m", "anagram_detector", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_check(cwd: Path = Path.cwd()) -> None:
    result = run_cli("check", "listen", "silent", cwd=cwd)

    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_cli_json_find(cwd: Path = Path.cwd()) -> None:
    result = run_cli("--format", "json", "find", "listen", cwd=cwd)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert {match["original"] for match in payload["matches"]} >= {"listen", "silent"}


def test_cli_group_from_stdin(cwd: Path = Path.cwd()) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    result = subprocess.run(
        [sys.executable, "-m", "anagram_detector", "group", "-"],
        input="care\nrace\nacre\nhello\n",
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "care" in result.stdout
    assert "race" in result.stdout


def test_cli_rejects_invalid_min_length(cwd: Path = Path.cwd()) -> None:
    result = run_cli("--min-length", "0", "find", "listen", cwd=cwd)

    assert result.returncode != 0
    assert "min-length must be >= 1" in result.stderr


def test_cli_rejects_invalid_max_words(cwd: Path = Path.cwd()) -> None:
    result = run_cli("multi", "listen", "--max-words", "1", cwd=cwd)

    assert result.returncode != 0
    assert "max-words must be >= 2" in result.stderr
