"""Workflow backup management for spec CLI.

This module provides the WorkflowBackupManager class which handles backup and rollback
operations for spec generation workflows. It creates backup tags before workflow
execution and provides rollback capabilities to restore the repository state in case
of workflow failures.
"""

from pathlib import Path
from typing import Any

from ...exceptions import SpecWorkflowError
from ...logging.debug import debug_logger
from ...utils.error_utils import create_error_context
from ..commit_manager import SpecCommitManager


class WorkflowBackupManager:
    """Manages backup and rollback operations for workflows."""

    def __init__(self, commit_manager: SpecCommitManager):
        """Initialize the backup manager with a commit manager.

        Args:
            commit_manager: SpecCommitManager instance for Git operations

        Raises:
            TypeError: If commit_manager is not a SpecCommitManager instance
        """
        if not isinstance(commit_manager, SpecCommitManager):
            raise TypeError(f"Expected SpecCommitManager, got {type(commit_manager)}")

        self.commit_manager = commit_manager
        debug_logger.log("INFO", "WorkflowBackupManager initialized")

    def create_backup(self, workflow_id: str) -> dict[str, Any]:
        """Create backup tag for a workflow.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Dictionary containing backup information with keys:
            - backup_tag: str - The created backup tag name
            - commit_hash: str - The commit hash of the backup point

        Raises:
            SpecWorkflowError: If backup creation fails
            TypeError: If workflow_id is not a string
            ValueError: If workflow_id is empty or contains invalid characters

        Example:
            >>> manager = WorkflowBackupManager(commit_manager)
            >>> backup_info = manager.create_backup("workflow-123")
            >>> print(backup_info["backup_tag"])  # "backup-workflow-123"
        """
        if not isinstance(workflow_id, str):
            raise TypeError(f"workflow_id must be string, got {type(workflow_id)}")

        if not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")

        # Validate workflow_id contains only safe characters
        if not all(c.isalnum() or c in "-_" for c in workflow_id):
            raise ValueError(f"workflow_id contains invalid characters: {workflow_id}")

        backup_tag = f"backup-{workflow_id}"

        debug_logger.log(
            "INFO",
            "Creating backup for workflow",
            workflow_id=workflow_id,
            backup_tag=backup_tag,
        )

        try:
            tag_result = self.commit_manager.create_tag(
                backup_tag,
                f"Backup before spec generation workflow {workflow_id}",
            )

            if not tag_result["success"]:
                error_context = create_error_context(Path.cwd())
                error_context.update(
                    {
                        "workflow_id": workflow_id,
                        "backup_tag": backup_tag,
                        "tag_errors": tag_result["errors"],
                    }
                )
                debug_logger.log("ERROR", "Backup creation failed", **error_context)
                raise SpecWorkflowError(
                    f"Backup creation failed: {'; '.join(tag_result['errors'])}"
                )

            backup_info = {
                "backup_tag": backup_tag,
                "commit_hash": tag_result["commit_hash"],
            }

            debug_logger.log(
                "INFO",
                "Backup created successfully",
                workflow_id=workflow_id,
                backup_tag=backup_tag,
                commit_hash=tag_result["commit_hash"],
            )

            return backup_info

        except Exception as e:
            error_context = create_error_context(Path.cwd())
            error_context.update(
                {
                    "workflow_id": workflow_id,
                    "backup_tag": backup_tag,
                    "error": str(e),
                }
            )
            debug_logger.log("ERROR", "Backup creation exception", **error_context)
            raise SpecWorkflowError(f"Failed to create backup: {e}") from e

    def rollback_to_backup(self, backup_tag: str, commit_hash: str) -> dict[str, Any]:
        """Rollback repository to a backup point.

        Args:
            backup_tag: The backup tag name to rollback to
            commit_hash: The commit hash to rollback to

        Returns:
            Dictionary containing rollback results with keys:
            - success: bool - Whether rollback succeeded
            - backup_tag: str - The backup tag used
            - commit_hash: str - The commit hash rolled back to

        Raises:
            SpecWorkflowError: If rollback fails
            TypeError: If backup_tag or commit_hash are not strings
            ValueError: If backup_tag or commit_hash are empty

        Example:
            >>> result = manager.rollback_to_backup("backup-workflow-123", "abc123")
            >>> print(result["success"])  # True
        """
        if not isinstance(backup_tag, str):
            raise TypeError(f"backup_tag must be string, got {type(backup_tag)}")

        if not isinstance(commit_hash, str):
            raise TypeError(f"commit_hash must be string, got {type(commit_hash)}")

        if not backup_tag.strip():
            raise ValueError("backup_tag cannot be empty")

        if not commit_hash.strip():
            raise ValueError("commit_hash cannot be empty")

        debug_logger.log(
            "INFO",
            "Starting rollback to backup",
            backup_tag=backup_tag,
            commit_hash=commit_hash,
        )

        try:
            rollback_result = self.commit_manager.rollback_to_commit(
                commit_hash, hard=True, create_backup=False
            )

            if not rollback_result["success"]:
                error_context = create_error_context(Path.cwd())
                error_context.update(
                    {
                        "backup_tag": backup_tag,
                        "commit_hash": commit_hash,
                        "rollback_errors": rollback_result["errors"],
                    }
                )
                debug_logger.log("ERROR", "Rollback failed", **error_context)
                raise SpecWorkflowError(
                    f"Rollback failed: {'; '.join(rollback_result['errors'])}"
                )

            result = {
                "success": True,
                "backup_tag": backup_tag,
                "commit_hash": commit_hash,
            }

            debug_logger.log(
                "INFO",
                "Rollback completed successfully",
                backup_tag=backup_tag,
                commit_hash=commit_hash,
            )

            return result

        except Exception as e:
            error_context = create_error_context(Path.cwd())
            error_context.update(
                {
                    "backup_tag": backup_tag,
                    "commit_hash": commit_hash,
                    "error": str(e),
                }
            )
            debug_logger.log("ERROR", "Rollback exception", **error_context)
            raise SpecWorkflowError(f"Failed to rollback: {e}") from e
