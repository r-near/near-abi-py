"""
Core components for NEAR ABI generation.
"""

from .constants import SCHEMA_VERSION
from .metadata import MetadataExtractor
from .schema import SchemaManager
from .types import AbiFunctionKind, AbiFunctionModifier, FunctionDef, NearDecorator
from .utils import (
    configure_console,
    console,
    log_error,
    log_info,
    log_success,
    log_warning,
)

__all__ = [
    "SCHEMA_VERSION",
    "AbiFunctionKind",
    "AbiFunctionModifier",
    "NearDecorator",
    "FunctionDef",
    "MetadataExtractor",
    "SchemaManager",
    "log_error",
    "log_info",
    "log_success",
    "log_warning",
    "console",
    "configure_console",
]
