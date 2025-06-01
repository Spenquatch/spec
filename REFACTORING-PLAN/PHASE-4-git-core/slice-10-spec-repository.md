# Slice 10: Spec Repository Orchestration and Main Operations [DEPRECATED - SPLIT INTO 10A/10B/10C]

**NOTE: This slice has been split into focused components for better implementation:**
- **[slice-10a-repo-init.md](./slice-10a-repo-init.md)**: Repository initialization and state management
- **[slice-10b-commit-wrappers.md](./slice-10b-commit-wrappers.md)**: Git commit wrappers and operations
- **[slice-10c-spec-workflow.md](./slice-10c-spec-workflow.md)**: High-level spec workflow orchestration

Please implement the individual slices instead of this combined version.

## Goal

Create the main spec repository orchestration layer that combines Git operations, file processing, and template generation to provide high-level spec operations that will be used by the CLI commands.

## Context

Building on the Git operations foundation from slice-9, this slice implements the main spec repository orchestration that combines all previous systems. It provides the high-level operations that the CLI commands will use, handling the complex coordination between Git operations, file processing, template generation, and directory management.

## Scope

**Included in this slice:**
- SpecRepository class for high-level spec operations
- Integration of Git operations with file processing
- Spec generation workflow orchestration
- Repository state management and validation
- Batch operations for multiple files
- Error recovery and rollback capabilities

**NOT included in this slice:**
- File processing workflow implementation (comes in slice-11-file-processing)
- Rich UI integration (comes in slice-12-rich-ui)
- CLI command implementations (comes in slice-13-cli-commands)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for repository errors)
- `spec_cli.logging.debug` (debug_logger for operation tracking)
- `spec_cli.config.settings` (SpecSettings for repository configuration)
- `spec_cli.git.repository` (SpecGitRepository for Git operations)
- `spec_cli.git.operations` (GitOperations for low-level Git commands)
- `spec_cli.file_system.directory_manager` (DirectoryManager for spec directories)
- `spec_cli.templates.generator` (SpecContentGenerator for content generation)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration
- `SpecGitRepository` from slice-9-git-operations
- `DirectoryManager` from slice-6-directory-management
- `SpecContentGenerator` from slice-8-template-generation

## Files to Create

```
spec_cli/core/
├── __init__.py             # Module exports
├── spec_repository.py      # SpecRepository orchestration class
└── operations.py           # High-level operation implementations
```

## Implementation Steps

### Step 1: Create spec_cli/core/__init__.py

```python
"""Core orchestration layer for spec CLI.

This package provides high-level operations that coordinate between
Git operations, file processing, template generation, and directory management.
"""

from .spec_repository import SpecRepository
from .operations import SpecOperationManager

__all__ = [
    "SpecRepository",
    "SpecOperationManager",
]
```

### Step 2: Create spec_cli/core/spec_repository.py

