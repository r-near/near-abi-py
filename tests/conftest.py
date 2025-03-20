import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path if running tests outside of pytest
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory"""
    return FIXTURES_DIR


@pytest.fixture
def basic_contract_path():
    """Return the path to the basic contract fixture"""
    return FIXTURES_DIR / "basic_contract.py"


@pytest.fixture
def complex_types_path():
    """Return the path to the complex types fixture"""
    return FIXTURES_DIR / "complex_types.py"


@pytest.fixture
def multi_file_project_path():
    """Return the path to the multi-file project fixture"""
    return FIXTURES_DIR / "multi_file_project"
