"""Slice 3.1: Comprehensive Singleton Detection Execution.

This module executes comprehensive singleton detection across the entire codebase
to identify all singleton patterns with precise location information and performance monitoring.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from spec_cli.exceptions import SpecError
from spec_cli.logging.debug import debug_logger
from spec_cli.utils.detection_execution.comprehensive_scanner import (
    ComprehensiveScanResult,
    execute_full_codebase_scan,
)

class DetectionExecutionError(SpecError):
    """Exception raised when detection execution fails."""

    def __init__(
        self, message: str, execution_context: dict[str, Any] | None = None
    ) -> None:
        """Initialize DetectionExecutionError with message and context.

        Args:
            message: Error message describing the execution failure
            execution_context: Optional context dictionary with execution details
        """
        super().__init__(message)
        self.execution_context = execution_context or {}

def execute_comprehensive_detection(
    codebase_root: str, scan_config: dict[str, Any], exclusion_patterns: list[str]
) -> dict[str, Any]:
    """Execute comprehensive singleton detection across entire codebase.

    Args:
        codebase_root: Root directory path for codebase scanning
        scan_config: Configuration dictionary for scan execution
        exclusion_patterns: List of patterns to exclude from scanning

    Returns:
        Dictionary containing:
        - singleton_patterns: List of detected singleton patterns
        - scan_statistics: Scan execution statistics
        - detection_report: Comprehensive detection report

    Raises:
        DetectionExecutionError: If detection execution fails
        FileNotFoundError: If codebase_root doesn't exist

    Example:
        result = execute_comprehensive_detection(
            "spec_cli",
            {"max_workers": 4, "timeout_seconds": 300},
            ["test_*", "*.pyc"]
        )
        print(f"Found {len(result['singleton_patterns'])} patterns")
    """
    debug_logger.log(
        "INFO",
        "Starting comprehensive singleton detection execution",
        codebase_root=codebase_root,
        exclusion_count=len(exclusion_patterns),
    )

    # Validate inputs
    if not codebase_root or not isinstance(codebase_root, str):
        raise DetectionExecutionError("codebase_root must be a non-empty string")

    if not isinstance(scan_config, dict):
        raise DetectionExecutionError("scan_config must be a dictionary")

    if not isinstance(exclusion_patterns, list):
        raise DetectionExecutionError("exclusion_patterns must be a list")

    # Prepare comprehensive scan configuration
    comprehensive_config = _prepare_scan_configuration(
        codebase_root, scan_config, exclusion_patterns
    )

    try:
        # Execute comprehensive scan using helper
        scan_result = execute_full_codebase_scan(comprehensive_config)

        # Process and format results
        processed_result = _process_scan_results(scan_result)

        debug_logger.log(
            "INFO",
            "Comprehensive detection execution completed successfully",
            patterns_found=len(processed_result["singleton_patterns"]),
            scan_duration=scan_result.scan_statistics.scan_duration_seconds,
        )

        return processed_result

    except Exception as e:
        execution_context = {
            "codebase_root": codebase_root,
            "scan_config": scan_config,
            "exclusion_patterns": exclusion_patterns,
        }
        debug_logger.log(
            "ERROR",
            "Detection execution failed",
            error=str(e),
            error_type=type(e).__name__,
            execution_context=execution_context,
        )
        raise DetectionExecutionError(
            f"Detection execution failed: {e}", execution_context
        ) from e

def generate_detection_summary(
    singleton_patterns: list[dict[str, Any]],
) -> dict[str, int]:
    """Generate summary statistics from detected singleton patterns.

    Args:
        singleton_patterns: List of detected singleton pattern dictionaries

    Returns:
        Dictionary with summary statistics including pattern type counts

    Example:
        patterns = [{"pattern_type": "metaclass_singleton", ...}, ...]
        summary = generate_detection_summary(patterns)
        print(f"Metaclass patterns: {summary['metaclass_singleton']}")
    """
    debug_logger.log(
        "DEBUG", "Generating detection summary", pattern_count=len(singleton_patterns)
    )

    summary: dict[str, int] = {
        "total_patterns": len(singleton_patterns),
        "unique_singletons": 0,
        "files_with_patterns": 0,
    }

    if not singleton_patterns:
        return summary

    # Count patterns by type
    pattern_types: dict[str, int] = {}
    unique_singletons = set()
    files_with_patterns = set()

    for pattern in singleton_patterns:
        # Count pattern types
        pattern_type = pattern.get("pattern_type", "unknown")
        pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1

        # Track unique singleton names
        singleton_name = pattern.get("singleton_name", "")
        if singleton_name:
            unique_singletons.add(singleton_name)

        # Track files with patterns
        file_path = pattern.get("file_path", "")
        if file_path:
            files_with_patterns.add(file_path)

    # Update summary with counts
    summary.update(pattern_types)
    summary["unique_singletons"] = len(unique_singletons)
    summary["files_with_patterns"] = len(files_with_patterns)

    debug_logger.log(
        "INFO",
        "Detection summary generated",
        summary_stats=summary,
        pattern_types=list(pattern_types.keys()),
    )

    return summary

def save_detection_results(results: dict[str, Any], output_path: Path) -> None:
    """Save detection results to JSON file with comprehensive formatting.

    Args:
        results: Detection results dictionary to save
        output_path: Path where to save the results file

    Raises:
        DetectionExecutionError: If saving results fails
        OSError: If file system operations fail

    Example:
        save_detection_results(
            detection_results,
            Path("singleton_detection_results.json")
        )
    """
    debug_logger.log("INFO", "Saving detection results", output_path=str(output_path))

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare results for JSON serialization
        serializable_results = _prepare_results_for_serialization(results)

        # Write results to file with formatting
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        debug_logger.log(
            "INFO", "Detection results saved successfully", output_path=str(output_path)
        )

    except (OSError, TypeError, ValueError) as e:
        execution_context = {
            "output_path": str(output_path),
            "results_keys": list(results.keys()),
        }
        debug_logger.log(
            "ERROR",
            "Failed to save detection results",
            error=str(e),
            error_type=type(e).__name__,
            execution_context=execution_context,
        )
        raise DetectionExecutionError(
            f"Failed to save results: {e}", execution_context
        ) from e

def _prepare_scan_configuration(
    codebase_root: str, scan_config: dict[str, Any], exclusion_patterns: list[str]
) -> dict[str, Any]:
    """Prepare comprehensive scan configuration from inputs.

    Args:
        codebase_root: Root directory for scanning
        scan_config: User-provided scan configuration
        exclusion_patterns: Patterns to exclude from scanning

    Returns:
        Complete scan configuration dictionary
    """
    # Default configuration
    default_config = {
        "max_workers": 4,
        "timeout_seconds": 300,
    }

    # Merge with user configuration
    comprehensive_config = {**default_config, **scan_config}
    comprehensive_config["codebase_root"] = codebase_root
    comprehensive_config["exclusion_patterns"] = exclusion_patterns

    debug_logger.log(
        "DEBUG", "Scan configuration prepared", config=comprehensive_config
    )

    return comprehensive_config

def _process_scan_results(scan_result: ComprehensiveScanResult) -> dict[str, Any]:
    """Process comprehensive scan results into standardized format.

    Args:
        scan_result: Result from comprehensive scan execution

    Returns:
        Processed results dictionary
    """
    # Convert singleton patterns to dictionaries
    pattern_dicts = []
    for pattern in scan_result.singleton_patterns:
        pattern_dict = asdict(pattern)
        # Convert Path objects to strings for JSON serialization
        pattern_dict["file_path"] = str(pattern_dict["file_path"])
        pattern_dicts.append(pattern_dict)

    # Convert statistics to dictionary
    stats_dict = asdict(scan_result.scan_statistics)

    processed_result = {
        "singleton_patterns": pattern_dicts,
        "scan_statistics": stats_dict,
        "detection_report": scan_result.detection_report,
        "scan_config": scan_result.scan_config,
        "error_details": scan_result.error_details,
        "summary": generate_detection_summary(pattern_dicts),
    }

    return processed_result

def _prepare_results_for_serialization(results: dict[str, Any]) -> dict[str, Any]:
    """Prepare results dictionary for JSON serialization.

    Args:
        results: Results dictionary to prepare

    Returns:
        Serializable results dictionary
    """
    serializable: dict[str, Any] = {}

    for key, value in results.items():
        if isinstance(value, Path):
            serializable[key] = str(value)
        elif isinstance(value, dict):
            serializable[key] = _prepare_results_for_serialization(value)
        elif isinstance(value, list):
            serializable[key] = [
                _prepare_results_for_serialization(item)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            serializable[key] = value

    return serializable

