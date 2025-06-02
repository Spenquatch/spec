import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from ..exceptions import SpecBatchProcessingError
from ..config.settings import get_settings, SpecSettings
from ..core.workflow_orchestrator import SpecWorkflowOrchestrator
from ..logging.debug import debug_logger
from .change_detector import FileChangeDetector
from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy
from .processing_pipeline import FileProcessingPipeline, FileProcessingResult
from .progress_events import ProgressReporter, ProgressEventType, progress_reporter

class BatchProcessingOptions:
    """Configuration options for batch processing."""
    
    def __init__(self,
                 max_files: Optional[int] = None,
                 max_parallel: int = 1,
                 force_regenerate: bool = False,
                 skip_unchanged: bool = True,
                 conflict_strategy: Optional[ConflictResolutionStrategy] = None,
                 create_backups: bool = True,
                 auto_commit: bool = False,
                 custom_variables: Optional[Dict[str, Any]] = None):
        self.max_files = max_files
        self.max_parallel = max_parallel
        self.force_regenerate = force_regenerate
        self.skip_unchanged = skip_unchanged
        self.conflict_strategy = conflict_strategy or ConflictResolutionStrategy.MERGE_INTELLIGENT
        self.create_backups = create_backups
        self.auto_commit = auto_commit
        self.custom_variables = custom_variables or {}

class BatchProcessingResult:
    """Result of batch processing operation."""
    
    def __init__(self):
        self.success = False
        self.total_files = 0
        self.successful_files: List[Path] = []
        self.failed_files: List[Path] = []
        self.skipped_files: List[Path] = []
        self.file_results: Dict[str, FileProcessingResult] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.workflow_id: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "total_files": self.total_files,
            "successful_count": len(self.successful_files),
            "failed_count": len(self.failed_files),
            "skipped_count": len(self.skipped_files),
            "successful_files": [str(f) for f in self.successful_files],
            "failed_files": [str(f) for f in self.failed_files],
            "skipped_files": [str(f) for f in self.skipped_files],
            "errors": self.errors,
            "warnings": self.warnings,
            "duration": self.duration,
            "workflow_id": self.workflow_id,
        }

