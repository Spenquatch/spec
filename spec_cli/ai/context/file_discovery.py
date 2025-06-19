"""Documentation discovery and cataloging for search index creation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ...utils.path_utils import resolve_project_root
from ...utils.workflow_utils import create_workflow_result

logger = logging.getLogger(__name__)


class DocumentationDiscovery:
    """Discover and catalog documentation files."""

    def __init__(self) -> None:
        """Initialize DocumentationDiscovery with project root resolution."""
        self.project_root = resolve_project_root()

    def discover_documentation(
        self, file_patterns: list[str] | None = None, max_files: int = 1000
    ) -> dict[str, Any]:
        """Discover all documentation files for indexing.

        Args:
            file_patterns: File patterns to match (defaults to markdown and text files)
            max_files: Maximum number of files to discover

        Returns:
            Workflow result with discovered files data or error message

        Raises:
            ValueError: If max_files is less than 1
        """
        if max_files < 1:
            raise ValueError("max_files must be at least 1")

        try:
            logger.info(
                "Starting documentation discovery",
                extra={"project_root": str(self.project_root), "max_files": max_files},
            )

            specs_path = self.project_root / ".specs"

            # Check if documentation exists
            if not specs_path.exists():
                logger.warning("No .specs directory found")
                return create_workflow_result(
                    files=[], success=False, workflow_id="documentation_discovery"
                )

            # Discover files with patterns
            discovered_files = []
            patterns = file_patterns or ["*.md", "*.txt"]

            for pattern in patterns:
                for file_path in specs_path.rglob(pattern):
                    # Validate file (check if it's under .specs and is a file)
                    if file_path.is_file() and file_path.is_relative_to(specs_path):
                        discovered_files.append(file_path)
                        if len(discovered_files) >= max_files:
                            break

                if len(discovered_files) >= max_files:
                    break

            # Validate discovery results
            if not discovered_files:
                logger.info("No documentation files found matching patterns")
                return create_workflow_result(
                    files=[], success=False, workflow_id="documentation_discovery"
                )

            logger.info(
                "Documentation discovery completed",
                extra={"total_files": len(discovered_files), "patterns_used": patterns},
            )

            return create_workflow_result(
                files=discovered_files,
                success=True,
                workflow_id="documentation_discovery",
            )

        except Exception as e:
            logger.error(f"Documentation discovery failed: {str(e)}")
            return create_workflow_result(
                files=[], success=False, workflow_id="documentation_discovery"
            )

    def get_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata from a discovered file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing file metadata

        Raises:
            ValueError: If file_path does not exist
        """
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        try:
            stats = file_path.stat()
            content = file_path.read_text(encoding="utf-8")

            return {
                "file_path": str(file_path),
                "size_bytes": stats.st_size,
                "modified_time": stats.st_mtime,
                "created_time": stats.st_ctime,
                "line_count": len(content.splitlines()),
                "character_count": len(content),
                "file_extension": file_path.suffix,
                "file_name": file_path.name,
                "relative_path": str(file_path.relative_to(self.project_root)),
                "content_preview": content[:300] if content else "",
                "is_empty": len(content.strip()) == 0,
            }
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "error": str(e),
                "metadata_extraction_failed": True,
            }

    def validate_discovered_files(self, file_paths: list[Path]) -> dict[str, Any]:
        """Validate discovered files and filter out problematic ones.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Dictionary with validation results including valid and invalid files
        """
        valid_files = []
        invalid_files = []
        validation_errors = []

        for file_path in file_paths:
            try:
                # Check file exists and is readable
                if not file_path.exists():
                    invalid_files.append(str(file_path))
                    validation_errors.append(f"File does not exist: {file_path}")
                    continue

                if not file_path.is_file():
                    invalid_files.append(str(file_path))
                    validation_errors.append(f"Path is not a file: {file_path}")
                    continue

                # Try to read the file to ensure it's accessible
                file_path.read_text(encoding="utf-8")
                valid_files.append(file_path)

            except PermissionError:
                invalid_files.append(str(file_path))
                validation_errors.append(f"Permission denied: {file_path}")
            except UnicodeDecodeError:
                invalid_files.append(str(file_path))
                validation_errors.append(f"Encoding error: {file_path}")
            except Exception as e:
                invalid_files.append(str(file_path))
                validation_errors.append(f"Validation error for {file_path}: {e}")

        logger.info(
            "File validation completed",
            extra={
                "valid_files": len(valid_files),
                "invalid_files": len(invalid_files),
                "total_errors": len(validation_errors),
            },
        )

        return {
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "validation_errors": validation_errors,
            "total_valid": len(valid_files),
            "total_invalid": len(invalid_files),
        }

    def get_discovery_summary(self, discovered_files: list[Path]) -> dict[str, Any]:
        """Generate summary of discovery results.

        Args:
            discovered_files: List of discovered file paths

        Returns:
            Dictionary with discovery summary statistics
        """
        if not discovered_files:
            return {
                "total_files": 0,
                "file_types": {},
                "total_size_bytes": 0,
                "discovery_time": datetime.now().isoformat(),
                "project_root": str(self.project_root),
            }

        file_types: dict[str, int] = {}
        total_size = 0

        for file_path in discovered_files:
            try:
                extension = file_path.suffix or "no_extension"
                file_types[extension] = file_types.get(extension, 0) + 1

                if file_path.exists():
                    total_size += file_path.stat().st_size
            except Exception:
                # Skip files that can't be accessed
                continue

        return {
            "total_files": len(discovered_files),
            "file_types": file_types,
            "total_size_bytes": total_size,
            "discovery_time": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "specs_directory": str(self.project_root / ".specs"),
        }
