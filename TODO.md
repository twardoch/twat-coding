---
this_file: TODO.md
---

# TODO

## 1. Immediate Priorities

- [!] **Fix Private Class Exclusion**
  - *Critical Bug*:
    - [!] Fix failing test in `test_stub_generation_config`
    - [!] Ensure private classes are properly excluded in `StubVisitor`
    - [!] Add test cases for special methods and nested private classes

- [x] **Add CLI Interface**
  - *Using Fire for Command Line*:
    - [x] Create `cli.py` with Fire interface
      - [x] Add `generate` command for single file
      - [x] Add `generate-dir` command for directory
      - [x] Add `--config` option for configuration file
    - [x] Add progress bar using rich
    - [x] Add colorful output for errors and warnings

- [!] **Add Config File Support**
  - *YAML Configuration*:
    - [!] Add YAML config file support to CLI
    - [!] Add config validation using Pydantic
    - [!] Add config file examples

- [!] **Fix Type Annotations**
  - *High Priority Fixes*:
    - [!] Add missing type annotations in `stub_generation.py`:
      - [!] Fix "sorted_imports" type annotation
      - [!] Fix "imports" type annotation
      - [!] Fix ImportFrom/Import type mismatches

- [!] **Reduce Code Complexity**
  - *Refactoring*:
    - [!] Split `generate_stub` method (complexity: 13 > 10)
      - [!] Extract AST processing logic
      - [!] Extract content generation logic
    - [!] Split `_sort_imports` method (complexity: 11 > 10)
      - [!] Extract import categorization logic
      - [!] Extract sorting logic

## 2. Near-term Tasks

- [ ] **Improve Test Coverage (Current: 46%)**
  - *Critical Modules with Low Coverage*:
    - [ ] Write tests for `type_inference.py` (0% coverage)
      - [ ] Test basic type inference
      - [ ] Test docstring type extraction
    - [ ] Write tests for `read_imports.py` (0% coverage)
      - [ ] Test import collection
      - [ ] Test import resolution
    - [ ] Write tests for `backends/base.py` (0% coverage)
      - [ ] Test backend interface
      - [ ] Test common functionality

## 3. Future Tasks

- [ ] **Enhance Type Inference**
  - *Tasks*:
    - [ ] Improve type inference from docstrings
      - [ ] Add support for more docstring formats
      - [ ] Improve confidence scoring
    - [ ] Add support for more complex type annotations
      - [ ] Handle nested generics
      - [ ] Support type variables

- [ ] **Documentation Updates**
  - Update README.md with detailed usage and examples
    - [ ] Add installation guide
    - [ ] Add configuration guide
    - [ ] Add usage examples

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