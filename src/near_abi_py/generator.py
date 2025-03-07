"""
ABI generation for NEAR Python contracts.

This module analyzes Python contract files and generates ABI definitions
using the metaschema, with support for multi-file projects.
"""

import ast
import platform
import importlib
import importlib.metadata
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import (
    AbiFunctionKind,
    AbiFunctionModifier,
    AbiSerializationType,
    create_abi_skeleton,
)

from .type_analyzer import scan_module_for_types, extract_type_schema


def generate_abi(
    contract_file: str, package_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate ABI for a Python NEAR contract file

    Args:
        contract_file: Path to the Python contract file
        package_path: Path to the package information (setup.py or pyproject.toml)

    Returns:
        ABI definition as a dictionary
    """
    # Create the basic ABI structure
    abi = create_abi_skeleton()

    # Parse the contract file
    contract_ast = parse_contract_file(contract_file)

    # Extract metadata from package info
    abi["metadata"] = extract_metadata(package_path or contract_file)

    # Extract functions from the AST
    abi["body"]["functions"] = extract_functions(contract_ast)

    return abi


def generate_abi_from_files(file_paths: List[str], project_dir: str) -> Dict[str, Any]:
    """
    Generate ABI from multiple Python files in a project directory

    Args:
        file_paths: List of Python file paths to analyze
        project_dir: Root directory of the project

    Returns:
        ABI definition as a dictionary
    """
    # Create the basic ABI structure
    abi = create_abi_skeleton()

    # Extract metadata from project directory
    abi["metadata"] = extract_project_metadata(project_dir)

    # Track all functions found across files
    all_functions = []

    # Process each file
    console_output = []
    console_output.append(f"Processing {len(file_paths)} Python files:")

    for file_path in file_paths:
        rel_path = os.path.relpath(file_path, project_dir)
        try:
            # Parse the contract file
            file_ast = parse_contract_file(file_path)

            # Extract functions from the AST
            functions = extract_functions(file_ast)

            if functions:
                # If functions found, add to our collection
                all_functions.extend(functions)
                console_output.append(
                    f"  ✓ {rel_path}: Found {len(functions)} contract function(s)"
                )
            else:
                console_output.append(f"  - {rel_path}: No contract functions found")

        except Exception as e:
            console_output.append(f"  × {rel_path}: Error: {str(e)}")

    # Print processing summary
    for line in console_output:
        print(line)

    # Add combined functions to ABI
    abi["body"]["functions"] = all_functions

    # Add source information to metadata
    abi["metadata"]["sources"] = [os.path.relpath(f, project_dir) for f in file_paths]

    return abi


def parse_contract_file(file_path: str) -> ast.Module:
    """
    Parse a Python file into an AST

    Args:
        file_path: Path to the Python file

    Returns:
        AST module node
    """
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    return ast.parse(code, filename=file_path)


def extract_metadata(package_path: str) -> Dict[str, Any]:
    """
    Extract metadata from package information

    Args:
        package_path: Path to the package directory or file

    Returns:
        Metadata dictionary
    """
    # Try to determine SDK version
    try:
        near_sdk_version = importlib.metadata.version("near-sdk-py")
    except importlib.metadata.PackageNotFoundError:
        near_sdk_version = "unknown"

    # Basic metadata with defaults
    metadata = {
        "name": Path(package_path).stem,
        "version": "0.1.0",
        "authors": ["Unknown"],
        "build": {
            "compiler": f"python {platform.python_version()}",
            "builder": f"near-sdk-py {near_sdk_version}",
        },
    }

    # Try to extract more information from package files
    pyproject_path = find_project_file(package_path, "pyproject.toml")
    if pyproject_path:
        # Extract info from pyproject.toml if available
        try:
            import tomllib

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
        except (ImportError, Exception):
            # Fallback to simple metadata if tomli is not available
            pass

    return metadata


def extract_project_metadata(project_dir: str) -> Dict[str, Any]:
    """
    Extract metadata from a project directory

    Args:
        project_dir: Path to the project directory

    Returns:
        Metadata dictionary
    """
    # First, try to find pyproject.toml or setup.py
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    setup_path = os.path.join(project_dir, "setup.py")

    if os.path.exists(pyproject_path):
        return extract_metadata(pyproject_path)
    elif os.path.exists(setup_path):
        return extract_metadata(setup_path)
    else:
        # If no project files found, use directory name as project name
        return extract_metadata(project_dir)


def find_project_file(start_path: str, filename: str) -> Optional[str]:
    """
    Find a project file by searching upwards from start_path

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


def extract_functions(module_ast: ast.Module) -> List[Dict[str, Any]]:
    """
    Extract contract functions from an AST

    Args:
        module_ast: AST module node

    Returns:
        List of function definitions
    """
    functions = []

    # First, scan the module for custom types
    type_registry = scan_module_for_types(module_ast)

    # Helper function to get the docstring
    def get_docstring(node):
        docstring = ast.get_docstring(node)
        return docstring.strip() if docstring else ""

    # Helper function to find functions with NEAR decorators
    def visit_function(node):
        if not isinstance(node, ast.FunctionDef):
            return

        # Check for NEAR decorators
        is_view = False
        is_call = False
        is_init = False
        modifiers = []

        for decorator in node.decorator_list:
            decorator_name = None

            # Extract decorator name
            if isinstance(decorator, ast.Name):
                decorator_name = decorator.id
            elif isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                decorator_name = decorator.func.id
            elif isinstance(decorator, ast.Attribute) and isinstance(
                decorator.value, ast.Name
            ):
                # Handle cases like "@near.view"
                if decorator.value.id in ["near"]:
                    decorator_name = decorator.attr

            # Skip if not a NEAR decorator
            if decorator_name not in ["view", "call", "init", "callback"]:
                continue

            # Process decorator type
            if decorator_name == "view":
                is_view = True
            elif decorator_name == "call":
                is_call = True
            elif decorator_name == "callback":
                is_call = True
                modifiers.append(AbiFunctionModifier.PRIVATE)
            elif decorator_name == "init":
                is_init = True
                modifiers.append(AbiFunctionModifier.INIT)

        # Skip if not a contract method
        if not (is_view or is_call or is_init):
            return

        # Create function definition
        func_def = {
            "name": node.name,
            "kind": AbiFunctionKind.VIEW if is_view else AbiFunctionKind.CALL,
        }

        # Add modifiers if any
        if modifiers:
            func_def["modifiers"] = modifiers

        # Extract parameters if any
        if node.args.args and len(node.args.args) > 0:
            # Skip 'self' parameter for methods
            params = [arg for arg in node.args.args if arg.arg != "self"]

            if params:
                param_defs = []

                for param in params:
                    param_def = {
                        "name": param.arg,
                        "type_schema": extract_type_schema(
                            param.annotation, type_registry
                        ),
                    }
                    param_defs.append(param_def)

                func_def["params"] = {
                    "serialization_type": AbiSerializationType.JSON,
                    "args": param_defs,
                }

        # Extract return type if any
        if node.returns:
            func_def["result"] = {
                "serialization_type": AbiSerializationType.JSON,
                "type_schema": extract_type_schema(node.returns, type_registry),
            }

        functions.append(func_def)

    # Visit all classes in the AST first (contract classes)
    for node in ast.iter_child_nodes(module_ast):
        if isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                visit_function(child)

    # Then visit top-level functions (might be decorated contract functions)
    for node in ast.iter_child_nodes(module_ast):
        visit_function(node)

    return functions
