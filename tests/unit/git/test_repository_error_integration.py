"""Integration tests for Git Repository error handling utilities."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from spec_cli.git.repository import SpecGitRepository
from spec_cli.utils.error_utils import create_error_context, handle_subprocess_error


class TestGitRepositoryErrorIntegration:
    """Test Git Repository integration with error utilities."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Mock settings for Git Repository."""
        settings = Mock()
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.index_file = tmp_path / ".spec-index"
        return settings

    @pytest.fixture
    def mock_git_operations(self):
        """Mock GitOperations."""
        return Mock()

    @pytest.fixture
    def mock_path_converter(self):
        """Mock GitPathConverter."""
        converter = Mock()
        converter.convert_to_git_path.side_effect = lambda x: x  # Identity conversion
        return converter

    @pytest.fixture
    def git_repository(self, mock_settings):
        """Create Git Repository instance with mocked dependencies."""
        with patch("spec_cli.git.repository.GitOperations") as mock_ops:
            with patch("spec_cli.git.repository.GitPathConverter") as mock_conv:
                repo = SpecGitRepository(mock_settings)
                repo.operations = mock_ops.return_value
                repo.path_converter = mock_conv.return_value
                return repo

    def test_git_command_when_subprocess_error_then_uses_utilities(
        self, git_repository
    ):
        """Test that subprocess errors in git commands use error utilities."""
        # Create a subprocess error for rev-parse command
        subprocess_error = subprocess.CalledProcessError(
            1,
            ["git", "rev-parse", "HEAD"],
            stderr="fatal: ambiguous argument 'HEAD': unknown revision",
        )

        # Mock git operations - succeed for commit, fail for rev-parse
        def mock_git_command(args, **kwargs):
            if args[0] == "commit":
                return Mock(stdout="", stderr="", returncode=0)
            elif args[0] == "rev-parse":
                raise subprocess_error
            return Mock(stdout="", stderr="", returncode=0)

        git_repository.operations.run_git_command.side_effect = mock_git_command

        with patch("spec_cli.git.repository.debug_logger") as mock_logger:
            # Call commit method which tries to get commit hash
            commit_hash = git_repository.commit("test message")

            # Verify fallback behavior
            assert commit_hash == "unknown"

            # Verify debug_logger.log was called with formatted error
            mock_logger.log.assert_called()

            # Find the WARNING log call
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "WARNING"
                and "Failed to retrieve commit hash" in call[0][1]
            ]
            assert len(warning_calls) > 0

            # Verify error message uses utility formatting
            warning_message = warning_calls[0][0][1]
            expected_formatted = handle_subprocess_error(subprocess_error)
            assert expected_formatted in warning_message

    def test_repository_validation_when_error_then_uses_utilities(self, git_repository):
        """Test that repository validation errors use error utilities."""
        subprocess_error = subprocess.CalledProcessError(
            128,
            ["git", "symbolic-ref", "--short", "HEAD"],
            stderr="fatal: ref HEAD is not a symbolic ref",
        )

        # Mock git operations to raise subprocess error
        git_repository.operations.run_git_command.side_effect = subprocess_error

        with patch("spec_cli.git.repository.debug_logger") as mock_logger:
            # Call get_current_branch which should handle the error
            branch = git_repository.get_current_branch()

            # Verify fallback behavior
            assert branch == "HEAD"

            # Verify debug_logger.log was called with context
            mock_logger.log.assert_called()

            # Find the WARNING log call
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "WARNING"
                and "Could not determine current branch" in call[0][1]
            ]
            assert len(warning_calls) > 0

            # Verify context includes git-specific info
            call_kwargs = warning_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "git_current_branch"
            assert "git_command" in call_kwargs
            assert call_kwargs["git_command"] == "symbolic-ref --short HEAD"

    def test_git_error_context_includes_command_details(self, git_repository):
        """Test that git error context includes command details."""
        subprocess_error = subprocess.CalledProcessError(
            1,
            ["git", "log", "--max-count=5"],
            stderr="fatal: your current branch 'main' does not have any commits yet",
        )

        # Mock git operations to raise subprocess error
        git_repository.operations.run_git_command.side_effect = subprocess_error

        with patch("spec_cli.git.repository.debug_logger") as mock_logger:
            # Call get_recent_commits
            commits = git_repository.get_recent_commits(count=5)

            # Verify fallback behavior
            assert commits == []

            # Find the WARNING log call
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "WARNING"
                and "Could not get recent commits" in call[0][1]
            ]
            assert len(warning_calls) > 0

            # Verify context includes git operation details
            call_kwargs = warning_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "git_recent_commits"
            assert "git_command" in call_kwargs
            assert call_kwargs["git_command"] == "log --max-count=5"
            assert "requested_count" in call_kwargs
            assert call_kwargs["requested_count"] == 5

    def test_error_messages_consistent_across_git_operations(self, git_repository):
        """Test that error messages are consistent across git operations."""
        # Test different git operations with specific errors

        # Test symbolic-ref error for get_current_branch
        symbolic_ref_error = subprocess.CalledProcessError(
            128,
            ["git", "symbolic-ref", "HEAD"],
            stderr="fatal: ref HEAD is not a symbolic ref",
        )
        git_repository.operations.run_git_command.side_effect = symbolic_ref_error
        result = git_repository.get_current_branch()
        assert result == "HEAD"

        # Test log error for get_recent_commits
        log_error = subprocess.CalledProcessError(
            129, ["git", "log"], stderr="fatal: ambiguous argument"
        )
        git_repository.operations.run_git_command.side_effect = log_error
        result = git_repository.get_recent_commits()
        assert result == []

        # Test rev-parse error for commit (with proper mocking)
        rev_parse_error = subprocess.CalledProcessError(
            1, ["git", "rev-parse", "HEAD"], stderr="fatal: bad revision 'HEAD'"
        )

        def mock_git_command_for_commit(args, **kwargs):
            if args[0] == "commit":
                return Mock(stdout="", stderr="", returncode=0)
            elif args[0] == "rev-parse":
                raise rev_parse_error
            return Mock(stdout="", stderr="", returncode=0)

        git_repository.operations.run_git_command.side_effect = (
            mock_git_command_for_commit
        )
        result = git_repository.commit("test")
        assert result == "unknown"

        # Verify error formatting is consistent for all error types
        for error in [symbolic_ref_error, log_error, rev_parse_error]:
            expected_formatted = handle_subprocess_error(error)
            assert "Command failed" in expected_formatted
            assert f"exit {error.returncode}" in expected_formatted

    def test_context_creation_includes_git_repo_info(self, git_repository, tmp_path):
        """Test that error context includes git repository information."""
        # Create actual directories for context testing
        git_repository.settings.spec_dir.mkdir(parents=True, exist_ok=True)
        git_repository.settings.specs_dir.mkdir(parents=True, exist_ok=True)

        # Test context creation
        context = create_error_context(git_repository.settings.spec_dir)

        # Verify required context fields
        assert "file_path" in context
        assert "file_exists" in context
        assert context["file_exists"] is True
        assert "is_dir" in context
        assert context["is_dir"] is True
        assert "parent_path" in context
        assert "parent_exists" in context

    def test_non_subprocess_errors_handled_gracefully(self, git_repository):
        """Test that non-subprocess errors are handled gracefully."""
        # Test with a generic Exception (not subprocess.CalledProcessError)
        generic_error = Exception("Some generic error")

        # Mock git operations to raise generic error
        git_repository.operations.run_git_command.side_effect = generic_error

        with patch("spec_cli.git.repository.debug_logger") as mock_logger:
            # Call method that handles errors
            result = git_repository.get_current_branch()

            # Verify fallback behavior
            assert result == "HEAD"

            # Verify warning was logged (but without subprocess-specific formatting)
            mock_logger.log.assert_called()
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "WARNING"
            ]
            assert len(warning_calls) > 0

            # For generic errors, should use simple string representation
            warning_message = warning_calls[0][0][1]
            assert "Some generic error" in warning_message

    def test_git_repository_methods_maintain_functionality(self, git_repository):
        """Test that git repository methods maintain their core functionality."""

        # Mock successful git operations for both commit and rev-parse
        def mock_successful_git_command(args, **kwargs):
            if args[0] == "commit":
                return Mock(stdout="", stderr="", returncode=0)
            elif args[0] == "rev-parse":
                return Mock(stdout="abc123\n", stderr="", returncode=0)
            return Mock(stdout="", stderr="", returncode=0)

        git_repository.operations.run_git_command.side_effect = (
            mock_successful_git_command
        )

        # Test successful operations don't trigger error handling
        commit_hash = git_repository.commit("test message")
        assert commit_hash == "abc123"

        # Verify git_repository.operations.run_git_command was called
        assert (
            git_repository.operations.run_git_command.call_count >= 2
        )  # commit + rev-parse

        # Check that commit command was called properly
        call_args_list = git_repository.operations.run_git_command.call_args_list
        commit_call = None
        for call in call_args_list:
            if call[0][0][0] == "commit":
                commit_call = call[0][0]
                break

        assert commit_call is not None
        assert "commit" in commit_call
        assert "-m" in commit_call
        assert "test message" in commit_call

    def test_error_utilities_integration_patterns(self, tmp_path):
        """Test that error utility integration patterns work correctly."""
        # Test error formatting with different subprocess errors
        errors_to_test = [
            subprocess.CalledProcessError(1, ["git", "status"], "error output"),
            subprocess.CalledProcessError(
                128, ["git", "branch"], stderr="branch error"
            ),
            subprocess.CalledProcessError(129, ["git", "log", "--oneline"]),
        ]

        for error in errors_to_test:
            formatted = handle_subprocess_error(error)

            # Verify consistent formatting
            assert "Command failed" in formatted
            assert f"exit {error.returncode}" in formatted
            assert " ".join(error.cmd) in formatted

            # Verify stderr is included when present
            if hasattr(error, "stderr") and error.stderr:
                assert error.stderr in formatted

        # Test context creation
        test_path = tmp_path / "test_repo"
        test_path.mkdir()

        context = create_error_context(test_path)
        assert isinstance(context, dict)
        assert "file_path" in context
        assert "file_exists" in context
        assert "is_dir" in context
