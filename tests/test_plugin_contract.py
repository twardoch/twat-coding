"""Smoke tests for the twat_coding plugin contract."""

from __future__ import annotations

import subprocess
import sys
from importlib import metadata

import twat_coding


def test_public_contract_exports() -> None:
    """The package exposes the public API used by callers and the twat host."""
    assert isinstance(twat_coding.__version__, str)
    assert callable(twat_coding.main)
    assert "__version__" in twat_coding.__all__
    assert "main" in twat_coding.__all__
    assert "StubConfig" in twat_coding.__all__
    assert "StubGenerator" in twat_coding.__all__


def test_installed_entry_points() -> None:
    """Installed metadata exposes the direct CLI and twat plugin entry."""
    console_scripts = metadata.entry_points(group="console_scripts")
    scripts = {entry_point.name: entry_point.value for entry_point in console_scripts}
    assert scripts["twat-coding"] == "twat_coding.pystubnik.cli:main"

    plugin_entries = metadata.entry_points(group="twat.plugins")
    plugins = {entry_point.name: entry_point.value for entry_point in plugin_entries}
    assert plugins["coding"] == "twat_coding"


def test_python_module_help_smoke() -> None:
    """`python -m twat_coding --help` reaches the pystubnik CLI."""
    result = subprocess.run(
        [sys.executable, "-m", "twat_coding", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "CLI interface for pystubnik" in output
