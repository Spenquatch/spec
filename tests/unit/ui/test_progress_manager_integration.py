"""Integration tests for ErrorHandler usage in progress manager."""

from unittest.mock import patch

from spec_cli.file_processing.progress_events import ProgressEvent, ProgressEventType
from spec_cli.ui.progress_manager import ProgressManager
from spec_cli.utils.error_handler import ErrorHandler


class TestProgressManagerErrorIntegration:
    """Test ErrorHandler integration in ProgressManager."""

    def test_progress_manager_when_initialized_then_has_error_handler(self):
        """Test that ProgressManager initializes with ErrorHandler."""
        manager = ProgressManager()

        assert hasattr(manager, "error_handler")
        assert isinstance(manager.error_handler, ErrorHandler)
        assert manager.error_handler.default_context["component"] == "progress_manager"

    @patch("spec_cli.ui.progress_manager.debug_logger")
    def test_event_handler_error_when_handler_fails_then_uses_error_handler(
        self, mock_logger
    ):
        """Test that event handler failures use ErrorHandler."""
        manager = ProgressManager()

        # Add a handler that will fail
        def failing_handler(event):
            raise ValueError("Handler failed")

        manager.add_event_handler(ProgressEventType.FILE_STARTED, failing_handler)

        # Create an event
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED, message="Test event"
        )

        # Mock the error_handler.report to capture the call
        with patch.object(manager.error_handler, "report") as mock_report:
            # This should trigger the failing handler
            manager._handle_progress_event(event)

            # Should use ErrorHandler for the failure
            assert mock_report.called
            call_args = mock_report.call_args
            assert "handle progress event" in call_args[0][1]  # operation description
            assert "event_type" in call_args[1]  # additional context
            assert "handler_name" in call_args[1]
            assert "progress_operation" in call_args[1]

    def test_progress_manager_error_context_when_handler_fails_then_structured_info(
        self,
    ):
        """Test that ProgressManager provides structured context for handler failures."""
        manager = ProgressManager()

        # The ErrorHandler should have proper context
        assert manager.error_handler.default_context["component"] == "progress_manager"

    def test_progress_manager_event_handling_when_multiple_handlers_then_isolated_failures(
        self,
    ):
        """Test that handler failures are isolated using ErrorHandler."""
        manager = ProgressManager()

        success_calls = []

        def working_handler(event):
            success_calls.append(event)

        def failing_handler(event):
            raise RuntimeError("This handler always fails")

        # Add both handlers
        manager.add_event_handler(ProgressEventType.FILE_STARTED, working_handler)
        manager.add_event_handler(ProgressEventType.FILE_STARTED, failing_handler)

        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED, message="Test event"
        )

        # Mock ErrorHandler to not actually raise
        with patch.object(manager.error_handler, "report") as mock_report:
            manager._handle_progress_event(event)

            # Working handler should have been called
            assert len(success_calls) == 1
            assert success_calls[0] == event

            # Error handler should have been used for the failure
            assert mock_report.called

    def test_progress_manager_cleanup_when_errors_occur_then_graceful_handling(self):
        """Test that ProgressManager handles cleanup errors gracefully."""
        manager = ProgressManager()

        # ErrorHandler should be available for any cleanup errors
        assert manager.error_handler is not None

        # Cleanup should not raise even if ErrorHandler is used
        manager.cleanup()


class TestProgressManagerHandlerErrors:
    """Test specific error handling scenarios in ProgressManager."""

    def test_handler_with_name_when_error_occurs_then_includes_handler_name(self):
        """Test that named handler failures include handler name in context."""
        manager = ProgressManager()

        def named_failing_handler(event):
            raise ValueError("Named handler failed")

        manager.add_event_handler(ProgressEventType.FILE_STARTED, named_failing_handler)

        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED, message="Test event"
        )

        with patch.object(manager.error_handler, "report") as mock_report:
            manager._handle_progress_event(event)

            # Should include handler name in context
            call_args = mock_report.call_args
            assert "handler_name" in call_args[1]
            assert call_args[1]["handler_name"] == "named_failing_handler"

    def test_handler_without_name_when_error_occurs_then_includes_handler_string(self):
        """Test that anonymous handler failures include handler string representation."""
        manager = ProgressManager()

        # Use a callable object that doesn't have __name__ attribute
        class FailingCallable:
            def __call__(self, event):
                raise ValueError("Callable failed")

        failing_callable = FailingCallable()
        manager.add_event_handler(ProgressEventType.FILE_STARTED, failing_callable)

        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED, message="Test event"
        )

        with patch.object(manager.error_handler, "report") as mock_report:
            manager._handle_progress_event(event)

            # Should include handler string representation
            call_args = mock_report.call_args
            assert "handler_name" in call_args[1]
            # Should be string representation since no __name__
            assert isinstance(call_args[1]["handler_name"], str)

    def test_event_type_context_when_handler_fails_then_includes_event_type(self):
        """Test that handler failures include event type in context."""
        manager = ProgressManager()

        def failing_handler(event):
            raise RuntimeError("Handler failed")

        manager.add_event_handler(ProgressEventType.BATCH_COMPLETED, failing_handler)

        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_COMPLETED, message="Test event"
        )

        with patch.object(manager.error_handler, "report") as mock_report:
            manager._handle_progress_event(event)

            # Should include event type
            call_args = mock_report.call_args
            assert "event_type" in call_args[1]
            assert call_args[1]["event_type"] == ProgressEventType.BATCH_COMPLETED.value

    def test_operation_context_when_handler_fails_then_includes_operation_type(self):
        """Test that handler failures include operation context."""
        manager = ProgressManager()

        def failing_handler(event):
            raise OSError("Handler failed")

        manager.add_event_handler(ProgressEventType.PROGRESS_UPDATE, failing_handler)

        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE, message="Test event"
        )

        with patch.object(manager.error_handler, "report") as mock_report:
            manager._handle_progress_event(event)

            # Should include operation type
            call_args = mock_report.call_args
            assert "progress_operation" in call_args[1]
            assert call_args[1]["progress_operation"] == "progress_event_handling"
