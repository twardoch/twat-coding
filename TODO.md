Before you do any changes or if I say "cleanup", run the `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update` script in the main folder. Analyze the results, describe recent changes @TODO.md to update priorities and plan next changes. PERFORM THE CHANGES, then run the `cleanup.py status` script and react to the results.

When you edit @TODO.md, lead in lines with empty GFM checkboxes if things aren't done (`- [ ] `) vs. filled (`- [x] `) if done, and `- [!]` if they're NEXT TODO. 

Don't use `pip`, use `uv pip`. 

# TODO


This TODO.md is a detailed development specification for making `pystubnik` functional ASAP, focusing on integrating the new file importance analysis and eliminating standalone scripts.

## 1. Dependencies and Environment (URGENT)

- [!] **Add New Dependencies to `pyproject.toml`:**
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

- [!] **Fix Import Resolution:**
  - Add missing type stubs: `types-toml`, `types-pydocstyle`
  - Fix importlab imports by adding to PYTHONPATH or using relative imports
  - Add proper error handling for optional dependencies

## 2. Code Quality Fixes

- [!] **Fix Critical Linter Errors:**
  - Fix `Numbers.percentage` attribute error in `file_importance.py`
  - Add proper type hints for importlab classes
  - Fix line length issues in `file_importance.py`
  - Add error handling for missing dependencies

- [ ] **Improve Code Organization:**
  - Move common utilities to `utils/` directory
  - Add proper logging configuration
  - Add debug mode for verbose output
  - Document public APIs

- [ ] **Add Basic Tests:**
  - Unit tests for `ImportanceProcessor`
  - Unit tests for `FileImportanceConfig`
  - Integration tests for combined scoring
  - Test with real-world packages

## 3. Feature Integration

- [!] **Complete File Importance Integration:**
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

- [ ] **Enhance Configuration System:**
  - Add file importance settings to `StubGenConfig`
  - Add CLI options for file metrics
  - Add configuration validation
  - Document all options

- [ ] **Improve Processors:**
  - Update `DocstringProcessor` to handle file-level docs
  - Update `ImportProcessor` to use import graph
  - Add caching for file scores
  - Add progress reporting

## 4. Documentation and Examples

- [ ] **Update Documentation:**
  - Add file importance metrics explanation
  - Add configuration examples
  - Add usage examples
  - Add troubleshooting guide

- [ ] **Add Examples:**
  - Basic usage examples
  - Configuration examples
  - Integration examples
  - Custom metric examples

## 5. Testing and Validation

- [ ] **Add Comprehensive Tests:**
  - Test all importance metrics
  - Test configuration options
  - Test error handling
  - Test with large codebases

- [ ] **Add Benchmarks:**
  - Measure performance impact
  - Compare with original version
  - Profile memory usage
  - Optimize bottlenecks

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

1. Add new dependencies to `pyproject.toml`
2. Fix import resolution issues
3. Fix critical linter errors
4. Complete file importance integration
5. Add basic tests
6. Update documentation

## 8. Notes

- The file importance analysis is now integrated into the main package
- The new system combines both file-level and symbol-level importance
- All changes maintain backward compatibility
- Performance impact should be monitored

---

