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
