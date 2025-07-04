"""Unit tests for SpecCommitManager validation logic - Micro-Agent Implementation.

This module tests the validation logic within SpecCommitManager, focusing on
add operation validation, commit operation validation, error handling,
and integration with repository state checking.

Slice: commit_001 - Commit Manager Unit Tests - Validation Logic
Coverage Target: 90%
Test Types: unit conflict_resolution validation
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.core.commit_manager import SpecCommitManager
from spec_cli.exceptions import SpecGitError
from spec_cli.utils.test_helpers.git_test_helpers import create_git_repository_mocker


class TestSpecCommitManagerValidation:
    """Test SpecCommitManager validation logic."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create mock settings
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

        # Mock all the dependencies during initialization
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    # Create commit manager with mocked dependencies
                    self.commit_manager = SpecCommitManager(self.mock_settings)

                    # Get the mock instances that were created
                    self.mock_git_repo = mock_repo_class.return_value
                    self.mock_state_checker = mock_checker_class.return_value

        # Create Git repository mocker for realistic Git simulation
        self.git_mocker = create_git_repository_mocker(Path("/tmp/test"))

    def test_validate_for_add_operation_success_when_no_issues(self):
        """Test _validate_for_add_operation returns no issues when validation passes."""
        # Arrange
        self.mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        issues = self.commit_manager._validate_for_add_operation()

        # Assert
        assert issues == []
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "add"
        )

    def test_validate_for_add_operation_returns_issues_when_validation_fails(self):
        """Test _validate_for_add_operation returns issues when validation fails."""
        # Arrange
        expected_issues = ["Repository not initialized", "Working directory dirty"]
        self.mock_state_checker.validate_pre_operation_state.return_value = (
            expected_issues
        )

        # Act
        issues = self.commit_manager._validate_for_add_operation()

        # Assert
        assert issues == expected_issues
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "add"
        )

    def test_validate_for_commit_operation_success_when_no_issues_and_staged_files_exist(
        self,
    ):
        """Test _validate_for_commit_operation success when validation passes and files staged."""
        # Arrange
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = ["test.txt", "other.md"]
        allow_empty = False

        # Act
        issues = self.commit_manager._validate_for_commit_operation(allow_empty)

        # Assert
        assert issues == []
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "commit"
        )
        self.mock_git_repo.get_staged_files.assert_called_once()

    def test_validate_for_commit_operation_fails_when_no_staged_files_and_not_allowing_empty(
        self,
    ):
        """Test _validate_for_commit_operation fails when no staged files and not allowing empty."""
        # Arrange
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = []
        allow_empty = False

        # Act
        issues = self.commit_manager._validate_for_commit_operation(allow_empty)

        # Assert
        assert "No staged files to commit" in issues
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "commit"
        )
        self.mock_git_repo.get_staged_files.assert_called_once()

    def test_validate_for_commit_operation_success_when_no_staged_files_but_allowing_empty(
        self,
    ):
        """Test _validate_for_commit_operation success when no staged files but allowing empty."""
        # Arrange
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        allow_empty = True

        # Act
        issues = self.commit_manager._validate_for_commit_operation(allow_empty)

        # Assert
        assert issues == []
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "commit"
        )
        # get_staged_files should not be called when allow_empty is True

    def test_validate_for_commit_operation_includes_pre_operation_validation_issues(
        self,
    ):
        """Test _validate_for_commit_operation includes pre-operation validation issues."""
        # Arrange
        pre_operation_issues = ["Repository corrupted", "Branch not clean"]
        self.mock_state_checker.validate_pre_operation_state.return_value = (
            pre_operation_issues
        )
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        allow_empty = False

        # Act
        issues = self.commit_manager._validate_for_commit_operation(allow_empty)

        # Assert
        assert issues == pre_operation_issues
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "commit"
        )
        self.mock_git_repo.get_staged_files.assert_called_once()

    def test_validate_for_commit_operation_handles_git_repo_exception_gracefully(self):
        """Test _validate_for_commit_operation handles Git repository exceptions."""
        # Arrange
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.side_effect = Exception(
            "Git command failed"
        )
        allow_empty = False

        # Act
        issues = self.commit_manager._validate_for_commit_operation(allow_empty)

        # Assert
        assert len(issues) == 1
        assert "Could not check staged files: Git command failed" in issues
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "commit"
        )
        self.mock_git_repo.get_staged_files.assert_called_once()


