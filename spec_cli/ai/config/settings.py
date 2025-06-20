"""AI configuration data models with validation using Pydantic."""

import re
import sys

from pydantic import BaseModel, Field, field_validator

from ...utils.path_utils import normalize_path_separators


class SecurityConfig(BaseModel):
    """Security configuration for AI integration."""

    sanitize_code: bool = Field(default=True)
    allowed_file_patterns: list[str] = Field(
        default_factory=lambda: ["*.py", "*.js", "*.ts"]
    )
    blocked_patterns: list[str] = Field(
        default_factory=lambda: [r"api[_-]?key", r"secret", r"password", r"token"]
    )
    max_file_size_kb: int = Field(default=100, ge=1, le=1000)

    @field_validator("blocked_patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate regex patterns are compileable."""
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e
        return v


class LocalModelConfig(BaseModel):
    """Configuration for local AI model."""

    model_name: str = Field(default="Qwen/Qwen2.5-Coder-0.5B-Instruct")
    max_tokens: int = Field(default=512, ge=50, le=2048)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    use_4bit: bool = Field(default=True)
    device: str = Field(default="auto")
    cache_enabled: bool = Field(default=True)
    cache_dir: str | None = Field(
        default=None, description="Cross-platform cache directory"
    )

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v: str | None) -> str | None:
        """Validate cache directory path and normalize for cross-platform use."""
        if v is None:
            return v

        # Normalize path separators for cross-platform compatibility
        normalized_path = normalize_path_separators(v)

        # Validate that the path is reasonable
        if len(normalized_path) > 255:
            raise ValueError(
                f"Cache directory path too long: {len(normalized_path)} chars"
            )

        return normalized_path


class MonitoringConfig(BaseModel):
    """Configuration for AI performance monitoring."""

    enabled: bool = Field(default=False, description="Enable performance monitoring")
    overhead_limit_percent: float = Field(
        default=5.0, ge=0.0, le=20.0, description="Maximum overhead percentage"
    )


class AIConfig(BaseModel):
    """AI integration configuration - AI is the primary documentation engine."""

    enabled: bool = Field(
        default=True,
        description="AI is the core feature - disable only for fallback mode",
    )
    provider: str = Field(
        default="local", description="Primary provider for AI documentation generation"
    )
    local: LocalModelConfig = Field(default_factory=LocalModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    fallback_to_templates: bool = Field(
        default=True, description="Use template fallback when AI unavailable"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider type with platform-specific considerations."""
        valid_providers = ["local", "disabled"]

        if v not in valid_providers:
            raise ValueError(
                f"Unsupported provider: {v}. Valid options: {valid_providers}"
            )

        # Platform-specific validation
        if v == "local":
            # Validate that platform can support local models
            if sys.platform not in ["darwin", "linux", "win32"]:
                raise ValueError(
                    f"Local AI provider not supported on platform: {sys.platform}"
                )

        return v
