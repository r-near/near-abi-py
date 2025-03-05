"""
Schema definitions for NEAR Python ABI.

This module loads the NEAR ABI metaschema and provides validation functionality.
"""

import json
import os
from enum import Enum
from typing import Any, Dict, List

import jsonschema


# Get ABI metaschema from included file
def _load_metaschema() -> Dict[str, Any]:
    """Load the NEAR ABI metaschema from the package data"""
    schema_path = os.path.join(os.path.dirname(__file__), "abi_schema.json")
    with open(schema_path, "r") as f:
        return json.load(f)


ABI_METASCHEMA = _load_metaschema()


# Current schema version
SCHEMA_VERSION = "0.4.0"


# Enums for ABI components
class AbiFunctionKind(str, Enum):
    """Function kinds in ABI"""

    VIEW = "view"
    CALL = "call"


class AbiFunctionModifier(str, Enum):
    """Function modifiers in ABI"""

    PRIVATE = "private"
    PAYABLE = "payable"
    INIT = "init"


class AbiSerializationType(str, Enum):
    """Serialization types in ABI"""

    JSON = "json"
    BORSH = "borsh"


def validate_abi(abi: Dict[str, Any]) -> List[str]:
    """
    Validate an ABI against the metaschema

    Args:
        abi: The ABI to validate

    Returns:
        List of validation error messages, empty if valid
    """
    messages = []

    # Basic schema validation
    try:
        jsonschema.validate(abi, ABI_METASCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        # Get the specific validation error
        messages.append(f"Error: {e.message}")
        return messages

    # Additional custom validations

    # Check schema version
    if abi.get("schema_version") != SCHEMA_VERSION:
        messages.append(
            f"Warning: ABI schema version mismatch. Expected {SCHEMA_VERSION}"
        )

    # Check for functions
    body = abi.get("body", {})
    functions = body.get("functions", [])

    if not functions:
        messages.append("Warning: No functions defined in the ABI")

    # Check for duplicate function names
    function_names = set()
    for func in functions:
        name = func.get("name")
        if name in function_names:
            messages.append(f"Error: Duplicate function name '{name}'")
        function_names.add(name)

    return messages


def create_abi_skeleton() -> Dict[str, Any]:
    """
    Create a skeleton ABI structure

    Returns:
        Dictionary with basic ABI structure
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "name": "",
            "version": "",
            "authors": [],
            "build": {"compiler": "", "builder": ""},
        },
        "body": {"functions": [], "root_schema": create_root_schema()},
    }


def create_root_schema() -> Dict[str, Any]:
    """
    Create a root schema with common NEAR types

    Returns:
        Dictionary with JSON Schema for common NEAR types
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NEAR Contract Schema",
        "definitions": {
            "AccountId": {"type": "string", "description": "NEAR account identifier"},
            "Balance": {
                "type": "string",
                "description": "Balance value in yoctoNEAR (10^-24 NEAR)",
                "pattern": "^[0-9]+$",
            },
            "Gas": {
                "type": "integer",
                "description": "Gas units for NEAR VM operations",
                "minimum": 0,
            },
            "PublicKey": {
                "type": "string",
                "description": "Public key in base58 or base64 format",
            },
            "Timestamp": {
                "type": "integer",
                "description": "Timestamp in nanoseconds",
                "minimum": 0,
            },
            "BlockHeight": {
                "type": "integer",
                "description": "Block height on the NEAR blockchain",
                "minimum": 0,
            },
            "StorageUsage": {
                "type": "integer",
                "description": "Storage usage in bytes",
                "minimum": 0,
            },
            "U128": {
                "type": "string",
                "description": "128-bit unsigned integer in decimal string representation",
                "pattern": "^[0-9]+$",
            },
            "U64": {
                "type": "integer",
                "description": "64-bit unsigned integer",
                "minimum": 0,
            },
            "Promise": {
                "type": "object",
                "description": "NEAR Promise for async cross-contract calls",
            },
        },
    }