class TestSpecCommitManagerAddFiles:
    """Test SpecCommitManager add_files method validation logic."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

        # Mock all the dependencies during initialization
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    self.commit_manager = SpecCommitManager(self.mock_settings)

                    # Get the mock instances that were created
                    self.mock_git_repo = mock_repo_class.return_value
                    self.mock_state_checker = mock_checker_class.return_value

    def test_add_files_skips_validation_when_validate_false(self):
        """Test add_files skips validation when validate=False."""
        # Arrange
        file_paths = ["test.txt"]

        # Mock successful add operation
        with patch.object(self.commit_manager, "_add_single_file") as mock_add_single:
            mock_add_single.return_value = None

            # Act
            result = self.commit_manager.add_files(file_paths, validate=False)

            # Assert
            assert result["success"] is True
            assert result["added"] == []
            assert result["errors"] == []
            self.mock_state_checker.validate_pre_operation_state.assert_not_called()

    def test_add_files_performs_validation_when_validate_true(self):
        """Test add_files performs validation when validate=True."""
        # Arrange
        file_paths = ["test.txt"]
        self.mock_state_checker.validate_pre_operation_state.return_value = []

        # Mock successful add operation
        with patch.object(self.commit_manager, "_add_single_file") as mock_add_single:
            mock_add_single.return_value = None

            # Act
            result = self.commit_manager.add_files(file_paths, validate=True)

            # Assert
            assert result["success"] is True
            self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
                "add"
            )

    def test_add_files_returns_validation_errors_when_validation_fails(self):
        """Test add_files returns validation errors when validation fails."""
        # Arrange
        file_paths = ["test.txt"]
        validation_issues = ["Repository not initialized", "Conflicting operation"]
        self.mock_state_checker.validate_pre_operation_state.return_value = (
            validation_issues
        )

        # Act
        result = self.commit_manager.add_files(file_paths, validate=True)

        # Assert
        assert result["success"] is False
        assert result["errors"] == validation_issues
        assert result["added"] == []
        self.mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "add"
        )

    def test_add_files_processes_each_file_individually(self):
        """Test add_files processes each file individually through _add_single_file."""
        # Arrange
        file_paths = ["file1.txt", "file2.txt", "file3.txt"]
        self.mock_state_checker.validate_pre_operation_state.return_value = []

        with patch.object(self.commit_manager, "_add_single_file") as mock_add_single:
            mock_add_single.return_value = None

            # Act
            result = self.commit_manager.add_files(file_paths, validate=True)

            # Assert
            assert result["success"] is True
            assert mock_add_single.call_count == 3
            # Verify each file was processed
            calls = mock_add_single.call_args_list
            assert calls[0][0][0] == "file1.txt"
            assert calls[1][0][0] == "file2.txt"
            assert calls[2][0][0] == "file3.txt"

    def test_add_files_handles_individual_file_exceptions_gracefully(self):
        """Test add_files handles exceptions from individual file processing."""
        # Arrange
        file_paths = ["good_file.txt", "bad_file.txt", "another_good_file.txt"]
        self.mock_state_checker.validate_pre_operation_state.return_value = []

        def mock_add_single_file_side_effect(file_path, force, result):
            if file_path == "bad_file.txt":
                raise Exception("File processing error")
            # Don't modify result for successful files in this test

        with patch.object(self.commit_manager, "_add_single_file") as mock_add_single:
            mock_add_single.side_effect = mock_add_single_file_side_effect

            # Act
            result = self.commit_manager.add_files(file_paths, validate=True)

            # Assert
            assert result["success"] is False  # Should be false due to errors
            assert len(result["errors"]) == 1
            assert (
                "Failed to add bad_file.txt: File processing error" in result["errors"]
            )
            assert mock_add_single.call_count == 3  # All files should be attempted

    def test_add_files_success_determined_by_absence_of_errors(self):
        """Test add_files success is determined by absence of errors."""
        # Arrange
        file_paths = ["test.txt"]
        self.mock_state_checker.validate_pre_operation_state.return_value = []

        with patch.object(self.commit_manager, "_add_single_file") as mock_add_single:
            # Configure mock to add an error to the result
            def add_error(file_path, force, result):
                result["errors"].append("Simulated error")

            mock_add_single.side_effect = add_error

            # Act
            result = self.commit_manager.add_files(file_paths, validate=True)

            # Assert
            assert result["success"] is False
            assert "Simulated error" in result["errors"]


class TestSpecCommitManagerCommitChanges:
    """Test SpecCommitManager commit_changes method validation logic."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

        # Mock all the dependencies during initialization
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    self.commit_manager = SpecCommitManager(self.mock_settings)

                    # Get the mock instances that were created
                    self.mock_git_repo = mock_repo_class.return_value
                    self.mock_state_checker = mock_checker_class.return_value

    def test_commit_changes_skips_validation_when_validate_false(self):
        """Test commit_changes skips validation when validate=False."""
        # Arrange
        message = "Test commit"
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                result = self.commit_manager.commit_changes(message, validate=False)

                # Assert
                assert result["success"] is True
                self.mock_state_checker.validate_pre_operation_state.assert_not_called()

    def test_commit_changes_performs_validation_when_validate_true(self):
        """Test commit_changes performs validation when validate=True."""
        # Arrange
        message = "Test commit"
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                result = self.commit_manager.commit_changes(message, validate=True)

                # Assert
                assert result["success"] is True
                self.mock_state_checker.validate_pre_operation_state.assert_called()

    def test_commit_changes_returns_validation_errors_when_validation_fails(self):
        """Test commit_changes returns validation errors when validation fails."""
        # Arrange
        message = "Test commit"
        validation_issues = ["No staged files to commit", "Repository locked"]

        with patch.object(
            self.commit_manager, "_validate_for_commit_operation"
        ) as mock_validate:
            mock_validate.return_value = validation_issues

            # Act
            result = self.commit_manager.commit_changes(message, validate=True)

            # Assert
            assert result["success"] is False
            assert result["errors"] == validation_issues
            assert result["commit_hash"] is None
            mock_validate.assert_called_once_with(
                False
            )  # allow_empty defaults to False

    def test_commit_changes_passes_allow_empty_to_validation(self):
        """Test commit_changes passes allow_empty parameter to validation."""
        # Arrange
        message = "Test commit"
        allow_empty = True

        with patch.object(
            self.commit_manager, "_validate_for_commit_operation"
        ) as mock_validate:
            mock_validate.return_value = ["Validation failed"]

            # Act
            result = self.commit_manager.commit_changes(
                message, allow_empty=allow_empty, validate=True
            )

            # Assert
            assert result["success"] is False
            mock_validate.assert_called_once_with(True)  # allow_empty should be passed

    def test_commit_changes_formats_commit_message(self):
        """Test commit_changes formats commit message through _format_commit_message."""
        # Arrange
        original_message = "  Test commit with extra spaces  "
        formatted_message = "Test commit with extra spaces"
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = formatted_message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                self.commit_manager.commit_changes(original_message, validate=True)

                # Assert
                mock_format.assert_called_once_with(original_message)
                # Verify the formatted message was used in the git command
                git_command_calls = self.mock_git_repo.run_git_command.call_args_list
                commit_args = git_command_calls[0][0][
                    0
                ]  # First call, first positional arg
                assert formatted_message in commit_args

    def test_commit_changes_extracts_commit_hash_from_git_output(self):
        """Test commit_changes extracts commit hash from Git command output."""
        # Arrange
        message = "Test commit"
        expected_hash = "abc1234567"
        git_output = f"[main {expected_hash[:7]}] {message}"

        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        self.mock_git_repo.run_git_command.return_value = Mock(stdout=git_output)

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = expected_hash

                # Act
                result = self.commit_manager.commit_changes(message, validate=True)

                # Assert
                assert result["success"] is True
                assert result["commit_hash"] == expected_hash
                mock_extract.assert_called_once_with(git_output)

    def test_commit_changes_includes_author_in_git_command_when_provided(self):
        """Test commit_changes includes author in Git command when provided."""
        # Arrange
        message = "Test commit"
        author = "Test User <test@example.com>"

        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = ["test.txt"]
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                result = self.commit_manager.commit_changes(
                    message, author=author, validate=True
                )

                # Assert
                assert result["success"] is True
                # Verify author was included in git command
                git_command_calls = self.mock_git_repo.run_git_command.call_args_list
                commit_args = git_command_calls[0][0][0]
                assert "--author" in commit_args
                assert author in commit_args

    def test_commit_changes_includes_allow_empty_flag_when_true(self):
        """Test commit_changes includes --allow-empty flag when allow_empty=True."""
        # Arrange
        message = "Test commit"
        allow_empty = True

        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.return_value = []
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                result = self.commit_manager.commit_changes(
                    message, allow_empty=allow_empty, validate=True
                )

                # Assert
                assert result["success"] is True
                # Verify --allow-empty was included in git command
                git_command_calls = self.mock_git_repo.run_git_command.call_args_list
                commit_args = git_command_calls[0][0][0]
                assert "--allow-empty" in commit_args

    def test_commit_changes_handles_staged_files_exception_gracefully(self):
        """Test commit_changes handles get_staged_files exception gracefully."""
        # Arrange
        message = "Test commit"

        # Set up mock to first return empty list for validation, then throw exception for staging check
        validation_call_count = 0

        def mock_get_staged_files():
            nonlocal validation_call_count
            validation_call_count += 1
            if validation_call_count == 1:  # First call during validation
                return ["test.txt"]  # Return non-empty for validation
            else:  # Second call for getting files committed
                raise Exception("Git status failed")

        self.mock_state_checker.validate_pre_operation_state.return_value = []
        self.mock_git_repo.get_staged_files.side_effect = mock_get_staged_files
        self.mock_git_repo.run_git_command.return_value = Mock(
            stdout="[main abc1234] Test commit"
        )

        with patch.object(self.commit_manager, "_format_commit_message") as mock_format:
            mock_format.return_value = message
            with patch.object(
                self.commit_manager, "_extract_commit_hash"
            ) as mock_extract:
                mock_extract.return_value = "abc1234"

                # Act
                result = self.commit_manager.commit_changes(message, validate=True)

                # Assert
                assert result["success"] is True
                assert len(result["warnings"]) == 1
                assert (
                    "Could not get staged files: Git status failed"
                    in result["warnings"]
                )


