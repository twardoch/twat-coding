# this_file: tests/test_cli.py
"""Tests for twat-coding Fire CLI entry points."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "twat_coding", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _help_output(result: subprocess.CompletedProcess[str]) -> str:
    """Fire writes help to stderr; fall back to stdout."""
    return result.stderr or result.stdout


def test_help_exits_zero():
    """twat-coding --help exits 0 and prints a command listing."""
    result = run(["--help"])
    assert result.returncode == 0
    assert _help_output(result)


def test_version_leaf():
    """twat-coding version prints a semver string."""
    result = run(["version"])
    assert result.returncode == 0
    version = (result.stdout or result.stderr).strip()
    assert version, "version output must not be empty"
    parts = version.split(".")
    assert len(parts) >= 2, f"Expected semver, got: {version!r}"


def test_pystubnik_help():
    """twat-coding pystubnik --help exits 0."""
    result = run(["pystubnik", "--help"])
    assert result.returncode == 0
    assert _help_output(result)


def test_pystubnik_generate_help():
    """twat-coding pystubnik generate --help exits 0."""
    result = run(["pystubnik", "generate", "--help"])
    assert result.returncode == 0
    assert _help_output(result)


def test_pystubnik_generate_dir_help():
    """twat-coding pystubnik generate-dir --help exits 0."""
    result = run(["pystubnik", "generate-dir", "--help"])
    assert result.returncode == 0
    assert _help_output(result)


def test_imports_help():
    """twat-coding imports --help exits 0."""
    result = run(["imports", "--help"])
    assert result.returncode == 0
    assert _help_output(result)


def test_imports_process(tmp_path: Path):
    """twat-coding imports processes a Python file and prints import lines."""
    py_file = tmp_path / "sample.py"
    py_file.write_text("import os\nfrom pathlib import Path\n")
    result = run(["imports", str(py_file)])
    assert result.returncode == 0
    output = result.stdout
    assert "import os" in output
    assert "from pathlib import Path" in output