```python
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from ..exceptions import SpecGitError, SpecFileError, SpecOperationError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from ..git.repository import SpecGitRepository
from ..file_system.directory_manager import DirectoryManager
from ..templates.generator import SpecContentGenerator
from ..templates.loader import load_template
from .operations import SpecOperationManager

class SpecRepository:
    """High-level spec repository orchestration managing Git operations and file processing."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
        self.content_generator = SpecContentGenerator(self.settings)
        self.operation_manager = SpecOperationManager(self.settings)
        
        debug_logger.log("INFO", "SpecRepository initialized",
                        root_path=str(self.settings.root_path),
                        spec_dir=str(self.settings.spec_dir),
                        specs_dir=str(self.settings.specs_dir))
    
    def initialize(self) -> None:
        """Initialize the spec repository with all necessary setup.
        
        Raises:
            SpecOperationError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing spec repository")
        
        try:
            with debug_logger.timer("spec_repository_initialization"):
                # Ensure .specs directory exists
                self.directory_manager.ensure_specs_directory()
                
                # Initialize Git repository
                self.git_repo.initialize_repository()
                
                # Set up ignore files and main .gitignore
                self.directory_manager.setup_ignore_files()
                self.directory_manager.update_main_gitignore()
                
                debug_logger.log("INFO", "Spec repository initialization complete")
                
        except Exception as e:
            error_msg = f"Failed to initialize spec repository: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def is_initialized(self) -> bool:
        """Check if spec repository is properly initialized.
        
        Returns:
            True if repository is initialized and ready for operations
        """
        try:
            git_initialized = self.git_repo.is_initialized()
            specs_dir_exists = self.settings.specs_dir.exists()
            
            is_ready = git_initialized and specs_dir_exists
            
            debug_logger.log("INFO", "Repository initialization check",
                           git_initialized=git_initialized,
                           specs_dir_exists=specs_dir_exists,
                           is_ready=is_ready)
            
            return is_ready
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to check initialization status", error=str(e))
            return False
    
    def add_files(self, file_paths: List[str], force: bool = False) -> Dict[str, Any]:
        """Add spec files to the repository.
        
        Args:
            file_paths: List of file paths to add
            force: Whether to force add (bypass validation)
            
        Returns:
            Dictionary with operation results
            
        Raises:
            SpecOperationError: If add operation fails
        """
        debug_logger.log("INFO", "Adding files to spec repository",
                        file_count=len(file_paths), force=force)
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            with debug_logger.timer("add_files_operation"):
                # Validate file paths
                validated_paths = self.operation_manager.validate_file_paths(file_paths, force)
                
                # Add files to Git
                self.git_repo.add(validated_paths)
                
                result = {
                    "added_files": validated_paths,
                    "file_count": len(validated_paths),
                    "operation": "add",
                    "success": True,
                }
                
                debug_logger.log("INFO", "Files added successfully",
                               added_count=len(validated_paths))
                
                return result
                
        except Exception as e:
            error_msg = f"Failed to add files: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def commit_changes(self, message: str, validate: bool = True) -> Dict[str, Any]:
        """Commit changes to the spec repository.
        
        Args:
            message: Commit message
            validate: Whether to validate before committing
            
        Returns:
            Dictionary with commit results
            
        Raises:
            SpecOperationError: If commit operation fails
        """
        debug_logger.log("INFO", "Creating commit in spec repository",
                        message=message[:50] + "..." if len(message) > 50 else message,
                        validate=validate)
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            with debug_logger.timer("commit_operation"):
                # Pre-commit validation if requested
                if validate:
                    validation_result = self.operation_manager.validate_repository_state()
                    if not validation_result["is_valid"]:
                        raise SpecOperationError(f"Repository validation failed: {validation_result['issues']}")
                
                # Create the commit
                self.git_repo.commit(message)
                
                result = {
                    "message": message,
                    "operation": "commit",
                    "success": True,
                    "validated": validate,
                }
                
                debug_logger.log("INFO", "Commit created successfully")
                
                return result
                
        except Exception as e:
            error_msg = f"Failed to commit changes: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def generate_specs(self, 
                      file_paths: List[str],
                      template_name: Optional[str] = None,
                      ai_enabled: bool = False,
                      backup_existing: bool = True) -> Dict[str, Any]:
        """Generate spec documentation for files.
        
        Args:
            file_paths: List of file paths to generate specs for
            template_name: Optional template preset name
            ai_enabled: Whether to use AI for content generation
            backup_existing: Whether to backup existing spec files
            
        Returns:
            Dictionary with generation results
            
        Raises:
            SpecOperationError: If generation fails
        """
        debug_logger.log("INFO", "Generating spec documentation",
                        file_count=len(file_paths),
                        template=template_name,
                        ai_enabled=ai_enabled,
                        backup=backup_existing)
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            with debug_logger.timer("generate_specs_operation"):
                # Load template configuration
                template_config = load_template()
                if template_name:
                    from ..templates.defaults import get_template_preset
                    template_config = get_template_preset(template_name)
                
                generated_files = []
                backed_up_files = []
                
                for file_path_str in file_paths:
                    file_path = Path(file_path_str)
                    
                    try:
                        # Create spec directory
                        spec_dir = self.directory_manager.create_spec_directory(file_path)
                        
                        # Backup existing files if requested
                        if backup_existing:
                            backup_dir = self.directory_manager.backup_existing_specs(spec_dir)
                            if backup_dir:
                                backed_up_files.append(str(backup_dir))
                        
                        # Generate content
                        self.content_generator.generate_spec_content(
                            file_path, spec_dir, template_config, ai_enabled=ai_enabled
                        )
                        
                        generated_files.append({
                            "source_file": str(file_path),
                            "spec_directory": str(spec_dir),
                            "index_file": str(spec_dir / "index.md"),
                            "history_file": str(spec_dir / "history.md"),
                        })
                        
                        debug_logger.log("INFO", "Generated spec for file",
                                       source=str(file_path), spec_dir=str(spec_dir))
                        
                    except Exception as e:
                        debug_logger.log("ERROR", "Failed to generate spec for file",
                                       file=str(file_path), error=str(e))
                        # Continue with other files
                        continue
                
                result = {
                    "generated_files": generated_files,
                    "backed_up_files": backed_up_files,
                    "successful_count": len(generated_files),
                    "total_requested": len(file_paths),
                    "template_used": template_name or "default",
                    "ai_enabled": ai_enabled,
                    "operation": "generate",
                    "success": len(generated_files) > 0,
                }
                
                debug_logger.log("INFO", "Spec generation complete",
                               successful=len(generated_files),
                               total=len(file_paths))
                
                return result
                
        except Exception as e:
            error_msg = f"Failed to generate specs: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the spec repository.
        
        Returns:
            Dictionary with repository status information
        """
        debug_logger.log("INFO", "Getting spec repository status")
        
        try:
            status = {
                "initialized": self.is_initialized(),
                "git_repository": self.git_repo.get_repository_info(),
            }
            
            if status["initialized"]:
                # Get directory statistics
                status["directory_stats"] = self.directory_manager.get_directory_stats(
                    self.settings.specs_dir
                )
                
                # Count spec files
                spec_files = list(self.settings.specs_dir.rglob("*.md"))
                status["spec_file_count"] = len(spec_files)
                
                # Get recent activity
                recent_files = [
                    f for f in spec_files 
                    if self._is_recent_file(f, days=7)
                ]
                status["recent_activity"] = {
                    "files_modified_last_7_days": len(recent_files),
                    "has_recent_activity": len(recent_files) > 0,
                }
            
            debug_logger.log("INFO", "Repository status retrieved",
                           initialized=status["initialized"],
                           spec_files=status.get("spec_file_count", 0))
            
            return status
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to get repository status", error=str(e))
            return {
                "initialized": False,
                "error": str(e),
            }
    
    def show_log(self, file_paths: Optional[List[str]] = None, limit: int = 10) -> None:
        """Show commit log for the spec repository.
        
        Args:
            file_paths: Optional list of file paths to filter log
            limit: Maximum number of commits to show
        """
        debug_logger.log("INFO", "Showing spec repository log",
                        file_filter=bool(file_paths), limit=limit)
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            self.git_repo.log(file_paths)
            
        except Exception as e:
            error_msg = f"Failed to show log: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def show_diff(self, file_paths: Optional[List[str]] = None) -> None:
        """Show diff for the spec repository.
        
        Args:
            file_paths: Optional list of file paths to filter diff
        """
        debug_logger.log("INFO", "Showing spec repository diff",
                        file_filter=bool(file_paths))
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            self.git_repo.diff(file_paths)
            
        except Exception as e:
            error_msg = f"Failed to show diff: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def show_repository_status(self) -> None:
        """Show Git status for the spec repository."""
        debug_logger.log("INFO", "Showing spec repository Git status")
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            self.git_repo.status()
            
        except Exception as e:
            error_msg = f"Failed to show status: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def cleanup_repository(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up repository by removing orphaned or invalid spec files.
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Dictionary with cleanup results
        """
        debug_logger.log("INFO", "Cleaning up spec repository", dry_run=dry_run)
        
        if not self.is_initialized():
            raise SpecOperationError("Spec repository is not initialized. Run 'spec init' first.")
        
        try:
            cleanup_result = self.operation_manager.cleanup_orphaned_specs(dry_run)
            
            debug_logger.log("INFO", "Repository cleanup complete",
                           dry_run=dry_run,
                           items_found=len(cleanup_result.get("orphaned_specs", [])))
            
            return cleanup_result
            
        except Exception as e:
            error_msg = f"Failed to cleanup repository: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def _is_recent_file(self, file_path: Path, days: int = 7) -> bool:
        """Check if file was modified recently."""
        try:
            from ..file_system.metadata import is_recent_file
            return is_recent_file(file_path, days)
        except Exception:
            return False
    
    def get_repository_health(self) -> Dict[str, Any]:
        """Get comprehensive health check of the repository.
        
        Returns:
            Dictionary with health check results
        """
        debug_logger.log("INFO", "Performing repository health check")
        
        health = {
            "overall_status": "unknown",
            "checks": {},
            "issues": [],
            "recommendations": [],
        }
        
        try:
            # Check initialization
            health["checks"]["initialized"] = self.is_initialized()
            
            if health["checks"]["initialized"]:
                # Check Git repository integrity
                git_info = self.git_repo.get_repository_info()
                health["checks"]["git_repository_valid"] = git_info.get("is_initialized", False)
                
                # Check directory structure
                health["checks"]["specs_directory_exists"] = self.settings.specs_dir.exists()
                health["checks"]["specs_directory_writable"] = (
                    self.settings.specs_dir.exists() and 
                    os.access(self.settings.specs_dir, os.W_OK)
                )
                
                # Check for common issues
                validation_result = self.operation_manager.validate_repository_state()
                health["checks"]["repository_state_valid"] = validation_result["is_valid"]
                if not validation_result["is_valid"]:
                    health["issues"].extend(validation_result["issues"])
                
                # Determine overall status
                all_checks_pass = all(health["checks"].values())
                health["overall_status"] = "healthy" if all_checks_pass else "issues_found"
                
                # Generate recommendations
                if not all_checks_pass:
                    health["recommendations"] = self._generate_health_recommendations(health["checks"])
            else:
                health["overall_status"] = "not_initialized"
                health["recommendations"] = ["Run 'spec init' to initialize the repository"]
            
            debug_logger.log("INFO", "Repository health check complete",
                           status=health["overall_status"],
                           issues=len(health["issues"]))
            
            return health
            
        except Exception as e:
            health["overall_status"] = "error"
            health["issues"].append(f"Health check failed: {e}")
            debug_logger.log("ERROR", "Repository health check failed", error=str(e))
            return health
    
    def _generate_health_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        """Generate health recommendations based on failed checks."""
        recommendations = []
        
        if not checks.get("initialized", True):
            recommendations.append("Initialize the repository with 'spec init'")
        
        if not checks.get("git_repository_valid", True):
            recommendations.append("Re-initialize Git repository - the .spec directory may be corrupted")
        
        if not checks.get("specs_directory_exists", True):
            recommendations.append("Create the .specs directory or re-run initialization")
        
        if not checks.get("specs_directory_writable", True):
            recommendations.append("Check permissions on .specs directory - write access is required")
        
        if not checks.get("repository_state_valid", True):
            recommendations.append("Run repository validation to identify and fix state issues")
        
        return recommendations
```

