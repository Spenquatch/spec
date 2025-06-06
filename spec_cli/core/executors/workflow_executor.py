"""Workflow execution component for handling execution stages of spec workflows.

This module provides the WorkflowExecutor class which handles the actual execution
of workflow stages after validation and setup. It manages the content generation,
commit operations, and cleanup phases while maintaining workflow state tracking.

Key responsibilities:
- Executing generation stage using content_generator
- Conditionally executing commit stage if auto_commit is enabled
- Executing cleanup stage for temporary resources
- Returning structured execution results with generated files
"""

from pathlib import Path
from typing import Any

from ...config.settings import SpecSettings
from ...exceptions import SpecWorkflowError
from ...logging.debug import debug_logger
from ...templates.generator import SpecContentGenerator
from ...templates.loader import load_template
from ...utils.error_handler import ErrorHandler
from ...utils.path_utils import safe_relative_to
from ...utils.workflow_utils import create_workflow_result
from ..commit_manager import SpecCommitManager
from ..workflow_state import WorkflowStage, WorkflowState


class WorkflowExecutor:
    """Executes workflow stages for spec generation workflows."""

    def __init__(
        self,
        content_generator: SpecContentGenerator,
        commit_manager: SpecCommitManager,
        settings: SpecSettings,
    ):
        """Initialize the workflow executor with required dependencies.

        Args:
            content_generator: Generator for creating spec content
            commit_manager: Manager for Git operations and commits
            settings: Configuration settings for the spec system

        The executor requires pre-configured components for content generation
        and commit management to handle the actual workflow execution phases.
        """
        self.content_generator = content_generator
        self.commit_manager = commit_manager
        self.settings = settings
        self.error_handler = ErrorHandler({"component": "WorkflowExecutor"})

        debug_logger.log("INFO", "WorkflowExecutor initialized")

    def execute_workflow(
        self,
        workflow: WorkflowState,
        file_path: Path,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the complete workflow for spec generation.

        Args:
            workflow: Current workflow state for tracking progress
            file_path: Path to source file for spec generation
            options: Configuration options including auto_commit, custom_variables

        Returns:
            Dictionary with execution results containing success status,
            generated files mapping, and optional commit information

        Raises:
            SpecWorkflowError: If any execution stage fails

        The execution follows this sequence:
        1. Generate spec content using content_generator
        2. Conditionally commit if auto_commit is enabled
        3. Clean up temporary resources
        4. Return structured results
        """
        debug_logger.log(
            "INFO",
            "Starting workflow execution",
            file_path=str(file_path),
            workflow_id=workflow.workflow_id,
        )

        try:
            # Execute generation stage
            generated_files = self._execute_generation_stage(
                workflow, file_path, options.get("custom_variables")
            )

            # Execute commit stage if requested
            commit_info = None
            if options.get("auto_commit", True):
                commit_info = self._execute_commit_stage(
                    workflow, file_path, generated_files
                )

            # Execute cleanup stage
            self._execute_cleanup_stage(workflow)

            # Create structured result
            result = create_workflow_result(
                files=[file_path], success=True, workflow_id=workflow.workflow_id
            )
            result["generated_files"] = {str(file_path): generated_files}
            result["commit_info"] = commit_info

            debug_logger.log(
                "INFO",
                "Workflow execution completed successfully",
                workflow_id=workflow.workflow_id,
                generated_count=len(generated_files),
            )

            return result

        except Exception as e:
            self.error_handler.report(
                e,
                "execute workflow",
                code_path=file_path,
                workflow_id=workflow.workflow_id,
                options=options,
            )
            raise SpecWorkflowError(f"Workflow execution failed: {e}") from e

    def _execute_generation_stage(
        self,
        workflow: WorkflowState,
        file_path: Path,
        custom_variables: dict[str, Any] | None,
    ) -> dict[str, Path]:
        """Execute content generation stage.

        Args:
            workflow: Current workflow state for progress tracking
            file_path: Path to source file for spec generation
            custom_variables: Optional custom variables for template substitution

        Returns:
            Dictionary mapping file types to generated file paths

        Raises:
            SpecWorkflowError: If content generation fails

        This stage loads the template and generates spec content using the
        content generator component.
        """
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
            self.error_handler.report(
                e,
                "generate spec content",
                code_path=file_path,
                workflow_id=workflow.workflow_id,
            )
            raise

    def _execute_commit_stage(
        self, workflow: WorkflowState, file_path: Path, generated_files: dict[str, Path]
    ) -> dict[str, Any]:
        """Execute commit stage for generated files.

        Args:
            workflow: Current workflow state for progress tracking
            file_path: Original source file path for commit message
            generated_files: Dictionary of generated files to commit

        Returns:
            Dictionary with commit information including hash and files

        Raises:
            SpecWorkflowError: If commit operations fail

        This stage adds generated files to Git staging and creates a commit
        with a descriptive message about the spec generation.
        """
        step = workflow.add_step("Commit generated content", WorkflowStage.COMMIT)
        step.start()

        try:
            # Convert generated files to relative paths for Git
            file_paths = []
            for _file_type, full_path in generated_files.items():
                relative_path = safe_relative_to(
                    full_path, self.settings.specs_dir, strict=False
                )
                # safe_relative_to returns the original path if not strict and outside root
                if Path(full_path) != relative_path:
                    file_paths.append(str(relative_path))
                else:
                    debug_logger.log(
                        "WARNING",
                        "Generated file outside .specs directory",
                        file_path=str(full_path),
                    )

            if not file_paths:
                raise SpecWorkflowError("No files to commit")

            # Add files to staging
            add_result = self.commit_manager.add_files(file_paths)
            if not add_result["success"]:
                raise SpecWorkflowError(
                    f"Failed to add files: {'; '.join(add_result['errors'])}"
                )

            # Create commit with descriptive message
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
            self.error_handler.report(
                e,
                "commit generated files",
                code_path=file_path,
                workflow_id=workflow.workflow_id,
            )
            raise

    def _execute_cleanup_stage(self, workflow: WorkflowState) -> None:
        """Execute cleanup stage for temporary resources.

        Args:
            workflow: Current workflow state for progress tracking

        This stage performs cleanup of any temporary files or state.
        Cleanup failures are logged as warnings rather than errors
        to avoid failing the entire workflow.
        """
        step = workflow.add_step("Cleanup temporary files", WorkflowStage.CLEANUP)
        step.start()

        try:
            # Cleanup any temporary files or state
            # Currently minimal, but provides extension point

            step.complete({"cleaned_up": True})

        except Exception as e:
            # Cleanup failures are warnings, not errors
            step.fail(str(e))
            debug_logger.log(
                "WARNING",
                "Cleanup stage failed",
                error=str(e),
                workflow_id=workflow.workflow_id,
            )
