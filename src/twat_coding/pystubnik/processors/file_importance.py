"""Enhanced file importance analysis for Python packages.

This module provides tools to analyze and rank Python files based on multiple metrics:
- Dependency centrality (PageRank)
- Code complexity
- Test coverage
- Documentation quality
"""

import argparse
import ast
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import networkx as nx
import toml
from coverage import Coverage
from importlab.env import Environment
from importlab.graph import ImportGraph
from importlab.resolve import Resolver
from pydocstyle import check as pydocstyle_check
from radon.complexity import cc_visit


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


def build_import_graph(package_dir: str, py_files: list[str]) -> ImportGraph:
    """Build the import graph using importlab."""
    env = Environment()
    resolver = Resolver(env)
    graph = ImportGraph()
    for file in py_files:
        graph.add_file(file)
    graph.resolve_imports(resolver)
    return graph


def calculate_complexity(file_path: str) -> float:
    """Calculate average cyclomatic complexity using radon."""
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        complexities = cc_visit(code)
        if not complexities:
            return 0
        total_complexity = sum(c.complexity for c in complexities)
        return total_complexity / len(complexities)
    except Exception:
        return 0


def calculate_coverage(file_path: str, coverage_data: str | None) -> float:
    """Get test coverage percentage for the file."""
    if not coverage_data or not os.path.exists(coverage_data):
        return 0
    try:
        cov = Coverage(data_file=coverage_data)
        cov.load()
        analysis = cov._analyze(file_path)
        return analysis.numbers.percentage or 0
    except Exception:
        return 0


def calculate_doc_quality(file_path: str) -> float:
    """Assess documentation quality using pydocstyle."""
    try:
        violations = list(pydocstyle_check([file_path], ignore=["D100", "D101"]))
        return max(0, 1 - (len(violations) / 10))
    except Exception:
        return 0


def prioritize_files(package_dir: str, config: FileImportanceConfig) -> None:
    """Analyze and prioritize .py files in the package based on multiple metrics.

    Args:
        package_dir: Root directory of the Python package
        config: Configuration for importance analysis
    """
    # Step 1: Collect .py files
    py_files = find_py_files(package_dir, config.exclude_dirs)
    if not py_files:
        print("No Python files found in the package directory.")
        return

    # Step 2: Build import graph
    import_graph = build_import_graph(package_dir, py_files)

    # Step 3: Create networkx graph
    G = nx.DiGraph()
    for file in py_files:
        G.add_node(file)
    for file, imports in import_graph.graph.items():
        for imported_file in imports:
            if imported_file in py_files:
                G.add_edge(file, imported_file)

    # Step 4: Identify entry points
    entry_points = {file: is_entry_point(file) for file in py_files}
    additional_eps = get_additional_entry_points(package_dir)
    for ep in additional_eps:
        if ep in py_files:
            entry_points[ep] = True

    # Step 5: Compute centrality
    centrality_measure = config.centrality
    personalization = {file: 1 if entry_points[file] else 0 for file in py_files}

    if centrality_measure == "pagerank":
        if sum(personalization.values()) == 0:
            personalization = None
        centrality = nx.pagerank(G, personalization=personalization)
    elif centrality_measure == "betweenness":
        centrality = nx.betweenness_centrality(G)
    elif centrality_measure == "eigenvector":
        try:
            centrality = nx.eigenvector_centrality(G, max_iter=500)
        except nx.PowerIterationFailedConvergence:
            centrality = {file: 0 for file in py_files}
    else:
        print(
            f"Warning: Unsupported centrality measure '{centrality_measure}'. Using PageRank."
        )
        centrality = nx.pagerank(G)

    # Step 6: Calculate additional metrics
    complexity_scores = {file: calculate_complexity(file) for file in py_files}
    coverage_scores = {
        file: calculate_coverage(file, config.coverage_data) for file in py_files
    }
    doc_scores = {file: calculate_doc_quality(file) for file in py_files}

    # Step 7: Normalize complexity
    max_complexity = max(complexity_scores.values(), default=1)
    complexity_normalized = {
        file: score / max_complexity for file, score in complexity_scores.items()
    }

    # Step 8: Compute composite score
    weights = config.weights
    composite_scores = {}
    for file in py_files:
        score = (
            weights["centrality"] * centrality.get(file, 0)
            + weights["complexity"] * complexity_normalized.get(file, 0)
            + weights["coverage"] * (coverage_scores.get(file, 0) / 100)
            + weights["doc_quality"] * doc_scores.get(file, 0)
        )
        composite_scores[file] = score

    # Step 9: Sort and output
    sorted_files = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)

    header = (
        f"{'File Path':<50} {'Composite':<10} {'Centrality':<10} "
        f"{'Complexity':<10} {'Coverage':<10} {'Doc':<10} {'Entry':<6} {'Init'}"
    )
    print(header)
    print("-" * len(header))

    for file, score in sorted_files:
        is_entry = "Yes" if entry_points.get(file, False) else "No"
        is_init = "Yes" if os.path.basename(file) == "__init__.py" else "No"
        print(
            f"{file:<50} {score:<10.3f} {centrality.get(file, 0):<10.3f} "
            f"{complexity_scores.get(file, 0):<10.1f} "
            f"{coverage_scores.get(file, 0):<10.1f} "
            f"{doc_scores.get(file, 0):<10.2f} {is_entry:<6} {is_init}"
        )


def load_config(config_file: str | None) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception as e:
            print(
                f"Warning: Failed to load config file '{config_file}': {e}. Using defaults."
            )
    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prioritize .py files in a Python package based on multiple metrics."
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
