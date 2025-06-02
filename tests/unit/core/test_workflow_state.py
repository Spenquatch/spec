import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from spec_cli.core.workflow_state import (
    WorkflowStatus, WorkflowStage, WorkflowStep, WorkflowState, 
    WorkflowStateManager, workflow_state_manager
)

class TestWorkflowStep:
    """Test WorkflowStep class."""
    
    def test_workflow_step_creation(self):
        """Test creating a workflow step."""
        step = WorkflowStep("test step", WorkflowStage.INITIALIZATION)
        
        assert step.name == "test step"
        assert step.stage == WorkflowStage.INITIALIZATION
        assert step.status == WorkflowStatus.PENDING
        assert step.start_time is None
        assert step.end_time is None
        assert step.duration is None
        assert step.result is None
        assert step.error is None
    
    def test_workflow_step_start(self):
        """Test starting a workflow step."""
        step = WorkflowStep("test step", WorkflowStage.VALIDATION)
        
        start_time = datetime.now()
        step.start()
        
        assert step.status == WorkflowStatus.RUNNING
        assert step.start_time is not None
        assert step.start_time >= start_time
    
    def test_workflow_step_complete(self):
        """Test completing a workflow step."""
        step = WorkflowStep("test step", WorkflowStage.GENERATION)
        step.start()
        
        result = {"files_generated": 2}
        step.complete(result)
        
        assert step.status == WorkflowStatus.COMPLETED
        assert step.end_time is not None
        assert step.duration is not None
        assert step.duration >= 0
        assert step.result == result
    
    def test_workflow_step_complete_without_result(self):
        """Test completing a workflow step without result."""
        step = WorkflowStep("test step", WorkflowStage.CLEANUP)
        step.start()
        
        step.complete()
        
        assert step.status == WorkflowStatus.COMPLETED
        assert step.result == {}
    
    def test_workflow_step_fail(self):
        """Test failing a workflow step."""
        step = WorkflowStep("test step", WorkflowStage.COMMIT)
        step.start()
        
        error_msg = "Git commit failed"
        step.fail(error_msg)
        
        assert step.status == WorkflowStatus.FAILED
        assert step.end_time is not None
        assert step.duration is not None
        assert step.error == error_msg
    
    def test_workflow_step_timing_without_start(self):
        """Test step timing when start wasn't called."""
        step = WorkflowStep("test step", WorkflowStage.BACKUP)
        
        step.complete()
        
        assert step.status == WorkflowStatus.COMPLETED
        assert step.duration is None

