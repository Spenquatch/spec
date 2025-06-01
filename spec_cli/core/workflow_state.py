from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
        current_step = self.get_current_step()
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status.value,
            "duration": self.duration,
            "total_steps": len(self.steps),
            "completed_steps": len(self.get_completed_steps()),
            "failed_steps": len(self.get_failed_steps()),
            "current_stage": current_step.stage.value if current_step else None,
        }

class WorkflowStateManager:
    """Manages workflow state tracking and persistence."""

    def __init__(self) -> None:
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

            # Keep history limited
            if len(self.workflow_history) > 100:
                self.workflow_history = self.workflow_history[-50:]

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
