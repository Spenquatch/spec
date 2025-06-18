# Slice 4.2: Performance Monitoring

**Goal**: Implement AI performance metrics collection and optimization monitoring for resource usage and generation quality

**Slice Type**: Observability

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(platform|workflow)"`
- spec_cli/utils/platform_utils.py → get_gpu_capabilities(), get_environment_info() for system resource monitoring
- spec_cli/utils/workflow_utils.py → create_workflow_result() for metrics result handling
- spec_cli/ai/config/loader.py → ConfigLoader (existing, from slice 1b)
- spec_cli/ai/providers/base.py → GenerationResult (existing, from slice 2a)
- Create helper: spec_cli/ai/monitoring/metrics_collector.py → collect_generation_metrics(result: GenerationResult) → "Collect and aggregate AI performance metrics"
- Create helper: spec_cli/ai/monitoring/resource_monitor.py → monitor_resource_usage() → "Track memory and CPU usage during AI operations"

**Complexity Analysis:**
- Decision points: 4/7 (if monitoring_enabled, if metrics_collected, try/except blocks)
- Helper calls: 5 (get_gpu_capabilities, get_environment_info, collect_generation_metrics, monitor_resource_usage, create_workflow_result)
- McCabe validation: Pass (4 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {operation_type: str, start_time: float, end_time: float, resource_data: Dict[str, Any]}
- **Action**:
  1. Check if monitoring is enabled in configuration (decision point)
  2. Collect resource usage metrics using platform helpers (try/except)
  3. Aggregate performance data using metrics helper (decision point)
  4. Store metrics for analysis and reporting (try/except)
  5. Generate performance summary and recommendations (decision point)
- **Outputs**: {metrics_summary: Dict[str, Any], recommendations: List[str]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/monitoring/performance_monitor.py (new - main performance monitoring implementation)
- spec_cli/ai/monitoring/metrics_collector.py (new - metrics collection helper)
- spec_cli/ai/monitoring/resource_monitor.py (new - resource monitoring helper)

**Test Requirements:**
- **Unit Tests**: Test metrics collection, resource monitoring, performance analysis, error handling for missing data
- **Integration Test**: End-to-end test with real AI operations, verify metrics are collected and analyzed correctly
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Mock AI operations, sample performance data, resource usage fixtures, monitoring configuration

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: Monitoring adds ≤5% overhead to AI operations

**Integration Validation:**
Run AI generation with performance monitoring enabled, verify that metrics are collected for generation time, memory usage, model loading time, and quality scores. Test that monitoring provides actionable optimization recommendations (e.g., device suggestions, memory optimization tips).

**AI Agent Execution Notes:**
This slice provides observability into AI operations for optimization. Focus on minimal overhead monitoring that doesn't impact AI performance significantly. Collect actionable metrics that help users optimize their AI setup. Ensure monitoring is optional and can be disabled for production use. Consider implementing sampling for high-frequency operations.

**Expected Implementation Pattern:**
```python
class PerformanceMonitor:
    """AI performance monitoring and optimization recommendations."""

    def __init__(self, config: AIConfig):
        self.config = config
        self.metrics_collector = MetricsCollector()
        self.resource_monitor = ResourceMonitor()
        self.enabled = config.monitoring.enabled if config.monitoring else False

    def monitor_ai_operation(self, operation_name: str) -> ContextManager:
        """Context manager for monitoring AI operations."""
        return AIOperationMonitor(self, operation_name)

    def collect_generation_metrics(self, result: GenerationResult,
                                 operation_time: float, resource_usage: Dict[str, Any]) -> PerformanceReport:
        """Collect and analyze AI generation performance."""
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
                memory_usage=resource_usage.get("memory_mb", 0),
                generation_quality=metrics.get("quality_score", 0),
                recommendations=recommendations,
                system_info=system_info
            )

        except Exception as e:
            return PerformanceReport(
                enabled=True,
                error=f"Performance monitoring failed: {str(e)}"
            )

    def _generate_recommendations(self, metrics: Dict[str, Any],
                                resource_analysis: Dict[str, Any],
                                system_info: Dict[str, Any],
                                gpu_info: Dict[str, Any]) -> List[str]:
        """Generate actionable optimization recommendations."""
        recommendations = []

        # Memory optimization recommendations
        if resource_analysis.get("memory_usage_mb", 0) > 200:
            recommendations.append("Consider enabling 4-bit quantization to reduce memory usage")

        # Device optimization recommendations
        if gpu_info.cuda_available and not metrics.get("used_gpu", False):
            recommendations.append("GPU detected but not used - enable CUDA for faster generation")

        # Performance recommendations
        if metrics.get("generation_time_s", 0) > 10:
            recommendations.append("Generation time is high - consider using a smaller model")

        return recommendations

class AIOperationMonitor:
    """Context manager for monitoring individual AI operations."""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.resource_monitor = None

    def __enter__(self):
        if self.monitor.enabled:
            self.start_time = time.time()
            self.resource_monitor = self.monitor.resource_monitor.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.monitor.enabled and self.start_time:
            end_time = time.time()
            operation_time = end_time - self.start_time
            resource_usage = self.resource_monitor.stop_monitoring() if self.resource_monitor else {}

            # Log performance metrics
            logger.info(f"AI operation '{self.operation_name}' completed",
                       extra={
                           "operation_time": operation_time,
                           "memory_usage": resource_usage.get("memory_mb", 0)
                       })
```

This slice provides essential observability for AI operations, enabling users to optimize their AI setup and troubleshoot performance issues.