class BatchFileProcessor:
    """Processes multiple files in batch with progress tracking and error recovery."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.change_detector = FileChangeDetector(self.settings)
        self.conflict_resolver = ConflictResolver(self.settings)
        self.workflow_orchestrator = SpecWorkflowOrchestrator(self.settings)
        self.progress_reporter = progress_reporter
        
        # Create processing pipeline
        from ..templates.generator import SpecContentGenerator
        content_generator = SpecContentGenerator(self.settings)
        
        self.pipeline = FileProcessingPipeline(
            content_generator=content_generator,
            change_detector=self.change_detector,
            conflict_resolver=self.conflict_resolver,
            progress_reporter=self.progress_reporter
        )
        
        debug_logger.log("INFO", "BatchFileProcessor initialized")
    
    def process_files(self,
                     file_paths: List[Path],
                     options: Optional[BatchProcessingOptions] = None,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None) -> BatchProcessingResult:
        """Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            options: Batch processing options
            progress_callback: Optional progress callback function
            
        Returns:
            BatchProcessingResult with processing outcomes
        """
        options = options or BatchProcessingOptions()
        
        debug_logger.log("INFO", "Starting batch file processing",
                        total_files=len(file_paths),
                        max_files=options.max_files,
                        force_regenerate=options.force_regenerate)
        
        result = BatchProcessingResult()
        result.start_time = time.time()
        
        try:
            with debug_logger.timer("batch_file_processing"):
                # Limit files if specified
                files_to_process = file_paths
                if options.max_files and len(file_paths) > options.max_files:
                    files_to_process = file_paths[:options.max_files]
                    result.warnings.append(f"Limited to {options.max_files} files")
                
                result.total_files = len(files_to_process)
                
                # Filter files that need processing (unless force regenerate)
                if not options.force_regenerate and options.skip_unchanged:
                    files_needing_processing = self.change_detector.get_files_needing_processing(
                        files_to_process, force_all=False
                    )
                    
                    # Track skipped files
                    skipped = set(files_to_process) - set(files_needing_processing)
                    result.skipped_files.extend(skipped)
                    
                    files_to_process = files_needing_processing
                    
                    debug_logger.log("INFO", "Filtered files needing processing",
                                   original_count=result.total_files,
                                   processing_count=len(files_to_process),
                                   skipped_count=len(skipped))
                
                # Emit batch started event
                self.progress_reporter.emit_batch_started(
                    len(files_to_process),
                    f"Processing {len(files_to_process)} files"
                )
                
                # Process files
                self._process_files_sequentially(
                    files_to_process, options, result, progress_callback
                )
                
                # Handle post-processing
                if options.auto_commit and result.successful_files:
                    self._handle_auto_commit(result, options)
                
                # Finalize result
                result.success = len(result.errors) == 0
                result.end_time = time.time()
                
                # Emit batch completed event
                self.progress_reporter.emit_batch_completed(
                    result.total_files,
                    len(result.successful_files),
                    len(result.failed_files),
                    result.duration
                )
            
            debug_logger.log("INFO", "Batch file processing completed",
                           total_files=result.total_files,
                           successful=len(result.successful_files),
                           failed=len(result.failed_files),
                           duration=result.duration)
            
            return result
            
        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            debug_logger.log("ERROR", error_msg)
            
            result.errors.append(error_msg)
            result.success = False
            result.end_time = time.time()
            
            # Emit batch failed event
            self.progress_reporter.emit_event(
                ProgressEventType.BATCH_FAILED,
                message=error_msg
            )
            
            return result
    
    def _process_files_sequentially(self,
                                   files: List[Path],
                                   options: BatchProcessingOptions,
                                   result: BatchProcessingResult,
                                   progress_callback: Optional[Callable[[int, int, str], None]]) -> None:
        """Process files sequentially."""
        for i, file_path in enumerate(files):
            try:
                # Emit file started event
                self.progress_reporter.emit_file_started(file_path, i, len(files))
                
                # Progress callback
                if progress_callback:
                    progress_callback(i, len(files), f"Processing {file_path.name}")
                
                # Process single file
                file_result = self.pipeline.process_file(
                    file_path=file_path,
                    custom_variables=options.custom_variables,
                    conflict_strategy=options.conflict_strategy,
                    force_regenerate=options.force_regenerate
                )
                
                # Store result
                result.file_results[str(file_path)] = file_result
                
                # Categorize result
                if file_result.success:
                    result.successful_files.append(file_path)
                    
                    # Emit file completed event
                    self.progress_reporter.emit_file_completed(file_path, i, len(files), True)
                else:
                    result.failed_files.append(file_path)
                    result.errors.extend(file_result.errors)
                    
                    # Emit file failed event
                    self.progress_reporter.emit_file_completed(file_path, i, len(files), False)
                    
                    # Emit error event
                    error_msg = f"Processing failed for {file_path}: {'; '.join(file_result.errors)}"
                    self.progress_reporter.emit_error(error_msg, file_path)
                
                # Add warnings
                result.warnings.extend(file_result.warnings)
                
            except Exception as e:
                error_msg = f"Unexpected error processing {file_path}: {e}"
                debug_logger.log("ERROR", error_msg)
                
                result.failed_files.append(file_path)
                result.errors.append(error_msg)
                
                # Emit error event
                self.progress_reporter.emit_error(error_msg, file_path, e)
        
        # Final progress callback
        if progress_callback:
            progress_callback(len(files), len(files), "Completed")
    
    def _handle_auto_commit(self, result: BatchProcessingResult, options: BatchProcessingOptions) -> None:
        """Handle automatic commit of successful files."""
        try:
            debug_logger.log("INFO", "Handling auto-commit",
                           successful_files=len(result.successful_files))
            
            # Use workflow orchestrator for commit
            workflow_result = self.workflow_orchestrator.generate_specs_for_files(
                result.successful_files,
                custom_variables=options.custom_variables,
                auto_commit=True,
                create_backup=options.create_backups
            )
            
            result.workflow_id = workflow_result.get("workflow_id")
            
            if not workflow_result.get("success"):
                result.warnings.append("Auto-commit failed")
                
        except Exception as e:
            result.warnings.append(f"Auto-commit failed: {e}")
            debug_logger.log("WARNING", "Auto-commit failed", error=str(e))
    
    def estimate_batch_processing(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Estimate batch processing requirements.
        
        Args:
            file_paths: List of files to estimate
            
        Returns:
            Dictionary with processing estimates
        """
        return self.pipeline.get_processing_estimate(file_paths)
    
    def validate_batch_processing(self,
                                file_paths: List[Path],
                                options: Optional[BatchProcessingOptions] = None) -> List[str]:
        """Validate batch processing requirements.
        
        Args:
            file_paths: List of files to validate
            options: Processing options
            
        Returns:
            List of validation issues
        """
        issues = []
        options = options or BatchProcessingOptions()
        
        # Validate file count
        if not file_paths:
            issues.append("No files provided for processing")
            return issues
        
        # Validate individual files
        for file_path in file_paths:
            file_issues = self.pipeline.validate_file_for_processing(file_path)
            issues.extend(file_issues)
        
        # Validate conflict strategy
        if options.conflict_strategy:
            try:
                # Test if strategy is valid
                ConflictResolutionStrategy(options.conflict_strategy.value)
            except ValueError:
                issues.append(f"Invalid conflict strategy: {options.conflict_strategy}")
        
        return issues
    
    def get_processing_summary(self, result: BatchProcessingResult) -> Dict[str, Any]:
        """Get a summary of batch processing results.
        
        Args:
            result: Batch processing result
            
        Returns:
            Summary dictionary
        """
        summary = {
            "overview": {
                "total_files": result.total_files,
                "successful": len(result.successful_files),
                "failed": len(result.failed_files),
                "skipped": len(result.skipped_files),
                "success_rate": (
                    len(result.successful_files) / result.total_files * 100
                    if result.total_files > 0 else 0
                ),
                "duration": result.duration,
            },
            "conflicts": {
                "files_with_conflicts": 0,
                "conflict_types": {},
                "resolution_strategies": {},
            },
            "errors": {
                "total_errors": len(result.errors),
                "error_types": {},
            },
            "warnings": {
                "total_warnings": len(result.warnings),
            },
        }
        
        # Analyze file results for conflicts and errors
        for file_result in result.file_results.values():
            if file_result.conflict_info:
                summary["conflicts"]["files_with_conflicts"] += 1
                
                conflict_type = file_result.conflict_info.conflict_type.value
                summary["conflicts"]["conflict_types"][conflict_type] = \
                    summary["conflicts"]["conflict_types"].get(conflict_type, 0) + 1
                
                if file_result.resolution_strategy:
                    strategy = file_result.resolution_strategy.value
                    summary["conflicts"]["resolution_strategies"][strategy] = \
                        summary["conflicts"]["resolution_strategies"].get(strategy, 0) + 1
            
            # Analyze errors (simplified)
            for error in file_result.errors:
                if "permission" in error.lower():
                    error_type = "permission"
                elif "conflict" in error.lower():
                    error_type = "conflict"
                elif "generation" in error.lower():
                    error_type = "generation"
                else:
                    error_type = "other"
                
                summary["errors"]["error_types"][error_type] = \
                    summary["errors"]["error_types"].get(error_type, 0) + 1
        
        return summary

# Convenience functions
def process_files_batch(file_paths: List[Path],
                       **kwargs) -> BatchProcessingResult:
    """Convenience function for batch processing."""
    processor = BatchFileProcessor()
    options = BatchProcessingOptions(**kwargs)
    return processor.process_files(file_paths, options)

def estimate_processing_time(file_paths: List[Path]) -> Dict[str, Any]:
    """Convenience function for processing estimation."""
    processor = BatchFileProcessor()
    return processor.estimate_batch_processing(file_paths)