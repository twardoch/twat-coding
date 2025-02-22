---
this_file: TODO.md
---

# TODO

## 1. Immediate Priorities

- [!] **Fix Import and Type Errors**
  - *Problem*: Import errors with `TruncationConfig` and type compatibility issues
  - *Solution*: 
    1. Update imports to use `shared_types.TruncationConfig` instead of `types.TruncationConfig`
    2. Fix type compatibility in `ast_utils.py` and `config.py`
    3. Resolve remaining type errors in `__init__.py`

- [!] **Improve Test Coverage**
  - *Current*: 10% (target: 50%)
  - *Focus Areas*:
    1. `src/twat_coding/pystubnik/backends/ast_backend.py` (8% coverage)
    2. `src/twat_coding/pystubnik/processors/stub_generation.py` (0% coverage)
    3. `src/twat_coding/pystubnik/processors/type_inference.py` (0% coverage)
  - *Next Steps*:
    1. Fix failing test imports first
    2. Add core tests for AST backend
    3. Add tests for processors

## 2. Future Tasks

- [ ] **Enhance Documentation**
  - Update README.md with clear usage examples
  - Add docstrings to key classes and functions
  - Create example files demonstrating features

- [ ] **Code Cleanup**
  - Refactor complex functions in `ast_backend.py`
  - Simplify configuration system
  - Remove redundant code

- [ ] **Performance Optimization**
  - Profile stub generation performance
  - Optimize memory usage in AST processing
  - Improve concurrent processing

## 3. Completed Tasks

- [x] **Core AST Backend Implementation**
  - Basic stub generation functionality
  - AST transformation logic
  - Error handling

- [x] **Project Structure**
  - Basic project layout
  - Module organization
  - Package configuration

- [x] **Type System Improvements**
  - Created `shared_types.py` for common types
  - Defined `TruncationConfig` as a shared type
  - Implemented Protocol for type compatibility

## 4. Notes

- Focus on fixing the import errors first as they're blocking tests
- Prioritize type error fixes to ensure code reliability
- Improve test coverage incrementally, focusing on core functionality first

Before you do any changes or if I say "cleanup", run the `./cleanup.py install && source .venv/bin/activate && ./cleanup.py update | cat` script in the main folder. Analyze the results, describe recent changes @TODO.md to update priorities and plan next changes. PERFORM THE CHANGES, then run the `./cleanup.py update | cat` script and react to the results.

When you edit @TODO.md, lead in lines with empty GFM checkboxes if things aren't done (`- [ ] `) vs. filled (`- [x] `) if done, and `- [!]` if they're NEXT TODO.

Don't use `pip`, use `uv pip`. Ignore minor problems like "line too long", FOCUS ON MAJOR PROBLEMS!

---

Hey, junior dev! This `TODO.md` is your step-by-step guide to get `pystubnik` ready for its 1.0 release—a rock-solid tool for generating smart stubs. We're keeping it simple: one backend (AST), smart file importance, basic tests, and clear docs. Every task below is broken down so you can nail it. If you get stuck, run `./cleanup.py status`, check `CLEANUP.log`, and ask for help. Let's make this awesome together!

## 5. Core Functionality

- [x] **Lock Down the AST Backend**
  - *Status*: It's in `src/twat_coding/pystubnik/backends/ast_backend.py` and works!
  - *Why*: This is our stub-generating powerhouse for 1.0—no MyPy or hybrid yet (but keep them around)

