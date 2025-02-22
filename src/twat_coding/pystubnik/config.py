#!/usr/bin/env -S uv run
"""Configuration system for stub generation."""

import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .core.config import PathConfig, StubGenConfig
from .errors import ConfigError, ErrorCode


class FileLocations(BaseModel):
    """File locations for stub generation."""

    source_path: Path = Field(..., description="Path to Python source file")
    input_dir: Path = Field(..., description="Base input directory")
    output_dir: Path = Field(..., description="Base output directory")

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: Path) -> Path:
        """Validate source file exists."""
        if not v.exists():
            raise ConfigError(
                "Source file does not exist",
                ErrorCode.CONFIG_VALIDATION_ERROR,
                source=str(v),
            )
        return v

    @field_validator("input_dir")
    @classmethod
    def validate_input_dir(cls, v: Path) -> Path:
        """Validate input directory exists."""
        if not v.exists():
            raise ConfigError(
                "Input directory does not exist",
                ErrorCode.CONFIG_VALIDATION_ERROR,
                source=str(v),
            )
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Validate and create output directory."""
        try:
            v.mkdir(parents=True, exist_ok=True)
            return v
        except Exception as e:
            raise ConfigError(
                f"Failed to create output directory: {e}",
                ErrorCode.CONFIG_IO_ERROR,
                source=str(v),
            ) from e

    @property
    def output_path(self) -> Path:
        """Calculate output path based on input path and bases."""
        try:
            rel_path = self.source_path.relative_to(self.input_dir)
            return self.output_dir / rel_path
        except ValueError as e:
            raise ConfigError(
                f"Source file {self.source_path} is not within input directory {self.input_dir}",
                ErrorCode.CONFIG_VALIDATION_ERROR,
            ) from e

    def check_paths(self) -> None:
        """Validate file locations and create output directories."""
        # Create output directory and verify permissions
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        if not os.access(self.output_path.parent, os.W_OK):
            raise ConfigError(
                f"No write permission: {self.output_path.parent}",
                ErrorCode.CONFIG_IO_ERROR,
                source=str(self.output_path.parent),
            )


def _default_stub_gen_config() -> StubGenConfig:
    """Create default StubGenConfig instance.

    Returns:
        Default StubGenConfig instance
    """
    return StubGenConfig(paths=PathConfig())


class StubConfig(BaseModel):
    """Configuration for stub generation."""

    model_config = SettingsConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=True,
    )

    # Input/Output settings
    input_path: Path = Field(
        ...,
        description="Path to Python source files or directory",
    )
    output_path: Path | None = Field(
        None,
        description="Path to output directory for stubs",
    )
    files: list[Path] = Field(
        default_factory=list,
        description="List of files to process",
    )
    include_patterns: list[str] = Field(
        default_factory=lambda: ["*.py"],
        description="Glob patterns for files to include",
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["test_*.py", "*_test.py"],
        description="Glob patterns for files to exclude",
    )

    # Processing settings
    backend: Literal["ast", "mypy"] = Field(
        "ast",
        description="Backend to use for stub generation",
    )
    parallel: bool = Field(
        True,
        description="Enable parallel processing",
    )
    max_workers: int | None = Field(
        None,
        description="Maximum number of worker threads",
        ge=1,
    )

    # Stub generation settings
    stub_gen_config: StubGenConfig = Field(
        default_factory=_default_stub_gen_config,
        description="Configuration for stub generation",
    )

    # Type inference settings
    infer_types: bool = Field(
        True,
        description="Enable type inference",
    )
    preserve_literals: bool = Field(
        False,
        description="Preserve literal values in stubs",
    )
    docstring_type_hints: bool = Field(
        True,
        description="Extract type hints from docstrings",
    )

    # Output settings
    line_length: int = Field(
        88,
        description="Maximum line length for output",
        ge=1,
    )
    sort_imports: bool = Field(
        True,
        description="Sort imports in output",
    )
    add_header: bool = Field(
        True,
        description="Add header to generated files",
    )

    # MyPy-specific settings
    python_version: tuple[int, int] = Field(
        default_factory=lambda: (sys.version_info.major, sys.version_info.minor),
        description="Python version to target",
    )
    no_import: bool = Field(
        False,
        description="Don't import modules, just parse and analyze",
    )
    inspect: bool = Field(
        False,
        description="Import and inspect modules instead of parsing source",
    )
    doc_dir: str = Field(
        "",
        description="Path to .rst documentation directory",
    )
    search_paths: Sequence[str | Path] = Field(
        default_factory=list,
        description="Module search paths",
    )
    interpreter: str | Path = Field(
        default_factory=lambda: sys.executable,
        description="Python interpreter to use",
    )
    ignore_errors: bool = Field(
        True,
        description="Ignore errors during stub generation",
    )
    parse_only: bool = Field(
        False,
        description="Don't do semantic analysis of source",
    )
    include_private: bool = Field(
        False,
        description="Include private objects in stubs",
    )
    modules: Sequence[str] = Field(
        default_factory=list,
        description="List of module names to process",
    )

    def get_file_locations(self, source_path: Path) -> FileLocations:
        """Get file locations for a source file.

        Args:
            source_path: Path to source file

        Returns:
            FileLocations object
        """
        return FileLocations(
            source_path=source_path,
            input_dir=self.input_path,
            output_dir=self.output_path or Path("out"),
        )


class RuntimeConfig(BaseSettings):
    """Runtime configuration for the application."""

    model_config = SettingsConfigDict(
        env_prefix="PYSTUBNIK_",
        env_file=".env",
        extra="ignore",
    )

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_file: Path | None = None

    # Performance settings
    cache_dir: Path = Field(default_factory=lambda: Path(".cache"))
    memory_limit: int | None = None  # In megabytes
    timeout: int | None = None  # In seconds

    # Development settings
    debug: bool = False
    profile: bool = False

    @field_validator("cache_dir", mode="before")
    @classmethod
    def validate_cache_dir(cls, v: Any) -> Path:
        """Validate and create cache directory."""
        try:
            path = Path(v)
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise ConfigError(
                f"Failed to create cache directory: {e}",
                ErrorCode.CONFIG_IO_ERROR,
                source=str(v),
            ) from e
