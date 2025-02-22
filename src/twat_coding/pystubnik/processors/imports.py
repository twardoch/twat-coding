"""Import analysis for stub generation."""

import ast
from pathlib import Path

from pystubnik.core.types import ImportInfo, ImportType, StubResult
from pystubnik.processors import Processor


class ImportProcessor(Processor):
    """Processor for analyzing and organizing imports in stub generation."""

    def __init__(self):
        self.stdlib_modules: set[str] = self._get_stdlib_modules()

    def process(self, stub_result: StubResult) -> StubResult:
        """Process imports in the stub result.

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result with organized imports
        """
        tree = ast.parse(stub_result.stub_content)
        imports = self._analyze_imports(tree)

        # Group imports by type
        grouped_imports = self._group_imports(imports)

        # Generate new import section
        new_imports = self._format_imports(grouped_imports)

        # Replace imports in stub content
        stub_result.stub_content = self._replace_imports(tree, new_imports)
        stub_result.imports = list(imports.values())

        return stub_result

    def _get_stdlib_modules(self) -> set[str]:
        """Get a set of standard library module names."""
        import sysconfig

        stdlib_path = sysconfig.get_path("stdlib")
        if not stdlib_path:
            return set()

        stdlib_modules = set()
        for path in Path(stdlib_path).glob("**/*.py"):
            module_name = path.stem
            if module_name != "__init__":
                stdlib_modules.add(module_name)

        return stdlib_modules

    def _analyze_imports(self, tree: ast.AST) -> dict[str, ImportInfo]:
        """Analyze imports in an AST.

        Args:
            tree: The AST to analyze

        Returns:
            Dictionary mapping module names to ImportInfo
        """
        imports: dict[str, ImportInfo] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    module_name = name.name
                    import_type = self._get_import_type(module_name)
                    imports[module_name] = ImportInfo(
                        module_name=module_name,
                        import_type=import_type,
                        imported_names=[name.asname or name.name],
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                import_type = self._get_import_type(module)
                if module not in imports:
                    imports[module] = ImportInfo(
                        module_name=module,
                        import_type=import_type,
                        imported_names=[],
                        is_from_import=True,
                        relative_level=node.level,
                    )
                for name in node.names:
                    imports[module].imported_names.append(name.asname or name.name)

        return imports

    def _get_import_type(self, module_name: str) -> ImportType:
        """Determine the type of an import.

        Args:
            module_name: Name of the module

        Returns:
            The ImportType of the module
        """
        if not module_name:
            return ImportType.RELATIVE

        base_module = module_name.split(".")[0]
        if base_module in self.stdlib_modules:
            return ImportType.STANDARD_LIB
        elif "." in module_name:
            return ImportType.LOCAL
        else:
            return ImportType.THIRD_PARTY

    def _group_imports(
        self, imports: dict[str, ImportInfo]
    ) -> dict[ImportType, list[ImportInfo]]:
        """Group imports by their type.

        Args:
            imports: Dictionary of imports to group

        Returns:
            Dictionary mapping import types to lists of imports
        """
        grouped: dict[ImportType, list[ImportInfo]] = {
            ImportType.STANDARD_LIB: [],
            ImportType.THIRD_PARTY: [],
            ImportType.LOCAL: [],
            ImportType.RELATIVE: [],
        }

        for import_info in imports.values():
            grouped[import_info.import_type].append(import_info)

        # Sort each group
        for group in grouped.values():
            group.sort(key=lambda x: x.module_name)

        return grouped

    def _format_imports(
        self, grouped_imports: dict[ImportType, list[ImportInfo]]
    ) -> str:
        """Format grouped imports into a string.

        Args:
            grouped_imports: Dictionary of grouped imports

        Returns:
            Formatted import section as a string
        """
        sections = []

        for import_type in ImportType:
            imports = grouped_imports[import_type]
            if not imports:
                continue

            section = []
            for import_info in imports:
                if import_info.is_from_import:
                    relative = "." * import_info.relative_level
                    names = ", ".join(sorted(import_info.imported_names))
                    section.append(
                        f"from {relative}{import_info.module_name} import {names}"
                    )
                else:
                    section.append(f"import {import_info.module_name}")

            if section:
                sections.append("\n".join(sorted(section)))

        return "\n\n".join(sections) + "\n\n"

    def _replace_imports(self, tree: ast.AST, new_imports: str) -> str:
        """Replace imports in the AST with new formatted imports.

        Args:
            tree: The AST to modify
            new_imports: The new import section

        Returns:
            Modified source code as a string
        """
        # Find the last import node
        last_import = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                last_import = node

        if last_import:
            # Get the source up to the first import and after the last import
            source_lines = ast.unparse(tree).split("\n")
            first_import_line = min(
                node.lineno
                for node in ast.walk(tree)
                if isinstance(node, ast.Import | ast.ImportFrom)
            )
            last_import_line = max(
                node.end_lineno or node.lineno
                for node in ast.walk(tree)
                if isinstance(node, ast.Import | ast.ImportFrom)
            )

            before = "\n".join(source_lines[: first_import_line - 1])
            after = "\n".join(source_lines[last_import_line:])

            return f"{before}\n{new_imports}{after}"

        return ast.unparse(tree)
