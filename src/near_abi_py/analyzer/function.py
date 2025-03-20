"""
Function analysis for NEAR ABI generation.
"""

import inspect
from typing import Any, Callable, Dict, Optional, get_type_hints

from pydantic import TypeAdapter

from ..core.types import (
    AbiFunctionKind,
    AbiFunctionModifier,
    FunctionDef,
    NearDecorator,
)
from ..core.utils import log_warning
from .inspector import FunctionInspector


class FunctionAnalyzer:
    """
    Analyzes and extracts ABI information from Python functions.
    """

    def __init__(self):
        self.inspector = FunctionInspector()

    def analyze_function(self, func: Callable) -> Optional[FunctionDef]:
        """
        Analyze a function and extract its ABI definition.

        Args:
            func: Function to analyze

        Returns:
            FunctionDef or None if not a contract function
        """
        # Get decorators
        decorators = self.inspector.get_decorators(func)

        if not decorators:
            return None

        # Determine function kind and modifiers
        is_view = NearDecorator.VIEW in decorators
        is_init = NearDecorator.INIT in decorators
        is_private = (
            NearDecorator.PRIVATE in decorators or NearDecorator.CALLBACK in decorators
        )
        is_payable = NearDecorator.PAYABLE in decorators

        # Create function definition
        func_def = FunctionDef(
            name=func.__name__,
            kind=AbiFunctionKind.VIEW if is_view else AbiFunctionKind.CALL,
        )

        # Add docstring
        func_def.doc = self.inspector.get_docstring(func)

        # Add modifiers
        if is_init:
            func_def.modifiers.append(AbiFunctionModifier.INIT)
        if is_private:
            func_def.modifiers.append(AbiFunctionModifier.PRIVATE)
        if is_payable:
            func_def.modifiers.append(AbiFunctionModifier.PAYABLE)

        # Process function signature
        self._process_signature(func, func_def)

        return func_def

    def _process_signature(self, func: Callable, func_def: FunctionDef) -> None:
        """
        Process function signature to extract parameters and return type.

        Args:
            func: Function to process
            func_def: FunctionDef to update
        """
        # Get signature
        sig = self.inspector.get_signature(func)

        # Skip 'self' parameter for methods
        params = []
        filtered_params = {
            name: param for name, param in sig.parameters.items() if name != "self"
        }

        if filtered_params:
            # Get type hints
            try:
                type_hints = get_type_hints(func)
            except Exception:
                type_hints = {}

            # Process parameters
            for name, param in filtered_params.items():
                # Get type annotation
                param_type = type_hints.get(name, Any)

                # Create JSON schema for the parameter
                param_schema = self._create_schema_for_type(param_type)

                # Add to parameters list
                params.append(
                    {
                        "name": name,
                        "type_schema": param_schema,
                    }
                )

            # Create params section if we have parameters
            if params:
                func_def.params = {
                    "serialization_type": "json",
                    "args": params,
                }

        # Handle return type
        return_annotation = sig.return_annotation
        if return_annotation is not inspect.Signature.empty:
            # Create schema for return type
            return_schema = self._create_schema_for_type(return_annotation)

            if return_schema:
                func_def.result = {
                    "serialization_type": "json",
                    "type_schema": return_schema,
                }

    def _create_schema_for_type(self, type_annotation: Any) -> Dict[str, Any]:
        """
        Create a JSON schema for a type annotation using Pydantic.

        Args:
            type_annotation: Python type annotation

        Returns:
            JSON schema for the type
        """
        try:
            # Use Pydantic's TypeAdapter to generate schema
            adapter = TypeAdapter(type_annotation)
            schema = adapter.json_schema()

            # Clean up the schema - remove unnecessary fields
            if "title" in schema and schema["title"] == "type_annotation":
                del schema["title"]

            return schema
        except Exception as e:
            # Fallback for types Pydantic can't handle
            log_warning(f"Could not generate schema for {type_annotation}: {e}")
            return {"type": "object"}
