# Slice 10C: Spec Workflow Orchestration

## Goal

Orchestrate high-level spec generation workflow, backup branch management, and PR creation. Relies on slice-8b generator and slice-10b Git operations without other dependencies.

## Context

Building on the Git operations from slice-10b and spec generation from slice-8b, this slice creates the high-level workflow orchestration. It focuses on coordinating multiple systems to provide complete spec generation workflows, including backup strategies and integration points for future PR automation.

## Scope

**Included in this slice:**
- SpecWorkflowOrchestrator for high-level workflow coordination
- Spec generation workflow with backup and rollback
- Branch management for safe spec operations
- Integration points for PR creation (stubbed for future)
- Workflow state tracking and progress monitoring
- Error recovery and cleanup workflows

**NOT included in this slice:**
- Change detection and file processing (comes in slice-11)
- Actual PR creation implementation (integration points only)
- Rich UI integration (comes in PHASE-5)
- Batch processing workflows (comes in slice-11c)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for workflow errors)
- `spec_cli.logging.debug` (debug_logger for workflow tracking)
- `spec_cli.config.settings` (SpecSettings for workflow configuration)
- `spec_cli.core.repository_state` (RepositoryStateChecker for validation)
- `spec_cli.core.commit_manager` (SpecCommitManager for Git operations)
- `spec_cli.templates.generator` (SpecContentGenerator for content generation)
- `spec_cli.file_system.directory_manager` (DirectoryManager for file operations)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `RepositoryStateChecker` from slice-10a-repo-init
- `SpecCommitManager` from slice-10b-commit-wrappers
- `SpecContentGenerator` from slice-8b-spec-generator
- `DirectoryManager` from slice-6b-directory-operations

## Files to Create

```
spec_cli/core/
├── workflow_orchestrator.py # SpecWorkflowOrchestrator class
└── workflow_state.py        # Workflow state tracking utilities
```

## Implementation Steps

### Step 1: Create spec_cli/core/workflow_state.py

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..logging.debug import debug_logger

class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"

class WorkflowStage(Enum):
    """Workflow execution stages."""
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    BACKUP = "backup"
    GENERATION = "generation"
    COMMIT = "commit"
    TAG = "tag"
    CLEANUP = "cleanup"
    ROLLBACK = "rollback"

@dataclass
class WorkflowStep:
    """Individual workflow step with timing and results."""
    name: str
    stage: WorkflowStage
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def start(self) -> None:
        """Mark step as started."""
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed."""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.result = result or {}
    
    def fail(self, error: str) -> None:
        """Mark step as failed."""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.error = error

@dataclass
class WorkflowState:
    """Complete workflow state tracking."""
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Start the workflow."""
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
        debug_logger.log("INFO", "Workflow started", 
                        workflow_id=self.workflow_id,
                        workflow_type=self.workflow_type)
    
    def complete(self) -> None:
        """Complete the workflow."""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        debug_logger.log("INFO", "Workflow completed", 
                        workflow_id=self.workflow_id,
                        duration=self.duration)
    
    def fail(self, error: str) -> None:
        """Fail the workflow."""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        debug_logger.log("ERROR", "Workflow failed", 
                        workflow_id=self.workflow_id,
                        error=error)
    
    def add_step(self, name: str, stage: WorkflowStage) -> WorkflowStep:
        """Add a new step to the workflow."""
        step = WorkflowStep(name=name, stage=stage)
        self.steps.append(step)
        return step
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the currently running step."""
        for step in reversed(self.steps):
            if step.status == WorkflowStatus.RUNNING:
                return step
        return None
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get all failed steps."""
        return [step for step in self.steps if step.status == WorkflowStatus.FAILED]
    
    def get_completed_steps(self) -> List[WorkflowStep]:
        """Get all completed steps."""
        return [step for step in self.steps if step.status == WorkflowStatus.COMPLETED]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status.value,
            "duration": self.duration,
            "total_steps": len(self.steps),
            "completed_steps": len(self.get_completed_steps()),
            "failed_steps": len(self.get_failed_steps()),
            "current_stage": self.get_current_step().stage.value if self.get_current_step() else None,
        }

