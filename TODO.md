# TODO

## 1. Foundation Improvements (High Priority)

### 1.1. Error Handling & Validation (Completed)
- [x] Create unified error handling system:
  - [x] Add `StubGenerationError` base class:
    ```python
    class StubGenerationError(Exception):
        """Base class for all stub generation errors."""
        def __init__(self, message: str, code: str, details: dict[str, str] | None = None):
            self.code = code
            self.details = details or {}
            super().__init__(message)
    ```
  - [x] Create backend-specific errors:
    ```python
    class ASTError(StubGenerationError):
        """AST processing errors."""
        pass

    class MyPyError(StubGenerationError):
        """MyPy backend errors."""
        pass
    ```
  - [x] Add error code taxonomy in `error_codes.py`:
    ```python
    from enum import Enum, auto
    
    class ErrorCode(str, Enum):
        """Error codes for stub generation."""
        AST_PARSE_ERROR = "AST001"
        TYPE_INFERENCE_ERROR = "TYPE001"
        CONFIG_ERROR = "CFG001"
    ```
  - [x] Implement error recovery strategies using context managers

- [x] Add configuration validation:
  - [x] Define JSON Schema for TOML config in `config_schema.json`
  - [x] Add runtime validation using Pydantic models
  - [x] Create config migration system with version tracking
  - [x] Add config diffing for changes using `deepdiff`

### 1.2. Core Architecture Improvements (Completed)
- [x] Enhance AST backend with advanced concurrency:
  - [x] Implement asyncio-based processing with `asyncio.gather`
  - [x] Add LRU cache using `functools.lru_cache`
  - [x] Create AST node registry using weak references
  - [x] Add incremental parsing support with file checksums
- [x] Optimize memory usage for large codebases:
  - [x] Profile memory usage with `memory_profiler`
  - [x] Implement memory-efficient AST traversal using generators
  - [x] Add streaming processing for large files
  - [x] Set up memory usage monitoring with `psutil`

### 1.3. Type System Enhancements (Completed)
- [x] Improve type preservation:
  - [x] Handle PEP 593 Annotated types with full metadata
  - [x] Support TypeVar and generic types with bounds
  - [x] Add type alias resolution with dependency tracking
  - [x] Preserve typing.Protocol definitions with docstrings
- [x] Integrate type hint extraction from docstrings:
  - [x] Parse docstring type hints using `docstring_parser`
  - [x] Merge with explicit annotations using precedence rules
  - [x] Handle conflicting type information with warnings
  - [x] Support multiple docstring formats (Google, NumPy, reST)

### 1.4. Development Infrastructure (High Priority, Next)
- [ ] Create automated testing infrastructure:
  - [ ] Set up differential testing system using `pytest-golden`
  - [ ] Add performance benchmark suite with `pytest-benchmark`
  - [ ] Create comparative benchmarks against other stub generators
  - [ ] Track memory usage patterns with `pytest-memray`
- [ ] Create pre-configured CI/CD pipelines:
  - [ ] Add GitHub Actions workflows:
    ```yaml
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
          - run: pip install -e .[test,dev]
          - run: pytest
    ```
  - [ ] Support pre-commit hooks with `.pre-commit-config.yaml`
  - [ ] Add release automation using `python-semantic-release`
  - [ ] Set up dependency updates with `dependabot`

### 1.5. Documentation & Usability (Medium Priority, Next)
- [ ] Enhance documentation system:
  - [ ] Generate API reference using `mkdocs-material`:
    ```yaml
    # mkdocs.yml
    site_name: Stub Generator
    theme:
      name: material
      features:
        - content.code.annotate
    plugins:
      - mkdocstrings
      - mkdocs-jupyter
    ```
  - [ ] Convert docstrings to Markdown using `docstring-to-markdown`
  - [ ] Create usage examples from tests using `pytest-examples`
  - [ ] Add architecture diagrams with `diagrams` package
- [ ] Develop interactive CLI mode:
  - [ ] Add guided configuration using `questionary`
  - [ ] Implement progress visualization with `rich.progress`
  - [ ] Add error recovery suggestions using fuzzy matching
  - [ ] Create interactive debugging mode with `ipdb`

