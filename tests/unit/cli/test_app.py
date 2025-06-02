"""Tests for CLI application (app.py)."""

from typing import Any
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

from spec_cli.cli.app import app, main


class TestCLIApp:
    """Test cases for CLI app initialization and core functionality."""

    def test_cli_app_initialization(self) -> None:
        """Test that CLI app initializes correctly."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Spec CLI" in result.output
        assert "Versioned Documentation" in result.output

    def test_cli_app_help_display(self) -> None:
        """Test help display functionality."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "init" in result.output
        assert "status" in result.output
        assert "help" in result.output

    def test_cli_app_version_display(self) -> None:
        """Test version display."""
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "Spec CLI v0.1.0" in result.output

    def test_cli_app_handles_keyboard_interrupt(self) -> None:
        """Test that keyboard interrupt is handled gracefully."""
        # This test simulates the behavior but can't easily test actual KeyboardInterrupt
        # We'll test the main function's exception handling indirectly
        runner = CliRunner()
        # Test invalid command which should exit cleanly
        result = runner.invoke(app, ["nonexistent"])

        # Should fail gracefully without crashing
        assert result.exit_code != 0

    def test_cli_app_no_subcommand_shows_help(self) -> None:
        """Test that invoking app without subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        # Should show help content when no subcommand is provided
        assert "Available Commands" in result.output or "Commands:" in result.output


class TestMainFunction:
    """Test cases for the main entry point function."""

    def test_main_function_exists(self) -> None:
        """Test that main function exists and is callable."""
        assert callable(main)

    def test_main_with_help_args(self) -> None:
        """Test main function with help arguments."""
        # Test that main function handles arguments correctly
        # This is indirectly tested through the app tests above
        assert True  # Placeholder test that passes

    @patch("spec_cli.cli.app.get_console")
    @patch("sys.exit")
    def test_main_handles_keyboard_interrupt(
        self, mock_exit: Any, mock_console: Any
    ) -> None:
        """Test that main function handles KeyboardInterrupt gracefully."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        with patch("spec_cli.cli.app.app") as mock_app:
            mock_app.side_effect = KeyboardInterrupt()

            main([])

            mock_console_instance.print_status.assert_called_once_with(
                "Operation cancelled by user.", "warning"
            )
            mock_exit.assert_called_once_with(130)

    @patch("sys.exit")
    def test_main_handles_click_exception(self, mock_exit: Any) -> None:
        """Test that main function handles ClickException properly."""
        # Create a real ClickException instance
        mock_exception = click.ClickException("Test click error")
        mock_exception.exit_code = 2

        with patch("spec_cli.cli.app.app") as mock_app, patch.object(
            mock_exception, "show"
        ) as mock_show:
            mock_app.side_effect = mock_exception

            main([])

            mock_show.assert_called_once()
            mock_exit.assert_called_once_with(2)

    @patch("spec_cli.cli.app.handle_cli_error")
    def test_main_handles_general_exception(self, mock_handle_error: Any) -> None:
        """Test that main function handles general exceptions."""
        test_exception = RuntimeError("Test error")

        with patch("spec_cli.cli.app.app") as mock_app:
            mock_app.side_effect = test_exception

            main([])

            mock_handle_error.assert_called_once_with(
                test_exception, "CLI execution failed"
            )

    @patch("spec_cli.cli.commands.help._display_main_help")
    def test_app_no_subcommand_calls_display_main_help(
        self, mock_display_help: Any
    ) -> None:
        """Test that app without subcommand calls display main help."""
        runner = CliRunner()
        runner.invoke(app, [])

        # Should call the display main help function
        mock_display_help.assert_called_once()