class TestSpecCommitManagerErrorHandling:
    """Test SpecCommitManager error handling for OS and subprocess errors."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

        # Mock all the dependencies during initialization
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    self.commit_manager = SpecCommitManager(self.mock_settings)

                    # Get the mock instances that were created
                    self.mock_git_repo = mock_repo_class.return_value
                    self.mock_state_checker = mock_checker_class.return_value

    def test_add_files_handles_os_error_with_proper_context(self):
        """Test add_files handles OSError with proper error context."""
        # Arrange
        file_paths = ["test.txt"]
        os_error = OSError("Permission denied")

        with patch.object(
            self.commit_manager, "_validate_for_add_operation"
        ) as mock_validate:
            mock_validate.side_effect = os_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.add_files(file_paths, validate=True)

            assert "Add operation failed" in str(exc_info.value)

    def test_add_files_handles_subprocess_error_with_proper_context(self):
        """Test add_files handles subprocess error with proper error context."""
        # Arrange
        file_paths = ["test.txt"]
        subprocess_error = subprocess.CalledProcessError(1, "git", "Command failed")

        with patch.object(
            self.commit_manager, "_validate_for_add_operation"
        ) as mock_validate:
            mock_validate.side_effect = subprocess_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.add_files(file_paths, validate=True)

            assert "Add operation failed" in str(exc_info.value)

    def test_add_files_handles_generic_exception_with_basic_error_message(self):
        """Test add_files handles generic exceptions with basic error message."""
        # Arrange
        file_paths = ["test.txt"]
        generic_error = ValueError("Invalid input")

        with patch.object(
            self.commit_manager, "_validate_for_add_operation"
        ) as mock_validate:
            mock_validate.side_effect = generic_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.add_files(file_paths, validate=True)

            assert "Add operation failed: Invalid input" in str(exc_info.value)

    def test_commit_changes_handles_os_error_with_proper_context(self):
        """Test commit_changes handles OSError with proper error context."""
        # Arrange
        message = "Test commit"
        os_error = OSError("Disk full")

        with patch.object(
            self.commit_manager, "_validate_for_commit_operation"
        ) as mock_validate:
            mock_validate.side_effect = os_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.commit_changes(message, validate=True)

            assert "Commit operation failed" in str(exc_info.value)

    def test_commit_changes_handles_subprocess_error_with_proper_context(self):
        """Test commit_changes handles subprocess error with proper error context."""
        # Arrange
        message = "Test commit"
        subprocess_error = subprocess.CalledProcessError(128, "git", "Fatal error")

        with patch.object(
            self.commit_manager, "_validate_for_commit_operation"
        ) as mock_validate:
            mock_validate.side_effect = subprocess_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.commit_changes(message, validate=True)

            assert "Commit operation failed" in str(exc_info.value)

    def test_commit_changes_handles_generic_exception_with_basic_error_message(self):
        """Test commit_changes handles generic exceptions with basic error message."""
        # Arrange
        message = "Test commit"
        generic_error = RuntimeError("Unexpected error")

        with patch.object(
            self.commit_manager, "_validate_for_commit_operation"
        ) as mock_validate:
            mock_validate.side_effect = generic_error

            # Act & Assert
            with pytest.raises(SpecGitError) as exc_info:
                self.commit_manager.commit_changes(message, validate=True)

            assert "Commit operation failed: Unexpected error" in str(exc_info.value)


class TestSpecCommitManagerMessageAndHashUtilities:
    """Test SpecCommitManager message formatting and hash extraction utilities."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

        # Mock all the dependencies during initialization
        with patch("spec_cli.core.commit_manager.SpecGitRepository"):
            with patch("spec_cli.core.commit_manager.RepositoryStateChecker"):
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    self.commit_manager = SpecCommitManager(self.mock_settings)

    def test_format_commit_message_strips_whitespace(self):
        """Test _format_commit_message strips leading and trailing whitespace."""
        # Arrange
        message_with_whitespace = "  \n  Test commit message  \n  "

        # Act
        formatted = self.commit_manager._format_commit_message(message_with_whitespace)

        # Assert
        assert formatted == "Test commit message"

    def test_format_commit_message_preserves_internal_formatting(self):
        """Test _format_commit_message preserves internal line breaks and formatting."""
        # Arrange
        multiline_message = "First line\n\nSecond paragraph\nContinued line"

        # Act
        formatted = self.commit_manager._format_commit_message(multiline_message)

        # Assert
        assert formatted == multiline_message
        assert "\n\n" in formatted
        assert formatted.count("\n") == 3

    def test_format_commit_message_logs_warning_for_long_first_line(self):
        """Test _format_commit_message logs warning for long first line."""
        # Arrange
        long_message = "This is a very long commit message that exceeds the recommended 72 character limit for the first line"

        with patch("spec_cli.core.commit_manager.debug_logger") as mock_logger:
            # Act
            formatted = self.commit_manager._format_commit_message(long_message)

            # Assert
            assert formatted == long_message
            # Verify warning was logged
            mock_logger.log.assert_called()
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if len(call[0]) > 1 and call[0][0] == "WARNING"
            ]
            assert len(warning_calls) > 0

    def test_extract_commit_hash_finds_hash_in_square_brackets(self):
        """Test _extract_commit_hash extracts hash from square bracket format."""
        # Arrange
        git_output = "[main abc1234567] Initial commit"

        # Act
        hash_result = self.commit_manager._extract_commit_hash(git_output)

        # Assert
        assert hash_result == "abc1234567"

    def test_extract_commit_hash_finds_full_hash_pattern(self):
        """Test _extract_commit_hash extracts full 40-character hash."""
        # Arrange
        full_hash = "abc1234567890123456789012345678901234567"
        git_output = f"commit {full_hash}"

        # Act
        hash_result = self.commit_manager._extract_commit_hash(git_output)

        # Assert
        assert hash_result == full_hash

    def test_extract_commit_hash_returns_none_when_no_hash_found(self):
        """Test _extract_commit_hash returns None when no hash pattern found."""
        # Arrange
        git_output = "No commit hash in this output"

        # Act
        hash_result = self.commit_manager._extract_commit_hash(git_output)

        # Assert
        assert hash_result is None

    def test_extract_commit_hash_prefers_square_bracket_pattern(self):
        """Test _extract_commit_hash prefers square bracket pattern over full hash."""
        # Arrange
        short_hash = "abc1234"
        full_hash = "def5678901234567890123456789012345678901"
        git_output = f"[main {short_hash}] commit {full_hash}"

        # Act
        hash_result = self.commit_manager._extract_commit_hash(git_output)

        # Assert
        assert hash_result == short_hash  # Should prefer the square bracket format


