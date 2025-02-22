"""Enhanced file importance analysis for Python packages.

This module provides tools to analyze and rank Python files based on multiple metrics:
- Dependency centrality (PageRank)
- Code complexity
- Test coverage
- Documentation quality
"""

import argparse
import ast
import importlib.util
import json
import os
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast

import networkx as nx
import toml
from coverage import Coverage
from pydocstyle import check as pydocstyle_check
from radon.complexity import cc_visit

# Type variables for better type safety
T = TypeVar("T")


def _cast_or_default(value: Any, default: T) -> T:
    """Cast a value to the type of the default or return the default if casting fails."""
    try:
        if isinstance(value, type(default)):
            return cast(T, value)
        return default
    except Exception:
        return default


# Optional dependency error messages
COVERAGE_MISSING = "coverage package not installed. Coverage analysis will be disabled."
PYDOCSTYLE_MISSING = (
    "pydocstyle package not installed. Documentation quality analysis will be disabled."
)
RADON_MISSING = (
    "radon package not installed. Code complexity analysis will be disabled."
)


def _check_optional_dependencies() -> dict[str, bool]:
    """Check which optional dependencies are available.

    Returns:
        Dictionary mapping dependency names to their availability status
    """
    available = {
        "coverage": True,
        "pydocstyle": True,
        "radon": True,
    }

    if not importlib.util.find_spec("coverage"):
        available["coverage"] = False
        print(COVERAGE_MISSING)

    if not importlib.util.find_spec("pydocstyle"):
        available["pydocstyle"] = False
        print(PYDOCSTYLE_MISSING)

    if not importlib.util.find_spec("radon"):
        available["radon"] = False
        print(RADON_MISSING)

    return available


# Check optional dependencies at module import time
AVAILABLE_DEPS = _check_optional_dependencies()


@dataclass
class FileImportanceConfig:
    """Configuration for file importance analysis."""

    exclude_dirs: list[str] = field(default_factory=list)
    centrality: str = "pagerank"  # One of: pagerank, betweenness, eigenvector
    coverage_data: str | None = None
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "centrality": 0.4,
            "complexity": 0.3,
            "coverage": 0.15,
            "doc_quality": 0.15,
        }
    )


def find_py_files(package_dir: str, exclude_dirs: list[str] | None = None) -> list[str]:
    """Find all .py files in the package directory, excluding specified directories.

    Args:
        package_dir: Root directory to search
        exclude_dirs: List of directory names to exclude

    Returns:
        List of Python file paths
    """
    py_files = []
    exclude_dirs = exclude_dirs or []
    for root, _, files in os.walk(package_dir):
        if any(exclude in root for exclude in exclude_dirs):
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def is_entry_point(file_path: str) -> bool:
    """Check if the file contains if __name__ == '__main__'."""
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)
                and len(node.test.comparators) == 1
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "__main__"
            ):
                return True
    except Exception:
        return False
    return False


def get_additional_entry_points(package_dir: str) -> list[str]:
    """Parse pyproject.toml for additional entry points like console scripts."""
    entry_points = []
    pyproject_path = os.path.join(package_dir, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path) as f:
                data = toml.load(f)
                scripts = data.get("project", {}).get("scripts", {})
                for script in scripts.values():
                    if os.path.exists(script) and script.endswith(".py"):
                        entry_points.append(script)
        except Exception:
            pass
    return entry_points


def _parse_import_node(
    source_file: str, node: ast.Import | ast.ImportFrom, py_files: list[str]
) -> list[tuple[str, str]]:
    """Parse a single import node and return edges for the import graph.

    Args:
        source_file: Path to the source file containing the import
        node: The AST import node to parse
        py_files: List of all Python files in the package

    Returns:
        List of (source, target) tuples representing import edges
    """
    edges = []
    if isinstance(node, ast.Import):
        for name in node.names:
            imported = name.name.split(".")[0]
            for target in py_files:
                if os.path.basename(target) == f"{imported}.py":
                    edges.append((source_file, target))
    elif isinstance(node, ast.ImportFrom) and node.module:
        imported = node.module.split(".")[0]
        for target in py_files:
            if os.path.basename(target) == f"{imported}.py":
                edges.append((source_file, target))
    return edges


