"""Unit tests for factory_utils module."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.utils.factory_utils import (
    detect_environment_type,
    validate_factory_inputs,
)


class TestDetectEnvironmentType:
    """Test environment detection functionality."""

    def test_detect_environment_type_when_pytest_in_modules_then_returns_testing(self):
        """Test environment detection identifies pytest in modules."""
        with patch.dict(sys.modules, {"pytest": MagicMock()}):
            result = detect_environment_type()
            assert result == "testing"

    def test_detect_environment_type_when_pytest_in_argv_then_returns_testing(self):
        """Test environment detection identifies pytest in argv."""
        with patch.object(sys, "argv", ["python", "-m", "pytest", "tests/"]):
            result = detect_environment_type()
            assert result == "testing"

    def test_detect_environment_type_when_spec_env_testing_then_returns_testing(self):
        """Test environment detection via SPEC_ENV variable."""
        with patch.dict(os.environ, {"SPEC_ENV": "testing"}):
            result = detect_environment_type()
            assert result == "testing"

    def test_detect_environment_type_when_testing_env_set_then_returns_testing(self):
        """Test environment detection via TESTING variable."""
        with patch.dict(os.environ, {"TESTING": "1"}):
            result = detect_environment_type()
            assert result == "testing"

    def test_detect_environment_type_when_cli_filename_then_returns_cli(self):
        """Test environment detection identifies CLI entry point."""
        mock_frame = MagicMock()
        mock_frame.f_code.co_filename = "/path/to/spec_cli/cli.py"
        mock_frame.f_back = None

        with (
            patch(
                "spec_cli.utils.factory_utils.inspect.currentframe",
                return_value=mock_frame,
            ),
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "argv", ["python", "script.py"]),  # Non-pytest argv
        ):
            # Remove pytest from modules temporarily if present
            pytest_module = sys.modules.pop("pytest", None)
            try:
                result = detect_environment_type()
                assert result == "cli"
            finally:
                if pytest_module:
                    sys.modules["pytest"] = pytest_module

    def test_detect_environment_type_when_cli_args_then_returns_cli(self):
        """Test environment detection identifies CLI arguments."""
        with (
            patch.object(sys, "argv", ["spec", "init"]),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "spec_cli.utils.factory_utils.inspect.currentframe", return_value=None
            ),
        ):
            # Remove pytest from modules temporarily if present
            pytest_module = sys.modules.pop("pytest", None)
            try:
                result = detect_environment_type()
                assert result == "cli"
            finally:
                if pytest_module:
                    sys.modules["pytest"] = pytest_module

    def test_detect_environment_type_when_no_indicators_then_returns_unknown(self):
        """Test environment detection returns unknown when no clear indicators."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "argv", ["python", "script.py"]),
            patch(
                "spec_cli.utils.factory_utils.inspect.currentframe", return_value=None
            ),
        ):
            # Remove pytest from modules temporarily if present
            pytest_module = sys.modules.pop("pytest", None)
            try:
                result = detect_environment_type()
                assert result == "unknown"
            finally:
                if pytest_module:
                    sys.modules["pytest"] = pytest_module


