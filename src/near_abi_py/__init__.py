"""
NEAR Python ABI Builder

A tool for generating Application Binary Interface (ABI) definitions for NEAR smart contracts
written in Python, following the same schema as NEAR's JavaScript/TypeScript SDK.
"""

from .generator import generate_abi
from .schema import validate_abi


__version__ = "0.1.0"


__all__ = ["generate_abi", "validate_abi"]
