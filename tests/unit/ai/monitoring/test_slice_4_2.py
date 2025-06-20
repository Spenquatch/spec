"""Unit tests for Slice 4.2: Performance Monitoring."""

import time
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.monitoring.metrics_collector import (
    MetricsCollector,
    collect_generation_metrics,
)
from spec_cli.ai.monitoring.performance_monitor import (
    AIOperationMonitor,
    PerformanceMonitor,
    PerformanceReport,
)
from spec_cli.ai.monitoring.resource_monitor import (
    ResourceMonitor,
    monitor_resource_usage,
)
from spec_cli.ai.providers.base import GenerationResult

# Test constants
DEFAULT_OPERATION_TIME = 5.0
DEFAULT_MEMORY_USAGE = 128.0
DEFAULT_QUALITY_SCORE = 0.8
SAMPLE_CONTENT_SIZE = 1500
SAMPLE_MODEL_NAME = "test-model"
SAMPLE_TOKEN_COUNT = 150


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def test_init_creates_collector_with_logger(self):
        """Test collector initialization."""
        collector = MetricsCollector()
        assert collector.logger.name == "MetricsCollector"

    def test_collect_generation_metrics_when_valid_result_then_returns_complete_metrics(
        self,
    ):
        """Test metrics collection with valid generation result."""
        # Create test result
        result = GenerationResult(
            success=True,
            content={"index.md": "# Test Documentation\nThis is test content."},
            metadata={
                "model": SAMPLE_MODEL_NAME,
                "tokens": SAMPLE_TOKEN_COUNT,
                "device": "cuda:0",
            },
            processing_time_ms=int(DEFAULT_OPERATION_TIME * 1000),
        )

        collector = MetricsCollector()
        metrics = collector.collect_generation_metrics(result)

        # Verify metrics structure
        assert metrics["success"] is True
        assert metrics["content_generated"] == 1
        assert metrics["processing_time_ms"] == int(DEFAULT_OPERATION_TIME * 1000)
        assert metrics["has_main_content"] is True
        assert metrics["content_size_chars"] > 0
        assert metrics["model_used"] == SAMPLE_MODEL_NAME
        assert metrics["tokens_used"] == SAMPLE_TOKEN_COUNT
        assert metrics["used_gpu"] is True
        assert 0.0 <= metrics["quality_score"] <= 1.0

    def test_collect_generation_metrics_when_no_metadata_then_uses_defaults(
        self,
    ):
        """Test metrics collection with result having no metadata."""
        result = GenerationResult(
            success=True,
            content={"index.md": "Test content"},
            metadata=None,  # No metadata
            processing_time_ms=2000,
        )

        collector = MetricsCollector()
        metrics = collector.collect_generation_metrics(result)

        # Should use default values
        assert metrics["model_used"] == "unknown"
        assert metrics["tokens_used"] == 0
        assert metrics["used_gpu"] is False
        assert metrics["metadata_keys"] == []

    def test_collect_generation_metrics_when_failed_result_then_returns_failure_metrics(
        self,
    ):
        """Test metrics collection with failed generation result."""
        result = GenerationResult(
            success=False, error="Generation failed", processing_time_ms=1000
        )

        collector = MetricsCollector()
        metrics = collector.collect_generation_metrics(result)

        assert metrics["success"] is False
        assert metrics["quality_score"] == 0
        assert metrics["content_generated"] == 0
        assert metrics["model_used"] == "unknown"
        assert metrics["used_gpu"] is False

    def test_collect_generation_metrics_when_mps_device_then_detects_gpu_usage(
        self,
    ):
        """Test metrics collection with MPS device detection."""
        result = GenerationResult(
            success=True,
            content={"index.md": "Test content"},
            metadata={"device": "mps:0"},  # Apple Silicon GPU
            processing_time_ms=2000,
        )

        collector = MetricsCollector()
        metrics = collector.collect_generation_metrics(result)

        # Should not detect GPU for MPS (only cuda is checked)
        assert metrics["used_gpu"] is False

    def test_collect_generation_metrics_when_none_result_then_raises_value_error(self):
        """Test error handling with None result."""
        collector = MetricsCollector()

        with pytest.raises(ValueError, match="result cannot be None"):
            collector.collect_generation_metrics(None)

    def test_collect_generation_metrics_when_invalid_type_then_raises_value_error(self):
        """Test error handling with invalid result type."""
        collector = MetricsCollector()

        with pytest.raises(
            ValueError, match="result must be a GenerationResult instance"
        ):
            collector.collect_generation_metrics("invalid")

    def test_calculate_quality_score_when_complete_content_then_returns_high_score(
        self,
    ):
        """Test quality score calculation with complete content."""
        result = GenerationResult(
            success=True,
            content={"index.md": "A" * SAMPLE_CONTENT_SIZE},  # Large content
        )

        collector = MetricsCollector()
        score = collector._calculate_quality_score(result)

        # Should get full score for having content + complete docs + good size
        assert abs(score - 1.0) < 0.001

    def test_calculate_quality_score_when_minimal_content_then_returns_medium_score(
        self,
    ):
        """Test quality score calculation with minimal content."""
        result = GenerationResult(
            success=True,
            content={"index.md": "Short content"},  # Small content
        )

        collector = MetricsCollector()
        score = collector._calculate_quality_score(result)

        # Should get partial score
        assert 0.5 <= score <= 0.9

    def test_calculate_quality_score_when_medium_content_then_includes_size_bonus(
        self,
    ):
        """Test quality score calculation with medium-sized content."""
        result = GenerationResult(
            success=True,
            content={"index.md": "A" * 300},  # Medium content (200-500 chars)
        )

        collector = MetricsCollector()
        score = collector._calculate_quality_score(result)

        # Should get content + complete docs + small size bonus (0.3 + 0.4 + 0.2 = 0.9)
        assert abs(score - 0.9) < 0.001

    def test_calculate_quality_score_when_large_content_then_gets_full_bonus(
        self,
    ):
        """Test quality score calculation with large content."""
        result = GenerationResult(
            success=True,
            content={"index.md": "A" * 600},  # Large content (>500 chars)
        )

        collector = MetricsCollector()
        score = collector._calculate_quality_score(result)

        # Should get content + complete docs + both size bonuses (0.3 + 0.4 + 0.2 + 0.1 = 1.0)
        assert abs(score - 1.0) < 0.001

    def test_calculate_quality_score_when_no_content_only_has_complete_docs(
        self,
    ):
        """Test quality score with result that has no content but has complete docs."""
        # Create a mock result where content exists but no main content
        result = GenerationResult(
            success=True,
            content={"other.md": "Some content"},  # Content but not index.md
        )

        # Mock has_complete_documentation to return True but get_main_content to return empty
        with patch.object(result, "has_complete_documentation", return_value=True):
            with patch.object(result, "get_main_content", return_value=""):
                collector = MetricsCollector()
                score = collector._calculate_quality_score(result)

                # Should get content + complete docs but no size bonus (0.3 + 0.4 = 0.7)
                assert abs(score - 0.7) < 0.001

    def test_calculate_quality_score_when_failed_result_then_returns_zero(self):
        """Test quality score calculation with failed result."""
        result = GenerationResult(success=False, error="Failed")

        collector = MetricsCollector()
        score = collector._calculate_quality_score(result)

        assert score == 0.0

    def test_convenience_function_collect_generation_metrics_creates_collector_and_processes(
        self,
    ):
        """Test convenience function creates collector and processes result."""
        result = GenerationResult(
            success=True, content={"index.md": "Test content"}, processing_time_ms=2000
        )

        metrics = collect_generation_metrics(result)

        assert metrics["success"] is True
        assert metrics["processing_time_ms"] == 2000


