"""Unit tests for WorkflowBackupManager."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.commit_manager import SpecCommitManager
from spec_cli.core.managers.backup_manager import WorkflowBackupManager
from spec_cli.exceptions import SpecWorkflowError


class TestWorkflowBackupManagerInitialization:
    """Test WorkflowBackupManager initialization."""

    def test_initialization_with_valid_commit_manager_then_succeeds(self):
        """Test initialization with valid SpecCommitManager succeeds."""
        mock_commit_manager = Mock(spec=SpecCommitManager)

        manager = WorkflowBackupManager(mock_commit_manager)

        assert manager.commit_manager is mock_commit_manager

    def test_initialization_with_invalid_commit_manager_then_raises_type_error(self):
        """Test initialization with invalid commit manager raises TypeError."""
        invalid_manager = Mock()  # Not a SpecCommitManager

        with pytest.raises(TypeError, match="Expected SpecCommitManager"):
            WorkflowBackupManager(invalid_manager)

    def test_initialization_with_none_then_raises_type_error(self):
        """Test initialization with None raises TypeError."""
        with pytest.raises(TypeError, match="Expected SpecCommitManager"):
            WorkflowBackupManager(None)


class TestWorkflowBackupManagerCreateBackup:
    """Test WorkflowBackupManager create_backup method."""

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for testing."""
        return Mock(spec=SpecCommitManager)

    @pytest.fixture
    def backup_manager(self, mock_commit_manager):
        """Backup manager instance with mocked commit manager."""
        return WorkflowBackupManager(mock_commit_manager)

    def test_create_backup_when_valid_workflow_id_then_returns_backup_info(
        self, backup_manager, mock_commit_manager
    ):
        """Test create_backup with valid workflow ID returns backup info."""
        workflow_id = "test-workflow-123"
        expected_tag = "backup-test-workflow-123"
        expected_hash = "abc123def456"

        mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": expected_hash,
            "errors": [],
        }

        result = backup_manager.create_backup(workflow_id)

        assert result["backup_tag"] == expected_tag
        assert result["commit_hash"] == expected_hash
        mock_commit_manager.create_tag.assert_called_once_with(
            expected_tag,
            f"Backup before spec generation workflow {workflow_id}",
        )

    def test_create_backup_when_non_string_workflow_id_then_raises_type_error(
        self, backup_manager
    ):
        """Test create_backup with non-string workflow ID raises TypeError."""
        with pytest.raises(TypeError, match="workflow_id must be string"):
            backup_manager.create_backup(123)

    def test_create_backup_when_empty_workflow_id_then_raises_value_error(
        self, backup_manager
    ):
        """Test create_backup with empty workflow ID raises ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            backup_manager.create_backup("")

    def test_create_backup_when_whitespace_workflow_id_then_raises_value_error(
        self, backup_manager
    ):
        """Test create_backup with whitespace-only workflow ID raises ValueError."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            backup_manager.create_backup("   ")

    def test_create_backup_when_invalid_characters_then_raises_value_error(
        self, backup_manager
    ):
        """Test create_backup with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            backup_manager.create_backup("workflow/with/slashes")

    def test_create_backup_when_tag_creation_fails_then_raises_spec_workflow_error(
        self, backup_manager, mock_commit_manager
    ):
        """Test create_backup when tag creation fails raises SpecWorkflowError."""
        workflow_id = "test-workflow"
        mock_commit_manager.create_tag.return_value = {
            "success": False,
            "commit_hash": None,
            "errors": ["Tag creation failed", "Repository not found"],
        }

        with pytest.raises(SpecWorkflowError, match="Backup creation failed"):
            backup_manager.create_backup(workflow_id)

    def test_create_backup_when_commit_manager_raises_exception_then_raises_spec_workflow_error(
        self, backup_manager, mock_commit_manager
    ):
        """Test create_backup when commit manager raises exception."""
        workflow_id = "test-workflow"
        mock_commit_manager.create_tag.side_effect = RuntimeError("Git error")

        with pytest.raises(SpecWorkflowError, match="Failed to create backup"):
            backup_manager.create_backup(workflow_id)

    def test_create_backup_when_valid_alphanumeric_workflow_id_then_succeeds(
        self, backup_manager, mock_commit_manager
    ):
        """Test create_backup with valid alphanumeric workflow ID succeeds."""
        workflow_id = "workflow123"
        mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "errors": [],
        }

        result = backup_manager.create_backup(workflow_id)

        assert result["backup_tag"] == "backup-workflow123"
        assert result["commit_hash"] == "abc123"

    def test_create_backup_when_valid_workflow_id_with_hyphens_and_underscores_then_succeeds(
        self, backup_manager, mock_commit_manager
    ):
        """Test create_backup with workflow ID containing hyphens and underscores."""
        workflow_id = "test-workflow_123"
        mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "def456",
            "errors": [],
        }

        result = backup_manager.create_backup(workflow_id)

        assert result["backup_tag"] == "backup-test-workflow_123"
        assert result["commit_hash"] == "def456"


class TestWorkflowBackupManagerRollbackToBackup:
    """Test WorkflowBackupManager rollback_to_backup method."""

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for testing."""
        return Mock(spec=SpecCommitManager)

    @pytest.fixture
    def backup_manager(self, mock_commit_manager):
        """Backup manager instance with mocked commit manager."""
        return WorkflowBackupManager(mock_commit_manager)

    def test_rollback_to_backup_when_valid_parameters_then_returns_success_result(
        self, backup_manager, mock_commit_manager
    ):
        """Test rollback_to_backup with valid parameters returns success result."""
        backup_tag = "backup-test-workflow"
        commit_hash = "abc123def456"

        mock_commit_manager.rollback_to_commit.return_value = {
            "success": True,
            "errors": [],
        }

        result = backup_manager.rollback_to_backup(backup_tag, commit_hash)

        assert result["success"] is True
        assert result["backup_tag"] == backup_tag
        assert result["commit_hash"] == commit_hash
        mock_commit_manager.rollback_to_commit.assert_called_once_with(
            commit_hash, hard=True, create_backup=False
        )

    def test_rollback_to_backup_when_non_string_backup_tag_then_raises_type_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with non-string backup tag raises TypeError."""
        with pytest.raises(TypeError, match="backup_tag must be string"):
            backup_manager.rollback_to_backup(123, "abc123")

    def test_rollback_to_backup_when_non_string_commit_hash_then_raises_type_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with non-string commit hash raises TypeError."""
        with pytest.raises(TypeError, match="commit_hash must be string"):
            backup_manager.rollback_to_backup("backup-tag", 456)

    def test_rollback_to_backup_when_empty_backup_tag_then_raises_value_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with empty backup tag raises ValueError."""
        with pytest.raises(ValueError, match="backup_tag cannot be empty"):
            backup_manager.rollback_to_backup("", "abc123")

    def test_rollback_to_backup_when_empty_commit_hash_then_raises_value_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with empty commit hash raises ValueError."""
        with pytest.raises(ValueError, match="commit_hash cannot be empty"):
            backup_manager.rollback_to_backup("backup-tag", "")

    def test_rollback_to_backup_when_whitespace_backup_tag_then_raises_value_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with whitespace-only backup tag raises ValueError."""
        with pytest.raises(ValueError, match="backup_tag cannot be empty"):
            backup_manager.rollback_to_backup("   ", "abc123")

    def test_rollback_to_backup_when_whitespace_commit_hash_then_raises_value_error(
        self, backup_manager
    ):
        """Test rollback_to_backup with whitespace-only commit hash raises ValueError."""
        with pytest.raises(ValueError, match="commit_hash cannot be empty"):
            backup_manager.rollback_to_backup("backup-tag", "   ")

    def test_rollback_to_backup_when_rollback_fails_then_raises_spec_workflow_error(
        self, backup_manager, mock_commit_manager
    ):
        """Test rollback_to_backup when rollback fails raises SpecWorkflowError."""
        backup_tag = "backup-test-workflow"
        commit_hash = "abc123"

        mock_commit_manager.rollback_to_commit.return_value = {
            "success": False,
            "errors": ["Rollback failed", "Invalid commit hash"],
        }

        with pytest.raises(SpecWorkflowError, match="Rollback failed"):
            backup_manager.rollback_to_backup(backup_tag, commit_hash)

    def test_rollback_to_backup_when_commit_manager_raises_exception_then_raises_spec_workflow_error(
        self, backup_manager, mock_commit_manager
    ):
        """Test rollback_to_backup when commit manager raises exception."""
        backup_tag = "backup-test-workflow"
        commit_hash = "abc123"

        mock_commit_manager.rollback_to_commit.side_effect = RuntimeError("Git error")

        with pytest.raises(SpecWorkflowError, match="Failed to rollback"):
            backup_manager.rollback_to_backup(backup_tag, commit_hash)


class TestWorkflowBackupManagerErrorHandling:
    """Test WorkflowBackupManager error handling and context creation."""

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for testing."""
        return Mock(spec=SpecCommitManager)

    @pytest.fixture
    def backup_manager(self, mock_commit_manager):
        """Backup manager instance with mocked commit manager."""
        return WorkflowBackupManager(mock_commit_manager)

    @patch("spec_cli.core.managers.backup_manager.create_error_context")
    def test_create_backup_error_creates_context_with_workflow_info(
        self, mock_create_error_context, backup_manager, mock_commit_manager
    ):
        """Test create_backup error handling creates context with workflow info."""
        workflow_id = "test-workflow"
        mock_create_error_context.return_value = {"file_path": "/test"}
        mock_commit_manager.create_tag.return_value = {
            "success": False,
            "commit_hash": None,
            "errors": ["Tag creation failed"],
        }

        with pytest.raises(SpecWorkflowError):
            backup_manager.create_backup(workflow_id)

        # Verify create_error_context was called with Path argument
        assert mock_create_error_context.call_count >= 1
        call_args = mock_create_error_context.call_args[0]
        assert isinstance(call_args[0], Path)

    @patch("spec_cli.core.managers.backup_manager.create_error_context")
    def test_rollback_to_backup_error_creates_context_with_backup_info(
        self, mock_create_error_context, backup_manager, mock_commit_manager
    ):
        """Test rollback_to_backup error handling creates context with backup info."""
        backup_tag = "backup-test"
        commit_hash = "abc123"
        mock_create_error_context.return_value = {"file_path": "/test"}
        mock_commit_manager.rollback_to_commit.return_value = {
            "success": False,
            "errors": ["Rollback failed"],
        }

        with pytest.raises(SpecWorkflowError):
            backup_manager.rollback_to_backup(backup_tag, commit_hash)

        # Verify create_error_context was called with Path argument
        assert mock_create_error_context.call_count >= 1
        call_args = mock_create_error_context.call_args[0]
        assert isinstance(call_args[0], Path)


