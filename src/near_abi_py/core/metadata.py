"""
Project metadata extraction for NEAR ABI generation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import DEFAULT_METADATA, PROJECT_FILES
from .utils import log_warning


class MetadataExtractor:
    """
    Extracts metadata from project files.
    """

    def __init__(self):
        self.default_metadata = DEFAULT_METADATA.copy()

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a contract file.

        Args:
            file_path: Path to the contract file

        Returns:
            Metadata dictionary
        """
        # Basic metadata with defaults
        metadata = self.default_metadata.copy()
        metadata["name"] = Path(file_path).stem

        # Add build info
        metadata["build"] = {
            "compiler": f"python {sys.version.split()[0]}",
            "builder": "near-abi-py",
        }

        # Find and process project file
        project_file = self._find_project_file(file_path)
        if project_file:
            self._update_from_project_file(metadata, project_file)

        return metadata

    def extract_from_directory(self, project_dir: str) -> Dict[str, Any]:
        """
        Extract metadata from a project directory.

        Args:
            project_dir: Path to the project directory

        Returns:
            Metadata dictionary
        """
        # Check each possible project file
        for filename in PROJECT_FILES:
            project_file = os.path.join(project_dir, filename)
            if os.path.exists(project_file):
                return self.extract_from_file(project_file)

        # If no project file found, use directory name as project name
        metadata = self.default_metadata.copy()
        metadata["name"] = os.path.basename(project_dir)

        # Add build info
        metadata["build"] = {
            "compiler": f"python {sys.version.split()[0]}",
            "builder": "near-abi-py",
        }

        return metadata

    def _find_project_file(self, start_path: str) -> Optional[str]:
        """
        Find a project file by searching upwards from start_path.

        Args:
            start_path: Path to start searching from

        Returns:
            Path to the found file, or None if not found
        """
        current_dir = os.path.abspath(start_path)

        # If start_path is a file, start from its directory
        if os.path.isfile(current_dir):
            current_dir = os.path.dirname(current_dir)

        # Search upwards for each possible project file
        while True:
            for filename in PROJECT_FILES:
                file_path = os.path.join(current_dir, filename)
                if os.path.exists(file_path):
                    return file_path

            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached root
                return None

            current_dir = parent_dir

    def _update_from_project_file(
        self, metadata: Dict[str, Any], project_file: str
    ) -> None:
        """
        Update metadata from a project file.

        Args:
            metadata: Metadata dictionary to update
            project_file: Path to the project file
        """
        # Handle pyproject.toml
        if project_file.endswith("pyproject.toml"):
            self._update_from_pyproject(metadata, project_file)
        # Handle setup.py - more complex, may implement later
        # elif project_file.endswith("setup.py"):
        #    self._update_from_setup_py(metadata, project_file)
        # Handle Cargo.toml for mixed Rust/Python projects
        elif project_file.endswith("Cargo.toml"):
            self._update_from_cargo_toml(metadata, project_file)

    def _update_from_pyproject(
        self, metadata: Dict[str, Any], pyproject_path: str
    ) -> None:
        """
        Update metadata from pyproject.toml.

        Args:
            metadata: Metadata dictionary to update
            pyproject_path: Path to pyproject.toml
        """
        try:
            # Use tomli for Python < 3.11, or tomllib for Python >= 3.11
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                try:
                    import tomli as tomllib
                except ImportError:
                    # Skip if tomli is not available
                    return

            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)

            # Extract project info
            if "project" in pyproject_data:
                project = pyproject_data["project"]
                if "name" in project:
                    metadata["name"] = project["name"]
                if "version" in project:
                    metadata["version"] = project["version"]
                if "authors" in project:
                    metadata["authors"] = [
                        author["name"] if isinstance(author, dict) else author
                        for author in project["authors"]
                    ]
        except Exception as e:
            log_warning(f"Error reading pyproject.toml: {e}")

    def _update_from_cargo_toml(
        self, metadata: Dict[str, Any], cargo_path: str
    ) -> None:
        """
        Update metadata from Cargo.toml for mixed Rust/Python projects.

        Args:
            metadata: Metadata dictionary to update
            cargo_path: Path to Cargo.toml
        """
        try:
            # Use tomli for Python < 3.11, or tomllib for Python >= 3.11
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                try:
                    import tomli as tomllib
                except ImportError:
                    # Skip if tomli is not available
                    return

            with open(cargo_path, "rb") as f:
                cargo_data = tomllib.load(f)

            # Extract package info
            if "package" in cargo_data:
                package = cargo_data["package"]
                if "name" in package:
                    metadata["name"] = package["name"]
                if "version" in package:
                    metadata["version"] = package["version"]
                if "authors" in package:
                    metadata["authors"] = package["authors"]
        except Exception as e:
            log_warning(f"Error reading Cargo.toml: {e}")
