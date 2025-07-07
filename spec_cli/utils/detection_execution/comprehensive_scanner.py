"""Comprehensive scanner for executing singleton detection across entire codebase.

This module provides the comprehensive scanning functionality to execute singleton detection
across all Python files in a codebase with performance monitoring and detailed reporting.
"""

import concurrent.futures
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...exceptions import SpecError
from ...logging.debug import debug_logger
from ..singleton_detection import SingletonPatternDetector, SingletonViolation

class ScanExecutionError(SpecError):
    """Exception raised when scan execution fails."""

    def __init__(self, message: str, scan_context: dict[str, Any] | None = None) -> None:
        """Initialize ScanExecutionError with message and context.

        Args:
            message: Error message describing the scan failure
            scan_context: Optional context dictionary with scan details
        """
        super().__init__(message)
        self.scan_context = scan_context or {}

@dataclass
class SingletonPattern:
    """Comprehensive singleton pattern detected in codebase scan."""

    file_path: Path
    line_number: int
    pattern_type: str
    singleton_name: str
    description: str
    code_snippet: str
    usage_context: str | None = None

@dataclass
class ScanStatistics:
    """Statistics from comprehensive codebase scan execution."""

    total_files_scanned: int
    python_files_found: int
    singleton_patterns_detected: int
    scan_duration_seconds: float
    files_per_second: float
    errors_encountered: int
    excluded_files: int

@dataclass
class ComprehensiveScanResult:
    """Result from comprehensive singleton detection scan."""

    singleton_patterns: list[SingletonPattern]
    scan_statistics: ScanStatistics
    detection_report: str
    scan_config: dict[str, Any]
    error_details: list[str]

def execute_full_codebase_scan(scan_config: dict[str, Any]) -> ComprehensiveScanResult:
    """Execute comprehensive singleton detection scan across entire codebase.

    Args:
        scan_config: Configuration dictionary containing:
            - codebase_root: str - Root directory to scan
            - exclusion_patterns: List[str] - Patterns to exclude
            - max_workers: int - Maximum parallel workers (default: 4)
            - timeout_seconds: int - Scan timeout (default: 300)

    Returns:
        ComprehensiveScanResult with detected patterns and statistics

    Raises:
        ScanExecutionError: If scan configuration is invalid or execution fails
        FileNotFoundError: If codebase_root doesn't exist

    Example:
        config = {
            "codebase_root": "spec_cli",
            "exclusion_patterns": ["test_*", "*.pyc"],
            "max_workers": 4
        }
        result = execute_full_codebase_scan(config)
        print(f"Found {len(result.singleton_patterns)} patterns")
    """
    debug_logger.log(
        "INFO", "Starting comprehensive singleton detection scan", scan_config=scan_config
    )

    # Validate scan configuration
    _validate_scan_config(scan_config)

    codebase_root = Path(scan_config["codebase_root"])
    if not codebase_root.exists():
        raise FileNotFoundError(f"Codebase root not found: {codebase_root}")

    start_time = time.time()
    scan_errors: list[str] = []

    try:
        # Discover Python files to scan
        python_files = _discover_python_files(
            codebase_root,
            scan_config.get("exclusion_patterns", [])
        )

        debug_logger.log(
            "INFO",
            "Python files discovered for scanning",
            file_count=len(python_files),
            codebase_root=str(codebase_root)
        )

        # Execute parallel scanning
        all_patterns = _execute_parallel_scan(
            python_files,
            scan_config.get("max_workers", 4),
            scan_config.get("timeout_seconds", 300),
            scan_errors
        )

        # Calculate scan statistics
        end_time = time.time()
        duration = end_time - start_time

        statistics = ScanStatistics(
            total_files_scanned=len(python_files),
            python_files_found=len(python_files),
            singleton_patterns_detected=len(all_patterns),
            scan_duration_seconds=duration,
            files_per_second=len(python_files) / duration if duration > 0 else 0,
            errors_encountered=len(scan_errors),
            excluded_files=0  # Would need file counting to implement properly
        )

        # Generate detection report
        report = _generate_detection_report(all_patterns, statistics, scan_config)

        debug_logger.log(
            "INFO",
            "Comprehensive scan completed successfully",
            patterns_found=len(all_patterns),
            duration_seconds=duration,
            files_scanned=len(python_files)
        )

        return ComprehensiveScanResult(
            singleton_patterns=all_patterns,
            scan_statistics=statistics,
            detection_report=report,
            scan_config=scan_config,
            error_details=scan_errors
        )

    except Exception as e:
        scan_context = {
            "codebase_root": str(codebase_root),
            "scan_config": scan_config,
            "duration": time.time() - start_time
        }
        debug_logger.log(
            "ERROR",
            "Comprehensive scan execution failed",
            error=str(e),
            error_type=type(e).__name__,
            scan_context=scan_context
        )
        raise ScanExecutionError(f"Scan execution failed: {e}", scan_context) from e

