from pathlib import Path

import pytest

from near_abi_py import generate_abi, generate_abi_from_files
from near_abi_py.utils import validate_abi

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_basic_contract_abi_generation():
    """Test generating ABI from a basic contract file"""
    # Path to the test fixture
    contract_file = FIXTURES_DIR / "basic_contract.py"

    # Generate ABI
    abi = generate_abi(str(contract_file))

    # Validate the ABI structure
    is_valid, messages = validate_abi(abi)
    assert is_valid, f"ABI validation failed: {messages}"

    # Check schema version
    assert abi["schema_version"] == "0.4.0"

    # Check functions are extracted
    functions = abi["body"]["functions"]
    assert len(functions) == 3

    # Check function names
    function_names = [f["name"] for f in functions]
    assert "get_greeting" in function_names
    assert "set_greeting" in function_names
    assert "new" in function_names

    # Check function kinds
    get_greeting = next(f for f in functions if f["name"] == "get_greeting")
    assert get_greeting["kind"] == "view"

    set_greeting = next(f for f in functions if f["name"] == "set_greeting")
    assert set_greeting["kind"] == "call"

    new_func = next(f for f in functions if f["name"] == "new")
    assert new_func["kind"] == "call"
    assert "modifiers" in new_func
    assert "init" in new_func["modifiers"]


def test_complex_types_contract_abi_generation():
    """Test generating ABI from a contract with complex types"""
    # Path to the test fixture
    contract_file = FIXTURES_DIR / "complex_types.py"

    # Generate ABI
    abi = generate_abi(str(contract_file))

    # Validate the ABI structure
    is_valid, messages = validate_abi(abi)
    assert is_valid, f"ABI validation failed: {messages}"

    # Check functions
    functions = abi["body"]["functions"]
    assert len(functions) == 5

    # Check Enum handling
    get_items = next(f for f in functions if f["name"] == "get_items_by_status")
    status_param = get_items["params"]["args"][0]
    assert status_param["name"] == "status"
    assert status_param["type_schema"]["type"] == "string"

    # Check TypedDict handling
    get_profile = next(f for f in functions if f["name"] == "get_user_profile")
    result_schema = get_profile["result"]["type_schema"]
    assert result_schema["type"] == "object"
    assert "properties" in result_schema
    assert "display_name" in result_schema["properties"]

    # Check Dataclass handling
    get_settings = next(f for f in functions if f["name"] == "get_settings")
    result_schema = get_settings["result"]["type_schema"]
    assert result_schema["type"] == "object"
    assert "properties" in result_schema
    assert "theme" in result_schema["properties"]
    assert "notifications_enabled" in result_schema["properties"]

    # Check Union handling
    batch_op = next(f for f in functions if f["name"] == "batch_operation")
    options_param = batch_op["params"]["args"][1]
    assert options_param["name"] == "options"
    assert options_param["type_schema"]["type"] == "object"


def test_multi_file_project_abi_generation():
    """Test generating ABI from a multi-file project"""
    # Path to the multi-file project
    project_dir = FIXTURES_DIR / "multi_file_project"

    # Find Python files
    python_files = list(project_dir.glob("**/*.py"))
    assert len(python_files) >= 3  # main.py, models/__init__.py, models/account.py

    # Generate ABI
    abi = generate_abi_from_files([str(f) for f in python_files], str(project_dir))

    # Validate the ABI structure
    is_valid, messages = validate_abi(abi)
    assert is_valid, f"ABI validation failed: {messages}"

    # Check functions are collected from all files
    functions = abi["body"]["functions"]
    assert len(functions) == 4

    # Check function names from different files
    function_names = [f["name"] for f in functions]
    assert "new" in function_names
    assert "get_account_info" in function_names
    assert "get_account_detail" in function_names
    assert "get_account_history" in function_names

    # Check source file information
    assert "sources" in abi["metadata"]
    assert len(abi["metadata"]["sources"]) == 3


def test_python_type_to_json_schema():
    """Test that Python types are correctly converted to JSON Schema"""
    contract_file = FIXTURES_DIR / "complex_types.py"
    abi = generate_abi(str(contract_file))
    functions = abi["body"]["functions"]

    # Test string type
    get_profile = next(f for f in functions if f["name"] == "get_user_profile")
    user_id_param = get_profile["params"]["args"][0]
    assert user_id_param["type_schema"]["type"] == "string"

    # Test list type
    get_items = next(f for f in functions if f["name"] == "get_items_by_status")
    result_schema = get_items["result"]["type_schema"]
    assert result_schema["type"] == "array"
    assert result_schema["items"]["type"] == "string"

    # Test enum type
    status_param = get_items["params"]["args"][0]
    assert status_param["type_schema"]["type"] == "string"

    # Test optional type
    update_profile = next(f for f in functions if f["name"] == "update_profile")
    profile_param = update_profile["params"]["args"][1]
    email_schema = profile_param["type_schema"]["properties"].get("email")
    assert email_schema["anyOf"] == [{"type": "string"}, {"type": "null"}]

    # Test dict with union values
    batch_op = next(f for f in functions if f["name"] == "batch_operation")
    options_param = batch_op["params"]["args"][1]
    assert options_param["type_schema"]["type"] == "object"

    # Test return dict mapping
    result_schema = batch_op["result"]["type_schema"]
    assert result_schema["type"] == "object"
    assert "additionalProperties" in result_schema
    assert result_schema["additionalProperties"]["type"] == "boolean"


def test_empty_contract():
    """Test handling of a contract with no NEAR functions"""
    contract_file = FIXTURES_DIR / "empty_contract.py"

    # Generate ABI
    abi = generate_abi(str(contract_file))

    # Should have an empty functions list
    assert "functions" in abi["body"]
    assert len(abi["body"]["functions"]) == 0


def test_contract_with_syntax_error():
    """Test handling of a contract file with syntax errors"""
    contract_file = FIXTURES_DIR / "invalid_syntax.py"

    # Should raise an exception
    with pytest.raises(Exception):
        generate_abi(str(contract_file))
