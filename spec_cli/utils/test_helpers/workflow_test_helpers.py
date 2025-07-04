"""Workflow test infrastructure for testing complex state management.

This module provides comprehensive workflow testing infrastructure to enable testing
of complex state management across workflow stages. It includes builders for workflow
state objects, transition mockers, backup/rollback fixtures, and error simulators.

Key components:
- WorkflowStateBuilder: Build workflow state objects for testing scenarios
- StateTransitionMocker: Mock state transitions and validate transition rules
- BackupRollbackFixtures: Create backup and rollback scenarios for testing
- WorkflowErrorSimulator: Simulate various workflow error conditions
"""

import copy
import random
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import pytest

from ...core.workflow_state import (
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
    WorkflowStep,
)


class WorkflowTestState(Enum):
    """Test-specific workflow state enumeration."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    BACKING_UP = "backing_up"
    COMMITTING = "committing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class WorkflowStateBuilder:
    """Builder for creating workflow state objects for testing.

    Provides a fluent interface for constructing WorkflowState objects
    with various configurations needed for testing scenarios.
    """

    def __init__(self) -> None:
        """Initialize the builder with default state."""
        self.reset()

    def reset(self) -> "WorkflowStateBuilder":
        """Reset builder to initial state.

        Returns:
            Self for method chaining
        """
        self._workflow_id = "test-workflow-001"
        self._workflow_type = "test"
        self._status = WorkflowStatus.PENDING
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._duration: float | None = None
        self._steps: list[WorkflowStep] = []
        self._metadata: dict[str, Any] = {}
        return self

    def with_id(self, workflow_id: str) -> "WorkflowStateBuilder":
        """Set workflow ID.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            Self for method chaining
        """
        self._workflow_id = workflow_id
        return self

    def with_type(self, workflow_type: str) -> "WorkflowStateBuilder":
        """Set workflow type.

        Args:
            workflow_type: Type of workflow (e.g., 'spec_generation', 'batch_processing')

        Returns:
            Self for method chaining
        """
        self._workflow_type = workflow_type
        return self

    def with_status(self, status: WorkflowStatus) -> "WorkflowStateBuilder":
        """Set current workflow status.

        Args:
            status: Workflow status enum value

        Returns:
            Self for method chaining
        """
        self._status = status
        return self

    def with_timing(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
        duration: float | None = None,
    ) -> "WorkflowStateBuilder":
        """Set timing information.

        Args:
            start_time: When workflow started
            end_time: When workflow ended (optional)
            duration: Duration in seconds (optional, calculated if not provided)

        Returns:
            Self for method chaining
        """
        self._start_time = start_time
        self._end_time = end_time
        if end_time and start_time and not duration:
            self._duration = (end_time - start_time).total_seconds()
        elif duration:
            self._duration = duration
        return self

    def with_steps(self, steps: list[WorkflowStep]) -> "WorkflowStateBuilder":
        """Set workflow steps.

        Args:
            steps: List of WorkflowStep objects

        Returns:
            Self for method chaining
        """
        self._steps = copy.deepcopy(steps)
        return self

    def with_metadata(self, metadata: dict[str, Any]) -> "WorkflowStateBuilder":
        """Set workflow metadata.

        Args:
            metadata: Dictionary of metadata values

        Returns:
            Self for method chaining
        """
        self._metadata = metadata.copy()
        return self

    def add_step(
        self,
        name: str,
        stage: WorkflowStage,
        status: WorkflowStatus = WorkflowStatus.PENDING,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> "WorkflowStateBuilder":
        """Add a workflow step.

        Args:
            name: Step name
            stage: Workflow stage
            status: Step status
            start_time: When step started
            end_time: When step ended
            result: Step result data
            error: Error message if step failed

        Returns:
            Self for method chaining
        """
        step = WorkflowStep(
            name=name,
            stage=stage,
            status=status,
            start_time=start_time,
            end_time=end_time,
            result=result,
            error=error,
        )

        if start_time and end_time:
            step.duration = (end_time - start_time).total_seconds()

        self._steps.append(step)
        return self

    def build(self) -> WorkflowState:
        """Build the workflow state object.

        Returns:
            Configured WorkflowState instance
        """
        workflow = WorkflowState(
            workflow_id=self._workflow_id,
            workflow_type=self._workflow_type,
            status=self._status,
            start_time=self._start_time,
            end_time=self._end_time,
            duration=self._duration,
            steps=self._steps.copy(),
            metadata=self._metadata.copy(),
        )
        return workflow


class StateTransitionMocker:
    """Mock state transitions for testing workflow flows.

    Provides controlled state transition simulation with configurable
    rules, failure conditions, and transition history tracking.
    """

    def __init__(self) -> None:
        """Initialize the transition mocker."""
        self.transition_rules: dict[
            tuple[WorkflowStatus, WorkflowStatus], dict[str, Any]
        ] = {}
        self.transition_history: list[dict[str, Any]] = []
        self.failure_conditions: dict[WorkflowStatus, list[dict[str, str]]] = {}
        self.current_state = WorkflowStatus.PENDING

    def register_transition(
        self,
        from_state: WorkflowStatus,
        to_state: WorkflowStatus,
        duration: float = 0.1,
        success_rate: float = 1.0,
    ) -> None:
        """Register a state transition rule.

        Args:
            from_state: Source state
            to_state: Target state
            duration: Simulated transition duration in seconds
            success_rate: Probability of successful transition (0.0 to 1.0)
        """
        key = (from_state, to_state)
        self.transition_rules[key] = {
            "duration": duration,
            "success_rate": success_rate,
        }

    def register_failure_condition(
        self, state: WorkflowStatus, condition: str, error_msg: str
    ) -> None:
        """Register a failure condition for a state.

        Args:
            state: State where failure can occur
            condition: Condition string to check in context
            error_msg: Error message to raise when condition is met
        """
        if state not in self.failure_conditions:
            self.failure_conditions[state] = []
        self.failure_conditions[state].append(
            {"condition": condition, "error_msg": error_msg}
        )

    def execute_transition(
        self, target_state: WorkflowStatus, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a state transition with mocking.

        Args:
            target_state: Target state to transition to
            context: Optional context data for transition

        Returns:
            Transition result dictionary

        Raises:
            Exception: If transition fails or is not allowed
        """
        from_state = self.current_state
        transition_key = (from_state, target_state)

        # Record transition attempt
        self.transition_history.append(
            {
                "from": from_state,
                "to": target_state,
                "context": context or {},
                "timestamp": time.time(),
            }
        )

        # Check for failure conditions
        if target_state in self.failure_conditions:
            for failure in self.failure_conditions[target_state]:
                if context and failure["condition"] in str(context):
                    raise Exception(failure["error_msg"])

        # Execute transition
        if transition_key in self.transition_rules:
            rule = self.transition_rules[transition_key]
            time.sleep(rule["duration"])

            # Check success rate
            if random.random() > rule["success_rate"]:
                raise Exception(
                    f"Transition from {from_state} to {target_state} failed"
                )

            # Update current state
            self.current_state = target_state

            return {
                "success": True,
                "from_state": from_state,
                "to_state": target_state,
                "duration": rule["duration"],
            }
        else:
            raise ValueError(
                f"No transition rule defined for {from_state} -> {target_state}"
            )

    def get_transition_history(self) -> list[dict[str, Any]]:
        """Get the complete transition history.

        Returns:
            List of transition records
        """
        return self.transition_history.copy()

    def reset(self):
        """Reset the mocker to initial state."""
        self.current_state = WorkflowStatus.PENDING
        self.transition_history = []


