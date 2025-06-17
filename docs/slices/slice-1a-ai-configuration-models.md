# Slice 1a: AI Configuration Models

## Goal
Implement AI configuration data models with validation using Pydantic, following existing config patterns.

## Scope
- Configuration data models only (no loading logic)
- Pydantic models with validation
- Security configuration patterns
- Integration with existing config system patterns

## Files to Create (≤3)
- `spec_cli/ai/config/settings.py` (≤150 lines, complexity ≤7)

## Classes/Services (≤2)
1. **AIConfig** - Main AI configuration model
2. **SecurityConfig** - Security-specific configuration (nested within AIConfig)

## McCabe Complexity (≤7 per function)
- **Configuration validation**: ≤5 decision points (provider validation, bounds checking)
- **Default factory methods**: ≤3 decision points (simple conditionals)
- **Security pattern validation**: ≤6 decision points (pattern matching, file size checks)

## External Integrations (≤1)
- **0 external integrations** - Pure data models and validation

## Implementation

```python
# spec_cli/ai/config/settings.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from pathlib import Path

class SecurityConfig(BaseModel):
    """Security configuration for AI integration."""
    sanitize_code: bool = Field(default=True)
    allowed_file_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.js", "*.ts"])
    blocked_patterns: List[str] = Field(default_factory=lambda: [
        r"api[_-]?key", r"secret", r"password", r"token"
    ])
    max_file_size_kb: int = Field(default=100, ge=1, le=1000)

    @validator('blocked_patterns')
    def validate_patterns(cls, v):
        """Validate regex patterns are compileable."""
        import re
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
        return v

class LocalModelConfig(BaseModel):
    """Configuration for local AI model."""
    model_name: str = Field(default="Qwen/Qwen2.5-Coder-0.5B-Instruct")
    max_tokens: int = Field(default=512, ge=50, le=2048)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    use_4bit: bool = Field(default=True)
    device: str = Field(default="auto")
    cache_enabled: bool = Field(default=True)

class AIConfig(BaseModel):
    """AI integration configuration - AI is the primary documentation engine."""
    enabled: bool = Field(default=True, description="AI is the core feature - disable only for fallback mode")
    provider: str = Field(default="local", description="Primary provider for AI documentation generation")
    local: LocalModelConfig = Field(default_factory=LocalModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    fallback_to_templates: bool = Field(default=True, description="Use template fallback when AI unavailable")

    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider type."""
        if v not in ['local', 'disabled']:
            raise ValueError(f"Unsupported provider: {v}")
        return v
```

## Inputs - EXPLICIT
- **No runtime inputs** - Pure data model definitions
- **Configuration data**: Dict from pyproject.toml or environment variables (handled by slice 1b)

## Actions - UNAMBIGUOUS
1. Define Pydantic models with complete type safety
2. Implement field validation with clear error messages
3. Provide secure defaults for all configuration options
4. Validate regex patterns and numeric bounds

## Outputs - WELL-DEFINED
- **AIConfig model class** - Ready for instantiation by configuration loader
- **SecurityConfig model class** - Embedded in AIConfig
- **LocalModelConfig model class** - Embedded in AIConfig
- **Validation errors** - Clear Pydantic validation messages when invalid data provided

## Helper Dependencies
- **Existing helpers**: None required (pure Pydantic models)
- **Standard library**: `re` module for regex validation
- **Third-party**: `pydantic` for model definitions

## Individual Test Scenarios (100% coverage achievable)
1. **test_ai_config_uses_secure_defaults** - Verify all defaults are security-conscious
2. **test_ai_config_validates_provider_types** - Test valid/invalid provider values
3. **test_ai_config_validates_token_limits** - Test token bounds (50-2048)
4. **test_ai_config_validates_temperature_bounds** - Test temperature bounds (0.0-1.0)
5. **test_security_config_validates_patterns** - Test regex pattern compilation
6. **test_security_config_validates_file_size_limits** - Test file size bounds
7. **test_local_model_config_defaults** - Verify model configuration defaults
8. **test_nested_config_validation** - Test nested model validation

## Quality Assurance
- **Poetry compliance**: Pydantic dependency managed via Poetry
- **Type safety**: Complete type annotations for all fields
- **Security clearance**: Secure defaults, no secrets exposure
- **Cross-platform**: Pure Python, no OS-specific dependencies

## Integration with Next Slices
- **Used by Slice 1b**: Configuration loader will instantiate these models
- **Used by Slice 1c**: Code sanitizer will use SecurityConfig
- **Interface**: Models exported for import by other slices

## Delivery Requirements
- **Independent execution**: Can be implemented and tested in complete isolation
- **No external dependencies**: No calls to external services or complex integrations
- **Clear validation**: All edge cases covered with specific error messages
- **Ready for integration**: Clean interfaces for use by dependent slices

## Quality Gates
```bash
poetry run pytest tests/unit/ai/config/test_settings.py -v --cov=spec_cli.ai.config.settings --cov-fail-under=100
poetry run mypy spec_cli/ai/config/settings.py --strict
poetry run ruff check spec_cli/ai/config/settings.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