### Step 3: Create spec_cli/core/operations.py

```python
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from ..exceptions import SpecFileError, SpecValidationError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from ..file_system.path_resolver import PathResolver
from ..file_system.file_analyzer import FileAnalyzer

class SpecOperationManager:
    """Manages high-level spec operations and validation."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.path_resolver = PathResolver(self.settings)
        self.file_analyzer = FileAnalyzer(self.settings)
        
        debug_logger.log("INFO", "SpecOperationManager initialized")
    
    def validate_file_paths(self, file_paths: List[str], force: bool = False) -> List[str]:
        """Validate and normalize file paths for spec operations.
        
        Args:
            file_paths: List of file paths to validate
            force: Whether to force validation (skip some checks)
            
        Returns:
            List of validated and normalized file paths
            
        Raises:
            SpecValidationError: If validation fails
        """
        debug_logger.log("INFO", "Validating file paths",
                        file_count=len(file_paths), force=force)
        
        validated_paths = []
        validation_errors = []
        
        for file_path_str in file_paths:
            try:
                # Convert to Path and resolve
                file_path = Path(file_path_str)
                resolved_path = self.path_resolver.resolve_input_path(file_path)
                
                # Check if file exists (unless force)
                if not force:
                    absolute_path = self.path_resolver.convert_to_absolute_path(resolved_path)
                    if not absolute_path.exists():
                        validation_errors.append(f"File does not exist: {file_path_str}")
                        continue
                    
                    if not absolute_path.is_file():
                        validation_errors.append(f"Path is not a file: {file_path_str}")
                        continue
                
                # Check if file is processable (unless force)
                if not force and not self.file_analyzer.is_processable_file(resolved_path):
                    validation_errors.append(f"File is not processable: {file_path_str}")
                    continue
                
                # Convert to specs context for Git operations
                specs_path = self.path_resolver.convert_to_specs_path(resolved_path)
                validated_paths.append(str(specs_path))
                
                debug_logger.log("DEBUG", "File path validated",
                               original=file_path_str,
                               resolved=str(resolved_path),
                               specs_path=str(specs_path))
                
            except Exception as e:
                validation_errors.append(f"Invalid file path '{file_path_str}': {e}")
        
        if validation_errors and not force:
            error_msg = "File path validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            debug_logger.log("ERROR", "File path validation failed",
                           errors=validation_errors)
            raise SpecValidationError(error_msg)
        
        if not validated_paths:
            raise SpecValidationError("No valid file paths provided")
        
        debug_logger.log("INFO", "File path validation complete",
                        input_count=len(file_paths),
                        validated_count=len(validated_paths),
                        errors=len(validation_errors))
        
        return validated_paths
    
    def validate_repository_state(self) -> Dict[str, Any]:
        """Validate the current state of the spec repository.
        
        Returns:
            Dictionary with validation results
        """
        debug_logger.log("INFO", "Validating repository state")
        
        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "checks_performed": [],
        }
        
        try:
            # Check basic directory structure
            self._check_directory_structure(validation_result)
            
            # Check for orphaned spec files
            self._check_orphaned_specs(validation_result)
            
            # Check for corrupted spec files
            self._check_spec_file_integrity(validation_result)
            
            # Check Git repository state
            self._check_git_repository_state(validation_result)
            
            # Determine overall validity
            validation_result["is_valid"] = len(validation_result["issues"]) == 0
            
            debug_logger.log("INFO", "Repository state validation complete",
                           is_valid=validation_result["is_valid"],
                           issues=len(validation_result["issues"]),
                           warnings=len(validation_result["warnings"]))
            
            return validation_result
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Validation error: {e}")
            debug_logger.log("ERROR", "Repository validation failed", error=str(e))
            return validation_result
    
    def _check_directory_structure(self, result: Dict[str, Any]) -> None:
        """Check basic directory structure."""
        result["checks_performed"].append("directory_structure")
        
        # Check .specs directory
        if not self.settings.specs_dir.exists():
            result["issues"].append(f".specs directory does not exist: {self.settings.specs_dir}")
        elif not self.settings.specs_dir.is_dir():
            result["issues"].append(f".specs path is not a directory: {self.settings.specs_dir}")
        elif not os.access(self.settings.specs_dir, os.W_OK):
            result["issues"].append(f".specs directory is not writable: {self.settings.specs_dir}")
        
        # Check .spec Git directory
        if not self.settings.spec_dir.exists():
            result["issues"].append(f".spec Git directory does not exist: {self.settings.spec_dir}")
        elif not self.settings.spec_dir.is_dir():
            result["issues"].append(f".spec path is not a directory: {self.settings.spec_dir}")
    
    def _check_orphaned_specs(self, result: Dict[str, Any]) -> None:
        """Check for orphaned spec files (specs without corresponding source files)."""
        result["checks_performed"].append("orphaned_specs")
        
        if not self.settings.specs_dir.exists():
            return
        
        try:
            orphaned_specs = []
            
            # Find all spec directories
            for spec_dir in self.settings.specs_dir.rglob("*"):
                if not spec_dir.is_dir():
                    continue
                
                # Check if this looks like a spec directory (contains index.md or history.md)
                if not any((spec_dir / filename).exists() for filename in ["index.md", "history.md"]):
                    continue
                
                # Convert spec directory back to source file path
                try:
                    relative_spec_path = spec_dir.relative_to(self.settings.specs_dir)
                    source_path = self.settings.root_path / relative_spec_path
                    
                    if not source_path.exists():
                        orphaned_specs.append(str(spec_dir))
                        
                except ValueError:
                    # Spec directory path doesn't match expected structure
                    result["warnings"].append(f"Unexpected spec directory structure: {spec_dir}")
            
            if orphaned_specs:
                result["warnings"].extend([
                    f"Orphaned spec directory (source file no longer exists): {spec_dir}"
                    for spec_dir in orphaned_specs[:5]  # Limit to first 5
                ])
                
                if len(orphaned_specs) > 5:
                    result["warnings"].append(f"... and {len(orphaned_specs) - 5} more orphaned spec directories")
            
        except Exception as e:
            result["warnings"].append(f"Could not check for orphaned specs: {e}")
    
    def _check_spec_file_integrity(self, result: Dict[str, Any]) -> None:
        """Check for corrupted or invalid spec files."""
        result["checks_performed"].append("spec_file_integrity")
        
        if not self.settings.specs_dir.exists():
            return
        
        try:
            corrupted_files = []
            
            # Check all .md files in .specs directory
            for md_file in self.settings.specs_dir.rglob("*.md"):
                try:
                    # Basic file integrity check
                    if md_file.stat().st_size == 0:
                        corrupted_files.append(f"Empty file: {md_file}")
                        continue
                    
                    # Try to read the file
                    with md_file.open('r', encoding='utf-8') as f:
                        content = f.read(100)  # Read first 100 characters
                        if not content.strip():
                            corrupted_files.append(f"File appears empty: {md_file}")
                        
                except (UnicodeDecodeError, OSError) as e:
                    corrupted_files.append(f"Cannot read file {md_file}: {e}")
            
            if corrupted_files:
                result["issues"].extend(corrupted_files[:10])  # Limit to first 10
                
                if len(corrupted_files) > 10:
                    result["issues"].append(f"... and {len(corrupted_files) - 10} more corrupted spec files")
            
        except Exception as e:
            result["warnings"].append(f"Could not check spec file integrity: {e}")
    
    def _check_git_repository_state(self, result: Dict[str, Any]) -> None:
        """Check Git repository state."""
        result["checks_performed"].append("git_repository_state")
        
        try:
            # Check if .spec directory has basic Git structure
            git_objects_dir = self.settings.spec_dir / "objects"
            git_refs_dir = self.settings.spec_dir / "refs"
            git_head_file = self.settings.spec_dir / "HEAD"
            
            if not git_objects_dir.exists():
                result["issues"].append("Git objects directory missing in .spec")
            
            if not git_refs_dir.exists():
                result["issues"].append("Git refs directory missing in .spec")
            
            if not git_head_file.exists():
                result["issues"].append("Git HEAD file missing in .spec")
            
        except Exception as e:
            result["warnings"].append(f"Could not check Git repository state: {e}")
    
    def cleanup_orphaned_specs(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up orphaned spec files and directories.
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Dictionary with cleanup results
        """
        debug_logger.log("INFO", "Cleaning up orphaned specs", dry_run=dry_run)
        
        cleanup_result = {
            "orphaned_specs": [],
            "cleaned_up": [],
            "errors": [],
            "dry_run": dry_run,
        }
        
        if not self.settings.specs_dir.exists():
            debug_logger.log("INFO", "No .specs directory found, nothing to clean up")
            return cleanup_result
        
        try:
            # Find orphaned spec directories
            for spec_dir in self.settings.specs_dir.rglob("*"):
                if not spec_dir.is_dir():
                    continue
                
                # Check if this looks like a spec directory
                if not any((spec_dir / filename).exists() for filename in ["index.md", "history.md"]):
                    continue
                
                try:
                    # Convert spec directory back to source file path
                    relative_spec_path = spec_dir.relative_to(self.settings.specs_dir)
                    source_path = self.settings.root_path / relative_spec_path
                    
                    if not source_path.exists():
                        orphaned_spec = {
                            "spec_directory": str(spec_dir),
                            "expected_source": str(source_path),
                            "relative_path": str(relative_spec_path),
                        }
                        cleanup_result["orphaned_specs"].append(orphaned_spec)
                        
                        # Clean up if not dry run
                        if not dry_run:
                            try:
                                import shutil
                                shutil.rmtree(spec_dir)
                                cleanup_result["cleaned_up"].append(orphaned_spec)
                                debug_logger.log("INFO", "Removed orphaned spec directory",
                                               spec_dir=str(spec_dir))
                            except Exception as e:
                                error_msg = f"Failed to remove {spec_dir}: {e}"
                                cleanup_result["errors"].append(error_msg)
                                debug_logger.log("ERROR", error_msg)
                        
                except ValueError as e:
                    debug_logger.log("WARNING", "Invalid spec directory structure",
                                   spec_dir=str(spec_dir), error=str(e))
            
            debug_logger.log("INFO", "Orphaned spec cleanup complete",
                           found=len(cleanup_result["orphaned_specs"]),
                           cleaned=len(cleanup_result["cleaned_up"]),
                           errors=len(cleanup_result["errors"]))
            
            return cleanup_result
            
        except Exception as e:
            error_msg = f"Failed to cleanup orphaned specs: {e}"
            cleanup_result["errors"].append(error_msg)
            debug_logger.log("ERROR", error_msg)
            return cleanup_result
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get statistics about spec operations and repository state.
        
        Returns:
            Dictionary with operation statistics
        """
        debug_logger.log("INFO", "Gathering operation statistics")
        
        stats = {
            "repository": {
                "specs_directory_exists": self.settings.specs_dir.exists(),
                "git_directory_exists": self.settings.spec_dir.exists(),
            },
            "files": {
                "total_spec_files": 0,
                "spec_directories": 0,
                "index_files": 0,
                "history_files": 0,
            },
            "content": {
                "total_size_bytes": 0,
                "average_file_size": 0,
                "recent_modifications": 0,
            },
        }
        
        if self.settings.specs_dir.exists():
            try:
                # Count files and directories
                spec_files = list(self.settings.specs_dir.rglob("*.md"))
                stats["files"]["total_spec_files"] = len(spec_files)
                
                # Count specific file types
                for spec_file in spec_files:
                    if spec_file.name == "index.md":
                        stats["files"]["index_files"] += 1
                    elif spec_file.name == "history.md":
                        stats["files"]["history_files"] += 1
                    
                    # Add to total size
                    try:
                        stats["content"]["total_size_bytes"] += spec_file.stat().st_size
                    except OSError:
                        pass
                
                # Count spec directories
                spec_dirs = [
                    d for d in self.settings.specs_dir.rglob("*")
                    if d.is_dir() and any((d / f).exists() for f in ["index.md", "history.md"])
                ]
                stats["files"]["spec_directories"] = len(spec_dirs)
                
                # Calculate average file size
                if stats["files"]["total_spec_files"] > 0:
                    stats["content"]["average_file_size"] = (
                        stats["content"]["total_size_bytes"] / stats["files"]["total_spec_files"]
                    )
                
                # Count recent modifications (last 7 days)
                import time
                week_ago = time.time() - (7 * 24 * 60 * 60)
                for spec_file in spec_files:
                    try:
                        if spec_file.stat().st_mtime > week_ago:
                            stats["content"]["recent_modifications"] += 1
                    except OSError:
                        pass
                
            except Exception as e:
                debug_logger.log("WARNING", "Could not gather complete statistics", error=str(e))
        
        debug_logger.log("INFO", "Operation statistics gathered",
                        spec_files=stats["files"]["total_spec_files"],
                        spec_directories=stats["files"]["spec_directories"])
        
        return stats
```

