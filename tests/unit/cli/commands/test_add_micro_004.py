"""Unit tests for CLI add command implementation.

This module tests the add command functionality including file validation,
directory expansion, Git integration, and error handling for add.py and add_command.py.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.cli.commands.add import add_command
from spec_cli.cli.commands.add_command import AddCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    create_cli_output_capture,
)


class TestAddCommandCLIMicro004:
    """Unit tests for CLI add command - Micro-Agent Implementation."""

    def setup_method(self) -> None:
        """Setup using discovered CLI test helpers."""
        self.cli_runner = create_cli_command_runner()
        self.output_capture = create_cli_output_capture()

    def test_add_command_with_valid_files_succeeds(self) -> None:
        """Test add_command with valid file paths succeeds."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            with patch("spec_cli.cli.commands.add.AddCommand") as mock_command_class:
                mock_validate.return_value = [Path(".specs/test.md")]
                mock_command = Mock()
                mock_command.safe_execute.return_value = {
                    "success": True,
                    "message": "Files added successfully",
                }
                mock_command_class.return_value = mock_command

                result = self.cli_runner.run_command(
                    add_command, [".specs/test.md", "--debug"]
                )

                result.assert_success()
                mock_validate.assert_called_once_with([".specs/test.md"])
                mock_command.safe_execute.assert_called_once_with(
                    files=[Path(".specs/test.md")], force=False, dry_run=False
                )

    def test_add_command_with_force_flag_passes_force_option(self):
        """Test add_command with --force flag passes force option to command."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            with patch("spec_cli.cli.commands.add.AddCommand") as mock_command_class:
                mock_validate.return_value = [Path(".specs/test.md")]
                mock_command = Mock()
                mock_command.safe_execute.return_value = {
                    "success": True,
                    "message": "Files added successfully",
                }
                mock_command_class.return_value = mock_command

                result = self.cli_runner.run_command(
                    add_command, [".specs/test.md", "--force"]
                )

                result.assert_success()
                mock_command.safe_execute.assert_called_once_with(
                    files=[Path(".specs/test.md")], force=True, dry_run=False
                )

    def test_add_command_with_dry_run_flag_passes_dry_run_option(self):
        """Test add_command with --dry-run flag passes dry_run option to command."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            with patch("spec_cli.cli.commands.add.AddCommand") as mock_command_class:
                mock_validate.return_value = [Path(".specs/test.md")]
                mock_command = Mock()
                mock_command.safe_execute.return_value = {
                    "success": True,
                    "message": "Files added successfully",
                }
                mock_command_class.return_value = mock_command

                result = self.cli_runner.run_command(
                    add_command, [".specs/test.md", "--dry-run"]
                )

                result.assert_success()
                mock_command.safe_execute.assert_called_once_with(
                    files=[Path(".specs/test.md")], force=False, dry_run=True
                )

    def test_add_command_with_no_files_raises_missing_argument_error(self):
        """Test add_command with no file paths raises Click missing argument error."""
        result = self.cli_runner.run_command(add_command, [])

        result.assert_failure()
        result.assert_output_contains("Missing argument 'FILES...'")

    def test_add_command_with_invalid_paths_raises_bad_parameter(self):
        """Test add_command with invalid file paths after validation raises BadParameter."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.return_value = []

            result = self.cli_runner.run_command(add_command, ["invalid_path"])

            result.assert_failure()
            result.assert_output_contains("No valid file paths provided")

    def test_add_command_with_command_failure_raises_click_exception(self):
        """Test add_command with command execution failure raises ClickException."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            with patch("spec_cli.cli.commands.add.AddCommand") as mock_command_class:
                mock_validate.return_value = [Path(".specs/test.md")]
                mock_command = Mock()
                mock_command.safe_execute.return_value = {
                    "success": False,
                    "message": "Add operation failed",
                }
                mock_command_class.return_value = mock_command

                result = self.cli_runner.run_command(add_command, [".specs/test.md"])

                result.assert_failure()
                result.assert_output_contains("Add operation failed")

    def test_add_command_with_exception_raises_click_exception(self):
        """Test add_command with unexpected exception raises ClickException."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.side_effect = RuntimeError("Unexpected error")

            result = self.cli_runner.run_command(add_command, [".specs/test.md"])

            result.assert_failure()
            result.assert_output_contains("Add failed: Unexpected error")

    def test_add_command_preserves_click_bad_parameter_exceptions(self):
        """Test add_command preserves click.BadParameter exceptions without wrapping."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.side_effect = click.BadParameter("Invalid path format")

            result = self.cli_runner.run_command(add_command, [".specs/test.md"])

            result.assert_failure()
            result.assert_output_contains("Invalid path format")

    def test_add_command_preserves_click_exceptions(self):
        """Test add_command preserves click.ClickException without double-wrapping."""
        with patch("spec_cli.cli.commands.add.validate_file_paths") as mock_validate:
            mock_validate.side_effect = click.ClickException("Click error")

            result = self.cli_runner.run_command(add_command, [".specs/test.md"])

            result.assert_failure()
            result.assert_output_contains("Click error")