def _parse_imports_from_file(file: str, py_files: list[str]) -> list[tuple[str, str]]:
    """Parse imports from a Python file and return edges for the import graph.

    Args:
        file: Path to the Python file to parse
        py_files: List of all Python files in the package

    Returns:
        List of (source, target) tuples representing import edges
    """
    edges = []
    try:
        with open(file, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                edges.extend(_parse_import_node(file, node, py_files))
    except Exception:
        pass
    return edges


def build_import_graph(package_dir: str, py_files: list[str]) -> nx.DiGraph:
    """Build the import graph using importlab and convert to networkx.

    Args:
        package_dir: Root directory of the Python package
        py_files: List of Python files to analyze

    Returns:
        A networkx DiGraph representing the import dependencies
    """
    # Create networkx graph
    G = nx.DiGraph()
    for file in py_files:
        G.add_node(file)

    # Parse imports from each file and add edges
    for file in py_files:
        edges = _parse_imports_from_file(file, py_files)
        G.add_edges_from(edges)

    return G


def calculate_complexity(file_path: str) -> float:
    """Calculate average cyclomatic complexity using radon."""
    if not AVAILABLE_DEPS["radon"]:
        return 0.0

    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        complexities = cc_visit(code)
        if not complexities:
            return 0.0
        total_complexity = sum(
            _cast_or_default(c.complexity, 0.0) for c in complexities
        )
        return total_complexity / len(complexities)
    except Exception as e:
        print(f"Warning: Failed to calculate complexity for {file_path}: {e}")
        return 0.0


def calculate_coverage(file_path: str, coverage_data: str | None) -> float:
    """Get test coverage percentage for the file.

    Args:
        file_path: Path to the Python file
        coverage_data: Path to coverage data file

    Returns:
        Coverage percentage between 0 and 100
    """
    if not AVAILABLE_DEPS["coverage"]:
        return 0.0

    if not coverage_data or not os.path.exists(coverage_data):
        return 0.0
    try:
        cov = Coverage(data_file=coverage_data)
        cov.load()
        analysis = cov._analyze(file_path)
        total_lines = _cast_or_default(analysis.numbers.n_statements, 0)
        covered_lines = _cast_or_default(analysis.numbers.n_executed, 0)
        return (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
    except Exception as e:
        print(f"Warning: Failed to calculate coverage for {file_path}: {e}")
        return 0.0


def calculate_doc_quality(file_path: str) -> float:
    """Assess documentation quality using pydocstyle."""
    if not AVAILABLE_DEPS["pydocstyle"]:
        return 0.0

    try:
        violations = list(pydocstyle_check([file_path], ignore=["D100", "D101"]))
        return max(0.0, 1.0 - (len(violations) / 10))
    except Exception as e:
        print(f"Warning: Failed to assess documentation quality for {file_path}: {e}")
        return 0.0


def _calculate_centrality(
    G: nx.DiGraph,
    py_files: list[str],
    centrality_measure: str,
    entry_points: dict[str, bool],
) -> dict[str, float]:
    """Calculate centrality scores for files in the import graph.

    Args:
        G: The import dependency graph
        py_files: List of Python files
        centrality_measure: Type of centrality to calculate
        entry_points: Dict mapping files to their entry point status

    Returns:
        Dictionary mapping files to their centrality scores
    """
    personalization_dict = {
        file: 1.0 if entry_points[file] else 0.0 for file in py_files
    }

    if centrality_measure == "pagerank":
        # If all values are 0, use uniform personalization
        if sum(personalization_dict.values()) == 0:
            personalization_dict = {file: 1.0 for file in py_files}
        result = nx.pagerank(G, personalization=personalization_dict)
        return {k: float(v) for k, v in result.items()}
    elif centrality_measure == "betweenness":
        result = nx.betweenness_centrality(G)
        return {k: float(v) for k, v in result.items()}
    elif centrality_measure == "eigenvector":
        try:
            result = nx.eigenvector_centrality(G, max_iter=500)
            return {k: float(v) for k, v in result.items()}
        except nx.PowerIterationFailedConvergence:
            return {file: 0.0 for file in py_files}
    else:
        print(
            f"Warning: Unsupported centrality measure '{centrality_measure}'. "
            "Using PageRank."
        )
        result = nx.pagerank(G)
        return {k: float(v) for k, v in result.items()}


def _print_results(
    sorted_files: list[tuple[str, float]],
    package_dir: str,
    entry_points: dict[str, bool],
    centrality: dict[str, float],
    complexity_scores: dict[str, float],
    coverage_scores: dict[str, float],
    doc_scores: dict[str, float],
) -> None:
    """Print analysis results in a formatted table.

    Args:
        sorted_files: List of (file, score) tuples sorted by score
        package_dir: Root directory of the package
        entry_points: Dict mapping files to their entry point status
        centrality: Dict mapping files to their centrality scores
        complexity_scores: Dict mapping files to their complexity scores
        coverage_scores: Dict mapping files to their coverage scores
        doc_scores: Dict mapping files to their documentation quality scores
    """
    header = (
        f"{'File Path':<50} {'Composite':<10} {'Centrality':<10} "
        f"{'Complexity':<10} {'Coverage':<10} {'Doc':<10} {'Entry':<6} {'Init'}"
    )
    print(header)
    print("-" * len(header))

    for file, score in sorted_files:
        is_entry = "Yes" if entry_points.get(file, False) else "No"
        is_init = "Yes" if os.path.basename(file) == "__init__.py" else "No"
        rel_path = os.path.relpath(file, package_dir)

        # Split long line into multiple lines for readability
        print(
            f"{rel_path:<50} {score:<10.3f} "
            f"{centrality.get(file, 0):<10.3f} "
            f"{complexity_scores.get(file, 0):<10.1f} "
            f"{coverage_scores.get(file, 0):<10.1f} "
            f"{doc_scores.get(file, 0):<10.2f} "
            f"{is_entry:<6} {is_init}"
        )


def prioritize_files(
    package_dir: str, config: FileImportanceConfig
) -> dict[str, float]:
    """Analyze and prioritize .py files in the package based on multiple metrics.

    Args:
        package_dir: Root directory of the Python package
        config: Configuration for importance analysis

    Returns:
        Dictionary mapping file paths to their composite importance scores
    """
    # Step 1: Collect .py files
    py_files = find_py_files(package_dir, config.exclude_dirs)
    if not py_files:
        print("No Python files found in the package directory.")
        return {}

    # Step 2: Build import graph and identify entry points
    G = build_import_graph(package_dir, py_files)
    entry_points = {file: is_entry_point(file) for file in py_files}
    additional_eps = get_additional_entry_points(package_dir)
    for ep in additional_eps:
        if ep in py_files:
            entry_points[ep] = True

    # Step 3: Calculate metrics
    centrality = _calculate_centrality(G, py_files, config.centrality, entry_points)
    complexity_scores = {file: calculate_complexity(file) for file in py_files}
    coverage_scores = {
        file: calculate_coverage(file, config.coverage_data) for file in py_files
    }
    doc_scores = {file: calculate_doc_quality(file) for file in py_files}

    # Step 4: Normalize complexity
    max_complexity = max(complexity_scores.values(), default=1.0)
    complexity_normalized = {
        file: score / max_complexity for file, score in complexity_scores.items()
    }

    # Step 5: Compute composite scores
    weights = config.weights
    composite_scores: dict[str, float] = {}
    for file in py_files:
        score = (
            weights["centrality"] * centrality.get(file, 0.0)
            + weights["complexity"] * complexity_normalized.get(file, 0.0)
            + weights["coverage"] * (coverage_scores.get(file, 0.0) / 100)
            + weights["doc_quality"] * doc_scores.get(file, 0.0)
        )
        composite_scores[file] = score

    # Step 6: Sort and display results
    sorted_files = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
    _print_results(
        sorted_files,
        package_dir,
        entry_points,
        centrality,
        complexity_scores,
        coverage_scores,
        doc_scores,
    )

    return composite_scores


def load_config(config_file: str | None) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = json.load(f)
                return cast(dict[str, Any], config)
        except Exception as e:
            print(
                "Warning: Failed to load config file "
                f"'{config_file}': {e}. Using defaults."
            )
    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Prioritize .py files in a Python package based on multiple metrics."
        )
    )
    parser.add_argument("package_dir", help="Path to the package directory")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--coverage-data", help="Path to coverage.py data file")
    parser.add_argument("--exclude-dirs", nargs="+", help="Directories to exclude")
    parser.add_argument(
        "--centrality",
        choices=["pagerank", "betweenness", "eigenvector"],
        default="pagerank",
        help="Centrality measure to use",
    )
    args = parser.parse_args()

    config = FileImportanceConfig()
    user_config = load_config(args.config)

    if user_config:
        config.weights.update(user_config.get("weights", {}))
        config.exclude_dirs.extend(user_config.get("exclude_dirs", []))
        if "centrality" in user_config:
            config.centrality = user_config["centrality"]

    if args.coverage_data:
        config.coverage_data = args.coverage_data
    if args.exclude_dirs:
        config.exclude_dirs.extend(args.exclude_dirs)
    if args.centrality:
        config.centrality = args.centrality

    prioritize_files(args.package_dir, config)