class TestWorkflowState:
    """Test WorkflowState class."""
    
    def test_workflow_state_creation(self):
        """Test creating a workflow state."""
        workflow = WorkflowState("test-123", "spec_generation")
        
        assert workflow.workflow_id == "test-123"
        assert workflow.workflow_type == "spec_generation"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.start_time is None
        assert workflow.end_time is None
        assert workflow.duration is None
        assert len(workflow.steps) == 0
        assert len(workflow.metadata) == 0
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_workflow_state_start(self, mock_logger):
        """Test starting a workflow."""
        workflow = WorkflowState("test-456", "batch_generation")
        
        start_time = datetime.now()
        workflow.start()
        
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.start_time is not None
        assert workflow.start_time >= start_time
        mock_logger.log.assert_called_once()
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_workflow_state_complete(self, mock_logger):
        """Test completing a workflow."""
        workflow = WorkflowState("test-789", "spec_generation")
        workflow.start()
        
        workflow.complete()
        
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.end_time is not None
        assert workflow.duration is not None
        assert workflow.duration >= 0
        assert mock_logger.log.call_count == 2  # start and complete
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_workflow_state_fail(self, mock_logger):
        """Test failing a workflow."""
        workflow = WorkflowState("test-fail", "spec_generation")
        workflow.start()
        
        error_msg = "Template processing failed"
        workflow.fail(error_msg)
        
        assert workflow.status == WorkflowStatus.FAILED
        assert workflow.end_time is not None
        assert workflow.duration is not None
        # Check that error was logged
        error_call = mock_logger.log.call_args_list[-1]
        assert error_call[0][0] == "ERROR"
        assert "failed" in error_call[0][1]
    
    def test_workflow_add_step(self):
        """Test adding steps to workflow."""
        workflow = WorkflowState("test-steps", "spec_generation")
        
        step1 = workflow.add_step("Validation", WorkflowStage.VALIDATION)
        step2 = workflow.add_step("Generation", WorkflowStage.GENERATION)
        
        assert len(workflow.steps) == 2
        assert workflow.steps[0] == step1
        assert workflow.steps[1] == step2
        assert step1.name == "Validation"
        assert step2.stage == WorkflowStage.GENERATION
    
    def test_workflow_get_current_step(self):
        """Test getting current running step."""
        workflow = WorkflowState("test-current", "spec_generation")
        
        # No current step initially
        assert workflow.get_current_step() is None
        
        # Add some steps
        step1 = workflow.add_step("Step 1", WorkflowStage.VALIDATION)
        step2 = workflow.add_step("Step 2", WorkflowStage.GENERATION)
        step3 = workflow.add_step("Step 3", WorkflowStage.COMMIT)
        
        # Still no current step
        assert workflow.get_current_step() is None
        
        # Start step 2 (most recent running step should be returned)
        step1.start()
        step1.complete()
        step2.start()
        step3.start()
        step3.fail("Error")
        
        # Step 2 should be current (running)
        current = workflow.get_current_step()
        assert current == step2
        assert current.status == WorkflowStatus.RUNNING
    
    def test_workflow_get_failed_steps(self):
        """Test getting failed steps."""
        workflow = WorkflowState("test-failed", "spec_generation")
        
        step1 = workflow.add_step("Step 1", WorkflowStage.VALIDATION)
        step2 = workflow.add_step("Step 2", WorkflowStage.GENERATION)
        step3 = workflow.add_step("Step 3", WorkflowStage.COMMIT)
        
        step1.start()
        step1.complete()
        step2.start()
        step2.fail("Generation error")
        step3.start()
        step3.fail("Commit error")
        
        failed_steps = workflow.get_failed_steps()
        assert len(failed_steps) == 2
        assert step2 in failed_steps
        assert step3 in failed_steps
    
    def test_workflow_get_completed_steps(self):
        """Test getting completed steps."""
        workflow = WorkflowState("test-completed", "spec_generation")
        
        step1 = workflow.add_step("Step 1", WorkflowStage.VALIDATION)
        step2 = workflow.add_step("Step 2", WorkflowStage.GENERATION)
        step3 = workflow.add_step("Step 3", WorkflowStage.COMMIT)
        
        step1.start()
        step1.complete()
        step2.start()
        step2.complete()
        step3.start()
        step3.fail("Error")
        
        completed_steps = workflow.get_completed_steps()
        assert len(completed_steps) == 2
        assert step1 in completed_steps
        assert step2 in completed_steps
    
    def test_workflow_get_summary(self):
        """Test getting workflow summary."""
        workflow = WorkflowState("test-summary", "batch_generation")
        workflow.start()
        
        step1 = workflow.add_step("Step 1", WorkflowStage.VALIDATION)
        step2 = workflow.add_step("Step 2", WorkflowStage.GENERATION)
        step3 = workflow.add_step("Step 3", WorkflowStage.COMMIT)
        
        step1.start()
        step1.complete()
        step2.start()
        step2.fail("Error")
        
        summary = workflow.get_summary()
        
        assert summary["workflow_id"] == "test-summary"
        assert summary["workflow_type"] == "batch_generation"
        assert summary["status"] == WorkflowStatus.RUNNING.value
        assert summary["total_steps"] == 3
        assert summary["completed_steps"] == 1
        assert summary["failed_steps"] == 1
        # step2 failed, so no current running step
        current_step = workflow.get_current_step()
        if current_step:
            assert summary["current_stage"] == current_step.stage.value
        else:
            assert summary["current_stage"] is None

