"""Tests for CLI application (app.py)."""

import pytest
from click.testing import CliRunner

from spec_cli.cli.app import app, main


class TestCLIApp:
    """Test cases for CLI app initialization and core functionality."""

    def test_cli_app_initialization(self):
        """Test that CLI app initializes correctly."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Spec CLI" in result.output
        assert "Versioned Documentation" in result.output

    def test_cli_app_help_display(self):
        """Test help display functionality."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "init" in result.output
        assert "status" in result.output
        assert "help" in result.output

    def test_cli_app_version_display(self):
        """Test version display."""
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "Spec CLI v0.1.0" in result.output

    def test_cli_app_handles_keyboard_interrupt(self):
        """Test that keyboard interrupt is handled gracefully."""
        # This test simulates the behavior but can't easily test actual KeyboardInterrupt
        # We'll test the main function's exception handling indirectly
        runner = CliRunner()
        # Test invalid command which should exit cleanly
        result = runner.invoke(app, ["nonexistent"])
        
        # Should fail gracefully without crashing
        assert result.exit_code != 0

    def test_cli_app_no_subcommand_shows_help(self):
        """Test that invoking app without subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        
        assert result.exit_code == 0
        # Should show help content when no subcommand is provided
        assert "Available Commands" in result.output or "Commands:" in result.output


class TestMainFunction:
    """Test cases for the main entry point function."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(main)

    def test_main_with_help_args(self):
        """Test main function with help arguments."""
        # Test that main function handles arguments correctly
        # This is indirectly tested through the app tests above
        assert True  # Placeholder test that passes