"""Slice 2.2: Rich vs Plain Text Output Compatibility Resolution.

This module implements a compatibility layer to resolve Rich vs plain text
output formatting issues causing test failures. It provides utilities for
normalizing CLI output and ensuring consistent test validation across
different output modes.
"""

from typing import Any

from spec_cli.logging.debug import debug_logger
from spec_cli.utils.output_formatters.test_output_normalizer import (
    extract_formatting_metadata,
    normalize_output_for_testing,
)
from spec_cli.utils.test_helpers.cli_test_helpers import CLITestResult


class OutputCompatibilityResolver:
    """Resolve Rich vs plain text output formatting compatibility issues."""

    def __init__(self, default_mode: str = "auto") -> None:
        """Initialize output compatibility resolver.

        Args:
            default_mode: Default normalization mode ("auto", "rich", "plain")

        Raises:
            ValueError: If default_mode is invalid
        """
        valid_modes = {"auto", "rich", "plain"}
        if default_mode not in valid_modes:
            raise ValueError(
                f"Invalid default_mode '{default_mode}'. Must be one of: {valid_modes}"
            )

        self.default_mode = default_mode
        self.processed_outputs: list[dict[str, Any]] = []

        debug_logger.log(
            "INFO",
            "OutputCompatibilityResolver initialized",
            default_mode=default_mode,
        )

    def resolve_output_compatibility(
        self,
        test_output: str,
        expected_format: str = "plain",
    ) -> dict[str, Any]:
        """Resolve compatibility between Rich and plain text output formats.

        Args:
            test_output: Raw CLI output from test execution
            expected_format: Expected output format for test validation

        Returns:
            Dictionary with normalized output and compatibility status

        Raises:
            TypeError: If test_output is not a string
            ValueError: If expected_format is invalid

        Example:
            >>> resolver = OutputCompatibilityResolver()
            >>> result = resolver.resolve_output_compatibility(
            ...     "[bold]Success[/bold]",
            ...     "plain"
            ... )
            >>> print(result["normalized_output"])
            "Success"
        """
        if not isinstance(test_output, str):
            raise TypeError(f"test_output must be a string, got {type(test_output)}")

        valid_formats = {"rich", "plain"}
        if expected_format not in valid_formats:
            raise ValueError(
                f"Invalid expected_format '{expected_format}'. Must be one of: {valid_formats}"
            )

        debug_logger.log(
            "INFO",
            "Resolving output compatibility",
            output_length=len(test_output),
            expected_format=expected_format,
        )

        try:
            # Extract metadata about the original output
            metadata = extract_formatting_metadata(test_output)

            # Normalize output based on expected format
            normalized_output = normalize_output_for_testing(
                test_output, mode=expected_format
            )

            # Determine compatibility status
            compatibility_status = self._assess_compatibility(metadata, expected_format)

            result = {
                "normalized_output": normalized_output,
                "compatibility_status": compatibility_status,
                "original_metadata": metadata,
                "expected_format": expected_format,
                "transformation_applied": metadata["detected_format"]
                != expected_format,
            }

            # Track processed output for analysis
            self.processed_outputs.append(
                {
                    "original_length": len(test_output),
                    "normalized_length": len(normalized_output),
                    "original_format": metadata["detected_format"],
                    "target_format": expected_format,
                    "success": compatibility_status,
                }
            )

            debug_logger.log(
                "INFO",
                "Output compatibility resolved",
                compatibility_status=compatibility_status,
                transformation_applied=result["transformation_applied"],
            )

            return result

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to resolve output compatibility",
                error=str(e),
            )
            raise

    def validate_cli_test_result(
        self,
        test_result: CLITestResult,
        expected_outputs: list[str],
    ) -> bool:
        """Validate CLI test result with compatibility resolution.

        Args:
            test_result: CLI test result from command execution
            expected_outputs: List of expected output patterns

        Returns:
            True if test result is valid after compatibility resolution

        Raises:
            TypeError: If test_result is not CLITestResult
            ValueError: If expected_outputs is empty

        Example:
            >>> resolver = OutputCompatibilityResolver()
            >>> # Assume we have a CLI test result
            >>> is_valid = resolver.validate_cli_test_result(result, ["Success"])
        """
        if not isinstance(test_result, CLITestResult):
            raise TypeError(
                f"test_result must be CLITestResult, got {type(test_result)}"
            )

        if not expected_outputs:
            raise ValueError("expected_outputs cannot be empty")

        debug_logger.log(
            "INFO",
            "Validating CLI test result with compatibility resolution",
            command=test_result.command,
            exit_code=test_result.exit_code,
            expected_pattern_count=len(expected_outputs),
        )

        try:
            # Normalize the test output
            compatibility_result = self.resolve_output_compatibility(
                test_result.output, expected_format="plain"
            )

            normalized_output = compatibility_result["normalized_output"]

            # Check if all expected patterns are found in normalized output
            patterns_found = []
            for expected_pattern in expected_outputs:
                if expected_pattern in normalized_output:
                    patterns_found.append(expected_pattern)

            validation_success = len(patterns_found) == len(expected_outputs)

            debug_logger.log(
                "INFO",
                "CLI test result validation completed",
                patterns_found=len(patterns_found),
                total_patterns=len(expected_outputs),
                validation_success=validation_success,
            )

            return validation_success

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "CLI test result validation failed",
                error=str(e),
            )
            return False

    def get_compatibility_report(self) -> dict[str, Any]:
        """Generate compatibility analysis report.

        Returns:
            Dictionary with compatibility statistics and analysis

        Example:
            >>> resolver = OutputCompatibilityResolver()
            >>> # After processing some outputs...
            >>> report = resolver.get_compatibility_report()
            >>> print(f"Success rate: {report['success_rate']}")
        """
        if not self.processed_outputs:
            return {
                "total_processed": 0,
                "success_rate": 0.0,
                "transformations_applied": 0,
                "format_distribution": {},
                "message": "No outputs have been processed yet",
            }

        total_processed = len(self.processed_outputs)
        successful_resolutions = sum(
            1 for output in self.processed_outputs if output["success"]
        )
        transformations_applied = sum(
            1
            for output in self.processed_outputs
            if output["original_format"] != output["target_format"]
        )

        # Analyze format distribution
        format_distribution: dict[str, int] = {}
        for output in self.processed_outputs:
            orig_format = output["original_format"]
            format_distribution[orig_format] = (
                format_distribution.get(orig_format, 0) + 1
            )

        report = {
            "total_processed": total_processed,
            "successful_resolutions": successful_resolutions,
            "success_rate": successful_resolutions / total_processed
            if total_processed > 0
            else 0.0,
            "transformations_applied": transformations_applied,
            "transformation_rate": transformations_applied / total_processed
            if total_processed > 0
            else 0.0,
            "format_distribution": format_distribution,
        }

        debug_logger.log(
            "INFO",
            "Generated compatibility report",
            **report,
        )

        return report

    def _assess_compatibility(
        self, metadata: dict[str, Any], expected_format: str
    ) -> bool:
        """Assess compatibility between detected and expected formats.

        Args:
            metadata: Formatting metadata from extract_formatting_metadata
            expected_format: Expected output format

        Returns:
            True if formats are compatible or can be resolved
        """
        detected_format = metadata["detected_format"]

        # Same format is always compatible
        if detected_format == expected_format:
            return True

        # Rich to plain conversion is always supported
        if detected_format == "rich" and expected_format == "plain":
            return True

        # Plain to rich conversion is not meaningful but not an error
        if detected_format == "plain" and expected_format == "rich":
            return True

        return False


