#!/usr/bin/env -S uv run
"""Base interface for stub generation backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Union

from .. import _convert_to_stub_gen_config
from ..config import StubConfig
from ..core.config import PathConfig, StubGenConfig
from ..core.types import StubResult


class StubBackend(ABC):
    """Base class for stub generation backends."""

    def __init__(self, config: Union[StubConfig, StubGenConfig] | None = None) -> None:
        """Initialize the backend.

        Args:
            config: Configuration for stub generation
        """
        # Convert StubConfig to StubGenConfig if needed
        if isinstance(config, StubConfig):
            self._config = _convert_to_stub_gen_config(config)
        else:
            self._config = config or StubGenConfig(paths=PathConfig())

    @abstractmethod
    async def generate_stub(self, source_path: Path) -> StubResult:
        """Generate a stub for a Python source file.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub result
        """
        raise NotImplementedError

    @abstractmethod
    async def process_module(self, module_name: str) -> StubResult:
        """Process a module by its import name.

        Args:
            module_name: Fully qualified module name

        Returns:
            Generated stub result

        Raises:
            StubGenerationError: If module processing fails
        """
        raise NotImplementedError

    @abstractmethod
    async def process_package(self, package_path: Path) -> dict[Path, StubResult]:
        """Process a package directory recursively.

        Args:
            package_path: Path to the package directory

        Returns:
            Dictionary mapping output paths to stub results

        Raises:
            StubGenerationError: If package processing fails
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources used by the backend.

        This method should be called when the backend is no longer needed.
        """
        pass

    def __enter__(self) -> "StubBackend":
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager."""
        self.cleanup()
