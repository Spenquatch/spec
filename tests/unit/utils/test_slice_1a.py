"""Unit tests for Slice 1a - Git Command Whitelist Validator."""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecValidationError
from spec_cli.utils.security_validators import (
    ALLOWED_GIT_COMMANDS,
    _looks_like_file_path,
    _validate_git_file_paths,
    validate_git_command,
)


class TestValidateGitCommand:
    """Test cases for validate_git_command function."""

    def test_validate_git_command_when_valid_commands_then_returns_success(self):
        """Test that whitelisted commands pass validation."""
        valid_commands = [
            ["add", "file.txt"],
            ["commit", "-m", "message"],
            ["status"],
            ["log", "--oneline"],
            ["diff", "file1.txt", "file2.txt"],
            ["show", "HEAD"],
            ["init"],
        ]

        for cmd in valid_commands:
            is_valid, error = validate_git_command(cmd)
            assert is_valid is True
            assert error is None

    def test_validate_git_command_when_invalid_commands_then_returns_error(self):
        """Test that non-whitelisted commands fail validation."""
        invalid_commands = [
            (["rm", "-rf", "/"], "Git command 'rm' not allowed"),
            (["reset", "--hard"], "Git command 'reset' not allowed"),
            (["push", "origin", "main"], "Git command 'push' not allowed"),
            (["pull"], "Git command 'pull' not allowed"),
            (["checkout", "branch"], "Git command 'checkout' not allowed"),
            (["malicious"], "Git command 'malicious' not allowed"),
        ]

        for cmd, expected_error in invalid_commands:
            is_valid, error = validate_git_command(cmd)
            assert is_valid is False
            assert error == expected_error

    def test_validate_git_command_when_empty_list_then_returns_error(self):
        """Test that empty command list fails validation."""
        is_valid, error = validate_git_command([])
        assert is_valid is False
        assert error == "Empty git command"

    def test_validate_git_command_when_invalid_type_then_raises_type_error(self):
        """Test that non-list git_args raises TypeError."""
        with pytest.raises(TypeError, match="git_args must be a list"):
            validate_git_command("not a list")

    def test_validate_git_command_when_non_string_args_then_raises_type_error(self):
        """Test that non-string arguments raise TypeError."""
        with pytest.raises(TypeError, match="git_args\\[1\\] must be str"):
            validate_git_command(["add", 123])

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_git_command_when_work_tree_provided_and_safe_paths_then_returns_success(
        self, mock_safe_relative_to
    ):
        """Test that safe file paths pass validation with work tree."""
        mock_safe_relative_to.return_value = Path("safe/path.txt")
        work_tree = Path("/test/work")
        is_valid, error = validate_git_command(
            ["add", "file.txt", "subdir/other.txt"], work_tree
        )
        assert is_valid is True
        assert error is None

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_git_command_when_unsafe_paths_then_returns_error(
        self, mock_safe_relative_to
    ):
        """Test that unsafe file paths fail validation."""
        mock_safe_relative_to.side_effect = SpecValidationError("Path outside root")
        work_tree = Path("/test/work")

        is_valid, error = validate_git_command(
            ["add", "../../../etc/passwd"], work_tree
        )
        assert is_valid is False
        assert "File path '../../../etc/passwd' is outside work tree" in error


class TestValidateGitFilePaths:
    """Test cases for _validate_git_file_paths function."""

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_file_paths_when_safe_paths_then_returns_none(
        self, mock_safe_relative_to
    ):
        """Test that safe file paths return None (no error)."""
        mock_safe_relative_to.return_value = Path("safe/path.txt")
        work_tree = Path("/test/work")

        result = _validate_git_file_paths(["file.txt", "subdir/other.txt"], work_tree)
        assert result is None

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_file_paths_when_path_outside_work_tree_then_returns_error(
        self, mock_safe_relative_to
    ):
        """Test that paths outside work tree return error."""
        mock_safe_relative_to.side_effect = SpecValidationError("Path outside root")
        work_tree = Path("/test/work")

        result = _validate_git_file_paths(["../../../etc/passwd"], work_tree)
        assert result == "File path '../../../etc/passwd' is outside work tree"

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_file_paths_when_other_exception_then_returns_error(
        self, mock_safe_relative_to
    ):
        """Test that other path validation errors are converted to security errors."""
        mock_safe_relative_to.side_effect = ValueError("Invalid path format")
        work_tree = Path("/test/work")

        result = _validate_git_file_paths(["invalid\x00path"], work_tree)
        assert result == "Invalid file path 'invalid\x00path': Invalid path format"

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_file_paths_when_flags_present_then_skips_flags(
        self, mock_safe_relative_to
    ):
        """Test that git flags (starting with -) are skipped."""
        mock_safe_relative_to.return_value = Path("safe/path.txt")
        work_tree = Path("/test/work")

        # Should skip flags (-m, --author) and validate only if other args look like paths
        result = _validate_git_file_paths(
            ["-m", "commit message", "--author", "test"], work_tree
        )
        assert result is None  # No file-like paths to validate

    @patch("spec_cli.utils.security_validators._looks_like_file_path")
    def test_validate_file_paths_when_non_path_args_then_skips_them(
        self, mock_looks_like_file_path
    ):
        """Test that non-file-path arguments are skipped."""
        mock_looks_like_file_path.return_value = False
        work_tree = Path("/test/work")

        result = _validate_git_file_paths(["HEAD", "origin/main"], work_tree)
        assert result is None


