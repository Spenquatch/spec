"""Unit tests for WorkflowState transitions - Micro-Agent workflow_003.

This module provides comprehensive unit testing for workflow state transitions,
including state management, timing validation, error handling, and integration
with the workflow test infrastructure.

Test coverage targets:
- WorkflowState status transitions and timing
- WorkflowStep status transitions and error handling
- WorkflowStateManager lifecycle management
- State transition validation and rollback scenarios
- Error simulation and recovery mechanisms
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from spec_cli.core.workflow_state import (
    WorkflowStage,
    WorkflowState,
    WorkflowStateManager,
    WorkflowStatus,
    WorkflowStep,
)
from spec_cli.utils.test_helpers.workflow_test_helpers import (
    create_state_transition_mocker,
    create_workflow_error_simulator,
    create_workflow_state_builder,
)


class TestWorkflowStateTransitions:
    """Test suite for WorkflowState status transitions."""

    def setup_method(self):
        """Setup for each test method."""
        self.workflow_state = WorkflowState(
            workflow_id="test-workflow-001", workflow_type="test_workflow"
        )

    @patch("spec_cli.core.workflow_state.debug_logger")
    def test_workflow_start_transition_when_pending_then_sets_running_status(
        self, mock_logger
    ):
        """Test workflow start transition from PENDING to RUNNING."""
        # Initial state verification
        assert self.workflow_state.status == WorkflowStatus.PENDING
        assert self.workflow_state.start_time is None

        # Execute transition
        self.workflow_state.start()

        # Verify state changes
        assert self.workflow_state.status == WorkflowStatus.RUNNING
        assert self.workflow_state.start_time is not None
        assert isinstance(self.workflow_state.start_time, datetime)

        # Verify logging
        mock_logger.log.assert_called_once_with(
            "INFO",
            "Workflow started",
            workflow_id="test-workflow-001",
            workflow_type="test_workflow",
        )

    @patch("spec_cli.core.workflow_state.debug_logger")
    def test_workflow_complete_transition_when_running_then_sets_completed_status(
        self, mock_logger
    ):
        """Test workflow completion transition from RUNNING to COMPLETED."""
        # Setup: start the workflow first
        self.workflow_state.start()
        start_time = self.workflow_state.start_time

        # Execute transition
        self.workflow_state.complete()

        # Verify state changes
        assert self.workflow_state.status == WorkflowStatus.COMPLETED
        assert self.workflow_state.end_time is not None
        assert isinstance(self.workflow_state.end_time, datetime)
        assert self.workflow_state.duration is not None
        assert self.workflow_state.duration > 0

        # Verify duration calculation
        expected_duration = (self.workflow_state.end_time - start_time).total_seconds()
        assert self.workflow_state.duration == expected_duration

        # Verify logging
        mock_logger.log.assert_called_with(
            "INFO",
            "Workflow completed",
            workflow_id="test-workflow-001",
            duration=self.workflow_state.duration,
        )

    @patch("spec_cli.core.workflow_state.debug_logger")
    def test_workflow_fail_transition_when_running_then_sets_failed_status(
        self, mock_logger
    ):
        """Test workflow failure transition from RUNNING to FAILED."""
        # Setup: start the workflow first
        self.workflow_state.start()
        start_time = self.workflow_state.start_time
        error_msg = "Test error occurred"

        # Execute transition
        self.workflow_state.fail(error_msg)

        # Verify state changes
        assert self.workflow_state.status == WorkflowStatus.FAILED
        assert self.workflow_state.end_time is not None
        assert isinstance(self.workflow_state.end_time, datetime)
        assert self.workflow_state.duration is not None
        assert self.workflow_state.duration > 0

        # Verify duration calculation
        expected_duration = (self.workflow_state.end_time - start_time).total_seconds()
        assert self.workflow_state.duration == expected_duration

        # Verify logging
        mock_logger.log.assert_called_with(
            "ERROR", "Workflow failed", workflow_id="test-workflow-001", error=error_msg
        )

    def test_workflow_complete_without_start_time_then_no_duration_calculated(self):
        """Test workflow completion without start time doesn't calculate duration."""
        # Execute completion without starting
        self.workflow_state.complete()

        # Verify state
        assert self.workflow_state.status == WorkflowStatus.COMPLETED
        assert self.workflow_state.end_time is not None
        assert self.workflow_state.duration is None

    def test_workflow_fail_without_start_time_then_no_duration_calculated(self):
        """Test workflow failure without start time doesn't calculate duration."""
        # Execute failure without starting
        self.workflow_state.fail("Test error")

        # Verify state
        assert self.workflow_state.status == WorkflowStatus.FAILED
        assert self.workflow_state.end_time is not None
        assert self.workflow_state.duration is None