- [!] **Fully Integrate File Importance**
  - *What*: Use importance scores to control stub detail (e.g., keep docstrings for important files).
  - *Why*: This is the "smart" in smart stubs—more detail where it matters.
  - *How*:
    1. Open `src/twat_coding/pystubnik/core/types.py`.
    2. Update `StubResult` to store metadata:
       ```python
       @dataclass
       class StubResult:
           source_path: Path
           stub_content: str
           imports: list[ImportInfo]
           errors: list[str]
           importance_score: float = 0.0
           metadata: dict[str, Any] = field(default_factory=dict)  # Add this
       ```
    3. Open `src/twat_coding/pystubnik/backends/ast_backend.py`.
    4. In `SignatureExtractor.__init__`, add importance:
       ```python
       def __init__(self, config: StubGenConfig, file_size: int = 0, importance_score: float = 1.0):
           super().__init__()
           self.config = config
           self.file_size = file_size
           self.importance_score = importance_score  # Add this
       ```
    5. Update `_preserve_docstring` to use importance:
       ```python
       def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
           if not body:
               return []
           if self.file_size > self.config.truncation.max_file_size and self.importance_score < 0.7:
               return []  # Skip docstrings for big, low-importance files
           match body[0]:
               case ast.Expr(value=ast.Constant(value=str() as docstring)):
                   if len(docstring) > self.config.truncation.max_docstring_length and self.importance_score < 0.9:
                       return []  # Skip long docstrings unless very important
                   return [body[0]]
               case _:
                   return []
       ```
    6. In `ASTBackend.generate_stub`, pass the score:
       ```python
       async def generate_stub(self, source_path: Path) -> str:
           # ... existing code ...
           # After getting file_score elsewhere or calculating it:
           file_score = 0.5  # Placeholder; we'll get this from ImportanceProcessor
           tree = await self._run_in_executor(
               functools.partial(ast.parse, source, filename=str(source_path))
           )
           attach_parents(tree)
           transformer = SignatureExtractor(self.config.stub_gen_config, len(source), file_score)
           transformed = transformer.visit(tree)
           stub_content = ast.unparse(transformed)
           # ... rest of the method ...
       ```
    7. Open `src/twat_coding/pystubnik/processors/importance.py`.
    8. Update `process` to set the score:
       ```python
       def process(self, stub_result: StubResult) -> StubResult:
           package_dir = str(stub_result.source_path.parent)
           self._file_scores = prioritize_files(package_dir, self.config.file_importance)
           file_score = self._file_scores.get(str(stub_result.source_path), 0.5)
           stub_result.importance_score = file_score
           stub_result.metadata["file_score"] = file_score
           # Process individual symbols
           tree = ast.parse(stub_result.stub_content)
           for node in ast.walk(tree):
               if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                   docstring = ast.get_docstring(node)
                   score = self.calculate_importance(
                       name=node.name,
                       docstring=docstring,
                       is_public=not node.name.startswith('_'),
                       is_special=node.name.startswith('__') and node.name.endswith('__'),
                       extra_info={"file_path": stub_result.source_path}
                   )
                   stub_result.metadata[f"{node.name}_score"] = score
                   if score < 0.7 and isinstance(node, ast.FunctionDef):
                       node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
           stub_result.stub_content = ast.unparse(tree)
           return stub_result
       ```
    9. Test it:
       - Run `./cleanup.py install && source .venv/bin/activate`.
       - Run `python -m twat_coding.pystubnik generate --files src/twat_coding/pystubnik/__init__.py`.
       - Check `out/__init__.pyi`—important functions should keep docstrings, others should simplify.

- [ ] **Simplify Configuration**
  - *What*: Trim `StubGenConfig` to essentials for 1.0.
  - *Why*: Less complexity for users and you!
  - *How*:
    1. Open `src/twat_coding/pystubnik/core/config.py`.
    2. Replace `StubGenConfig` with:
       ```python
       @dataclass(frozen=True)
       class StubGenConfig:
           output_dir: Path = Path("out")
           files: Sequence[Path] = field(default_factory=list)
           include_docstrings: bool = True
           max_docstring_length: int = 150
           ignore_errors: bool = True
       ```
    3. Update `SmartStubGenerator.__init__` in `__init__.py`:
       ```python
       def __init__(
           self,
           output_dir: str | Path = "out",
           files: Sequence[str | Path] = (),
           include_docstrings: bool = True,
           max_docstring_length: int = 150,
           ignore_errors: bool = True,
       ):
           self.config = StubGenConfig(
               output_dir=Path(output_dir),
               files=[Path(f) for f in files],
               include_docstrings=include_docstrings,
               max_docstring_length=max_docstring_length,
               ignore_errors=ignore_errors,
           )
           # ... rest of init ...
       ```
    4. Fix any import errors in other files (e.g., `ast_backend.py`).

