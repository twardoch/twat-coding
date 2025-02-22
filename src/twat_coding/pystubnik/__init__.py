#!/usr/bin/env python3
"""Smart stub generation for Python code.

This package provides tools for generating high-quality type stubs for Python code,
with support for multiple backends and intelligent processing of imports,
docstrings, and code importance.
"""

from pathlib import Path
from typing import Any, Optional, Union
from collections.abc import Mapping, Sequence

from loguru import logger

from .backends import StubBackend
from .backends.ast_backend import AstBackend
from .backends.mypy_backend import MypyBackend
from .core.config import (
    Backend,
    ImportanceLevel,
    PathConfig,
    ProcessingConfig,
    RuntimeConfig,
    StubGenConfig,
    TruncationConfig,
)
from .core.types import (
    ArgInfo,
    ClassInfo,
    FunctionInfo,
    ModuleInfo,
    PathLike,
    StubResult,
)
from .core.utils import setup_logging
from .processors.docstring import DocstringProcessor
from .processors.imports import ImportProcessor
from .processors.importance import ImportanceProcessor


class SmartStubGenerator:
    """Main interface for generating smart stubs."""

    def __init__(
        self,
        *,
        # Path configuration
        output_dir: str | Path = "out",
        doc_dir: str | Path | None = None,
        search_paths: Sequence[str | Path] = (),
        modules: Sequence[str] = (),
        packages: Sequence[str] = (),
        files: Sequence[str | Path] = (),
        # Runtime configuration
        backend: Backend | str = Backend.HYBRID,
        python_version: tuple[int, int] | None = None,
        interpreter: str | Path | None = None,
        no_import: bool = False,
        inspect: bool = False,
        parse_only: bool = False,
        ignore_errors: bool = True,
        verbose: bool = False,
        quiet: bool = True,
        parallel: bool = True,
        max_workers: int | None = None,
        # Processing configuration
        include_docstrings: bool = True,
        include_private: bool = False,
        include_type_comments: bool = True,
        infer_property_types: bool = True,
        export_less: bool = False,
        importance_patterns: Mapping[str, float] | None = None,
        importance_keywords: set[str] | None = None,
        # Truncation configuration
        max_sequence_length: int | None = None,
        max_string_length: int | None = None,
        max_docstring_length: int | None = None,
        max_file_size: int | None = None,
        truncation_marker: str | None = None,
    ):
        """Initialize the stub generator with configuration.

        Args:
            output_dir: Directory to write stubs to
            doc_dir: Directory containing .rst documentation
            search_paths: Module search paths
            modules: Module names to process
            packages: Package names to process recursively
            files: Specific files to process
            backend: Stub generation backend (AST, MYPY, or HYBRID)
            python_version: Python version to target
            interpreter: Python interpreter to use
            no_import: Don't import modules
            inspect: Use runtime inspection
            parse_only: Only parse, no semantic analysis
            ignore_errors: Continue on errors
            verbose: Show detailed output
            quiet: Minimal output
            parallel: Use parallel processing
            max_workers: Maximum worker threads
            include_docstrings: Include docstrings in stubs
            include_private: Include private symbols
            include_type_comments: Include type comments
            infer_property_types: Try to infer property types
            export_less: Don't export imported names
            importance_patterns: Patterns for importance scoring
            importance_keywords: Keywords indicating importance
            max_sequence_length: Maximum sequence length
            max_string_length: Maximum string length
            max_docstring_length: Maximum docstring length
            max_file_size: Maximum file size
            truncation_marker: Marker for truncated content
        """
        # Convert backend string to enum
        if isinstance(backend, str):
            backend = Backend[backend.upper()]

        # Create configuration objects
        self.config = StubGenConfig(
            paths=PathConfig(
                output_dir=Path(output_dir),
                doc_dir=Path(doc_dir) if doc_dir else None,
                search_paths=[Path(p) for p in search_paths],
                modules=list(modules),
                packages=list(packages),
                files=[Path(f) for f in files],
            ),
            runtime=RuntimeConfig.create(
                backend=backend,
                python_version=python_version,
                interpreter=interpreter,
                no_import=no_import,
                inspect=inspect,
                parse_only=parse_only,
                ignore_errors=ignore_errors,
                verbose=verbose,
                quiet=quiet,
                parallel=parallel,
                max_workers=max_workers,
            ),
            processing=ProcessingConfig(
                include_docstrings=include_docstrings,
                include_private=include_private,
                include_type_comments=include_type_comments,
                infer_property_types=infer_property_types,
                export_less=export_less,
                importance_patterns=dict(importance_patterns or {}),
                importance_keywords=set(importance_keywords or set()),
            ),
            truncation=TruncationConfig(
                max_sequence_length=max_sequence_length or 4,
                max_string_length=max_string_length or 17,
                max_docstring_length=max_docstring_length or 150,
                max_file_size=max_file_size or 3_000,
                truncation_marker=truncation_marker or "...",
            ),
        )

        # Configure logging
        logger.remove()
        logger.add(
            lambda msg: print(msg, end=""),
            format="<blue>{time:HH:mm:ss}</blue> | {message}",
            level="DEBUG" if verbose else "INFO",
            enabled=not quiet,
        )

    def generate(self) -> None:
        """Generate stubs according to configuration."""
        try:
            logger.info(
                f"Generating stubs using {self.config.runtime.backend.name} backend"
            )
            logger.info(f"Output directory: {self.config.paths.output_dir}")

            # TODO: Implement stub generation logic
            # This will be implemented in subsequent commits as we
            # reorganize the existing code into the new structure

            logger.info("Stub generation completed successfully")

        except Exception as e:
            logger.error(f"Failed to generate stubs: {e}")
            if self.config.runtime.verbose:
                import traceback

                logger.debug(traceback.format_exc())
            if not self.config.runtime.ignore_errors:
                raise

    def generate_for_file(self, file_path: str | Path) -> str:
        """Generate stub for a single file.

        Args:
            file_path: Path to the Python file

        Returns:
            Generated stub content
        """
        # TODO: Implement single file stub generation
        raise NotImplementedError

    def generate_for_module(self, module_name: str) -> str:
        """Generate stub for a module by name.

        Args:
            module_name: Fully qualified module name

        Returns:
            Generated stub content
        """
        # TODO: Implement module stub generation
        raise NotImplementedError


