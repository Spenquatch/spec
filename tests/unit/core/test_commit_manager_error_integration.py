"""Integration tests for Commit Manager error handling utilities."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.commit_manager import SpecCommitManager
from spec_cli.exceptions import SpecGitError
from spec_cli.utils.error_utils import (
    create_error_context,
    handle_os_error,
    handle_subprocess_error,
)


class TestCommitManagerErrorIntegration:
    """Test Commit Manager integration with error utilities."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Mock settings for Commit Manager."""
        settings = Mock()
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.index_file = tmp_path / ".spec-index"
        return settings

    @pytest.fixture
    def mock_git_repo(self):
        """Mock Git Repository."""
        return Mock()

    @pytest.fixture
    def mock_state_checker(self):
        """Mock Repository State Checker."""
        return Mock()

    @pytest.fixture
    def commit_manager(self, mock_settings):
        """Create Commit Manager instance with mocked dependencies."""
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_git:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker:
                manager = SpecCommitManager(mock_settings)
                manager.git_repo = mock_git.return_value
                manager.state_checker = mock_checker.return_value
                return manager

    def test_commit_validation_when_os_error_then_uses_utilities(self, commit_manager):
        """Test that OS errors in commit validation use error utilities."""
        # Mock validation to pass
        commit_manager.state_checker.validate_pre_operation_state.return_value = []
        commit_manager.git_repo.get_staged_files.return_value = ["test.md"]

        # Create an OS error for the commit operation
        os_error = OSError(28, "No space left on device", "/tmp/git_commit")
        commit_manager.git_repo.run_git_command.side_effect = os_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError) as exc_info:
                commit_manager.commit_changes("test commit")

            # Verify error uses utility formatting
            expected_formatted = handle_os_error(os_error)
            assert expected_formatted in str(exc_info.value)

            # Verify debug_logger.log was called with context
            mock_logger.log.assert_called()

            # Find the ERROR log call
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Commit operation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            # Verify context includes commit-specific info
            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_commit_changes"
            assert "message_length" in call_kwargs
            assert "allow_empty" in call_kwargs

    def test_commit_execution_when_subprocess_error_then_uses_utilities(
        self, commit_manager
    ):
        """Test that subprocess errors in commit execution use error utilities."""
        # Mock validation to pass
        commit_manager.state_checker.validate_pre_operation_state.return_value = []
        commit_manager.git_repo.get_staged_files.return_value = ["test.md"]

        # Create a subprocess error for the commit operation
        subprocess_error = subprocess.CalledProcessError(
            1,
            ["git", "commit", "-m", "test"],
            stderr="error: gpg failed to sign the data",
        )
        commit_manager.git_repo.run_git_command.side_effect = subprocess_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError) as exc_info:
                commit_manager.commit_changes("test commit")

            # Verify error uses utility formatting
            expected_formatted = handle_subprocess_error(subprocess_error)
            assert expected_formatted in str(exc_info.value)

            # Verify debug_logger.log was called with context
            mock_logger.log.assert_called()

            # Find the ERROR log call
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Commit operation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            # Verify context includes subprocess-specific info
            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_commit_changes"

    def test_commit_error_context_includes_workflow_details(self, commit_manager):
        """Test that commit error context includes workflow details."""
        # Mock validation to pass
        commit_manager.state_checker.validate_pre_operation_state.return_value = []
        commit_manager.git_repo.get_staged_files.return_value = ["test.md"]

        # Create an error
        os_error = OSError(13, "Permission denied", "/repo/.git/objects")
        commit_manager.git_repo.run_git_command.side_effect = os_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError):
                commit_manager.commit_changes(
                    "test commit", author="Test Author", allow_empty=True
                )

            # Find the ERROR log call
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Commit operation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            # Verify context includes commit workflow details
            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_commit_changes"
            assert "message_length" in call_kwargs
            assert call_kwargs["message_length"] == len("test commit")
            assert "author" in call_kwargs
            assert call_kwargs["author"] == "Test Author"
            assert "allow_empty" in call_kwargs
            assert call_kwargs["allow_empty"] is True

    def test_error_handling_consistent_across_commit_stages(self, commit_manager):
        """Test that error handling is consistent across different commit stages."""
        # Test add_files method properly handles missing files (normal case)
        with patch("pathlib.Path.exists", return_value=False):  # File doesn't exist
            result = commit_manager.add_files(["missing.md"], validate=False)
            assert not result["success"]
            assert len(result["errors"]) > 0

        # Test create_tag error handling
        subprocess_error = subprocess.CalledProcessError(
            128, ["git", "tag", "-a", "v1.0"], stderr="error: tag 'v1.0' already exists"
        )
        commit_manager.git_repo.run_git_command.side_effect = subprocess_error

        with pytest.raises(SpecGitError) as exc_info:
            commit_manager.create_tag("v1.0", "Version 1.0")

        # Verify error uses utility formatting
        expected_formatted = handle_subprocess_error(subprocess_error)
        assert expected_formatted in str(exc_info.value)

        # Reset side effect for rollback test
        rollback_error = subprocess.CalledProcessError(
            1,
            ["git", "reset", "--hard", "abc123"],
            stderr="fatal: ambiguous argument 'abc123': unknown revision",
        )
        commit_manager.git_repo.run_git_command.side_effect = rollback_error

        # Mock commit exists validation to pass
        commit_manager._commit_exists = Mock(return_value=True)

        with pytest.raises(SpecGitError) as exc_info:
            commit_manager.rollback_to_commit("abc123")

        # Verify error uses utility formatting
        expected_formatted = handle_subprocess_error(rollback_error)
        assert expected_formatted in str(exc_info.value)

    def test_add_files_error_integration(self, commit_manager):
        """Test add_files method error integration."""
        # Create an OS error for file operations
        os_error = OSError(13, "Permission denied", "/specs/restricted.md")

        # To trigger the exception path, we need an exception at the top level
        # Mock the state_checker validation to raise an OSError
        commit_manager.state_checker.validate_pre_operation_state.side_effect = os_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError) as exc_info:
                commit_manager.add_files(["restricted.md"], force=True)

            # Verify error uses utility formatting
            expected_formatted = handle_os_error(os_error)
            assert expected_formatted in str(exc_info.value)

            # Verify context includes add-specific info
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Add operation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_add_files"
            assert "file_count" in call_kwargs
            assert call_kwargs["file_count"] == 1
            assert "force" in call_kwargs
            assert call_kwargs["force"] is True

    def test_tag_creation_error_integration(self, commit_manager):
        """Test tag creation error integration."""
        # Mock validation to pass
        commit_manager._validate_tag_name = Mock(return_value=[])
        commit_manager._tag_exists = Mock(return_value=False)

        # Create a subprocess error for tag creation
        subprocess_error = subprocess.CalledProcessError(
            128,
            ["git", "tag", "-a", "release-v1.0", "-m", "Release version 1.0"],
            stderr="fatal: tag 'release-v1.0' already exists",
        )
        commit_manager.git_repo.run_git_command.side_effect = subprocess_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError) as exc_info:
                commit_manager.create_tag(
                    "release-v1.0", "Release version 1.0", force=False
                )

            # Verify error uses utility formatting
            expected_formatted = handle_subprocess_error(subprocess_error)
            assert expected_formatted in str(exc_info.value)

            # Verify context includes tag-specific info
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Tag creation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_create_tag"
            assert "tag_name" in call_kwargs
            assert call_kwargs["tag_name"] == "release-v1.0"
            assert "force" in call_kwargs
            assert call_kwargs["force"] is False
            assert "has_message" in call_kwargs
            assert call_kwargs["has_message"] is True

    def test_rollback_error_integration(self, commit_manager):
        """Test rollback operation error integration."""
        # Mock validation to pass
        commit_manager._commit_exists = Mock(return_value=True)

        # Create a subprocess error for rollback
        subprocess_error = subprocess.CalledProcessError(
            1,
            ["git", "reset", "--hard", "abc123def"],
            stderr="fatal: Could not parse object 'abc123def'",
        )
        commit_manager.git_repo.run_git_command.side_effect = subprocess_error

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            with pytest.raises(SpecGitError) as exc_info:
                commit_manager.rollback_to_commit(
                    "abc123def", hard=True, create_backup=False
                )

            # Verify error uses utility formatting
            expected_formatted = handle_subprocess_error(subprocess_error)
            assert expected_formatted in str(exc_info.value)

            # Verify context includes rollback-specific info
            error_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "ERROR" and "Rollback operation failed" in call[0][1]
            ]
            assert len(error_calls) > 0

            call_kwargs = error_calls[0][1]
            assert "operation" in call_kwargs
            assert call_kwargs["operation"] == "commit_manager_rollback"
            assert "target_commit" in call_kwargs
            assert call_kwargs["target_commit"] == "abc123def"
            assert "hard" in call_kwargs
            assert call_kwargs["hard"] is True
            assert "create_backup" in call_kwargs
            assert call_kwargs["create_backup"] is False

    def test_error_utilities_integration_patterns(self, tmp_path):
        """Test that error utility integration patterns work correctly."""
        # Test error formatting with different error types
        errors_to_test = [
            OSError(13, "Permission denied", "/restricted/file"),
            OSError(28, "No space left on device", "/tmp/git"),
            subprocess.CalledProcessError(1, ["git", "commit"], "commit failed"),
            subprocess.CalledProcessError(
                128, ["git", "tag", "v1.0"], stderr="tag exists"
            ),
        ]

        for error in errors_to_test:
            if isinstance(error, OSError):
                formatted = handle_os_error(error)
                assert "Permission denied" in formatted or "No space left" in formatted
                assert f"errno {error.errno}" in formatted
                if error.filename:
                    assert error.filename in formatted
            elif hasattr(error, "cmd"):
                formatted = handle_subprocess_error(error)
                assert "Command failed" in formatted
                assert f"exit {error.returncode}" in formatted
                assert " ".join(error.cmd) in formatted

        # Test context creation
        test_path = tmp_path / "test_specs"
        test_path.mkdir()

        context = create_error_context(test_path)
        assert isinstance(context, dict)
        assert "file_path" in context
        assert "file_exists" in context
        assert "is_dir" in context
        assert context["is_dir"] is True