class BackupRollbackFixtures:
    """Fixtures for testing backup and rollback functionality.

    Provides predefined scenarios for testing backup creation,
    corruption simulation, and rollback operations.
    """

    def __init__(self) -> None:
        """Initialize backup/rollback fixtures."""
        self.backup_scenarios: dict[str, dict[str, Any]] = {}
        self.rollback_scenarios: dict[str, dict[str, Any]] = {}

    def create_backup_scenario(
        self,
        name: str,
        original_data: dict[str, Any],
        backup_data: dict[str, Any],
        corruption_points: list[str] | None = None,
    ):
        """Create a backup scenario for testing.

        Args:
            name: Scenario name
            original_data: Original data state
            backup_data: Backed up data state
            corruption_points: List of possible corruption points
        """
        self.backup_scenarios[name] = {
            "original_data": copy.deepcopy(original_data),
            "backup_data": copy.deepcopy(backup_data),
            "corruption_points": corruption_points or [],
        }

    def create_rollback_scenario(
        self,
        name: str,
        corrupted_state: dict[str, Any],
        backup_state: dict[str, Any],
        expected_final_state: dict[str, Any],
    ):
        """Create a rollback scenario for testing.

        Args:
            name: Scenario name
            corrupted_state: State after corruption
            backup_state: State to rollback to
            expected_final_state: Expected state after rollback
        """
        self.rollback_scenarios[name] = {
            "corrupted_state": copy.deepcopy(corrupted_state),
            "backup_state": copy.deepcopy(backup_state),
            "expected_final_state": copy.deepcopy(expected_final_state),
        }

    def get_backup_scenario(self, name: str) -> dict[str, Any]:
        """Get a backup scenario by name.

        Args:
            name: Scenario name

        Returns:
            Backup scenario data
        """
        return copy.deepcopy(self.backup_scenarios.get(name, {}))

    def get_rollback_scenario(self, name: str) -> dict[str, Any]:
        """Get a rollback scenario by name.

        Args:
            name: Scenario name

        Returns:
            Rollback scenario data
        """
        return copy.deepcopy(self.rollback_scenarios.get(name, {}))

    def simulate_corruption(
        self, data: dict[str, Any], corruption_point: str
    ) -> dict[str, Any]:
        """Simulate data corruption at a specific point.

        Args:
            data: Original data
            corruption_point: Type of corruption to simulate

        Returns:
            Corrupted data
        """
        corrupted_data = copy.deepcopy(data)

        if corruption_point == "partial_write":
            # Simulate partial write corruption
            if "files" in corrupted_data:
                corrupted_data["files"] = corrupted_data["files"][
                    : len(corrupted_data["files"]) // 2
                ]
        elif corruption_point == "metadata_loss":
            # Simulate metadata corruption
            corrupted_data.pop("metadata", None)
        elif corruption_point == "state_inconsistency":
            # Simulate state inconsistency
            corrupted_data["status"] = WorkflowStatus.FAILED.value
            corrupted_data["steps_completed"] = []
        elif corruption_point == "timing_corruption":
            # Simulate timing data corruption
            corrupted_data.pop("start_time", None)
            corrupted_data.pop("duration", None)

        return corrupted_data


