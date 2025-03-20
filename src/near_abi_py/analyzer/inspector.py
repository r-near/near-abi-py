"""
Function inspection utilities for NEAR ABI generation.
"""

import inspect
import re
from typing import Callable, List, Optional

from ..core.types import NearDecorator


class FunctionInspector:
    """
    Inspects Python functions to identify NEAR contract functions and their properties.
    """

    @staticmethod
    def get_decorators(func: Callable) -> List[NearDecorator]:
        """
        Extract NEAR decorators from a function.

        Args:
            func: Function object to inspect

        Returns:
            List of NEAR decorators found on the function
        """
        decorators = []

        # Method 1: Check for explicitly stored decorators
        if hasattr(func, "__decorators__"):
            for decorator in getattr(func, "__decorators__"):
                try:
                    decorators.append(NearDecorator(decorator))
                except ValueError:
                    pass  # Not a NEAR decorator

            return decorators

        # Method 2: Source code inspection fallback
        try:
            source = inspect.getsource(func)
            for decorator_value in NearDecorator:
                decorator_name = decorator_value.value
                # Match both @decorator and @near.decorator forms
                if re.search(r"@(near\.)?(" + decorator_name + r")\b", source):
                    decorators.append(decorator_value)
        except Exception:
            # Source inspection failed - could be a built-in or C function
            pass

        return decorators

    @staticmethod
    def get_docstring(func: Callable) -> Optional[str]:
        """Extract and clean the function's docstring."""
        if func.__doc__:
            return inspect.cleandoc(func.__doc__)
        return None

    @staticmethod
    def get_signature(func: Callable) -> inspect.Signature:
        """Get the function's signature."""
        return inspect.signature(func)

    @staticmethod
    def is_contract_function(func: Callable) -> bool:
        """
        Determine if a function is a NEAR contract function.

        Args:
            func: Function to check

        Returns:
            True if this is a contract function
        """
        # Must have at least one NEAR decorator
        return len(FunctionInspector.get_decorators(func)) > 0
