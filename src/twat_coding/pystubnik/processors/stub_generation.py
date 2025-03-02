#!/usr/bin/env -S uv run
"""Stub generation processor for creating type stub files."""

from ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    BinOp,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    List as AstList,
    Module,
    Name,
    NodeVisitor,
    Subscript,
    Tuple as AstTuple,
    alias,
    get_docstring,
    iter_child_nodes,
    parse,
    unparse,
)
from pathlib import Path

from ..config import StubConfig
from ..utils.ast_utils import attach_parents, should_include_member


class StubVisitor(NodeVisitor):
    """Visit AST nodes for stub generation."""

    def __init__(self, config: StubConfig) -> None:
        """Initialize the visitor.

        Args:
            config: Configuration for stub generation
        """
        super().__init__()
        self.config = config
        self.imports: dict[str, list[Import | ImportFrom]] = {
            "stdlib": [],
            "pathlib": [],
            "typing": [],
            "local": [],
        }
        self.classes: list[ClassDef] = []
        self.functions: list[FunctionDef] = []
        self.assignments: list[Assign | AnnAssign] = []

    def _should_include_member(self, name: str) -> bool:
        """Check if a member should be included in the stub.

        Args:
            name: Name of the member

        Returns:
            True if the member should be included
        """
        return should_include_member(name, self.config.include_private)

    def visit_ClassDef(self, node: ClassDef) -> None:
        """Visit class definitions."""
        # Skip private classes
        if not should_include_member(node.name, self.config.include_private):
            return

        self.classes.append(node)

        # Visit class body for methods and assignments
        for item in node.body:
            if isinstance(item, FunctionDef):
                if should_include_member(item.name, self.config.include_private):
                    self.visit(item)
            elif isinstance(item, Assign | AnnAssign):
                self.visit(item)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        """Visit function definitions."""
        if not self._should_include_member(node.name):
            return

        self.functions.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> None:
        """Visit assignments."""
        self.assignments.append(node)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        """Visit annotated assignments."""
        self.assignments.append(node)

    def visit_Import(self, node: Import) -> None:
        """Visit import statements."""
        for name in node.names:
            if name.name == "pathlib" or name.name.startswith("pathlib."):
                self.imports["pathlib"].append(node)
                break
            elif name.name == "typing" or name.name.startswith("typing."):
                self.imports["typing"].append(node)
                break
            else:
                self.imports["stdlib"].append(node)
                break

    def visit_ImportFrom(self, node: ImportFrom) -> None:
        """Visit from-import statements."""
        if node.level > 0:
            # Preserve relative imports with dots
            self.imports["local"].append(node)
        elif node.module == "pathlib":
            self.imports["pathlib"].append(node)
        elif node.module == "typing":
            # Combine all typing imports into one
            names = sorted(name.name for name in node.names)
            if any(
                imp
                for imp in self.imports["typing"]
                if isinstance(imp, ImportFrom) and imp.module == "typing"
            ):
                existing = next(
                    imp
                    for imp in self.imports["typing"]
                    if isinstance(imp, ImportFrom) and imp.module == "typing"
                )
                existing_names = {name.name for name in existing.names}
                new_names = [
                    alias(name=name) for name in sorted(set(names) | existing_names)
                ]
                existing.names = new_names
            else:
                self.imports["typing"].append(node)
        else:
            self.imports["stdlib"].append(node)

    def get_sorted_imports(self) -> list[str]:
        """Get sorted imports in the correct order."""
        sorted_imports = []

        # Standard library imports first
        stdlib_imports = sorted(
            self.imports["stdlib"], key=lambda x: self._get_import_name(x)
        )
        sorted_imports.extend(self._format_import(imp) for imp in stdlib_imports)

        # Pathlib imports next
        pathlib_imports = sorted(
            self.imports["pathlib"], key=lambda x: self._get_import_name(x)
        )
        if pathlib_imports:
            if sorted_imports:
                sorted_imports.append("")
            sorted_imports.extend(self._format_import(imp) for imp in pathlib_imports)

        # Typing imports
        typing_imports = sorted(
            self.imports["typing"], key=lambda x: self._get_import_name(x)
        )
        if typing_imports:
            if sorted_imports:
                sorted_imports.append("")
            sorted_imports.extend(self._format_import(imp) for imp in typing_imports)

        # Local imports last
        local_imports = sorted(
            self.imports["local"], key=lambda x: self._get_import_name(x)
        )
        if local_imports:
            if sorted_imports:
                sorted_imports.append("")
            sorted_imports.extend(self._format_import(imp) for imp in local_imports)

        return [imp for imp in sorted_imports if imp]

    def _get_import_name(self, node: Import | ImportFrom) -> str:
        """Get the import name for sorting."""
        if isinstance(node, Import):
            return node.names[0].name
        return (
            f"{node.module}.{node.names[0].name}" if node.module else node.names[0].name
        )

    def _format_import(self, node: Import | ImportFrom) -> str:
        """Format an import node as a string."""
        if isinstance(node, Import):
            return f"import {node.names[0].name}"
        module = f"from {node.module} " if node.module else "from "
        if node.level > 0:
            module = f"from {'.' * node.level}{node.module if node.module else ''} "
        names = ", ".join(sorted(name.name for name in node.names))
        return f"{module}import {names}"


