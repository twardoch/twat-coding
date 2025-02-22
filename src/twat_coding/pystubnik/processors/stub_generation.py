#!/usr/bin/env -S uv run
"""Stub generation processor for creating type stub files."""

import ast
from pathlib import Path
from typing import ClassVar

from ..config import StubConfig
from ..core.config import StubGenConfig
from ..errors import ErrorCode, StubGenerationError
from ..types.type_system import TypeRegistry
from ..utils.ast_utils import attach_parents


class StubGenerator:
    """Generate type stubs from Python source code."""

    # Common import patterns to preserve
    ESSENTIAL_IMPORTS: ClassVar[set[str]] = {
        "typing",
        "dataclasses",
        "enum",
        "abc",
        "contextlib",
        "pathlib",
        "collections.abc",
    }

    def __init__(
        self,
        config: StubConfig | StubGenConfig | None = None,
        type_registry: TypeRegistry | None = None,
    ) -> None:
        """Initialize the stub generator.

        Args:
            config: Configuration for stub generation
            type_registry: Registry for type resolution
        """
        if isinstance(config, StubGenConfig):
            # Create a StubConfig from StubGenConfig
            self.config = StubConfig(
                input_path=Path("."),  # Temporary path, will be set per file
                output_path=None,  # Will be set per file
                line_length=88,
                sort_imports=True,
                add_header=True,
                include_private=config.processing.include_private,
                include_type_comments=config.processing.include_type_comments,
                infer_property_types=config.processing.infer_property_types,
                export_less=config.processing.export_less,
                docstring_type_hints=config.processing.include_docstrings,
                backend="ast",
                parallel=True,
                max_workers=None,
                infer_types=True,
                preserve_literals=False,
                no_import=False,
                inspect=False,
                doc_dir="",
                ignore_errors=True,
                parse_only=False,
                verbose=False,
                quiet=True,
                max_docstring_length=150,
            )
        else:
            # Use provided config or create default
            self.config = config or StubConfig(
                input_path=Path("."),
                output_path=None,
                backend="ast",
                parallel=True,
                max_workers=None,
                infer_types=True,
                preserve_literals=False,
                docstring_type_hints=True,
                line_length=88,
                sort_imports=True,
                add_header=True,
                no_import=False,
                inspect=False,
                doc_dir="",
                ignore_errors=True,
                parse_only=False,
                include_private=False,
                verbose=False,
                quiet=True,
                export_less=False,
                max_docstring_length=150,
                include_type_comments=True,
                infer_property_types=True,
            )
        self.type_registry = type_registry or TypeRegistry()

    def generate_stub(self, source_path: Path, tree: ast.AST | None = None) -> str:
        """Generate a type stub for a Python source file.

        Args:
            source_path: Path to the source file
            tree: Optional pre-parsed AST

        Returns:
            Generated stub content

        Raises:
            StubGenerationError: If stub generation fails
        """
        try:
            # Parse source if not provided
            if tree is None:
                with source_path.open() as f:
                    tree = ast.parse(f.read(), filename=str(source_path))

            # Attach parent references for better context
            attach_parents(tree)

            # Process the AST
            if not isinstance(tree, ast.Module):
                raise StubGenerationError(
                    "Expected Module AST node",
                    ErrorCode.AST_PARSE_ERROR,
                    source=str(source_path),
                )
            processed = self._process_module(tree)

            # Generate stub content
            return self._generate_content(processed)

        except Exception as e:
            raise StubGenerationError(
                f"Failed to generate stub for {source_path}: {e}",
                ErrorCode.AST_TRANSFORM_ERROR,
                source=str(source_path),
            ) from e

    def _process_module(self, node: ast.Module) -> ast.Module:
        """Process a module AST for stub generation.

        Args:
            node: Module AST to process

        Returns:
            Processed module AST
        """
        # Create a new module for the stub
        stub = ast.Module(body=[], type_ignores=[])

        # Process imports and definitions
        imports = self._collect_imports(node)
        definitions = self._collect_definitions(node)

        # Build the stub body
        stub.body = self._build_stub_body(imports, definitions)

        return stub

    def _collect_imports(self, node: ast.Module) -> list[ast.Import | ast.ImportFrom]:
        """Collect and process import statements.

        Args:
            node: Module AST to process

        Returns:
            List of processed import statements
        """
        imports = [
            child
            for child in node.body
            if isinstance(child, ast.Import | ast.ImportFrom)
            and self._should_keep_import(child)
        ]

        if self.config.sort_imports and imports:
            # Group imports by module
            grouped_imports: dict[str, list[ast.ImportFrom]] = {}
            regular_imports: list[ast.Import] = []

            for imp in imports:
                if isinstance(imp, ast.ImportFrom):
                    module = imp.module or ""
                    if module not in grouped_imports:
                        grouped_imports[module] = []
                    grouped_imports[module].append(imp)
                else:
                    regular_imports.append(imp)

            # Combine imports from the same module
            combined_imports: list[ast.Import | ast.ImportFrom] = []
            for module in sorted(grouped_imports.keys()):
                module_imports = grouped_imports[module]
                if len(module_imports) == 1:
                    combined_imports.append(module_imports[0])
                else:
                    # Combine names from all imports
                    names = []
                    for imp in module_imports:
                        names.extend(imp.names)
                    # Sort names by alias or name
                    names.sort(key=lambda n: n.asname or n.name)
                    # Create new combined import
                    combined = ast.ImportFrom(
                        module=module,
                        names=names,
                        level=module_imports[0].level,
                    )
                    # Copy location from first import
                    for attr in [
                        "lineno",
                        "col_offset",
                        "end_lineno",
                        "end_col_offset",
                    ]:
                        if hasattr(module_imports[0], attr):
                            setattr(combined, attr, getattr(module_imports[0], attr))
                    combined_imports.append(combined)

            # Add regular imports at the beginning
            imports = (
                sorted(regular_imports, key=lambda x: x.names[0].name)
                + combined_imports
            )

        return imports

    def _collect_definitions(self, node: ast.Module) -> list[ast.stmt]:
        """Collect and process module definitions.

        Args:
            node: Module AST to process

        Returns:
            List of processed definitions
        """
        definitions = []
        for child in node.body:
            if not isinstance(child, ast.Import | ast.ImportFrom):
                if processed := self._process_node(child):
                    if isinstance(processed, ast.stmt):
                        definitions.append(processed)
        return definitions

    def _build_stub_body(
        self,
        imports: list[ast.Import | ast.ImportFrom],
        definitions: list[ast.stmt],
    ) -> list[ast.stmt]:
        """Build the final stub body from components.

        Args:
            imports: List of processed import statements
            definitions: List of processed definitions

        Returns:
            Complete list of statements for the stub body
        """
        body: list[ast.stmt] = []

        # Add header if configured
        if self.config.add_header:
            header = ast.Expr(
                value=ast.Constant(
                    value="# Generated by pystubnik\n# Do not edit this file directly\n\n"
                )
            )
            body.append(header)

        # Add imports
        body.extend(imports)

        # Add separator if needed
        if imports and definitions:
            body.append(ast.Expr(value=ast.Constant(value="")))

        # Add definitions
        body.extend(definitions)

        return body

    def _process_node(self, node: ast.AST) -> ast.stmt | None:
        """Process a single AST node for stub generation.

        Args:
            node: AST node to process

        Returns:
            Processed node or None if node should be skipped
        """
        match node:
            case ast.ClassDef():
                return self._process_class(node)
            case ast.FunctionDef() | ast.AsyncFunctionDef():
                return self._process_function(node)
            case ast.AnnAssign() | ast.Assign():
                return self._process_assignment(node)
            case _:
                return None

    def _process_class(self, node: ast.ClassDef) -> ast.ClassDef | None:
        """Process a class definition.

        Args:
            node: Class definition node

        Returns:
            Processed class definition or None if class should be skipped
        """
        # Skip private classes if configured
        if not self.config.include_private and node.name.startswith("_"):
            return None

        # Create new class with same name and bases
        new_class = ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=[],
            decorator_list=node.decorator_list,
            type_params=getattr(node, "type_params", []),  # For Python 3.12+
        )

        # Process class body
        for child in node.body:
            if processed := self._process_node(child):
                new_class.body.append(processed)

        # Preserve docstring if present
        if (
            isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        ):
            new_class.body.insert(0, node.body[0])

        # Copy location info
        self._ensure_node_attributes(new_class)
        return new_class

    def _process_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        """Process a function definition.

        Args:
            node: Function definition node

        Returns:
            Processed function definition or None if function should be skipped
        """
        # Skip private functions if configured
        if not self.config.include_private and node.name.startswith("_"):
            if node.name != "__init__":  # Always include __init__
                return None

        # Create new function with same signature
        new_func = type(node)(
            name=node.name,
            args=node.args,
            returns=node.returns,
            type_comment=node.type_comment if hasattr(node, "type_comment") else None,
            body=[ast.Pass()],  # Replace body with pass statement
            decorator_list=node.decorator_list,
            type_params=getattr(node, "type_params", []),  # For Python 3.12+
        )

        # Preserve docstring if present
        if (
            len(node.body) > 0
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        ):
            new_func.body.insert(0, node.body[0])

        # Copy location info
        self._ensure_node_attributes(new_func)
        return new_func

    def _process_assignment(self, node: ast.AnnAssign | ast.Assign) -> ast.stmt | None:
        """Process an assignment for stub generation.

        Args:
            node: Assignment to process

        Returns:
            Processed assignment or None if it should be excluded
        """
        match node:
            case ast.AnnAssign():
                # Preserve annotated assignments
                return node
            case ast.Assign(
                targets=[ast.Name() as name_node], value=ast.Constant() as value
            ):
                # Only keep module-level assignments of constants
                if not name_node.id.startswith("_") or name_node.id.isupper():
                    return ast.AnnAssign(
                        target=name_node,
                        annotation=ast.Name(id=type(value.value).__name__),
                        value=value,
                        simple=1,
                    )
        return None

    def _should_keep_import(self, node: ast.Import | ast.ImportFrom) -> bool:
        """Check if an import should be kept in the stub.

        Args:
            node: Import node to check

        Returns:
            True if the import should be kept
        """
        if isinstance(node, ast.ImportFrom):
            return node.module in self.ESSENTIAL_IMPORTS or any(
                name.name.isupper() for name in node.names
            )
        return any(
            name.name in self.ESSENTIAL_IMPORTS
            or name.name.split(".")[0] in self.ESSENTIAL_IMPORTS
            for name in node.names
        )

    def _import_sort_key(self, node: ast.Import | ast.ImportFrom) -> tuple[int, str]:
        """Get sort key for import statements.

        Args:
            node: Import node to sort

        Returns:
            Tuple of (import type, module name) for sorting
        """
        if isinstance(node, ast.ImportFrom):
            return (1, node.module or "")
        return (0, node.names[0].name)

    def _ensure_node_attributes(self, node: ast.AST) -> None:
        """Ensure AST nodes have required attributes for unparsing.

        Args:
            node: AST node to process
        """
        # Add required attributes if missing
        for attr, default in [
            ("lineno", 0),
            ("col_offset", 0),
            ("end_lineno", 0),
            ("end_col_offset", 0),
        ]:
            if not hasattr(node, attr):
                setattr(node, attr, default)

        # Process child nodes
        for child in ast.iter_child_nodes(node):
            self._ensure_node_attributes(child)

    def _generate_content(self, node: ast.Module) -> str:
        """Generate the final stub content.

        Args:
            node: Processed module AST

        Returns:
            Generated stub content
        """
        # Ensure all nodes have required attributes
        self._ensure_node_attributes(node)
        return ast.unparse(node)
