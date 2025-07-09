"""Factory utilities for environment detection and input validation.

This module provides utilities for factory interface implementations including
environment detection and factory input validation for context creation.
"""

import inspect
import os
import sys
from typing import Any

from ..logging.debug import debug_logger


def detect_environment_type() -> str:
    """Detect the current execution environment type.

    Analyzes the execution context to determine if running in CLI, testing,
    or other environments for appropriate factory selection.

    Returns:
        Environment type: "cli", "testing", or "unknown"

    Example:
        env_type = detect_environment_type()
        if env_type == "testing":
            factory = TestingContextFactory()
        elif env_type == "cli":
            factory = CLIContextFactory()
    """
    # Check if running under pytest
    if "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv):
        debug_logger.log(
            "DEBUG",
            "Environment detected as testing",
            reason="pytest_detected",
            argv_contains_pytest=any("pytest" in arg for arg in sys.argv),
            pytest_in_modules="pytest" in sys.modules,
        )
        return "testing"

    # Check for test environment variables
    if os.environ.get("SPEC_ENV") == "testing" or os.environ.get("TESTING"):
        debug_logger.log(
            "DEBUG",
            "Environment detected as testing",
            reason="environment_variables",
            spec_env=os.environ.get("SPEC_ENV"),
            testing_env=os.environ.get("TESTING"),
        )
        return "testing"

    # Check if running from CLI entry point
    frame = inspect.currentframe()
    try:
        # Walk up the call stack to find CLI indicators
        while frame:
            if frame.f_code.co_filename.endswith("spec_cli/cli.py"):
                debug_logger.log(
                    "DEBUG",
                    "Environment detected as CLI",
                    reason="cli_entry_point",
                    filename=frame.f_code.co_filename,
                )
                return "cli"
            frame = frame.f_back
    finally:
        del frame

    # Check for CLI arguments
    if len(sys.argv) > 0 and any("spec" in arg or "cli" in arg for arg in sys.argv):
        debug_logger.log(
            "DEBUG",
            "Environment detected as CLI",
            reason="cli_arguments",
            argv=sys.argv,
        )
        return "cli"

    debug_logger.log(
        "DEBUG",
        "Environment type unknown",
        reason="no_clear_indicators",
        argv=sys.argv,
        modules=list(sys.modules.keys())[:10],
    )
    return "unknown"


def validate_factory_inputs(**kwargs: Any) -> dict[str, Any]:
    """Validate and normalize factory input parameters.

    Validates factory configuration parameters and returns normalized
    values with appropriate defaults and type conversions.

    Args:
        **kwargs: Factory configuration parameters to validate

    Returns:
        Dictionary with validated and normalized factory inputs

    Raises:
        ValueError: If required parameters missing or invalid types
        TypeError: If parameter types cannot be converted

    Example:
        config = validate_factory_inputs(
            factory_type="context",
            timeout=30,
            debug_mode=True
        )
    """
    debug_logger.log(
        "DEBUG",
        "Validating factory inputs",
        input_count=len(kwargs),
        input_keys=list(kwargs.keys()),
    )

    validated: dict[str, Any] = {}

    # Validate factory_type if provided
    if "factory_type" in kwargs:
        factory_type = kwargs["factory_type"]
        if not isinstance(factory_type, str):
            raise TypeError(f"factory_type must be string, got {type(factory_type)}")
        if not factory_type.strip():
            raise ValueError("factory_type cannot be empty")
        validated["factory_type"] = factory_type.strip().lower()
        debug_logger.log(
            "DEBUG",
            "Factory type validated",
            factory_type=validated["factory_type"],
        )

    # Validate timeout if provided
    if "timeout" in kwargs:
        timeout = kwargs["timeout"]
        if isinstance(timeout, str):
            try:
                timeout = int(timeout)
            except ValueError as exc:
                raise TypeError(
                    f"timeout must be convertible to int, got '{timeout}'"
                ) from exc
        if not isinstance(timeout, int):
            raise TypeError(f"timeout must be int, got {type(timeout)}")
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")
        validated["timeout"] = timeout
        debug_logger.log("DEBUG", "Timeout validated", timeout=timeout)

    # Validate debug_mode if provided
    if "debug_mode" in kwargs:
        debug_mode = kwargs["debug_mode"]
        if isinstance(debug_mode, str):
            debug_mode = debug_mode.lower() in ("true", "1", "yes", "on")
        if not isinstance(debug_mode, bool):
            raise TypeError(
                f"debug_mode must be bool or convertible, got {type(debug_mode)}"
            )
        validated["debug_mode"] = debug_mode
        debug_logger.log("DEBUG", "Debug mode validated", debug_mode=debug_mode)

    # Validate factory_config if provided
    if "factory_config" in kwargs:
        factory_config = kwargs["factory_config"]
        if not isinstance(factory_config, dict):
            raise TypeError(f"factory_config must be dict, got {type(factory_config)}")
        validated["factory_config"] = factory_config.copy()
        debug_logger.log(
            "DEBUG",
            "Factory config validated",
            config_keys=list(factory_config.keys()),
        )

    # Add any unvalidated parameters with warning
    for key, value in kwargs.items():
        if key not in validated:
            debug_logger.log(
                "DEBUG",
                "Unvalidated parameter passed through",
                parameter=key,
                value_type=type(value).__name__,
            )
            validated[key] = value

    debug_logger.log(
        "DEBUG",
        "Factory inputs validation completed",
        validated_count=len(validated),
        validated_keys=list(validated.keys()),
    )

    return validated
