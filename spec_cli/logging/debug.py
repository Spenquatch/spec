"""Debug logging utilities with structured output and timing capabilities.

Provides enhanced debug logging with environment-based configuration,
structured data support, and performance timing integration.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Any

from ..exceptions import SpecError


class DebugLogger:
    """Enhanced debug logging with structured output and timing capabilities."""

    def __init__(self) -> None:
        """Initialize debug logger with environment-based configuration."""
        self.enabled = self._is_debug_enabled()
        self.level = self._get_debug_level()
        self.timing_enabled = self._is_timing_enabled()
        self.logger = self._setup_logger()

    def _is_debug_enabled(self) -> bool:
        """Check if debug logging is enabled via environment."""
        debug_value = os.environ.get("SPEC_DEBUG", "").lower()
        return debug_value in ["1", "true", "yes"]

    def _get_debug_level(self) -> str:
        """Get debug level from environment."""
        return os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()

    def _is_timing_enabled(self) -> bool:
        """Check if performance timing is enabled."""
        timing_value = os.environ.get("SPEC_DEBUG_TIMING", "").lower()
        return timing_value in ["1", "true", "yes"]

    def _setup_logger(self) -> logging.Logger:
        """Set up the internal logger with appropriate configuration."""
        logger = logging.getLogger("spec_cli.debug")

        if not self.enabled:
            logger.setLevel(logging.CRITICAL + 1)  # Disable all logging
            return logger

        # Set level based on environment
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        logger.setLevel(level_map.get(self.level, logging.INFO))

        # Create console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[SPEC DEBUG] %(asctime)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False

        return logger

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message with structured data.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Primary log message
            **kwargs: Additional contextual data to include
        """
        if not self.enabled:
            return

        # Format structured data
        extra_data = ""
        if kwargs:
            extra_parts = [f"{key}={value}" for key, value in kwargs.items()]
            extra_data = f" ({', '.join(extra_parts)})"

        full_message = f"{message}{extra_data}"
        level_method = getattr(self.logger, level.lower(), self.logger.info)
        level_method(full_message)

    def log_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> None:
        """Log error with full context information.

        Args:
            error: Exception that occurred
            context: Additional context information
        """
        if not self.enabled:
            return

        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        # Add SpecError context if available
        if isinstance(error, SpecError):
            error_info.update(error.get_context())

        # Add additional context
        if context:
            error_info.update(context)

        self.log("ERROR", f"Exception occurred: {error}", **error_info)

    @contextmanager
    def timer(self, operation_name: str):  # type: ignore
        """Context manager for timing operations.

        Args:
            operation_name: Name of the operation being timed
        """
        if not self.timing_enabled:
            yield
            return

        start_time = time.perf_counter()
        self.log("INFO", f"Starting operation: {operation_name}")

        try:
            yield
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self.log(
                "ERROR",
                f"Operation failed: {operation_name}",
                duration_ms=f"{elapsed * 1000:.2f}ms",
                error=str(e),
            )
            raise
        finally:
            elapsed = time.perf_counter() - start_time
            self.log(
                "INFO",
                f"Completed operation: {operation_name}",
                duration_ms=f"{elapsed * 1000:.2f}ms",
            )

    def log_function_call(
        self,
        func_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Log function call with arguments.

        Args:
            func_name: Name of the function being called
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if not self.enabled:
            return

        call_info: dict[str, Any] = {"function": func_name}

        if args:
            call_info["args_count"] = len(args)
            # Only log first few args to avoid too much output
            if len(args) <= 3:
                call_info["args"] = str(args)

        if kwargs:
            call_info["kwargs_keys"] = list(kwargs.keys())

        self.log("DEBUG", f"Function call: {func_name}", **call_info)


# Global debug logger instance
debug_logger = DebugLogger()
