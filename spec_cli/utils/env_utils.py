"""Environment variable utilities for consistent configuration management.

This module provides standardized functions for reading environment variables
with proper type conversion and default value handling.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, cast

from ..logging.debug import debug_logger


def get_env_str(key: str, default: str = "") -> str:
    """Get string environment variable with default fallback.

    Args:
        key: Environment variable name
        default: Default value if variable is not set

    Returns:
        Environment variable value as string, or default if not set

    Example:
        api_url = get_env_str("SPEC_API_URL", "https://api.example.com")
    """
    value = os.environ.get(key, default)

    debug_logger.log(
        "DEBUG",
        "Environment string variable retrieved",
        key=key,
        value_length=len(value),
        using_default=(value == default),
    )

    return value


def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable with default fallback.

    Args:
        key: Environment variable name
        default: Default value if variable is not set or invalid

    Returns:
        Environment variable value as integer, or default if not set/invalid

    Example:
        timeout = get_env_int("SPEC_TIMEOUT", 30)
    """
    value_str = os.environ.get(key)

    if value_str is None:
        debug_logger.log(
            "DEBUG",
            "Environment int variable not set, using default",
            key=key,
            default=default,
        )
        return default

    try:
        value = int(value_str)
        debug_logger.log(
            "DEBUG",
            "Environment int variable retrieved",
            key=key,
            value=value,
            using_default=False,
        )
        return value

    except ValueError:
        debug_logger.log(
            "WARNING",
            "Invalid integer environment variable, using default",
            key=key,
            invalid_value=value_str,
            default=default,
        )
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable with default fallback.

    Recognizes common boolean representations:
    - True: "1", "true", "yes", "on" (case-insensitive)
    - False: "0", "false", "no", "off" (case-insensitive)

    Args:
        key: Environment variable name
        default: Default value if variable is not set or invalid

    Returns:
        Environment variable value as boolean, or default if not set/invalid

    Example:
        debug_enabled = get_env_bool("SPEC_DEBUG", False)
    """
    value_str = os.environ.get(key)

    if value_str is None:
        debug_logger.log(
            "DEBUG",
            "Environment bool variable not set, using default",
            key=key,
            default=default,
        )
        return default

    # Normalize value for comparison
    normalized_value = value_str.lower().strip()

    # True values
    if normalized_value in ["1", "true", "yes", "on"]:
        debug_logger.log(
            "DEBUG",
            "Environment bool variable retrieved",
            key=key,
            value=True,
            raw_value=value_str,
            using_default=False,
        )
        return True

    # False values
    if normalized_value in ["0", "false", "no", "off"]:
        debug_logger.log(
            "DEBUG",
            "Environment bool variable retrieved",
            key=key,
            value=False,
            raw_value=value_str,
            using_default=False,
        )
        return False

    # Invalid value - use default
    debug_logger.log(
        "WARNING",
        "Invalid boolean environment variable, using default",
        key=key,
        invalid_value=value_str,
        default=default,
    )
    return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable with default fallback.

    Args:
        key: Environment variable name
        default: Default value if variable is not set or invalid

    Returns:
        Environment variable value as float, or default if not set/invalid

    Example:
        rate_limit = get_env_float("SPEC_RATE_LIMIT", 1.5)
    """
    value_str = os.environ.get(key)

    if value_str is None:
        debug_logger.log(
            "DEBUG",
            "Environment float variable not set, using default",
            key=key,
            default=default,
        )
        return default

    try:
        value = float(value_str)
        debug_logger.log(
            "DEBUG",
            "Environment float variable retrieved",
            key=key,
            value=value,
            using_default=False,
        )
        return value

    except ValueError:
        debug_logger.log(
            "WARNING",
            "Invalid float environment variable, using default",
            key=key,
            invalid_value=value_str,
            default=default,
        )
        return default


def validate_env_vars(required_vars: Dict[str, Any]) -> Dict[str, str]:
    """Validate that required environment variables are set.

    Args:
        required_vars: Dictionary mapping variable names to expected types

    Returns:
        Dictionary of validation errors (empty if all valid)

    Raises:
        ValueError: If any required variables are missing or invalid

    Example:
        errors = validate_env_vars({
            "SPEC_API_KEY": str,
            "SPEC_PORT": int,
            "SPEC_DEBUG": bool
        })
    """
    errors = {}

    for var_name, expected_type in required_vars.items():
        value = os.environ.get(var_name)

        if value is None:
            errors[var_name] = "Required environment variable not set"
            continue

        # Type validation
        if expected_type == int:
            try:
                int(value)
            except ValueError:
                errors[var_name] = f"Invalid integer value: {value}"
        elif expected_type == float:
            try:
                float(value)
            except ValueError:
                errors[var_name] = f"Invalid float value: {value}"
        elif expected_type == bool:
            normalized = value.lower().strip()
            if normalized not in ["1", "true", "yes", "on", "0", "false", "no", "off"]:
                errors[var_name] = f"Invalid boolean value: {value}"

    debug_logger.log(
        "INFO",
        "Environment variables validated",
        checked_count=len(required_vars),
        error_count=len(errors),
        errors=list(errors.keys()) if errors else None,
    )

    return errors


