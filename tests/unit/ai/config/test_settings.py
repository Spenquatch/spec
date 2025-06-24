"""Tests for AI configuration models."""

import sys
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from spec_cli.ai.config.settings import AIConfig, LocalModelConfig, SecurityConfig

# Test constants
VALID_REGEX_PATTERN = r"test[_-]?pattern"
INVALID_REGEX_PATTERN = r"[invalid"
LONG_CACHE_PATH = "a" * 300
VALID_CACHE_PATH = "~/.cache/spec-cli"
MIN_TOKEN_LIMIT = 50
MAX_TOKEN_LIMIT = 2048
ABOVE_MAX_TOKEN_LIMIT = 3000
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 1.0
ABOVE_MAX_TEMPERATURE = 1.5
MIN_FILE_SIZE = 1
MAX_FILE_SIZE = 1000
ABOVE_MAX_FILE_SIZE = 1500
EXPECTED_NORMALIZED_CACHE_PATH = "~/.cache/spec-cli"


class TestSecurityConfig:
    """Test SecurityConfig model validation."""

    def test_security_config_uses_secure_defaults(self) -> None:
        """Verify all defaults are security-conscious."""
        config = SecurityConfig()

        assert config.sanitize_code is True
        assert config.allowed_file_patterns == ["*.py", "*.js", "*.ts"]
        assert config.blocked_patterns == [
            r"api[_-]?key",
            r"secret",
            r"password",
            r"token",
        ]
        assert config.max_file_size_kb == 100

    def test_security_config_validates_patterns_valid_regex(self) -> None:
        """Test valid regex patterns are accepted."""
        config = SecurityConfig(blocked_patterns=[VALID_REGEX_PATTERN])

        assert config.blocked_patterns == [VALID_REGEX_PATTERN]

    def test_security_config_validates_patterns_invalid_regex(self) -> None:
        """Test invalid regex patterns raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(blocked_patterns=[INVALID_REGEX_PATTERN])

        error_msg = str(exc_info.value)
        assert "Invalid regex pattern" in error_msg
        assert INVALID_REGEX_PATTERN in error_msg

    def test_security_config_validates_file_size_limits_within_bounds(self) -> None:
        """Test file size bounds are enforced - valid values."""
        config = SecurityConfig(max_file_size_kb=MIN_FILE_SIZE)
        assert config.max_file_size_kb == MIN_FILE_SIZE

        config = SecurityConfig(max_file_size_kb=MAX_FILE_SIZE)
        assert config.max_file_size_kb == MAX_FILE_SIZE

    def test_security_config_validates_file_size_limits_above_bounds(self) -> None:
        """Test file size bounds are enforced - invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(max_file_size_kb=ABOVE_MAX_FILE_SIZE)

        error_msg = str(exc_info.value)
        assert "Input should be less than or equal to" in error_msg

    def test_security_config_validates_file_size_limits_below_bounds(self) -> None:
        """Test file size bounds are enforced - zero value."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(max_file_size_kb=0)

        error_msg = str(exc_info.value)
        assert "Input should be greater than or equal to" in error_msg


class TestLocalModelConfig:
    """Test LocalModelConfig model validation."""

    def test_local_model_config_defaults(self) -> None:
        """Verify model configuration defaults."""
        config = LocalModelConfig()

        assert config.model_name == "Qwen/Qwen2.5-Coder-0.5B-Instruct"
        assert config.max_tokens == 512
        assert config.temperature == 0.1
        assert config.use_4bit is True
        assert config.device == "auto"
        assert config.cache_enabled is True
        assert config.cache_dir is None

    def test_local_model_config_validates_token_limits_within_bounds(self) -> None:
        """Test token bounds (50-2048)."""
        config = LocalModelConfig(max_tokens=MIN_TOKEN_LIMIT)
        assert config.max_tokens == MIN_TOKEN_LIMIT

        config = LocalModelConfig(max_tokens=MAX_TOKEN_LIMIT)
        assert config.max_tokens == MAX_TOKEN_LIMIT

    def test_local_model_config_validates_token_limits_above_bounds(self) -> None:
        """Test token bounds enforcement for values above limit."""
        with pytest.raises(ValidationError) as exc_info:
            LocalModelConfig(max_tokens=ABOVE_MAX_TOKEN_LIMIT)

        error_msg = str(exc_info.value)
        assert "Input should be less than or equal to" in error_msg

    def test_local_model_config_validates_token_limits_below_bounds(self) -> None:
        """Test token bounds enforcement for values below limit."""
        with pytest.raises(ValidationError) as exc_info:
            LocalModelConfig(max_tokens=MIN_TOKEN_LIMIT - 1)

        error_msg = str(exc_info.value)
        assert "Input should be greater than or equal to" in error_msg

    def test_local_model_config_validates_temperature_bounds_within_bounds(
        self,
    ) -> None:
        """Test temperature bounds (0.0-1.0)."""
        config = LocalModelConfig(temperature=MIN_TEMPERATURE)
        assert config.temperature == MIN_TEMPERATURE

        config = LocalModelConfig(temperature=MAX_TEMPERATURE)
        assert config.temperature == MAX_TEMPERATURE

    def test_local_model_config_validates_temperature_bounds_above_bounds(self) -> None:
        """Test temperature bounds enforcement for values above limit."""
        with pytest.raises(ValidationError) as exc_info:
            LocalModelConfig(temperature=ABOVE_MAX_TEMPERATURE)

        error_msg = str(exc_info.value)
        assert "Input should be less than or equal to" in error_msg

    def test_local_model_config_validates_temperature_bounds_below_bounds(self) -> None:
        """Test temperature bounds enforcement for values below limit."""
        with pytest.raises(ValidationError) as exc_info:
            LocalModelConfig(temperature=MIN_TEMPERATURE - 0.1)

        error_msg = str(exc_info.value)
        assert "Input should be greater than or equal to" in error_msg

    def test_local_model_config_cache_dir_normalization_none_value(self) -> None:
        """Test cross-platform cache path handling - None value."""
        config = LocalModelConfig(cache_dir=None)
        assert config.cache_dir is None

    def test_local_model_config_cache_dir_normalization_valid_path(self) -> None:
        """Test cross-platform cache path handling - valid path."""
        config = LocalModelConfig(cache_dir=VALID_CACHE_PATH)
        assert config.cache_dir == EXPECTED_NORMALIZED_CACHE_PATH

    def test_local_model_config_cache_dir_normalization_backslash_path(self) -> None:
        """Test cross-platform cache path handling - Windows-style path."""
        windows_path = "C:\\Users\\test\\.cache\\spec-cli"
        expected_normalized = "C:/Users/test/.cache/spec-cli"

        config = LocalModelConfig(cache_dir=windows_path)
        assert config.cache_dir == expected_normalized

    def test_local_model_config_cache_dir_normalization_too_long(self) -> None:
        """Test cache directory path length validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocalModelConfig(cache_dir=LONG_CACHE_PATH)

        error_msg = str(exc_info.value)
        assert "Cache directory path too long" in error_msg
        assert str(len(LONG_CACHE_PATH)) in error_msg


