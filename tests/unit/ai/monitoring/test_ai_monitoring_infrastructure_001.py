"""Unit tests for AI monitoring infrastructure framework.

Tests comprehensive mocking framework for AI monitoring components including
metrics collection, performance monitoring, and resource tracking.
"""
# type: ignore  # Test file with comprehensive mocking - type hints not required

import time
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.monitoring.metrics_collector import MetricsCollector
from spec_cli.ai.monitoring.performance_monitor import (
    AIOperationMonitor,
    PerformanceMonitor,
    PerformanceReport,
)
from spec_cli.ai.monitoring.resource_monitor import ResourceMonitor
from spec_cli.ai.providers.base import GenerationResult


class TestAIMonitoringInfrastructure:
    """Test AI monitoring infrastructure and mocking framework."""

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()

        assert collector.logger.name == "MetricsCollector"

    def test_metrics_collector_with_valid_generation_result(self):
        """Test metrics collection with valid generation result."""
        collector = MetricsCollector()

        # Create mock generation result
        result = Mock(spec=GenerationResult)
        result.success = True
        result.content = {"index.md": "# Test Documentation\n\nThis is test content."}
        result.processing_time_ms = 1500
        result.metadata = {"model": "test-model", "tokens": 150, "device": "cuda:0"}
        result.has_complete_documentation.return_value = True
        result.get_main_content.return_value = (
            "# Test Documentation\n\nThis is test content."
        )
        result.get_history_content.return_value = "# History\n\nChanges made."

        metrics = collector.collect_generation_metrics(result)

        assert metrics["success"] is True
        assert (
            metrics["content_generated"] == 1
        )  # Length of content dict (number of files)
        assert metrics["processing_time_ms"] == 1500
        assert metrics["has_main_content"] is True
        assert metrics["model_used"] == "test-model"
        assert metrics["tokens_used"] == 150
        assert metrics["used_gpu"] is True
        assert 0 <= metrics["quality_score"] <= 1

    def test_metrics_collector_with_failed_generation_result(self):
        """Test metrics collection with failed generation result."""
        collector = MetricsCollector()

        # Create mock failed generation result
        result = Mock(spec=GenerationResult)
        result.success = False
        result.content = {}
        result.processing_time_ms = None
        result.metadata = None
        result.has_complete_documentation.return_value = False
        result.get_main_content.return_value = ""
        result.get_history_content.return_value = ""

        metrics = collector.collect_generation_metrics(result)

        assert metrics["success"] is False
        assert metrics["quality_score"] == 0
        assert metrics["model_used"] == "unknown"
        assert metrics["tokens_used"] == 0
        assert metrics["used_gpu"] is False

    def test_metrics_collector_with_none_result_raises_error(self):
        """Test metrics collection with None result raises ValueError."""
        collector = MetricsCollector()

        with pytest.raises(ValueError, match="result cannot be None"):
            collector.collect_generation_metrics(None)

    def test_metrics_collector_with_invalid_result_type_raises_error(self):
        """Test metrics collection with invalid result type raises ValueError."""
        collector = MetricsCollector()

        with pytest.raises(
            ValueError, match="result must be a GenerationResult instance"
        ):
            collector.collect_generation_metrics("invalid_result")

    def test_metrics_collector_quality_score_calculation(self):
        """Test quality score calculation logic."""
        collector = MetricsCollector()

        # Test high quality content
        result = Mock(spec=GenerationResult)
        result.success = True
        result.content = {"index.md": "Long documentation content " * 50}
        result.has_complete_documentation.return_value = True
        result.get_main_content.return_value = "Long documentation content " * 50

        quality_score = collector._calculate_quality_score(result)

        assert abs(quality_score - 1.0) < 0.01  # Should be very close to maximum score

    def test_resource_monitor_initialization(self):
        """Test ResourceMonitor initialization."""
        monitor = ResourceMonitor()

        assert monitor.logger.name == "ResourceMonitor"
        assert monitor._start_time is None
        assert monitor._start_memory is None

    @patch("builtins.__import__")
    def test_resource_monitor_start_monitoring_with_psutil(self, mock_import):
        """Test resource monitoring start with psutil available."""
        # Mock psutil module
        mock_psutil = Mock()
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        mock_psutil.Process.return_value = mock_process

        def mock_import_func(name, *args, **kwargs):
            if name == "psutil":
                return mock_psutil
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = mock_import_func

        monitor = ResourceMonitor()
        result = monitor.start_monitoring()

        assert result is monitor
        assert monitor._start_time is not None
        assert monitor._start_memory == 100.0  # 100 MB

    @patch("builtins.__import__", side_effect=ImportError)
    def test_resource_monitor_start_monitoring_without_psutil(self, mock_import):
        """Test resource monitoring start without psutil available."""
        monitor = ResourceMonitor()
        result = monitor.start_monitoring()

        assert result is monitor
        assert monitor._start_time is not None
        assert monitor._start_memory == 0

    @patch("builtins.__import__")
    def test_resource_monitor_stop_monitoring(self, mock_import):
        """Test resource monitoring stop with data collection."""
        # Mock psutil module
        mock_psutil = Mock()
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 120 * 1024 * 1024  # 120 MB
        mock_process.cpu_percent.return_value = 75.5
        mock_psutil.Process.return_value = mock_process

        def mock_import_func(name, *args, **kwargs):
            if name == "psutil":
                return mock_psutil
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = mock_import_func

        monitor = ResourceMonitor()
        monitor._start_time = time.time() - 2.5  # 2.5 seconds ago
        monitor._start_memory = 100.0  # 100 MB

        resource_data = monitor.stop_monitoring()

        assert "operation_time_s" in resource_data
        assert resource_data["operation_time_s"] >= 2.5
        assert resource_data["start_memory_mb"] == 100.0
        assert resource_data["end_memory_mb"] == 120.0
        assert resource_data["memory_delta_mb"] == 20.0
        assert resource_data["cpu_usage_percent"] == 75.5

    def test_resource_monitor_stop_monitoring_without_start(self):
        """Test stop monitoring called without start monitoring."""
        monitor = ResourceMonitor()

        resource_data = monitor.stop_monitoring()

        assert resource_data == {}

    def test_resource_monitor_analyze_usage_with_no_data(self):
        """Test resource usage analysis with no data."""
        monitor = ResourceMonitor()

        analysis = monitor.analyze_usage({})

        assert analysis["analysis"] == "no_data"
        assert analysis["recommendations"] == []

    def test_resource_monitor_analyze_usage_with_high_memory(self):
        """Test resource usage analysis with high memory usage."""
        monitor = ResourceMonitor()
        resource_usage = {
            "memory_delta_mb": 600,
            "operation_time_s": 5.0,
            "cpu_usage_percent": 80,
        }

        analysis = monitor.analyze_usage(resource_usage)

        assert analysis["analysis"] == "high_memory"
        assert "High memory usage detected" in analysis["recommendations"][0]
        assert analysis["cpu_efficiency"] == "normal"

    def test_resource_monitor_analyze_usage_with_long_operation(self):
        """Test resource usage analysis with long operation time."""
        monitor = ResourceMonitor()
        resource_usage = {
            "memory_delta_mb": 50,
            "operation_time_s": 35.0,
            "cpu_usage_percent": 45,
        }

        analysis = monitor.analyze_usage(resource_usage)

        assert "Long operation time" in str(analysis["recommendations"])
        assert analysis["cpu_efficiency"] == "low"

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_performance_monitor_initialization(self, mock_gpu_caps, mock_env_info):
        """Test PerformanceMonitor initialization."""
        # Mock AI config
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        assert monitor.config is mock_config
        assert monitor.enabled is True
        assert monitor.logger.name == "PerformanceMonitor"

    def test_performance_monitor_disabled_monitoring(self):
        """Test PerformanceMonitor with disabled monitoring."""
        # Mock AI config without monitoring
        mock_config = Mock()
        mock_config.monitoring = None

        monitor = PerformanceMonitor(mock_config)

        assert monitor.enabled is False

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_performance_monitor_collect_generation_metrics_disabled(
        self, mock_gpu_caps, mock_env_info
    ):
        """Test performance monitor metrics collection when disabled."""
        mock_config = Mock()
        mock_config.monitoring = None

        monitor = PerformanceMonitor(mock_config)

        # Mock generation result
        result = Mock(spec=GenerationResult)

        report = monitor.collect_generation_metrics(result, 1.5, {})

        assert isinstance(report, PerformanceReport)
        assert report.enabled is False

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_performance_monitor_collect_generation_metrics_enabled(
        self, mock_gpu_caps, mock_env_info
    ):
        """Test performance monitor metrics collection when enabled."""
        # Mock dependencies
        mock_env_info.return_value = {"platform": "linux", "python_version": "3.11"}
        mock_gpu_caps.return_value = {"cuda_available": True, "mps_available": False}

        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        # Mock generation result
        result = Mock(spec=GenerationResult)
        result.success = True
        result.content = {"index.md": "Test content"}
        result.processing_time_ms = 2000
        result.metadata = {"model": "test-model", "tokens": 100}
        result.has_complete_documentation.return_value = True
        result.get_main_content.return_value = "Test content"
        result.get_history_content.return_value = ""

        # Mock resource usage
        resource_usage = {"memory_delta_mb": 150, "operation_time_s": 2.0}

        # Mock metrics collector
        with patch.object(
            monitor.metrics_collector, "collect_generation_metrics"
        ) as mock_collect:
            mock_collect.return_value = {
                "success": True,
                "quality_score": 0.8,
                "processing_time_ms": 2000,
                "used_gpu": False,
            }

            # Mock resource monitor
            with patch.object(
                monitor.resource_monitor, "analyze_usage"
            ) as mock_analyze:
                mock_analyze.return_value = {
                    "memory_usage_mb": 150,
                    "cpu_efficiency": "normal",
                }

                report = monitor.collect_generation_metrics(result, 2.0, resource_usage)

        assert report.enabled is True
        assert report.operation_time == 2.0
        assert report.memory_usage == 150
        assert report.generation_quality == 0.8
        assert isinstance(report.recommendations, list)
        assert report.error is None

    def test_performance_monitor_generate_recommendations_gpu_available(self):
        """Test recommendation generation with GPU available but not used."""
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        metrics = {"used_gpu": False, "processing_time_ms": 5000, "quality_score": 0.8}
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {"platform": "linux"}
        gpu_info = {"cuda_available": True, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("enable CUDA" in rec for rec in recommendations)

    def test_performance_monitor_generate_recommendations_high_memory(self):
        """Test recommendation generation with high memory usage."""
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        metrics = {"used_gpu": True, "processing_time_ms": 2000, "quality_score": 0.8}
        resource_analysis = {"memory_usage_mb": 250, "cpu_efficiency": "normal"}
        system_info = {"platform": "linux"}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("quantization" in rec for rec in recommendations)

    def test_performance_monitor_generate_recommendations_low_quality(self):
        """Test recommendation generation with low quality score."""
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        metrics = {"used_gpu": True, "processing_time_ms": 2000, "quality_score": 0.3}
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {"platform": "linux"}
        gpu_info = {"cuda_available": False, "mps_available": False}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("quality is low" in rec for rec in recommendations)

    def test_ai_operation_monitor_initialization(self):
        """Test AIOperationMonitor initialization."""
        mock_monitor = Mock(spec=PerformanceMonitor)
        mock_monitor.enabled = True

        operation_monitor = AIOperationMonitor(mock_monitor, "test_operation")

        assert operation_monitor.monitor is mock_monitor
        assert operation_monitor.operation_name == "test_operation"
        assert operation_monitor.start_time is None
        assert operation_monitor.resource_monitor is None

    def test_ai_operation_monitor_context_manager_enabled(self):
        """Test AIOperationMonitor as context manager when enabled."""
        mock_monitor = Mock(spec=PerformanceMonitor)
        mock_monitor.enabled = True
        mock_resource_monitor_instance = Mock()
        mock_monitor.resource_monitor = Mock()
        mock_monitor.resource_monitor.start_monitoring.return_value = (
            mock_resource_monitor_instance
        )

        operation_monitor = AIOperationMonitor(mock_monitor, "test_operation")

        with operation_monitor as monitor:
            assert monitor is operation_monitor
            assert monitor.start_time is not None
            assert monitor.resource_monitor is mock_resource_monitor_instance

            # Test get_operation_time during operation
            operation_time = monitor.get_operation_time()
            assert operation_time >= 0

    def test_ai_operation_monitor_context_manager_disabled(self):
        """Test AIOperationMonitor as context manager when disabled."""
        mock_monitor = Mock(spec=PerformanceMonitor)
        mock_monitor.enabled = False

        operation_monitor = AIOperationMonitor(mock_monitor, "test_operation")

        with operation_monitor as monitor:
            assert monitor is operation_monitor
            assert monitor.start_time is None
            assert monitor.resource_monitor is None

    def test_ai_operation_monitor_get_operation_time_not_started(self):
        """Test get_operation_time when monitoring not started."""
        mock_monitor = Mock(spec=PerformanceMonitor)
        operation_monitor = AIOperationMonitor(mock_monitor, "test_operation")

        operation_time = operation_monitor.get_operation_time()

        assert operation_time == 0.0

    def test_performance_report_dataclass(self):
        """Test PerformanceReport dataclass functionality."""
        report = PerformanceReport(enabled=True)

        assert report.enabled is True
        assert report.operation_time == 0.0
        assert report.memory_usage == 0.0
        assert report.generation_quality == 0.0
        assert report.recommendations == []
        assert report.system_info == {}
        assert report.error is None

    def test_performance_report_with_data(self):
        """Test PerformanceReport with actual data."""
        report = PerformanceReport(
            enabled=True,
            operation_time=2.5,
            memory_usage=150.0,
            generation_quality=0.85,
            recommendations=["Use GPU acceleration"],
            system_info={"platform": "linux"},
            error=None,
        )

        assert report.enabled is True
        assert report.operation_time == 2.5
        assert report.memory_usage == 150.0
        assert report.generation_quality == 0.85
        assert len(report.recommendations) == 1
        assert "linux" in report.system_info["platform"]


class TestAIMonitoringIntegrationScenarios:
    """Test realistic integration scenarios for AI monitoring."""

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_complete_monitoring_workflow(self, mock_gpu_caps, mock_env_info):
        """Test complete monitoring workflow from start to finish."""
        # Mock dependencies
        mock_env_info.return_value = {"platform": "linux", "python_version": "3.11"}
        mock_gpu_caps.return_value = {"cuda_available": True, "mps_available": False}

        # Setup performance monitor
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        # Create realistic generation result
        GenerationResult(
            success=True,
            content={"index.md": "# Documentation\n\nDetailed content here." * 20},
            metadata={"model": "llama-7b", "tokens": 250, "device": "cpu"},
            processing_time_ms=3000,
        )

        # Simulate operation monitoring
        with monitor.monitor_ai_operation("documentation_generation") as op_monitor:
            time.sleep(0.1)  # Simulate some work
            operation_time = op_monitor.get_operation_time()
            assert operation_time >= 0.1

    def test_error_handling_in_monitoring(self):
        """Test error handling during monitoring operations."""
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        # Mock metrics collector to raise exception
        with patch.object(
            monitor.metrics_collector,
            "collect_generation_metrics",
            side_effect=Exception("Test error"),
        ):
            result = Mock(spec=GenerationResult)

            report = monitor.collect_generation_metrics(result, 1.0, {})

            assert report.enabled is True
            assert "Performance monitoring failed" in report.error

    def test_monitoring_with_mps_gpu(self):
        """Test monitoring with Apple Silicon MPS GPU."""
        mock_config = Mock()
        mock_config.monitoring = Mock()
        mock_config.monitoring.enabled = True

        monitor = PerformanceMonitor(mock_config)

        metrics = {"used_gpu": False, "processing_time_ms": 2000, "quality_score": 0.8}
        resource_analysis = {"memory_usage_mb": 100, "cpu_efficiency": "normal"}
        system_info = {"platform": "darwin"}
        gpu_info = {"cuda_available": False, "mps_available": True}

        recommendations = monitor._generate_recommendations(
            metrics, resource_analysis, system_info, gpu_info
        )

        assert any("enable MPS" in rec for rec in recommendations)

    def test_resource_monitoring_factory_function(self):
        """Test resource monitoring factory function."""
        from spec_cli.ai.monitoring.resource_monitor import monitor_resource_usage

        # Test factory function creates and starts monitoring
        resource_monitor = monitor_resource_usage()

        assert isinstance(resource_monitor, ResourceMonitor)
        assert resource_monitor._start_time is not None

    def test_metrics_collection_factory_function(self):
        """Test metrics collection factory function."""
        from spec_cli.ai.monitoring.metrics_collector import collect_generation_metrics

        # Create realistic generation result
        result = GenerationResult(
            success=True,
            content={"index.md": "Test documentation content"},
            metadata={"model": "test-model", "tokens": 50},
            processing_time_ms=1000,
        )

        metrics = collect_generation_metrics(result)

        assert metrics["success"] is True
        assert metrics["model_used"] == "test-model"
        assert metrics["tokens_used"] == 50
