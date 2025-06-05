"""Tests for Slice 2: Decoupled BatchProcessor without workflow_orchestrator dependency."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.file_processing.batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
    BatchProcessingResult,
)
from spec_cli.utils.workflow_utils import create_workflow_result


class TestWorkflowUtils:
    """Test workflow_utils helper functions."""

    def test_create_workflow_result_when_successful_files_then_returns_success_result(
        self,
    ):
        """Test that create_workflow_result returns correct structure for successful files."""
        files = [Path("src/main.py"), Path("src/utils.py")]
        result = create_workflow_result(files, True, "batch-001")

        assert result["success"] is True
        assert result["total_files"] == 2
        assert result["successful_files"] == ["src/main.py", "src/utils.py"]
        assert result["failed_files"] == []
        assert result["workflow_id"] == "batch-001"
        assert "generated_files" in result
        assert "commit_info" in result
        assert "backup_info" in result

    def test_create_workflow_result_when_failed_files_then_returns_failure_result(self):
        """Test that create_workflow_result returns correct structure for failed files."""
        files = [Path("src/broken.py")]
        result = create_workflow_result(files, False)

        assert result["success"] is False
        assert result["total_files"] == 1
        assert result["successful_files"] == []
        assert result["failed_files"] == ["src/broken.py"]
        assert "workflow_id" not in result

    def test_create_workflow_result_when_empty_files_then_returns_empty_result(self):
        """Test that create_workflow_result handles empty file list."""
        files: list[Path] = []
        result = create_workflow_result(files, True)

        assert result["success"] is True
        assert result["total_files"] == 0
        assert result["successful_files"] == []
        assert result["failed_files"] == []


class TestDecoupledBatchProcessor:
    """Test BatchProcessor without workflow_orchestrator dependency."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.specs_dir = Path(".specs")
        return settings

    @pytest.fixture
    def mock_processor_components(self):
        """Mock all the processor's components."""
        with (
            patch(
                "spec_cli.file_processing.batch_processor.FileChangeDetector"
            ) as mock_detector,
            patch(
                "spec_cli.file_processing.batch_processor.ConflictResolver"
            ) as mock_resolver,
            patch(
                "spec_cli.file_processing.batch_processor.FileProcessingPipeline"
            ) as mock_pipeline,
            patch(
                "spec_cli.templates.generator.SpecContentGenerator"
            ) as mock_generator,
        ):
            yield {
                "detector": mock_detector,
                "resolver": mock_resolver,
                "pipeline": mock_pipeline,
                "generator": mock_generator,
            }

    def test_batch_processor_when_initialized_then_no_workflow_orchestrator(
        self, mock_settings, mock_processor_components
    ):
        """Test that BatchProcessor no longer depends on workflow_orchestrator."""
        processor = BatchFileProcessor(mock_settings)

        # Verify no workflow_orchestrator attribute exists
        assert not hasattr(processor, "workflow_orchestrator")

        # Verify required components exist
        assert hasattr(processor, "change_detector")
        assert hasattr(processor, "conflict_resolver")
        assert hasattr(processor, "pipeline")

    def test_handle_auto_commit_when_successful_files_then_uses_direct_git_operations(
        self, mock_settings, mock_processor_components
    ):
        """Test that auto-commit uses direct git operations instead of workflow orchestrator."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            # Mock successful git operations
            mock_repo.add_files.return_value = None  # void method
            mock_repo.commit.return_value = "abc123"  # returns commit hash

            processor = BatchFileProcessor(mock_settings)

            # Create test result with successful files
            result = BatchProcessingResult()
            result.successful_files = [Path("test1.py"), Path("test2.py")]

            options = BatchProcessingOptions(auto_commit=True)

            # Call _handle_auto_commit
            processor._handle_auto_commit(result, options)

            # Verify git operations were called
            mock_repo.add_files.assert_called_once_with(["test1.py", "test2.py"])
            mock_repo.commit.assert_called_once_with("Process 2 spec files")

            # Verify workflow_id was set
            assert result.workflow_id is not None
            assert result.workflow_id.startswith("batch-")

    def test_handle_auto_commit_when_git_add_fails_then_adds_warning(
        self, mock_settings, mock_processor_components
    ):
        """Test that auto-commit handles git add failures gracefully."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            # Mock failed git add (raises exception)
            mock_repo.add_files.side_effect = Exception("Git add failed")

            processor = BatchFileProcessor(mock_settings)

            result = BatchProcessingResult()
            result.successful_files = [Path("test.py")]
            result.warnings = []

            options = BatchProcessingOptions(auto_commit=True)

            processor._handle_auto_commit(result, options)

            # Verify warning was added
            assert len(result.warnings) == 1
            assert "Auto-commit failed: Git add failed" in result.warnings[0]

    def test_handle_auto_commit_when_git_commit_fails_then_adds_warning(
        self, mock_settings, mock_processor_components
    ):
        """Test that auto-commit handles git commit failures gracefully."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            # Mock successful add but failed commit
            mock_repo.add_files.return_value = None
            mock_repo.commit.side_effect = Exception("Git commit failed")

            processor = BatchFileProcessor(mock_settings)

            result = BatchProcessingResult()
            result.successful_files = [Path("test.py")]
            result.warnings = []

            options = BatchProcessingOptions(auto_commit=True)

            processor._handle_auto_commit(result, options)

            # Verify warning was added
            assert len(result.warnings) == 1
            assert "Auto-commit failed: Git commit failed" in result.warnings[0]

    def test_handle_auto_commit_when_exception_occurs_then_handles_gracefully(
        self, mock_settings, mock_processor_components
    ):
        """Test that auto-commit handles exceptions gracefully."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo_class.side_effect = Exception("Repository error")

            processor = BatchFileProcessor(mock_settings)

            result = BatchProcessingResult()
            result.successful_files = [Path("test.py")]
            result.warnings = []

            options = BatchProcessingOptions(auto_commit=True)

            processor._handle_auto_commit(result, options)

            # Verify warning was added
            assert len(result.warnings) == 1
            assert "Auto-commit failed: Repository error" in result.warnings[0]

    def test_process_files_when_auto_commit_enabled_then_calls_handle_auto_commit(
        self, mock_settings, mock_processor_components
    ):
        """Test that process_files calls auto-commit when enabled."""
        with patch("spec_cli.git.repository.SpecGitRepository"):
            processor = BatchFileProcessor(mock_settings)

            # Mock pipeline to return successful results
            mock_file_result = Mock()
            mock_file_result.success = True
            mock_file_result.errors = []
            mock_file_result.warnings = []

            processor.pipeline.process_file.return_value = mock_file_result
            processor.change_detector.get_files_needing_processing.return_value = [
                Path("test.py")
            ]

            # Mock _handle_auto_commit to verify it's called
            with patch.object(processor, "_handle_auto_commit") as mock_auto_commit:
                options = BatchProcessingOptions(auto_commit=True)
                processor.process_files([Path("test.py")], options)

                # Verify auto-commit was called
                mock_auto_commit.assert_called_once()

    def test_process_files_when_auto_commit_disabled_then_skips_auto_commit(
        self, mock_settings, mock_processor_components
    ):
        """Test that process_files skips auto-commit when disabled."""
        processor = BatchFileProcessor(mock_settings)

        # Mock pipeline to return successful results
        mock_file_result = Mock()
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []

        processor.pipeline.process_file.return_value = mock_file_result
        processor.change_detector.get_files_needing_processing.return_value = [
            Path("test.py")
        ]

        # Mock _handle_auto_commit to verify it's not called
        with patch.object(processor, "_handle_auto_commit") as mock_auto_commit:
            options = BatchProcessingOptions(auto_commit=False)
            processor.process_files([Path("test.py")], options)

            # Verify auto-commit was not called
            mock_auto_commit.assert_not_called()


