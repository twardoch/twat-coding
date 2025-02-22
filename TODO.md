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

- [!] **Fix Syntax Error in `__init__.py`**
  - *Task*: Correct the syntax error on line 428 to enable execution.

- [!] **Fix Critical Type Errors**
  - *Tasks*:
    1. In `docstring.py`, fix `key_info.annotation` and `value_info.annotation` errors.
    2. In `__init__.py`, complete `StubConfig` initialization.
    3. In `__init__.py`, align `StubConfig` and `StubGenConfig` types.

- [!] **Clean Up Unused Imports**
  - *Task*: Remove unused imports per Ruff reports.

- [!] **Fix Failing Tests**
  - *Tasks*:
    1. Update `test_package.py` to use `StubResult.stub_content`.
    2. Verify AST backend and docstring tests pass.

- [!] **Simplify Configuration**
  - *Tasks*:
    1. Reduce `StubGenConfig` to core settings in `core/config.py`.
    2. Adjust `SmartStubGenerator` accordingly.

- [!] **Integrate File Importance**
  - *Tasks*:
    1. Enhance `StubResult` with metadata.
    2. Update `SignatureExtractor` for importance-based decisions.
    3. Configure `ImportanceProcessor` to apply scores.
    4. Test importance functionality.

- [!] **Implement Basic CLI** *(Optional if time-constrained)*
  - *Tasks*:
    1. Add Click CLI in `__init__.py`.
    2. Test with a sample file.

- [!] **Improve Test Coverage to 50%**
  - *Tasks*:
    1. Test key modules (e.g., `imports.py`).
    2. Confirm coverage target met.

- [!] **Prepare for Release**
  - *Tasks*:
    1. Set version to `1.0.0`.
    2. Run cleanup scripts and push.
    3. Build and test package installation.

## 3. Future Tasks

- [ ] **Documentation Updates**
  - Revamp README.md with detailed usage and examples.
  - Add `examples/greet.py`.
  - Ensure `pystubnik/README.md` has basic usage.

- [ ] **Code Cleanup**
  - Refactor complex functions.
  - Evaluate `stub_generation.py`’s role.

- [ ] **Performance Optimization**
  - Optimize stub generation performance.

## 4. Notes

- Prioritize AST backend; CLI is optional for MVP if rushed.
- Update `pystubnik/README.md` with basic usage for MVP.
- Use `./cleanup.py status` for progress checks.
- Use `uv pip` for package management.

## 5. Next Actions

- Fix syntax error in `__init__.py`.
- Address type errors and test failures.
- Integrate file importance.
