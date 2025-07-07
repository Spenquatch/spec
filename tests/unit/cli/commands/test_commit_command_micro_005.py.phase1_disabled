"""Unit tests for CLI commit command with comprehensive coverage.

This module tests the complete commit command functionality including
repository operations, staging, previews, and error handling.
"""

import unittest.mock
from typing import Any
from unittest.mock import Mock, patch

from spec_cli.cli.commands.commit import (
    _auto_stage_changes,
    _show_commit_preview,
    _show_commit_result,
    commit_command,
)
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    create_cli_output_capture,
)


class TestCommitCommandMicro005:
    """Unit tests for commit_command function - Micro-Agent Implementation."""

    def setup_method(self) -> None:
        """Setup using CLI test helpers and mock dependencies."""
        self.cli_runner = create_cli_command_runner()
        self.output_capture = create_cli_output_capture()

        self.mock_repo = Mock()
        self.mock_repo.get_git_status.return_value = {
            "staged": ["file1.md", "file2.md"],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }
        self.mock_repo.commit.return_value = "abc123456"
        self.mock_repo.amend_commit.return_value = "def789012"

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    @patch("spec_cli.cli.commands.commit._show_commit_result")
    @patch("spec_cli.cli.commands.commit.get_user_confirmation")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_commit_command_with_staged_files_succeeds(
        self,
        mock_debug_logger: Any,
        mock_confirmation: Any,
        mock_show_result: Any,
        mock_show_preview: Any,
        mock_show_message: Any,
        mock_get_repo: Any,
    ) -> None:
        """Test commit command with staged files succeeds and creates commit."""
        # Setup mocks
        mock_get_repo.return_value = self.mock_repo
        mock_confirmation.return_value = True

        # Execute commit command via CLI runner
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command succeeded
        result.assert_success()

        # Verify repository operations
        mock_get_repo.assert_called_once()
        self.mock_repo.get_git_status.assert_called_once()
        self.mock_repo.commit.assert_called_once_with("Test commit")

        # Verify UI interactions
        mock_show_preview.assert_called_once_with(
            ["file1.md", "file2.md"], "Test commit", False
        )
        mock_confirmation.assert_called_once_with("Commit 2 files?", default=True)
        mock_show_message.assert_called_with("Created commit: abc12345", "success")
        mock_show_result.assert_called_once_with(
            self.mock_repo, "abc123456", ["file1.md", "file2.md"]
        )

        # Verify logging
        mock_debug_logger.log.assert_called_with(
            "INFO",
            "Commit command completed",
            commit_hash="abc123456",
            files=2,
            amend=False,
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._auto_stage_changes")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    @patch("spec_cli.cli.commands.commit._show_commit_result")
    @patch("spec_cli.cli.commands.commit.get_user_confirmation")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_commit_command_with_all_flag_auto_stages_files(
        self,
        mock_debug_logger: Any,
        mock_confirmation: Any,
        mock_show_result: Any,
        mock_show_preview: Any,
        mock_auto_stage: Any,
        mock_show_message: Any,
        mock_get_repo: Any,
    ) -> None:
        """Test commit command with --all flag auto-stages modified files."""
        # Setup initial status without staged files
        initial_status = {
            "staged": [],
            "modified": ["file1.md", "file2.md"],
            "untracked": ["file3.md"],
            "deleted": [],
        }
        # Status after auto-staging
        staged_status = {
            "staged": ["file1.md", "file2.md", "file3.md"],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }

        self.mock_repo.get_git_status.side_effect = [initial_status, staged_status]
        mock_get_repo.return_value = self.mock_repo
        mock_confirmation.return_value = True

        # Execute commit command with --all via CLI runner
        result = self.cli_runner.run_command(
            commit_command, ["-m", "Test commit with --all", "--all"]
        )

        # Verify command succeeded
        result.assert_success()

        # Verify auto-staging was called
        mock_auto_stage.assert_called_once_with(self.mock_repo, initial_status)

        # Verify git status was called twice (before and after staging)
        assert self.mock_repo.get_git_status.call_count == 2

        # Verify commit was made with staged files
        self.mock_repo.commit.assert_called_once_with("Test commit with --all")
        mock_show_preview.assert_called_once_with(
            ["file1.md", "file2.md", "file3.md"], "Test commit with --all", False
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    def test_commit_command_with_no_staged_files_shows_warning(
        self, mock_show_message: Any, mock_get_repo: Any
    ) -> None:
        """Test commit command with no staged files shows appropriate warning."""
        # Setup status with no staged files but has modified files
        self.mock_repo.get_git_status.return_value = {
            "staged": [],
            "modified": ["file1.md"],
            "untracked": ["file2.md"],
            "deleted": [],
        }
        mock_get_repo.return_value = self.mock_repo

        # Execute commit command via CLI runner
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command succeeded but no commit was made
        result.assert_success()

        # Verify no commit was made
        self.mock_repo.commit.assert_not_called()

        # Verify warning message was shown
        mock_show_message.assert_called_once_with(
            "No changes staged for commit. Use 'spec add' to stage changes "
            "or use --all to stage all modified files.",
            "warning",
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    def test_commit_command_with_clean_working_directory_shows_info(
        self, mock_show_message: Any, mock_get_repo: Any
    ) -> None:
        """Test commit command with clean working directory shows info message."""
        # Setup status with no changes at all
        self.mock_repo.get_git_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }
        mock_get_repo.return_value = self.mock_repo

        # Execute commit command via CLI runner
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command succeeded but no commit was made
        result.assert_success()

        # Verify no commit was made
        self.mock_repo.commit.assert_not_called()

        # Verify info message was shown
        mock_show_message.assert_called_once_with(
            "No changes to commit. Working directory clean.", "info"
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    def test_commit_command_with_dry_run_shows_preview_without_committing(
        self, mock_show_preview: Any, mock_show_message: Any, mock_get_repo: Any
    ) -> None:
        """Test commit command with --dry-run shows preview without committing."""
        mock_get_repo.return_value = self.mock_repo

        # Execute commit command with dry run via CLI runner
        result = self.cli_runner.run_command(
            commit_command, ["-m", "Test dry run commit", "--dry-run"]
        )

        # Verify command succeeded but no commit was made
        result.assert_success()

        # Verify preview was shown
        mock_show_preview.assert_called_once_with(
            ["file1.md", "file2.md"], "Test dry run commit", False
        )

        # Verify dry run message was shown
        mock_show_message.assert_called_with(
            "This is a dry run. No commit would be created.", "info"
        )

        # Verify no commit was made
        self.mock_repo.commit.assert_not_called()

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    @patch("spec_cli.cli.commands.commit._show_commit_result")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_commit_command_with_amend_flag_amends_last_commit(
        self,
        mock_debug_logger: Any,
        mock_show_result: Any,
        mock_show_preview: Any,
        mock_show_message: Any,
        mock_get_repo: Any,
    ) -> None:
        """Test commit command with --amend flag amends the last commit."""
        mock_get_repo.return_value = self.mock_repo

        # Execute commit command with amend via CLI runner
        result = self.cli_runner.run_command(
            commit_command, ["-m", "Amended commit message", "--amend"]
        )

        # Verify command succeeded
        result.assert_success()

        # Verify amend was called instead of regular commit
        self.mock_repo.amend_commit.assert_called_once_with("Amended commit message")
        self.mock_repo.commit.assert_not_called()

        # Verify amend preview was shown
        mock_show_preview.assert_called_once_with(
            ["file1.md", "file2.md"], "Amended commit message", True
        )

        # Verify success message
        mock_show_message.assert_called_with("Amended commit: def78901", "success")

        # Verify logging
        mock_debug_logger.log.assert_called_with(
            "INFO",
            "Commit command completed",
            commit_hash="def789012",
            files=2,
            amend=True,
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    @patch("spec_cli.cli.commands.commit.get_user_confirmation")
    def test_commit_command_with_user_cancellation_aborts_commit(
        self,
        mock_confirmation: Any,
        mock_show_preview: Any,
        mock_show_message: Any,
        mock_get_repo: Any,
    ) -> None:
        """Test commit command with user cancellation aborts the commit."""
        mock_get_repo.return_value = self.mock_repo
        mock_confirmation.return_value = False

        # Execute commit command via CLI runner
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command succeeded but no commit was made
        result.assert_success()

        # Verify preview was shown
        mock_show_preview.assert_called_once()

        # Verify user was asked for confirmation
        mock_confirmation.assert_called_once_with("Commit 2 files?", default=True)

        # Verify cancellation message
        mock_show_message.assert_called_with("Commit cancelled", "info")

        # Verify no commit was made
        self.mock_repo.commit.assert_not_called()

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_commit_command_with_repository_error_raises_click_exception(
        self, mock_debug_logger: Any, mock_get_repo: Any
    ) -> None:
        """Test commit command with repository error raises ClickException."""
        # Setup repository to raise an error
        mock_get_repo.side_effect = Exception("Repository error")

        # Execute commit command via CLI runner and expect failure
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command failed
        result.assert_failure()
        result.assert_output_contains("Commit failed: Repository error")

        # Verify error was logged
        mock_debug_logger.log.assert_called_with(
            "ERROR", "Commit command failed", error="Repository error"
        )

    @patch("spec_cli.cli.commands.commit.get_spec_repository")
    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit._show_commit_preview")
    @patch("spec_cli.cli.commands.commit._show_commit_result")
    @patch("spec_cli.cli.commands.commit.get_user_confirmation")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_commit_command_with_commit_error_raises_click_exception(
        self,
        mock_debug_logger: Any,
        mock_confirmation: Any,
        mock_show_result: Any,
        mock_show_preview: Any,
        mock_show_message: Any,
        mock_get_repo: Any,
    ) -> None:
        """Test commit command with commit error raises ClickException."""
        mock_get_repo.return_value = self.mock_repo
        mock_confirmation.return_value = True
        self.mock_repo.commit.side_effect = Exception("Commit failed")

        # Execute commit command via CLI runner and expect failure
        result = self.cli_runner.run_command(commit_command, ["-m", "Test commit"])

        # Verify command failed
        result.assert_failure()
        result.assert_output_contains("Commit failed: Commit failed")

        # Verify error was logged
        mock_debug_logger.log.assert_called_with(
            "ERROR", "Commit command failed", error="Commit failed"
        )


class TestAutoStageChangesMicro005:
    """Unit tests for _auto_stage_changes helper function."""

    def setup_method(self) -> None:
        """Setup using mock repository."""
        self.mock_repo = Mock()

    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_auto_stage_changes_with_modified_files_stages_successfully(
        self, mock_debug_logger: Any, mock_show_message: Any
    ) -> None:
        """Test _auto_stage_changes with modified files stages them successfully."""
        status: dict[str, list[str]] = {
            "modified": ["file1.md", "file2.md"],
            "deleted": [],
            "staged": [],
            "untracked": [],
        }

        # Execute auto-staging
        _auto_stage_changes(self.mock_repo, status)

        # Verify files were staged
        expected_calls = [
            unittest.mock.call(["file1.md"]),
            unittest.mock.call(["file2.md"]),
        ]
        self.mock_repo.add_files.assert_has_calls(expected_calls)

        # Verify success message
        mock_show_message.assert_called_once_with("Auto-staged 2 files", "info")

    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_auto_stage_changes_with_deleted_files_handles_placeholder(
        self, mock_debug_logger: Any, mock_show_message: Any
    ) -> None:
        """Test _auto_stage_changes with deleted files handles placeholder logic."""
        status: dict[str, list[str]] = {
            "modified": [],
            "deleted": ["deleted_file.md"],
            "staged": [],
            "untracked": [],
        }

        # Execute auto-staging
        _auto_stage_changes(self.mock_repo, status)

        # Note: Currently deleted files are not handled (placeholder implementation)
        # So we expect only the "Auto-staged X files" message for deleted count
        mock_show_message.assert_called_once_with("Auto-staged 1 files", "info")

    @patch("spec_cli.cli.commands.commit.show_message")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_auto_stage_changes_with_staging_error_logs_warning(
        self, mock_debug_logger: Any, mock_show_message: Any
    ) -> None:
        """Test _auto_stage_changes with staging error logs warning and continues."""
        status: dict[str, list[str]] = {
            "modified": ["file1.md", "file2.md"],
            "deleted": [],
            "staged": [],
            "untracked": [],
        }

        # Setup repository to fail on first file but succeed on second
        self.mock_repo.add_files.side_effect = [
            Exception("Permission denied"),
            None,
        ]

        # Execute auto-staging
        _auto_stage_changes(self.mock_repo, status)

        # Verify warning was logged for failed file
        mock_debug_logger.log.assert_called_with(
            "WARNING",
            "Failed to stage file",
            file="file1.md",
            error="Permission denied",
        )

        # Verify success message for staged files
        mock_show_message.assert_called_once_with("Auto-staged 2 files", "info")

    @patch("spec_cli.cli.commands.commit.show_message")
    def test_auto_stage_changes_with_no_files_does_not_show_message(
        self, mock_show_message: Any
    ) -> None:
        """Test _auto_stage_changes with no files does not show staged message."""
        status: dict[str, list[str]] = {
            "modified": [],
            "deleted": [],
            "staged": [],
            "untracked": [],
        }

        # Execute auto-staging
        _auto_stage_changes(self.mock_repo, status)

        # Verify no staging operations occurred
        self.mock_repo.add_files.assert_not_called()

        # Verify no message was shown
        mock_show_message.assert_not_called()


class TestShowCommitPreviewMicro005:
    """Unit tests for _show_commit_preview helper function."""

    @patch("spec_cli.cli.commands.commit.get_console")
    def test_show_commit_preview_with_new_commit_displays_correctly(
        self, mock_get_console: Any
    ) -> None:
        """Test _show_commit_preview with new commit displays correct information."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        staged_files = ["file1.md", "file2.md", "file3.md"]

        # Execute preview
        _show_commit_preview(staged_files, "Test commit message", False)

        # Verify console output calls
        expected_calls = [
            unittest.mock.call("\n[bold cyan]New commit Preview:[/bold cyan]"),
            unittest.mock.call("Message: [yellow]Test commit message[/yellow]"),
            unittest.mock.call("Files to commit: [yellow]3[/yellow]\n"),
            unittest.mock.call("[bold cyan]Staged files:[/bold cyan]"),
            unittest.mock.call("  [green]M[/green] [path]file1.md[/path]"),
            unittest.mock.call("  [green]M[/green] [path]file2.md[/path]"),
            unittest.mock.call("  [green]M[/green] [path]file3.md[/path]"),
            unittest.mock.call(),
        ]
        mock_console.print.assert_has_calls(expected_calls)

    @patch("spec_cli.cli.commands.commit.get_console")
    def test_show_commit_preview_with_amend_commit_displays_correctly(
        self, mock_get_console: Any
    ) -> None:
        """Test _show_commit_preview with amend commit displays correct information."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        staged_files = ["file1.md"]

        # Execute preview with amend=True
        _show_commit_preview(staged_files, "Amended message", True)

        # Verify amend-specific output
        mock_console.print.assert_any_call(
            "\n[bold cyan]Amend commit Preview:[/bold cyan]"
        )
        mock_console.print.assert_any_call("Message: [yellow]Amended message[/yellow]")

    @patch("spec_cli.cli.commands.commit.get_console")
    def test_show_commit_preview_with_many_files_truncates_list(
        self, mock_get_console: Any
    ) -> None:
        """Test _show_commit_preview with many files truncates the file list."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        # Create list with 20 files (more than 15 threshold)
        staged_files = [f"file{i}.md" for i in range(1, 21)]

        # Execute preview
        _show_commit_preview(staged_files, "Many files commit", False)

        # Verify truncation message is shown
        mock_console.print.assert_any_call("  [dim]... and 10 more files[/dim]")

        # Verify only first 10 files are shown individually
        for i in range(1, 11):
            mock_console.print.assert_any_call(
                f"  [green]M[/green] [path]file{i}.md[/path]"
            )

    @patch("spec_cli.cli.commands.commit.get_console")
    def test_show_commit_preview_with_empty_file_list_shows_zero_files(
        self, mock_get_console: Any
    ) -> None:
        """Test _show_commit_preview with empty file list shows zero files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        # Execute preview with empty file list
        _show_commit_preview([], "Empty commit", False)

        # Verify zero files message
        mock_console.print.assert_any_call("Files to commit: [yellow]0[/yellow]\n")


class TestShowCommitResultMicro005:
    """Unit tests for _show_commit_result helper function."""

    def setup_method(self) -> None:
        """Setup using mock repository and console."""
        self.mock_repo = Mock()

    @patch("spec_cli.cli.commands.commit.get_console")
    @patch("spec_cli.cli.commands.commit.StatusTable")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_show_commit_result_displays_commit_details_table(
        self,
        mock_debug_logger: Any,
        mock_status_table_class: Any,
        mock_get_console: Any,
    ) -> None:
        """Test _show_commit_result displays commit details in table format."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_status_table_class.return_value = mock_table

        staged_files = ["file1.md", "file2.md"]

        # Execute result display
        _show_commit_result(self.mock_repo, "abc123456", staged_files)

        # Verify table creation and content
        mock_status_table_class.assert_called_once_with("Commit Details")

        expected_table_calls = [
            unittest.mock.call("Hash", "abc12345", status="success"),
            unittest.mock.call("Files changed", "2", status="info"),
            unittest.mock.call("Author", "Unknown", status="info"),
            unittest.mock.call("Date", "Unknown", status="info"),
        ]
        mock_table.add_status_item.assert_has_calls(expected_table_calls)
        mock_table.print.assert_called_once()

        # Verify next steps information
        mock_console.print.assert_any_call("\n[bold cyan]Next steps:[/bold cyan]")
        mock_console.print.assert_any_call(
            "  Use [yellow]spec log[/yellow] to view commit history"
        )
        mock_console.print.assert_any_call(
            "  Use [yellow]spec diff[/yellow] to see working directory changes"
        )

    @patch("spec_cli.cli.commands.commit.get_console")
    @patch("spec_cli.cli.commands.commit.StatusTable")
    @patch("spec_cli.cli.commands.commit.debug_logger")
    def test_show_commit_result_with_table_error_continues_gracefully(
        self,
        mock_debug_logger: Any,
        mock_status_table_class: Any,
        mock_get_console: Any,
    ) -> None:
        """Test _show_commit_result with table error continues gracefully."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        # Setup table to raise an error
        mock_status_table_class.side_effect = Exception("Table creation failed")

        staged_files = ["file1.md"]

        # Execute result display
        _show_commit_result(self.mock_repo, "abc123456", staged_files)

        # Verify error was logged
        mock_debug_logger.log.assert_called_with(
            "WARNING", "Failed to get commit details", error="Table creation failed"
        )

        # Verify next steps are still shown
        mock_console.print.assert_any_call("\n[bold cyan]Next steps:[/bold cyan]")

    @patch("spec_cli.cli.commands.commit.get_console")
    @patch("spec_cli.cli.commands.commit.StatusTable")
    def test_show_commit_result_with_single_file_shows_correct_count(
        self, mock_status_table_class: Any, mock_get_console: Any
    ) -> None:
        """Test _show_commit_result with single file shows correct file count."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_status_table_class.return_value = mock_table

        staged_files = ["single_file.md"]

        # Execute result display
        _show_commit_result(self.mock_repo, "def789012", staged_files)

        # Verify correct file count in table
        mock_table.add_status_item.assert_any_call("Files changed", "1", status="info")

    @patch("spec_cli.cli.commands.commit.get_console")
    @patch("spec_cli.cli.commands.commit.StatusTable")
    def test_show_commit_result_truncates_long_commit_hash(
        self, mock_status_table_class: Any, mock_get_console: Any
    ) -> None:
        """Test _show_commit_result truncates long commit hash to 8 characters."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_status_table_class.return_value = mock_table

        staged_files = ["file1.md"]
        long_hash = "abc123456789012345678901234567890"

        # Execute result display
        _show_commit_result(self.mock_repo, long_hash, staged_files)

        # Verify hash is truncated to 8 characters
        mock_table.add_status_item.assert_any_call("Hash", "abc12345", status="success")
