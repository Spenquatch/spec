"""Unit tests for workflow test helpers infrastructure.

Tests the workflow test infrastructure components including state builders,
transition mockers, backup/rollback fixtures, and error simulators.
"""

import copy
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from spec_cli.core.workflow_state import (
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
    WorkflowStep,
)
from spec_cli.utils.test_helpers.workflow_test_helpers import (
    BackupRollbackFixtures,
    StateTransitionMocker,
    WorkflowErrorSimulator,
    WorkflowStateBuilder,
    create_backup_rollback_fixtures,
    create_state_transition_mocker,
    create_workflow_error_simulator,
    create_workflow_state_builder,
)


class TestWorkflowStateBuilder:
    """Test WorkflowStateBuilder functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = WorkflowStateBuilder()

    def test_initial_state(self):
        """Test builder initial state."""
        workflow = self.builder.build()

        assert workflow.workflow_id == "test-workflow-001"
        assert workflow.workflow_type == "test"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.start_time is None
        assert workflow.end_time is None
        assert workflow.duration is None
        assert workflow.steps == []
        assert workflow.metadata == {}

    def test_reset_functionality(self):
        """Test builder reset functionality."""
        # Modify builder state
        self.builder.with_id("modified").with_type("modified_type")

        # Reset and build
        workflow = self.builder.reset().build()

        assert workflow.workflow_id == "test-workflow-001"
        assert workflow.workflow_type == "test"

    def test_with_id(self):
        """Test setting workflow ID."""
        workflow_id = "custom-workflow-123"
        workflow = self.builder.with_id(workflow_id).build()

        assert workflow.workflow_id == workflow_id

    def test_with_type(self):
        """Test setting workflow type."""
        workflow_type = "spec_generation"
        workflow = self.builder.with_type(workflow_type).build()

        assert workflow.workflow_type == workflow_type

    def test_with_status(self):
        """Test setting workflow status."""
        status = WorkflowStatus.RUNNING
        workflow = self.builder.with_status(status).build()

        assert workflow.status == status

    def test_with_timing_complete(self):
        """Test setting complete timing information."""
        start_time = datetime.now() - timedelta(minutes=10)
        end_time = datetime.now()

        workflow = self.builder.with_timing(start_time, end_time).build()

        assert workflow.start_time == start_time
        assert workflow.end_time == end_time
        assert workflow.duration == (end_time - start_time).total_seconds()

    def test_with_timing_explicit_duration(self):
        """Test setting timing with explicit duration."""
        start_time = datetime.now() - timedelta(minutes=5)
        duration = 300.0  # 5 minutes

        workflow = self.builder.with_timing(start_time, duration=duration).build()

        assert workflow.start_time == start_time
        assert workflow.duration == duration

    def test_with_metadata(self):
        """Test setting workflow metadata."""
        metadata = {"source": "test", "batch_size": 10}
        workflow = self.builder.with_metadata(metadata).build()

        assert workflow.metadata == metadata
        # Ensure metadata is copied, not referenced
        metadata["modified"] = True
        assert "modified" not in workflow.metadata

    def test_add_step_basic(self):
        """Test adding basic workflow step."""
        workflow = self.builder.add_step("validation", WorkflowStage.VALIDATION).build()

        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.name == "validation"
        assert step.stage == WorkflowStage.VALIDATION
        assert step.status == WorkflowStatus.PENDING

    def test_add_step_complete(self):
        """Test adding complete workflow step with all fields."""
        start_time = datetime.now() - timedelta(minutes=2)
        end_time = datetime.now()
        result = {"files_processed": 5}

        workflow = self.builder.add_step(
            "generation",
            WorkflowStage.GENERATION,
            WorkflowStatus.COMPLETED,
            start_time,
            end_time,
            result,
        ).build()

        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.name == "generation"
        assert step.stage == WorkflowStage.GENERATION
        assert step.status == WorkflowStatus.COMPLETED
        assert step.start_time == start_time
        assert step.end_time == end_time
        assert step.result == result
        assert step.duration == (end_time - start_time).total_seconds()

    def test_add_step_failed(self):
        """Test adding failed workflow step."""
        error_msg = "Generation failed due to invalid template"

        workflow = self.builder.add_step(
            "generation",
            WorkflowStage.GENERATION,
            WorkflowStatus.FAILED,
            error=error_msg,
        ).build()

        step = workflow.steps[0]
        assert step.status == WorkflowStatus.FAILED
        assert step.error == error_msg

    def test_multiple_steps(self):
        """Test adding multiple workflow steps."""
        workflow = (
            self.builder.add_step(
                "validation", WorkflowStage.VALIDATION, WorkflowStatus.COMPLETED
            )
            .add_step("backup", WorkflowStage.BACKUP, WorkflowStatus.RUNNING)
            .add_step("generation", WorkflowStage.GENERATION, WorkflowStatus.PENDING)
            .build()
        )

        assert len(workflow.steps) == 3
        assert workflow.steps[0].name == "validation"
        assert workflow.steps[1].name == "backup"
        assert workflow.steps[2].name == "generation"

    def test_with_steps_direct(self):
        """Test setting steps directly."""
        steps = [
            WorkflowStep("step1", WorkflowStage.VALIDATION),
            WorkflowStep("step2", WorkflowStage.BACKUP),
        ]

        workflow = self.builder.with_steps(steps).build()

        assert len(workflow.steps) == 2
        assert workflow.steps[0].name == "step1"
        assert workflow.steps[1].name == "step2"
        # Ensure steps are copied
        steps[0].name = "modified"
        assert workflow.steps[0].name == "step1"

    def test_method_chaining(self):
        """Test fluent interface method chaining."""
        start_time = datetime.now() - timedelta(minutes=5)
        end_time = datetime.now()

        workflow = (
            self.builder.with_id("chained-test")
            .with_type("batch_processing")
            .with_status(WorkflowStatus.COMPLETED)
            .with_timing(start_time, end_time)
            .with_metadata({"test": True})
            .add_step("step1", WorkflowStage.VALIDATION, WorkflowStatus.COMPLETED)
            .build()
        )

        assert workflow.workflow_id == "chained-test"
        assert workflow.workflow_type == "batch_processing"
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.start_time == start_time
        assert workflow.end_time == end_time
        assert workflow.metadata["test"] is True
        assert len(workflow.steps) == 1


class TestStateTransitionMocker:
    """Test StateTransitionMocker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mocker = StateTransitionMocker()

    def test_initial_state(self):
        """Test initial mocker state."""
        assert self.mocker.current_state == WorkflowStatus.PENDING
        assert self.mocker.transition_rules == {}
        assert self.mocker.transition_history == []
        assert self.mocker.failure_conditions == {}

    def test_register_transition(self):
        """Test registering transition rules."""
        self.mocker.register_transition(
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            duration=0.5,
            success_rate=0.9,
        )

        key = (WorkflowStatus.PENDING, WorkflowStatus.RUNNING)
        assert key in self.mocker.transition_rules
        rule = self.mocker.transition_rules[key]
        assert rule["duration"] == 0.5
        assert rule["success_rate"] == 0.9

    def test_register_failure_condition(self):
        """Test registering failure conditions."""
        self.mocker.register_failure_condition(
            WorkflowStatus.RUNNING, "disk_full", "No space left on device"
        )

        assert WorkflowStatus.RUNNING in self.mocker.failure_conditions
        conditions = self.mocker.failure_conditions[WorkflowStatus.RUNNING]
        assert len(conditions) == 1
        assert conditions[0]["condition"] == "disk_full"
        assert conditions[0]["error_msg"] == "No space left on device"

    def test_execute_transition_success(self):
        """Test successful transition execution."""
        # Register transition
        self.mocker.register_transition(
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            duration=0.1,
            success_rate=1.0,
        )

        # Execute transition
        start_time = time.time()
        result = self.mocker.execute_transition(WorkflowStatus.RUNNING)
        elapsed = time.time() - start_time

        assert result["success"] is True
        assert result["from_state"] == WorkflowStatus.PENDING
        assert result["to_state"] == WorkflowStatus.RUNNING
        assert result["duration"] == 0.1
        assert elapsed >= 0.1  # Should have actually waited
        assert self.mocker.current_state == WorkflowStatus.RUNNING

    def test_execute_transition_with_context(self):
        """Test transition execution with context."""
        self.mocker.register_transition(
            WorkflowStatus.PENDING, WorkflowStatus.RUNNING, duration=0.01
        )

        context = {"operation": "validation", "files": 5}
        result = self.mocker.execute_transition(WorkflowStatus.RUNNING, context)

        assert result["success"] is True
        # Check history includes context
        history = self.mocker.get_transition_history()
        assert len(history) == 1
        assert history[0]["context"] == context

    def test_execute_transition_no_rule(self):
        """Test transition execution without registered rule."""
        with pytest.raises(ValueError, match="No transition rule defined"):
            self.mocker.execute_transition(WorkflowStatus.RUNNING)

    def test_execute_transition_failure_condition(self):
        """Test transition execution with failure condition."""
        # Register transition and failure condition
        self.mocker.register_transition(WorkflowStatus.PENDING, WorkflowStatus.RUNNING)
        self.mocker.register_failure_condition(
            WorkflowStatus.RUNNING, "disk_full", "No space left on device"
        )

        # Execute with failure context
        context = {"error": "disk_full"}
        with pytest.raises(Exception, match="No space left on device"):
            self.mocker.execute_transition(WorkflowStatus.RUNNING, context)

    @patch("random.random")
    def test_execute_transition_random_failure(self, mock_random):
        """Test transition execution with random failure."""
        # Mock random to return value that causes failure
        mock_random.return_value = 0.95  # > success_rate of 0.8

        self.mocker.register_transition(
            WorkflowStatus.PENDING, WorkflowStatus.RUNNING, success_rate=0.8
        )

        with pytest.raises(Exception, match="Transition from .* failed"):
            self.mocker.execute_transition(WorkflowStatus.RUNNING)

    def test_transition_history_tracking(self):
        """Test transition history tracking."""
        self.mocker.register_transition(WorkflowStatus.PENDING, WorkflowStatus.RUNNING)
        self.mocker.register_transition(
            WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED
        )

        # Execute multiple transitions
        self.mocker.execute_transition(WorkflowStatus.RUNNING)
        self.mocker.execute_transition(WorkflowStatus.COMPLETED)

        history = self.mocker.get_transition_history()
        assert len(history) == 2
        assert history[0]["from"] == WorkflowStatus.PENDING
        assert history[0]["to"] == WorkflowStatus.RUNNING
        assert history[1]["from"] == WorkflowStatus.RUNNING
        assert history[1]["to"] == WorkflowStatus.COMPLETED

    def test_reset_functionality(self):
        """Test mocker reset functionality."""
        # Set up some state
        self.mocker.register_transition(WorkflowStatus.PENDING, WorkflowStatus.RUNNING)
        self.mocker.execute_transition(WorkflowStatus.RUNNING)

        # Verify state before reset
        assert self.mocker.current_state == WorkflowStatus.RUNNING
        assert len(self.mocker.transition_history) == 1

        # Reset and verify
        self.mocker.reset()
        assert self.mocker.current_state == WorkflowStatus.PENDING
        assert self.mocker.transition_history == []


