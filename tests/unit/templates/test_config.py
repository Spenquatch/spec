import pytest
from pydantic import ValidationError

from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.config import TemplateConfig, TemplateValidator


class TestTemplateConfig:
    """Test TemplateConfig Pydantic model."""

    def test_template_config_validates_required_placeholders(self) -> None:
        """Test that required placeholders are validated."""
        # Valid templates with required placeholders
        config = TemplateConfig(
            index="# {{filename}}\nContent here",
            history="# History for {{filename}}\nHistory here",
        )
        assert config.index == "# {{filename}}\nContent here"
        assert config.history == "# History for {{filename}}\nHistory here"

        # Invalid - missing required placeholder
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                index="# Missing filename placeholder",
                history="# History for {{filename}}\nHistory here",
            )
        assert "filename" in str(exc_info.value)

    def test_template_config_rejects_empty_templates(self) -> None:
        """Test that empty templates are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(index="", history="# {{filename}}")
        assert (
            "should have at least" in str(exc_info.value)
            or "empty" in str(exc_info.value).lower()
        )

        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(index="# {{filename}}", history="")
        assert (
            "should have at least" in str(exc_info.value)
            or "empty" in str(exc_info.value).lower()
        )

        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(index="   ", history="# {{filename}}")
        error_msg = str(exc_info.value).lower()
        assert "empty" in error_msg or "should have at least" in error_msg

    def test_template_config_validates_balanced_braces(self) -> None:
        """Test that unbalanced braces are detected."""
        # Missing closing brace
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                index="# {{filename}\nMissing closing brace", history="# {{filename}}"
            )
        assert "unmatched braces" in str(exc_info.value)

        # Missing opening brace
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                index="# filename}}\nMissing opening brace", history="# {{filename}}"
            )
        assert "unmatched braces" in str(exc_info.value)

    def test_template_config_detects_malformed_placeholders(self) -> None:
        """Test that malformed placeholders are detected."""
        # Single brace placeholders
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(index="# {{filename}}\n{invalid}", history="# {{filename}}")
        assert "malformed single braces" in str(
            exc_info.value
        ) or "malformed placeholders" in str(exc_info.value)

        # Mixed valid and invalid
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                index="# {{filename}}\n{also_invalid}", history="# {{filename}}"
            )
        assert "malformed single braces" in str(
            exc_info.value
        ) or "malformed placeholders" in str(exc_info.value)

    def test_template_config_provides_available_variables(self) -> None:
        """Test that available variables are documented."""
        config = TemplateConfig(index="# {{filename}}", history="# {{filename}}")
        variables = config.get_available_variables()

        # Check required variables are present
        assert "filename" in variables
        assert "filepath" in variables
        assert "file_type" in variables
        assert "date" in variables
        assert "purpose" in variables

        # Check descriptions are provided
        assert isinstance(variables["filename"], str)
        assert len(variables["filename"]) > 0

        # Check we have a reasonable number of variables
        assert len(variables) >= 20

    def test_template_config_extracts_used_placeholders(self) -> None:
        """Test that placeholders are extracted correctly."""
        config = TemplateConfig(
            index="# {{filename}}\n**Location**: {{filepath}}\n{{purpose}}",
            history="# {{filename}} history\n{{context}} and {{decisions}}",
        )
        placeholders = config.get_placeholders_in_templates()

        expected = {"filename", "filepath", "purpose", "context", "decisions"}
        assert placeholders == expected

    def test_template_config_validates_ai_settings(self) -> None:
        """Test AI configuration validation."""
        # Valid AI config
        config = TemplateConfig(
            index="# {{filename}}",
            history="# {{filename}}",
            ai_enabled=True,
            ai_model="gpt-4",
            ai_temperature=0.5,
            ai_max_tokens=2000,
        )
        assert config.ai_enabled is True
        assert config.ai_model == "gpt-4"

        # Invalid - AI enabled but no model
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                index="# {{filename}}",
                history="# {{filename}}",
                ai_enabled=True,
                ai_model="",
            )
        assert "AI model cannot be empty" in str(exc_info.value)

        # Invalid temperature range
        with pytest.raises(ValidationError):
            TemplateConfig(
                index="# {{filename}}", history="# {{filename}}", ai_temperature=1.5
            )

        # Invalid token range
        with pytest.raises(ValidationError):
            TemplateConfig(
                index="# {{filename}}", history="# {{filename}}", ai_max_tokens=50
            )

    def test_template_config_rejects_unknown_fields(self) -> None:
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(  # type: ignore[call-arg]  # Testing invalid args
                index="# {{filename}}",
                history="# {{filename}}",
                unknown_field="should not be allowed",
            )
        error_msg = str(exc_info.value).lower()
        assert (
            "extra fields not permitted" in error_msg
            or "extra inputs are not permitted" in error_msg
        )

    def test_template_config_serializes_to_dict(self) -> None:
        """Test serialization to dictionary."""
        config = TemplateConfig(
            index="# {{filename}}",
            history="# {{filename}}",
            version="2.0",
            description="Test template",
            ai_enabled=True,
            ai_model="gpt-3.5-turbo",
        )

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["index"] == "# {{filename}}"
        assert data["history"] == "# {{filename}}"
        assert data["version"] == "2.0"
        assert data["description"] == "Test template"
        assert data["ai_enabled"] is True
        assert data["ai_model"] == "gpt-3.5-turbo"


class TestTemplateValidator:
    """Test TemplateValidator class."""

    def test_template_validator_validates_complete_config(self) -> None:
        """Test validation of complete configuration."""
        validator = TemplateValidator()

        # Valid configuration with required placeholders
        config = TemplateConfig(
            index="""# {{filename}}

