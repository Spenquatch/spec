"""File system test infrastructure for comprehensive file operation testing.

This module provides comprehensive file system test infrastructure to enable testing
of file operations across platforms without affecting the host system, including
temporary file structure creation, permission mocking, and cross-platform validation.
"""

import os
import stat
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from ...core.context_bridge import debug_logger
from ...utils.path_utils import normalize_path_separators


class TempFileStructureBuilder:
    """Builder for creating temporary file structures for testing.

    This class provides a fluent API for creating complex file and directory
    structures in temporary locations for testing file operations.
    """

    def __init__(self, base_path: Path):
        """Initialize temporary file structure builder.

        Args:
            base_path: Base path where structure will be created
        """
        self.base_path = Path(base_path).resolve()
        self.structure: dict[str, Any] = {}
        self.permissions: dict[str, int] = {}
        self.created_paths: set[Path] = set()

        debug_logger.log(
            "DEBUG",
            "Initializing TempFileStructureBuilder",
            base_path=str(self.base_path),
        )

    def add_file(
        self, path: str, content: str = "", permissions: int | None = None
    ) -> "TempFileStructureBuilder":
        """Add a file to the structure.

        Args:
            path: Relative path to the file
            content: File content
            permissions: Optional file permissions (octal)

        Returns:
            Self for method chaining
        """
        normalized_path = normalize_path_separators(path)
        self.structure[normalized_path] = {"type": "file", "content": content}

        if permissions is not None:
            self.permissions[normalized_path] = permissions

        debug_logger.log(
            "DEBUG",
            "Added file to structure",
            path=normalized_path,
            content_length=len(content),
            permissions=permissions,
        )

        return self

    def add_directory(
        self, path: str, permissions: int | None = None
    ) -> "TempFileStructureBuilder":
        """Add a directory to the structure.

        Args:
            path: Relative path to the directory
            permissions: Optional directory permissions (octal)

        Returns:
            Self for method chaining
        """
        normalized_path = normalize_path_separators(path)
        self.structure[normalized_path] = {"type": "directory"}

        if permissions is not None:
            self.permissions[normalized_path] = permissions

        debug_logger.log(
            "DEBUG",
            "Added directory to structure",
            path=normalized_path,
            permissions=permissions,
        )

        return self

    def add_symlink(self, path: str, target: str) -> "TempFileStructureBuilder":
        """Add a symbolic link to the structure.

        Args:
            path: Relative path to the symlink
            target: Target path for the symlink

        Returns:
            Self for method chaining
        """
        normalized_path = normalize_path_separators(path)
        normalized_target = normalize_path_separators(target)

        self.structure[normalized_path] = {
            "type": "symlink",
            "target": normalized_target,
        }

        debug_logger.log(
            "DEBUG",
            "Added symlink to structure",
            path=normalized_path,
            target=normalized_target,
        )

        return self

    def build(self) -> Path:
        """Create the file structure on disk.

        Returns:
            Path to the created structure base

        Raises:
            OSError: If creation fails
        """
        try:
            # Ensure base directory exists
            self.base_path.mkdir(parents=True, exist_ok=True)

            # Sort paths to create directories before files
            sorted_paths = sorted(
                self.structure.keys(), key=lambda x: (x.count("/"), x)
            )

            for relative_path in sorted_paths:
                full_path = self.base_path / relative_path
                item = self.structure[relative_path]

                if item["type"] == "directory":
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.created_paths.add(full_path)

                elif item["type"] == "file":
                    # Ensure parent directory exists
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(item["content"], encoding="utf-8")
                    self.created_paths.add(full_path)

                elif item["type"] == "symlink":
                    # Ensure parent directory exists
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path = Path(item["target"])
                    if not target_path.is_absolute():
                        target_path = self.base_path / target_path
                    full_path.symlink_to(target_path)
                    self.created_paths.add(full_path)

                # Set permissions if specified
                if relative_path in self.permissions:
                    full_path.chmod(self.permissions[relative_path])

            debug_logger.log(
                "DEBUG",
                "Built file structure",
                base_path=str(self.base_path),
                items_created=len(self.created_paths),
            )

            return self.base_path

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to build file structure",
                base_path=str(self.base_path),
                error=str(e),
            )
            raise OSError(f"Failed to create file structure: {e}") from e

    def cleanup(self) -> None:
        """Clean up created file structure.

        Removes all files and directories that were created.
        """
        import shutil

        try:
            if self.base_path.exists():
                shutil.rmtree(self.base_path)
                debug_logger.log(
                    "DEBUG", "Cleaned up file structure", base_path=str(self.base_path)
                )
        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to cleanup file structure",
                base_path=str(self.base_path),
                error=str(e),
            )


