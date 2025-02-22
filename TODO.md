Before you do any changes or if I say "cleanup", run the `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update | cat` script in the main folder. Analyze the results, describe recent changes @TODO.md to update priorities and plan next changes. PERFORM THE CHANGES, then run the `./cleanup.py update | cat` script and react to the results.

When you edit @TODO.md, lead in lines with empty GFM checkboxes if things aren't done (`- [ ] `) vs. filled (`- [x] `) if done, and `- [!]` if they're NEXT TODO. 

Don't use `pip`, use `uv pip`. Ignore minor problems like "line too long", FOCUS ON MAJOR PROBLEMS! 

# TODO

This TODO.md is a detailed development specification for making `pystubnik` functional ASAP, focusing on integrating the new file importance analysis and eliminating standalone scripts.

## 1. Dependencies and Environment (URGENT)

- [x] **Add New Dependencies to `pyproject.toml`:**
  ```toml
  [project]
  dependencies = [
      # ... existing deps ...
      "networkx>=3.2.1",     # For import graph analysis
      "radon>=6.0.1",       # For code complexity metrics
      "coverage>=7.4.1",    # For test coverage analysis
      "pydocstyle>=6.3.0", # For docstring quality checks
      "importlab>=0.8",    # For import graph building
      "toml>=0.10.2",      # For pyproject.toml parsing
  ]
  ```

- [x] **Fix Import Resolution:**
  - Added missing type stubs: `types-toml`, replaced `types-pydocstyle` with `mypy-extensions`
  - Simplified import graph building to not rely on importlab
  - Added proper error handling for optional dependencies

## 2. Code Quality Fixes

- [x] **Fix Critical Linter Errors:**
  - Fixed `Numbers.percentage` attribute error in `file_importance.py`
  - Added proper type hints for importlab classes
  - Fixed line length issues in `file_importance.py`
  - Added error handling for missing dependencies
  - Fixed type errors in centrality calculation

- [x] **Fix Remaining Linter Errors:**
  - Removed unused imports in `backends/__init__.py` and `processors/__init__.py`
  - Replaced deprecated type hints with modern syntax:
    - Replaced `typing.Dict` with `dict`
    - Replaced `typing.Type` with `type`
    - Used `X | Y` instead of `Union[X, Y]`
  - Fixed line length issues in:
    - `config.py`
    - `core/utils.py`
    - `types/docstring.py`
  - Refactored complex functions:
    - `truncate_literal` in `make_stubs_ast.py`
    - `calculate_importance` in `importance.py`
    - `extract_types` in `types/docstring.py`

- [!] **Fix Type Checking Errors:**
  The following type errors need to be fixed:
  1. In `type_system.py`:
     ```python
     # Fix incompatible type in issubclass call by:
     # 1. Import the correct type from typing._TypeAliasForm
     # 2. Use isinstance() instead of issubclass() for type checking
     # 3. Add proper type guards
     ```
  2. In `make_stubs_ast.py`:
     ```python
     # Fix bytes/str type mismatch by:
     # 1. Add explicit encoding when converting between bytes and str
     # 2. Use proper type annotations for binary data
     # 3. Add error handling for encoding/decoding failures
     ```
  3. In `make_stubs_ast.py`:
     ```python
     # Fix AST parent attribute error by:
     # 1. Create a custom AST node class that includes parent attribute
     # 2. Use ast.fix_missing_locations after modifying AST
     # 3. Add proper type hints for the parent attribute
     ```
  4. In `docstring.py`:
     ```python
     # Fix type annotation by:
     # 1. Update type hints to use modern Python syntax
     # 2. Add proper type guards for optional attributes
     # 3. Use TypeVar for generic type parameters
     ```