class TestWorkflowStepTransitions:
    """Test suite for WorkflowStep status transitions."""

    def setup_method(self):
        """Setup for each test method."""
        self.step = WorkflowStep(name="test_step", stage=WorkflowStage.GENERATION)

    def test_step_start_transition_when_pending_then_sets_running_status(self):
        """Test step start transition from PENDING to RUNNING."""
        # Initial state verification
        assert self.step.status == WorkflowStatus.PENDING
        assert self.step.start_time is None

        # Execute transition
        self.step.start()

        # Verify state changes
        assert self.step.status == WorkflowStatus.RUNNING
        assert self.step.start_time is not None
        assert isinstance(self.step.start_time, datetime)

    def test_step_complete_transition_when_running_then_sets_completed_status(self):
        """Test step completion transition from RUNNING to COMPLETED."""
        # Setup: start the step first
        self.step.start()
        start_time = self.step.start_time
        test_result = {"files_generated": 5, "success": True}

        # Execute transition
        self.step.complete(test_result)

        # Verify state changes
        assert self.step.status == WorkflowStatus.COMPLETED
        assert self.step.end_time is not None
        assert isinstance(self.step.end_time, datetime)
        assert self.step.duration is not None
        assert self.step.duration >= 0
        assert self.step.result == test_result
        assert self.step.error is None

        # Verify duration calculation
        expected_duration = (self.step.end_time - start_time).total_seconds()
        assert self.step.duration == expected_duration

    def test_step_complete_without_result_then_uses_empty_dict(self):
        """Test step completion without result uses empty dict."""
        self.step.start()

        # Execute completion without result
        self.step.complete()

        # Verify default result
        assert self.step.status == WorkflowStatus.COMPLETED
        assert self.step.result == {}

    def test_step_fail_transition_when_running_then_sets_failed_status(self):
        """Test step failure transition from RUNNING to FAILED."""
        # Setup: start the step first
        self.step.start()
        start_time = self.step.start_time
        error_msg = "Generation failed due to invalid input"

        # Execute transition
        self.step.fail(error_msg)

        # Verify state changes
        assert self.step.status == WorkflowStatus.FAILED
        assert self.step.end_time is not None
        assert isinstance(self.step.end_time, datetime)
        assert self.step.duration is not None
        assert self.step.duration >= 0
        assert self.step.error == error_msg
        assert self.step.result is None

        # Verify duration calculation
        expected_duration = (self.step.end_time - start_time).total_seconds()
        assert self.step.duration == expected_duration

    def test_step_complete_without_start_time_then_no_duration_calculated(self):
        """Test step completion without start time doesn't calculate duration."""
        test_result = {"test": "data"}

        # Execute completion without starting
        self.step.complete(test_result)

        # Verify state
        assert self.step.status == WorkflowStatus.COMPLETED
        assert self.step.end_time is not None
        assert self.step.duration is None
        assert self.step.result == test_result

    def test_step_fail_without_start_time_then_no_duration_calculated(self):
        """Test step failure without start time doesn't calculate duration."""
        error_msg = "Test error"

        # Execute failure without starting
        self.step.fail(error_msg)

        # Verify state
        assert self.step.status == WorkflowStatus.FAILED
        assert self.step.end_time is not None
        assert self.step.duration is None
        assert self.step.error == error_msg


