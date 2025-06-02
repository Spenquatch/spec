"""Tests for SpecCommitManager functionality."""

from typing import cast
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.commit_manager import SpecCommitManager
from spec_cli.exceptions import SpecGitError


class TestSpecCommitManager:
    """Test SpecCommitManager class functionality."""

    @pytest.fixture
    def mock_settings(self) -> Mock:
        """Create mock settings for testing."""
        settings = Mock()
        settings.spec_dir = "/test/.spec"
        settings.specs_dir = "/test/.specs"
        return settings

    @pytest.fixture
    def mock_git_repo(self) -> Mock:
        """Create mock git repository for testing."""
        return Mock()

    @pytest.fixture
    def mock_state_checker(self) -> Mock:
        """Create mock repository state checker for testing."""
        return Mock()

    @pytest.fixture
    def commit_manager(self, mock_settings: Mock) -> SpecCommitManager:
        """Create SpecCommitManager instance with mocked dependencies."""
        with patch("spec_cli.core.commit_manager.SpecGitRepository"), patch(
            "spec_cli.core.commit_manager.RepositoryStateChecker"
        ):
            manager = SpecCommitManager(mock_settings)
            manager.git_repo = Mock()
            manager.state_checker = Mock()
            return manager

    def test_commit_manager_initialization(self, mock_settings: Mock) -> None:
        """Test SpecCommitManager initializes correctly."""
        with patch("spec_cli.core.commit_manager.SpecGitRepository"), patch(
            "spec_cli.core.commit_manager.RepositoryStateChecker"
        ):
            manager = SpecCommitManager(mock_settings)
            assert manager.settings is mock_settings

    def test_commit_manager_default_settings(self) -> None:
        """Test SpecCommitManager uses default settings when none provided."""
        with patch(
            "spec_cli.core.commit_manager.get_settings"
        ) as mock_get_settings, patch(
            "spec_cli.core.commit_manager.SpecGitRepository"
        ), patch("spec_cli.core.commit_manager.RepositoryStateChecker"):
            mock_get_settings.return_value = Mock()
            SpecCommitManager()
            mock_get_settings.assert_called_once()

    def test_add_files_success(self, commit_manager: SpecCommitManager) -> None:
        """Test successful file addition."""
        # Mock the internal validation method to return no issues
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        # Mock settings.specs_dir as pathlib.Path object
        mock_path = Mock()
        mock_path.exists.return_value = True
        commit_manager.settings.specs_dir = Mock()
        commit_manager.settings.specs_dir.__truediv__ = Mock(return_value=mock_path)
        # Mock git operations
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []
        cast(Mock, commit_manager.git_repo.run_git_command).return_value = None

        result = commit_manager.add_files(["test.md", "other.md"])

        assert result["success"] is True
        assert result["added"] == ["test.md", "other.md"]
        assert result["errors"] == []

    def test_add_files_without_validation(
        self, commit_manager: SpecCommitManager
    ) -> None:
        """Test file addition without validation."""
        # Mock settings.specs_dir as pathlib.Path object
        mock_path = Mock()
        mock_path.exists.return_value = True
        commit_manager.settings.specs_dir = Mock()
        commit_manager.settings.specs_dir.__truediv__ = Mock(return_value=mock_path)
        # Mock git operations
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []
        cast(Mock, commit_manager.git_repo.run_git_command).return_value = None

        result = commit_manager.add_files(["test.md"], validate=False)

        assert result["success"] is True
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).assert_not_called()

    def test_add_files_with_force(self, commit_manager: SpecCommitManager) -> None:
        """Test file addition with force flag."""
        # Mock the internal validation method to return no issues
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        # Mock settings.specs_dir as pathlib.Path object
        mock_path = Mock()
        mock_path.exists.return_value = True
        commit_manager.settings.specs_dir = Mock()
        commit_manager.settings.specs_dir.__truediv__ = Mock(return_value=mock_path)
        # Mock git operations
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []
        cast(Mock, commit_manager.git_repo.run_git_command).return_value = None

        result = commit_manager.add_files(["test.md"], force=True)

        assert result["success"] is True

    def test_add_files_validation_failure(
        self, commit_manager: SpecCommitManager
    ) -> None:
        """Test file addition when validation fails."""
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = ["Repository not in safe state"]

        result = commit_manager.add_files(["test.md"])
        assert result["success"] is False
        assert "Repository not in safe state" in result["errors"]

    def test_add_files_git_error(self, commit_manager: SpecCommitManager) -> None:
        """Test file addition when git operation fails."""
        # Mock the internal validation method to return no issues
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        # Mock settings.specs_dir as pathlib.Path object
        mock_path = Mock()
        mock_path.exists.return_value = True
        commit_manager.settings.specs_dir = Mock()
        commit_manager.settings.specs_dir.__truediv__ = Mock(return_value=mock_path)
        # Mock git operations
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []
        cast(Mock, commit_manager.git_repo.run_git_command).side_effect = Exception(
            "Git error"
        )

        result = commit_manager.add_files(["test.md", "other.md"])

        assert result["success"] is False
        assert result["added"] == []
        assert len(result["errors"]) == 2
        assert "Git error" in result["errors"][0]

    def test_commit_success(self, commit_manager: SpecCommitManager) -> None:
        """Test successful commit creation."""
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = ["test.md"]
        mock_result = Mock()
        mock_result.stdout = "[main abc123def456] Test commit message"
        cast(Mock, commit_manager.git_repo.run_git_command).return_value = mock_result

        result = commit_manager.commit_changes("Test commit message")

        assert result["success"] is True
        assert result["commit_hash"] == "abc123def456"
        assert result["files_committed"] == ["test.md"]

    def test_commit_no_staged_files(self, commit_manager: SpecCommitManager) -> None:
        """Test commit when no files are staged."""
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []

        result = commit_manager.commit_changes("Test commit")
        assert result["success"] is False
        assert "No staged files to commit" in result["errors"]

    def test_commit_validation_failure(self, commit_manager: SpecCommitManager) -> None:
        """Test commit when validation fails."""
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = ["Repository not in safe state"]

        result = commit_manager.commit_changes("Test commit")
        assert result["success"] is False
        assert "Repository not in safe state" in result["errors"]

    def test_commit_git_error(self, commit_manager: SpecCommitManager) -> None:
        """Test commit when git operation fails."""
        cast(
            Mock, commit_manager.state_checker.validate_pre_operation_state
        ).return_value = []
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = ["test.md"]
        cast(Mock, commit_manager.git_repo.run_git_command).side_effect = Exception(
            "Commit failed"
        )

        with pytest.raises(SpecGitError, match="Commit operation failed"):
            commit_manager.commit_changes("Test commit")

    def test_get_commit_status(self, commit_manager: SpecCommitManager) -> None:
        """Test getting commit status."""
        cast(Mock, commit_manager.git_repo.is_initialized).return_value = True
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = [
            "staged.md"
        ]
        cast(Mock, commit_manager.git_repo.get_unstaged_files).return_value = [
            "modified.md"
        ]
        cast(Mock, commit_manager.git_repo.get_untracked_files).return_value = [
            "new.md"
        ]
        cast(
            Mock, commit_manager.state_checker.check_branch_cleanliness
        ).return_value = {"clean": True}
        cast(
            Mock, commit_manager.state_checker.is_safe_for_spec_operations
        ).return_value = True

        status = commit_manager.get_commit_status()

        assert status["staged_files"] == ["staged.md"]
        assert status["unstaged_files"] == ["modified.md"]
        assert status["untracked_files"] == ["new.md"]
        assert status["safe_for_operations"] is True

    def test_get_commit_status_not_ready(
        self, commit_manager: SpecCommitManager
    ) -> None:
        """Test getting commit status when not ready to commit."""
        cast(Mock, commit_manager.git_repo.is_initialized).return_value = True
        cast(Mock, commit_manager.git_repo.get_staged_files).return_value = []
        cast(Mock, commit_manager.git_repo.get_unstaged_files).return_value = [
            "modified.md"
        ]
        cast(Mock, commit_manager.git_repo.get_untracked_files).return_value = [
            "new.md"
        ]
        cast(
            Mock, commit_manager.state_checker.check_branch_cleanliness
        ).return_value = {"clean": False}
        cast(
            Mock, commit_manager.state_checker.is_safe_for_spec_operations
        ).return_value = False

        status = commit_manager.get_commit_status()

        assert status["safe_for_operations"] is False
