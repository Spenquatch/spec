"""Security validation utilities for safe command execution."""

from pathlib import Path

from ..exceptions import SpecValidationError
from .path_utils import safe_relative_to

# Whitelist of allowed git commands for spec operations
ALLOWED_GIT_COMMANDS = {
    "add",
    "commit",
    "status",
    "log",
    "diff",
    "show",
    "init",
}


def validate_git_command(
    git_args: list[str], work_tree_path: Path | None = None
) -> tuple[bool, str | None]:
    """Validate git command arguments against security whitelist.

    Validates that the git command is in the allowed whitelist and that
    any file path arguments are safe from directory traversal attacks.

    Args:
        git_args: List of git command arguments (e.g., ["add", "file.txt"])
        work_tree_path: Optional work tree path for validating file arguments

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
        If invalid, error_message contains the specific security issue.

    Raises:
        TypeError: If git_args is not a list or contains non-string elements

    Example:
        >>> validate_git_command(["add", "file.txt"])
        (True, None)
        >>> validate_git_command(["rm", "-rf", "/"])
        (False, "Git command 'rm' not allowed")
        >>> validate_git_command(["add", "../../../etc/passwd"], Path("/work"))
        (False, "File path '../../../etc/passwd' is outside work tree")
    """
    if not isinstance(git_args, list):
        raise TypeError(f"git_args must be a list, got {type(git_args)}")

    if not git_args:
        return False, "Empty git command"

    # Validate all arguments are strings
    for i, arg in enumerate(git_args):
        if not isinstance(arg, str):
            raise TypeError(f"git_args[{i}] must be str, got {type(arg)}")

    # Extract and validate the git command
    git_command = git_args[0]

    if git_command not in ALLOWED_GIT_COMMANDS:
        return False, f"Git command '{git_command}' not allowed"

    # Validate file path arguments if work_tree_path is provided
    if work_tree_path is not None:
        validation_result = _validate_git_file_paths(git_args[1:], work_tree_path)
        if validation_result is not None:
            return False, validation_result

    return True, None


def _validate_git_file_paths(file_args: list[str], work_tree_path: Path) -> str | None:
    """Validate git file path arguments for directory traversal prevention.

    Args:
        file_args: List of file arguments from git command
        work_tree_path: Work tree root path for validation

    Returns:
        Error message if validation fails, None if all paths are safe
    """
    for arg in file_args:
        # Skip git flags (start with -)
        if arg.startswith("-"):
            continue

        # Skip non-path arguments
        if not _looks_like_file_path(arg):
            continue

        try:
            safe_relative_to(arg, work_tree_path, strict=True)
        except SpecValidationError:
            return f"File path '{arg}' is outside work tree"
        except Exception as e:
            # Convert any other path validation errors to security error
            return f"Invalid file path '{arg}': {str(e)}"

    return None


def _looks_like_file_path(arg: str) -> bool:
    """Heuristic check if argument looks like a file path.

    Args:
        arg: Command argument to check

    Returns:
        True if argument appears to be a file path
    """
    # Skip obvious non-file arguments
    if "=" in arg:  # Likely a flag like --author=name
        return False

    # Skip common Git references that aren't file paths
    git_refs = {"HEAD", "HEAD~1", "HEAD^", "origin", "main", "master", "@"}
    if arg in git_refs or arg.startswith("origin/") or arg.startswith("refs/"):
        return False

    # Consider it a file path if it contains path separators
    if "/" in arg or "\\" in arg:
        return True

    # Consider simple names as potential file paths (but exclude common git refs)
    # This allows for files like "README", "Makefile" etc.
    return not arg.isupper() or "." in arg
