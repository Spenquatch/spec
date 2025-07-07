"""Unit tests for ProgressManager - UI Display Coordination.

Test Coverage Focus:
- ProgressState data class and properties
- ProgressManager initialization and configuration
- Progress display coordination (progress bars and spinners)
- Event handling and state management
- Singleton functionality and convenience functions
- Error handling and cleanup operations

This test module achieves 40% coverage target for UI progress display functionality.
"""

import time
from unittest.mock import Mock, patch

from spec_cli.file_processing.progress_events import (
    ProcessingStage,
    ProgressEvent,
    ProgressEventType,
    ProgressReporter,
)
from spec_cli.ui.progress_manager import (
    ProgressManager,
    ProgressManagerSingleton,
    ProgressState,
    get_progress_manager,
    reset_progress_manager,
    set_progress_manager,
)


class TestProgressState:
    """Test ProgressState data class and its properties."""

    def test_progress_state_initialization(self):
        """Test ProgressState initialization with all fields."""
        state = ProgressState(
            operation_id="test_op",
            total_items=100,
            completed_items=25,
            current_item="file.py",
            stage=ProcessingStage.CONTENT_GENERATION,
            start_time=time.time(),
            estimated_completion=time.time() + 60,
        )

        assert state.operation_id == "test_op"
        assert state.total_items == 100
        assert state.completed_items == 25
        assert state.current_item == "file.py"
        assert state.stage == ProcessingStage.CONTENT_GENERATION
        assert state.start_time is not None
        assert state.estimated_completion is not None

    def test_progress_state_minimal_initialization(self):
        """Test ProgressState with only required fields."""
        state = ProgressState(
            operation_id="minimal_op", total_items=50, completed_items=10
        )

        assert state.operation_id == "minimal_op"
        assert state.total_items == 50
        assert state.completed_items == 10
        assert state.current_item is None
        assert state.stage is None
        assert state.start_time is None
        assert state.estimated_completion is None

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        # Normal case
        state = ProgressState("op1", total_items=100, completed_items=25)
        assert state.progress_percentage == 0.25

        # Complete case
        state = ProgressState("op2", total_items=50, completed_items=50)
        assert state.progress_percentage == 1.0

        # Zero total case
        state = ProgressState("op3", total_items=0, completed_items=0)
        assert state.progress_percentage == 0.0

    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        # No start time
        state = ProgressState("op1", total_items=10, completed_items=5)
        assert state.elapsed_time is None

        # With start time
        start_time = time.time() - 5.0  # 5 seconds ago
        state = ProgressState(
            "op2", total_items=10, completed_items=5, start_time=start_time
        )
        elapsed = state.elapsed_time
        assert elapsed is not None
        assert 4.5 <= elapsed <= 5.5  # Allow for timing variations

class TestProgressManagerInitialization:
    """Test ProgressManager initialization and configuration."""

    @patch("spec_cli.ui.progress_manager.progress_reporter")
    @patch("spec_cli.ui.progress_manager.SpecProgressBar")
    @patch("spec_cli.ui.progress_manager.SpinnerManager")
    @patch("spec_cli.ui.progress_manager.ErrorHandler")
    def test_default_initialization(
        self,
        mock_error_handler,
        mock_spinner_manager,
        mock_progress_bar,
        mock_progress_reporter,
    ):
        """Test ProgressManager initialization with default settings."""
        mock_reporter_instance = Mock(spec=ProgressReporter)
        mock_progress_reporter.return_value = mock_reporter_instance

        manager = ProgressManager()

        # Verify initialization
        assert manager.progress_reporter == mock_progress_reporter
        assert manager.auto_display is True
        assert isinstance(manager.progress_states, dict)
        assert isinstance(manager.active_operations, dict)

        # Verify component creation
        mock_progress_bar.assert_called_once_with(
            show_percentage=True, show_time_remaining=True, auto_refresh=True
        )
        mock_spinner_manager.assert_called_once()
        mock_error_handler.assert_called_once_with({"component": "progress_manager"})

    @patch("spec_cli.ui.progress_manager.SpecProgressBar")
    @patch("spec_cli.ui.progress_manager.SpinnerManager")
    @patch("spec_cli.ui.progress_manager.ErrorHandler")
    def test_custom_initialization(
        self, mock_error_handler, mock_spinner_manager, mock_progress_bar
    ):
        """Test ProgressManager initialization with custom settings."""
        custom_reporter = Mock(spec=ProgressReporter)

        manager = ProgressManager(
            progress_reporter_instance=custom_reporter, auto_display=False
        )

        assert manager.progress_reporter == custom_reporter
        assert manager.auto_display is False

    @patch("spec_cli.ui.progress_manager.SpecProgressBar")
    @patch("spec_cli.ui.progress_manager.SpinnerManager")
    @patch("spec_cli.ui.progress_manager.ErrorHandler")
    def test_event_handling_setup(
        self, mock_error_handler, mock_spinner_manager, mock_progress_bar
    ):
        """Test that event handling is properly set up during initialization."""
        mock_reporter = Mock(spec=ProgressReporter)

        manager = ProgressManager(progress_reporter_instance=mock_reporter)

        # Verify reporter listener was added
        mock_reporter.add_listener.assert_called_once()

        # Verify event handlers are set up
        expected_events = {
            ProgressEventType.BATCH_STARTED,
            ProgressEventType.BATCH_COMPLETED,
            ProgressEventType.BATCH_FAILED,
            ProgressEventType.FILE_STARTED,
            ProgressEventType.FILE_COMPLETED,
            ProgressEventType.FILE_FAILED,
            ProgressEventType.STAGE_STARTED,
            ProgressEventType.PROGRESS_UPDATE,
        }

        assert set(manager._event_handlers.keys()) == expected_events

