"""
Project scanner for NEAR Python ABI Builder.

This module provides functionality to scan directories for Python files
and build a complete view of a multi-file NEAR contract project.
"""

import os
from pathlib import Path
from typing import List
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
