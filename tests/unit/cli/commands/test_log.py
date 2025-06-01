"""Tests for log command (commands/log.py)."""

from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.log import log_command


class TestLogCommand:
    """Test cases for log command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_shows_commit_history(self, mock_format_log, mock_get_repo):
        """Test log command shows commit history."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'author': 'Test User',
                'date': '2023-12-01T10:00:00Z',
                'message': 'Test commit'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, [])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        mock_format_log.assert_called_once()

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_filters_by_date_and_author(self, mock_format_log, mock_get_repo):
        """Test log command filters by date and author."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'author': 'John Doe',
                'date': '2023-12-01T10:00:00Z',
                'message': 'Test commit'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, [
            '--since', '2023-01-01',
            '--until', '2023-12-31',
            '--author', 'John Doe'
        ])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once_with(
            limit=10,
            since='2023-01-01',
            until='2023-12-31',
            author='John Doe',
            files=None,
            include_stats=False
        )
        mock_format_log.assert_called_once()

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_shows_file_specific_history(self, mock_format_log, mock_get_repo):
        """Test log command shows file-specific history."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'author': 'Test User',
                'date': '2023-12-01T10:00:00Z',
                'message': 'Update main.py'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['src/main.py'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        # Check that files parameter was passed
        call_args = mock_repo.get_commit_history.call_args[1]
        assert call_args['files'] == ['src/main.py']

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_oneline_format(self, mock_format_log, mock_get_repo):
        """Test log command with oneline format."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'author': 'Test User',
                'date': '2023-12-01T10:00:00Z',
                'message': 'Test commit'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['--oneline'])
        
        assert result.exit_code == 0
        mock_format_log.assert_called_once_with(mock_repo.get_commit_history.return_value, compact=True)

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.show_message')
    def test_log_command_no_commits_found(self, mock_show_message, mock_get_repo):
        """Test log command when no commits found."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = []
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, [])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with("No commits found in repository", "info")

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.show_message')
    def test_log_command_no_commits_for_files(self, mock_show_message, mock_get_repo):
        """Test log command when no commits found for specific files."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = []
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['src/main.py'])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with(
            "No commits found for files: src/main.py", "info"
        )

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_with_limit(self, mock_format_log, mock_get_repo):
        """Test log command with custom limit."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = []
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['--limit', '20'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        call_args = mock_repo.get_commit_history.call_args[1]
        assert call_args['limit'] == 20

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_with_grep_filter(self, mock_format_log, mock_get_repo):
        """Test log command with grep filter."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'message': 'feat: add new feature'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['--grep', 'feat'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        call_args = mock_repo.get_commit_history.call_args[1]
        assert call_args['grep'] == 'feat'

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_with_stats(self, mock_format_log, mock_get_repo):
        """Test log command with file change statistics."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'author': 'Test User',
                'message': 'Test commit',
                'stats': {
                    'files_changed': 2,
                    'insertions': 10,
                    'deletions': 5
                }
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['--stat'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        call_args = mock_repo.get_commit_history.call_args[1]
        assert call_args['include_stats'] is True

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.show_message')
    def test_log_command_shows_filter_context(self, mock_show_message, mock_get_repo):
        """Test log command shows filter context in output."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'message': 'Test commit'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, [
            'src/main.py',
            '--since', '2023-01-01',
            '--author', 'John Doe',
            '--grep', 'feature'
        ])
        
        assert result.exit_code == 0
        # Check that the context message includes filters
        show_message_calls = [call[0] for call in mock_show_message.call_args_list]
        context_message = show_message_calls[0][0]
        assert 'for src/main.py' in context_message
        assert 'since 2023-01-01' in context_message
        assert 'by John Doe' in context_message
        assert "containing 'feature'" in context_message

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    def test_log_command_repository_error(self, mock_get_repo):
        """Test log command handles repository errors."""
        mock_get_repo.side_effect = Exception("Repository error")
        
        result = self.runner.invoke(log_command, [])
        
        assert result.exit_code == 1
        assert "Log failed" in result.output

    def test_log_command_help(self):
        """Test log command help display."""
        result = self.runner.invoke(log_command, ['--help'])
        
        assert result.exit_code == 0
        assert "Show commit history" in result.output
        assert "--limit" in result.output
        assert "--oneline" in result.output
        assert "--since" in result.output
        assert "--until" in result.output
        assert "--author" in result.output
        assert "--grep" in result.output
        assert "--stat" in result.output

    @patch('spec_cli.cli.commands.log.get_spec_repository')
    @patch('spec_cli.cli.commands.log.format_commit_log')
    def test_log_command_multiple_files(self, mock_format_log, mock_get_repo):
        """Test log command with multiple files."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_history.return_value = [
            {
                'hash': 'abc123',
                'message': 'Update files'
            }
        ]
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(log_command, ['file1.py', 'file2.py'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_history.assert_called_once()
        call_args = mock_repo.get_commit_history.call_args[1]
        assert call_args['files'] == ['file1.py', 'file2.py']