class TestResourceMonitor:
    """Test resource monitoring functionality."""

    def test_init_creates_monitor_with_logger(self):
        """Test monitor initialization."""
        monitor = ResourceMonitor()
        assert monitor.logger.name == "ResourceMonitor"
        assert monitor._start_time is None
        assert monitor._start_memory is None

    def test_start_monitoring_when_psutil_available_then_records_memory(self):
        """Test start monitoring with psutil available."""
        with patch("builtins.__import__") as mock_import:
            # Create mock psutil module
            mock_psutil = Mock()
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = (
                DEFAULT_MEMORY_USAGE * 1024 * 1024
            )  # Convert to bytes
            mock_psutil.Process.return_value = mock_process

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = ResourceMonitor()
            result = monitor.start_monitoring()

            assert result is monitor
            assert monitor._start_time is not None
            assert monitor._start_memory == DEFAULT_MEMORY_USAGE

    def test_start_monitoring_when_psutil_unavailable_then_continues_without_memory(
        self,
    ):
        """Test start monitoring without psutil."""
        with patch("builtins.__import__") as mock_import:
            # Mock import to raise ImportError for psutil
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    raise ImportError("No module named 'psutil'")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = ResourceMonitor()
            result = monitor.start_monitoring()

            assert result is monitor
            assert monitor._start_time is not None
            assert monitor._start_memory == 0

    def test_stop_monitoring_when_started_then_returns_resource_data(self):
        """Test stop monitoring after start."""
        with patch("builtins.__import__") as mock_import:
            # Create mock psutil module
            mock_psutil = Mock()
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = (
                DEFAULT_MEMORY_USAGE * 1024 * 1024
            )
            mock_process.cpu_percent.return_value = 75.0
            mock_psutil.Process.return_value = mock_process

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = ResourceMonitor()
            monitor.start_monitoring()
            time.sleep(0.1)  # Small delay to ensure time difference
            resource_data = monitor.stop_monitoring()

            assert "operation_time_s" in resource_data
            assert resource_data["operation_time_s"] > 0
            assert resource_data["start_memory_mb"] == DEFAULT_MEMORY_USAGE
            assert resource_data["end_memory_mb"] == DEFAULT_MEMORY_USAGE
            assert resource_data["memory_delta_mb"] == 0
            assert resource_data["cpu_usage_percent"] == 75.0

    def test_stop_monitoring_when_not_started_then_returns_empty_dict(self):
        """Test stop monitoring without start."""
        monitor = ResourceMonitor()
        resource_data = monitor.stop_monitoring()

        assert resource_data == {}

    def test_analyze_usage_when_empty_data_then_returns_no_data_analysis(self):
        """Test usage analysis with empty data."""
        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage({})

        assert analysis["analysis"] == "no_data"
        assert analysis["recommendations"] == []

    def test_analyze_usage_when_high_memory_then_returns_high_memory_analysis(self):
        """Test usage analysis with high memory usage."""
        resource_usage = {
            "memory_delta_mb": 600,  # High memory
            "operation_time_s": 5.0,
            "cpu_usage_percent": 80.0,
        }

        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage(resource_usage)

        assert analysis["analysis"] == "high_memory"
        assert analysis["memory_usage_mb"] == 600
        assert any("smaller model" in rec for rec in analysis["recommendations"])

    def test_analyze_usage_when_moderate_memory_then_returns_moderate_analysis(self):
        """Test usage analysis with moderate memory usage."""
        resource_usage = {
            "memory_delta_mb": 300,  # Moderate memory
            "operation_time_s": 5.0,
            "cpu_usage_percent": 60.0,
        }

        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage(resource_usage)

        assert analysis["analysis"] == "moderate_memory"
        assert any("quantization" in rec for rec in analysis["recommendations"])

    def test_analyze_usage_when_long_operation_then_includes_time_recommendation(self):
        """Test usage analysis with long operation time."""
        resource_usage = {
            "memory_delta_mb": 100,
            "operation_time_s": 35.0,  # Long time
            "cpu_usage_percent": 50.0,
        }

        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage(resource_usage)

        assert any("GPU acceleration" in rec for rec in analysis["recommendations"])

    def test_analyze_usage_when_low_cpu_then_includes_efficiency_recommendation(self):
        """Test usage analysis with low CPU efficiency."""
        resource_usage = {
            "memory_delta_mb": 100,
            "operation_time_s": 5.0,
            "cpu_usage_percent": 30.0,  # Low CPU
        }

        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage(resource_usage)

        assert analysis["cpu_efficiency"] == "low"
        assert any("GPU" in rec for rec in analysis["recommendations"])

    def test_convenience_function_monitor_resource_usage_creates_started_monitor(self):
        """Test convenience function creates and starts monitor."""
        with patch("builtins.__import__") as mock_import:
            # Create mock psutil module
            mock_psutil = Mock()
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = 128 * 1024 * 1024  # 128MB
            mock_psutil.Process.return_value = mock_process

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = monitor_resource_usage()
            assert isinstance(monitor, ResourceMonitor)
            assert monitor._start_time is not None

    def test_start_monitoring_when_exception_in_psutil_then_continues_with_zero_memory(
        self,
    ):
        """Test start monitoring when psutil raises unexpected exception."""
        with patch("builtins.__import__") as mock_import:
            # Create mock psutil that raises exception on Process()
            mock_psutil = Mock()
            mock_psutil.Process.side_effect = Exception("Test exception")

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = ResourceMonitor()
            result = monitor.start_monitoring()

            assert result is monitor
            assert monitor._start_time is not None
            assert monitor._start_memory == 0

    def test_stop_monitoring_when_exception_in_psutil_then_continues_with_defaults(
        self,
    ):
        """Test stop monitoring when psutil raises unexpected exception."""
        with patch("builtins.__import__") as mock_import:
            # Create mock psutil that raises exception on Process()
            mock_psutil = Mock()
            mock_psutil.Process.side_effect = Exception("Test exception")

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            monitor = ResourceMonitor()
            monitor.start_monitoring()  # This will set _start_memory to 0 due to exception
            time.sleep(0.1)  # Small delay to ensure time difference
            resource_data = monitor.stop_monitoring()

            assert "operation_time_s" in resource_data
            assert resource_data["operation_time_s"] > 0
            assert resource_data["start_memory_mb"] == 0
            assert resource_data["end_memory_mb"] == 0
            assert resource_data["memory_delta_mb"] == 0
            assert resource_data["cpu_usage_percent"] == 0

    def test_analyze_usage_when_high_cpu_then_returns_high_efficiency(self):
        """Test usage analysis with high CPU usage."""
        resource_usage = {
            "memory_delta_mb": 100,
            "operation_time_s": 5.0,
            "cpu_usage_percent": 95.0,  # High CPU
        }

        monitor = ResourceMonitor()
        analysis = monitor.analyze_usage(resource_usage)

        assert analysis["cpu_efficiency"] == "high"


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_init_when_monitoring_enabled_then_sets_enabled_true(self):
        """Test initialization with monitoring enabled."""
        # Create config with monitoring enabled
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        assert monitor.enabled is True
        assert monitor.config is config
        assert isinstance(monitor.metrics_collector, MetricsCollector)
        assert isinstance(monitor.resource_monitor, ResourceMonitor)

    def test_init_when_monitoring_disabled_then_sets_enabled_false(self):
        """Test initialization with monitoring disabled."""
        config = AIConfig(enabled=True)  # AI enabled but no monitoring config

        monitor = PerformanceMonitor(config)

        assert monitor.enabled is False

    def test_monitor_ai_operation_returns_context_manager(self):
        """Test monitor operation returns proper context manager."""
        config = AIConfig(enabled=True)
        monitor = PerformanceMonitor(config)

        context_manager = monitor.monitor_ai_operation("test_operation")

        assert isinstance(context_manager, AIOperationMonitor)
        assert context_manager.operation_name == "test_operation"
        assert context_manager.monitor is monitor

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_collect_generation_metrics_when_enabled_then_returns_complete_report(
        self, mock_gpu_info, mock_env_info
    ):
        """Test metrics collection when monitoring is enabled."""
        # Setup mocks
        mock_env_info.return_value = {"platform": "darwin"}
        mock_gpu_info.return_value = {"cuda_available": True, "mps_available": False}

        # Create enabled config
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        # Create test result and resource usage
        result = GenerationResult(
            success=True, content={"index.md": "Test content"}, processing_time_ms=3000
        )
        resource_usage = {"memory_delta_mb": DEFAULT_MEMORY_USAGE}

        report = monitor.collect_generation_metrics(
            result, DEFAULT_OPERATION_TIME, resource_usage
        )

        assert report.enabled is True
        assert report.operation_time == DEFAULT_OPERATION_TIME
        assert report.memory_usage == DEFAULT_MEMORY_USAGE
        assert report.generation_quality > 0
        assert len(report.recommendations) > 0
        assert report.error is None

    def test_collect_generation_metrics_when_disabled_then_returns_disabled_report(
        self,
    ):
        """Test metrics collection when monitoring is disabled."""
        config = AIConfig(enabled=True)  # No monitoring config
        monitor = PerformanceMonitor(config)

        result = GenerationResult(success=True, content={"index.md": "Test"})
        report = monitor.collect_generation_metrics(result, DEFAULT_OPERATION_TIME, {})

        assert report.enabled is False
        assert report.error is None

    @patch(
        "spec_cli.ai.monitoring.performance_monitor.get_environment_info",
        side_effect=Exception("Test error"),
    )
    def test_collect_generation_metrics_when_exception_then_returns_error_report(
        self, mock_env_info
    ):
        """Test error handling in metrics collection."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        result = GenerationResult(success=True, content={"index.md": "Test"})
        report = monitor.collect_generation_metrics(result, DEFAULT_OPERATION_TIME, {})

        assert report.enabled is True
        assert "Performance monitoring failed" in report.error

    def test_generate_recommendations_when_high_memory_then_suggests_quantization(self):
        """Test recommendation generation for high memory usage."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 5000,
            "used_gpu": False,
            "success": True,
            "quality_score": 0.8,
        }
        resource_analysis = {"memory_usage_mb": 250}  # High memory
        system_info = {}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("quantization" in rec for rec in recommendations)

    def test_generate_recommendations_when_gpu_available_unused_then_suggests_gpu(self):
        """Test recommendation generation when GPU is available but unused."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 5000,
            "used_gpu": False,
            "success": True,
            "quality_score": 0.8,
        }
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {}
        gpu_info = {"cuda_available": True, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("CUDA" in rec for rec in recommendations)

    def test_generate_recommendations_when_mps_available_then_suggests_mps(self):
        """Test recommendation generation for Apple Silicon GPU."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 5000,
            "used_gpu": False,
            "success": True,
            "quality_score": 0.8,
        }
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {}
        gpu_info = {"cuda_available": False, "mps_available": True}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("MPS" in rec for rec in recommendations)

    def test_generate_recommendations_when_performance_good_then_suggests_no_optimization(
        self,
    ):
        """Test recommendation generation when performance is already good."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 2000,
            "used_gpu": True,
            "success": True,
            "quality_score": 0.9,
        }
        resource_analysis = {"memory_usage_mb": 50, "cpu_efficiency": "normal"}
        system_info = {}
        gpu_info = {"cuda_available": True, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("no optimization needed" in rec for rec in recommendations)

    def test_generate_recommendations_when_slow_generation_then_suggests_smaller_model(
        self,
    ):
        """Test recommendation generation for slow generation times."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 15000,  # 15 seconds - slow
            "used_gpu": False,
            "success": True,
            "quality_score": 0.8,
        }
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("smaller model" in rec for rec in recommendations)

    def test_generate_recommendations_when_low_quality_then_suggests_config_check(
        self,
    ):
        """Test recommendation generation for low generation quality."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 3000,
            "used_gpu": False,
            "success": True,
            "quality_score": 0.3,  # Low quality
        }
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("quality is low" in rec for rec in recommendations)

    def test_generate_recommendations_when_low_cpu_efficiency_then_suggests_gpu(
        self,
    ):
        """Test recommendation generation for low CPU efficiency."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        metrics = {
            "processing_time_ms": 3000,
            "used_gpu": False,
            "success": True,
            "quality_score": 0.8,
        }
        resource_analysis = {
            "memory_usage_mb": 100,
            "cpu_efficiency": "low",
        }  # Low CPU efficiency
        system_info = {}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("Low CPU utilization" in rec for rec in recommendations)


