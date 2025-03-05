"""
Type conversion utilities for NEAR Python ABI Builder.

This module handles conversion of Python type annotations to JSON Schema.
"""

from typing import Any, Dict, Union
import typing


def python_type_to_json_schema(type_annotation: Any) -> Dict[str, Any]:
    """
    Convert Python type annotations to JSON Schema

    Args:
        type_annotation: Python type object or annotation

    Returns:
        JSON Schema representation of the type
    """
    # Handle None type (null in JSON Schema)
    if type_annotation is None or type_annotation is type(None):
        return {"type": "null"}

    # Handle basic types
    if isinstance(type_annotation, type):
        if type_annotation is str:
            return {"type": "string"}
        elif type_annotation is int:
            return {"type": "integer"}
        elif type_annotation is float:
            return {"type": "number"}
        elif type_annotation is bool:
            return {"type": "boolean"}
        elif type_annotation is list:
            return {"type": "array", "items": {}}
        elif type_annotation is dict:
            return {"type": "object"}

    # Handle typing.Any or any unknown type
    if type_annotation is Any:
        return {}  # Empty schema accepts anything

    # Handle lists, sequences, and arrays
    origin = getattr(type_annotation, "__origin__", None)
    if origin in (list, typing.List):
        item_type = Any
        if hasattr(type_annotation, "__args__") and type_annotation.__args__:
            item_type = type_annotation.__args__[0]
        return {"type": "array", "items": python_type_to_json_schema(item_type)}

    # Handle dictionaries
    if origin in (dict, typing.Dict):
        # Default schema for generic dict
        schema: Dict[str, Any] = {"type": "object"}

        # If we have key and value types in the annotation
        if hasattr(type_annotation, "__args__") and len(type_annotation.__args__) == 2:
            key_type, value_type = type_annotation.__args__

            # In JSON Schema, keys are always strings, so we only care if it's a string annotation
            if key_type is str:
                schema["additionalProperties"] = python_type_to_json_schema(value_type)

        return schema

    # Handle Union types (including Optional)
    if origin in (Union, typing.Union):
        # Extract the types in the union
        union_types = type_annotation.__args__

        # Handle Optional[T] which is Union[T, None]
        none_type = type(None)
        if none_type in union_types:
            # Remove None and make the field nullable
            remaining_types = [t for t in union_types if t is not none_type]
            if len(remaining_types) == 1:
                schema = python_type_to_json_schema(remaining_types[0])
                schema["nullable"] = True
                return schema

        # Handle regular Union with multiple types
        return {"anyOf": [python_type_to_json_schema(t) for t in union_types]}

    # Handle literal types
    if origin is typing.Literal:
        literal_values = type_annotation.__args__
        return {"enum": list(literal_values)}

    # Try to handle custom classes as objects
    if hasattr(type_annotation, "__annotations__"):
        properties = {}
        required = []

        for field_name, field_type in type_annotation.__annotations__.items():
            properties[field_name] = python_type_to_json_schema(field_type)
            required.append(field_name)

        return {"type": "object", "properties": properties, "required": required}

    # Default to object for any other type
    return {"type": "object"}


def get_near_type_schema(near_type: str) -> Dict[str, Any]:
    """
    Get JSON Schema for NEAR-specific types

    Args:
        near_type: NEAR type name (e.g. 'AccountId', 'Balance')

    Returns:
        JSON Schema reference to the type
    """
    # Map of NEAR types to their schema references
    near_types = {
        "AccountId": "AccountId",
        "Balance": "Balance",
        "Gas": "Gas",
        "PublicKey": "PublicKey",
        "Timestamp": "Timestamp",
        "BlockHeight": "BlockHeight",
        "StorageUsage": "StorageUsage",
        "U128": "U128",
        "U64": "U64",
        "Promise": "Promise",
    }

    if near_type in near_types:
        return {"$ref": f"#/definitions/{near_types[near_type]}"}

    # If not a known NEAR type, return unknown
    return {"type": "object"}
