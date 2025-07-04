"""Unit tests for CLI utility functions.

This module tests the CLI utility functions in utils.py including error handling,
path validation, logging setup, and repository operations.
"""

from pathlib import Path
from unittest.mock import Mock, patch

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
    with_progress_context,
)
from spec_cli.exceptions import SpecError, SpecRepositoryError
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    create_user_input_mocker,
)


class TestCLIUtilsMicro001:
    """Unit tests for CLI utilities - Micro-Agent Implementation."""

    def setup_method(self):
        """Setup using discovered CLI test helpers."""
        self.cli_runner = create_cli_command_runner()
        self.input_mocker = create_user_input_mocker()

    def test_handle_cli_error_with_click_exception(self):
        """Test handle_cli_error with Click exception shows error and exits."""
        click_error = click.ClickException("Test click error")

        with patch("sys.exit") as mock_exit:
            with patch.object(click_error, "show") as mock_show:
                with patch(
                    "spec_cli.cli.utils.cli_error_handler.report"
                ) as mock_report:
                    handle_cli_error(click_error, "test context", 2)

                    mock_report.assert_called_once_with(
                        click_error, "CLI command execution", cli_context="test context"
                    )
                    mock_show.assert_called_once()
                    mock_exit.assert_called_once_with(2)

    def test_handle_cli_error_with_spec_error(self):
        """Test handle_cli_error with SpecError formats message and exits."""
        spec_error = SpecError("Test spec error")
        spec_error.suggestions = ["Try this", "Or this"]

        with patch("sys.exit") as mock_exit:
            with patch("spec_cli.ui.error_display.show_message") as mock_show:
                with patch(
                    "spec_cli.cli.utils.cli_error_handler.report"
                ) as mock_report:
                    handle_cli_error(spec_error, "test context", 1)

                    mock_report.assert_called_once()
                    mock_show.assert_called_once()
                    # Verify message includes suggestions
                    args, kwargs = mock_show.call_args
                    assert "Suggestions:" in args[0]
                    assert "Try this" in args[0]
                    assert "Or this" in args[0]
                    mock_exit.assert_called_once_with(1)

    def test_handle_cli_error_with_generic_exception(self):
        """Test handle_cli_error with generic exception formats and exits."""
        generic_error = ValueError("Test generic error")

        with patch("sys.exit") as mock_exit:
            with patch("spec_cli.ui.error_display.show_message") as mock_show:
                with patch(
                    "spec_cli.cli.utils.cli_error_handler.report"
                ) as mock_report:
                    handle_cli_error(generic_error, "test context", 3)

                    mock_report.assert_called_once()
                    mock_show.assert_called_once()
                    # Verify message format
                    args, kwargs = mock_show.call_args
                    assert "ValueError: Test generic error" in args[0]
                    mock_exit.assert_called_once_with(3)

    def test_setup_cli_logging_debug_mode(self):
        """Test setup_cli_logging with debug mode enabled."""
        with patch("spec_cli.cli.utils.debug_logger.log") as mock_log:
            setup_cli_logging(debug_mode=True, verbose=False)

            mock_log.assert_called_once_with("INFO", "Debug mode enabled for CLI")

    def test_setup_cli_logging_verbose_mode(self):
        """Test setup_cli_logging with verbose mode enabled."""
        with patch("spec_cli.cli.utils.debug_logger.log") as mock_log:
            setup_cli_logging(debug_mode=False, verbose=True)

            mock_log.assert_called_once_with("INFO", "Verbose mode enabled for CLI")

    def test_setup_cli_logging_normal_mode(self):
        """Test setup_cli_logging with normal mode (no debug/verbose)."""
        with patch("spec_cli.cli.utils.debug_logger.log") as mock_log:
            setup_cli_logging(debug_mode=False, verbose=False)

            # Should not call log in normal mode
            mock_log.assert_not_called()

    def test_validate_file_paths_with_valid_paths(self):
        """Test validate_file_paths with valid file paths."""
        test_paths = ["test1.txt", "test2.py", "./test3.md"]

        result = validate_file_paths(test_paths)

        assert len(result) == 3
        assert all(isinstance(path, Path) for path in result)
        # Verify paths are resolved
        assert all(path.is_absolute() for path in result)

    def test_validate_file_paths_with_empty_list(self):
        """Test validate_file_paths with empty path list raises error."""
        with pytest.raises(click.BadParameter) as exc_info:
            validate_file_paths([])

        assert "No file paths provided" in str(exc_info.value)

    def test_validate_file_paths_with_invalid_path(self):
        """Test validate_file_paths with invalid path raises error."""
        # Use a path that would cause Path.resolve() to fail
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.side_effect = OSError("Invalid path")

            with pytest.raises(click.BadParameter) as exc_info:
                validate_file_paths(["invalid/path"])

            assert "Invalid file path" in str(exc_info.value)

    def test_get_user_confirmation_with_default_false(self):
        """Test get_user_confirmation with default False."""
        with patch("click.confirm") as mock_confirm:
            mock_confirm.return_value = True

            result = get_user_confirmation("Confirm action?", default=False)

            assert result is True
            mock_confirm.assert_called_once_with("Confirm action?", default=False)

    def test_get_user_confirmation_with_default_true(self):
        """Test get_user_confirmation with default True."""
        with patch("click.confirm") as mock_confirm:
            mock_confirm.return_value = False

            result = get_user_confirmation("Confirm action?", default=True)

            assert result is False
            mock_confirm.assert_called_once_with("Confirm action?", default=True)

    def test_format_command_output_auto_format(self):
        """Test format_command_output with auto format detection."""
        test_data = {"key": "value", "list": [1, 2, 3]}

        with patch("spec_cli.ui.error_display.format_data") as mock_format:
            format_command_output(test_data, "auto")

            mock_format.assert_called_once_with(test_data)

    def test_format_command_output_specific_format(self):
        """Test format_command_output with specific format type."""
        test_data = {"key": "value"}

        with patch("spec_cli.ui.error_display.format_data") as mock_format:
            format_command_output(test_data, "json")

            mock_format.assert_called_once_with(test_data, "json")

    def test_echo_status_with_different_types(self):
        """Test echo_status with different status types."""
        status_types = ["info", "success", "warning", "error"]

        with patch("spec_cli.ui.error_display.show_message") as mock_show:
            for status_type in status_types:
                echo_status(f"Test {status_type} message", status_type)

        assert mock_show.call_count == len(status_types)

    def test_get_spec_repository_success(self):
        """Test get_spec_repository with successful repository retrieval."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True

        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repo

            result = get_spec_repository()

            assert result is mock_repo
            mock_repo.is_initialized.assert_called_once()

    def test_get_spec_repository_not_initialized(self):
        """Test get_spec_repository when repository is not initialized."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False

        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repo

            with pytest.raises(click.ClickException) as exc_info:
                get_spec_repository()

            assert "Not in a spec repository" in str(exc_info.value)

    def test_get_spec_repository_with_repository_error(self):
        """Test get_spec_repository when SpecRepositoryError occurs."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.side_effect = SpecRepositoryError("Repository error")

            with patch(
                "spec_cli.cli.utils.cli_error_handler.log_and_raise"
            ) as mock_log_raise:
                mock_log_raise.side_effect = click.ClickException("Converted error")

                with pytest.raises(click.ClickException):
                    get_spec_repository()

                mock_log_raise.assert_called_once()

    def test_with_progress_context_decorator_success(self):
        """Test with_progress_context decorator with successful operation."""

        @with_progress_context("test_operation")
        def test_function():
            return "success"

        with patch(
            "spec_cli.ui.progress_manager.get_progress_manager"
        ) as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            result = test_function()

            assert result == "success"
            mock_manager.start_indeterminate_operation.assert_called_once()
            mock_manager.finish_operation.assert_called_once()

    def test_with_progress_context_decorator_exception(self):
        """Test with_progress_context decorator with exception in operation."""

        @with_progress_context("test_operation")
        def test_function():
            raise ValueError("Test error")

        with patch(
            "spec_cli.ui.progress_manager.get_progress_manager"
        ) as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            with pytest.raises(ValueError):
                test_function()

            # Should still finish operation on exception
            mock_manager.start_indeterminate_operation.assert_called_once()
            mock_manager.finish_operation.assert_called_once()

    def test_get_current_working_directory(self):
        """Test get_current_working_directory returns Path object."""
        result = get_current_working_directory()

        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result == Path.cwd()

    def test_is_in_spec_repository_true(self):
        """Test is_in_spec_repository when in spec repository."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = True

        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repo

            result = is_in_spec_repository()

            assert result is True
            mock_repo.is_initialized.assert_called_once()

    def test_is_in_spec_repository_false(self):
        """Test is_in_spec_repository when not in spec repository."""
        mock_repo = Mock()
        mock_repo.is_initialized.return_value = False

        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.return_value = mock_repo

            result = is_in_spec_repository()

            assert result is False

    def test_is_in_spec_repository_exception(self):
        """Test is_in_spec_repository when exception occurs."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.side_effect = Exception("Error")

            result = is_in_spec_repository()

            assert result is False

    def test_handle_cli_error_default_exit_code(self):
        """Test handle_cli_error uses default exit code when not specified."""
        test_error = RuntimeError("Test error")

        with patch("sys.exit") as mock_exit:
            with patch("spec_cli.ui.error_display.show_message"):
                with patch("spec_cli.cli.utils.cli_error_handler.report"):
                    handle_cli_error(test_error)

                    mock_exit.assert_called_once_with(1)  # Default exit code

    def test_validate_file_paths_resolves_relative_paths(self):
        """Test validate_file_paths properly resolves relative paths to absolute."""
        test_paths = ["../test.txt", "./local.py"]

        result = validate_file_paths(test_paths)

        # All paths should be absolute after validation
        assert all(path.is_absolute() for path in result)
        # Should have resolved relative components
        assert all("../" not in str(path) and "./" not in str(path) for path in result)
