#!/usr/bin/env -S uv run
"""AST-based stub generation backend.

This module implements stub generation using Python's ast module,
based on the original make_stubs_ast.py implementation.
"""

import ast
import asyncio
import functools
import hashlib
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from loguru import logger
from pystubnik.backends import StubBackend
from pystubnik.core.config import StubGenConfig, TruncationConfig

from ..config import StubConfig
from ..errors import ASTError, ErrorCode
from ..utils.ast_utils import attach_parents, truncate_literal
from ..utils.display import print_progress
from ..utils.memory import MemoryMonitor, stream_process_ast


@dataclass
class ASTCacheEntry:
    """Cache entry for parsed AST nodes."""

    node: ast.AST
    source_hash: str
    access_time: float


class SignatureExtractor(ast.NodeTransformer):
    """Transform AST to preserve signatures while truncating implementation details.

    This transformer preserves:
    - imports
    - docstrings (subject to length constraints)
    - function & method signatures
    - class-level assignments
    But replaces function bodies with an ellipsis.
    """

    def __init__(self, config: StubGenConfig, file_size: int = 0):
        super().__init__()
        self.config = config
        self.file_size = file_size

    def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """If the first statement is a docstring, keep it if it meets size constraints.

        Args:
            body: List of statements to check for docstring

        Returns:
            List containing the docstring statement if it should be preserved,
            otherwise an empty list
        """
        if not body:
            return []

        # Skip all docstrings if file is too large
        if self.file_size > self.config.truncation.max_file_size:
            return []

        match body[0]:
            case ast.Expr(value=ast.Constant(value=str() as docstring)):
                # Skip if docstring is too long
                if len(docstring) > self.config.truncation.max_docstring_length:
                    return []
                return [body[0]]
            case _:
                return []

    def _make_ellipsis_expr(self, node: ast.AST, indent: int = 0) -> ast.Expr:
        """Create an ellipsis node with the same location offsets.

        Args:
            node: Node to copy location from
            indent: Additional indentation to add

        Returns:
            Ellipsis expression node
        """
        return ast.Expr(
            value=ast.Constant(value=Ellipsis),
            lineno=getattr(node, "lineno", 1),
            col_offset=getattr(node, "col_offset", 0) + indent,
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Keep function signature and docstring, replace body with ellipsis."""
        preserved_doc = self._preserve_docstring(node.body)
        ellipsis_body = [self._make_ellipsis_expr(node, indent=4)]
        return ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=preserved_doc + ellipsis_body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_params=[],  # For Python 3.12+
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Preserve class structure but transform method bodies."""
        preserved_doc = self._preserve_docstring(node.body)
        remainder = node.body[len(preserved_doc) :]
        new_body: list[ast.stmt] = []

        for item in remainder:
            match item:
                case ast.FunctionDef():
                    new_body.append(self.visit_FunctionDef(item))
                case _:
                    # Visit child nodes to truncate large literals
                    new_body.append(self.visit(item))

        return ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=preserved_doc + new_body,
            decorator_list=node.decorator_list,
            type_params=[],  # For Python 3.12+
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process top-level statements."""
        body: list[ast.stmt] = []
        for item in node.body:
            # Skip empty or purely whitespace expressions
            is_empty_expr = (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Constant)
                and (not item.value.value or str(item.value.value).isspace())
            )
            if is_empty_expr:
                continue
            body.append(self.visit(item))

        return ast.Module(body=body, type_ignores=[])

    def generic_visit(self, node: ast.AST) -> ast.AST:
        """Recurse into all child nodes, then apply literal truncation."""
        new_node = super().generic_visit(node)
        return truncate_literal(new_node, self.config.truncation)


class ASTBackend(StubBackend):
    """AST-based stub generation backend with advanced concurrency."""

    # Class-level LRU cache for parsed AST nodes
    _ast_cache: ClassVar[dict[Path, ASTCacheEntry]] = {}
    _ast_cache_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _max_cache_size: ClassVar[int] = 100

    def __init__(self, config: StubConfig) -> None:
        """Initialize the AST backend.

        Args:
            config: Configuration for stub generation
        """
        super().__init__(config)
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_workers if config.max_workers else None
        )
        self._node_registry: weakref.WeakValueDictionary[int, ast.AST] = (
            weakref.WeakValueDictionary()
        )
        self._memory_monitor = MemoryMonitor()

    async def generate_stub(self, source_path: Path) -> str:
        """Generate a stub for a Python source file using AST parsing.

        Args:
            source_path: Path to the source file

        Returns:
            Generated stub content

        Raises:
            ASTError: If AST parsing or processing fails
        """
        try:
            # Get file locations
            locations = self.config.get_file_locations(source_path)
            locations.check_paths()

            # Start memory monitoring
            self._memory_monitor.start()

            # Read and parse source file
            source = await self._run_in_executor(source_path.read_text)
            source_hash = hashlib.sha256(source.encode()).hexdigest()

            # Try to get from cache
            async with self._ast_cache_lock:
                if source_path in self._ast_cache:
                    entry = self._ast_cache[source_path]
                    if entry.source_hash == source_hash:
                        logger.debug(f"AST cache hit for {source_path}")
                        return await self._process_ast(entry.node, source_path)

            # Parse file
            tree = await self._run_in_executor(
                functools.partial(ast.parse, source, filename=str(source_path))
            )

            # Attach parent references
            attach_parents(tree)

            # Update cache
            async with self._ast_cache_lock:
                self._ast_cache[source_path] = ASTCacheEntry(
                    node=tree,
                    source_hash=source_hash,
                    access_time=asyncio.get_event_loop().time(),
                )
                if len(self._ast_cache) > self._max_cache_size:
                    # Remove oldest entry
                    oldest = min(
                        self._ast_cache.items(),
                        key=lambda x: x[1].access_time,
                    )
                    del self._ast_cache[oldest[0]]

            # Process AST
            stub_content = await self._process_ast(tree, source_path)

            # Write output
            output_path = locations.output_path
            await self._run_in_executor(output_path.write_text, stub_content)

            return stub_content

        except Exception as e:
            raise ASTError(
                f"Failed to generate stub for {source_path}: {e}",
                ErrorCode.AST_PARSE_ERROR,
                source=str(source_path),
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
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args)