## Test Requirements

Create comprehensive tests for the spec repository orchestration:

### Test Cases (30 tests total)

**SpecRepository Tests:**
1. **test_spec_repository_initializes_properly**
2. **test_spec_repository_checks_initialization_status**
3. **test_spec_repository_adds_files_successfully**
4. **test_spec_repository_commits_changes**
5. **test_spec_repository_generates_specs_for_files**
6. **test_spec_repository_generates_specs_with_ai_enabled**
7. **test_spec_repository_handles_template_presets**
8. **test_spec_repository_backs_up_existing_specs**
9. **test_spec_repository_gets_comprehensive_status**
10. **test_spec_repository_shows_git_log**
11. **test_spec_repository_shows_git_diff**
12. **test_spec_repository_shows_git_status**
13. **test_spec_repository_cleans_up_orphaned_files**
14. **test_spec_repository_performs_health_check**
15. **test_spec_repository_handles_uninitialized_state**
16. **test_spec_repository_validates_before_operations**

**SpecOperationManager Tests:**
17. **test_operation_manager_validates_file_paths**
18. **test_operation_manager_handles_invalid_file_paths**
19. **test_operation_manager_forces_validation_when_requested**
20. **test_operation_manager_validates_repository_state**
21. **test_operation_manager_detects_directory_structure_issues**
22. **test_operation_manager_finds_orphaned_specs**
23. **test_operation_manager_checks_spec_file_integrity**
24. **test_operation_manager_validates_git_repository_state**
25. **test_operation_manager_cleans_up_orphaned_specs**
26. **test_operation_manager_handles_cleanup_errors**
27. **test_operation_manager_gathers_operation_statistics**

