"""Tests for diff command (commands/diff.py)."""

from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.diff import diff_command, _display_diff_stats, _display_plain_diff


class TestDiffCommand:
    """Test cases for diff command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff.format_diff_output')
    def test_diff_command_working_directory_changes(self, mock_format_diff, mock_get_repo):
        """Test diff command shows working directory changes."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified',
                    'insertions': 5,
                    'deletions': 2
                }
            ]
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, [])
        
        assert result.exit_code == 0
        mock_repo.get_working_diff.assert_called_once_with(files=None, unified=3)
        mock_format_diff.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff.format_diff_output')
    def test_diff_command_staged_changes(self, mock_format_diff, mock_get_repo):
        """Test diff command shows staged changes."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_staged_diff.return_value = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified'
                }
            ]
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['--cached'])
        
        assert result.exit_code == 0
        mock_repo.get_staged_diff.assert_called_once_with(files=None, unified=3)
        mock_format_diff.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff.format_diff_output')
    def test_diff_command_compare_with_commit(self, mock_format_diff, mock_get_repo):
        """Test diff command compares with specific commit."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_commit_diff.return_value = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified'
                }
            ]
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['--commit', 'abc123'])
        
        assert result.exit_code == 0
        mock_repo.get_commit_diff.assert_called_once_with('abc123', files=None, unified=3)
        mock_format_diff.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff._display_diff_stats')
    def test_diff_command_stat_summary_only(self, mock_display_stats, mock_get_repo):
        """Test diff command shows statistics summary only."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified',
                    'insertions': 10,
                    'deletions': 5
                }
            ]
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['--stat'])
        
        assert result.exit_code == 0
        mock_display_stats.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff.show_message')
    def test_diff_command_no_differences(self, mock_show_message, mock_get_repo):
        """Test diff command when no differences found."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {'files': []}
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, [])
        
        assert result.exit_code == 0
        mock_show_message.assert_called_with(
            "No differences found in working directory changes", "info"
        )

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    @patch('spec_cli.cli.commands.diff._display_plain_diff')
    def test_diff_command_no_color(self, mock_display_plain, mock_get_repo):
        """Test diff command with no color output."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified'
                }
            ]
        }
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['--no-color'])
        
        assert result.exit_code == 0
        mock_display_plain.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    def test_diff_command_with_files(self, mock_get_repo):
        """Test diff command with specific files."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {'files': []}
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['file1.py', 'file2.py'])
        
        assert result.exit_code == 0
        mock_repo.get_working_diff.assert_called_once_with(
            files=['file1.py', 'file2.py'], unified=3
        )

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    def test_diff_command_unified_context(self, mock_get_repo):
        """Test diff command with custom unified context."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_working_diff.return_value = {'files': []}
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(diff_command, ['--unified', '5'])
        
        assert result.exit_code == 0
        mock_repo.get_working_diff.assert_called_once_with(files=None, unified=5)

    @patch('spec_cli.cli.commands.diff.get_spec_repository')
    def test_diff_command_repository_error(self, mock_get_repo):
        """Test diff command handles repository errors."""
        mock_get_repo.side_effect = Exception("Repository error")
        
        result = self.runner.invoke(diff_command, [])
        
        assert result.exit_code == 1
        assert "Diff failed" in result.output


class TestDiffUtilityFunctions:
    """Test cases for diff utility functions."""

    @patch('spec_cli.cli.commands.diff.get_console')
    def test_display_diff_stats_no_files(self, mock_get_console):
        """Test displaying diff stats with no files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        diff_data = {'files': []}
        _display_diff_stats(diff_data)
        
        mock_console.print.assert_called_with("[muted]No changes found[/muted]")

    @patch('spec_cli.cli.commands.diff.get_console')
    @patch('spec_cli.cli.commands.diff.StatusTable')
    def test_display_diff_stats_with_files(self, mock_status_table, mock_get_console):
        """Test displaying diff stats with files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_table = Mock()
        mock_status_table.return_value = mock_table
        
        diff_data = {
            'files': [
                {
                    'filename': 'test1.py',
                    'insertions': 10,
                    'deletions': 5
                },
                {
                    'filename': 'test2.py',
                    'insertions': 3,
                    'deletions': 2
                }
            ]
        }
        
        _display_diff_stats(diff_data)
        
        # Should create and print table
        mock_status_table.assert_called_once_with("Diff Statistics")
        mock_table.add_status.assert_called()
        mock_table.print.assert_called_once()

    @patch('spec_cli.cli.commands.diff.get_console')
    def test_display_diff_stats_with_many_files(self, mock_get_console):
        """Test displaying diff stats with many files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        # Create many files to test the file detail limit
        files = []
        for i in range(15):
            files.append({
                'filename': f'test{i}.py',
                'insertions': i,
                'deletions': i // 2
            })
        
        diff_data = {'files': files}
        
        with patch('spec_cli.cli.commands.diff.StatusTable'):
            _display_diff_stats(diff_data)
        
        # Should not show individual file details for many files
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        file_details = any('File Details:' in call for call in calls)
        assert not file_details

    @patch('spec_cli.cli.commands.diff.get_console')
    def test_display_plain_diff(self, mock_get_console):
        """Test displaying plain diff without color."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        diff_data = {
            'files': [
                {
                    'filename': 'test.py',
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
        
        _display_plain_diff(diff_data)
        
        # Should print file headers and diff content
        assert mock_console.print.call_count >= 3

    @patch('spec_cli.cli.commands.diff.get_console')
    def test_display_plain_diff_empty(self, mock_get_console):
        """Test displaying plain diff with empty data."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        diff_data = {'files': []}
        _display_plain_diff(diff_data)
        
        # Should handle empty data gracefully
        assert mock_console.print.call_count == 0

    def test_diff_command_help(self):
        """Test diff command help display."""
        runner = CliRunner()
        result = runner.invoke(diff_command, ['--help'])
        
        assert result.exit_code == 0
        assert "Show differences between versions" in result.output
        assert "--cached" in result.output
        assert "--commit" in result.output
        assert "--unified" in result.output
        assert "--no-color" in result.output
        assert "--stat" in result.output