class TestBackupRollbackFixtures:
    """Test BackupRollbackFixtures functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fixtures = BackupRollbackFixtures()

    def test_initial_state(self):
        """Test initial fixtures state."""
        assert self.fixtures.backup_scenarios == {}
        assert self.fixtures.rollback_scenarios == {}

    def test_create_backup_scenario(self):
        """Test creating backup scenario."""
        original_data = {"files": ["file1.py", "file2.py"], "metadata": {"version": 1}}
        backup_data = {
            "files": ["file1.py", "file2.py"],
            "metadata": {"version": 1, "backup_time": "2025-01-01"},
        }
        corruption_points = ["partial_write", "metadata_loss"]

        self.fixtures.create_backup_scenario(
            "test_scenario", original_data, backup_data, corruption_points
        )

        assert "test_scenario" in self.fixtures.backup_scenarios
        scenario = self.fixtures.backup_scenarios["test_scenario"]
        assert scenario["original_data"] == original_data
        assert scenario["backup_data"] == backup_data
        assert scenario["corruption_points"] == corruption_points

    def test_create_rollback_scenario(self):
        """Test creating rollback scenario."""
        corrupted_state = {"files": ["file1.py"], "metadata": None}
        backup_state = {"files": ["file1.py", "file2.py"], "metadata": {"version": 1}}
        expected_final_state = {
            "files": ["file1.py", "file2.py"],
            "metadata": {"version": 1},
        }

        self.fixtures.create_rollback_scenario(
            "rollback_test", corrupted_state, backup_state, expected_final_state
        )

        assert "rollback_test" in self.fixtures.rollback_scenarios
        scenario = self.fixtures.rollback_scenarios["rollback_test"]
        assert scenario["corrupted_state"] == corrupted_state
        assert scenario["backup_state"] == backup_state
        assert scenario["expected_final_state"] == expected_final_state

    def test_get_backup_scenario(self):
        """Test getting backup scenario."""
        original_data = {"test": "data"}
        self.fixtures.create_backup_scenario("test", original_data, {})

        scenario = self.fixtures.get_backup_scenario("test")
        assert scenario["original_data"] == original_data

        # Verify data is deep copied
        scenario["original_data"]["modified"] = True
        original_scenario = self.fixtures.backup_scenarios["test"]
        assert "modified" not in original_scenario["original_data"]

    def test_get_nonexistent_scenario(self):
        """Test getting non-existent scenario."""
        scenario = self.fixtures.get_backup_scenario("nonexistent")
        assert scenario == {}

    def test_simulate_corruption_partial_write(self):
        """Test partial write corruption simulation."""
        data = {"files": ["file1.py", "file2.py", "file3.py"], "metadata": {"count": 3}}

        corrupted = self.fixtures.simulate_corruption(data, "partial_write")

        assert len(corrupted["files"]) == 1  # Half of original 3 files
        assert corrupted["metadata"] == data["metadata"]  # Metadata unchanged

    def test_simulate_corruption_metadata_loss(self):
        """Test metadata loss corruption simulation."""
        data = {"files": ["file1.py"], "metadata": {"version": 1}}

        corrupted = self.fixtures.simulate_corruption(data, "metadata_loss")

        assert corrupted["files"] == data["files"]  # Files unchanged
        assert "metadata" not in corrupted  # Metadata removed

    def test_simulate_corruption_state_inconsistency(self):
        """Test state inconsistency corruption simulation."""
        data = {"status": "running", "steps_completed": ["step1", "step2"]}

        corrupted = self.fixtures.simulate_corruption(data, "state_inconsistency")

        assert corrupted["status"] == WorkflowStatus.FAILED.value
        assert corrupted["steps_completed"] == []

    def test_simulate_corruption_timing_corruption(self):
        """Test timing corruption simulation."""
        data = {"start_time": "2025-01-01", "duration": 300, "other": "data"}

        corrupted = self.fixtures.simulate_corruption(data, "timing_corruption")

        assert "start_time" not in corrupted
        assert "duration" not in corrupted
        assert corrupted["other"] == "data"  # Other data preserved

    def test_simulate_corruption_preserves_original(self):
        """Test that corruption simulation preserves original data."""
        original_data = {"files": ["file1.py", "file2.py"], "metadata": {"version": 1}}

        self.fixtures.simulate_corruption(original_data, "metadata_loss")

        # Original data should be unchanged
        assert "metadata" in original_data
        assert original_data["metadata"]["version"] == 1


class TestWorkflowErrorSimulator:
    """Test WorkflowErrorSimulator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = WorkflowErrorSimulator()

    def test_initial_scenarios(self):
        """Test initial error scenarios are loaded."""
        expected_scenarios = [
            "disk_full",
            "permission_denied",
            "network_failure",
            "timeout",
            "validation_error",
            "state_corruption",
        ]

        for scenario in expected_scenarios:
            assert scenario in self.simulator.error_scenarios

    def test_simulate_disk_full_error(self):
        """Test disk full error simulation."""
        with pytest.raises(OSError, match="No space left on device"):
            self.simulator.simulate_error("disk_full", "backup_creation")

    def test_simulate_permission_error(self):
        """Test permission denied error simulation."""
        with pytest.raises(PermissionError, match="Permission denied"):
            self.simulator.simulate_error("permission_denied", "file_operations")

    def test_simulate_network_error(self):
        """Test network failure error simulation."""
        with pytest.raises(ConnectionError, match="Network connection failed"):
            self.simulator.simulate_error("network_failure", "external_service")

    def test_simulate_timeout_error(self):
        """Test timeout error simulation."""
        with pytest.raises(TimeoutError, match="Operation timed out"):
            self.simulator.simulate_error("timeout", "long_running_operation")

    def test_simulate_validation_error(self):
        """Test validation error simulation."""
        with pytest.raises(ValueError, match="Invalid workflow configuration"):
            self.simulator.simulate_error("validation_error", "validation")

    def test_simulate_state_corruption_error(self):
        """Test state corruption error simulation."""
        with pytest.raises(RuntimeError, match="Workflow state corrupted"):
            self.simulator.simulate_error("state_corruption", "state_management")

    def test_simulate_error_wrong_context(self):
        """Test error simulation with wrong context."""
        # Should not raise error when context doesn't match
        self.simulator.simulate_error("disk_full", "wrong_context")

    def test_simulate_error_no_context(self):
        """Test error simulation without context check."""
        with pytest.raises(OSError):
            self.simulator.simulate_error("disk_full")

    def test_simulate_unknown_scenario(self):
        """Test simulating unknown error scenario."""
        with pytest.raises(ValueError, match="Unknown error scenario"):
            self.simulator.simulate_error("nonexistent_scenario")

    def test_add_custom_scenario(self):
        """Test adding custom error scenario."""
        self.simulator.add_custom_scenario(
            "custom_error", RuntimeError, "Custom error message", "custom_operation"
        )

        assert "custom_error" in self.simulator.error_scenarios
        scenario = self.simulator.error_scenarios["custom_error"]
        assert scenario["error_type"] is RuntimeError
        assert scenario["message"] == "Custom error message"
        assert scenario["occurs_at"] == "custom_operation"

        # Test the custom scenario works
        with pytest.raises(RuntimeError, match="Custom error message"):
            self.simulator.simulate_error("custom_error", "custom_operation")

    def test_error_context_manager(self):
        """Test error context manager."""
        with pytest.raises(OSError):
            with self.simulator.error_context("disk_full", "backup_creation"):
                pass  # Error should be raised on exit

    def test_error_context_manager_wrong_context(self):
        """Test error context manager with wrong context."""
        # Should not raise error
        with self.simulator.error_context("disk_full", "wrong_context"):
            pass


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_workflow_state_builder(self):
        """Test workflow state builder factory."""
        builder = create_workflow_state_builder()
        assert isinstance(builder, WorkflowStateBuilder)

    def test_create_state_transition_mocker(self):
        """Test state transition mocker factory."""
        mocker = create_state_transition_mocker()
        assert isinstance(mocker, StateTransitionMocker)

    def test_create_backup_rollback_fixtures(self):
        """Test backup rollback fixtures factory."""
        fixtures = create_backup_rollback_fixtures()
        assert isinstance(fixtures, BackupRollbackFixtures)

    def test_create_workflow_error_simulator(self):
        """Test workflow error simulator factory."""
        simulator = create_workflow_error_simulator()
        assert isinstance(simulator, WorkflowErrorSimulator)


