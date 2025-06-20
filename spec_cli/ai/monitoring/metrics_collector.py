"""AI performance metrics collection helper."""

import logging
from typing import Any

from ..providers.base import GenerationResult

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate AI performance metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def collect_generation_metrics(self, result: GenerationResult) -> dict[str, Any]:
        """Collect and aggregate AI performance metrics from generation result.

        Args:
            result: AI generation result to analyze

        Returns:
            Dictionary containing collected metrics

        Raises:
            ValueError: If result is None or invalid
        """
        if result is None:
            raise ValueError("result cannot be None")

        if not isinstance(result, GenerationResult):
            raise ValueError("result must be a GenerationResult instance")

        self.logger.debug(
            "Collecting generation metrics",
            extra={
                "success": result.success,
                "has_content": bool(result.content),
                "processing_time": result.processing_time_ms,
            },
        )

        metrics = {
            "success": result.success,
            "content_generated": len(result.content) if result.content else 0,
            "processing_time_ms": result.processing_time_ms or 0,
            "has_main_content": result.has_complete_documentation(),
            "content_size_chars": len(result.get_main_content()),
            "history_size_chars": len(result.get_history_content()),
            "metadata_keys": list(result.metadata.keys()) if result.metadata else [],
        }

        # Calculate quality score based on content completeness
        if result.success:
            metrics["quality_score"] = self._calculate_quality_score(result)
        else:
            metrics["quality_score"] = 0

        # Extract metadata information
        if result.metadata:
            metrics["model_used"] = result.metadata.get("model", "unknown")
            metrics["tokens_used"] = result.metadata.get("tokens", 0)
            metrics["used_gpu"] = result.metadata.get("device", "").startswith("cuda")
        else:
            metrics["model_used"] = "unknown"
            metrics["tokens_used"] = 0
            metrics["used_gpu"] = False

        self.logger.debug(
            "Generated metrics",
            extra={
                "quality_score": metrics["quality_score"],
                "content_size": metrics["content_size_chars"],
                "model_used": metrics["model_used"],
            },
        )

        return metrics

    def _calculate_quality_score(self, result: GenerationResult) -> float:
        """Calculate quality score based on content analysis.

        Args:
            result: Generation result to analyze

        Returns:
            Quality score between 0 and 1
        """
        if not result.success:
            return 0.0

        score = 0.0

        # Base score for having content
        if result.content:
            score += 0.3

        # Score for complete documentation
        if result.has_complete_documentation():
            score += 0.4

        # Score for content size (reasonable documentation length)
        main_content_size = len(result.get_main_content())
        if main_content_size > 100:
            score += 0.2
        if main_content_size > 500:
            score += 0.1

        return min(score, 1.0)


def collect_generation_metrics(result: GenerationResult) -> dict[str, Any]:
    """Collect generation metrics using default collector.

    Args:
        result: Generation result to analyze

    Returns:
        Dictionary containing collected metrics
    """
    collector = MetricsCollector()
    return collector.collect_generation_metrics(result)
