"""Tests for BatchProgressTracker class."""

import time
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from spec_cli.file_processing.progress_events import ProgressReporter
from spec_cli.file_processing.trackers.batch_progress_tracker import (
    BatchProgressTracker,
    create_batch_progress_tracker,
)


class TestBatchProgressTracker:
    """Test BatchProgressTracker initialization and basic functionality."""

    def test_init_when_valid_parameters_then_initializes_correctly(self) -> None:
        """Test tracker initialization with valid parameters."""
        progress_reporter = Mock(spec=ProgressReporter)

        tracker = BatchProgressTracker(5, progress_reporter)

        assert tracker.total_files == 5
        assert tracker.progress_reporter is progress_reporter
        assert tracker.processed_files == 0
        assert tracker.successful_files == 0
        assert tracker.failed_files == 0
        assert tracker.skipped_files == 0
        assert tracker.start_time is None
        assert tracker.end_time is None

    def test_init_when_negative_total_files_then_raises_value_error(self) -> None:
        """Test tracker initialization with negative total_files."""
        progress_reporter = Mock(spec=ProgressReporter)

        with pytest.raises(ValueError, match="total_files must be non-negative"):
            BatchProgressTracker(-1, progress_reporter)

    def test_init_when_zero_total_files_then_initializes_correctly(self) -> None:
        """Test tracker initialization with zero total_files."""
        progress_reporter = Mock(spec=ProgressReporter)

        tracker = BatchProgressTracker(0, progress_reporter)

        assert tracker.total_files == 0
        assert tracker.processed_files == 0