class TestWorkflowStateStepManagement:
    """Test suite for WorkflowState step management operations."""

    def setup_method(self):
        """Setup for each test method."""
        self.workflow_state = WorkflowState(
            workflow_id="test-workflow-steps", workflow_type="step_management_test"
        )

    def test_add_step_when_valid_params_then_creates_and_adds_step(self):
        """Test adding a new step to workflow."""
        step_name = "validation"
        step_stage = WorkflowStage.VALIDATION

        # Execute step addition
        step = self.workflow_state.add_step(step_name, step_stage)

        # Verify step creation
        assert isinstance(step, WorkflowStep)
        assert step.name == step_name
        assert step.stage == step_stage
        assert step.status == WorkflowStatus.PENDING

        # Verify step is added to workflow
        assert len(self.workflow_state.steps) == 1
        assert self.workflow_state.steps[0] is step

    def test_get_current_step_when_running_step_exists_then_returns_latest_running(
        self,
    ):
        """Test getting current running step returns the latest one."""
        # Add multiple steps
        step1 = self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        step2 = self.workflow_state.add_step("generation", WorkflowStage.GENERATION)
        step3 = self.workflow_state.add_step("commit", WorkflowStage.COMMIT)

        # Start steps in order
        step1.start()
        step1.complete()
        step2.start()
        step3.start()  # Latest running step

        # Execute current step retrieval
        current_step = self.workflow_state.get_current_step()

        # Verify latest running step is returned
        assert current_step is step3
        assert current_step.status == WorkflowStatus.RUNNING

    def test_get_current_step_when_no_running_steps_then_returns_none(self):
        """Test getting current step when none are running returns None."""
        # Add steps but don't start any
        self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        self.workflow_state.add_step("generation", WorkflowStage.GENERATION)

        # Execute current step retrieval
        current_step = self.workflow_state.get_current_step()

        # Verify None is returned
        assert current_step is None

    def test_get_failed_steps_when_mixed_statuses_then_returns_only_failed(self):
        """Test getting failed steps returns only those with failed status."""
        # Add and configure steps with different statuses
        step1 = self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        step2 = self.workflow_state.add_step("generation", WorkflowStage.GENERATION)
        step3 = self.workflow_state.add_step("commit", WorkflowStage.COMMIT)

        step1.start()
        step1.complete()
        step2.start()
        step2.fail("Generation error")
        step3.start()
        step3.fail("Commit error")

        # Execute failed steps retrieval
        failed_steps = self.workflow_state.get_failed_steps()

        # Verify only failed steps are returned
        assert len(failed_steps) == 2
        assert step2 in failed_steps
        assert step3 in failed_steps
        assert step1 not in failed_steps

    def test_get_completed_steps_when_mixed_statuses_then_returns_only_completed(self):
        """Test getting completed steps returns only those with completed status."""
        # Add and configure steps with different statuses
        step1 = self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        step2 = self.workflow_state.add_step("generation", WorkflowStage.GENERATION)
        step3 = self.workflow_state.add_step("commit", WorkflowStage.COMMIT)

        step1.start()
        step1.complete()
        step2.start()
        step2.complete()
        step3.start()
        step3.fail("Commit error")

        # Execute completed steps retrieval
        completed_steps = self.workflow_state.get_completed_steps()

        # Verify only completed steps are returned
        assert len(completed_steps) == 2
        assert step1 in completed_steps
        assert step2 in completed_steps
        assert step3 not in completed_steps


