import pytest

from spec_cli.templates.config import TemplateConfig, TemplateValidator
from spec_cli.templates.defaults import (
    DEFAULT_HISTORY_TEMPLATE,
    DEFAULT_INDEX_TEMPLATE,
    TEMPLATE_PRESETS,
    get_comprehensive_template_config,
    get_default_template_config,
    get_minimal_template_config,
    get_template_preset,
)


class TestDefaultTemplates:
    """Test default template configurations."""

    def test_default_template_config_has_valid_structure(self) -> None:
        """Test that default template config is valid."""
        config = get_default_template_config()

        assert isinstance(config, TemplateConfig)
        assert config.version == "1.0"
        assert len(config.index) > 100  # Substantial content
        assert len(config.history) > 100

        # Check required placeholders are present
        assert "{{filename}}" in config.index
        assert "{{filename}}" in config.history
        assert "{{filepath}}" in config.index

        # Validate with validator
        validator = TemplateValidator()
        issues = validator.validate_config(config)
        assert issues == []  # Should have no validation issues

    def test_minimal_template_config_is_valid(self) -> None:
        """Test that minimal template config is valid."""
        config = get_minimal_template_config()

        assert isinstance(config, TemplateConfig)
        assert len(config.index) > 50  # Should have reasonable content
        assert len(config.history) > 30

        # Check required placeholders
        assert "{{filename}}" in config.index
        assert "{{filename}}" in config.history

        # Should be shorter than default
        default_config = get_default_template_config()
        assert len(config.index) < len(default_config.index)
        assert len(config.history) < len(default_config.history)

        # Validate
        validator = TemplateValidator()
        issues = validator.validate_config(config)
        assert issues == []

    def test_comprehensive_template_config_is_valid(self) -> None:
        """Test that comprehensive template config is valid."""
        config = get_comprehensive_template_config()

        assert isinstance(config, TemplateConfig)
        assert len(config.index) > 200  # Should have extensive content
        assert len(config.history) > 200

        # Check required placeholders
        assert "{{filename}}" in config.index
        assert "{{filename}}" in config.history

        # Should be longer than default
        default_config = get_default_template_config()
        assert len(config.index) > len(default_config.index)
        assert len(config.history) > len(default_config.history)

        # Check for additional comprehensive sections
        assert "architecture" in config.index.lower()
        assert "design patterns" in config.index.lower()
        assert "monitoring" in config.index.lower()

        # Validate
        validator = TemplateValidator()
        issues = validator.validate_config(config)
        assert issues == []

    def test_template_presets_are_accessible(self) -> None:
        """Test that template presets can be accessed."""
        assert "default" in TEMPLATE_PRESETS
        assert "minimal" in TEMPLATE_PRESETS
        assert "comprehensive" in TEMPLATE_PRESETS

        # Test each preset
        for preset_name in TEMPLATE_PRESETS:
            config = get_template_preset(preset_name)
            assert isinstance(config, TemplateConfig)

            # Each should have required placeholders
            assert "{{filename}}" in config.index
            assert "{{filename}}" in config.history

    def test_template_presets_handle_unknown_names(self) -> None:
        """Test error handling for unknown preset names."""
        with pytest.raises(ValueError) as exc_info:
            get_template_preset("nonexistent")

        assert "Unknown template preset" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

        # Should list available presets
        error_msg = str(exc_info.value)
        assert "default" in error_msg
        assert "minimal" in error_msg
        assert "comprehensive" in error_msg


