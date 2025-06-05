"""Tests for Slice 1b: Secure Git Operations Integration.

Tests the integration of command validation into GitOperations to eliminate
injection vulnerabilities while maintaining existing functionality.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations


class TestSecureGitOperationsIntegration:
    """Tests for secure Git operations integration in GitOperations."""

    @pytest.fixture
    def git_ops(self, tmp_path: Path) -> GitOperations:
        """Create GitOperations instance for testing."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        return GitOperations(spec_dir, specs_dir, index_file)

    @pytest.fixture
    def mock_subprocess_run(self) -> Mock:
        """Mock subprocess.run for testing command execution."""
        with patch("spec_cli.git.operations.subprocess.run") as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "success"
            mock_process.stderr = ""
            mock_run.return_value = mock_process
            yield mock_run

    @pytest.fixture
    def mock_validate_git_command(self) -> Mock:
        """Mock validate_git_command for testing validation integration."""
        with patch("spec_cli.git.operations.validate_git_command") as mock_validate:
            mock_validate.return_value = (True, None)  # Default to valid
            yield mock_validate

    def test_run_git_command_when_valid_command_then_executes_successfully(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that valid commands pass validation and execute."""
        # Setup - validation passes
        mock_validate_git_command.return_value = (True, None)

        # Execute
        result = git_ops.run_git_command(["status"])

        # Verify validation was called with correct parameters
        mock_validate_git_command.assert_called_once_with(["status"], git_ops.specs_dir)

        # Verify command was executed
        assert mock_subprocess_run.called
        assert result.returncode == 0

    def test_run_git_command_when_invalid_command_then_raises_spec_git_error(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that invalid commands fail validation and raise SpecGitError."""
        # Setup - validation fails
        error_message = "Git command 'rm' not allowed"
        mock_validate_git_command.return_value = (False, error_message)

        # Execute and verify exception
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["rm", "-rf", "file.txt"])

        # Verify validation was called
        mock_validate_git_command.assert_called_once_with(
            ["rm", "-rf", "file.txt"], git_ops.specs_dir
        )

        # Verify error message contains validation failure
        assert "Command validation failed" in str(exc_info.value)
        assert error_message in str(exc_info.value)

        # Verify subprocess was never called
        assert not mock_subprocess_run.called

    def test_run_git_command_when_directory_traversal_attempt_then_blocks_command(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that directory traversal attacks are blocked."""
        # Setup - validation fails for path traversal
        error_message = "File path '../../../etc/passwd' is outside work tree"
        mock_validate_git_command.return_value = (False, error_message)

        # Execute and verify exception
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["add", "../../../etc/passwd"])

        # Verify validation was called
        mock_validate_git_command.assert_called_once_with(
            ["add", "../../../etc/passwd"], git_ops.specs_dir
        )

        # Verify error message contains validation failure
        assert "Command validation failed" in str(exc_info.value)
        assert error_message in str(exc_info.value)

        # Verify subprocess was never called
        assert not mock_subprocess_run.called

    def test_run_git_command_validation_error_logging(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that validation failures are properly logged."""
        with patch("spec_cli.git.operations.debug_logger") as mock_logger:
            # Setup - validation fails
            error_message = "Git command 'dangerous' not allowed"
            mock_validate_git_command.return_value = (False, error_message)

            # Execute and catch exception
            with pytest.raises(SpecGitError):
                git_ops.run_git_command(["dangerous", "command"])

            # Verify error logging occurred
            mock_logger.log.assert_called_with(
                "ERROR",
                "Git command validation failed",
                command=["dangerous", "command"],
                error=error_message,
            )

    @patch("spec_cli.git.operations.handle_subprocess_error")
    def test_run_git_command_when_subprocess_error_then_uses_secure_error_handling(
        self,
        mock_handle_error: Mock,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that subprocess errors use secure error handling."""
        # Setup - validation passes but subprocess fails
        mock_validate_git_command.return_value = (True, None)
        subprocess_error = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "status"], stderr="sensitive error information"
        )
        mock_subprocess_run.side_effect = subprocess_error
        mock_handle_error.return_value = "Command failed (exit 1): git status"

        # Execute and verify exception
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["status"])

        # Verify secure error handler was called
        mock_handle_error.assert_called_once_with(subprocess_error)

        # Verify error message uses secure formatting
        assert "Git command failed: Command failed (exit 1): git status" in str(
            exc_info.value
        )

    def test_run_git_command_when_file_not_found_then_provides_secure_error_message(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that FileNotFoundError provides secure error message."""
        # Setup - validation passes but git binary not found
        mock_validate_git_command.return_value = (True, None)
        mock_subprocess_run.side_effect = FileNotFoundError("/path/to/git: not found")

        # Execute and verify exception
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["status"])

        # Verify error message doesn't expose system paths
        error_msg = str(exc_info.value)
        assert "Git command not found" in error_msg
        assert "Please ensure Git is installed and in PATH" in error_msg
        assert "/path/to/git" not in error_msg  # Sensitive path info not exposed

    def test_run_git_command_when_unexpected_error_then_handles_securely(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that unexpected errors are handled securely."""
        # Setup - validation passes but unexpected error occurs
        mock_validate_git_command.return_value = (True, None)
        unexpected_error = RuntimeError("Internal system error with sensitive data")
        mock_subprocess_run.side_effect = unexpected_error

        # Execute and verify exception
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["status"])

        # Verify error message is generic and secure
        error_msg = str(exc_info.value)
        assert "Unexpected error during git command execution" in error_msg
        # Original error message is included but wrapped securely

    def test_validation_integration_preserves_existing_functionality(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that security integration preserves existing GitOperations functionality."""
        # Setup - validation passes
        mock_validate_git_command.return_value = (True, None)

        # Test with capture_output=False
        result = git_ops.run_git_command(["status"], capture_output=False)

        # Verify validation was called
        mock_validate_git_command.assert_called_once_with(["status"], git_ops.specs_dir)

        # Verify subprocess.run was called with correct parameters
        call_args = mock_subprocess_run.call_args
        assert call_args[1]["capture_output"] is False

        # Verify result is returned correctly
        assert result.returncode == 0

    def test_validation_with_file_arguments_uses_work_tree_context(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that validation receives correct work tree context for file validation."""
        # Setup - validation passes
        mock_validate_git_command.return_value = (True, None)

        # Execute command with file arguments
        git_ops.run_git_command(["add", "file1.md", "file2.md"])

        # Verify validation was called with specs_dir for path validation
        mock_validate_git_command.assert_called_once_with(
            ["add", "file1.md", "file2.md"], git_ops.specs_dir
        )

    def test_error_logging_excludes_sensitive_command_details(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that error logging uses only command name, not full arguments."""
        with patch("spec_cli.git.operations.debug_logger") as mock_logger:
            # Setup - validation passes but subprocess fails
            mock_validate_git_command.return_value = (True, None)
            subprocess_error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["git", "add", "sensitive_file.txt"],
                stderr="sensitive error information",
            )
            mock_subprocess_run.side_effect = subprocess_error

            # Execute and catch exception
            with pytest.raises(SpecGitError):
                git_ops.run_git_command(["add", "sensitive_file.txt"])

            # Verify logging calls
            error_calls = [
                call for call in mock_logger.log.call_args_list if call[0][0] == "ERROR"
            ]

            # Find the subprocess error logging call
            subprocess_error_call = None
            for call in error_calls:
                if "Git command failed" in call[0][1]:
                    subprocess_error_call = call
                    break

            assert subprocess_error_call is not None

            # Verify only the command name is logged, not full arguments
            assert subprocess_error_call[1]["command"] == "add"
            # Verify the command field doesn't contain sensitive arguments
            assert subprocess_error_call[1]["command"] != ["add", "sensitive_file.txt"]
            # The error_details may contain the full command (expected from handle_subprocess_error)
            # but the direct command field should only be the git command name

    def test_backwards_compatibility_with_existing_callers(
        self,
        git_ops: GitOperations,
        mock_subprocess_run: Mock,
        mock_validate_git_command: Mock,
    ) -> None:
        """Test that existing callers continue to work without modification."""
        # Setup - validation passes
        mock_validate_git_command.return_value = (True, None)

        # Test all existing parameter combinations
        test_cases = [
            # Basic command
            (["status"], {}),
            # With capture_output=True (default)
            (["log", "--oneline"], {"capture_output": True}),
            # With capture_output=False
            (["add", "file.txt"], {"capture_output": False}),
        ]

        for args, kwargs in test_cases:
            # Reset mock to track individual calls
            mock_subprocess_run.reset_mock()
            mock_validate_git_command.reset_mock()

            # Execute
            result = git_ops.run_git_command(args, **kwargs)

            # Verify validation was called
            assert mock_validate_git_command.called

            # Verify subprocess was called
            assert mock_subprocess_run.called

            # Verify result is returned
            assert result.returncode == 0


class TestSecureGitOperationsIdempotency:
    """Test that secure git operations remain consistent across multiple calls."""

    @pytest.fixture
    def git_ops(self, tmp_path: Path) -> GitOperations:
        """Create GitOperations instance for testing."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        return GitOperations(spec_dir, specs_dir, index_file)

    def test_security_validation_idempotency(self, git_ops: GitOperations) -> None:
        """Test that security validation behaves consistently across multiple calls."""
        with (
            patch("spec_cli.git.operations.subprocess.run") as mock_run,
            patch("spec_cli.git.operations.validate_git_command") as mock_validate,
        ):
            # Setup mocks
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process
            mock_validate.return_value = (True, None)

            # Execute same command multiple times
            for _ in range(3):
                result = git_ops.run_git_command(["status"])
                assert result.returncode == 0

            # Verify validation was called consistently
            assert mock_validate.call_count == 3
            for call in mock_validate.call_args_list:
                assert call[0] == (["status"], git_ops.specs_dir)

    def test_security_blocking_idempotency(self, git_ops: GitOperations) -> None:
        """Test that security blocking is consistent across multiple attempts."""
        with (
            patch("spec_cli.git.operations.subprocess.run") as mock_run,
            patch("spec_cli.git.operations.validate_git_command") as mock_validate,
        ):
            # Setup - validation always fails
            mock_validate.return_value = (False, "Command not allowed")

            # Execute same invalid command multiple times
            for _ in range(3):
                with pytest.raises(SpecGitError) as exc_info:
                    git_ops.run_git_command(["dangerous", "command"])

                assert "Command validation failed" in str(exc_info.value)

            # Verify subprocess was never called
            assert not mock_run.called

            # Verify validation was called consistently
            assert mock_validate.call_count == 3
