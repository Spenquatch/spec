"""Tests for history formatters (history/formatters.py)."""

from unittest.mock import Mock, patch
import pytest
from datetime import datetime

from spec_cli.cli.commands.history.formatters import (
    GitLogFormatter, GitDiffFormatter, CommitFormatter,
    format_commit_log, format_diff_output, format_commit_info
)


class TestGitLogFormatter:
    """Test cases for GitLogFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = GitLogFormatter()

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_commit_log_empty(self, mock_get_console):
        """Test formatting empty commit log."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        self.formatter.format_commit_log([])
        
        mock_console.print.assert_called_once_with("[muted]No commits found[/muted]")

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_commit_log_compact(self, mock_get_console):
        """Test formatting commit log in compact mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        commits = [
            {
                'hash': 'abc123',
                'date': '2023-12-01T10:00:00Z',
                'author': 'Test User',
                'message': 'Test commit'
            }
        ]
        
        self.formatter.format_commit_log(commits, compact=True)
        
        # Should create a table
        assert mock_console.print.call_count >= 1

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_commit_log_detailed(self, mock_get_console):
        """Test formatting commit log in detailed mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        commits = [
            {
                'hash': 'abc123def456',
                'date': '2023-12-01T10:00:00Z',
                'author': 'Test User',
                'message': 'Test commit\nWith details',
                'files': [
                    {'status': 'M', 'filename': 'test.py'},
                    {'status': 'A', 'filename': 'new.py'}
                ]
            }
        ]
        
        self.formatter.format_commit_log(commits, compact=False)
        
        # Should print commit details
        assert mock_console.print.call_count >= 1

    def test_format_single_commit(self):
        """Test formatting a single commit entry."""
        commit = {
            'hash': 'abc123def456',
            'author': 'Test User',
            'date': '2023-12-01T10:00:00Z',
            'message': 'Test commit',
            'files': [
                {'status': 'M', 'filename': 'test.py'}
            ]
        }
        
        with patch('spec_cli.cli.commands.history.formatters.get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            self.formatter._format_single_commit(commit)
            
            # Check that key information was printed
            calls = [call[0][0] for call in mock_console.print.call_args_list]
            commit_info = ' '.join(calls)
            
            assert 'abc123def456' in commit_info
            assert 'Test User' in commit_info
            assert 'Test commit' in commit_info


class TestGitDiffFormatter:
    """Test cases for GitDiffFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = GitDiffFormatter()

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_diff_output_empty(self, mock_get_console):
        """Test formatting empty diff output."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        self.formatter.format_diff_output({})
        
        mock_console.print.assert_called_once_with("[muted]No differences found[/muted]")

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_diff_output_with_files(self, mock_get_console):
        """Test formatting diff output with files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        diff_data = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified',
                    'hunks': [
                        {
                            'header': '@@ -1,3 +1,4 @@',
                            'lines': [
                                ' unchanged line',
                                '-removed line',
                                '+added line'
                            ]
                        }
                    ]
                }
            ]
        }
        
        self.formatter.format_diff_output(diff_data)
        
        # Should print summary and file diffs
        assert mock_console.print.call_count >= 2

    def test_format_diff_line(self):
        """Test formatting individual diff lines."""
        with patch('spec_cli.cli.commands.history.formatters.get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            # Test different line types
            self.formatter._format_diff_line('+added line')
            self.formatter._format_diff_line('-removed line')
            self.formatter._format_diff_line('@@ header @@')
            self.formatter._format_diff_line(' unchanged line')
            
            assert mock_console.print.call_count == 4


class TestCommitFormatter:
    """Test cases for CommitFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = CommitFormatter()

    @patch('spec_cli.cli.commands.history.formatters.get_console')
    def test_format_commit_info(self, mock_get_console):
        """Test formatting commit information."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        commit_data = {
            'hash': 'abc123def456',
            'author': 'Test User',
            'date': '2023-12-01T10:00:00Z',
            'message': 'Test commit\nWith details',
            'parent': 'parent123',
            'stats': {
                'files_changed': 2,
                'insertions': 10,
                'deletions': 5
            }
        }
        
        self.formatter.format_commit_info(commit_data)
        
        # Should print commit info and stats
        assert mock_console.print.call_count >= 1

    def test_format_commit_stats(self):
        """Test formatting commit statistics."""
        stats = {
            'files_changed': 3,
            'insertions': 15,
            'deletions': 8
        }
        
        with patch('spec_cli.cli.commands.history.formatters.get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            self.formatter._format_commit_stats(stats)
            
            # Should print statistics
            assert mock_console.print.call_count >= 1


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch('spec_cli.cli.commands.history.formatters.GitLogFormatter')
    def test_format_commit_log_function(self, mock_formatter_class):
        """Test format_commit_log convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        commits = [{'hash': 'abc123'}]
        format_commit_log(commits, compact=True)
        
        mock_formatter_class.assert_called_once()
        mock_formatter.format_commit_log.assert_called_once_with(commits, True)

    @patch('spec_cli.cli.commands.history.formatters.GitDiffFormatter')
    def test_format_diff_output_function(self, mock_formatter_class):
        """Test format_diff_output convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        diff_data = {'files': []}
        format_diff_output(diff_data)
        
        mock_formatter_class.assert_called_once()
        mock_formatter.format_diff_output.assert_called_once_with(diff_data)

    @patch('spec_cli.cli.commands.history.formatters.CommitFormatter')
    def test_format_commit_info_function(self, mock_formatter_class):
        """Test format_commit_info convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        commit_data = {'hash': 'abc123'}
        format_commit_info(commit_data)
        
        mock_formatter_class.assert_called_once()
        mock_formatter.format_commit_info.assert_called_once_with(commit_data)

    def test_formatter_initialization(self):
        """Test that formatters can be initialized without errors."""
        # Test that all formatters can be created
        git_log_formatter = GitLogFormatter()
        git_diff_formatter = GitDiffFormatter()
        commit_formatter = CommitFormatter()
        
        assert git_log_formatter is not None
        assert git_diff_formatter is not None
        assert commit_formatter is not None
        
        # Test they have expected attributes
        assert hasattr(git_log_formatter, 'console')
        assert hasattr(git_log_formatter, 'data_formatter')
        assert hasattr(git_diff_formatter, 'console')
        assert hasattr(commit_formatter, 'console')