class TestSpecCommitManagerIntegration:
    """Test integration between SpecCommitManager and its dependencies."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/tmp/test/.specs")
        self.mock_settings.spec_dir = Path("/tmp/test/.spec")

    def test_initialization_creates_proper_dependencies(self):
        """Test SpecCommitManager initialization creates proper dependency instances."""
        # Act
        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                mock_repo = Mock()
                mock_checker = Mock()
                mock_repo_class.return_value = mock_repo
                mock_checker_class.return_value = mock_checker

                commit_manager = SpecCommitManager(self.mock_settings)

                # Assert
                mock_repo_class.assert_called_once_with(self.mock_settings)
                mock_checker_class.assert_called_once_with(self.mock_settings)
                assert commit_manager.git_repo is mock_repo
                assert commit_manager.state_checker is mock_checker

    def test_initialization_uses_default_settings_when_none_provided(self):
        """Test SpecCommitManager uses default settings when none provided."""
        # Act
        with patch("spec_cli.core.commit_manager.get_settings") as mock_get_settings:
            with patch("spec_cli.core.commit_manager.SpecGitRepository"):
                with patch("spec_cli.core.commit_manager.RepositoryStateChecker"):
                    mock_default_settings = Mock()
                    mock_get_settings.return_value = mock_default_settings

                    commit_manager = SpecCommitManager()

                    # Assert
                    mock_get_settings.assert_called_once()
                    assert commit_manager.settings is mock_default_settings

    def test_integration_validation_flows_through_state_checker(self):
        """Test validation operations flow through RepositoryStateChecker correctly."""
        # Arrange
        # Mock settings with all required attributes
        self.mock_settings.index_file = Path("/tmp/test/.spec/index")
        self.mock_settings.global_config_file = Path("/tmp/test/global_config")
        self.mock_settings.system_config_file = Path("/tmp/test/system_config")

        with patch("spec_cli.core.commit_manager.SpecGitRepository") as mock_repo_class:
            with patch(
                "spec_cli.core.commit_manager.RepositoryStateChecker"
            ) as mock_checker_class:
                with patch("spec_cli.core.commit_manager.debug_logger"):
                    commit_manager = SpecCommitManager(self.mock_settings)

                    mock_state_checker = mock_checker_class.return_value
                    mock_git_repo = mock_repo_class.return_value

                    # Return fresh list each time to avoid mutation issues
                    mock_state_checker.validate_pre_operation_state.side_effect = (
                        lambda op: ["Validation error"]
                    )
                    mock_git_repo.get_staged_files.return_value = []

                    # Act
                    add_issues = commit_manager._validate_for_add_operation()
                    commit_issues = commit_manager._validate_for_commit_operation(False)

                    # Assert
                    assert add_issues == ["Validation error"]
                    assert "Validation error" in commit_issues
                    assert (
                        "No staged files to commit" in commit_issues
                    )  # Should also include staging validation
                    assert (
                        len(commit_issues) == 2
                    )  # Should have both validation error and staging error
                    mock_state_checker.validate_pre_operation_state.assert_any_call(
                        "add"
                    )
                    mock_state_checker.validate_pre_operation_state.assert_any_call(
                        "commit"
                    )