## 6. Testing

- [!] **Add Core Tests**
  - *What*: Test stub generation and importance logic.
  - *Why*: We need 50% coverage for trust—start here.
  - *How*:
    1. Replace `tests/test_package.py` with:
       ```python
       import pytest
       from twat_coding.pystubnik import SmartStubGenerator, StubResult
       from twat_coding.pystubnik.backends.ast_backend import ASTBackend
       from twat_coding.pystubnik.processors.importance import ImportanceProcessor
       from pathlib import Path

       def test_ast_backend(tmp_path):
           """Test AST stub generation."""
           test_file = tmp_path / "test.py"
           test_file.write_text('''"""
           Important file
           """
           def hello(name: str) -> str:
               return "Hello"
           ''')
           config = StubGenConfig(output_dir=tmp_path, files=[test_file])
           backend = ASTBackend(config)
           result = backend.generate_stub(test_file).result()  # Async call
           stub_file = tmp_path / "test.pyi"
           assert stub_file.exists()
           content = stub_file.read_text()
           assert "def hello(name: str) -> str" in content
           assert '"""Important file"""' in content  # Docstring preserved

       def test_importance_processor(tmp_path):
           """Test importance scoring affects stubs."""
           test_file = tmp_path / "low.py"
           test_file.write_text('''def minor():
               """Minor function"""
               pass
           ''')
           config = StubGenConfig(output_dir=tmp_path, files=[test_file])
           generator = SmartStubGenerator(output_dir=tmp_path, files=[str(test_file)])
           generator.generate()
           stub_file = tmp_path / "low.pyi"
           content = stub_file.read_text()
           assert "def minor(): ..." in content  # Low importance, no docstring

       def test_cli(tmp_path):
           """Test CLI end-to-end."""
           test_file = tmp_path / "cli.py"
           test_file.write_text("def run(): pass")
           import subprocess
           subprocess.run([
               "python", "-m", "twat_coding.pystubnik", "generate",
               "--files", str(test_file), "--output-dir", str(tmp_path)
           ], check=True)
           assert (tmp_path / "cli.pyi").exists()
       ```
    2. Run `./cleanup.py install && source .venv/bin/activate && pytest tests/`.
    3. Fix failures (e.g., add `asyncio.run()` around async calls if needed).

- [ ] **Boost Coverage to 50%**
  - *What*: Add tests for key modules.
  - *Why*: Ensures stuff doesn't break.
  - *How*:
    1. Run `pytest --cov=src/twat_coding tests/`.
    2. Create `tests/test_processors.py`:
       ```python
       def test_import_processor(tmp_path):
           from twat_coding.pystubnik.processors.imports import ImportProcessor
           processor = ImportProcessor()
           result = StubResult(tmp_path / "test.py", "import os\n", [], [])
           processed = processor.process(result)
           assert "import os" in processed.stub_content
       ```
    3. Add more tests for `docstring.py`, `ast_utils.py` based on coverage gaps.
    4. Rerun until coverage hits 50%.

## 7. Documentation

- [!] **Revamp README.md**
  - *What*: Make it user-ready with usage and example.
  - *Why*: First impression for adopters.
  - *How*:
    1. Open `README.md`.
    2. Replace "Usage" section with:
       ```markdown
       ## 8. Usage

       Generate smart stubs with a simple command:

       ```bash
       python -m twat_coding.pystubnik generate --files my_script.py --output-dir stubs
       ```

       Or in Python:

       ```python
       from twat_coding.pystubnik import SmartStubGenerator

       generator = SmartStubGenerator(
           output_dir="stubs",
           files=["my_script.py"],
           include_docstrings=True
       )
       generator.generate()
       ```

       ### 8.1. Example

       **Input** (`example.py`):
       ```python
       def greet(name: str) -> str:
           """Say hello to someone important."""
           return f"Hello, {name}"
       ```

       **Output** (`stubs/example.pyi`):
       ```python
       def greet(name: str) -> str:
           """Say hello to someone important."""
           ...
       ```
       ```
    3. Save and check with `cat README.md`.

