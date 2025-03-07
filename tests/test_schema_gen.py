"""
Integration tests for the NEAR Python ABI generator with complex types.

These tests verify that the entire ABI generation pipeline works correctly
with complex types, from parsing Python files to generating the final ABI.
"""

import os
import tempfile

from near_abi_py.generator import generate_abi
from near_abi_py.schema import validate_abi


def test_complex_types_abi_generation():
    """Test generating ABI from a file with complex types."""
    # Create a temporary contract file with complex types
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("""
from typing import TypedDict, Dict, List, Optional, Union, NamedTuple, Tuple, Any, Literal
from enum import Enum, IntEnum
from dataclasses import dataclass

# TypedDict examples
class UserProfile(TypedDict, total=False):
    id: str
    email: str
    age: Optional[int]

# NamedTuple example
class Point(NamedTuple):
    x: float
    y: float
    label: Optional[str] = None

# Enum example
class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# IntEnum example
class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

# Dataclass example
@dataclass
class Configuration:
    name: str
    timeout: int = 30

# Contract functions using these types
@view
def get_user_info(user_id: str) -> UserProfile:
    \"\"\"Get a user's profile by ID.\"\"\"
    pass

@call
def update_status(item_id: str, new_status: Status) -> bool:
    \"\"\"Update an item's status.\"\"\"
    pass

@view
def get_points_by_priority(min_priority: Priority) -> List[Point]:
    \"\"\"Get points filtered by minimum priority.\"\"\"
    pass

@call
def save_configuration(config: Configuration) -> None:
    \"\"\"Save a new configuration.\"\"\"
    pass

@view
def get_coordinates() -> List[Tuple[float, float]]:
    \"\"\"Get a list of coordinate pairs.\"\"\"
    pass

@call
def update_multiple(
    user_ids: List[str],
    profiles: Dict[str, UserProfile],
    statuses: Dict[str, Status]
) -> Dict[str, bool]:
    \"\"\"Update multiple users at once.\"\"\"
    pass
""")
        temp_file = f.name

    try:
        # Generate ABI from the temp file
        abi = generate_abi(temp_file)

        # Validate the ABI
        validation_messages = validate_abi(abi)
        assert not any(msg.startswith("Error") for msg in validation_messages), (
            f"ABI validation errors: {validation_messages}"
        )

        # Check if functions were extracted
        assert len(abi["body"]["functions"]) == 6

        # Find functions by name
        functions_by_name = {func["name"]: func for func in abi["body"]["functions"]}

        # Check UserProfile (TypedDict with total=False)
        user_info_func = functions_by_name["get_user_info"]
        user_profile_schema = user_info_func["result"]["type_schema"]
        assert user_profile_schema["type"] == "object"
        assert "id" in user_profile_schema["properties"]
        assert "email" in user_profile_schema["properties"]
        assert "age" in user_profile_schema["properties"]
        assert user_profile_schema["properties"]["age"]["type"] == ["integer", "null"]
        assert (
            "required" not in user_profile_schema
        )  # total=False means no required fields

        # Check Point (NamedTuple with default)
        points_func = functions_by_name["get_points_by_priority"]
        point_schema = points_func["result"]["type_schema"]["items"]
        assert point_schema["type"] == "object"
        assert "x" in point_schema["properties"]
        assert "y" in point_schema["properties"]
        assert "label" in point_schema["properties"]
        assert point_schema["properties"]["label"]["type"] == ["string", "null"]
        assert "required" in point_schema
        assert "x" in point_schema["required"]
        assert "y" in point_schema["required"]
        assert (
            "label" not in point_schema["required"]
        )  # Has default value, should not be required

        # Check Status (Enum)
        status_func = functions_by_name["update_status"]
        status_param = next(
            p for p in status_func["params"]["args"] if p["name"] == "new_status"
        )
        status_schema = status_param["type_schema"]
        assert status_schema["type"] == "string"
        assert "enum" in status_schema
        assert "pending" in status_schema["enum"]
        assert "approved" in status_schema["enum"]
        assert "rejected" in status_schema["enum"]

        # Check Priority (IntEnum)
        priority_param = functions_by_name["get_points_by_priority"]["params"]["args"][
            0
        ]
        priority_schema = priority_param["type_schema"]
        assert priority_schema["type"] == "integer"
        assert "enum" in priority_schema
        assert 1 in priority_schema["enum"]
        assert 2 in priority_schema["enum"]
        assert 3 in priority_schema["enum"]

        # Check Configuration (dataclass)
        config_param = functions_by_name["save_configuration"]["params"]["args"][0]
        config_schema = config_param["type_schema"]
        assert config_schema["type"] == "object"
        assert "name" in config_schema["properties"]
        assert "timeout" in config_schema["properties"]
        assert "required" in config_schema
        assert "name" in config_schema["required"]
        assert "timeout" not in config_schema["required"]  # Has default value

        # Check List[Tuple[float, float]]
        coord_func = functions_by_name["get_coordinates"]
        coord_schema = coord_func["result"]["type_schema"]
        assert coord_schema["type"] == "array"
        assert "items" in coord_schema
        assert coord_schema["items"]["type"] == "array"
        assert "prefixItems" in coord_schema["items"]
        assert len(coord_schema["items"]["prefixItems"]) == 2
        assert coord_schema["items"]["prefixItems"][0]["type"] == "number"
        assert coord_schema["items"]["prefixItems"][1]["type"] == "number"

        # Check Dict[str, TypedDict] and Dict[str, Enum]
        update_multiple_func = functions_by_name["update_multiple"]
        profiles_param = next(
            p for p in update_multiple_func["params"]["args"] if p["name"] == "profiles"
        )
        statuses_param = next(
            p for p in update_multiple_func["params"]["args"] if p["name"] == "statuses"
        )

        # Check profiles parameter (Dict[str, UserProfile])
        assert profiles_param["type_schema"]["type"] == "object"
        assert "additionalProperties" in profiles_param["type_schema"]
        profile_prop_schema = profiles_param["type_schema"]["additionalProperties"]
        assert profile_prop_schema["type"] == "object"
        assert "id" in profile_prop_schema["properties"]

        # Check statuses parameter (Dict[str, Status])
        assert statuses_param["type_schema"]["type"] == "object"
        assert "additionalProperties" in statuses_param["type_schema"]
        status_prop_schema = statuses_param["type_schema"]["additionalProperties"]
        assert status_prop_schema["type"] == "string"
        assert "enum" in status_prop_schema
        assert "pending" in status_prop_schema["enum"]

    finally:
        # Clean up the temporary file
        os.unlink(temp_file)


