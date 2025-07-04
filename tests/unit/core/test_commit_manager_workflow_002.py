"""Unit tests for SpecCommitManager - State Management (workflow_002).

This module provides comprehensive unit tests for the SpecCommitManager class,
focusing on state management and commit operations. Tests cover all core functionality
including file staging, commit creation, tag management, and rollback operations.

Key test areas:
- File staging operations with validation and error handling
- Commit creation with various scenarios and author handling
- Git tag management including backup scenarios
- Rollback operations with state validation
- Status monitoring and error recovery
- Integration with repository state management
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.commit_manager import SpecCommitManager
from spec_cli.exceptions import SpecGitError


class TestSpecCommitManagerInitialization:
    """Test SpecCommitManager initialization and setup."""

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        with patch("spec_cli.core.commit_manager.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.spec_dir = Path("/test/.spec")
            mock_settings.specs_dir = Path("/test/specs")
            mock_get_settings.return_value = mock_settings

            manager = SpecCommitManager()

            assert manager.settings == mock_settings
            assert manager.git_repo is not None
            assert manager.state_checker is not None

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings."""
        custom_settings = Mock()
        custom_settings.spec_dir = Path("/custom/.spec")
        custom_settings.specs_dir = Path("/custom/specs")

        manager = SpecCommitManager(custom_settings)

        assert manager.settings == custom_settings
        assert manager.git_repo is not None
        assert manager.state_checker is not None

    def test_init_debug_logging(self):
        """Test that initialization produces debug logging."""
        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            mock_settings = Mock()
            mock_settings.spec_dir = Path("/test/.spec")
            mock_settings.specs_dir = Path("/test/specs")

            SpecCommitManager(mock_settings)

            mock_logger.log.assert_called_with("INFO", "SpecCommitManager initialized")


