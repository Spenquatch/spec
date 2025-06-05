"""Path conversion utilities for Git operations in different contexts.

Handles conversion between absolute paths, .specs/ prefixed paths, and
Git work tree relative paths for cross-platform compatibility.
"""

from pathlib import Path
from typing import Any

from ..file_system.path_utils import normalize_path_separators, remove_specs_prefix
from ..logging.debug import debug_logger


class GitPathConverter:
    """Converts paths between different Git contexts (.specs/, relative, absolute)."""

    def __init__(self, specs_dir: Path):
        """Initialize path converter with specs directory configuration.

        Args:
            specs_dir: Path to the .specs working tree directory
        """
        self.specs_dir = specs_dir
        debug_logger.log(
            "INFO", "GitPathConverter initialized", specs_dir=str(specs_dir)
        )

    def convert_to_git_path(self, path: str | Path) -> str:
        """Convert path to be relative to Git work tree (.specs/).

        Args:
            path: Path to convert (can be absolute, relative, or .specs/ prefixed)

        Returns:
            Path relative to Git work tree
        """
        path_obj = Path(path)
        path_str = str(path)

        debug_logger.log("DEBUG", "Converting path to Git context", input_path=path_str)

        # Handle absolute paths
        if path_obj.is_absolute():
            try:
                # Try to make it relative to .specs/ directory
                relative_path = path_obj.relative_to(self.specs_dir)
                result = normalize_path_separators(relative_path)
                debug_logger.log(
                    "DEBUG",
                    "Converted absolute path",
                    absolute=path_str,
                    relative=result,
                )
                return result
            except ValueError:
                # Path is not under .specs/, return as-is
                debug_logger.log(
                    "DEBUG",
                    "Absolute path not under .specs/, returning as-is",
                    path=path_str,
                )
                return path_str

        # Handle .specs/ or .specs\ prefixed paths using cross-platform utility
        if path_str.startswith((".specs/", ".specs\\")):
            result = remove_specs_prefix(path_str)
            debug_logger.log(
                "DEBUG",
                "Removed .specs prefix (cross-platform)",
                original=path_str,
                result=result,
            )
            return result

        # Path is already relative, return as-is (but normalize separators)
        result = normalize_path_separators(path_obj)
        debug_logger.log(
            "DEBUG",
            "Path already relative, normalized separators",
            original=path_str,
            result=result,
        )
        return result

    def convert_from_git_path(self, git_path: str | Path) -> Path:
        """Convert path from Git work tree context to .specs/ prefixed path.

        Args:
            git_path: Path relative to Git work tree

        Returns:
            Path with .specs/ prefix (always uses forward slashes)
        """
        git_path_str = str(git_path)

        debug_logger.log("DEBUG", "Converting from Git context", git_path=git_path_str)

        # Normalize path separators using utility
        normalized_path = normalize_path_separators(git_path_str)

        # Add .specs/ prefix if not already present and ensure forward slashes
        if not normalized_path.startswith(".specs/"):
            result_str = f".specs/{normalized_path}"
        else:
            result_str = normalized_path

        # Create Path object from normalized string
        result = Path(result_str)

        debug_logger.log(
            "DEBUG",
            "Converted from Git context",
            git_path=git_path_str,
            result=result_str,
        )

        return result

    def convert_to_absolute_specs_path(self, path: str | Path) -> Path:
        """Convert path to absolute path under .specs/ directory.

        Args:
            path: Path to convert

        Returns:
            Absolute path under .specs/ directory
        """
        path_str = str(path)

        debug_logger.log(
            "DEBUG", "Converting to absolute .specs/ path", input_path=path_str
        )

        # Convert to Git path first (removes .specs/ prefix if present)
        git_path = self.convert_to_git_path(path)

        # Create absolute path under .specs/
        absolute_path = self.specs_dir / git_path

        debug_logger.log(
            "DEBUG",
            "Converted to absolute .specs/ path",
            input_path=path_str,
            git_path=git_path,
            absolute=str(absolute_path),
        )

        return absolute_path

    def is_under_specs_dir(self, path: str | Path) -> bool:
        """Check if path is under the .specs/ directory.

        Args:
            path: Path to check

        Returns:
            True if path is under .specs/ directory
        """
        path_obj = Path(path)

        # Convert to absolute path if relative
        if not path_obj.is_absolute():
            # Try to interpret as relative to .specs/
            test_path = self.specs_dir / path_obj
        else:
            test_path = path_obj

        try:
            test_path.relative_to(self.specs_dir)
            debug_logger.log("DEBUG", "Path is under .specs/ directory", path=str(path))
            return True
        except ValueError:
            debug_logger.log(
                "DEBUG", "Path is not under .specs/ directory", path=str(path)
            )
            return False

    def normalize_path_separators(self, path: str | Path) -> str:
        """Normalize path separators to forward slashes.

        Args:
            path: Path to normalize

        Returns:
            Path with normalized separators
        """
        normalized = normalize_path_separators(path)
        debug_logger.log(
            "DEBUG",
            "Normalized path separators",
            original=str(path),
            normalized=normalized,
        )
        return normalized

    def get_conversion_info(self, path: str | Path) -> dict[str, Any]:
        """Get detailed information about path conversion.

        Args:
            path: Path to analyze

        Returns:
            Dictionary with conversion information
        """
        path_str = str(path)
        path_obj = Path(path)

        info = {
            "original_path": path_str,
            "is_absolute": path_obj.is_absolute(),
            "has_specs_prefix": path_str.startswith((".specs/", ".specs\\")),
            "is_under_specs_dir": self.is_under_specs_dir(path),
            "git_path": self.convert_to_git_path(path),
            "specs_prefixed_path": normalize_path_separators(
                self.convert_from_git_path(self.convert_to_git_path(path))
            ),
            "absolute_specs_path": str(self.convert_to_absolute_specs_path(path)),
            "normalized_separators": self.normalize_path_separators(path),
        }

        debug_logger.log(
            "DEBUG",
            "Path conversion info generated",
            original=path_str,
            conversions=len(info),
        )

        return info