class TestValidateFactoryInputs:
    """Test factory input validation functionality."""

    def test_validate_factory_inputs_when_valid_config_then_returns_validated_config(
        self,
    ):
        """Test factory input validation with valid configuration."""
        inputs = {
            "factory_type": "context",
            "timeout": 30,
            "debug_mode": True,
            "factory_config": {"key": "value"},
        }
        result = validate_factory_inputs(**inputs)

        assert result["factory_type"] == "context"
        assert result["timeout"] == 30
        assert result["debug_mode"] is True
        assert result["factory_config"] == {"key": "value"}

    def test_validate_factory_inputs_when_empty_then_returns_empty_dict(self):
        """Test validation with no inputs returns empty dict."""
        result = validate_factory_inputs()
        assert result == {}

    def test_validate_factory_inputs_when_factory_type_string_conversion_then_normalizes(
        self,
    ):
        """Test factory_type string normalization."""
        result = validate_factory_inputs(factory_type="  CONTEXT  ")
        assert result["factory_type"] == "context"

    def test_validate_factory_inputs_when_timeout_string_conversion_then_converts_to_int(
        self,
    ):
        """Test timeout string to int conversion."""
        result = validate_factory_inputs(timeout="45")
        assert result["timeout"] == 45
        assert isinstance(result["timeout"], int)

    def test_validate_factory_inputs_when_debug_mode_string_conversion_then_converts_to_bool(
        self,
    ):
        """Test debug_mode string to bool conversion."""
        true_values = ["true", "1", "yes", "on", "TRUE", "Yes", "ON"]
        false_values = ["false", "0", "no", "off", "FALSE", "anything_else"]

        for value in true_values:
            result = validate_factory_inputs(debug_mode=value)
            assert result["debug_mode"] is True

        for value in false_values:
            result = validate_factory_inputs(debug_mode=value)
            assert result["debug_mode"] is False

    def test_validate_factory_inputs_when_factory_config_copy_then_creates_independent_copy(
        self,
    ):
        """Test factory_config creates independent copy."""
        original_config = {"key": "value", "nested": {"inner": "data"}}
        result = validate_factory_inputs(factory_config=original_config)

        # Modify original to verify independence
        original_config["key"] = "modified"
        assert result["factory_config"]["key"] == "value"
        assert result["factory_config"] is not original_config

    def test_validate_factory_inputs_when_unvalidated_parameters_then_passes_through(
        self,
    ):
        """Test unvalidated parameters are passed through with warning."""
        result = validate_factory_inputs(custom_param="value", another_param=123)
        assert result["custom_param"] == "value"
        assert result["another_param"] == 123

    def test_validate_factory_inputs_when_invalid_factory_type_then_raises_type_error(
        self,
    ):
        """Test invalid factory_type raises TypeError."""
        with pytest.raises(TypeError, match="factory_type must be string"):
            validate_factory_inputs(factory_type=123)

        with pytest.raises(ValueError, match="factory_type cannot be empty"):
            validate_factory_inputs(factory_type="")

        with pytest.raises(ValueError, match="factory_type cannot be empty"):
            validate_factory_inputs(factory_type="   ")

    def test_validate_factory_inputs_when_invalid_timeout_then_raises_type_error(self):
        """Test invalid timeout raises TypeError."""
        with pytest.raises(TypeError, match="timeout must be convertible to int"):
            validate_factory_inputs(timeout="invalid")

        with pytest.raises(TypeError, match="timeout must be int"):
            validate_factory_inputs(timeout=30.5)

        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_factory_inputs(timeout=0)

        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_factory_inputs(timeout=-5)

    def test_validate_factory_inputs_when_invalid_debug_mode_then_raises_type_error(
        self,
    ):
        """Test invalid debug_mode raises TypeError."""
        with pytest.raises(TypeError, match="debug_mode must be bool or convertible"):
            validate_factory_inputs(debug_mode=123)

    def test_validate_factory_inputs_when_invalid_factory_config_then_raises_type_error(
        self,
    ):
        """Test invalid factory_config raises TypeError."""
        with pytest.raises(TypeError, match="factory_config must be dict"):
            validate_factory_inputs(factory_config="not_a_dict")

        with pytest.raises(TypeError, match="factory_config must be dict"):
            validate_factory_inputs(factory_config=123)

    def test_validate_factory_inputs_when_mixed_valid_invalid_then_validates_good_raises_bad(
        self,
    ):
        """Test mixed valid and invalid parameters."""
        # Valid parameters should be validated, invalid should raise
        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_factory_inputs(
                factory_type="context",  # valid
                timeout=-1,  # invalid
                debug_mode=True,  # valid
            )

    def test_validate_factory_inputs_when_all_parameter_types_then_validates_correctly(
        self,
    ):
        """Test comprehensive validation of all supported parameter types."""
        inputs = {
            "factory_type": "  TEST_TYPE  ",
            "timeout": "60",
            "debug_mode": "true",
            "factory_config": {"nested": {"key": "value"}},
            "custom_string": "value",
            "custom_int": 42,
            "custom_list": [1, 2, 3],
        }

        result = validate_factory_inputs(**inputs)

        # Validated parameters
        assert result["factory_type"] == "test_type"
        assert result["timeout"] == 60
        assert result["debug_mode"] is True
        assert result["factory_config"] == {"nested": {"key": "value"}}

        # Pass-through parameters
        assert result["custom_string"] == "value"
        assert result["custom_int"] == 42
        assert result["custom_list"] == [1, 2, 3]
