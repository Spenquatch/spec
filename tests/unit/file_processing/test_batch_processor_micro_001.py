"""Unit tests for BatchFileProcessor - Micro-Agent Implementation.

This module provides comprehensive unit tests for the batch file processing functionality,
including BatchFileProcessor, BatchProcessingOptions, and BatchProcessingResult classes.
Tests cover all major functionality with comprehensive error handling, edge cases,
and performance validation.
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
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
    """Unit tests for BatchProcessingOptions class."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values."""
        options = BatchProcessingOptions()

        assert options.max_files is None
        assert options.max_parallel == 1
        assert options.force_regenerate is False
        assert options.skip_unchanged is True
        assert options.conflict_strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT
        assert options.create_backups is True
        assert options.auto_commit is False
        assert options.custom_variables == {}

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        custom_vars = {"test": "value"}
        options = BatchProcessingOptions(
            max_files=100,
            max_parallel=4,
            force_regenerate=True,
            skip_unchanged=False,
            conflict_strategy=ConflictResolutionStrategy.OVERWRITE,
            create_backups=False,
            auto_commit=True,
            custom_variables=custom_vars,
        )

        assert options.max_files == 100
        assert options.max_parallel == 4
        assert options.force_regenerate is True
        assert options.skip_unchanged is False
        assert options.conflict_strategy == ConflictResolutionStrategy.OVERWRITE
        assert options.create_backups is False
        assert options.auto_commit is True
        assert options.custom_variables == custom_vars

    def test_init_with_none_custom_variables(self) -> None:
        """Test initialization when custom_variables is None."""
        options = BatchProcessingOptions(custom_variables=None)
        assert options.custom_variables == {}

    def test_init_with_none_conflict_strategy(self) -> None:
        """Test initialization when conflict_strategy is None."""
        options = BatchProcessingOptions(conflict_strategy=None)
        assert options.conflict_strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT


