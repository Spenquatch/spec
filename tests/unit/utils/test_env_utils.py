"""Tests for environment variable utilities."""

import os
from unittest.mock import patch

from spec_cli.utils.env_utils import (
    EnvironmentConfig,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_str,
    validate_env_vars,
)


class TestGetEnvStr:
    """Test string environment variable getter."""

    def test_get_env_str_when_variable_exists_then_returns_value(self):
        """Test getting existing string environment variable."""
        with patch.dict(os.environ, {"TEST_STR": "hello world"}, clear=True):
            result = get_env_str("TEST_STR", "default")
            assert result == "hello world"

    def test_get_env_str_when_variable_missing_then_returns_default(self):
        """Test getting missing string environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_str("MISSING_VAR", "default_value")
            assert result == "default_value"

    def test_get_env_str_when_no_default_specified_then_returns_empty_string(self):
        """Test getting missing string with no default specified."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_str("MISSING_VAR")
            assert result == ""

    def test_get_env_str_when_variable_empty_then_returns_empty_string(self):
        """Test getting empty string environment variable."""
        with patch.dict(os.environ, {"EMPTY_VAR": ""}, clear=True):
            result = get_env_str("EMPTY_VAR", "default")
            assert result == ""

    def test_get_env_str_when_variable_has_spaces_then_preserves_spaces(self):
        """Test getting string with leading/trailing spaces."""
        with patch.dict(os.environ, {"SPACED_VAR": "  value  "}, clear=True):
            result = get_env_str("SPACED_VAR", "default")
            assert result == "  value  "


class TestGetEnvInt:
    """Test integer environment variable getter."""

    def test_get_env_int_when_valid_integer_then_returns_value(self):
        """Test getting valid integer environment variable."""
        with patch.dict(os.environ, {"TEST_INT": "42"}, clear=True):
            result = get_env_int("TEST_INT", 0)
            assert result == 42

    def test_get_env_int_when_negative_integer_then_returns_value(self):
        """Test getting negative integer environment variable."""
        with patch.dict(os.environ, {"TEST_NEG": "-123"}, clear=True):
            result = get_env_int("TEST_NEG", 0)
            assert result == -123

    def test_get_env_int_when_variable_missing_then_returns_default(self):
        """Test getting missing integer environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_int("MISSING_INT", 999)
            assert result == 999

    def test_get_env_int_when_no_default_specified_then_returns_zero(self):
        """Test getting missing integer with no default specified."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_int("MISSING_INT")
            assert result == 0

    def test_get_env_int_when_invalid_value_then_returns_default(self):
        """Test getting invalid integer environment variable."""
        with patch.dict(os.environ, {"INVALID_INT": "not_a_number"}, clear=True):
            result = get_env_int("INVALID_INT", 100)
            assert result == 100

    def test_get_env_int_when_float_value_then_returns_default(self):
        """Test getting float value as integer."""
        with patch.dict(os.environ, {"FLOAT_AS_INT": "3.14"}, clear=True):
            result = get_env_int("FLOAT_AS_INT", 50)
            assert result == 50

    def test_get_env_int_when_empty_string_then_returns_default(self):
        """Test getting empty string as integer."""
        with patch.dict(os.environ, {"EMPTY_INT": ""}, clear=True):
            result = get_env_int("EMPTY_INT", 75)
            assert result == 75