class TestWorkflowStateSummary:
    """Test suite for WorkflowState summary generation."""

    def setup_method(self):
        """Setup for each test method."""
        self.workflow_state = WorkflowState(
            workflow_id="test-summary-workflow", workflow_type="summary_test"
        )

    def test_get_summary_when_workflow_with_mixed_steps_then_returns_accurate_summary(
        self,
    ):
        """Test workflow summary with mixed step statuses."""
        # Setup workflow with various steps
        self.workflow_state.start()
        self.workflow_state.duration = 120.5

        # Add steps with different statuses
        step1 = self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        step2 = self.workflow_state.add_step("generation", WorkflowStage.GENERATION)
        step3 = self.workflow_state.add_step("commit", WorkflowStage.COMMIT)
        step4 = self.workflow_state.add_step("cleanup", WorkflowStage.CLEANUP)

        step1.start()
        step1.complete()
        step2.start()
        step2.complete()
        step3.start()
        step3.fail("Commit failed")
        step4.start()  # Currently running

        # Execute summary generation
        summary = self.workflow_state.get_summary()

        # Verify summary contents
        expected_summary = {
            "workflow_id": "test-summary-workflow",
            "workflow_type": "summary_test",
            "status": "running",
            "duration": 120.5,
            "total_steps": 4,
            "completed_steps": 2,
            "failed_steps": 1,
            "current_stage": "cleanup",
        }
        assert summary == expected_summary

    def test_get_summary_when_no_current_step_then_current_stage_is_none(self):
        """Test workflow summary when no step is currently running."""
        # Setup workflow without current running step
        self.workflow_state.status = WorkflowStatus.COMPLETED
        self.workflow_state.duration = 45.2

        step1 = self.workflow_state.add_step("validation", WorkflowStage.VALIDATION)
        step1.start()
        step1.complete()

        # Execute summary generation
        summary = self.workflow_state.get_summary()

        # Verify current_stage is None
        assert summary["current_stage"] is None
        assert summary["total_steps"] == 1
        assert summary["completed_steps"] == 1
        assert summary["failed_steps"] == 0


