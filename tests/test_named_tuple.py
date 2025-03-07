"""
Focused test for NamedTuple with optional fields.

This test specifically checks the issue we fixed - making sure that
fields with Optional type or default values aren't marked as required.
"""

import ast

from near_abi_py.type_analyzer import (
    scan_module_for_types,
    extract_named_tuple_schema,
    should_be_required,
)


def test_namedtuple_optional_field_not_required():
    """Test that optional fields in a NamedTuple are not marked as required."""
    # Test with a NamedTuple containing various combinations of optional fields
    code = """
from typing import NamedTuple, Optional, List

class Point(NamedTuple):
    x: float                      # Required - no default, not Optional
    y: float                      # Required - no default, not Optional
    label: Optional[str] = None   # Not required - has default AND is Optional
    color: str = "black"          # Not required - has default
    tags: Optional[List[str]]     # Not required - is Optional but no default
"""
    module = ast.parse(code)
    registry = scan_module_for_types(module)

    class_node = None
    for node in ast.iter_child_nodes(module):
        if isinstance(node, ast.ClassDef) and node.name == "Point":
            class_node = node
            break

    assert class_node is not None
    schema = extract_named_tuple_schema(class_node, registry)

    # Check the schema properties
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "x" in schema["properties"]
    assert "y" in schema["properties"]
    assert "label" in schema["properties"]
    assert "color" in schema["properties"]
    assert "tags" in schema["properties"]

    # Check the type of label and tags fields
    assert schema["properties"]["label"]["type"] == ["string", "null"]
    assert schema["properties"]["tags"]["type"] == ["array", "null"]

    # Check required fields
    assert "required" in schema
    assert "x" in schema["required"]
    assert "y" in schema["required"]

    # Check that the optional fields are NOT required
    assert "label" not in schema["required"]
    assert "color" not in schema["required"]
    assert "tags" not in schema["required"]

    # Also test each field individually with should_be_required
    for field_name, annotation, has_default in [
        ("x", "float", False),  # Should be required
        ("y", "float", False),  # Should be required
        ("label", "Optional[str]", True),  # Should NOT be required (Optional + default)
        ("color", "str", True),  # Should NOT be required (has default)
        ("tags", "Optional[List[str]]", False),  # Should NOT be required (Optional)
    ]:
        # Parse the type annotation
        type_node = ast.parse(annotation, mode="eval").body
        # Check if it should be required
        required = should_be_required(type_node, has_default)

        if field_name in ["x", "y"]:
            assert required, f"Field {field_name} should be required"
        else:
            assert not required, f"Field {field_name} should NOT be required"
