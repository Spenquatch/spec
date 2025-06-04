"""Tests for help command (commands/help.py)."""

import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.help import help_command


class TestHelpCommand:
    """Test cases for help command functionality."""

    def test_help_command_main_help(self) -> None:
        """Test help command showing main help."""
        runner = CliRunner()
        result = runner.invoke(help_command, [])

        assert result.exit_code == 0
        assert "Spec CLI" in result.output
        assert "Available Commands" in result.output
        assert "init" in result.output
        assert "status" in result.output
        assert "help" in result.output

    def test_help_command_specific_command_init(self) -> None:
        """Test help command for specific init command."""
        runner = CliRunner()
        result = runner.invoke(help_command, ["init"])

        assert result.exit_code == 0
        assert "init" in result.output
        assert "Initialize spec repository" in result.output
        assert "--force" in result.output
        assert "Examples:" in result.output

    def test_help_command_specific_command_status(self) -> None:
        """Test help command for specific status command."""
        runner = CliRunner()
        result = runner.invoke(help_command, ["status"])

        assert result.exit_code == 0
        assert "status" in result.output
        assert "Show repository status" in result.output
        assert "--health" in result.output
        assert "--git" in result.output
        assert "--summary" in result.output

    def test_help_command_specific_command_help(self) -> None:
        """Test help command for help command itself."""
        runner = CliRunner()
        result = runner.invoke(help_command, ["help"])

        assert result.exit_code == 0
        assert "help" in result.output
        assert "Show help information" in result.output

    def test_help_command_unknown_command(self) -> None:
        """Test help command with unknown command."""
        runner = CliRunner()
        result = runner.invoke(help_command, ["unknown"])

        assert result.exit_code == 0
        assert "Unknown command: unknown" in result.output
        assert "Available commands:" in result.output

    def test_help_command_help_display(self) -> None:
        """Test help command's own help display."""
        runner = CliRunner()
        result = runner.invoke(help_command, ["--help"])

        assert result.exit_code == 0
        assert "Show help information" in result.output


class TestHelpHelperFunctions:
    """Test cases for help command helper functions."""

    def test_display_main_help(self) -> None:
        """Test _display_main_help function."""
        from spec_cli.cli.commands.help import _display_main_help

        # Test that function runs without error
        # (Output testing is covered in the main command tests)
        try:
            _display_main_help()
        except Exception as e:
            pytest.fail(f"_display_main_help raised an exception: {e}")

    def test_display_command_help_valid_command(self) -> None:
        """Test _display_command_help with valid command."""
        from spec_cli.cli.commands.help import _display_command_help

        try:
            _display_command_help("init")
        except Exception as e:
            pytest.fail(f"_display_command_help raised an exception: {e}")

    def test_display_command_help_invalid_command(self) -> None:
        """Test _display_command_help with invalid command."""
        from spec_cli.cli.commands.help import _display_command_help

        try:
            _display_command_help("invalid")
        except Exception as e:
            pytest.fail(f"_display_command_help raised an exception: {e}")

    def test_get_command_help_data(self) -> None:
        """Test _get_command_help function."""
        from spec_cli.cli.commands.help import _get_command_help

        # Test valid commands
        init_help = _get_command_help("init")
        assert init_help is not None
        assert "description" in init_help
        assert "usage" in init_help

        status_help = _get_command_help("status")
        assert status_help is not None
        assert "description" in status_help

        help_help = _get_command_help("help")
        assert help_help is not None
        assert "description" in help_help

        # Test invalid command
        invalid_help = _get_command_help("invalid")
        assert invalid_help == {}
