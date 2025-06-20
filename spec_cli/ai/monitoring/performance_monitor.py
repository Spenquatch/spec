"""AI performance monitoring and optimization recommendations."""

import logging
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any

from ...utils.platform_utils import (
    GPUCapabilitiesResult,
    get_environment_info,
    get_gpu_capabilities,
)
from ..config.settings import AIConfig
from ..providers.base import GenerationResult
from .metrics_collector import MetricsCollector
from .resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """Performance monitoring report with metrics and recommendations."""

    enabled: bool
    operation_time: float = 0.0
    memory_usage: float = 0.0
    generation_quality: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    system_info: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class PerformanceMonitor:
    """AI performance monitoring and optimization recommendations."""

    def __init__(self, config: AIConfig) -> None:
        """Initialize performance monitor with configuration.

        Args:
            config: AI configuration containing monitoring settings
        """
        self.config = config
        self.metrics_collector = MetricsCollector()
        self.resource_monitor = ResourceMonitor()

        # Check if monitoring is enabled
        monitoring_config = getattr(config, "monitoring", None)
        self.enabled = bool(
            monitoring_config and getattr(monitoring_config, "enabled", False)
        )

        self.logger = logging.getLogger(self.__class__.__name__)

        if self.enabled:
            self.logger.debug("Performance monitoring enabled")
        else:
            self.logger.debug("Performance monitoring disabled")

    def monitor_ai_operation(
        self, operation_name: str
    ) -> AbstractContextManager["AIOperationMonitor"]:
        """Context manager for monitoring AI operations.

        Args:
            operation_name: Name of the operation being monitored

        Returns:
            Context manager for AI operation monitoring
        """
        return AIOperationMonitor(self, operation_name)

    def collect_generation_metrics(
        self,
        result: GenerationResult,
        operation_time: float,
        resource_usage: dict[str, Any],
    ) -> PerformanceReport:
        """Collect and analyze AI generation performance.

        Args:
            result: AI generation result to analyze
            operation_time: Time taken for the operation in seconds
            resource_usage: Resource usage data from monitoring

        Returns:
            Performance report with metrics and recommendations
        """
        if not self.enabled:
            return PerformanceReport(enabled=False)

        try:
            # Collect system information using helpers
            system_info = get_environment_info()
            gpu_info = get_gpu_capabilities()

            # Aggregate metrics using helper
            metrics = self.metrics_collector.collect_generation_metrics(result)

            # Analyze resource usage
            resource_analysis = self.resource_monitor.analyze_usage(resource_usage)

            # Generate optimization recommendations
            recommendations = self._generate_recommendations(
                metrics, resource_analysis, system_info, gpu_info
            )

            return PerformanceReport(
                enabled=True,
                operation_time=operation_time,
                memory_usage=resource_usage.get("memory_delta_mb", 0),
                generation_quality=metrics.get("quality_score", 0),
                recommendations=recommendations,
                system_info=system_info,
            )

        except Exception as e:
            self.logger.error(
                "Performance monitoring failed",
                extra={"error": str(e), "operation_time": operation_time},
            )
            return PerformanceReport(
                enabled=True, error=f"Performance monitoring failed: {str(e)}"
            )

    def _generate_recommendations(
        self,
        metrics: dict[str, Any],
        resource_analysis: dict[str, Any],
        system_info: dict[str, Any],
        gpu_info: GPUCapabilitiesResult,
    ) -> list[str]:
        """Generate actionable optimization recommendations.

        Args:
            metrics: Generation metrics
            resource_analysis: Resource usage analysis
            system_info: System information
            gpu_info: GPU capabilities

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        # Memory optimization recommendations
        memory_usage = resource_analysis.get("memory_usage_mb", 0)
        if memory_usage > 200:
            recommendations.append(
                "Consider enabling 4-bit quantization to reduce memory usage"
            )

        # Device optimization recommendations
        if gpu_info.get("cuda_available") and not metrics.get("used_gpu", False):
            recommendations.append(
                "GPU detected but not used - enable CUDA for faster generation"
            )

        if gpu_info.get("mps_available") and not metrics.get("used_gpu", False):
            recommendations.append(
                "Apple Silicon GPU detected - enable MPS for faster generation"
            )

        # Performance recommendations
        generation_time = metrics.get("processing_time_ms", 0) / 1000.0
        if generation_time > 10:
            recommendations.append(
                "Generation time is high - consider using a smaller model"
            )

        # Quality recommendations
        quality_score = metrics.get("quality_score", 0)
        if quality_score < 0.5:
            recommendations.append(
                "Generation quality is low - check model configuration"
            )

        # Resource efficiency recommendations
        cpu_efficiency = resource_analysis.get("cpu_efficiency", "unknown")
        if cpu_efficiency == "low":
            recommendations.append("Low CPU utilization - consider GPU acceleration")

        # Add general recommendations if no specific issues found
        if not recommendations and metrics.get("success", False):
            recommendations.append("Performance looks good - no optimization needed")

        self.logger.debug(
            "Generated recommendations",
            extra={
                "recommendation_count": len(recommendations),
                "memory_usage_mb": memory_usage,
                "generation_time_s": generation_time,
            },
        )

        return recommendations


class AIOperationMonitor:
    """Context manager for monitoring individual AI operations."""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str) -> None:
        """Initialize operation monitor.

        Args:
            monitor: Parent performance monitor
            operation_name: Name of the operation being monitored
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: float | None = None
        self.resource_monitor: ResourceMonitor | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self) -> "AIOperationMonitor":
        """Start monitoring the AI operation."""
        if self.monitor.enabled:
            self.start_time = time.time()
            self.resource_monitor = self.monitor.resource_monitor.start_monitoring()

            self.logger.debug(
                "Started monitoring AI operation",
                extra={"operation_name": self.operation_name},
            )

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop monitoring and log performance metrics."""
        if self.monitor.enabled and self.start_time:
            end_time = time.time()
            operation_time = end_time - self.start_time

            resource_usage = {}
            if self.resource_monitor:
                resource_usage = self.resource_monitor.stop_monitoring()

            # Log performance metrics
            self.logger.info(
                "AI operation completed",
                extra={
                    "operation_name": self.operation_name,
                    "operation_time_s": operation_time,
                    "memory_usage_mb": resource_usage.get("memory_delta_mb", 0),
                },
            )

    def get_operation_time(self) -> float:
        """Get current operation time if monitoring is active.

        Returns:
            Operation time in seconds, or 0 if not monitoring
        """
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
