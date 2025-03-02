"""Test package functionality."""

from pathlib import Path

import pytest
from twat_coding.pystubnik.backends.ast_backend import ASTBackend
from twat_coding.pystubnik.backends.mypy_backend import MypyBackend
from twat_coding.pystubnik.config import StubConfig
from twat_coding.pystubnik.core.config import (Backend, PathConfig,
                                               StubGenConfig)
from twat_coding.pystubnik.core.conversion import convert_to_stub_gen_config
from twat_coding.pystubnik.processors.stub_generation import StubGenerator
from twat_coding.pystubnik.types.docstring import DocstringTypeExtractor
from twat_coding.pystubnik.types.type_system import TypeRegistry


@pytest.mark.asyncio
async def test_ast_backend(tmp_path: Path) -> None:
    """Test AST stub generation."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def hello(name: str) -> str:
    \"\"\"Important function.\"\"\"
    return "Hello"
""")
    config = StubGenConfig(paths=PathConfig(output_dir=tmp_path, files=[test_file]))
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)
    assert "def hello(name: str) -> str" in result.stub_content
    assert "Important function" in result.stub_content


@pytest.mark.asyncio
async def test_docstring_preservation(tmp_path: Path) -> None:
    """Test docstring handling based on importance."""
    test_file = tmp_path / "important.py"
    test_file.write_text("""
def critical_function():
    \"\"\"This is a very important function that should keep its docstring.\"\"\"
    pass

def minor_function():
    \"\"\"This is a less important function that might lose its docstring.\"\"\"
    pass
""")
    config = StubGenConfig(paths=PathConfig(output_dir=tmp_path, files=[test_file]))
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)
    assert "This is a very important function" in result.stub_content


@pytest.mark.asyncio
async def test_type_hints(tmp_path: Path) -> None:
    """Test type hint preservation."""
    test_file = tmp_path / "types.py"
    test_file.write_text("""
from typing import List, Dict, Optional

def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> bool:
    return True
""")
    config = StubGenConfig(paths=PathConfig(output_dir=tmp_path, files=[test_file]))
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)

    # Remove all spaces to handle different formatting styles
    result_no_spaces = result.stub_content.replace(" ", "")
    expected_no_spaces = "config:Optional[Dict[str,int]]"

    # Check each part of the type hint separately
    assert "def process_data" in result.stub_content
    assert "items:List[str]" in result_no_spaces
    assert expected_no_spaces in result_no_spaces
    assert "->bool" in result_no_spaces


def test_config_conversion() -> None:
    """Test conversion between StubConfig and StubGenConfig."""
    # Create a StubConfig with various settings
    stub_config = StubConfig(
        input_path=Path("src"),
        output_path=Path("out"),
        backend="ast",
        parallel=True,
        max_workers=4,
        infer_types=True,
        preserve_literals=True,
        docstring_type_hints=True,
        python_version=(3, 12),
        search_paths=["lib", "tests"],
        include_private=True,
        files=[Path("main.py")],
        importance_patterns={"critical": 1.0},
        max_docstring_length=150,
        line_length=88,
        sort_imports=True,
        add_header=True,
        no_import=False,
        inspect=False,
        doc_dir="",
        ignore_errors=True,
        parse_only=False,
        verbose=False,
        quiet=True,
        export_less=False,
        include_type_comments=True,
        infer_property_types=True,
        modules=[],
        packages=[],
    )

    # Convert to StubGenConfig
    stub_gen_config = convert_to_stub_gen_config(stub_config)

    # Verify conversion results
    assert stub_gen_config.paths.output_dir == Path("out")
    assert stub_gen_config.runtime.backend == Backend.AST
    assert stub_gen_config.runtime.parallel is True
    assert stub_gen_config.runtime.max_workers == 4
    assert stub_gen_config.runtime.python_version == (3, 12)
    assert stub_gen_config.processing.include_docstrings is True
    assert stub_gen_config.processing.include_private is True
    assert stub_gen_config.truncation.max_docstring_length == 150
    assert Path("main.py") in stub_gen_config.paths.files
    assert stub_gen_config.processing.importance_patterns == {"critical": 1.0}


@pytest.mark.asyncio
async def test_backend_type_compatibility() -> None:
    """Test type compatibility between different backends."""
    test_file = Path("test.py")

    # Create configs for both backends
    ast_config = StubGenConfig(paths=PathConfig(files=[test_file]))
    mypy_config = StubGenConfig(paths=PathConfig(files=[test_file]))

    # Initialize backends
    ast_backend = ASTBackend(ast_config)
    mypy_backend = MypyBackend(mypy_config)

    # Verify both backends implement StubBackend protocol
    assert hasattr(ast_backend, "generate_stub")
    assert hasattr(mypy_backend, "generate_stub")

    # Verify return type annotations
    from inspect import signature

    ast_sig = signature(ast_backend.generate_stub)
    mypy_sig = signature(mypy_backend.generate_stub)

    assert str(ast_sig.return_annotation) == str(mypy_sig.return_annotation)


