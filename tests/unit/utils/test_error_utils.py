"""Tests for error_utils module."""

import errno
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from spec_cli.utils.error_utils import (
    create_error_context,
    handle_os_error,
    handle_subprocess_error,
)


class TestHandleOsError:
    """Test handle_os_error function."""

    def test_handle_os_error_when_permission_denied_then_returns_formatted_message(
        self,
    ):
        """Test handling of permission denied error."""
        # Create OSError with permission denied errno
        exc = OSError(errno.EACCES, "Permission denied", "/protected/file")

        result = handle_os_error(exc)

        assert "Permission denied (errno 13)" in result
        assert "/protected/file" in result

    def test_handle_os_error_when_file_not_found_then_returns_descriptive_message(self):
        """Test handling of file not found error."""
        # Create OSError with file not found errno
        exc = OSError(errno.ENOENT, "No such file or directory", "/missing/file")

        result = handle_os_error(exc)

        assert "No such file or directory (errno 2)" in result
        assert "/missing/file" in result

    def test_handle_os_error_when_generic_error_then_includes_errno(self):
        """Test handling of generic OSError with errno."""
        # Create generic OSError with errno
        exc = OSError(errno.EIO, "Input/output error")

        result = handle_os_error(exc)

        assert "Input/output error (errno 5)" in result

    def test_handle_os_error_when_no_errno_then_returns_strerror_only(self):
        """Test handling of OSError without errno."""
        # Create OSError without errno
        exc = OSError("Generic error message")

        result = handle_os_error(exc)

        assert result == "Generic error message"

    def test_handle_os_error_when_no_filename_then_excludes_filename(self):
        """Test handling of OSError without filename."""
        # Create OSError without filename
        exc = OSError(errno.EPERM, "Operation not permitted")

        result = handle_os_error(exc)

        assert "Operation not permitted (errno 1)" == result

    def test_handle_os_error_when_invalid_type_then_raises_type_error(self):
        """Test that non-OSError raises TypeError."""
        with pytest.raises(TypeError, match="Expected OSError, got <class 'str'>"):
            handle_os_error("not an OSError")  # type: ignore

    def test_handle_os_error_when_complex_filename_then_formats_correctly(self):
        """Test handling of OSError with complex filename."""
        # Create OSError with path containing spaces and special chars
        complex_path = "/path/with spaces/file-name_123.txt"
        exc = OSError(errno.EACCES, "Permission denied", complex_path)

        result = handle_os_error(exc)

        assert "Permission denied (errno 13)" in result
        assert complex_path in result


class TestHandleSubprocessError:
    """Test handle_subprocess_error function."""

    def test_handle_subprocess_error_when_called_process_error_then_includes_stderr(
        self,
    ):
        """Test handling of CalledProcessError with stderr."""
        # Create CalledProcessError with stderr
        exc = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "status"], stderr="fatal: not a git repository"
        )

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 1): git status" in result
        assert "Stderr: fatal: not a git repository" in result

    def test_handle_subprocess_error_when_timeout_expired_then_returns_timeout_message(
        self,
    ):
        """Test handling of TimeoutExpired error."""
        # Create TimeoutExpired error
        exc = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=5.0)

        result = handle_subprocess_error(exc)

        assert "Command timed out after 5.0s: sleep 10" == result

    def test_handle_subprocess_error_when_command_list_then_formats_command(self):
        """Test handling when command is a list."""
        # Create CalledProcessError with command as list
        exc = subprocess.CalledProcessError(
            returncode=127,
            cmd=["unknown-command", "--flag", "value"],
            stderr="command not found",
        )

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 127): unknown-command --flag value" in result
        assert "Stderr: command not found" in result

    def test_handle_subprocess_error_when_command_string_then_formats_correctly(self):
        """Test handling when command is a string."""
        # Create CalledProcessError with command as string
        exc = subprocess.CalledProcessError(
            returncode=2,
            cmd="ls /nonexistent",
            stderr="ls: cannot access '/nonexistent': No such file or directory",
        )

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 2): ls /nonexistent" in result
        assert (
            "Stderr: ls: cannot access '/nonexistent': No such file or directory"
            in result
        )

    def test_handle_subprocess_error_when_both_stdout_stderr_then_includes_both(self):
        """Test handling when both stdout and stderr are present."""
        exc = subprocess.CalledProcessError(
            returncode=1, cmd=["test-command"], stderr="Some error"
        )
        # Manually set stdout since constructor doesn't accept it
        exc.stdout = "Some output"

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 1): test-command" in result
        assert "Stderr: Some error" in result
        assert "Stdout: Some output" in result

    def test_handle_subprocess_error_when_empty_stderr_then_excludes_stderr(self):
        """Test handling when stderr is empty."""
        exc = subprocess.CalledProcessError(
            returncode=1, cmd=["test-command"], stderr=""
        )

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 1): test-command" == result
        assert "Stderr:" not in result

    def test_handle_subprocess_error_when_whitespace_stderr_then_excludes_stderr(self):
        """Test handling when stderr contains only whitespace."""
        exc = subprocess.CalledProcessError(
            returncode=1, cmd=["test-command"], stderr="   \n\t  "
        )

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 1): test-command" == result
        assert "Stderr:" not in result

    def test_handle_subprocess_error_when_generic_subprocess_error_then_returns_generic_message(
        self,
    ):
        """Test handling of generic SubprocessError."""
        # Create generic SubprocessError
        exc = subprocess.SubprocessError("Generic subprocess error")

        result = handle_subprocess_error(exc)

        assert "Subprocess error: Generic subprocess error" == result

    def test_handle_subprocess_error_when_invalid_type_then_raises_type_error(self):
        """Test that non-SubprocessError raises TypeError."""
        with pytest.raises(
            TypeError, match="Expected SubprocessError, got <class 'str'>"
        ):
            handle_subprocess_error("not a SubprocessError")  # type: ignore

    def test_handle_subprocess_error_when_non_string_stdout_stderr_then_converts_to_string(
        self,
    ):
        """Test handling when stdout/stderr are not strings."""
        exc = subprocess.CalledProcessError(
            returncode=1, cmd=["test-command"], stderr=b"binary error"
        )
        # Manually set stdout since constructor doesn't accept it
        exc.stdout = b"binary output"

        result = handle_subprocess_error(exc)

        assert "Command failed (exit 1): test-command" in result
        assert "Stderr: b'binary error'" in result
        assert "Stdout: b'binary output'" in result