def test_optional_fields_handling():
    """Test handling of optional fields across different complex types."""
    # Create a temporary contract file focused on optional fields
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("""
from typing import TypedDict, Optional, NamedTuple, Dict, List, Union
from dataclasses import dataclass

# Different ways a field can be optional:
# 1. Using Optional[Type]
# 2. Having a default value
# 3. In TypedDict with total=False
# 4. Using Union[Type, None]

class RegularDict(TypedDict):
    required_field: str
    optional_field: Optional[str]
    union_optional: Union[int, None]

class PartialDict(TypedDict, total=False):
    all_fields_optional: str
    nested_optional: Optional[List[str]]

class TestTuple(NamedTuple):
    required_field: str
    optional_with_type: Optional[int]
    optional_with_default: str = "default"
    optional_both: Optional[Dict[str, str]] = None

@dataclass
class TestDataclass:
    required_field: str
    optional_with_type: Optional[bool]
    optional_with_default: int = 42
    optional_both: Optional[List[int]] = None

@view
def test_optional_returns(
    param1: RegularDict,
    param2: Optional[PartialDict] = None
) -> Optional[TestTuple]:
    pass

@call
def test_optional_params(
    required: str,
    opt_type: Optional[int],
    opt_default: str = "test",
    opt_both: Optional[bool] = None
) -> Dict[str, Union[str, None]]:
    pass
""")
        temp_file = f.name

    try:
        # Generate ABI from the temp file
        abi = generate_abi(temp_file)

        # Validate the ABI
        validation_messages = validate_abi(abi)
        assert not any(msg.startswith("Error") for msg in validation_messages), (
            f"ABI validation errors: {validation_messages}"
        )

        # Check if functions were extracted
        assert len(abi["body"]["functions"]) == 2

        # Find functions by name
        functions_by_name = {func["name"]: func for func in abi["body"]["functions"]}

        # Check RegularDict
        test_func = functions_by_name["test_optional_returns"]
        regular_dict_schema = test_func["params"]["args"][0]["type_schema"]

        assert regular_dict_schema["type"] == "object"
        assert "required" in regular_dict_schema
        assert "required_field" in regular_dict_schema["required"]
        assert "optional_field" not in regular_dict_schema["required"]
        assert "union_optional" not in regular_dict_schema["required"]
        assert regular_dict_schema["properties"]["optional_field"]["type"] == [
            "string",
            "null",
        ]
        assert regular_dict_schema["properties"]["union_optional"] == {
            "anyOf": [{"type": "integer"}, {"type": "null"}]
        }

        # Check PartialDict (total=False)
        param2_schema = test_func["params"]["args"][1]["type_schema"]
        assert param2_schema["type"] == ["object", "null"]  # Optional[PartialDict]
        partial_dict_schema = param2_schema
        assert "required" not in partial_dict_schema  # total=False

        # Check TestTuple in return type
        tuple_schema = test_func["result"]["type_schema"]
        assert tuple_schema["type"] == ["object", "null"]  # Optional[TestTuple]
        assert "properties" in tuple_schema
        assert "required" in tuple_schema
        assert "required_field" in tuple_schema["required"]
        assert "optional_with_type" not in tuple_schema["required"]
        assert "optional_with_default" not in tuple_schema["required"]
        assert "optional_both" not in tuple_schema["required"]

        # Check function with optional parameters
        params_func = functions_by_name["test_optional_params"]
        params = {p["name"]: p["type_schema"] for p in params_func["params"]["args"]}

        assert params["required"]["type"] == "string"
        assert params["opt_type"]["type"] == ["integer", "null"]
        assert params["opt_default"]["type"] == "string"
        assert params["opt_both"]["type"] == ["boolean", "null"]

        # Check Dict[str, Union[str, None]] return type
        return_schema = params_func["result"]["type_schema"]
        assert return_schema["type"] == "object"
        assert "additionalProperties" in return_schema
        assert return_schema["additionalProperties"] == {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        }

    finally:
        # Clean up the temporary file
        os.unlink(temp_file)