class TestPytestFixtures:
    """Test pytest fixtures integration."""

    def test_workflow_state_builder_fixture(self, workflow_state_builder):
        """Test workflow state builder fixture."""
        assert isinstance(workflow_state_builder, WorkflowStateBuilder)
        workflow = workflow_state_builder.with_id("fixture-test").build()
        assert workflow.workflow_id == "fixture-test"

    def test_state_transition_mocker_fixture(self, state_transition_mocker):
        """Test state transition mocker fixture."""
        assert isinstance(state_transition_mocker, StateTransitionMocker)
        assert state_transition_mocker.current_state == WorkflowStatus.PENDING

    def test_backup_rollback_fixtures_fixture(self, backup_rollback_fixtures):
        """Test backup rollback fixtures fixture."""
        assert isinstance(backup_rollback_fixtures, BackupRollbackFixtures)
        backup_rollback_fixtures.create_backup_scenario("test", {}, {})
        assert "test" in backup_rollback_fixtures.backup_scenarios

    def test_workflow_error_simulator_fixture(self, workflow_error_simulator):
        """Test workflow error simulator fixture."""
        assert isinstance(workflow_error_simulator, WorkflowErrorSimulator)
        assert "disk_full" in workflow_error_simulator.error_scenarios

    def test_sample_pending_workflow_fixture(self, sample_pending_workflow):
        """Test sample pending workflow fixture."""
        assert isinstance(sample_pending_workflow, WorkflowState)
        assert sample_pending_workflow.status == WorkflowStatus.PENDING
        assert sample_pending_workflow.workflow_id == "test-pending-001"

    def test_sample_running_workflow_fixture(self, sample_running_workflow):
        """Test sample running workflow fixture."""
        assert isinstance(sample_running_workflow, WorkflowState)
        assert sample_running_workflow.status == WorkflowStatus.RUNNING
        assert len(sample_running_workflow.steps) == 2
        assert sample_running_workflow.steps[0].status == WorkflowStatus.COMPLETED
        assert sample_running_workflow.steps[1].status == WorkflowStatus.RUNNING

    def test_sample_failed_workflow_fixture(self, sample_failed_workflow):
        """Test sample failed workflow fixture."""
        assert isinstance(sample_failed_workflow, WorkflowState)
        assert sample_failed_workflow.status == WorkflowStatus.FAILED
        assert len(sample_failed_workflow.steps) == 2
        failed_step = sample_failed_workflow.steps[1]
        assert failed_step.status == WorkflowStatus.FAILED
        assert failed_step.error == "Generation failed"


