"""
Module loading utilities for NEAR ABI generation.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, List


class ModuleLoader:
    """
    Handles loading Python modules from file paths.
    """

    @staticmethod
    def load_module(file_path: str) -> Any:
        """
        Load a Python module from a file path.

        Args:
            file_path: Path to the Python file

        Returns:
            Loaded module object

        Raises:
            ImportError: If the module cannot be loaded
        """
        module_name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")

        # Add directory to sys.path temporarily
        module_dir = os.path.dirname(os.path.abspath(file_path))
        original_path = list(sys.path)

        try:
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        finally:
            # Restore original sys.path
            sys.path = original_path

    @staticmethod
    def find_python_files(directory: str, recursive: bool = True) -> List[str]:
        """
        Find all Python files in a directory.

        Args:
            directory: Directory to search
            recursive: Whether to search recursively

        Returns:
            List of Python file paths
        """
        python_files = []
        directory_path = Path(directory)

        if recursive:
            # Use glob for recursive search
            for file_path in directory_path.glob("**/*.py"):
                python_files.append(str(file_path))
        else:
            # Non-recursive search
            for file_path in directory_path.glob("*.py"):
                python_files.append(str(file_path))

        return python_files