class WorkflowErrorSimulator:
    """Simulate various workflow error scenarios.

    Provides controlled error simulation for testing error handling
    and recovery mechanisms in workflow components.
    """

    def __init__(self) -> None:
        """Initialize the error simulator."""
        self.error_scenarios = {
            "disk_full": {
                "error_type": OSError,
                "message": "No space left on device",
                "occurs_at": "backup_creation",
            },
            "permission_denied": {
                "error_type": PermissionError,
                "message": "Permission denied",
                "occurs_at": "file_operations",
            },
            "network_failure": {
                "error_type": ConnectionError,
                "message": "Network connection failed",
                "occurs_at": "external_service",
            },
            "timeout": {
                "error_type": TimeoutError,
                "message": "Operation timed out",
                "occurs_at": "long_running_operation",
            },
            "validation_error": {
                "error_type": ValueError,
                "message": "Invalid workflow configuration",
                "occurs_at": "validation",
            },
            "state_corruption": {
                "error_type": RuntimeError,
                "message": "Workflow state corrupted",
                "occurs_at": "state_management",
            },
        }

    def simulate_error(self, scenario: str, operation_context: str | None = None):
        """Simulate a specific error scenario.

        Args:
            scenario: Name of error scenario to simulate
            operation_context: Context where error should occur

        Raises:
            Exception: The simulated error
        """
        if scenario not in self.error_scenarios:
            raise ValueError(f"Unknown error scenario: {scenario}")

        error_info = self.error_scenarios[scenario]

        if operation_context and error_info["occurs_at"] != operation_context:
            return  # Error doesn't occur in this context

        error_class = error_info["error_type"]
        raise error_class(error_info["message"])  # type: ignore[operator]

    def add_custom_scenario(
        self, name: str, error_type: type, message: str, occurs_at: str
    ):
        """Add a custom error scenario.

        Args:
            name: Scenario name
            error_type: Exception type to raise
            message: Error message
            occurs_at: Context where error occurs
        """
        self.error_scenarios[name] = {
            "error_type": error_type,
            "message": message,
            "occurs_at": occurs_at,
        }

    @contextmanager
    def error_context(self, scenario: str, operation_context: str | None = None):
        """Context manager for simulating errors in specific operations.

        Args:
            scenario: Error scenario name
            operation_context: Operation context

        Yields:
            None

        Raises:
            Exception: If scenario conditions are met
        """
        try:
            yield
        finally:
            self.simulate_error(scenario, operation_context)


