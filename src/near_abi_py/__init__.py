"""
NEAR Python ABI Builder (Ultra-Simplified)

A minimalist tool for generating Application Binary Interface (ABI) definitions
for NEAR smart contracts written in Python.
"""

from .generator import generate_abi, generate_abi_from_files

__version__ = "0.3.0"

__all__ = [
    "generate_abi",
    "generate_abi_from_files",
]
