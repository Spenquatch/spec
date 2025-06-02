# Slice 11B: Conflict Resolution Strategies

## Goal

Implement conflict resolution enum strategies (keep-ours/keep-theirs/merge) with merge helpers for handling existing spec files and content conflicts.

## Context

Building on the change detection from slice-11a, this slice implements conflict resolution strategies for handling situations where spec files already exist or content conflicts arise. It provides a clean, strategy-based approach to conflict resolution with isolated, testable components.

## Scope

**Included in this slice:**
- ConflictResolutionStrategy enum with standard strategies
- ConflictResolver class for strategy-based resolution
- Merge helpers for content combination and conflict detection
- Backup and rollback utilities for safe conflict resolution
- Strategy validation and recommendation systems

**NOT included in this slice:**
- Change detection logic (handled by slice-11a)
- Batch processing workflows (moved to slice-11c)
- File processing orchestration (moved to slice-11c)
- Rich UI integration (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for conflict errors)
- `spec_cli.logging.debug` (debug_logger for conflict resolution tracking)
- `spec_cli.config.settings` (SpecSettings for resolution configuration)
- `spec_cli.file_processing.change_detector` (FileChangeDetector for change tracking)
- `spec_cli.file_system.directory_manager` (DirectoryManager for backup operations)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `FileChangeDetector` from slice-11a-change-detection
- `DirectoryManager` from slice-6b-directory-operations

## Files to Create

```
spec_cli/file_processing/
├── conflict_resolver.py    # ConflictResolver class and strategies
└── merge_helpers.py       # Content merging utilities
```

## Implementation Steps

### Step 1: Create spec_cli/file_processing/merge_helpers.py