def _validate_scan_config(scan_config: dict[str, Any]) -> None:
    """Validate scan configuration parameters.

    Args:
        scan_config: Configuration dictionary to validate

    Raises:
        ScanExecutionError: If configuration is invalid
    """
    if not isinstance(scan_config, dict):
        raise ScanExecutionError("Scan config must be a dictionary")

    if "codebase_root" not in scan_config:
        raise ScanExecutionError("Scan config missing required 'codebase_root'")

    if not isinstance(scan_config["codebase_root"], str):
        raise ScanExecutionError("codebase_root must be a string path")

    # Validate optional parameters
    max_workers = scan_config.get("max_workers", 4)
    if not isinstance(max_workers, int) or max_workers < 1:
        raise ScanExecutionError("max_workers must be positive integer")

    timeout = scan_config.get("timeout_seconds", 300)
    if not isinstance(timeout, int) or timeout < 1:
        raise ScanExecutionError("timeout_seconds must be positive integer")

def _discover_python_files(
    codebase_root: Path, exclusion_patterns: list[str]
) -> list[Path]:
    """Discover Python files in codebase excluding specified patterns.

    Args:
        codebase_root: Root directory to search
        exclusion_patterns: Patterns to exclude from scan

    Returns:
        List of Python file paths to scan
    """
    python_files = []

    for py_file in codebase_root.rglob("*.py"):
        # Check exclusion patterns
        if any(pattern in str(py_file) for pattern in exclusion_patterns):
            continue

        python_files.append(py_file)

    return python_files

def _execute_parallel_scan(
    python_files: list[Path],
    max_workers: int,
    timeout_seconds: int,
    scan_errors: list[str]
) -> list[SingletonPattern]:
    """Execute parallel scanning of Python files for singleton patterns.

    Args:
        python_files: List of Python files to scan
        max_workers: Maximum number of parallel workers
        timeout_seconds: Timeout for entire scan operation
        scan_errors: List to collect scan errors

    Returns:
        List of all detected singleton patterns
    """
    all_patterns: list[SingletonPattern] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scan tasks
        future_to_file = {
            executor.submit(_scan_single_file, py_file): py_file
            for py_file in python_files
        }

        try:
            # Collect results with timeout
            for future in concurrent.futures.as_completed(
                future_to_file, timeout=timeout_seconds
            ):
                py_file = future_to_file[future]
                try:
                    patterns = future.result()
                    all_patterns.extend(patterns)
                except Exception as e:
                    error_msg = f"Failed to scan {py_file}: {e}"
                    scan_errors.append(error_msg)
                    debug_logger.log(
                        "WARNING",
                        "File scan failed",
                        file_path=str(py_file),
                        error=str(e)
                    )

        except concurrent.futures.TimeoutError:
            error_msg = f"Scan timeout exceeded {timeout_seconds} seconds"
            scan_errors.append(error_msg)
            debug_logger.log("ERROR", "Scan timeout exceeded", timeout=timeout_seconds)

    return all_patterns

