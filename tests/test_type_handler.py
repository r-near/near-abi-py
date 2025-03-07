"""
Tests for the complex type analyzer.

This module contains pytest tests to verify that the type analyzer correctly
handles complex Python types including TypedDict, NamedTuple, Enum, etc.
"""

import ast

from near_abi_py.type_analyzer import (
    TypeRegistry,
    scan_module_for_types,
    extract_type_schema,
    extract_typed_dict_schema,
    extract_named_tuple_schema,
    extract_enum_schema,
    extract_dataclass_schema,
    is_optional_type,
    should_be_required,
)


def parse_code(code: str) -> ast.Module:
    """Parse Python code string into an AST."""
    return ast.parse(code)


def test_is_optional_type():
    """Test that Optional type detection works correctly."""
    # Test with Optional[str]
    code = "Optional[str]"
    node = ast.parse(code, mode="eval").body
    assert is_optional_type(node) is True

    # Test with Union[str, None]
    code = "Union[str, None]"
    node = ast.parse(code, mode="eval").body
    assert is_optional_type(node) is True

    # Test with non-optional type
    code = "str"
    node = ast.parse(code, mode="eval").body
    assert is_optional_type(node) is False

    # Test with Union that doesn't include None
    code = "Union[str, int]"
    node = ast.parse(code, mode="eval").body
    assert is_optional_type(node) is False


def test_should_be_required():
    """Test the should_be_required function."""
    # Test with regular type, no default
    code = "str"
    node = ast.parse(code, mode="eval").body
    assert should_be_required(node, False) is True

    # Test with regular type, with default
    code = "str"
    node = ast.parse(code, mode="eval").body
    assert should_be_required(node, True) is False

    # Test with Optional type, no default
    code = "Optional[str]"
    node = ast.parse(code, mode="eval").body
    assert should_be_required(node, False) is False

    # Test with Optional type, with default
    code = "Optional[str]"
    node = ast.parse(code, mode="eval").body
    assert should_be_required(node, True) is False


def test_extract_basic_type_schemas():
    """Test extraction of basic type schemas."""
    registry = TypeRegistry()

    # Test string type
    code = "str"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "string"}

    # Test integer type
    code = "int"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "integer"}

    # Test float type
    code = "float"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "number"}

    # Test boolean type
    code = "bool"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "boolean"}

    # Test None type
    code = "None"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "null"}


def test_extract_container_type_schemas():
    """Test extraction of container type schemas."""
    registry = TypeRegistry()

    # Test List[str]
    code = "List[str]"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "array", "items": {"type": "string"}}

    # Test Dict[str, int]
    code = "Dict[str, int]"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": "object", "additionalProperties": {"type": "integer"}}

    # Test Optional[List[str]]
    code = "Optional[List[str]]"
    node = ast.parse(code, mode="eval").body
    schema = extract_type_schema(node, registry)
    assert schema == {"type": ["array", "null"], "items": {"type": "string"}}


def test_extract_typed_dict():
    """Test extraction of TypedDict schemas."""
    # Regular TypedDict with required fields
    code = """
from typing import TypedDict, Optional

class UserProfile(TypedDict):
    name: str
    age: int
    email: Optional[str]
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "UserProfile":
            class_node = node
            break

    assert class_node is not None
    schema = extract_typed_dict_schema(class_node, registry)

    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "email" in schema["properties"]
    assert schema["properties"]["email"]["type"] == ["string", "null"]
    assert "required" in schema
    assert "name" in schema["required"]
    assert "age" in schema["required"]
    assert "email" not in schema["required"]

    # TypedDict with total=False
    code = """
from typing import TypedDict

class PartialUser(TypedDict, total=False):
    name: str
    age: int
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "PartialUser":
            class_node = node
            break

    assert class_node is not None
    schema = extract_typed_dict_schema(class_node, registry)

    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "required" not in schema or len(schema["required"]) == 0