class StubGenerator:
    """Generator for creating Python stub files."""

    ESSENTIAL_IMPORTS: set[str] = {
        "typing",
        "pathlib",
        "collections",
        "dataclasses",
        "enum",
        "abc",
    }

    def __init__(self, config: StubConfig | None = None) -> None:
        """Initialize the stub generator with optional configuration.

        Args:
            config: Optional configuration for stub generation. If None, default config is used.
        """
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
        self.current_file: Path | None = None

    def _should_include_member(self, name: str) -> bool:
        """Check if a member should be included in the stub.

        Args:
            name: Name of the member

        Returns:
            True if the member should be included
        """
        return should_include_member(name, self.config.include_private)

    def generate_stub(
        self, source_file: str | Path, ast_tree: AST | None = None
    ) -> str:
        """Generate a stub file from the given source file or AST.

        Args:
            source_file: Path to the source file
            ast_tree: Optional pre-parsed AST

        Returns:
            Generated stub content as a string
        """
        self.current_file = Path(source_file)

        if ast_tree is None:
            with open(source_file, encoding="utf-8") as f:
                source = f.read()
            ast_tree = parse(source)

        if not isinstance(ast_tree, Module):
            raise ValueError("AST must be a Module node")

        attach_parents(ast_tree)

        # Initialize visitor and process AST
        visitor = StubVisitor(self.config)
        visitor.visit(ast_tree)

        # Add header if configured
        lines: list[str] = []
        if self.config.add_header:
            lines.append('"""# Generated stub file"""\n')

        # Process imports
        if not self.config.no_import:
            sorted_imports = visitor.get_sorted_imports()
            lines.extend(sorted_imports)
            if sorted_imports:
                lines.append("")

        # Process classes
        for class_def in visitor.classes:
            class_lines = self._process_class_to_lines(class_def)
            if class_lines:  # Only add if we got lines back
                lines.extend(class_lines)
                lines.append("")

        # Process functions
        for func_def in visitor.functions:
            func_lines = self._process_function_to_lines(func_def)
            if func_lines:  # Only add if we got lines back
                lines.extend(func_lines)
                lines.append("")

        # Process assignments
        for assignment in visitor.assignments:
            assign_lines = self._process_assignment_to_lines(assignment)
            if assign_lines:  # Only add if we got lines back
                lines.extend(assign_lines)
                lines.append("")

        # Remove trailing newlines and join
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    def _process_class_to_lines(self, node: ClassDef) -> list[str]:
        """Process a class definition to lines.

        Args:
            node: Class definition AST node

        Returns:
            List of lines for the stub
        """
        # Check if class should be included
        if not self._should_include_member(node.name):
            return []

        lines: list[str] = []

        # Add docstring if present
        docstring = get_docstring(node)
        if docstring:
            lines.append(f'"""{docstring}"""')

        # Build class definition line
        bases = [unparse(base) for base in node.bases]
        if bases:
            lines.append(f"class {node.name}({', '.join(bases)}):")
        else:
            lines.append(f"class {node.name}:")

        # Process class body
        body_lines: list[str] = []
        for item in node.body:
            if isinstance(item, FunctionDef):
                if self._should_include_member(item.name):
                    method_lines = self._process_function_to_lines(item)
                    if method_lines:
                        body_lines.extend("    " + line for line in method_lines)
            elif isinstance(item, Assign | AnnAssign):
                assign_lines = self._process_assignment_to_lines(item)
                if assign_lines:
                    body_lines.extend("    " + line for line in assign_lines)

        # If no body, add pass statement
        if not body_lines:
            body_lines = ["    pass"]

        lines.extend(body_lines)
        return lines

    def _process_function_to_lines(self, node: FunctionDef) -> list[str]:
        """Process a function definition into lines of code.

        Args:
            node: The function definition node to process

        Returns:
            List of lines representing the function
        """
        lines = []

        # Add docstring if present
        if (
            node.body
            and len(node.body) > 0
            and isinstance(node.body[0], Expr)
            and isinstance(node.body[0].value, Constant)
        ):
            docstring = get_docstring(node)
            if docstring:
                lines.append(f'"""{docstring}"""')

        # Build function signature
        args_parts = []

        # Handle arguments
        for arg_node in node.args.args:
            arg_str = arg_node.arg
            if arg_node.annotation:
                arg_str += f": {self._format_annotation(arg_node.annotation)}"
            # Add default value if present
            arg_idx = node.args.args.index(arg_node)
            if node.args.defaults and arg_idx >= len(node.args.args) - len(
                node.args.defaults
            ):
                default_idx = arg_idx - (len(node.args.args) - len(node.args.defaults))
                default_value = self._format_annotation(node.args.defaults[default_idx])
                arg_str += f" = {default_value}"
            args_parts.append(arg_str)

        args_str = ", ".join(args_parts)
        returns_str = (
            f" -> {self._format_annotation(node.returns)}" if node.returns else ""
        )

        func_def = f"def {node.name}({args_str}){returns_str}:"
        lines.append(func_def)
        lines.append("    pass")

        return lines

    def _process_assignment_to_lines(self, node: Assign | AnnAssign) -> list[str]:
        """Process an assignment node into lines of code.

        Args:
            node: The assignment node to process

        Returns:
            List of lines representing the assignment
        """
        if isinstance(node, Assign):
            target = node.targets[0]
            if isinstance(target, Name):
                if isinstance(node.value, Constant):
                    value_str = repr(node.value.value)
                    type_str = type(node.value.value).__name__
                    return [f"{target.id}: {type_str} = {value_str}"]
                return [f"{target.id} = ..."]
        elif isinstance(node, AnnAssign):
            if isinstance(node.target, Name):
                annotation = unparse(node.annotation)
                if node.value is not None:
                    value_str = unparse(node.value)
                    return [f"{node.target.id}: {annotation} = {value_str}"]
                return [f"{node.target.id}: {annotation} = ..."]
        return []

    def _format_annotation(self, node: AST) -> str:
        """Format a type annotation node as a string.

        Args:
            node: The AST node representing the type annotation

        Returns:
            Formatted type annotation string
        """
        if isinstance(node, Name):
            return node.id
        elif isinstance(node, Constant):
            return repr(node.value)
        elif isinstance(node, Attribute):
            return f"{self._format_annotation(node.value)}.{node.attr}"
        elif isinstance(node, Subscript):
            return f"{self._format_annotation(node.value)}[{self._format_annotation(node.slice)}]"
        elif isinstance(node, BinOp):
            return f"{self._format_annotation(node.left)} | {self._format_annotation(node.right)}"
        elif isinstance(node, AstList):
            return f"[{', '.join(self._format_annotation(elt) for elt in node.elts)}]"
        elif isinstance(node, AstTuple):
            return f"({', '.join(self._format_annotation(elt) for elt in node.elts)})"
        else:
            return unparse(node)

    def _format_import(self, node: Import | ImportFrom) -> str:
        """Format an import node as a string.

        Args:
            node: The import node to format

        Returns:
            Formatted import statement
        """
        if isinstance(node, Import):
            return f"import {', '.join(sorted(alias.name for alias in node.names))}"
        else:
            from_part = f"from {node.module or '.'}"
            if node.level > 0:
                from_part = "from " + "." * node.level + (node.module or "")
            names_part = (
                f"import {', '.join(sorted(alias.name for alias in node.names))}"
            )
            return f"{from_part} {names_part}"

    def _sort_imports(self, imports: list[Import | ImportFrom]) -> list[str]:
        """Sort import statements."""
        stdlib_imports = []
        typing_imports = []
        pathlib_imports = []
        local_imports = []

        for node in imports:
            if isinstance(node, Import):
                module_path = node.names[0].name
                if module_path.startswith("typing"):
                    typing_imports.append(node)
                elif module_path.startswith("pathlib"):
                    pathlib_imports.append(node)
                elif module_path.startswith("."):
                    local_imports.append(node)
                else:
                    stdlib_imports.append(node)
            else:
                module_path = node.module or ""
                if node.level > 0:
                    local_imports.append(node)
                elif module_path.startswith("typing"):
                    typing_imports.append(node)
                elif module_path.startswith("pathlib"):
                    pathlib_imports.append(node)
                else:
                    stdlib_imports.append(node)

        sorted_imports = []
        for import_group in [
            stdlib_imports,
            pathlib_imports,
            typing_imports,
            local_imports,
        ]:
            for node in sorted(import_group, key=lambda x: x.names[0].name):
                sorted_imports.append(self._format_import(node))

        return sorted_imports

    def _import_sort_key(self, node: Import | ImportFrom) -> tuple[int, str, str]:
        """Generate a sort key for import statements.

        Args:
            node: The import node to generate a key for

        Returns:
            Tuple of (import_type, module_path, imported_names)
        """
        if isinstance(node, Import):
            module_path = node.names[0].name
            import_type = (
                1
                if any(module_path.startswith(imp) for imp in self.ESSENTIAL_IMPORTS)
                else 2
            )
            return (import_type, module_path, "")
        else:
            module_path = node.module or ""
            if node.level > 0:
                module_path = "." * node.level + module_path
            import_type = (
                1
                if any(module_path.startswith(imp) for imp in self.ESSENTIAL_IMPORTS)
                else 2
            )
            return (import_type, module_path, node.names[0].name)

    def _ensure_node_attributes(self, node: AST) -> None:
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
        for child in iter_child_nodes(node):
            self._ensure_node_attributes(child)

    def _generate_content(self, node: Module) -> str:
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
        source = unparse(node)

        # Fix spacing in function arguments and assignments
        source = source.replace("=", " = ")
        source = source.replace("  =  ", " = ")

        # Fix docstring formatting
        source = source.replace("'''", '"""')
        source = source.replace('""""""', '"""')

        # Add header and return
        return header + source

    def _collect_imports(self, node: Module) -> list[tuple[str, str]]:
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
            if isinstance(child, Import | ImportFrom) and self._should_keep_import(
                child
            ):
                if isinstance(child, ImportFrom):
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

    def _should_keep_import(self, node: Import | ImportFrom) -> bool:
        """Check if an import should be kept in the stub.

        Args:
            node: The import node to check

        Returns:
            True if the import should be kept
        """
        if isinstance(node, Import):
            return any(
                name.name in self.ESSENTIAL_IMPORTS or not name.name.startswith("_")
                for name in node.names
            )
        else:
            if node.level > 0:  # Always keep relative imports
                return True
            return bool(
                node.module
                and (
                    node.module in self.ESSENTIAL_IMPORTS
                    or not node.module.startswith("_")
                )
            )
