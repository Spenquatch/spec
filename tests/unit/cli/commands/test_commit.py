"""Tests for commit command (commands/commit.py)."""

from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.commit import (
    commit_command, _auto_stage_changes, _show_commit_preview, _show_commit_result
)


class TestCommitCommand:
    """Test cases for commit command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('spec_cli.cli.commands.commit.get_user_confirmation')
    @patch('spec_cli.cli.commands.commit._show_commit_result')
    @patch('spec_cli.cli.commands.commit._show_commit_preview')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_creates_new_commit(self, mock_get_repo, mock_preview, 
                                              mock_result, mock_confirm):
        """Test commit command creates new commit."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': ['test.py', 'doc.md'],
            'modified': [],
            'untracked': []
        }
        mock_repo.commit.return_value = 'abc123def456'
        mock_get_repo.return_value = mock_repo
        mock_confirm.return_value = True
        
        result = self.runner.invoke(commit_command, ['-m', 'Test commit'])
        
        assert result.exit_code == 0
        mock_repo.commit.assert_called_once_with('Test commit')
        mock_preview.assert_called_once()
        mock_result.assert_called_once()

    @patch('spec_cli.cli.commands.commit._auto_stage_changes')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_auto_stages_changes(self, mock_get_repo, mock_auto_stage):
        """Test commit command auto-stages changes with --all flag."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.side_effect = [
            {
                'staged': [],
                'modified': ['test.py'],
                'untracked': []
            },
            {
                'staged': ['test.py'],
                'modified': [],
                'untracked': []
            }
        ]
        mock_repo.commit.return_value = 'abc123def456'
        mock_get_repo.return_value = mock_repo
        
        with patch('spec_cli.cli.commands.commit.get_user_confirmation', return_value=True):
            result = self.runner.invoke(commit_command, ['-a', '-m', 'Auto stage commit'])
        
        assert result.exit_code == 0
        mock_auto_stage.assert_called_once()

    @patch('spec_cli.cli.commands.commit._show_commit_result')
    @patch('spec_cli.cli.commands.commit._show_commit_preview')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_amends_last_commit(self, mock_get_repo, mock_preview, mock_result):
        """Test commit command amends last commit."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': ['test.py'],
            'modified': [],
            'untracked': []
        }
        mock_repo.amend_commit.return_value = 'abc123def456'
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(commit_command, ['--amend', '-m', 'Amended commit'])
        
        assert result.exit_code == 0
        mock_repo.amend_commit.assert_called_once_with('Amended commit')
        mock_preview.assert_called_once()
        mock_result.assert_called_once()

    @patch('spec_cli.cli.commands.commit._show_commit_preview')
    @patch('spec_cli.cli.commands.commit.show_message')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_dry_run_preview(self, mock_get_repo, mock_show_message, mock_preview):
        """Test commit command dry run shows preview without committing."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': ['test.py'],
            'modified': [],
            'untracked': []
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(commit_command, ['--dry-run', '-m', 'Dry run commit'])
        
        assert result.exit_code == 0
        mock_preview.assert_called_once()
        mock_show_message.assert_called_with(
            "This is a dry run. No commit would be created.", "info"
        )
        # Should not call commit
        mock_repo.commit.assert_not_called()
        mock_repo.amend_commit.assert_not_called()

    @patch('spec_cli.cli.commands.commit.show_message')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_no_staged_changes(self, mock_get_repo, mock_show_message):
        """Test commit command when no changes are staged."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': [],
            'modified': ['test.py'],
            'untracked': []
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(commit_command, ['-m', 'Test commit'])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with(
            "No changes staged for commit. Use 'spec add' to stage changes "
            "or use --all to stage all modified files.",
            "warning"
        )

    @patch('spec_cli.cli.commands.commit.show_message')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_no_changes_clean_directory(self, mock_get_repo, mock_show_message):
        """Test commit command when working directory is clean."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': [],
            'modified': [],
            'untracked': []
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(commit_command, ['-m', 'Test commit'])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with(
            "No changes to commit. Working directory clean.", "info"
        )

    @patch('spec_cli.cli.commands.commit.get_user_confirmation')
    @patch('spec_cli.cli.commands.commit.show_message')
    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_user_cancels(self, mock_get_repo, mock_show_message, mock_confirm):
        """Test commit command when user cancels confirmation."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_git_status.return_value = {
            'staged': ['test.py'],
            'modified': [],
            'untracked': []
        }
        mock_get_repo.return_value = mock_repo
        mock_confirm.return_value = False
        
        result = self.runner.invoke(commit_command, ['-m', 'Test commit'])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with("Commit cancelled", "info")

    @patch('spec_cli.cli.commands.commit.get_spec_repository')
    def test_commit_command_repository_error(self, mock_get_repo):
        """Test commit command handles repository errors."""
        mock_get_repo.side_effect = Exception("Repository error")
        
        result = self.runner.invoke(commit_command, ['-m', 'Test commit'])
        
        assert result.exit_code == 1
        assert "Commit failed" in result.output

    def test_commit_command_help(self):
        """Test commit command help display."""
        result = self.runner.invoke(commit_command, ['--help'])
        
        assert result.exit_code == 0
        assert "Commit staged changes" in result.output
        assert "--message" in result.output
        assert "--all" in result.output
        assert "--amend" in result.output
        assert "--dry-run" in result.output


