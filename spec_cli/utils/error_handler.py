"""Centralized error handling using error utilities."""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from ..exceptions import SpecError
from ..logging.debug import debug_logger
from .error_utils import (
    create_error_context,
    handle_os_error,
    handle_subprocess_error,
)
from .security_validators import sanitize_error_message

F = TypeVar("F", bound=Callable[..., Any])


class ErrorHandler:
    """Centralized error handling with context information."""

    def __init__(self, default_context: dict[str, Any] | None = None):
        """Initialize error handler with optional default context.

        Args:
            default_context: Default context to include in all error reports
        """
        self.default_context = default_context or {}

    def wrap(self, func: F) -> F:
        """Wrap functions with consistent error handling.

        Args:
            func: Function to wrap with error handling

        Returns:
            Wrapped function with error handling

        Example:
            @error_handler.wrap
            def risky_operation(path: str):
                return Path(path).read_text()
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.report(e, f"execute {func.__name__}", args=args, kwargs=kwargs)
                raise

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__qualname__ = func.__qualname__

        return wrapper  # type: ignore

    def report(
        self,
        exc: Exception,
        operation: str,
        code_path: Path | None = None,
        **additional_context: Any,
    ) -> None:
        """Report error with structured context information.

        Args:
            exc: Exception that occurred
            operation: Description of what operation was being performed
            code_path: Optional path related to the error
            **additional_context: Additional context information

        Example:
            try:
                result = dangerous_operation()
            except Exception as e:
                error_handler.report(e, "dangerous operation", code_path=Path("file.py"))
                raise
        """
        # Build context from multiple sources
        context = dict(self.default_context)
        context.update(additional_context)
        context["operation"] = operation

        # Add path-specific context if provided
        if code_path:
            try:
                path_context = create_error_context(code_path)
                context.update(path_context)
            except Exception:
                # Don't let context creation errors interfere with main error reporting
                context["path_context_error"] = str(code_path)

        # Format error message based on exception type
        if isinstance(exc, OSError):
            formatted_message = handle_os_error(exc)
            context["error_type"] = "os_error"
        elif isinstance(exc, subprocess.SubprocessError):
            formatted_message = handle_subprocess_error(exc)
            context["error_type"] = "subprocess_error"
        elif isinstance(exc, SpecError):
            formatted_message = exc.get_user_message()
            context["error_type"] = "spec_error"
            # Add SpecError's own context
            context.update(exc.get_context())
        else:
            formatted_message = str(exc)
            context["error_type"] = "generic_error"

        # Sanitize error message to prevent information disclosure
        command_context = context.get("command_context")
        sanitized_message = sanitize_error_message(formatted_message, command_context)

        # Log the error with sanitized message and full context
        debug_logger.log(
            "ERROR",
            f"Error in {operation}: {sanitized_message}",
            exception_type=type(exc).__name__,
            original_message=formatted_message,  # Keep original for debugging
            **context,
        )

    def log_and_raise(
        self,
        exc: Exception,
        operation: str,
        reraise_as: type | None = None,
        code_path: Path | None = None,
        **additional_context: Any,
    ) -> None:
        """Log error and re-raise as different exception type if needed.

        Args:
            exc: Original exception
            operation: Description of operation
            reraise_as: Exception type to raise instead of original
            code_path: Optional path related to the error
            **additional_context: Additional context information

        Raises:
            reraise_as: If specified, raises this exception type
            exc: Otherwise re-raises original exception

        Example:
            try:
                result = risky_operation()
            except OSError as e:
                error_handler.log_and_raise(
                    e, "file operation", reraise_as=SpecFileError
                )
        """
        # First report the error
        self.report(exc, operation, code_path=code_path, **additional_context)

        # Then re-raise appropriately
        if reraise_as:
            if isinstance(exc, OSError):
                message = handle_os_error(exc)
            elif isinstance(exc, subprocess.SubprocessError):
                message = handle_subprocess_error(exc)
            else:
                message = str(exc)

            # Sanitize error message for user-facing exception
            command_context = additional_context.get("command_context")
            sanitized_message = sanitize_error_message(message, command_context)
            raise reraise_as(f"Failed to {operation}: {sanitized_message}") from exc
        else:
            raise exc


# Default error handler instance for module-level usage
default_error_handler = ErrorHandler()
