import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from spec_cli.core.workflow_orchestrator import SpecWorkflowOrchestrator
from spec_cli.core.workflow_state import WorkflowStatus, WorkflowStage
from spec_cli.exceptions import SpecWorkflowError
from spec_cli.config.settings import SpecSettings

class TestSpecWorkflowOrchestrator:
    """Test SpecWorkflowOrchestrator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock settings
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.mock_settings.project_root = Path("/test")
        
        # Create orchestrator with mocked dependencies
        with patch('spec_cli.core.workflow_orchestrator.get_settings', return_value=self.mock_settings), \
             patch('spec_cli.core.workflow_orchestrator.RepositoryStateChecker') as mock_state_checker, \
             patch('spec_cli.core.workflow_orchestrator.SpecCommitManager') as mock_commit_manager, \
             patch('spec_cli.core.workflow_orchestrator.SpecContentGenerator') as mock_content_gen, \
             patch('spec_cli.core.workflow_orchestrator.DirectoryManager') as mock_dir_manager:
            
            self.orchestrator = SpecWorkflowOrchestrator(self.mock_settings)
            self.mock_state_checker = mock_state_checker.return_value
            self.mock_commit_manager = mock_commit_manager.return_value
            self.mock_content_generator = mock_content_gen.return_value
            self.mock_directory_manager = mock_dir_manager.return_value
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        assert self.orchestrator.settings == self.mock_settings
        assert self.orchestrator.state_checker == self.mock_state_checker
        assert self.orchestrator.commit_manager == self.mock_commit_manager
        assert self.orchestrator.content_generator == self.mock_content_generator
        assert self.orchestrator.directory_manager == self.mock_directory_manager
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.load_template')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_spec_for_file_success(self, mock_logger, mock_load_template, mock_wf_manager):
        """Test successful spec generation for a single file."""
        # Setup mocks
        test_file = Path("/test/src/example.py")
        mock_workflow = Mock()
        mock_workflow.workflow_id = "test-workflow-123"
        mock_workflow.duration = 1.5
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        mock_template = Mock()
        mock_template.name = "default"
        mock_load_template.return_value = mock_template
        
        # Setup validation to pass
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        # Setup tag creation (backup)
        self.mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "abc123"
        }
        
        # Setup content generation
        generated_files = {
            "index": Path("/test/.specs/src/example.py/index.md"),
            "history": Path("/test/.specs/src/example.py/history.md")
        }
        self.mock_content_generator.generate_spec_content.return_value = generated_files
        
        # Setup commit operations
        self.mock_commit_manager.add_files.return_value = {"success": True}
        self.mock_commit_manager.commit_changes.return_value = {
            "success": True,
            "commit_hash": "def456"
        }
        
        # Mock Path.exists to return True
        with patch.object(Path, 'exists', return_value=True):
            result = self.orchestrator.generate_spec_for_file(test_file)
        
        # Verify result
        assert result["success"] is True
        assert result["workflow_id"] == "test-workflow-123"
        assert result["file_path"] == str(test_file)
        assert result["generated_files"] == generated_files
        assert result["duration"] == 1.5
        
        # Verify workflow was created and completed
        mock_wf_manager.create_workflow.assert_called_once()
        mock_workflow.start.assert_called_once()
        mock_workflow.complete.assert_called_once()
        mock_wf_manager.complete_workflow.assert_called_once_with("test-workflow-123")
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_spec_for_file_validation_failure(self, mock_logger, mock_wf_manager):
        """Test spec generation with validation failure."""
        test_file = Path("/test/src/example.py")
        mock_workflow = Mock()
        mock_workflow.workflow_id = "test-workflow-456"
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        
        # Setup validation to fail
        self.mock_state_checker.is_safe_for_spec_operations.return_value = False
        
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(SpecWorkflowError, match="Repository is not safe"):
                self.orchestrator.generate_spec_for_file(test_file)
        
        # Verify workflow was failed
        mock_workflow.fail.assert_called_once()
        mock_wf_manager.fail_workflow.assert_called_once()
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_spec_for_file_missing_file(self, mock_logger, mock_wf_manager):
        """Test spec generation with missing source file."""
        test_file = Path("/test/src/nonexistent.py")
        mock_workflow = Mock()
        mock_workflow.workflow_id = "test-workflow-789"
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        
        # Setup validation to pass initially
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        
        # Mock Path.exists to return False
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(SpecWorkflowError, match="Source file does not exist"):
                self.orchestrator.generate_spec_for_file(test_file)
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.load_template')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_spec_for_file_with_rollback(self, mock_logger, mock_load_template, mock_wf_manager):
        """Test spec generation with error and rollback."""
        test_file = Path("/test/src/example.py")
        mock_workflow = Mock()
        mock_workflow.workflow_id = "test-workflow-rollback"
        mock_workflow.metadata = {"backup_commit": "backup123"}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        mock_template = Mock()
        mock_template.name = "default"
        mock_load_template.return_value = mock_template
        
        # Setup validation to pass
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        # Setup backup creation
        self.mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "backup123"
        }
        
        # Setup content generation to fail
        self.mock_content_generator.generate_spec_content.side_effect = Exception("Generation failed")
        
        # Setup rollback
        self.mock_commit_manager.rollback_to_commit.return_value = {"success": True}
        
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(SpecWorkflowError, match="Spec generation workflow failed"):
                self.orchestrator.generate_spec_for_file(test_file, create_backup=True)
        
        # Verify rollback was attempted
        self.mock_commit_manager.rollback_to_commit.assert_called_once_with(
            "backup123", hard=True, create_backup=False
        )
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_specs_for_files_success(self, mock_logger, mock_wf_manager):
        """Test successful batch spec generation."""
        test_files = [Path("/test/src/file1.py"), Path("/test/src/file2.py")]
        mock_workflow = Mock()
        mock_workflow.workflow_id = "batch-workflow-123"
        mock_workflow.duration = 5.0
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        
        # Setup validation to pass
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            # Mock the single file generation method
            with patch.object(self.orchestrator, 'generate_spec_for_file') as mock_single_gen:
                mock_single_gen.return_value = {
                    "success": True,
                    "generated_files": {"index": "/test/.specs/src/file.py/index.md"}
                }
                
                # Mock backup creation
                with patch.object(self.orchestrator, '_execute_backup_stage') as mock_backup:
                    mock_backup.return_value = {"backup_tag": "backup-tag"}
                    
                    # Mock batch commit
                    with patch.object(self.orchestrator, '_execute_batch_commit_stage') as mock_commit:
                        mock_commit.return_value = {"commit_hash": "batch123"}
                        
                        result = self.orchestrator.generate_specs_for_files(test_files)
        
        # Verify result
        assert result["success"] is True
        assert result["workflow_id"] == "batch-workflow-123"
        assert result["total_files"] == 2
        assert len(result["successful_files"]) == 2
        assert len(result["failed_files"]) == 0
        
        # Verify single file generation was called for each file
        assert mock_single_gen.call_count == 2
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_generate_specs_for_files_partial_failure(self, mock_logger, mock_wf_manager):
        """Test batch spec generation with partial failures."""
        test_files = [Path("/test/src/file1.py"), Path("/test/src/file2.py")]
        mock_workflow = Mock()
        mock_workflow.workflow_id = "batch-workflow-456"
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        
        # Setup validation to pass
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            # Mock the single file generation method with mixed results
            def mock_single_gen(file_path, **kwargs):
                if "file1" in str(file_path):
                    return {
                        "success": True,
                        "generated_files": {"index": "/test/.specs/src/file1.py/index.md"}
                    }
                else:
                    raise Exception("File 2 generation failed")
            
            with patch.object(self.orchestrator, 'generate_spec_for_file', side_effect=mock_single_gen):
                with patch.object(self.orchestrator, '_execute_backup_stage') as mock_backup:
                    mock_backup.return_value = {"backup_tag": "backup-tag"}
                    
                    with patch.object(self.orchestrator, '_execute_batch_commit_stage') as mock_commit:
                        mock_commit.return_value = {"commit_hash": "batch456"}
                        
                        result = self.orchestrator.generate_specs_for_files(test_files)
        
        # Verify result
        assert result["success"] is True  # Should still be true if at least one succeeded
        assert len(result["successful_files"]) == 1
        assert len(result["failed_files"]) == 1
        assert result["failed_files"][0]["file_path"] == str(test_files[1])
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_batch_workflow_progress_tracking(self, mock_logger, mock_wf_manager):
        """Test batch spec generation with progress callback tracking."""
        test_files = [Path("/test/src/file1.py"), Path("/test/src/file2.py"), Path("/test/src/file3.py")]
        mock_workflow = Mock()
        mock_workflow.workflow_id = "progress-workflow-123"
        mock_workflow.metadata = {}
        
        mock_wf_manager.create_workflow.return_value = mock_workflow
        
        # Setup validation to pass
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        # Mock progress callback
        progress_callback = Mock()
        
        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            # Mock the single file generation method
            with patch.object(self.orchestrator, 'generate_spec_for_file') as mock_single_gen:
                mock_single_gen.return_value = {
                    "success": True,
                    "generated_files": {"index": "/test/.specs/src/file.py/index.md"}
                }
                
                # Mock backup creation
                with patch.object(self.orchestrator, '_execute_backup_stage') as mock_backup:
                    mock_backup.return_value = {"backup_tag": "backup-tag"}
                    
                    # Mock batch commit
                    with patch.object(self.orchestrator, '_execute_batch_commit_stage') as mock_commit:
                        mock_commit.return_value = {"commit_hash": "progress123"}
                        
                        result = self.orchestrator.generate_specs_for_files(
                            test_files, progress_callback=progress_callback
                        )
        
        # Verify progress callback was called correctly
        expected_calls = [
            # Called for each file during processing
            ((0, 3, "Processing file1.py"), {}),
            ((1, 3, "Processing file2.py"), {}),
            ((2, 3, "Processing file3.py"), {}),
            # Called at completion
            ((3, 3, "Completed"), {}),
        ]
        
        assert progress_callback.call_count == 4
        actual_calls = progress_callback.call_args_list
        
        for i, (expected_call, actual_call) in enumerate(zip(expected_calls, actual_calls)):
            expected_args, expected_kwargs = expected_call
            actual_args, actual_kwargs = actual_call
            
            # Verify arguments match
            assert actual_args == expected_args, f"Progress call {i}: expected {expected_args}, got {actual_args}"
        
        # Verify result is successful
        assert result["success"] is True
        assert len(result["successful_files"]) == 3
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_create_pull_request_stub(self, mock_wf_manager):
        """Test PR creation stub functionality."""
        mock_workflow = Mock()
        mock_wf_manager.get_workflow.return_value = mock_workflow
        
        result = self.orchestrator.create_pull_request_stub(
            "test-workflow-123",
            title="Test PR",
            description="Test description"
        )
        
        assert result["success"] is True
        assert result["implementation_status"] == "stub"
        assert result["pr_number"] == 123
        assert result["title"] == "Test PR"
        assert result["description"] == "Test description"
        assert "github.com" in result["pr_url"]
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_create_pull_request_stub_workflow_not_found(self, mock_wf_manager):
        """Test PR creation stub with non-existent workflow."""
        mock_wf_manager.get_workflow.return_value = None
        
        with pytest.raises(SpecWorkflowError, match="Workflow not found"):
            self.orchestrator.create_pull_request_stub("nonexistent-workflow")
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_get_workflow_status(self, mock_wf_manager):
        """Test getting workflow status."""
        mock_workflow = Mock()
        mock_workflow.get_summary.return_value = {
            "workflow_id": "test-123",
            "status": "completed",
            "duration": 2.5
        }
        # Create mock steps with proper attributes
        step1 = Mock()
        step1.name = "Step 1"
        step1.stage = WorkflowStage.VALIDATION
        step1.status = WorkflowStatus.COMPLETED
        step1.duration = 0.5
        step1.error = None
        
        step2 = Mock()
        step2.name = "Step 2"
        step2.stage = WorkflowStage.GENERATION
        step2.status = WorkflowStatus.COMPLETED
        step2.duration = 1.0
        step2.error = None
        
        mock_workflow.steps = [step1, step2]
        
        mock_wf_manager.get_workflow.return_value = mock_workflow
        
        status = self.orchestrator.get_workflow_status("test-123")
        
        assert status is not None
        assert status["workflow_id"] == "test-123"
        assert status["status"] == "completed"
        assert len(status["steps"]) == 2
        assert status["steps"][0]["name"] == "Step 1"
        assert status["steps"][0]["stage"] == "validation"
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_get_workflow_status_not_found(self, mock_wf_manager):
        """Test getting status for non-existent workflow."""
        mock_wf_manager.get_workflow.return_value = None
        
        status = self.orchestrator.get_workflow_status("nonexistent")
        assert status is None
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_list_active_workflows(self, mock_wf_manager):
        """Test listing active workflows."""
        mock_workflow1 = Mock()
        mock_workflow1.get_summary.return_value = {"workflow_id": "active-1"}
        mock_workflow2 = Mock()
        mock_workflow2.get_summary.return_value = {"workflow_id": "active-2"}
        
        mock_wf_manager.get_active_workflows.return_value = [mock_workflow1, mock_workflow2]
        
        active = self.orchestrator.list_active_workflows()
        
        assert len(active) == 2
        assert active[0]["workflow_id"] == "active-1"
        assert active[1]["workflow_id"] == "active-2"
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    @patch('spec_cli.core.workflow_orchestrator.debug_logger')
    def test_cancel_workflow_success(self, mock_logger, mock_wf_manager):
        """Test successfully cancelling a workflow."""
        mock_workflow = Mock()
        mock_workflow.status = WorkflowStatus.RUNNING
        mock_wf_manager.get_workflow.return_value = mock_workflow
        
        result = self.orchestrator.cancel_workflow("test-workflow-123")
        
        assert result is True
        assert mock_workflow.status == WorkflowStatus.CANCELLED
        mock_wf_manager.fail_workflow.assert_called_once_with("test-workflow-123", "Cancelled by user")
        mock_logger.log.assert_called_with("INFO", "Workflow cancelled", workflow_id="test-workflow-123")
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_cancel_workflow_not_found(self, mock_wf_manager):
        """Test cancelling a non-existent workflow."""
        mock_wf_manager.get_workflow.return_value = None
        
        result = self.orchestrator.cancel_workflow("nonexistent")
        assert result is False
    
    @patch('spec_cli.core.workflow_orchestrator.workflow_state_manager')
    def test_cancel_workflow_not_running(self, mock_wf_manager):
        """Test cancelling a workflow that's not running."""
        mock_workflow = Mock()
        mock_workflow.status = WorkflowStatus.COMPLETED
        mock_wf_manager.get_workflow.return_value = mock_workflow
        
        result = self.orchestrator.cancel_workflow("completed-workflow")
        assert result is False

