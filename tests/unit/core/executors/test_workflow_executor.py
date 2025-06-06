"""Unit tests for WorkflowExecutor class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.core.executors.workflow_executor import WorkflowExecutor
from spec_cli.core.workflow_state import WorkflowStage, WorkflowState
from spec_cli.exceptions import SpecWorkflowError


class TestWorkflowExecutor:
    """Test cases for WorkflowExecutor class."""

    @pytest.fixture
    def mock_content_generator(self):
        """Mock content generator for testing."""
        mock_generator = Mock()
        mock_generator.generate_spec_content.return_value = {
            "index": Path("/test/.specs/src/main/index.md"),
            "history": Path("/test/.specs/src/main/history.md"),
        }
        return mock_generator

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for testing."""
        mock_manager = Mock()
        mock_manager.add_files.return_value = {"success": True, "errors": []}
        mock_manager.commit_changes.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "errors": [],
        }
        return mock_manager

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.specs_dir = Path("/test/.specs")
        return settings

    @pytest.fixture
    def workflow_executor(
        self, mock_content_generator, mock_commit_manager, mock_settings
    ):
        """Create WorkflowExecutor instance for testing."""
        return WorkflowExecutor(
            mock_content_generator, mock_commit_manager, mock_settings
        )

    @pytest.fixture
    def mock_workflow(self):
        """Mock workflow state for testing."""
        workflow = Mock(spec=WorkflowState)
        workflow.workflow_id = "test-workflow-123"

        # Mock step creation
        mock_step = Mock()
        mock_step.start.return_value = None
        mock_step.complete.return_value = None
        mock_step.fail.return_value = None
        workflow.add_step.return_value = mock_step

        return workflow

    @pytest.fixture
    def sample_file_path(self):
        """Sample file path for testing."""
        return Path("src/main.py")

    @pytest.fixture
    def sample_options(self):
        """Sample workflow options for testing."""
        return {
            "auto_commit": True,
            "custom_variables": {"project": "test-project"},
        }

    def test_initialization_creates_error_handler(
        self, mock_content_generator, mock_commit_manager, mock_settings
    ):
        """Test WorkflowExecutor initialization creates error handler."""
        executor = WorkflowExecutor(
            mock_content_generator, mock_commit_manager, mock_settings
        )

        assert executor.content_generator == mock_content_generator
        assert executor.commit_manager == mock_commit_manager
        assert executor.settings == mock_settings
        assert executor.error_handler is not None

    def test_execute_workflow_when_successful_then_returns_complete_result(
        self, workflow_executor, mock_workflow, sample_file_path, sample_options
    ):
        """Test successful workflow execution returns complete result."""
        with patch(
            "spec_cli.core.executors.workflow_executor.load_template"
        ) as mock_load_template:
            mock_template = Mock()
            mock_load_template.return_value = mock_template

            result = workflow_executor.execute_workflow(
                mock_workflow, sample_file_path, sample_options
            )

            # Verify result structure
            assert result["success"] is True
            assert result["workflow_id"] == "test-workflow-123"
            assert result["total_files"] == 1
            assert str(sample_file_path) in result["successful_files"]
            assert str(sample_file_path) in result["generated_files"]
            assert result["commit_info"] is not None

            # Verify commit info structure
            commit_info = result["commit_info"]
            assert "commit_hash" in commit_info
            assert "files_committed" in commit_info
            assert "commit_message" in commit_info

    def test_execute_workflow_when_auto_commit_false_then_no_commit_info(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test workflow execution without auto_commit returns no commit info."""
        options = {"auto_commit": False, "custom_variables": {}}

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            result = workflow_executor.execute_workflow(
                mock_workflow, sample_file_path, options
            )

            assert result["success"] is True
            assert result["commit_info"] is None

    def test_execute_workflow_when_generation_fails_then_raises_workflow_error(
        self, workflow_executor, mock_workflow, sample_file_path, sample_options
    ):
        """Test workflow execution raises SpecWorkflowError when generation fails."""
        workflow_executor.content_generator.generate_spec_content.side_effect = (
            Exception("Generation failed")
        )

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            with pytest.raises(SpecWorkflowError, match="Workflow execution failed"):
                workflow_executor.execute_workflow(
                    mock_workflow, sample_file_path, sample_options
                )

    def test_execute_workflow_when_commit_fails_then_raises_workflow_error(
        self, workflow_executor, mock_workflow, sample_file_path, sample_options
    ):
        """Test workflow execution raises SpecWorkflowError when commit fails."""
        workflow_executor.commit_manager.commit_changes.return_value = {
            "success": False,
            "errors": ["Commit failed"],
        }

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            with pytest.raises(SpecWorkflowError, match="Workflow execution failed"):
                workflow_executor.execute_workflow(
                    mock_workflow, sample_file_path, sample_options
                )

    def test_execute_generation_stage_when_successful_then_returns_generated_files(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test generation stage returns generated files."""
        with patch(
            "spec_cli.core.executors.workflow_executor.load_template"
        ) as mock_load_template:
            mock_template = Mock()
            mock_load_template.return_value = mock_template

            generated_files = workflow_executor._execute_generation_stage(
                mock_workflow, sample_file_path, {"custom": "vars"}
            )

            assert "index" in generated_files
            assert "history" in generated_files
            assert isinstance(generated_files["index"], Path)
            assert isinstance(generated_files["history"], Path)

            # Verify content generator was called correctly
            workflow_executor.content_generator.generate_spec_content.assert_called_once_with(
                file_path=sample_file_path,
                template=mock_template,
                custom_variables={"custom": "vars"},
                backup_existing=True,
            )

    def test_execute_generation_stage_when_fails_then_raises_and_fails_step(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test generation stage failure raises exception and fails workflow step."""
        workflow_executor.content_generator.generate_spec_content.side_effect = (
            Exception("Generation error")
        )

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            with pytest.raises(Exception, match="Generation error"):
                workflow_executor._execute_generation_stage(
                    mock_workflow, sample_file_path, None
                )

            # Verify step was failed
            mock_step = mock_workflow.add_step.return_value
            mock_step.fail.assert_called_once_with("Generation error")

    def test_execute_commit_stage_when_successful_then_returns_commit_info(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test commit stage returns commit information."""
        generated_files = {
            "index": Path("/test/.specs/src/main/index.md"),
            "history": Path("/test/.specs/src/main/history.md"),
        }

        commit_info = workflow_executor._execute_commit_stage(
            mock_workflow, sample_file_path, generated_files
        )

        assert commit_info["commit_hash"] == "abc123"
        assert "files_committed" in commit_info
        assert "commit_message" in commit_info
        assert sample_file_path.name in commit_info["commit_message"]

        # Verify commit manager was called correctly
        expected_files = ["src/main/index.md", "src/main/history.md"]
        workflow_executor.commit_manager.add_files.assert_called_once_with(
            expected_files
        )
        workflow_executor.commit_manager.commit_changes.assert_called_once()

    def test_execute_commit_stage_when_no_files_to_commit_then_raises_error(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test commit stage raises error when no files are within specs directory."""
        generated_files = {
            "index": Path("/outside/.specs/src/main/index.md"),  # Outside specs_dir
        }

        with pytest.raises(SpecWorkflowError, match="No files to commit"):
            workflow_executor._execute_commit_stage(
                mock_workflow, sample_file_path, generated_files
            )

    def test_execute_commit_stage_when_add_files_fails_then_raises_error(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test commit stage raises error when adding files fails."""
        workflow_executor.commit_manager.add_files.return_value = {
            "success": False,
            "errors": ["Add failed"],
        }

        generated_files = {
            "index": Path("/test/.specs/src/main/index.md"),
        }

        with pytest.raises(SpecWorkflowError, match="Failed to add files"):
            workflow_executor._execute_commit_stage(
                mock_workflow, sample_file_path, generated_files
            )

    def test_execute_commit_stage_when_commit_fails_then_raises_error(
        self, workflow_executor, mock_workflow, sample_file_path
    ):
        """Test commit stage raises error when commit operation fails."""
        workflow_executor.commit_manager.commit_changes.return_value = {
            "success": False,
            "errors": ["Commit failed"],
        }

        generated_files = {
            "index": Path("/test/.specs/src/main/index.md"),
        }

        with pytest.raises(SpecWorkflowError, match="Failed to commit"):
            workflow_executor._execute_commit_stage(
                mock_workflow, sample_file_path, generated_files
            )

    def test_execute_cleanup_stage_when_successful_then_completes_step(
        self, workflow_executor, mock_workflow
    ):
        """Test cleanup stage completes successfully."""
        workflow_executor._execute_cleanup_stage(mock_workflow)

        # Verify step was completed
        mock_step = mock_workflow.add_step.return_value
        mock_step.complete.assert_called_once_with({"cleaned_up": True})

    def test_execute_cleanup_stage_when_fails_then_logs_warning_and_fails_step(
        self, workflow_executor, mock_workflow
    ):
        """Test cleanup stage logs warning when it fails."""
        # Mock step to raise exception during complete
        mock_step = mock_workflow.add_step.return_value
        mock_step.complete.side_effect = Exception("Cleanup error")

        # Should not raise exception (cleanup failures are warnings)
        workflow_executor._execute_cleanup_stage(mock_workflow)

        # Verify step was failed
        mock_step.fail.assert_called_once_with("Cleanup error")

    def test_workflow_executor_handles_path_conversion_correctly(
        self, workflow_executor, mock_workflow, sample_file_path, sample_options
    ):
        """Test WorkflowExecutor correctly converts paths for Git operations."""
        # Test with files that need path conversion
        workflow_executor.content_generator.generate_spec_content.return_value = {
            "index": Path("/test/.specs/src/main/index.md"),
            "history": Path("/test/.specs/src/main/history.md"),
        }

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            result = workflow_executor.execute_workflow(
                mock_workflow, sample_file_path, sample_options
            )

            # Verify files were added with correct relative paths
            expected_files = ["src/main/index.md", "src/main/history.md"]
            workflow_executor.commit_manager.add_files.assert_called_once_with(
                expected_files
            )

            assert result["success"] is True

    def test_workflow_executor_logs_warnings_for_files_outside_specs_dir(
        self, workflow_executor, mock_workflow, sample_file_path, sample_options
    ):
        """Test WorkflowExecutor logs warnings for files outside specs directory."""
        # Mock generated files with one outside specs directory
        workflow_executor.content_generator.generate_spec_content.return_value = {
            "index": Path("/test/.specs/src/main/index.md"),  # Inside specs_dir
            "outside": Path("/outside/specs/file.md"),  # Outside specs_dir
        }

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            with patch(
                "spec_cli.core.executors.workflow_executor.debug_logger"
            ) as mock_logger:
                result = workflow_executor.execute_workflow(
                    mock_workflow, sample_file_path, sample_options
                )

                # Verify warning was logged
                mock_logger.log.assert_any_call(
                    "WARNING",
                    "Generated file outside .specs directory",
                    file_path="/outside/specs/file.md",
                )

                # Only file inside specs_dir should be committed
                expected_files = ["src/main/index.md"]
                workflow_executor.commit_manager.add_files.assert_called_once_with(
                    expected_files
                )

                assert result["success"] is True


class TestWorkflowExecutorIntegration:
    """Integration tests for WorkflowExecutor with real workflow state."""

    @pytest.fixture
    def real_workflow(self):
        """Create real WorkflowState for integration testing."""
        from spec_cli.core.workflow_state import workflow_state_manager

        workflow = workflow_state_manager.create_workflow(
            "test_execution", {"file_path": "src/test.py", "auto_commit": True}
        )
        workflow.start()
        return workflow

    @pytest.fixture
    def mock_content_generator(self):
        """Mock content generator for integration testing."""
        mock_generator = Mock()
        mock_generator.generate_spec_content.return_value = {
            "index": Path("/test/.specs/src/test/index.md"),
            "history": Path("/test/.specs/src/test/history.md"),
        }
        return mock_generator

    @pytest.fixture
    def mock_commit_manager(self):
        """Mock commit manager for integration testing."""
        mock_manager = Mock()
        mock_manager.add_files.return_value = {"success": True, "errors": []}
        mock_manager.commit_changes.return_value = {
            "success": True,
            "commit_hash": "def456",
            "errors": [],
        }
        return mock_manager

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for integration testing."""
        settings = Mock(spec=SpecSettings)
        settings.specs_dir = Path("/test/.specs")
        return settings

    def test_workflow_executor_integration_with_real_workflow_state(
        self, real_workflow, mock_content_generator, mock_commit_manager, mock_settings
    ):
        """Test WorkflowExecutor integration with real WorkflowState."""
        executor = WorkflowExecutor(
            mock_content_generator, mock_commit_manager, mock_settings
        )

        file_path = Path("src/test.py")
        options = {"auto_commit": True, "custom_variables": {"test": "integration"}}

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            result = executor.execute_workflow(real_workflow, file_path, options)

            # Verify result
            assert result["success"] is True
            assert result["workflow_id"] == real_workflow.workflow_id

            # Verify workflow state was updated
            assert len(real_workflow.steps) == 3  # generation, commit, cleanup
            generation_step = real_workflow.steps[0]
            assert generation_step.name == "Generate spec content"
            assert generation_step.stage == WorkflowStage.GENERATION

            commit_step = real_workflow.steps[1]
            assert commit_step.name == "Commit generated content"
            assert commit_step.stage == WorkflowStage.COMMIT

            cleanup_step = real_workflow.steps[2]
            assert cleanup_step.name == "Cleanup temporary files"
            assert cleanup_step.stage == WorkflowStage.CLEANUP

    def test_workflow_executor_integration_error_handling_with_real_workflow(
        self, real_workflow, mock_content_generator, mock_commit_manager, mock_settings
    ):
        """Test WorkflowExecutor error handling with real WorkflowState."""
        # Configure content generator to fail
        mock_content_generator.generate_spec_content.side_effect = Exception(
            "Integration test error"
        )

        executor = WorkflowExecutor(
            mock_content_generator, mock_commit_manager, mock_settings
        )

        file_path = Path("src/test.py")
        options = {"auto_commit": True, "custom_variables": {}}

        with patch("spec_cli.core.executors.workflow_executor.load_template"):
            with pytest.raises(SpecWorkflowError, match="Workflow execution failed"):
                executor.execute_workflow(real_workflow, file_path, options)

            # Verify workflow step was failed
            assert len(real_workflow.steps) == 1
            failed_step = real_workflow.steps[0]
            assert failed_step.name == "Generate spec content"
            assert "Integration test error" in failed_step.error