def _scan_single_file(file_path: Path) -> list[SingletonPattern]:
    """Scan a single Python file for singleton patterns.

    Args:
        file_path: Path to Python file to scan

    Returns:
        List of singleton patterns found in the file
    """
    patterns: list[SingletonPattern] = []

    try:
        # Use existing singleton detection utilities
        detector = SingletonPatternDetector()
        violations = detector.detect_violations(file_path)

        # Convert violations to comprehensive patterns
        for violation in violations:
            pattern = SingletonPattern(
                file_path=violation.file_path,
                line_number=violation.line_number,
                pattern_type=violation.pattern_type,
                singleton_name=_extract_singleton_name(violation),
                description=violation.description,
                code_snippet=violation.code_snippet
            )
            patterns.append(pattern)

        # Also check for usage patterns via pattern analysis
        usage_patterns = analyze_singleton_usage(file_path)

        for usage in usage_patterns:
            if usage.usage_type in ["class_definition", "instantiation"]:
                pattern = SingletonPattern(
                    file_path=usage.file_path,
                    line_number=usage.line_number,
                    pattern_type=f"usage_{usage.usage_type}",
                    singleton_name=usage.singleton_name,
                    description=f"Singleton usage: {usage.usage_type}",
                    code_snippet=usage.context,
                    usage_context=usage.context
                )
                patterns.append(pattern)

    except Exception as e:
        debug_logger.log(
            "WARNING",
            "Failed to scan file for patterns",
            file_path=str(file_path),
            error=str(e)
        )

    return patterns

def _extract_singleton_name(violation: SingletonViolation) -> str:
    """Extract singleton name from violation description or code snippet.

    Args:
        violation: Singleton violation to extract name from

    Returns:
        Extracted singleton name
    """
    # Try to extract from description first
    if ":" in violation.description:
        parts = violation.description.split(":")
        if len(parts) > 1:
            return parts[1].strip()

    # Fall back to extracting from code snippet
    snippet = violation.code_snippet.strip()
    if snippet:
        # Simple extraction for class names
        if snippet.startswith("class "):
            class_parts = snippet.split()
            if len(class_parts) > 1:
                return class_parts[1].split("(")[0]

    return "unknown_singleton"

def _generate_detection_report(
    patterns: list[SingletonPattern],
    statistics: ScanStatistics,
    scan_config: dict[str, Any]
) -> str:
    """Generate comprehensive detection report from scan results.

    Args:
        patterns: List of detected singleton patterns
        statistics: Scan execution statistics
        scan_config: Original scan configuration

    Returns:
        Formatted detection report string
    """
    report_lines = [
        "=== Comprehensive Singleton Detection Report ===",
        "",
        "Scan Configuration:",
        f"  Codebase Root: {scan_config['codebase_root']}",
        f"  Max Workers: {scan_config.get('max_workers', 4)}",
        f"  Exclusion Patterns: {scan_config.get('exclusion_patterns', [])}",
        "",
        "Scan Statistics:",
        f"  Files Scanned: {statistics.total_files_scanned}",
        f"  Patterns Detected: {statistics.singleton_patterns_detected}",
        f"  Scan Duration: {statistics.scan_duration_seconds:.2f} seconds",
        f"  Scan Rate: {statistics.files_per_second:.2f} files/second",
        f"  Errors Encountered: {statistics.errors_encountered}",
        "",
        "Detected Patterns by Type:",
    ]

    # Group patterns by type
    pattern_groups: dict[str, list[SingletonPattern]] = {}
    for pattern in patterns:
        if pattern.pattern_type not in pattern_groups:
            pattern_groups[pattern.pattern_type] = []
        pattern_groups[pattern.pattern_type].append(pattern)

    for pattern_type, type_patterns in pattern_groups.items():
        report_lines.append(f"  {pattern_type}: {len(type_patterns)} occurrences")
        for pattern in type_patterns[:3]:  # Show first 3 examples
            report_lines.append(
                f"    - {pattern.file_path}:{pattern.line_number} "
                f"({pattern.singleton_name})"
            )
        if len(type_patterns) > 3:
            report_lines.append(f"    ... and {len(type_patterns) - 3} more")
        report_lines.append("")

    report_lines.extend([
        "",
        "=== Scan Completed Successfully ===",
        f"Total singleton patterns found: {len(patterns)}",
        f"Scan completed in {statistics.scan_duration_seconds:.2f} seconds"
    ])

    return "\n".join(report_lines)
