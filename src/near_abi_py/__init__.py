"""
NEAR Python ABI Builder

A tool for generating Application Binary Interface (ABI) definitions for NEAR smart contracts
written in Python, following the same schema as NEAR's JavaScript/TypeScript SDK.
"""

from .generator import generate_abi, generate_abi_from_files
from .schema import validate_abi
from .scanner import find_python_files


__version__ = "0.2.0"


__all__ = [
    "generate_abi",
    "generate_abi_from_files",
    "validate_abi",
    "find_python_files",
]
