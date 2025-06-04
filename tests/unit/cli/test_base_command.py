"""Tests for BaseCommand class."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.base_command import BaseCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.core.error_handler import ErrorHandler
from spec_cli.exceptions import SpecError


class TestBaseCommand:
    """Test BaseCommand class functionality."""

    # Concrete implementation for testing
    class ConcreteCommand(BaseCommand):
        """Concrete command implementation for testing."""

        def execute(self, **kwargs: Any) -> dict[str, Any]:
            """Test execute implementation."""
            if kwargs.get("should_fail"):
                raise ValueError("Test failure")

            return {
                "success": True,
                "message": "Test executed successfully",
                "data": kwargs.get("test_data"),
            }

        def validate_arguments(self, **kwargs: Any) -> None:
            """Test validation implementation."""
            if kwargs.get("invalid_args"):
                raise SpecError("Invalid arguments provided")

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.root_path = tmp_path
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.is_initialized.return_value = True
        settings.validate_permissions.return_value = None
        return settings

    @pytest.fixture
    def command(self, mock_settings: Mock) -> "TestBaseCommand.ConcreteCommand":
        """Create test command instance."""
        return self.ConcreteCommand(settings=mock_settings)

    def test_base_command_when_initialized_then_creates_error_handler(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test that BaseCommand creates error handler with correct context."""
        assert isinstance(command.error_handler, ErrorHandler)
        assert command.error_handler.default_context["module"] == "cli"
        assert command.error_handler.default_context["component"] == "concrete"

    def test_base_command_when_no_settings_provided_then_uses_default(self):
        """Test BaseCommand uses default settings when none provided."""
        with patch("spec_cli.cli.base_command.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            command = self.ConcreteCommand()

            mock_get_settings.assert_called_once()
            assert command.settings is mock_settings

    def test_base_command_when_custom_settings_provided_then_uses_them(
        self, mock_settings: Mock
    ):
        """Test BaseCommand uses provided settings."""
        command = self.ConcreteCommand(settings=mock_settings)
        assert command.settings is mock_settings

    def test_validate_repository_state_when_initialized_and_required_then_passes(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test repository validation passes when initialized and required."""
        # Should not raise any exception
        command.validate_repository_state(require_initialized=True)

    def test_validate_repository_state_when_not_initialized_and_required_then_raises_error(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test repository validation fails when not initialized but required."""
        command.settings.is_initialized.return_value = False

        with pytest.raises(SpecError, match="not initialized"):
            command.validate_repository_state(require_initialized=True)

    def test_validate_repository_state_when_not_initialized_and_not_required_then_passes(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test repository validation passes when not initialized and not required."""
        command.settings.is_initialized.return_value = False

        # Should not raise any exception
        command.validate_repository_state(require_initialized=False)

    def test_validate_repository_state_when_permission_error_then_raises_spec_error(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test repository validation converts permission errors to SpecError."""
        command.settings.validate_permissions.side_effect = OSError("Permission denied")

        with pytest.raises(SpecError):
            command.validate_repository_state()

    def test_validate_arguments_when_base_implementation_then_passes(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test base validate_arguments implementation passes by default."""
        # Should not raise any exception
        command.validate_arguments(some_arg="value")

    def test_safe_execute_when_successful_then_returns_result(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test safe_execute returns result when execution succeeds."""
        result = command.safe_execute(test_data="example")

        assert result["success"] is True
        assert result["message"] == "Test executed successfully"
        assert result["data"] == "example"

    def test_safe_execute_when_validation_fails_then_raises_spec_error(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test safe_execute re-raises SpecError from validation."""
        with pytest.raises(SpecError, match="Invalid arguments"):
            command.safe_execute(invalid_args=True)

    def test_safe_execute_when_execution_raises_spec_error_then_re_raises(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test safe_execute re-raises SpecError from execution."""
        # Override execute to raise SpecError
        original_execute = command.execute
        command.execute = lambda **kwargs: (_ for _ in ()).throw(
            SpecError("Test spec error")
        )

        with pytest.raises(SpecError, match="Test spec error"):
            command.safe_execute()

        # Restore original method
        command.execute = original_execute

    def test_safe_execute_when_execution_raises_other_error_then_wraps_as_spec_error(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test safe_execute wraps non-SpecError exceptions."""
        with pytest.raises(SpecError):
            command.safe_execute(should_fail=True)

    def test_get_command_name_when_called_then_returns_class_name_lowercase(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test get_command_name returns lowercase class name."""
        assert command.get_command_name() == "concrete"

    def test_get_command_name_when_class_ends_with_command_then_strips_command(self):
        """Test get_command_name strips 'command' suffix."""

        class TestCommand(BaseCommand):
            def execute(self, **kwargs: Any) -> dict[str, Any]:
                return {"success": True, "message": "test"}

        command = TestCommand()
        assert command.get_command_name() == "test"

    def test_create_result_when_minimal_args_then_creates_basic_result(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test create_result with minimal arguments."""
        result = command.create_result(True, "Success message")

        assert result["success"] is True
        assert result["message"] == "Success message"
        assert result["command"] == "concrete"
        assert "data" not in result

    def test_create_result_when_data_provided_then_includes_data(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test create_result includes data when provided."""
        test_data = {"key": "value"}
        result = command.create_result(False, "Error message", data=test_data)

        assert result["success"] is False
        assert result["message"] == "Error message"
        assert result["data"] == test_data

    def test_create_result_when_additional_fields_then_includes_them(
        self, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test create_result includes additional fields."""
        result = command.create_result(
            True, "Success", extra_field="extra_value", count=42
        )

        assert result["success"] is True
        assert result["message"] == "Success"
        assert result["extra_field"] == "extra_value"
        assert result["count"] == 42

    def test_execute_when_abstract_method_then_requires_implementation(
        self, mock_settings: Mock
    ):
        """Test that execute is abstract and requires implementation."""
        # BaseCommand cannot be instantiated directly
        with pytest.raises(TypeError, match="abstract method"):
            BaseCommand(settings=mock_settings)  # type: ignore

    @patch("spec_cli.cli.base_command.debug_logger")
    def test_initialization_when_called_then_logs_initialization(
        self, mock_logger: Mock, mock_settings: Mock
    ):
        """Test that command initialization is logged."""
        _command = self.ConcreteCommand(settings=mock_settings)

        mock_logger.log.assert_called_with(
            "INFO",
            "Initialized ConcreteCommand",
            command="concrete",
            root_path=str(mock_settings.root_path),
        )

    @patch("spec_cli.cli.base_command.debug_logger")
    def test_safe_execute_when_successful_then_logs_completion(
        self, mock_logger: Mock, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test that successful execution is logged."""
        command.safe_execute(test_data="example")

        # Find the completion log call
        completion_calls = [
            call
            for call in mock_logger.log.call_args_list
            if len(call[0]) > 1 and "completed successfully" in call[0][1]
        ]
        assert len(completion_calls) == 1

        call_args = completion_calls[0]
        kwargs = call_args[1]
        assert kwargs["success"] is True
        assert kwargs["command"] == "concrete"

    @patch("spec_cli.cli.base_command.debug_logger")
    def test_safe_execute_when_called_then_uses_timer(
        self, mock_logger: Mock, command: "TestBaseCommand.ConcreteCommand"
    ):
        """Test that safe_execute uses debug timer."""
        command.safe_execute()

        # Verify timer was used
        mock_logger.timer.assert_called_with("concrete_execution")


class TestBaseCommandIntegration:
    """Test BaseCommand integration with other components."""

    class IntegrationTestCommand(BaseCommand):
        """Command for integration testing."""

        def execute(self, **kwargs: Any) -> dict[str, Any]:
            """Integration test execute implementation."""
            return self.create_result(True, "Integration test successful")

        def validate_arguments(self, **kwargs: Any) -> None:
            """Integration test validation."""
            self.validate_repository_state()

    def test_command_integration_when_repository_valid_then_executes_successfully(
        self, tmp_path: Path
    ):
        """Test full command integration with valid repository."""
        # Create mock settings that simulate initialized repository
        with patch("spec_cli.cli.base_command.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=SpecSettings)
            mock_settings.root_path = tmp_path
            mock_settings.is_initialized.return_value = True
            mock_settings.validate_permissions.return_value = None
            mock_get_settings.return_value = mock_settings

            command = self.IntegrationTestCommand()
            result = command.safe_execute()

            assert result["success"] is True
            assert result["message"] == "Integration test successful"
            assert result["command"] == "integrationtest"

    def test_command_integration_when_repository_invalid_then_fails(
        self, tmp_path: Path
    ):
        """Test command integration fails with invalid repository."""
        with patch("spec_cli.cli.base_command.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=SpecSettings)
            mock_settings.root_path = tmp_path
            mock_settings.is_initialized.return_value = False
            mock_get_settings.return_value = mock_settings

            command = self.IntegrationTestCommand()

            with pytest.raises(SpecError, match="not initialized"):
                command.safe_execute()