class TestBatchProcessorIntegration:
    """Integration tests for BatchProcessor without workflow orchestrator."""

    @pytest.fixture
    def processor_with_mocks(self):
        """Create processor with minimal mocking for integration tests."""
        with (
            patch(
                "spec_cli.file_processing.batch_processor.FileChangeDetector"
            ) as mock_detector,
            patch("spec_cli.file_processing.batch_processor.ConflictResolver"),
            patch(
                "spec_cli.file_processing.batch_processor.FileProcessingPipeline"
            ) as mock_pipeline,
            patch("spec_cli.templates.generator.SpecContentGenerator"),
        ):
            # Configure mocks for successful processing
            mock_detector.return_value.get_files_needing_processing.return_value = [
                Path("test.py")
            ]

            mock_file_result = Mock()
            mock_file_result.success = True
            mock_file_result.errors = []
            mock_file_result.warnings = []

            mock_pipeline.return_value.process_file.return_value = mock_file_result

            processor = BatchFileProcessor()
            yield processor

    def test_batch_processing_when_auto_commit_true_then_creates_commits_without_orchestrator(
        self, processor_with_mocks
    ):
        """Integration test: verify auto_commit works without workflow orchestrator."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.add_files.return_value = None
            mock_repo.commit.return_value = "abc123"

            options = BatchProcessingOptions(auto_commit=True)
            result = processor_with_mocks.process_files([Path("test.py")], options)

            # Verify processing succeeded
            assert result.success is True
            assert len(result.successful_files) == 1
            assert result.workflow_id is not None

            # Verify git operations were performed
            mock_repo.add_files.assert_called_once()
            mock_repo.commit.assert_called_once()

    def test_batch_processing_when_multiple_files_then_processes_consistently(
        self, processor_with_mocks
    ):
        """Integration test: verify consistent behavior with multiple files."""
        test_files = [Path("test1.py"), Path("test2.py"), Path("test3.py")]

        # Configure detector to return all files
        processor_with_mocks.change_detector.get_files_needing_processing.return_value = test_files

        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.add_files.return_value = None
            mock_repo.commit.return_value = "abc123"

            options = BatchProcessingOptions(auto_commit=True)
            result = processor_with_mocks.process_files(test_files, options)

            # Verify all files were processed
            assert result.success is True
            assert len(result.successful_files) == 3
            assert result.total_files == 3

            # Verify commit message reflects file count
            commit_calls = mock_repo.commit.call_args_list
            assert len(commit_calls) == 1
            commit_message = commit_calls[0][0][0]
            assert "Process 3 spec files" in commit_message
