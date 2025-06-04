"""Error handling utilities for consistent error formatting and context."""

import subprocess
from pathlib import Path
from typing import Any, Dict


def handle_os_error(exc: OSError) -> str:
    """Format OSError messages with consistent context.

    Args:
        exc: OSError exception to format

    Returns:
        Formatted error message string

    Raises:
        TypeError: If exc is not an OSError

    Example:
        >>> import os
        >>> try:
        ...     os.open('/nonexistent', os.O_RDONLY)
        ... except OSError as e:
        ...     formatted = handle_os_error(e)
        ...     print(formatted)  # "Permission denied (errno 13): /nonexistent"
    """
    if not isinstance(exc, OSError):
        raise TypeError(f"Expected OSError, got {type(exc)}")

    # Extract error details
    error_code = getattr(exc, "errno", None)
    filename = getattr(exc, "filename", None)
    strerror = getattr(exc, "strerror", str(exc)) or str(exc)

    # Build formatted message
    message_parts = [strerror]

    if error_code is not None:
        message_parts[0] = f"{strerror} (errno {error_code})"

    if filename:
        message_parts.append(f": {filename}")

    return "".join(message_parts)


def handle_subprocess_error(exc: subprocess.SubprocessError) -> str:
    """Format subprocess errors with command details.

    Args:
        exc: SubprocessError exception to format

    Returns:
        Formatted error message string

    Raises:
        TypeError: If exc is not a SubprocessError

    Example:
        >>> import subprocess
        >>> try:
        ...     subprocess.run(['false'], check=True)
        ... except subprocess.CalledProcessError as e:
        ...     formatted = handle_subprocess_error(e)
        ...     print(formatted)  # "Command failed (exit 1): false"
    """
    if not isinstance(exc, subprocess.SubprocessError):
        raise TypeError(f"Expected SubprocessError, got {type(exc)}")

    if isinstance(exc, subprocess.CalledProcessError):
        # Format CalledProcessError with command and return code
        cmd_str = " ".join(exc.cmd) if isinstance(exc.cmd, list) else str(exc.cmd)
        message = f"Command failed (exit {exc.returncode}): {cmd_str}"

        # Add stderr if available and not empty
        if hasattr(exc, "stderr") and exc.stderr:
            stderr_str = (
                exc.stderr.strip() if isinstance(exc.stderr, str) else str(exc.stderr)
            )
            if stderr_str:
                message += f"\nStderr: {stderr_str}"

        # Add stdout if available and not empty
        if hasattr(exc, "stdout") and exc.stdout:
            stdout_str = (
                exc.stdout.strip() if isinstance(exc.stdout, str) else str(exc.stdout)
            )
            if stdout_str:
                message += f"\nStdout: {stdout_str}"

        return message

    elif isinstance(exc, subprocess.TimeoutExpired):
        # Format TimeoutExpired
        cmd_str = " ".join(exc.cmd) if isinstance(exc.cmd, list) else str(exc.cmd)
        return f"Command timed out after {exc.timeout}s: {cmd_str}"

    else:
        # Generic SubprocessError
        return f"Subprocess error: {str(exc)}"


def create_error_context(code_path: Path) -> Dict[str, Any]:
    """Create standardized error context dictionary.

    Args:
        code_path: Path related to the error for context

    Returns:
        Dictionary containing standardized error context

    Raises:
        TypeError: If code_path is not a Path object

    Example:
        >>> from pathlib import Path
        >>> context = create_error_context(Path("src/main.py"))
        >>> print(context["file_path"])  # "src/main.py"
        >>> print(context["file_exists"])  # True or False
    """
    if not isinstance(code_path, Path):
        raise TypeError(f"Expected Path object, got {type(code_path)}")

    context: Dict[str, Any] = {
        "file_path": str(code_path),
        "file_exists": code_path.exists(),
    }

    # Add file-specific information if it exists
    if code_path.exists():
        context.update(
            {
                "is_file": code_path.is_file(),
                "is_dir": code_path.is_dir(),
                "absolute_path": str(code_path.resolve()),
            }
        )

        if code_path.is_file():
            try:
                context["file_size"] = code_path.stat().st_size
            except OSError:
                # Ignore stat errors, just continue without size info
                pass

    # Add parent directory information
    parent = code_path.parent
    context.update(
        {
            "parent_path": str(parent),
            "parent_exists": parent.exists(),
        }
    )

    return context
