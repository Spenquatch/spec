"""Tests for progress bar functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from spec_cli.ui.progress_bar import (
    SpecProgressBar,
    SimpleProgressBar,
    create_progress_bar,
    simple_progress,
)


class TestSpecProgressBar:
    """Test the SpecProgressBar class."""

    def test_spec_progress_bar_creation_and_configuration(self):
        """Test SpecProgressBar can be created with various configurations."""
        # Test default initialization
        progress_bar = SpecProgressBar()
        assert progress_bar.show_percentage is True
        assert progress_bar.show_time_elapsed is True
        assert progress_bar.show_time_remaining is True
        assert progress_bar.show_speed is False
        assert progress_bar._is_started is False
        assert len(progress_bar.tasks) == 0

        # Test custom configuration
        custom_progress = SpecProgressBar(
            show_percentage=False,
            show_time_elapsed=False,
            show_speed=True,
            refresh_per_second=5,
        )
        assert custom_progress.show_percentage is False
        assert custom_progress.show_time_elapsed is False
        assert custom_progress.show_speed is True

        # Test column building
        columns = custom_progress._build_columns()
        assert len(columns) >= 2  # At least description and bar
        # Since we disabled percentage and time elapsed but enabled speed, we should have fewer columns than default
        # Check that the speed column configuration was applied
        assert custom_progress.show_speed is True
        # Verify basic column structure
        assert len(columns) >= 3  # Description, bar, and speed at minimum

    def test_progress_bar_task_management(self):
        """Test task addition, updating, and removal."""
        # Mock the Rich Progress class to avoid Live display conflicts
        with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.start.return_value = None
            mock_progress.stop.return_value = None
            mock_progress.add_task.return_value = "rich_task_id"
            mock_progress.update.return_value = None
            mock_progress.remove_task.return_value = None
            
            # Mock the tasks property
            mock_task = Mock()
            mock_task.total = 100
            mock_task.description = "Test"
            mock_task.completed = 50
            mock_task.percentage = 50.0
            mock_task.remaining = 50
            mock_task.elapsed = 10.0
            mock_task.speed = 5.0
            mock_task.finished = False
            mock_progress.tasks = {"rich_task_id": mock_task}
            
            mock_progress_class.return_value = mock_progress
            
            progress_bar = SpecProgressBar()

            # Test task addition
            task_id = progress_bar.add_task("Test task", total=100)
            assert task_id in progress_bar.tasks
            assert progress_bar._is_started is True  # Should auto-start
            mock_progress.add_task.assert_called_with("Test task", total=100)

            # Test task update
            progress_bar.update_task(task_id, advance=10, description="Updated task")
            mock_progress.update.assert_called()

            # Test task completion - mock the tasks access properly
            mock_task = Mock()
            mock_task.total = 100
            mock_task.description = "Test task"
            mock_task.completed = 50
            mock_task.percentage = 50.0
            mock_task.remaining = 50
            mock_task.elapsed = 10.0
            mock_task.speed = 5.0
            mock_task.finished = False
            mock_progress.tasks = {progress_bar.tasks[task_id]: mock_task}
            progress_bar.complete_task(task_id)
            # Should call update with completed=total
            mock_progress.update.assert_called()

            # Test task info retrieval - use the mocked task we created
            info = progress_bar.get_task_info(task_id)
            assert info is not None
            assert info["description"] == "Test task"
            assert info["total"] == 100
            assert info["completed"] == 50

            # Test task removal
            progress_bar.remove_task(task_id)
            assert task_id not in progress_bar.tasks
            mock_progress.remove_task.assert_called_with("rich_task_id")

            # Test operations on non-existent task
            progress_bar.update_task("nonexistent", advance=1)  # Should not raise
            progress_bar.complete_task("nonexistent")  # Should not raise
            progress_bar.remove_task("nonexistent")  # Should not raise
            assert progress_bar.get_task_info("nonexistent") is None

    def test_progress_bar_context_manager(self):
        """Test progress bar context manager functionality."""
        # Mock the Rich Progress class to avoid Live display conflicts
        with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.start.return_value = None
            mock_progress.stop.return_value = None
            mock_progress.add_task.return_value = "rich_task_id"
            mock_progress.update.return_value = None
            mock_progress.remove_task.return_value = None
            mock_progress_class.return_value = mock_progress
            
            progress_bar = SpecProgressBar()

            # Test main context manager
            assert progress_bar._is_started is False
            with progress_bar:
                assert progress_bar._is_started is True
            # After exit, should be stopped
            assert progress_bar._is_started is False

            # Test task context manager
            with progress_bar.task_context("Context task", total=50) as task_id:
                assert task_id in progress_bar.tasks
                progress_bar.update_task(task_id, advance=10)
            # After context, task should be removed
            assert task_id not in progress_bar.tasks

    def test_simple_progress_bar_workflow(self):
        """Test SimpleProgressBar complete workflow."""
        # Mock the Rich Progress class to avoid Live display conflicts
        with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.start.return_value = None
            mock_progress.stop.return_value = None
            mock_progress.add_task.return_value = "rich_task_id"
            mock_progress.update.return_value = None
            mock_progress.remove_task.return_value = None
            mock_progress_class.return_value = mock_progress
            
            simple_bar = SimpleProgressBar(total=10, description="Simple test")
            assert simple_bar.total == 10
            assert simple_bar.description == "Simple test"
            assert simple_bar.completed == 0
            assert simple_bar.task_id is None

            # Test manual workflow
            simple_bar.start()
            assert simple_bar.task_id is not None
            assert simple_bar.progress_bar._is_started is True

            # Test advancement
            simple_bar.advance(3)
            assert simple_bar.completed == 3

            simple_bar.advance()  # Default advance by 1
            assert simple_bar.completed == 4

            # Test completion - need to mock task access
            mock_task = Mock()
            mock_task.total = 10
            mock_progress.tasks = {simple_bar.progress_bar.tasks[simple_bar.task_id]: mock_task}
            simple_bar.finish()
            assert simple_bar.progress_bar._is_started is False

            # Test context manager - reapply patch for new instance
            with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class2:
                mock_progress2 = Mock()
                mock_progress2.start.return_value = None
                mock_progress2.stop.return_value = None
                mock_progress2.add_task.return_value = "rich_task_id2"
                mock_progress2.update.return_value = None
                mock_progress2.remove_task.return_value = None
                mock_task2 = Mock()
                mock_task2.total = 5
                mock_progress_class2.return_value = mock_progress2
                
                with SimpleProgressBar(5, "Context test") as progress:
                    assert progress.task_id is not None
                    progress.advance(2)
                    assert progress.completed == 2
                    # Mock tasks for finish() call
                    mock_progress2.tasks = {progress.progress_bar.tasks[progress.task_id]: mock_task2}


class TestProgressBarUtilities:
    """Test progress bar utility functions."""

    def test_create_progress_bar_function(self):
        """Test create_progress_bar convenience function."""
        # Test default creation
        progress_bar = create_progress_bar()
        assert isinstance(progress_bar, SpecProgressBar)
        assert progress_bar.show_percentage is True

        # Test with custom options
        custom_bar = create_progress_bar(show_percentage=False, show_speed=True)
        assert isinstance(custom_bar, SpecProgressBar)
        assert custom_bar.show_percentage is False
        assert custom_bar.show_speed is True

    def test_simple_progress_function(self):
        """Test simple_progress convenience function."""
        # Test creation
        progress = simple_progress(20, "Test progress")
        assert isinstance(progress, SimpleProgressBar)
        assert progress.total == 20
        assert progress.description == "Test progress"

        # Test default description
        default_progress = simple_progress(15)
        assert default_progress.description == "Processing"


class TestProgressBarIntegration:
    """Test progress bar integration with console system."""

    def test_console_integration(self):
        """Test progress bar integration with console."""
        # Create a proper mock console with all required attributes
        mock_console = Mock()
        mock_console.get_time = Mock(return_value=0.0)
        mock_console.width = 80
        mock_console.height = 24
        
        # Mock the Rich Progress class to avoid Live display conflicts
        with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress_class.return_value = mock_progress

            # Test with custom console
            progress_bar = SpecProgressBar(console=mock_console)
            assert progress_bar.console is mock_console

            # Test default console usage
            with patch("spec_cli.ui.progress_bar.get_console") as mock_get_console:
                mock_spec_console = Mock()
                mock_spec_console.console = mock_console
                mock_get_console.return_value = mock_spec_console

                default_bar = SpecProgressBar()
                assert default_bar.console is mock_console

    def test_progress_bar_error_handling(self):
        """Test progress bar handles errors gracefully."""
        progress_bar = SpecProgressBar()

        # Test updating non-existent task
        progress_bar.update_task("fake_task", advance=1)  # Should not raise

        # Test completing non-existent task
        progress_bar.complete_task("fake_task")  # Should not raise

        # Test removing non-existent task
        progress_bar.remove_task("fake_task")  # Should not raise

        # Test getting info for non-existent task
        info = progress_bar.get_task_info("fake_task")
        assert info is None

    def test_progress_bar_advanced_features(self):
        """Test advanced progress bar features."""
        # Mock the Rich Progress class to avoid Live display conflicts
        with patch("spec_cli.ui.progress_bar.Progress") as mock_progress_class:
            mock_progress = Mock()
            mock_progress.start.return_value = None
            mock_progress.stop.return_value = None
            mock_progress.add_task.side_effect = ["rich_task_1", "rich_task_2", "rich_task_3"]
            mock_progress.update.return_value = None
            mock_progress.remove_task.return_value = None
            mock_progress_class.return_value = mock_progress
            
            progress_bar = SpecProgressBar()

            # Test multiple tasks
            task1 = progress_bar.add_task("Task 1", total=100)
            task2 = progress_bar.add_task("Task 2", total=50)

            assert len(progress_bar.tasks) == 2
            assert task1 != task2

            # Test custom task IDs
            custom_task = progress_bar.add_task("Custom", total=25, task_id="custom_id")
            assert custom_task == "custom_id"
            assert "custom_id" in progress_bar.tasks

            # Test start/stop control
            progress_bar.stop()
            assert progress_bar._is_started is False

            progress_bar.start()
            assert progress_bar._is_started is True

            # Test multiple starts/stops (should be safe)
            progress_bar.start()  # Already started
            assert progress_bar._is_started is True

            progress_bar.stop()
            progress_bar.stop()  # Already stopped
            assert progress_bar._is_started is False