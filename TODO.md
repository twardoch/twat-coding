Before you do any changes or if I say "cleanup", run the `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update` script in the main folder. Analyze the results, describe recent changes @TODO.md to update priorities and plan next changes. PERFORM THE CHANGES, then run the `cleanup.py status` script and react to the results.

When you edit @TODO.md, lead in lines with empty GFM checkboxes if things aren't done (`- [ ] `) vs. filled (`- [x] `) if done, and `- [!]` if they're NEXT TODO. 

Don't use `pip`, use `uv pip`. 

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

- [!] **Fix Remaining Linter Errors:**
  - Remove unused imports in `backends/__init__.py` and `processors/__init__.py`
  - Replace deprecated type hints with modern syntax:
    - Replace `typing.Dict` with `dict`
    - Replace `typing.Type` with `type`
    - Use `X | Y` instead of `Union[X, Y]`
  - Fix line length issues in:
    - `config.py`
    - `core/utils.py`
    - `types/docstring.py`
  - Refactor complex functions:
    - `truncate_literal` in `make_stubs_ast.py`
    - `calculate_importance` in `importance.py`
    - `extract_types` in `types/docstring.py`

- [!] **Fix Type Checking Errors:**
  - Fix incompatible type in `issubclass` call in `type_system.py`
  - Fix bytes/str type mismatch in `make_stubs_ast.py`
  - Fix AST parent attribute error in `make_stubs_ast.py`
  - Fix type annotation in `docstring.py`

- [!] **Improve Code Organization:**
  - Create `utils/` directory with:
    - `graph_utils.py`: Import graph building and analysis
    - `metrics.py`: Code complexity, coverage, and doc quality metrics
    - `config.py`: Configuration handling and validation
    - `logging.py`: Centralized logging setup
  - Move common functions from `file_importance.py` to appropriate utils
  - Add proper error handling and logging throughout
  - Document all utility functions with type hints and docstrings

- [!] **Add Basic Tests:**
  - Create `tests/processors/test_file_importance.py` with:
    - Test cases for graph building with mock files
    - Test cases for each metric calculation
    - Test cases for config loading and validation
    - Test cases for error handling of missing dependencies
  - Add test fixtures for sample Python files
  - Add test coverage reporting (current coverage is only 1%)
  - Add performance benchmarks for large codebases

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
  - Create `FileImportanceConfig` class with:
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
  - Add validation for all config fields
  - Add CLI options for all config settings
  - Add config file support (JSON/TOML)
  - Add config documentation and examples

- [!] **Improve Processors:**
  - Update `DocstringProcessor` to:
    - Handle file-level docstrings
    - Use file importance scores
    - Add quality metrics
  - Update `ImportProcessor` to:
    - Use cached import graph
    - Handle circular imports
    - Support namespace packages
  - Add progress reporting with rich
  - Add caching system for file scores

## 4. Documentation and Examples

- [ ] **Update Documentation:**
  - Add architecture overview
  - Add metric explanations
  - Add configuration guide
  - Add troubleshooting guide
  - Add performance tips
  - Add migration guide

- [ ] **Add Examples:**
  - Basic usage examples
  - Custom metric examples
  - Integration examples
  - Configuration examples
  - Performance optimization examples

## 5. Testing and Validation

- [ ] **Add Comprehensive Tests:**
  - Unit tests for all components (current coverage is only 1%)
  - Integration tests
  - Performance tests
  - Edge case tests
  - Regression tests

- [ ] **Add Benchmarks:**
  - Measure processing time
  - Measure memory usage
  - Compare with baseline
  - Profile bottlenecks
  - Document optimizations

## 6. Final Steps

- [ ] **Clean Up Old Code:**
  - Remove standalone scripts
  - Update imports
  - Remove deprecated code
  - Update documentation

- [ ] **Release Preparation:**
  - Update version numbers
  - Update changelog
  - Update README
  - Prepare release notes

## 7. Next Actions

1. [x] Add new dependencies to `pyproject.toml`
2. [x] Fix import resolution issues
3. [x] Fix critical linter errors
4. [!] Fix remaining linter errors
5. [!] Fix type checking errors
6. [!] Improve code organization
7. [!] Add basic tests
8. [!] Enhance configuration system

## 8. Notes

- The file importance analysis is now integrated into the main package
- The new system combines both file-level and symbol-level importance
- All changes maintain backward compatibility
- Performance impact should be monitored
- Optional dependencies are now properly handled with graceful fallbacks
- Current test coverage is only 1%, needs immediate attention
- Several complex functions need refactoring
- Type system needs modernization (using newer Python type hints)

---