class TestWorkflowStateManager:
    """Test WorkflowStateManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = WorkflowStateManager()
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_workflow_state_manager_init(self, mock_logger):
        """Test WorkflowStateManager initialization."""
        manager = WorkflowStateManager()
        
        assert len(manager.active_workflows) == 0
        assert len(manager.workflow_history) == 0
        mock_logger.log.assert_called_once_with("INFO", "WorkflowStateManager initialized")
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_create_workflow(self, mock_logger):
        """Test creating a workflow."""
        metadata = {"test": True, "file_count": 5}
        workflow = self.manager.create_workflow("test_type", metadata)
        
        assert workflow.workflow_type == "test_type"
        assert workflow.metadata == metadata
        assert workflow.workflow_id in self.manager.active_workflows
        assert len(self.manager.active_workflows) == 1
        mock_logger.log.assert_called()
    
    def test_complete_workflow(self):
        """Test completing a workflow."""
        workflow = self.manager.create_workflow("test_complete")
        workflow_id = workflow.workflow_id
        workflow.start()
        
        self.manager.complete_workflow(workflow_id)
        
        # Should be removed from active and added to history
        assert workflow_id not in self.manager.active_workflows
        assert len(self.manager.workflow_history) == 1
        assert workflow.status == WorkflowStatus.COMPLETED
    
    def test_fail_workflow(self):
        """Test failing a workflow."""
        workflow = self.manager.create_workflow("test_fail")
        workflow_id = workflow.workflow_id
        workflow.start()
        
        error_msg = "Something went wrong"
        self.manager.fail_workflow(workflow_id, error_msg)
        
        # Should be removed from active and added to history
        assert workflow_id not in self.manager.active_workflows
        assert len(self.manager.workflow_history) == 1
        assert workflow.status == WorkflowStatus.FAILED
    
    def test_get_workflow_active(self):
        """Test getting an active workflow."""
        workflow = self.manager.create_workflow("test_get_active")
        workflow_id = workflow.workflow_id
        
        retrieved = self.manager.get_workflow(workflow_id)
        
        assert retrieved == workflow
        assert retrieved.workflow_id == workflow_id
    
    def test_get_workflow_from_history(self):
        """Test getting a workflow from history."""
        workflow = self.manager.create_workflow("test_get_history")
        workflow_id = workflow.workflow_id
        
        # Complete it to move to history
        self.manager.complete_workflow(workflow_id)
        
        retrieved = self.manager.get_workflow(workflow_id)
        
        assert retrieved == workflow
        assert retrieved.workflow_id == workflow_id
    
    def test_get_workflow_not_found(self):
        """Test getting a non-existent workflow."""
        result = self.manager.get_workflow("nonexistent-id")
        assert result is None
    
    def test_get_active_workflows(self):
        """Test getting all active workflows."""
        workflow1 = self.manager.create_workflow("type1")
        workflow2 = self.manager.create_workflow("type2")
        workflow3 = self.manager.create_workflow("type3")
        
        # Complete one to remove from active
        self.manager.complete_workflow(workflow3.workflow_id)
        
        active = self.manager.get_active_workflows()
        
        assert len(active) == 2
        assert workflow1 in active
        assert workflow2 in active
        assert workflow3 not in active
    
    def test_get_recent_workflows(self):
        """Test getting recent workflows from history."""
        # Create and complete several workflows
        workflows = []
        for i in range(5):
            workflow = self.manager.create_workflow(f"type{i}")
            workflows.append(workflow)
            self.manager.complete_workflow(workflow.workflow_id)
        
        # Get recent workflows
        recent = self.manager.get_recent_workflows(3)
        
        assert len(recent) == 3
        # Should be the last 3 in order
        assert recent == workflows[-3:]
    
    def test_get_recent_workflows_empty(self):
        """Test getting recent workflows when history is empty."""
        recent = self.manager.get_recent_workflows()
        assert recent == []
    
    @patch('spec_cli.core.workflow_state.debug_logger')
    def test_cleanup_stale_workflows(self, mock_logger):
        """Test cleaning up stale workflows."""
        # Create workflows with different ages
        old_workflow = self.manager.create_workflow("old_type")
        new_workflow = self.manager.create_workflow("new_type")
        
        # Manually set start times to simulate age
        old_workflow.start()
        new_workflow.start()
        
        # Make the old workflow appear very old
        old_workflow.start_time = datetime.now() - timedelta(hours=48)
        
        # Cleanup workflows older than 24 hours
        cleaned_count = self.manager.cleanup_stale_workflows(24)
        
        assert cleaned_count == 1
        assert old_workflow.workflow_id not in self.manager.active_workflows
        assert new_workflow.workflow_id in self.manager.active_workflows
        assert old_workflow.status == WorkflowStatus.FAILED
        mock_logger.log.assert_called()
    
    def test_cleanup_stale_workflows_none_stale(self):
        """Test cleanup when no workflows are stale."""
        workflow = self.manager.create_workflow("fresh_type")
        workflow.start()
        
        cleaned_count = self.manager.cleanup_stale_workflows(24)
        
        assert cleaned_count == 0
        assert workflow.workflow_id in self.manager.active_workflows
    
    def test_workflow_history_limit(self):
        """Test that workflow history is limited to prevent memory issues."""
        # Create fresh manager to avoid interference from other tests
        manager = WorkflowStateManager()
        
        # Create many workflows to test history limiting
        for i in range(150):
            workflow = manager.create_workflow(f"type{i}")
            manager.complete_workflow(workflow.workflow_id)
        
        # History should be less than 100 (trimming happens when > 100)
        # At 150: first 101 items -> trim to 50, then add 49 more = 99 total
        assert len(manager.workflow_history) < 100
        
        # Verify that the most recent workflows are kept
        last_workflow_id = f"type149-{datetime.now().strftime('%Y%m%d')}"
        recent_workflow_ids = [w.workflow_id for w in manager.workflow_history[-10:]]
        # At least some of the recent ones should be there
        assert any("type14" in wid for wid in recent_workflow_ids)

class TestGlobalWorkflowStateManager:
    """Test the global workflow state manager instance."""
    
    def test_global_instance_exists(self):
        """Test that global workflow state manager exists."""
        assert workflow_state_manager is not None
        assert isinstance(workflow_state_manager, WorkflowStateManager)
    
    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        workflow = workflow_state_manager.create_workflow("test_global")
        
        assert workflow.workflow_id in workflow_state_manager.active_workflows
        
        # Clean up
        workflow_state_manager.complete_workflow(workflow.workflow_id)