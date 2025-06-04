"""Tests for progress utilities functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ui.progress_utils import (
    ProgressTracker,
    calculate_processing_speed,
    create_file_progress_tracker,
    estimate_operation_time,
    format_time_duration,
    progress_context,
    show_progress_for_files,
    timed_operation,
    track_progress,
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_estimate_operation_time_basic(self) -> None:
        """Test basic operation time estimation."""
        result = estimate_operation_time(10, 2.0, 1.0)

        assert result == 21.0  # (10 * 2.0) + 1.0

    def test_estimate_operation_time_defaults(self) -> None:
        """Test operation time estimation with defaults."""
        result = estimate_operation_time(5)

        assert result == 11.0  # (5 * 2.0) + 1.0

    def test_estimate_operation_time_zero_items(self) -> None:
        """Test operation time estimation with zero items."""
        result = estimate_operation_time(0, 3.0, 5.0)

        assert result == 5.0  # (0 * 3.0) + 5.0

    def test_format_time_duration_seconds(self) -> None:
        """Test time formatting for seconds."""
        assert format_time_duration(30.5) == "30.5s"
        assert format_time_duration(59.9) == "59.9s"
        assert format_time_duration(0.1) == "0.1s"

    def test_format_time_duration_minutes(self) -> None:
        """Test time formatting for minutes."""
        assert format_time_duration(60) == "1.0m"
        assert format_time_duration(90) == "1.5m"
        assert format_time_duration(3540) == "59.0m"

    def test_format_time_duration_hours(self) -> None:
        """Test time formatting for hours."""
        assert format_time_duration(3600) == "1.0h"
        assert format_time_duration(5400) == "1.5h"
        assert format_time_duration(7200) == "2.0h"

    def test_calculate_processing_speed_normal(self) -> None:
        """Test processing speed calculation."""
        speed = calculate_processing_speed(100, 50.0)

        assert speed == 2.0  # 100 items / 50 seconds

    def test_calculate_processing_speed_zero_time(self) -> None:
        """Test processing speed with zero elapsed time."""
        speed = calculate_processing_speed(100, 0.0)

        assert speed == 0.0

    def test_calculate_processing_speed_negative_time(self) -> None:
        """Test processing speed with negative time."""
        speed = calculate_processing_speed(100, -10.0)

        assert speed == 0.0

    def test_calculate_processing_speed_zero_items(self) -> None:
        """Test processing speed with zero items."""
        speed = calculate_processing_speed(0, 10.0)

        assert speed == 0.0


class TestProgressContext:
    """Test progress_context context manager."""

    @patch("spec_cli.ui.progress_utils.simple_progress")
    def test_progress_context_determinate(self, mock_simple_progress: Mock) -> None:
        """Test progress context with determinate progress."""
        mock_progress_bar = Mock()
        mock_simple_progress.return_value.__enter__ = Mock(
            return_value=mock_progress_bar
        )
        mock_simple_progress.return_value.__exit__ = Mock(return_value=None)

        with progress_context(total_items=100, description="Testing") as update_func:
            # Test that we get an update function
            assert callable(update_func)

            # Test updating progress
            update_func(5)
            mock_progress_bar.advance.assert_called_with(5)

            # Test updating with message (limited support)
            update_func(1, "Processing item")
            mock_progress_bar.advance.assert_called_with(1)

        # Verify simple_progress was called with correct parameters
        mock_simple_progress.assert_called_once_with(100, "Testing")

    @patch("spec_cli.ui.progress_utils.spinner_context")
    def test_progress_context_indeterminate_with_spinner(
        self, mock_spinner_context: Mock
    ) -> None:
        """Test progress context with indeterminate progress and spinner."""
        mock_spinner = Mock()
        mock_spinner_context.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_spinner_context.return_value.__exit__ = Mock(return_value=None)

        with progress_context(
            total_items=None, description="Loading", show_spinner=True
        ) as update_func:
            # Test that we get an update function
            assert callable(update_func)

            # Test updating with message
            update_func(1, "Loading data...")
            mock_spinner.update_text.assert_called_with("Loading data...")

            # Test updating without message (should not crash)
            update_func(1)

        # Verify spinner_context was called
        mock_spinner_context.assert_called_once_with("Loading")

    def test_progress_context_indeterminate_no_spinner(self) -> None:
        """Test progress context with indeterminate progress without spinner."""
        with progress_context(
            total_items=None, description="Silent", show_spinner=False
        ) as update_func:
            # Test that we get an update function
            assert callable(update_func)

            # Test that updates do nothing (should not crash)
            update_func(1)
            update_func(5, "Silent message")


class TestTimedOperation:
    """Test timed_operation context manager."""

    @patch("time.time")
    def test_timed_operation_basic(self, mock_time: Mock) -> None:
        """Test basic timed operation."""
        mock_time.side_effect = [1000.0, 1010.5, 1010.5]  # start, get_elapsed, finally

        with timed_operation("test_operation") as get_elapsed:
            # Test get_elapsed function
            elapsed = get_elapsed()
            assert elapsed == 10.5

    @patch("time.time")
    def test_timed_operation_no_logging(self, mock_time: Mock) -> None:
        """Test timed operation without logging."""
        mock_time.side_effect = [1000.0, 1005.0, 1005.0]

        with timed_operation("test_operation", log_result=False) as get_elapsed:
            elapsed = get_elapsed()
            assert elapsed == 5.0

    @patch("time.time")
    def test_timed_operation_with_exception(self, mock_time: Mock) -> None:
        """Test timed operation with exception."""
        mock_time.side_effect = [1000.0, 1002.0, 1002.0]

        with pytest.raises(ValueError):
            with timed_operation("failing_operation") as get_elapsed:
                # Should still measure time even with exception
                elapsed = get_elapsed()
                assert elapsed == 2.0
                raise ValueError("Test exception")


class TestCreateFileProgressTracker:
    """Test create_file_progress_tracker function."""

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_create_file_progress_tracker(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test creating file progress tracker."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        files = [Path("file1.txt"), Path("file2.txt"), Path("file3.txt")]
        tracker_func = create_file_progress_tracker(files)

        # Verify initial setup
        mock_manager.start_indeterminate_operation.assert_called_once_with(
            "file_operation_1000", "Processing 3 files"
        )

        # Test tracking file completion
        tracker_func(files[0])
        mock_manager._update_operation_text.assert_called_with(
            "file_operation_1000", "Processing file1.txt (1/3)"
        )

        # Complete second file
        tracker_func(files[1])
        mock_manager._update_operation_text.assert_called_with(
            "file_operation_1000", "Processing file2.txt (2/3)"
        )

        # Complete final file - should finish operation
        tracker_func(files[2])
        mock_manager._update_operation_text.assert_called_with(
            "file_operation_1000", "Processing file3.txt (3/3)"
        )
        mock_manager.finish_operation.assert_called_once_with("file_operation_1000")

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_create_file_progress_tracker_empty_list(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test creating file progress tracker with empty file list."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        files: list[Path] = []
        tracker_func = create_file_progress_tracker(files)

        # Should still set up operation
        mock_manager.start_indeterminate_operation.assert_called_once_with(
            "file_operation_1000", "Processing 0 files"
        )

        # No files to track, but function should work
        assert callable(tracker_func)


class TestProgressTracker:
    """Test ProgressTracker class."""

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_initialization(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test ProgressTracker initialization."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=10, auto_finish=False)

        assert tracker.operation_name == "test_operation"
        assert tracker.total_items == 10
        assert tracker.auto_finish is False
        assert tracker.completed_items == 0
        assert tracker.start_time is None
        assert tracker.progress_manager == mock_manager
        assert tracker.operation_id == "test_operation_1000"

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_start_indeterminate(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test starting indeterminate progress tracker."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=None)
        tracker.start()

        assert tracker.start_time == 1000
        mock_manager.start_indeterminate_operation.assert_called_once_with(
            "test_operation_1000", "test_operation"
        )

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_start_determinate(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test starting determinate progress tracker."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=10)
        tracker.start()

        assert tracker.start_time == 1000
        # Should not start indeterminate operation for determinate progress
        mock_manager.start_indeterminate_operation.assert_not_called()

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    def test_progress_tracker_update_basic(self, mock_get_manager: Mock) -> None:
        """Test basic progress tracker update."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=10, auto_finish=False)

        tracker.update(3)
        assert tracker.completed_items == 3

        tracker.update(2)
        assert tracker.completed_items == 5

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    def test_progress_tracker_update_with_message(self, mock_get_manager: Mock) -> None:
        """Test progress tracker update with message."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", auto_finish=False)

        tracker.update(1, "Processing item 1")

        mock_manager._update_operation_text.assert_called_once_with(
            tracker.operation_id, "test_operation: Processing item 1"
        )

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    def test_progress_tracker_auto_finish(self, mock_get_manager: Mock) -> None:
        """Test progress tracker auto-finish."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=5, auto_finish=True)

        # Update to completion
        tracker.update(5)

        # Should auto-finish
        mock_manager.finish_operation.assert_called_once_with(tracker.operation_id)

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    def test_progress_tracker_manual_finish(self, mock_get_manager: Mock) -> None:
        """Test manual progress tracker finish."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation")
        tracker.finish()

        mock_manager.finish_operation.assert_called_once_with(tracker.operation_id)

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_get_statistics_basic(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test getting basic progress statistics."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=10)
        tracker.completed_items = 5

        stats = tracker.get_statistics()

        assert stats["operation_name"] == "test_operation"
        assert stats["completed_items"] == 5
        assert stats["total_items"] == 10

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_get_statistics_with_timing(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test getting progress statistics with timing."""
        mock_time.side_effect = [1000.0, 1010.0]  # start_time, current_time
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        tracker = ProgressTracker("test_operation", total_items=10)
        tracker.start_time = 1000.0
        tracker.completed_items = 5

        stats = tracker.get_statistics()

        assert stats["elapsed_time"] == 10.0
        assert stats["items_per_second"] == 0.5  # 5 items / 10 seconds
        assert stats["progress_percentage"] == 50.0  # 5/10 * 100
        assert "estimated_completion" in stats

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_context_manager(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test ProgressTracker as context manager."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        with ProgressTracker("test_operation", total_items=5) as tracker:
            assert tracker.start_time == 1000
            tracker.update(3)
            assert tracker.completed_items == 3

        # Should finish automatically
        mock_manager.finish_operation.assert_called_once()

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_progress_tracker_context_manager_exception(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test ProgressTracker context manager with exception."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        with pytest.raises(ValueError):
            with ProgressTracker("test_operation") as tracker:
                tracker.update(1)
                raise ValueError("Test exception")

        # Should still finish even with exception
        mock_manager.finish_operation.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("spec_cli.ui.progress_utils.ProgressTracker")
    def test_track_progress(self, mock_progress_tracker_class: Mock) -> None:
        """Test track_progress convenience function."""
        mock_tracker = Mock()
        mock_progress_tracker_class.return_value = mock_tracker

        result = track_progress("test_operation", total_items=100)

        assert result == mock_tracker
        mock_progress_tracker_class.assert_called_once_with("test_operation", 100)

    @patch("spec_cli.ui.progress_utils.create_file_progress_tracker")
    def test_show_progress_for_files(self, mock_create_tracker: Mock) -> None:
        """Test show_progress_for_files convenience function."""
        mock_tracker_func = Mock()
        mock_create_tracker.return_value = mock_tracker_func

        files = [Path("file1.txt"), Path("file2.txt")]
        result = show_progress_for_files(files, "Custom Operation")

        assert result == mock_tracker_func
        mock_create_tracker.assert_called_once_with(files)

    @patch("spec_cli.ui.progress_utils.create_file_progress_tracker")
    def test_show_progress_for_files_default_name(
        self, mock_create_tracker: Mock
    ) -> None:
        """Test show_progress_for_files with default operation name."""
        mock_tracker_func = Mock()
        mock_create_tracker.return_value = mock_tracker_func

        files = [Path("file1.txt")]
        result = show_progress_for_files(files)

        assert result == mock_tracker_func
        mock_create_tracker.assert_called_once_with(files)


class TestProgressUtilsIntegration:
    """Test progress utilities integration scenarios."""

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_complete_file_processing_workflow(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test complete file processing workflow."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]

        # Create file tracker
        tracker_func = create_file_progress_tracker(files)

        # Simulate processing each file
        for file_path in files:
            # Process file...
            tracker_func(file_path)

        # Verify all files were tracked and operation completed
        assert mock_manager._update_operation_text.call_count == 3
        mock_manager.finish_operation.assert_called_once()

    @patch("spec_cli.ui.progress_utils.get_progress_manager")
    @patch("time.time")
    def test_nested_progress_tracking(
        self, mock_time: Mock, mock_get_manager: Mock
    ) -> None:
        """Test nested progress tracking scenarios."""
        mock_time.return_value = 1000
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        # Outer operation (disable auto-finish to control when it finishes)
        with ProgressTracker(
            "outer_operation", total_items=3, auto_finish=False
        ) as outer_tracker:
            outer_tracker.update(1, "Starting phase 1")

            # Inner operation (disable auto-finish)
            with ProgressTracker(
                "inner_operation", total_items=5, auto_finish=False
            ) as inner_tracker:
                for i in range(5):
                    inner_tracker.update(1, f"Inner step {i+1}")

            outer_tracker.update(1, "Phase 1 complete")
            outer_tracker.update(1, "All phases complete")

        # Both operations should have finished (once each from context manager exit)
        assert mock_manager.finish_operation.call_count == 2

    @patch("spec_cli.ui.progress_utils.simple_progress")
    @patch("spec_cli.ui.progress_utils.spinner_context")
    def test_different_progress_types(
        self, mock_spinner_context: Mock, mock_simple_progress: Mock
    ) -> None:
        """Test different types of progress displays."""
        mock_progress_bar = Mock()
        mock_simple_progress.return_value.__enter__ = Mock(
            return_value=mock_progress_bar
        )
        mock_simple_progress.return_value.__exit__ = Mock(return_value=None)

        mock_spinner = Mock()
        mock_spinner_context.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_spinner_context.return_value.__exit__ = Mock(return_value=None)

        # Test determinate progress
        with progress_context(
            total_items=10, description="Processing files"
        ) as update_func:
            update_func(5)
            mock_progress_bar.advance.assert_called_with(5)

        # Test indeterminate progress with spinner
        with progress_context(
            total_items=None, description="Loading", show_spinner=True
        ) as update_func:
            update_func(1, "Loading configuration...")
            mock_spinner.update_text.assert_called_with("Loading configuration...")

        # Test silent progress
        with progress_context(total_items=None, show_spinner=False) as update_func:
            update_func(1, "Silent operation")  # Should not crash

    def test_time_formatting_comprehensive(self) -> None:
        """Test comprehensive time formatting scenarios."""
        # Test various time durations
        test_cases = [
            (0.5, "0.5s"),
            (30, "30.0s"),
            (60, "1.0m"),
            (90, "1.5m"),
            (3600, "1.0h"),
            (5400, "1.5h"),
            (7200, "2.0h"),
            (10800, "3.0h"),
        ]

        for seconds, expected in test_cases:
            result = format_time_duration(seconds)
            assert (
                result == expected
            ), f"Expected {expected} for {seconds}s, got {result}"

    def test_processing_speed_edge_cases(self) -> None:
        """Test processing speed calculation edge cases."""
        # Normal cases
        assert calculate_processing_speed(100, 10.0) == 10.0
        assert calculate_processing_speed(50, 25.0) == 2.0

        # Edge cases
        assert calculate_processing_speed(0, 10.0) == 0.0
        assert calculate_processing_speed(100, 0.0) == 0.0
        assert calculate_processing_speed(100, -5.0) == 0.0
        assert calculate_processing_speed(-10, 5.0) == -2.0  # Negative items

    def test_operation_time_estimation_edge_cases(self) -> None:
        """Test operation time estimation edge cases."""
        # Zero items
        assert estimate_operation_time(0) == 1.0  # Just overhead

        # Large numbers
        assert estimate_operation_time(1000, 0.1, 10.0) == 110.0

        # Zero time per item
        assert estimate_operation_time(100, 0.0, 5.0) == 5.0

        # Negative values
        assert estimate_operation_time(10, -1.0, 5.0) == -5.0
