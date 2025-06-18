"""AI configuration loading system with cross-platform support."""

import logging
import os
from pathlib import Path
from typing import Any

from ...config.loader import ConfigurationLoader
from ...utils.path_utils import normalize_path_separators
from .settings import AIConfig

logger = logging.getLogger(__name__)


class AIConfigLoader:
    """Load AI configuration following existing spec config patterns."""

    def __init__(self, config_loader: ConfigurationLoader | None = None):
        """Initialize with optional existing config loader for integration.

        Args:
            config_loader: Optional existing configuration loader for integration
        """
        self.config_loader = config_loader

    def load_ai_config(self, config_path: Path | None = None) -> AIConfig:
        """Load AI configuration from pyproject.toml and environment variables.

        Args:
            config_path: Optional path to pyproject.toml file (normalized for cross-platform)

        Returns:
            AIConfig: Loaded and validated AI configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Normalize config path for cross-platform compatibility
        if config_path is not None:
            config_path = Path(normalize_path_separators(str(config_path)))

        # Try pyproject.toml first, then environment variables, then defaults
        config_data = {}

        # Load from pyproject.toml if available
        pyproject_data = self._load_from_pyproject(config_path)
        if pyproject_data:
            config_data.update(pyproject_data)

        # Override with environment variables
        env_data = self._load_from_env()
        if env_data:
            config_data.update(env_data)

        # Create and validate configuration
        try:
            return AIConfig(**config_data)
        except Exception as e:
            logger.error("Failed to load AI configuration: %s", e)
            # Fall back to defaults with AI disabled if configuration fails
            return AIConfig(enabled=False)

    def _load_from_pyproject(self, config_path: Path | None = None) -> dict[str, Any]:
        """Load AI config from pyproject.toml [tool.spec.ai] section.

        Args:
            config_path: Optional path to pyproject.toml file

        Returns:
            Dictionary containing AI configuration from pyproject.toml
        """
        try:
            # Use existing config loader to get pyproject.toml data
            if self.config_loader is None:
                # Create default config loader if not provided
                root_path = config_path.parent if config_path else Path.cwd()
                self.config_loader = ConfigurationLoader(root_path)

            # Load project configuration
            project_config = self.config_loader.load_configuration()

            # Extract AI-specific configuration from [tool.spec.ai]
            ai_config = project_config.get("ai", {})

            if ai_config:
                logger.debug("Loaded AI configuration from pyproject.toml")
                return dict(ai_config)

        except Exception as e:
            logger.debug("Could not load AI config from pyproject.toml: %s", e)

        return {}

    def _load_from_env(self) -> dict[str, Any]:
        """Load AI configuration from environment variables.

        Returns:
            Dictionary containing AI configuration from environment variables
        """
        env_config: dict[str, Any] = {}

        # Map environment variables to config keys (cross-platform support)
        env_mappings = {
            "SPEC_AI_ENABLED": ("enabled", bool),
            "SPEC_AI_PROVIDER": ("provider", str),
            "SPEC_AI_MODEL_NAME": ("local.model_name", str),
            "SPEC_AI_MAX_TOKENS": ("local.max_tokens", int),
            "SPEC_AI_TEMPERATURE": ("local.temperature", float),
            "SPEC_AI_CACHE_DIR": ("local.cache_dir", str),
            "SPEC_AI_DEVICE": ("local.device", str),
        }

        for env_key, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    # Convert to appropriate type
                    converted_value: Any
                    if value_type is bool:
                        converted_value = env_value.lower() in (
                            "true",
                            "1",
                            "yes",
                            "on",
                        )
                    elif value_type is int:
                        converted_value = int(env_value)
                    elif value_type is float:
                        converted_value = float(env_value)
                    else:
                        converted_value = env_value

                    # Normalize path values for cross-platform compatibility
                    if config_key.endswith("_dir") or config_key.endswith("cache_dir"):
                        if isinstance(converted_value, str):
                            converted_value = normalize_path_separators(converted_value)

                    # Handle nested config keys
                    self._set_nested_value(env_config, config_key, converted_value)

                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Invalid environment variable %s=%s: %s", env_key, env_value, e
                    )

        if env_config:
            logger.debug("Loaded AI configuration from environment variables")

        return env_config

    def _set_nested_value(
        self, config: dict[str, Any], key_path: str, value: Any
    ) -> None:
        """Set nested configuration value using dot notation.

        Args:
            config: Configuration dictionary to update
            key_path: Dot-separated key path (e.g., "local.model_name")
            value: Value to set
        """
        keys = key_path.split(".")
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value


# Convenience function for easy importing
def load_ai_config(config_path: Path | None = None) -> AIConfig:
    """Load AI configuration using default loader.

    Args:
        config_path: Optional path to pyproject.toml file

    Returns:
        AIConfig: Loaded and validated AI configuration
    """
    loader = AIConfigLoader()
    return loader.load_ai_config(config_path)