class TestWorkflowExecutionStages:
    """Test individual workflow execution stages."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.specs_dir = Path("/test/.specs")
        
        with patch('spec_cli.core.workflow_orchestrator.get_settings', return_value=self.mock_settings), \
             patch('spec_cli.core.workflow_orchestrator.RepositoryStateChecker') as mock_state_checker, \
             patch('spec_cli.core.workflow_orchestrator.SpecCommitManager') as mock_commit_manager, \
             patch('spec_cli.core.workflow_orchestrator.SpecContentGenerator') as mock_content_gen, \
             patch('spec_cli.core.workflow_orchestrator.DirectoryManager') as mock_dir_manager:
            
            self.orchestrator = SpecWorkflowOrchestrator(self.mock_settings)
            self.mock_state_checker = mock_state_checker.return_value
            self.mock_commit_manager = mock_commit_manager.return_value
    
    def test_execute_validation_stage_success(self):
        """Test successful validation stage."""
        from spec_cli.core.workflow_state import WorkflowState
        
        workflow = WorkflowState("test-123", "spec_generation")
        test_file = Path("/test/src/example.py")
        
        # Setup mocks for successful validation
        self.mock_state_checker.is_safe_for_spec_operations.return_value = True
        self.mock_state_checker.validate_pre_operation_state.return_value = []
        
        with patch.object(Path, 'exists', return_value=True):
            self.orchestrator._execute_validation_stage(workflow, test_file)
        
        # Verify step was completed successfully
        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.name == "Pre-flight validation"
        assert step.status == WorkflowStatus.COMPLETED
        assert step.result == {"validated": True}
    
    def test_execute_validation_stage_unsafe_repo(self):
        """Test validation stage with unsafe repository."""
        from spec_cli.core.workflow_state import WorkflowState
        
        workflow = WorkflowState("test-456", "spec_generation")
        test_file = Path("/test/src/example.py")
        
        # Setup mock for unsafe repository
        self.mock_state_checker.is_safe_for_spec_operations.return_value = False
        
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(SpecWorkflowError, match="Repository is not safe"):
                self.orchestrator._execute_validation_stage(workflow, test_file)
        
        # Verify step was failed
        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.status == WorkflowStatus.FAILED
    
    def test_execute_backup_stage_success(self):
        """Test successful backup stage."""
        from spec_cli.core.workflow_state import WorkflowState
        
        workflow = WorkflowState("test-backup", "spec_generation")
        
        # Setup successful tag creation
        self.mock_commit_manager.create_tag.return_value = {
            "success": True,
            "commit_hash": "backup123"
        }
        
        result = self.orchestrator._execute_backup_stage(workflow)
        
        # Verify backup was created
        assert result["backup_tag"] == f"backup-{workflow.workflow_id}"
        assert result["commit_hash"] == "backup123"
        assert workflow.metadata["backup_tag"] == f"backup-{workflow.workflow_id}"
        assert workflow.metadata["backup_commit"] == "backup123"
        
        # Verify step was completed
        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.name == "Create backup"
        assert step.status == WorkflowStatus.COMPLETED
    
    def test_execute_backup_stage_failure(self):
        """Test backup stage failure."""
        from spec_cli.core.workflow_state import WorkflowState
        
        workflow = WorkflowState("test-backup-fail", "spec_generation")
        
        # Setup failed tag creation
        self.mock_commit_manager.create_tag.return_value = {
            "success": False,
            "errors": ["Tag creation failed"]
        }
        
        with pytest.raises(SpecWorkflowError, match="Backup creation failed"):
            self.orchestrator._execute_backup_stage(workflow)
        
        # Verify step was failed
        assert len(workflow.steps) == 1
        step = workflow.steps[0]
        assert step.status == WorkflowStatus.FAILED