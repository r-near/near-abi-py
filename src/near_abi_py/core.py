"""
Core types and constants for NEAR ABI generation.
"""

import sys
from enum import Enum
from typing import Any, Dict, List, Optional

# Schema version
SCHEMA_VERSION = "0.4.0"


# Type definitions
class AbiFunctionKind(str, Enum):
    """Function kind in ABI"""

    VIEW = "view"
    CALL = "call"


class AbiFunctionModifier(str, Enum):
    """Function modifiers in ABI"""

    PRIVATE = "private"
    PAYABLE = "payable"
    INIT = "init"


class NearDecorator(str, Enum):
    """NEAR contract decorators"""

    VIEW = "view"
    CALL = "call"
    INIT = "init"
    PAYABLE = "payable"
    PRIVATE = "private"
    CALLBACK = "callback"


# Default metadata values
DEFAULT_METADATA = {
    "name": "unknown",
    "version": "0.1.0",
    "authors": ["Unknown"],
    "build": {"compiler": f"python {sys.version.split()[0]}", "builder": "near-abi-py"},
}


# Type definitions for function analysis
class FunctionDef:
    """Represents a NEAR contract function definition"""

    def __init__(self, name: str, kind: AbiFunctionKind):
        self.name = name
        self.kind = kind
        self.doc: Optional[str] = None
        self.modifiers: List[AbiFunctionModifier] = []
        self.params: Optional[Dict[str, Any]] = None
        self.result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to ABI dictionary representation"""
        func_def: Dict[str, Any] = {
            "name": self.name,
            "kind": self.kind.value,
        }

        if self.doc:
            func_def["doc"] = self.doc

        if self.modifiers:
            func_def["modifiers"] = [m.value for m in self.modifiers]

        if self.params:
            func_def["params"] = self.params

        if self.result:
            func_def["result"] = self.result

        return func_def


# Root schema for common NEAR types
def create_root_schema() -> Dict[str, Any]:
    """Create a root schema with common NEAR types"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NEAR Contract Schema",
        "definitions": {
            "AccountId": {"type": "string", "description": "NEAR account identifier"},
            "Balance": {
                "type": "string",
                "description": "Balance value in yoctoNEAR",
                "pattern": "^[0-9]+$",
            },
            "Gas": {
                "type": "integer",
                "description": "Gas units for NEAR VM operations",
                "minimum": 0,
            },
            "PublicKey": {
                "type": "string",
                "description": "Public key in base58 or base64 format",
            },
            "Promise": {
                "type": "object",
                "description": "NEAR Promise for async cross-contract calls",
            },
        },
    }
