"""Path operation utilities for consistent path handling."""

import os
from pathlib import Path

from ..exceptions import SpecValidationError


def safe_relative_to(path: str | Path, root: str | Path, strict: bool = True) -> Path:
    """Safely compute relative path with consistent error handling.

    Args:
        path: Path to make relative (string or Path object)
        root: Root path to compute relative to (string or Path object)
        strict: If True, raise error when path is outside root.
               If False, return original path when outside root.

    Returns:
        Path relative to root, or original path if not strict

    Raises:
        TypeError: If path or root are not str or Path objects
        SpecValidationError: If path is outside root and strict=True

    Example:
        >>> safe_relative_to("/project/src/main.py", "/project")
        Path("src/main.py")
        >>> safe_relative_to("/outside/file.py", "/project", strict=False)
        Path("/outside/file.py")
    """
    if not isinstance(path, str | Path):
        raise TypeError(f"path must be str or Path, got {type(path)}")
    if not isinstance(root, str | Path):
        raise TypeError(f"root must be str or Path, got {type(root)}")

    path_obj = Path(path).resolve()
    root_obj = Path(root).resolve()

    try:
        relative = path_obj.relative_to(root_obj)
        return relative

    except ValueError as e:
        if strict:
            error_msg = f"Path '{path_obj}' is outside root '{root_obj}'"
            raise SpecValidationError(error_msg) from e

        # Non-strict mode: return original path
        return path_obj


def ensure_directory(path: str | Path, parents: bool = True) -> Path:
    """Create directory if it doesn't exist with consistent error handling.

    Args:
        path: Directory path to create (string or Path object)
        parents: Whether to create parent directories if they don't exist

    Returns:
        Path object of the created/existing directory

    Raises:
        TypeError: If path is not str or Path object
        SpecValidationError: If path exists but is not a directory
        OSError: If directory creation fails due to permissions or other OS issues

    Example:
        >>> ensure_directory("/project/.specs/docs")
        Path("/project/.specs/docs")
    """
    if not isinstance(path, str | Path):
        raise TypeError(f"path must be str or Path, got {type(path)}")

    path_obj = Path(path)

    # Check if path exists and is not a directory
    if path_obj.exists() and not path_obj.is_dir():
        raise SpecValidationError(f"Path '{path_obj}' exists but is not a directory")

    # Create directory if it doesn't exist
    if not path_obj.exists():
        path_obj.mkdir(parents=parents, exist_ok=True)

    return path_obj


def normalize_path(path: str | Path, resolve_symlinks: bool = True) -> Path:
    """Normalize path with consistent handling of strings and Path objects.

    Args:
        path: Path to normalize (string or Path object)
        resolve_symlinks: Whether to resolve symbolic links

    Returns:
        Normalized Path object (absolute path)

    Raises:
        TypeError: If path is not str or Path object

    Example:
        >>> normalize_path("./src/../main.py")
        Path("/current/working/directory/main.py")
        >>> normalize_path("/project/./docs")
        Path("/project/docs")
    """
    if not isinstance(path, str | Path):
        raise TypeError(f"path must be str or Path, got {type(path)}")

    path_obj = Path(path)

    if resolve_symlinks:
        return path_obj.resolve()
    else:
        # Make absolute without resolving symlinks
        if path_obj.is_absolute():
            return path_obj
        else:
            return Path.cwd() / path_obj


def resolve_project_root(start_path: str | Path | None = None) -> Path:
    """Find project root directory by looking for Git repository or spec markers.

    Args:
        start_path: Path to start searching from (defaults to current directory)

    Returns:
        Project root directory path

    Raises:
        TypeError: If start_path is not str, Path, or None

    Example:
        >>> resolve_project_root()
        Path("/project/root")
    """
    if start_path is not None and not isinstance(start_path, str | Path):
        raise TypeError(
            f"start_path must be str, Path, or None, got {type(start_path)}"
        )

    current_path = normalize_path(start_path or Path.cwd())

    # Walk up the directory tree looking for project markers
    for path in [current_path] + list(current_path.parents):
        # Check for .git directory (main Git repo)
        if (path / ".git").exists():
            return path

        # Check for .spec directory (spec repo)
        if (path / ".spec").exists():
            return path

        # Check for common project files
        project_markers = [
            "pyproject.toml",
            "setup.py",
            "package.json",
            "Cargo.toml",
            "go.mod",
            ".projectroot",
        ]

        for marker in project_markers:
            if (path / marker).exists():
                return path

    # If no project root found, return the starting directory
    return current_path


def is_subpath(child: str | Path, parent: str | Path) -> bool:
    """Check if child path is a subpath of parent path.

    Args:
        child: Child path to check
        parent: Parent path to check against

    Returns:
        True if child is a subpath of parent, False otherwise

    Raises:
        TypeError: If child or parent are not str or Path objects

    Example:
        >>> is_subpath("/project/src/main.py", "/project")
        True
        >>> is_subpath("/other/file.py", "/project")
        False
    """
    if not isinstance(child, str | Path):
        raise TypeError(f"child must be str or Path, got {type(child)}")
    if not isinstance(parent, str | Path):
        raise TypeError(f"parent must be str or Path, got {type(parent)}")

    try:
        child_path = normalize_path(child)
        parent_path = normalize_path(parent)
        child_path.relative_to(parent_path)
        return True
    except ValueError:
        return False


def get_relative_path_or_absolute(path: str | Path, base: str | Path) -> Path:
    """Get relative path if possible, otherwise return absolute path.

    Args:
        path: Path to make relative
        base: Base path to compute relative to

    Returns:
        Relative path if path is under base, otherwise absolute path

    Raises:
        TypeError: If path or base are not str or Path objects

    Example:
        >>> get_relative_path_or_absolute("/project/src/main.py", "/project")
        Path("src/main.py")
        >>> get_relative_path_or_absolute("/other/file.py", "/project")
        Path("/other/file.py")
    """
    if not isinstance(path, str | Path):
        raise TypeError(f"path must be str or Path, got {type(path)}")
    if not isinstance(base, str | Path):
        raise TypeError(f"base must be str or Path, got {type(base)}")

    try:
        return safe_relative_to(path, base, strict=True)
    except SpecValidationError:
        return normalize_path(path)


def ensure_path_permissions(path: str | Path, require_write: bool = False) -> None:
    """Check and ensure path has required permissions.

    Args:
        path: Path to check permissions for
        require_write: Whether write permission is required

    Raises:
        TypeError: If path is not str or Path object
        SpecValidationError: If path doesn't exist or lacks required permissions

    Example:
        >>> ensure_path_permissions("/project/.specs", require_write=True)
        # Passes if directory exists and is writable
    """
    if not isinstance(path, str | Path):
        raise TypeError(f"path must be str or Path, got {type(path)}")

    path_obj = Path(path)

    if not path_obj.exists():
        raise SpecValidationError(f"Path does not exist: {path_obj}")

    # Check read permission
    if not os.access(path_obj, os.R_OK):
        raise SpecValidationError(f"No read permission for path: {path_obj}")

    # Check write permission if required
    if require_write and not os.access(path_obj, os.W_OK):
        raise SpecValidationError(f"No write permission for path: {path_obj}")


# Cross-platform path utilities for .specs/ directory handling


def normalize_path_separators(path: str | Path) -> str:
    r"""Normalize path separators to forward slashes for cross-platform consistency.

    Args:
        path: Path to normalize (string or Path object)

    Returns:
        Path string with forward slashes as separators

    Examples:
        >>> normalize_path_separators("src\\models\\user.py")
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
