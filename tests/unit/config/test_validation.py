"""Unit tests for configuration validation module.

Tests ConfigurationValidator class for validating configuration values
and generating helpful error messages for various configuration sections.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.validation import ConfigurationValidator
from spec_cli.exceptions import SpecConfigurationError


class TestConfigurationValidator:
    """Unit tests for ConfigurationValidator class."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.validator = ConfigurationValidator()

    # Test fixtures for configuration data
    @pytest.fixture
    def valid_debug_config(self) -> dict[str, Any]:
        """Valid debug configuration."""
        return {"enabled": True, "level": "DEBUG", "timing": False}

    @pytest.fixture
    def valid_terminal_config(self) -> dict[str, Any]:
        """Valid terminal configuration."""
        return {"use_color": True, "console_width": 120}

    @pytest.fixture
    def valid_path_config(self, tmp_path: Any) -> dict[str, Any]:
        """Valid path configuration."""
        test_dir = tmp_path / "test_root"
        test_dir.mkdir()
        return {"root_path": str(test_dir), "template_file": "custom_template.md"}

    @pytest.fixture
    def valid_template_config(self) -> dict[str, Any]:
        """Valid template configuration."""
        return {
            "index": "# {{filename}}\n\nIndex content",
            "history": "# {{filename}} History\n\nHistory content",
        }

    @pytest.fixture
    def complete_valid_config(
        self,
        valid_debug_config: dict[str, Any],
        valid_terminal_config: dict[str, Any],
        valid_path_config: dict[str, Any],
        valid_template_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Complete valid configuration."""
        return {
            "debug": valid_debug_config,
            "terminal": valid_terminal_config,
            "paths": valid_path_config,
            "template": valid_template_config,
        }

    # Core validation tests
    def test_validate_configuration_when_valid_complete_config_then_returns_no_errors(
        self, complete_valid_config: dict[str, Any]
    ) -> None:
        """Test validation with complete valid configuration."""
        errors = self.validator.validate_configuration(complete_valid_config)
        assert errors == []

    def test_validate_configuration_when_empty_config_then_returns_no_errors(
        self,
    ) -> None:
        """Test validation with empty configuration."""
        errors = self.validator.validate_configuration({})
        assert errors == []

    def test_validate_configuration_when_partial_config_then_validates_present_sections(
        self, valid_debug_config: dict[str, Any]
    ) -> None:
        """Test validation with partial configuration."""
        config: dict[str, Any] = {"debug": valid_debug_config}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    # Debug configuration validation tests
    def test_validate_debug_config_when_valid_level_then_no_errors(self) -> None:
        """Test debug config validation with valid level."""
        config: dict[str, Any] = {"debug": {"level": "INFO"}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_debug_config_when_invalid_level_type_then_returns_error(
        self,
    ) -> None:
        """Test debug config validation with invalid level type."""
        config: dict[str, Any] = {"debug": {"level": 123}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "debug.level must be a string" in errors[0]
        assert "got int" in errors[0]

    def test_validate_debug_config_when_invalid_level_value_then_returns_error(
        self,
    ) -> None:
        """Test debug config validation with invalid level value."""
        config: dict[str, Any] = {"debug": {"level": "INVALID"}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "Invalid debug level 'INVALID'" in errors[0]
        assert "Must be one of: DEBUG, INFO, WARNING, ERROR" in errors[0]

    def test_validate_debug_config_when_invalid_enabled_type_then_returns_error(
        self,
    ) -> None:
        """Test debug config validation with invalid enabled type."""
        config: dict[str, Any] = {"debug": {"enabled": "true"}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "debug.enabled must be a boolean value" in errors[0]
        assert "got str" in errors[0]

    def test_validate_debug_config_when_invalid_timing_type_then_returns_error(
        self,
    ) -> None:
        """Test debug config validation with invalid timing type."""
        config: dict[str, Any] = {"debug": {"timing": 1}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "debug.timing must be a boolean value" in errors[0]
        assert "got int" in errors[0]

    def test_validate_debug_config_when_all_valid_levels_then_no_errors(self) -> None:
        """Test debug config validation with all valid level values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            config: dict[str, Any] = {"debug": {"level": level}}
            errors = self.validator.validate_configuration(config)
            assert errors == [], f"Level {level} should be valid"

    def test_validate_debug_config_when_case_insensitive_level_then_valid(self) -> None:
        """Test debug config validation is case insensitive for levels."""
        for level in ["debug", "info", "warning", "error"]:
            config: dict[str, Any] = {"debug": {"level": level}}
            errors = self.validator.validate_configuration(config)
            assert errors == [], f"Level {level} should be valid (case insensitive)"

    # Terminal configuration validation tests
    def test_validate_terminal_config_when_valid_use_color_then_no_errors(self) -> None:
        """Test terminal config validation with valid use_color."""
        config: dict[str, Any] = {"terminal": {"use_color": False}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_terminal_config_when_invalid_use_color_type_then_returns_error(
        self,
    ) -> None:
        """Test terminal config validation with invalid use_color type."""
        config: dict[str, Any] = {"terminal": {"use_color": "false"}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "terminal.use_color must be a boolean value" in errors[0]
        assert "got str" in errors[0]

    def test_validate_terminal_config_when_valid_console_width_then_no_errors(
        self,
    ) -> None:
        """Test terminal config validation with valid console width."""
        config: dict[str, Any] = {"terminal": {"console_width": 80}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_terminal_config_when_invalid_console_width_type_then_returns_error(
        self,
    ) -> None:
        """Test terminal config validation with invalid console width type."""
        config: dict[str, Any] = {"terminal": {"console_width": "80"}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "terminal.console_width must be an integer" in errors[0]
        assert "got str" in errors[0]

    def test_validate_terminal_config_when_console_width_too_small_then_returns_error(
        self,
    ) -> None:
        """Test terminal config validation with console width too small."""
        config: dict[str, Any] = {"terminal": {"console_width": 39}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "terminal.console_width must be at least 40, got 39" in errors[0]

    def test_validate_terminal_config_when_console_width_too_large_then_returns_error(
        self,
    ) -> None:
        """Test terminal config validation with console width too large."""
        config: dict[str, Any] = {"terminal": {"console_width": 1001}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "terminal.console_width must be at most 1000, got 1001" in errors[0]

    def test_validate_terminal_config_when_console_width_boundary_values_then_valid(
        self,
    ) -> None:
        """Test terminal config validation with boundary values for console width."""
        for width in [40, 1000]:
            config: dict[str, Any] = {"terminal": {"console_width": width}}
            errors = self.validator.validate_configuration(config)
            assert errors == [], f"Width {width} should be valid"

    # Path configuration validation tests
    def test_validate_path_config_when_valid_existing_root_path_then_no_errors(
        self, tmp_path: Any
    ) -> None:
        """Test path config validation with valid existing root path."""
        test_dir = tmp_path / "valid_root"
        test_dir.mkdir()
        config: dict[str, Any] = {"paths": {"root_path": str(test_dir)}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_path_config_when_invalid_root_path_type_then_returns_error(
        self,
    ) -> None:
        """Test path config validation with invalid root path type."""
        config: dict[str, Any] = {"paths": {"root_path": 123}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "paths.root_path must be a string" in errors[0]
        assert "got int" in errors[0]

    def test_validate_path_config_when_nonexistent_root_path_then_returns_error(
        self,
    ) -> None:
        """Test path config validation with nonexistent root path."""
        config: dict[str, Any] = {"paths": {"root_path": "/nonexistent/path"}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "Specified root_path does not exist: /nonexistent/path" in errors[0]

    def test_validate_path_config_when_root_path_is_file_then_returns_error(
        self, tmp_path: Any
    ) -> None:
        """Test path config validation when root path is a file not directory."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        config: dict[str, Any] = {"paths": {"root_path": str(test_file)}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert f"Specified root_path is not a directory: {test_file}" in errors[0]

    def test_validate_path_config_when_valid_template_file_then_no_errors(self) -> None:
        """Test path config validation with valid template file."""
        config: dict[str, Any] = {"paths": {"template_file": "custom.md"}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_path_config_when_invalid_template_file_type_then_returns_error(
        self,
    ) -> None:
        """Test path config validation with invalid template file type."""
        config: dict[str, Any] = {"paths": {"template_file": 123}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "paths.template_file must be a string" in errors[0]
        assert "got int" in errors[0]

    # Template configuration validation tests
    def test_validate_template_config_when_valid_index_template_then_no_errors(
        self,
    ) -> None:
        """Test template config validation with valid index template."""
        config: dict[str, Any] = {"template": {"index": "# {{filename}}\n\nContent"}}
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_template_config_when_valid_history_template_then_no_errors(
        self,
    ) -> None:
        """Test template config validation with valid history template."""
        config: dict[str, Any] = {
            "template": {"history": "# {{filename}} History\n\nContent"}
        }
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_validate_template_config_when_invalid_index_type_then_returns_error(
        self,
    ) -> None:
        """Test template config validation with invalid index type."""
        config: dict[str, Any] = {"template": {"index": 123}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.index must be a string" in errors[0]
        assert "got int" in errors[0]

    def test_validate_template_config_when_empty_index_then_returns_error(self) -> None:
        """Test template config validation with empty index template."""
        config: dict[str, Any] = {"template": {"index": "   "}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.index cannot be empty" in errors[0]

    def test_validate_template_config_when_missing_filename_placeholder_then_returns_error(
        self,
    ) -> None:
        """Test template config validation with missing filename placeholder."""
        config: dict[str, Any] = {
            "template": {"index": "# Title\n\nContent without placeholder"}
        }
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.index must contain {{filename}} placeholder" in errors[0]

    def test_validate_template_config_when_invalid_history_type_then_returns_error(
        self,
    ) -> None:
        """Test template config validation with invalid history type."""
        config: dict[str, Any] = {"template": {"history": []}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.history must be a string" in errors[0]
        assert "got list" in errors[0]

    def test_validate_template_config_when_empty_history_then_returns_error(
        self,
    ) -> None:
        """Test template config validation with empty history template."""
        config: dict[str, Any] = {"template": {"history": ""}}
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.history cannot be empty" in errors[0]

    def test_validate_template_config_when_history_missing_filename_placeholder_then_returns_error(
        self,
    ) -> None:
        """Test template config validation with history missing filename placeholder."""
        config: dict[str, Any] = {
            "template": {"history": "# History\n\nContent without placeholder"}
        }
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 1
        assert "template.history must contain {{filename}} placeholder" in errors[0]

    # Multiple error scenarios
    def test_validate_configuration_when_multiple_errors_then_returns_all_errors(
        self,
    ) -> None:
        """Test validation with multiple configuration errors."""
        config: dict[str, Any] = {
            "debug": {"level": "INVALID", "enabled": "not_boolean"},
            "terminal": {"console_width": 30},
            "template": {"index": "", "history": "No placeholder"},
        }
        errors = self.validator.validate_configuration(config)
        assert len(errors) == 5
        assert any("Invalid debug level" in error for error in errors)
        assert any("debug.enabled must be a boolean" in error for error in errors)
        assert any("console_width must be at least 40" in error for error in errors)
        assert any("template.index cannot be empty" in error for error in errors)
        assert any(
            "template.history must contain {{filename}}" in error for error in errors
        )

    # validate_and_raise method tests
    def test_validate_and_raise_when_valid_config_then_no_exception(
        self, complete_valid_config: dict[str, Any]
    ) -> None:
        """Test validate_and_raise with valid configuration."""
        # Should not raise any exception
        self.validator.validate_and_raise(complete_valid_config)

    def test_validate_and_raise_when_invalid_config_then_raises_spec_configuration_error(
        self,
    ) -> None:
        """Test validate_and_raise with invalid configuration."""
        config: dict[str, Any] = {"debug": {"level": "INVALID"}}

        with pytest.raises(SpecConfigurationError) as exc_info:
            self.validator.validate_and_raise(config)

        assert "Configuration validation failed" in str(exc_info.value)
        assert "Invalid debug level 'INVALID'" in str(exc_info.value)

    @patch("spec_cli.config.validation.ErrorHandler")
    def test_validate_and_raise_when_invalid_config_then_calls_error_handler(
        self, mock_error_handler_class: Any
    ) -> None:
        """Test validate_and_raise calls error handler correctly."""
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler

        validator = ConfigurationValidator()
        config: dict[str, Any] = {"debug": {"level": "INVALID"}}

        try:
            validator.validate_and_raise(config)
        except SpecConfigurationError:
            pass  # Expected

        # Verify error handler was called
        mock_error_handler.log_and_raise.assert_called_once()
        call_args = mock_error_handler.log_and_raise.call_args
        assert call_args[1]["reraise_as"] == SpecConfigurationError
        assert "validation_errors" in call_args[1]
        assert "config_keys" in call_args[1]

    # get_validation_schema method tests
    def test_get_validation_schema_when_called_then_returns_complete_schema(
        self,
    ) -> None:
        """Test get_validation_schema returns complete schema."""
        schema = self.validator.get_validation_schema()

        # Verify main sections exist
        assert "debug" in schema
        assert "terminal" in schema
        assert "paths" in schema
        assert "template" in schema

        # Verify debug section
        debug_schema = schema["debug"]
        assert "enabled" in debug_schema
        assert "level" in debug_schema
        assert "timing" in debug_schema
        assert "boolean" in debug_schema["enabled"]
        assert "DEBUG, INFO, WARNING, ERROR" in debug_schema["level"]

        # Verify terminal section
        terminal_schema = schema["terminal"]
        assert "use_color" in terminal_schema
        assert "console_width" in terminal_schema
        assert "40-1000" in terminal_schema["console_width"]

        # Verify paths section
        paths_schema = schema["paths"]
        assert "root_path" in paths_schema
        assert "template_file" in paths_schema

        # Verify template section
        template_schema = schema["template"]
        assert "index" in template_schema
        assert "history" in template_schema

    # Edge cases and boundary conditions
    def test_validate_configuration_when_none_values_then_handles_gracefully(
        self,
    ) -> None:
        """Test validation handles None values gracefully."""
        config: dict[str, Any] = {
            "debug": {"level": None, "enabled": None},
            "terminal": {"use_color": None, "console_width": None},
            "paths": {"root_path": None, "template_file": None},
            "template": {"index": None, "history": None},
        }
        errors = self.validator.validate_configuration(config)
        # None values should be ignored (treated as not specified)
        assert errors == []

    def test_validate_configuration_when_extra_fields_then_ignores_them(self) -> None:
        """Test validation ignores extra/unknown fields."""
        config: dict[str, Any] = {
            "debug": {"level": "INFO", "unknown_field": "value"},
            "unknown_section": {"field": "value"},
        }
        errors = self.validator.validate_configuration(config)
        assert errors == []

    def test_initialization_creates_error_handler_with_component_context(self) -> None:
        """Test ConfigurationValidator initialization creates error handler."""
        validator = ConfigurationValidator()
        assert validator.error_handler is not None
        # Verify error handler was initialized with correct context
        assert hasattr(validator.error_handler, "default_context")
        assert (
            validator.error_handler.default_context.get("component")
            == "config_validator"
        )