class TestCreateErrorContext:
    """Test create_error_context function."""

    def test_create_error_context_when_path_provided_then_includes_path_info(self):
        """Test creation of error context with valid path."""
        # Use a path that should exist in any system
        test_path = Path(__file__).parent  # Test directory should exist

        result = create_error_context(test_path)

        assert result["file_path"] == str(test_path)
        assert result["file_exists"] is True
        assert result["is_dir"] is True
        assert result["is_file"] is False
        assert "absolute_path" in result
        assert result["parent_path"] == str(test_path.parent)
        assert result["parent_exists"] is True

    def test_create_error_context_when_file_path_then_includes_file_info(self):
        """Test creation of error context with file path."""
        # Use current test file as it should exist
        test_file = Path(__file__)

        result = create_error_context(test_file)

        assert result["file_path"] == str(test_file)
        assert result["file_exists"] is True
        assert result["is_file"] is True
        assert result["is_dir"] is False
        assert "file_size" in result
        assert isinstance(result["file_size"], int)
        assert result["file_size"] > 0

    def test_create_error_context_when_nonexistent_path_then_marks_not_exists(self):
        """Test creation of error context with nonexistent path."""
        nonexistent = Path("/this/path/should/not/exist/anywhere")

        result = create_error_context(nonexistent)

        assert result["file_path"] == str(nonexistent)
        assert result["file_exists"] is False
        assert "is_file" not in result
        assert "is_dir" not in result
        assert "file_size" not in result
        assert result["parent_path"] == str(nonexistent.parent)

    def test_create_error_context_when_minimal_info_then_returns_basic_context(self):
        """Test that context always includes basic required fields."""
        test_path = Path("/tmp")

        result = create_error_context(test_path)

        # These fields should always be present
        required_fields = ["file_path", "file_exists", "parent_path", "parent_exists"]
        for field in required_fields:
            assert field in result

    def test_create_error_context_when_invalid_type_then_raises_type_error(self):
        """Test that non-Path object raises TypeError."""
        with pytest.raises(TypeError, match="Expected Path object, got <class 'str'>"):
            create_error_context("/not/a/path/object")  # type: ignore

    def test_create_error_context_when_stat_fails_then_continues_without_size(self):
        """Test that stat errors are handled gracefully."""
        # Create a mock path that exists but stat fails for size info
        test_file = MagicMock(spec=Path)
        test_file.exists.return_value = True
        test_file.is_file.return_value = True
        test_file.is_dir.return_value = False
        test_file.resolve.return_value = Path("/resolved/path")
        test_file.__str__ = lambda self: "/test/file"

        # Mock parent
        parent_mock = MagicMock(spec=Path)
        parent_mock.exists.return_value = True
        parent_mock.__str__ = lambda self: "/test"
        test_file.parent = parent_mock

        # Mock stat to fail
        test_file.stat.side_effect = OSError("Permission denied")

        result = create_error_context(test_file)

        # Should still work but without file_size
        assert result["file_exists"] is True
        assert result["is_file"] is True
        assert "file_size" not in result
        assert result["parent_exists"] is True

    def test_create_error_context_when_relative_path_then_includes_absolute(self):
        """Test that relative paths get resolved to absolute."""
        relative_path = Path(".")

        result = create_error_context(relative_path)

        assert result["file_exists"] is True
        assert "absolute_path" in result
        assert Path(result["absolute_path"]).is_absolute()

    def test_create_error_context_when_root_path_then_handles_parent_correctly(self):
        """Test handling of root path where parent might be same as path."""
        if Path.cwd().anchor:  # Only test on systems with drive letters/root
            root_path = Path(Path.cwd().anchor)

            result = create_error_context(root_path)

            assert result["file_exists"] is True
            assert "parent_path" in result
            assert "parent_exists" in result
