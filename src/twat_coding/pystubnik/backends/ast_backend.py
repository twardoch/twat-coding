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
from typing import Any, ClassVar, cast

from loguru import logger

from ..core.config import StubGenConfig
from ..core.shared_types import TruncationConfig
from ..errors import ASTError, ErrorCode
from ..utils.ast_utils import attach_parents, truncate_literal
from ..utils.display import print_progress
from ..utils.memory import MemoryMonitor, stream_process_ast
from . import StubBackend


@dataclass
class ASTCacheEntry:
    """Cache entry for parsed AST nodes."""

    node: ast.AST
    source_hash: str
    access_time: float


class SignatureExtractor(ast.NodeTransformer):
    """Extract type signatures and docstrings from AST."""

    def __init__(
        self, config: StubGenConfig, file_size: int = 0, importance_score: float = 1.0
    ):
        """Initialize the signature extractor.

        Args:
            config: Configuration for stub generation
            file_size: Size of the source file
            importance_score: Importance score for the file
        """
        super().__init__()
        self.config = config
        self.file_size = file_size
        self.importance_score = importance_score

    def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """Preserve docstrings based on importance and configuration.

        Args:
            body: List of AST statements

        Returns:
            List of AST statements with docstrings preserved or removed
        """
        if not body:
            return []
        if (
            self.file_size > self.config.truncation.max_file_size
            and self.importance_score < 0.7
        ):
            return []  # Skip docstrings for big, low-importance files
        match body[0]:
            case ast.Expr(value=ast.Constant(value=str() as docstring)):
                if (
                    len(docstring) > self.config.truncation.max_docstring_length
                    and self.importance_score < 0.9
                ):
                    return []  # Skip long docstrings unless very important
                return [body[0]]
            case _:
                return []

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process module node.

        Args:
            node: Module AST node

        Returns:
            Processed module node
        """
        node.body = [
            stmt
            for stmt in node.body
            if isinstance(
                stmt, ast.FunctionDef | ast.ClassDef | ast.Import | ast.ImportFrom
            )
            or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
        ]
        return cast(ast.Module, self.generic_visit(node))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Process function definition.

        Args:
            node: Function definition AST node

        Returns:
            Processed function node
        """
        docstring = self._preserve_docstring(node.body)
        node.body = docstring + [ast.Expr(value=ast.Constant(value=...))]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Process class definition.

        Args:
            node: Class definition AST node

        Returns:
            Processed class node
        """
        docstring = self._preserve_docstring(node.body)
        node.body = docstring + [
            stmt
            for stmt in node.body
            if isinstance(stmt, ast.FunctionDef | ast.ClassDef)
        ]
        return cast(ast.ClassDef, self.generic_visit(node))


class ASTBackend(StubBackend):
    """AST-based stub generation backend with advanced concurrency."""

    # Class-level LRU cache for parsed AST nodes
    _ast_cache: ClassVar[dict[Path, Any]] = {}
    _ast_cache_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _max_cache_size: ClassVar[int] = 100

    def __init__(self, config: StubGenConfig):
        """Initialize the backend.

        Args:
            config: Stub generation configuration
        """
        super().__init__()
        self.config = config
        self._executor = ThreadPoolExecutor(
            max_workers=config.runtime.max_workers
            if config.runtime.max_workers
            else None
        )
        self._node_registry: weakref.WeakValueDictionary[int, ast.AST] = (
            weakref.WeakValueDictionary()
        )
        self._memory_monitor = MemoryMonitor()

    async def generate_stub(
        self, source_path: Path, output_path: Path | None = None
    ) -> str:
        """Generate a stub for a Python source file using AST parsing.

        Args:
            source_path: Path to the source file
            output_path: Optional output path for the stub file

        Returns:
            Generated stub content

        Raises:
            ASTError: If AST parsing or processing fails
        """
        try:
            # Get file locations
            input_path, stub_path = self.config.get_file_locations(source_path)
            output_path = output_path or stub_path

            # Start memory monitoring
            self._memory_monitor.start()

            # Read source file
            try:
                source = input_path.read_text()
            except Exception as e:
                raise ASTError(
                    f"Failed to read source file {input_path}: {e}",
                    ErrorCode.IO_READ_ERROR,
                ) from e

            # Calculate importance score
            file_score = 0.5  # Default score
            try:
                from ..processors.importance import ImportanceProcessor

                processor = ImportanceProcessor()
                file_score = processor._get_file_score({"file_path": source_path})
            except Exception as e:
                logger.warning(f"Failed to calculate importance score: {e}")

            # Parse AST
            tree = await self._run_in_executor(
                functools.partial(ast.parse, source, filename=str(source_path))
            )
            attach_parents(tree)

            # Transform AST
            transformer = SignatureExtractor(self.config, len(source), file_score)
            transformed = transformer.visit(tree)
            stub_content = ast.unparse(transformed)

            return stub_content

        except Exception as e:
            if isinstance(e, ASTError):
                raise
            raise ASTError(
                f"Failed to generate stub for {source_path}: {e}",
                ErrorCode.AST_TRANSFORM_ERROR,
            ) from e
        finally:
            # Stop memory monitoring and log stats
            self._memory_monitor.stop()
            peak_mb = self._memory_monitor.peak_memory / 1024 / 1024
            logger.debug(f"Peak memory usage: {peak_mb:.1f}MB")
            self._memory_monitor.clear_stats()

    async def process_directory(self, directory: Path) -> dict[Path, str]:
        """Process a directory recursively.

        Args:
            directory: Directory to process

        Returns:
            Dictionary mapping output paths to stub contents

        Raises:
            ASTError: If directory processing fails
        """
        try:
            # Find all Python files matching patterns
            python_files: list[Path] = []
            for pattern in self.config.include_patterns:
                python_files.extend(directory.rglob(pattern))

            # Filter out excluded files
            for pattern in self.config.exclude_patterns:
                python_files = [f for f in python_files if not f.match(pattern)]

            # Process files with progress reporting
            results: dict[Path, str] = {}
            total = len(python_files)
            for i, path in enumerate(python_files, 1):
                try:
                    print_progress("Processing files", i, total)
                    stub = await self.generate_stub(path)
                    results[path] = stub
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
                    if not self.config.ignore_errors:
                        raise

            return results

        except Exception as e:
            raise ASTError(
                f"Failed to process directory {directory}: {e}",
                ErrorCode.AST_PARSE_ERROR,
                source=str(directory),
            ) from e

    def cleanup(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=True)
        self._ast_cache.clear()
        self._node_registry.clear()
        self._memory_monitor.stop()

    async def _process_ast(self, tree: ast.AST, source_path: Path) -> str:
        """Process an AST to generate a stub.

        Args:
            tree: AST to process
            source_path: Source file path for error reporting

        Returns:
            Generated stub content

        Raises:
            ASTError: If processing fails
        """
        try:
            # Create truncation config
            trunc_config = TruncationConfig(
                max_sequence_length=4,  # TODO: Make configurable
                max_string_length=17,
                max_docstring_length=150,
                max_file_size=3_000,
                truncation_marker="...",
            )

            # Process AST nodes in chunks to optimize memory usage
            stub_parts = []
            async for nodes in stream_process_ast(tree):
                # Process each chunk of nodes
                for node in nodes:
                    # Apply truncation
                    truncated = truncate_literal(node, trunc_config)
                    # Convert to string
                    stub_parts.append(ast.unparse(truncated))

            # Combine processed parts
            return "\n".join(stub_parts)

        except Exception as e:
            raise ASTError(
                f"Failed to process AST for {source_path}: {e}",
                ErrorCode.AST_TRANSFORM_ERROR,
                source=str(source_path),
            ) from e

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
