"""
Main ABI builder logic for NEAR ABI generation.
"""

import inspect
import os
from typing import Any, Dict, List

from ..analyzer.function import FunctionAnalyzer
from ..analyzer.loader import ModuleLoader
from ..core.constants import SCHEMA_VERSION
from ..core.metadata import MetadataExtractor
from ..core.schema import SchemaManager
from ..core.utils import log_error, log_info, log_success


class ABIBuilder:
    """
    Builds ABI definitions for NEAR contracts.
    """

    def __init__(self):
        self.module_loader = ModuleLoader()
        self.function_analyzer = FunctionAnalyzer()
        self.metadata_extractor = MetadataExtractor()
        self.schema_manager = SchemaManager()

    def generate_abi(self, contract_file: str) -> Dict[str, Any]:
        """
        Generate ABI for a Python NEAR contract file.

        Args:
            contract_file: Path to the Python contract file

        Returns:
            ABI definition as a dictionary
        """
        # Create basic ABI structure
        abi = {
            "schema_version": SCHEMA_VERSION,
            "metadata": self.metadata_extractor.extract_from_file(contract_file),
            "body": {
                "functions": [],
                "root_schema": self.schema_manager.create_root_schema(),
            },
        }

        # Load the module
        module = self.module_loader.load_module(contract_file)

        # Extract contract functions
        abi["body"]["functions"] = self._extract_functions(module)

        return abi

    def generate_abi_from_files(
        self, file_paths: List[str], project_dir: str
    ) -> Dict[str, Any]:
        """
        Generate ABI from multiple Python files.

        Args:
            file_paths: List of Python file paths to analyze
            project_dir: Root directory of the project

        Returns:
            ABI definition as a dictionary
        """
        # Create basic ABI structure
        abi = {
            "schema_version": SCHEMA_VERSION,
            "metadata": self.metadata_extractor.extract_from_directory(project_dir),
            "body": {
                "functions": [],
                "root_schema": self.schema_manager.create_root_schema(),
            },
        }

        # Process each file and collect functions
        all_functions = []

        for file_path in file_paths:
            try:
                module = self.module_loader.load_module(file_path)
                functions = self._extract_functions(module)

                if functions:
                    all_functions.extend(functions)
                    # Using rich logging format but stored as string for compatibility
                    rel_path = os.path.relpath(file_path, project_dir)
                    log_success(
                        f"{rel_path}: Found {len(functions)} contract function(s)"
                    )
                else:
                    rel_path = os.path.relpath(file_path, project_dir)
                    log_info(f"{rel_path}: No contract functions found")
            except Exception as e:
                rel_path = os.path.relpath(file_path, project_dir)
                log_error(f"{rel_path}: Error: {str(e)}")

        # Add functions to ABI
        abi["body"]["functions"] = all_functions

        # Add source files to metadata
        abi["metadata"]["sources"] = [
            os.path.relpath(f, project_dir) for f in file_paths
        ]

        return abi

    def _extract_functions(self, module: Any) -> List[Dict[str, Any]]:
        """
        Extract contract functions from a module.

        Args:
            module: Python module object

        Returns:
            List of function definitions for ABI
        """
        functions = []

        # Find all contract functions in the module
        for name, obj in inspect.getmembers(module):
            # Skip private members
            if name.startswith("_"):
                continue

            # For classes, check methods for contract functions
            if inspect.isclass(obj):
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue

                    # Analyze the method
                    func_def = self.function_analyzer.analyze_function(method)
                    if func_def:
                        functions.append(func_def.to_dict())

            # For top-level functions, check for contract functions
            elif inspect.isfunction(obj):
                # Analyze the function
                func_def = self.function_analyzer.analyze_function(obj)
                if func_def:
                    functions.append(func_def.to_dict())

        return functions
