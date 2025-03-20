"""
Constants and configuration values for NEAR ABI generation.
"""

# ABI Schema version
SCHEMA_VERSION = "0.4.0"

# List of recognized NEAR decorators
NEAR_DECORATORS = ["view", "call", "init", "payable", "private", "callback"]

# Default metadata values
DEFAULT_METADATA = {
    "name": "unknown",
    "version": "0.1.0",
    "authors": ["Unknown"],
}

# Files to look for when extracting project metadata
PROJECT_FILES = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Cargo.toml",  # Some NEAR projects use mixed Rust/Python
]
