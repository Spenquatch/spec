"""Tests for history formatters (history/formatters.py)."""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

from spec_cli.cli.commands.history.formatters import (
    CommitFormatter,
    GitDiffFormatter,
    GitLogFormatter,
    format_commit_info,
    format_commit_log,
    format_diff_output,
)


class TestGitLogFormatter:
    """Test cases for GitLogFormatter."""

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_commit_log_empty(self, mock_get_console: Mock) -> None:
        """Test formatting empty commit log."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitLogFormatter()
        formatter.format_commit_log([])

        mock_console.print.assert_called_once_with("[muted]No commits found[/muted]")

    @patch("spec_cli.cli.commands.history.formatters.SpecTable")
    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_commit_log_compact(
        self, mock_get_console: Mock, mock_spec_table: Mock
    ) -> None:
        """Test formatting commit log in compact mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_spec_table.return_value = mock_table

        formatter = GitLogFormatter()

        commits = [
            {
                "hash": "abc123",
                "date": "2023-12-01T10:00:00Z",
                "author": "Test User",
                "message": "Test commit",
            }
        ]

        formatter.format_commit_log(commits, compact=True)

        # Should create a table and print it
        mock_spec_table.assert_called_once()
        mock_table.print.assert_called_once()

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_commit_log_detailed(self, mock_get_console: Mock) -> None:
        """Test formatting commit log in detailed mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitLogFormatter()

        commits = [
            {
                "hash": "abc123def456",
                "date": "2023-12-01T10:00:00Z",
                "author": "Test User",
                "message": "Test commit\nWith details",
                "files": [
                    {"status": "M", "filename": "test.py"},
                    {"status": "A", "filename": "new.py"},
                ],
            }
        ]

        formatter.format_commit_log(commits, compact=False)

        # Should print commit details
        assert mock_console.print.call_count >= 1

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_single_commit(self, mock_get_console: Mock) -> None:
        """Test formatting a single commit entry."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitLogFormatter()

        commit = {
            "hash": "abc123def456",
            "author": "Test User",
            "date": "2023-12-01T10:00:00Z",
            "message": "Test commit",
            "files": [{"status": "M", "filename": "test.py"}],
        }

        formatter._format_single_commit(commit)

        # Check that key information was printed
        calls = [
            str(call.args[0]) for call in mock_console.print.call_args_list if call.args
        ]
        commit_info = " ".join(calls)

        assert "abc123def456" in commit_info
        assert "Test User" in commit_info
        assert "Test commit" in commit_info


class TestGitDiffFormatter:
    """Test cases for GitDiffFormatter."""

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_diff_output_empty(self, mock_get_console: Mock) -> None:
        """Test formatting empty diff output."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitDiffFormatter()
        formatter.format_diff_output({})

        mock_console.print.assert_called_once_with(
            "[muted]No differences found[/muted]"
        )

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_diff_output_with_files(self, mock_get_console: Mock) -> None:
        """Test formatting diff output with files."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitDiffFormatter()

        diff_data = {
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "hunks": [
                        {
                            "header": "@@ -1,3 +1,4 @@",
                            "lines": [
                                " unchanged line",
                                "-removed line",
                                "+added line",
                            ],
                        }
                    ],
                }
            ]
        }

        formatter.format_diff_output(diff_data)

        # Should print summary and file diffs
        assert mock_console.print.call_count >= 2

    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_diff_line(self, mock_get_console: Mock) -> None:
        """Test formatting individual diff lines."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        formatter = GitDiffFormatter()

        # Test different line types
        formatter._format_diff_line("+added line")
        formatter._format_diff_line("-removed line")
        formatter._format_diff_line("@@ header @@")
        formatter._format_diff_line(" unchanged line")

        assert mock_console.print.call_count == 4


class TestCommitFormatter:
    """Test cases for CommitFormatter."""

    @patch("spec_cli.cli.commands.history.formatters.SpecTable")
    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_commit_info(
        self, mock_get_console: Mock, mock_spec_table: Mock
    ) -> None:
        """Test formatting commit information."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_spec_table.return_value = mock_table

        formatter = CommitFormatter()

        commit_data = {
            "hash": "abc123def456",
            "author": "Test User",
            "date": "2023-12-01T10:00:00Z",
            "message": "Test commit\nWith details",
            "parent": "parent123",
            "stats": {"files_changed": 2, "insertions": 10, "deletions": 5},
        }

        formatter.format_commit_info(commit_data)

        # Should create table and print
        mock_spec_table.assert_called()
        mock_table.print.assert_called()

    @patch("spec_cli.cli.commands.history.formatters.SpecTable")
    @patch("spec_cli.cli.commands.history.formatters.get_console")
    def test_format_commit_stats(
        self, mock_get_console: Mock, mock_spec_table: Mock
    ) -> None:
        """Test formatting commit statistics."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        mock_table = Mock()
        mock_spec_table.return_value = mock_table

        formatter = CommitFormatter()

        stats = {"files_changed": 3, "insertions": 15, "deletions": 8}

        formatter._format_commit_stats(stats)

        # Should create table and call print method
        mock_spec_table.assert_called_once()
        mock_table.add_row.assert_called()
        mock_table.print.assert_called_once()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch("spec_cli.cli.commands.history.formatters.GitLogFormatter")
    def test_format_commit_log_function(self, mock_formatter_class: Mock) -> None:
        """Test format_commit_log convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter

        commits = [{"hash": "abc123"}]
        format_commit_log(commits, compact=True)

        mock_formatter_class.assert_called_once()
        mock_formatter.format_commit_log.assert_called_once_with(commits, True)

    @patch("spec_cli.cli.commands.history.formatters.GitDiffFormatter")
    def test_format_diff_output_function(self, mock_formatter_class: Mock) -> None:
        """Test format_diff_output convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter

        diff_data: Dict[str, List[Any]] = {"files": []}
        format_diff_output(diff_data)

        mock_formatter_class.assert_called_once()
        mock_formatter.format_diff_output.assert_called_once_with(diff_data)

    @patch("spec_cli.cli.commands.history.formatters.CommitFormatter")
    def test_format_commit_info_function(self, mock_formatter_class: Mock) -> None:
        """Test format_commit_info convenience function."""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter

        commit_data = {"hash": "abc123"}
        format_commit_info(commit_data)

        mock_formatter_class.assert_called_once()
        mock_formatter.format_commit_info.assert_called_once_with(commit_data)

    def test_formatter_initialization(self) -> None:
        """Test that formatters can be initialized without errors."""
        # Test that all formatters can be created
        git_log_formatter = GitLogFormatter()
        git_diff_formatter = GitDiffFormatter()
        commit_formatter = CommitFormatter()

        assert git_log_formatter is not None
        assert git_diff_formatter is not None
        assert commit_formatter is not None

        # Test they have expected attributes
        assert hasattr(git_log_formatter, "console")
        assert hasattr(git_diff_formatter, "console")
        assert hasattr(commit_formatter, "console")
