"""Unit tests for add command migration to context injection."""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.cli.commands.add import add_command
from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)


def get_unwrapped_function(func):
    """Get the completely unwrapped function by following __wrapped__ chain."""
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func

class TestAddCommandMigration:
    """Test add command migration to context injection."""

    # Test constants
    TEST_FILES = ("test.md", "index.md")
    TEST_FILE_PATHS = [Path("test.md"), Path("index.md")]
    EXPECTED_SUCCESS_RESULT = {"success": True, "message": "Files added"}
    EXPECTED_ERROR_RESULT = {"success": False, "message": "Add failed"}

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        return SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

    def test_add_command_when_context_decorator_applied_then_receives_context_parameter(
        self, mock_context
    ):
        """Test that add command receives context parameter when decorator applied."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = self.EXPECTED_SUCCESS_RESULT
            mock_cmd_class.return_value = mock_instance

            # Call the completely unwrapped function directly with context as first parameter
            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

            # Verify context was passed to AddCommand constructor
            mock_cmd_class.assert_called_once_with(settings=mock_context.settings)

    def test_add_command_when_using_context_settings_then_accesses_settings_from_context(
        self, mock_context
    ):
        """Test that add command accesses settings from context."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = self.EXPECTED_SUCCESS_RESULT
            mock_cmd_class.return_value = mock_instance

            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

            # Verify settings accessed from context
            mock_cmd_class.assert_called_once_with(settings=mock_context.settings)

    def test_add_command_when_migrated_signature_then_maintains_click_compatibility(self):
        """Test that migrated command maintains Click compatibility."""
        # Verify function has required Click attributes
        assert hasattr(add_command, "callback")
        assert hasattr(add_command, "params")
        assert hasattr(add_command, "name")

        # Verify callback signature includes expected parameters
        import inspect

        sig = inspect.signature(add_command.callback)
        params = list(sig.parameters.keys())

        # Note: context is injected, so it's not in the Click signature
        assert "debug" in params
        assert "verbose" in params
        assert "files" in params
        assert "force" in params
        assert "dry_run" in params

    def test_add_command_when_behavior_validation_then_identical_to_original_behavior(
        self, mock_context
    ):
        """Test that migrated command maintains identical behavior."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = self.EXPECTED_SUCCESS_RESULT
            mock_cmd_class.return_value = mock_instance

            # Execute command
            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(
                mock_context,
                debug=True,
                verbose=True,
                files=self.TEST_FILES,
                force=True,
                dry_run=True,
            )

            # Verify same behavior: file validation, command creation, execution
            mock_validate.assert_called_once_with(list(self.TEST_FILES))
            mock_cmd_class.assert_called_once_with(settings=mock_context.settings)
            mock_instance.safe_execute.assert_called_once_with(
                files=self.TEST_FILE_PATHS, force=True, dry_run=True
            )

    def test_add_command_when_no_valid_files_then_raises_bad_parameter(
        self, mock_context
    ):
        """Test that command raises BadParameter when no valid files provided."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.return_value = []

            with pytest.raises(click.BadParameter, match="No valid file paths provided"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=(),
                    force=False,
                    dry_run=False,
                )

    def test_add_command_when_execution_fails_then_raises_click_exception(
        self, mock_context
    ):
        """Test that command raises ClickException when execution fails."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = self.EXPECTED_ERROR_RESULT
            mock_cmd_class.return_value = mock_instance

            with pytest.raises(click.ClickException, match="Add failed"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=self.TEST_FILES,
                    force=False,
                    dry_run=False,
                )

    def test_add_command_when_unexpected_exception_then_wraps_in_click_exception(
        self, mock_context
    ):
        """Test that unexpected exceptions are wrapped in ClickException."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_cmd_class.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(click.ClickException, match="Add failed: Unexpected error"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=self.TEST_FILES,
                    force=False,
                    dry_run=False,
                )

    def test_add_command_when_missing_context_then_raises_context_error(self):
        """Test that add command raises error when context is missing."""
        with pytest.raises(TypeError):
            # This should fail because context parameter is required
            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(  # type: ignore[call-arg]
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

    def test_add_command_when_invalid_context_then_raises_validation_error(self):
        """Test that add command raises error when context is invalid."""
        with pytest.raises(click.ClickException, match="Add failed"):
            # This should fail because invalid context doesn't have required attributes
            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(
                "invalid_context",  # type: ignore[arg-type]
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

class TestAddCommandContextUsage:
    """Test that add command properly uses context dependencies."""

    TEST_FILES = ("test.md",)
    TEST_FILE_PATHS = [Path("test.md")]

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        return SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

    def test_add_command_when_context_factory_provides_dependencies_then_uses_injected_instances(
        self, mock_context
    ):
        """Test that command uses dependencies from context factory."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = {"success": True, "message": "OK"}
            mock_cmd_class.return_value = mock_instance

            unwrapped_func = get_unwrapped_function(add_command.callback)
            unwrapped_func(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

            # Verify the exact settings instance from context is used
            mock_cmd_class.assert_called_once_with(settings=mock_context.settings)

    def test_add_command_when_singleton_elimination_complete_then_no_global_state_access(
        self, mock_context
    ):
        """Test that command has no remaining global state access."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = {"success": True, "message": "OK"}
            mock_cmd_class.return_value = mock_instance

            # Mock any potential singleton access that should not happen
            with (
                patch("spec_cli.config.settings.get_settings") as mock_get_settings,
                patch("spec_cli.ui.console.get_console") as mock_get_console,
            ):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=self.TEST_FILES,
                    force=False,
                    dry_run=False,
                )

                # Verify no singleton access occurred in the add command wrapper
                # Note: The AddCommand class may still use singletons internally
                mock_get_settings.assert_not_called()
                mock_get_console.assert_not_called()

class TestAddCommandErrorHandling:
    """Test error handling in migrated add command."""

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        return SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

    def test_add_command_when_click_bad_parameter_then_reraises_unchanged(
        self, mock_context
    ):
        """Test that Click BadParameter exceptions are re-raised unchanged."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.side_effect = click.BadParameter("Invalid parameter")

            with pytest.raises(click.BadParameter, match="Invalid parameter"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=(),
                    force=False,
                    dry_run=False,
                )

    def test_add_command_when_click_exception_then_reraises_unchanged(
        self, mock_context
    ):
        """Test that Click exceptions are re-raised unchanged."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = [Path("test.md")]
            mock_cmd_class.side_effect = click.ClickException("Click error")

            with pytest.raises(click.ClickException, match="Click error"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=("test.md",),
                    force=False,
                    dry_run=False,
                )

    def test_add_command_when_generic_exception_then_wraps_in_click_exception(
        self, mock_context
    ):
        """Test that generic exceptions are wrapped in ClickException."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = [Path("test.md")]
            mock_cmd_class.side_effect = ValueError("Generic error")

            with pytest.raises(click.ClickException, match="Add failed: Generic error"):
                unwrapped_func = get_unwrapped_function(add_command.callback)
                unwrapped_func(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=("test.md",),
                    force=False,
                    dry_run=False,
                )