**Integration Tests:**
28. **test_spec_repository_integrates_with_git_operations**
29. **test_spec_repository_integrates_with_template_system**
30. **test_spec_repository_coordinates_all_subsystems**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/core/test_spec_repository.py tests/unit/core/test_operations.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/core/ --cov=spec_cli.core --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/core/

# Check code formatting
poetry run ruff check spec_cli/core/
poetry run ruff format spec_cli/core/

# Verify imports work correctly
python -c "from spec_cli.core import SpecRepository, SpecOperationManager; print('Import successful')"

# Test repository initialization workflow
python -c "
from spec_cli.core import SpecRepository
from pathlib import Path

repo = SpecRepository()
print(f'Repository initialized: {repo.is_initialized()}')

# Get repository health
health = repo.get_repository_health()
print(f'Health status: {health[\"overall_status\"]}')
print(f'Checks: {list(health[\"checks\"].keys())}')

if health['recommendations']:
    print(f'Recommendations: {health[\"recommendations\"][:3]}...')
"

# Test operation manager validation
python -c "
from spec_cli.core import SpecOperationManager
from pathlib import Path

manager = SpecOperationManager()

# Test file path validation
test_paths = ['spec_cli/__main__.py', 'nonexistent.py']
try:
    validated = manager.validate_file_paths(test_paths, force=True)
    print(f'Validated paths: {len(validated)}')
