---
this_file: TODO.md
---

# TODO

## 1. Intro

- Focus on fixing type errors first as they affect core functionality
- Then improve test coverage to ensure stability
- Complete file importance integration to enable smart stub generation
- Use `uv pip` instead of `pip` for package management
- Ignore minor linting issues (line length) for now
- Before you do any changes or if I say "cleanup", run the `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update | cat` script in the main folder. Analyze the results, describe recent changes @TODO.md to update priorities and plan next changes. PERFORM THE CHANGES, then run the `./cleanup.py update | cat` script and react to the results.
- When you edit @TODO.md, lead in lines with empty GFM checkboxes if things aren't done (`- [ ]`) vs. filled (`- [x]`) if done, and `- [!]` if they're NEXT TODO.

## 2. Immediate Priorities

- [!] **Fix Critical Type Errors**
  - *Tasks*:
    1. Fix remaining type errors in `docstring.py` for `key_info.annotation` and `value_info.annotation`.
    2. Fix type errors in `ast_backend.py` for imports and assignments.
    3. Fix type error in `__init__.py` for `MypyBackend` argument type.

- [!] **Improve Test Coverage**
  - *Tasks*:
    1. Add tests for configuration conversion.
    2. Add tests for backend type compatibility.
    3. Add tests for docstring type extraction.

- [ ] **Integrate File Importance**
  - *Tasks*:
    1. Enhance `StubResult` with metadata.
    2. Update `SignatureExtractor` for importance-based decisions.
    3. Configure `ImportanceProcessor` to apply scores.

## 3. Future Tasks

- [ ] **Documentation Updates**
  - Update README.md with detailed usage and examples.
  - Add `examples/greet.py`.
  - Ensure `pystubnik/README.md` has basic usage.

- [ ] **Code Cleanup**
  - Refactor complex functions.
  - Evaluate `stub_generation.py`'s role.

- [ ] **Performance Optimization**
  - Optimize stub generation performance.
  - Improve caching in AST backend.

## 4. Completed Tasks

- [x] **Fix Syntax Error in `__init__.py`**
  - Fixed syntax error on line 428.

- [x] **Clean Up Unused Imports**
  - Removed unused imports from `backends/__init__.py`:
    - `collections.abc.Coroutine`
    - `typing.Any`
    - `..core.types.StubResult`

- [x] **Fix Failing Tests**
  - Updated `test_package.py` to use `StubResult.stub_content`.
  - Fixed AST backend and docstring tests.

- [x] **Fix Backend Type Compatibility**
  - Fixed `MypyBackend` signature compatibility with `StubBackend`.
  - Ensured consistent return types across all backend implementations.

- [x] **Fix Configuration Structure**
  - Fixed `StubGenConfig` initialization in `core/config.py`.
  - Fixed `StubConfig` attribute access in `core/conversion.py`.
  - Fixed circular import between `__init__.py` and `ast_backend.py`.

## 5. Next Actions

1. Fix remaining type errors in `docstring.py`
2. Fix type errors in `ast_backend.py`
3. Fix type error in `__init__.py` for `MypyBackend`

## 6. Notes

- Use `uv pip` for package management
- Ignore minor linting issues (line length) for now
- Run `./cleanup.py update | cat` after changes to verify fixes
