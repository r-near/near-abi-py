"""
Enhanced AST-based type analysis for NEAR Python ABI Builder.

This module provides functions to analyze Python type annotations
using only AST (Abstract Syntax Tree) without runtime imports,
supporting a wide range of Python types including TypedDict,
NamedTuple, Enums, and more.
"""

import ast
from typing import Any, Dict, Optional


class TypeRegistry:
    """Registry of user-defined types found in the AST."""

    def __init__(self) -> None:
        self.types: Dict[str, ast.ClassDef] = {}
        self.imports: Dict[
            str, str
        ] = {}  # Maps imported names to their original module paths

    def register_type(self, name: str, node: ast.ClassDef) -> None:
        """Register a user-defined type."""
        self.types[name] = node

    def register_import(self, name: str, module_path: str) -> None:
        """Register an imported name and its origin."""
        self.imports[name] = module_path

    def get_type(self, name: str) -> Optional[ast.ClassDef]:
        """Get a user-defined type by name."""
        return self.types.get(name)

    def has_type(self, name: str) -> bool:
        """Check if a type is registered."""
        return name in self.types

    def get_import(self, name: str) -> Optional[str]:
        """Get the original module path for an imported name."""
        return self.imports.get(name)


def scan_module_for_types(module_ast: ast.Module) -> TypeRegistry:
    """
    Scan a module AST for user-defined types and imports.

    Args:
        module_ast: The module AST to scan

    Returns:
        A TypeRegistry containing found types and imports
    """
    registry = TypeRegistry()

    for node in ast.iter_child_nodes(module_ast):
        # Look for class definitions
        if isinstance(node, ast.ClassDef):
            # Register all classes by name
            registry.register_type(node.name, node)

        # Track imports for type resolution
        elif isinstance(node, ast.Import):
            for name in node.names:
                if name.asname:
                    # Import x as y
                    registry.register_import(name.asname, name.name)
                else:
                    # Simple import x
                    registry.register_import(name.name, name.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                if name.asname:
                    # from x import y as z
                    registry.register_import(name.asname, f"{module}.{name.name}")
                else:
                    # from x import y
                    registry.register_import(name.name, f"{module}.{name.name}")

    return registry


def is_typed_dict_class(class_node: ast.ClassDef) -> bool:
    """
    Check if a class is a TypedDict.

    Args:
        class_node: The class AST node

    Returns:
        True if the class is a TypedDict, False otherwise
    """
    # Check direct inheritance from TypedDict
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id == "TypedDict":
            return True

    # Check class decorators for @dataclass_transform() used in newer TypedDict implementations
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            if decorator.func.id == "dataclass_transform":
                return True

    return False


def is_named_tuple_class(class_node: ast.ClassDef) -> bool:
    """
    Check if a class is a NamedTuple.

    Args:
        class_node: The class AST node

    Returns:
        True if the class is a NamedTuple, False otherwise
    """
    # Check direct inheritance from NamedTuple
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id == "NamedTuple":
            return True

    # Check for the functional form with class decoration
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            if decorator.func.id == "namedtuple":
                return True

    return False


def is_enum_class(class_node: ast.ClassDef) -> bool:
    """
    Check if a class is an Enum.

    Args:
        class_node: The class AST node

    Returns:
        True if the class is an Enum, False otherwise
    """
    # Check inheritance from Enum
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in ["Enum", "IntEnum", "StrEnum"]:
            return True

    return False


def is_dataclass(class_node: ast.ClassDef) -> bool:
    """
    Check if a class is a dataclass.

    Args:
        class_node: The class AST node

    Returns:
        True if the class is a dataclass, False otherwise
    """
    # Check for @dataclass decorator
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return True
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            if decorator.func.id == "dataclass":
                return True

    return False


def extract_type_schema(
    type_node: Optional[ast.expr], registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Extract a JSON Schema from a type annotation AST node.

    Args:
        type_node: The type annotation AST node
        registry: The type registry containing user-defined types

    Returns:
        A JSON Schema representing the type
    """
    if type_node is None:
        return {"type": "object"}

    # Handle basic types (Name nodes)
    if isinstance(type_node, ast.Name):
        type_name = type_node.id

        # Check built-in types
        if type_name == "str":
            return {"type": "string"}
        elif type_name == "int":
            return {"type": "integer"}
        elif type_name == "float":
            return {"type": "number"}
        elif type_name == "bool":
            return {"type": "boolean"}
        elif type_name == "list":
            return {"type": "array"}
        elif type_name == "dict":
            return {"type": "object"}
        elif type_name == "None":
            return {"type": "null"}
        elif type_name == "Any":
            return {}  # Empty schema accepts anything

        # Check common NEAR types
        elif type_name in ["AccountId", "Balance", "Gas", "PublicKey", "Promise"]:
            return {"$ref": f"#/definitions/{type_name}"}

        # Check user-defined types
        elif registry.has_type(type_name):
            class_node = registry.get_type(type_name)
            if class_node:
                if is_typed_dict_class(class_node):
                    return extract_typed_dict_schema(class_node, registry)
                elif is_named_tuple_class(class_node):
                    return extract_named_tuple_schema(class_node, registry)
                elif is_enum_class(class_node):
                    return extract_enum_schema(class_node, registry)
                elif is_dataclass(class_node):
                    return extract_dataclass_schema(class_node, registry)

        # Default for unknown types
        return {"type": "object"}

    # Handle subscript types (e.g., List[str], Dict[str, int], etc.)
    elif isinstance(type_node, ast.Subscript):
        container_type = ""
        if isinstance(type_node.value, ast.Name):
            container_type = type_node.value.id

        # Handle List[T]
        if container_type in ["List", "list"]:
            item_type = extract_slice_value(type_node)
            item_schema = extract_type_schema(item_type, registry)
            return {"type": "array", "items": item_schema}

        # Handle Dict[K, V]
        elif container_type in ["Dict", "dict"]:
            # Get key and value types if available
            key_type, value_type = None, None

            # Different approaches based on Python version
            if isinstance(type_node.slice, ast.Tuple):
                if len(type_node.slice.elts) == 2:
                    key_type, value_type = type_node.slice.elts
            else:
                # Single value in slice (unusual but possible)
                value_type = type_node.slice

            # Create schema
            value_schema = (
                extract_type_schema(value_type, registry)
                if value_type
                else {"type": "object"}
            )
            return {"type": "object", "additionalProperties": value_schema}

        # Handle Optional[T]
        elif container_type == "Optional":
            inner_type = extract_slice_value(type_node)
            inner_schema = extract_type_schema(inner_type, registry)

            # Make the schema nullable according to JSON Schema best practices
            if "type" in inner_schema:
                if isinstance(inner_schema["type"], list):
                    if "null" not in inner_schema["type"]:
                        inner_schema["type"].append("null")
                else:
                    inner_schema["type"] = [inner_schema["type"], "null"]
            else:
                # For schemas without a type (like anyOf), use nullable
                inner_schema["nullable"] = True

            return inner_schema

        # Handle Union[T1, T2, ...]
        elif container_type == "Union":
            union_types = []
            if isinstance(type_node.slice, ast.Tuple):
                union_types = type_node.slice.elts

            # Create schema
            if union_types:
                return {
                    "anyOf": [extract_type_schema(t, registry) for t in union_types]
                }

        # Handle Literal[v1, v2, ...]
        elif container_type == "Literal":
            literals = []

            # Extract literal values based on Python version
            if isinstance(type_node.slice, ast.Tuple):
                for elt in type_node.slice.elts:
                    literals.append(extract_literal_value(elt))
            else:
                # Single value
                literals.append(extract_literal_value(type_node.slice))

            # Create schema
            if literals:
                return {"enum": literals}

        # Handle Tuple[T1, T2, ...]
        elif container_type in ["Tuple", "tuple"]:
            item_types = []

            # Extract tuple types based on Python version
            if isinstance(type_node.slice, ast.Tuple):
                item_types = type_node.slice.elts
            else:
                # Single value
                item_types = [type_node.slice]

            # If we have a single item with an ellipsis (Tuple[T, ...])
            if len(item_types) == 2 and isinstance(item_types[1], ast.Constant):
                # Homogeneous tuple, treat like an array
                item_schema = extract_type_schema(item_types[0], registry)
                return {"type": "array", "items": item_schema}

            # Create schema for heterogeneous tuple (fixed items)
            if item_types:
                return {
                    "type": "array",
                    "prefixItems": [
                        extract_type_schema(t, registry) for t in item_types
                    ],
                    "minItems": len(item_types),
                    "maxItems": len(item_types),
                }

    # Handle constant values (strings, numbers, etc.)
    elif isinstance(type_node, ast.Constant):
        if isinstance(type_node.value, str):
            return {"type": "string", "const": type_node.value}
        elif isinstance(type_node.value, (int, float)):
            return {"type": "number", "const": type_node.value}
        elif isinstance(type_node.value, bool):
            return {"type": "boolean", "const": type_node.value}
        elif type_node.value is None:
            return {"type": "null"}

    # Default for unknown or complex types
    return {"type": "object"}


def extract_slice_value(subscript_node: ast.Subscript) -> Optional[ast.expr]:
    """
    Extract the value(s) from a subscript's slice.
    Handles different Python versions' AST structures.

    Args:
        subscript_node: The subscript AST node

    Returns:
        The extracted type node from the slice
    """
    return subscript_node.slice


def extract_literal_value(node: ast.expr) -> Any:
    """
    Extract a literal value from an AST node.

    Args:
        node: The AST node

    Returns:
        The extracted value
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.NameConstant):
        return node.value
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # Handle negative numbers
        if isinstance(node.operand, ast.Constant):
            return -node.operand.value
        elif isinstance(node.operand, ast.Num):
            return -node.operand.n

    # Default for unknown nodes
    return None


def extract_typed_dict_schema(
    class_node: ast.ClassDef, registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Extract a JSON Schema from a TypedDict class definition.

    Args:
        class_node: The TypedDict class AST node
        registry: The type registry

    Returns:
        A JSON Schema representing the TypedDict
    """
    properties = {}
    required = []

    # Check for total=False keyword
    total = True
    for keyword in class_node.keywords:
        if keyword.arg == "total" and isinstance(keyword.value, ast.Constant):
            total = keyword.value.value

    # Extract class variables with annotations
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign):
            # This is a typed field like "name: str"
            if isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                field_type = stmt.annotation

                # Get schema for this field
                field_schema = extract_type_schema(field_type, registry)
                properties[field_name] = field_schema

                # Check if the field type is Optional
                is_optional = is_optional_type(field_type)

                # Only add to required if total=True (default) and not Optional
                if total and not is_optional:
                    required.append(field_name)

    # Create the schema
    schema = {"type": "object", "properties": properties}

    # Add required fields
    if required:
        schema["required"] = required

    return schema


def extract_named_tuple_schema(
    class_node: ast.ClassDef, registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Extract a JSON Schema from a NamedTuple class definition.

    Args:
        class_node: The NamedTuple class AST node
        registry: The type registry

    Returns:
        A JSON Schema representing the NamedTuple
    """
    properties = {}
    required = []

    # Extract class variables with annotations
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                field_type = stmt.annotation

                # Get schema for this field
                field_schema = extract_type_schema(field_type, registry)
                properties[field_name] = field_schema

                # Check if it should be required
                has_default = stmt.value is not None
                if should_be_required(field_type, has_default):
                    required.append(field_name)

    # Check for the functional form with field definitions as arguments
    if not properties:
        for decorator in class_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                if decorator.func.id == "namedtuple":
                    # Extract field names from the second argument if it's a list/tuple
                    if len(decorator.args) >= 2:
                        fields_arg = decorator.args[1]
                        if isinstance(fields_arg, (ast.List, ast.Tuple)):
                            for i, elt in enumerate(fields_arg.elts):
                                if isinstance(elt, ast.Str):
                                    # Simple field without type annotation
                                    field_name = elt.s
                                    properties[field_name] = {"type": "object"}
                                    required.append(field_name)

    # Create the schema
    schema = {"type": "object", "properties": properties}

    # Add required fields
    if required:
        schema["required"] = required

    return schema


def extract_enum_schema(
    class_node: ast.ClassDef, registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Extract a JSON Schema from an Enum class definition.

    Args:
        class_node: The Enum class AST node
        registry: The type registry

    Returns:
        A JSON Schema representing the Enum
    """
    enum_values = []
    enum_type = "string"  # Default type for enums

    # Check if it's an IntEnum or StrEnum
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            if base.id == "IntEnum":
                enum_type = "integer"
            elif base.id == "StrEnum":
                enum_type = "string"

    # Extract enum values from assignments
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            # Simple assignment like NAME = value
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    # Skip private members (starting with _)
                    if target.id.startswith("_"):
                        continue

                    # Extract the value
                    if isinstance(stmt.value, ast.Constant):
                        enum_values.append(stmt.value.value)
                    elif isinstance(stmt.value, (ast.Str, ast.Num)):
                        # Handle older Python versions
                        if hasattr(stmt.value, "s"):
                            enum_values.append(stmt.value.s)
                        elif hasattr(stmt.value, "n"):
                            enum_values.append(stmt.value.n)

    # Create schema with enum values
    if enum_values:
        return {"type": enum_type, "enum": enum_values}

    # If no values found, create simple schema
    return {"type": enum_type}


def extract_dataclass_schema(
    class_node: ast.ClassDef, registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Extract a JSON Schema from a dataclass definition.

    Args:
        class_node: The dataclass AST node
        registry: The type registry

    Returns:
        A JSON Schema representing the dataclass
    """
    properties = {}
    required = []

    # Extract class variables with annotations
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign):
            # This is a typed field like "name: str"
            if isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                field_type = stmt.annotation

                # Skip private members (starting with _)
                if field_name.startswith("_"):
                    continue

                # Get schema for this field
                field_schema = extract_type_schema(field_type, registry)
                properties[field_name] = field_schema

                # Check if it has a default value
                has_default = False
                if stmt.value is not None:
                    has_default = True

                # Add to required fields if no default value
                if not has_default:
                    required.append(field_name)

    # Create the schema
    schema = {"type": "object", "properties": properties}

    # Add required fields
    if required:
        schema["required"] = required

    return schema


def should_be_required(field_type: ast.expr, has_default: bool) -> bool:
    """
    Determine if a field should be marked as required in the schema.

    Args:
        field_type: The field's type annotation AST node
        has_default: Whether the field has a default value

    Returns:
        True if the field should be required, False otherwise
    """
    # If the field has a default value, it's not required
    if has_default:
        return False

    # If the field is Optional, it's not required
    if is_optional_type(field_type):
        return False

    # Otherwise, it's required
    return True


def is_optional_type(type_node: ast.expr) -> bool:
    """
    Check if a type annotation is Optional[T].

    Args:
        type_node: The type annotation AST node

    Returns:
        True if the type is Optional, False otherwise
    """
    # Direct Optional[T]
    if (
        isinstance(type_node, ast.Subscript)
        and isinstance(type_node.value, ast.Name)
        and type_node.value.id == "Optional"
    ):
        return True

    # Union[T, None] form
    if (
        isinstance(type_node, ast.Subscript)
        and isinstance(type_node.value, ast.Name)
        and type_node.value.id == "Union"
    ):
        # Check if None is in the union
        union_types = []
        if isinstance(type_node.slice, ast.Tuple):
            union_types = type_node.slice.elts

        # Look for None in the union types
        for t in union_types:
            if (
                (isinstance(t, ast.Constant) and t.value is None)
                or (isinstance(t, ast.Name) and t.id == "None")
                or (isinstance(t, ast.Constant) and t.value is None)
            ):
                return True

    return False


def analyze_function_types(
    func_node: ast.FunctionDef, registry: TypeRegistry
) -> Dict[str, Any]:
    """
    Analyze a function's parameter and return types.

    Args:
        func_node: The function AST node
        registry: The type registry

    Returns:
        A dictionary with parameter and return type schemas
    """
    result: Dict[str, Any] = {"params": {}, "return": None}

    # Skip 'self' parameter for methods
    params = [arg for arg in func_node.args.args if arg.arg != "self"]

    if params:
        param_schemas = []

        for param in params:
            if param.annotation:
                param_schema = {
                    "name": param.arg,
                    "type_schema": extract_type_schema(param.annotation, registry),
                }
                param_schemas.append(param_schema)

        if param_schemas:
            result["params"] = {"serialization_type": "json", "args": param_schemas}

    # Extract return type
    if func_node.returns:
        result["return"] = {
            "serialization_type": "json",
            "type_schema": extract_type_schema(func_node.returns, registry),
        }

    return result
