"""Cross-platform path utilities for consistent path handling.

This module provides utilities to handle path operations consistently
across Windows and Unix-like systems, ensuring forward slash separators
and proper prefix handling for .specs/ directories.
"""

from pathlib import Path


def normalize_path_separators(path: str | Path) -> str:
    r"""Normalize path separators to forward slashes for cross-platform consistency.

    Args:
        path: Path to normalize (string or Path object)

    Returns:
        Path string with forward slashes as separators

    Examples:
        >>> normalize_path_separators("src\models\user.py")
        'src/models/user.py'
        >>> normalize_path_separators(Path("src/models/user.py"))
        'src/models/user.py'

    """
    return str(path).replace("\\", "/")


def remove_specs_prefix(path_str: str) -> str:
    r"""Remove .specs/ or .specs\ prefix from path in a cross-platform way.

    Args:
        path_str: Path string that may have .specs prefix

    Returns:
        Path string with .specs prefix removed and normalized separators

    Examples:
        >>> remove_specs_prefix(".specs/src/models/user.py")
        'src/models/user.py'
        >>> remove_specs_prefix(".specs\\src\\models\\user.py")
        'src/models/user.py'
        >>> remove_specs_prefix("src/models/user.py")
        'src/models/user.py'

    """
    # Handle both Unix and Windows style .specs prefixes
    specs_prefixes = [".specs/", ".specs\\"]

    for prefix in specs_prefixes:
        if path_str.startswith(prefix):
            # Remove prefix and normalize remaining path
            cleaned_path = path_str[len(prefix) :]
            return normalize_path_separators(cleaned_path)

    # No .specs prefix found, just normalize separators
    return normalize_path_separators(path_str)


def ensure_specs_prefix(path: str | Path) -> str:
    r"""Ensure path has .specs/ prefix with normalized separators.

    Args:
        path: Path that should have .specs/ prefix

    Returns:
        Path string with .specs/ prefix and normalized separators

    Examples:
        >>> ensure_specs_prefix("src/models/user.py")
        '.specs/src/models/user.py'
        >>> ensure_specs_prefix(".specs/src/models/user.py")
        '.specs/src/models/user.py'
        >>> ensure_specs_prefix(".specs\\src\\models\\user.py")
        '.specs/src/models/user.py'

    """
    normalized_path = normalize_path_separators(path)

    # If already has .specs prefix, normalize and return
    if normalized_path.startswith(".specs/"):
        return normalized_path

    # Remove any existing .specs prefix variants and add normalized one
    cleaned_path = remove_specs_prefix(normalized_path)
    return f".specs/{cleaned_path}"


def is_specs_path(path: str | Path) -> bool:
    r"""Check if path is under .specs/ directory (cross-platform).

    Args:
        path: Path to check

    Returns:
        True if path is under .specs/ directory

    Examples:
        >>> is_specs_path(".specs/src/models/user.py")
        True
        >>> is_specs_path(".specs\\src\\models\\user.py")
        True
        >>> is_specs_path("src/models/user.py")
        False

    """
    normalized_path = normalize_path_separators(path)
    return normalized_path.startswith(".specs/")


def convert_to_posix_style(path: str | Path) -> str:
    """Convert path to POSIX-style (forward slashes) regardless of platform.

    This is an alias for normalize_path_separators for semantic clarity.

    Args:
        path: Path to convert

    Returns:
        POSIX-style path string

    """
    return normalize_path_separators(path)
