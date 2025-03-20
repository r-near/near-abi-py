"""
Type definitions for NEAR ABI generation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


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
        func_def = {
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