class TestAddCommandClassMicro004:
    """Unit tests for AddCommand class implementation - Micro-Agent Implementation."""

    def setup_method(self):
        """Setup using mock settings and dependencies."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.root_path = Path(".")

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_add_command_initialization_succeeds(self, mock_get_console):
        """Test AddCommand initialization succeeds with proper setup."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        assert command.settings == self.mock_settings
        assert command.console == mock_console

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.base_command.get_settings")
    def test_add_command_initialization_with_none_settings(
        self, mock_get_settings, mock_get_console
    ):
        """Test AddCommand initialization with None settings uses default."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_get_settings.return_value = self.mock_settings

        command = AddCommand(None)

        assert command.settings == self.mock_settings
        mock_get_settings.assert_called_once()

    def test_validate_arguments_with_valid_files_succeeds(self):
        """Test validate_arguments with valid file paths succeeds."""
        with patch("spec_cli.cli.commands.add_command.get_console"):
            command = AddCommand(self.mock_settings)

            # Should not raise exception
            command.validate_arguments(
                files=[Path(".specs/test.md"), ".specs/other.md"]
            )

    def test_validate_arguments_with_no_files_raises_spec_error(self):
        """Test validate_arguments with no files raises SpecError."""
        with patch("spec_cli.cli.commands.add_command.get_console"):
            command = AddCommand(self.mock_settings)

            with pytest.raises(SpecError, match="No file paths provided"):
                command.validate_arguments(files=[])

    def test_validate_arguments_with_invalid_file_type_raises_spec_error(self):
        """Test validate_arguments with invalid file type raises SpecError."""
        with patch("spec_cli.cli.commands.add_command.get_console"):
            command = AddCommand(self.mock_settings)

            with pytest.raises(SpecError, match="Invalid file path type"):
                command.validate_arguments(files=[123])

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_expand_spec_files_with_single_file_returns_file(self, mock_get_console):
        """Test _expand_spec_files with single file returns that file."""
        command = AddCommand(self.mock_settings)

        mock_file = Mock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.is_dir.return_value = False

        result = command._expand_spec_files([mock_file])

        assert result == [mock_file]
        mock_file.is_file.assert_called_once()

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_expand_spec_files_with_directory_returns_all_files(self, mock_get_console):
        """Test _expand_spec_files with directory returns all files in directory."""
        command = AddCommand(self.mock_settings)

        mock_dir = Mock(spec=Path)
        mock_dir.is_file.return_value = False
        mock_dir.is_dir.return_value = True

        mock_file1 = Mock(spec=Path)
        mock_file1.is_file.return_value = True
        mock_file2 = Mock(spec=Path)
        mock_file2.is_file.return_value = True
        mock_subdir = Mock(spec=Path)
        mock_subdir.is_file.return_value = False

        mock_dir.rglob.return_value = [mock_file1, mock_file2, mock_subdir]

        result = command._expand_spec_files([mock_dir])

        assert result == [mock_file1, mock_file2]
        mock_dir.rglob.assert_called_once_with("*")

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.safe_relative_to")
    def test_filter_spec_files_with_valid_spec_files_returns_filtered_list(
        self, mock_safe_relative_to, mock_get_console
    ):
        """Test _filter_spec_files returns only files in .specs directory."""
        command = AddCommand(self.mock_settings)

        spec_file = Path(".specs/test.md")
        non_spec_file = Path("src/main.py")

        # Mock safe_relative_to to succeed for spec files, fail for others
        def mock_relative_side_effect(file_path, specs_dir, strict=False):
            if file_path == spec_file:
                return Path("test.md")
            else:
                raise ValueError("Not in specs directory")

        mock_safe_relative_to.side_effect = mock_relative_side_effect

        result = command._filter_spec_files([spec_file, non_spec_file])

        assert result == [spec_file]
        assert mock_safe_relative_to.call_count == 2

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.debug_logger")
    def test_analyze_git_status_with_successful_repo_status(
        self, mock_debug_logger, mock_get_console
    ):
        """Test _analyze_git_status with successful repository status call."""
        command = AddCommand(self.mock_settings)

        mock_repo = Mock()
        mock_repo.status.return_value = None  # Successful status call

        spec_files = [Path(".specs/test.md"), Path(".specs/other.md")]

        result = command._analyze_git_status(spec_files, mock_repo)

        expected = {
            "untracked": [".specs/test.md", ".specs/other.md"],
            "modified": [],
            "staged": [],
            "up_to_date": [],
        }

        assert result == expected
        mock_repo.status.assert_called_once()

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.debug_logger")
    def test_analyze_git_status_with_failed_repo_status_logs_warning(
        self, mock_debug_logger, mock_get_console
    ):
        """Test _analyze_git_status with failed repository status logs warning."""
        command = AddCommand(self.mock_settings)

        mock_repo = Mock()
        mock_repo.status.side_effect = RuntimeError("Git error")

        spec_files = [Path(".specs/test.md")]

        result = command._analyze_git_status(spec_files, mock_repo)

        expected = {
            "untracked": [".specs/test.md"],
            "modified": [],
            "staged": [],
            "up_to_date": [],
        }

        assert result == expected
        mock_debug_logger.log.assert_called_with(
            "WARNING", "Failed to get Git status", error="Git error"
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_show_add_preview_displays_file_counts(self, mock_get_console):
        """Test _show_add_preview displays correct file counts for each status."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        git_status = {
            "untracked": ["file1.md", "file2.md"],
            "modified": ["file3.md"],
            "staged": ["file4.md"],
            "up_to_date": ["file5.md"],
        }

        command._show_add_preview(git_status, is_dry_run=False)

        # Verify console print calls include status counts
        print_calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("New files: [green]2[/green]" in call for call in print_calls)
        assert any("Modified files: [yellow]1[/yellow]" in call for call in print_calls)
        assert any("Already staged: [blue]1[/blue]" in call for call in print_calls)
        assert any("Up to date: [dim]1[/dim]" in call for call in print_calls)

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_show_add_preview_with_dry_run_shows_dry_run_title(self, mock_get_console):
        """Test _show_add_preview with dry_run=True shows dry run title."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        git_status = {"untracked": [], "modified": [], "staged": [], "up_to_date": []}

        command._show_add_preview(git_status, is_dry_run=True)

        # Verify dry run title is shown
        print_calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("Add Preview (Dry Run)" in call for call in print_calls)

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_display_add_results_with_successful_results(
        self, mock_show_message, mock_get_console
    ):
        """Test _display_add_results with successful add operation results."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        result = {
            "success": True,
            "added": ["file1.md", "file2.md"],
            "skipped": [{"file": "file3.md", "reason": "Already tracked"}],
            "failed": [],
        }

        command._display_add_results(result)

        mock_show_message.assert_called_with(
            "Successfully added 2 files to spec repository", "success"
        )

        # Verify console displays statistics
        print_calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("Added files: [green]2[/green]" in call for call in print_calls)
        assert any("Skipped files: [yellow]1[/yellow]" in call for call in print_calls)
        assert any("Failed files: [red]0[/red]" in call for call in print_calls)

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_display_add_results_with_failures_shows_warning(
        self, mock_show_message, mock_get_console
    ):
        """Test _display_add_results with failed operations shows warning."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        result = {
            "success": False,
            "added": [],
            "skipped": [],
            "failed": [{"file": "file1.md", "error": "Permission denied"}],
        }

        command._display_add_results(result)

        mock_show_message.assert_called_with("Add completed with 1 failures", "warning")