# Factory functions for easy helper creation
def create_workflow_state_builder() -> WorkflowStateBuilder:
    """Create WorkflowStateBuilder instance.

    Returns:
        New WorkflowStateBuilder instance
    """
    return WorkflowStateBuilder()


def create_state_transition_mocker() -> StateTransitionMocker:
    """Create StateTransitionMocker instance.

    Returns:
        New StateTransitionMocker instance
    """
    return StateTransitionMocker()


def create_backup_rollback_fixtures() -> BackupRollbackFixtures:
    """Create BackupRollbackFixtures instance.

    Returns:
        New BackupRollbackFixtures instance
    """
    return BackupRollbackFixtures()


def create_workflow_error_simulator() -> WorkflowErrorSimulator:
    """Create WorkflowErrorSimulator instance.

    Returns:
        New WorkflowErrorSimulator instance
    """
    return WorkflowErrorSimulator()


# Pytest fixtures for integration
@pytest.fixture
def workflow_state_builder():
    """Pytest fixture for workflow state builder.

    Returns:
        WorkflowStateBuilder instance
    """
    return create_workflow_state_builder()


@pytest.fixture
def state_transition_mocker():
    """Pytest fixture for state transition mocker.

    Returns:
        StateTransitionMocker instance
    """
    return create_state_transition_mocker()


@pytest.fixture
def backup_rollback_fixtures():
    """Pytest fixture for backup/rollback scenarios.

    Returns:
        BackupRollbackFixtures instance
    """
    return create_backup_rollback_fixtures()


@pytest.fixture
def workflow_error_simulator():
    """Pytest fixture for workflow error simulator.

    Returns:
        WorkflowErrorSimulator instance
    """
    return create_workflow_error_simulator()


# Sample workflow fixtures for common test scenarios
@pytest.fixture
def sample_pending_workflow(workflow_state_builder):
    """Sample pending workflow for testing.

    Returns:
        WorkflowState in pending status
    """
    return workflow_state_builder.with_id("test-pending-001").build()


@pytest.fixture
def sample_running_workflow(workflow_state_builder):
    """Sample running workflow for testing.

    Returns:
        WorkflowState in running status with steps
    """
    start_time = datetime.now() - timedelta(minutes=5)
    return (
        workflow_state_builder.with_id("test-running-001")
        .with_status(WorkflowStatus.RUNNING)
        .with_timing(start_time)
        .add_step("validation", WorkflowStage.VALIDATION, WorkflowStatus.COMPLETED)
        .add_step("backup", WorkflowStage.BACKUP, WorkflowStatus.RUNNING)
        .build()
    )


@pytest.fixture
def sample_failed_workflow(workflow_state_builder):
    """Sample failed workflow for testing.

    Returns:
        WorkflowState in failed status with error information
    """
    start_time = datetime.now() - timedelta(minutes=10)
    end_time = datetime.now() - timedelta(minutes=2)
    return (
        workflow_state_builder.with_id("test-failed-001")
        .with_status(WorkflowStatus.FAILED)
        .with_timing(start_time, end_time)
        .add_step("validation", WorkflowStage.VALIDATION, WorkflowStatus.COMPLETED)
        .add_step(
            "generation",
            WorkflowStage.GENERATION,
            WorkflowStatus.FAILED,
            error="Generation failed",
        )
        .build()
    )
