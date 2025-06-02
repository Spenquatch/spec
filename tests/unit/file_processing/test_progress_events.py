"""Tests for progress events functionality."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from spec_cli.file_processing.progress_events import (
    ProcessingStage,
    ProgressEvent,
    ProgressEventType,
    ProgressReporter,
    progress_reporter,
)


class TestProgressEvent:
    """Test ProgressEvent class."""

    def test_progress_event_creation_and_serialization(self) -> None:
        """Test creating and serializing progress events."""
        file_path = Path("/test/file.py")
        stage = ProcessingStage.CONTENT_GENERATION
        metadata = {"file_size": 1024, "language": "python"}

        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED,
            file_path=file_path,
            stage=stage,
            progress=0.5,
            total_files=10,
            processed_files=5,
            message="Processing file",
            metadata=metadata,
        )

        # Test properties
        assert event.event_type == ProgressEventType.FILE_STARTED
        assert event.file_path == file_path
        assert event.stage == stage
        assert event.progress == 0.5
        assert event.total_files == 10
        assert event.processed_files == 5
        assert event.message == "Processing file"
        assert event.metadata == metadata

        # Test serialization
        event_dict = event.to_dict()
        expected_keys = {
            "event_type",
            "timestamp",
            "file_path",
            "stage",
            "progress",
            "total_files",
            "processed_files",
            "message",
            "metadata",
        }
        assert set(event_dict.keys()) == expected_keys
        assert event_dict["event_type"] == "file_started"
        assert event_dict["file_path"] == str(file_path)
        assert event_dict["stage"] == "content_generation"
        assert event_dict["progress"] == 0.5
        assert event_dict["metadata"] == metadata

    def test_progress_event_with_minimal_data(self) -> None:
        """Test progress event with only required data."""
        event = ProgressEvent(event_type=ProgressEventType.WARNING)

        # Should have default values for optional fields
        assert event.file_path is None
        assert event.stage is None
        assert event.progress is None
        assert event.total_files is None
        assert event.processed_files is None
        assert event.message is None
        assert event.metadata == {}

        # Serialization should handle None values
        event_dict = event.to_dict()
        assert event_dict["file_path"] is None
        assert event_dict["stage"] is None


class TestProgressReporter:
    """Test ProgressReporter class."""

    @pytest.fixture
    def progress_reporter(self) -> ProgressReporter:
        """Create fresh progress reporter for testing."""
        return ProgressReporter()

    def test_progress_reporter_listener_management(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test adding and removing event listeners."""
        # Create mock listeners
        listener1 = MagicMock()
        listener2 = MagicMock()

        # Initially no listeners
        assert len(progress_reporter.listeners) == 0

        # Add listeners
        progress_reporter.add_listener(listener1)
        progress_reporter.add_listener(listener2)
        assert len(progress_reporter.listeners) == 2

        # Remove listener
        removed = progress_reporter.remove_listener(listener1)
        assert removed is True
        assert len(progress_reporter.listeners) == 1

        # Try to remove non-existent listener
        removed = progress_reporter.remove_listener(listener1)
        assert removed is False
        assert len(progress_reporter.listeners) == 1

    def test_progress_reporter_event_emission(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test event emission to listeners."""
        # Create mock listeners
        listener1 = MagicMock()
        listener2 = MagicMock()
        listener_error = MagicMock(side_effect=Exception("Listener error"))

        progress_reporter.add_listener(listener1)
        progress_reporter.add_listener(listener2)
        progress_reporter.add_listener(listener_error)

        # Create test event
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_COMPLETED, message="Test event"
        )

        # Emit event
        progress_reporter.emit_event(event)

        # All listeners should be called (even if one fails)
        listener1.assert_called_once_with(event)
        listener2.assert_called_once_with(event)
        listener_error.assert_called_once_with(event)

        # Event should be stored
        assert len(progress_reporter.events) == 1
        assert progress_reporter.events[0] == event

    def test_progress_reporter_event_storage_and_retrieval(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test event storage and retrieval functionality."""
        # Create multiple events
        events = [
            ProgressEvent(
                event_type=ProgressEventType.FILE_STARTED, message=f"Event {i}"
            )
            for i in range(15)
        ]

        # Emit all events
        for event in events:
            progress_reporter.emit_event(event)

        # Test basic retrieval
        all_events = progress_reporter.events
        assert len(all_events) == 15

        # Test recent events
        recent = progress_reporter.get_recent_events(5)
        assert len(recent) == 5
        assert recent[-1].message == "Event 14"  # Most recent

        # Test events by type
        file_started_events = progress_reporter.get_events_by_type(
            ProgressEventType.FILE_STARTED
        )
        assert len(file_started_events) == 15

        warning_events = progress_reporter.get_events_by_type(ProgressEventType.WARNING)
        assert len(warning_events) == 0

        # Test event storage limit
        # Add many more events to test limit
        for i in range(progress_reporter.max_events):
            progress_reporter.emit_event(
                ProgressEvent(
                    event_type=ProgressEventType.WARNING, message=f"Extra {i}"
                )
            )

        # Should not exceed max_events
        assert len(progress_reporter.events) <= progress_reporter.max_events

    def test_progress_reporter_convenience_methods(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test convenience methods for common events."""
        file_path = Path("/test/file.py")

        # Test batch started
        progress_reporter.emit_batch_started(5, "Starting batch")
        events = progress_reporter.get_events_by_type(ProgressEventType.BATCH_STARTED)
        assert len(events) == 1
        assert events[0].total_files == 5
        assert events[0].processed_files == 0
        assert events[0].progress == 0.0
        assert events[0].message is not None and "Starting batch" in events[0].message

        # Test batch completed
        progress_reporter.emit_batch_completed(5, 4, 1, 10.5)
        events = progress_reporter.get_events_by_type(ProgressEventType.BATCH_COMPLETED)
        assert len(events) == 1
        assert events[0].total_files == 5
        assert events[0].processed_files == 5
        assert events[0].progress == 1.0
        assert events[0].metadata["successful_files"] == 4
        assert events[0].metadata["failed_files"] == 1
        assert events[0].metadata["duration"] == 10.5

        # Test file started
        progress_reporter.emit_file_started(file_path, 2, 5)
        events = progress_reporter.get_events_by_type(ProgressEventType.FILE_STARTED)
        assert len(events) == 1
        assert events[0].file_path == file_path
        assert events[0].progress == 2 / 5
        assert events[0].total_files == 5
        assert events[0].processed_files == 2

        # Test file completed (success)
        progress_reporter.emit_file_completed(file_path, 2, 5, True)
        events = progress_reporter.get_events_by_type(ProgressEventType.FILE_COMPLETED)
        assert len(events) == 1
        assert events[0].file_path == file_path
        assert events[0].progress == 3 / 5  # file_index + 1

        # Test file completed (failure)
        progress_reporter.emit_file_completed(file_path, 2, 5, False)
        events = progress_reporter.get_events_by_type(ProgressEventType.FILE_FAILED)
        assert len(events) == 1

        # Test stage update
        progress_reporter.emit_stage_update(
            file_path, ProcessingStage.CONFLICT_DETECTION, "Checking conflicts"
        )
        events = progress_reporter.get_events_by_type(ProgressEventType.STAGE_STARTED)
        assert len(events) == 1
        assert events[0].stage == ProcessingStage.CONFLICT_DETECTION
        assert events[0].message == "Checking conflicts"

        # Test conflict detected
        progress_reporter.emit_conflict_detected(
            file_path, "content_modified", "merge_intelligent"
        )
        events = progress_reporter.get_events_by_type(
            ProgressEventType.CONFLICT_DETECTED
        )
        assert len(events) == 1
        assert events[0].metadata["conflict_type"] == "content_modified"
        assert events[0].metadata["strategy"] == "merge_intelligent"

        # Test warning
        progress_reporter.emit_warning("Test warning", file_path)
        events = progress_reporter.get_events_by_type(ProgressEventType.WARNING)
        assert len(events) == 1
        assert events[0].message == "Test warning"
        assert events[0].file_path == file_path

        # Test error
        test_error = ValueError("Test error")
        progress_reporter.emit_error("Error occurred", file_path, test_error)
        events = progress_reporter.get_events_by_type(ProgressEventType.ERROR)
        assert len(events) == 1
        assert events[0].message == "Error occurred"
        assert events[0].metadata["error_type"] == "ValueError"
        assert events[0].metadata["error_details"] == "Test error"

    def test_progress_reporter_summary_generation(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test summary generation."""
        # Empty reporter
        summary = progress_reporter.get_summary()
        assert summary["total_events"] == 0

        # Add various events
        events = [
            ProgressEvent(event_type=ProgressEventType.FILE_STARTED),
            ProgressEvent(event_type=ProgressEventType.FILE_COMPLETED),
            ProgressEvent(event_type=ProgressEventType.FILE_STARTED),
            ProgressEvent(event_type=ProgressEventType.WARNING),
        ]

        for event in events:
            progress_reporter.emit_event(event)

        summary = progress_reporter.get_summary()
        assert summary["total_events"] == 4
        assert summary["event_counts"]["file_started"] == 2
        assert summary["event_counts"]["file_completed"] == 1
        assert summary["event_counts"]["warning"] == 1
        assert "latest_event" in summary
        assert "timespan" in summary

        # Latest event should be the warning
        assert summary["latest_event"]["event_type"] == "warning"

    def test_progress_reporter_clear_events(
        self, progress_reporter: ProgressReporter
    ) -> None:
        """Test clearing stored events."""
        # Add some events
        for _ in range(5):
            progress_reporter.emit_event(
                ProgressEvent(event_type=ProgressEventType.FILE_STARTED)
            )

        assert len(progress_reporter.events) == 5

        # Clear events
        progress_reporter.clear_events()
        assert len(progress_reporter.events) == 0

        # Summary should show no events
        summary = progress_reporter.get_summary()
        assert summary["total_events"] == 0


class TestProgressEventTypes:
    """Test progress event type enumerations."""

    def test_progress_event_type_enumeration(self) -> None:
        """Test all progress event types are defined."""
        expected_types = {
            "batch_started",
            "batch_completed",
            "batch_failed",
            "file_started",
            "file_completed",
            "file_failed",
            "file_skipped",
            "stage_started",
            "stage_completed",
            "conflict_detected",
            "conflict_resolved",
            "progress_update",
            "warning",
            "error",
        }

        actual_types = {event_type.value for event_type in ProgressEventType}
        assert actual_types == expected_types

    def test_processing_stage_enumeration(self) -> None:
        """Test all processing stages are defined."""
        expected_stages = {
            "initialization",
            "change_detection",
            "content_generation",
            "conflict_detection",
            "conflict_resolution",
            "file_writing",
            "cache_update",
            "cleanup",
        }

        actual_stages = {stage.value for stage in ProcessingStage}
        assert actual_stages == expected_stages


class TestGlobalProgressReporter:
    """Test global progress reporter instance."""

    def test_global_progress_reporter_exists(self) -> None:
        """Test that global progress reporter instance exists."""
        # Should be able to import and use global instance
        assert progress_reporter is not None
        assert isinstance(progress_reporter, ProgressReporter)

        # Should be functional
        listener = MagicMock()
        progress_reporter.add_listener(listener)

        event = ProgressEvent(event_type=ProgressEventType.FILE_STARTED)
        progress_reporter.emit_event(event)

        listener.assert_called_once_with(event)

        # Clean up
        progress_reporter.remove_listener(listener)
        progress_reporter.clear_events()

    def test_progress_calculations(self) -> None:
        """Test progress percentage calculations in convenience methods."""
        reporter = ProgressReporter()

        # Test file started progress calculation
        reporter.emit_file_started(Path("test.py"), 3, 10)
        events = reporter.get_events_by_type(ProgressEventType.FILE_STARTED)
        assert events[0].progress == 3 / 10  # 0.3

        # Test file completed progress calculation
        reporter.emit_file_completed(Path("test.py"), 3, 10, True)
        events = reporter.get_events_by_type(ProgressEventType.FILE_COMPLETED)
        assert events[0].progress == 4 / 10  # (index + 1) / total = 0.4

        # Test edge case: zero total files
        reporter.emit_file_started(Path("test.py"), 0, 0)
        events = reporter.get_events_by_type(ProgressEventType.FILE_STARTED)
        assert events[-1].progress == 0.0  # Should handle division by zero

    def test_event_message_generation(self) -> None:
        """Test automatic message generation in convenience methods."""
        reporter = ProgressReporter()
        file_path = Path("example.py")

        # Test default messages
        reporter.emit_file_started(file_path, 0, 5)
        events = reporter.get_events_by_type(ProgressEventType.FILE_STARTED)
        assert events[0].message == "Processing example.py"

        reporter.emit_file_completed(file_path, 0, 5, True)
        events = reporter.get_events_by_type(ProgressEventType.FILE_COMPLETED)
        assert events[0].message == "Completed example.py"

        reporter.emit_file_completed(file_path, 0, 5, False)
        events = reporter.get_events_by_type(ProgressEventType.FILE_FAILED)
        assert events[0].message == "Failed example.py"

        # Test custom vs default stage messages
        reporter.emit_stage_update(file_path, ProcessingStage.CONTENT_GENERATION)
        events = reporter.get_events_by_type(ProgressEventType.STAGE_STARTED)
        assert events[0].message == "Stage: content_generation"

        reporter.emit_stage_update(
            file_path, ProcessingStage.CONTENT_GENERATION, "Custom message"
        )
        events = reporter.get_events_by_type(ProgressEventType.STAGE_STARTED)
        assert events[-1].message == "Custom message"