class TestBatchProgressTrackerBatchOperations:
    """Test batch-level operations (start/complete)."""

    @pytest.fixture
    def mock_progress_reporter(self) -> Mock:
        """Mock progress reporter for testing."""
        return Mock(spec=ProgressReporter)

    @pytest.fixture
    def tracker(self, mock_progress_reporter: Mock) -> BatchProgressTracker:
        """Sample tracker for testing."""
        return BatchProgressTracker(3, mock_progress_reporter)

    def test_start_batch_when_called_then_initializes_state_and_emits_event(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test batch start functionality."""
        tracker.start_batch()

        assert tracker.processed_files == 0
        assert tracker.successful_files == 0
        assert tracker.failed_files == 0
        assert tracker.skipped_files == 0
        assert tracker.start_time is not None
        assert tracker.end_time is None

        mock_progress_reporter.emit_batch_started.assert_called_once_with(
            3, "Processing 3 files"
        )

    def test_start_batch_when_custom_message_then_uses_custom_message(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test batch start with custom message."""
        custom_message = "Custom batch message"

        tracker.start_batch(custom_message)

        mock_progress_reporter.emit_batch_started.assert_called_once_with(
            3, custom_message
        )

    def test_complete_batch_when_called_then_sets_end_time_and_emits_event(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test batch completion functionality."""
        tracker.start_batch()
        tracker.successful_files = 2
        tracker.failed_files = 1

        tracker.complete_batch()

        assert tracker.end_time is not None
        mock_progress_reporter.emit_batch_completed.assert_called_once_with(
            3, 2, 1, tracker.duration
        )

    def test_complete_batch_when_duration_provided_then_uses_provided_duration(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test batch completion with provided duration."""
        tracker.start_batch()
        custom_duration = 5.5

        tracker.complete_batch(custom_duration)

        mock_progress_reporter.emit_batch_completed.assert_called_once_with(
            3, 0, 0, custom_duration
        )


class TestBatchProgressTrackerFileOperations:
    """Test file-level tracking operations."""

    @pytest.fixture
    def mock_progress_reporter(self) -> Mock:
        """Mock progress reporter for testing."""
        return Mock(spec=ProgressReporter)

    @pytest.fixture
    def tracker(self, mock_progress_reporter: Mock) -> BatchProgressTracker:
        """Sample tracker for testing."""
        return BatchProgressTracker(3, mock_progress_reporter)

    def test_track_file_started_when_called_then_emits_file_started_event(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test file started tracking."""
        file_path = Path("/test/file.py")

        tracker.track_file_started(file_path)

        mock_progress_reporter.emit_file_started.assert_called_once_with(
            file_path, 0, 3
        )

    def test_track_file_completed_when_success_then_increments_successful_and_emits_event(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test successful file completion tracking."""
        file_path = Path("/test/file.py")

        tracker.track_file_completed(file_path, True)

        assert tracker.processed_files == 1
        assert tracker.successful_files == 1
        assert tracker.failed_files == 0

        mock_progress_reporter.emit_file_completed.assert_called_once_with(
            file_path, 0, 3, True
        )

    def test_track_file_completed_when_failure_then_increments_failed_and_emits_event(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test failed file completion tracking."""
        file_path = Path("/test/file.py")

        tracker.track_file_completed(file_path, False)

        assert tracker.processed_files == 1
        assert tracker.successful_files == 0
        assert tracker.failed_files == 1

        mock_progress_reporter.emit_file_completed.assert_called_once_with(
            file_path, 0, 3, False
        )

    def test_track_file_completed_when_multiple_files_then_tracks_sequence_correctly(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test tracking multiple file completions."""
        file1 = Path("/test/file1.py")
        file2 = Path("/test/file2.py")

        tracker.track_file_completed(file1, True)
        tracker.track_file_completed(file2, False)

        assert tracker.processed_files == 2
        assert tracker.successful_files == 1
        assert tracker.failed_files == 1

        expected_calls = [call(file1, 0, 3, True), call(file2, 1, 3, False)]
        mock_progress_reporter.emit_file_completed.assert_has_calls(expected_calls)

    def test_track_file_skipped_when_called_then_increments_skipped_count(
        self, tracker: BatchProgressTracker, mock_progress_reporter: Mock
    ) -> None:
        """Test file skipped tracking."""
        file_path = Path("/test/file.py")

        tracker.track_file_skipped(file_path)

        assert tracker.skipped_files == 1
        # Skipped files don't emit progress events, just debug logging


class TestBatchProgressTrackerProgressCalculation:
    """Test progress calculation and statistics."""

    @pytest.fixture
    def mock_progress_reporter(self) -> Mock:
        """Mock progress reporter for testing."""
        return Mock(spec=ProgressReporter)

    def test_get_current_progress_when_no_files_processed_then_returns_zero(
        self,
    ) -> None:
        """Test progress calculation with no files processed."""
        tracker = BatchProgressTracker(5, Mock(spec=ProgressReporter))

        progress = tracker.get_current_progress()

        assert progress == 0.0

    def test_get_current_progress_when_zero_total_files_then_returns_one(self) -> None:
        """Test progress calculation with zero total files."""
        tracker = BatchProgressTracker(0, Mock(spec=ProgressReporter))

        progress = tracker.get_current_progress()

        assert progress == 1.0

    def test_get_current_progress_when_partial_completion_then_returns_correct_ratio(
        self,
    ) -> None:
        """Test progress calculation with partial completion."""
        tracker = BatchProgressTracker(4, Mock(spec=ProgressReporter))
        tracker.processed_files = 2

        progress = tracker.get_current_progress()

        assert progress == 0.5

    def test_get_current_progress_when_all_completed_then_returns_one(self) -> None:
        """Test progress calculation with all files completed."""
        tracker = BatchProgressTracker(3, Mock(spec=ProgressReporter))
        tracker.processed_files = 3

        progress = tracker.get_current_progress()

        assert progress == 1.0

    def test_is_complete_when_not_all_processed_then_returns_false(self) -> None:
        """Test completion check with incomplete processing."""
        tracker = BatchProgressTracker(5, Mock(spec=ProgressReporter))
        tracker.processed_files = 3

        assert not tracker.is_complete

    def test_is_complete_when_all_processed_then_returns_true(self) -> None:
        """Test completion check with complete processing."""
        tracker = BatchProgressTracker(3, Mock(spec=ProgressReporter))
        tracker.processed_files = 3

        assert tracker.is_complete

    def test_duration_when_not_started_then_returns_none(self) -> None:
        """Test duration property when not started."""
        tracker = BatchProgressTracker(3, Mock(spec=ProgressReporter))

        assert tracker.duration is None

    def test_duration_when_started_but_not_completed_then_returns_current_duration(
        self,
    ) -> None:
        """Test duration property when started but not completed."""
        tracker = BatchProgressTracker(3, Mock(spec=ProgressReporter))
        start_time = time.time()
        tracker.start_time = start_time

        duration = tracker.duration

        assert duration is not None
        assert duration >= 0
        # Allow for small timing differences
        assert duration < 1.0

    def test_duration_when_completed_then_returns_total_duration(self) -> None:
        """Test duration property when completed."""
        tracker = BatchProgressTracker(3, Mock(spec=ProgressReporter))
        tracker.start_time = 10.0
        tracker.end_time = 15.5

        duration = tracker.duration

        assert duration == 5.5


class TestBatchProgressTrackerSummaryStatistics:
    """Test summary statistics generation."""

    @pytest.fixture
    def mock_progress_reporter(self) -> Mock:
        """Mock progress reporter for testing."""
        return Mock(spec=ProgressReporter)

    def test_get_summary_statistics_when_initial_state_then_returns_default_values(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test summary statistics with initial state."""
        tracker = BatchProgressTracker(5, mock_progress_reporter)

        summary = tracker.get_summary_statistics()

        expected = {
            "total_files": 5,
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "progress": 0.0,
            "duration": None,
            "success_rate": 0.0,
            "completion_rate": 0.0,
        }
        assert summary == expected

    def test_get_summary_statistics_when_partial_completion_then_returns_correct_values(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test summary statistics with partial completion."""
        tracker = BatchProgressTracker(4, mock_progress_reporter)
        tracker.processed_files = 3
        tracker.successful_files = 2
        tracker.failed_files = 1
        tracker.skipped_files = 1
        tracker.start_time = 10.0
        tracker.end_time = 15.0

        summary = tracker.get_summary_statistics()

        assert summary["total_files"] == 4
        assert summary["processed_files"] == 3
        assert summary["successful_files"] == 2
        assert summary["failed_files"] == 1
        assert summary["skipped_files"] == 1
        assert summary["progress"] == 0.75
        assert summary["duration"] == 5.0
        assert summary["success_rate"] == 2 / 3
        assert summary["completion_rate"] == 0.75

    def test_get_summary_statistics_when_in_progress_then_calculates_current_duration(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test summary statistics with batch in progress."""
        tracker = BatchProgressTracker(3, mock_progress_reporter)
        tracker.start_time = time.time() - 2.0  # Started 2 seconds ago
        tracker.processed_files = 1
        tracker.successful_files = 1

        summary = tracker.get_summary_statistics()

        assert summary["duration"] is not None
        assert summary["duration"] >= 1.9  # Allow for timing differences
        assert summary["duration"] < 3.0

    def test_get_summary_statistics_when_zero_processed_then_handles_division_by_zero(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test summary statistics handles division by zero correctly."""
        tracker = BatchProgressTracker(5, mock_progress_reporter)
        # No files processed

        summary = tracker.get_summary_statistics()

        # Should use max(processed_files, 1) to avoid division by zero
        assert summary["success_rate"] == 0.0


class TestFactoryFunction:
    """Test the factory function for creating trackers."""

    def test_create_batch_progress_tracker_when_called_then_returns_configured_instance(
        self,
    ) -> None:
        """Test factory function creates properly configured tracker."""
        progress_reporter = Mock(spec=ProgressReporter)

        tracker = create_batch_progress_tracker(10, progress_reporter)

        assert isinstance(tracker, BatchProgressTracker)
        assert tracker.total_files == 10
        assert tracker.progress_reporter is progress_reporter

    def test_create_batch_progress_tracker_when_invalid_params_then_raises_error(
        self,
    ) -> None:
        """Test factory function with invalid parameters."""
        progress_reporter = Mock(spec=ProgressReporter)

        with pytest.raises(ValueError):
            create_batch_progress_tracker(-5, progress_reporter)


class TestBatchProgressTrackerIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.fixture
    def mock_progress_reporter(self) -> Mock:
        """Mock progress reporter for testing."""
        return Mock(spec=ProgressReporter)

    def test_complete_workflow_when_all_successful_then_tracks_correctly(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test complete workflow with all files successful."""
        tracker = BatchProgressTracker(3, mock_progress_reporter)
        files = [Path("/test/file1.py"), Path("/test/file2.py"), Path("/test/file3.py")]

        # Start batch
        tracker.start_batch("Test batch")

        # Process files
        for _i, file_path in enumerate(files):
            tracker.track_file_started(file_path)
            tracker.track_file_completed(file_path, True)

        # Complete batch
        tracker.complete_batch()

        # Verify final state
        assert tracker.is_complete
        assert tracker.successful_files == 3
        assert tracker.failed_files == 0
        assert tracker.get_current_progress() == 1.0

        # Verify events were emitted
        mock_progress_reporter.emit_batch_started.assert_called_once()
        mock_progress_reporter.emit_batch_completed.assert_called_once()
        assert mock_progress_reporter.emit_file_started.call_count == 3
        assert mock_progress_reporter.emit_file_completed.call_count == 3

    def test_complete_workflow_when_mixed_results_then_tracks_correctly(
        self, mock_progress_reporter: Mock
    ) -> None:
        """Test complete workflow with mixed success/failure/skipped files."""
        tracker = BatchProgressTracker(5, mock_progress_reporter)
        files = [
            Path("/test/file1.py"),
            Path("/test/file2.py"),
            Path("/test/file3.py"),
            Path("/test/file4.py"),
            Path("/test/file5.py"),
        ]

        # Start batch
        tracker.start_batch()

        # Process files with mixed results
        tracker.track_file_started(files[0])
        tracker.track_file_completed(files[0], True)  # Success

        tracker.track_file_started(files[1])
        tracker.track_file_completed(files[1], False)  # Failure

        tracker.track_file_skipped(files[2])  # Skipped

        tracker.track_file_started(files[3])
        tracker.track_file_completed(files[3], True)  # Success

        tracker.track_file_started(files[4])
        tracker.track_file_completed(files[4], True)  # Success

        # Complete batch
        tracker.complete_batch()

        # Verify final state
        summary = tracker.get_summary_statistics()
        assert summary["total_files"] == 5
        assert summary["processed_files"] == 4  # 3 success + 1 failure
        assert summary["successful_files"] == 3
        assert summary["failed_files"] == 1
        assert summary["skipped_files"] == 1
        assert summary["success_rate"] == 0.75  # 3/4 processed files
        assert summary["completion_rate"] == 0.8  # 4/5 total files
