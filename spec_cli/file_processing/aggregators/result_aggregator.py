"""Result aggregation for batch file processing."""

from pathlib import Path
from typing import Any, cast

from ...utils.workflow_utils import create_workflow_result
from ..processing_pipeline import FileProcessingResult


class BatchResultAggregator:
    """Aggregates and analyzes batch file processing results."""

    def __init__(self) -> None:
        """Initialize the batch result aggregator."""
        pass

    def aggregate_results(
        self, file_results: dict[str, FileProcessingResult]
    ) -> dict[str, Any]:
        """Aggregate file processing results into comprehensive summary.

        Args:
            file_results: Dictionary mapping file paths to processing results

        Returns:
            Dictionary containing aggregated summary and statistics

        Example:
            >>> aggregator = BatchResultAggregator()
            >>> results = {"file1.py": FileProcessingResult(...)}
            >>> summary = aggregator.aggregate_results(results)
            >>> print(summary["statistics"]["success_rate"])
        """
        if not file_results:
            return self._create_empty_summary()

        # Categorize files by outcome
        successful_files, failed_files, skipped_files = self._categorize_files(
            file_results
        )

        # Analyze conflicts and resolutions
        conflict_analysis = self._analyze_conflicts(file_results)

        # Classify error types
        error_analysis = self._classify_errors(file_results)

        # Generate statistics
        statistics = self._calculate_statistics(
            len(file_results), successful_files, failed_files, skipped_files
        )

        return {
            "summary": {
                "overview": {
                    "total_files": len(file_results),
                    "successful": len(successful_files),
                    "failed": len(failed_files),
                    "skipped": len(skipped_files),
                },
                "conflicts": conflict_analysis,
                "errors": error_analysis,
            },
            "statistics": statistics,
        }

    def create_workflow_summary(
        self, successful_files: list[Path], workflow_id: str | None = None
    ) -> dict[str, Any]:
        """Create workflow result summary for successful files.

        Args:
            successful_files: List of successfully processed files
            workflow_id: Optional workflow identifier

        Returns:
            Workflow result dictionary from create_workflow_result helper
        """
        return create_workflow_result(successful_files, True, workflow_id)

    def _create_empty_summary(self) -> dict[str, Any]:
        """Create empty summary for no results."""
        return {
            "summary": {
                "overview": {
                    "total_files": 0,
                    "successful": 0,
                    "failed": 0,
                    "skipped": 0,
                },
                "conflicts": {
                    "files_with_conflicts": 0,
                    "conflict_types": {},
                    "resolution_strategies": {},
                },
                "errors": {
                    "total_errors": 0,
                    "error_types": {},
                },
            },
            "statistics": {
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "skip_rate": 0.0,
            },
        }

    def _categorize_files(
        self, file_results: dict[str, FileProcessingResult]
    ) -> tuple[list[str], list[str], list[str]]:
        """Categorize files into successful, failed, and skipped lists."""
        successful_files = []
        failed_files = []
        skipped_files = []

        for file_path, result in file_results.items():
            if result.success:
                successful_files.append(file_path)
            elif result.metadata.get("skipped", False):
                skipped_files.append(file_path)
            else:
                failed_files.append(file_path)

        return successful_files, failed_files, skipped_files

    def _analyze_conflicts(
        self, file_results: dict[str, FileProcessingResult]
    ) -> dict[str, Any]:
        """Analyze conflict patterns and resolutions."""
        conflict_analysis = {
            "files_with_conflicts": 0,
            "conflict_types": {},
            "resolution_strategies": {},
        }

        for file_result in file_results.values():
            if file_result.conflict_info:
                conflict_analysis["files_with_conflicts"] = (
                    cast(int, conflict_analysis["files_with_conflicts"]) + 1
                )

                # Track conflict types
                conflict_type = file_result.conflict_info.conflict_type.value
                conflict_types = cast(
                    dict[str, int], conflict_analysis["conflict_types"]
                )
                conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1

                # Track resolution strategies
                if file_result.resolution_strategy:
                    strategy = file_result.resolution_strategy.value
                    resolution_strategies = cast(
                        dict[str, int], conflict_analysis["resolution_strategies"]
                    )
                    resolution_strategies[strategy] = (
                        resolution_strategies.get(strategy, 0) + 1
                    )

        return conflict_analysis

    def _classify_errors(
        self, file_results: dict[str, FileProcessingResult]
    ) -> dict[str, Any]:
        """Classify error types from file processing results."""
        error_analysis = {
            "total_errors": 0,
            "error_types": {},
        }

        for file_result in file_results.values():
            for error in file_result.errors:
                error_analysis["total_errors"] = (
                    cast(int, error_analysis["total_errors"]) + 1
                )

                # Classify error type based on content
                if "permission" in error.lower():
                    error_type = "permission"
                elif "conflict" in error.lower():
                    error_type = "conflict"
                elif "generation" in error.lower():
                    error_type = "generation"
                else:
                    error_type = "other"

                error_types = cast(dict[str, int], error_analysis["error_types"])
                error_types[error_type] = error_types.get(error_type, 0) + 1

        return error_analysis

    def _calculate_statistics(
        self,
        total_files: int,
        successful_files: list[str],
        failed_files: list[str],
        skipped_files: list[str],
    ) -> dict[str, float]:
        """Calculate processing statistics."""
        if total_files == 0:
            return {
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "skip_rate": 0.0,
            }

        return {
            "success_rate": len(successful_files) / total_files * 100,
            "failure_rate": len(failed_files) / total_files * 100,
            "skip_rate": len(skipped_files) / total_files * 100,
        }
