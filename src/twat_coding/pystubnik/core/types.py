#!/usr/bin/env python3
"""Core type definitions for pystubnik."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, Union


@dataclass(frozen=True)
class ArgInfo:
    """Information about a function argument."""

    name: str
    type: str | None = None
    default: bool = False
    default_value: Any | None = None
    is_kwonly: bool = False
    is_posonly: bool = False
    is_variadic: bool = False


@dataclass(frozen=True)
class FunctionInfo:
    """Information about a function or method."""

    name: str
    args: Sequence[ArgInfo]
    return_type: str | None = None
    docstring: str | None = None
    decorators: Sequence[str] = ()
    is_async: bool = False
    is_generator: bool = False
    is_abstract: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    importance_score: float = 1.0


@dataclass(frozen=True)
class ClassInfo:
    """Information about a class."""

    name: str
    bases: Sequence[str] = ()
    docstring: str | None = None
    decorators: Sequence[str] = ()
    methods: Sequence[FunctionInfo] = ()
    properties: Sequence[FunctionInfo] = ()
    class_vars: dict[str, str] = field(default_factory=dict)  # name -> type
    instance_vars: dict[str, str] = field(default_factory=dict)  # name -> type
    is_abstract: bool = False
    importance_score: float = 1.0


@dataclass(frozen=True)
class ModuleInfo:
    """Information about a module."""

    name: str
    path: Path | None = None
    docstring: str | None = None
    imports: Sequence[str] = ()
    functions: Sequence[FunctionInfo] = ()
    classes: Sequence[ClassInfo] = ()
    variables: dict[str, str] = field(default_factory=dict)  # name -> type
    all_names: Sequence[str] | None = None
    importance_score: float = 1.0


class StubBackend(Protocol):
    """Protocol for stub generation backends."""

    def generate_module_info(self, module_path: Path) -> ModuleInfo:
        """Generate module information from a source file."""
        ...

    def generate_stub(self, module_info: ModuleInfo) -> str:
        """Generate stub content from module information."""
        ...


class ImportProcessor(Protocol):
    """Protocol for import processing."""

    def process_imports(self, source: str) -> Sequence[str]:
        """Extract and process imports from source code."""
        ...

    def sort_imports(self, imports: Sequence[str]) -> Sequence[str]:
        """Sort imports in a standard way."""
        ...


class DocstringProcessor(Protocol):
    """Protocol for docstring processing."""

    def process_docstring(
        self, docstring: str | None, context: dict[str, Any]
    ) -> tuple[str | None, dict[str, Any]]:
        """Process a docstring and extract type information."""
        ...


class ImportanceScorer(Protocol):
    """Protocol for importance scoring."""

    def calculate_score(
        self,
        name: str,
        docstring: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> float:
        """Calculate importance score for a symbol."""
        ...


class ImportType(Enum):
    """Types of imports that can be found in Python code."""

    STANDARD_LIB = "stdlib"
    THIRD_PARTY = "third_party"
    LOCAL = "local"
    RELATIVE = "relative"


@dataclass
class ImportInfo:
    """Information about an import statement."""

    module_name: str
    import_type: "ImportType"
    imported_names: list[str]
    is_from_import: bool = False
    relative_level: int = 0


@dataclass
class StubResult:
    """Result of stub generation."""

    source_path: Path
    stub_content: str
    imports: list[ImportInfo]
    errors: list[str]
    importance_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# Type aliases
PathLike = Union[str, Path]
ImportMap = dict[str, ImportInfo]
StubMap = dict[PathLike, StubResult]