- [!] **Improve Code Organization:**
  Create a new `utils/` directory with the following structure and functionality:
  ```
  utils/
  ├── graph_utils.py       # Import graph building and analysis
  │   ├── build_import_graph()  # Build graph from Python files
  │   ├── analyze_centrality()  # Calculate node importance
  │   └── resolve_imports()     # Handle import resolution
  │
  ├── metrics.py          # Code complexity and quality metrics
  │   ├── calculate_complexity()  # Using radon
  │   ├── check_coverage()       # Using coverage.py
  │   └── evaluate_docs()        # Using pydocstyle
  │
  ├── config.py          # Configuration handling
  │   ├── load_config()   # Load from pyproject.toml
  │   ├── validate()      # Validate settings
  │   └── merge()         # Merge with defaults
  │
  └── logging.py         # Centralized logging
      ├── setup_logging()  # Configure loguru
      ├── log_error()     # Error handling
      └── log_metrics()   # Metrics reporting
  ```

  Move the following functions from their current locations:
  1. From `file_importance.py`:
     - `calculate_file_scores()` → `metrics.py`
     - `build_import_graph()` → `graph_utils.py`
  2. From `importance.py`:
     - `calculate_importance()` → `metrics.py`
  3. From `core/utils.py`:
     - `setup_logging()` → `logging.py`
     - `normalize_path()` → `config.py`

- [!] **Add Basic Tests:**
  Create the following test files with specific test cases:
  ```
  tests/
  ├── processors/
  │   └── test_file_importance.py
  │       ├── test_graph_building()  # Test import graph construction
  │       ├── test_metrics()         # Test each metric calculation
  │       ├── test_config()          # Test config validation
  │       └── test_error_handling()  # Test dependency errors
  │
  ├── test_utils/
  │   ├── test_files/               # Sample Python files for testing
  │   │   ├── simple_module.py
  │   │   ├── complex_module.py
  │   │   └── error_module.py
  │   └── fixtures.py               # Common test fixtures
  │
  └── conftest.py                   # pytest configuration
  ```

  Add performance benchmarks:
  ```python
  # benchmarks/test_performance.py
  def test_large_codebase():
      """Test processing speed on large codebase."""
      # Process >1000 Python files
      # Measure memory usage
      # Track processing time
  ```

## 3. Feature Integration

- [x] **Complete File Importance Integration:**
  ```python
  # In ImportanceProcessor.process():
  def process(self, stub_result: StubResult) -> StubResult:
      # Calculate file scores
      package_dir = str(stub_result.source_path.parent)
      self._file_scores = calculate_file_scores(package_dir, self.config.file_importance)
      
      # Process AST
      tree = ast.parse(stub_result.stub_content)
      for node in ast.walk(tree):
          if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
              score = self.calculate_importance(
                  name=node.name,
                  docstring=ast.get_docstring(node),
                  is_public=not node.name.startswith('_'),
                  is_special=node.name.startswith('__'),
                  extra_info={"file_path": stub_result.source_path}
              )
              # TODO: Store score in node.importance_score
              
      return stub_result
  ```

- [!] **Enhance Configuration System:**
  Create a comprehensive configuration system with the following components:

  1. `FileImportanceConfig` class:
  ```python
  @dataclass
  class FileImportanceConfig:
      exclude_dirs: list[str]
      centrality_measure: Literal["pagerank", "betweenness", "eigenvector"]
      coverage_data_path: Path | None
      weights: dict[str, float]
      min_coverage_threshold: float
      max_complexity_threshold: float
      doc_quality_checks: list[str]
      cache_results: bool
  ```

  2. Configuration validation:
  ```python
  def validate_config(config: FileImportanceConfig) -> None:
      """Validate configuration values."""
      # Check thresholds are between 0 and 1
      # Verify centrality measure is valid
      # Ensure weights sum to 1.0
      # Validate paths exist
  ```

  3. CLI integration:
  ```python
  @click.command()
  @click.option("--config", type=click.Path(), help="Config file path")
  @click.option("--exclude", multiple=True, help="Dirs to exclude")
  @click.option("--measure", type=click.Choice(["pagerank", "betweenness"]))
  def main(config: str, exclude: list[str], measure: str) -> None:
      """Process files with importance analysis."""
      # Load config from file
      # Override with CLI options
      # Run processing
  ```

  4. Documentation:
  ```markdown
  # Configuration Guide
  
  ## 4. File Importance Settings
  - exclude_dirs: List of directories to exclude
  - centrality_measure: Graph centrality algorithm
  - weights: Metric importance weights
  
  ## 5. Examples
  ```toml
  [importance]
  exclude_dirs = ["tests", "examples"]
  centrality_measure = "pagerank"
  weights = { complexity = 0.3, coverage = 0.3, docs = 0.4 }
  ```
  ```

