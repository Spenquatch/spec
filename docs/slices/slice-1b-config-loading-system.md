# Slice 1b: Configuration Loading System

## Goal
Implement AI configuration loading that integrates with existing spec config patterns and supports pyproject.toml.

## Scope
- Configuration loading logic only (uses models from 1a)
- Integration with existing config system patterns
- pyproject.toml [tool.spec] section support
- Environment variable support following existing patterns

## Files to Create (≤3)
- `spec_cli/ai/config/loader.py` (≤120 lines, complexity ≤7)

## Classes/Services (≤2)
1. **AIConfigLoader** - Handles loading AI configuration from various sources

## McCabe Complexity (≤7 per function)
- **load_ai_config()**: ≤6 decision points (source checking, fallback logic)
- **_load_from_pyproject()**: ≤5 decision points (file existence, parsing, validation)
- **_load_from_env()**: ≤4 decision points (env var checking, type conversion)

## External Integrations (≤1)
- **0 external integrations** - Pure configuration loading logic

## Implementation

```python
# spec_cli/ai/config/loader.py
from typing import Optional, Dict, Any
from pathlib import Path
import os
import logging

from .settings import AIConfig
from ...config.loader import ConfigLoader  # Existing config loader patterns

logger = logging.getLogger(__name__)

class AIConfigLoader:
    """Load AI configuration following existing spec config patterns."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Initialize with optional existing config loader for integration."""
        self.config_loader = config_loader or ConfigLoader()

    def load_ai_config(self, config_path: Optional[Path] = None) -> AIConfig:
        """Load AI configuration from pyproject.toml and environment variables.

        Args:
            config_path: Optional path to pyproject.toml file

        Returns:
            AIConfig: Loaded and validated AI configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
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
            logger.error(f"Failed to load AI configuration: {e}")
            # Fall back to defaults with AI disabled if configuration fails
            return AIConfig(enabled=False)

    def _load_from_pyproject(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load AI config from pyproject.toml [tool.spec.ai] section."""
        try:
            # Use existing config loader to get pyproject.toml data
            project_config = self.config_loader.load_project_config(config_path)

            # Extract AI-specific configuration
            tool_spec = project_config.get('tool', {}).get('spec', {})
            ai_config = tool_spec.get('ai', {})

            if ai_config:
                logger.debug("Loaded AI configuration from pyproject.toml")
                return ai_config

        except Exception as e:
            logger.debug(f"Could not load AI config from pyproject.toml: {e}")

        return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """Load AI configuration from environment variables."""
        env_config = {}

        # Map environment variables to config keys
        env_mappings = {
            'SPEC_AI_ENABLED': ('enabled', bool),
            'SPEC_AI_PROVIDER': ('provider', str),
            'SPEC_AI_MODEL_NAME': ('local.model_name', str),
            'SPEC_AI_MAX_TOKENS': ('local.max_tokens', int),
            'SPEC_AI_TEMPERATURE': ('local.temperature', float),
        }

        for env_key, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    # Convert to appropriate type
                    if value_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        converted_value = int(env_value)
                    elif value_type == float:
                        converted_value = float(env_value)
                    else:
                        converted_value = env_value

                    # Handle nested config keys
                    self._set_nested_value(env_config, config_key, converted_value)

                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid environment variable {env_key}={env_value}: {e}")

        if env_config:
            logger.debug("Loaded AI configuration from environment variables")

        return env_config

    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        keys = key_path.split('.')
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value


# Convenience function for easy importing
def load_ai_config(config_path: Optional[Path] = None) -> AIConfig:
    """Load AI configuration using default loader."""
    loader = AIConfigLoader()
    return loader.load_ai_config(config_path)
```

## Inputs - EXPLICIT
- **config_path: Optional[Path]** - Path to pyproject.toml file (None uses default discovery)
- **Environment variables** - SPEC_AI_* prefixed variables for configuration override
- **AIConfig models** - From slice 1a for data structure definitions

## Actions - UNAMBIGUOUS
1. Load configuration from pyproject.toml [tool.spec.ai] section using existing config loader patterns
2. Override with environment variables using standard SPEC_AI_* naming convention
3. Create and validate AIConfig instance using models from slice 1a
4. Fall back to secure defaults if configuration loading fails
5. Log configuration loading process for debugging

## Outputs - WELL-DEFINED
- **Success**: `AIConfig` instance with validated configuration from all sources
- **Fallback**: `AIConfig(enabled=False)` if configuration loading fails but system should continue
- **Logging**: Debug/warning messages about configuration loading process

## Helper Dependencies
- **Existing helpers**: ConfigLoader from existing config system for pyproject.toml handling
- **Slice dependencies**: AIConfig models from slice 1a
- **Standard library**: `os`, `pathlib`, `logging` for environment and file operations

## Individual Test Scenarios (100% coverage achievable)
1. **test_loads_from_pyproject_toml** - Test successful pyproject.toml loading
2. **test_loads_from_environment_variables** - Test environment variable override
3. **test_environment_overrides_pyproject** - Test precedence of environment variables
4. **test_handles_missing_pyproject** - Test graceful handling of missing config file
5. **test_handles_invalid_pyproject_format** - Test invalid TOML format handling
6. **test_handles_invalid_environment_values** - Test invalid env var type conversion
7. **test_falls_back_to_defaults** - Test fallback to AIConfig defaults
8. **test_nested_config_key_setting** - Test dot notation environment variable mapping
9. **test_boolean_environment_conversion** - Test various boolean string formats
10. **test_numeric_environment_conversion** - Test int/float environment variable conversion

## Quality Assurance
- **Poetry compliance**: Uses existing config loader patterns, no new dependencies
- **Type safety**: Complete type annotations and error handling
- **Security clearance**: No secrets in logs, secure fallback behavior
- **Integration**: Follows existing spec config patterns for consistency

## Integration with Other Slices
- **Depends on Slice 1a**: Uses AIConfig models for validation and structure
- **Used by Slice 1c**: Code sanitizer will use loaded configuration
- **Used by later slices**: All AI components will use this loader
- **Interface**: Provides `load_ai_config()` function for easy importing

## Delivery Requirements
- **Independent execution**: Can be implemented after slice 1a is complete
- **Clear error handling**: Graceful fallback when configuration fails
- **Logging integration**: Uses existing logging patterns for debugging
- **Ready for integration**: Clean interface for use by all AI components

## Quality Gates
```bash
poetry run pytest tests/unit/ai/config/test_loader.py -v --cov=spec_cli.ai.config.loader --cov-fail-under=100
poetry run mypy spec_cli/ai/config/loader.py --strict
poetry run ruff check spec_cli/ai/config/loader.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
**Dependency**: Requires slice 1a completion (AIConfig models).
