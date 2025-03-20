"""
Main ABI generation for NEAR Python contracts.
"""

import inspect
import os
from typing import Any, Callable, Dict, List, Optional, get_type_hints

from pydantic import TypeAdapter

from near_abi_py.core import (
    SCHEMA_VERSION,
    AbiFunctionKind,
    AbiFunctionModifier,
    FunctionDef,
    NearDecorator,
    create_root_schema,
)
from near_abi_py.utils import (
    extract_metadata,
    extract_project_metadata,
    get_function_decorators,
    get_function_docstring,
    load_module,
    log_error,
    log_info,
    log_success,
    log_warning,
)


def generate_abi(contract_file: str) -> Dict[str, Any]:
    """
    Generate ABI for a Python NEAR contract file.

    Args:
        contract_file: Path to the Python contract file

    Returns:
        ABI definition as a dictionary
    """
    # Create basic ABI structure
    abi: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "metadata": extract_metadata(contract_file),
        "body": {
            "functions": [],
            "root_schema": create_root_schema(),
        },
    }

    # Load the module
    module = load_module(contract_file)

    # Extract contract functions
    abi["body"]["functions"] = extract_functions(module)

    return abi


def generate_abi_from_files(file_paths: List[str], project_dir: str) -> Dict[str, Any]:
    """
    Generate ABI from multiple Python files.

    Args:
        file_paths: List of Python file paths to analyze
        project_dir: Root directory of the project

    Returns:
        ABI definition as a dictionary
    """
    # Create basic ABI structure
    abi: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "metadata": extract_project_metadata(project_dir),
        "body": {
            "functions": [],
            "root_schema": create_root_schema(),
        },
    }

    # Process each file and collect functions
    all_functions = []

    for file_path in file_paths:
        try:
            module = load_module(file_path)
            functions = extract_functions(module)

            if functions:
                all_functions.extend(functions)
                rel_path = os.path.relpath(file_path, project_dir)
                log_success(f"{rel_path}: Found {len(functions)} contract function(s)")
            else:
                rel_path = os.path.relpath(file_path, project_dir)
                log_info(f"{rel_path}: No contract functions found")
        except Exception as e:
            rel_path = os.path.relpath(file_path, project_dir)
            log_error(f"{rel_path}: Error: {str(e)}")

    # Add functions to ABI
    abi["body"]["functions"] = all_functions

    # Add source files to metadata
    abi["metadata"]["sources"] = [os.path.relpath(f, project_dir) for f in file_paths]

    return abi


def extract_functions(module: Any) -> List[Dict[str, Any]]:
    """
    Extract contract functions from a module.

    Args:
        module: Python module object

    Returns:
        List of function definitions for ABI
    """
    functions = []

    # Find all contract functions in the module
    for name, obj in inspect.getmembers(module):
        # Skip private members
        if name.startswith("_"):
            continue

        # For classes, check methods for contract functions
        if inspect.isclass(obj):
            for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                if method_name.startswith("_"):
                    continue

                # Analyze the method
                func_def = analyze_function(method)
                if func_def:
                    functions.append(func_def.to_dict())

        # For top-level functions, check for contract functions
        elif inspect.isfunction(obj):
            # Analyze the function
            func_def = analyze_function(obj)
            if func_def:
                functions.append(func_def.to_dict())

    return functions


def analyze_function(func: Callable) -> Optional[FunctionDef]:
    """
    Analyze a function and extract its ABI definition.

    Args:
        func: Function to analyze

    Returns:
        FunctionDef or None if not a contract function
    """
    # Get decorators
    decorators = get_function_decorators(func)

    if not decorators:
        return None

    # Determine function kind and modifiers
    is_view = NearDecorator.VIEW in decorators
    is_init = NearDecorator.INIT in decorators
    is_private = (
        NearDecorator.PRIVATE in decorators or NearDecorator.CALLBACK in decorators
    )
    is_payable = NearDecorator.PAYABLE in decorators

    # Create function definition
    func_def = FunctionDef(
        name=func.__name__,
        kind=AbiFunctionKind.VIEW if is_view else AbiFunctionKind.CALL,
    )

    # Add docstring
    func_def.doc = get_function_docstring(func)

    # Add modifiers
    if is_init:
        func_def.modifiers.append(AbiFunctionModifier.INIT)
    if is_private:
        func_def.modifiers.append(AbiFunctionModifier.PRIVATE)
    if is_payable:
        func_def.modifiers.append(AbiFunctionModifier.PAYABLE)

    # Process function signature
    process_function_signature(func, func_def)

    return func_def


def process_function_signature(func: Callable, func_def: FunctionDef) -> None:
    """
    Process function signature to extract parameters and return type.

    Args:
        func: Function to process
        func_def: FunctionDef to update
    """
    # Get signature
    sig = inspect.signature(func)

    # Skip 'self' parameter for methods
    params = []
    filtered_params = {
        name: param for name, param in sig.parameters.items() if name != "self"
    }

    if filtered_params:
        # Get type hints
        try:
            type_hints = get_type_hints(func)
        except Exception:
            type_hints = {}

        # Process parameters
        for name, param in filtered_params.items():
            # Get type annotation
            param_type = type_hints.get(name, Any)

            # Create JSON schema for the parameter
            param_schema = create_schema_for_type(param_type)

            # Add to parameters list
            params.append(
                {
                    "name": name,
                    "type_schema": param_schema,
                }
            )

        # Create params section if we have parameters
        if params:
            func_def.params = {
                "serialization_type": "json",
                "args": params,
            }

    # Handle return type
    return_annotation = sig.return_annotation
    if return_annotation is not inspect.Signature.empty:
        # Create schema for return type
        return_schema = create_schema_for_type(return_annotation)

        if return_schema:
            func_def.result = {
                "serialization_type": "json",
                "type_schema": return_schema,
            }


def create_schema_for_type(type_annotation: Any) -> Dict[str, Any]:
    """
    Create a JSON schema for a type annotation using Pydantic.

    Args:
        type_annotation: Python type annotation

    Returns:
        JSON schema for the type
    """
    try:
        # Use Pydantic's TypeAdapter to generate schema
        adapter = TypeAdapter(type_annotation)
        schema = adapter.json_schema()

        # Clean up the schema - remove unnecessary fields
        if "title" in schema and schema["title"] == "type_annotation":
            del schema["title"]

        return schema
    except Exception as e:
        # Fallback for types Pydantic can't handle
        log_warning(f"Could not generate schema for {type_annotation}: {e}")
        return {"type": "object"}
