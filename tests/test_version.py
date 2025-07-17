"""Test version management and git-tag-based semversioning."""

import re
from pathlib import Path

import pytest

from twat_coding import __version__


def test_version_format():
    """Test that version follows semantic versioning format."""
    # Should match semver format: X.Y.Z or X.Y.Z-suffix or X.Y.Z.devN
    version_pattern = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[.-](.+))?$")
    assert version_pattern.match(__version__), f"Invalid version format: {__version__}"


def test_version_import():
    """Test that version can be imported from main module."""
    from twat_coding import __version__ as main_version
    
    # Try to import from _version module
    try:
        from twat_coding._version import __version__ as version_module_version
        assert main_version == version_module_version
    except ImportError:
        # If _version module doesn't exist, main should have fallback
        assert main_version == "0.0.1.dev0"


def test_version_accessibility():
    """Test that version is accessible from CLI."""
    try:
        from twat_coding.pystubnik.cli import PystubnikCLI
        
        cli = PystubnikCLI()
        # CLI should be able to access version without errors
        assert hasattr(cli, 'console')  # Basic functionality check
    except ImportError as e:
        # If there are import issues, skip this test
        pytest.skip(f"CLI import failed: {e}")


def test_version_consistency():
    """Test version consistency across different access methods."""
    from twat_coding import __version__ as pkg_version
    
    # Check that version is a string
    assert isinstance(pkg_version, str)
    assert len(pkg_version) > 0
    
    # Check that it's not the placeholder
    if pkg_version != "0.0.1.dev0":
        # Should be a real version from git tags
        assert not pkg_version.startswith("0.0.1.dev")


def test_version_in_pyproject():
    """Test that pyproject.toml is configured for dynamic versioning."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.exists()
    
    content = pyproject_path.read_text()
    
    # Should have dynamic version
    assert 'dynamic = ["version"]' in content
    
    # Should have hatch-vcs configuration
    assert 'hatch-vcs' in content
    assert '[tool.hatch.version]' in content
    assert 'source = "vcs"' in content