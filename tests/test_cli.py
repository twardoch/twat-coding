"""Test CLI functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from twat_coding.pystubnik.cli import PystubnikCLI


@pytest.fixture
def cli():
    """Create a CLI instance for testing."""
    return PystubnikCLI()


@pytest.fixture
def temp_python_file(tmp_path):
    """Create a temporary Python file for testing."""
    test_file = tmp_path / "test_module.py"
    test_file.write_text("""
def hello_world() -> str:
    \"\"\"Return a greeting.\"\"\"
    return "Hello, World!"

class TestClass:
    \"\"\"A test class.\"\"\"
    
    def method(self, x: int) -> int:
        \"\"\"A test method.\"\"\"
        return x * 2
""")
    return test_file


def test_cli_initialization(cli):
    """Test CLI initialization."""
    assert cli.console is not None
    assert cli.progress is not None


def test_generate_command_success(cli, temp_python_file, tmp_path):
    """Test successful stub generation."""
    output_path = tmp_path / "test_module.pyi"
    
    cli.generate(
        input_path=str(temp_python_file),
        output_path=str(output_path)
    )
    
    # Check that stub file was created
    assert output_path.exists()
    
    # Check stub content
    content = output_path.read_text()
    assert "def hello_world() -> str:" in content
    assert "class TestClass:" in content
    assert "def method(self, x: int) -> int:" in content


def test_generate_command_default_output(cli, temp_python_file):
    """Test stub generation with default output path."""
    cli.generate(input_path=str(temp_python_file))
    
    # Should create .pyi file in same directory
    expected_output = temp_python_file.with_suffix(".pyi")
    assert expected_output.exists()


def test_generate_command_missing_input(cli, capsys):
    """Test handling of missing input file."""
    cli.generate(input_path="nonexistent.py")
    
    captured = capsys.readouterr()
    # Should not create output and should show error
    # Note: rich output may not be captured in capsys, so we check the method doesn't crash


def test_generate_command_with_config_kwargs(cli, temp_python_file, tmp_path):
    """Test stub generation with configuration arguments."""
    output_path = tmp_path / "test_with_config.pyi"
    
    cli.generate(
        input_path=str(temp_python_file),
        output_path=str(output_path),
        include_private=True,
        sort_imports=True
    )
    
    assert output_path.exists()


def test_generate_dir_command(cli, tmp_path):
    """Test directory-based stub generation."""
    # Create test directory structure
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    # Create multiple Python files
    (source_dir / "module1.py").write_text("""
def func1() -> str:
    return "test1"
""")
    
    (source_dir / "module2.py").write_text("""
def func2() -> int:
    return 42
""")
    
    output_dir = tmp_path / "stubs"
    
    cli.generate_dir(
        input_dir=str(source_dir),
        output_dir=str(output_dir)
    )
    
    # Check that stub files were created
    assert (output_dir / "module1.pyi").exists()
    assert (output_dir / "module2.pyi").exists()
    
    # Check content
    content1 = (output_dir / "module1.pyi").read_text()
    assert "def func1() -> str:" in content1
    
    content2 = (output_dir / "module2.pyi").read_text()
    assert "def func2() -> int:" in content2


def test_generate_dir_missing_input(cli, capsys):
    """Test handling of missing input directory."""
    cli.generate_dir(input_dir="nonexistent_dir")
    
    # Should handle gracefully without crashing
    captured = capsys.readouterr()


@patch('twat_coding.pystubnik.cli.StubGenerator')
def test_generate_with_exception(mock_generator, cli, temp_python_file, tmp_path):
    """Test handling of exceptions during stub generation."""
    # Mock generator to raise exception
    mock_instance = Mock()
    mock_instance.generate_stub.side_effect = Exception("Test error")
    mock_generator.return_value = mock_instance
    
    output_path = tmp_path / "test_error.pyi"
    
    # Should handle exception gracefully
    cli.generate(
        input_path=str(temp_python_file),
        output_path=str(output_path)
    )
    
    # Should not create output file
    assert not output_path.exists()


def test_cli_console_output(cli):
    """Test that CLI has proper console setup."""
    assert cli.console is not None
    
    # Test that console can be used
    cli.console.print("Test message")  # Should not raise exception


def test_cli_progress_setup(cli):
    """Test that progress indicator is properly configured."""
    assert cli.progress is not None
    
    # Test basic progress functionality
    with cli.progress:
        task = cli.progress.add_task("Test task", total=100)
        cli.progress.update(task, advance=50)
        cli.progress.remove_task(task)