class TestWorkflowStateManagerTransitions:
    """Test suite for WorkflowStateManager lifecycle transitions."""

    def setup_method(self):
        """Setup for each test method."""
        self.manager = WorkflowStateManager()

    @patch("spec_cli.core.workflow_state.debug_logger")
    def test_create_workflow_when_valid_params_then_creates_and_tracks_workflow(
        self, mock_logger
    ):
        """Test workflow creation and tracking in manager."""
        workflow_type = "test_creation"
        metadata = {"source": "unit_test", "priority": "high"}

        # Execute workflow creation
        workflow = self.manager.create_workflow(workflow_type, metadata)

        # Verify workflow properties
        assert isinstance(workflow, WorkflowState)
        assert workflow.workflow_type == workflow_type
        assert workflow.metadata == metadata
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.workflow_id.startswith(workflow_type)

        # Verify tracking in active workflows
        assert workflow.workflow_id in self.manager.active_workflows
        assert self.manager.active_workflows[workflow.workflow_id] is workflow

        # Verify logging
        mock_logger.log.assert_called_with(
            "INFO",
            "Workflow created",
            workflow_id=workflow.workflow_id,
            workflow_type=workflow_type,
        )

    def test_complete_workflow_when_active_workflow_then_moves_to_history(self):
        """Test completing active workflow moves it to history."""
        # Setup: create workflow
        workflow = self.manager.create_workflow("test_completion")
        workflow_id = workflow.workflow_id
        workflow.start()

        # Execute workflow completion
        self.manager.complete_workflow(workflow_id)

        # Verify workflow is completed
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.end_time is not None
        assert workflow.duration is not None

        # Verify workflow moved to history
        assert workflow_id not in self.manager.active_workflows
        assert len(self.manager.workflow_history) == 1
        assert self.manager.workflow_history[0] is workflow

    def test_complete_workflow_when_nonexistent_workflow_then_no_error(self):
        """Test completing nonexistent workflow doesn't raise error."""
        # Execute completion of nonexistent workflow
        self.manager.complete_workflow("nonexistent-workflow")

        # Verify no changes to state
        assert len(self.manager.active_workflows) == 0
        assert len(self.manager.workflow_history) == 0

    def test_fail_workflow_when_active_workflow_then_moves_to_history(self):
        """Test failing active workflow moves it to history."""
        # Setup: create workflow
        workflow = self.manager.create_workflow("test_failure")
        workflow_id = workflow.workflow_id
        workflow.start()
        error_msg = "Test failure scenario"

        # Execute workflow failure
        self.manager.fail_workflow(workflow_id, error_msg)

        # Verify workflow is failed
        assert workflow.status == WorkflowStatus.FAILED
        assert workflow.end_time is not None
        assert workflow.duration is not None

        # Verify workflow moved to history
        assert workflow_id not in self.manager.active_workflows
        assert len(self.manager.workflow_history) == 1
        assert self.manager.workflow_history[0] is workflow

    def test_history_limit_when_exceeds_100_workflows_then_keeps_only_50(self):
        """Test history trimming when exceeding 100 workflows."""
        # Setup: create and complete 101 workflows to trigger trimming
        workflows = []
        for i in range(101):
            workflow = self.manager.create_workflow(f"test_history_{i}")
            workflows.append(workflow)
            self.manager.complete_workflow(workflow.workflow_id)

        # Verify history is trimmed to 50 most recent
        assert len(self.manager.workflow_history) == 50

        # Verify correct workflows are kept (last 50)
        kept_workflows = self.manager.workflow_history
        expected_workflows = workflows[-50:]
        assert kept_workflows == expected_workflows

    def test_get_workflow_when_active_workflow_then_returns_from_active(self):
        """Test getting workflow finds it in active workflows first."""
        # Setup: create active workflow
        workflow = self.manager.create_workflow("test_get_active")
        workflow_id = workflow.workflow_id

        # Execute workflow retrieval
        retrieved_workflow = self.manager.get_workflow(workflow_id)

        # Verify correct workflow returned
        assert retrieved_workflow is workflow

    def test_get_workflow_when_history_workflow_then_returns_from_history(self):
        """Test getting workflow finds it in history when not active."""
        # Setup: create and complete workflow
        workflow = self.manager.create_workflow("test_get_history")
        workflow_id = workflow.workflow_id
        self.manager.complete_workflow(workflow_id)

        # Execute workflow retrieval
        retrieved_workflow = self.manager.get_workflow(workflow_id)

        # Verify correct workflow returned from history
        assert retrieved_workflow is workflow

    def test_get_workflow_when_nonexistent_workflow_then_returns_none(self):
        """Test getting nonexistent workflow returns None."""
        # Execute retrieval of nonexistent workflow
        retrieved_workflow = self.manager.get_workflow("nonexistent-workflow")

        # Verify None is returned
        assert retrieved_workflow is None

    def test_get_active_workflows_when_multiple_active_then_returns_all(self):
        """Test getting all active workflows."""
        # Setup: create multiple active workflows
        workflow1 = self.manager.create_workflow("test_active_1")
        workflow2 = self.manager.create_workflow("test_active_2")
        workflow3 = self.manager.create_workflow("test_active_3")

        # Execute active workflows retrieval
        active_workflows = self.manager.get_active_workflows()

        # Verify all active workflows returned
        assert len(active_workflows) == 3
        assert workflow1 in active_workflows
        assert workflow2 in active_workflows
        assert workflow3 in active_workflows

    def test_get_recent_workflows_when_history_exists_then_returns_requested_count(
        self,
    ):
        """Test getting recent workflows from history."""
        # Setup: create and complete multiple workflows
        workflows = []
        for i in range(5):
            workflow = self.manager.create_workflow(f"test_recent_{i}")
            workflows.append(workflow)
            self.manager.complete_workflow(workflow.workflow_id)

        # Execute recent workflows retrieval
        recent_workflows = self.manager.get_recent_workflows(3)

        # Verify correct count and workflows returned
        assert len(recent_workflows) == 3
        assert recent_workflows == workflows[-3:]  # Last 3 workflows

    def test_get_recent_workflows_when_empty_history_then_returns_empty_list(self):
        """Test getting recent workflows when history is empty."""
        # Execute recent workflows retrieval with empty history
        recent_workflows = self.manager.get_recent_workflows(5)

        # Verify empty list returned
        assert recent_workflows == []