@dataclass
class EnvironmentConfig:
    """Standard environment configuration for spec-cli application.

    This dataclass provides a structured way to access common environment
    variables used throughout the spec-cli application with proper defaults
    and type safety.

    Attributes:
        debug: Enable debug mode (SPEC_DEBUG)
        debug_level: Debug logging level (SPEC_DEBUG_LEVEL)
        debug_timing: Enable debug timing (SPEC_DEBUG_TIMING)
        use_color: Enable color output (SPEC_USE_COLOR)
        console_width: Console width override (SPEC_CONSOLE_WIDTH)
        api_timeout: API request timeout in seconds (SPEC_API_TIMEOUT)
        max_retries: Maximum retry attempts (SPEC_MAX_RETRIES)
        config_file: Custom config file path (SPEC_CONFIG_FILE)
    """

    debug: bool = False
    debug_level: str = "INFO"
    debug_timing: bool = False
    use_color: bool = True
    console_width: int = 0  # 0 means auto-detect
    api_timeout: float = 30.0
    max_retries: int = 3
    config_file: str = ""

    @classmethod
    def from_environment(cls) -> "EnvironmentConfig":
        """Create EnvironmentConfig from current environment variables.

        Returns:
            EnvironmentConfig instance populated from environment

        Example:
            config = EnvironmentConfig.from_environment()
            if config.debug:
                print("Debug mode enabled")
        """
        debug_logger.log("DEBUG", "Loading environment configuration")

        config = cls(
            debug=get_env_bool("SPEC_DEBUG", False),
            debug_level=get_env_str("SPEC_DEBUG_LEVEL", "INFO").upper(),
            debug_timing=get_env_bool("SPEC_DEBUG_TIMING", False),
            use_color=get_env_bool("SPEC_USE_COLOR", True),
            console_width=get_env_int("SPEC_CONSOLE_WIDTH", 0),
            api_timeout=get_env_float("SPEC_API_TIMEOUT", 30.0),
            max_retries=get_env_int("SPEC_MAX_RETRIES", 3),
            config_file=get_env_str("SPEC_CONFIG_FILE", ""),
        )

        debug_logger.log(
            "INFO",
            "Environment configuration loaded",
            debug=config.debug,
            debug_level=config.debug_level,
            use_color=config.use_color,
            console_width=config.console_width or "auto",
            api_timeout=config.api_timeout,
            max_retries=config.max_retries,
            has_config_file=bool(config.config_file),
        )

        return config

    def validate(self) -> Dict[str, str]:
        """Validate the current configuration values.

        Returns:
            Dictionary of validation errors (empty if all valid)

        Example:
            config = EnvironmentConfig.from_environment()
            errors = config.validate()
            if errors:
                print(f"Configuration errors: {errors}")
        """
        errors = {}

        # Validate debug_level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.debug_level not in valid_levels:
            errors[
                "debug_level"
            ] = f"Invalid debug level '{self.debug_level}'. Must be one of: {valid_levels}"

        # Validate console_width
        if self.console_width < 0:
            errors[
                "console_width"
            ] = f"Console width must be >= 0, got {self.console_width}"
        elif self.console_width > 0 and self.console_width < 40:
            errors[
                "console_width"
            ] = f"Console width must be >= 40 if specified, got {self.console_width}"

        # Validate api_timeout
        if self.api_timeout <= 0:
            errors["api_timeout"] = f"API timeout must be > 0, got {self.api_timeout}"
        elif self.api_timeout > 300:  # 5 minutes max
            errors[
                "api_timeout"
            ] = f"API timeout too large (max 300s), got {self.api_timeout}"

        # Validate max_retries
        if self.max_retries < 0:
            errors["max_retries"] = f"Max retries must be >= 0, got {self.max_retries}"
        elif self.max_retries > 10:
            errors[
                "max_retries"
            ] = f"Max retries too large (max 10), got {self.max_retries}"

        debug_logger.log(
            "DEBUG",
            "Environment configuration validated",
            error_count=len(errors),
            errors=list(errors.keys()) if errors else None,
        )

        return errors

    def apply_overrides(self, **overrides: Any) -> "EnvironmentConfig":
        """Create new config with specified field overrides.

        Args:
            **overrides: Field names and values to override

        Returns:
            New EnvironmentConfig instance with overrides applied

        Example:
            config = EnvironmentConfig.from_environment()
            test_config = config.apply_overrides(debug=True, api_timeout=5.0)
        """
        # Create a copy of current values
        current_values = {
            "debug": self.debug,
            "debug_level": self.debug_level,
            "debug_timing": self.debug_timing,
            "use_color": self.use_color,
            "console_width": self.console_width,
            "api_timeout": self.api_timeout,
            "max_retries": self.max_retries,
            "config_file": self.config_file,
        }

        # Apply overrides
        current_values.update(overrides)

        debug_logger.log(
            "DEBUG",
            "Creating config with overrides",
            override_count=len(overrides),
            overrides=list(overrides.keys()),
        )

        return self.__class__(
            debug=cast(bool, current_values["debug"]),
            debug_level=cast(str, current_values["debug_level"]),
            debug_timing=cast(bool, current_values["debug_timing"]),
            use_color=cast(bool, current_values["use_color"]),
            console_width=cast(int, current_values["console_width"]),
            api_timeout=cast(float, current_values["api_timeout"]),
            max_retries=cast(int, current_values["max_retries"]),
            config_file=cast(str, current_values["config_file"]),
        )
