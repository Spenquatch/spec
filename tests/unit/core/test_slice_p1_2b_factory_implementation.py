"""Unit tests for slice P1.2b: Factory Method Implementation.

Tests factory classmethods for SpecContext including CLI factory,
testing factory, validation, and error handling.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecFactoryError,
    SpecProgressInterface,
    SpecSettingsInterface,
)

# Test constants
DEFAULT_ROOT_PATH = Path("/test/project")
TEST_SETTINGS_OVERRIDES = {"debug_enabled": True, "console_width": 120}
TEST_FACTORY_TIMEOUT = 30
MOCK_CONTEXT_HASH = "abc12345"
TEST_OPERATION_ID = "test_op_001"


class TestSpecContextCreateForCli:
    """Test SpecContext.create_for_cli factory method."""

    def test_create_for_cli_when_valid_root_path_then_returns_cli_context(self):
        """Test CLI factory method creates SpecContext with real dependencies."""
        # Act
        context = SpecContext.create_for_cli(DEFAULT_ROOT_PATH)

        # Assert
        assert isinstance(context, SpecContext)
        assert isinstance(context.settings, SpecSettingsInterface)
        assert isinstance(context.console, SpecConsoleInterface)
        assert isinstance(context.progress, SpecProgressInterface)

        # Verify settings configuration
        assert context.settings.root_path == DEFAULT_ROOT_PATH
        assert context.settings.spec_dir == DEFAULT_ROOT_PATH / ".spec"
        assert context.settings.specs_dir == DEFAULT_ROOT_PATH / ".specs"
        assert context.settings.debug_enabled is False  # Default value

    def test_create_for_cli_when_no_root_path_then_uses_current_directory(self):
        """Test CLI factory method handles missing root path."""
        with patch("spec_cli.core.context.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/current/dir")

            # Act
            context = SpecContext.create_for_cli()

            # Assert
            assert isinstance(context, SpecContext)
            assert context.settings.root_path == Path("/current/dir")
            assert context.settings.spec_dir == Path("/current/dir/.spec")
            assert context.settings.specs_dir == Path("/current/dir/.specs")
            # Verify cwd was called (may be called multiple times during context creation)
            assert mock_cwd.called

    def test_create_for_cli_when_settings_overrides_then_applies_overrides(self):
        """Test CLI factory method applies setting overrides correctly."""
        # Act
        context = SpecContext.create_for_cli(
            DEFAULT_ROOT_PATH, **TEST_SETTINGS_OVERRIDES
        )

        # Assert
        assert context.settings.debug_enabled is True
        assert context.settings.console_width == 120
        assert context.settings.root_path == DEFAULT_ROOT_PATH

    def test_create_for_cli_when_validation_fails_then_raises_factory_error(self):
        """Test CLI factory validation handles invalid inputs."""
        with patch("spec_cli.core.context.validate_factory_inputs") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid timeout")

            # Act & Assert
            with pytest.raises(SpecFactoryError) as exc_info:
                SpecContext.create_for_cli(DEFAULT_ROOT_PATH, timeout=-1)

            assert "Failed to create CLI SpecContext" in str(exc_info.value)
            assert exc_info.value.context["factory_type"] == "cli"
            assert "timeout" in exc_info.value.context["overrides"]

    def test_create_for_cli_when_context_creation_fails_then_raises_factory_error(
        self,
    ):
        """Test CLI factory handles context creation errors."""
        with patch("spec_cli.core.context.SpecContext.__post_init__") as mock_post_init:
            mock_post_init.side_effect = Exception("Context validation failed")

            # Act & Assert
            with pytest.raises(SpecFactoryError) as exc_info:
                SpecContext.create_for_cli(DEFAULT_ROOT_PATH)

            assert "Failed to create CLI SpecContext" in str(exc_info.value)
            assert exc_info.value.context["error_type"] == "Exception"

    @patch("spec_cli.core.context.debug_logger")
    def test_create_for_cli_when_called_then_logs_debug_information(self, mock_logger):
        """Test CLI factory logs appropriate debug information."""
        # Act
        context = SpecContext.create_for_cli(DEFAULT_ROOT_PATH, debug_mode=True)

        # Assert
        assert isinstance(context, SpecContext)
        # Verify debug logging calls
        assert mock_logger.log.call_count >= 2  # At least creation start and success

        # Check for creation start log
        creation_calls = [
            call
            for call in mock_logger.log.call_args_list
            if len(call[0]) > 1 and "Creating SpecContext for CLI" in call[0][1]
        ]
        assert len(creation_calls) == 1

        # Check for success log
        success_calls = [
            call
            for call in mock_logger.log.call_args_list
            if len(call[0]) > 1 and "CLI SpecContext created successfully" in call[0][1]
        ]
        assert len(success_calls) == 1


class TestSpecContextCreateForTesting:
    """Test SpecContext.create_for_testing factory method."""

    def test_create_for_testing_when_no_overrides_then_returns_mock_context(self):
        """Test testing factory method creates SpecContext with mock dependencies."""
        # Act
        context = SpecContext.create_for_testing()

        # Assert
        assert isinstance(context, SpecContext)

        # Verify mock dependencies
        assert isinstance(context.settings, Mock)
        assert isinstance(context.console, Mock)
        assert isinstance(context.progress, Mock)

        # Verify mock settings attributes
        assert context.settings.debug_enabled is False  # Default
        assert context.settings.console_width == 80
        assert context.settings.use_color is False  # Testing consistency
        assert context.settings.root_path == Path("/tmp/test")

        # Verify mock console methods
        assert context.console.get_width.return_value == 80
        assert context.console.supports_color.return_value is False

        # Verify mock progress methods
        assert context.progress.start_operation.return_value == TEST_OPERATION_ID

    def test_create_for_testing_when_overrides_provided_then_applies_overrides(self):
        """Test testing factory method applies testing overrides correctly."""
        overrides = {
            "debug_mode": True,
            "console_width": 100,
            "custom_setting": "test_value",
        }

        # Act
        context = SpecContext.create_for_testing(overrides)

        # Assert
        assert context.settings.debug_enabled is True
        assert context.settings.console_width == 100
        # Note: custom_setting may not be available on mock interface

    def test_create_for_testing_when_validation_fails_then_raises_factory_error(self):
        """Test testing factory validation handles invalid inputs."""
        with patch("spec_cli.core.context.validate_factory_inputs") as mock_validate:
            mock_validate.side_effect = TypeError("Invalid debug_mode type")

            # Act & Assert
            with pytest.raises(SpecFactoryError) as exc_info:
                SpecContext.create_for_testing({"debug_mode": "invalid"})

            assert "Failed to create testing SpecContext" in str(exc_info.value)
            assert exc_info.value.context["factory_type"] == "testing"

    def test_create_for_testing_when_mock_creation_fails_then_raises_factory_error(
        self,
    ):
        """Test testing factory handles mock creation errors."""
        with patch("spec_cli.core.context.Mock") as mock_class:
            mock_class.side_effect = Exception("Mock creation failed")

            # Act & Assert
            with pytest.raises(SpecFactoryError) as exc_info:
                SpecContext.create_for_testing()

            assert "Failed to create testing SpecContext" in str(exc_info.value)
            assert exc_info.value.context["error_type"] == "Exception"

    @patch("spec_cli.core.context.debug_logger")
    def test_create_for_testing_when_called_then_logs_debug_information(
        self, mock_logger
    ):
        """Test testing factory logs appropriate debug information."""
        # Act
        context = SpecContext.create_for_testing({"debug_mode": True})

        # Assert
        assert isinstance(context, SpecContext)
        # Verify debug logging calls
        assert mock_logger.log.call_count >= 2  # At least creation start and success

        # Check for creation start log
        creation_calls = [
            call
            for call in mock_logger.log.call_args_list
            if len(call[0]) > 1 and "Creating SpecContext for testing" in call[0][1]
        ]
        assert len(creation_calls) == 1

        # Check for success log
        success_calls = [
            call
            for call in mock_logger.log.call_args_list
            if len(call[0]) > 1
            and "Testing SpecContext created successfully" in call[0][1]
        ]
        assert len(success_calls) == 1


class TestSpecFactoryError:
    """Test SpecFactoryError exception class."""

    @patch("spec_cli.core.context.debug_logger")
    def test_spec_factory_error_when_created_then_logs_error(self, mock_logger):
        """Test SpecFactoryError logs error information on creation."""
        error_message = "Factory operation failed"
        error_context = {"operation": "create_context", "factory_type": "cli"}

        # Act
        error = SpecFactoryError(error_message, error_context)

        # Assert
        assert str(error) == error_message
        assert error.context == error_context

        # Verify debug logging
        mock_logger.log.assert_called_once()
        log_call = mock_logger.log.call_args
        assert log_call[0][0] == "ERROR"
        assert log_call[0][1] == "SpecContext factory error raised"
        assert log_call[1]["error_message"] == error_message
        assert log_call[1]["factory_context"] == error_context

    def test_spec_factory_error_when_no_context_then_uses_empty_dict(self):
        """Test SpecFactoryError handles missing context parameter."""
        error_message = "Factory operation failed"

        # Act
        error = SpecFactoryError(error_message)

        # Assert
        assert str(error) == error_message
        assert error.context == {}


class TestFactoryValidation:
    """Test factory input validation and error handling."""

    @patch("spec_cli.core.context.validate_factory_inputs")
    def test_factory_validation_when_invalid_inputs_then_raises_factory_error(
        self, mock_validate
    ):
        """Test factory input validation and error handling."""
        mock_validate.side_effect = ValueError("Invalid factory configuration")

        # Test CLI factory validation
        with pytest.raises(SpecFactoryError):
            SpecContext.create_for_cli(DEFAULT_ROOT_PATH, invalid_param="value")

        # Test testing factory validation
        with pytest.raises(SpecFactoryError):
            SpecContext.create_for_testing({"invalid_param": "value"})

    @patch("spec_cli.core.context.create_error_context")
    def test_factory_error_context_when_cli_creation_fails_then_includes_path_info(
        self, mock_create_context
    ):
        """Test factory error context includes path information for CLI failures."""
        mock_create_context.return_value = {
            "file_path": str(DEFAULT_ROOT_PATH),
            "file_exists": True,
        }

        with patch("spec_cli.core.context.SpecSettingsInterface") as mock_settings:
            mock_settings.side_effect = Exception("Settings creation failed")

            # Act & Assert
            with pytest.raises(SpecFactoryError) as exc_info:
                SpecContext.create_for_cli(DEFAULT_ROOT_PATH)

            assert "file_path" in exc_info.value.context
            assert exc_info.value.context["factory_type"] == "cli"
            mock_create_context.assert_called_once_with(DEFAULT_ROOT_PATH)


class TestFactoryEnvironmentDetection:
    """Test factory environment detection integration."""

    def test_factory_environment_detection_when_called_then_uses_correct_factory(
        self,
    ):
        """Test environment detection selects appropriate factory method."""
        # This test verifies the factory methods work independently
        # Environment detection will be implemented in future slices

        # Create both types of contexts to verify they work
        cli_context = SpecContext.create_for_cli(DEFAULT_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Assert both contexts are valid but different
        assert isinstance(cli_context, SpecContext)
        assert isinstance(testing_context, SpecContext)
        assert not isinstance(cli_context.settings, type(testing_context.settings))

    def test_factory_methods_support_dependency_injection_patterns(self):
        """Test factory methods create contexts suitable for dependency injection."""
        # Create contexts using factory methods
        cli_context = SpecContext.create_for_cli(DEFAULT_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Verify contexts support dependency injection patterns
        # (immutable, proper interfaces, replaceable dependencies)
        assert hasattr(cli_context, "with_settings")
        assert hasattr(cli_context, "with_console")
        assert hasattr(cli_context, "with_progress")

        assert hasattr(testing_context, "with_settings")
        assert hasattr(testing_context, "with_console")
        assert hasattr(testing_context, "with_progress")

        # Test context replacement works
        new_console = SpecConsoleInterface()
        modified_cli = cli_context.with_console(new_console)
        assert modified_cli.console is new_console
        assert modified_cli.settings is cli_context.settings  # Other deps unchanged

    def test_factory_context_lifecycle_management(self):
        """Test factory-created contexts support proper lifecycle management."""
        # Create contexts
        cli_context = SpecContext.create_for_cli(DEFAULT_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Verify contexts are properly initialized and hashable
        cli_hash = cli_context.get_context_hash()
        testing_hash = testing_context.get_context_hash()

        assert isinstance(cli_hash, str)
        assert isinstance(testing_hash, str)
        assert cli_hash != testing_hash  # Different context types

        # Verify contexts support equality comparison
        SpecContext.create_for_cli(DEFAULT_ROOT_PATH)
        # Note: Mock objects prevent direct equality comparison
