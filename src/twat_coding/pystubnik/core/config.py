"""Configuration for pystubnik stub generation."""

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from twat_coding.pystubnik.core.shared_types import TruncationConfig


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


def _default_include_patterns() -> list[str]:
    """Get default include patterns.

    Returns:
        List of default include patterns

    """
    return ["*.py"]


def _default_exclude_patterns() -> list[str]:
    """Get default exclude patterns.

    Returns:
        List of default exclude patterns

    """
    return ["test_*.py", "*_test.py"]


@dataclass(frozen=True)
class PathConfig:
    """Configuration for file paths and search."""

    output_dir: Path = Path("out")
    doc_dir: Path | None = None
    search_paths: Sequence[Path] = field(default_factory=list)
    modules: Sequence[str] = field(default_factory=list)
    packages: Sequence[str] = field(default_factory=list)
    files: Sequence[Path] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=_default_include_patterns)
    exclude_patterns: list[str] = field(default_factory=_default_exclude_patterns)


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

    # Convenience properties to access common settings
    @property
    def include_patterns(self) -> list[str]:
        """Get include patterns."""
        return self.paths.include_patterns

    @property
    def exclude_patterns(self) -> list[str]:
        """Get exclude patterns."""
        return self.paths.exclude_patterns

    @property
    def ignore_errors(self) -> bool:
        """Get ignore errors setting."""
        return self.runtime.ignore_errors

    def get_file_locations(self, source_path: Path) -> tuple[Path, Path]:
        """Get input and output paths for a source file.

        Args:
            source_path: Path to source file

        Returns:
            Tuple of (input_path, output_path)

        """
        try:
            rel_path = source_path.relative_to(self.paths.output_dir)
            output_path = self.paths.output_dir / rel_path
            return source_path, output_path
        except ValueError as e:
            raise ValueError(
                f"Source file {source_path} is not within output directory {self.paths.output_dir}"
            ) from e

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