class TestTemplateConstants:
    """Test template constants and their structure."""

    def test_default_index_template_structure(self) -> None:
        """Test the structure of the default index template."""
        template = DEFAULT_INDEX_TEMPLATE

        # Check for main sections
        assert "# {{filename}}" in template
        assert "## Purpose" in template
        assert "## Overview" in template
        assert "## Key Responsibilities" in template
        assert "## Dependencies" in template
        assert "## Usage Examples" in template
        assert "## Configuration" in template
        assert "## Error Handling" in template
        assert "## Testing" in template
        assert "## Performance Considerations" in template
        assert "## Security Considerations" in template
        assert "## Future Enhancements" in template

        # Check for required placeholders
        required_placeholders = [
            "{{filename}}",
            "{{filepath}}",
            "{{file_type}}",
            "{{date}}",
            "{{purpose}}",
            "{{overview}}",
            "{{responsibilities}}",
            "{{dependencies}}",
            "{{api_interface}}",
            "{{example_usage}}",
            "{{configuration}}",
            "{{error_handling}}",
            "{{testing_notes}}",
            "{{performance_notes}}",
            "{{security_notes}}",
            "{{future_enhancements}}",
            "{{related_docs}}",
            "{{notes}}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in template, f"Missing placeholder: {placeholder}"

        # Check for proper markdown structure
        assert template.startswith("# {{filename}}")
        assert "```{{file_extension}}" in template
        assert "Generated by spec-cli" in template

    def test_default_history_template_structure(self) -> None:
        """Test the structure of the default history template."""
        template = DEFAULT_HISTORY_TEMPLATE

        # Check for main sections
        assert "# History for {{filename}}" in template
        assert "## {{date}} - Initial Creation" in template
        assert "## Change Log" in template
        assert "## Templates for Future Entries" in template

        # Check for required placeholders
        required_placeholders = [
            "{{filename}}",
            "{{filepath}}",
            "{{date}}",
            "{{context}}",
            "{{initial_purpose}}",
            "{{decisions}}",
            "{{implementation_notes}}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in template, f"Missing placeholder: {placeholder}"

        # Check for change log templates
        assert "### Feature Addition" in template
        assert "### Bug Fix" in template
        assert "### Refactoring" in template

        # Check for proper structure
        assert template.startswith("# History for {{filename}}")
        assert "History maintained by spec-cli" in template


class TestTemplateVariations:
    """Test variations between different template presets."""

    def test_template_sizes_are_appropriate(self) -> None:
        """Test that template sizes follow expected hierarchy."""
        minimal = get_minimal_template_config()
        default = get_default_template_config()
        comprehensive = get_comprehensive_template_config()

        # Size hierarchy: minimal < default < comprehensive
        assert len(minimal.index) < len(default.index)
        assert len(default.index) < len(comprehensive.index)

        assert len(minimal.history) <= len(default.history)
        assert len(default.history) < len(comprehensive.history)

    def test_all_templates_have_required_sections(self) -> None:
        """Test that all templates have essential sections."""
        configs = [
            get_minimal_template_config(),
            get_default_template_config(),
            get_comprehensive_template_config(),
        ]

        for config in configs:
            # All should have filename as header
            assert config.index.startswith("# {{filename}}")
            assert config.history.startswith("# History for {{filename}}")

            # All should have purpose and overview
            assert "purpose" in config.index.lower()
            assert "overview" in config.index.lower()

            # All should have usage or example section
            usage_present = any(
                keyword in config.index.lower() for keyword in ["usage", "example"]
            )
            assert usage_present

    def test_comprehensive_template_has_advanced_sections(self) -> None:
        """Test that comprehensive template has advanced sections."""
        config = get_comprehensive_template_config()

        advanced_sections = [
            "architecture",
            "design patterns",
            "code quality",
            "monitoring",
            "troubleshooting",
            "migration guide",
        ]

        for section in advanced_sections:
            assert section.lower() in config.index.lower(), (
                f"Missing section: {section}"
            )

        # History should also have advanced sections
        history_sections = [
            "architecture evolution",
            "performance impact",
            "security implications",
            "technical debt",
            "future planning",
        ]

        for section in history_sections:
            assert section.lower() in config.history.lower(), (
                f"Missing history section: {section}"
            )

    def test_templates_use_consistent_placeholder_style(self) -> None:
        """Test that all templates use consistent placeholder formatting."""
        configs = [
            get_minimal_template_config(),
            get_default_template_config(),
            get_comprehensive_template_config(),
        ]

        for config in configs:
            # Extract placeholders
            placeholders = config.get_placeholders_in_templates()

            # All placeholders should be lowercase with underscores
            for placeholder in placeholders:
                assert (
                    placeholder.islower() or placeholder.replace("_", "").islower()
                ), f"Placeholder not lowercase: {placeholder}"

                # Should not contain spaces or special characters
                assert " " not in placeholder
                assert all(c.isalnum() or c == "_" for c in placeholder)


class TestTemplateIntegration:
    """Test template integration with other components."""

    def test_templates_integrate_with_validator(self) -> None:
        """Test that all default templates pass validation."""
        validator = TemplateValidator()

        for preset_name in TEMPLATE_PRESETS:
            config = get_template_preset(preset_name)
            issues = validator.validate_config(config)
            assert issues == [], f"Validation issues in {preset_name}: {issues}"

    def test_templates_have_comprehensive_variable_coverage(self) -> None:
        """Test that templates use a good variety of available variables."""
        config = get_default_template_config()
        available_vars = set(config.get_available_variables().keys())
        used_vars = config.get_placeholders_in_templates()

        # Should use a reasonable percentage of available variables
        usage_ratio = len(used_vars) / len(available_vars)
        assert usage_ratio >= 0.3, (
            f"Templates only use {usage_ratio:.1%} of available variables"
        )

        # Should include essential variables
        essential_vars = {
            "filename",
            "filepath",
            "purpose",
            "overview",
            "example_usage",
            "date",
            "context",
        }
        assert essential_vars.issubset(used_vars), (
            f"Missing essential variables: {essential_vars - used_vars}"
        )

    def test_template_preset_consistency(self) -> None:
        """Test that template presets are consistent in structure."""
        presets = ["default", "minimal", "comprehensive"]

        for preset_name in presets:
            config = get_template_preset(preset_name)

            # All should have same basic structure
            assert config.version == "1.0"
            assert config.ai_enabled is False
            assert config.preserve_manual_edits is True

            # All should have proper markdown headers
            assert config.index.startswith("# {{filename}}")
            assert "History for {{filename}}" in config.history
