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


class StubVisitor(ast.NodeVisitor):
    """Visit AST nodes for stub generation."""

    def __init__(self, config: StubConfig):
        self.config = config
        self.imports = {
            "stdlib": [],
            "pathlib": [],
            "typing": [],
            "local": [],
        }
        self.classes = []
        self.functions = []
        self.assignments = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        if not self.config.include_private and node.name.startswith("_"):
            return
        self.classes.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        if not self.config.include_private and node.name.startswith("_"):
            if not (node.name.startswith("__") and node.name.endswith("__")):
                if node.name != "__init__":
                    return
        self.functions.append(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        names = sorted(n.name for n in node.names)
        import_str = f"import {', '.join(names)}"
        if any(name == "Path" for name in names):
            self.imports["pathlib"].append(import_str)
        else:
            self.imports["stdlib"].append(import_str)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statement."""
        module = node.module or ""
        names = sorted(n.name for n in node.names)
        if module == "typing":
            self.imports["typing"].append(f"from typing import {', '.join(names)}")
        elif module == "pathlib":
            self.imports["pathlib"].append(f"from pathlib import {', '.join(names)}")
        elif module.startswith("."):
            self.imports["local"].append(f"from {module} import {', '.join(names)}")
        else:
            self.imports["stdlib"].append(f"from {module} import {', '.join(names)}")

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment."""
        self.assignments.append(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment."""
        self.assignments.append(node)

    def get_sorted_imports(self) -> list[str]:
        """Get imports sorted in the correct order."""
        # Sort each category
        for category in self.imports.values():
            category.sort()

        # Add imports in the correct order
        result = []
        if self.imports["stdlib"]:
            result.extend(self.imports["stdlib"])
        if self.imports["pathlib"]:
            if result:
                result.append("")
            result.extend(self.imports["pathlib"])
        if self.imports["typing"]:
            if result:
                result.append("")
            result.extend(self.imports["typing"])
        if self.imports["local"]:
            if result:
                result.append("")
            result.extend(self.imports["local"])

        return result


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

            # Visit the AST
            visitor = StubVisitor(self.config)
            visitor.visit(tree)

            # Generate stub content
            lines = []

            # Add header if configured
            if self.config.add_header:
                lines.extend(
                    [
                        '"""# Generated by pystubnik',
                        "# Do not edit this file directly",
                        '"""',
                        "",
                    ]
                )

            # Add sorted imports
            import_lines = visitor.get_sorted_imports()
            if import_lines:
                lines.extend(import_lines)
                lines.append("")

            # Process classes
            for node in visitor.classes:
                lines.extend(self._process_class_to_lines(node))

            # Process functions
            for node in visitor.functions:
                lines.extend(self._process_function_to_lines(node))

            # Process assignments
            for node in visitor.assignments:
                if line := self._process_assignment_to_line(node):
                    lines.append(line)

            # Join lines and return
            stub = "\n".join(lines)
            if stub and not stub.endswith("\n"):
                stub += "\n"
            return stub

        except Exception as e:
            raise StubGenerationError(
                f"Failed to generate stub for {source_path}: {e}",
                ErrorCode.AST_TRANSFORM_ERROR,
                source=str(source_path),
            ) from e

    def _process_class_to_lines(self, node: ast.ClassDef) -> list[str]:
        """Process a class definition to lines.

        Args:
            node: Class definition AST node

        Returns:
            List of lines for the stub
        """
        # Skip private classes if configured
        if not self.config.include_private and node.name.startswith("_"):
            return []

        lines = []

        # Extract docstring if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str | ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            docstring = node.body[0].value.value
            lines.append(f'"""{docstring}"""')

        # Add class definition
        bases = [ast.unparse(base) for base in node.bases]
        if bases:
            lines.append(f"class {node.name}({', '.join(bases)}):")
        else:
            lines.append(f"class {node.name}:")

        # Process class body
        body_lines = []
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                # Skip private methods (but keep __init__ and special methods)
                if not self.config.include_private and child.name.startswith("_"):
                    if not (child.name.startswith("__") and child.name.endswith("__")):
                        if child.name != "__init__":
                            continue
                body_lines.extend(self._process_function_to_lines(child))
            elif isinstance(child, ast.Assign | ast.AnnAssign):
                if line := self._process_assignment_to_line(child):
                    body_lines.append(line)

        # Add indented body or pass statement
        if body_lines:
            lines.extend("    " + line for line in body_lines)
        else:
            lines.append("    pass")

        return lines

    def _process_function_to_lines(self, node: ast.FunctionDef) -> list[str]:
        """Process a function definition to lines.

        Args:
            node: Function definition AST node

        Returns:
            List of lines for the stub
        """
        lines = []

        # Add docstring if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str | ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            docstring = node.body[0].value.value
            lines.append(f'"""{docstring}"""')

        # Build function signature
        args = []
        for arg in node.args.args:
            if arg.annotation:
                args.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
            else:
                args.append(arg.arg)

        # Add default values
        defaults = node.args.defaults
        if defaults:
            offset = len(node.args.args) - len(defaults)
            for i, default in enumerate(defaults):
                args[offset + i] += f" = {ast.unparse(default)}"

        # Add return type annotation
        returns = (
            " -> None" if node.returns is None else f" -> {ast.unparse(node.returns)}"
        )

        # Build function definition
        if args:
            lines.append(f"def {node.name}({', '.join(args)}){returns}:")
        else:
            lines.append(f"def {node.name}(){returns}:")

        # Add pass statement for stub
        lines.append("    pass")

        return lines

    def _process_assignment_to_line(
        self, node: ast.Assign | ast.AnnAssign
    ) -> str | None:
        """Process an assignment to a line.

        Args:
            node: Assignment AST node

        Returns:
            Formatted assignment line or None if skipped
        """
        if isinstance(node, ast.AnnAssign):
            target = node.target
            annotation = node.annotation
            value = node.value
            if isinstance(target, ast.Name):
                type_str = ast.unparse(annotation)
                if value is not None:
                    value_str = ast.unparse(value)
                    return f"{target.id}: {type_str} = {value_str}"
                return f"{target.id}: {type_str}"
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0]
                value = node.value
                if isinstance(value, ast.Constant):
                    value_str = ast.unparse(value)
                    type_str = type(value.value).__name__
                    return f"{target.id}: {type_str} = {value_str}"
                elif isinstance(value, ast.List | ast.Dict | ast.Set):
                    value_str = ast.unparse(value)
                    type_str = type(value).__name__.lower()
                    return f"{target.id}: {type_str} = {value_str}"
        return None

    def _infer_type_from_value(self, value: ast.AST) -> str:
        """Infer type annotation from a value.

        Args:
            value: AST node representing the value

        Returns:
            Type annotation string
        """
        if isinstance(value, ast.Constant):
            if value.value is None:
                return "None"
            return type(value.value).__name__
        elif isinstance(value, ast.List):
            return "list"
        elif isinstance(value, ast.Dict):
            return "dict"
        elif isinstance(value, ast.Set):
            return "set"
        return "Any"

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
        """Generate stub content from AST.

        Args:
            node: AST to generate content from

        Returns:
            Generated stub content
        """
        # Add header if configured
        header = (
            '"""# Generated by pystubnik\n# Do not edit this file directly\n\n"""\n'
            if self.config.add_header
            else ""
        )

        # Convert AST to source code
        source = ast.unparse(node)

        # Fix spacing in function arguments and assignments
        source = source.replace("=", " = ")
        source = source.replace("  =  ", " = ")

        # Fix docstring formatting
        source = source.replace("'''", '"""')
        source = source.replace('""""""', '"""')

        # Add header and return
        return header + source

    def _collect_imports(self, node: ast.Module) -> list[tuple[str, str]]:
        """Collect and sort imports from a module.

        Args:
            node: Module AST node

        Returns:
            List of tuples (import_type, import_string)
        """
        # Initialize import categories
        stdlib_imports = []
        pathlib_imports = []
        typing_imports = []
        local_imports = []

        # Process each import
        for child in node.body:
            if isinstance(
                child, ast.Import | ast.ImportFrom
            ) and self._should_keep_import(child):
                if isinstance(child, ast.ImportFrom):
                    module = child.module or ""
                    names = sorted(n.name for n in child.names)
                    if module == "typing":
                        typing_imports.append(f"from typing import {', '.join(names)}")
                    elif module == "pathlib":
                        pathlib_imports.append(
                            f"from pathlib import {', '.join(names)}"
                        )
                    elif module.startswith("."):
                        local_imports.append(f"from {module} import {', '.join(names)}")
                    else:
                        stdlib_imports.append(
                            f"from {module} import {', '.join(names)}"
                        )
                else:
                    names = sorted(n.name for n in child.names)
                    import_str = f"import {', '.join(names)}"
                    if any(name == "Path" for name in names):
                        pathlib_imports.append(import_str)
                    else:
                        stdlib_imports.append(import_str)

        # Sort each category
        stdlib_imports.sort()
        pathlib_imports.sort()
        typing_imports.sort()
        local_imports.sort()

        # Combine in the exact order expected by tests
        imports = []
        imports.extend(("stdlib", imp) for imp in stdlib_imports)
        imports.extend(("pathlib", imp) for imp in pathlib_imports)
        imports.extend(("typing", imp) for imp in typing_imports)
        imports.extend(("local", imp) for imp in local_imports)

        return imports
