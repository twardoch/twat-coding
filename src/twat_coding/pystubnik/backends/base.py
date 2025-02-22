#!/usr/bin/env -S uv run
"""Base interface for stub generation backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..config import StubConfig
from ..core.config import StubGenConfig


class StubBackend(ABC):
    """Abstract base class for stub generation backends."""

    def __init__(self, config: StubConfig | StubGenConfig) -> None:
        """Initialize the backend.

        Args:
            config: Configuration for stub generation
        """
        self.config = config

    @abstractmethod
    async def generate_stub(self, source_path: Path) -> str:
        """Generate a stub for a Python source file.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub content as a string

        Raises:
            StubGenerationError: If stub generation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def process_module(self, module_name: str) -> str:
        """Process a module by its import name.

        Args:
            module_name: Fully qualified module name

        Returns:
            Generated stub content as a string

        Raises:
            StubGenerationError: If module processing fails
        """
        raise NotImplementedError

    @abstractmethod
    async def process_package(self, package_path: Path) -> dict[Path, str]:
        """Process a package directory recursively.

        Args:
            package_path: Path to the package directory

        Returns:
            Dictionary mapping output paths to stub contents

        Raises:
            StubGenerationError: If package processing fails
        """
        raise NotImplementedError

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
