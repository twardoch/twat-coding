### 0.1. Step 1: Understand the Current State

The `pystubnik` package generates "smart stubs" for Python code, an intermediate representation optimized for large language model (LLM) understanding. The current TODO.md reflects a mix of completed and pending tasks, but it's not aligned with the specific goal of eliminating the standalone scripts. The thinking trace provides a detailed analysis of `@make_stubs_ast.py` (AST-based stub generation) and `@make_stubs_mypy.py` (MyPy-based stub generation), suggesting their functionalities be integrated into `backends/ast_backend.py`, `backends/mypy_backend.py`, and supporting modules like `processors` and `config`.

### 0.2. Step 2: Identify Key Functionalities to Port

- **From `@make_stubs_ast.py`:**
  - AST parsing with `SignatureExtractor` for signature preservation.
  - Literal truncation (`truncate_literal`).
  - Docstring handling with size constraints.
  - Parallel processing with `ThreadPoolExecutor`.
- **From `@make_stubs_mypy.py`:**
  - MyPy stubgen integration via `SmartStubGenerator`.
  - Docstring processing for type inference.
  - Importance-based filtering.
  - Configuration mapping to MyPy options.

### 0.3. Step 4: Define the New TODO Structure

To achieve a functioning library ASAP:
1. **Configuration:** Update the config system to support all settings from the old scripts.
2. **Backends:** Port all functionality into `ast_backend.py` and `mypy_backend.py`.
3. **Processors:** Enhance processors to handle backend outputs.
4. **Entry Points:** Update `__init__.py` for immediate usability.
5. **Testing:** Add basic tests to verify functionality.
6. **Cleanup:** Deprecate and remove old scripts.

# TODO

This TODO.md is a detailed development specification to make `pystubnik` functional ASAP, eliminating `@make_stubs_ast.py` and `@make_stubs_mypy.py` by porting their functionality into the new structure. Tasks are ordered for rapid progress with early validation, including specific instructions for immediate implementation.

---

## 1. Code Quality Fixes (URGENT)

- [ ] **Fix Ruff Errors:**
  - [x] Fix deprecated typing imports (UP035) in ast_utils.py
  - [x] Remove unused imports (F401) in ast_utils.py
  - [x] Fix line length issues (E501) in ast_utils.py
  - [x] Address complex functions (C901) in ast_utils.py
  - [x] Fix remaining issues in __init__.py
  - [!] Fix remaining issues in other files

- [ ] **Fix Type Checking Errors:**
  - [x] Fix bytes/str type mismatches in ast_utils.py
  - [x] Fix AST.parent attribute errors in ast_utils.py
  - [x] Fix type system and docstring type errors in __init__.py
  - [x] Address object.process attribute error in __init__.py
  - [!] Fix tuple attribute errors in make_stubs_mypy.py

- [ ] **Improve Test Coverage:**
  - [!] Add basic unit tests for ast_utils.py
  - [!] Add basic unit tests for __init__.py
  - [ ] Add tests for other core functionality
  - [ ] Focus on critical paths in backends and processors

## 2. Update Configuration

- [!] **Extend `StubGenConfig` in `src/twat_coding/pystubnik/core/config.py`:**
  - Add AST fields: `max_sequence_length`, `max_string_length`, `max_docstring_length`, `max_file_size`, `truncation_marker`
  - Add MyPy fields: `include_docstrings`, `importance_patterns`, `max_docstring_length`, `infer_property_types`
  - Document and type all fields

- [ ] **Update `config.py` in `src/twat_coding/pystubnik/config.py`:**
  - Sync `StubConfig` with new `StubGenConfig` fields
  - Add Pydantic validation
  - Update `get_file_locations` for relative path logic

---

## 3. Port AST-based Stub Generation

- [x] **Move `truncate_literal` into `src/twat_coding/pystubnik/utils/ast_utils.py`:**
  - [x] Update to use `StubGenConfig.truncation`
  - [x] Split into smaller functions
  - [x] Add proper type hints
  - [x] Add error handling

- [!] **Move `SignatureExtractor` to `src/twat_coding/pystubnik/backends/ast_backend.py`:**
  - Use `StubGenConfig` for settings
  - Keep all methods intact

- [ ] **Enhance `ASTBackend.generate_stub`:**
  - Implement AST parsing, transformation, and writing as shown above
  - Use `ASTError` for exceptions

- [ ] **Add Smoke Test in `tests/test_ast_backend.py`:**
  - Test basic stub generation with a simple function

- [ ] **Add Parallel Processing to `ASTBackend.process_directory`:**
  - Implement with `asyncio` and `ThreadPoolExecutor`

---

## 4. Port MyPy-based Stub Generation

- [ ] **Move `SmartStubGenerator` to `src/twat_coding/pystubnik/backends/mypy_backend.py`:**
  - Rename to `MypyBackend`, inherit from `StubBackend`.

- [ ] **Implement `MypyBackend.generate_stub`:**
  - Use `stubgen.generate_stubs` with enhanced post-processing.

- [ ] **Port `process_docstring` and `calculate_importance`:**
  - Integrate into `MypyBackend`.

- [ ] **Add Smoke Test in `tests/test_mypy_backend.py`:**
  - Test basic stub generation with type hints.

---

## 5. Enhance Processors

- [ ] **Update `processors/docstring.py`, `processors/importance.py`, `processors/imports.py`:**
  - Align with new backend outputs as described.

---

## 6. Update Main Entry Points

- [ ] **Update `generate_stub` and `SmartStubGenerator.generate` in `src/twat_coding/pystubnik/__init__.py`:**
  - Integrate new backends and processors.

---

## 7. Comprehensive Testing

- [ ] **Expand Unit Tests:**
  - Full coverage for `ASTBackend` and `MypyBackend`.

- [ ] **Add Integration Tests in `tests/test_integration.py`:**
  - Test end-to-end stub generation.

---

## 8. Deprecate Old Scripts

- [ ] **Mark as Deprecated, Update Docs, Remove Scripts:**
  - Final cleanup steps.

---

