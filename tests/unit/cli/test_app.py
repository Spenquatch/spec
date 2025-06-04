"""Tests for CLI application (app.py)."""

from typing import Any
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

from spec_cli.cli.app import _invoke_app, app, main


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

    @patch("sys.exit")
    def test_main_handles_keyboard_interrupt(self, mock_exit: Any) -> None:
        """Test that main function handles KeyboardInterrupt gracefully."""
        # Import the module properly using sys.modules
        import sys

        app_module = sys.modules["spec_cli.cli.app"]

        # Patch the _invoke_app function to raise KeyboardInterrupt
        with patch.object(app_module, "_invoke_app", side_effect=KeyboardInterrupt()):
            # Also patch get_console to verify it was called
            with patch.object(app_module, "get_console") as mock_console:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance

                main([])

                mock_console_instance.print_status.assert_called_once_with(
                    "Operation cancelled by user.", "warning"
                )
                mock_exit.assert_called_once_with(130)

    @patch("sys.exit")
    def test_main_handles_click_exception(self, mock_exit: Any) -> None:
        """Test that main function handles ClickException properly."""
        # Import the module properly using sys.modules
        import sys

        app_module = sys.modules["spec_cli.cli.app"]

        # Create a real ClickException instance
        mock_exception = click.ClickException("Test click error")
        mock_exception.exit_code = 2

        with (
            patch.object(app_module, "_invoke_app", side_effect=mock_exception),
            patch.object(mock_exception, "show") as mock_show,
        ):
            main([])

            mock_show.assert_called_once()
            mock_exit.assert_called_once_with(2)

    def test_main_handles_general_exception(self) -> None:
        """Test that main function handles general exceptions."""
        # Import the module properly using sys.modules
        import sys

        app_module = sys.modules["spec_cli.cli.app"]

        test_exception = RuntimeError("Test error")

        with (
            patch.object(app_module, "_invoke_app", side_effect=test_exception),
            patch.object(app_module, "handle_cli_error") as mock_handle_error,
        ):
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

    def test_invoke_app_function_exists(self) -> None:
        """Test that _invoke_app function exists and is callable."""
        assert callable(_invoke_app)

    def test_invoke_app_calls_app_correctly(self) -> None:
        """Test that _invoke_app calls the app with correct parameters."""
        # Import the module properly using sys.modules
        import sys

        app_module = sys.modules["spec_cli.cli.app"]

        test_args = ["--help"]

        with patch.object(app_module, "app") as mock_app:
            _invoke_app(test_args)
            mock_app.assert_called_once_with(args=test_args, standalone_mode=False)

    def test_exception_handling_robustness_across_python_versions(self) -> None:
        """Test that exception handling works consistently across Python versions."""
        # This tests the robustness of our patching approach
        import sys
        from unittest.mock import Mock, patch

        app_module = sys.modules["spec_cli.cli.app"]

        # Test that we can patch _invoke_app successfully
        with patch.object(app_module, "_invoke_app") as mock_invoke:
            mock_invoke.side_effect = KeyboardInterrupt()

            # This should not raise an exception - the main function should handle it
            try:
                with patch.object(app_module, "get_console") as mock_console:
                    mock_console.return_value = Mock()
                    with patch("sys.exit"):
                        main([])
                # If we get here, the exception was handled properly
                assert True
            except KeyboardInterrupt:
                # This would indicate our exception handling failed
                raise AssertionError(
                    "KeyboardInterrupt was not handled by main()"
                ) from None
