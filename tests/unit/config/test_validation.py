import tempfile
from typing import Any, Dict  # noqa: F401

import pytest

from spec_cli.config.validation import ConfigurationValidator
from spec_cli.exceptions import SpecConfigurationError


class TestConfigurationValidator:
    """Test the ConfigurationValidator class functionality."""

    def test_configuration_validator_accepts_valid_config(self) -> None:
        """Test that validator accepts valid configuration."""
        validator = ConfigurationValidator()

        valid_config = {
            "debug": {"enabled": True, "level": "DEBUG", "timing": False},
            "terminal": {"use_color": True, "console_width": 120},
            "template": {
                "index": "# {{filename}}\n\nContent here",
                "history": "## History for {{filename}}\n\nHistory here",
            },
        }

        errors = validator.validate_configuration(valid_config)
        assert errors == []

    def test_configuration_validator_rejects_invalid_debug_config(self) -> None:
        """Test validation of debug configuration section."""
        validator = ConfigurationValidator()

        # Invalid debug level type
        config1 = {"debug": {"level": 123}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config1)
        assert any("debug.level must be a string" in error for error in errors)

        # Invalid debug level value
        config2 = {"debug": {"level": "INVALID"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config2)
        assert any("Invalid debug level 'INVALID'" in error for error in errors)

        # Invalid boolean type
        config3 = {"debug": {"enabled": "not_boolean"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config3)
        assert any("debug.enabled must be a boolean" in error for error in errors)

        # Invalid timing type
        config4 = {"debug": {"timing": "also_not_boolean"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config4)
        assert any("debug.timing must be a boolean" in error for error in errors)

    def test_configuration_validator_rejects_invalid_terminal_config(self) -> None:
        """Test validation of terminal configuration section."""
        validator = ConfigurationValidator()

        # Invalid use_color type
        config5 = {"terminal": {"use_color": "maybe"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config5)
        assert any("terminal.use_color must be a boolean" in error for error in errors)

        # Invalid console_width type
        config6 = {"terminal": {"console_width": "wide"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config6)
        assert any(
            "terminal.console_width must be an integer" in error for error in errors
        )

        # Console width too small
        config7 = {"terminal": {"console_width": 20}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config7)
        assert any(
            "terminal.console_width must be at least 40" in error for error in errors
        )

        # Console width too large
        config8 = {"terminal": {"console_width": 2000}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config8)
        assert any(
            "terminal.console_width must be at most 1000" in error for error in errors
        )

    def test_configuration_validator_rejects_invalid_path_config(self) -> None:
        """Test validation of path configuration section."""
        validator = ConfigurationValidator()

        # Invalid root_path type
        config9 = {"paths": {"root_path": 123}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config9)
        assert any("paths.root_path must be a string" in error for error in errors)

        # Non-existent root_path
        config10 = {"paths": {"root_path": "/nonexistent/path"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config10)
        assert any("Specified root_path does not exist" in error for error in errors)

        # Create a temporary file (not directory) to test validation
        with tempfile.NamedTemporaryFile() as temp_file:
            config11 = {"paths": {"root_path": temp_file.name}}  # type: Dict[str, Any]
            errors = validator.validate_configuration(config11)
            assert any(
                "Specified root_path is not a directory" in error for error in errors
            )

        # Invalid template_file type
        config12 = {"paths": {"template_file": ["not", "a", "string"]}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config12)
        assert any("paths.template_file must be a string" in error for error in errors)

    def test_configuration_validator_rejects_invalid_template_config(self) -> None:
        """Test validation of template configuration section."""
        validator = ConfigurationValidator()

        # Invalid template type
        config13 = {"template": {"index": 123}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config13)
        assert any("template.index must be a string" in error for error in errors)

        # Empty template
        config14 = {"template": {"index": "   "}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config14)
        assert any("template.index cannot be empty" in error for error in errors)

        # Missing filename placeholder
        config15 = {"template": {"index": "Template without placeholder"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config15)
        assert any(
            "template.index must contain {{filename}}" in error for error in errors
        )

        # Test history template validation
        config16 = {"template": {"history": "Missing placeholder"}}  # type: Dict[str, Any]
        errors = validator.validate_configuration(config16)
        assert any(
            "template.history must contain {{filename}}" in error for error in errors
        )

    def test_configuration_validator_provides_helpful_error_messages(self) -> None:
        """Test that validator provides helpful and specific error messages."""
        validator = ConfigurationValidator()

        # Multiple errors in one config
        config = {
            "debug": {"level": "INVALID_LEVEL", "enabled": "not_boolean"},
            "terminal": {
                "console_width": 10  # Too small
            },
            "template": {
                "index": ""  # Empty
            },
        }

        errors = validator.validate_configuration(config)

        # Should have multiple specific errors
        assert len(errors) >= 4
        assert any("Invalid debug level 'INVALID_LEVEL'" in error for error in errors)
        assert any("debug.enabled must be a boolean" in error for error in errors)
        assert any(
            "terminal.console_width must be at least 40" in error for error in errors
        )
        assert any("template.index cannot be empty" in error for error in errors)

    def test_configuration_validator_validate_and_raise(self) -> None:
        """Test validate_and_raise method."""
        validator = ConfigurationValidator()

        # Valid config should not raise
        valid_config = {"debug": {"enabled": True}}
        validator.validate_and_raise(valid_config)  # Should not raise

        # Invalid config should raise with detailed message
        invalid_config = {"debug": {"level": "INVALID"}}

        with pytest.raises(SpecConfigurationError) as exc_info:
            validator.validate_and_raise(invalid_config)

        error_message = str(exc_info.value)
        assert "Configuration validation failed" in error_message
        assert "Invalid debug level 'INVALID'" in error_message

    def test_configuration_validator_get_validation_schema(self) -> None:
        """Test getting validation schema for documentation."""
        validator = ConfigurationValidator()
        schema = validator.get_validation_schema()

        # Should contain expected sections
        assert "debug" in schema
        assert "terminal" in schema
        assert "paths" in schema
        assert "template" in schema

        # Check debug section
        debug_schema = schema["debug"]
        assert "enabled" in debug_schema
        assert "level" in debug_schema
        assert "timing" in debug_schema

        # Check that descriptions are helpful
        assert "boolean" in debug_schema["enabled"]
        assert "DEBUG, INFO, WARNING, ERROR" in debug_schema["level"]

    def test_configuration_validator_handles_valid_path_config(self) -> None:
        """Test validation with valid path configuration."""
        validator = ConfigurationValidator()

        # Test with existing directory (use temp directory)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "paths": {"root_path": temp_dir, "template_file": "custom.template"}
            }

            errors = validator.validate_configuration(config)
            assert errors == []

    def test_configuration_validator_handles_mixed_valid_invalid(self) -> None:
        """Test validator with mix of valid and invalid sections."""
        validator = ConfigurationValidator()

        config = {
            "debug": {"enabled": True, "level": "INFO"},  # Valid
            "terminal": {"console_width": 5},  # Invalid (too small)
            "template": {"index": "# {{filename}}\nContent"},  # Valid
        }

        errors = validator.validate_configuration(config)

        # Should only have error for terminal section
        assert len(errors) == 1
        assert "terminal.console_width must be at least 40" in errors[0]
