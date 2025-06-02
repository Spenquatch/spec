"""Tests for spinner functionality."""

from unittest.mock import Mock, patch

import pytest
from rich.spinner import Spinner

from spec_cli.ui.spinner import (
    SpecSpinner,
    SpinnerManager,
    TimedSpinner,
    create_spinner,
    spinner_context,
    timed_spinner,
)


class TestSpecSpinner:
    """Test SpecSpinner class functionality."""

    def test_spec_spinner_initialization_defaults(self) -> None:
        """Test SpecSpinner initialization with defaults."""
        spinner = SpecSpinner()

        assert spinner.text == "Loading..."
        assert spinner.spinner_style == "dots"
        assert spinner.speed == 1.0
        assert spinner.console is not None
        assert isinstance(spinner.spinner, Spinner)
        assert spinner.live is None
        assert spinner._is_running is False

    def test_spec_spinner_initialization_custom(self) -> None:
        """Test SpecSpinner initialization with custom options."""
        mock_console = Mock()
        text = "Processing files..."
        spinner_style = "arc"
        speed = 2.0

        spinner = SpecSpinner(
            text=text, spinner_style=spinner_style, console=mock_console, speed=speed
        )

        assert spinner.text == text
        assert spinner.spinner_style == spinner_style
        assert spinner.console == mock_console
        assert spinner.speed == speed
        assert isinstance(spinner.spinner, Spinner)

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_start(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner start functionality."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = SpecSpinner("Test")
        spinner.start()

        assert spinner._is_running is True
        assert spinner.live == mock_live
        mock_live_class.assert_called_once()
        mock_live.start.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_start_already_running(self, mock_get_console: Mock) -> None:
        """Test spinner start when already running."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = SpecSpinner("Test")
        spinner._is_running = True  # Simulate already running

        with patch("spec_cli.ui.spinner.Live") as mock_live_class:
            spinner.start()

            # Should not create new Live instance
            mock_live_class.assert_not_called()

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_stop(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner stop functionality."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = SpecSpinner("Test")
        spinner.start()
        spinner.stop()

        assert spinner._is_running is False
        assert spinner.live is None
        mock_live.stop.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_stop_not_running(self, mock_get_console: Mock) -> None:
        """Test spinner stop when not running."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = SpecSpinner("Test")

        # Should not raise error when stopping non-running spinner
        spinner.stop()

        assert spinner._is_running is False
        assert spinner.live is None

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_update_text_running(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test updating spinner text while running."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = SpecSpinner("Original text")
        spinner.start()

        new_text = "Updated text"
        spinner.update_text(new_text)

        assert spinner.text == new_text
        mock_live.update.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_update_text_not_running(self, mock_get_console: Mock) -> None:
        """Test updating spinner text when not running."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = SpecSpinner("Original text")

        new_text = "Updated text"
        spinner.update_text(new_text)

        assert spinner.text == new_text
        # No Live instance to update, should work without error

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_context_manager(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner as context manager."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = SpecSpinner("Test")

        with spinner:
            assert spinner._is_running is True
            mock_live.start.assert_called_once()

        assert spinner._is_running is False
        mock_live.stop.assert_called_once()

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spec_spinner_context_manager_exception(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner context manager with exception."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = SpecSpinner("Test")

        with pytest.raises(ValueError):
            with spinner:
                assert spinner._is_running is True
                raise ValueError("Test exception")

        # Should still stop spinner after exception
        assert spinner._is_running is False
        mock_live.stop.assert_called_once()


class TestTimedSpinner:
    """Test TimedSpinner class functionality."""

    def test_timed_spinner_initialization(self) -> None:
        """Test TimedSpinner initialization."""
        timeout = 10.0
        spinner = TimedSpinner(timeout=timeout, text="Timed test")

        assert spinner.timeout == timeout
        assert spinner.text == "Timed test"
        assert spinner._timer is None
        assert isinstance(spinner, SpecSpinner)

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    @patch("threading.Timer")
    def test_timed_spinner_start(
        self,
        mock_timer_class: Mock,
        mock_get_console: Mock,
        mock_text: Mock,
        mock_live_class: Mock,
    ) -> None:
        """Test timed spinner start functionality."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = TimedSpinner(timeout=5.0)
        spinner.start()

        assert spinner._is_running is True
        mock_timer_class.assert_called_once_with(5.0, spinner._timeout_callback)
        mock_timer.start.assert_called_once()

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    @patch("threading.Timer")
    def test_timed_spinner_stop(
        self,
        mock_timer_class: Mock,
        mock_get_console: Mock,
        mock_text: Mock,
        mock_live_class: Mock,
    ) -> None:
        """Test timed spinner stop functionality."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = TimedSpinner(timeout=5.0)
        spinner.start()
        spinner.stop()

        assert spinner._is_running is False
        assert spinner._timer is None
        mock_timer.cancel.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_timed_spinner_timeout_callback(self, mock_get_console: Mock) -> None:
        """Test timed spinner timeout callback."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = TimedSpinner(timeout=0.1)  # Very short timeout

        # Mock the stop method to track calls
        with patch.object(spinner, "stop") as mock_stop:
            spinner._timeout_callback()
            mock_stop.assert_called_once()

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    @patch("threading.Timer")
    def test_timed_spinner_context_manager(
        self,
        mock_timer_class: Mock,
        mock_get_console: Mock,
        mock_text: Mock,
        mock_live_class: Mock,
    ) -> None:
        """Test timed spinner as context manager."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        spinner = TimedSpinner(timeout=5.0)

        with spinner:
            assert spinner._is_running is True
            mock_timer.start.assert_called_once()

        assert spinner._is_running is False
        mock_timer.cancel.assert_called_once()


class TestSpinnerManager:
    """Test SpinnerManager class functionality."""

    def test_spinner_manager_initialization(self) -> None:
        """Test SpinnerManager initialization."""
        manager = SpinnerManager()

        assert manager.console is not None
        assert manager.spinners == {}
        assert manager._active_spinner is None

    def test_spinner_manager_custom_console(self) -> None:
        """Test SpinnerManager with custom console."""
        mock_console = Mock()
        manager = SpinnerManager(console=mock_console)

        assert manager.console == mock_console

    @patch("spec_cli.ui.spinner.get_console")
    def test_create_spinner(self, mock_get_console: Mock) -> None:
        """Test creating spinner through manager."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        spinner_id = "test_spinner"
        text = "Test spinner"

        spinner = manager.create_spinner(spinner_id, text)

        assert isinstance(spinner, SpecSpinner)
        assert spinner.text == text
        assert spinner_id in manager.spinners
        assert manager.spinners[spinner_id] == spinner

    @patch("spec_cli.ui.spinner.get_console")
    def test_create_spinner_duplicate(self, mock_get_console: Mock) -> None:
        """Test creating spinner with duplicate ID."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        spinner_id = "test_spinner"

        # Create first spinner
        spinner1 = manager.create_spinner(spinner_id, "First")

        # Try to create duplicate
        spinner2 = manager.create_spinner(spinner_id, "Second")

        # Should return the existing spinner
        assert spinner1 == spinner2
        assert len(manager.spinners) == 1

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_start_spinner(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test starting spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        manager = SpinnerManager()
        spinner_id = "test_spinner"

        manager.create_spinner(spinner_id, "Test")
        result = manager.start_spinner(spinner_id)

        assert result is True
        assert manager._active_spinner == spinner_id
        mock_live.start.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_start_spinner_not_found(self, mock_get_console: Mock) -> None:
        """Test starting non-existent spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        result = manager.start_spinner("nonexistent")

        assert result is False
        assert manager._active_spinner is None

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_stop_spinner(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test stopping spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        manager = SpinnerManager()
        spinner_id = "test_spinner"

        manager.create_spinner(spinner_id, "Test")
        manager.start_spinner(spinner_id)
        result = manager.stop_spinner(spinner_id)

        assert result is True
        assert manager._active_spinner is None
        mock_live.stop.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_stop_spinner_not_found(self, mock_get_console: Mock) -> None:
        """Test stopping non-existent spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        result = manager.stop_spinner("nonexistent")

        assert result is False

    @patch("spec_cli.ui.spinner.get_console")
    def test_update_spinner_text(self, mock_get_console: Mock) -> None:
        """Test updating spinner text."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        spinner_id = "test_spinner"
        new_text = "Updated text"

        manager.create_spinner(spinner_id, "Original text")
        result = manager.update_spinner_text(spinner_id, new_text)

        assert result is True
        assert manager.spinners[spinner_id].text == new_text

    @patch("spec_cli.ui.spinner.get_console")
    def test_update_spinner_text_not_found(self, mock_get_console: Mock) -> None:
        """Test updating text for non-existent spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        result = manager.update_spinner_text("nonexistent", "Text")

        assert result is False

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_remove_spinner(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test removing spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        manager = SpinnerManager()
        spinner_id = "test_spinner"

        manager.create_spinner(spinner_id, "Test")
        manager.start_spinner(spinner_id)
        result = manager.remove_spinner(spinner_id)

        assert result is True
        assert spinner_id not in manager.spinners
        assert manager._active_spinner is None
        mock_live.stop.assert_called_once()

    @patch("spec_cli.ui.spinner.get_console")
    def test_remove_spinner_not_found(self, mock_get_console: Mock) -> None:
        """Test removing non-existent spinner."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()
        result = manager.remove_spinner("nonexistent")

        assert result is False

    @patch("spec_cli.ui.spinner.get_console")
    def test_stop_all_spinners(self, mock_get_console: Mock) -> None:
        """Test stopping all spinners."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()

        # Create multiple spinners
        manager.create_spinner("spinner1", "First")
        manager.create_spinner("spinner2", "Second")
        manager.create_spinner("spinner3", "Third")

        manager.stop_all()

        # All spinners should still exist but be stopped
        assert len(manager.spinners) == 3
        for spinner in manager.spinners.values():
            assert not spinner._is_running

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spinner_context_manager(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner context manager."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        manager = SpinnerManager()
        spinner_id = "context_spinner"
        text = "Context text"

        with manager.spinner_context(spinner_id, text) as spinner:
            assert isinstance(spinner, SpecSpinner)
            assert spinner.text == text
            assert spinner_id in manager.spinners
            assert manager._active_spinner == spinner_id
            mock_live.start.assert_called_once()

        # Spinner should be removed after context
        assert spinner_id not in manager.spinners
        assert manager._active_spinner is None
        mock_live.stop.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("spec_cli.ui.spinner.get_console")
    def test_create_spinner_function(self, mock_get_console: Mock) -> None:
        """Test create_spinner convenience function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        text = "Test spinner"
        spinner = create_spinner(text, spinner_style="arc")

        assert isinstance(spinner, SpecSpinner)
        assert spinner.text == text
        assert spinner.spinner_style == "arc"

    @patch("spec_cli.ui.spinner.get_console")
    def test_create_spinner_function_defaults(self, mock_get_console: Mock) -> None:
        """Test create_spinner with defaults."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = create_spinner()

        assert isinstance(spinner, SpecSpinner)
        assert spinner.text == "Loading..."

    @patch("spec_cli.ui.spinner.get_console")
    def test_timed_spinner_function(self, mock_get_console: Mock) -> None:
        """Test timed_spinner convenience function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        text = "Timed spinner"
        timeout = 15.0
        spinner = timed_spinner(text, timeout, spinner_style="arc")

        assert isinstance(spinner, TimedSpinner)
        assert spinner.text == text
        assert spinner.timeout == timeout
        assert spinner.spinner_style == "arc"

    @patch("spec_cli.ui.spinner.get_console")
    def test_timed_spinner_function_defaults(self, mock_get_console: Mock) -> None:
        """Test timed_spinner with defaults."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        spinner = timed_spinner()

        assert isinstance(spinner, TimedSpinner)
        assert spinner.text == "Loading..."
        assert spinner.timeout == 30.0

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spinner_context_function(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner_context convenience function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        text = "Context spinner"

        with spinner_context(text, spinner_style="arc") as spinner:
            assert isinstance(spinner, SpecSpinner)
            assert spinner.text == text
            assert spinner.spinner_style == "arc"
            assert spinner._is_running is True
            mock_live.start.assert_called_once()

        assert spinner._is_running is False
        mock_live.stop.assert_called_once()

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spinner_context_function_defaults(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner_context with defaults."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        with spinner_context() as spinner:
            assert isinstance(spinner, SpecSpinner)
            assert spinner.text == "Loading..."
            assert spinner._is_running is True

        assert spinner._is_running is False

    @patch("spec_cli.ui.spinner.Live")
    @patch("spec_cli.ui.spinner.Text")
    @patch("spec_cli.ui.spinner.get_console")
    def test_spinner_context_function_exception(
        self, mock_get_console: Mock, mock_text: Mock, mock_live_class: Mock
    ) -> None:
        """Test spinner_context with exception."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        mock_text.from_markup.return_value = "markup_text"
        mock_text.assemble.return_value = "assembled_display"

        with pytest.raises(RuntimeError):
            with spinner_context("Test") as spinner:
                assert spinner._is_running is True
                raise RuntimeError("Test error")

        # Spinner should still be stopped after exception
        assert spinner._is_running is False
        mock_live.stop.assert_called_once()


class TestSpinnerIntegration:
    """Test spinner integration scenarios."""

    @patch("spec_cli.ui.spinner.get_console")
    def test_multiple_spinners_basic(self, mock_get_console: Mock) -> None:
        """Test basic multiple spinners functionality."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()

        # Create multiple spinners
        manager.create_spinner("loading", "Loading files...")
        manager.create_spinner("processing", "Processing data...")
        manager.create_spinner("saving", "Saving results...")

        # Test text updates
        manager.update_spinner_text("loading", "Loading 50% complete...")
        assert manager.spinners["loading"].text == "Loading 50% complete..."

        # Test removal
        manager.remove_spinner("processing")
        assert "processing" not in manager.spinners
        assert len(manager.spinners) == 2

    @patch("spec_cli.ui.spinner.get_console")
    @patch("threading.Timer")
    def test_timed_spinner_timeout_simulation(
        self, mock_timer_class: Mock, mock_get_console: Mock
    ) -> None:
        """Test timed spinner timeout behavior simulation."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer

        spinner = TimedSpinner(timeout=1.0, text="Test timeout")

        # Simulate timeout by calling the callback directly
        spinner._timeout_callback()

        # Should handle timeout gracefully
        assert not spinner._is_running

    @patch("spec_cli.ui.spinner.get_console")
    def test_spinner_state_management(self, mock_get_console: Mock) -> None:
        """Test spinner state management."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        # Test individual spinner state
        spinner = SpecSpinner("Test spinner")
        assert not spinner._is_running

        # Test manager state
        manager = SpinnerManager()
        assert manager._active_spinner is None
        assert len(manager.spinners) == 0

        # Create and track state
        manager.create_spinner("test", "Test")
        assert len(manager.spinners) == 1
        assert "test" in manager.spinners

    @patch("spec_cli.ui.spinner.get_console")
    def test_error_handling(self, mock_get_console: Mock) -> None:
        """Test error handling in spinner operations."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        manager = SpinnerManager()

        # Test operations on non-existent spinners
        assert not manager.start_spinner("nonexistent")
        assert not manager.stop_spinner("nonexistent")
        assert not manager.update_spinner_text("nonexistent", "text")
        assert not manager.remove_spinner("nonexistent")

        # Should not raise errors, just return False
        manager.stop_all()  # Should work even with no spinners
