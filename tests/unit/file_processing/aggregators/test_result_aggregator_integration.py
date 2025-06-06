"""Integration tests for BatchResultAggregator with multi-file batch processing."""

from pathlib import Path
from unittest.mock import Mock, patch

from spec_cli.file_processing.aggregators.result_aggregator import BatchResultAggregator
from spec_cli.file_processing.batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
)
from spec_cli.file_processing.conflict_resolver import (
    ConflictInfo,
    ConflictResolutionStrategy,
    ConflictType,
)
from spec_cli.file_processing.processing_pipeline import FileProcessingResult


class TestBatchResultAggregatorIntegration:
    """Integration tests for BatchResultAggregator with real batch processing scenarios."""

    @patch("spec_cli.file_processing.batch_processor.FileProcessingPipeline")
    @patch("spec_cli.file_processing.batch_processor.FileChangeDetector")
    @patch("spec_cli.file_processing.batch_processor.ConflictResolver")
    def test_integration_multi_file_batch_processing_with_aggregator(
        self, mock_conflict_resolver, mock_change_detector, mock_pipeline
    ):
        """Test integration of aggregator with multi-file batch processing."""
        # Setup mocks
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance

        # Create varied file processing results
        successful_result = FileProcessingResult(Path("success.py"), True)

        conflict_info = ConflictInfo(
            ConflictType.CONTENT_MODIFIED,
            Path("conflict.py"),
            "old content",
            "new content",
        )
        conflict_result = FileProcessingResult(
            Path("conflict.py"),
            True,
            conflict_info=conflict_info,
            resolution_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT,
        )

        permission_error_result = FileProcessingResult(
            Path("permission_error.py"),
            False,
            errors=["Permission denied: access forbidden"],
        )

        generation_error_result = FileProcessingResult(
            Path("generation_error.py"),
            False,
            errors=["Generation template failed", "Generation syntax error"],
        )

        # Configure pipeline to return these results (excluding skipped for processor test)
        file_results = [
            successful_result,
            conflict_result,
            permission_error_result,
            generation_error_result,
        ]
        mock_pipeline_instance.process_file.side_effect = file_results

        # Create processor and test files
        processor = BatchFileProcessor()
        test_files = [
            Path("success.py"),
            Path("conflict.py"),
            Path("permission_error.py"),
            Path("generation_error.py"),
        ]

        # Process files
        options = BatchProcessingOptions(force_regenerate=True)
        batch_result = processor.process_files(test_files, options)

        # Verify batch processing completed
        assert batch_result.total_files == 4
        assert len(batch_result.successful_files) == 2  # success.py and conflict.py
        assert len(batch_result.failed_files) == 2  # permission and generation errors
        assert len(batch_result.skipped_files) == 0  # no skipped files in this test

        # Get processing summary which should use aggregator
        summary = processor.get_processing_summary(batch_result)

        # Verify aggregated summary structure
        assert "overview" in summary
        assert "conflicts" in summary
        assert "errors" in summary
        assert "warnings" in summary

        # Verify overview matches batch results
        overview = summary["overview"]
        assert overview["total_files"] == 4
        assert overview["successful"] == 2
        assert overview["failed"] == 2
        assert overview["skipped"] == 0
        assert overview["success_rate"] == 50.0  # 2/4 * 100

        # Verify conflict analysis from aggregator
        conflicts = summary["conflicts"]
        assert conflicts["files_with_conflicts"] == 1
        assert conflicts["conflict_types"]["content_modified"] == 1
        assert conflicts["resolution_strategies"]["merge_intelligent"] == 1

        # Verify error classification from aggregator
        errors = summary["errors"]
        assert errors["error_types"]["permission"] == 1
        assert errors["error_types"]["generation"] == 2  # Two generation errors

    def test_integration_aggregator_workflow_summary_creation(self):
        """Test integration of aggregator workflow summary creation."""
        aggregator = BatchResultAggregator()

        # Create test files that were successfully processed
        successful_files = [
            Path("src/module1.py"),
            Path("src/module2.py"),
            Path("tests/test_module.py"),
        ]

        workflow_id = "integration-test-123"

        # Create workflow summary
        workflow_summary = aggregator.create_workflow_summary(
            successful_files, workflow_id
        )

        # Verify workflow summary structure
        assert workflow_summary["success"] is True
        assert workflow_summary["total_files"] == 3
        assert workflow_summary["workflow_id"] == workflow_id
        assert len(workflow_summary["successful_files"]) == 3
        assert len(workflow_summary["failed_files"]) == 0

        # Verify file paths are properly normalized
        for file_path in workflow_summary["successful_files"]:
            assert "/" in file_path  # Should use forward slashes
            assert "\\" not in file_path  # Should not have backslashes

    def test_integration_aggregator_handles_empty_batch_gracefully(self):
        """Test that aggregator handles empty batch processing gracefully."""
        aggregator = BatchResultAggregator()

        # Test with empty file results
        summary = aggregator.aggregate_results({})

        # Verify empty summary structure
        assert summary["summary"]["overview"]["total_files"] == 0
        assert summary["summary"]["overview"]["successful"] == 0
        assert summary["summary"]["overview"]["failed"] == 0
        assert summary["summary"]["overview"]["skipped"] == 0

        assert summary["summary"]["conflicts"]["files_with_conflicts"] == 0
        assert summary["summary"]["conflicts"]["conflict_types"] == {}
        assert summary["summary"]["conflicts"]["resolution_strategies"] == {}

        assert summary["summary"]["errors"]["total_errors"] == 0
        assert summary["summary"]["errors"]["error_types"] == {}

        assert summary["statistics"]["success_rate"] == 0.0
        assert summary["statistics"]["failure_rate"] == 0.0
        assert summary["statistics"]["skip_rate"] == 0.0

    def test_integration_aggregator_with_complex_error_patterns(self):
        """Test aggregator with complex error patterns and edge cases."""
        aggregator = BatchResultAggregator()

        # Create files with multiple error types
        file_results = {
            "multi_error.py": FileProcessingResult(
                Path("multi_error.py"),
                False,
                errors=[
                    "Permission denied access",
                    "Conflict resolution failed during merge",
                    "Generation template syntax error",
                    "Unknown system failure",
                ],
            ),
            "permission_only.py": FileProcessingResult(
                Path("permission_only.py"),
                False,
                errors=["Permission error: file locked"],
            ),
        }

        # Aggregate results
        summary = aggregator.aggregate_results(file_results)

        # Verify error classification handles multiple errors per file
        errors = summary["summary"]["errors"]
        assert (
            errors["total_errors"] == 5
        )  # 4 from multi_error + 1 from permission_only
        assert (
            errors["error_types"]["permission"] == 2
        )  # 1 from multi_error + 1 from permission_only
        assert errors["error_types"]["conflict"] == 1  # 1 from multi_error
        assert errors["error_types"]["generation"] == 1  # 1 from multi_error
        assert errors["error_types"]["other"] == 1  # 1 from multi_error

        # Verify statistics
        stats = summary["statistics"]
        assert stats["success_rate"] == 0.0
        assert stats["failure_rate"] == 100.0
        assert stats["skip_rate"] == 0.0

    def test_integration_aggregator_statistics_calculation_accuracy(self):
        """Test that aggregator calculates statistics accurately for various scenarios."""
        aggregator = BatchResultAggregator()

        # Create a large dataset with known ratios
        file_results = {}

        # 60% successful (60 files)
        for i in range(60):
            file_results[f"success_{i}.py"] = FileProcessingResult(
                Path(f"success_{i}.py"), True
            )

        # 25% failed (25 files)
        for i in range(25):
            file_results[f"failed_{i}.py"] = FileProcessingResult(
                Path(f"failed_{i}.py"), False, errors=["Processing failed"]
            )

        # 15% skipped (15 files)
        for i in range(15):
            file_results[f"skipped_{i}.py"] = FileProcessingResult(
                Path(f"skipped_{i}.py"), False, metadata={"skipped": True}
            )

        # Total: 100 files
        summary = aggregator.aggregate_results(file_results)

        # Verify statistics are calculated correctly
        stats = summary["statistics"]
        assert stats["success_rate"] == 60.0
        assert stats["failure_rate"] == 25.0
        assert stats["skip_rate"] == 15.0

        # Verify overview counts
        overview = summary["summary"]["overview"]
        assert overview["total_files"] == 100
        assert overview["successful"] == 60
        assert overview["failed"] == 25
        assert overview["skipped"] == 15