### 1.6. Analysis & Visualization (Medium)
- [ ] Implement dependency graph visualizer:
  - [ ] Generate visual import maps using `graphviz`:
    ```python
    from graphviz import Digraph
    
    def create_import_graph(modules: list[str]) -> Digraph:
        """Create a visual representation of module dependencies."""
        dot = Digraph(comment='Module Dependencies')
        # Add nodes and edges
        return dot
    ```
  - [ ] Add interactive navigation with `networkx`
  - [ ] Support export formats (PNG, SVG, PDF)
  - [ ] Add impact analysis for changes
- [ ] Add custom importance scoring:
  - [ ] Support rule-based scoring with configurable weights
  - [ ] Add pattern matching using `fnmatch`
  - [ ] Enable weight customization via TOML config
  - [ ] Provide scoring templates for common use cases

## 2. Implementation Plan

### 2.1. Critical Priority (In Progress)
- [x] Add `__version__` to the package
- [x] Fix type compatibility issues
- [x] Fix boolean parameter warnings
- [x] Move `SmartStubGenerator` to `mypy_backend.py`
- [x] Move AST utilities to `utils/ast.py`
- [x] Move display functions to `utils/display.py`
- [x] Move docstring processor to `processors/docstring.py`
- [x] Move importance processor to `processors/importance.py`
- [x] Move type inference to `processors/type_inference.py`
- [ ] Move stub generation to `processors/stub_generation.py`
- [ ] Add integration tests for all components
- [ ] Fix remaining linter errors
- [ ] Complete legacy code migration

### 2.2. AST Backend Implementation (In Progress)
- [x] Port `SignatureExtractor` from `make_stubs_ast.py`:
  - [x] Add parent reference tracking for docstrings
  - [x] Implement literal truncation with configuration
  - [x] Add support for Python 3.12+ type parameters
  - [x] Preserve class-level assignments
- [ ] Add parallel processing support:
  - [ ] Use `ThreadPoolExecutor` for file processing:
    ```python
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    
    def process_files(files: list[Path]) -> None:
        with ThreadPoolExecutor() as executor:
            executor.map(process_single_file, files)
    ```
  - [ ] Add progress reporting with `rich.progress`
  - [ ] Implement error handling and logging with `loguru`
- [ ] Enhance docstring handling:
  - [ ] Add size-based truncation with configurable limits
  - [ ] Support format conversion between styles
  - [ ] Preserve important docstrings based on scoring

### 2.3. MyPy Backend Implementation (Completed)
- [x] Port smart features from `make_stubs_mypy.py`:
  - [x] Add docstring-based type inference using `docstring_parser`
  - [x] Implement property type inference with static analysis
  - [x] Support type comment extraction with `ast` module
- [x] Enhance MyPy integration:
  - [x] Add configuration mapping:
    ```python
    from dataclasses import dataclass
    from typing import Any
    
    @dataclass
    class MyPyConfig:
        """Configuration for MyPy backend."""
        python_version: tuple[int, int]
        platform: str
        custom_typeshed_dir: Path | None
        follow_imports: str = "silent"
    ```
  - [x] Support custom search paths with environment variables
  - [x] Handle special cases (dataclasses, protocols, etc.)
- [x] Add result post-processing:
  - [x] Clean up generated stubs using `black`
  - [x] Add missing imports with import sorting
  - [x] Format output consistently with configurable style

### 2.4. Testing and Documentation (High Priority, Next)
- [ ] Add test suite:
  - [ ] Unit tests for each component using `pytest`:
    ```python
    def test_stub_generation(tmp_path: Path) -> None:
        """Test basic stub generation functionality."""
        source = tmp_path / "example.py"
        source.write_text("def example() -> int: return 42")
        
        generator = StubGenerator()
        stub = generator.generate_stub(source)
        
        assert "def example() -> int" in stub
    ```
  - [ ] Integration tests with real-world examples
  - [ ] Performance tests with benchmarking
- [ ] Create documentation:
  - [ ] API reference with docstring examples
  - [ ] Usage examples with code snippets
  - [ ] Configuration guide with all options
- [ ] Add examples:
  - [ ] Basic usage patterns
  - [ ] Advanced features demonstration
  - [ ] Common patterns and solutions