def create_output_compatibility_resolver(
    default_mode: str = "auto",
) -> OutputCompatibilityResolver:
    """Create output compatibility resolver instance.

    Args:
        default_mode: Default normalization mode

    Returns:
        OutputCompatibilityResolver instance

    Example:
        >>> resolver = create_output_compatibility_resolver("plain")
        >>> result = resolver.resolve_output_compatibility("[bold]Text[/bold]")
    """
    return OutputCompatibilityResolver(default_mode)


def batch_resolve_compatibility(
    outputs: list[tuple[str, str]],
    resolver: OutputCompatibilityResolver | None = None,
) -> list[dict[str, Any]]:
    """Batch resolve compatibility for multiple outputs.

    Args:
        outputs: List of (output_text, expected_format) tuples
        resolver: Optional resolver instance (creates new if None)

    Returns:
        List of compatibility resolution results

    Raises:
        ValueError: If outputs list is empty
        TypeError: If outputs format is invalid

    Example:
        >>> outputs = [("[bold]Success[/bold]", "plain"), ("Error", "plain")]
        >>> results = batch_resolve_compatibility(outputs)
        >>> print(len(results))
        2
    """
    if not outputs:
        raise ValueError("outputs list cannot be empty")

    if not isinstance(outputs, list):
        raise TypeError(f"outputs must be a list, got {type(outputs)}")

    # Validate output format
    for i, output_pair in enumerate(outputs):
        if not isinstance(output_pair, tuple) or len(output_pair) != 2:
            raise TypeError(
                f"outputs[{i}] must be a tuple of (str, str), got {type(output_pair)}"
            )

    if resolver is None:
        resolver = create_output_compatibility_resolver()

    debug_logger.log(
        "INFO",
        "Starting batch compatibility resolution",
        batch_size=len(outputs),
    )

    results = []
    for output_text, expected_format in outputs:
        try:
            result = resolver.resolve_output_compatibility(output_text, expected_format)
            results.append(result)
        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to resolve compatibility for output in batch",
                error=str(e),
            )
            # Add error result to maintain batch consistency
            results.append(
                {
                    "normalized_output": output_text,  # Fallback to original
                    "compatibility_status": False,
                    "error": str(e),
                }
            )

    debug_logger.log(
        "INFO",
        "Completed batch compatibility resolution",
        total_processed=len(results),
        successful_resolutions=sum(
            1 for r in results if r.get("compatibility_status", False)
        ),
    )

    return results