```python
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from ..exceptions import SpecFileError
from ..logging.debug import debug_logger

class ContentMerger:
    """Utilities for merging and combining file content."""
    
    def __init__(self):
        # Patterns for detecting markdown sections
        self.section_patterns = {
            "heading": re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            "yaml_frontmatter": re.compile(r'^---\n(.+?)\n---', re.DOTALL),
            "code_block": re.compile(r'^```([a-z]*\n.*?^```)$', re.MULTILINE | re.DOTALL),
        }
        
        debug_logger.log("INFO", "ContentMerger initialized")
    
    def detect_content_sections(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Detect structured sections in markdown content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dictionary mapping section types to detected sections
        """
        sections = {
            "headings": [],
            "yaml_frontmatter": [],
            "code_blocks": [],
            "paragraphs": [],
        }
        
        # Detect headings
        for match in self.section_patterns["heading"].finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            start_pos = match.start()
            end_pos = match.end()
            
            sections["headings"].append({
                "level": level,
                "title": title,
                "start": start_pos,
                "end": end_pos,
                "content": match.group(0),
            })
        
        # Detect YAML frontmatter
        frontmatter_match = self.section_patterns["yaml_frontmatter"].match(content)
        if frontmatter_match:
            sections["yaml_frontmatter"].append({
                "content": frontmatter_match.group(1),
                "start": frontmatter_match.start(),
                "end": frontmatter_match.end(),
            })
        
        # Detect code blocks
        for match in self.section_patterns["code_block"].finditer(content):
            sections["code_blocks"].append({
                "language": match.group(1).strip() if match.group(1) else "text",
                "content": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })
        
        # Simple paragraph detection (non-empty lines not in other sections)
        lines = content.split('\n')
        in_code_block = False
        current_paragraph = []
        line_start = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block or line.startswith('#') or not line.strip():
                if current_paragraph:
                    sections["paragraphs"].append({
                        "content": '\n'.join(current_paragraph),
                        "start_line": line_start,
                        "end_line": i - 1,
                    })
                    current_paragraph = []
                continue
            
            if not current_paragraph:
                line_start = i
            current_paragraph.append(line)
        
        if current_paragraph:
            sections["paragraphs"].append({
                "content": '\n'.join(current_paragraph),
                "start_line": line_start,
                "end_line": len(lines) - 1,
            })
        
        debug_logger.log("DEBUG", "Content sections detected",
                        headings=len(sections["headings"]),
                        code_blocks=len(sections["code_blocks"]),
                        paragraphs=len(sections["paragraphs"]))
        
        return sections
    
    def merge_markdown_content(self, 
                              base_content: str,
                              new_content: str,
                              strategy: str = "intelligent") -> str:
        """Merge two markdown contents using specified strategy.
        
        Args:
            base_content: Existing content
            new_content: New content to merge
            strategy: Merge strategy ('intelligent', 'append', 'prepend', 'replace')
            
        Returns:
            Merged content
        """
        debug_logger.log("INFO", "Merging markdown content",
                        strategy=strategy,
                        base_length=len(base_content),
                        new_length=len(new_content))
        
        if strategy == "replace":
            return new_content
        elif strategy == "append":
            return base_content + "\n\n" + new_content
        elif strategy == "prepend":
            return new_content + "\n\n" + base_content
        elif strategy == "intelligent":
            return self._intelligent_merge(base_content, new_content)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")
    
    def _intelligent_merge(self, base_content: str, new_content: str) -> str:
        """Perform intelligent merge based on content structure."""
        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)
        
        # Start with base content
        merged_lines = base_content.split('\n')
        
        # Merge headings intelligently
        base_headings = {h["title"].lower(): h for h in base_sections["headings"]}
        
        for new_heading in new_sections["headings"]:
            title_lower = new_heading["title"].lower()
            
            if title_lower not in base_headings:
                # Add new heading
                merged_lines.append("")
                merged_lines.append(new_heading["content"])
                
                # Find content after this heading in new content
                heading_end = new_heading["end"]
                next_heading_start = len(new_content)
                
                for other_heading in new_sections["headings"]:
                    if other_heading["start"] > heading_end:
                        next_heading_start = min(next_heading_start, other_heading["start"])
                
                if next_heading_start > heading_end:
                    section_content = new_content[heading_end:next_heading_start].strip()
                    if section_content:
                        merged_lines.append(section_content)
        
        merged_content = '\n'.join(merged_lines)
        
        debug_logger.log("DEBUG", "Intelligent merge completed",
                        result_length=len(merged_content))
        
        return merged_content
    
    def detect_conflicts(self, 
                        base_content: str, 
                        new_content: str) -> List[Dict[str, Any]]:
        """Detect potential conflicts between content versions.
        
        Args:
            base_content: Original content
            new_content: New content
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)
        
        # Check for heading conflicts
        base_headings = {h["title"].lower(): h for h in base_sections["headings"]}
        new_headings = {h["title"].lower(): h for h in new_sections["headings"]}
        
        common_headings = set(base_headings.keys()) & set(new_headings.keys())
        
        for heading_title in common_headings:
            base_heading = base_headings[heading_title]
            new_heading = new_headings[heading_title]
            
            if base_heading["level"] != new_heading["level"]:
                conflicts.append({
                    "type": "heading_level_conflict",
                    "heading": heading_title,
                    "base_level": base_heading["level"],
                    "new_level": new_heading["level"],
                    "severity": "medium",
                })
        
        # Check for substantial content differences
        base_words = set(re.findall(r'\b\w+\b', base_content.lower()))
        new_words = set(re.findall(r'\b\w+\b', new_content.lower()))
        
        common_words = base_words & new_words
        total_words = base_words | new_words
        
        if total_words:
            similarity = len(common_words) / len(total_words)
            
            if similarity < 0.5:  # Less than 50% similarity
                conflicts.append({
                    "type": "content_divergence",
                    "similarity": similarity,
                    "severity": "high" if similarity < 0.3 else "medium",
                })
        
        debug_logger.log("DEBUG", "Conflict detection completed",
                        conflicts=len(conflicts))
        
        return conflicts
    
    def create_merge_preview(self, 
                           base_content: str,
                           new_content: str,
                           strategy: str) -> Dict[str, Any]:
        """Create a preview of what merge would produce.
        
        Args:
            base_content: Base content
            new_content: New content
            strategy: Merge strategy
            
        Returns:
            Dictionary with merge preview information
        """
        try:
            merged_content = self.merge_markdown_content(base_content, new_content, strategy)
            conflicts = self.detect_conflicts(base_content, new_content)
            
            preview = {
                "strategy": strategy,
                "base_length": len(base_content),
                "new_length": len(new_content),
                "merged_length": len(merged_content),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "has_conflicts": len(conflicts) > 0,
                "merged_preview": merged_content[:500] + "..." if len(merged_content) > 500 else merged_content,
            }
            
            return preview
            
        except Exception as e:
            return {
                "strategy": strategy,
                "error": str(e),
                "has_conflicts": True,
            }
    
    def extract_metadata_diff(self, 
                            base_content: str,
                            new_content: str) -> Dict[str, Any]:
        """Extract differences in metadata between content versions.
        
        Args:
            base_content: Base content
            new_content: New content
            
        Returns:
            Dictionary with metadata differences
        """
        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)
        
        diff = {
            "headings_added": [],
            "headings_removed": [],
            "headings_modified": [],
            "structure_changes": [],
        }
        
        base_heading_titles = {h["title"].lower() for h in base_sections["headings"]}
        new_heading_titles = {h["title"].lower() for h in new_sections["headings"]}
        
        diff["headings_added"] = list(new_heading_titles - base_heading_titles)
        diff["headings_removed"] = list(base_heading_titles - new_heading_titles)
        
        # Check for structure changes
        if len(base_sections["headings"]) != len(new_sections["headings"]):
            diff["structure_changes"].append("heading_count_changed")
        
        if len(base_sections["code_blocks"]) != len(new_sections["code_blocks"]):
            diff["structure_changes"].append("code_block_count_changed")
        
        return diff
```

### Step 2: Create spec_cli/file_processing/conflict_resolver.py

```python
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
```

### Step 3: Update spec_cli/file_processing/__init__.py

```python
"""File processing utilities for spec CLI.

This package provides change detection, conflict resolution, and batch processing
capabilities for efficient spec generation workflows.
"""

from .change_detector import FileChangeDetector
from .file_cache import FileCacheManager
from .conflict_resolver import (
    ConflictResolver,
    ConflictResolutionStrategy,
    ConflictType,
    ConflictInfo,
    ConflictResolutionResult,
)
from .merge_helpers import ContentMerger

__all__ = [
    "FileChangeDetector",
    "FileCacheManager",
    "ConflictResolver",
    "ConflictResolutionStrategy",
    "ConflictType",
    "ConflictInfo",
    "ConflictResolutionResult",
    "ContentMerger",
]
```

## Test Requirements

Create comprehensive tests for conflict resolution:

### Test Cases (12 tests total)

**Content Merger Tests:**
1. **test_content_section_detection**
2. **test_markdown_content_merging_strategies**
3. **test_conflict_detection_in_content**
4. **test_merge_preview_generation**

**Conflict Resolver Tests:**
5. **test_conflict_detection_various_types**
6. **test_strategy_application_keep_ours_theirs**
7. **test_strategy_application_merge_variants**
8. **test_backup_creation_during_resolution**
9. **test_multiple_conflict_resolution**
10. **test_strategy_recommendation_system**
11. **test_conflict_summary_generation**
12. **test_strategy_validation**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_processing/test_conflict_resolver.py tests/unit/file_processing/test_merge_helpers.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_processing/test_conflict_resolver.py tests/unit/file_processing/test_merge_helpers.py --cov=spec_cli.file_processing.conflict_resolver --cov=spec_cli.file_processing.merge_helpers --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_processing/conflict_resolver.py spec_cli/file_processing/merge_helpers.py

# Check code formatting
poetry run ruff check spec_cli/file_processing/conflict_resolver.py spec_cli/file_processing/merge_helpers.py
poetry run ruff format spec_cli/file_processing/conflict_resolver.py spec_cli/file_processing/merge_helpers.py

# Verify imports work correctly
python -c "from spec_cli.file_processing import ConflictResolver, ConflictResolutionStrategy, ContentMerger; print('Import successful')"

# Test content merging
python -c "
from spec_cli.file_processing.merge_helpers import ContentMerger

merger = ContentMerger()

# Test content section detection
content = '''# Header 1
Some content here.

## Header 2
More content.

```python
print('code')
```
'''

sections = merger.detect_content_sections(content)
print(f'Detected sections:')
for section_type, items in sections.items():
    print(f'  {section_type}: {len(items)} items')

# Test merging
base_content = '# Title\nOriginal content.'
new_content = '# Title\nNew content.\n\n## New Section\nAdditional info.'

merged = merger.merge_markdown_content(base_content, new_content, 'intelligent')
print(f'Merged content length: {len(merged)}')

# Test conflict detection
conflicts = merger.detect_conflicts(base_content, new_content)
print(f'Conflicts detected: {len(conflicts)}')
"

# Test conflict resolution
python -c "
from spec_cli.file_processing.conflict_resolver import ConflictResolver, ConflictType, ConflictInfo, ConflictResolutionStrategy
from pathlib import Path
import tempfile

resolver = ConflictResolver()

# Create test file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
    f.write('# Original\nOriginal content')
    test_file = Path(f.name)

try:
    # Create conflict
    new_content = '# Modified\nNew content here'
    conflict = resolver.detect_conflict(test_file, new_content)
    
    if conflict:
        print(f'Conflict detected: {conflict.conflict_type.value}')
        
        # Get recommendation
        strategy = resolver.recommend_strategy(conflict)
        print(f'Recommended strategy: {strategy.value}')
        
        # Test resolution (dry run - don't actually resolve)
        print(f'Conflict info: {conflict.to_dict()}')
    else:
        print('No conflict detected')
        
finally:
    test_file.unlink()
"

# Test strategy enumeration
python -c "
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy, ConflictType

print('Available resolution strategies:')
for strategy in ConflictResolutionStrategy:
    print(f'  - {strategy.value}')

print('\nConflict types:')
for conflict_type in ConflictType:
    print(f'  - {conflict_type.value}')
"

# Test merge preview
python -c "
from spec_cli.file_processing.merge_helpers import ContentMerger

merger = ContentMerger()

base = '''# Documentation

## Overview
This is the original overview.

## Usage
Original usage info.
'''

new = '''# Documentation

## Overview
This is an updated overview with more details.

## Installation
New installation section.

## Usage
Updated usage information.
'''

preview = merger.create_merge_preview(base, new, 'intelligent')
print(f'Merge preview:')
print(f'  Strategy: {preview["strategy"]}')
print(f'  Conflicts: {preview["conflict_count"]}')
print(f'  Has conflicts: {preview["has_conflicts"]}')
print(f'  Result length: {preview["merged_length"]}')
if preview.get('merged_preview'):
    print(f'  Preview: {preview["merged_preview"][:100]}...')
"
```

## Definition of Done

- [ ] ConflictResolutionStrategy enum with comprehensive strategies
- [ ] ConflictResolver class for strategy-based conflict resolution
- [ ] ContentMerger class for intelligent content combination
- [ ] Conflict detection for various conflict types
- [ ] Merge helpers for markdown content structure analysis
- [ ] Strategy recommendation system based on conflict analysis
- [ ] Backup creation during conflict resolution
- [ ] Multiple conflict resolution with batch processing
- [ ] All 12 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with change detection and file management
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-11c (batch processor) by providing:
- Conflict resolution strategies that batch processing can use
- Content merging capabilities for handling multiple file conflicts
- Strategy recommendation system for automated conflict handling
- Foundation for intelligent batch processing with conflict management