class TestProgressManagerEventHandling:
    """Test ProgressManager event handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_reporter = Mock(spec=ProgressReporter)
        with (
            patch("spec_cli.ui.progress_manager.SpecProgressBar"),
            patch("spec_cli.ui.progress_manager.SpinnerManager"),
            patch("spec_cli.ui.progress_manager.ErrorHandler"),
        ):
            self.manager = ProgressManager(
                progress_reporter_instance=self.mock_reporter
            )

    def test_handle_progress_event_success(self):
        """Test successful progress event handling."""
        # Create mock handler
        mock_handler = Mock()
        self.manager._event_handlers[ProgressEventType.BATCH_STARTED] = [mock_handler]

        # Create test event
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Test batch started",
            total_files=10,
        )

        # Handle event
        self.manager._handle_progress_event(event)

        # Verify handler was called
        mock_handler.assert_called_once_with(event)

    def test_handle_progress_event_handler_error(self):
        """Test progress event handling when handler throws exception."""
        # Create failing handler
        failing_handler = Mock(side_effect=ValueError("Handler error"))
        working_handler = Mock()

        self.manager._event_handlers[ProgressEventType.BATCH_STARTED] = [
            failing_handler,
            working_handler,
        ]

        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Test event",
            total_files=5,
        )

        # Handle event - should not raise exception
        self.manager._handle_progress_event(event)

        # Verify both handlers were called
        failing_handler.assert_called_once_with(event)
        working_handler.assert_called_once_with(event)

    @patch("spec_cli.ui.progress_manager.time.time")
    def test_handle_batch_started_with_progress_bar(self, mock_time):
        """Test batch started event handling with progress bar display."""
        mock_time.return_value = 1000.0
        self.manager.auto_display = True

        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Processing files",
            total_files=20,
        )

        self.manager._handle_batch_started(event)

        # Verify operation state was created
        operation_id = f"batch_{int(1000.0)}"
        assert operation_id in self.manager.progress_states

        state = self.manager.progress_states[operation_id]
        assert state.total_items == 20
        assert state.completed_items == 0
        assert state.start_time == 1000.0

        # Verify progress bar was started
        self.manager.progress_bar.start.assert_called_once()
        self.manager.progress_bar.add_task.assert_called_once_with(
            "Processing files", total=20
        )

    def test_handle_batch_started_without_auto_display(self):
        """Test batch started event handling without auto display."""
        self.manager.auto_display = False

        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Processing files",
            total_files=15,
        )

        self.manager._handle_batch_started(event)

        # Verify progress bar was not started
        self.manager.progress_bar.start.assert_not_called()
        self.manager.progress_bar.add_task.assert_not_called()

class TestProgressManagerOperations:
    """Test ProgressManager operation management."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("spec_cli.ui.progress_manager.SpecProgressBar"),
            patch("spec_cli.ui.progress_manager.SpinnerManager"),
            patch("spec_cli.ui.progress_manager.ErrorHandler"),
        ):
            self.manager = ProgressManager()

    @patch("spec_cli.ui.progress_manager.time.time")
    def test_start_indeterminate_operation(self, mock_time):
        """Test starting an indeterminate operation with spinner."""
        mock_time.return_value = 2000.0

        self.manager.start_indeterminate_operation("test_op", "Loading...")

        # Verify spinner was created and started
        self.manager.spinner_manager.create_spinner.assert_called_once_with(
            "test_op", "Loading..."
        )
        self.manager.spinner_manager.start_spinner.assert_called_once_with("test_op")

        # Verify operation tracking
        assert "test_op" in self.manager.active_operations
        assert self.manager.active_operations["test_op"] == "spinner:test_op"

        # Verify state tracking
        assert "test_op" in self.manager.progress_states
        state = self.manager.progress_states["test_op"]
        assert state.operation_id == "test_op"
        assert state.total_items == 0
        assert state.completed_items == 0
        assert state.start_time == 2000.0

    def test_finish_operation(self):
        """Test finishing an operation."""
        # Set up operation
        operation_id = "test_finish"
        self.manager.active_operations[operation_id] = "spinner:test_finish"
        self.manager.progress_states[operation_id] = ProgressState(
            operation_id=operation_id, total_items=0, completed_items=0
        )

        self.manager.finish_operation(operation_id)

        # Verify cleanup occurred
        assert operation_id not in self.manager.active_operations
        assert operation_id not in self.manager.progress_states

    def test_get_operation_state_exists(self):
        """Test getting operation state that exists."""
        operation_id = "existing_op"
        expected_state = ProgressState(
            operation_id=operation_id, total_items=100, completed_items=50
        )
        self.manager.progress_states[operation_id] = expected_state

        result = self.manager.get_operation_state(operation_id)

        assert result == expected_state

    def test_get_operation_state_not_exists(self):
        """Test getting operation state that doesn't exist."""
        result = self.manager.get_operation_state("nonexistent_op")

        assert result is None

    def test_cleanup_all_operations(self):
        """Test cleaning up all operations."""
        # Set up some operations
        self.manager.active_operations["op1"] = "spinner:op1"
        self.manager.active_operations["op2"] = "progress_bar:task1"
        self.manager.progress_states["op1"] = ProgressState("op1", 10, 5)
        self.manager.progress_states["op2"] = ProgressState("op2", 20, 10)

        self.manager.cleanup()

        # Verify all operations were cleaned up
        assert len(self.manager.active_operations) == 0
        assert len(self.manager.progress_states) == 0

        # Verify displays were stopped
        self.manager.spinner_manager.stop_all.assert_called_once()
        self.manager.progress_bar.stop.assert_called_once()

