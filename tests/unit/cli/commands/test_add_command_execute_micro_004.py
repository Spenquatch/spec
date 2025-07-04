"""Unit tests for AddCommand.execute method with comprehensive coverage.

This module tests the complete execute method functionality including workflow
integration, repository validation, file processing, and result handling.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.add_command import AddCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError


class TestAddCommandExecuteMicro004:
    """Unit tests for AddCommand.execute method - Micro-Agent Implementation."""

    def setup_method(self):
        """Setup using mock settings and dependencies."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.root_path = Path(".")
        self.mock_settings.spec_dir = Path(".spec")
        self.mock_settings.index_file = Path(".spec-index")
        self.mock_settings.debug_enabled = False

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    @patch("spec_cli.cli.commands.add_command.create_add_workflow")
    @patch("spec_cli.cli.commands.add_command.show_message")
    @patch("spec_cli.cli.commands.add_command.debug_logger")
    def test_execute_with_valid_files_succeeds(
        self,
        mock_debug_logger,
        mock_show_message,
        mock_create_workflow,
        mock_repo_class,
        mock_get_console,
    ):
        """Test execute with valid files succeeds and returns success result."""
        # Setup mocks
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_workflow = Mock()
        mock_workflow.add_files.return_value = {
            "success": True,
            "added": ["file1.md", "file2.md"],
            "skipped": [],
            "failed": [],
        }
        mock_create_workflow.return_value = mock_workflow

        command = AddCommand(self.mock_settings)

        # Mock file operations
        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            with patch.object(command, "_display_add_results"):
                                mock_expand.return_value = [
                                    Path("file1.md"),
                                    Path("file2.md"),
                                ]
                                mock_filter.return_value = [
                                    Path("file1.md"),
                                    Path("file2.md"),
                                ]
                                mock_analyze.return_value = {
                                    "untracked": ["file1.md", "file2.md"],
                                    "modified": [],
                                    "staged": [],
                                    "up_to_date": [],
                                }

                                result = command.execute(
                                    files=[Path("file1.md"), Path("file2.md")],
                                    force=False,
                                    dry_run=False,
                                )

        # Verify result
        assert result["success"] is True
        assert "Added 2 files" in result["message"]
        assert result["data"]["success"] is True

        # Verify workflow was called correctly
        mock_workflow.add_files.assert_called_once_with(
            [Path("file1.md"), Path("file2.md")]
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_execute_with_no_expanded_files_returns_success_with_no_files_message(
        self, mock_show_message, mock_get_console
    ):
        """Test execute with no expanded files returns success with informative message."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                mock_expand.return_value = []

                result = command.execute(files=[Path("nonexistent.md")])

        assert result["success"] is True
        assert result["message"] == "No files to add"
        assert result["data"]["added"] == []
        mock_show_message.assert_called_with(
            "No spec files found in the specified paths", "warning"
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_execute_with_no_spec_files_returns_success_with_gen_suggestion(
        self, mock_show_message, mock_get_console
    ):
        """Test execute with no spec files suggests using 'spec gen' command."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    mock_expand.return_value = [Path("file1.md")]
                    mock_filter.return_value = []

                    result = command.execute(files=[Path("file1.md")])

        assert result["success"] is True
        assert result["message"] == "No spec files found"
        mock_show_message.assert_called_with(
            "No files in .specs/ directory found. Use 'spec gen' to create documentation first.",
            "warning",
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_execute_with_dry_run_returns_preview_without_adding_files(
        self, mock_show_message, mock_get_console
    ):
        """Test execute with dry_run=True shows preview without adding files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            mock_expand.return_value = [Path("file1.md")]
                            mock_filter.return_value = [Path("file1.md")]
                            mock_analyze.return_value = {
                                "untracked": ["file1.md"],
                                "modified": [],
                                "staged": [],
                                "up_to_date": [],
                            }

                            result = command.execute(
                                files=[Path("file1.md")], dry_run=True
                            )

        assert result["success"] is True
        assert "Dry run completed" in result["message"]
        assert result["data"]["files_to_add"] == [Path("file1.md")]
        mock_show_message.assert_called_with(
            "This is a dry run. No files would be added.", "info"
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    @patch("spec_cli.cli.commands.add_command.show_message")
    def test_execute_with_all_files_already_tracked_returns_success_message(
        self, mock_show_message, mock_repo_class, mock_get_console
    ):
        """Test execute with all files already tracked returns informative message."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            mock_expand.return_value = [Path("file1.md")]
                            mock_filter.return_value = [Path("file1.md")]
                            mock_analyze.return_value = {
                                "untracked": [],
                                "modified": [],
                                "staged": [],
                                "up_to_date": ["file1.md"],
                            }

                            result = command.execute(files=[Path("file1.md")])

        assert result["success"] is True
        assert result["message"] == "All files already tracked"
        mock_show_message.assert_called_with(
            "All specified files are already tracked and up to date", "info"
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    @patch("spec_cli.cli.commands.add_command.create_add_workflow")
    @patch("spec_cli.cli.commands.add_command.show_message")
    @patch("spec_cli.cli.commands.add_command.debug_logger")
    def test_execute_with_workflow_failure_returns_failure_result(
        self,
        mock_debug_logger,
        mock_show_message,
        mock_create_workflow,
        mock_repo_class,
        mock_get_console,
    ):
        """Test execute with workflow failure returns failure result."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_workflow = Mock()
        mock_workflow.add_files.return_value = {
            "success": False,
            "added": [],
            "skipped": [],
            "failed": [{"file": "file1.md", "error": "Permission denied"}],
        }
        mock_create_workflow.return_value = mock_workflow

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            with patch.object(command, "_display_add_results"):
                                mock_expand.return_value = [Path("file1.md")]
                                mock_filter.return_value = [Path("file1.md")]
                                mock_analyze.return_value = {
                                    "untracked": ["file1.md"],
                                    "modified": [],
                                    "staged": [],
                                    "up_to_date": [],
                                }

                                result = command.execute(files=[Path("file1.md")])

        assert result["success"] is False
        assert "Added 0 files" in result["message"]

    @patch("spec_cli.cli.commands.add_command.get_console")
    def test_execute_with_repository_validation_failure_raises_exception(
        self, mock_get_console
    ):
        """Test execute with repository validation failure raises exception."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state") as mock_validate:
            mock_validate.side_effect = SpecError("Repository not initialized")

            with pytest.raises(SpecError, match="Repository not initialized"):
                command.execute(files=[Path("file1.md")])

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    def test_execute_creates_repository_with_settings(
        self, mock_repo_class, mock_get_console
    ):
        """Test execute creates SpecGitRepository with correct settings."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                mock_expand.return_value = []

                command.execute(files=[Path("file1.md")])

        mock_repo_class.assert_called_once_with(self.mock_settings)

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    @patch("spec_cli.cli.commands.add_command.create_add_workflow")
    def test_execute_creates_workflow_with_force_and_settings(
        self, mock_create_workflow, mock_repo_class, mock_get_console
    ):
        """Test execute creates workflow with correct force flag and settings."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_workflow = Mock()
        mock_workflow.add_files.return_value = {
            "success": True,
            "added": ["file1.md"],
            "skipped": [],
            "failed": [],
        }
        mock_create_workflow.return_value = mock_workflow

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            with patch.object(command, "_display_add_results"):
                                mock_expand.return_value = [Path("file1.md")]
                                mock_filter.return_value = [Path("file1.md")]
                                mock_analyze.return_value = {
                                    "untracked": ["file1.md"],
                                    "modified": [],
                                    "staged": [],
                                    "up_to_date": [],
                                }

                                command.execute(files=[Path("file1.md")], force=True)

        mock_create_workflow.assert_called_once_with(
            force=True, settings=self.mock_settings
        )

    @patch("spec_cli.cli.commands.add_command.get_console")
    @patch("spec_cli.cli.commands.add_command.SpecGitRepository")
    @patch("spec_cli.cli.commands.add_command.show_message")
    @patch("spec_cli.cli.commands.add_command.debug_logger")
    def test_execute_logs_completion_information(
        self, mock_debug_logger, mock_show_message, mock_repo_class, mock_get_console
    ):
        """Test execute logs completion information with correct context."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        command = AddCommand(self.mock_settings)

        with patch.object(command, "validate_repository_state"):
            with patch.object(command, "_expand_spec_files") as mock_expand:
                with patch.object(command, "_filter_spec_files") as mock_filter:
                    with patch.object(command, "_analyze_git_status") as mock_analyze:
                        with patch.object(command, "_show_add_preview"):
                            mock_expand.return_value = [Path("file1.md")]
                            mock_filter.return_value = [Path("file1.md")]
                            mock_analyze.return_value = {
                                "untracked": [],
                                "modified": [],
                                "staged": [],
                                "up_to_date": ["file1.md"],
                            }

                            command.execute(files=[Path("file1.md")])

        # Verify debug logging was not called since no workflow was executed
        # (all files were already tracked)
        assert mock_debug_logger.log.call_count == 0
