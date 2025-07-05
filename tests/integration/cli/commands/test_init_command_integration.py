"""Integration tests for init command migration with context injection."""

from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.init import init_command
from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)


class TestInitCommandIntegration:
    """Integration tests for init command migration."""

    def test_init_command_full_migration_with_context_injection(self, tmp_path):
        """Test complete init command migration from CLI entry to execution."""
        # Setup: CLI application with context injection and migrated init command
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = True
        mock_settings.root_path = tmp_path
        mock_settings.spec_dir = tmp_path / ".spec"
        mock_settings.specs_dir = tmp_path / ".specs"

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        test_context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.cli.commands.init.debug_logger") as mock_debug_logger,
        ):
            # Setup mocks for successful initialization
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo.initialize.return_value = None
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = tmp_path

            # Action: Execute init command through CLI interface with context injection
            init_command(context=test_context, debug=True, verbose=False, force=False)

            # Assert: Command executes successfully with context injection
            mock_repo.is_initialized.assert_called()
            mock_repo.initialize.assert_called_once()

            # Assert: Console interface used through context
            test_context.console.print_message.assert_called_once()
            test_context.console.print_success.assert_called_once()

            # Assert: Settings accessed through context
            assert test_context.settings.debug_enabled is True

            # Assert: Debug logging called when debug enabled
            mock_debug_logger.log.assert_called_with(
                "INFO", "Repository initialized", directory=str(tmp_path), force=False
            )

    def test_init_command_force_flag_behavior_through_context(self, tmp_path):
        """Test init command force flag behavior with context injection."""
        # Setup context with force behavior testing
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = False

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        test_context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
        ):
            # Setup repository as already initialized
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = True
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = tmp_path

            # Test without force flag - should show warning
            init_command(context=test_context, debug=False, verbose=False, force=False)

            # Verify warning displayed and no initialization
            test_context.console.print_warning.assert_called_once()
            mock_repo.initialize.assert_not_called()

            # Reset mocks for force test
            test_context.console.reset_mock()
            mock_repo.reset_mock()
            mock_repo.is_initialized.return_value = True

            # Test with force flag - should reinitialize
            init_command(context=test_context, debug=False, verbose=False, force=True)

            # Verify force initialization message and repository initialization
            test_context.console.print_message.assert_called_once()
            mock_repo.initialize.assert_called_once()

    def test_init_command_error_handling_with_context(self, tmp_path):
        """Test init command error handling preserves context patterns."""
        # Setup context for error testing
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = True

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        test_context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.cli.commands.init.debug_logger") as mock_debug_logger,
            pytest.raises(Exception) as exc_info,
        ):
            # Setup repository to fail
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo.initialize.side_effect = RuntimeError("Initialization failure")
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = tmp_path

            # Execute command that should fail
            init_command(context=test_context, debug=True, verbose=False, force=False)

        # Verify error handling through context
        assert "Unexpected error during initialization" in str(exc_info.value)

        # Verify debug logging called for error when debug enabled
        mock_debug_logger.log.assert_called_with(
            "ERROR", "Initialization failed", error="Initialization failure"
        )

    def test_init_command_context_attribute_access_patterns(self, tmp_path):
        """Test init command properly accesses context attributes."""
        # Setup context with specific attribute values
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = False
        mock_settings.root_path = tmp_path

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        test_context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.cli.commands.init.debug_logger") as mock_debug_logger,
        ):
            # Setup successful scenario
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = tmp_path

            # Execute command
            init_command(context=test_context, debug=False, verbose=False, force=False)

            # Verify context.console access pattern used
            assert test_context.console.print_message.called
            assert test_context.console.print_success.called

            # Verify context.settings access pattern for debug check
            # Debug logging should NOT be called since debug_enabled is False
            mock_debug_logger.log.assert_not_called()

    def test_init_command_signature_compatibility_with_context_injection(self):
        """Test init command signature is compatible with context injection."""
        import inspect

        # Get init command signature
        signature = inspect.signature(init_command)
        params = list(signature.parameters.keys())

        # Verify context parameter is first
        assert params[0] == "context"

        # Verify original parameters preserved
        assert "debug" in params
        assert "verbose" in params
        assert "force" in params

        # Verify parameter count (context + 3 original)
        assert len(params) == 4

        # Verify context parameter annotation
        context_param = signature.parameters["context"]
        assert (
            context_param.annotation == "SpecContext"
            or context_param.annotation == SpecContext
        )

    def test_init_command_maintains_click_compatibility_after_migration(self):
        """Test init command maintains Click compatibility after context injection."""
        # Verify Click attributes are preserved
        assert hasattr(init_command, "__click_params__")

        # Verify function name preserved
        assert init_command.__name__ == "init_command"

        # Verify docstring preserved and updated
        assert init_command.__doc__ is not None
        assert "Initialize spec repository" in init_command.__doc__
        assert "context: SpecContext" in init_command.__doc__

    def test_init_command_behavior_identical_to_pre_migration(self, tmp_path):
        """Test migrated init command behavior is identical to pre-migration."""
        # This test verifies the behavior preservation requirement
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = False

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        test_context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
        ):
            # Test scenario 1: Fresh initialization
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = tmp_path

            init_command(test_context, debug=False, verbose=False, force=False)

            # Verify expected behavior sequence
            mock_repo.is_initialized.assert_called()
            mock_repo.initialize.assert_called_once()
            test_context.console.print_message.assert_called_once()
            test_context.console.print_success.assert_called_once()

            # Reset for next test
            test_context.console.reset_mock()
            mock_repo.reset_mock()

            # Test scenario 2: Already initialized without force
            mock_repo.is_initialized.return_value = True

            init_command(test_context, debug=False, verbose=False, force=False)

            # Verify warning behavior (pre-migration equivalent)
            test_context.console.print_warning.assert_called_once()
            mock_repo.initialize.assert_not_called()