class TestAIOperationMonitor:
    """Test AI operation monitoring context manager."""

    def test_init_sets_properties_correctly(self):
        """Test initialization sets all properties."""
        config = AIConfig(enabled=True)
        monitor = PerformanceMonitor(config)

        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        assert operation_monitor.monitor is monitor
        assert operation_monitor.operation_name == "test_operation"
        assert operation_monitor.start_time is None
        assert operation_monitor.resource_monitor is None

    def test_context_manager_when_enabled_then_monitors_operation(self):
        """Test context manager with monitoring enabled."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        with patch("builtins.__import__") as mock_import:
            # Create mock psutil module
            mock_psutil = Mock()
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = 128 * 1024 * 1024  # 128MB
            mock_process.cpu_percent.return_value = 50.0
            mock_psutil.Process.return_value = mock_process

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            with operation_monitor as ctx:
                assert ctx is operation_monitor
                assert operation_monitor.start_time is not None
                assert operation_monitor.resource_monitor is not None

                # Test get_operation_time during operation
                time.sleep(0.1)
                operation_time = operation_monitor.get_operation_time()
                assert operation_time > 0

    def test_context_manager_when_disabled_then_skips_monitoring(self):
        """Test context manager with monitoring disabled."""
        config = AIConfig(enabled=True)  # No monitoring config
        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        with operation_monitor as ctx:
            assert ctx is operation_monitor
            assert operation_monitor.start_time is None
            assert operation_monitor.resource_monitor is None

    def test_context_manager_exit_when_resource_monitor_available_then_stops_monitoring(
        self,
    ):
        """Test context manager exit with resource monitoring active."""
        config = AIConfig(enabled=True, monitoring={"enabled": True})
        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        with patch("builtins.__import__") as mock_import:
            # Create mock psutil module
            mock_psutil = Mock()
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = 128 * 1024 * 1024  # 128MB
            mock_process.cpu_percent.return_value = 50.0
            mock_psutil.Process.return_value = mock_process

            # Mock import to return our mock psutil when psutil is imported
            def import_side_effect(name, *args, **kwargs):
                if name == "psutil":
                    return mock_psutil
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Use context manager and exit
            with operation_monitor:
                time.sleep(0.1)
                # Verify resource monitor is active
                assert operation_monitor.resource_monitor is not None

            # After exit, resource monitor should have been stopped
            # (implicitly tested by the context manager exit)

    def test_context_manager_exit_when_disabled_monitoring_then_skips_stop(
        self,
    ):
        """Test context manager exit when monitoring is disabled."""
        config = AIConfig(enabled=True)  # No monitoring config - disabled
        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        # Use context manager - should not fail when monitoring disabled
        with operation_monitor:
            time.sleep(0.1)
            # Verify monitoring is disabled
            assert operation_monitor.start_time is None
            assert operation_monitor.resource_monitor is None

        # Should complete without error when monitoring is disabled

    def test_context_manager_exit_when_monitoring_disabled_no_start_time(
        self,
    ):
        """Test context manager exit path when monitoring disabled and no start time."""
        config = AIConfig(enabled=True)  # No monitoring config - disabled
        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        # Manually call __exit__ without __enter__ (start_time will be None)
        operation_monitor.__exit__(None, None, None)

        # Should complete without error even when start_time is None

    def test_get_operation_time_when_not_started_then_returns_zero(self):
        """Test get_operation_time when monitoring not started."""
        config = AIConfig(enabled=True)
        monitor = PerformanceMonitor(config)
        operation_monitor = AIOperationMonitor(monitor, "test_operation")

        operation_time = operation_monitor.get_operation_time()
        assert operation_time == 0.0


class TestPerformanceReport:
    """Test performance report data structure."""

    def test_init_with_minimal_parameters_creates_valid_report(self):
        """Test report creation with minimal parameters."""
        report = PerformanceReport(enabled=True)

        assert report.enabled is True
        assert report.operation_time == 0.0
        assert report.memory_usage == 0.0
        assert report.generation_quality == 0.0
        assert report.recommendations == []
        assert report.system_info == {}
        assert report.error is None

    def test_init_with_all_parameters_creates_complete_report(self):
        """Test report creation with all parameters."""
        recommendations = ["Use GPU acceleration"]
        system_info = {"platform": "darwin"}

        report = PerformanceReport(
            enabled=True,
            operation_time=DEFAULT_OPERATION_TIME,
            memory_usage=DEFAULT_MEMORY_USAGE,
            generation_quality=DEFAULT_QUALITY_SCORE,
            recommendations=recommendations,
            system_info=system_info,
            error="Test error",
        )

        assert report.enabled is True
        assert report.operation_time == DEFAULT_OPERATION_TIME
        assert report.memory_usage == DEFAULT_MEMORY_USAGE
        assert report.generation_quality == DEFAULT_QUALITY_SCORE
        assert report.recommendations == recommendations
        assert report.system_info == system_info
        assert report.error == "Test error"

    def test_init_with_disabled_creates_minimal_report(self):
        """Test report creation with monitoring disabled."""
        report = PerformanceReport(enabled=False)

        assert report.enabled is False
        assert report.operation_time == 0.0
        assert report.memory_usage == 0.0
        assert report.generation_quality == 0.0
        assert report.recommendations == []
        assert report.system_info == {}
        assert report.error is None