**Location**: {{filepath}}

## Purpose
{{purpose}}

## Overview
{{overview}}

## Usage
```{{file_extension}}
{{example_usage}}
```
""",
            history="# History for {{filename}}\n\n{{filepath}}\n\n## {{date}} - Initial Creation\n{{context}}",
        )

        issues = validator.validate_config(config)
        assert issues == []

    def test_template_validator_detects_missing_sections(self) -> None:
        """Test detection of missing recommended sections."""
        validator = TemplateValidator()

        # Template missing too many recommended sections
        config = TemplateConfig(
            index="# {{filename}}\nMinimal content only", history="# {{filename}}"
        )

        issues = validator.validate_config(config)
        assert any("missing recommended sections" in issue for issue in issues)

    def test_template_validator_validates_markdown_structure(self) -> None:
        """Test validation of markdown structure."""
        validator = TemplateValidator()

        # Templates not starting with headers
        config = TemplateConfig(
            index="No header {{filename}}", history="Also no header {{filename}}"
        )

        issues = validator.validate_config(config)
        assert any("should start with a markdown header" in issue for issue in issues)

    def test_template_validator_validates_ai_configuration(self) -> None:
        """Test AI configuration validation."""
        validator = TemplateValidator()

        # AI enabled but no model
        config = TemplateConfig(
            index="# {{filename}}", history="# {{filename}}", ai_enabled=True
        )

        issues = validator.validate_config(config)
        assert any("AI model must be specified" in issue for issue in issues)

        # Temperature warnings
        config = TemplateConfig(
            index="# {{filename}}",
            history="# {{filename}}",
            ai_enabled=True,
            ai_model="gpt-4",
            ai_temperature=0.05,  # Very low
        )

        issues = validator.validate_config(config)
        assert any("temperature is very low" in issue for issue in issues)

    def test_template_validator_provides_helpful_error_messages(self) -> None:
        """Test that error messages are helpful."""
        validator = TemplateValidator()

        config = TemplateConfig(
            index="# {{filename}}\n{{unknown_placeholder}}", history="# {{filename}}"
        )

        issues = validator.validate_config(config)
        assert any("Unknown placeholders" in issue for issue in issues)
        assert any("unknown_placeholder" in issue for issue in issues)

    def test_template_validator_raises_on_invalid_config(self) -> None:
        """Test that validator raises exception for invalid config."""
        validator = TemplateValidator()

        config = TemplateConfig(
            index="# {{filename}}\n{{invalid_var}}", history="# {{filename}}"
        )

        with pytest.raises(SpecTemplateError) as exc_info:
            validator.validate_and_raise(config)

        assert "validation failed" in str(exc_info.value).lower()
        assert "invalid_var" in str(exc_info.value)
