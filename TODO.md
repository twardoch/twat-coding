---
this_file: TODO.md
---

# TODO

## 1. Immediate Priorities

- [!] **Improve Test Coverage (Current: 40%)**
  - *Critical Modules with 0% Coverage*:
    - [ ] Write tests for `stub_generation.py`
    - [ ] Write tests for `type_inference.py`
    - [ ] Write tests for `read_imports.py`
    - [ ] Write tests for `backends/base.py`
    - [ ] Write tests for `twat_coding.py`

- [!] **Enhance Type Inference**
  - *Tasks*:
    - [ ] Improve type inference from docstrings
    - [ ] Add support for more complex type annotations
    - [ ] Handle generic types and type variables
    - [ ] Fix UP007 type annotation in `core/types.py` (use `X | Y` syntax)

- [!] **Code Quality Improvements**
  - *High Priority*:
    - [ ] Remove unused `sys` import from `__init__.py`
    - [ ] Refactor complex `_parse_type_string` function in `docstring.py`
    - [ ] Fix type comparison in `test_package.py` (use `isinstance()`)

## 2. Future Tasks

- [ ] **Documentation Updates**
  - Update README.md with detailed usage and examples
  - Add `examples/greet.py`
  - Ensure `pystubnik/README.md` has basic usage
  - Add docstrings to untested modules

- [ ] **Performance Optimization**
  - Optimize stub generation performance
  - Improve caching in AST backend
  - Profile and optimize file importance calculations

## 3. Notes

- Use `uv pip` for package management
- Ignore minor linting issues (line length) for now
- Run `./cleanup.py update | cat` after changes to verify fixes

## 4. Development Guidelines

1. Before making changes:
   - Run: `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update | cat`
   - Analyze results and update priorities
2. After changes:
   - Run: `./cleanup.py update | cat`
   - Verify fixes and update TODO.md
3. When editing TODO.md:
   - Use `- [ ]` for pending tasks
   - Use `- [x]` for completed tasks
   - Use `- [!]` for next priority tasks
