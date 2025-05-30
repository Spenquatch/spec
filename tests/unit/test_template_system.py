"""Unit tests for template system functionality."""

from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from spec_cli.__main__ import TEMPLATE_FILE, TemplateConfig, load_template


class TestTemplateConfig:
    """Test the TemplateConfig Pydantic model."""

    def test_template_config_default_values(self):
        """Test that TemplateConfig has proper default values."""
        config = TemplateConfig()

        assert isinstance(config.index, str)
        assert isinstance(config.history, str)
        assert len(config.index) > 0
        assert len(config.history) > 0
        assert "{{filename}}" in config.index
        assert "{{filename}}" in config.history

    def test_template_config_custom_values(self):
        """Test that TemplateConfig accepts custom values."""
        custom_index = "# Custom Index Template for {{filename}}"
        custom_history = "# Custom History Template for {{filename}}"

        config = TemplateConfig(index=custom_index, history=custom_history)

        assert config.index == custom_index
        assert config.history == custom_history

    def test_template_config_validates_required_fields(self):
        """Test that TemplateConfig validates field types."""
        # Should work with strings
        config = TemplateConfig(index="valid", history="valid")
        assert config.index == "valid"
        assert config.history == "valid"

        # Pydantic v2 is strict about types - integers should raise validation error
        with pytest.raises(ValidationError):
            TemplateConfig(index=123, history=456)

    def test_template_config_contains_all_placeholders(self):
        """Test that default template contains expected placeholders."""
        config = TemplateConfig()

        # Check index template placeholders
        expected_placeholders = [
            "{{filename}}",
            "{{filepath}}",
            "{{purpose}}",
            "{{responsibilities}}",
            "{{requirements}}",
            "{{file_extension}}",
            "{{example_usage}}",
            "{{notes}}",
        ]

        for placeholder in expected_placeholders:
            assert placeholder in config.index

        # Check history template placeholders
        history_placeholders = [
            "{{filename}}",
            "{{date}}",
            "{{context}}",
            "{{decisions}}",
            "{{lessons}}",
        ]

        for placeholder in history_placeholders:
            assert placeholder in config.history


class TestLoadTemplate:
    """Test the load_template function."""

    def test_load_template_with_no_file_returns_default(self):
        """Test that load_template returns default when no .spectemplate file exists."""
        # Ensure no template file exists
        if TEMPLATE_FILE.exists():
            TEMPLATE_FILE.unlink()

        result = load_template()

        assert isinstance(result, TemplateConfig)
        # Should be default values
        default = TemplateConfig()
        assert result.index == default.index
        assert result.history == default.history

    def test_load_template_with_valid_yaml_parses_correctly(self):
        """Test that load_template parses valid YAML correctly."""
        custom_config = {
            "index": "Custom index template for {{filename}}",
            "history": "Custom history template for {{filename}}",
        }

        # Create temporary template file
        TEMPLATE_FILE.write_text(yaml.dump(custom_config))

        try:
            result = load_template()

            assert isinstance(result, TemplateConfig)
            assert result.index == custom_config["index"]
            assert result.history == custom_config["history"]

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    def test_load_template_with_partial_yaml_uses_defaults(self):
        """Test that load_template uses defaults for missing fields."""
        partial_config = {
            "index": "Custom index only"
            # history field missing
        }

        TEMPLATE_FILE.write_text(yaml.dump(partial_config))

        try:
            result = load_template()

            assert isinstance(result, TemplateConfig)
            assert result.index == partial_config["index"]
            # Should use default for missing history field
            assert result.history == TemplateConfig().history

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    def test_load_template_with_empty_yaml_returns_defaults(self):
        """Test that load_template handles empty YAML file."""
        # Create empty YAML file
        TEMPLATE_FILE.write_text("")

        try:
            result = load_template()

            assert isinstance(result, TemplateConfig)
            # Should be default values
            default = TemplateConfig()
            assert result.index == default.index
            assert result.history == default.history

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    def test_load_template_with_invalid_yaml_raises_error(self):
        """Test that load_template raises YAMLError for invalid YAML."""
        # Create file with invalid YAML
        TEMPLATE_FILE.write_text("invalid: yaml: content: [unclosed")

        try:
            with pytest.raises(yaml.YAMLError, match="Invalid YAML in template file"):
                load_template()

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    def test_load_template_with_invalid_config_raises_error(self):
        """Test that load_template raises ValueError for invalid configuration."""
        # Create YAML with invalid field types (list instead of string)
        TEMPLATE_FILE.write_text("index:\n  - this\n  - is\n  - a\n  - list\n")

        try:
            with pytest.raises(ValueError, match="Invalid template configuration"):
                load_template()

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    @patch("spec_cli.__main__.DEBUG", True)
    def test_load_template_debug_output_no_file(self, capsys):
        """Test that load_template produces debug output when no file exists."""
        if TEMPLATE_FILE.exists():
            TEMPLATE_FILE.unlink()

        load_template()

        captured = capsys.readouterr()
        assert (
            "🔍 Debug: No .spectemplate file found, using default template"
            in captured.out
        )

    @patch("spec_cli.__main__.DEBUG", True)
    def test_load_template_debug_output_with_file(self, capsys):
        """Test that load_template produces debug output when file exists."""
        TEMPLATE_FILE.write_text("index: 'test'")

        try:
            load_template()

            captured = capsys.readouterr()
            assert f"🔍 Debug: Loaded template from {TEMPLATE_FILE}" in captured.out

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    @patch("spec_cli.__main__.DEBUG", False)
    def test_load_template_no_debug_output(self, capsys):
        """Test that load_template produces no debug output when DEBUG is False."""
        if TEMPLATE_FILE.exists():
            TEMPLATE_FILE.unlink()

        load_template()

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out

    def test_load_template_handles_unicode_content(self):
        """Test that load_template handles Unicode content in templates."""
        unicode_config = {
            "index": "Unicode template: 🚀 {{filename}} 📝",
            "history": "Unicode history: ⭐ {{filename}} 📚",
        }

        TEMPLATE_FILE.write_text(yaml.dump(unicode_config), encoding="utf-8")

        try:
            result = load_template()

            assert result.index == unicode_config["index"]
            assert result.history == unicode_config["history"]
            assert "🚀" in result.index
            assert "⭐" in result.history

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()

    def test_load_template_preserves_multiline_content(self):
        """Test that load_template preserves multiline template content."""
        multiline_config = {
            "index": """# {{filename}}

This is a multiline
template with proper
formatting and indentation.

**Location**: {{filepath}}""",
            "history": """# History

Line 1
Line 2
Line 3""",
        }

        TEMPLATE_FILE.write_text(yaml.dump(multiline_config))

        try:
            result = load_template()

            assert "\n" in result.index
            assert "\n" in result.history
            assert "multiline" in result.index
            assert "Line 1" in result.history

        finally:
            if TEMPLATE_FILE.exists():
                TEMPLATE_FILE.unlink()
