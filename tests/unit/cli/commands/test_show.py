"""Tests for show command (commands/show.py)."""

from unittest.mock import Mock, patch, mock_open
import pytest
from click.testing import CliRunner
from pathlib import Path

from spec_cli.cli.commands.show import (
    show_command, _show_current_file, _show_file_from_commit,
    _is_spec_file, _parse_spec_content
)


class TestShowCommand:
    """Test cases for show command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('spec_cli.cli.commands.show._show_current_file')
    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_displays_current_file_content(self, mock_validate, mock_show_current):
        """Test show command displays current file content."""
        mock_validate.return_value = [Path('test.py')]
        
        result = self.runner.invoke(show_command, ['test.py'])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once_with(['test.py'])
        mock_show_current.assert_called_once()

    @patch('spec_cli.cli.commands.show._show_file_from_commit')
    @patch('spec_cli.cli.commands.show.get_spec_repository')
    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_displays_file_from_commit(self, mock_validate, mock_get_repo, mock_show_commit):
        """Test show command displays file from specific commit."""
        mock_validate.return_value = [Path('test.py')]
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        
        result = self.runner.invoke(show_command, ['--commit', 'abc123', 'test.py'])
        
        assert result.exit_code == 0
        mock_get_repo.assert_called_once()
        mock_show_commit.assert_called_once()

    @patch('spec_cli.cli.commands.show._show_current_file')
    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_handles_spec_file_formatting(self, mock_validate, mock_show_current):
        """Test show command handles spec file formatting."""
        mock_validate.return_value = [Path('.specs/test.py/index.md')]
        
        result = self.runner.invoke(show_command, ['.specs/test.py/index.md'])
        
        assert result.exit_code == 0
        mock_show_current.assert_called_once()

    @patch('spec_cli.cli.commands.show.get_console')
    @patch('spec_cli.cli.commands.show._show_current_file')
    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_raw_output_mode(self, mock_validate, mock_show_current, mock_console):
        """Test show command raw output mode."""
        mock_validate.return_value = [Path('test.py')]
        
        result = self.runner.invoke(show_command, ['--raw', 'test.py'])
        
        assert result.exit_code == 0
        mock_show_current.assert_called_once()

    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_no_valid_files(self, mock_validate):
        """Test show command with no valid file paths."""
        mock_validate.return_value = []
        
        result = self.runner.invoke(show_command, ['nonexistent.py'])
        
        assert result.exit_code == 2  # Click parameter error
        assert "No valid file paths provided" in result.output

    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_handles_file_error(self, mock_validate):
        """Test show command handles file reading errors."""
        mock_validate.side_effect = Exception("Validation error")
        
        result = self.runner.invoke(show_command, ['test.py'])
        
        assert result.exit_code == 1
        assert "Show failed" in result.output

    @patch('spec_cli.cli.commands.show._show_current_file')
    @patch('spec_cli.cli.commands.show.validate_file_paths')
    def test_show_command_multiple_files(self, mock_validate, mock_show_current):
        """Test show command with multiple files."""
        mock_validate.return_value = [Path('test1.py'), Path('test2.py')]
        
        result = self.runner.invoke(show_command, ['test1.py', 'test2.py'])
        
        assert result.exit_code == 0
        assert mock_show_current.call_count == 2

    def test_show_command_help(self):
        """Test show command help display."""
        result = self.runner.invoke(show_command, ['--help'])
        
        assert result.exit_code == 0
        assert "Display spec file content" in result.output
        assert "--commit" in result.output
        assert "--no-syntax" in result.output
        assert "--no-line-numbers" in result.output
        assert "--raw" in result.output


class TestShowUtilityFunctions:
    """Test cases for show utility functions."""

    @patch('spec_cli.cli.commands.show.display_file_content')
    @patch('builtins.open', new_callable=mock_open, read_data="print('hello')")
    def test_show_current_file_success(self, mock_file, mock_display):
        """Test showing current file content successfully."""
        file_path = Path('test.py')
        
        with patch.object(file_path, 'exists', return_value=True):
            _show_current_file(file_path, False, False, False)
        
        mock_display.assert_called_once()

    @patch('spec_cli.cli.commands.show.show_message')
    def test_show_current_file_not_found(self, mock_show_message):
        """Test showing current file when file not found."""
        file_path = Path('nonexistent.py')
        
        with patch.object(file_path, 'exists', return_value=False):
            _show_current_file(file_path, False, False, False)
        
        mock_show_message.assert_called_with(f"File not found: {file_path}", "error")

    @patch('spec_cli.cli.commands.show.get_console')
    @patch('builtins.open', new_callable=mock_open, read_data="content")
    def test_show_current_file_raw_mode(self, mock_file, mock_console):
        """Test showing current file in raw mode."""
        file_path = Path('test.py')
        mock_console_obj = Mock()
        mock_console.return_value = mock_console_obj
        
        with patch.object(file_path, 'exists', return_value=True):
            _show_current_file(file_path, False, False, True)
        
        mock_console_obj.print.assert_called_with("content")

    @patch('spec_cli.cli.commands.show.show_message')
    @patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test'))
    def test_show_current_file_encoding_fallback(self, mock_file, mock_show_message):
        """Test showing current file with encoding fallback."""
        file_path = Path('test.py')
        
        # Mock the fallback encoding to also fail
        with patch.object(file_path, 'exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Encoding error")):
                _show_current_file(file_path, False, False, False)
        
        mock_show_message.assert_called()

    @patch('spec_cli.cli.commands.show.get_console')
    @patch('spec_cli.cli.commands.show.display_file_content')
    def test_show_file_from_commit_success(self, mock_display, mock_console):
        """Test showing file from commit successfully."""
        mock_repo = Mock()
        mock_repo.get_file_content_at_commit.return_value = "commit content"
        mock_console_obj = Mock()
        mock_console.return_value = mock_console_obj
        
        _show_file_from_commit(mock_repo, Path('test.py'), 'abc123', False, False, False)
        
        mock_repo.get_file_content_at_commit.assert_called_once_with('test.py', 'abc123')
        mock_display.assert_called_once()

    @patch('spec_cli.cli.commands.show.show_message')
    def test_show_file_from_commit_not_found(self, mock_show_message):
        """Test showing file from commit when file not found."""
        mock_repo = Mock()
        mock_repo.get_file_content_at_commit.return_value = None
        
        _show_file_from_commit(mock_repo, Path('test.py'), 'abc123', False, False, False)
        
        mock_show_message.assert_called_with(
            "File test.py not found in commit abc123", "warning"
        )

    @patch('spec_cli.cli.commands.show.get_console')
    def test_show_file_from_commit_raw_mode(self, mock_console):
        """Test showing file from commit in raw mode."""
        mock_repo = Mock()
        mock_repo.get_file_content_at_commit.return_value = "raw content"
        mock_console_obj = Mock()
        mock_console.return_value = mock_console_obj
        
        _show_file_from_commit(mock_repo, Path('test.py'), 'abc123', False, False, True)
        
        mock_console_obj.print.assert_called_with("raw content")

    @patch('spec_cli.cli.commands.show.show_message')
    def test_show_file_from_commit_error(self, mock_show_message):
        """Test showing file from commit with error."""
        mock_repo = Mock()
        mock_repo.get_file_content_at_commit.side_effect = Exception("Git error")
        
        _show_file_from_commit(mock_repo, Path('test.py'), 'abc123', False, False, False)
        
        mock_show_message.assert_called_with(
            "Error retrieving file from commit: Git error", "error"
        )

    def test_is_spec_file_true(self):
        """Test detecting spec files correctly."""
        spec_file = Path('.specs/test.py/index.md')
        
        with patch.object(spec_file, 'relative_to', return_value=Path('test.py/index.md')):
            result = _is_spec_file(spec_file)
        
        assert result is True

    def test_is_spec_file_false_not_in_specs(self):
        """Test detecting non-spec files correctly."""
        regular_file = Path('test.py')
        
        with patch.object(regular_file, 'relative_to', side_effect=ValueError()):
            result = _is_spec_file(regular_file)
        
        assert result is False

    def test_is_spec_file_false_not_markdown(self):
        """Test detecting non-markdown files in specs directory."""
        non_md_file = Path('.specs/test.py/config.json')
        
        with patch.object(non_md_file, 'relative_to', return_value=Path('test.py/config.json')):
            result = _is_spec_file(non_md_file)
        
        assert result is False

    def test_parse_spec_content_with_frontmatter(self):
        """Test parsing spec content with YAML frontmatter."""
        content = """---
title: Test Spec
author: Test User
---
# Main Content

This is the spec content."""
        
        result = _parse_spec_content(content)
        
        assert result is not None
        assert 'metadata' in result
        assert 'content' in result
        assert result['metadata']['title'] == 'Test Spec'
        assert result['metadata']['author'] == 'Test User'
        assert '# Main Content' in result['content']

    def test_parse_spec_content_without_frontmatter(self):
        """Test parsing spec content without frontmatter."""
        content = "# Regular Content\n\nNo frontmatter here."
        
        result = _parse_spec_content(content)
        
        assert result is not None
        assert result['metadata'] == {}
        assert result['content'] == content

    def test_parse_spec_content_invalid(self):
        """Test parsing invalid spec content."""
        content = "---\ninvalid yaml: [unclosed\n---\ncontent"
        
        # Should handle gracefully and return None or basic structure
        result = _parse_spec_content(content)
        
        # Should not crash, may return None or basic structure
        assert result is None or isinstance(result, dict)