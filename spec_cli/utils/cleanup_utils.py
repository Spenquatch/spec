"""Safe file removal and validation utilities for infrastructure cleanup.

This module provides utilities for safely removing infrastructure files
and validating that no remaining references exist in the codebase.
"""

import re
from pathlib import Path

from ..exceptions import InfrastructureRemovalError
from ..logging.debug import debug_logger
from .error_utils import create_error_context

def safe_file_removal(file_path: Path) -> bool:
    """Safely remove a file with error handling and validation.

    Args:
        file_path: Path to file to remove

    Returns:
        True if file was removed successfully, False if file didn't exist

    Raises:
        InfrastructureRemovalError: If file removal fails

    Example:
        >>> success = safe_file_removal(Path("spec_cli/utils/singleton.py"))
        >>> assert success is True  # File was removed
    """
    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a Path object")

    try:
        # Check if file exists
        if not file_path.exists():
            debug_logger.log(
                "INFO",
                "File does not exist - skipping removal",
                file_path=str(file_path),
            )
            return False

        # Validate it's actually a file, not a directory
        if not file_path.is_file():
            error_context = create_error_context(file_path)
            error_context.update({"operation": "file_removal", "issue": "not_a_file"})
            raise InfrastructureRemovalError(
                f"Path exists but is not a file: {file_path}", error_context
            )

        # Perform safe file removal with proper error handling
        file_path.unlink()

        debug_logger.log(
            "INFO",
            "File removed successfully",
            file_path=str(file_path),
            operation="safe_file_removal",
        )
        return True

    except InfrastructureRemovalError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        error_context = create_error_context(file_path)
        error_context.update({"operation": "file_removal", "error": str(e)})
        debug_logger.log(
            "ERROR",
            "Failed to remove file",
            file_path=str(file_path),
            error=str(e),
            error_context=error_context,
        )
        raise InfrastructureRemovalError(
            f"Failed to remove file {file_path}: {e}", error_context
        ) from e

def validate_no_references(
    codebase_path: Path, removed_modules: list[str]
) -> list[str]:
    """Validate no remaining references to removed modules exist in codebase.

    Args:
        codebase_path: Root path of codebase to search
        removed_modules: List of module names that were removed

    Returns:
        List of files containing references to removed modules (empty if clean)

    Raises:
        InfrastructureRemovalError: If validation process fails

    Example:
        >>> violations = validate_no_references(
        ...     Path("."), ["singleton", "compatibility"]
        ... )
        >>> assert len(violations) == 0  # No remaining references
    """
    if not isinstance(codebase_path, Path):
        raise TypeError("codebase_path must be a Path object")
    if not isinstance(removed_modules, list):
        raise TypeError("removed_modules must be a list")

    violations: list[str] = []

    try:
        # Build search patterns for removed modules
        import_patterns = []
        for module in removed_modules:
            # Match import statements and references
            patterns = [
                rf"from\s+.*{re.escape(module)}\s+import",
                rf"import\s+.*{re.escape(module)}",
                rf"{re.escape(module)}Meta",  # For SingletonMeta specifically
                rf"from.*{re.escape(module)}",
            ]
            import_patterns.extend(patterns)

        debug_logger.log(
            "INFO",
            "Starting reference validation",
            codebase_path=str(codebase_path),
            removed_modules=removed_modules,
            pattern_count=len(import_patterns),
        )

        # Search for Python files in codebase
        python_files = list(codebase_path.rglob("*.py"))

        # Exclude virtual environment and cache directories
        excluded_patterns = [".venv", "__pycache__", ".git", "site-packages"]
        python_files = [
            f
            for f in python_files
            if not any(pattern in str(f) for pattern in excluded_patterns)
        ]

        checked_files = 0
        for py_file in python_files:
            try:
                # Read file content
                content = py_file.read_text(encoding="utf-8")

                # Check for any pattern matches
                for pattern in import_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                        violations.append(str(py_file))
                        debug_logger.log(
                            "WARNING",
                            "Found reference to removed module",
                            file_path=str(py_file),
                            pattern=pattern,
                        )
                        break  # Only report each file once

                checked_files += 1

            except UnicodeDecodeError:
                # Skip files that can't be decoded as text
                debug_logger.log(
                    "DEBUG",
                    "Skipping non-text file",
                    file_path=str(py_file),
                )
                continue
            except Exception as e:
                debug_logger.log(
                    "WARNING",
                    "Error reading file during validation",
                    file_path=str(py_file),
                    error=str(e),
                )
                continue

        debug_logger.log(
            "INFO",
            "Reference validation completed",
            checked_files=checked_files,
            violations_found=len(violations),
        )

        return violations

    except Exception as e:
        error_context = create_error_context(codebase_path)
        error_context.update(
            {
                "operation": "reference_validation",
                "removed_modules": removed_modules,
                "error": str(e),
            }
        )
        debug_logger.log(
            "ERROR",
            "Reference validation failed",
            codebase_path=str(codebase_path),
            error=str(e),
            error_context=error_context,
        )
        raise InfrastructureRemovalError(
            f"Reference validation failed: {e}", error_context
        ) from e