class FilePermissionMocker:
    """Mock file permissions for cross-platform testing.

    This class provides platform-independent file permission mocking,
    allowing tests to verify permission-related behavior consistently
    across Windows, macOS, and Linux.
    """

    def __init__(self) -> None:
        """Initialize file permission mocker."""
        self.mocked_permissions: dict[str, int] = {}
        self.active_patches: list[Any] = []

        debug_logger.log("DEBUG", "Initializing FilePermissionMocker")

    def set_file_permissions(self, path: str | Path, permissions: int) -> None:
        """Set mock permissions for a file or directory.

        Args:
            path: Path to the file or directory
            permissions: Permission bits (octal, e.g., 0o755)
        """
        normalized_path = normalize_path_separators(str(path))
        self.mocked_permissions[normalized_path] = permissions

        debug_logger.log(
            "DEBUG",
            "Set mock permissions",
            path=normalized_path,
            permissions=oct(permissions),
        )

    def make_readonly(self, path: str | Path) -> None:
        """Make a file or directory read-only.

        Args:
            path: Path to make read-only
        """
        self.set_file_permissions(path, 0o444)

    def make_writable(self, path: str | Path) -> None:
        """Make a file or directory writable.

        Args:
            path: Path to make writable
        """
        self.set_file_permissions(path, 0o644)

    def make_executable(self, path: str | Path) -> None:
        """Make a file executable.

        Args:
            path: Path to make executable
        """
        self.set_file_permissions(path, 0o755)

    def remove_all_permissions(self, path: str | Path) -> None:
        """Remove all permissions from a file or directory.

        Args:
            path: Path to remove permissions from
        """
        self.set_file_permissions(path, 0o000)

    @contextmanager
    def mock_permissions(self) -> Generator["FilePermissionMocker", None, None]:
        """Context manager to apply permission mocking.

        Yields:
            Self for additional configuration
        """
        # Store original functions to avoid recursion
        original_stat = os.stat
        original_access = os.access

        def mock_stat(path: str) -> Mock | os.stat_result:
            """Mock stat function that returns configured permissions."""
            normalized_path = normalize_path_separators(str(path))
            if normalized_path in self.mocked_permissions:
                mock_stat_result = Mock()
                mock_stat_result.st_mode = self.mocked_permissions[normalized_path]
                return mock_stat_result
            # Fall back to real stat for unmocked paths
            return original_stat(path)

        def mock_access(path: str, mode: int) -> bool:
            """Mock access function based on configured permissions."""
            normalized_path = normalize_path_separators(str(path))
            if normalized_path in self.mocked_permissions:
                perms = self.mocked_permissions[normalized_path]

                # Check read permission
                if mode & os.R_OK and not (perms & stat.S_IRUSR):
                    return False

                # Check write permission
                if mode & os.W_OK and not (perms & stat.S_IWUSR):
                    return False

                # Check execute permission
                if mode & os.X_OK and not (perms & stat.S_IXUSR):
                    return False

                return True

            # Fall back to real access for unmocked paths
            return original_access(path, mode)

        def mock_pathlib_stat(path_instance: Path) -> Mock | os.stat_result:
            """Mock pathlib.Path.stat method."""
            return mock_stat(str(path_instance))

        try:
            # Apply patches
            stat_patch = patch("os.stat", side_effect=mock_stat)
            access_patch = patch("os.access", side_effect=mock_access)
            pathlib_stat_patch = patch(
                "pathlib.Path.stat", side_effect=mock_pathlib_stat
            )

            self.active_patches = [stat_patch, access_patch, pathlib_stat_patch]

            for patch_obj in self.active_patches:
                patch_obj.start()

            debug_logger.log(
                "DEBUG",
                "Activated permission mocking",
                mocked_paths=len(self.mocked_permissions),
            )

            yield self

        finally:
            # Clean up patches
            for patch_obj in self.active_patches:
                patch_obj.stop()

            debug_logger.log("DEBUG", "Deactivated permission mocking")
            self.active_patches.clear()


