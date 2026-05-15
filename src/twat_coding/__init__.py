"""twat-coding: Python toolkit for code analysis and smart stub generation."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("twat-coding")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from .pystubnik.config import StubConfig
from .pystubnik.processors.stub_generation import StubGenerator

try:
    from .pystubnik.cli import main
except ImportError:

    def main() -> None:
        """CLI entry point for twat-coding."""
        print("twat-coding CLI not configured.")


__all__ = [
    "StubConfig",
    "StubGenerator",
    "__version__",
    "main",
]
