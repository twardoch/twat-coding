"""Processor interface and registry for stub generation.

This module provides the base classes and interfaces for different
processors that can be used during stub generation.
"""

from abc import abstractmethod
from typing import Protocol

from pystubnik.core.types import StubResult


class Processor(Protocol):
    """Protocol defining the interface for stub processors."""

    @abstractmethod
    def process(self, stub_result: StubResult) -> StubResult:
        """Process a stub generation result.

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result
        """
        ...


_processors: dict[str, type[Processor]] = {}


def register_processor(name: str, processor: type[Processor]) -> None:
    """Register a new processor implementation."""
    _processors[name] = processor


def get_processor(name: str) -> type[Processor]:
    """Get a registered processor by name."""
    if name not in _processors:
        msg = f"Processor '{name}' not found"
        raise KeyError(msg)
    return _processors[name]


def list_processors() -> list[str]:
    """List all registered processor names."""
    return list(_processors.keys())