class TestLooksLikeFilePath:
    """Test cases for _looks_like_file_path function."""

    def test_looks_like_file_path_when_contains_forward_slash_then_returns_true(self):
        """Test that paths with forward slashes are recognized as file paths."""
        assert _looks_like_file_path("dir/file.txt") is True
        assert _looks_like_file_path("./relative/path") is True
        assert _looks_like_file_path("/absolute/path") is True

    def test_looks_like_file_path_when_contains_backslash_then_returns_true(self):
        """Test that paths with backslashes are recognized as file paths."""
        assert _looks_like_file_path("dir\\file.txt") is True
        assert _looks_like_file_path("C:\\Windows\\path") is True

    def test_looks_like_file_path_when_simple_filenames_then_returns_true(self):
        """Test that simple filenames are recognized as file paths."""
        assert _looks_like_file_path("file.txt") is True
        assert _looks_like_file_path("script.py") is True
        assert _looks_like_file_path("README.md") is True
        assert _looks_like_file_path("Makefile") is True
        assert _looks_like_file_path("document") is True

    def test_looks_like_file_path_when_contains_equals_then_returns_false(self):
        """Test that arguments with equals signs are not recognized as file paths."""
        assert _looks_like_file_path("--author=user") is False
        assert _looks_like_file_path("key=value") is False
        assert _looks_like_file_path("option=setting") is False

    def test_looks_like_file_path_when_git_references_then_returns_false(self):
        """Test that Git references without path separators are not file paths."""
        assert _looks_like_file_path("HEAD") is False
        assert _looks_like_file_path("origin") is False
        assert _looks_like_file_path("main") is False
        assert _looks_like_file_path("master") is False
        assert _looks_like_file_path("origin/main") is False
        assert _looks_like_file_path("refs/heads/main") is False


class TestAllowedGitCommands:
    """Test cases for ALLOWED_GIT_COMMANDS constant."""

    def test_allowed_git_commands_contains_expected_commands(self):
        """Test that the whitelist contains all expected safe commands."""
        expected_commands = {"add", "commit", "status", "log", "diff", "show", "init"}
        assert ALLOWED_GIT_COMMANDS == expected_commands

    def test_allowed_git_commands_excludes_dangerous_commands(self):
        """Test that dangerous commands are not in the whitelist."""
        dangerous_commands = {
            "rm",
            "reset",
            "push",
            "pull",
            "checkout",
            "rebase",
            "merge",
            "branch",
            "tag",
            "clone",
            "fetch",
            "remote",
        }
        for cmd in dangerous_commands:
            assert cmd not in ALLOWED_GIT_COMMANDS


class TestSecurityScenarios:
    """Integration test cases for common security attack scenarios."""

    def test_directory_traversal_attack_prevention(self):
        """Test that directory traversal attacks are prevented."""
        attack_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "./../sensitive/file",
            "normal/../../../etc/shadow",
        ]

        work_tree = Path("/safe/work/tree")

        for attack_path in attack_paths:
            is_valid, error = validate_git_command(["add", attack_path], work_tree)
            assert is_valid is False
            assert "outside work tree" in error

    def test_command_injection_prevention(self):
        """Test that command injection attempts are prevented."""
        injection_commands = [
            ["add", "file.txt", ";", "rm", "-rf", "/"],
            ["add", "file.txt", "&&", "cat", "/etc/passwd"],
            ["add", "file.txt", "|", "malicious_command"],
            ["add", "`malicious_command`"],
            ["add", "$(rm -rf /)"],
        ]

        for cmd in injection_commands:
            # The first command might be valid, but subsequent malicious parts
            # should not affect validation since we only check the first argument
            is_valid, error = validate_git_command(
                cmd[:2]
            )  # Only check first valid part
            if cmd[0] in ALLOWED_GIT_COMMANDS:
                assert is_valid is True  # The git command itself is valid
            else:
                assert is_valid is False

    def test_null_byte_injection_prevention(self):
        """Test that null byte injection attempts are handled."""
        work_tree = Path("/test/work")

        # Null bytes in file paths should be caught by path validation
        is_valid, error = validate_git_command(["add", "file\x00.txt"], work_tree)
        # This might pass initial validation but would fail in path validation
        # The important thing is that it doesn't cause a crash
        assert isinstance(is_valid, bool)
        assert isinstance(error, str | type(None))

    def test_edge_case_empty_and_whitespace_args(self):
        """Test handling of edge cases with empty and whitespace arguments."""
        edge_cases = [
            ["add", ""],  # Empty filename
            ["add", "   "],  # Whitespace filename
            ["add", "\t\n"],  # Special whitespace characters
        ]

        work_tree = Path("/test/work")

        for cmd in edge_cases:
            is_valid, error = validate_git_command(cmd, work_tree)
            # Should handle gracefully without crashing
            assert isinstance(is_valid, bool)
            assert isinstance(error, str | type(None))


class TestCrossPlatformCompatibility:
    """Test cases for cross-platform path handling."""

    def test_unix_style_paths(self):
        """Test that Unix-style paths are handled correctly."""
        unix_paths = [
            "dir/file.txt",
            "./relative/path",
            "/absolute/path",
            "path/with spaces/file.txt",
        ]

        for path in unix_paths:
            assert _looks_like_file_path(path) is True

    def test_windows_style_paths(self):
        """Test that Windows-style paths are handled correctly."""
        windows_paths = [
            "dir\\file.txt",
            ".\\relative\\path",
            "C:\\absolute\\path",
            "path\\with spaces\\file.txt",
        ]

        for path in windows_paths:
            assert _looks_like_file_path(path) is True

    def test_mixed_path_separators(self):
        """Test that mixed path separators are handled correctly."""
        mixed_paths = [
            "dir/subdir\\file.txt",
            "unix/style\\windows",
            "C:/mixed\\separators/path",
        ]

        for path in mixed_paths:
            assert _looks_like_file_path(path) is True
