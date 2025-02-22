"""Test suite for twat_coding."""


def test_version() -> None:
    """Verify package exposes version."""
    import twat_coding

    assert twat_coding.__version__

#!/usr/bin/env -S uv run
"""Core tests for pystubnik."""

import asyncio
import pytest
from pathlib import Path
from twat_coding.pystubnik import SmartStubGenerator
from twat_coding.pystubnik.config import StubConfig
from twat_coding.pystubnik.backends.ast_backend import ASTBackend
from twat_coding.pystubnik.processors.importance import ImportanceProcessor
from twat_coding.pystubnik.core.types import StubResult


@pytest.mark.asyncio
async def test_ast_backend(tmp_path: Path) -> None:
    """Test AST stub generation."""
    test_file = tmp_path / "test.py"
    test_file.write_text('''"""
    Important file
    """
    def hello(name: str) -> str:
        return "Hello"
    ''')
    config = StubConfig(
        input_path=tmp_path,
        output_path=tmp_path,
        files=[test_file]
    )
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)
    stub_file = tmp_path / "test.pyi"
    assert "def hello(name: str) -> str" in result
    assert '"""Important file"""' in result  # Docstring preserved


def test_importance_processor(tmp_path: Path) -> None:
    """Test importance scoring affects stubs."""
    test_file = tmp_path / "low.py"
    test_file.write_text('''def minor():
        """Minor function"""
        pass
    ''')
    result = StubResult(
        source_path=test_file,
        stub_content='''def minor():
            """Minor function"""
            pass
        ''',
        imports=[],
        errors=[]
    )
    processor = ImportanceProcessor()
    processed = processor.process(result)
    assert processed.importance_score <= 0.7  # Low importance score


def test_cli(tmp_path: Path) -> None:
    """Test CLI end-to-end."""
    test_file = tmp_path / "cli.py"
    test_file.write_text("def run(): pass")
    import subprocess
    subprocess.run([
        "python", "-m", "twat_coding.pystubnik", "generate",
        "--files", str(test_file), "--output-dir", str(tmp_path)
    ], check=True)
    assert (tmp_path / "cli.pyi").exists()


def test_import_processor(tmp_path: Path) -> None:
    """Test import processing."""
    from twat_coding.pystubnik.processors.imports import ImportProcessor
    processor = ImportProcessor()
    result = StubResult(tmp_path / "test.py", "import os\n", [], [])
    processed = processor.process(result)
    assert "import os" in processed.stub_content


@pytest.mark.asyncio
async def test_docstring_preservation(tmp_path: Path) -> None:
    """Test docstring handling based on importance."""
    test_file = tmp_path / "important.py"
    test_file.write_text('''
    def critical_function():
        """This is a very important function that should keep its docstring."""
        pass

    def minor_function():
        """This is a less important function that might lose its docstring."""
        pass
    ''')
    config = StubConfig(
        input_path=tmp_path,
        output_path=tmp_path,
        files=[test_file]
    )
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)
    assert '"""This is a very important function' in result  # Important docstring kept
    assert "minor_function(): ..." in result  # Less important function simplified


@pytest.mark.asyncio
async def test_type_hints(tmp_path: Path) -> None:
    """Test type hint preservation."""
    test_file = tmp_path / "types.py"
    test_file.write_text('''
    from typing import List, Dict, Optional

    def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> bool:
        return True
    ''')
    config = StubConfig(
        input_path=tmp_path,
        output_path=tmp_path,
        files=[test_file]
    )
    backend = ASTBackend(config)
    result = await backend.generate_stub(test_file)
    assert "def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> bool:" in result