class TestGetEnvBool:
    """Test boolean environment variable getter."""

    def test_get_env_bool_when_true_values_then_returns_true(self):
        """Test getting various true boolean values."""
        true_values = [
            "1",
            "true",
            "TRUE",
            "True",
            "yes",
            "YES",
            "Yes",
            "on",
            "ON",
            "On",
        ]

        for true_value in true_values:
            with patch.dict(os.environ, {"TEST_BOOL": true_value}, clear=True):
                result = get_env_bool("TEST_BOOL", False)
                assert result is True, f"Failed for value: {true_value}"

    def test_get_env_bool_when_false_values_then_returns_false(self):
        """Test getting various false boolean values."""
        false_values = [
            "0",
            "false",
            "FALSE",
            "False",
            "no",
            "NO",
            "No",
            "off",
            "OFF",
            "Off",
        ]

        for false_value in false_values:
            with patch.dict(os.environ, {"TEST_BOOL": false_value}, clear=True):
                result = get_env_bool("TEST_BOOL", True)
                assert result is False, f"Failed for value: {false_value}"

    def test_get_env_bool_when_variable_missing_then_returns_default(self):
        """Test getting missing boolean environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_bool("MISSING_BOOL", True)
            assert result is True

    def test_get_env_bool_when_no_default_specified_then_returns_false(self):
        """Test getting missing boolean with no default specified."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_bool("MISSING_BOOL")
            assert result is False

    def test_get_env_bool_when_invalid_value_then_returns_default(self):
        """Test getting invalid boolean environment variable."""
        with patch.dict(os.environ, {"INVALID_BOOL": "maybe"}, clear=True):
            result = get_env_bool("INVALID_BOOL", True)
            assert result is True

    def test_get_env_bool_when_spaces_around_value_then_handles_correctly(self):
        """Test getting boolean with spaces around value."""
        with patch.dict(os.environ, {"SPACED_BOOL": "  true  "}, clear=True):
            result = get_env_bool("SPACED_BOOL", False)
            assert result is True

    def test_get_env_bool_when_empty_string_then_returns_default(self):
        """Test getting empty string as boolean."""
        with patch.dict(os.environ, {"EMPTY_BOOL": ""}, clear=True):
            result = get_env_bool("EMPTY_BOOL", True)
            assert result is True


class TestGetEnvFloat:
    """Test float environment variable getter."""

    def test_get_env_float_when_valid_float_then_returns_value(self):
        """Test getting valid float environment variable."""
        with patch.dict(os.environ, {"TEST_FLOAT": "3.14"}, clear=True):
            result = get_env_float("TEST_FLOAT", 0.0)
            assert result == 3.14

    def test_get_env_float_when_integer_value_then_returns_as_float(self):
        """Test getting integer value as float."""
        with patch.dict(os.environ, {"INT_AS_FLOAT": "42"}, clear=True):
            result = get_env_float("INT_AS_FLOAT", 0.0)
            assert result == 42.0
            assert isinstance(result, float)

    def test_get_env_float_when_negative_float_then_returns_value(self):
        """Test getting negative float environment variable."""
        with patch.dict(os.environ, {"NEG_FLOAT": "-2.718"}, clear=True):
            result = get_env_float("NEG_FLOAT", 0.0)
            assert result == -2.718

    def test_get_env_float_when_variable_missing_then_returns_default(self):
        """Test getting missing float environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_float("MISSING_FLOAT", 1.5)
            assert result == 1.5

    def test_get_env_float_when_no_default_specified_then_returns_zero(self):
        """Test getting missing float with no default specified."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_float("MISSING_FLOAT")
            assert result == 0.0

    def test_get_env_float_when_invalid_value_then_returns_default(self):
        """Test getting invalid float environment variable."""
        with patch.dict(os.environ, {"INVALID_FLOAT": "not_a_number"}, clear=True):
            result = get_env_float("INVALID_FLOAT", 2.5)
            assert result == 2.5

    def test_get_env_float_when_scientific_notation_then_returns_value(self):
        """Test getting scientific notation as float."""
        with patch.dict(os.environ, {"SCI_FLOAT": "1.23e-4"}, clear=True):
            result = get_env_float("SCI_FLOAT", 0.0)
            assert result == 1.23e-4


