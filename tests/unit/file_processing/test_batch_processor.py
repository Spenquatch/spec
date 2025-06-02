"""Tests for batch processing functionality."""
# mypy: disable-error-code=attr-defined

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.file_processing.batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
    BatchProcessingResult,
    estimate_processing_time,
    process_files_batch,
)
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy
from spec_cli.file_processing.processing_pipeline import FileProcessingResult


class TestBatchProcessingOptions:
    """Test BatchProcessingOptions class."""

    def test_batch_processing_options_defaults(self) -> None:
        """Test default values for batch processing options."""
        options = BatchProcessingOptions()

        assert options.max_files is None
        assert options.max_parallel == 1
        assert options.force_regenerate is False
        assert options.skip_unchanged is True
        assert options.conflict_strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT
        assert options.create_backups is True
        assert options.auto_commit is False
        assert options.custom_variables == {}

    def test_batch_processing_options_custom_values(self) -> None:
        """Test custom values for batch processing options."""
        custom_variables = {"author": "test", "version": "1.0"}

        options = BatchProcessingOptions(
            max_files=50,
            max_parallel=3,
            force_regenerate=True,
            skip_unchanged=False,
            conflict_strategy=ConflictResolutionStrategy.KEEP_THEIRS,
            create_backups=False,
            auto_commit=True,
            custom_variables=custom_variables,
        )

        assert options.max_files == 50
        assert options.max_parallel == 3
        assert options.force_regenerate is True
        assert options.skip_unchanged is False
        assert options.conflict_strategy == ConflictResolutionStrategy.KEEP_THEIRS
        assert options.create_backups is False
        assert options.auto_commit is True
        assert options.custom_variables == custom_variables


class TestBatchProcessingResult:
    """Test BatchProcessingResult class."""

    def test_batch_processing_result_initialization(self) -> None:
        """Test BatchProcessingResult initialization."""
        result = BatchProcessingResult()

        # Default values
        assert result.success is False
        assert result.total_files == 0
        assert result.successful_files == []
        assert result.failed_files == []
        assert result.skipped_files == []
        assert result.file_results == {}
        assert result.errors == []
        assert result.warnings == []
        assert result.start_time is None
        assert result.end_time is None
        assert result.workflow_id is None

        # Duration calculation
        assert result.duration is None

    def test_batch_processing_result_duration_calculation(self) -> None:
        """Test duration calculation."""
        result = BatchProcessingResult()

        # Set times
        result.start_time = 1000.0
        result.end_time = 1005.5

        assert result.duration == 5.5

    def test_batch_processing_result_serialization(self) -> None:
        """Test BatchProcessingResult serialization."""
        result = BatchProcessingResult()
        result.success = True
        result.total_files = 10
        result.successful_files = [Path("file1.py"), Path("file2.py")]
        result.failed_files = [Path("file3.py")]
        result.skipped_files = [Path("file4.py")]
        result.errors = ["error1"]
        result.warnings = ["warning1"]
        result.start_time = 1000.0
        result.end_time = 1005.0
        result.workflow_id = "workflow123"

        result_dict = result.to_dict()
        expected_keys = {
            "success",
            "total_files",
            "successful_count",
            "failed_count",
            "skipped_count",
            "successful_files",
            "failed_files",
            "skipped_files",
            "errors",
            "warnings",
            "duration",
            "workflow_id",
        }

        assert set(result_dict.keys()) == expected_keys
        assert result_dict["success"] is True
        assert result_dict["total_files"] == 10
        assert result_dict["successful_count"] == 2
        assert result_dict["failed_count"] == 1
        assert result_dict["skipped_count"] == 1
        assert result_dict["duration"] == 5.0
        assert result_dict["workflow_id"] == "workflow123"


