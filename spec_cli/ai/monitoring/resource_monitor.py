"""Resource monitoring for AI operations."""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor system resource usage during AI operations."""

    def __init__(self) -> None:
        """Initialize resource monitor."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._start_time: float | None = None
        self._start_memory: float | None = None

    def start_monitoring(self) -> "ResourceMonitor":
        """Start monitoring resource usage.

        Returns:
            Self for chaining
        """
        self._start_time = time.time()

        try:
            import psutil

            process = psutil.Process()
            self._start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            self.logger.debug(
                "Started resource monitoring",
                extra={"start_memory_mb": self._start_memory},
            )
        except ImportError:
            self._start_memory = 0
            self.logger.debug("psutil not available, memory monitoring disabled")
        except Exception as e:
            self._start_memory = 0
            self.logger.warning("Failed to get memory info: %s", e)

        return self

    def stop_monitoring(self) -> dict[str, Any]:
        """Stop monitoring and return resource usage data.

        Returns:
            Dictionary containing resource usage metrics
        """
        if self._start_time is None:
            self.logger.warning("stop_monitoring called without start_monitoring")
            return {}

        end_time = time.time()
        operation_time = end_time - self._start_time

        resource_data = {
            "operation_time_s": operation_time,
            "start_memory_mb": self._start_memory or 0,
            "end_memory_mb": 0,
            "memory_delta_mb": 0,
            "cpu_usage_percent": 0,
        }

        try:
            import psutil

            process = psutil.Process()
            end_memory = process.memory_info().rss / (1024 * 1024)  # MB

            resource_data["end_memory_mb"] = end_memory
            resource_data["memory_delta_mb"] = end_memory - (self._start_memory or 0)
            resource_data["cpu_usage_percent"] = process.cpu_percent()

            self.logger.debug(
                "Resource monitoring completed",
                extra={
                    "operation_time_s": operation_time,
                    "memory_delta_mb": resource_data["memory_delta_mb"],
                },
            )

        except ImportError:
            self.logger.debug("psutil not available for end monitoring")
        except Exception as e:
            self.logger.warning("Failed to get end resource info: %s", e)

        # Reset state
        self._start_time = None
        self._start_memory = None

        return resource_data

    def analyze_usage(self, resource_usage: dict[str, Any]) -> dict[str, Any]:
        """Analyze resource usage and provide insights.

        Args:
            resource_usage: Resource usage data from monitoring

        Returns:
            Dictionary containing analysis results
        """
        if not resource_usage:
            return {"analysis": "no_data", "recommendations": []}

        analysis = {
            "analysis": "normal",
            "memory_usage_mb": resource_usage.get("memory_delta_mb", 0),
            "operation_time_s": resource_usage.get("operation_time_s", 0),
            "cpu_efficiency": "unknown",
            "recommendations": [],
        }

        # Analyze memory usage
        memory_delta = resource_usage.get("memory_delta_mb", 0)
        if memory_delta > 500:
            analysis["analysis"] = "high_memory"
            analysis["recommendations"].append(
                "High memory usage detected - consider using a smaller model"
            )
        elif memory_delta > 200:
            analysis["analysis"] = "moderate_memory"
            analysis["recommendations"].append(
                "Moderate memory usage - consider enabling quantization"
            )

        # Analyze operation time
        operation_time = resource_usage.get("operation_time_s", 0)
        if operation_time > 30:
            analysis["recommendations"].append(
                "Long operation time - consider GPU acceleration or smaller model"
            )

        # Analyze CPU usage
        cpu_usage = resource_usage.get("cpu_usage_percent", 0)
        if cpu_usage > 0:
            if cpu_usage < 50:
                analysis["cpu_efficiency"] = "low"
                analysis["recommendations"].append(
                    "Low CPU utilization - check if GPU is being used effectively"
                )
            elif cpu_usage > 90:
                analysis["cpu_efficiency"] = "high"
            else:
                analysis["cpu_efficiency"] = "normal"

        self.logger.debug(
            "Resource usage analysis completed",
            extra={
                "analysis_type": analysis["analysis"],
                "recommendation_count": len(analysis["recommendations"]),
            },
        )

        return analysis


def monitor_resource_usage() -> ResourceMonitor:
    """Create and start resource monitoring.

    Returns:
        ResourceMonitor instance ready for monitoring
    """
    monitor = ResourceMonitor()
    return monitor.start_monitoring()