class TestAIConfig:
    """Test AIConfig model validation."""

    def test_ai_config_uses_secure_defaults(self) -> None:
        """Verify all defaults are security-conscious."""
        config = AIConfig()

        assert config.enabled is True
        assert config.provider == "local"
        assert isinstance(config.local, LocalModelConfig)
        assert isinstance(config.security, SecurityConfig)
        assert config.fallback_to_templates is True

    def test_ai_config_validates_provider_types_valid_providers(self) -> None:
        """Test valid/invalid provider values - valid providers."""
        config = AIConfig(provider="local")
        assert config.provider == "local"

        config = AIConfig(provider="llamacpp")
        assert config.provider == "llamacpp"

        config = AIConfig(provider="disabled")
        assert config.provider == "disabled"

    def test_ai_config_validates_provider_types_invalid_providers(self) -> None:
        """Test valid/invalid provider values - invalid providers."""
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(provider="openai")

        error_msg = str(exc_info.value)
        assert "Unsupported provider: openai" in error_msg
        assert "Valid options: ['local', 'llamacpp', 'disabled']" in error_msg

    def test_ai_config_validates_platform_support_supported_platforms(self) -> None:
        """Test platform-specific provider validation - supported platforms."""
        supported_platforms = ["darwin", "linux", "win32"]

        for platform in supported_platforms:
            with patch.object(sys, "platform", platform):
                config = AIConfig(provider="local")
                assert config.provider == "local"

    def test_ai_config_validates_platform_support_unsupported_platforms(self) -> None:
        """Test platform-specific provider validation - unsupported platforms."""
        unsupported_platform = "unknown_os"

        with patch.object(sys, "platform", unsupported_platform):
            with pytest.raises(ValidationError) as exc_info:
                AIConfig(provider="local")

            error_msg = str(exc_info.value)
            assert "Local AI provider not supported on platform" in error_msg
            assert unsupported_platform in error_msg

    def test_ai_config_validates_platform_support_disabled_provider_any_platform(
        self,
    ) -> None:
        """Test disabled provider works on any platform."""
        unsupported_platform = "unknown_os"

        with patch.object(sys, "platform", unsupported_platform):
            config = AIConfig(provider="disabled")
            assert config.provider == "disabled"

    def test_nested_config_validation_security_config(self) -> None:
        """Test nested model validation - SecurityConfig validation."""
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(security={"blocked_patterns": [INVALID_REGEX_PATTERN]})

        error_msg = str(exc_info.value)
        assert "Invalid regex pattern" in error_msg

    def test_nested_config_validation_local_model_config(self) -> None:
        """Test nested model validation - LocalModelConfig validation."""
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(local={"max_tokens": ABOVE_MAX_TOKEN_LIMIT})

        error_msg = str(exc_info.value)
        assert "Input should be less than or equal to" in error_msg

    def test_nested_config_validation_valid_nested_configs(self) -> None:
        """Test nested model validation - valid configurations."""
        config = AIConfig(
            provider="local",
            local={"max_tokens": 1024, "temperature": 0.5},
            security={"max_file_size_kb": 200},
        )

        assert config.provider == "local"
        assert config.local.max_tokens == 1024
        assert config.local.temperature == 0.5
        assert config.security.max_file_size_kb == 200