except Exception as e:
    print(f'Validation error: {e}')

# Test repository state validation
state = manager.validate_repository_state()
print(f'Repository state valid: {state[\"is_valid\"]}')
print(f'Checks performed: {state[\"checks_performed\"]}')
"

# Test repository status and statistics
python -c "
from spec_cli.core import SpecRepository
import json

repo = SpecRepository()

# Get repository status
status = repo.get_status()
print('Repository Status:')
print(f'  Initialized: {status[\"initialized\"]}')
if 'spec_file_count' in status:
    print(f'  Spec files: {status[\"spec_file_count\"]}')

# Get operation statistics
manager = repo.operation_manager
stats = manager.get_operation_statistics()
print('Operation Statistics:')
print(f'  Specs dir exists: {stats[\"repository\"][\"specs_directory_exists\"]}')
print(f'  Total spec files: {stats[\"files\"][\"total_spec_files\"]}')
"

# Test cleanup operations
python -c "
from spec_cli.core import SpecRepository

repo = SpecRepository()

# Test cleanup (dry run)
cleanup_result = repo.cleanup_repository(dry_run=True)
print(f'Cleanup (dry run):')
print(f'  Orphaned specs found: {len(cleanup_result[\"orphaned_specs\"])}')
print(f'  Would clean up: {len(cleanup_result[\"orphaned_specs\"])}')
print(f'  Errors: {len(cleanup_result[\"errors\"])}')
"
```

## Definition of Done

- [ ] `SpecRepository` class with comprehensive high-level operations
- [ ] Integration of Git operations with file processing workflows
- [ ] Spec generation orchestration with template system integration
- [ ] Repository state management and validation capabilities
- [ ] `SpecOperationManager` for operation validation and coordination
- [ ] Batch operations support for multiple files
- [ ] Error recovery and rollback capabilities
- [ ] Repository health checking and diagnostics
- [ ] Cleanup operations for orphaned and invalid specs
- [ ] All 30 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with all previous system components
- [ ] Comprehensive operation statistics and reporting

## Next Slice Preparation

This slice enables **slice-11-file-processing.md** by providing:
- `SpecRepository` as the main orchestration layer for all spec operations
- High-level operations that CLI commands can use directly
- Repository state management and validation
- Integration point for all subsystems (Git, templates, file system)

The file processing slice will use this repository orchestration to provide the batch processing workflows and advanced file handling capabilities.