"""Workflow validation module for spec CLI.

This module provides the WorkflowValidator class that extracts and centralizes
validation logic for spec generation workflows. It validates repository state,
file existence, and pre-operation conditions before workflow execution.
"""

from pathlib import Path
from typing import Any

from ...config.settings import SpecSettings
from ...exceptions import SpecWorkflowError
from ...logging.debug import debug_logger
from ...utils.error_handler import ErrorHandler
from ...utils.path_utils import ensure_path_permissions
from ..repository_state import RepositoryStateChecker


class WorkflowValidator:
    """Validates workflow preconditions and operation readiness."""

    def __init__(self, settings: SpecSettings, state_checker: RepositoryStateChecker):
        """Initialize the workflow validator.

        Args:
            settings: SpecSettings instance for configuration
            state_checker: RepositoryStateChecker for repository validation
        """
        self.settings = settings
        self.state_checker = state_checker
        self.error_handler = ErrorHandler()

        debug_logger.log("INFO", "WorkflowValidator initialized")

    def validate_workflow_preconditions(
        self, file_path: Path, operation_type: str
    ) -> dict[str, Any]:
        """Validate all preconditions for a workflow operation.

        Args:
            file_path: Path to the file being processed
            operation_type: Type of operation (e.g., "generate", "regenerate")

        Returns:
            Dictionary with validation results:
                {
                    "valid": bool,
                    "issues": list[str]
                }

        Raises:
            SpecWorkflowError: If critical validation errors occur
        """
        debug_logger.log(
            "INFO",
            "Validating workflow preconditions",
            file_path=str(file_path),
            operation_type=operation_type,
        )

        issues: list[str] = []

        try:
            # Check repository health
            if not self._validate_repository_health():
                issues.append("Repository is not safe for spec operations")

            # Validate file existence and accessibility
            file_issues = self._validate_file_path(file_path)
            issues.extend(file_issues)

            # Check pre-operation state
            operation_issues = self._validate_pre_operation_state(operation_type)
            issues.extend(operation_issues)

            validation_result = {"valid": len(issues) == 0, "issues": issues}

            if not validation_result["valid"]:
                debug_logger.log(
                    "WARNING",
                    "Workflow validation failed",
                    issue_count=len(issues),
                    issues=issues,
                )

            return validation_result

        except Exception as e:
            error_msg = f"Workflow validation error: {str(e)}"
            debug_logger.log("ERROR", error_msg, error=str(e))
            raise SpecWorkflowError(error_msg) from e

    def _validate_repository_health(self) -> bool:
        """Check if repository is healthy for operations.

        Returns:
            True if repository is safe for operations
        """
        try:
            return self.state_checker.is_safe_for_spec_operations()
        except Exception as e:
            debug_logger.log("ERROR", "Failed to check repository health", error=str(e))
            return False

    def _validate_file_path(self, file_path: Path) -> list[str]:
        """Validate file path existence and permissions.

        Args:
            file_path: Path to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check file existence
        if not file_path.exists():
            issues.append(f"Source file does not exist: {file_path}")
            return issues

        # Check if it's a file (not directory)
        if not file_path.is_file():
            issues.append(f"Path is not a file: {file_path}")
            return issues

        # Check read permissions
        try:
            ensure_path_permissions(file_path, require_write=False)
        except Exception as e:
            issues.append(f"File is not readable: {e}")

        return issues

    def _validate_pre_operation_state(self, operation_type: str) -> list[str]:
        """Validate pre-operation state using state checker.

        Args:
            operation_type: Type of operation being validated

        Returns:
            List of validation issues (empty if valid)
        """
        try:
            return self.state_checker.validate_pre_operation_state(operation_type)
        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Pre-operation validation failed",
                operation_type=operation_type,
                error=str(e),
            )
            return [f"Pre-operation validation error: {e}"]

    def validate_batch_operation(
        self, file_paths: list[Path], operation_type: str
    ) -> dict[str, Any]:
        """Validate preconditions for batch operations.

        Args:
            file_paths: List of file paths to validate
            operation_type: Type of batch operation

        Returns:
            Dictionary with batch validation results:
                {
                    "valid": bool,
                    "total_files": int,
                    "valid_files": list[Path],
                    "invalid_files": dict[Path, list[str]],
                    "global_issues": list[str]
                }
        """
        debug_logger.log(
            "INFO",
            "Validating batch operation",
            file_count=len(file_paths),
            operation_type=operation_type,
        )

        valid_files: list[Path] = []
        invalid_files: dict[Path, list[str]] = {}
        global_issues: list[str] = []

        result = {
            "valid": True,
            "total_files": len(file_paths),
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "global_issues": global_issues,
        }

        # Check repository health once
        if not self._validate_repository_health():
            global_issues.append("Repository is not safe for spec operations")
            result["valid"] = False

        # Check pre-operation state once
        operation_issues = self._validate_pre_operation_state(operation_type)
        if operation_issues:
            global_issues.extend(operation_issues)
            result["valid"] = False

        # Validate each file if global checks passed
        if not global_issues:
            for file_path in file_paths:
                file_issues = self._validate_file_path(file_path)
                if file_issues:
                    invalid_files[file_path] = file_issues
                    result["valid"] = False
                else:
                    valid_files.append(file_path)

        debug_logger.log(
            "INFO",
            "Batch validation complete",
            valid_files=len(valid_files),
            invalid_files=len(invalid_files),
            has_global_issues=bool(global_issues),
        )

        return result