def cleanup_singleton_infrastructure(codebase_path: Path) -> list[str]:
    """Remove singleton infrastructure files from codebase.

    Args:
        codebase_path: Root path of codebase

    Returns:
        List of files that were successfully removed

    Raises:
        InfrastructureRemovalError: If cleanup fails

    Example:
        >>> removed_files = cleanup_singleton_infrastructure(Path("."))
        >>> assert "spec_cli/utils/singleton.py" in removed_files
    """
    removed_files: list[str] = []

    try:
        debug_logger.log(
            "INFO",
            "Starting singleton infrastructure cleanup",
            codebase_path=str(codebase_path),
        )

        # Target singleton files to remove
        singleton_files = [
            codebase_path / "spec_cli" / "utils" / "singleton.py",
        ]

        for file_path in singleton_files:
            if safe_file_removal(file_path):
                removed_files.append(str(file_path))

        debug_logger.log(
            "INFO",
            "Singleton infrastructure cleanup completed",
            removed_files_count=len(removed_files),
            removed_files=removed_files,
        )

        return removed_files

    except Exception as e:
        error_context = create_error_context(codebase_path)
        error_context.update(
            {
                "operation": "singleton_infrastructure_cleanup",
                "removed_files": removed_files,
                "error": str(e),
            }
        )
        debug_logger.log(
            "ERROR",
            "Singleton infrastructure cleanup failed",
            codebase_path=str(codebase_path),
            error=str(e),
            error_context=error_context,
        )
        raise InfrastructureRemovalError(
            f"Singleton infrastructure cleanup failed: {e}", error_context
        ) from e

def cleanup_compatibility_layer(codebase_path: Path) -> list[str]:
    """Remove compatibility layer files from codebase.

    Args:
        codebase_path: Root path of codebase

    Returns:
        List of files that were successfully removed

    Raises:
        InfrastructureRemovalError: If cleanup fails

    Example:
        >>> removed_files = cleanup_compatibility_layer(Path("."))
        >>> assert "spec_cli/core/compatibility.py" in removed_files
    """
    removed_files: list[str] = []

    try:
        debug_logger.log(
            "INFO",
            "Starting compatibility layer cleanup",
            codebase_path=str(codebase_path),
        )

        # Target compatibility files to remove
        compatibility_files = [
            codebase_path / "spec_cli" / "core" / "compatibility.py",
        ]

        for file_path in compatibility_files:
            if safe_file_removal(file_path):
                removed_files.append(str(file_path))

        debug_logger.log(
            "INFO",
            "Compatibility layer cleanup completed",
            removed_files_count=len(removed_files),
            removed_files=removed_files,
        )

        return removed_files

    except Exception as e:
        error_context = create_error_context(codebase_path)
        error_context.update(
            {
                "operation": "compatibility_layer_cleanup",
                "removed_files": removed_files,
                "error": str(e),
            }
        )
        debug_logger.log(
            "ERROR",
            "Compatibility layer cleanup failed",
            codebase_path=str(codebase_path),
            error=str(e),
            error_context=error_context,
        )
        raise InfrastructureRemovalError(
            f"Compatibility layer cleanup failed: {e}", error_context
        ) from e