class TestCommitUtilityFunctions:
    """Test cases for commit utility functions."""

    @patch('spec_cli.cli.commands.commit.show_message')
    def test_auto_stage_changes_success(self, mock_show_message):
        """Test auto-staging changes successfully."""
        mock_repo = Mock()
        status = {
            'modified': ['test1.py', 'test2.py'],
            'deleted': ['old.py']
        }
        
        _auto_stage_changes(mock_repo, status)
        
        # Should stage modified files
        assert mock_repo.add_file.call_count == 2
        mock_repo.add_file.assert_any_call('test1.py')
        mock_repo.add_file.assert_any_call('test2.py')
        
        # Should stage deleted files
        mock_repo.remove_file.assert_called_once_with('old.py')
        
        mock_show_message.assert_called_with("Auto-staged 3 files", "info")

    @patch('spec_cli.cli.commands.commit.show_message')
    def test_auto_stage_changes_with_errors(self, mock_show_message):
        """Test auto-staging changes with some errors."""
        mock_repo = Mock()
        mock_repo.add_file.side_effect = [None, Exception("Add error")]
        status = {
            'modified': ['test1.py', 'test2.py'],
            'deleted': []
        }
        
        _auto_stage_changes(mock_repo, status)
        
        # Should attempt to stage both files
        assert mock_repo.add_file.call_count == 2
        mock_show_message.assert_called_with("Auto-staged 2 files", "info")

    @patch('spec_cli.cli.commands.commit.get_console')
    def test_show_commit_preview_few_files(self, mock_get_console):
        """Test showing commit preview with few files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        staged_files = ['test1.py', 'test2.py']
        message = "Test commit"
        
        _show_commit_preview(staged_files, message, False)
        
        # Should print commit info
        assert mock_console.print.call_count >= 4  # Header, message, files count, files

    @patch('spec_cli.cli.commands.commit.get_console')
    def test_show_commit_preview_many_files(self, mock_get_console):
        """Test showing commit preview with many files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        # Create many files to test truncation
        staged_files = [f'test{i}.py' for i in range(20)]
        message = "Test commit"
        
        _show_commit_preview(staged_files, message, False)
        
        # Should print commit info and truncated file list
        assert mock_console.print.call_count >= 4

    @patch('spec_cli.cli.commands.commit.get_console')
    def test_show_commit_preview_amend(self, mock_get_console):
        """Test showing commit preview for amend operation."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        staged_files = ['test.py']
        message = "Amended commit"
        
        _show_commit_preview(staged_files, message, True)
        
        # Should show amend commit preview
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        preview_text = ' '.join(calls)
        assert 'Amend commit' in preview_text

    @patch('spec_cli.cli.commands.commit.get_console')
    @patch('spec_cli.cli.commands.commit.StatusTable')
    def test_show_commit_result_success(self, mock_status_table, mock_get_console):
        """Test showing commit result successfully."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_table = Mock()
        mock_status_table.return_value = mock_table
        
        mock_repo = Mock()
        mock_repo.get_commit_info.return_value = {
            'author': 'Test User',
            'date': '2023-12-01T10:00:00Z'
        }
        
        _show_commit_result(mock_repo, 'abc123def456', ['test.py'])
        
        # Should create and print table
        mock_status_table.assert_called_once_with("Commit Details")
        mock_table.add_status.assert_called()
        mock_table.print.assert_called_once()

    @patch('spec_cli.cli.commands.commit.get_console')
    def test_show_commit_result_get_info_error(self, mock_get_console):
        """Test showing commit result when getting commit info fails."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        mock_repo = Mock()
        mock_repo.get_commit_info.side_effect = Exception("Info error")
        
        # Should not raise exception
        _show_commit_result(mock_repo, 'abc123def456', ['test.py'])
        
        # Should still print next steps
        assert mock_console.print.call_count >= 2

    def test_commit_command_message_required(self):
        """Test commit command requires message."""
        runner = CliRunner()
        result = runner.invoke(commit_command, [])
        
        assert result.exit_code == 2  # Click parameter error
        assert "Missing option" in result.output or "required" in result.output.lower()