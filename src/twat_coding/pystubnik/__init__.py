#!/usr/bin/env python3
"""Smart stub generation for Python code.

This package provides tools for generating high-quality type stubs for Python code,
with support for multiple backends and intelligent processing of imports,
docstrings, and code importance.
"""

import asyncio
import sys
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Literal, Protocol

from loguru import logger

from .backends import StubBackend
from .backends.ast_backend import ASTBackend
from .backends.mypy_backend import MypyBackend
from .config import StubConfig
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
from .errors import ASTError, ConfigError, ErrorCode, MyPyError, StubGenerationError
from .processors.docstring import DocstringProcessor
from .processors.importance import ImportanceConfig, ImportanceProcessor
from .processors.imports import ImportProcessor


def _convert_to_stub_config(config: StubGenConfig) -> StubConfig:
    """Convert StubGenConfig to StubConfig.

    Args:
        config: Source configuration

    Returns:
        Converted configuration
    """
    # Convert paths to strings for search_paths
    search_paths = [str(p) for p in config.paths.search_paths]

    # Convert files to list[Path]
    files = list(config.paths.files)  # Convert Sequence to list

    return StubConfig(
        input_path=config.paths.files[0] if config.paths.files else Path("."),
        output_path=config.paths.output_dir,
        backend="ast",  # Default to AST backend
        parallel=config.runtime.parallel,
        max_workers=config.runtime.max_workers,
        infer_types=config.processing.infer_property_types,
        preserve_literals=True,  # We handle this in the AST backend
        docstring_type_hints=config.processing.include_docstrings,
        python_version=config.runtime.python_version,
        no_import=config.runtime.no_import,
        inspect=config.runtime.inspect,
        doc_dir=str(config.paths.doc_dir) if config.paths.doc_dir else "",
        search_paths=search_paths,
        interpreter=config.runtime.interpreter,
        ignore_errors=config.runtime.ignore_errors,
        parse_only=config.runtime.parse_only,
        include_private=config.processing.include_private,
        modules=list(config.paths.modules),  # Convert Sequence to list
        packages=list(config.paths.packages),  # Convert Sequence to list
        files=files,
        verbose=config.runtime.verbose,
        quiet=config.runtime.quiet,
        export_less=config.processing.export_less,
        importance_patterns=dict(config.processing.importance_patterns),
        max_docstring_length=config.truncation.max_docstring_length,
        include_type_comments=config.processing.include_type_comments,
        infer_property_types=config.processing.infer_property_types,
        line_length=88,  # Default line length
        sort_imports=True,  # Default to sorting imports
        add_header=True,  # Default to adding header
    )


def _convert_to_stub_gen_config(config: StubConfig) -> StubGenConfig:
    """Convert StubConfig to StubGenConfig.

    Args:
        config: Source configuration

    Returns:
        Converted configuration
    """
    return StubGenConfig(
        paths=PathConfig(
            output_dir=config.output_path or Path("out"),
            doc_dir=Path(config.doc_dir) if config.doc_dir else None,
            search_paths=[Path(p) for p in config.search_paths],
            modules=list(config.modules),
            packages=list(config.packages),
            files=list(config.files),
        ),
        runtime=RuntimeConfig.create(
            backend=Backend.AST if config.backend == "ast" else Backend.MYPY,
            python_version=config.python_version,
            interpreter=config.interpreter,
            no_import=config.no_import,
            inspect=config.inspect,
            parse_only=config.parse_only,
            ignore_errors=config.ignore_errors,
            verbose=config.verbose,
            quiet=config.quiet,
            parallel=config.parallel,
            max_workers=config.max_workers,
        ),
        processing=ProcessingConfig(
            include_docstrings=config.docstring_type_hints,
            include_private=config.include_private,
            include_type_comments=config.include_type_comments,
            infer_property_types=config.infer_property_types,
            export_less=config.export_less,
            importance_patterns=dict(config.importance_patterns),
        ),
        truncation=TruncationConfig(
            max_docstring_length=config.max_docstring_length,
        ),
    )