class TestValidateEnvVars:
    """Test environment variable validation."""

    def test_validate_env_vars_when_all_valid_then_returns_empty_dict(self):
        """Test validation with all valid environment variables."""
        with patch.dict(
            os.environ,
            {
                "STR_VAR": "hello",
                "INT_VAR": "42",
                "FLOAT_VAR": "3.14",
                "BOOL_VAR": "true",
            },
            clear=True,
        ):
            required = {
                "STR_VAR": str,
                "INT_VAR": int,
                "FLOAT_VAR": float,
                "BOOL_VAR": bool,
            }
            errors = validate_env_vars(required)
            assert errors == {}

    def test_validate_env_vars_when_missing_variables_then_returns_errors(self):
        """Test validation with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            required = {"MISSING_STR": str, "MISSING_INT": int}
            errors = validate_env_vars(required)

            assert len(errors) == 2
            assert "MISSING_STR" in errors
            assert "MISSING_INT" in errors
            assert "not set" in errors["MISSING_STR"]
            assert "not set" in errors["MISSING_INT"]

    def test_validate_env_vars_when_invalid_types_then_returns_errors(self):
        """Test validation with invalid type environment variables."""
        with patch.dict(
            os.environ,
            {
                "INVALID_INT": "not_a_number",
                "INVALID_FLOAT": "also_not_a_number",
                "INVALID_BOOL": "maybe",
            },
            clear=True,
        ):
            required = {
                "INVALID_INT": int,
                "INVALID_FLOAT": float,
                "INVALID_BOOL": bool,
            }
            errors = validate_env_vars(required)

            assert len(errors) == 3
            assert "INVALID_INT" in errors
            assert "INVALID_FLOAT" in errors
            assert "INVALID_BOOL" in errors
            assert "Invalid integer" in errors["INVALID_INT"]
            assert "Invalid float" in errors["INVALID_FLOAT"]
            assert "Invalid boolean" in errors["INVALID_BOOL"]

    def test_validate_env_vars_when_mixed_valid_invalid_then_returns_partial_errors(
        self,
    ):
        """Test validation with mix of valid and invalid variables."""
        with patch.dict(
            os.environ,
            {"VALID_STR": "hello", "VALID_INT": "42", "INVALID_INT": "not_a_number"},
            clear=True,
        ):
            required = {
                "VALID_STR": str,
                "VALID_INT": int,
                "INVALID_INT": int,
                "MISSING_VAR": str,
            }
            errors = validate_env_vars(required)

            assert len(errors) == 2
            assert "VALID_STR" not in errors
            assert "VALID_INT" not in errors
            assert "INVALID_INT" in errors
            assert "MISSING_VAR" in errors

    def test_validate_env_vars_when_empty_required_then_returns_empty_dict(self):
        """Test validation with no required variables."""
        errors = validate_env_vars({})
        assert errors == {}


class TestLoggingIntegration:
    """Test that environment utilities log appropriately."""

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_get_env_str_logs_retrieval(self, mock_logger):
        """Test that string retrieval is logged."""
        with patch.dict(os.environ, {"TEST_VAR": "value"}, clear=True):
            get_env_str("TEST_VAR", "default")

            mock_logger.log.assert_called_with(
                "DEBUG",
                "Environment string variable retrieved",
                key="TEST_VAR",
                value_length=5,
                using_default=False,
            )

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_get_env_int_logs_invalid_value_warning(self, mock_logger):
        """Test that invalid integer values log warnings."""
        with patch.dict(os.environ, {"INVALID_INT": "not_a_number"}, clear=True):
            get_env_int("INVALID_INT", 42)

            mock_logger.log.assert_called_with(
                "WARNING",
                "Invalid integer environment variable, using default",
                key="INVALID_INT",
                invalid_value="not_a_number",
                default=42,
            )

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_get_env_bool_logs_invalid_value_warning(self, mock_logger):
        """Test that invalid boolean values log warnings."""
        with patch.dict(os.environ, {"INVALID_BOOL": "maybe"}, clear=True):
            get_env_bool("INVALID_BOOL", True)

            mock_logger.log.assert_called_with(
                "WARNING",
                "Invalid boolean environment variable, using default",
                key="INVALID_BOOL",
                invalid_value="maybe",
                default=True,
            )

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_validate_env_vars_logs_validation_summary(self, mock_logger):
        """Test that validation logs summary information."""
        with patch.dict(os.environ, {"VALID_VAR": "42"}, clear=True):
            validate_env_vars({"VALID_VAR": int, "MISSING_VAR": str})

            mock_logger.log.assert_called_with(
                "INFO",
                "Environment variables validated",
                checked_count=2,
                error_count=1,
                errors=["MISSING_VAR"],
            )


class TestEnvironmentConfig:
    """Test EnvironmentConfig dataclass functionality."""

    def test_environment_config_default_initialization(self):
        """Test EnvironmentConfig with default values."""
        config = EnvironmentConfig()

        assert config.debug is False
        assert config.debug_level == "INFO"
        assert config.debug_timing is False
        assert config.use_color is True
        assert config.console_width == 0
        assert config.api_timeout == 30.0
        assert config.max_retries == 3
        assert config.config_file == ""

    def test_environment_config_custom_initialization(self):
        """Test EnvironmentConfig with custom values."""
        config = EnvironmentConfig(
            debug=True,
            debug_level="DEBUG",
            debug_timing=True,
            use_color=False,
            console_width=120,
            api_timeout=60.0,
            max_retries=5,
            config_file="/path/to/config",
        )

        assert config.debug is True
        assert config.debug_level == "DEBUG"
        assert config.debug_timing is True
        assert config.use_color is False
        assert config.console_width == 120
        assert config.api_timeout == 60.0
        assert config.max_retries == 5
        assert config.config_file == "/path/to/config"

    def test_environment_config_from_environment_with_defaults(self):
        """Test EnvironmentConfig.from_environment() with no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvironmentConfig.from_environment()

            assert config.debug is False
            assert config.debug_level == "INFO"
            assert config.debug_timing is False
            assert config.use_color is True
            assert config.console_width == 0
            assert config.api_timeout == 30.0
            assert config.max_retries == 3
            assert config.config_file == ""

    def test_environment_config_from_environment_with_values(self):
        """Test EnvironmentConfig.from_environment() with env vars set."""
        with patch.dict(
            os.environ,
            {
                "SPEC_DEBUG": "true",
                "SPEC_DEBUG_LEVEL": "debug",
                "SPEC_DEBUG_TIMING": "yes",
                "SPEC_USE_COLOR": "false",
                "SPEC_CONSOLE_WIDTH": "120",
                "SPEC_API_TIMEOUT": "60.5",
                "SPEC_MAX_RETRIES": "5",
                "SPEC_CONFIG_FILE": "/path/to/config.yaml",
            },
            clear=True,
        ):
            config = EnvironmentConfig.from_environment()

            assert config.debug is True
            assert config.debug_level == "DEBUG"  # Should be uppercased
            assert config.debug_timing is True
            assert config.use_color is False
            assert config.console_width == 120
            assert config.api_timeout == 60.5
            assert config.max_retries == 5
            assert config.config_file == "/path/to/config.yaml"

    def test_environment_config_validate_when_all_valid_then_returns_empty_dict(self):
        """Test validation with all valid configuration values."""
        config = EnvironmentConfig(
            debug=True,
            debug_level="WARNING",
            debug_timing=False,
            use_color=True,
            console_width=80,
            api_timeout=45.0,
            max_retries=2,
            config_file="/valid/path",
        )

        errors = config.validate()
        assert errors == {}

    def test_environment_config_validate_when_invalid_debug_level_then_returns_error(
        self,
    ):
        """Test validation with invalid debug level."""
        config = EnvironmentConfig(debug_level="INVALID")
        errors = config.validate()

        assert "debug_level" in errors
        assert "Invalid debug level" in errors["debug_level"]
        assert "INVALID" in errors["debug_level"]

    def test_environment_config_validate_when_invalid_console_width_then_returns_errors(
        self,
    ):
        """Test validation with invalid console width values."""
        # Negative width
        config_negative = EnvironmentConfig(console_width=-1)
        errors_negative = config_negative.validate()
        assert "console_width" in errors_negative
        assert "must be >= 0" in errors_negative["console_width"]

        # Too small width
        config_small = EnvironmentConfig(console_width=30)
        errors_small = config_small.validate()
        assert "console_width" in errors_small
        assert "must be >= 40" in errors_small["console_width"]

        # Valid widths (0 for auto, >= 40)
        config_auto = EnvironmentConfig(console_width=0)
        assert config_auto.validate() == {}

        config_valid = EnvironmentConfig(console_width=80)
        assert config_valid.validate() == {}

    def test_environment_config_validate_when_invalid_api_timeout_then_returns_errors(
        self,
    ):
        """Test validation with invalid API timeout values."""
        # Zero timeout
        config_zero = EnvironmentConfig(api_timeout=0.0)
        errors_zero = config_zero.validate()
        assert "api_timeout" in errors_zero
        assert "must be > 0" in errors_zero["api_timeout"]

        # Negative timeout
        config_negative = EnvironmentConfig(api_timeout=-5.0)
        errors_negative = config_negative.validate()
        assert "api_timeout" in errors_negative
        assert "must be > 0" in errors_negative["api_timeout"]

        # Too large timeout
        config_large = EnvironmentConfig(api_timeout=500.0)
        errors_large = config_large.validate()
        assert "api_timeout" in errors_large
        assert "too large" in errors_large["api_timeout"]

    def test_environment_config_validate_when_invalid_max_retries_then_returns_errors(
        self,
    ):
        """Test validation with invalid max retries values."""
        # Negative retries
        config_negative = EnvironmentConfig(max_retries=-1)
        errors_negative = config_negative.validate()
        assert "max_retries" in errors_negative
        assert "must be >= 0" in errors_negative["max_retries"]

        # Too many retries
        config_large = EnvironmentConfig(max_retries=15)
        errors_large = config_large.validate()
        assert "max_retries" in errors_large
        assert "too large" in errors_large["max_retries"]

    def test_environment_config_validate_when_multiple_errors_then_returns_all_errors(
        self,
    ):
        """Test validation with multiple invalid values."""
        config = EnvironmentConfig(
            debug_level="INVALID", console_width=-1, api_timeout=0.0, max_retries=-1
        )

        errors = config.validate()
        assert len(errors) == 4
        assert "debug_level" in errors
        assert "console_width" in errors
        assert "api_timeout" in errors
        assert "max_retries" in errors

    def test_environment_config_apply_overrides_when_valid_overrides_then_creates_new_config(
        self,
    ):
        """Test applying overrides creates new config with changes."""
        original_config = EnvironmentConfig(debug=False, api_timeout=30.0)

        new_config = original_config.apply_overrides(debug=True, api_timeout=60.0)

        # Original should be unchanged
        assert original_config.debug is False
        assert original_config.api_timeout == 30.0

        # New config should have overrides
        assert new_config.debug is True
        assert new_config.api_timeout == 60.0

        # Other fields should be copied
        assert new_config.debug_level == original_config.debug_level
        assert new_config.use_color == original_config.use_color

    def test_environment_config_apply_overrides_when_no_overrides_then_creates_identical_config(
        self,
    ):
        """Test applying no overrides creates identical config."""
        original_config = EnvironmentConfig(debug=True, console_width=120)
        new_config = original_config.apply_overrides()

        # Should be different objects but same values
        assert original_config is not new_config
        assert original_config.debug == new_config.debug
        assert original_config.console_width == new_config.console_width
        assert original_config.debug_level == new_config.debug_level

    def test_environment_config_apply_overrides_when_partial_overrides_then_preserves_other_fields(
        self,
    ):
        """Test applying partial overrides preserves non-overridden fields."""
        original_config = EnvironmentConfig(
            debug=True,
            debug_level="DEBUG",
            use_color=False,
            console_width=100,
            api_timeout=45.0,
        )

        new_config = original_config.apply_overrides(console_width=120)

        # Only console_width should change
        assert new_config.console_width == 120
        assert new_config.debug == original_config.debug
        assert new_config.debug_level == original_config.debug_level
        assert new_config.use_color == original_config.use_color
        assert new_config.api_timeout == original_config.api_timeout


