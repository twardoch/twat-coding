"""Backend interface and registry for stub generation.

This module provides the abstract base class for stub generation backends
and a registry to manage different backend implementations.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Protocol

from twat_coding.pystubnik.core.types import StubResult


class StubBackend(Protocol):
    """Protocol defining the interface for stub generation backends."""

    @abstractmethod
    async def generate_stub(self, source_path: Path) -> StubResult:
        """Generate a stub for a Python source file.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub result

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
