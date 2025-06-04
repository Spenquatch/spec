from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ..logging.debug import debug_logger
from ..templates.generator import SpecContentGenerator
from ..templates.loader import load_template
from ..utils.error_utils import create_error_context, handle_os_error
from .change_detector import FileChangeDetector
from .conflict_resolver import (
    ConflictInfo,
    ConflictResolutionStrategy,
    ConflictResolver,
)
from .progress_events import ProcessingStage, ProgressReporter


class FileProcessingResult:
    """Result of processing a single file."""

    def __init__(
        self,
        file_path: Path,
        success: bool,
        generated_files: Optional[Dict[str, Path]] = None,
        conflict_info: Optional[ConflictInfo] = None,
        resolution_strategy: Optional[ConflictResolutionStrategy] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.file_path = file_path
        self.success = success
        self.generated_files = generated_files or {}
        self.conflict_info = conflict_info
        self.resolution_strategy = resolution_strategy
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": str(self.file_path),
            "success": self.success,
            "generated_files": {k: str(v) for k, v in self.generated_files.items()},
            "has_conflict": self.conflict_info is not None,
            "conflict_type": self.conflict_info.conflict_type.value
            if self.conflict_info
            else None,
            "resolution_strategy": self.resolution_strategy.value
            if self.resolution_strategy
            else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class FileProcessingPipeline:
    """Pipeline for processing individual files through all stages."""

    def __init__(
        self,
        content_generator: SpecContentGenerator,
        change_detector: FileChangeDetector,
        conflict_resolver: ConflictResolver,
        progress_reporter: ProgressReporter,
    ):
        self.content_generator = content_generator
        self.change_detector = change_detector
        self.conflict_resolver = conflict_resolver
        self.progress_reporter = progress_reporter

        debug_logger.log("INFO", "FileProcessingPipeline initialized")

    def process_file(
        self,
        file_path: Path,
        custom_variables: Optional[Dict[str, Any]] = None,
        conflict_strategy: Optional[ConflictResolutionStrategy] = None,
        force_regenerate: bool = False,
    ) -> FileProcessingResult:
        """Process a single file through the complete pipeline.

        Args:
            file_path: Path to the file to process
            custom_variables: Optional custom template variables
            conflict_strategy: Strategy for conflict resolution
            force_regenerate: Whether to force regeneration even if unchanged

        Returns:
            FileProcessingResult with processing outcome
        """
        debug_logger.log(
            "INFO", "Processing file through pipeline", file_path=str(file_path)
        )

        result = FileProcessingResult(file_path, success=False)

        try:
            with debug_logger.timer("file_processing_pipeline"):
                # Stage 1: Change Detection
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CHANGE_DETECTION
                )

                if not force_regenerate and not self.change_detector.has_file_changed(
                    file_path
                ):
                    result.success = True
                    result.warnings.append("File unchanged, skipping")
                    debug_logger.log(
                        "INFO", "File unchanged, skipping", file_path=str(file_path)
                    )
                    return result

                # Stage 2: Content Generation
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CONTENT_GENERATION
                )

                template = load_template()
                generation_result = self._generate_content(
                    file_path, template, custom_variables
                )

                if not generation_result["success"]:
                    result.errors.extend(generation_result["errors"])
                    return result

                generated_files = generation_result["generated_files"]

                # Stage 3: Conflict Detection and Resolution
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CONFLICT_DETECTION
                )

                conflicts_resolved = self._handle_conflicts(
                    generated_files, conflict_strategy
                )

                if conflicts_resolved["conflicts"]:
                    result.conflict_info = conflicts_resolved["conflicts"][
                        0
                    ]  # First conflict for reference
                    result.resolution_strategy = conflicts_resolved["strategy_used"]

                if not conflicts_resolved["success"]:
                    result.errors.extend(conflicts_resolved["errors"])
                    return result

                # Stage 4: Cache Update
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CACHE_UPDATE
                )

                self.change_detector.update_file_cache(file_path)

                # Success
                result.success = True
                result.generated_files = generated_files
                result.warnings.extend(conflicts_resolved["warnings"])

            debug_logger.log(
                "INFO",
                "File processing completed successfully",
                file_path=str(file_path),
            )

            return result

        except Exception as e:
            if isinstance(e, OSError):
                formatted_error = handle_os_error(e)
                context = create_error_context(file_path)
                context.update(
                    {
                        "operation": "file_processing_pipeline",
                        "force_regenerate": force_regenerate,
                    }
                )
                debug_logger.log(
                    "ERROR",
                    f"File processing pipeline failed: {formatted_error}",
                    **context,
                )
                error_msg = f"File processing failed: {formatted_error}"
            else:
                error_msg = f"File processing failed: {e}"
                debug_logger.log("ERROR", error_msg, file_path=str(file_path))
            result.errors.append(error_msg)
            return result

    def _generate_content(
        self, file_path: Path, template: Any, custom_variables: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate content for the file."""
        try:
            generated_files = self.content_generator.generate_spec_content(
                file_path=file_path,
                template=template,
                custom_variables=custom_variables,
                backup_existing=False,  # Conflict resolution handles backups
            )

            return {
                "success": True,
                "generated_files": generated_files,
                "errors": [],
            }

        except Exception as e:
            return {
                "success": False,
                "generated_files": {},
                "errors": [f"Content generation failed: {e}"],
            }

    def _handle_conflicts(
        self,
        generated_files: Dict[str, Path],
        strategy: Optional[ConflictResolutionStrategy],
    ) -> Dict[str, Any]:
        """Handle conflicts for generated files."""
        conflicts = []
        resolved_conflicts = []
        errors = []
        warnings = []
        strategy_used = None

        try:
            # Check each generated file for conflicts
            for _file_type, file_path in generated_files.items():
                if not file_path.exists():
                    continue  # No conflict for new files

                # Read the content that would be written
                try:
                    new_content = file_path.read_text(encoding="utf-8")
                except OSError as e:
                    formatted_error = handle_os_error(e)
                    context = create_error_context(file_path)
                    context.update(
                        {
                            "operation": "conflict_handling_read",
                            "stage": "generated_content_read",
                        }
                    )
                    debug_logger.log(
                        "ERROR",
                        f"Conflict handling failed: {formatted_error}",
                        **context,
                    )
                    errors.append(
                        f"Could not read generated content for {file_path}: {formatted_error}"
                    )
                    continue

                # Detect conflict
                conflict = self.conflict_resolver.detect_conflict(
                    file_path, new_content
                )
                if conflict:
                    conflicts.append(conflict)

                    # Emit conflict detected event
                    self.progress_reporter.emit_conflict_detected(
                        file_path,
                        conflict.conflict_type.value,
                        strategy.value if strategy else None,
                    )

                    # Resolve conflict
                    resolution_result = self.conflict_resolver.resolve_conflict(
                        conflict, strategy, create_backup=True
                    )

                    if resolution_result.success:
                        resolved_conflicts.append(resolution_result)
                        strategy_used = resolution_result.strategy_used
                        warnings.extend(resolution_result.warnings)
                    else:
                        errors.extend(resolution_result.errors)

            return {
                "success": len(errors) == 0,
                "conflicts": conflicts,
                "resolved_conflicts": resolved_conflicts,
                "strategy_used": strategy_used,
                "errors": errors,
                "warnings": warnings,
            }

        except Exception as e:
            return {
                "success": False,
                "conflicts": conflicts,
                "resolved_conflicts": [],
                "strategy_used": None,
                "errors": [f"Conflict handling failed: {e}"],
                "warnings": warnings,
            }

    def validate_file_for_processing(self, file_path: Path) -> List[str]:
        """Validate that a file can be processed.

        Args:
            file_path: Path to validate

        Returns:
            List of validation issues
        """
        issues = []

        # Check file exists
        if not file_path.exists():
            issues.append(f"File does not exist: {file_path}")
            return issues

        # Check file is readable
        try:
            file_path.read_text(encoding="utf-8")
        except OSError as e:
            formatted_error = handle_os_error(e)
            issues.append(f"Cannot read file {file_path}: {formatted_error}")

        # Check file size
        try:
            size = file_path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB limit
            if size > max_size:
                issues.append(f"File too large: {size} bytes (max {max_size})")
        except OSError as e:
            formatted_error = handle_os_error(e)
            issues.append(f"Cannot get file stats for {file_path}: {formatted_error}")

        return issues

    def get_processing_estimate(self, files: List[Path]) -> Dict[str, Any]:
        """Estimate processing requirements for a list of files.

        Args:
            files: List of files to estimate

        Returns:
            Dictionary with processing estimates
        """
        estimate: Dict[str, Any] = {
            "total_files": len(files),
            "processable_files": 0,
            "files_needing_processing": 0,
            "estimated_duration_seconds": 0,
            "validation_issues": [],
        }

        for file_path in files:
            issues = self.validate_file_for_processing(file_path)
            if issues:
                cast(List[str], estimate["validation_issues"]).extend(issues)
                continue

            estimate["processable_files"] = cast(int, estimate["processable_files"]) + 1

            # Check if file needs processing
            if self.change_detector.has_file_changed(file_path):
                estimate["files_needing_processing"] = (
                    cast(int, estimate["files_needing_processing"]) + 1
                )

                # Rough time estimate (2 seconds per file)
                estimate["estimated_duration_seconds"] = (
                    cast(int, estimate["estimated_duration_seconds"]) + 2
                )

        return estimate
