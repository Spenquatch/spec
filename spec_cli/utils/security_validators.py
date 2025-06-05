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


def sanitize_error_message(
    error_message: str, command_context: str | None = None
) -> str:
    """Sanitize error messages to prevent information disclosure.

    Removes absolute paths and potentially sensitive command arguments while
    preserving actionable error information for debugging.

    Args:
        error_message: Original error message to sanitize
        command_context: Optional command context for additional filtering

    Returns:
        Sanitized error message with sensitive information removed

    Raises:
        TypeError: If error_message is not a string

    Example:
        >>> sanitize_error_message("fatal: repository '/Users/secret/project/.git' does not exist")
        "fatal: repository '<path>/.git' does not exist"
        >>> sanitize_error_message("git add --password=secret123 file.txt", "git")
        "git add <filtered> file.txt"
    """
    if not isinstance(error_message, str):
        raise TypeError(f"error_message must be str, got {type(error_message)}")

    sanitized = error_message

    # Decision point 1: Check for environment variable disclosure (do this first)
    if _contains_env_vars(sanitized):
        sanitized = _sanitize_env_vars(sanitized)

    # Decision point 2: Check for sensitive command arguments
    if command_context and _contains_sensitive_args(sanitized):
        sanitized = _sanitize_command_arguments(sanitized)

    # Decision point 3: Check for potential credentials
    if _contains_credentials(sanitized):
        sanitized = _sanitize_credentials(sanitized)

    # Decision point 4: Check for home directory paths
    if _contains_home_paths(sanitized):
        sanitized = _sanitize_home_paths(sanitized)

    # Decision point 5: Check for absolute path patterns (do this last)
    if _contains_absolute_paths(sanitized):
        sanitized = _sanitize_absolute_paths(sanitized)

    return sanitized


def _contains_absolute_paths(message: str) -> bool:
    """Check if message contains absolute file paths."""
    import re

    # Check for Unix absolute paths
    if re.search(r"/[^/\s]+(?:/[^/\s]*)*", message):
        return True
    # Check for Windows absolute paths
    if re.search(r"[A-Za-z]:[/\\][^\s]*", message):
        return True
    return False


def _sanitize_absolute_paths(message: str) -> str:
    """Replace absolute paths with sanitized placeholders."""
    import re

    # Replace Unix-style absolute paths (preserve surrounding quotes/delimiters)
    # Exclude already sanitized paths starting with placeholders
    message = re.sub(r"(?<!<home>)(/[^/\s<]+(?:/[^/\s'\"<]*)*)", r"<path>", message)
    # Replace Windows-style absolute paths
    message = re.sub(r"([A-Za-z]:[/\\][^\s'\"<]*)", r"<path>", message)
    return message


def _contains_sensitive_args(message: str) -> bool:
    """Check if message contains potentially sensitive command arguments."""
    sensitive_patterns = ["--password", "--token", "--key", "--secret", "--auth"]
    return any(pattern in message.lower() for pattern in sensitive_patterns)


def _sanitize_command_arguments(message: str) -> str:
    """Remove sensitive command line arguments."""
    import re

    # Replace sensitive arguments and their values
    sensitive_pattern = r"--(?:password|token|key|secret|auth)[=\s]+\S+"
    return re.sub(sensitive_pattern, "<filtered>", message, flags=re.IGNORECASE)


def _contains_credentials(message: str) -> bool:
    """Check if message contains credential-like strings."""
    import re

    # Look for patterns like API keys, tokens, etc.
    # Be more restrictive to avoid file path false positives
    credential_patterns = [
        r"\b[a-zA-Z0-9]{32,}\b",  # Long alphanumeric strings (word boundaries)
        r"\b[A-Za-z0-9+/]{20,}={1,2}(?=\s|$)",  # Base64 strings with padding
        r"\bsk-[a-zA-Z0-9]{32,}\b",  # API key format (e.g., OpenAI)
        r"\b[0-9a-f]{40,}\b",  # Hex strings (SHA hashes, etc.)
    ]
    return any(re.search(pattern, message) for pattern in credential_patterns)


def _sanitize_credentials(message: str) -> str:
    """Replace potential credential strings with placeholders."""
    import re

    # Replace specific API key formats first
    message = re.sub(r"\bsk-[a-zA-Z0-9]{32,}\b", "<api_key>", message)
    # Replace base64 strings with padding (do this before general token pattern)
    message = re.sub(r"\b[A-Za-z0-9+/]{20,}={1,2}(?=\s|$)", "<encoded>", message)
    # Replace hex strings (hashes)
    message = re.sub(r"\b[0-9a-f]{40,}\b", "<hash>", message)
    # Replace long alphanumeric strings (potential API keys) - be careful not to match paths
    message = re.sub(r"(?<!/)\b[a-zA-Z0-9]{32,}\b(?!/)", "<token>", message)
    return message


def _contains_env_vars(message: str) -> bool:
    """Check if message contains environment variable references."""
    return "${" in message or "$(" in message


def _sanitize_env_vars(message: str) -> str:
    """Replace environment variable references with placeholders."""
    import re

    # Replace ${VAR} and $(command) patterns
    message = re.sub(r"\$\{[^}]+\}", "<env_var>", message)
    message = re.sub(r"\$\([^)]+\)", "<command>", message)
    return message


def _contains_home_paths(message: str) -> bool:
    """Check if message contains home directory paths."""
    return "~/" in message or "/Users/" in message or "/home/" in message


def _sanitize_home_paths(message: str) -> str:
    """Replace home directory paths with generic placeholders."""
    import re

    # Replace home directory references
    message = re.sub(r"~/([^\s'\"]*)", r"<home>/<path>", message)
    message = re.sub(r"/Users/[^/\s'\"]+(/[^\s'\"]*)?", r"<home>\1", message)
    message = re.sub(r"/home/[^/\s'\"]+(/[^\s'\"]*)?", r"<home>\1", message)
    return message