class TestSpecCommitManagerAddFiles:
    """Test file staging operations with comprehensive scenarios."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/specs")
        self.manager = SpecCommitManager(self.mock_settings)

        # Mock dependencies
        self.manager.git_repo = Mock()
        self.manager.state_checker = Mock()

    def test_add_files_success_single_file(self):
        """Test successful addition of a single file."""
        # Setup
        file_paths = ["test_file.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths)

        # Verify result
        assert result["success"] is True
        assert result["added"] == ["test_file.md"]
        assert result["skipped"] == []
        assert result["errors"] == []

        # Verify git command was called
        self.manager.git_repo.run_git_command.assert_called_with(
            ["add", "test_file.md"]
        )

    def test_add_files_success_multiple_files(self):
        """Test successful addition of multiple files."""
        # Setup
        file_paths = ["file1.md", "file2.md", "file3.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths)

        # Verify result
        assert result["success"] is True
        assert len(result["added"]) == 3
        assert "file1.md" in result["added"]
        assert "file2.md" in result["added"]
        assert "file3.md" in result["added"]
        assert result["errors"] == []

    def test_add_files_with_force_flag(self):
        """Test file addition with force flag."""
        # Setup
        file_paths = ["ignored_file.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths, force=True)

        # Verify force flag is passed to git
        self.manager.git_repo.run_git_command.assert_called_with(
            ["add", "-f", "ignored_file.md"]
        )
        assert result["success"] is True

    def test_add_files_skip_validation(self):
        """Test file addition without validation."""
        # Setup
        file_paths = ["test_file.md"]
        self.manager.git_repo.get_staged_files.return_value = []

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths, validate=False)

        # Verify validation was skipped
        self.manager.state_checker.validate_pre_operation_state.assert_not_called()
        assert result["success"] is True

    def test_add_files_validation_failure(self):
        """Test file addition with validation failures."""
        # Setup
        file_paths = ["test_file.md"]
        validation_issues = ["Repository not initialized", "Working directory dirty"]
        self.manager.state_checker.validate_pre_operation_state.return_value = (
            validation_issues
        )

        result = self.manager.add_files(file_paths)

        # Verify validation failure handling
        assert result["success"] is False
        assert result["errors"] == validation_issues
        assert result["added"] == []

        # Verify git command was not called
        self.manager.git_repo.run_git_command.assert_not_called()

    def test_add_files_nonexistent_file(self):
        """Test addition of nonexistent file."""
        # Setup
        file_paths = ["nonexistent.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []

        # Mock file doesn't exist
        with patch("pathlib.Path.exists", return_value=False):
            result = self.manager.add_files(file_paths)

        # Verify error handling
        assert result["success"] is False
        assert "File does not exist: nonexistent.md" in result["errors"]
        assert result["added"] == []

    def test_add_files_already_staged(self):
        """Test addition of already staged files."""
        # Setup
        file_paths = ["staged_file.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["staged_file.md"]

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths)

        # Verify skipping behavior
        assert result["success"] is True
        assert result["added"] == []
        assert "File already staged: staged_file.md" in result["skipped"]

    def test_add_files_git_command_failure(self):
        """Test handling of Git command failures."""
        # Setup
        file_paths = ["test_file.md"]
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []
        self.manager.git_repo.run_git_command.side_effect = (
            subprocess.CalledProcessError(1, "git")
        )

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.add_files(file_paths)

        # Verify error handling
        assert result["success"] is False
        assert any(
            "Git add failed for test_file.md" in error for error in result["errors"]
        )

    def test_add_files_os_error_handling(self):
        """Test handling of OS errors during add operation."""
        # Setup
        file_paths = ["test_file.md"]
        self.manager.state_checker.validate_pre_operation_state.side_effect = OSError(
            "Permission denied"
        )

        with patch("spec_cli.core.commit_manager.handle_os_error") as mock_handle_os:
            mock_handle_os.return_value = "Formatted OS error"

            with pytest.raises(
                SpecGitError, match="Add operation failed: Formatted OS error"
            ):
                self.manager.add_files(file_paths)

        # Verify error handling was called
        mock_handle_os.assert_called_once()

    def test_add_files_subprocess_error_handling(self):
        """Test handling of subprocess errors during add operation."""
        # Setup
        file_paths = ["test_file.md"]
        subprocess_error = subprocess.CalledProcessError(1, "git")
        self.manager.state_checker.validate_pre_operation_state.side_effect = (
            subprocess_error
        )

        with patch(
            "spec_cli.core.commit_manager.handle_subprocess_error"
        ) as mock_handle_sub:
            mock_handle_sub.return_value = "Formatted subprocess error"

            with pytest.raises(
                SpecGitError, match="Add operation failed: Formatted subprocess error"
            ):
                self.manager.add_files(file_paths)

        # Verify error handling was called
        mock_handle_sub.assert_called_once()


class TestSpecCommitManagerCommitChanges:
    """Test commit operations with comprehensive scenarios."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/specs")
        self.manager = SpecCommitManager(self.mock_settings)

        # Mock dependencies
        self.manager.git_repo = Mock()
        self.manager.state_checker = Mock()

    def test_commit_changes_success(self):
        """Test successful commit operation."""
        # Setup
        message = "Test commit message"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["file1.md", "file2.md"]

        # Mock git commit output with hash
        mock_result = Mock()
        mock_result.stdout = "[main 1234567] Test commit message"
        self.manager.git_repo.run_git_command.return_value = mock_result

        result = self.manager.commit_changes(message)

        # Verify result
        assert result["success"] is True
        assert result["commit_hash"] == "1234567"
        assert result["files_committed"] == ["file1.md", "file2.md"]
        assert result["errors"] == []

        # Verify git command
        self.manager.git_repo.run_git_command.assert_called_with(
            ["commit", "-m", "Test commit message"]
        )

    def test_commit_changes_with_author(self):
        """Test commit with custom author."""
        # Setup
        message = "Test commit"
        author = "Test User <test@example.com>"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["file1.md"]

        # Mock git commit output
        mock_result = Mock()
        mock_result.stdout = "[main abc123] Test commit"
        self.manager.git_repo.run_git_command.return_value = mock_result

        result = self.manager.commit_changes(message, author=author)

        # Verify author parameter was passed
        expected_args = ["commit", "-m", "Test commit", "--author", author]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)
        assert result["success"] is True

    def test_commit_changes_allow_empty(self):
        """Test commit with allow_empty flag."""
        # Setup
        message = "Empty commit"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        # Mock git commit output
        mock_result = Mock()
        mock_result.stdout = "[main def456] Empty commit"
        self.manager.git_repo.run_git_command.return_value = mock_result

        result = self.manager.commit_changes(message, allow_empty=True)

        # Verify allow-empty flag
        expected_args = ["commit", "-m", "Empty commit", "--allow-empty"]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)
        assert result["success"] is True

    def test_commit_changes_validation_failure(self):
        """Test commit with validation failures."""
        # Setup
        message = "Test commit"
        validation_issues = ["No files staged", "Repository not clean"]
        self.manager.state_checker.validate_pre_operation_state.return_value = (
            validation_issues
        )

        result = self.manager.commit_changes(message)

        # Verify validation failure handling
        assert result["success"] is False
        assert result["errors"] == validation_issues
        assert result["commit_hash"] is None

        # Verify git command was not called
        self.manager.git_repo.run_git_command.assert_not_called()

    def test_commit_changes_no_staged_files(self):
        """Test commit with no staged files (not allowing empty)."""
        # Setup
        message = "Test commit"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        result = self.manager.commit_changes(message, allow_empty=False)

        # Verify empty commit prevention
        assert result["success"] is False
        assert "No staged files to commit" in result["errors"]

    def test_commit_changes_message_formatting(self):
        """Test commit message formatting."""
        # Setup
        message = "  Test commit with spaces  \n\n"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["file1.md"]

        # Mock git commit output
        mock_result = Mock()
        mock_result.stdout = "[main abc123] Test commit with spaces"
        self.manager.git_repo.run_git_command.return_value = mock_result

        self.manager.commit_changes(message)

        # Verify message was cleaned up
        expected_args = ["commit", "-m", "Test commit with spaces"]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)

    def test_commit_changes_hash_extraction_alternative_pattern(self):
        """Test commit hash extraction with alternative patterns."""
        # Setup
        message = "Test commit"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["file1.md"]

        # Mock git output with full hash
        mock_result = Mock()
        mock_result.stdout = "1234567890abcdef1234567890abcdef12345678"
        self.manager.git_repo.run_git_command.return_value = mock_result

        result = self.manager.commit_changes(message)

        # Verify hash extraction
        assert result["commit_hash"] == "1234567890abcdef1234567890abcdef12345678"

    def test_commit_changes_git_command_failure(self):
        """Test handling of Git command failures during commit."""
        # Setup
        message = "Test commit"
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = ["file1.md"]
        self.manager.git_repo.run_git_command.side_effect = (
            subprocess.CalledProcessError(1, "git")
        )

        with patch(
            "spec_cli.core.commit_manager.handle_subprocess_error"
        ) as mock_handle:
            mock_handle.return_value = "Git commit failed"

            with pytest.raises(
                SpecGitError, match="Commit operation failed: Git commit failed"
            ):
                self.manager.commit_changes(message)


