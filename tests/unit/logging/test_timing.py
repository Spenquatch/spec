import time
from unittest.mock import MagicMock

import pytest

from spec_cli.logging.timing import TimingContext, TimingResult, timer


class TestTimingContext:
    """Test the TimingContext class functionality."""

    def test_timing_context_collects_operation_results(self) -> None:
        """Test that TimingContext collects timing results correctly."""
        context = TimingContext()

        with context.time_operation("test_op1"):
            time.sleep(0.001)  # 1ms

        with context.time_operation("test_op2"):
            time.sleep(0.002)  # 2ms

        assert len(context.results) == 2
        assert context.results[0].operation == "test_op1"
        assert context.results[1].operation == "test_op2"
        assert all(result.success for result in context.results)
        assert all(result.duration_ms > 0 for result in context.results)

    def test_timing_context_handles_failed_operations(self) -> None:
        """Test that TimingContext handles failed operations correctly."""
        context = TimingContext()

        # Successful operation
        with context.time_operation("success_op"):
            pass

        # Failed operation
        with pytest.raises(ValueError):
            with context.time_operation("failed_op"):
                raise ValueError("Test error")

        assert len(context.results) == 2
        assert context.results[0].success is True
        assert context.results[1].success is False
        assert context.results[1].error == "Test error"

    def test_timing_context_calculates_summary_statistics(self) -> None:
        """Test that TimingContext calculates summary statistics correctly."""
        context = TimingContext()

        # Add some results manually for predictable testing
        context.results = [
            TimingResult("op1", 10.0, 0.0, 0.01, True),
            TimingResult("op2", 20.0, 0.0, 0.02, True),
            TimingResult("op3", 30.0, 0.0, 0.03, False, "error"),
        ]

        summary = context.get_summary()

        assert summary["total_operations"] == 3
        assert summary["successful_operations"] == 2
        assert summary["failed_operations"] == 1
        assert summary["total_time_ms"] == 60.0
        assert summary["average_time_ms"] == 20.0
        assert summary["fastest_operation_ms"] == 10.0
        assert summary["slowest_operation_ms"] == 30.0

    def test_timing_context_identifies_slowest_operations(self) -> None:
        """Test that TimingContext identifies slowest operations correctly."""
        context = TimingContext()

        # Add results with different durations
        context.results = [
            TimingResult("fast_op", 5.0, 0.0, 0.005, True),
            TimingResult("slow_op", 50.0, 0.0, 0.05, True),
            TimingResult("medium_op", 25.0, 0.0, 0.025, True),
        ]

        slowest = context.get_slowest_operations(limit=2)

        assert len(slowest) == 2
        assert slowest[0].operation == "slow_op"
        assert slowest[1].operation == "medium_op"

    def test_timing_context_empty_results_handling(self) -> None:
        """Test that TimingContext handles empty results correctly."""
        context = TimingContext()

        summary = context.get_summary()
        assert summary == {}

        slowest = context.get_slowest_operations()
        assert slowest == []

    def test_timing_context_cleans_up_active_operations(self) -> None:
        """Test that TimingContext cleans up active operations properly."""
        context = TimingContext()

        # Normal completion
        with context.time_operation("normal_op"):
            assert "normal_op" in context._active_operations

        assert "normal_op" not in context._active_operations

        # Exception handling
        with pytest.raises(ValueError):
            with context.time_operation("error_op"):
                assert "error_op" in context._active_operations
                raise ValueError("Test error")

        assert "error_op" not in context._active_operations


class TestTimerFunction:
    """Test the timer convenience function."""

    def test_timer_function_works_with_logger(self) -> None:
        """Test that timer function works with a logger."""
        mock_logger = MagicMock()

        with timer("test_operation", logger=mock_logger):
            time.sleep(0.001)

        # Should call log twice (start and end)
        assert mock_logger.log.call_count == 2

        start_call = mock_logger.log.call_args_list[0]
        end_call = mock_logger.log.call_args_list[1]

        assert start_call[0] == ("INFO", "Starting: test_operation")
        assert end_call[0][0] == "INFO"
        assert "Completed: test_operation" in end_call[0][1]
        # Check that duration_ms is in the kwargs
        assert "duration_ms" in end_call[1]

    def test_timer_function_works_without_logger(self) -> None:
        """Test that timer function works without a logger."""
        # Should not raise any exceptions
        with timer("test_operation", logger=None):
            time.sleep(0.001)

        # Test with no logger argument
        with timer("test_operation"):
            time.sleep(0.001)

    def test_timer_function_handles_exceptions(self) -> None:
        """Test that timer function handles exceptions properly."""
        mock_logger = MagicMock()

        with pytest.raises(ValueError):
            with timer("failing_operation", logger=mock_logger):
                raise ValueError("Test error")

        # Should still call start log and end log
        assert mock_logger.log.call_count == 2


class TestTimingResult:
    """Test the TimingResult dataclass."""

    def test_timing_result_creation(self) -> None:
        """Test that TimingResult can be created correctly."""
        result = TimingResult(
            operation="test_op",
            duration_ms=42.5,
            start_time=1.0,
            end_time=1.0425,
            success=True,
        )

        assert result.operation == "test_op"
        assert result.duration_ms == 42.5
        assert result.start_time == 1.0
        assert result.end_time == 1.0425
        assert result.success is True
        assert result.error is None

    def test_timing_result_with_error(self) -> None:
        """Test that TimingResult can store error information."""
        result = TimingResult(
            operation="failed_op",
            duration_ms=10.0,
            start_time=1.0,
            end_time=1.01,
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"