class CrossPlatformPathValidator:
    """Validator for cross-platform path handling in tests.

    This class provides utilities to validate that path operations
    work correctly across Windows, macOS, and Linux platforms.
    """

    def __init__(self) -> None:
        """Initialize cross-platform path validator."""
        self.validation_results: list[dict[str, Any]] = []

        debug_logger.log("DEBUG", "Initializing CrossPlatformPathValidator")

    def validate_path_normalization(
        self, original_path: str, expected_normalized: str
    ) -> bool:
        """Validate that path normalization works correctly.

        Args:
            original_path: Original path with mixed separators
            expected_normalized: Expected normalized path

        Returns:
            True if normalization is correct
        """
        normalized = normalize_path_separators(original_path)
        is_valid = normalized == expected_normalized

        result = {
            "test": "path_normalization",
            "original": original_path,
            "expected": expected_normalized,
            "actual": normalized,
            "valid": is_valid,
        }
        self.validation_results.append(result)

        debug_logger.log("DEBUG", "Validated path normalization", **result)

        return is_valid

    def validate_relative_path_handling(
        self, base_path: Path, relative_path: str
    ) -> bool:
        """Validate relative path resolution.

        Args:
            base_path: Base path for resolution
            relative_path: Relative path to resolve

        Returns:
            True if relative path resolves correctly
        """
        try:
            resolved = base_path / relative_path
            resolved_normalized = resolved.resolve()

            # Check that the resolved path is under base_path
            is_valid = str(resolved_normalized).startswith(str(base_path.resolve()))

            result = {
                "test": "relative_path_handling",
                "base_path": str(base_path),
                "relative_path": relative_path,
                "resolved": str(resolved_normalized),
                "valid": is_valid,
            }
            self.validation_results.append(result)

            debug_logger.log("DEBUG", "Validated relative path handling", **result)

            return is_valid

        except Exception as e:
            result = {
                "test": "relative_path_handling",
                "base_path": str(base_path),
                "relative_path": relative_path,
                "error": str(e),
                "valid": False,
            }
            self.validation_results.append(result)

            debug_logger.log("ERROR", "Failed relative path validation", **result)

            return False

    def validate_absolute_path_detection(
        self, path: str, should_be_absolute: bool
    ) -> bool:
        """Validate absolute path detection.

        Args:
            path: Path to check
            should_be_absolute: Whether path should be detected as absolute

        Returns:
            True if detection is correct
        """
        path_obj = Path(path)
        is_absolute = path_obj.is_absolute()
        is_valid = is_absolute == should_be_absolute

        result = {
            "test": "absolute_path_detection",
            "path": path,
            "expected_absolute": should_be_absolute,
            "detected_absolute": is_absolute,
            "valid": is_valid,
        }
        self.validation_results.append(result)

        debug_logger.log("DEBUG", "Validated absolute path detection", **result)

        return is_valid

    def get_validation_summary(self) -> dict[str, Any]:
        """Get summary of all validation results.

        Returns:
            Summary dict with validation statistics
        """
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for result in self.validation_results if result["valid"])
        failed_tests = total_tests - passed_tests

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
            "results": self.validation_results,
        }

        debug_logger.log(
            "INFO",
            "Generated validation summary",
            **{k: v for k, v in summary.items() if k != "results"},
        )

        return summary


# Factory functions for easy test helper creation


def create_temp_file_structure(base_path: Path) -> TempFileStructureBuilder:
    """Create a temporary file structure builder.

    Args:
        base_path: Base path for the structure

    Returns:
        Configured TempFileStructureBuilder instance
    """
    return TempFileStructureBuilder(base_path)


def create_file_permission_mocker() -> FilePermissionMocker:
    """Create a file permission mocker.

    Returns:
        Configured FilePermissionMocker instance
    """
    return FilePermissionMocker()


def create_cross_platform_path_validator() -> CrossPlatformPathValidator:
    """Create a cross-platform path validator.

    Returns:
        Configured CrossPlatformPathValidator instance
    """
    return CrossPlatformPathValidator()
