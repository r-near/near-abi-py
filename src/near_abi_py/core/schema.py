"""
JSON Schema utilities for NEAR ABI generation.
"""

import json
import os
from typing import Any, Dict, List, Tuple

import jsonschema


class SchemaManager:
    """
    Manages JSON Schema creation and validation for NEAR ABI.
    """

    @staticmethod
    def create_root_schema() -> Dict[str, Any]:
        """
        Create a root schema with common NEAR types.

        Returns:
            Dictionary with JSON Schema for common NEAR types
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "NEAR Contract Schema",
            "definitions": {
                "AccountId": {
                    "type": "string",
                    "description": "NEAR account identifier",
                },
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

    @staticmethod
    def validate_abi(abi: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an ABI against the schema.

        Args:
            abi: The ABI to validate

        Returns:
            Tuple of (is_valid, messages)
        """
        # Load the schema
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "abi_schema.json"
        )

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Basic validation
        try:
            jsonschema.validate(abi, schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            return False, [f"Error: {e.message}"]
