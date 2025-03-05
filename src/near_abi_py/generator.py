"""
Simplified ABI generation for NEAR Python contracts.

This module analyzes Python contract files and generates ABI definitions
using the metaschema.
"""

import ast
import platform
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import (
    AbiFunctionKind,
    AbiFunctionModifier,
    AbiSerializationType,
    create_abi_skeleton,
)


def generate_abi(
    contract_file: str, package_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate ABI for a Python NEAR contract

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


def parse_contract_file(file_path: str) -> ast.Module:
    """
    Parse a Python file into an AST

    Args:
        file_path: Path to the Python file

    Returns:
        AST module node
    """
    with open(file_path, "r") as f:
        code = f.read()

    return ast.parse(code)


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
    # This could be enhanced to read from pyproject.toml or setup.py

    return metadata


def extract_functions(module_ast: ast.Module) -> List[Dict[str, Any]]:
    """
    Extract contract functions from an AST

    Args:
        module_ast: AST module node

    Returns:
        List of function definitions
    """
    functions = []

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

            # Skip if not a NEAR decorator
            if decorator_name not in ["view", "call", "init"]:
                continue

            # Process decorator type
            if decorator_name == "view":
                is_view = True
            elif decorator_name == "call":
                is_call = True
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
                        "type_schema": extract_type_schema(param.annotation),
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
                "type_schema": extract_type_schema(node.returns),
            }

        functions.append(func_def)

    # Visit all nodes in the AST
    for node in ast.walk(module_ast):
        visit_function(node)

    return functions


def extract_type_schema(type_annotation: Optional[ast.expr]) -> Dict[str, Any]:
    """
    Extract JSON Schema from type annotation

    Args:
        type_annotation: AST node for type annotation

    Returns:
        JSON Schema representation of the type
    """
    if type_annotation is None:
        return {"type": "object"}

    # Handle basic types
    if isinstance(type_annotation, ast.Name):
        type_name = type_annotation.id

        # Map Python types to JSON Schema
        type_map = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array"},
            "dict": {"type": "object"},
            "None": {"type": "null"},
        }

        return type_map.get(type_name, {"type": "object"})

    # For more complex types, use a generic schema
    # This is simplified - a full implementation would handle generics,
    # unions, etc. by parsing the AST more completely
    return {"type": "object"}