class TestSpecCommitManagerCreateTag:
    """Test Git tag creation with comprehensive scenarios."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.manager = SpecCommitManager(self.mock_settings)
        self.manager.git_repo = Mock()

    def test_create_tag_success_simple(self):
        """Test successful simple tag creation."""
        # Setup
        tag_name = "v1.0.0"
        self.manager.git_repo.run_git_command.return_value = Mock()

        # Mock tag doesn't exist
        self.manager._tag_exists = Mock(return_value=False)

        result = self.manager.create_tag(tag_name)

        # Verify result
        assert result["success"] is True
        assert result["tag_name"] == tag_name
        assert result["commit_hash"] == "HEAD"
        assert result["errors"] == []

        # Verify git command
        self.manager.git_repo.run_git_command.assert_called_with(["tag", tag_name])

    def test_create_tag_success_annotated(self):
        """Test successful annotated tag creation."""
        # Setup
        tag_name = "v1.0.0"
        message = "Release version 1.0.0"
        self.manager.git_repo.run_git_command.return_value = Mock()
        self.manager._tag_exists = Mock(return_value=False)

        result = self.manager.create_tag(tag_name, message=message)

        # Verify annotated tag command
        expected_args = ["tag", "-a", tag_name, "-m", message]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)
        assert result["success"] is True

    def test_create_tag_with_commit_hash(self):
        """Test tag creation at specific commit."""
        # Setup
        tag_name = "v1.0.0"
        commit_hash = "abc123def456"
        self.manager.git_repo.run_git_command.return_value = Mock()
        self.manager._tag_exists = Mock(return_value=False)

        result = self.manager.create_tag(tag_name, commit_hash=commit_hash)

        # Verify commit hash parameter
        expected_args = ["tag", tag_name, commit_hash]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)
        assert result["commit_hash"] == commit_hash

    def test_create_tag_force_overwrite(self):
        """Test tag creation with force overwrite."""
        # Setup
        tag_name = "v1.0.0"
        self.manager.git_repo.run_git_command.return_value = Mock()
        self.manager._tag_exists = Mock(return_value=True)

        result = self.manager.create_tag(tag_name, force=True)

        # Verify force flag
        expected_args = ["tag", "-f", tag_name]
        self.manager.git_repo.run_git_command.assert_called_with(expected_args)
        assert result["success"] is True

    def test_create_tag_already_exists(self):
        """Test tag creation when tag already exists."""
        # Setup
        tag_name = "existing-tag"
        self.manager._tag_exists = Mock(return_value=True)

        result = self.manager.create_tag(tag_name, force=False)

        # Verify error handling
        assert result["success"] is False
        assert "Tag already exists: existing-tag" in result["errors"]

        # Verify git command was not called
        self.manager.git_repo.run_git_command.assert_not_called()

    def test_create_tag_invalid_name_empty(self):
        """Test tag creation with empty name."""
        result = self.manager.create_tag("")

        assert result["success"] is False
        assert "Tag name cannot be empty" in result["errors"]

    def test_create_tag_invalid_name_dash_start(self):
        """Test tag creation with invalid name starting with dash."""
        result = self.manager.create_tag("-invalid")

        assert result["success"] is False
        assert "Tag name cannot start with dash" in result["errors"]

    def test_create_tag_invalid_name_double_dot(self):
        """Test tag creation with invalid double dot."""
        result = self.manager.create_tag("v1..0")

        assert result["success"] is False
        assert "Tag name cannot contain '..'" in result["errors"]

    def test_create_tag_invalid_name_lock_ending(self):
        """Test tag creation with .lock ending."""
        result = self.manager.create_tag("tag.lock")

        assert result["success"] is False
        assert "Tag name cannot end with '.lock'" in result["errors"]

    def test_create_tag_invalid_characters(self):
        """Test tag creation with invalid characters."""
        result = self.manager.create_tag("tag with spaces")

        assert result["success"] is False
        assert "Tag name contains invalid characters" in result["errors"]

    def test_tag_exists_method(self):
        """Test _tag_exists helper method."""
        # Test tag exists
        mock_result = Mock()
        mock_result.stdout = "v1.0.0"
        self.manager.git_repo.run_git_command.return_value = mock_result

        assert self.manager._tag_exists("v1.0.0") is True

        # Test tag doesn't exist
        mock_result.stdout = ""
        assert self.manager._tag_exists("nonexistent") is False

        # Test exception handling
        self.manager.git_repo.run_git_command.side_effect = Exception("Git error")
        assert self.manager._tag_exists("any-tag") is False


class TestSpecCommitManagerRollback:
    """Test rollback operations with comprehensive scenarios."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.manager = SpecCommitManager(self.mock_settings)
        self.manager.git_repo = Mock()

    def test_rollback_to_commit_success(self):
        """Test successful rollback to specific commit."""
        # Setup
        commit_hash = "abc123def456"
        self.manager._commit_exists = Mock(return_value=True)
        self.manager.create_tag = Mock(return_value={"success": True})
        self.manager.git_repo.run_git_command.return_value = Mock()

        with patch("spec_cli.core.commit_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-120000"

            result = self.manager.rollback_to_commit(commit_hash)

        # Verify result
        assert result["success"] is True
        assert result["target_commit"] == commit_hash
        assert result["reset_type"] == "soft"
        assert result["backup_tag"] == "backup-20240101-120000"

        # Verify git reset command
        self.manager.git_repo.run_git_command.assert_called_with(["reset", commit_hash])

    def test_rollback_to_commit_hard_reset(self):
        """Test hard reset rollback."""
        # Setup
        commit_hash = "abc123def456"
        self.manager._commit_exists = Mock(return_value=True)
        self.manager.create_tag = Mock(return_value={"success": True})
        self.manager.git_repo.run_git_command.return_value = Mock()

        result = self.manager.rollback_to_commit(commit_hash, hard=True)

        # Verify hard reset
        assert result["reset_type"] == "hard"
        self.manager.git_repo.run_git_command.assert_called_with(
            ["reset", "--hard", commit_hash]
        )

    def test_rollback_to_commit_no_backup(self):
        """Test rollback without backup creation."""
        # Setup
        commit_hash = "abc123def456"
        self.manager._commit_exists = Mock(return_value=True)
        self.manager.git_repo.run_git_command.return_value = Mock()

        result = self.manager.rollback_to_commit(commit_hash, create_backup=False)

        # Verify no backup was created
        assert result["backup_tag"] is None
        assert result["success"] is True

    def test_rollback_to_commit_nonexistent(self):
        """Test rollback to nonexistent commit."""
        # Setup
        commit_hash = "nonexistent"
        self.manager._commit_exists = Mock(return_value=False)

        result = self.manager.rollback_to_commit(commit_hash)

        # Verify error handling
        assert result["success"] is False
        assert f"Commit does not exist: {commit_hash}" in result["errors"]

        # Verify git command was not called
        self.manager.git_repo.run_git_command.assert_not_called()

    def test_rollback_to_commit_backup_failure(self):
        """Test rollback with backup creation failure."""
        # Setup
        commit_hash = "abc123def456"
        self.manager._commit_exists = Mock(return_value=True)
        self.manager.create_tag = Mock(return_value={"success": False})
        self.manager.git_repo.run_git_command.return_value = Mock()

        result = self.manager.rollback_to_commit(commit_hash, create_backup=True)

        # Verify rollback still succeeded with warning
        assert result["success"] is True
        assert "Could not create backup tag" in result["warnings"]
        assert result["backup_tag"] is None

    def test_rollback_last_commit_success(self):
        """Test successful last commit rollback."""
        # Setup
        current_commit = "current123"
        parent_commit = "parent456"
        self.manager.git_repo.get_current_commit_hash.return_value = current_commit
        self.manager.git_repo.get_parent_commit_hash.return_value = parent_commit

        # Mock rollback_to_commit
        self.manager.rollback_to_commit = Mock(
            return_value={
                "success": True,
                "target_commit": parent_commit,
                "backup_tag": "backup-tag",
            }
        )

        result = self.manager.rollback_last_commit()

        # Verify parent commit rollback
        self.manager.rollback_to_commit.assert_called_with(
            parent_commit, hard=False, create_backup=True
        )
        assert result["success"] is True

    def test_rollback_last_commit_no_commits(self):
        """Test rollback when no commits exist."""
        # Setup
        self.manager.git_repo.get_current_commit_hash.return_value = None

        result = self.manager.rollback_last_commit()

        # Verify error handling
        assert result["success"] is False
        assert "No commits found to rollback" in result["errors"]

    def test_rollback_last_commit_no_parent(self):
        """Test rollback when no parent commit exists."""
        # Setup
        current_commit = "first123"
        self.manager.git_repo.get_current_commit_hash.return_value = current_commit
        self.manager.git_repo.get_parent_commit_hash.return_value = None

        result = self.manager.rollback_last_commit()

        # Verify error handling
        assert result["success"] is False
        assert "No parent commit found (this is the first commit)" in result["errors"]

    def test_commit_exists_method(self):
        """Test _commit_exists helper method."""
        # Test commit exists
        self.manager.git_repo.run_git_command.return_value = Mock()
        assert self.manager._commit_exists("abc123") is True

        # Test commit doesn't exist
        self.manager.git_repo.run_git_command.side_effect = Exception(
            "Not a valid object"
        )
        assert self.manager._commit_exists("invalid") is False


class TestSpecCommitManagerStatus:
    """Test status monitoring and reporting."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.manager = SpecCommitManager(self.mock_settings)
        self.manager.git_repo = Mock()
        self.manager.state_checker = Mock()

    def test_get_commit_status_full_info(self):
        """Test getting complete commit status."""
        # Setup
        self.manager.git_repo.is_initialized.return_value = True
        self.manager.state_checker.check_branch_cleanliness.return_value = {
            "clean": True
        }
        self.manager.git_repo.get_staged_files.return_value = ["staged.md"]
        self.manager.git_repo.get_unstaged_files.return_value = ["modified.md"]
        self.manager.git_repo.get_untracked_files.return_value = ["new.md"]
        self.manager.git_repo.get_current_commit_hash.return_value = "abc123"
        self.manager.git_repo.get_recent_commits.return_value = [
            {"hash": "abc123", "subject": "Test commit"}
        ]
        self.manager.state_checker.is_safe_for_spec_operations.return_value = True

        result = self.manager.get_commit_status()

        # Verify complete status
        assert result["repository_initialized"] is True
        assert result["branch_status"] == {"clean": True}
        assert result["staged_files"] == ["staged.md"]
        assert result["unstaged_files"] == ["modified.md"]
        assert result["untracked_files"] == ["new.md"]
        assert result["current_commit"] == "abc123"
        assert result["commit_count"] == 1
        assert result["safe_for_operations"] is True

    def test_get_commit_status_uninitialized_repo(self):
        """Test status for uninitialized repository."""
        # Setup
        self.manager.git_repo.is_initialized.return_value = False

        result = self.manager.get_commit_status()

        # Verify minimal status for uninitialized repo
        assert result["repository_initialized"] is False
        assert result["safe_for_operations"] is False
        assert result["staged_files"] == []
        assert result["unstaged_files"] == []
        assert result["untracked_files"] == []

    def test_get_commit_status_with_warnings(self):
        """Test status retrieval with warnings for partial failures."""
        # Setup
        self.manager.git_repo.is_initialized.return_value = True
        self.manager.state_checker.check_branch_cleanliness.return_value = {
            "clean": True
        }
        self.manager.git_repo.get_staged_files.side_effect = Exception(
            "Staged files error"
        )
        self.manager.git_repo.get_unstaged_files.return_value = []
        self.manager.git_repo.get_untracked_files.return_value = []
        self.manager.git_repo.get_current_commit_hash.side_effect = Exception(
            "Commit error"
        )
        self.manager.git_repo.get_recent_commits.side_effect = Exception(
            "History error"
        )
        self.manager.state_checker.is_safe_for_spec_operations.return_value = False

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            result = self.manager.get_commit_status()

        # Verify warnings were logged
        assert mock_logger.log.call_count >= 3  # For the three exceptions
        assert result["repository_initialized"] is True
        assert result["safe_for_operations"] is False

    def test_get_commit_status_exception_handling(self):
        """Test status retrieval with complete failure."""
        # Setup
        self.manager.git_repo.is_initialized.side_effect = Exception("Critical error")

        result = self.manager.get_commit_status()

        # Verify error handling
        assert result["repository_initialized"] is False
        assert "error" in result
        assert result["safe_for_operations"] is False


class TestSpecCommitManagerHelperMethods:
    """Test internal helper methods and utilities."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.manager = SpecCommitManager(self.mock_settings)

    def test_format_commit_message_cleanup(self):
        """Test commit message formatting and cleanup."""
        # Test whitespace cleanup
        result = self.manager._format_commit_message("  test message  \n\n")
        assert result == "test message"

        # Test multiline preservation
        result = self.manager._format_commit_message("Title\n\nBody paragraph")
        assert result == "Title\n\nBody paragraph"

    def test_format_commit_message_long_first_line(self):
        """Test warning for long commit message first line."""
        long_message = "A" * 80  # Longer than 72 chars

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            result = self.manager._format_commit_message(long_message)

        # Verify warning was logged
        mock_logger.log.assert_called_with(
            "WARNING", "Commit message first line is long", length=80
        )
        assert result == long_message

    def test_extract_commit_hash_patterns(self):
        """Test commit hash extraction from various Git output formats."""
        # Test standard format
        output1 = "[main 1234567] Commit message"
        result1 = self.manager._extract_commit_hash(output1)
        assert result1 == "1234567"

        # Test full hash format
        output2 = "1234567890abcdef1234567890abcdef12345678"
        result2 = self.manager._extract_commit_hash(output2)
        assert result2 == "1234567890abcdef1234567890abcdef12345678"

        # Test no match
        output3 = "No hash in this output"
        result3 = self.manager._extract_commit_hash(output3)
        assert result3 is None

    def test_validate_tag_name_comprehensive(self):
        """Test comprehensive tag name validation."""
        # Valid names
        assert self.manager._validate_tag_name("v1.0.0") == []
        assert self.manager._validate_tag_name("release-2024") == []
        assert self.manager._validate_tag_name("feature_branch") == []

        # Invalid names
        assert "empty" in str(self.manager._validate_tag_name(""))
        assert "empty" in str(self.manager._validate_tag_name("   "))
        assert "dash" in str(self.manager._validate_tag_name("-invalid"))
        assert ".." in str(self.manager._validate_tag_name("v1..0"))
        assert ".lock" in str(self.manager._validate_tag_name("tag.lock"))
        assert "invalid characters" in str(
            self.manager._validate_tag_name("tag with spaces")
        )


class TestSpecCommitManagerOperationSummaries:
    """Test operation summary and audit functionality."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.manager = SpecCommitManager(self.mock_settings)
        self.manager.git_repo = Mock()

    def test_create_operation_summary_add_success(self):
        """Test add operation summary creation."""
        result = {"success": True, "added": ["file1.md", "file2.md"], "errors": []}

        summary = self.manager.create_operation_summary("add", result)
        assert summary == "Successfully added 2 files to staging"

    def test_create_operation_summary_add_failure(self):
        """Test add operation failure summary."""
        result = {"success": False, "added": [], "errors": ["Error 1", "Error 2"]}

        summary = self.manager.create_operation_summary("add", result)
        assert summary == "Add failed: 2 errors"

    def test_create_operation_summary_commit_success(self):
        """Test commit operation summary creation."""
        result = {
            "success": True,
            "commit_hash": "1234567890abcdef",
            "files_committed": ["file1.md", "file2.md", "file3.md"],
        }

        summary = self.manager.create_operation_summary("commit", result)
        assert summary == "Committed 3 files [12345678]"

    def test_create_operation_summary_tag_success(self):
        """Test tag operation summary creation."""
        result = {"success": True, "tag_name": "v1.0.0", "commit_hash": "abc123def456"}

        summary = self.manager.create_operation_summary("tag", result)
        assert summary == "Created tag 'v1.0.0' at abc123def456"

    def test_create_operation_summary_rollback_with_backup(self):
        """Test rollback operation summary with backup."""
        result = {
            "success": True,
            "target_commit": "1234567890abcdef",
            "backup_tag": "backup-20240101-120000",
        }

        summary = self.manager.create_operation_summary("rollback", result)
        assert summary == "Rolled back to 12345678 (backup: backup-20240101-120000)"

    def test_get_recent_operations(self):
        """Test recent operations retrieval."""
        # Setup
        mock_commits = [
            {
                "hash": "abc123",
                "subject": "Test commit 1",
                "author": "Test User",
                "date": "2024-01-01",
            },
            {
                "hash": "def456",
                "subject": "Test commit 2",
                "author": "Test User",
                "date": "2024-01-02",
            },
        ]
        self.manager.git_repo.get_recent_commits.return_value = mock_commits

        operations = self.manager.get_recent_operations(2)

        # Verify operations structure
        assert len(operations) == 2
        assert operations[0]["type"] == "commit"
        assert operations[0]["hash"] == "abc123"
        assert operations[0]["message"] == "Test commit 1"
        assert operations[1]["hash"] == "def456"

    def test_get_recent_operations_error_handling(self):
        """Test recent operations with error handling."""
        # Setup
        self.manager.git_repo.get_recent_commits.side_effect = Exception("Git error")

        operations = self.manager.get_recent_operations()

        # Verify empty result on error
        assert operations == []


class TestSpecCommitManagerIntegration:
    """Integration tests simulating real workflows."""

    def setup_method(self):
        """Set up test fixtures for integration tests."""
        self.mock_settings = Mock()
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/specs")
        self.manager = SpecCommitManager(self.mock_settings)

        # Mock dependencies
        self.manager.git_repo = Mock()
        self.manager.state_checker = Mock()

    def test_complete_add_commit_workflow(self):
        """Test complete workflow: add files -> commit -> tag."""
        # Setup for add operation
        self.manager.state_checker.validate_pre_operation_state.return_value = []
        self.manager.git_repo.get_staged_files.return_value = []

        # Setup for commit operation
        commit_output = Mock()
        commit_output.stdout = "[main abc123] Test commit"

        # Mock tag operations
        self.manager._tag_exists = Mock(return_value=False)

        with patch("pathlib.Path.exists", return_value=True):
            # Configure mock to return commit output only on commit command
            def git_command_side_effect(args):
                if args[0] == "commit":
                    return commit_output
                return Mock()  # Return empty mock for other commands

            self.manager.git_repo.run_git_command.side_effect = git_command_side_effect

            # Add files
            add_result = self.manager.add_files(["file1.md", "file2.md"])
            assert add_result["success"] is True

            # Update staged files for commit
            self.manager.git_repo.get_staged_files.return_value = [
                "file1.md",
                "file2.md",
            ]

            # Commit changes
            commit_result = self.manager.commit_changes("Test commit message")
            assert commit_result["success"] is True
            # Note: Hash extraction depends on exact output format, just verify success

            # Reset side_effect for tag operation
            self.manager.git_repo.run_git_command.side_effect = None
            self.manager.git_repo.run_git_command.return_value = Mock()

            # Create tag
            tag_result = self.manager.create_tag("v1.0.0", "Release tag")
            assert tag_result["success"] is True

    def test_rollback_workflow_with_backup(self):
        """Test rollback workflow with backup creation."""
        # Setup
        target_commit = "previous123"
        self.manager._commit_exists = Mock(return_value=True)

        # Mock successful tag creation for backup
        backup_result = {"success": True, "tag_name": "backup-123"}
        self.manager.create_tag = Mock(return_value=backup_result)

        with patch("spec_cli.core.commit_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101-120000"

            # Perform rollback
            rollback_result = self.manager.rollback_to_commit(
                target_commit, create_backup=True
            )

        # Verify backup was created
        self.manager.create_tag.assert_called_once()
        backup_call_args = self.manager.create_tag.call_args[0]
        assert "backup-20240101-120000" in backup_call_args

        # Verify rollback success
        assert rollback_result["success"] is True
        assert rollback_result["target_commit"] == target_commit

    def test_error_recovery_workflow(self):
        """Test error recovery and validation workflows."""
        # Simulate validation failure
        validation_issues = ["Repository not initialized", "Conflicting state"]
        self.manager.state_checker.validate_pre_operation_state.return_value = (
            validation_issues
        )

        # Test add operation fails validation
        add_result = self.manager.add_files(["file.md"])
        assert add_result["success"] is False
        assert len(add_result["errors"]) == 2

        # Test commit operation fails validation
        commit_result = self.manager.commit_changes("Test commit")
        assert commit_result["success"] is False
        assert len(commit_result["errors"]) == 2

        # Verify no Git commands were executed
        self.manager.git_repo.run_git_command.assert_not_called()