class TestEnvironmentConfigLogging:
    """Test EnvironmentConfig logging integration."""

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_from_environment_logs_loading_and_configuration(self, mock_logger):
        """Test that from_environment() logs configuration loading."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "true"}, clear=True):
            EnvironmentConfig.from_environment()

            # Should log loading start
            mock_logger.log.assert_any_call(
                "DEBUG", "Loading environment configuration"
            )

            # Should log configuration details
            info_call = None
            for call in mock_logger.log.call_args_list:
                if (
                    call[0][0] == "INFO"
                    and "Environment configuration loaded" in call[0][1]
                ):
                    info_call = call
                    break

            assert info_call is not None
            assert info_call[1]["debug"] is True

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_validate_logs_validation_results(self, mock_logger):
        """Test that validate() logs validation results."""
        config = EnvironmentConfig(debug_level="INVALID")
        config.validate()

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Environment configuration validated",
            error_count=1,
            errors=["debug_level"],
        )

    @patch("spec_cli.utils.env_utils.debug_logger")
    def test_apply_overrides_logs_override_details(self, mock_logger):
        """Test that apply_overrides() logs override details."""
        config = EnvironmentConfig()
        config.apply_overrides(debug=True, api_timeout=60.0)

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Creating config with overrides",
            override_count=2,
            overrides=["debug", "api_timeout"],
        )
