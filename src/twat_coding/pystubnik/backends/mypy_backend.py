"""MyPy-based stub generation backend.

This module implements stub generation using MyPy's stubgen functionality,
based on the original make_stubs_mypy.py implementation.
"""

from pathlib import Path

from pystubnik.backends import StubBackend
from pystubnik.core.config import PathConfig, StubGenConfig
from pystubnik.core.types import StubResult


class MypyBackend(StubBackend):
    """MyPy-based stub generation backend."""

    def __init__(self, config: StubGenConfig | None = None):
        self.config = config or StubGenConfig(paths=PathConfig())

    def generate_stub(
        self, source_path: Path, output_path: Path | None = None
    ) -> StubResult:
        """Generate stub for the given source file using MyPy's stubgen.

        Args:
            source_path: Path to the source file
            output_path: Optional path to write the stub file

        Returns:
            StubResult containing the generated stub and metadata
        """
        # TODO: Port functionality from make_stubs_mypy.py
        msg = "MyPy backend not yet implemented"
        raise NotImplementedError(msg)
