"""Repository state management and health checking module for spec CLI.

This module provides comprehensive repository state monitoring and health checking
capabilities for spec repositories. It includes classes for assessing repository
health, branch status, and validating that repositories are in a safe state
for spec operations.

Key responsibilities:
- Monitoring repository health with detailed status reporting
- Checking branch cleanliness and Git repository state
- Validating pre-operation conditions for safe spec operations
- Providing structured health reports with warnings and errors
- Ensuring repository integrity before performing critical operations
"""

from enum import Enum
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..git.repository import SpecGitRepository
from ..logging.debug import debug_logger


class RepositoryHealth(Enum):
    """Repository health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BranchStatus(Enum):
    """Branch status for cleanliness checking."""

    CLEAN = "clean"
    UNCOMMITTED_CHANGES = "uncommitted_changes"
    UNTRACKED_FILES = "untracked_files"
    STAGED_CHANGES = "staged_changes"
    DIVERGED = "diverged"
    UNKNOWN = "unknown"


class RepositoryStateChecker:
    """Checks and validates spec repository state and health."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize the repository state checker with configuration.

        Args:
            settings: Optional SpecSettings instance. If None, uses default settings
                     from get_settings()

        The state checker sets up the Git repository interface for performing
        comprehensive health checks and state validation operations.
        """
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)

        debug_logger.log("INFO", "RepositoryStateChecker initialized")

    def check_repository_health(self) -> dict[str, Any]:
        """Perform comprehensive repository health check.

        Returns:
            Dictionary with health status and detailed information
        """
        debug_logger.log("INFO", "Performing repository health check")

        health_report: dict[str, Any] = {
            "overall_health": RepositoryHealth.HEALTHY,
            "issues": [],
            "warnings": [],
            "checks": {
                "spec_repo_exists": False,
                "spec_dir_exists": False,
                "git_repo_valid": False,
                "branch_status": BranchStatus.UNKNOWN,
                "work_tree_valid": False,
                "permissions_ok": False,
            },
            "details": {},
        }

        try:
            with debug_logger.timer("repository_health_check"):
                # Check .spec repository existence
                self._check_spec_repository(health_report)

                # Check .specs directory
                self._check_specs_directory(health_report)

                # Check Git repository validity
                self._check_git_repository(health_report)

                # Check branch status
                self._check_branch_status(health_report)

                # Check work tree validity
                self._check_work_tree(health_report)

                # Check permissions
                self._check_permissions(health_report)

                # Determine overall health
                self._determine_overall_health(health_report)

            debug_logger.log(
                "INFO",
                "Repository health check complete",
                overall_health=health_report["overall_health"].value,
                issues=len(health_report["issues"]),
                warnings=len(health_report["warnings"]),
            )

            return health_report

        except Exception as e:
            error_msg = f"Repository health check failed: {e}"
            debug_logger.log("ERROR", error_msg)
            health_report["overall_health"] = RepositoryHealth.CRITICAL
            health_report["issues"].append(error_msg)
            return health_report

    def _check_spec_repository(self, report: dict[str, Any]) -> None:
        """Check if .spec repository exists and is valid."""
        spec_dir = self.settings.spec_dir

        if spec_dir.exists() and spec_dir.is_dir():
            report["checks"]["spec_repo_exists"] = True

            # Check if it's a valid Git repository
            if (spec_dir / "HEAD").exists():
                report["details"]["spec_repo_path"] = str(spec_dir)
            else:
                report["issues"].append(
                    f"Directory {spec_dir} exists but is not a valid Git repository"
                )
        else:
            report["checks"]["spec_repo_exists"] = False
            report["details"]["spec_repo_missing"] = str(spec_dir)

    def _check_specs_directory(self, report: dict[str, Any]) -> None:
        """Check if .specs directory exists and is accessible."""
        specs_dir = self.settings.specs_dir

        if specs_dir.exists() and specs_dir.is_dir():
            report["checks"]["spec_dir_exists"] = True
            report["details"]["specs_dir_path"] = str(specs_dir)

            # Check if directory is empty or has content
            try:
                content_count = len(list(specs_dir.rglob("*")))
                report["details"]["specs_content_count"] = content_count
            except OSError as e:
                report["warnings"].append(f"Could not scan .specs directory: {e}")
        else:
            report["checks"]["spec_dir_exists"] = False
            report["details"]["specs_dir_missing"] = str(specs_dir)

    def _check_git_repository(self, report: dict[str, Any]) -> None:
        """Check if Git repository is valid and accessible."""
        try:
            if self.git_repo.is_initialized():
                report["checks"]["git_repo_valid"] = True

                # Get additional Git info
                try:
                    current_branch = self.git_repo.get_current_branch()
                    report["details"]["current_branch"] = current_branch
                except Exception as e:
                    report["warnings"].append(
                        f"Could not determine current branch: {e}"
                    )

                try:
                    commit_count = len(self.git_repo.get_recent_commits(5))
                    report["details"]["recent_commits"] = commit_count
                except Exception as e:
                    report["warnings"].append(f"Could not access recent commits: {e}")
            else:
                report["checks"]["git_repo_valid"] = False
                report["issues"].append(
                    "Spec Git repository is not properly initialized"
                )

        except Exception as e:
            report["checks"]["git_repo_valid"] = False
            report["issues"].append(f"Git repository check failed: {e}")

    def _check_branch_status(self, report: dict[str, Any]) -> None:
        """Check branch cleanliness and status."""
        try:
            if report["checks"]["git_repo_valid"]:
                branch_status = self.check_branch_cleanliness()
                report["checks"]["branch_status"] = branch_status
                report["details"]["branch_clean"] = branch_status == BranchStatus.CLEAN

                if branch_status != BranchStatus.CLEAN:
                    report["warnings"].append(
                        f"Branch is not clean: {branch_status.value}"
                    )
            else:
                report["checks"]["branch_status"] = BranchStatus.UNKNOWN

        except Exception as e:
            report["checks"]["branch_status"] = BranchStatus.UNKNOWN
            report["warnings"].append(f"Could not check branch status: {e}")

    def _check_work_tree(self, report: dict[str, Any]) -> None:
        """Check if work tree is valid and accessible."""
        try:
            if report["checks"]["git_repo_valid"]:
                # Verify work tree configuration
                work_tree = self.settings.specs_dir
                if work_tree.exists():
                    report["checks"]["work_tree_valid"] = True
                    report["details"]["work_tree_path"] = str(work_tree)
                else:
                    report["checks"]["work_tree_valid"] = False
                    report["issues"].append(
                        f"Work tree directory does not exist: {work_tree}"
                    )
            else:
                report["checks"]["work_tree_valid"] = False

        except Exception as e:
            report["checks"]["work_tree_valid"] = False
            report["warnings"].append(f"Work tree check failed: {e}")

    def _check_permissions(self, report: dict[str, Any]) -> None:
        """Check file system permissions for spec operations."""
        import os

        permissions_ok = True
        permission_issues = []

        # Check .spec directory permissions
        spec_dir = self.settings.spec_dir
        if spec_dir.exists():
            if not os.access(spec_dir, os.R_OK | os.W_OK):
                permissions_ok = False
                permission_issues.append(f"No read/write access to {spec_dir}")

        # Check .specs directory permissions
        specs_dir = self.settings.specs_dir
        if specs_dir.exists():
            if not os.access(specs_dir, os.R_OK | os.W_OK):
                permissions_ok = False
                permission_issues.append(f"No read/write access to {specs_dir}")

        # Check parent directory permissions for creation
        parent_dir = spec_dir.parent
        if not os.access(parent_dir, os.W_OK):
            permissions_ok = False
            permission_issues.append(
                f"No write access to parent directory {parent_dir}"
            )

        report["checks"]["permissions_ok"] = permissions_ok
        if permission_issues:
            report["issues"].extend(permission_issues)

        report["details"]["permission_issues"] = permission_issues

    def _determine_overall_health(self, report: dict[str, Any]) -> None:
        """Determine overall repository health based on checks."""
        checks = report["checks"]
        issues = report["issues"]
        warnings = report["warnings"]

        if issues:
            if not checks["permissions_ok"] or not checks["git_repo_valid"]:
                report["overall_health"] = RepositoryHealth.CRITICAL
            else:
                report["overall_health"] = RepositoryHealth.ERROR
        elif warnings:
            report["overall_health"] = RepositoryHealth.WARNING
        else:
            report["overall_health"] = RepositoryHealth.HEALTHY

    def check_branch_cleanliness(self) -> BranchStatus:
        """Check if the current branch is clean for spec operations.

        Returns:
            BranchStatus indicating the cleanliness state
        """
        debug_logger.log("DEBUG", "Checking branch cleanliness")

        try:
            # Check for uncommitted changes
            if self.git_repo.has_uncommitted_changes():
                debug_logger.log("WARNING", "Branch has uncommitted changes")
                return BranchStatus.UNCOMMITTED_CHANGES

            # Check for untracked files
            if self.git_repo.has_untracked_files():
                debug_logger.log("WARNING", "Branch has untracked files")
                return BranchStatus.UNTRACKED_FILES

            # Check for staged changes
            if self.git_repo.has_staged_changes():
                debug_logger.log("WARNING", "Branch has staged changes")
                return BranchStatus.STAGED_CHANGES

            debug_logger.log("INFO", "Branch is clean")
            return BranchStatus.CLEAN

        except Exception as e:
            debug_logger.log(
                "ERROR", "Failed to check branch cleanliness", error=str(e)
            )
            return BranchStatus.UNKNOWN

    def is_safe_for_spec_operations(self) -> bool:
        """Check if repository is safe for spec operations.

        Returns:
            True if safe to proceed with spec operations
        """
        try:
            health = self.check_repository_health()

            # Repository must be healthy or have only warnings
            if health["overall_health"] in [
                RepositoryHealth.ERROR,
                RepositoryHealth.CRITICAL,
            ]:
                return False

            # Must have basic repository structure
            checks = health["checks"]
            if not (checks["spec_repo_exists"] and checks["git_repo_valid"]):
                return False

            # Must have proper permissions
            if not checks["permissions_ok"]:
                return False

            return True

        except Exception as e:
            debug_logger.log("ERROR", "Safety check failed", error=str(e))
            return False

    def get_repository_summary(self) -> dict[str, Any]:
        """Get a concise summary of repository status.

        Returns:
            Dictionary with summary information
        """
        try:
            health = self.check_repository_health()

            summary = {
                "initialized": health["checks"]["spec_repo_exists"],
                "healthy": health["overall_health"]
                in [RepositoryHealth.HEALTHY, RepositoryHealth.WARNING],
                "safe_for_operations": self.is_safe_for_spec_operations(),
                "branch_clean": health["checks"]["branch_status"] == BranchStatus.CLEAN,
                "specs_dir_exists": health["checks"]["spec_dir_exists"],
                "issue_count": len(health["issues"]),
                "warning_count": len(health["warnings"]),
                "current_branch": health["details"].get("current_branch", "unknown"),
            }

            return summary

        except Exception as e:
            debug_logger.log("ERROR", "Failed to get repository summary", error=str(e))
            return {
                "initialized": False,
                "healthy": False,
                "safe_for_operations": False,
                "error": str(e),
            }

    def validate_pre_operation_state(self, operation_name: str) -> list[str]:
        """Validate that repository state is ready for a specific operation.

        Args:
            operation_name: Name of the operation being attempted

        Returns:
            List of validation issues (empty if valid)
        """
        debug_logger.log(
            "INFO", "Validating pre-operation state", operation=operation_name
        )

        issues = []

        try:
            health = self.check_repository_health()

            # Check overall health
            if health["overall_health"] == RepositoryHealth.CRITICAL:
                issues.append(
                    f"Repository is in critical state, cannot perform {operation_name}"
                )
                return issues  # Don't continue if critical

            # Check basic requirements
            if not health["checks"]["spec_repo_exists"]:
                issues.append("Spec repository not initialized")

            if not health["checks"]["git_repo_valid"]:
                issues.append("Git repository is not valid")

            if not health["checks"]["permissions_ok"]:
                issues.append("Insufficient permissions for spec operations")

            # Operation-specific validations
            if operation_name in ["commit", "add", "generate"]:
                if health["checks"]["branch_status"] not in [
                    BranchStatus.CLEAN,
                    BranchStatus.UNTRACKED_FILES,
                ]:
                    issues.append(f"Branch is not clean for {operation_name} operation")

            # Add any health issues as validation failures
            issues.extend(health["issues"])

        except Exception as e:
            issues.append(f"Pre-operation validation failed: {e}")

        debug_logger.log(
            "INFO",
            "Pre-operation validation complete",
            operation=operation_name,
            issues=len(issues),
        )

        return issues