def test_extract_named_tuple():
    """Test extraction of NamedTuple schemas."""
    # NamedTuple with required and optional fields
    code = """
from typing import NamedTuple, Optional, List

class Person(NamedTuple):
    name: str
    age: int
    email: Optional[str] = None
    tags: List[str] = []
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "Person":
            class_node = node
            break

    assert class_node is not None
    schema = extract_named_tuple_schema(class_node, registry)

    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "email" in schema["properties"]
    assert "tags" in schema["properties"]
    assert schema["properties"]["email"]["type"] == ["string", "null"]
    assert "required" in schema
    assert "name" in schema["required"]
    assert "age" in schema["required"]
    assert "email" not in schema["required"]
    assert "tags" not in schema["required"]


def test_extract_enum():
    """Test extraction of Enum schemas."""
    # String Enum
    code = """
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "Status":
            class_node = node
            break

    assert class_node is not None
    schema = extract_enum_schema(class_node, registry)

    assert schema["type"] == "string"
    assert "enum" in schema
    assert "pending" in schema["enum"]
    assert "active" in schema["enum"]
    assert "disabled" in schema["enum"]

    # Integer Enum
    code = """
from enum import IntEnum

class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "Priority":
            class_node = node
            break

    assert class_node is not None
    schema = extract_enum_schema(class_node, registry)

    assert schema["type"] == "integer"
    assert "enum" in schema
    assert 1 in schema["enum"]
    assert 2 in schema["enum"]
    assert 3 in schema["enum"]


def test_extract_dataclass():
    """Test extraction of dataclass schemas."""
    code = """
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Config:
    name: str
    timeout: int = 30
    retries: int = 3
    tags: Optional[List[str]] = None
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "Config":
            class_node = node
            break

    assert class_node is not None
    schema = extract_dataclass_schema(class_node, registry)

    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "timeout" in schema["properties"]
    assert "retries" in schema["properties"]
    assert "tags" in schema["properties"]
    assert "required" in schema
    assert "name" in schema["required"]
    assert "timeout" not in schema["required"]
    assert "retries" not in schema["required"]
    assert "tags" not in schema["required"]


def test_nested_type_schemas():
    """Test extraction of complex nested type schemas."""
    code = """
from typing import Dict, List, Optional, TypedDict, NamedTuple
from enum import Enum
from dataclasses import dataclass

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Address(TypedDict):
    street: str
    city: str
    zip: str

class Contact(NamedTuple):
    email: str
    phone: Optional[str] = None

@dataclass
class User:
    id: str
    name: str
    status: Status
    address: Address
    contacts: List[Contact]
    settings: Optional[Dict[str, str]] = None
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    # Get the User dataclass
    user_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "User":
            user_node = node
            break

    assert user_node is not None
    schema = extract_dataclass_schema(user_node, registry)

    # Check top-level properties
    assert schema["type"] == "object"
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "status" in schema["properties"]
    assert "address" in schema["properties"]
    assert "contacts" in schema["properties"]
    assert "settings" in schema["properties"]

    # Check nested types
    # Status enum
    status_schema = schema["properties"]["status"]
    assert status_schema["type"] == "string"
    assert "enum" in status_schema
    assert "active" in status_schema["enum"]
    assert "inactive" in status_schema["enum"]

    # Address TypedDict
    address_schema = schema["properties"]["address"]
    assert address_schema["type"] == "object"
    assert "street" in address_schema["properties"]
    assert "city" in address_schema["properties"]
    assert "zip" in address_schema["properties"]

    # Contacts List[Contact]
    contacts_schema = schema["properties"]["contacts"]
    assert contacts_schema["type"] == "array"
    contact_schema = contacts_schema["items"]
    assert contact_schema["type"] == "object"
    assert "email" in contact_schema["properties"]
    assert "phone" in contact_schema["properties"]
    assert contact_schema["properties"]["phone"]["type"] == ["string", "null"]

    # Settings Optional[Dict[str, str]]
    settings_schema = schema["properties"]["settings"]
    assert settings_schema["type"] == ["object", "null"]
    assert "additionalProperties" in settings_schema
    assert settings_schema["additionalProperties"]["type"] == "string"

    # Check required fields
    assert "required" in schema
    assert "id" in schema["required"]
    assert "name" in schema["required"]
    assert "status" in schema["required"]
    assert "address" in schema["required"]
    assert "contacts" in schema["required"]
    assert "settings" not in schema["required"]


def test_function_parameter_extraction():
    """Test extraction of function parameter types."""
    code = """
from typing import Dict, List, Optional, Union, Literal
from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

def process_data(
    user_id: str,
    status: Status,
    tags: List[str],
    options: Optional[Dict[str, str]] = None,
    mode: Literal["fast", "accurate"] = "fast",
    limit: Union[int, None] = None
) -> Dict[str, Any]:
    pass
"""
    module = parse_code(code)
    registry = scan_module_for_types(module)

    # Get the function node
    func_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.FunctionDef) and node.name == "process_data":
            func_node = node
            break

    assert func_node is not None

    # Parse parameter types
    params = {}
    for arg in func_node.args.args:
        if arg.annotation:
            params[arg.arg] = extract_type_schema(arg.annotation, registry)

    # Check parameter schemas
    assert "user_id" in params
    assert params["user_id"]["type"] == "string"

    assert "status" in params
    assert params["status"]["type"] == "string"
    assert "enum" in params["status"]
    assert "active" in params["status"]["enum"]

    assert "tags" in params
    assert params["tags"]["type"] == "array"
    assert params["tags"]["items"]["type"] == "string"

    assert "options" in params
    assert params["options"]["type"] == ["object", "null"]

    assert "mode" in params
    assert "enum" in params["mode"]
    assert "fast" in params["mode"]["enum"]
    assert "accurate" in params["mode"]["enum"]

    assert "limit" in params
    assert params["limit"] == {"anyOf": [{"type": "integer"}, {"type": "null"}]}