class WorkflowStateManager:
    """Manages workflow state tracking and persistence."""
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: List[WorkflowState] = []
        debug_logger.log("INFO", "WorkflowStateManager initialized")
    
    def create_workflow(self, workflow_type: str, metadata: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """Create a new workflow."""
        workflow_id = f"{workflow_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        workflow = WorkflowState(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            metadata=metadata or {}
        )
        
        self.active_workflows[workflow_id] = workflow
        debug_logger.log("INFO", "Workflow created", 
                        workflow_id=workflow_id,
                        workflow_type=workflow_type)
        
        return workflow
    
    def complete_workflow(self, workflow_id: str) -> None:
        """Mark workflow as completed and archive it."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.complete()
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            # Keep history limited
            if len(self.workflow_history) > 100:
                self.workflow_history = self.workflow_history[-50:]
    
    def fail_workflow(self, workflow_id: str, error: str) -> None:
        """Mark workflow as failed and archive it."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.fail(error)
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow by ID."""
        # Check active workflows first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check history
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        return None
    
    def get_active_workflows(self) -> List[WorkflowState]:
        """Get all active workflows."""
        return list(self.active_workflows.values())
    
    def get_recent_workflows(self, count: int = 10) -> List[WorkflowState]:
        """Get recent workflows from history."""
        return self.workflow_history[-count:] if self.workflow_history else []
    
    def cleanup_stale_workflows(self, max_age_hours: int = 24) -> int:
        """Clean up stale workflows that have been running too long."""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        stale_count = 0
        
        stale_workflows = []
        for workflow_id, workflow in self.active_workflows.items():
            if workflow.start_time and workflow.start_time < cutoff_time:
                stale_workflows.append(workflow_id)
        
        for workflow_id in stale_workflows:
            self.fail_workflow(workflow_id, f"Workflow stale (running > {max_age_hours} hours)")
            stale_count += 1
        
        if stale_count > 0:
            debug_logger.log("INFO", "Cleaned up stale workflows", count=stale_count)
        
        return stale_count

# Global workflow state manager
workflow_state_manager = WorkflowStateManager()
```

### Step 2: Create spec_cli/core/workflow_orchestrator.py

```python
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from ..exceptions import SpecWorkflowError, SpecGitError, SpecTemplateError
from ..config.settings import get_settings, SpecSettings
from ..templates.generator import SpecContentGenerator
from ..templates.loader import load_template
from ..file_system.directory_manager import DirectoryManager
from ..logging.debug import debug_logger
from .repository_state import RepositoryStateChecker
from .commit_manager import SpecCommitManager
from .workflow_state import (
    WorkflowState, WorkflowStatus, WorkflowStage, 
    workflow_state_manager
)

class SpecWorkflowOrchestrator:
    """Orchestrates high-level spec generation workflows."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.state_checker = RepositoryStateChecker(self.settings)
        self.commit_manager = SpecCommitManager(self.settings)
        self.content_generator = SpecContentGenerator(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
        
        debug_logger.log("INFO", "SpecWorkflowOrchestrator initialized")
    
    def generate_spec_for_file(self,
                              file_path: Path,
                              custom_variables: Optional[Dict[str, Any]] = None,
                              auto_commit: bool = True,
                              create_backup: bool = True) -> Dict[str, Any]:
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
        debug_logger.log("INFO", "Starting spec generation workflow",
                        file_path=str(file_path),
                        auto_commit=auto_commit,
                        create_backup=create_backup)
        
        # Create workflow
        workflow = workflow_state_manager.create_workflow(
            "spec_generation",
            {
                "file_path": str(file_path),
                "auto_commit": auto_commit,
                "create_backup": create_backup,
                "custom_variables": custom_variables or {},
            }
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
            
            debug_logger.log("INFO", "Spec generation workflow completed",
                           workflow_id=workflow.workflow_id,
                           duration=workflow.duration)
            
            return result
            
        except Exception as e:
            error_msg = f"Spec generation workflow failed: {e}"
            debug_logger.log("ERROR", error_msg)
            
            # Attempt rollback if backup was created
            if create_backup and workflow.metadata.get("backup_commit"):
                try:
                    self._execute_rollback_stage(workflow, str(e))
                except Exception as rollback_error:
                    debug_logger.log("ERROR", "Rollback failed", error=str(rollback_error))
            
            workflow.fail(error_msg)
            workflow_state_manager.fail_workflow(workflow.workflow_id, error_msg)
            
            raise SpecWorkflowError(error_msg) from e
    
    def _execute_validation_stage(self, workflow: WorkflowState, file_path: Path) -> None:
        """Execute validation stage."""
        step = workflow.add_step("Pre-flight validation", WorkflowStage.VALIDATION)
        step.start()
        
        try:
            # Check repository health
            if not self.state_checker.is_safe_for_spec_operations():
                raise SpecWorkflowError("Repository is not safe for spec operations")
            
            # Validate file exists
            if not file_path.exists():
                raise SpecWorkflowError(f"Source file does not exist: {file_path}")
            
            # Check pre-operation state
            validation_issues = self.state_checker.validate_pre_operation_state("generate")
            if validation_issues:
                raise SpecWorkflowError(f"Validation failed: {'; '.join(validation_issues)}")
            
            step.complete({"validated": True})
            
        except Exception as e:
            step.fail(str(e))
            raise
    
    def _execute_backup_stage(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute backup stage."""
        step = workflow.add_step("Create backup", WorkflowStage.BACKUP)
        step.start()
        
        try:
            # Create backup tag
            backup_tag = f"backup-{workflow.workflow_id}"
            tag_result = self.commit_manager.create_tag(
                backup_tag,
                f"Backup before spec generation workflow {workflow.workflow_id}"
            )
            
            if not tag_result["success"]:
                raise SpecWorkflowError(f"Backup creation failed: {'; '.join(tag_result['errors'])}")
            
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
    
    def _execute_generation_stage(self,
                                 workflow: WorkflowState,
                                 file_path: Path,
                                 custom_variables: Optional[Dict[str, Any]]) -> Dict[str, Path]:
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
                backup_existing=True
            )
            
            step.complete({
                "generated_files": {k: str(v) for k, v in generated_files.items()},
                "template_used": template.name,
            })
            
            return generated_files
            
        except Exception as e:
            step.fail(str(e))
            raise
    
    def _execute_commit_stage(self,
                             workflow: WorkflowState,
                             file_path: Path,
                             generated_files: Dict[str, Path]) -> Dict[str, Any]:
        """Execute commit stage."""
        step = workflow.add_step("Commit generated content", WorkflowStage.COMMIT)
        step.start()
        
        try:
            # Add generated files to staging
            file_paths = []
            for file_type, full_path in generated_files.items():
                # Convert to relative path from .specs
                try:
                    relative_path = full_path.relative_to(self.settings.specs_dir)
                    file_paths.append(str(relative_path))
                except ValueError:
                    debug_logger.log("WARNING", "Generated file outside .specs directory",
                                   file_path=str(full_path))
            
            if not file_paths:
                raise SpecWorkflowError("No files to commit")
            
            # Add files
            add_result = self.commit_manager.add_files(file_paths)
            if not add_result["success"]:
                raise SpecWorkflowError(f"Failed to add files: {'; '.join(add_result['errors'])}")
            
            # Commit changes
            commit_message = f"Generate spec documentation for {file_path.name}\n\nFiles generated:\n" + \
                           "\n".join(f"- {fp}" for fp in file_paths)
            
            commit_result = self.commit_manager.commit_changes(commit_message)
            if not commit_result["success"]:
                raise SpecWorkflowError(f"Failed to commit: {'; '.join(commit_result['errors'])}")
            
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
                    step.complete({
                        "rolled_back_to": backup_commit,
                        "reason": error,
                    })
                else:
                    step.fail(f"Rollback failed: {'; '.join(rollback_result['errors'])}")
            else:
                step.fail("No backup commit available for rollback")
                
        except Exception as e:
            step.fail(str(e))
            raise
    
    def generate_specs_for_files(self,
                                file_paths: List[Path],
                                custom_variables: Optional[Dict[str, Any]] = None,
                                auto_commit: bool = True,
                                create_backup: bool = True,
                                progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict[str, Any]:
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
        debug_logger.log("INFO", "Starting batch spec generation workflow",
                        file_count=len(file_paths),
                        auto_commit=auto_commit)
        
        # Create batch workflow
        workflow = workflow_state_manager.create_workflow(
            "batch_spec_generation",
            {
                "file_paths": [str(fp) for fp in file_paths],
                "auto_commit": auto_commit,
                "create_backup": create_backup,
                "custom_variables": custom_variables or {},
            }
        )
        
        try:
            workflow.start()
            
            with debug_logger.timer("batch_spec_generation_workflow"):
                results = {
                    "success": True,
                    "workflow_id": workflow.workflow_id,
                    "total_files": len(file_paths),
                    "successful_files": [],
                    "failed_files": [],
                    "generated_files": {},
                    "commit_info": None,
                    "backup_info": None,
                }
                
                # Global validation
                self._execute_validation_stage(workflow, file_paths[0] if file_paths else Path("."))
                
                # Global backup
                if create_backup:
                    results["backup_info"] = self._execute_backup_stage(workflow)
                
                # Process each file
                for i, file_path in enumerate(file_paths):
                    if progress_callback:
                        progress_callback(i, len(file_paths), f"Processing {file_path.name}")
                    
                    try:
                        file_result = self.generate_spec_for_file(
                            file_path,
                            custom_variables=custom_variables,
                            auto_commit=False,  # Batch commit at the end
                            create_backup=False  # Already created global backup
                        )
                        
                        results["successful_files"].append(str(file_path))
                        results["generated_files"][str(file_path)] = file_result["generated_files"]
                        
                    except Exception as e:
                        debug_logger.log("ERROR", "File processing failed",
                                       file_path=str(file_path), error=str(e))
                        results["failed_files"].append({
                            "file_path": str(file_path),
                            "error": str(e),
                        })
                
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
            
            debug_logger.log("INFO", "Batch spec generation workflow completed",
                           workflow_id=workflow.workflow_id,
                           successful=len(results["successful_files"]),
                           failed=len(results["failed_files"]))
            
            return results
            
        except Exception as e:
            error_msg = f"Batch spec generation workflow failed: {e}"
            debug_logger.log("ERROR", error_msg)
            
            workflow.fail(error_msg)
            workflow_state_manager.fail_workflow(workflow.workflow_id, error_msg)
            
            raise SpecWorkflowError(error_msg) from e
    
    def _execute_batch_commit_stage(self, workflow: WorkflowState, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute batch commit stage."""
        step = workflow.add_step("Batch commit generated content", WorkflowStage.COMMIT)
        step.start()
        
        try:
            # Collect all generated files
            all_file_paths = []
            for file_path, generated_files in batch_results["generated_files"].items():
                for file_type, full_path in generated_files.items():
                    try:
                        relative_path = Path(full_path).relative_to(self.settings.specs_dir)
                        all_file_paths.append(str(relative_path))
                    except ValueError:
                        debug_logger.log("WARNING", "Generated file outside .specs directory",
                                       file_path=str(full_path))
            
            if not all_file_paths:
                raise SpecWorkflowError("No files to commit")
            
            # Add all files
            add_result = self.commit_manager.add_files(all_file_paths)
            if not add_result["success"]:
                raise SpecWorkflowError(f"Failed to add files: {'; '.join(add_result['errors'])}")
            
            # Create batch commit message
            successful_files = batch_results["successful_files"]
            commit_message = f"Generate spec documentation for {len(successful_files)} files\n\n" + \
                           "Files processed:\n" + \
                           "\n".join(f"- {fp}" for fp in successful_files[:10])  # Limit for readability
            
            if len(successful_files) > 10:
                commit_message += f"\n... and {len(successful_files) - 10} more files"
            
            # Commit changes
            commit_result = self.commit_manager.commit_changes(commit_message)
            if not commit_result["success"]:
                raise SpecWorkflowError(f"Failed to commit: {'; '.join(commit_result['errors'])}")
            
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
    
    def create_pull_request_stub(self,
                                workflow_id: str,
                                title: Optional[str] = None,
                                description: Optional[str] = None) -> Dict[str, Any]:
        """Stub for PR creation integration (future implementation).
        
        Args:
            workflow_id: ID of the workflow to create PR for
            title: Optional PR title
            description: Optional PR description
            
        Returns:
            Dictionary with PR creation results (stub)
        """
        debug_logger.log("INFO", "PR creation requested (stub)",
                        workflow_id=workflow_id)
        
        # Get workflow info
        workflow = workflow_state_manager.get_workflow(workflow_id)
        if not workflow:
            raise SpecWorkflowError(f"Workflow not found: {workflow_id}")
        
        # Stub implementation - in the future this would integrate with
        # GitHub/GitLab APIs to create actual pull requests
        pr_info = {
            "success": True,
            "pr_url": f"https://github.com/example/repo/pull/123",  # Stub URL
            "pr_number": 123,  # Stub number
            "title": title or f"Spec documentation update - {workflow_id}",
            "description": description or "Generated spec documentation via spec CLI",
            "workflow_id": workflow_id,
            "implementation_status": "stub",
        }
        
        debug_logger.log("INFO", "PR creation completed (stub)",
                        workflow_id=workflow_id,
                        pr_number=pr_info["pr_number"])
        
        return pr_info
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
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
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
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
```

### Step 3: Update spec_cli/core/__init__.py

```python
"""Core business logic for spec CLI.

This package contains the main orchestration logic for spec operations,
repository management, and high-level workflows.
"""

from .repository_init import SpecRepositoryInitializer
from .repository_state import RepositoryStateChecker
from .commit_manager import SpecCommitManager
from .workflow_orchestrator import SpecWorkflowOrchestrator
from .workflow_state import WorkflowState, WorkflowStatus, workflow_state_manager

__all__ = [
    "SpecRepositoryInitializer",
    "RepositoryStateChecker",
    "SpecCommitManager",
    "SpecWorkflowOrchestrator",
    "WorkflowState",
    "WorkflowStatus",
    "workflow_state_manager",
]
```

## Test Requirements

Create comprehensive tests for workflow orchestration:

### Test Cases (15 tests total)

**Workflow State Management Tests:**
1. **test_workflow_state_creation_and_tracking**
2. **test_workflow_step_execution_and_timing**
3. **test_workflow_state_manager_lifecycle**
4. **test_workflow_cleanup_and_archival**

**Single File Workflow Tests:**
5. **test_generate_spec_for_file_complete_workflow**
6. **test_generate_spec_for_file_with_backup**
7. **test_generate_spec_for_file_validation_failure**
8. **test_generate_spec_for_file_rollback_on_error**

**Batch Workflow Tests:**
9. **test_generate_specs_for_multiple_files**
10. **test_batch_workflow_partial_failures**
11. **test_batch_workflow_progress_tracking**

**Workflow Management Tests:**
12. **test_workflow_status_monitoring**
13. **test_workflow_cancellation**
14. **test_pull_request_stub_integration**
15. **test_workflow_error_recovery**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/core/test_workflow_orchestrator.py tests/unit/core/test_workflow_state.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/core/test_workflow_orchestrator.py tests/unit/core/test_workflow_state.py --cov=spec_cli.core.workflow_orchestrator --cov=spec_cli.core.workflow_state --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/core/workflow_orchestrator.py spec_cli/core/workflow_state.py

# Check code formatting
poetry run ruff check spec_cli/core/workflow_orchestrator.py spec_cli/core/workflow_state.py
poetry run ruff format spec_cli/core/workflow_orchestrator.py spec_cli/core/workflow_state.py

# Verify imports work correctly
python -c "from spec_cli.core.workflow_orchestrator import SpecWorkflowOrchestrator; from spec_cli.core.workflow_state import workflow_state_manager; print('Import successful')"

# Test workflow state management
python -c "
from spec_cli.core.workflow_state import workflow_state_manager, WorkflowStage

# Create a test workflow
workflow = workflow_state_manager.create_workflow('test', {'test': True})
print(f'Created workflow: {workflow.workflow_id}')

# Add and execute steps
step1 = workflow.add_step('Test step 1', WorkflowStage.INITIALIZATION)
step1.start()
step1.complete({'result': 'success'})

step2 = workflow.add_step('Test step 2', WorkflowStage.VALIDATION)
step2.start()
step2.fail('Test failure')

# Get workflow summary
summary = workflow.get_summary()
print(f'Workflow summary:')
for key, value in summary.items():
    print(f'  {key}: {value}')

print(f'Failed steps: {len(workflow.get_failed_steps())}')
print(f'Completed steps: {len(workflow.get_completed_steps())}')
"

# Test workflow orchestrator basic functionality
python -c "
from spec_cli.core.workflow_orchestrator import SpecWorkflowOrchestrator
from pathlib import Path

orchestrator = SpecWorkflowOrchestrator()

# List active workflows
active = orchestrator.list_active_workflows()
print(f'Active workflows: {len(active)}')

# Test PR stub
try:
    pr_result = orchestrator.create_pull_request_stub(
        'test-workflow-123',
        title='Test PR',
        description='Test description'
    )
    print(f'PR creation stub result:')
    print(f'  Success: {pr_result["success"]}')
    print(f'  Status: {pr_result["implementation_status"]}')
    print(f'  URL: {pr_result["pr_url"]}')
except Exception as e:
    print(f'PR stub test failed (expected): {e}')

# Test workflow status
status = orchestrator.get_workflow_status('nonexistent')
print(f'Status for nonexistent workflow: {status}')
"

# Test workflow state manager features
python -c "
from spec_cli.core.workflow_state import workflow_state_manager

# Create multiple workflows
workflows = []
for i in range(3):
    workflow = workflow_state_manager.create_workflow(f'test-type-{i}', {'index': i})
    workflows.append(workflow)
    
    # Simulate workflow progression
    workflow.start()
    if i == 0:
        workflow.complete()
        workflow_state_manager.complete_workflow(workflow.workflow_id)
    elif i == 1:
        workflow.fail('Test failure')
        workflow_state_manager.fail_workflow(workflow.workflow_id, 'Test failure')
    # Leave workflow 2 running

print(f'Active workflows: {len(workflow_state_manager.get_active_workflows())}')
print(f'Recent workflows: {len(workflow_state_manager.get_recent_workflows())}')

# Test cleanup
cleaned = workflow_state_manager.cleanup_stale_workflows(max_age_hours=0)  # Very aggressive cleanup
print(f'Cleaned up workflows: {cleaned}')
"
```

## Definition of Done

- [ ] SpecWorkflowOrchestrator class for high-level workflow coordination
- [ ] WorkflowState and WorkflowStateManager for workflow tracking
- [ ] Single file spec generation workflow with backup and rollback
- [ ] Batch file processing workflow with progress tracking
- [ ] Workflow validation and error recovery capabilities
- [ ] Pull request creation integration points (stubbed)
- [ ] Workflow status monitoring and management
- [ ] Integration with commit manager and content generator
- [ ] All 15 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Comprehensive workflow state tracking and persistence
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice completes the high-level workflow orchestration and enables slice-11 (file processing) by providing:
- Complete workflow infrastructure that file processing can integrate with
- Backup and rollback capabilities that batch processing can use
- Workflow state management that change detection can leverage
- Foundation for complex multi-file operations and conflict resolution workflows