class TestProgressManagerEventHandlers:
    """Test specific progress event handler methods."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("spec_cli.ui.progress_manager.SpecProgressBar"),
            patch("spec_cli.ui.progress_manager.SpinnerManager"),
            patch("spec_cli.ui.progress_manager.ErrorHandler"),
        ):
            self.manager = ProgressManager()

    def test_add_event_handler(self):
        """Test adding custom event handler."""
        custom_handler = Mock()

        self.manager.add_event_handler(ProgressEventType.FILE_STARTED, custom_handler)

        # Verify handler was added
        handlers = self.manager._event_handlers[ProgressEventType.FILE_STARTED]
        assert custom_handler in handlers

    def test_remove_event_handler_success(self):
        """Test successfully removing event handler."""
        custom_handler = Mock()
        self.manager._event_handlers[ProgressEventType.FILE_COMPLETED] = [
            custom_handler
        ]

        result = self.manager.remove_event_handler(
            ProgressEventType.FILE_COMPLETED, custom_handler
        )

        assert result is True
        handlers = self.manager._event_handlers[ProgressEventType.FILE_COMPLETED]
        assert custom_handler not in handlers

    def test_remove_event_handler_not_found(self):
        """Test removing event handler that doesn't exist."""
        nonexistent_handler = Mock()

        result = self.manager.remove_event_handler(
            ProgressEventType.FILE_FAILED, nonexistent_handler
        )

        assert result is False

    def test_remove_event_handler_wrong_event_type(self):
        """Test removing handler from event type that doesn't exist."""
        # Remove all handlers for the event type
        if ProgressEventType.PROGRESS_UPDATE in self.manager._event_handlers:
            del self.manager._event_handlers[ProgressEventType.PROGRESS_UPDATE]

        nonexistent_handler = Mock()
        result = self.manager.remove_event_handler(
            ProgressEventType.PROGRESS_UPDATE, nonexistent_handler
        )

        assert result is False

