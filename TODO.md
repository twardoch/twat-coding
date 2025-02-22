---
this_file: TODO.md
---

# TODO

## 1. Immediate Priorities

- [!] **Fix Critical Test Failures**
  - *High Priority Fixes*:
    - [x] Replace deprecated `ast.Str` usage with `ast.Constant` (affects multiple tests)
    - [x] Fix private class exclusion in `stub_generation.py`
    - [x] Fix import sorting order to match test expectations
    - [x] Fix assignment formatting to match test expectations
    - [x] Fix constant handling in stub generation
    - [!] Fix remaining test failures in `test_stub_generation_config` and `test_stub_generation_imports`
      - [ ] Debug private class exclusion logic
      - [ ] Fix import sorting order for stdlib imports

- [!] **Refactor Stub Generation**
  - *Code Quality Improvements*:
    - [!] Split `generate_stub` into smaller functions (current complexity: 25)
      - [ ] Create `_process_header` for header generation
      - [ ] Create `_process_imports` for import collection and sorting
      - [ ] Create `_process_definitions` for class/function/assignment handling
      - [ ] Create `_format_stub` for final formatting and cleanup
    - [ ] Refactor `_process_class_to_lines` (current complexity: 13)
      - [ ] Create `_extract_docstring` helper
      - [ ] Create `_process_class_methods` helper
      - [ ] Create `_process_class_attributes` helper
      - [ ] Create `_format_class_definition` helper
    - [ ] Fix line length violations in `stub_generation.py`
      - [ ] Break long import strings into multiple lines
      - [ ] Split long function signatures
      - [ ] Wrap long docstrings

## 2. Near-term Tasks

- [ ] **Improve Test Coverage (Current: 46%)**
  - *Critical Modules with 0% Coverage*:
    - [ ] Write tests for `type_inference.py`
      - [ ] Test basic type inference
      - [ ] Test docstring type extraction
      - [ ] Test complex type handling
    - [ ] Write tests for `read_imports.py`
      - [ ] Test import collection
      - [ ] Test import resolution
    - [ ] Write tests for `backends/base.py`
      - [ ] Test backend interface
      - [ ] Test common functionality
    - [ ] Write tests for `twat_coding.py`
      - [ ] Test CLI functionality
      - [ ] Test configuration handling

## 3. Future Tasks

- [ ] **Enhance Type Inference**
  - *Tasks*:
    - [ ] Improve type inference from docstrings
      - [ ] Add support for more docstring formats
      - [ ] Improve confidence scoring
    - [ ] Add support for more complex type annotations
      - [ ] Handle nested generics
      - [ ] Support type variables
    - [ ] Handle generic types and type variables
      - [ ] Add TypeVar support
      - [ ] Add Callable support

- [ ] **Documentation Updates**
  - Update README.md with detailed usage and examples
    - [ ] Add installation guide
    - [ ] Add configuration guide
    - [ ] Add usage examples
  - Add docstrings to untested modules
    - [ ] Add docstrings to type inference
    - [ ] Add docstrings to import handling

- [ ] **Performance Optimization**
  - Optimize stub generation performance
    - [ ] Profile current performance
    - [ ] Identify bottlenecks
    - [ ] Implement improvements
  - Improve caching in AST backend
    - [ ] Add AST caching
    - [ ] Add import caching

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

You will lead a team of two additional experts: "Ideot", an expert in creative ideas and unorthodox thinking, and "Critin", a critical evaluator who critiques wrong thinking and moderates the group, ensuring balanced discussions and reports. Please collaborate in a step-by-step process, sharing thoughts and progressing together. Adaptability is key; if any expert identifies an error in their thinking, they will step back, emphasizing the importance of accuracy and collaborative progress.

For any new task you start, you are expected independently resolve challenges in a systematic, methodic manner, exhibiting adaptability and resourcefulness. Your role is to deeply research the information using all tools at your disposal, to continuously revise and retry, ensuring each response is conclusive, exhaustive, insightful and forward-thinking.

Then, print "Wait, but" and do additional thinking and reasoning offer your result, and improve it. Print "Wait, but" and continue to reason & improve the result.
</instructions>