"""Test package functionality."""

from pathlib import Path

import pytest

from twat_coding.pystubnik.backends.ast_backend import ASTBackend
from twat_coding.pystubnik.core.config import PathConfig, StubGenConfig


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
    assert "def hello(name: str) -> str" in result
    assert "Important function" in result


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
    assert "This is a very important function" in result


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
    assert (
        "def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> bool"
        in result
    )
