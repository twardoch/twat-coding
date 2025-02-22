"""Backend interface and registry for stub generation.

This module provides the abstract base class for stub generation backends
and a registry to manage different backend implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Protocol, Type

from pystubnik.core.types import StubResult


class StubBackend(Protocol):
    """Protocol defining the interface for stub generation backends."""

    @abstractmethod
    def generate_stub(
        self, source_path: Path, output_path: Path | None = None
    ) -> StubResult:
        """Generate stub for the given source file.

        Args:
            source_path: Path to the source file
            output_path: Optional path to write the stub file

        Returns:
            StubResult containing the generated stub and metadata
        """
        ...


_backends: dict[str, type[StubBackend]] = {}


def register_backend(name: str, backend: type[StubBackend]) -> None:
    """Register a new backend implementation."""
    _backends[name] = backend


def get_backend(name: str) -> type[StubBackend]:
    """Get a registered backend by name."""
    if name not in _backends:
        msg = f"Backend '{name}' not found"
        raise KeyError(msg)
    return _backends[name]


def list_backends() -> list[str]:
    """List all registered backend names."""
    return list(_backends.keys())