class TestWorkflowStateManagerStaleCleanup:
    """Test suite for WorkflowStateManager stale workflow cleanup."""

    def setup_method(self):
        """Setup for each test method."""
        self.manager = WorkflowStateManager()

    @patch("spec_cli.core.workflow_state.debug_logger")
    def test_cleanup_stale_workflows_when_old_workflows_exist_then_moves_to_failed(
        self, mock_logger
    ):
        """Test cleanup of stale workflows that have been running too long."""
        # Setup: create workflows with different ages
        now = datetime.now()

        # Recent workflow (should not be cleaned)
        recent_workflow = self.manager.create_workflow("recent_workflow")
        recent_workflow.start_time = now - timedelta(hours=12)

        # Stale workflow (should be cleaned)
        stale_workflow = self.manager.create_workflow("stale_workflow")
        stale_workflow.start_time = now - timedelta(hours=25)

        # Very stale workflow (should be cleaned)
        very_stale_workflow = self.manager.create_workflow("very_stale_workflow")
        very_stale_workflow.start_time = now - timedelta(hours=48)

        # Execute cleanup with 24-hour threshold
        cleaned_count = self.manager.cleanup_stale_workflows(max_age_hours=24)

        # Verify correct number cleaned
        assert cleaned_count == 2

        # Verify stale workflows moved to history as failed
        assert len(self.manager.active_workflows) == 1
        assert recent_workflow.workflow_id in self.manager.active_workflows
        assert len(self.manager.workflow_history) == 2

        # Verify stale workflows are marked as failed
        for workflow in self.manager.workflow_history:
            assert workflow.status == WorkflowStatus.FAILED

        # Verify logging
        mock_logger.log.assert_called_with(
            "INFO", "Cleaned up stale workflows", count=2
        )

    def test_cleanup_stale_workflows_when_no_stale_workflows_then_returns_zero(self):
        """Test cleanup when no stale workflows exist."""
        # Setup: create only recent workflows
        workflow1 = self.manager.create_workflow("recent_1")
        workflow1.start_time = datetime.now() - timedelta(hours=12)

        workflow2 = self.manager.create_workflow("recent_2")
        workflow2.start_time = datetime.now() - timedelta(hours=6)

        # Execute cleanup
        cleaned_count = self.manager.cleanup_stale_workflows(max_age_hours=24)

        # Verify no workflows cleaned
        assert cleaned_count == 0
        assert len(self.manager.active_workflows) == 2
        assert len(self.manager.workflow_history) == 0

    def test_cleanup_stale_workflows_when_no_start_time_then_workflow_not_cleaned(self):
        """Test cleanup skips workflows without start time."""
        # Setup: create workflow without start time
        workflow = self.manager.create_workflow("no_start_time")
        # Don't set start_time - it remains None

        # Execute cleanup
        cleaned_count = self.manager.cleanup_stale_workflows(max_age_hours=24)

        # Verify workflow not cleaned
        assert cleaned_count == 0
        assert len(self.manager.active_workflows) == 1
        assert workflow.workflow_id in self.manager.active_workflows


