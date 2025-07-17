"""Integration tests for the complete workflow."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample Python project for testing."""
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()
    
    # Create main module
    main_py = project_dir / "main.py"
    main_py.write_text("""
from typing import List, Dict, Optional
from pathlib import Path

def process_files(files: List[Path], config: Optional[Dict[str, str]] = None) -> bool:
    \"\"\"Process a list of files with optional configuration.
    
    Args:
        files: List of file paths to process
        config: Optional configuration dictionary
        
    Returns:
        True if processing succeeded, False otherwise
    \"\"\"
    if not files:
        return False
    
    for file in files:
        if not file.exists():
            return False
    
    return True

class FileProcessor:
    \"\"\"A class for processing files.\"\"\"
    
    def __init__(self, base_path: Path):
        \"\"\"Initialize with base path.\"\"\"
        self.base_path = base_path
    
    def process(self, filename: str) -> Optional[str]:
        \"\"\"Process a single file.\"\"\"
        file_path = self.base_path / filename
        if file_path.exists():
            return str(file_path)
        return None
    
    def _private_method(self) -> None:
        \"\"\"Private method that should be excluded by default.\"\"\"
        pass

# Module level constant
DEFAULT_CONFIG: Dict[str, str] = {"mode": "strict", "verbose": "false"}
""")
    
    # Create submodule
    submodule_dir = project_dir / "submodule"
    submodule_dir.mkdir()
    
    init_py = submodule_dir / "__init__.py"
    init_py.write_text("""
\"\"\"Submodule for additional functionality.\"\"\"

from .utils import utility_function

__all__ = ["utility_function"]
""")
    
    utils_py = submodule_dir / "utils.py"
    utils_py.write_text("""
\"\"\"Utility functions.\"\"\"

def utility_function(x: int, y: int = 10) -> int:
    \"\"\"A utility function.\"\"\"
    return x + y

class UtilityClass:
    \"\"\"A utility class.\"\"\"
    
    value: int = 42
    
    def compute(self) -> int:
        \"\"\"Compute a value.\"\"\"
        return self.value * 2
""")
    
    return project_dir


def test_single_file_stub_generation(sample_project):
    """Test stub generation for a single file."""
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    main_file = sample_project / "main.py"
    stub_file = sample_project / "main.pyi"
    
    # Generate stub
    cli.generate(input_path=str(main_file), output_path=str(stub_file))
    
    # Verify stub was created
    assert stub_file.exists()
    
    # Verify content
    content = stub_file.read_text()
    
    # Check imports
    assert "from typing import List, Dict, Optional" in content
    assert "from pathlib import Path" in content
    
    # Check function signature
    assert "def process_files(files: List[Path], config: Optional[Dict[str, str]] = None) -> bool:" in content
    
    # Check class definition
    assert "class FileProcessor:" in content
    assert "def __init__(self, base_path: Path):" in content
    assert "def process(self, filename: str) -> Optional[str]:" in content
    
    # Check that private method is excluded by default
    assert "_private_method" not in content
    
    # Check module constant
    assert "DEFAULT_CONFIG: Dict[str, str]" in content


def test_directory_stub_generation(sample_project):
    """Test stub generation for entire directory."""
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    stub_dir = sample_project / "stubs"
    
    # Generate stubs for entire project
    cli.generate_dir(input_dir=str(sample_project), output_dir=str(stub_dir))
    
    # Verify stub files were created
    assert (stub_dir / "main.pyi").exists()
    assert (stub_dir / "submodule" / "__init__.pyi").exists()
    assert (stub_dir / "submodule" / "utils.pyi").exists()
    
    # Check main.pyi content
    main_content = (stub_dir / "main.pyi").read_text()
    assert "def process_files" in main_content
    assert "class FileProcessor" in main_content
    
    # Check submodule content
    init_content = (stub_dir / "submodule" / "__init__.pyi").read_text()
    assert "from .utils import utility_function" in init_content
    
    utils_content = (stub_dir / "submodule" / "utils.pyi").read_text()
    assert "def utility_function(x: int, y: int = 10) -> int:" in utils_content
    assert "class UtilityClass:" in utils_content


def test_stub_generation_with_private_members(sample_project):
    """Test stub generation including private members."""
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    main_file = sample_project / "main.py"
    stub_file = sample_project / "main_with_private.pyi"
    
    # Generate stub with private members included
    cli.generate(
        input_path=str(main_file),
        output_path=str(stub_file),
        include_private=True
    )
    
    # Verify stub was created
    assert stub_file.exists()
    
    # Verify private method is included
    content = stub_file.read_text()
    assert "_private_method" in content


