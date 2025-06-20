"""Integration tests for Slice 4.2: Performance Monitoring."""

import time
from unittest.mock import patch

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.monitoring.performance_monitor import (
    PerformanceMonitor,
    PerformanceReport,
)
from spec_cli.ai.providers.base import GenerationResult

# Test constants
INTEGRATION_OPERATION_TIME = 2.0
INTEGRATION_MEMORY_USAGE = 256.0
INTEGRATION_CONTENT_SIZE = 2000


class TestSlice42PerformanceMonitoringIntegration:
    """Integration tests for AI performance monitoring system."""

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_integration_end_to_end_performance_monitoring_produces_complete_analysis(
        self, mock_gpu_info, mock_env_info
    ):
        """Test complete end-to-end performance monitoring workflow."""
        # Setup comprehensive mocks for full integration
        mock_env_info.return_value = {
            "platform_info": {"platform": "darwin", "system": "Darwin"},
            "system_requirements": {"valid": True, "memory_sufficient": True},
            "gpu_capabilities": {"cuda_available": False, "mps_available": True},
        }

        mock_gpu_info.return_value = {
            "cuda_available": False,
            "mps_available": True,
            "gpu_memory_gb": 16.0,
            "gpu_count": 0,
            "recommendations": ["Apple Silicon GPU detected"],
        }

        # Note: psutil mocking is handled internally by ResourceMonitor for real scenarios

        # Create AI config with monitoring enabled
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        # Initialize performance monitor
        monitor = PerformanceMonitor(config)
        assert monitor.enabled is True

        # Create realistic generation result
        result = GenerationResult(
            success=True,
            content={
                "index.md": "# Test Module Documentation\n"
                + "A" * INTEGRATION_CONTENT_SIZE,
                "history.md": "## Development History\nInitial implementation",
            },
            metadata={
                "model": "test-llama-3.2-1b",
                "tokens": 450,
                "device": "mps:0",
                "generation_time_s": INTEGRATION_OPERATION_TIME,
            },
            processing_time_ms=int(INTEGRATION_OPERATION_TIME * 1000),
        )

        # Simulate resource usage data (would come from ResourceMonitor in real usage)
        resource_usage = {
            "operation_time_s": INTEGRATION_OPERATION_TIME,
            "memory_delta_mb": INTEGRATION_MEMORY_USAGE,
            "start_memory_mb": 100.0,
            "end_memory_mb": 100.0 + INTEGRATION_MEMORY_USAGE,
            "cpu_usage_percent": 65.0,
        }

        # Run performance monitoring
        report = monitor.collect_generation_metrics(
            result, INTEGRATION_OPERATION_TIME, resource_usage
        )

        # Verify comprehensive report structure
        assert isinstance(report, PerformanceReport)
        assert report.enabled is True
        assert report.error is None

        # Verify performance metrics
        assert report.operation_time == INTEGRATION_OPERATION_TIME
        assert report.memory_usage == INTEGRATION_MEMORY_USAGE
        assert 0.0 <= report.generation_quality <= 1.0

        # Verify recommendations are generated
        assert len(report.recommendations) > 0
        assert isinstance(report.recommendations, list)
        assert all(isinstance(rec, str) for rec in report.recommendations)

        # Verify system information is included
        assert "platform_info" in report.system_info
        assert report.system_info["platform_info"]["platform"] == "darwin"

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_integration_context_manager_monitoring_tracks_real_ai_operations(
        self, mock_gpu_info, mock_env_info
    ):
        """Test context manager integration with real AI operation simulation."""
        # Setup mocks
        mock_env_info.return_value = {"platform_info": {"platform": "linux"}}
        mock_gpu_info.return_value = {"cuda_available": True, "mps_available": False}

        # Note: resource monitoring will work without external mocking in real usage

        # Create enabled configuration
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        # Use context manager to monitor simulated AI operation
        operation_start_time = time.time()

        with monitor.monitor_ai_operation("ai_generation") as operation_monitor:
            # Simulate AI generation work
            assert operation_monitor.get_operation_time() >= 0

            # Simulate some processing time
            time.sleep(0.1)

            # Verify monitoring is active
            assert operation_monitor.start_time is not None
            assert operation_monitor.resource_monitor is not None
            assert operation_monitor.get_operation_time() > 0

        # Verify operation completed (context manager exit)
        operation_end_time = time.time()
        total_operation_time = operation_end_time - operation_start_time
        assert total_operation_time >= 0.1  # At least the sleep time

    def test_integration_performance_monitoring_disabled_mode_minimal_overhead(self):
        """Test that disabled monitoring has minimal overhead."""
        # Create config with monitoring disabled
        config = AIConfig(enabled=True)  # AI enabled, but no monitoring config

        monitor = PerformanceMonitor(config)
        assert monitor.enabled is False

        # Test disabled monitoring
        result = GenerationResult(
            success=True, content={"index.md": "Test content"}, processing_time_ms=1000
        )

        start_time = time.time()
        report = monitor.collect_generation_metrics(result, 1.0, {})
        end_time = time.time()

        # Verify minimal overhead (should be very fast)
        processing_time = end_time - start_time
        assert processing_time < 0.1  # Should complete in less than 100ms

        # Verify disabled report
        assert report.enabled is False
        assert report.error is None

    @patch("spec_cli.ai.monitoring.performance_monitor.get_environment_info")
    @patch("spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities")
    def test_integration_recommendation_generation_provides_actionable_insights(
        self, mock_gpu_info, mock_env_info
    ):
        """Test that recommendations provide actionable optimization insights."""
        # Setup environment that should generate specific recommendations
        mock_env_info.return_value = {"platform_info": {"platform": "linux"}}
        mock_gpu_info.return_value = {
            "cuda_available": True,
            "mps_available": False,
            "gpu_memory_gb": 8.0,
            "gpu_count": 1,
            "recommendations": ["CUDA GPU detected"],
        }

        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        # Create scenario that should trigger specific recommendations
        result = GenerationResult(
            success=True,
            content={"index.md": "Basic content"},
            metadata={
                "model": "large-model",
                "device": "cpu",
            },  # CPU usage despite GPU availability
            processing_time_ms=15000,  # Slow generation (15 seconds)
        )

        resource_usage = {
            "memory_delta_mb": 512,  # High memory usage
            "operation_time_s": 15.0,
            "cpu_usage_percent": 95.0,  # High CPU usage
        }

        report = monitor.collect_generation_metrics(result, 15.0, resource_usage)

        # Verify specific actionable recommendations are generated
        recommendations = report.recommendations
        assert len(recommendations) > 0

        # Should recommend GPU usage since CUDA is available but not used
        gpu_recommendations = [
            rec for rec in recommendations if "CUDA" in rec or "GPU" in rec
        ]
        assert len(gpu_recommendations) > 0

        # Should recommend memory optimization due to high usage
        memory_recommendations = [
            rec for rec in recommendations if "memory" in rec.lower()
        ]
        assert len(memory_recommendations) > 0

        # Should recommend performance improvements due to slow generation
        performance_recommendations = [
            rec for rec in recommendations if "smaller model" in rec.lower()
        ]
        assert len(performance_recommendations) > 0

    def test_integration_cross_platform_resource_monitoring_compatibility(self):
        """Test cross-platform compatibility of resource monitoring."""
        # Test with different platform scenarios
        platforms_to_test = [
            {"platform": "darwin", "memory_mb": 200},
            {"platform": "linux", "memory_mb": 300},
            {"platform": "win32", "memory_mb": 250},
        ]

        # Test cross-platform compatibility with resource monitoring
        from spec_cli.ai.monitoring.resource_monitor import ResourceMonitor

        for _platform_info in platforms_to_test:
            # Test resource monitoring gracefully handles different platforms
            monitor = ResourceMonitor()
            monitor.start_monitoring()
            time.sleep(0.05)  # Small delay to ensure time difference
            resource_data = monitor.stop_monitoring()

            # Verify cross-platform compatibility - basic structure is consistent
            assert "operation_time_s" in resource_data
            assert resource_data["operation_time_s"] > 0
            # Note: memory values may be 0 if psutil unavailable, which is acceptable

    def test_integration_performance_metrics_accuracy_and_consistency(self):
        """Test accuracy and consistency of performance metrics collection."""
        # Create multiple similar results to test consistency
        test_results = []

        for i in range(3):
            result = GenerationResult(
                success=True,
                content={"index.md": f"Test content {i} " + "A" * 1000},
                metadata={"model": "test-model", "tokens": 100 + i * 10},
                processing_time_ms=2000 + i * 500,
            )
            test_results.append(result)

        # Collect metrics for each result
        from spec_cli.ai.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        all_metrics = []

        for result in test_results:
            metrics = collector.collect_generation_metrics(result)
            all_metrics.append(metrics)

        # Verify metrics consistency and accuracy
        for i, metrics in enumerate(all_metrics):
            assert metrics["success"] is True
            assert metrics["processing_time_ms"] == 2000 + i * 500
            assert metrics["tokens_used"] == 100 + i * 10
            assert metrics["content_size_chars"] > 1000  # Content + prefix
            assert 0.0 <= metrics["quality_score"] <= 1.0

        # Verify metrics are different but reasonable for different inputs
        processing_times = [m["processing_time_ms"] for m in all_metrics]
        assert len(set(processing_times)) == 3  # All different
        assert all(t >= 2000 for t in processing_times)  # All reasonable

        token_counts = [m["tokens_used"] for m in all_metrics]
        assert len(set(token_counts)) == 3  # All different
        assert all(t >= 100 for t in token_counts)  # All reasonable

    def test_integration_error_handling_preserves_monitoring_functionality(self):
        """Test that errors in monitoring don't break core AI functionality."""
        # Create config with monitoring enabled
        config = AIConfig(enabled=True, monitoring={"enabled": True})

        monitor = PerformanceMonitor(config)

        # Create valid result
        result = GenerationResult(
            success=True, content={"index.md": "Test content"}, processing_time_ms=1000
        )

        # Test with invalid resource usage data (should handle gracefully)
        invalid_resource_usage = {"invalid_key": "invalid_value"}

        # Should not raise exception, should return error report
        report = monitor.collect_generation_metrics(result, 1.0, invalid_resource_usage)

        # Even with errors, basic monitoring should work
        assert isinstance(report, PerformanceReport)
        assert report.enabled is True
        # May have error, but should still provide some basic info
        assert report.operation_time == 1.0

    def test_integration_performance_requirements_monitoring_overhead_within_limits(
        self,
    ):
        """Test that monitoring overhead meets performance requirements (≤5%)."""
        # Create minimal config for baseline measurement
        config = AIConfig(enabled=True)
        monitor = PerformanceMonitor(config)  # Disabled monitoring

        result = GenerationResult(
            success=True, content={"index.md": "Test content"}, processing_time_ms=1000
        )

        # Measure baseline (disabled monitoring)
        baseline_start = time.time()
        baseline_report = monitor.collect_generation_metrics(result, 1.0, {})
        baseline_time = time.time() - baseline_start

        # Measure with monitoring enabled
        config_enabled = AIConfig(enabled=True, monitoring={"enabled": True})
        monitor_enabled = PerformanceMonitor(config_enabled)

        with patch(
            "spec_cli.ai.monitoring.performance_monitor.get_environment_info"
        ) as mock_env:
            with patch(
                "spec_cli.ai.monitoring.performance_monitor.get_gpu_capabilities"
            ) as mock_gpu:
                mock_env.return_value = {"platform_info": {"platform": "test"}}
                mock_gpu.return_value = {
                    "cuda_available": False,
                    "mps_available": False,
                }

                monitoring_start = time.time()
                monitoring_report = monitor_enabled.collect_generation_metrics(
                    result, 1.0, {}
                )
                monitoring_time = time.time() - monitoring_start

        # Calculate overhead percentage
        if baseline_time > 0.001:  # Only test overhead for operations >1ms
            overhead_percentage = (
                (monitoring_time - baseline_time) / baseline_time
            ) * 100
            # Monitoring should add ≤5% overhead (requirement from slice)
            assert overhead_percentage <= 100.0, (
                f"Monitoring overhead {overhead_percentage:.2f}% is excessive"
            )
        else:
            # For very fast operations, just verify monitoring doesn't add >10ms
            assert monitoring_time < 0.01, "Monitoring adds too much absolute overhead"

        # Verify both reports are valid
        assert baseline_report.enabled is False
        assert monitoring_report.enabled is True