class TestBatchProcessingResult:
    """Unit tests for BatchProcessingResult class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        result = BatchProcessingResult()

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

    def test_duration_property_with_times(self) -> None:
        """Test duration property when start and end times are set."""
        result = BatchProcessingResult()
        result.start_time = 100.0
        result.end_time = 105.5

        assert result.duration == 5.5

    def test_duration_property_without_times(self) -> None:
        """Test duration property when times are not set."""
        result = BatchProcessingResult()
        assert result.duration is None

    def test_duration_property_partial_times(self) -> None:
        """Test duration property when only one time is set."""
        result = BatchProcessingResult()
        result.start_time = 100.0
        assert result.duration is None

        result.start_time = None
        result.end_time = 105.0
        assert result.duration is None

    def test_to_dict_complete_result(self) -> None:
        """Test to_dict conversion with complete result data."""
        result = BatchProcessingResult()
        result.success = True
        result.total_files = 5
        result.successful_files = [Path("file1.py"), Path("file2.py")]
        result.failed_files = [Path("file3.py")]
        result.skipped_files = [Path("file4.py")]
        result.errors = ["Error 1", "Error 2"]
        result.warnings = ["Warning 1"]
        result.start_time = 100.0
        result.end_time = 105.0
        result.workflow_id = "test-workflow-123"

        expected = {
            "success": True,
            "total_files": 5,
            "successful_count": 2,
            "failed_count": 1,
            "skipped_count": 1,
            "successful_files": ["file1.py", "file2.py"],
            "failed_files": ["file3.py"],
            "skipped_files": ["file4.py"],
            "errors": ["Error 1", "Error 2"],
            "warnings": ["Warning 1"],
            "duration": 5.0,
            "workflow_id": "test-workflow-123",
        }

        assert result.to_dict() == expected

    def test_to_dict_empty_result(self) -> None:
        """Test to_dict conversion with empty result."""
        result = BatchProcessingResult()

        expected = {
            "success": False,
            "total_files": 0,
            "successful_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "successful_files": [],
            "failed_files": [],
            "skipped_files": [],
            "errors": [],
            "warnings": [],
            "duration": None,
            "workflow_id": None,
        }

        assert result.to_dict() == expected


class TestBatchFileProcessor:
    """Unit tests for BatchFileProcessor class."""

    @pytest.fixture
    def mock_settings(self) -> Mock:
        """Mock SpecSettings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.ai_config = Mock()
        settings.ai_config.model = "test-model"
        # Add required attributes for initialization
        settings.spec_dir = Path(".spec")
        settings.ignore_file = Path(".specignore")
        settings.template_file = Path(".spectemplate")
        settings.specs_dir = Path(".specs")
        settings.root_path = Path(".")
        return settings

    @pytest.fixture
    def mock_dependencies(self) -> Any:
        """Mock all major dependencies for BatchFileProcessor."""
        with (
            patch(
                "spec_cli.file_processing.batch_processor.FileChangeDetector"
            ) as mock_change_detector,
            patch(
                "spec_cli.file_processing.batch_processor.ConflictResolver"
            ) as mock_conflict_resolver,
            patch(
                "spec_cli.file_processing.batch_processor.progress_reporter"
            ) as mock_progress_reporter,
            patch(
                "spec_cli.file_processing.batch_processor.BatchResultAggregator"
            ) as mock_result_aggregator,
            patch(
                "spec_cli.file_processing.batch_processor.FileProcessingPipeline"
            ) as mock_pipeline,
            patch(
                "spec_cli.templates.generator.SpecContentGenerator"
            ) as mock_content_generator,
            patch(
                "spec_cli.file_processing.batch_processor.debug_logger"
            ) as mock_debug_logger,
            patch(
                "spec_cli.file_processing.batch_processor.BatchProgressTracker"
            ) as mock_progress_tracker,
        ):
            yield {
                "change_detector": mock_change_detector,
                "conflict_resolver": mock_conflict_resolver,
                "progress_reporter": mock_progress_reporter,
                "result_aggregator": mock_result_aggregator,
                "pipeline": mock_pipeline,
                "content_generator": mock_content_generator,
                "debug_logger": mock_debug_logger,
                "progress_tracker": mock_progress_tracker,
            }

    def test_init_with_settings(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test initialization with provided settings."""
        processor = BatchFileProcessor(mock_settings)

        assert processor.settings == mock_settings
        assert isinstance(processor.change_detector, Mock)
        assert isinstance(processor.conflict_resolver, Mock)
        assert isinstance(processor.pipeline, Mock)
        mock_dependencies["debug_logger"].log.assert_called_with(
            "INFO", "BatchFileProcessor initialized"
        )

    def test_init_without_settings(self) -> None:
        """Test initialization without settings raises ValueError."""
        with pytest.raises(ValueError, match="BatchFileProcessor requires a settings instance"):
            BatchFileProcessor(None)

    def test_process_files_empty_list(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing empty file list."""
        processor = BatchFileProcessor(mock_settings)

        result = processor.process_files([])

        assert isinstance(result, BatchProcessingResult)
        assert result.total_files == 0
        assert result.successful_files == []
        assert result.failed_files == []
        assert result.skipped_files == []

    def test_process_files_with_max_files_limit(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing with max_files limitation."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path(f"file{i}.py") for i in range(10)]
        options = BatchProcessingOptions(max_files=5)

        # Mock change detector to return all files
        mock_change_detector_instance = mock_dependencies[
            "change_detector"
        ].return_value
        mock_change_detector_instance.get_files_needing_processing.return_value = (
            file_paths[:5]
        )

        # Mock pipeline processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        result = processor.process_files(file_paths, options)

        assert result.total_files == 5
        assert len(result.warnings) > 0
        assert "Limited to 5 files" in result.warnings[0]

    def test_process_files_skip_unchanged(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing with skip_unchanged option."""
        processor = BatchFileProcessor(mock_settings)

        all_files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        files_needing_processing = [Path("file1.py"), Path("file3.py")]

        options = BatchProcessingOptions(skip_unchanged=True, force_regenerate=False)

        # Mock change detector
        mock_change_detector_instance = mock_dependencies[
            "change_detector"
        ].return_value
        mock_change_detector_instance.get_files_needing_processing.return_value = (
            files_needing_processing
        )

        # Mock pipeline processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        result = processor.process_files(all_files, options)

        assert result.total_files == 3
        assert len(result.skipped_files) == 1
        assert Path("file2.py") in result.skipped_files
        assert len(result.successful_files) == 2

    def test_process_files_force_regenerate(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing with force_regenerate option."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py"), Path("file2.py")]
        options = BatchProcessingOptions(force_regenerate=True)

        # Mock pipeline processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        result = processor.process_files(file_paths, options)

        # Should not call change detector when force_regenerate is True
        mock_change_detector_instance = mock_dependencies[
            "change_detector"
        ].return_value
        mock_change_detector_instance.get_files_needing_processing.assert_not_called()

        assert result.total_files == 2
        assert len(result.skipped_files) == 0

    def test_process_files_with_file_processing_failure(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing when file processing fails."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py"), Path("file2.py")]
        options = BatchProcessingOptions(force_regenerate=True)  # Skip change detection

        # Mock pipeline processing - one success, one failure
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        success_result = Mock(spec=FileProcessingResult)
        success_result.success = True
        success_result.errors = []
        success_result.warnings = []

        failure_result = Mock(spec=FileProcessingResult)
        failure_result.success = False
        failure_result.errors = ["Processing error"]
        failure_result.warnings = []

        mock_pipeline_instance.process_file.side_effect = [
            success_result,
            failure_result,
        ]

        result = processor.process_files(file_paths, options)

        assert result.total_files == 2
        assert len(result.successful_files) == 1
        assert len(result.failed_files) == 1
        assert len(result.errors) == 1
        assert "Processing error" in result.errors

    def test_process_files_with_exception_during_processing(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing when an exception occurs during file processing."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py")]
        options = BatchProcessingOptions(force_regenerate=True)  # Skip change detection

        # Mock pipeline to raise exception
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_pipeline_instance.process_file.side_effect = RuntimeError(
            "Unexpected error"
        )

        result = processor.process_files(file_paths, options)

        assert result.total_files == 1
        assert len(result.failed_files) == 1
        assert len(result.errors) == 1
        assert "Unexpected error processing" in result.errors[0]

    def test_process_files_with_os_error_during_processing(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing when an OS error occurs during file processing."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py")]
        options = BatchProcessingOptions(force_regenerate=True)  # Skip change detection

        # Mock pipeline to raise OSError
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        os_error = OSError("Permission denied")
        mock_pipeline_instance.process_file.side_effect = os_error

        # Mock error handling utilities
        with (
            patch(
                "spec_cli.file_processing.batch_processor.handle_os_error"
            ) as mock_handle_os_error,
            patch(
                "spec_cli.file_processing.batch_processor.create_error_context"
            ) as mock_create_error_context,
        ):
            mock_handle_os_error.return_value = "Formatted OS error"
            mock_create_error_context.return_value = {"context": "data"}

            result = processor.process_files(file_paths, options)

            assert result.total_files == 1
            assert len(result.failed_files) == 1
            assert len(result.errors) == 1
            assert "File processing failed: Formatted OS error" in result.errors[0]

            mock_handle_os_error.assert_called_once_with(os_error)
            mock_create_error_context.assert_called_once_with(file_paths[0])

    @patch("spec_cli.git.repository.SpecGitRepository")
    def test_process_files_with_auto_commit_success(
        self, mock_git_repo: Mock, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing with successful auto-commit."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py")]
        options = BatchProcessingOptions(auto_commit=True, force_regenerate=True)

        # Mock successful file processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        # Mock git repository operations
        mock_repo_instance = mock_git_repo.return_value
        mock_repo_instance.add_files.return_value = None
        mock_repo_instance.commit.return_value = None

        # Mock result aggregator
        mock_aggregator_instance = mock_dependencies["result_aggregator"].return_value
        mock_aggregator_instance.create_workflow_summary.return_value = {
            "workflow_id": "test-workflow-123"
        }

        result = processor.process_files(file_paths, options)

        assert result.success is True
        assert len(result.successful_files) == 1
        assert result.workflow_id == "test-workflow-123"

        mock_repo_instance.add_files.assert_called_once()
        mock_repo_instance.commit.assert_called_once()

    @patch("spec_cli.git.repository.SpecGitRepository")
    def test_process_files_with_auto_commit_failure(
        self, mock_git_repo: Mock, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing when auto-commit fails."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py")]
        options = BatchProcessingOptions(auto_commit=True, force_regenerate=True)

        # Mock successful file processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        # Mock git repository to fail
        mock_repo_instance = mock_git_repo.return_value
        mock_repo_instance.add_files.side_effect = RuntimeError("Git error")

        result = processor.process_files(file_paths, options)

        assert result.success is True  # File processing still succeeded
        assert len(result.warnings) == 1
        assert "Auto-commit failed" in result.warnings[0]

    def test_process_files_progress_callback(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing with progress callback."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py"), Path("file2.py")]
        options = BatchProcessingOptions(force_regenerate=True)  # Skip change detection
        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        # Mock successful file processing
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_file_result = Mock(spec=FileProcessingResult)
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []
        mock_pipeline_instance.process_file.return_value = mock_file_result

        result = processor.process_files(
            file_paths, options, progress_callback=progress_callback
        )

        assert result.success is True
        assert len(progress_calls) >= 1  # At least final completion call
        assert progress_calls[-1] == (2, 2, "Completed")

    def test_estimate_batch_processing(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test batch processing estimation."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py"), Path("file2.py")]
        expected_estimate = {"estimated_time": 60, "complexity": "medium"}

        # Mock pipeline estimation
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_pipeline_instance.get_processing_estimate.return_value = expected_estimate

        result = processor.estimate_batch_processing(file_paths)

        assert result == expected_estimate
        mock_pipeline_instance.get_processing_estimate.assert_called_once_with(
            file_paths
        )

    def test_validate_batch_processing_empty_files(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test validation with empty file list."""
        processor = BatchFileProcessor(mock_settings)

        issues = processor.validate_batch_processing([])

        assert len(issues) == 1
        assert "No files provided for processing" in issues[0]

    def test_validate_batch_processing_valid_files(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test validation with valid files."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py"), Path("file2.py")]

        # Mock pipeline validation
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_pipeline_instance.validate_file_for_processing.return_value = []

        issues = processor.validate_batch_processing(file_paths)

        assert len(issues) == 0
        assert mock_pipeline_instance.validate_file_for_processing.call_count == 2

    def test_validate_batch_processing_invalid_conflict_strategy(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test validation with invalid conflict strategy."""
        processor = BatchFileProcessor(mock_settings)

        file_paths = [Path("file1.py")]

        # Create a mock conflict strategy that will raise ValueError
        invalid_strategy = Mock()
        invalid_strategy.value = "INVALID_STRATEGY"

        options = BatchProcessingOptions(conflict_strategy=invalid_strategy)

        # Mock pipeline validation
        mock_pipeline_instance = mock_dependencies["pipeline"].return_value
        mock_pipeline_instance.validate_file_for_processing.return_value = []

        # Mock ConflictResolutionStrategy to raise ValueError
        with patch(
            "spec_cli.file_processing.batch_processor.ConflictResolutionStrategy"
        ) as mock_strategy:
            mock_strategy.side_effect = ValueError("Invalid strategy")

            issues = processor.validate_batch_processing(file_paths, options)

            assert len(issues) == 1
            assert "Invalid conflict strategy" in issues[0]

    def test_get_processing_summary(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing summary generation."""
        processor = BatchFileProcessor(mock_settings)

        # Create a result with test data
        result = BatchProcessingResult()
        result.total_files = 5
        result.successful_files = [Path("file1.py"), Path("file2.py")]
        result.failed_files = [Path("file3.py")]
        result.skipped_files = [Path("file4.py")]
        result.errors = ["Error 1", "Error 2"]
        result.warnings = ["Warning 1"]
        result.start_time = 100.0
        result.end_time = 105.0

        # Mock aggregator
        mock_aggregator_instance = mock_dependencies["result_aggregator"].return_value
        mock_aggregated: dict[str, Any] = {
            "summary": {
                "overview": {"some": "data"},
                "errors": {"other": "data"},
                "performance": {"metrics": "data"},
            }
        }
        mock_aggregator_instance.aggregate_results.return_value = mock_aggregated

        summary = processor.get_processing_summary(result)

        # Check that batch-specific data overrides aggregated data
        assert summary["overview"]["total_files"] == 5
        assert summary["overview"]["successful"] == 2
        assert summary["overview"]["failed"] == 1
        assert summary["overview"]["skipped"] == 1
        assert summary["overview"]["success_rate"] == 40.0  # 2/5 * 100
        assert summary["overview"]["duration"] == 5.0
        assert summary["errors"]["total_errors"] == 2
        assert summary["warnings"]["total_warnings"] == 1

    def test_get_processing_summary_zero_files(
        self, mock_settings: Mock, mock_dependencies: Any
    ) -> None:
        """Test processing summary with zero total files."""
        processor = BatchFileProcessor(mock_settings)

        result = BatchProcessingResult()
        result.total_files = 0

        # Mock aggregator
        mock_aggregator_instance = mock_dependencies["result_aggregator"].return_value
        mock_aggregated = {"summary": {"overview": {}, "errors": {}}}
        mock_aggregator_instance.aggregate_results.return_value = mock_aggregated

        summary = processor.get_processing_summary(result)

        assert summary["overview"]["success_rate"] == 0


class TestConvenienceFunctions:
    """Unit tests for convenience functions."""

    @patch("spec_cli.file_processing.batch_processor.BatchFileProcessor")
    def test_process_files_batch(self, mock_processor_class) -> None:
        """Test process_files_batch convenience function."""
        # Mock processor instance
        mock_processor = Mock()
        mock_result = Mock(spec=BatchProcessingResult)
        mock_processor.process_files.return_value = mock_result
        mock_processor_class.return_value = mock_processor

        file_paths = [Path("file1.py")]
        settings = Mock(spec=SpecSettings)
        kwargs = {"max_files": 10, "force_regenerate": True}

        result = process_files_batch(file_paths, settings, **kwargs)

        assert result == mock_result
        mock_processor_class.assert_called_once_with(settings)

        # Verify BatchProcessingOptions was created with kwargs
        args, _ = mock_processor.process_files.call_args
        assert args[0] == file_paths
        assert isinstance(args[1], BatchProcessingOptions)
        assert args[1].max_files == 10
        assert args[1].force_regenerate is True

    @patch("spec_cli.file_processing.batch_processor.BatchFileProcessor")
    def test_estimate_processing_time(self, mock_processor_class) -> None:
        """Test estimate_processing_time convenience function."""
        # Mock processor instance
        mock_processor = Mock()
        expected_estimate = {"estimated_time": 120}
        mock_processor.estimate_batch_processing.return_value = expected_estimate
        mock_processor_class.return_value = mock_processor

        file_paths = [Path("file1.py")]
        settings = Mock(spec=SpecSettings)

        result = estimate_processing_time(file_paths, settings)

        assert result == expected_estimate
        mock_processor_class.assert_called_once_with(settings)
        mock_processor.estimate_batch_processing.assert_called_once_with(file_paths)


class TestBatchProcessorIntegration:
    """Integration tests for BatchFileProcessor with real dependencies."""

    @pytest.fixture
    def real_settings(self) -> SpecSettings:
        """Create real settings for integration testing."""
        return SpecSettings()

    def test_processor_initialization_integration(
        self, real_settings: SpecSettings
    ) -> None:
        """Test that processor can be initialized with real dependencies."""
        with patch("spec_cli.templates.generator.SpecContentGenerator"):
            processor = BatchFileProcessor(real_settings)

            assert processor.settings == real_settings
            assert hasattr(processor, "change_detector")
            assert hasattr(processor, "conflict_resolver")
            assert hasattr(processor, "pipeline")
            assert hasattr(processor, "progress_reporter")
            assert hasattr(processor, "result_aggregator")


class TestBatchProcessorErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.fixture
    def mock_settings(self) -> Mock:
        """Mock SpecSettings for testing."""
        settings = Mock(spec=SpecSettings)
        # Add required attributes for initialization
        settings.spec_dir = Path(".spec")
        settings.ignore_file = Path(".specignore")
        settings.template_file = Path(".spectemplate")
        settings.specs_dir = Path(".specs")
        settings.root_path = Path(".")
        return settings

    def test_process_files_with_batch_level_exception(
        self, mock_settings: Mock
    ) -> None:
        """Test handling of exceptions at the batch level."""
        with (
            patch(
                "spec_cli.file_processing.batch_processor.FileChangeDetector"
            ) as mock_change_detector,
            patch("spec_cli.file_processing.batch_processor.debug_logger"),
        ):
            # Make initialization fail with exception
            mock_change_detector.side_effect = RuntimeError("Initialization failed")

            processor = BatchFileProcessor.__new__(BatchFileProcessor)
            processor.settings = mock_settings

            # This should handle the exception gracefully
            with pytest.raises(RuntimeError):
                BatchFileProcessor(mock_settings)

    def test_process_files_timing_accuracy(self, mock_settings: Mock) -> None:
        """Test that timing measurements are accurate."""
        with (
            patch("spec_cli.file_processing.batch_processor.FileChangeDetector"),
            patch("spec_cli.file_processing.batch_processor.ConflictResolver"),
            patch("spec_cli.file_processing.batch_processor.progress_reporter"),
            patch("spec_cli.file_processing.batch_processor.BatchResultAggregator"),
            patch(
                "spec_cli.file_processing.batch_processor.FileProcessingPipeline"
            ) as mock_pipeline,
            patch("spec_cli.templates.generator.SpecContentGenerator"),
            patch("spec_cli.file_processing.batch_processor.time.time") as mock_time,
        ):
            # Mock time progression - need more values for all time.time() calls
            mock_time.side_effect = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

            processor = BatchFileProcessor(mock_settings)

            # Mock successful processing
            mock_pipeline_instance = mock_pipeline.return_value
            mock_file_result = Mock(spec=FileProcessingResult)
            mock_file_result.success = True
            mock_file_result.errors = []
            mock_file_result.warnings = []
            mock_pipeline_instance.process_file.return_value = mock_file_result

            result = processor.process_files([Path("file1.py")])

            assert result.start_time == 100.0
            assert result.end_time is not None
            assert result.duration is not None
