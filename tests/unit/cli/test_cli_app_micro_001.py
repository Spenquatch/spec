"""Unit tests for CLI app command routing and main application flow.

This module tests the main CLI application functionality including command routing,
version handling, help display, and error handling in app.py.
"""

from unittest.mock import Mock, patch

import click

from spec_cli.cli.app import _invoke_app, app, main
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    create_user_input_mocker,
)


class TestCLIAppMicro001:
    """Unit tests for CLI app main application - Micro-Agent Implementation."""

    def setup_method(self):
        """Setup using discovered CLI test helpers."""
        self.cli_runner = create_cli_command_runner()
        self.input_mocker = create_user_input_mocker()

    def test_app_with_version_flag_shows_version(self):
        """Test app command with --version flag displays version information."""
        result = self.cli_runner.run_command(app, ["--version"])

        result.assert_success()
        result.assert_output_contains("Spec CLI v0.1.0")

    def test_app_with_help_flag_shows_help(self):
        """Test app command with --help flag displays help information."""
        result = self.cli_runner.run_command(app, ["--help"])

        result.assert_success()
        result.assert_output_contains("Spec CLI - Versioned Documentation")
        result.assert_output_contains("Usage:")

    def test_app_without_subcommand_shows_main_help(self):
        """Test app command without subcommand displays main help."""
        with patch("spec_cli.cli.commands.help._display_main_help") as mock_help:
            # Mock the CLI context setup to avoid failures in isolated filesystem
            with patch("spec_cli.cli.app.initialize_cli_context") as mock_init:
                with patch("spec_cli.cli.app.setup_click_context_storage") as mock_setup:
                    # Mock successful context creation
                    from spec_cli.core.context import SpecContext
                    mock_context = Mock(spec=SpecContext)
                    mock_init.return_value = mock_context

                    # Setup the mock to store context in Click context meta
                    def setup_storage(ctx, spec_context):
                        ctx.meta["spec_context"] = spec_context
                    mock_setup.side_effect = setup_storage

                    result = self.cli_runner.run_command(app, [])

                    result.assert_success()
                    mock_help.assert_called_once_with(mock_context)

    def test_app_with_valid_subcommand_routes_correctly(self):
        """Test app command with valid subcommand routes correctly."""
        # Test that the app recognizes valid subcommands
        # We'll use init as it's a simple command for routing test
        result = self.cli_runner.run_command(app, ["init", "--help"])

        result.assert_success()
        # Should show init command help, not main help
        result.assert_output_contains("init")

    def test_app_with_invalid_subcommand_fails(self):
        """Test app command with invalid subcommand fails appropriately."""
        result = self.cli_runner.run_command(app, ["invalid-command"])

        result.assert_failure()
        result.assert_output_contains("No such command")

    def test_invoke_app_with_args(self):
        """Test _invoke_app function with specific arguments."""
        # Test internal invoke function
        with patch.object(app, "main") as mock_main:
            _invoke_app(["--version"])
            mock_main.assert_called_once_with(args=["--version"], standalone_mode=False)

    def test_invoke_app_without_args(self):
        """Test _invoke_app function without arguments."""
        with patch.object(app, "main") as mock_main:
            _invoke_app()
            mock_main.assert_called_once_with(args=None, standalone_mode=False)

    def test_main_function_handles_keyboard_interrupt(self):
        """Test main function properly handles KeyboardInterrupt."""
        with patch("spec_cli.cli.app._invoke_app") as mock_invoke:
            mock_invoke.side_effect = KeyboardInterrupt()

            with patch("spec_cli.cli.app.get_console") as mock_console:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance

                with patch("sys.exit") as mock_exit:
                    main()

                    mock_console_instance.print_status.assert_called_once_with(
                        "Operation cancelled by user.", "warning"
                    )
                    mock_exit.assert_called_once_with(130)

    def test_main_function_handles_click_exception(self):
        """Test main function properly handles Click exceptions."""
        mock_exception = click.ClickException("Test error")
        mock_exception.exit_code = 2

        with patch("spec_cli.cli.app._invoke_app") as mock_invoke:
            mock_invoke.side_effect = mock_exception

            with patch("sys.exit") as mock_exit:
                with patch.object(mock_exception, "show") as mock_show:
                    main()

                    mock_show.assert_called_once()
                    mock_exit.assert_called_once_with(2)

    def test_main_function_handles_generic_exception(self):
        """Test main function properly handles generic exceptions."""
        test_exception = RuntimeError("Unexpected error")

        with patch("spec_cli.cli.app._invoke_app") as mock_invoke:
            mock_invoke.side_effect = test_exception

            with patch("spec_cli.cli.app.handle_cli_error") as mock_handle_error:
                main()

                mock_handle_error.assert_called_once_with(
                    test_exception, "CLI execution failed"
                )

    def test_main_function_successful_execution(self):
        """Test main function with successful command execution."""
        with patch("spec_cli.cli.app._invoke_app") as mock_invoke:
            mock_invoke.return_value = None  # Successful execution

            # Should not raise any exception or call exit
            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_not_called()

    def test_app_context_settings_configured_correctly(self):
        """Test that app has correct context settings configured."""
        # Verify help option names are configured
        assert app.context_settings["help_option_names"] == ["-h", "--help"]

    def test_app_group_configuration(self):
        """Test that app group is configured correctly."""
        # Verify it's a group that can be invoked without command
        assert isinstance(app, click.Group)
        assert app.invoke_without_command is True

    def test_all_commands_registered(self):
        """Test that all expected commands are registered with the app."""
        expected_commands = [
            "init",
            "status",
            "help",
            "gen",
            "regen",
            "add",
            "agent-scope",
            "diff",
            "log",
            "show",
            "commit",
        ]

        for command_name in expected_commands:
            assert command_name in app.commands, (
                f"Command '{command_name}' not registered"
            )

    def test_app_with_help_short_flag(self):
        """Test app command with -h flag displays help information."""
        result = self.cli_runner.run_command(app, ["-h"])

        result.assert_success()
        result.assert_output_contains("Spec CLI - Versioned Documentation")
        result.assert_output_contains("Usage:")

    def test_app_version_handling_edge_cases(self):
        """Test edge cases in version flag handling."""
        # Test version flag by itself (the expected behavior)
        result = self.cli_runner.run_command(app, ["--version"])

        result.assert_success()
        result.assert_output_contains("Spec CLI v0.1.0")

    def test_cli_error_handling_integration(self):
        """Test integration with CLI error handling system."""
        # Test that error handling is properly integrated
        with patch("spec_cli.cli.app.handle_cli_error") as mock_handle:
            test_error = ValueError("Test error")

            with patch("spec_cli.cli.app._invoke_app") as mock_invoke:
                mock_invoke.side_effect = test_error

                main()
                mock_handle.assert_called_once_with(test_error, "CLI execution failed")
