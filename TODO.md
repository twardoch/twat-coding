# TODO

- [x] Analyze [make_stubs_ast.py](./src/twat_coding/pystubnik/make_stubs_ast.py)
- [x] Analyze [make_stubs_mypy.py](./src/twat_coding/pystubnik/make_stubs_mypy.py)
- [x] Analyze [stubgen.py](.venv/lib/python3.12/site-packages/mypy/stubgen.py) from the `mypy` package
- [x] Figure out how we can bring together the code with also [read_imports.py](./src/twat_coding/pystubnik/read_imports.py) and ported portions of [](./src/twat_coding/pystubnik/pypacky2.sh) to create a sub-package within the `twat-coding` package called `pystubnik`
- [x] Flesh out the details of the `pystubnik` package and make a detailed description in [README.md](./src/twat_coding/pystubnik/README.md)
- [x] Make a short description in the main [README.md](./README.md) file
- [x] Make a TLDR alongside a short structure description in [README.md](./cursor/rules/0project.mdc)
- [x] Create initial package structure with core components:
  - [x] Backend interface and registry
  - [x] Processor interface and registry
  - [x] Core types and configuration
  - [x] Utility functions
- [x] Set up processor implementations:
  - [x] Import analysis and organization
  - [x] Docstring processing and formatting
  - [x] Importance scoring and filtering

## 1. Integration Plan

### 1.1. Critical Priority (Immediate)
- [ ] Fix failing tests and linter errors:
  - [x] Add `__version__` to package
  - [ ] Fix type annotation issues:
    - [x] Fix "StubConfig" vs "StubGenConfig" confusion
    - [ ] Fix type compatibility in RuntimeConfig:
      - [ ] Handle optional python_version
      - [ ] Handle optional interpreter
    - [ ] Fix return type in MyPy backend
    - [ ] Fix missing return type annotations
  - [ ] Address linter warnings:
    - [ ] Fix boolean parameter warnings
    - [ ] Fix naming convention issues
    - [ ] Fix complexity warnings
  - [ ] Clean up code style issues:
    - [ ] Fix deprecated typing imports
    - [ ] Fix unused imports
    - [ ] Fix print statements
  - [ ] Fix dependency issues:
    - [ ] Add missing loguru dependency
    - [ ] Fix import resolution issues

### 1.2. AST Backend Implementation (High Priority)
- [x] Port `SignatureExtractor` from `make_stubs_ast.py`:
  - [x] Add parent reference tracking for docstrings
  - [x] Implement literal truncation with configuration
  - [x] Add support for Python 3.12+ type parameters
  - [x] Preserve class-level assignments
- [ ] Add parallel processing support:
  - [ ] Use `ThreadPoolExecutor` for file processing
  - [ ] Add progress reporting with `rich`
  - [ ] Implement error handling and logging
- [ ] Enhance docstring handling:
  - [ ] Add size-based truncation
  - [ ] Support format conversion
  - [ ] Preserve important docstrings

### 1.3. MyPy Backend Implementation (High Priority)
- [ ] Port smart features from `make_stubs_mypy.py`:
  - [ ] Add docstring-based type inference
  - [ ] Implement property type inference
  - [ ] Support type comment extraction
- [ ] Enhance MyPy integration:
  - [ ] Add configuration mapping
  - [ ] Support custom search paths
  - [ ] Handle special cases (dataclasses, etc.)
- [ ] Add result post-processing:
  - [ ] Clean up generated stubs
  - [ ] Add missing imports
  - [ ] Format output consistently

### 1.4. Testing and Documentation (High Priority, was 1.7)
- [ ] Add test suite:
  - [ ] Unit tests for each component
  - [ ] Integration tests
  - [ ] Performance tests
- [ ] Create documentation:
  - [ ] API reference
  - [ ] Usage examples
  - [ ] Configuration guide
- [ ] Add examples:
  - [ ] Basic usage
  - [ ] Advanced features
  - [ ] Common patterns

### 1.5. Import Processing Enhancement (Medium Priority, was 1.3)
- [ ] Improve import analysis:
  - [ ] Add import graph visualization
  - [ ] Detect unused imports
  - [ ] Support `__all__` declarations
- [ ] Add import organization:
  - [ ] Group by type (stdlib, third-party, local)
  - [ ] Sort within groups
  - [ ] Handle relative imports
- [ ] Implement import optimization:
  - [ ] Remove duplicate imports
  - [ ] Combine related imports
  - [ ] Minimize import statements

### 1.6. Docstring Processing Enhancement (Medium Priority, was 1.4)
- [ ] Add format detection:
  - [ ] Identify docstring style (Google, NumPy, reST)
  - [ ] Parse structured sections
  - [ ] Extract type information
- [ ] Implement format conversion:
  - [ ] Convert between styles
  - [ ] Preserve important information
  - [ ] Handle edge cases
- [ ] Add docstring optimization:
  - [ ] Remove redundant information
  - [ ] Normalize formatting
  - [ ] Preserve type hints

### 1.7. Importance Scoring Enhancement (Medium Priority, was 1.5)
- [ ] Improve scoring algorithm:
  - [ ] Add usage analysis
  - [ ] Consider inheritance
  - [ ] Weight public vs private
- [ ] Add pattern matching:
  - [ ] Support regex patterns
  - [ ] Add keyword scoring
  - [ ] Consider context
- [ ] Implement filtering:
  - [ ] Add threshold-based filtering
  - [ ] Preserve dependencies
  - [ ] Handle special cases

### 1.8. CLI and Configuration (Low Priority, was 1.6)
- [ ] Create unified CLI:
  - [ ] Add command groups
  - [ ] Support configuration files
  - [ ] Add validation
- [ ] Add configuration management:
  - [ ] Support TOML/YAML
  - [ ] Add schema validation
  - [ ] Provide defaults
- [ ] Implement logging:
  - [ ] Add levels and formatting
  - [ ] Support output redirection
  - [ ] Add progress indicators

### 1.9. Performance Optimization (Low Priority, was 1.8)
- [ ] Add caching:
  - [ ] Cache parsed ASTs
  - [ ] Cache import analysis
  - [ ] Cache docstring processing
- [ ] Optimize processing:
  - [ ] Improve parallel execution
  - [ ] Reduce memory usage
  - [ ] Add incremental processing
- [ ] Profile and optimize:
  - [ ] Identify bottlenecks
  - [ ] Optimize critical paths
  - [ ] Add benchmarks

### 1.10. Integration Features (Low Priority, was 1.9)
- [ ] Add IDE integration:
  - [ ] Create VS Code extension
  - [ ] Add editor commands
  - [ ] Support live preview
- [ ] Add CI/CD support:
  - [ ] Add GitHub Actions
  - [ ] Support pre-commit hooks
  - [ ] Add release workflow
- [ ] Add monitoring:
  - [ ] Track usage metrics
  - [ ] Monitor performance
  - [ ] Report errors