def generate_stub(
    source_path: PathLike,
    output_path: PathLike | None = None,
    backend: str = "ast",
    config: StubGenConfig | None = None,
) -> StubResult:
    """Generate a type stub for a Python source file.

    Args:
        source_path: Path to the source file
        output_path: Optional path to write the stub file
        backend: Backend to use for stub generation ("ast" or "mypy")
        config: Optional configuration for stub generation

    Returns:
        StubResult containing the generated stub and metadata

    Raises:
        ValueError: If the specified backend is not supported
    """
    source_path = Path(source_path)
    if output_path:
        output_path = Path(output_path)

    config = config or StubGenConfig(paths=PathConfig())

    # Initialize backend
    if backend == "ast":
        backend_impl = AstBackend(config)
    elif backend == "mypy":
        backend_impl = MypyBackend(config)
    else:
        msg = f"Unsupported backend: {backend}"
        raise ValueError(msg)

    # Generate initial stub
    result = backend_impl.generate_stub(source_path, output_path)

    # Apply processors
    processors = [
        ImportProcessor(),
        DocstringProcessor(
            include_docstrings=config.include_docstrings,
            doc_format=config.doc_format,
        ),
        ImportanceProcessor(
            min_importance=config.min_importance,
            importance_patterns=config.importance_patterns,
        ),
    ]

    for processor in processors:
        result = processor.process(result)

    # Write output if path specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.stub_content)

    return result


# Configure default logging
setup_logging()

# Version information
__version__ = "0.1.0"
__author__ = "Adam Twardoch"
__license__ = "MIT"

__all__ = [
    "ArgInfo",
    "AstBackend",
    "Backend",
    "ClassInfo",
    "FunctionInfo",
    "ImportanceLevel",
    "ModuleInfo",
    "MypyBackend",
    "SmartStubGenerator",
    "StubBackend",
    "StubGenConfig",
    "StubResult",
    "generate_stub",
]