- [ ] **Add Example File**
  - *What*: A real file to demo.
  - *Why*: Users can try it themselves.
  - *How*:
    1. Create `examples/greet.py`:
       ```python
       def greet(name: str) -> str:
           """Say hello to someone important."""
           return f"Hello, {name}"
       ```
    2. Test it: `python -m twat_coding.pystubnik generate --files examples/greet.py`.

- [ ] **Update CLI Help**
  - *What*: Add clear CLI options.
  - *Why*: Makes it user-friendly.
  - *How*:
    1. Open `src/twat_coding/pystubnik/__init__.py`.
    2. Add a CLI entry point:
       ```python
       import click

       @click.command()
       @click.option("--files", multiple=True, type=click.Path(exists=True), help="Files to process")
       @click.option("--output-dir", default="out", type=click.Path(), help="Output directory")
       @click.option("--include-docstrings", is_flag=True, default=True, help="Keep docstrings")
       def generate(files, output_dir, include_docstrings):
           """Generate smart stubs for Python files."""
           generator = SmartStubGenerator(
               output_dir=output_dir,
               files=files,
               include_docstrings=include_docstrings
           )
           generator.generate()

       if __name__ == "__main__":
           generate()
       ```
    3. Test: `python -m twat_coding.pystubnik --help`.

## 9. Code Quality

- [!] **Fix Type Errors**
  - *What*: Clear all `mypy` issues.
  - *Why*: Clean code = fewer bugs.
  - *How*:
    1. Run `./cleanup.py install && source .venv/bin/activate && mypy src/`.
    2. Fix errors:
       - `type_system.py`: Replace `issubclass` with:
         ```python
         if isinstance(resolved, type) and hasattr(resolved, "__mro__") and issubclass(resolved, Protocol):
         ```
       - Follow old `TODO.md` section 2 for others.
    3. Rerun until no errors.

- [ ] **Refactor Complex Functions**
  - *What*: Simplify `truncate_literal` and `calculate_importance`.
  - *Why*: Easier for you to maintain.
  - *How*:
    1. In `ast_backend.py`, split `truncate_literal`:
       ```python
       def truncate_string(self, s: str) -> str:
           return s if len(s) <= self.config.truncation.max_string_length else f"{s[:self.config.truncation.max_string_length]}..."

       def truncate_literal(self, node: ast.AST) -> ast.AST:
           if isinstance(node, ast.Constant) and isinstance(node.value, str):
               return ast.Constant(value=self.truncate_string(node.value))
           # ... other cases ...
       ```
    2. In `importance.py`, break down `calculate_importance`:
       ```python
       def _score_by_name(self, name: str) -> float:
           score = 1.0
           for pattern, weight in self.config.patterns.items():
               if re.search(pattern, name):
                   score *= weight
           return score

       def calculate_importance(self, name: str, docstring: str | None = None, ...):
           file_score = self._get_file_score(extra_info)
           pattern_score = self._score_by_name(name)
           # ... combine scores ...
       ```

- [x] **Remove Redundant Scripts**
  - *What*: Delete old standalone files DONE
  - *Why*: Keeps the codebase clean.

## 10. Release Preparation

- [ ] **Finalize 1.0**
  - *What*: Version it, log it, ship it.
  - *Why*: Makes it official!
  - *How*:
    1. In `src/twat_coding/__version__.py`, set:
       ```python
       version = "1.0.0"
       ```
    2. Run `./cleanup.py update && ./cleanup.py push`.

## 11. Next Actions

- [!] Integrate file importance fully (step 1.2).
- [!] Add core tests (step 2.1).
- [!] Revamp README.md (step 3.1).
- [!] Fix type errors (step 4.1).

## 12. Notes

- Focus on AST only—MyPy's for later.
- Test every change with `./cleanup.py status`.
- You're doing great—let's ship this!