- [!] **Improve Processors:**
  Enhance the processor system with the following improvements:

  1. Update `DocstringProcessor`:
  ```python
  class DocstringProcessor:
      """Process docstrings with quality metrics."""
      
      def process_file_docstring(self) -> float:
          """Handle file-level docstrings."""
          
      def use_importance_score(self) -> None:
          """Incorporate file importance."""
          
      def check_quality(self) -> float:
          """Check docstring quality."""
  ```

  2. Update `ImportProcessor`:
  ```python
  class ImportProcessor:
      """Handle imports with caching."""
      
      def process_imports(self) -> None:
          """Process with cached graph."""
          
      def handle_circular(self) -> None:
          """Handle circular imports."""
          
      def support_namespace(self) -> None:
          """Support namespace packages."""
  ```

  3. Add progress reporting:
  ```python
  from rich.progress import Progress
  
  def process_files() -> None:
      """Process files with progress bar."""
      with Progress() as progress:
          task = progress.add_task("Processing", total=len(files))
          for file in files:
              process_file(file)
              progress.update(task, advance=1)
  ```

  4. Add caching system:
  ```python
  class ImportanceCache:
      """Cache file importance scores."""
      
      def __init__(self, cache_dir: Path) -> None:
          self.cache_dir = cache_dir
          
      def get_score(self, file_path: Path) -> float:
          """Get cached score."""
          
      def set_score(self, file_path: Path, score: float) -> None:
          """Cache new score."""
  ```

## 6. Documentation and Examples

- [ ] **Update Documentation:**
  Create comprehensive documentation covering:
  1. Architecture overview
  2. Metric explanations
  3. Configuration guide
  4. Troubleshooting guide
  5. Performance tips
  6. Migration guide

- [ ] **Add Examples:**
  Create example code for:
  1. Basic usage
  2. Custom metrics
  3. Integration patterns
  4. Configuration examples
  5. Performance optimization

## 7. Testing and Validation

- [ ] **Add Comprehensive Tests:**
  Add tests for:
  1. Unit tests (current coverage is only 1%)
  2. Integration tests
  3. Performance tests
  4. Edge case tests
  5. Regression tests

- [ ] **Add Benchmarks:**
  Create benchmarks for:
  1. Processing time
  2. Memory usage
  3. Baseline comparison
  4. Bottleneck profiling
  5. Optimization documentation

## 8. Final Steps

- [ ] **Clean Up Old Code:**
  1. Remove standalone scripts
  2. Update imports
  3. Remove deprecated code
  4. Update documentation

- [ ] **Release Preparation:**
  1. Update version numbers
  2. Update changelog
  3. Update README
  4. Prepare release notes

## 9. Next Actions

1. [x] Add new dependencies to `pyproject.toml`
2. [x] Fix import resolution issues
3. [x] Fix critical linter errors
4. [x] Fix remaining linter errors
5. [!] Fix type checking errors
6. [!] Improve code organization
7. [!] Add basic tests
8. [!] Enhance configuration system

## 10. Notes

- The file importance analysis is now integrated into the main package
- The new system combines both file-level and symbol-level importance
- All changes maintain backward compatibility
- Performance impact should be monitored
- Optional dependencies are now properly handled with graceful fallbacks
- Current test coverage is only 1%, needs immediate attention
- Several complex functions need refactoring
- Type system needs modernization (using newer Python type hints)

---

