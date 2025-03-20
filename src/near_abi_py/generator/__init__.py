"""
NEAR ABI Generator exports.
"""

from typing import Any, Dict, List

from .builder import ABIBuilder


def generate_abi(contract_file: str) -> Dict[str, Any]:
    """
    Generate ABI for a Python NEAR contract file.

    Args:
        contract_file: Path to the Python contract file

    Returns:
        ABI definition as a dictionary
    """
    builder = ABIBuilder()
    return builder.generate_abi(contract_file)


def generate_abi_from_files(file_paths: List[str], project_dir: str) -> Dict[str, Any]:
    """
    Generate ABI from multiple Python files.

    Args:
        file_paths: List of Python file paths to analyze
        project_dir: Root directory of the project

    Returns:
        ABI definition as a dictionary
    """
    builder = ABIBuilder()
    return builder.generate_abi_from_files(file_paths, project_dir)
