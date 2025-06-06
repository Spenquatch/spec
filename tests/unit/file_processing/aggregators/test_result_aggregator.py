"""Tests for BatchResultAggregator class."""

from pathlib import Path

import pytest

from spec_cli.file_processing.aggregators.result_aggregator import BatchResultAggregator
from spec_cli.file_processing.conflict_resolver import (
    ConflictInfo,
    ConflictResolutionStrategy,
    ConflictType,
)
from spec_cli.file_processing.processing_pipeline import FileProcessingResult


class TestBatchResultAggregator:
    """Test cases for BatchResultAggregator class."""

    def test_aggregate_results_when_empty_then_returns_empty_summary(self):
        """Test aggregation with no results returns empty summary."""
        aggregator = BatchResultAggregator()

        result = aggregator.aggregate_results({})

        assert result["summary"]["overview"]["total_files"] == 0
        assert result["summary"]["overview"]["successful"] == 0
        assert result["summary"]["overview"]["failed"] == 0
        assert result["summary"]["overview"]["skipped"] == 0
        assert result["statistics"]["success_rate"] == 0.0
        assert result["statistics"]["failure_rate"] == 0.0
        assert result["statistics"]["skip_rate"] == 0.0

    def test_aggregate_results_when_all_successful_then_returns_correct_summary(self):
        """Test aggregation with all successful results."""
        aggregator = BatchResultAggregator()
        file_results = {
            "file1.py": FileProcessingResult(Path("file1.py"), True),
            "file2.py": FileProcessingResult(Path("file2.py"), True),
        }

        result = aggregator.aggregate_results(file_results)

        assert result["summary"]["overview"]["total_files"] == 2
        assert result["summary"]["overview"]["successful"] == 2
        assert result["summary"]["overview"]["failed"] == 0
        assert result["summary"]["overview"]["skipped"] == 0
        assert result["statistics"]["success_rate"] == 100.0
        assert result["statistics"]["failure_rate"] == 0.0
        assert result["statistics"]["skip_rate"] == 0.0

    def test_aggregate_results_when_mixed_outcomes_then_returns_correct_summary(self):
        """Test aggregation with mixed successful, failed, and skipped results."""
        aggregator = BatchResultAggregator()

        # Create successful result
        successful_result = FileProcessingResult(Path("success.py"), True)

        # Create failed result
        failed_result = FileProcessingResult(
            Path("failed.py"), False, errors=["Permission denied"]
        )

        # Create skipped result (simulated by setting metadata)
        skipped_result = FileProcessingResult(
            Path("skipped.py"), False, metadata={"skipped": True}
        )

        file_results = {
            "success.py": successful_result,
            "failed.py": failed_result,
            "skipped.py": skipped_result,
        }

        result = aggregator.aggregate_results(file_results)

        assert result["summary"]["overview"]["total_files"] == 3
        assert result["summary"]["overview"]["successful"] == 1
        assert result["summary"]["overview"]["failed"] == 1
        assert result["summary"]["overview"]["skipped"] == 1
        assert result["statistics"]["success_rate"] == pytest.approx(33.33, rel=1e-2)
        assert result["statistics"]["failure_rate"] == pytest.approx(33.33, rel=1e-2)
        assert result["statistics"]["skip_rate"] == pytest.approx(33.33, rel=1e-2)

    def test_aggregate_results_when_conflicts_exist_then_analyzes_conflicts(self):
        """Test conflict analysis in aggregation."""
        aggregator = BatchResultAggregator()

        # Create conflict info
        conflict_info = ConflictInfo(
            ConflictType.CONTENT_MODIFIED,
            Path("conflict.py"),
            "old content",
            "new content",
        )

        # Create result with conflict
        conflict_result = FileProcessingResult(
            Path("conflict.py"),
            True,
            conflict_info=conflict_info,
            resolution_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT,
        )

        file_results = {"conflict.py": conflict_result}

        result = aggregator.aggregate_results(file_results)

        conflicts = result["summary"]["conflicts"]
        assert conflicts["files_with_conflicts"] == 1
        assert conflicts["conflict_types"]["content_modified"] == 1
        assert conflicts["resolution_strategies"]["merge_intelligent"] == 1

    def test_aggregate_results_when_multiple_conflicts_then_counts_correctly(self):
        """Test multiple conflicts are counted correctly."""
        aggregator = BatchResultAggregator()

        # Create two different conflict types
        conflict1 = ConflictInfo(ConflictType.CONTENT_MODIFIED, Path("file1.py"))
        conflict2 = ConflictInfo(ConflictType.FILE_EXISTS, Path("file2.py"))

        result1 = FileProcessingResult(
            Path("file1.py"),
            True,
            conflict_info=conflict1,
            resolution_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT,
        )

        result2 = FileProcessingResult(
            Path("file2.py"),
            True,
            conflict_info=conflict2,
            resolution_strategy=ConflictResolutionStrategy.KEEP_OURS,
        )

        file_results = {"file1.py": result1, "file2.py": result2}

        result = aggregator.aggregate_results(file_results)

        conflicts = result["summary"]["conflicts"]
        assert conflicts["files_with_conflicts"] == 2
        assert conflicts["conflict_types"]["content_modified"] == 1
        assert conflicts["conflict_types"]["file_exists"] == 1
        assert conflicts["resolution_strategies"]["merge_intelligent"] == 1
        assert conflicts["resolution_strategies"]["keep_ours"] == 1

    def test_aggregate_results_when_errors_exist_then_classifies_errors(self):
        """Test error classification in aggregation."""
        aggregator = BatchResultAggregator()

        file_results = {
            "file1.py": FileProcessingResult(
                Path("file1.py"), False, errors=["Permission denied"]
            ),
            "file2.py": FileProcessingResult(
                Path("file2.py"), False, errors=["Conflict resolution failed"]
            ),
            "file3.py": FileProcessingResult(
                Path("file3.py"), False, errors=["Generation template error"]
            ),
            "file4.py": FileProcessingResult(
                Path("file4.py"), False, errors=["Unknown system error"]
            ),
        }

        result = aggregator.aggregate_results(file_results)

        errors = result["summary"]["errors"]
        assert errors["total_errors"] == 4
        assert errors["error_types"]["permission"] == 1
        assert errors["error_types"]["conflict"] == 1
        assert errors["error_types"]["generation"] == 1
        assert errors["error_types"]["other"] == 1

    def test_aggregate_results_when_multiple_errors_same_type_then_counts_correctly(
        self,
    ):
        """Test multiple errors of same type are counted correctly."""
        aggregator = BatchResultAggregator()

        file_results = {
            "file1.py": FileProcessingResult(
                Path("file1.py"),
                False,
                errors=["Permission denied", "Permission error"],
            ),
        }

        result = aggregator.aggregate_results(file_results)

        errors = result["summary"]["errors"]
        assert errors["total_errors"] == 2
        assert errors["error_types"]["permission"] == 2

    def test_create_workflow_summary_when_successful_files_then_returns_workflow_result(
        self,
    ):
        """Test workflow summary creation for successful files."""
        aggregator = BatchResultAggregator()
        successful_files = [Path("file1.py"), Path("file2.py")]
        workflow_id = "batch-123"

        result = aggregator.create_workflow_summary(successful_files, workflow_id)

        assert result["success"] is True
        assert result["total_files"] == 2
        assert result["workflow_id"] == "batch-123"
        assert len(result["successful_files"]) == 2
        assert len(result["failed_files"]) == 0

    def test_create_workflow_summary_when_no_workflow_id_then_excludes_workflow_id(
        self,
    ):
        """Test workflow summary creation without workflow ID."""
        aggregator = BatchResultAggregator()
        successful_files = [Path("file1.py")]

        result = aggregator.create_workflow_summary(successful_files)

        assert result["success"] is True
        assert result["total_files"] == 1
        assert "workflow_id" not in result

    def test_categorize_files_when_mixed_results_then_categorizes_correctly(self):
        """Test file categorization with mixed results."""
        aggregator = BatchResultAggregator()

        successful_result = FileProcessingResult(Path("success.py"), True)
        failed_result = FileProcessingResult(Path("failed.py"), False)
        skipped_result = FileProcessingResult(
            Path("skipped.py"), False, metadata={"skipped": True}
        )

        file_results = {
            "success.py": successful_result,
            "failed.py": failed_result,
            "skipped.py": skipped_result,
        }

        successful, failed, skipped = aggregator._categorize_files(file_results)

        assert successful == ["success.py"]
        assert failed == ["failed.py"]
        assert skipped == ["skipped.py"]

    def test_analyze_conflicts_when_no_conflicts_then_returns_empty_analysis(self):
        """Test conflict analysis with no conflicts."""
        aggregator = BatchResultAggregator()

        file_results = {
            "file1.py": FileProcessingResult(Path("file1.py"), True),
        }

        analysis = aggregator._analyze_conflicts(file_results)

        assert analysis["files_with_conflicts"] == 0
        assert analysis["conflict_types"] == {}
        assert analysis["resolution_strategies"] == {}

    def test_classify_errors_when_no_errors_then_returns_empty_classification(self):
        """Test error classification with no errors."""
        aggregator = BatchResultAggregator()

        file_results = {
            "file1.py": FileProcessingResult(Path("file1.py"), True),
        }

        analysis = aggregator._classify_errors(file_results)

        assert analysis["total_errors"] == 0
        assert analysis["error_types"] == {}

    def test_calculate_statistics_when_zero_files_then_returns_zero_rates(self):
        """Test statistics calculation with zero files."""
        aggregator = BatchResultAggregator()

        stats = aggregator._calculate_statistics(0, [], [], [])

        assert stats["success_rate"] == 0.0
        assert stats["failure_rate"] == 0.0
        assert stats["skip_rate"] == 0.0

    def test_calculate_statistics_when_files_exist_then_calculates_correct_rates(self):
        """Test statistics calculation with actual files."""
        aggregator = BatchResultAggregator()

        successful = ["file1.py", "file2.py"]
        failed = ["file3.py"]
        skipped = ["file4.py"]
        total = 4

        stats = aggregator._calculate_statistics(total, successful, failed, skipped)

        assert stats["success_rate"] == 50.0
        assert stats["failure_rate"] == 25.0
        assert stats["skip_rate"] == 25.0


@pytest.fixture
def sample_file_results():
    """Create sample file processing results for testing."""
    return {
        "success.py": FileProcessingResult(Path("success.py"), True),
        "failed.py": FileProcessingResult(
            Path("failed.py"), False, errors=["Processing failed"]
        ),
    }


@pytest.fixture
def conflict_file_results():
    """Create file processing results with conflicts for testing."""
    conflict_info = ConflictInfo(
        ConflictType.CONTENT_MODIFIED, Path("conflict.py"), "old content", "new content"
    )

    return {
        "conflict.py": FileProcessingResult(
            Path("conflict.py"),
            True,
            conflict_info=conflict_info,
            resolution_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT,
        ),
    }
