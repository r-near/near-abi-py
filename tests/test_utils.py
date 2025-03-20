from pathlib import Path

from near_abi_py.utils import (
    extract_metadata,
    extract_project_metadata,
    find_python_files,
    get_function_decorators,
    validate_abi,
)

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_find_python_files():
    """Test finding Python files in a directory"""
    # Test in the fixtures directory
    python_files = find_python_files(str(FIXTURES_DIR))

    # Should find at least our test contract files
    assert len(python_files) >= 4

    # All paths should be .py files
    for file_path in python_files:
        assert file_path.endswith(".py")

    # Test recursive mode off
    python_files_non_recursive = find_python_files(str(FIXTURES_DIR), recursive=False)
    assert len(python_files_non_recursive) < len(python_files)


def test_validate_abi_with_valid_abi():
    """Test ABI validation with a valid ABI"""
    # Create a minimal valid ABI
    valid_abi = {
        "schema_version": "0.4.0",
        "metadata": {
            "name": "test-contract",
            "version": "0.1.0",
            "authors": ["Test Author"],
            "build": {"compiler": "python 3.12", "builder": "near-abi-py"},
        },
        "body": {
            "functions": [],
            "root_schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "definitions": {},
            },
        },
    }

    is_valid, messages = validate_abi(valid_abi)
    assert is_valid
    assert not messages


def test_validate_abi_with_invalid_abi():
    """Test ABI validation with an invalid ABI"""
    # Create an invalid ABI missing required fields
    invalid_abi = {
        "schema_version": "0.4.0",
        "metadata": {},  # Missing required fields
        "body": {},  # Missing required fields
    }

    is_valid, messages = validate_abi(invalid_abi)
    assert not is_valid
    assert messages  # Should have validation error messages


def test_extract_metadata():
    """Test extracting metadata from a file"""
    # Get metadata from a test file
    basic_contract = FIXTURES_DIR / "basic_contract.py"
    metadata = extract_metadata(str(basic_contract))

    # Check basic metadata fields
    assert "name" in metadata
    assert metadata["name"] == "near-abi-py"
    assert "version" in metadata
    assert "authors" in metadata
    assert "build" in metadata


def test_extract_project_metadata():
    """Test extracting metadata from a project directory"""
    # Get metadata from the multi-file project
    project_dir = FIXTURES_DIR / "multi_file_project"
    metadata = extract_project_metadata(str(project_dir))

    # Check basic metadata fields
    assert "name" in metadata
    assert metadata["name"] == "multi_file_project"
    assert "version" in metadata
    assert "authors" in metadata
    assert "build" in metadata


def test_get_function_decorators():
    """Test extracting NEAR decorators from function objects"""
    # This requires loading the module first
    import importlib.util

    # Load the basic contract module
    basic_contract_path = FIXTURES_DIR / "basic_contract.py"
    spec = importlib.util.spec_from_file_location("basic_contract", basic_contract_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Check view function
    decorators = get_function_decorators(module.get_greeting)
    assert len(decorators) == 1
    assert decorators[0].value == "view"

    # Check call function
    decorators = get_function_decorators(module.set_greeting)
    assert len(decorators) == 1
    assert decorators[0].value == "call"

    # Check init function
    decorators = get_function_decorators(module.new)
    assert len(decorators) == 1
    assert decorators[0].value == "init"
