"""
Utility functions for NEAR ABI generation.
"""

import importlib.util
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import jsonschema
from rich.console import Console

from .core import DEFAULT_METADATA, NearDecorator

# Console for rich output - automatically detects color support
console = Console()


def log_success(message: str) -> None:
    """Log a success message"""
    console.print(f"[bold green]✓[/] {message}")


def log_error(message: str) -> None:
    """Log an error message"""
    console.print(f"[bold red]×[/] {message}")


def log_info(message: str) -> None:
    """Log an info message"""
    console.print(f"[bold blue]-[/] {message}")


def log_warning(message: str) -> None:
    """Log a warning message"""
    console.print(f"[bold yellow]![/] {message}")


def load_module(file_path: str) -> Any:
    """
    Load a Python module from a file path.

    Args:
        file_path: Path to the Python file

    Returns:
        Loaded module object
    """
    module_name = Path(file_path).stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")

    # Add directory to sys.path temporarily
    module_dir = os.path.dirname(os.path.abspath(file_path))
    original_path = list(sys.path)

    try:
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    finally:
        # Restore original sys.path
        sys.path = original_path


def find_python_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Find all Python files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search recursively

    Returns:
        List of Python file paths
    """
    python_files = []
    directory_path = Path(directory)

    if recursive:
        # Use glob for recursive search
        for file_path in directory_path.glob("**/*.py"):
            python_files.append(str(file_path))
    else:
        # Non-recursive search
        for file_path in directory_path.glob("*.py"):
            python_files.append(str(file_path))

    return python_files


def get_function_decorators(func: Callable) -> List[NearDecorator]:
    """
    Extract NEAR decorators from a function.

    Args:
        func: Function object to inspect

    Returns:
        List of NEAR decorators found on the function
    """
    decorators = []

    # Method 1: Check for explicitly stored decorators
    if hasattr(func, "__decorators__"):
        for decorator in getattr(func, "__decorators__"):
            try:
                decorators.append(NearDecorator(decorator))
            except ValueError:
                pass  # Not a NEAR decorator

        return decorators

    # Method 2: Source code inspection fallback
    try:
        source = inspect.getsource(func)
        for decorator_value in NearDecorator:
            decorator_name = decorator_value.value
            # Match both @decorator and @near.decorator forms
            if re.search(r"@(near\.)?(" + decorator_name + r")\b", source):
                decorators.append(decorator_value)
    except Exception:
        # Source inspection failed - could be a built-in or C function
        pass

    return decorators


def get_function_docstring(func: Callable) -> Optional[str]:
    """Extract and clean a function's docstring"""
    if func.__doc__:
        return inspect.cleandoc(func.__doc__)
    return None


def is_contract_function(func: Callable) -> bool:
    """
    Determine if a function is a NEAR contract function.

    Args:
        func: Function to check

    Returns:
        True if this is a contract function
    """
    return len(get_function_decorators(func)) > 0


def extract_metadata(package_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a file path or package directory.

    Args:
        package_path: Path to the contract file or directory

    Returns:
        Metadata dictionary
    """
    from .core import DEFAULT_METADATA

    # Basic metadata with defaults
    metadata = DEFAULT_METADATA.copy()
    metadata["name"] = Path(package_path).stem

    # Find and process project file
    project_file = find_project_file(package_path, "pyproject.toml")
    if project_file:
        update_from_project_file(metadata, project_file)

    return metadata


def extract_project_metadata(project_dir: str) -> Dict[str, Any]:
    """
    Extract metadata from a project directory.

    Args:
        project_dir: Path to the project directory

    Returns:
        Metadata dictionary
    """
    # Check each possible project file
    for filename in ["pyproject.toml", "setup.py", "Cargo.toml"]:
        project_file = os.path.join(project_dir, filename)
        if os.path.exists(project_file):
            return extract_metadata(project_file)

    # If no project file found, use directory name as project name
    metadata = DEFAULT_METADATA.copy()
    metadata["name"] = os.path.basename(project_dir)
    return metadata


def find_project_file(start_path: str, filename: str) -> Optional[str]:
    """
    Find a project file by searching upwards from start_path.

    Args:
        start_path: Path to start searching from
        filename: Name of file to search for

    Returns:
        Path to the found file, or None if not found
    """
    current_dir = os.path.abspath(start_path)

    # If start_path is a file, start from its directory
    if os.path.isfile(current_dir):
        current_dir = os.path.dirname(current_dir)

    # Search upwards until we find the file or hit the root
    while True:
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path):
            return file_path

        # Move up one directory
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            return None

        current_dir = parent_dir


def update_from_project_file(metadata: Dict[str, Any], project_file: str) -> None:
    """
    Update metadata from a project file.

    Args:
        metadata: Metadata dictionary to update
        project_file: Path to the project file
    """
    # Handle pyproject.toml
    if project_file.endswith("pyproject.toml"):
        update_from_pyproject(metadata, project_file)
    # Handle Cargo.toml for mixed Rust/Python projects
    elif project_file.endswith("Cargo.toml"):
        update_from_cargo_toml(metadata, project_file)


def update_from_pyproject(metadata: Dict[str, Any], pyproject_path: str) -> None:
    """
    Update metadata from pyproject.toml.

    Args:
        metadata: Metadata dictionary to update
        pyproject_path: Path to pyproject.toml
    """
    try:
        # Use tomllib for Python >= 3.11
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                # Skip if tomli is not available
                return

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        # Extract project info
        if "project" in pyproject_data:
            project = pyproject_data["project"]
            if "name" in project:
                metadata["name"] = project["name"]
            if "version" in project:
                metadata["version"] = project["version"]
            if "authors" in project:
                metadata["authors"] = [
                    author["name"] if isinstance(author, dict) else author
                    for author in project["authors"]
                ]
    except Exception as e:
        log_warning(f"Error reading pyproject.toml: {e}")


def update_from_cargo_toml(metadata: Dict[str, Any], cargo_path: str) -> None:
    """
    Update metadata from Cargo.toml for mixed Rust/Python projects.

    Args:
        metadata: Metadata dictionary to update
        cargo_path: Path to Cargo.toml
    """
    try:
        # Use tomllib for Python >= 3.11
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                # Skip if tomli is not available
                return

        with open(cargo_path, "rb") as f:
            cargo_data = tomllib.load(f)

        # Extract package info
        if "package" in cargo_data:
            package = cargo_data["package"]
            if "name" in package:
                metadata["name"] = package["name"]
            if "version" in package:
                metadata["version"] = package["version"]
            if "authors" in package:
                metadata["authors"] = package["authors"]
    except Exception as e:
        log_warning(f"Error reading Cargo.toml: {e}")


def validate_abi(abi: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate an ABI against the schema.

    Args:
        abi: The ABI to validate

    Returns:
        Tuple of (is_valid, messages)
    """
    # Load the schema
    schema_path = os.path.join(os.path.dirname(__file__), "abi_schema.json")

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Validate against schema
        jsonschema.validate(abi, schema)
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        return False, [f"Error: {e.message}"]
    except Exception as e:
        return False, [f"Error loading or validating schema: {str(e)}"]