class TestBatchFileProcessor:
    """Test BatchFileProcessor class."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        return settings

    @pytest.fixture
    def mock_processor(self, mock_settings: MagicMock) -> BatchFileProcessor:
        """Create BatchFileProcessor with mocked dependencies."""
        with patch(
            "spec_cli.file_processing.batch_processor.FileChangeDetector"
        ), patch("spec_cli.file_processing.batch_processor.ConflictResolver"), patch(
            "spec_cli.file_processing.batch_processor.SpecWorkflowOrchestrator"
        ), patch(
            "spec_cli.file_processing.batch_processor.FileProcessingPipeline"
        ), patch("spec_cli.templates.generator.SpecContentGenerator"):
            processor = BatchFileProcessor(mock_settings)
            processor.change_detector = MagicMock()
            processor.conflict_resolver = MagicMock()
            processor.workflow_orchestrator = MagicMock()
            processor.pipeline = MagicMock()
            processor.progress_reporter = MagicMock()
            return processor

    def test_batch_processor_sequential_processing(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test sequential processing of files."""
        file_paths = [Path(f"file{i}.py") for i in range(3)]
        options = BatchProcessingOptions()

        # Mock change detector
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths
        )

        # Mock successful file processing
        def mock_process_file(file_path: Path, **kwargs: Any) -> FileProcessingResult:
            return FileProcessingResult(file_path=file_path, success=True)

        mock_processor.pipeline.process_file.side_effect = mock_process_file

        # Process files
        result = mock_processor.process_files(file_paths, options)

        # Verify results
        assert result.success is True
        assert result.total_files == 3
        assert len(result.successful_files) == 3
        assert len(result.failed_files) == 0
        assert len(result.skipped_files) == 0

        # Verify pipeline was called for each file
        assert mock_processor.pipeline.process_file.call_count == 3

    def test_batch_processor_progress_tracking(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test progress tracking during batch processing."""
        file_paths = [Path(f"file{i}.py") for i in range(2)]
        options = BatchProcessingOptions()

        # Mock dependencies
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths
        )
        mock_processor.pipeline.process_file.return_value = FileProcessingResult(
            file_path=file_paths[0], success=True
        )

        # Mock progress callback
        progress_callback = MagicMock()

        # Process files
        _result = mock_processor.process_files(file_paths, options, progress_callback)

        # Verify progress events were emitted
        mock_processor.progress_reporter.emit_batch_started.assert_called_once()
        mock_processor.progress_reporter.emit_batch_completed.assert_called_once()

        # Verify progress callback was called
        assert progress_callback.call_count >= 2  # At least start and end

    def test_batch_processor_conflict_handling(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test handling of conflicts during batch processing."""
        file_paths = [Path("file1.py"), Path("file2.py")]
        options = BatchProcessingOptions(
            conflict_strategy=ConflictResolutionStrategy.KEEP_OURS
        )

        # Mock dependencies
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths
        )

        # Mock processing with conflicts
        def mock_process_file(file_path: Path, **kwargs: Any) -> FileProcessingResult:
            if file_path.name == "file1.py":
                # First file has conflicts
                result = FileProcessingResult(file_path=file_path, success=True)
                result.conflict_info = MagicMock()
                result.conflict_info.conflict_type.value = "content_modified"
                result.resolution_strategy = ConflictResolutionStrategy.KEEP_OURS
                return result
            else:
                # Second file processes normally
                return FileProcessingResult(file_path=file_path, success=True)

        mock_processor.pipeline.process_file.side_effect = mock_process_file

        # Process files
        result = mock_processor.process_files(file_paths, options)

        # Verify results
        assert result.success is True
        assert len(result.successful_files) == 2

        # Verify conflict strategy was passed to pipeline
        pipeline_calls = mock_processor.pipeline.process_file.call_args_list
        for call in pipeline_calls:
            assert call[1]["conflict_strategy"] == ConflictResolutionStrategy.KEEP_OURS

    def test_batch_processor_error_recovery(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test error recovery during batch processing."""
        file_paths = [Path("good.py"), Path("bad.py"), Path("good2.py")]
        options = BatchProcessingOptions()

        # Mock dependencies
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths
        )

        # Mock processing with one failure
        def mock_process_file(file_path: Path, **kwargs: Any) -> FileProcessingResult:
            if file_path.name == "bad.py":
                return FileProcessingResult(
                    file_path=file_path, success=False, errors=["Processing failed"]
                )
            else:
                return FileProcessingResult(file_path=file_path, success=True)

        mock_processor.pipeline.process_file.side_effect = mock_process_file

        # Process files
        result = mock_processor.process_files(file_paths, options)

        # Should continue processing despite one failure
        assert result.success is False  # Overall failure due to errors
        assert len(result.successful_files) == 2
        assert len(result.failed_files) == 1
        assert result.failed_files[0].name == "bad.py"
        assert "Processing failed" in result.errors

    def test_batch_processor_auto_commit_integration(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test auto-commit integration."""
        file_paths = [Path("file1.py"), Path("file2.py")]
        options = BatchProcessingOptions(auto_commit=True)

        # Mock dependencies
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths
        )
        mock_processor.pipeline.process_file.return_value = FileProcessingResult(
            file_path=file_paths[0], success=True
        )

        # Mock workflow orchestrator
        mock_processor.workflow_orchestrator.generate_specs_for_files.return_value = {
            "success": True,
            "workflow_id": "workflow123",
        }

        # Process files
        result = mock_processor.process_files(file_paths, options)

        # Verify auto-commit was attempted
        mock_processor.workflow_orchestrator.generate_specs_for_files.assert_called_once()
        assert result.workflow_id == "workflow123"

    def test_batch_processing_options_configuration(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test various batch processing options."""
        file_paths = [Path(f"file{i}.py") for i in range(10)]

        # Test max_files limitation
        options = BatchProcessingOptions(max_files=3)
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            file_paths[:3]
        )
        mock_processor.pipeline.process_file.return_value = FileProcessingResult(
            file_path=file_paths[0], success=True
        )

        result = mock_processor.process_files(file_paths, options)
        assert result.total_files == 3
        assert len(result.warnings) > 0  # Should warn about limiting files

        # Test force_regenerate
        options = BatchProcessingOptions(force_regenerate=True)
        mock_processor.change_detector.reset_mock()

        result = mock_processor.process_files(file_paths, options)
        # Should not call get_files_needing_processing when force_regenerate=True
        mock_processor.change_detector.get_files_needing_processing.assert_not_called()

    def test_batch_processing_validation(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test batch processing validation."""
        # Test empty file list
        issues = mock_processor.validate_batch_processing([], BatchProcessingOptions())
        assert len(issues) > 0
        assert "No files provided" in issues[0]

        # Test valid configuration
        file_paths = [Path("test.py")]
        options = BatchProcessingOptions(
            conflict_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT
        )

        # Mock pipeline validation
        mock_processor.pipeline.validate_file_for_processing.return_value = []

        issues = mock_processor.validate_batch_processing(file_paths, options)
        assert len(issues) == 0

    def test_batch_processing_estimation(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test batch processing estimation."""
        file_paths = [Path(f"file{i}.py") for i in range(5)]

        # Mock pipeline estimation
        mock_estimate = {
            "total_files": 5,
            "processable_files": 4,
            "files_needing_processing": 3,
            "estimated_duration_seconds": 6,
            "validation_issues": [],
        }
        mock_processor.pipeline.get_processing_estimate.return_value = mock_estimate

        estimate = mock_processor.estimate_batch_processing(file_paths)
        assert estimate == mock_estimate

        mock_processor.pipeline.get_processing_estimate.assert_called_once_with(
            file_paths
        )

    def test_batch_processing_summary_generation(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test processing summary generation."""
        # Create mock result with various outcomes
        result = BatchProcessingResult()
        result.total_files = 5
        result.successful_files = [Path("file1.py"), Path("file2.py")]
        result.failed_files = [Path("file3.py")]
        result.skipped_files = [Path("file4.py"), Path("file5.py")]
        result.errors = ["error1", "error2"]
        result.warnings = ["warning1"]
        result.start_time = 1000.0
        result.end_time = 1010.0

        # Add file results with conflicts
        file_result1 = FileProcessingResult(Path("file1.py"), True)
        file_result1.conflict_info = MagicMock()
        file_result1.conflict_info.conflict_type.value = "content_modified"
        file_result1.resolution_strategy = ConflictResolutionStrategy.MERGE_INTELLIGENT

        file_result2 = FileProcessingResult(Path("file3.py"), False)
        file_result2.errors = ["generation failed"]

        result.file_results = {
            str(Path("file1.py")): file_result1,
            str(Path("file3.py")): file_result2,
        }

        summary = mock_processor.get_processing_summary(result)

        # Verify summary structure
        assert "overview" in summary
        assert "conflicts" in summary
        assert "errors" in summary
        assert "warnings" in summary

        # Verify overview
        overview = summary["overview"]
        assert overview["total_files"] == 5
        assert overview["successful"] == 2
        assert overview["failed"] == 1
        assert overview["skipped"] == 2
        assert overview["success_rate"] == 40.0  # 2/5 * 100
        assert overview["duration"] == 10.0

        # Verify conflicts
        conflicts = summary["conflicts"]
        assert conflicts["files_with_conflicts"] == 1
        assert conflicts["conflict_types"]["content_modified"] == 1
        assert conflicts["resolution_strategies"]["merge_intelligent"] == 1

        # Verify errors
        errors = summary["errors"]
        assert errors["total_errors"] == 2
        assert errors["error_types"]["generation"] == 1

    def test_batch_processor_skip_unchanged_files(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test skipping unchanged files during batch processing."""
        all_files = [Path(f"file{i}.py") for i in range(5)]
        files_needing_processing = all_files[:2]  # Only first 2 need processing

        options = BatchProcessingOptions(skip_unchanged=True)

        # Mock change detector
        mock_processor.change_detector.get_files_needing_processing.return_value = (
            files_needing_processing
        )
        mock_processor.pipeline.process_file.return_value = FileProcessingResult(
            file_path=all_files[0], success=True
        )

        # Process files
        result = mock_processor.process_files(all_files, options)

        # Should have skipped 3 files
        assert len(result.skipped_files) == 3
        assert mock_processor.pipeline.process_file.call_count == 2

    def test_batch_processor_exception_handling(
        self, mock_processor: BatchFileProcessor
    ) -> None:
        """Test handling of unexpected exceptions."""
        file_paths = [Path("file1.py")]

        # Mock pipeline to raise exception
        mock_processor.change_detector.get_files_needing_processing.side_effect = (
            Exception("Unexpected error")
        )

        # Should handle exception gracefully
        result = mock_processor.process_files(file_paths, BatchProcessingOptions())

        assert result.success is False
        assert len(result.errors) > 0
        assert "Batch processing failed" in result.errors[0]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_process_files_batch_function(self) -> None:
        """Test process_files_batch convenience function."""
        file_paths = [Path("test.py")]

        with patch(
            "spec_cli.file_processing.batch_processor.BatchFileProcessor"
        ) as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor_class.return_value = mock_processor

            mock_result = BatchProcessingResult()
            mock_processor.process_files.return_value = mock_result

            # Call convenience function
            _result = process_files_batch(
                file_paths, max_files=10, force_regenerate=True
            )

            # Verify processor was created and called
            mock_processor_class.assert_called_once()
            mock_processor.process_files.assert_called_once()

            # Verify options were created correctly
            call_args = mock_processor.process_files.call_args
            options = call_args[0][1]  # Second argument should be options
            assert options.max_files == 10
            assert options.force_regenerate is True

    def test_estimate_processing_time_function(self) -> None:
        """Test estimate_processing_time convenience function."""
        file_paths = [Path("test.py")]

        with patch(
            "spec_cli.file_processing.batch_processor.BatchFileProcessor"
        ) as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor_class.return_value = mock_processor

            mock_estimate = {"total_files": 1, "estimated_duration_seconds": 2}
            mock_processor.estimate_batch_processing.return_value = mock_estimate

            # Call convenience function
            estimate = estimate_processing_time(file_paths)

            # Verify result
            assert estimate == mock_estimate
            mock_processor.estimate_batch_processing.assert_called_once_with(file_paths)