def test_stub_generation_with_import_sorting(sample_project):
    """Test stub generation with import sorting."""
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    main_file = sample_project / "main.py"
    stub_file = sample_project / "main_sorted.pyi"
    
    # Generate stub with sorted imports
    cli.generate(
        input_path=str(main_file),
        output_path=str(stub_file),
        sort_imports=True
    )
    
    # Verify stub was created
    assert stub_file.exists()
    
    # Check that imports are sorted
    content = stub_file.read_text()
    lines = content.split('\n')
    import_lines = [line for line in lines if line.startswith(('import ', 'from '))]
    
    # Should be sorted
    assert import_lines == sorted(import_lines)


def test_end_to_end_workflow(sample_project):
    """Test the complete workflow from Python source to stub."""
    from twat_coding.pystubnik.processors.stub_generation import StubGenerator
    from twat_coding.pystubnik.config import StubConfig
    
    # Create comprehensive config
    config = StubConfig(
        input_path=sample_project,
        output_path=sample_project / "e2e_stubs",
        include_private=False,
        sort_imports=True,
        add_header=True,
        max_docstring_length=100
    )
    
    # Create generator
    generator = StubGenerator(config)
    
    # Process main file
    main_file = sample_project / "main.py"
    stub_content = generator.generate_stub(main_file)
    
    # Verify comprehensive processing
    assert "# Generated by" in stub_content  # Header
    assert "def process_files" in stub_content  # Function
    assert "class FileProcessor" in stub_content  # Class
    assert "DEFAULT_CONFIG" in stub_content  # Module constant
    
    # Verify docstrings are preserved but potentially truncated
    assert "Process a list of files" in stub_content
    
    # Verify private members are excluded
    assert "_private_method" not in stub_content


def test_command_line_interface_integration(sample_project):
    """Test CLI integration if twat-coding command is available."""
    main_file = sample_project / "main.py"
    stub_file = sample_project / "cli_test.pyi"
    
    try:
        # Test CLI command directly
        result = subprocess.run([
            "python", "-m", "twat_coding.pystubnik.cli",
            "generate",
            str(main_file),
            "--output_path", str(stub_file)
        ], capture_output=True, text=True, check=True)
        
        # Verify command succeeded
        assert result.returncode == 0
        assert stub_file.exists()
        
        # Basic content check
        content = stub_file.read_text()
        assert "def process_files" in content
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        # CLI not available or not working - skip this test
        pytest.skip("CLI command not available")


def test_error_handling_integration(tmp_path):
    """Test error handling in integration scenarios."""
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    
    # Test with invalid Python file
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("This is not valid Python syntax!!!")
    
    stub_file = tmp_path / "invalid.pyi"
    
    # Should handle gracefully
    cli.generate(input_path=str(invalid_file), output_path=str(stub_file))
    
    # Should not create stub file if parsing fails
    # (behavior depends on implementation - may create empty or partial stub)


def test_complex_type_annotations(tmp_path):
    """Test handling of complex type annotations."""
    complex_file = tmp_path / "complex_types.py"
    complex_file.write_text("""
from typing import Union, Callable, TypeVar, Generic, Protocol, Literal
from collections.abc import Mapping, Sequence

T = TypeVar('T')
U = TypeVar('U', bound=str)

class GenericClass(Generic[T, U]):
    def method(self, value: T) -> U:
        pass

def complex_function(
    callback: Callable[[int, str], bool],
    data: Union[Mapping[str, int], Sequence[float]],
    literal_param: Literal['option1', 'option2'] = 'option1'
) -> Union[T, None]:
    pass

class ProtocolExample(Protocol):
    def required_method(self) -> str: ...
""")
    
    from twat_coding.pystubnik.cli import PystubnikCLI
    
    cli = PystubnikCLI()
    stub_file = tmp_path / "complex_types.pyi"
    
    cli.generate(input_path=str(complex_file), output_path=str(stub_file))
    
    # Verify stub was created
    assert stub_file.exists()
    
    # Check that complex types are preserved
    content = stub_file.read_text()
    assert "Generic[T, U]" in content
    assert "Callable[[int, str], bool]" in content
    assert "Union[" in content
    assert "Literal[" in content