class TestIntegrationScenarios:
    """Test integration scenarios using multiple helpers."""

    def test_complete_workflow_simulation(
        self, workflow_state_builder, state_transition_mocker
    ):
        """Test complete workflow simulation using multiple helpers."""
        # Set up transition rules
        state_transition_mocker.register_transition(
            WorkflowStatus.PENDING, WorkflowStatus.RUNNING, duration=0.01
        )
        state_transition_mocker.register_transition(
            WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED, duration=0.01
        )

        # Create workflow
        workflow_state_builder.with_id("integration-test").build()

        # Simulate transitions
        result1 = state_transition_mocker.execute_transition(WorkflowStatus.RUNNING)
        assert result1["success"]

        result2 = state_transition_mocker.execute_transition(WorkflowStatus.COMPLETED)
        assert result2["success"]

        # Verify final state
        assert state_transition_mocker.current_state == WorkflowStatus.COMPLETED
        assert len(state_transition_mocker.get_transition_history()) == 2

    def test_backup_and_corruption_scenario(
        self, backup_rollback_fixtures, workflow_error_simulator
    ):
        """Test backup and corruption scenario."""
        # Create backup scenario
        original_data = {"files": ["file1.py", "file2.py"], "metadata": {"version": 1}}
        backup_data = copy.deepcopy(original_data)
        backup_rollback_fixtures.create_backup_scenario(
            "corruption_test", original_data, backup_data, ["metadata_loss"]
        )

        # Simulate corruption
        corrupted = backup_rollback_fixtures.simulate_corruption(
            original_data, "metadata_loss"
        )
        assert "metadata" not in corrupted

        # Test error simulation in same context
        with pytest.raises(ValueError):
            workflow_error_simulator.simulate_error("validation_error", "validation")

    def test_failed_workflow_with_rollback(
        self, workflow_state_builder, backup_rollback_fixtures
    ):
        """Test failed workflow with rollback scenario."""
        # Create failed workflow
        workflow = (
            workflow_state_builder.with_id("failed-rollback-test")
            .with_status(WorkflowStatus.FAILED)
            .add_step("backup", WorkflowStage.BACKUP, WorkflowStatus.COMPLETED)
            .add_step(
                "generation",
                WorkflowStage.GENERATION,
                WorkflowStatus.FAILED,
                error="Corruption detected",
            )
            .build()
        )

        # Create rollback scenario
        corrupted_state = {"status": "failed", "partial_data": True}
        backup_state = {"status": "completed", "full_data": True}
        expected_state = {"status": "rolled_back", "full_data": True}

        backup_rollback_fixtures.create_rollback_scenario(
            "failed_workflow", corrupted_state, backup_state, expected_state
        )

        # Verify scenario creation
        scenario = backup_rollback_fixtures.get_rollback_scenario("failed_workflow")
        assert scenario["corrupted_state"]["status"] == "failed"
        assert scenario["expected_final_state"]["status"] == "rolled_back"

        # Verify workflow failure
        failed_steps = workflow.get_failed_steps()
        assert len(failed_steps) == 1
        assert failed_steps[0].error == "Corruption detected"
