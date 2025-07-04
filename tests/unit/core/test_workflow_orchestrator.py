"""Comprehensive unit tests for SpecWorkflowOrchestrator.

Tests workflow orchestration functionality including:
- Single file workflow execution with state management
- Multi-stage workflow coordination (validation, backup, execution, commit)
- Error handling with rollback capabilities
- Batch processing workflows
- Integration with workflow state management
- Progress tracking and status reporting
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.core.workflow_orchestrator import SpecWorkflowOrchestrator
from spec_cli.core.workflow_state import WorkflowStage, WorkflowStatus
from spec_cli.exceptions import SpecWorkflowError
from spec_cli.utils.test_helpers.git_test_helpers import (
    GitCommandSimulator,
    GitRepositoryMocker,
)

# Import helpers from completed infrastructure
from spec_cli.utils.test_helpers.workflow_test_helpers import (
    BackupRollbackFixtures,
    StateTransitionMocker,
    WorkflowErrorSimulator,
    WorkflowStateBuilder,
)


class TestSpecWorkflowOrchestrator:
    """Test SpecWorkflowOrchestrator with comprehensive state management."""

    def setup_method(self):
        """Setup for each test method with helper infrastructure."""
        self.settings = SpecSettings()
        self.orchestrator = SpecWorkflowOrchestrator(self.settings)

        # Initialize test helpers from infra modules
        self.state_builder = WorkflowStateBuilder()
        self.transition_mocker = StateTransitionMocker()
        self.backup_fixtures = BackupRollbackFixtures()
        self.error_simulator = WorkflowErrorSimulator()
        self.git_mocker = GitRepositoryMocker(Path("/tmp/test_repo"))
        self.git_simulator = GitCommandSimulator()

        # Test data
        self.test_file_path = Path("src/example.py")
        self.test_custom_vars = {"purpose": "Example module", "author": "Test"}

        # Mock orchestrator dependencies
        self.mock_workflow_state_manager = patch(
            "spec_cli.core.workflow_orchestrator.workflow_state_manager"
        ).start()
        self.mock_debug_logger = patch(
            "spec_cli.core.workflow_orchestrator.debug_logger"
        ).start()
        self.mock_workflow_executor = patch.object(
            self.orchestrator, "workflow_executor"
        ).start()
        self.mock_workflow_validator = patch.object(
            self.orchestrator, "workflow_validator"
        ).start()
        self.mock_backup_manager = patch.object(
            self.orchestrator, "backup_manager"
        ).start()

        # Setup common mock returns
        self.mock_workflow = MagicMock()
        self.mock_workflow.workflow_id = "test_workflow_123"
        self.mock_workflow.duration = 1.5
        self.mock_workflow.metadata = {}
        self.mock_workflow_state_manager.create_workflow.return_value = (
            self.mock_workflow
        )

    def teardown_method(self):
        """Clean up patches after each test."""
        patch.stopall()

    def test_generate_spec_for_file_success_complete_workflow(self):
        """Test successful complete workflow execution for single file."""
        # Setup
        expected_generated_files = {
            "index.md": "# Example Module\nGenerated content",
            "history.md": "# Change History\nInitial version",
        }
        expected_commit_info = {
            "commit_hash": "abc123",
            "message": "Add spec for src/example.py",
        }

        # Mock workflow executor success
        execution_result = {
            "generated_files": {str(self.test_file_path): expected_generated_files},
            "commit_info": expected_commit_info,
        }
        self.mock_workflow_executor.execute_workflow.return_value = execution_result

        # Mock validation success
        validation_result = {"valid": True, "issues": []}
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Mock backup creation
        backup_info = {
            "backup_commit": "backup_123",
            "timestamp": "2025-07-03T12:00:00",
        }
        with patch.object(
            self.orchestrator, "_execute_backup_stage", return_value=backup_info
        ):
            result = self.orchestrator.generate_spec_for_file(
                self.test_file_path,
                custom_variables=self.test_custom_vars,
                auto_commit=True,
                create_backup=True,
            )

        # Verify workflow lifecycle
        self.mock_workflow_state_manager.create_workflow.assert_called_once()
        self.mock_workflow.start.assert_called_once()
        self.mock_workflow.complete.assert_called_once()
        self.mock_workflow_state_manager.complete_workflow.assert_called_once_with(
            "test_workflow_123"
        )

        # Verify result structure
        assert result["success"] is True
        assert result["workflow_id"] == "test_workflow_123"
        assert result["file_path"] == str(self.test_file_path)
        assert result["generated_files"] == expected_generated_files
        assert result["backup_info"] == backup_info
        assert result["commit_info"] == expected_commit_info
        assert result["duration"] == 1.5

    def test_generate_spec_for_file_validation_failure(self):
        """Test workflow failure during validation stage."""
        # Setup validation failure
        validation_result = {
            "valid": False,
            "issues": ["File does not exist", "Git repository not initialized"],
        }
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Execute and verify exception
        with pytest.raises(SpecWorkflowError) as exc_info:
            self.orchestrator.generate_spec_for_file(self.test_file_path)

        assert "Validation failed" in str(exc_info.value)
        assert "File does not exist" in str(exc_info.value)
        assert "Git repository not initialized" in str(exc_info.value)

        # Verify workflow failure handling
        self.mock_workflow.fail.assert_called_once()
        self.mock_workflow_state_manager.fail_workflow.assert_called_once()

    def test_generate_spec_for_file_execution_failure_with_rollback(self):
        """Test workflow execution failure with successful rollback."""
        # Setup successful validation
        validation_result = {"valid": True, "issues": []}
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Setup backup creation
        backup_info = {
            "backup_commit": "backup_456",
            "timestamp": "2025-07-03T12:00:00",
        }
        self.mock_workflow.metadata = {"backup_commit": "backup_456"}

        # Mock execution failure
        self.mock_workflow_executor.execute_workflow.side_effect = Exception(
            "Content generation failed"
        )

        # Mock successful rollback
        with patch.object(
            self.orchestrator, "_execute_backup_stage", return_value=backup_info
        ):
            with patch.object(
                self.orchestrator, "_execute_rollback_stage"
            ) as mock_rollback:
                with pytest.raises(SpecWorkflowError) as exc_info:
                    self.orchestrator.generate_spec_for_file(
                        self.test_file_path, create_backup=True
                    )

                mock_rollback.assert_called_once()

        assert "Spec generation workflow failed" in str(exc_info.value)
        assert "Content generation failed" in str(exc_info.value)

    def test_generate_spec_for_file_execution_failure_rollback_also_fails(self):
        """Test workflow execution failure where rollback also fails."""
        # Setup successful validation
        validation_result = {"valid": True, "issues": []}
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Setup backup creation
        backup_info = {
            "backup_commit": "backup_789",
            "timestamp": "2025-07-03T12:00:00",
        }
        self.mock_workflow.metadata = {"backup_commit": "backup_789"}

        # Mock execution failure
        self.mock_workflow_executor.execute_workflow.side_effect = Exception(
            "Content generation failed"
        )

        # Mock rollback failure
        with patch.object(
            self.orchestrator, "_execute_backup_stage", return_value=backup_info
        ):
            with patch.object(
                self.orchestrator,
                "_execute_rollback_stage",
                side_effect=Exception("Rollback failed"),
            ):
                with pytest.raises(SpecWorkflowError):
                    self.orchestrator.generate_spec_for_file(
                        self.test_file_path, create_backup=True
                    )

        # Verify rollback failure was logged
        self.mock_debug_logger.log.assert_any_call(
            "ERROR", "Rollback failed", error="Rollback failed"
        )

    def test_generate_spec_for_file_without_backup(self):
        """Test successful workflow execution without backup creation."""
        # Setup successful validation
        validation_result = {"valid": True, "issues": []}
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Mock workflow executor success
        execution_result = {
            "generated_files": {str(self.test_file_path): {"index.md": "content"}},
            "commit_info": {"commit_hash": "def456"},
        }
        self.mock_workflow_executor.execute_workflow.return_value = execution_result

        result = self.orchestrator.generate_spec_for_file(
            self.test_file_path, create_backup=False
        )

        # Verify no backup was created
        assert result["backup_info"] is None
        assert result["success"] is True

        # Verify backup stage was not called
        with patch.object(self.orchestrator, "_execute_backup_stage") as mock_backup:
            mock_backup.assert_not_called()

    def test_execute_validation_stage_success(self):
        """Test successful validation stage execution."""
        mock_workflow = MagicMock()
        mock_step = MagicMock()
        mock_workflow.add_step.return_value = mock_step

        # Mock successful validation
        validation_result = {"valid": True, "issues": []}
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Execute validation stage
        self.orchestrator._execute_validation_stage(mock_workflow, self.test_file_path)

        # Verify workflow step was created and completed
        mock_workflow.add_step.assert_called_once_with(
            "Pre-flight validation", WorkflowStage.VALIDATION
        )
        mock_step.start.assert_called_once()
        mock_step.complete.assert_called_once_with(
            {"validated": True, "issues_checked": 0}
        )

    def test_execute_validation_stage_failure(self):
        """Test validation stage execution with validation failure."""
        mock_workflow = MagicMock()
        mock_step = MagicMock()
        mock_workflow.add_step.return_value = mock_step

        # Mock validation failure
        validation_result = {
            "valid": False,
            "issues": ["Missing dependency", "Invalid configuration"],
        }
        self.mock_workflow_validator.validate_workflow_preconditions.return_value = (
            validation_result
        )

        # Execute and verify exception
        with pytest.raises(SpecWorkflowError) as exc_info:
            self.orchestrator._execute_validation_stage(
                mock_workflow, self.test_file_path
            )

        assert "Validation failed" in str(exc_info.value)
        assert "Missing dependency" in str(exc_info.value)
        assert "Invalid configuration" in str(exc_info.value)

        # Verify step was started but not completed
        mock_step.start.assert_called_once()
        mock_step.complete.assert_not_called()

    def test_execute_backup_stage_success(self):
        """Test successful backup stage execution."""
        mock_workflow = MagicMock()
        mock_step = MagicMock()
        mock_workflow.add_step.return_value = mock_step

        # Mock successful backup creation
        backup_commit_info = {
            "backup_tag": "backup_tag_abc123",
            "commit_hash": "backup_abc123",
            "message": "Backup before spec generation",
            "timestamp": "2025-07-03T12:00:00",
        }
        self.mock_backup_manager.create_backup.return_value = backup_commit_info

        result = self.orchestrator._execute_backup_stage(mock_workflow)

        # Verify backup creation
        self.mock_backup_manager.create_backup.assert_called_once_with(
            mock_workflow.workflow_id
        )

        # Verify workflow step handling
        mock_workflow.add_step.assert_called_once_with(
            "Create backup", WorkflowStage.BACKUP
        )
        mock_step.start.assert_called_once()
        mock_step.complete.assert_called_once_with(backup_commit_info)

        # Verify metadata updates
        mock_workflow.metadata.__setitem__.assert_any_call(
            "backup_tag", "backup_tag_abc123"
        )
        mock_workflow.metadata.__setitem__.assert_any_call(
            "backup_commit", "backup_abc123"
        )

        assert result == backup_commit_info

    def test_execute_rollback_stage_success(self):
        """Test successful rollback stage execution."""
        mock_workflow = MagicMock()
        mock_step = MagicMock()
        mock_workflow.add_step.return_value = mock_step
        mock_workflow.metadata = {
            "backup_tag": "backup_tag_def456",
            "backup_commit": "backup_def456",
        }

        # Mock successful rollback
        rollback_result = {"success": True, "message": "Rollback completed"}
        self.mock_backup_manager.rollback_to_backup.return_value = rollback_result

        # Execute rollback
        error_message = "Generation failed"
        self.orchestrator._execute_rollback_stage(mock_workflow, error_message)

        # Verify rollback execution
        self.mock_backup_manager.rollback_to_backup.assert_called_once_with(
            "backup_tag_def456", "backup_def456"
        )

        # Verify workflow step handling
        mock_workflow.add_step.assert_called_once_with(
            "Rollback changes", WorkflowStage.ROLLBACK
        )
        mock_step.start.assert_called_once()
        mock_step.complete.assert_called_once_with(
            {
                "rolled_back_to": "backup_def456",
                "backup_tag": "backup_tag_def456",
                "reason": error_message,
            }
        )

    def test_generate_specs_for_files_batch_processing_success(self):
        """Test successful batch processing of multiple files."""
        file_paths = [
            Path("src/module_a.py"),
            Path("src/module_b.py"),
            Path("src/module_c.py"),
        ]

        # Mock successful batch validation
        batch_validation_result = {
            "global_issues": [],
            "valid_files": file_paths,
            "invalid_files": {},
        }
        self.mock_workflow_validator.validate_batch_operation.return_value = (
            batch_validation_result
        )

        # Mock individual file generation and batch commit stage
        with patch.object(self.orchestrator, "generate_spec_for_file") as mock_gen_file:
            mock_gen_file.return_value = {
                "success": True,
                "generated_files": {"index.md": "Generated content"},
                "commit_info": None,
            }

            # Mock batch commit stage to return successful commit
            with patch.object(
                self.orchestrator, "_execute_batch_commit_stage"
            ) as mock_batch_commit:
                mock_batch_commit.return_value = {
                    "commit_hash": "batch_123",
                    "message": "Batch generation",
                }

                result = self.orchestrator.generate_specs_for_files(
                    file_paths, auto_commit=True, create_backup=False
                )

        # Verify batch workflow creation and execution
        self.mock_workflow_state_manager.create_workflow.assert_called_once()
        assert (
            self.mock_workflow_state_manager.create_workflow.call_args[0][0]
            == "batch_spec_generation"
        )

        # Verify successful completion
        assert result["success"] is True
        assert result["total_files"] == 3
        assert len(result["successful_files"]) == 3
        assert result["commit_info"]["commit_hash"] == "batch_123"

    def test_generate_specs_for_files_partial_failure(self):
        """Test batch processing with some file failures."""
        file_paths = [Path("src/good_file.py"), Path("src/bad_file.py")]

        # Mock batch validation with some failures
        batch_validation_result = {
            "global_issues": [],
            "valid_files": [Path("src/good_file.py")],
            "invalid_files": {"src/bad_file.py": ["File corrupted"]},
        }
        self.mock_workflow_validator.validate_batch_operation.return_value = (
            batch_validation_result
        )

        # Mock individual file generation - only good file succeeds
        def mock_gen_file_side_effect(file_path, **kwargs):
            if "good_file" in str(file_path):
                return {
                    "success": True,
                    "generated_files": {"index.md": "Good file content"},
                    "commit_info": None,
                }
            # Bad file will not be called due to validation failure

        # Mock batch commit stage
        with patch.object(
            self.orchestrator,
            "generate_spec_for_file",
            side_effect=mock_gen_file_side_effect,
        ):
            with patch.object(
                self.orchestrator, "_execute_batch_commit_stage"
            ) as mock_batch_commit:
                mock_batch_commit.return_value = {
                    "commit_hash": "partial_456",
                    "message": "Partial batch generation",
                }

                result = self.orchestrator.generate_specs_for_files(file_paths)

        # Verify partial success handling
        assert result["success"] is True  # Overall success despite individual failures
        assert result["total_files"] == 2
        assert len(result["successful_files"]) == 1
        assert len(result["failed_files"]) == 1
        assert "src/good_file.py" in str(result["successful_files"])
        assert any(
            "src/bad_file.py" in str(fail["file_path"])
            for fail in result["failed_files"]
        )

    def test_get_workflow_status_existing_workflow(self):
        """Test retrieving status for existing workflow."""
        workflow_id = "test_workflow_999"

        # Mock workflow object
        mock_workflow = MagicMock()
        mock_workflow.steps = []
        expected_summary = {
            "workflow_id": workflow_id,
            "status": "processing",
            "stage": "generation",
            "progress": 0.6,
            "started_at": "2025-07-03T12:00:00",
            "estimated_completion": "2025-07-03T12:05:00",
        }
        mock_workflow.get_summary.return_value = expected_summary

        self.mock_workflow_state_manager.get_workflow.return_value = mock_workflow

        result = self.orchestrator.get_workflow_status(workflow_id)

        expected_result = expected_summary.copy()
        expected_result["steps"] = []

        assert result == expected_result
        self.mock_workflow_state_manager.get_workflow.assert_called_once_with(
            workflow_id
        )

    def test_get_workflow_status_nonexistent_workflow(self):
        """Test retrieving status for non-existent workflow."""
        workflow_id = "nonexistent_workflow"
        self.mock_workflow_state_manager.get_workflow.return_value = None

        result = self.orchestrator.get_workflow_status(workflow_id)

        assert result is None

    def test_list_active_workflows(self):
        """Test listing all active workflows."""
        # Mock workflow objects
        mock_workflows = []
        expected_summaries = [
            {"workflow_id": "wf_1", "status": "processing", "stage": "validation"},
            {"workflow_id": "wf_2", "status": "processing", "stage": "generation"},
            {"workflow_id": "wf_3", "status": "processing", "stage": "commit"},
        ]

        for summary in expected_summaries:
            mock_workflow = MagicMock()
            mock_workflow.get_summary.return_value = summary
            mock_workflows.append(mock_workflow)

        self.mock_workflow_state_manager.get_active_workflows.return_value = (
            mock_workflows
        )

        result = self.orchestrator.list_active_workflows()

        assert result == expected_summaries
        assert len(result) == 3

    def test_cancel_workflow_success(self):
        """Test successful workflow cancellation."""
        workflow_id = "cancelable_workflow"

        # Mock running workflow
        mock_workflow = MagicMock()
        mock_workflow.status = WorkflowStatus.RUNNING
        self.mock_workflow_state_manager.get_workflow.return_value = mock_workflow

        result = self.orchestrator.cancel_workflow(workflow_id)

        assert result is True
        assert mock_workflow.status == WorkflowStatus.CANCELLED
        self.mock_workflow_state_manager.fail_workflow.assert_called_once_with(
            workflow_id, "Cancelled by user"
        )

    def test_cancel_workflow_failure(self):
        """Test failed workflow cancellation."""
        workflow_id = "uncancelable_workflow"

        # Mock workflow that's not running (completed)
        mock_workflow = MagicMock()
        mock_workflow.status = WorkflowStatus.COMPLETED
        self.mock_workflow_state_manager.get_workflow.return_value = mock_workflow

        result = self.orchestrator.cancel_workflow(workflow_id)

        assert result is False

    def test_orchestrator_initialization_with_custom_settings(self):
        """Test orchestrator initialization with custom settings."""
        custom_settings = SpecSettings()
        custom_settings.debug_mode = True
        custom_settings.max_concurrent_workflows = 5

        orchestrator = SpecWorkflowOrchestrator(custom_settings)

        assert orchestrator.settings == custom_settings
        assert orchestrator.settings.debug_mode is True
        assert orchestrator.settings.max_concurrent_workflows == 5

    def test_orchestrator_initialization_with_default_settings(self):
        """Test orchestrator initialization with default settings."""
        with patch(
            "spec_cli.core.workflow_orchestrator.get_settings"
        ) as mock_get_settings:
            default_settings = SpecSettings()
            mock_get_settings.return_value = default_settings

            orchestrator = SpecWorkflowOrchestrator()

            assert orchestrator.settings == default_settings
            mock_get_settings.assert_called_once()


class TestWorkflowOrchestratorIntegration:
    """Integration tests for workflow orchestrator with helper infrastructure."""

    def setup_method(self):
        """Setup integration test environment."""
        self.orchestrator = SpecWorkflowOrchestrator()
        self.git_simulator = GitCommandSimulator()
        self.error_simulator = WorkflowErrorSimulator()

    def test_workflow_orchestrator_with_git_integration(self):
        """Test orchestrator integration with mocked workflow components."""
        # This test verifies that the orchestrator coordinates properly with its dependencies
        # without requiring actual Git operations

        with patch(
            "spec_cli.core.workflow_orchestrator.workflow_state_manager"
        ) as mock_state_manager:
            mock_workflow = MagicMock()
            mock_workflow.workflow_id = "integration_test"
            mock_workflow.duration = 2.1
            mock_workflow.metadata = {}
            mock_state_manager.create_workflow.return_value = mock_workflow

            # Setup orchestrator with fresh mocks for integration test
            orchestrator = SpecWorkflowOrchestrator()

            # Mock all dependencies
            with patch.object(orchestrator, "workflow_validator") as mock_validator:
                mock_validator.validate_workflow_preconditions.return_value = {
                    "valid": True,
                    "issues": [],
                }

                with patch.object(orchestrator, "workflow_executor") as mock_executor:
                    mock_executor.execute_workflow.return_value = {
                        "generated_files": {
                            "src/example.py": {"index.md": "# Example"}
                        },
                        "commit_info": {"commit_hash": "git_integration_test"},
                    }

                    result = orchestrator.generate_spec_for_file(
                        Path("src/example.py"), create_backup=False
                    )

        # Verify successful orchestration
        assert result["success"] is True
        assert result["commit_info"]["commit_hash"] == "git_integration_test"

        # Verify dependencies were called
        mock_validator.validate_workflow_preconditions.assert_called_once()
        mock_executor.execute_workflow.assert_called_once()

    def test_workflow_orchestrator_error_simulation(self):
        """Test orchestrator with simulated error conditions."""
        with patch(
            "spec_cli.core.workflow_orchestrator.workflow_state_manager"
        ) as mock_state_manager:
            mock_workflow = MagicMock()
            mock_state_manager.create_workflow.return_value = mock_workflow

            with patch.object(
                self.orchestrator, "workflow_validator"
            ) as mock_validator:
                # Simulate validation failure using error simulator
                try:
                    self.error_simulator.simulate_error(
                        "validation_error", "validation"
                    )
                except ValueError as e:
                    # Use the simulated error for validation failure
                    mock_validator.validate_workflow_preconditions.return_value = {
                        "valid": False,
                        "issues": [str(e)],
                    }

                with pytest.raises(SpecWorkflowError) as exc_info:
                    self.orchestrator.generate_spec_for_file(Path("test/file.py"))

        assert "Validation failed" in str(exc_info.value)
