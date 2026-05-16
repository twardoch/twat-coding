# this_file: src/twat_coding/__main__.py
"""Fire CLI entry point for twat-coding."""

from __future__ import annotations

import fire


def _version() -> str:
    """Print the twat-coding package version."""
    from twat_coding.__version__ import __version__

    return __version__


def _imports_process(file_path: str) -> None:
    """Extract and print all import statements from a Python file.

    Args:
        file_path: Path to the Python file to analyse.
    """
    from twat_coding.pystubnik.read_imports import extract_imports, ast_to_source
    from pathlib import Path

    source = Path(file_path).read_text()
    nodes = extract_imports(source)
    for node in nodes:
        print(ast_to_source(node))


# pystubnik group — wraps PystubnikCLI methods as plain functions
def _pystubnik_generate(
    input_path: str,
    output_path: str | None = None,
    config_file: str | None = None,
) -> None:
    """Generate a .pyi stub file for a single Python source file.

    Args:
        input_path: Path to the Python file to generate stubs for.
        output_path: Optional path to write the stub file (defaults to <input>.pyi).
        config_file: Optional path to a configuration file.
    """
    from twat_coding.pystubnik.cli import PystubnikCLI

    PystubnikCLI().generate(input_path=input_path, output_path=output_path, config_file=config_file)


def _pystubnik_generate_dir(
    input_dir: str,
    output_dir: str | None = None,
    config_file: str | None = None,
) -> None:
    """Generate .pyi stub files for all Python files in a directory.

    Args:
        input_dir: Path to the directory containing Python files.
        output_dir: Optional path to write stubs (defaults to <input_dir>/stubs).
        config_file: Optional path to a configuration file.
    """
    from twat_coding.pystubnik.cli import PystubnikCLI

    PystubnikCLI().generate_dir(input_dir=input_dir, output_dir=output_dir, config_file=config_file)


# Group dict for pystubnik sub-commands
PYSTUBNIK_COMMANDS: dict[str, object] = {
    "generate": _pystubnik_generate,
    "generate-dir": _pystubnik_generate_dir,
}

# Explicit allow-list — only expose implemented behaviour
COMMANDS: dict[str, object] = {
    "version": _version,
    "pystubnik": PYSTUBNIK_COMMANDS,
    "imports": _imports_process,
}


def main() -> None:
    """Main entry point for twat-coding."""
    fire.Fire(COMMANDS, name="twat-coding")


# Per-leaf / per-group dashed-entry helpers
def cmd_version() -> None:
    """Entry point for twat-coding-version."""
    fire.Fire(_version, name="twat-coding-version")


def cmd_pystubnik() -> None:
    """Entry point for twat-coding-pystubnik (group)."""
    fire.Fire(PYSTUBNIK_COMMANDS, name="twat-coding-pystubnik")


def cmd_imports() -> None:
    """Entry point for twat-coding-imports."""
    fire.Fire(_imports_process, name="twat-coding-imports")


if __name__ == "__main__":
    main()
