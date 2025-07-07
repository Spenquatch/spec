"""Integration tests for add command migration consistency."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.add import add_command
from spec_cli.cli.commands.init import init_command
from spec_cli.cli.commands.status import status_command
from spec_cli.core.context import SpecContext


class TestAddCommandMigrationIntegration:
    """Test add command migration integration with other migrated commands."""

    # Test constants
    TEST_FILES = ("test.md",)
    TEST_FILE_PATHS = [Path("test.md")]

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_context.settings = Mock()
        mock_context.console = Mock()
        mock_context.progress = Mock()
        return mock_context

    def test_add_command_migration_when_full_workflow_then_consistent_with_other_migrated_commands(
        self, mock_context
    ):
        """Test add command works consistently with other migrated commands in full workflow."""
        # This test verifies that the add command can be used in a workflow
        # with other migrated commands like init and status

        with (
            # Mock add command dependencies
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_add_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_add_cmd_class,
            # Mock init command dependencies
            patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class,
            # Mock status command dependencies
            patch(
                "spec_cli.cli.commands.status.StatusCommand"
            ) as mock_status_cmd_class,
        ):
            # Setup mocks for add command
            mock_add_validate.return_value = self.TEST_FILE_PATHS
            mock_add_instance = Mock()
            mock_add_instance.safe_execute.return_value = {
                "success": True,
                "message": "Files added",
            }
            mock_add_cmd_class.return_value = mock_add_instance

            # Setup mocks for init command
            mock_repo_instance = Mock()
            mock_repo_instance.is_initialized.return_value = True
            mock_repo_instance.initialize.return_value = None
            mock_repo_class.return_value = mock_repo_instance

            # Setup mocks for status command
            mock_status_instance = Mock()
            mock_status_instance.safe_execute.return_value = {
                "success": True,
                "message": "Status retrieved",
            }
            mock_status_cmd_class.return_value = mock_status_instance

            # Execute workflow: init -> add -> status
            # All commands should use the same context instance

            # Step 1: Initialize repository
            init_command.callback(mock_context, debug=False, verbose=False, force=False)

            # Step 2: Add files
            add_command.callback(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

            # Step 3: Check status
            status_command.callback(mock_context, debug=False, verbose=False)

            # Verify all commands used the same context.settings instance
            # This ensures consistency across the migration
            mock_add_cmd_class.assert_called_once_with(settings=mock_context.settings)
            mock_status_cmd_class.assert_called_once_with(
                settings=mock_context.settings
            )

    def test_add_command_when_used_with_migrated_init_then_context_consistent(
        self, mock_context
    ):
        """Test add command context consistency with migrated init command."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_add_cmd_class,
            patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_add_instance = Mock()
            mock_add_instance.safe_execute.return_value = {
                "success": True,
                "message": "OK",
            }
            mock_add_cmd_class.return_value = mock_add_instance

            mock_repo_instance = Mock()
            mock_repo_instance.is_initialized.return_value = True
            mock_repo_instance.initialize.return_value = None
            mock_repo_class.return_value = mock_repo_instance

            # Both commands should receive the same context
            init_command.callback(mock_context, debug=False, verbose=False, force=False)
            add_command.callback(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )

            # Verify both commands use the same settings from context
            mock_add_cmd_class.assert_called_once_with(settings=mock_context.settings)

    def test_add_command_when_used_with_migrated_status_then_dependency_injection_works(
        self, mock_context
    ):
        """Test add command dependency injection works with status command."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_add_cmd_class,
            patch(
                "spec_cli.cli.commands.status.StatusCommand"
            ) as mock_status_cmd_class,
        ):
            mock_validate.return_value = self.TEST_FILE_PATHS
            mock_add_instance = Mock()
            mock_add_instance.safe_execute.return_value = {
                "success": True,
                "message": "OK",
            }
            mock_add_cmd_class.return_value = mock_add_instance

            mock_status_instance = Mock()
            mock_status_instance.safe_execute.return_value = {
                "success": True,
                "message": "OK",
            }
            mock_status_cmd_class.return_value = mock_status_instance

            # Execute both commands with same context
            add_command.callback(
                mock_context,
                debug=False,
                verbose=False,
                files=self.TEST_FILES,
                force=False,
                dry_run=False,
            )
            status_command.callback(mock_context, debug=False, verbose=False)

            # Verify dependency injection worked for both
            mock_add_cmd_class.assert_called_once_with(settings=mock_context.settings)
            mock_status_cmd_class.assert_called_once_with(
                settings=mock_context.settings
            )

class TestCrossSliceContextIntegration:
    """Test context integration across different command slices."""

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_context.settings = Mock()
        mock_context.console = Mock()
        mock_context.progress = Mock()
        return mock_context

    def test_add_command_when_context_factory_provides_dependencies_then_uses_injected_instances(
        self, mock_context
    ):
        """Test add command uses dependencies from context factory properly."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = [Path("test.md")]
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = {
                "success": True,
                "message": "OK",
            }
            mock_cmd_class.return_value = mock_instance

            # Create specific settings instance to verify it's used
            specific_settings = Mock()
            mock_context.settings = specific_settings

            add_command.callback(
                mock_context,
                debug=False,
                verbose=False,
                files=("test.md",),
                force=False,
                dry_run=False,
            )

            # Verify the exact settings instance from context is passed
            mock_cmd_class.assert_called_once_with(settings=specific_settings)

    def test_add_command_when_singleton_elimination_complete_then_no_global_state_access(
        self, mock_context
    ):
        """Test that add command has no remaining singleton references."""
        with (
            patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.add.AddCommand") as mock_cmd_class,
        ):
            mock_validate.return_value = [Path("test.md")]
            mock_instance = Mock()
            mock_instance.safe_execute.return_value = {
                "success": True,
                "message": "OK",
            }
            mock_cmd_class.return_value = mock_instance

            # Monitor potential singleton access
            with (
                patch("spec_cli.config.settings.get_settings") as mock_get_settings,
                patch("spec_cli.ui.console.get_console") as mock_get_console,
                patch("spec_cli.ui.progress_manager.ProgressManager") as mock_progress,
            ):
                add_command.callback(
                    mock_context,
                    debug=False,
                    verbose=False,
                    files=("test.md",),
                    force=False,
                    dry_run=False,
                )

                # Verify no singleton access in the add command itself
                # (AddCommand class might still use singletons internally)
                mock_get_settings.assert_not_called()
                mock_get_console.assert_not_called()
                mock_progress.assert_not_called()

class TestAddCommandDecoratorCompatibility:
    """Test decorator compatibility and ordering."""

    def test_add_command_when_decorator_order_then_maintains_click_functionality(self):
        """Test that decorator order maintains Click functionality."""
        # Verify the command has all required Click attributes
        assert hasattr(add_command, "__click_params__")
        assert hasattr(add_command, "callback")

        # Verify decorator order is preserved
        # The command should have files_argument, force_option, dry_run_option decorators
        click_params = getattr(add_command, "__click_params__", [])
        assert len(click_params) > 0

        # Check for expected parameter names
        param_names = {param.name for param in click_params}
        expected_params = {"files", "force", "dry_run"}
        assert expected_params.issubset(param_names)

    def test_add_command_when_context_injection_decorator_then_preserves_metadata(self):
        """Test that context injection decorator preserves function metadata."""
        # Check that function name and docstring are preserved
        assert add_command.callback.__name__ == "add_command"
        assert "Add spec files to Git tracking" in add_command.callback.__doc__

        # Check that the context parameter is documented in docstring
        assert "context: SpecContext" in add_command.callback.__doc__
