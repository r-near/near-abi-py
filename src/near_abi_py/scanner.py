"""
Project scanner for NEAR Python ABI Builder.

This module provides functionality to scan directories for Python files
and build a complete view of a multi-file NEAR contract project.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import pathspec


def find_python_files(
    directory: str, recursive: bool = True, respect_gitignore: bool = True
) -> List[str]:
    """
    Find all Python files in the given directory.

    Args:
        directory: Path to the directory to scan
        recursive: Whether to scan subdirectories recursively
        respect_gitignore: Whether to respect .gitignore patterns

    Returns:
        List of paths to Python files
    """
    # Convert to absolute path to avoid relative path issues
    directory_path = Path(os.path.abspath(directory))
    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    # Load .gitignore if available and requested
    gitignore_spec = None
    if respect_gitignore:
        gitignore_path = directory_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                gitignore_content = f.read()
            gitignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, gitignore_content.splitlines()
            )

    python_files = []

    # Walk through the directory
    if recursive:
        for root, _, files in os.walk(str(directory_path)):
            root_path = Path(os.path.abspath(root))
            # Calculate relative path safely
            try:
                rel_path = root_path.relative_to(directory_path)
                rel_path_str = str(rel_path) if rel_path != Path(".") else ""
            except ValueError:
                # Fallback if relative_to fails
                rel_path_str = os.path.relpath(root, str(directory_path))
                rel_path_str = "" if rel_path_str == "." else rel_path_str

            for file in files:
                # Check file extension
                if not file.endswith(".py"):
                    continue

                # Build relative path for gitignore matching
                file_rel_path = os.path.join(rel_path_str, file).replace("\\", "/")

                # Skip if matched by gitignore
                if gitignore_spec and gitignore_spec.match_file(file_rel_path):
                    continue

                python_files.append(str(root_path / file))
    else:
        # Non-recursive version
        for item in directory_path.iterdir():
            if item.is_file() and item.suffix == ".py":
                # Calculate relative path for gitignore matching
                try:
                    rel_path = item.relative_to(directory_path)
                except ValueError:
                    # Fallback for relative path calculation
                    rel_path = Path(os.path.relpath(str(item), str(directory_path)))

                rel_path_str = str(rel_path).replace("\\", "/")
                if gitignore_spec and gitignore_spec.match_file(rel_path_str):
                    continue
                python_files.append(str(item))

    return python_files


def resolve_main_files(python_files: List[str]) -> List[str]:
    """
    Identify potential main contract files from a list of Python files.

    This looks for files that are likely to contain contract entry points
    based on common naming patterns in NEAR contracts.

    Args:
        python_files: List of Python file paths

    Returns:
        List of likely main contract files, sorted by likelihood
    """
    # Score each file based on potential indicators of being a main contract file
    scored_files = []

    for file_path in python_files:
        file_name = os.path.basename(file_path)
        score = 0

        # Check filename indicators
        if file_name == "contract.py":
            score += 10
        elif file_name == "main.py":
            score += 8
        elif "contract" in file_name:
            score += 5
        elif "main" in file_name:
            score += 4

        # Prioritize files in the root directory
        if (
            len(Path(file_path).parts) - len(Path(os.path.dirname(file_path)).parts)
            <= 1
        ):
            score += 3

        scored_files.append((file_path, score))

    # Sort by score, highest first
    scored_files.sort(key=lambda x: x[1], reverse=True)

    # Return paths only
    return [path for path, _ in scored_files]


def analyze_import_structure(
    project_path: str, python_files: List[str]
) -> Dict[str, List[str]]:
    """
    Analyze the import structure of Python files to detect dependencies.

    Args:
        project_path: Root path of the project
        python_files: List of Python file paths

    Returns:
        Dictionary mapping file paths to their imports
    """
    import_map: Dict[str, List[str]] = {}

    # Build module name to file path mapping
    module_map: Dict[str, str] = {}
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, project_path)
        module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")

        # Handle __init__.py files
        if module_path.endswith(".__init__"):
            package_name = module_path[:-9]  # Remove .__init__
            if package_name:
                module_map[package_name] = file_path

        module_map[module_path] = file_path

    # Analyze imports
    for file_path in python_files:
        try:
            imports = extract_imports(file_path)
            import_map[file_path] = []

            # Map import names to file paths
            for import_name in imports:
                # Check if import is a local module
                if import_name in module_map:
                    import_map[file_path].append(module_map[import_name])
        except Exception:
            # Skip files with parsing errors
            import_map[file_path] = []

    return import_map


def extract_imports(file_path: str) -> List[str]:
    """
    Extract import statements from a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        List of imported module names
    """
    import ast

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []

    imports = []

    # Find import statements
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imports.append(node.module)

    return imports


def detect_contract_dependencies(
    project_path: str, python_files: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect dependencies between contract files.

    Args:
        project_path: Root path of the project
        python_files: List of Python file paths

    Returns:
        Dictionary mapping file paths to their dependencies
    """
    import_structure = analyze_import_structure(project_path, python_files)

    # Build dependency graph
    dependency_graph: Dict[str, List[Dict[str, Any]]] = {}

    for file_path in python_files:
        if file_path not in dependency_graph:
            dependency_graph[file_path] = []

        # Add direct dependencies
        for imported_file in import_structure.get(file_path, []):
            if imported_file in python_files:
                dependency_graph[file_path].append(
                    {"path": imported_file, "type": "import"}
                )

    return dependency_graph


def scan_project(
    project_path: str, recursive: bool = True, respect_gitignore: bool = True
) -> Dict[str, Any]:
    """
    Scan a project directory and analyze its structure.

    Args:
        project_path: Path to the project directory
        recursive: Whether to scan subdirectories recursively
        respect_gitignore: Whether to respect .gitignore patterns

    Returns:
        Dictionary with project analysis results
    """
    # Find Python files
    python_files = find_python_files(
        project_path, recursive=recursive, respect_gitignore=respect_gitignore
    )

    # Identify main contract files
    main_files = resolve_main_files(python_files)

    # Analyze dependencies
    dependencies = detect_contract_dependencies(project_path, python_files)

    return {
        "project_path": project_path,
        "python_files": python_files,
        "main_files": main_files,
        "dependencies": dependencies,
        "file_count": len(python_files),
    }