def test_docstring_type_extraction() -> None:
    """Test extraction of type information from docstrings."""
    type_registry = TypeRegistry()
    extractor = DocstringTypeExtractor(type_registry)

    # Test basic type parsing
    type_info = extractor._parse_type_string("str")
    assert isinstance(type_info.annotation, type) and issubclass(
        type_info.annotation, str
    )
    assert type_info.confidence == 0.8

    # Test union type parsing
    type_info = extractor._parse_type_string("str or None")
    assert type_info.confidence == 0.7
    assert "union_types" in type_info.metadata

    # Test generic type parsing
    type_info = extractor._parse_type_string("List[str]")
    assert type_info.confidence == 0.7
    assert type_info.metadata["container"] == "List"

    # Test dict type parsing
    type_info = extractor._parse_type_string("Dict[str, int]")
    assert type_info.confidence == 0.7
    assert "key_type" in type_info.metadata
    assert "value_type" in type_info.metadata


def test_stub_generation_basic(tmp_path: Path) -> None:
    """Test basic stub generation functionality."""
    # Create a test file with various Python constructs
    test_file = tmp_path / "test_stub.py"
    test_file.write_text("""
import typing
from pathlib import Path
from typing import List, Optional

class MyClass:
    \"\"\"Test class docstring.\"\"\"

    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, items: List[int]) -> Optional[str]:
        \"\"\"Process items.\"\"\"
        return None

def helper(x: int = 42) -> bool:
    \"\"\"Helper function.\"\"\"
    return True

CONSTANT: int = 100
""")

    # Create stub generator with default config
    generator = StubGenerator()

    # Generate stub
    stub_content = generator.generate_stub(test_file)

    # Verify stub content
    assert "import typing" in stub_content
    assert "from pathlib import Path" in stub_content
    assert "from typing import List, Optional" in stub_content
    assert "class MyClass:" in stub_content
    assert '"""Test class docstring."""' in stub_content
    assert "def __init__(self, name: str) -> None:" in stub_content
    assert "def process(self, items: List[int]) -> Optional[str]:" in stub_content
    assert '"""Process items."""' in stub_content
    assert "def helper(x: int = 42) -> bool:" in stub_content
    assert "CONSTANT: int = 100" in stub_content


def test_stub_generation_config(tmp_path: Path) -> None:
    """Test stub generation with different configurations."""
    test_file = tmp_path / "test_config.py"
    test_file.write_text("""
class PrivateClass:
    \"\"\"Private class docstring.\"\"\"
    def __private_method(self) -> None:
        pass

class PublicClass:
    \"\"\"Public class docstring.\"\"\"
    def public_method(self) -> str:
        return "public"
""")

    # Test with private members excluded
    config = StubConfig(
        input_path=tmp_path,
        output_path=tmp_path / "stubs",
        include_private=False,
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
        verbose=False,
        quiet=True,
        export_less=False,
        max_docstring_length=150,
        include_type_comments=True,
        infer_property_types=True,
    )
    generator = StubGenerator(config)
    stub_content = generator.generate_stub(test_file)

    # Verify private members are excluded
    assert "class PrivateClass:" not in stub_content
    assert "def __private_method" not in stub_content
    assert "class PublicClass:" in stub_content
    assert "def public_method" in stub_content


def test_stub_generation_imports(tmp_path: Path) -> None:
    """Test import handling in stub generation."""
    test_file = tmp_path / "test_imports.py"
    test_file.write_text("""
from typing import List, Dict
import sys
import os.path
from pathlib import Path
from .local_module import something
from typing import Optional

def func(x: List[int], y: Dict[str, Optional[Path]]) -> None:
    pass
""")

    # Test with sorted imports
    config = StubConfig(
        input_path=tmp_path,
        output_path=tmp_path / "stubs",
        sort_imports=True,
        backend="ast",
        parallel=True,
        max_workers=None,
        infer_types=True,
        preserve_literals=False,
        docstring_type_hints=True,
        line_length=88,
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
    generator = StubGenerator(config)
    stub_content = generator.generate_stub(test_file)

    # Verify imports are sorted
    lines = stub_content.split("\n")
    import_lines = [line for line in lines if line.startswith(("import", "from"))]
    assert import_lines == [
        "import os.path",
        "import sys",
        "from pathlib import Path",
        "from typing import Dict, List, Optional",
        "from .local_module import something",
    ]


def test_stub_generation_assignments(tmp_path: Path) -> None:
    """Test handling of variable assignments in stub generation."""
    test_file = tmp_path / "test_assignments.py"
    test_file.write_text("""
from typing import List, Optional

# Type annotated assignments
x: int = 42
names: List[str] = ["a", "b"]
maybe: Optional[float] = None

# Regular assignments
CONSTANT = "value"
FLAG = True
""")

    generator = StubGenerator()
    stub_content = generator.generate_stub(test_file)

    # Verify type annotated assignments are preserved
    assert "x: int" in stub_content
    assert "names: List[str]" in stub_content
    assert "maybe: Optional[float]" in stub_content

    # Verify regular assignments are preserved with inferred types
    assert "CONSTANT: str = 'value'" in stub_content
    assert "FLAG: bool = True" in stub_content
