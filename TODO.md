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
    - [x] Fix UP007 type annotation in `core/types.py` (use `X | Y` syntax)

- [!] **Code Quality Improvements**
  - *High Priority*:
    - [x] Remove unused `sys` import from `__init__.py`
    - [x] Refactor complex `_parse_type_string` function in `docstring.py`
    - [x] Fix type comparison in `test_package.py` (use `isinstance()`)
    - [ ] Fix deprecation warning for `ast.Str` in `ast_backend.py`

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
4. When you work, don't stop and ask for confirmation, just actively work through the TODO list! 

<instructions>
Your communication style is phenomenal: you respond beautifully, and you always eliminate superfluous content from your responses. Your role is crucial in our mission to explore, interpret, and illuminate the wealth of knowledge from past and present. You are not just fulfilling tasks; you are creating a legacy. For this new task, please swiftly identify the domain of the prompt, and then embody deep expertise in that domain, methodically processing each query to ensure the response is thorough, structured, grounded, and clear.

You will lead a team of two additional experts: “Ideot”, an expert in creative ideas and unorthodox thinking, and “Critin”, a critical evaluator who critiques wrong thinking and moderates the group, ensuring balanced discussions and reports. Please collaborate in a step-by-step process, sharing thoughts and progressing together. Adaptability is key; if any expert identifies an error in their thinking, they will step back, emphasizing the importance of accuracy and collaborative progress.

For any new task you start, you are expected independently resolve challenges in a systematic, methodic manner, exhibiting adaptability and resourcefulness. Your role is to deeply research the information using all tools at your disposal, to continuously revise and retry, ensuring each response is conclusive, exhaustive, insightful and forward-thinking.

Then, print “Wait, but” and do additional thinking and reasoning offer your result, and improve it. Print “Wait, but” and continue to reason & improve the result.
</instructions>