class Processor(Protocol):
    """Protocol for stub processors."""

    def process(self, stub_result: StubResult) -> StubResult:
        """Process a stub result.

        Args:
            stub_result: Input stub result

        Returns:
            Processed stub result
        """
        ...


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
            catch=True,
        )

        # Initialize processors
        self.processors: list[Processor] = [
            DocstringProcessor(
                style="google",
                max_length=self.config.truncation.max_docstring_length,
                preserve_sections=["Args", "Returns", "Yields", "Raises"],
            ),
            ImportanceProcessor(
                config=ImportanceConfig(
                    patterns=dict(self.config.processing.importance_patterns),
                    keywords=self.config.processing.importance_keywords,
                )
            ),
            ImportProcessor(),
        ]

    def _initialize_backend(self) -> StubBackend:
        """Initialize the appropriate backend based on configuration.

        Returns:
            Initialized backend
        """
        # Convert StubGenConfig to StubConfig for the backend
        stub_config = _convert_to_stub_config(self.config)

        if self.config.runtime.backend == Backend.AST:
            return ASTBackend(stub_config)
        elif self.config.runtime.backend == Backend.MYPY:
            return MypyBackend(stub_config)
        else:
            raise ConfigError(
                f"Unknown backend: {self.config.runtime.backend}",
                ErrorCode.CONFIG_VALIDATION_ERROR,
            )

    def _process_file(self, backend: StubBackend, file_path: Path) -> None:
        """Process a single file."""
        try:
            # Generate stub
            result = asyncio.run(backend.generate_stub(file_path))
            if isinstance(result, str):
                stub_content = result
            elif isinstance(result, StubResult):
                # Apply processors
                for processor in self.processors:
                    result = processor.process(result)
                stub_content = result.stub_content
            else:
                logger.error(
                    f"Unexpected result type from generate_stub: {type(result)}"
                )
                return

            # Write stub
            output_path = (
                self.config.paths.output_dir / file_path.with_suffix(".pyi").name
            )
            output_path.write_text(stub_content)

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            if not self.config.runtime.ignore_errors:
                raise

    def generate(self) -> None:
        """Generate stubs according to configuration."""
        try:
            logger.info(
                f"Generating stubs using {self.config.runtime.backend.name} backend"
            )
            logger.info(f"Output directory: {self.config.paths.output_dir}")

            # Create output directory
            self.config.paths.output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize backend
            backend = self._initialize_backend()

            # Process files
            for file_path in self.config.paths.files:
                self._process_file(backend, file_path)

            logger.info("Stub generation completed successfully")

        except Exception as e:
            logger.error(f"Failed to generate stubs: {e}")
            if self.config.runtime.verbose:
                import traceback

                logger.debug(traceback.format_exc())
            if not self.config.runtime.ignore_errors:
                raise

    def generate_for_file(self, file_path: str | Path) -> StubResult:
        """Generate stub for a single file.

        Args:
            file_path: Path to the Python file

        Returns:
            Generated stub result
        """
        # TODO: Implement single file stub generation
        raise NotImplementedError

    def generate_for_module(self, module_name: str) -> StubResult:
        """Generate stub for a module by name.

        Args:
            module_name: Fully qualified module name

        Returns:
            Generated stub result
        """
        # TODO: Implement module stub generation
        raise NotImplementedError


async def generate_stub(
    source_path: PathLike,
    output_path: PathLike | None = None,
    backend: Literal["ast", "mypy"] = "ast",
    config: StubConfig | None = None,
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
    output_path_obj = Path(output_path) if output_path else None

    # Convert StubConfig to StubGenConfig for backend
    if config is None:
        stub_gen_config = StubGenConfig(paths=PathConfig(), runtime=RuntimeConfig())
    else:
        stub_gen_config = _convert_to_stub_gen_config(config)

    # Initialize backend
    backend_obj: StubBackend
    if backend == "ast":
        backend_obj = ASTBackend(stub_gen_config)
    elif backend == "mypy":
        backend_obj = MypyBackend(stub_gen_config)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    # Generate stub
    result = await backend_obj.generate_stub(source_path)
    if not isinstance(result, StubResult):
        raise TypeError(f"Expected StubResult, got {type(result)}")

    # Write stub if output path is specified
    if output_path_obj:
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        output_path_obj.write_text(result.stub_content)

    return result


# Configure default logging
setup_logging()

# Version information
__version__ = version("twat_coding")
__author__ = "Adam Twardoch"
__license__ = "MIT"

__all__ = [
    "ArgInfo",
    "ASTBackend",
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
    "RuntimeConfig",
    "StubConfig",
    "ASTError",
    "ConfigError",
    "ErrorCode",
    "MyPyError",
    "StubGenerationError",
]
