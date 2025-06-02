"""Tests for progress manager functionality."""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.file_processing.progress_events import ProcessingStage, ProgressEvent, ProgressEventType
from spec_cli.ui.progress_manager import (
    ProgressManager,
    ProgressState,
    get_progress_manager,
    reset_progress_manager,
    set_progress_manager,
)


class TestProgressState:
    """Test ProgressState dataclass functionality."""

    def test_progress_state_initialization(self):
        """Test ProgressState initialization."""
        operation_id = "test_op"
        total_items = 10
        completed_items = 3
        
        state = ProgressState(
            operation_id=operation_id,
            total_items=total_items,
            completed_items=completed_items
        )
        
        assert state.operation_id == operation_id
        assert state.total_items == total_items
        assert state.completed_items == completed_items
        assert state.current_item is None
        assert state.stage is None
        assert state.start_time is None
        assert state.estimated_completion is None

    def test_progress_state_with_optional_fields(self):
        """Test ProgressState with optional fields."""
        current_item = "file.txt"
        stage = ProcessingStage.CHANGE_DETECTION
        start_time = time.time()
        estimated_completion = start_time + 100
        
        state = ProgressState(
            operation_id="test",
            total_items=5,
            completed_items=2,
            current_item=current_item,
            stage=stage,
            start_time=start_time,
            estimated_completion=estimated_completion
        )
        
        assert state.current_item == current_item
        assert state.stage == stage
        assert state.start_time == start_time
        assert state.estimated_completion == estimated_completion

    def test_progress_percentage_normal(self):
        """Test progress percentage calculation."""
        state = ProgressState(
            operation_id="test",
            total_items=10,
            completed_items=3
        )
        
        assert state.progress_percentage == 0.3

    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total."""
        state = ProgressState(
            operation_id="test",
            total_items=0,
            completed_items=0
        )
        
        assert state.progress_percentage == 0.0

    def test_progress_percentage_complete(self):
        """Test progress percentage when complete."""
        state = ProgressState(
            operation_id="test",
            total_items=5,
            completed_items=5
        )
        
        assert state.progress_percentage == 1.0

    def test_elapsed_time_no_start(self):
        """Test elapsed time when no start time set."""
        state = ProgressState(
            operation_id="test",
            total_items=5,
            completed_items=2
        )
        
        assert state.elapsed_time is None

    @patch('time.time')
    def test_elapsed_time_with_start(self, mock_time):
        """Test elapsed time calculation."""
        start_time = 1000.0
        current_time = 1010.5
        
        mock_time.return_value = current_time
        
        state = ProgressState(
            operation_id="test",
            total_items=5,
            completed_items=2,
            start_time=start_time
        )
        
        assert state.elapsed_time == 10.5


class TestProgressManager:
    """Test ProgressManager class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global state
        reset_progress_manager()

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_progress_manager_initialization_defaults(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test ProgressManager initialization with defaults."""
        mock_reporter_instance = Mock()
        mock_reporter.return_value = mock_reporter_instance
        
        manager = ProgressManager()
        
        assert manager.progress_reporter == mock_reporter
        assert manager.auto_display is True
        assert manager.progress_states == {}
        assert manager.active_operations == {}
        mock_reporter.add_listener.assert_called_once()

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    def test_progress_manager_initialization_custom(self, mock_spinner_manager, mock_progress_bar):
        """Test ProgressManager initialization with custom parameters."""
        custom_reporter = Mock()
        auto_display = False
        
        manager = ProgressManager(
            progress_reporter_instance=custom_reporter,
            auto_display=auto_display
        )
        
        assert manager.progress_reporter == custom_reporter
        assert manager.auto_display is False
        custom_reporter.add_listener.assert_called_once()

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_setup_event_handling(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test event handling setup."""
        manager = ProgressManager()
        
        # Check that event handlers are set up
        assert ProgressEventType.BATCH_STARTED in manager._event_handlers
        assert ProgressEventType.BATCH_COMPLETED in manager._event_handlers
        assert ProgressEventType.FILE_STARTED in manager._event_handlers
        
        # Each event type should have at least one handler
        for event_type in manager._event_handlers:
            assert len(manager._event_handlers[event_type]) >= 1

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_handle_progress_event(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test progress event handling."""
        manager = ProgressManager()
        
        # Create mock handler
        mock_handler = Mock()
        manager._event_handlers[ProgressEventType.BATCH_STARTED] = [mock_handler]
        
        # Create test event
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Test batch started"
        )
        
        # Handle the event
        manager._handle_progress_event(event)
        
        # Verify handler was called
        mock_handler.assert_called_once_with(event)

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_handle_progress_event_handler_exception(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test progress event handling with handler exception."""
        manager = ProgressManager()
        
        # Create mock handler that raises exception
        mock_handler = Mock()
        mock_handler.side_effect = ValueError("Handler error")
        manager._event_handlers[ProgressEventType.BATCH_STARTED] = [mock_handler]
        
        # Create test event
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Test batch started"
        )
        
        # Should not raise exception
        manager._handle_progress_event(event)
        
        # Handler should have been called
        mock_handler.assert_called_once_with(event)

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('time.time')
    def test_handle_batch_started(self, mock_time, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test batch started event handling."""
        mock_time.return_value = 1000.0
        mock_progress_bar_instance = Mock()
        mock_progress_bar.return_value = mock_progress_bar_instance
        
        manager = ProgressManager()
        
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Processing files",
            total_files=5
        )
        
        manager._handle_batch_started(event)
        
        # Check that operation state was created
        assert len(manager.progress_states) == 1
        operation_id = next(iter(manager.progress_states.keys()))
        state = manager.progress_states[operation_id]
        
        assert state.total_items == 5
        assert state.completed_items == 0
        assert state.start_time == 1000.0
        
        # Check that progress bar was started
        mock_progress_bar_instance.start.assert_called_once()
        mock_progress_bar_instance.add_task.assert_called_once_with(
            "Processing files", total=5
        )

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('spec_cli.ui.progress_manager.get_console')
    def test_handle_batch_completed(self, mock_get_console, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test batch completed event handling."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        manager = ProgressManager()
        
        # Set up initial state
        operation_id = "test_batch_1000"
        state = ProgressState(operation_id=operation_id, total_items=5, completed_items=3)
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "progress_bar:task1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_COMPLETED,
            message="Batch completed successfully"
        )
        
        manager._handle_batch_completed(event)
        
        # Check completion
        mock_console.print_status.assert_called_once_with(
            "Batch completed successfully", "success"
        )

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('spec_cli.ui.progress_manager.get_console')
    def test_handle_batch_failed(self, mock_get_console, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test batch failed event handling."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        
        manager = ProgressManager()
        
        # Set up initial state
        operation_id = "test_batch_1000"
        manager.active_operations[operation_id] = "progress_bar:task1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_FAILED,
            message="Batch failed"
        )
        
        manager._handle_batch_failed(event)
        
        # Check error message
        mock_console.print_status.assert_called_once_with(
            "Batch failed", "error"
        )

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_handle_file_started(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test file started event handling."""
        manager = ProgressManager()
        
        # Set up initial state
        operation_id = "test_batch_1000"
        state = ProgressState(operation_id=operation_id, total_items=5, completed_items=2)
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "progress_bar:task1"
        
        file_path = Path("/test/file.txt")
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED,
            file_path=file_path,
            message="Processing file"
        )
        
        with patch.object(manager, '_update_progress_display') as mock_update:
            manager._handle_file_started(event)
            
            # Check that current item was updated
            assert state.current_item == str(file_path)
            
            # Check that display was updated
            mock_update.assert_called_once_with(operation_id, event)

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_handle_file_completed(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test file completed event handling."""
        manager = ProgressManager()
        
        # Set up initial state
        operation_id = "test_batch_1000"
        state = ProgressState(operation_id=operation_id, total_items=5, completed_items=2)
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "progress_bar:task1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_COMPLETED,
            processed_files=3,
            message="File completed"
        )
        
        with patch.object(manager, '_update_progress_display') as mock_update:
            manager._handle_file_completed(event)
            
            # Check that completed items was updated
            assert state.completed_items == 3
            
            # Check that display was updated
            mock_update.assert_called_once_with(operation_id, event)

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_handle_stage_started(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test stage started event handling."""
        manager = ProgressManager()
        
        # Set up initial state
        operation_id = "test_batch_1000"
        state = ProgressState(operation_id=operation_id, total_items=5, completed_items=2)
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "spinner:spinner1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.STAGE_STARTED,
            stage=ProcessingStage.CONTENT_GENERATION,
            message="Content generation stage started"
        )
        
        with patch.object(manager, '_update_operation_text') as mock_update_text:
            manager._handle_stage_started(event)
            
            # Check that stage was updated
            assert state.stage == ProcessingStage.CONTENT_GENERATION
            
            # Check that operation text was updated
            mock_update_text.assert_called_once_with(operation_id, "Stage: content_generation")

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_update_progress_display_progress_bar(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test updating progress bar display."""
        mock_progress_bar_instance = Mock()
        mock_progress_bar.return_value = mock_progress_bar_instance
        
        manager = ProgressManager()
        
        # Set up state
        operation_id = "test_op"
        state = ProgressState(
            operation_id=operation_id,
            total_items=5,
            completed_items=3,
            current_item="file.txt"
        )
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "progress_bar:task1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            message="Processing"
        )
        
        manager._update_progress_display(operation_id, event)
        
        # Check that progress bar was updated
        mock_progress_bar_instance.update_task.assert_called_once_with(
            "task1",
            completed=3,
            description="Processing: file.txt"
        )

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_update_progress_display_spinner(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test updating spinner display."""
        mock_spinner_manager_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_manager_instance
        
        manager = ProgressManager()
        manager.spinner_manager = mock_spinner_manager_instance
        
        # Set up state
        operation_id = "test_op"
        state = ProgressState(
            operation_id=operation_id,
            total_items=0,
            completed_items=0,
            current_item="file.txt"
        )
        manager.progress_states[operation_id] = state
        manager.active_operations[operation_id] = "spinner:spinner1"
        
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            message="Processing"
        )
        
        manager._update_progress_display(operation_id, event)
        
        # Check that spinner was updated
        mock_spinner_manager_instance.update_spinner_text.assert_called_once_with(
            "spinner1", "Processing: file.txt"
        )

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_find_active_operation(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test finding active operation."""
        manager = ProgressManager()
        
        # No active operations
        assert manager._find_active_operation() is None
        
        # Add operations
        manager.active_operations["op1"] = "progress_bar:task1"
        manager.active_operations["op2"] = "spinner:spinner1"
        
        # Should return first operation
        active_op = manager._find_active_operation()
        assert active_op in ["op1", "op2"]  # Order not guaranteed in dict iteration

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_cleanup_operation_progress_bar(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test cleaning up progress bar operation."""
        mock_progress_bar_instance = Mock()
        mock_progress_bar_instance.tasks = []  # Empty tasks after removal
        mock_progress_bar.return_value = mock_progress_bar_instance
        
        manager = ProgressManager()
        
        # Set up operation
        operation_id = "test_op"
        manager.active_operations[operation_id] = "progress_bar:task1"
        manager.progress_states[operation_id] = ProgressState(
            operation_id=operation_id, total_items=5, completed_items=3
        )
        
        manager._cleanup_operation(operation_id)
        
        # Check cleanup
        assert operation_id not in manager.active_operations
        assert operation_id not in manager.progress_states
        mock_progress_bar_instance.remove_task.assert_called_once_with("task1")
        mock_progress_bar_instance.stop.assert_called_once()

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_cleanup_operation_spinner(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test cleaning up spinner operation."""
        mock_spinner_manager_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_manager_instance
        
        manager = ProgressManager()
        manager.spinner_manager = mock_spinner_manager_instance
        
        # Set up operation
        operation_id = "test_op"
        manager.active_operations[operation_id] = "spinner:spinner1"
        manager.progress_states[operation_id] = ProgressState(
            operation_id=operation_id, total_items=0, completed_items=0
        )
        
        manager._cleanup_operation(operation_id)
        
        # Check cleanup
        assert operation_id not in manager.active_operations
        assert operation_id not in manager.progress_states
        mock_spinner_manager_instance.remove_spinner.assert_called_once_with("spinner1")

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('time.time')
    def test_start_indeterminate_operation(self, mock_time, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test starting indeterminate operation."""
        mock_time.return_value = 1000.0
        mock_spinner_manager_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_manager_instance
        
        manager = ProgressManager()
        manager.spinner_manager = mock_spinner_manager_instance
        
        operation_id = "test_spinner"
        message = "Processing files..."
        
        manager.start_indeterminate_operation(operation_id, message)
        
        # Check that spinner was created and started
        mock_spinner_manager_instance.create_spinner.assert_called_once_with(operation_id, message)
        mock_spinner_manager_instance.start_spinner.assert_called_once_with(operation_id)
        
        # Check tracking
        assert operation_id in manager.active_operations
        assert manager.active_operations[operation_id] == f"spinner:{operation_id}"
        
        assert operation_id in manager.progress_states
        state = manager.progress_states[operation_id]
        assert state.total_items == 0
        assert state.completed_items == 0
        assert state.start_time == 1000.0

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_finish_operation(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test finishing operation."""
        manager = ProgressManager()
        
        operation_id = "test_op"
        manager.active_operations[operation_id] = "spinner:spinner1"
        manager.progress_states[operation_id] = ProgressState(
            operation_id=operation_id, total_items=0, completed_items=0
        )
        
        with patch.object(manager, '_cleanup_operation') as mock_cleanup:
            manager.finish_operation(operation_id)
            mock_cleanup.assert_called_once_with(operation_id)

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_get_operation_state(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test getting operation state."""
        manager = ProgressManager()
        
        # Non-existent operation
        assert manager.get_operation_state("nonexistent") is None
        
        # Existing operation
        operation_id = "test_op"
        state = ProgressState(operation_id=operation_id, total_items=5, completed_items=3)
        manager.progress_states[operation_id] = state
        
        retrieved_state = manager.get_operation_state(operation_id)
        assert retrieved_state == state

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_add_event_handler(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test adding event handler."""
        manager = ProgressManager()
        
        # Custom handler
        custom_handler = Mock()
        
        # Add to existing event type
        initial_count = len(manager._event_handlers[ProgressEventType.BATCH_STARTED])
        manager.add_event_handler(ProgressEventType.BATCH_STARTED, custom_handler)
        
        assert len(manager._event_handlers[ProgressEventType.BATCH_STARTED]) == initial_count + 1
        assert custom_handler in manager._event_handlers[ProgressEventType.BATCH_STARTED]

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_remove_event_handler(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test removing event handler."""
        manager = ProgressManager()
        
        # Add custom handler first
        custom_handler = Mock()
        manager.add_event_handler(ProgressEventType.BATCH_STARTED, custom_handler)
        
        # Remove it
        result = manager.remove_event_handler(ProgressEventType.BATCH_STARTED, custom_handler)
        assert result is True
        assert custom_handler not in manager._event_handlers[ProgressEventType.BATCH_STARTED]
        
        # Try to remove non-existent handler
        result = manager.remove_event_handler(ProgressEventType.BATCH_STARTED, custom_handler)
        assert result is False

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_cleanup(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test cleanup functionality."""
        mock_spinner_manager_instance = Mock()
        mock_progress_bar_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_manager_instance
        mock_progress_bar.return_value = mock_progress_bar_instance
        
        manager = ProgressManager()
        manager.spinner_manager = mock_spinner_manager_instance
        manager.progress_bar = mock_progress_bar_instance
        
        # Add some tracking data
        manager.active_operations["op1"] = "spinner:spinner1"
        manager.progress_states["op1"] = ProgressState(
            operation_id="op1", total_items=5, completed_items=3
        )
        
        manager.cleanup()
        
        # Check that displays were stopped
        mock_spinner_manager_instance.stop_all.assert_called_once()
        mock_progress_bar_instance.stop.assert_called_once()
        
        # Check that tracking was cleared
        assert len(manager.active_operations) == 0
        assert len(manager.progress_states) == 0


class TestGlobalProgressManager:
    """Test global progress manager functions."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_progress_manager()

    @patch('spec_cli.ui.progress_manager.ProgressManager')
    def test_get_progress_manager_creates_instance(self, mock_progress_manager_class):
        """Test that get_progress_manager creates instance if none exists."""
        mock_instance = Mock()
        mock_progress_manager_class.return_value = mock_instance
        
        manager = get_progress_manager()
        
        assert manager == mock_instance
        mock_progress_manager_class.assert_called_once()

    @patch('spec_cli.ui.progress_manager.ProgressManager')
    def test_get_progress_manager_returns_existing(self, mock_progress_manager_class):
        """Test that get_progress_manager returns existing instance."""
        mock_instance = Mock()
        mock_progress_manager_class.return_value = mock_instance
        
        # First call creates instance
        manager1 = get_progress_manager()
        
        # Second call returns same instance
        manager2 = get_progress_manager()
        
        assert manager1 == manager2
        # Should only be called once
        mock_progress_manager_class.assert_called_once()

    def test_set_progress_manager(self):
        """Test setting global progress manager."""
        custom_manager = Mock()
        
        set_progress_manager(custom_manager)
        
        manager = get_progress_manager()
        assert manager == custom_manager

    @patch('spec_cli.ui.progress_manager._progress_manager')
    def test_reset_progress_manager_with_existing(self, mock_global_manager):
        """Test resetting progress manager when one exists."""
        mock_manager = Mock()
        mock_global_manager = mock_manager
        
        with patch('spec_cli.ui.progress_manager._progress_manager', mock_manager):
            reset_progress_manager()
            mock_manager.cleanup.assert_called_once()

    def test_reset_progress_manager_no_existing(self):
        """Test resetting progress manager when none exists."""
        # Should not raise error
        reset_progress_manager()
        
        # Next call should create new instance
        manager = get_progress_manager()
        assert manager is not None


class TestProgressManagerIntegration:
    """Test progress manager integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_progress_manager()

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('time.time')
    def test_complete_batch_workflow(self, mock_time, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test complete batch processing workflow."""
        mock_time.return_value = 1000.0
        mock_progress_bar_instance = Mock()
        mock_progress_bar_instance.tasks = []
        mock_progress_bar.return_value = mock_progress_bar_instance
        
        manager = ProgressManager()
        
        # 1. Start batch
        batch_start_event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Processing 3 files",
            total_files=3
        )
        manager._handle_batch_started(batch_start_event)
        
        assert len(manager.progress_states) == 1
        assert len(manager.active_operations) == 1
        
        # 2. Process files
        for i in range(3):
            file_start_event = ProgressEvent(
                event_type=ProgressEventType.FILE_STARTED,
                file_path=Path(f"file{i}.txt"),
                message=f"Processing file {i}"
            )
            manager._handle_file_started(file_start_event)
            
            file_complete_event = ProgressEvent(
                event_type=ProgressEventType.FILE_COMPLETED,
                processed_files=i + 1,
                message=f"Completed file {i}"
            )
            manager._handle_file_completed(file_complete_event)
        
        # 3. Complete batch
        with patch('spec_cli.ui.progress_manager.get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            batch_complete_event = ProgressEvent(
                event_type=ProgressEventType.BATCH_COMPLETED,
                message="All files processed"
            )
            manager._handle_batch_completed(batch_complete_event)
            
            # Should show success message
            mock_console.print_status.assert_called_with("All files processed", "success")
        
        # Operations should be cleaned up
        assert len(manager.progress_states) == 0
        assert len(manager.active_operations) == 0

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    def test_custom_event_handlers(self, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test custom event handlers."""
        manager = ProgressManager()
        
        # Add custom handlers
        batch_started_calls = []
        file_completed_calls = []
        
        def custom_batch_handler(event):
            batch_started_calls.append(event)
        
        def custom_file_handler(event):
            file_completed_calls.append(event)
        
        manager.add_event_handler(ProgressEventType.BATCH_STARTED, custom_batch_handler)
        manager.add_event_handler(ProgressEventType.FILE_COMPLETED, custom_file_handler)
        
        # Trigger events
        batch_event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            message="Custom batch",
            total_files=2
        )
        manager._handle_progress_event(batch_event)
        
        file_event = ProgressEvent(
            event_type=ProgressEventType.FILE_COMPLETED,
            message="Custom file complete"
        )
        manager._handle_progress_event(file_event)
        
        # Check custom handlers were called
        assert len(batch_started_calls) == 1
        assert batch_started_calls[0] == batch_event
        
        assert len(file_completed_calls) == 1
        assert file_completed_calls[0] == file_event

    @patch('spec_cli.ui.progress_manager.SpecProgressBar')
    @patch('spec_cli.ui.progress_manager.SpinnerManager')
    @patch('spec_cli.ui.progress_manager.progress_reporter')
    @patch('time.time')
    def test_indeterminate_operation_workflow(self, mock_time, mock_reporter, mock_spinner_manager, mock_progress_bar):
        """Test indeterminate operation workflow."""
        mock_time.return_value = 1000.0
        mock_spinner_manager_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_manager_instance
        
        manager = ProgressManager()
        manager.spinner_manager = mock_spinner_manager_instance
        
        # Start indeterminate operation
        operation_id = "loading_config"
        manager.start_indeterminate_operation(operation_id, "Loading configuration...")
        
        # Check that spinner was set up
        mock_spinner_manager_instance.create_spinner.assert_called_with(
            operation_id, "Loading configuration..."
        )
        mock_spinner_manager_instance.start_spinner.assert_called_with(operation_id)
        
        # Check tracking
        assert operation_id in manager.progress_states
        assert operation_id in manager.active_operations
        
        # Get state
        state = manager.get_operation_state(operation_id)
        assert state is not None
        assert state.total_items == 0
        assert state.start_time == 1000.0
        
        # Finish operation
        manager.finish_operation(operation_id)
        
        # Should be cleaned up
        assert operation_id not in manager.progress_states
        assert operation_id not in manager.active_operations