#!/usr/bin/env -S uv run
"""AST-based stub generation backend.

This module implements stub generation using Python's ast module,
based on the original make_stubs_ast.py implementation.
"""

import ast
import asyncio
import functools
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from loguru import logger

from ..config import StubConfig
from ..core.config import (
    PathConfig,
    RuntimeConfig,
    StubGenConfig,
)
from ..core.conversion import convert_to_stub_gen_config
from ..core.types import StubResult
from ..errors import ASTError, ErrorCode
from ..processors import Processor
from ..utils.ast_utils import attach_parents
from ..utils.display import print_progress
from ..utils.memory import MemoryMonitor
from . import StubBackend


@dataclass
class ASTCacheEntry:
    """Cache entry for parsed AST nodes."""

    node: ast.AST
    source_hash: str
    access_time: float


class SignatureExtractor(ast.NodeTransformer):
    """Extract signatures and important code from AST nodes."""

    def __init__(
        self, config: StubGenConfig, file_size: int = 0, importance_score: float = 1.0
    ):
        """Initialize the extractor.

        Args:
            config: Configuration for stub generation
            file_size: Size of the source file in bytes
            importance_score: Base importance score for the file
        """
        super().__init__()
        self.config = config
        self.file_size = file_size
        self.importance_score = importance_score

    def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """Preserve docstring in a node's body.

        Args:
            body: List of statements

        Returns:
            List with only docstring preserved
        """
        if not body:
            return []

        # Check if first statement is a docstring
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
            return [first]  # Keep only docstring
        return []  # No docstring found

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process a module node.

        Args:
            node: Module node to process

        Returns:
            Processed module node
        """
        # Keep imports and docstring
        new_body: list[ast.stmt] = []
        imports: list[ast.Import | ast.ImportFrom] = []

        for stmt in node.body:
            if isinstance(stmt, ast.Import | ast.ImportFrom):
                imports.append(stmt)
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                new_body.append(stmt)
            else:
                new_body.append(self.visit(stmt))

        # Add imports at the beginning
        node.body = imports + new_body
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Process a function definition.

        Args:
            node: Function node to process

        Returns:
            Processed function node
        """
        # Keep signature and docstring
        node.body = self._preserve_docstring(node.body) or [ast.Pass()]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Process a class definition.

        Args:
            node: Class node to process

        Returns:
            Processed class node
        """
        # Keep class signature, docstring, and method signatures
        node.body = [self.visit(stmt) for stmt in node.body]
        return node


class ASTBackend(StubBackend):
    """AST-based stub generation backend with advanced concurrency."""

    # Class-level LRU cache for parsed AST nodes
    _ast_cache: ClassVar[dict[Path, Any]] = {}
    _ast_cache_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _max_cache_size: ClassVar[int] = 100

    def __init__(self, config: StubConfig | StubGenConfig | None = None) -> None:
        """Initialize the backend.

        Args:
            config: Configuration for stub generation
        """
        super().__init__()  # Object doesn't take any arguments
        self._config = config  # Store config for later use
        self.processors: list[Processor] = []  # List of processors to apply to stubs
        self._node_registry: weakref.WeakValueDictionary[int, ast.AST] = (
            weakref.WeakValueDictionary()
        )

        # Handle different config types
        if isinstance(config, StubConfig):
            self._executor = ThreadPoolExecutor(
                max_workers=config.max_workers if config.parallel else 1,
                thread_name_prefix="ast_backend",
                initializer=None,
                initargs=(),
            )
            self.include_patterns = config.include_patterns
            self.exclude_patterns = config.exclude_patterns
        else:  # StubGenConfig or None
            stub_config = config or StubGenConfig(
                paths=PathConfig(), runtime=RuntimeConfig()
            )
            self._executor = ThreadPoolExecutor(
                max_workers=stub_config.runtime.max_workers
                if stub_config.runtime.parallel
                else 1,
                thread_name_prefix="ast_backend",
                initializer=None,
                initargs=(),
            )
            self.include_patterns = ["*.py"]  # Default patterns
            self.exclude_patterns = ["test_*.py", "*_test.py"]

        self._memory_monitor = MemoryMonitor()

    @property
    def config(self) -> StubGenConfig:
        """Get the current configuration.

        Returns:
            Current configuration
        """
        if not hasattr(self, "_config"):
            return StubGenConfig(paths=PathConfig(), runtime=RuntimeConfig())

        # Convert StubConfig to StubGenConfig if needed
        if isinstance(self._config, StubConfig):
            return convert_to_stub_gen_config(self._config)
        elif isinstance(self._config, StubGenConfig):
            return self._config
        else:  # None
            return StubGenConfig(paths=PathConfig(), runtime=RuntimeConfig())

    async def generate_stub(self, source_path: Path) -> StubResult:
        """Generate a stub for a Python source file.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub result
        """
        return await self._generate_stub_internal(source_path)

    async def _generate_stub_internal(self, source_path: Path) -> StubResult:
        """Internal method to generate a stub result.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub result
        """
        try:
            # Read source file
            source = await self._run_in_executor(source_path.read_text)

            # Parse AST
            tree = await self._run_in_executor(
                functools.partial(ast.parse, source, filename=str(source_path))
            )
            attach_parents(tree)

            # Transform AST
            transformer = SignatureExtractor(self.config, len(source))
            transformed = transformer.visit(tree)

            # Generate stub content
            stub_content = ast.unparse(transformed)

            # Create StubResult
            result = StubResult(
                source_path=source_path,
                stub_content=stub_content,
                imports=[],  # TODO: Extract imports
                errors=[],
                importance_score=0.0,
                metadata={},
            )

            # Apply processors if available
            if hasattr(self, "processors"):
                for processor in self.processors:
                    result = processor.process(result)

            return result

        except Exception as e:
            logger.error(f"Error generating stub for {source_path}: {e}")
            raise ASTError(
                code=ErrorCode.AST_TRANSFORM_ERROR,
                message=f"Failed to generate stub for {source_path}",
                details={"error": str(e)},
            ) from e

    async def process_directory(self, directory: Path) -> dict[Path, StubResult]:
        """Process a directory recursively.

        Args:
            directory: Directory to process

        Returns:
            Dictionary mapping output paths to stub results

        Raises:
            ASTError: If directory processing fails
        """
        try:
            # Find all Python files matching patterns
            python_files: list[Path] = []
            for pattern in self.include_patterns:
                python_files.extend(directory.rglob(pattern))

            # Filter out excluded files
            for pattern in self.exclude_patterns:
                python_files = [f for f in python_files if not f.match(pattern)]

            # Process files with progress reporting
            results: dict[Path, StubResult] = {}
            total = len(python_files)
            for i, path in enumerate(python_files, 1):
                try:
                    print_progress("Processing files", i, total)
                    result = await self._generate_stub_internal(path)
                    results[path] = result
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
                    if self.config.runtime.ignore_errors:
                        continue
                    raise

            return results

        except Exception as e:
            raise ASTError(
                f"Failed to process directory {directory}: {e}",
                ErrorCode.AST_PARSE_ERROR,
                source=str(directory),
            ) from e

    async def process_module(self, module_name: str) -> StubResult:
        """Process a module by its import name.

        Args:
            module_name: Fully qualified module name

        Returns:
            Generated stub result

        Raises:
            StubGenerationError: If module processing fails
        """
        # TODO: Implement module processing
        raise NotImplementedError

    async def process_package(self, package_path: Path) -> dict[Path, StubResult]:
        """Process a package directory recursively.

        Args:
            package_path: Path to the package directory

        Returns:
            Dictionary mapping output paths to stub results

        Raises:
            StubGenerationError: If package processing fails
        """
        return await self.process_directory(package_path)

    def cleanup(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=True)
        self._ast_cache.clear()
        self._node_registry.clear()
        self._memory_monitor.stop()

    async def _run_in_executor(self, func: Any, *args: Any) -> Any:
        """Run a function in the thread pool executor.

        Args:
            func: Function to run
            *args: Arguments to pass to the function

        Returns:
            Result of the function
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args)
