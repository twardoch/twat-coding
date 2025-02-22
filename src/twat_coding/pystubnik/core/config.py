#!/usr/bin/env python3
"""Configuration for pystubnik stub generation."""

import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any
from collections.abc import Mapping, Sequence


class Backend(Enum):
    """Available stub generation backends."""

    AST = auto()  # Use Python's AST for precise control
    MYPY = auto()  # Use MyPy's stubgen for better type inference
    HYBRID = auto()  # Use both and merge results


class ImportanceLevel(Enum):
    """Importance levels for code elements."""

    CRITICAL = 1.5  # Must preserve exactly
    HIGH = 1.2  # Should preserve most details
    NORMAL = 1.0  # Standard preservation
    LOW = 0.8  # Minimal preservation
    IGNORE = 0.0  # Can be omitted


@dataclass(frozen=True)
class TruncationConfig:
    """Configuration for code truncation."""

    max_sequence_length: int = 4  # For lists, dicts, sets, tuples
    max_string_length: int = 17  # For strings except docstrings
    max_docstring_length: int = 150  # Default max length for docstrings
    max_file_size: int = 3_000  # Default max file size before removing all docstrings
    truncation_marker: str = "..."


def _default_importance_keywords() -> set[str]:
    """Get default importance keywords.

    Returns:
        Set of default importance keywords
    """
    return {"important", "critical", "essential", "main", "key"}


@dataclass(frozen=True)
class ProcessingConfig:
    """Configuration for stub processing."""

    include_docstrings: bool = True
    include_private: bool = False
    include_type_comments: bool = True
    infer_property_types: bool = True
    export_less: bool = False
    importance_patterns: Mapping[str, float] = field(default_factory=dict)
    importance_keywords: set[str] = field(default_factory=_default_importance_keywords)


@dataclass(frozen=True)
class PathConfig:
    """Configuration for file paths and search."""

    output_dir: Path = Path("out")
    doc_dir: Path | None = None
    search_paths: Sequence[Path] = field(default_factory=list)
    modules: Sequence[str] = field(default_factory=list)
    packages: Sequence[str] = field(default_factory=list)
    files: Sequence[Path] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeConfig:
    """Configuration for runtime behavior."""

    backend: Backend = Backend.HYBRID
    python_version: tuple[int, int] = field(
        default_factory=lambda: sys.version_info[:2]
    )
    interpreter: Path = field(default_factory=lambda: Path(sys.executable))
    no_import: bool = False
    inspect: bool = False
    parse_only: bool = False
    ignore_errors: bool = True
    verbose: bool = False
    quiet: bool = True
    parallel: bool = True
    max_workers: int | None = None

    @classmethod
    def create(
        cls,
        *,
        python_version: tuple[int, int] | None = None,
        interpreter: Path | str | None = None,
        **kwargs: Any,
    ) -> "RuntimeConfig":
        """Create a RuntimeConfig with optional version and interpreter.

        Args:
            python_version: Optional Python version tuple
            interpreter: Optional interpreter path
            **kwargs: Additional configuration options

        Returns:
            RuntimeConfig instance
        """
        if python_version is None:
            python_version = sys.version_info[:2]

        if interpreter is None:
            interpreter = Path(sys.executable)
        elif isinstance(interpreter, str):
            interpreter = Path(interpreter)

        return cls(
            python_version=python_version,
            interpreter=interpreter,
            **kwargs,
        )


@dataclass(frozen=True)
class StubGenConfig:
    """Main configuration for stub generation."""

    paths: PathConfig
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    truncation: TruncationConfig = field(default_factory=TruncationConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StubGenConfig":
        """Create configuration from a dictionary."""
        paths = PathConfig(**data.get("paths", {}))
        runtime = RuntimeConfig(**data.get("runtime", {}))
        processing = ProcessingConfig(**data.get("processing", {}))
        truncation = TruncationConfig(**data.get("truncation", {}))
        return cls(
            paths=paths,
            runtime=runtime,
            processing=processing,
            truncation=truncation,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "paths": {
                k: str(v) if isinstance(v, Path) else v
                for k, v in self.paths.__dict__.items()
            },
            "runtime": self.runtime.__dict__,
            "processing": self.processing.__dict__,
            "truncation": self.truncation.__dict__,
        }