class TestProgressManagerSingleton:
    """Test ProgressManagerSingleton functionality."""

    def setup_method(self):
        """Reset singleton before each test."""
        # Reset the singleton
        reset_progress_manager()

    def test_singleton_initialization(self):
        """Test singleton initialization."""
        singleton = ProgressManagerSingleton()

        assert singleton._progress_manager is None
        assert hasattr(singleton, "_lock")
        assert singleton._lock is not None

    @patch("spec_cli.ui.progress_manager.ProgressManager")
    def test_get_progress_manager_first_call(self, mock_progress_manager_class):
        """Test getting progress manager on first call."""
        mock_manager = Mock()
        mock_progress_manager_class.return_value = mock_manager

        singleton = ProgressManagerSingleton()
        result = singleton.get_progress_manager()

        assert result == mock_manager
        mock_progress_manager_class.assert_called_once()

    @patch("spec_cli.ui.progress_manager.ProgressManager")
    def test_get_progress_manager_subsequent_calls(self, mock_progress_manager_class):
        """Test getting progress manager on subsequent calls."""
        mock_manager = Mock()
        mock_progress_manager_class.return_value = mock_manager

        singleton = ProgressManagerSingleton()

        # First call
        result1 = singleton.get_progress_manager()
        # Second call
        result2 = singleton.get_progress_manager()

        assert result1 == result2
        # Constructor should only be called once
        mock_progress_manager_class.assert_called_once()

    def test_set_progress_manager(self):
        """Test setting custom progress manager."""
        custom_manager = Mock(spec=ProgressManager)
        singleton = ProgressManagerSingleton()

        singleton.set_progress_manager(custom_manager)

        result = singleton.get_progress_manager()
        assert result == custom_manager

    def test_reset_progress_manager(self):
        """Test resetting progress manager."""
        mock_manager = Mock(spec=ProgressManager)
        singleton = ProgressManagerSingleton()
        singleton._progress_manager = mock_manager

        singleton.reset()

        # Verify cleanup was called
        mock_manager.cleanup.assert_called_once()
        # Verify manager was reset
        assert singleton._progress_manager is None

class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_progress_manager()

    @patch("spec_cli.ui.progress_manager.ProgressManagerSingleton")
    def test_get_progress_manager_function(self, mock_singleton_class):
        """Test get_progress_manager convenience function."""
        mock_singleton = Mock()
        mock_manager = Mock(spec=ProgressManager)
        mock_singleton.get_progress_manager.return_value = mock_manager
        mock_singleton_class.return_value = mock_singleton

        result = get_progress_manager()

        assert result == mock_manager
        mock_singleton_class.assert_called_once()
        mock_singleton.get_progress_manager.assert_called_once()

    @patch("spec_cli.ui.progress_manager.ProgressManagerSingleton")
    def test_set_progress_manager_function(self, mock_singleton_class):
        """Test set_progress_manager convenience function."""
        mock_singleton = Mock()
        mock_singleton_class.return_value = mock_singleton
        custom_manager = Mock(spec=ProgressManager)

        set_progress_manager(custom_manager)

        mock_singleton_class.assert_called_once()
        mock_singleton.set_progress_manager.assert_called_once_with(custom_manager)

        """Test reset_progress_manager convenience function."""
        # Mock the ProgressManagerSingleton class itself
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton"
        ) as mock_singleton_class:
            mock_singleton = Mock()
            mock_singleton_class.return_value = mock_singleton

            reset_progress_manager()

            mock_singleton_class.assert_called_once()
            mock_singleton.reset.assert_called_once()
            # The actual class will be passed, not the mock

class TestProgressManagerPrivateMethods:
    """Test ProgressManager private helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("spec_cli.ui.progress_manager.SpecProgressBar"),
            patch("spec_cli.ui.progress_manager.SpinnerManager"),
            patch("spec_cli.ui.progress_manager.ErrorHandler"),
        ):
            self.manager = ProgressManager()

    def test_find_active_operation_with_operations(self):
        """Test finding active operation when operations exist."""
        self.manager.active_operations["op1"] = "spinner:op1"
        self.manager.active_operations["op2"] = "progress_bar:task1"

        result = self.manager._find_active_operation()

        # Should return the first operation (implementation detail)
        assert result in ["op1", "op2"]

    def test_find_active_operation_no_operations(self):
        """Test finding active operation when no operations exist."""
        result = self.manager._find_active_operation()

        assert result is None

    def test_cleanup_operation_progress_bar(self):
        """Test cleaning up operation with progress bar."""
        operation_id = "test_op"
        task_id = "task_123"
        self.manager.active_operations[operation_id] = f"progress_bar:{task_id}"
        self.manager.progress_states[operation_id] = ProgressState(operation_id, 10, 5)

        # Mock progress bar with no tasks after removal
        self.manager.progress_bar.tasks = []

        self.manager._cleanup_operation(operation_id)

        # Verify progress bar cleanup
        self.manager.progress_bar.remove_task.assert_called_once_with(task_id)
        self.manager.progress_bar.stop.assert_called_once()

        # Verify tracking cleanup
        assert operation_id not in self.manager.active_operations
        assert operation_id not in self.manager.progress_states

    def test_cleanup_operation_spinner(self):
        """Test cleaning up operation with spinner."""
        operation_id = "test_spinner_op"
        spinner_id = operation_id
        self.manager.active_operations[operation_id] = f"spinner:{spinner_id}"
        self.manager.progress_states[operation_id] = ProgressState(operation_id, 0, 0)

        self.manager._cleanup_operation(operation_id)

        # Verify spinner cleanup
        self.manager.spinner_manager.remove_spinner.assert_called_once_with(spinner_id)

        # Verify tracking cleanup
        assert operation_id not in self.manager.active_operations
        assert operation_id not in self.manager.progress_states
