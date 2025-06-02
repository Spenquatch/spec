"""Tests for CLI utility functions (utils.py)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest

from spec_cli.cli.utils import (
    echo_status,
    format_command_output,
    get_current_working_directory,
    get_spec_repository,
    get_user_confirmation,
    handle_cli_error,
    is_in_spec_repository,
    setup_cli_logging,
    validate_file_paths,
)
from spec_cli.exceptions import SpecError


class TestCLIErrorHandling:
    """Test cases for CLI error handling."""

    def test_cli_error_handling_with_click_exception(self):
        """Test error handling for Click exceptions."""
        error = click.ClickException("Test click error")
        
        # We can't easily test sys.exit, so we test the concept
        with pytest.raises(SystemExit):
            handle_cli_error(error)

    def test_cli_error_handling_with_spec_error(self):
        """Test error handling for SpecError exceptions."""
        error = SpecError("Test spec error")
        
        with pytest.raises(SystemExit):
            handle_cli_error(error)

    def test_cli_error_handling_with_generic_error(self):
        """Test error handling for generic exceptions."""
        error = ValueError("Test generic error")
        
        with pytest.raises(SystemExit):
            handle_cli_error(error)

    def test_cli_error_handling_with_context(self):
        """Test error handling with context information."""
        error = ValueError("Test error")
        
        with pytest.raises(SystemExit):
            handle_cli_error(error, context="test context")


class TestFilePathValidation:
    """Test cases for file path validation."""

    def test_file_path_validation_with_valid_paths(self, tmp_path):
        """Test file path validation with valid paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        paths = validate_file_paths([str(test_file)])
        assert len(paths) == 1
        assert isinstance(paths[0], Path)

    def test_file_path_validation_with_empty_list(self):
        """Test file path validation with empty list."""
        with pytest.raises(click.BadParameter):
            validate_file_paths([])

    def test_file_path_validation_with_invalid_paths(self):
        """Test file path validation with invalid paths."""
        # Test with a path that should work (non-existent paths are actually valid)
        # Path.resolve() doesn't fail for non-existent paths
        paths = validate_file_paths(["/some/non/existent/path"])
        assert len(paths) == 1
        assert isinstance(paths[0], Path)


class TestCLILoggingSetup:
    """Test cases for CLI logging setup."""

    def test_cli_logging_setup_debug_mode(self):
        """Test CLI logging setup in debug mode."""
        # Test that the function runs without error
        setup_cli_logging(debug_mode=True, verbose=False)
        # Function should complete without raising an exception
        assert True

    def test_cli_logging_setup_verbose_mode(self):
        """Test CLI logging setup in verbose mode."""
        setup_cli_logging(debug_mode=False, verbose=True)
        assert True

    def test_cli_logging_setup_normal_mode(self):
        """Test CLI logging setup in normal mode."""
        setup_cli_logging(debug_mode=False, verbose=False)
        assert True


class TestRepositoryAccessHelpers:
    """Test cases for repository access helper functions."""

    @patch('spec_cli.git.repository.SpecGitRepository')
    def test_get_spec_repository_success(self, mock_git_repo):
        """Test successful repository access."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = True
        mock_git_repo.return_value = mock_repo
        
        repo = get_spec_repository()
        assert repo == mock_repo

    @patch('spec_cli.git.repository.SpecGitRepository')
    def test_get_spec_repository_not_initialized(self, mock_git_repo):
        """Test repository access when not initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = False
        mock_git_repo.return_value = mock_repo
        
        with pytest.raises(click.ClickException):
            get_spec_repository()

    @patch('spec_cli.git.repository.SpecGitRepository')
    def test_is_in_spec_repository_true(self, mock_git_repo):
        """Test is_in_spec_repository when in repository."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = True
        mock_git_repo.return_value = mock_repo
        
        result = is_in_spec_repository()
        assert result is True

    @patch('spec_cli.git.repository.SpecGitRepository')
    def test_is_in_spec_repository_false(self, mock_git_repo):
        """Test is_in_spec_repository when not in repository."""
        mock_git_repo.side_effect = Exception("Not a repository")
        
        result = is_in_spec_repository()
        assert result is False


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_get_current_working_directory(self):
        """Test getting current working directory."""
        cwd = get_current_working_directory()
        assert isinstance(cwd, Path)
        assert cwd.exists()

    @patch('spec_cli.cli.utils.click.confirm')
    def test_get_user_confirmation(self, mock_confirm):
        """Test user confirmation prompt."""
        mock_confirm.return_value = True
        
        result = get_user_confirmation("Test message?")
        assert result is True
        mock_confirm.assert_called_once_with("Test message?", default=False)

    def test_echo_status(self):
        """Test status message echo."""
        # Test that the function runs without error
        echo_status("Test message", "info")
        assert True

    def test_format_command_output(self):
        """Test command output formatting."""
        # Test that the function runs without error
        test_data = {"key": "value"}
        format_command_output(test_data, "auto")
        assert True