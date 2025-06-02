from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from ..exceptions import SpecConflictError, SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..file_system.directory_manager import DirectoryManager
from ..logging.debug import debug_logger
from .change_detector import FileChangeDetector
from .merge_helpers import ContentMerger

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving file conflicts."""
    KEEP_OURS = "keep_ours"          # Keep existing content
    KEEP_THEIRS = "keep_theirs"      # Use new content
    MERGE_INTELLIGENT = "merge_intelligent"  # Intelligent merge
    MERGE_APPEND = "merge_append"    # Append new to existing
    MERGE_PREPEND = "merge_prepend"  # Prepend new to existing
    SKIP = "skip"                   # Skip processing this file
    PROMPT = "prompt"               # Prompt user for decision
    BACKUP_AND_REPLACE = "backup_and_replace"  # Backup existing, use new
    OVERWRITE = "overwrite"         # Overwrite existing content
    FAIL = "fail"                   # Fail on conflict

class ConflictType(Enum):
    """Types of conflicts that can occur."""
    FILE_EXISTS = "file_exists"         # File already exists
    CONTENT_MODIFIED = "content_modified"  # File has been modified
    STRUCTURE_CONFLICT = "structure_conflict"  # Structural differences
    PERMISSION_DENIED = "permission_denied"  # Cannot write to file
    SIZE_LIMIT = "size_limit"           # File size limits exceeded

class ConflictInfo:
    """Information about a detected conflict."""
    
    def __init__(self,
                 conflict_type: ConflictType,
                 file_path: Path,
                 existing_content: Optional[str] = None,
                 new_content: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.conflict_type = conflict_type
        self.file_path = file_path
        self.existing_content = existing_content
        self.new_content = new_content
        self.metadata = metadata or {}
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_type": self.conflict_type.value,
            "file_path": str(self.file_path),
            "existing_content_length": len(self.existing_content) if self.existing_content else 0,
            "new_content_length": len(self.new_content) if self.new_content else 0,
            "metadata": self.metadata,
            "detected_at": self.detected_at.isoformat(),
        }

class ConflictResolutionResult:
    """Result of conflict resolution."""
    
    def __init__(self,
                 success: bool,
                 strategy_used: ConflictResolutionStrategy,
                 final_content: Optional[str] = None,
                 backup_path: Optional[Path] = None,
                 errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None):
        self.success = success
        self.strategy_used = strategy_used
        self.final_content = final_content
        self.backup_path = backup_path
        self.errors = errors or []
        self.warnings = warnings or []
        self.resolved_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "strategy_used": self.strategy_used.value,
            "final_content_length": len(self.final_content) if self.final_content else 0,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "resolved_at": self.resolved_at.isoformat(),
        }

class ConflictResolver:
    """Resolves file conflicts using configurable strategies."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.directory_manager = DirectoryManager(self.settings)
        self.change_detector = FileChangeDetector(self.settings)
        self.content_merger = ContentMerger()
        
        # Default strategy for different conflict types
        self.default_strategies = {
            ConflictType.FILE_EXISTS: ConflictResolutionStrategy.MERGE_INTELLIGENT,
            ConflictType.CONTENT_MODIFIED: ConflictResolutionStrategy.MERGE_INTELLIGENT,
            ConflictType.STRUCTURE_CONFLICT: ConflictResolutionStrategy.KEEP_THEIRS,
            ConflictType.PERMISSION_DENIED: ConflictResolutionStrategy.SKIP,
            ConflictType.SIZE_LIMIT: ConflictResolutionStrategy.SKIP,
        }
        
        debug_logger.log("INFO", "ConflictResolver initialized")
    
    def detect_conflict(self, 
                       file_path: Path,
                       new_content: str) -> Optional[ConflictInfo]:
        """Detect if a conflict exists for the given file and content.
        
        Args:
            file_path: Path to the file
            new_content: New content to write
            
        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        debug_logger.log("DEBUG", "Detecting conflicts",
                        file_path=str(file_path))
        
        # Check if file exists
        if not file_path.exists():
            return None  # No conflict for new files
        
        # Check permissions
        import os
        if not os.access(file_path, os.W_OK):
            return ConflictInfo(
                ConflictType.PERMISSION_DENIED,
                file_path,
                metadata={"reason": "No write permission"}
            )
        
        # Read existing content
        try:
            existing_content = file_path.read_text(encoding='utf-8')
        except OSError as e:
            return ConflictInfo(
                ConflictType.PERMISSION_DENIED,
                file_path,
                metadata={"reason": f"Cannot read file: {e}"}
            )
        
        # Check for size limits (configurable)
        max_size = getattr(self.settings, 'max_file_size', 10 * 1024 * 1024)  # 10MB default
        if len(new_content) > max_size:
            return ConflictInfo(
                ConflictType.SIZE_LIMIT,
                file_path,
                existing_content=existing_content,
                new_content=new_content,
                metadata={"size": len(new_content), "limit": max_size}
            )
        
        # Check if content has been modified
        if existing_content != new_content:
            # Detect structural conflicts
            conflicts = self.content_merger.detect_conflicts(existing_content, new_content)
            
            if any(c["severity"] == "high" for c in conflicts):
                conflict_type = ConflictType.STRUCTURE_CONFLICT
            elif existing_content.strip():  # Non-empty existing file
                conflict_type = ConflictType.CONTENT_MODIFIED
            else:
                conflict_type = ConflictType.FILE_EXISTS
            
            return ConflictInfo(
                conflict_type,
                file_path,
                existing_content=existing_content,
                new_content=new_content,
                metadata={"conflicts": conflicts}
            )
        
        return None  # No conflict detected
    
    def resolve_conflict(self,
                        conflict: ConflictInfo,
                        strategy: Optional[ConflictResolutionStrategy] = None,
                        create_backup: bool = True) -> ConflictResolutionResult:
        """Resolve a conflict using the specified strategy.
        
        Args:
            conflict: Conflict information
            strategy: Resolution strategy (uses default if None)
            create_backup: Whether to create backup before resolution
            
        Returns:
            ConflictResolutionResult with resolution details
        """
        if strategy is None:
            strategy = self.default_strategies.get(
                conflict.conflict_type,
                ConflictResolutionStrategy.SKIP
            )
        
        debug_logger.log("INFO", "Resolving conflict",
                        file_path=str(conflict.file_path),
                        conflict_type=conflict.conflict_type.value,
                        strategy=strategy.value)
        
        try:
            with debug_logger.timer("conflict_resolution"):
                # Create backup if requested
                backup_path = None
                if create_backup and conflict.existing_content is not None:
                    backup_path = self._create_backup(conflict.file_path, conflict.existing_content)
                
                # Apply resolution strategy
                final_content = self._apply_strategy(conflict, strategy)
                
                # Write resolved content
                if final_content is not None and strategy != ConflictResolutionStrategy.SKIP:
                    conflict.file_path.write_text(final_content, encoding='utf-8')
                    
                    # Update file cache
                    self.change_detector.update_file_cache(conflict.file_path)
                
                result = ConflictResolutionResult(
                    success=True,
                    strategy_used=strategy,
                    final_content=final_content,
                    backup_path=backup_path
                )
                
                debug_logger.log("INFO", "Conflict resolved successfully",
                               file_path=str(conflict.file_path),
                               strategy=strategy.value)
                
                return result
            
        except Exception as e:
            error_msg = f"Failed to resolve conflict: {e}"
            debug_logger.log("ERROR", error_msg,
                           file_path=str(conflict.file_path))
            
            return ConflictResolutionResult(
                success=False,
                strategy_used=strategy,
                errors=[error_msg]
            )
    
    def _apply_strategy(self,
                       conflict: ConflictInfo,
                       strategy: ConflictResolutionStrategy) -> Optional[str]:
        """Apply the specified resolution strategy."""
        if strategy == ConflictResolutionStrategy.KEEP_OURS:
            return conflict.existing_content
        
        elif strategy == ConflictResolutionStrategy.KEEP_THEIRS:
            return conflict.new_content
        
        elif strategy == ConflictResolutionStrategy.SKIP:
            return None
        
        elif strategy == ConflictResolutionStrategy.BACKUP_AND_REPLACE:
            return conflict.new_content
        
        elif strategy in [
            ConflictResolutionStrategy.MERGE_INTELLIGENT,
            ConflictResolutionStrategy.MERGE_APPEND,
            ConflictResolutionStrategy.MERGE_PREPEND
        ]:
            if conflict.existing_content is None or conflict.new_content is None:
                return conflict.new_content or conflict.existing_content
            
            merge_strategy_map = {
                ConflictResolutionStrategy.MERGE_INTELLIGENT: "intelligent",
                ConflictResolutionStrategy.MERGE_APPEND: "append",
                ConflictResolutionStrategy.MERGE_PREPEND: "prepend",
            }
            
            merge_strategy = merge_strategy_map[strategy]
            return self.content_merger.merge_markdown_content(
                conflict.existing_content,
                conflict.new_content,
                merge_strategy
            )
        
        elif strategy == ConflictResolutionStrategy.PROMPT:
            # For now, fall back to intelligent merge
            # In the future, this would integrate with Rich UI for user prompting
            debug_logger.log("WARNING", "PROMPT strategy not implemented, using MERGE_INTELLIGENT")
            return self._apply_strategy(conflict, ConflictResolutionStrategy.MERGE_INTELLIGENT)
        
        else:
            raise ValueError(f"Unknown resolution strategy: {strategy}")
    
    def _create_backup(self, file_path: Path, content: str) -> Path:
        """Create a backup of existing content."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
        
        try:
            backup_path.write_text(content, encoding='utf-8')
            debug_logger.log("DEBUG", "Backup created",
                           original=str(file_path),
                           backup=str(backup_path))
            return backup_path
        except OSError as e:
            debug_logger.log("WARNING", "Failed to create backup",
                           file_path=str(file_path), error=str(e))
            raise SpecFileError(f"Failed to create backup: {e}") from e
    
    def resolve_multiple_conflicts(self,
                                  conflicts: List[ConflictInfo],
                                  strategy_map: Optional[Dict[ConflictType, ConflictResolutionStrategy]] = None,
                                  create_backups: bool = True) -> List[ConflictResolutionResult]:
        """Resolve multiple conflicts using specified strategies.
        
        Args:
            conflicts: List of conflicts to resolve
            strategy_map: Map of conflict types to strategies
            create_backups: Whether to create backups
            
        Returns:
            List of resolution results
        """
        debug_logger.log("INFO", "Resolving multiple conflicts",
                        conflict_count=len(conflicts))
        
        strategies = strategy_map or self.default_strategies
        results = []
        
        for conflict in conflicts:
            strategy = strategies.get(conflict.conflict_type)
            result = self.resolve_conflict(conflict, strategy, create_backups)
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        debug_logger.log("INFO", "Multiple conflict resolution complete",
                        total=len(conflicts),
                        successful=successful,
                        failed=len(conflicts) - successful)
        
        return results
    
    def recommend_strategy(self, conflict: ConflictInfo) -> ConflictResolutionStrategy:
        """Recommend a resolution strategy for a conflict.
        
        Args:
            conflict: Conflict to analyze
            
        Returns:
            Recommended strategy
        """
        # Check for simple cases first
        if conflict.conflict_type == ConflictType.PERMISSION_DENIED:
            return ConflictResolutionStrategy.SKIP
        
        if conflict.conflict_type == ConflictType.SIZE_LIMIT:
            return ConflictResolutionStrategy.SKIP
        
        # Analyze content for more complex cases
        if conflict.existing_content and conflict.new_content:
            conflicts = self.content_merger.detect_conflicts(
                conflict.existing_content,
                conflict.new_content
            )
            
            high_severity_conflicts = [c for c in conflicts if c["severity"] == "high"]
            
            if high_severity_conflicts:
                # High conflicts suggest manual intervention
                return ConflictResolutionStrategy.PROMPT
            
            # Check content similarity
            existing_words = set(conflict.existing_content.lower().split())
            new_words = set(conflict.new_content.lower().split())
            
            if existing_words and new_words:
                similarity = len(existing_words & new_words) / len(existing_words | new_words)
                
                if similarity > 0.8:  # Very similar content
                    return ConflictResolutionStrategy.MERGE_INTELLIGENT
                elif similarity > 0.5:  # Moderately similar
                    return ConflictResolutionStrategy.MERGE_INTELLIGENT
                else:  # Very different content
                    return ConflictResolutionStrategy.BACKUP_AND_REPLACE
        
        # Default recommendation
        return self.default_strategies.get(
            conflict.conflict_type,
            ConflictResolutionStrategy.MERGE_INTELLIGENT
        )
    
    def get_conflict_summary(self, conflicts: List[ConflictInfo]) -> Dict[str, Any]:
        """Get summary information about a list of conflicts.
        
        Args:
            conflicts: List of conflicts to summarize
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_conflicts": len(conflicts),
            "by_type": {},
            "recommendations": {},
            "total_size": 0,
            "requires_manual_review": 0,
        }
        
        for conflict in conflicts:
            # Count by type
            conflict_type = conflict.conflict_type.value
            summary["by_type"][conflict_type] = summary["by_type"].get(conflict_type, 0) + 1
            
            # Get recommendations
            recommended_strategy = self.recommend_strategy(conflict)
            strategy_name = recommended_strategy.value
            summary["recommendations"][strategy_name] = summary["recommendations"].get(strategy_name, 0) + 1
            
            # Calculate sizes
            if conflict.new_content:
                summary["total_size"] += len(conflict.new_content)
            
            # Check if requires manual review
            if recommended_strategy == ConflictResolutionStrategy.PROMPT:
                summary["requires_manual_review"] += 1
        
        return summary
    
    def validate_resolution_strategies(self,
                                     strategy_map: Dict[ConflictType, ConflictResolutionStrategy]) -> List[str]:
        """Validate a set of resolution strategies.
        
        Args:
            strategy_map: Map of conflict types to strategies
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required conflict types
        required_types = set(ConflictType)
        provided_types = set(strategy_map.keys())
        missing_types = required_types - provided_types
        
        for missing_type in missing_types:
            issues.append(f"No strategy defined for conflict type: {missing_type.value}")
        
        # Check for invalid combinations
        for conflict_type, strategy in strategy_map.items():
            if conflict_type == ConflictType.PERMISSION_DENIED:
                if strategy not in [ConflictResolutionStrategy.SKIP, ConflictResolutionStrategy.PROMPT]:
                    issues.append(f"Strategy {strategy.value} not suitable for permission denied conflicts")
            
            if conflict_type == ConflictType.SIZE_LIMIT:
                if strategy not in [ConflictResolutionStrategy.SKIP, ConflictResolutionStrategy.PROMPT]:
                    issues.append(f"Strategy {strategy.value} not suitable for size limit conflicts")
        
        return issues