class TestWorkflowBackupManagerIntegration:
    """Integration tests for WorkflowBackupManager with mocked dependencies."""

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for integration testing."""
        return Mock(spec=SpecCommitManager)

    @pytest.fixture
    def backup_manager(self, mock_commit_manager):
        """Backup manager instance for integration testing."""
        return WorkflowBackupManager(mock_commit_manager)

    def test_create_backup_and_rollback_integration_scenario(
        self, backup_manager, mock_commit_manager
    ):
        """Test complete backup and rollback workflow integration."""
        workflow_id = "integration-test-workflow"
        expected_commit_hash = "integration-hash-123"

        # Mock successful backup creation
        mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": expected_commit_hash,
            "errors": [],
        }

        # Mock successful rollback
        mock_commit_manager.rollback_to_commit.return_value = {
            "success": True,
            "errors": [],
        }

        # Create backup
        backup_info = backup_manager.create_backup(workflow_id)
        assert backup_info["backup_tag"] == f"backup-{workflow_id}"
        assert backup_info["commit_hash"] == expected_commit_hash

        # Rollback to backup
        rollback_result = backup_manager.rollback_to_backup(
            backup_info["backup_tag"], backup_info["commit_hash"]
        )
        assert rollback_result["success"] is True
        assert rollback_result["backup_tag"] == backup_info["backup_tag"]
        assert rollback_result["commit_hash"] == expected_commit_hash

        # Verify method calls
        mock_commit_manager.create_tag.assert_called_once()
        mock_commit_manager.rollback_to_commit.assert_called_once_with(
            expected_commit_hash, hard=True, create_backup=False
        )

    def test_backup_creation_idempotent_behavior(
        self, backup_manager, mock_commit_manager
    ):
        """Test backup creation is idempotent and repeatable."""
        workflow_id = "idempotent-test"
        mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "hash123",
            "errors": [],
        }

        # Create backup twice
        backup_1 = backup_manager.create_backup(workflow_id)
        backup_2 = backup_manager.create_backup(workflow_id)

        # Both should have same tag name but potentially different commit hashes
        assert backup_1["backup_tag"] == backup_2["backup_tag"]
        assert backup_1["backup_tag"] == f"backup-{workflow_id}"

        # Verify commit manager was called twice
        assert mock_commit_manager.create_tag.call_count == 2