class TestWorkflowStateWithHelperIntegration:
    """Test suite for WorkflowState integration with test helpers."""

    def test_workflow_state_with_builder_creates_complex_scenarios(self):
        """Test using WorkflowStateBuilder for complex test scenarios."""
        # Create builder instance
        workflow_state_builder = create_workflow_state_builder()

        # Use builder to create complex workflow state
        start_time = datetime.now() - timedelta(minutes=30)
        end_time = datetime.now()

        workflow = (
            workflow_state_builder.with_id("integration-test-001")
            .with_type("integration_test")
            .with_status(WorkflowStatus.RUNNING)
            .with_timing(start_time, end_time)
            .add_step("validation", WorkflowStage.VALIDATION, WorkflowStatus.COMPLETED)
            .add_step("generation", WorkflowStage.GENERATION, WorkflowStatus.RUNNING)
            .with_metadata({"test_mode": True, "priority": "high"})
            .build()
        )

        # Verify complex workflow state
        assert workflow.workflow_id == "integration-test-001"
        assert workflow.workflow_type == "integration_test"
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.start_time == start_time
        assert workflow.end_time == end_time
        assert workflow.duration == (end_time - start_time).total_seconds()
        assert len(workflow.steps) == 2
        assert workflow.metadata["test_mode"] is True

        # Verify steps
        validation_step = workflow.steps[0]
        assert validation_step.name == "validation"
        assert validation_step.stage == WorkflowStage.VALIDATION
        assert validation_step.status == WorkflowStatus.COMPLETED

        generation_step = workflow.steps[1]
        assert generation_step.name == "generation"
        assert generation_step.stage == WorkflowStage.GENERATION
        assert generation_step.status == WorkflowStatus.RUNNING

    def test_state_transition_mocker_validates_workflow_transitions(self):
        """Test using StateTransitionMocker for transition validation."""
        # Create mocker instance
        state_transition_mocker = create_state_transition_mocker()

        # Setup transition rules
        state_transition_mocker.register_transition(
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            duration=0.1,
            success_rate=1.0,
        )
        state_transition_mocker.register_transition(
            WorkflowStatus.RUNNING,
            WorkflowStatus.COMPLETED,
            duration=0.1,
            success_rate=1.0,
        )

        # Execute transitions
        result1 = state_transition_mocker.execute_transition(WorkflowStatus.RUNNING)
        result2 = state_transition_mocker.execute_transition(WorkflowStatus.COMPLETED)

        # Verify transitions
        assert result1["success"] is True
        assert result1["from_state"] == WorkflowStatus.PENDING
        assert result1["to_state"] == WorkflowStatus.RUNNING

        assert result2["success"] is True
        assert result2["from_state"] == WorkflowStatus.RUNNING
        assert result2["to_state"] == WorkflowStatus.COMPLETED

        # Verify current state
        assert state_transition_mocker.current_state == WorkflowStatus.COMPLETED

        # Verify transition history
        history = state_transition_mocker.get_transition_history()
        assert len(history) == 2

    def test_workflow_error_simulator_handles_error_scenarios(self):
        """Test using WorkflowErrorSimulator for error condition testing."""
        # Create error simulator instance
        workflow_error_simulator = create_workflow_error_simulator()

        # Test specific error scenario
        with pytest.raises(RuntimeError, match="Workflow state corrupted"):
            workflow_error_simulator.simulate_error(
                "state_corruption", "state_management"
            )

        # Test error context that doesn't match
        # Should not raise error when context doesn't match
        try:
            workflow_error_simulator.simulate_error(
                "state_corruption", "different_context"
            )
        except Exception:
            pytest.fail("Error should not be raised for non-matching context")

        # Test custom error scenario
        workflow_error_simulator.add_custom_scenario(
            "custom_test_error",
            ValueError,
            "Custom test error occurred",
            "test_operation",
        )

        with pytest.raises(ValueError, match="Custom test error occurred"):
            workflow_error_simulator.simulate_error(
                "custom_test_error", "test_operation"
            )


class TestStateTransitionEdgeCases:
    """Test suite for edge cases in state transitions."""

    def test_multiple_consecutive_start_calls_then_updates_start_time(self):
        """Test multiple start calls update start time."""
        workflow = WorkflowState("test-multi-start", "test")

        # First start
        workflow.start()
        first_start_time = workflow.start_time

        # Wait briefly and start again
        import time

        time.sleep(0.01)
        workflow.start()
        second_start_time = workflow.start_time

        # Verify start time was updated
        assert second_start_time > first_start_time
        assert workflow.status == WorkflowStatus.RUNNING

    def test_complete_after_fail_then_overwrites_status(self):
        """Test completing workflow after failure overwrites status."""
        workflow = WorkflowState("test-fail-complete", "test")
        workflow.start()

        # Fail first
        workflow.fail("Test error")
        assert workflow.status == WorkflowStatus.FAILED

        # Then complete
        workflow.complete()
        assert workflow.status == WorkflowStatus.COMPLETED
        # Note: This demonstrates the behavior but might not be desired in practice

    def test_step_transitions_preserve_timing_integrity(self):
        """Test step transitions maintain timing integrity."""
        step = WorkflowStep("timing_test", WorkflowStage.GENERATION)

        # Start step
        step.start()
        start_time = step.start_time

        # Brief delay before completion
        import time

        time.sleep(0.01)

        # Complete step
        step.complete({"test": "result"})

        # Verify timing integrity
        assert step.end_time > start_time
        assert step.duration > 0
        assert step.duration == (step.end_time - start_time).total_seconds()
        assert step.status == WorkflowStatus.COMPLETED

    def test_workflow_summary_with_no_steps_then_returns_zero_counts(self):
        """Test workflow summary with no steps returns appropriate zero values."""
        workflow = WorkflowState("empty-workflow", "test")

        summary = workflow.get_summary()

        assert summary["total_steps"] == 0
        assert summary["completed_steps"] == 0
        assert summary["failed_steps"] == 0
        assert summary["current_stage"] is None