### 2.5. Import Processing Enhancement (Medium Priority)
- [ ] Improve import analysis:
  - [ ] Add import graph visualization using `graphviz`
  - [ ] Detect unused imports with static analysis
  - [ ] Support `__all__` declarations with AST parsing
- [ ] Add import organization:
  - [ ] Group imports using `isort`:
    ```python
    from isort import Config, sort_code_string
    
    def organize_imports(code: str) -> str:
        """Organize imports in the generated stub."""
        config = Config(
            profile="black",
            src_paths=["src"],
            known_first_party=["mypackage"],
        )
        return sort_code_string(code, config)
    ```
  - [ ] Sort within groups by convention
  - [ ] Handle relative imports correctly
- [ ] Implement import optimization:
  - [ ] Remove duplicate imports automatically
  - [ ] Combine related imports intelligently
  - [ ] Minimize import statements where possible

### 2.6. Docstring Processing Enhancement (Medium Priority)
- [ ] Add format detection:
  - [ ] Identify docstring style using heuristics
  - [ ] Parse structured sections with regular expressions
  - [ ] Extract type information from all formats
- [ ] Implement format conversion:
  - [ ] Convert between styles preserving semantics
  - [ ] Preserve important information during conversion
  - [ ] Handle edge cases and special formats
- [ ] Add docstring optimization:
  - [ ] Remove redundant information automatically
  - [ ] Normalize formatting across project
  - [ ] Preserve type hints with validation

### 2.7. Importance Scoring Enhancement (Low Priority)
- [ ] Improve scoring algorithm:
  - [ ] Add usage analysis with static parsing
  - [ ] Consider inheritance relationships
  - [ ] Weight public vs private members
- [ ] Add pattern matching:
  - [ ] Support regex patterns for matching
  - [ ] Add keyword scoring with weights
  - [ ] Consider context in scoring
- [ ] Implement filtering:
  - [ ] Add threshold-based filtering options
  - [ ] Preserve dependencies in filtered output
  - [ ] Handle special cases with rules

### 2.8. CLI and Configuration (Low Priority)
- [ ] Create unified CLI:
  - [ ] Add command groups using `click`:
    ```python
    import click
    
    @click.group()
    def cli() -> None:
        """Stub generator command line interface."""
        pass
    
    @cli.command()
    @click.argument('source', type=click.Path(exists=True))
    @click.option('--output', '-o', help='Output directory')
    def generate(source: str, output: str | None) -> None:
        """Generate stubs for Python source files."""
        pass
    ```
  - [ ] Support configuration files with validation
  - [ ] Add validation with error messages
- [ ] Add configuration management:
  - [ ] Support TOML/YAML with schema validation
  - [ ] Add schema validation using Pydantic
  - [ ] Provide sensible defaults
- [ ] Implement logging:
  - [ ] Add levels and formatting with `loguru`
  - [ ] Support output redirection to files
  - [ ] Add progress indicators with `rich`

### 2.9. Performance Optimization (Low Priority)
- [ ] Add caching:
  - [ ] Cache parsed ASTs with LRU cache
  - [ ] Cache import analysis results
  - [ ] Cache docstring processing output
- [ ] Optimize processing:
  - [ ] Improve parallel execution with asyncio
  - [ ] Reduce memory usage with generators
  - [ ] Add incremental processing support
- [ ] Profile and optimize:
  - [ ] Identify bottlenecks with cProfile
  - [ ] Optimize critical paths with profiling
  - [ ] Add benchmarks for comparison

### 2.10. Integration Features (Low Priority)
- [ ] Add IDE integration:
  - [ ] Create VS Code extension with LSP
  - [ ] Add editor commands for common tasks
  - [ ] Support live preview of stubs
- [ ] Add CI/CD support:
  - [ ] Add GitHub Actions for automation
  - [ ] Support pre-commit hooks for quality
  - [ ] Add release workflow with versioning
- [ ] Add monitoring:
  - [ ] Track usage metrics with telemetry
  - [ ] Monitor performance with metrics
  - [ ] Report errors with proper context

# Future Improvements

- [ ] Add support for more docstring formats
- [ ] Improve type inference accuracy
- [ ] Add more configuration options
- [ ] Optimize performance
- [ ] Add more test cases
- [ ] Improve error handling
- [ ] Add documentation
- [ ] Add examples
- [ ] Add CI/CD pipeline