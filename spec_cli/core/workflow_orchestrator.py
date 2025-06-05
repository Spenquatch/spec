"""Workflow orchestration module for spec CLI.

This module provides the SpecWorkflowOrchestrator class which manages high-level
spec generation workflows. It coordinates between different components to execute
complete spec generation processes including validation, backup, content generation,
committing, and error handling with rollback capabilities.

Key responsibilities:
- Orchestrating end-to-end spec generation workflows for single files and batches
- Managing workflow state and step tracking through the workflow state manager
- Coordinating validation, backup, generation, and commit stages
- Handling error conditions with automatic rollback to backup points
- Providing progress tracking and status reporting for long-running operations
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecWorkflowError
from ..file_system.directory_manager import DirectoryManager
from ..logging.debug import debug_logger
from ..templates.generator import SpecContentGenerator
from ..templates.loader import load_template
from .commit_manager import SpecCommitManager
from .repository_state import RepositoryStateChecker
from .validators.workflow_validator import WorkflowValidator
from .workflow_state import (
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
    workflow_state_manager,
)


class SpecWorkflowOrchestrator:
    """Orchestrates high-level spec generation workflows."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize the workflow orchestrator with configuration and dependencies.

        Args:
            settings: Optional SpecSettings instance. If None, uses default settings
                     from get_settings()

        The orchestrator sets up all required components for workflow execution:
        - State checker for repository health validation
        - Workflow validator for operation precondition validation
        - Commit manager for Git operations and backup management
        - Content generator for spec document creation
        - Directory manager for file system operations
        """
        self.settings = settings or get_settings()
        self.state_checker = RepositoryStateChecker(self.settings)
        self.workflow_validator = WorkflowValidator(self.settings, self.state_checker)
        self.commit_manager = SpecCommitManager(self.settings)
        self.content_generator = SpecContentGenerator(self.settings)
        self.directory_manager = DirectoryManager(self.settings)

        debug_logger.log("INFO", "SpecWorkflowOrchestrator initialized")

    def generate_spec_for_file(
        self,
        file_path: Path,
        custom_variables: dict[str, Any] | None = None,
        auto_commit: bool = True,
        create_backup: bool = True,
    ) -> dict[str, Any]:
        """Generate spec documentation for a single file.

        Args:
            file_path: Path to source file (relative to project root)
            custom_variables: Optional custom variables for template substitution
            auto_commit: Whether to automatically commit the generated content
            create_backup: Whether to create backup before generation

        Returns:
            Dictionary with workflow results

        Raises:
            SpecWorkflowError: If workflow fails
        """
        debug_logger.log(
            "INFO",
            "Starting spec generation workflow",
            file_path=str(file_path),
            auto_commit=auto_commit,
            create_backup=create_backup,
        )

        # Create workflow
        workflow = workflow_state_manager.create_workflow(
            "spec_generation",
            {
                "file_path": str(file_path),
                "auto_commit": auto_commit,
                "create_backup": create_backup,
                "custom_variables": custom_variables or {},
            },
        )

        try:
            workflow.start()

            with debug_logger.timer("spec_generation_workflow"):
                # Step 1: Validation
                self._execute_validation_stage(workflow, file_path)

                # Step 2: Backup (if requested)
                backup_info = None
                if create_backup:
                    backup_info = self._execute_backup_stage(workflow)

                # Step 3: Content Generation
                generated_files = self._execute_generation_stage(
                    workflow, file_path, custom_variables
                )

                # Step 4: Commit (if requested)
                commit_info = None
                if auto_commit:
                    commit_info = self._execute_commit_stage(
                        workflow, file_path, generated_files
                    )

                # Step 5: Cleanup
                self._execute_cleanup_stage(workflow)

                workflow.complete()
                workflow_state_manager.complete_workflow(workflow.workflow_id)

            result = {
                "success": True,
                "workflow_id": workflow.workflow_id,
                "file_path": str(file_path),
                "generated_files": generated_files,
                "backup_info": backup_info,
                "commit_info": commit_info,
                "duration": workflow.duration,
            }

            debug_logger.log(
                "INFO",
                "Spec generation workflow completed",
                workflow_id=workflow.workflow_id,
                duration=workflow.duration,
            )

            return result

        except Exception as e:
            error_msg = f"Spec generation workflow failed: {e}"
            debug_logger.log("ERROR", error_msg)

            # Attempt rollback if backup was created
            if create_backup and workflow.metadata.get("backup_commit"):
                try:
                    self._execute_rollback_stage(workflow, str(e))
                except Exception as rollback_error:
                    debug_logger.log(
                        "ERROR", "Rollback failed", error=str(rollback_error)
                    )

            workflow.fail(error_msg)
            workflow_state_manager.fail_workflow(workflow.workflow_id, error_msg)

            raise SpecWorkflowError(error_msg) from e

    def _execute_validation_stage(
        self, workflow: WorkflowState, file_path: Path
    ) -> None:
        """Execute validation stage."""
        step = workflow.add_step("Pre-flight validation", WorkflowStage.VALIDATION)
        step.start()

        try:
            # Use workflow validator for comprehensive validation
            validation_result = self.workflow_validator.validate_workflow_preconditions(
                file_path, "generate"
            )

            if not validation_result["valid"]:
                raise SpecWorkflowError(
                    f"Validation failed: {'; '.join(validation_result['issues'])}"
                )

            step.complete(
                {"validated": True, "issues_checked": len(validation_result["issues"])}
            )

        except Exception as e:
            step.fail(str(e))
            raise

    def _execute_backup_stage(self, workflow: WorkflowState) -> dict[str, Any]:
        """Execute backup stage."""
        step = workflow.add_step("Create backup", WorkflowStage.BACKUP)
        step.start()

        try:
            # Create backup tag
            backup_tag = f"backup-{workflow.workflow_id}"
            tag_result = self.commit_manager.create_tag(
                backup_tag,
                f"Backup before spec generation workflow {workflow.workflow_id}",
            )

            if not tag_result["success"]:
                raise SpecWorkflowError(
                    f"Backup creation failed: {'; '.join(tag_result['errors'])}"
                )

            backup_info = {
                "backup_tag": backup_tag,
                "commit_hash": tag_result["commit_hash"],
            }

            # Store backup info in workflow metadata
            workflow.metadata["backup_tag"] = backup_tag
            workflow.metadata["backup_commit"] = tag_result["commit_hash"]

            step.complete(backup_info)
            return backup_info

        except Exception as e:
            step.fail(str(e))
            raise

    def _execute_generation_stage(
        self,
        workflow: WorkflowState,
        file_path: Path,
        custom_variables: dict[str, Any] | None,
    ) -> dict[str, Path]:
        """Execute content generation stage."""
        step = workflow.add_step("Generate spec content", WorkflowStage.GENERATION)
        step.start()

        try:
            # Load template
            template = load_template()

            # Generate content
            generated_files = self.content_generator.generate_spec_content(
                file_path=file_path,
                template=template,
                custom_variables=custom_variables,
                backup_existing=True,
            )

            step.complete(
                {
                    "generated_files": {k: str(v) for k, v in generated_files.items()},
                    "template_used": getattr(template, "description", None)
                    or "default",
                }
            )

            return generated_files

        except Exception as e:
            step.fail(str(e))
            raise

    def _execute_commit_stage(
        self, workflow: WorkflowState, file_path: Path, generated_files: dict[str, Path]
    ) -> dict[str, Any]:
        """Execute commit stage."""
        step = workflow.add_step("Commit generated content", WorkflowStage.COMMIT)
        step.start()

        try:
            # Add generated files to staging
            file_paths = []
            for _file_type, full_path in generated_files.items():
                # Convert to relative path from .specs
                try:
                    relative_path = full_path.relative_to(self.settings.specs_dir)
                    file_paths.append(str(relative_path))
                except ValueError:
                    debug_logger.log(
                        "WARNING",
                        "Generated file outside .specs directory",
                        file_path=str(full_path),
                    )

            if not file_paths:
                raise SpecWorkflowError("No files to commit")

            # Add files
            add_result = self.commit_manager.add_files(file_paths)
            if not add_result["success"]:
                raise SpecWorkflowError(
                    f"Failed to add files: {'; '.join(add_result['errors'])}"
                )

            # Commit changes
            commit_message = (
                f"Generate spec documentation for {file_path.name}\n\nFiles generated:\n"
                + "\n".join(f"- {fp}" for fp in file_paths)
            )

            commit_result = self.commit_manager.commit_changes(commit_message)
            if not commit_result["success"]:
                raise SpecWorkflowError(
                    f"Failed to commit: {'; '.join(commit_result['errors'])}"
                )

            commit_info = {
                "commit_hash": commit_result["commit_hash"],
                "files_committed": file_paths,
                "commit_message": commit_message,
            }

            step.complete(commit_info)
            return commit_info

        except Exception as e:
            step.fail(str(e))
            raise

    def _execute_cleanup_stage(self, workflow: WorkflowState) -> None:
        """Execute cleanup stage."""
        step = workflow.add_step("Cleanup temporary files", WorkflowStage.CLEANUP)
        step.start()

        try:
            # Cleanup any temporary files or state
            # Currently minimal, but provides extension point

            step.complete({"cleaned_up": True})

        except Exception as e:
            # Cleanup failures are warnings, not errors
            step.fail(str(e))
            debug_logger.log("WARNING", "Cleanup stage failed", error=str(e))

    def _execute_rollback_stage(self, workflow: WorkflowState, error: str) -> None:
        """Execute rollback stage."""
        step = workflow.add_step("Rollback changes", WorkflowStage.ROLLBACK)
        step.start()

        try:
            backup_commit = workflow.metadata.get("backup_commit")
            if backup_commit:
                rollback_result = self.commit_manager.rollback_to_commit(
                    backup_commit, hard=True, create_backup=False
                )

                if rollback_result["success"]:
                    step.complete(
                        {
                            "rolled_back_to": backup_commit,
                            "reason": error,
                        }
                    )
                else:
                    step.fail(
                        f"Rollback failed: {'; '.join(rollback_result['errors'])}"
                    )
            else:
                step.fail("No backup commit available for rollback")

        except Exception as e:
            step.fail(str(e))
            raise

    def generate_specs_for_files(
        self,
        file_paths: list[Path],
        custom_variables: dict[str, Any] | None = None,
        auto_commit: bool = True,
        create_backup: bool = True,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, Any]:
        """Generate spec documentation for multiple files.

        Args:
            file_paths: List of file paths to generate specs for
            custom_variables: Optional custom variables for template substitution
            auto_commit: Whether to automatically commit generated content
            create_backup: Whether to create backup before generation
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with batch workflow results
        """
        debug_logger.log(
            "INFO",
            "Starting batch spec generation workflow",
            file_count=len(file_paths),
            auto_commit=auto_commit,
        )

        # Create batch workflow
        workflow = workflow_state_manager.create_workflow(
            "batch_spec_generation",
            {
                "file_paths": [str(fp) for fp in file_paths],
                "auto_commit": auto_commit,
                "create_backup": create_backup,
                "custom_variables": custom_variables or {},
            },
        )

        try:
            workflow.start()

            with debug_logger.timer("batch_spec_generation_workflow"):
                results: dict[str, Any] = {
                    "success": True,
                    "workflow_id": workflow.workflow_id,
                    "total_files": len(file_paths),
                    "successful_files": [],
                    "failed_files": [],
                    "generated_files": {},
                    "commit_info": None,
                    "backup_info": None,
                }

                # Global batch validation
                batch_validation = self.workflow_validator.validate_batch_operation(
                    file_paths, "generate"
                )

                if batch_validation["global_issues"]:
                    error_msg = f"Batch validation failed: {'; '.join(batch_validation['global_issues'])}"
                    raise SpecWorkflowError(error_msg)

                # Store validation results for use during processing
                workflow.metadata["batch_validation"] = batch_validation

                # Global backup
                if create_backup:
                    results["backup_info"] = self._execute_backup_stage(workflow)

                # Process valid files only (skip files that failed validation)
                valid_files = batch_validation["valid_files"]
                invalid_files = batch_validation["invalid_files"]

                # Add invalid files to failed results
                for file_path, issues in invalid_files.items():
                    results["failed_files"].append(
                        {
                            "file_path": str(file_path),
                            "error": f"Validation failed: {'; '.join(issues)}",
                        }
                    )

                # Process each file (valid ones only, but maintain original indices for progress)
                valid_file_set = set(valid_files)
                for i, file_path in enumerate(file_paths):
                    if progress_callback:
                        progress_callback(
                            i, len(file_paths), f"Processing {file_path.name}"
                        )

                    # Skip invalid files (already added to failed_files above)
                    if file_path not in valid_file_set:
                        continue

                    try:
                        file_result = self.generate_spec_for_file(
                            file_path,
                            custom_variables=custom_variables,
                            auto_commit=False,  # Batch commit at the end
                            create_backup=False,  # Already created global backup
                        )

                        results["successful_files"].append(str(file_path))
                        results["generated_files"][str(file_path)] = file_result[
                            "generated_files"
                        ]

                    except Exception as e:
                        debug_logger.log(
                            "ERROR",
                            "File processing failed",
                            file_path=str(file_path),
                            error=str(e),
                        )
                        results["failed_files"].append(
                            {
                                "file_path": str(file_path),
                                "error": str(e),
                            }
                        )

                # Batch commit if requested and we have successful files
                if auto_commit and results["successful_files"]:
                    commit_info = self._execute_batch_commit_stage(workflow, results)
                    results["commit_info"] = commit_info

                # Final progress update
                if progress_callback:
                    progress_callback(len(file_paths), len(file_paths), "Completed")

                # Mark as failed if no files were successful
                if not results["successful_files"]:
                    results["success"] = False

                workflow.complete()
                workflow_state_manager.complete_workflow(workflow.workflow_id)

            debug_logger.log(
                "INFO",
                "Batch spec generation workflow completed",
                workflow_id=workflow.workflow_id,
                successful=len(results["successful_files"]),
                failed=len(results["failed_files"]),
            )

            return results

        except Exception as e:
            error_msg = f"Batch spec generation workflow failed: {e}"
            debug_logger.log("ERROR", error_msg)

            workflow.fail(error_msg)
            workflow_state_manager.fail_workflow(workflow.workflow_id, error_msg)

            raise SpecWorkflowError(error_msg) from e

    def _execute_batch_commit_stage(
        self, workflow: WorkflowState, batch_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute batch commit stage."""
        step = workflow.add_step("Batch commit generated content", WorkflowStage.COMMIT)
        step.start()

        try:
            # Collect all generated files
            all_file_paths = []
            for _file_path, generated_files in batch_results["generated_files"].items():
                for _file_type, full_path in generated_files.items():
                    try:
                        relative_path = Path(full_path).relative_to(
                            self.settings.specs_dir
                        )
                        all_file_paths.append(str(relative_path))
                    except ValueError:
                        debug_logger.log(
                            "WARNING",
                            "Generated file outside .specs directory",
                            file_path=str(full_path),
                        )

            if not all_file_paths:
                raise SpecWorkflowError("No files to commit")

            # Add all files
            add_result = self.commit_manager.add_files(all_file_paths)
            if not add_result["success"]:
                raise SpecWorkflowError(
                    f"Failed to add files: {'; '.join(add_result['errors'])}"
                )

            # Create batch commit message
            successful_files = batch_results["successful_files"]
            commit_message = (
                f"Generate spec documentation for {len(successful_files)} files\n\n"
                + "Files processed:\n"
                + "\n".join(f"- {fp}" for fp in successful_files[:10])
            )  # Limit for readability

            if len(successful_files) > 10:
                commit_message += f"\n... and {len(successful_files) - 10} more files"

            # Commit changes
            commit_result = self.commit_manager.commit_changes(commit_message)
            if not commit_result["success"]:
                raise SpecWorkflowError(
                    f"Failed to commit: {'; '.join(commit_result['errors'])}"
                )

            commit_info = {
                "commit_hash": commit_result["commit_hash"],
                "files_committed": all_file_paths,
                "commit_message": commit_message,
                "batch_size": len(successful_files),
            }

            step.complete(commit_info)
            return commit_info

        except Exception as e:
            step.fail(str(e))
            raise

    def create_pull_request_stub(
        self,
        workflow_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Stub for PR creation integration (future implementation).

        Args:
            workflow_id: ID of the workflow to create PR for
            title: Optional PR title
            description: Optional PR description

        Returns:
            Dictionary with PR creation results (stub)
        """
        debug_logger.log(
            "INFO", "PR creation requested (stub)", workflow_id=workflow_id
        )

        # Get workflow info
        workflow = workflow_state_manager.get_workflow(workflow_id)
        if not workflow:
            raise SpecWorkflowError(f"Workflow not found: {workflow_id}")

        # Stub implementation - in the future this would integrate with
        # GitHub/GitLab APIs to create actual pull requests
        pr_info = {
            "success": True,
            "pr_url": "https://github.com/example/repo/pull/123",  # Stub URL
            "pr_number": 123,  # Stub number
            "title": title or f"Spec documentation update - {workflow_id}",
            "description": description or "Generated spec documentation via spec CLI",
            "workflow_id": workflow_id,
            "implementation_status": "stub",
        }

        debug_logger.log(
            "INFO",
            "PR creation completed (stub)",
            workflow_id=workflow_id,
            pr_number=pr_info["pr_number"],
        )

        return pr_info

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get status of a specific workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Dictionary with workflow status or None if not found
        """
        workflow = workflow_state_manager.get_workflow(workflow_id)
        if not workflow:
            return None

        status = workflow.get_summary()

        # Add step details
        status["steps"] = [
            {
                "name": step.name,
                "stage": step.stage.value,
                "status": step.status.value,
                "duration": step.duration,
                "error": step.error,
            }
            for step in workflow.steps
        ]

        return status

    def list_active_workflows(self) -> list[dict[str, Any]]:
        """List all active workflows.

        Returns:
            List of workflow summary dictionaries
        """
        active_workflows = workflow_state_manager.get_active_workflows()
        return [workflow.get_summary() for workflow in active_workflows]

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow.

        Args:
            workflow_id: ID of the workflow to cancel

        Returns:
            True if workflow was cancelled successfully
        """
        workflow = workflow_state_manager.get_workflow(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow_state_manager.fail_workflow(workflow_id, "Cancelled by user")

        debug_logger.log("INFO", "Workflow cancelled", workflow_id=workflow_id)
        return True
