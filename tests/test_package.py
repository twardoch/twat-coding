"""Test package functionality."""

from pathlib import Path

import pytest

from twat_coding.pystubnik.backends.ast_backend import ASTBackend
from twat_coding.pystubnik.backends.mypy_backend import MypyBackend
from twat_coding.pystubnik.config import StubConfig
from twat_coding.pystubnik.core.config import (
    Backend,
    PathConfig,
    StubGenConfig,
)
from twat_coding.pystubnik.core.conversion import convert_to_stub_gen_config
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
    assert type_info.annotation == str
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
