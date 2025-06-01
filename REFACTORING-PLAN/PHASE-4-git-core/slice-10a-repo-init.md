# Slice 10A: Repository Initialization and State Management

## Goal

Create and verify spec repository setup, implement branch-cleanliness guards, and bootstrap .spec folder with comprehensive state checking.

## Context

This slice focuses specifically on repository initialization and state validation. Building on the Git operations from slice-9, it creates the foundation for spec repository management by handling repo creation, state verification, and safety checks. It establishes the core repository structure without the complexity of high-level workflow operations.

## Scope

**Included in this slice:**
- SpecRepositoryInitializer for repo creation and verification
- Branch cleanliness validation and safety guards
- .spec folder bootstrap with proper structure
- Repository state checking and health validation
- Initialization error recovery and diagnostics

**NOT included in this slice:**
- Git command wrappers (moved to slice-10b)
- High-level spec workflow operations (moved to slice-10c)
- File processing or conflict resolution (comes in slice-11)
- User interface integration (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for repository errors)
- `spec_cli.logging.debug` (debug_logger for initialization tracking)
- `spec_cli.config.settings` (SpecSettings for repository configuration)
- `spec_cli.git.repository` (SpecGitRepository for Git operations)
- `spec_cli.file_system.directory_manager` (DirectoryManager for directory operations)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `SpecGitRepository` from slice-9-git-operations
- `DirectoryManager` from slice-6b-directory-operations

## Files to Create

```
spec_cli/core/
├── __init__.py             # Module exports
├── repository_init.py      # SpecRepositoryInitializer class
└── repository_state.py     # Repository state checking utilities
```

## Implementation Steps

### Step 1: Create spec_cli/core/__init__.py

```python
"""Core business logic for spec CLI.

This package contains the main orchestration logic for spec operations,
repository management, and high-level workflows.
"""

from .repository_init import SpecRepositoryInitializer
from .repository_state import RepositoryStateChecker

__all__ = [
    "SpecRepositoryInitializer",
    "RepositoryStateChecker",
]
```

### Step 2: Create spec_cli/core/repository_state.py

```python
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..exceptions import SpecRepositoryError, SpecGitError
from ..config.settings import get_settings, SpecSettings
from ..git.repository import SpecGitRepository
from ..logging.debug import debug_logger

class RepositoryHealth(Enum):
    """Repository health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class BranchStatus(Enum):
    """Branch status for cleanliness checking."""
    CLEAN = "clean"
    UNCOMMITTED_CHANGES = "uncommitted_changes"
    UNTRACKED_FILES = "untracked_files"
    STAGED_CHANGES = "staged_changes"
    DIVERGED = "diverged"
    UNKNOWN = "unknown"

class RepositoryStateChecker:
    """Checks and validates spec repository state and health."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)
        
        debug_logger.log("INFO", "RepositoryStateChecker initialized")
    
    def check_repository_health(self) -> Dict[str, Any]:
        """Perform comprehensive repository health check.
        
        Returns:
            Dictionary with health status and detailed information
        """
        debug_logger.log("INFO", "Performing repository health check")
        
        health_report = {
            "overall_health": RepositoryHealth.HEALTHY,
            "issues": [],
            "warnings": [],
            "checks": {
                "spec_repo_exists": False,
                "spec_dir_exists": False,
                "git_repo_valid": False,
                "branch_status": BranchStatus.UNKNOWN,
                "work_tree_valid": False,
                "permissions_ok": False,
            },
            "details": {},
        }
        
        try:
            with debug_logger.timer("repository_health_check"):
                # Check .spec repository existence
                self._check_spec_repository(health_report)
                
                # Check .specs directory
                self._check_specs_directory(health_report)
                
                # Check Git repository validity
                self._check_git_repository(health_report)
                
                # Check branch status
                self._check_branch_status(health_report)
                
                # Check work tree validity
                self._check_work_tree(health_report)
                
                # Check permissions
                self._check_permissions(health_report)
                
                # Determine overall health
                self._determine_overall_health(health_report)
            
            debug_logger.log("INFO", "Repository health check complete",
                           overall_health=health_report["overall_health"].value,
                           issues=len(health_report["issues"]),
                           warnings=len(health_report["warnings"]))
            
            return health_report
            
        except Exception as e:
            error_msg = f"Repository health check failed: {e}"
            debug_logger.log("ERROR", error_msg)
            health_report["overall_health"] = RepositoryHealth.CRITICAL
            health_report["issues"].append(error_msg)
            return health_report
    
    def _check_spec_repository(self, report: Dict[str, Any]) -> None:
        """Check if .spec repository exists and is valid."""
        spec_dir = self.settings.spec_git_dir
        
        if spec_dir.exists() and spec_dir.is_dir():
            report["checks"]["spec_repo_exists"] = True
            
            # Check if it's a valid Git repository
            if (spec_dir / "HEAD").exists():
                report["details"]["spec_repo_path"] = str(spec_dir)
            else:
                report["issues"].append(f"Directory {spec_dir} exists but is not a valid Git repository")
        else:
            report["checks"]["spec_repo_exists"] = False
            report["details"]["spec_repo_missing"] = str(spec_dir)
    
    def _check_specs_directory(self, report: Dict[str, Any]) -> None:
        """Check if .specs directory exists and is accessible."""
        specs_dir = self.settings.specs_dir
        
        if specs_dir.exists() and specs_dir.is_dir():
            report["checks"]["spec_dir_exists"] = True
            report["details"]["specs_dir_path"] = str(specs_dir)
            
            # Check if directory is empty or has content
            try:
                content_count = len(list(specs_dir.rglob("*")))
                report["details"]["specs_content_count"] = content_count
            except OSError as e:
                report["warnings"].append(f"Could not scan .specs directory: {e}")
        else:
            report["checks"]["spec_dir_exists"] = False
            report["details"]["specs_dir_missing"] = str(specs_dir)
    
    def _check_git_repository(self, report: Dict[str, Any]) -> None:
        """Check if Git repository is valid and accessible."""
        try:
            if self.git_repo.is_initialized():
                report["checks"]["git_repo_valid"] = True
                
                # Get additional Git info
                try:
                    current_branch = self.git_repo.get_current_branch()
                    report["details"]["current_branch"] = current_branch
                except Exception as e:
                    report["warnings"].append(f"Could not determine current branch: {e}")
                
                try:
                    commit_count = len(self.git_repo.get_recent_commits(5))
                    report["details"]["recent_commits"] = commit_count
                except Exception as e:
                    report["warnings"].append(f"Could not access recent commits: {e}")
            else:
                report["checks"]["git_repo_valid"] = False
                report["issues"].append("Spec Git repository is not properly initialized")
                
        except Exception as e:
            report["checks"]["git_repo_valid"] = False
            report["issues"].append(f"Git repository check failed: {e}")
    
    def _check_branch_status(self, report: Dict[str, Any]) -> None:
        """Check branch cleanliness and status."""
        try:
            if report["checks"]["git_repo_valid"]:
                branch_status = self.check_branch_cleanliness()
                report["checks"]["branch_status"] = branch_status
                report["details"]["branch_clean"] = branch_status == BranchStatus.CLEAN
                
                if branch_status != BranchStatus.CLEAN:
                    report["warnings"].append(f"Branch is not clean: {branch_status.value}")
            else:
                report["checks"]["branch_status"] = BranchStatus.UNKNOWN
                
        except Exception as e:
            report["checks"]["branch_status"] = BranchStatus.UNKNOWN
            report["warnings"].append(f"Could not check branch status: {e}")
    
    def _check_work_tree(self, report: Dict[str, Any]) -> None:
        """Check if work tree is valid and accessible."""
        try:
            if report["checks"]["git_repo_valid"]:
                # Verify work tree configuration
                work_tree = self.settings.specs_dir
                if work_tree.exists():
                    report["checks"]["work_tree_valid"] = True
                    report["details"]["work_tree_path"] = str(work_tree)
                else:
                    report["checks"]["work_tree_valid"] = False
                    report["issues"].append(f"Work tree directory does not exist: {work_tree}")
            else:
                report["checks"]["work_tree_valid"] = False
                
        except Exception as e:
            report["checks"]["work_tree_valid"] = False
            report["warnings"].append(f"Work tree check failed: {e}")
    
    def _check_permissions(self, report: Dict[str, Any]) -> None:
        """Check file system permissions for spec operations."""
        import os
        
        permissions_ok = True
        permission_issues = []
        
        # Check .spec directory permissions
        spec_dir = self.settings.spec_git_dir
        if spec_dir.exists():
            if not os.access(spec_dir, os.R_OK | os.W_OK):
                permissions_ok = False
                permission_issues.append(f"No read/write access to {spec_dir}")
        
        # Check .specs directory permissions
        specs_dir = self.settings.specs_dir
        if specs_dir.exists():
            if not os.access(specs_dir, os.R_OK | os.W_OK):
                permissions_ok = False
                permission_issues.append(f"No read/write access to {specs_dir}")
        
        # Check parent directory permissions for creation
        parent_dir = spec_dir.parent
        if not os.access(parent_dir, os.W_OK):
            permissions_ok = False
            permission_issues.append(f"No write access to parent directory {parent_dir}")
        
        report["checks"]["permissions_ok"] = permissions_ok
        if permission_issues:
            report["issues"].extend(permission_issues)
        
        report["details"]["permission_issues"] = permission_issues
    
    def _determine_overall_health(self, report: Dict[str, Any]) -> None:
        """Determine overall repository health based on checks."""
        checks = report["checks"]
        issues = report["issues"]
        warnings = report["warnings"]
        
        if issues:
            if not checks["permissions_ok"] or not checks["git_repo_valid"]:
                report["overall_health"] = RepositoryHealth.CRITICAL
            else:
                report["overall_health"] = RepositoryHealth.ERROR
        elif warnings:
            report["overall_health"] = RepositoryHealth.WARNING
        else:
            report["overall_health"] = RepositoryHealth.HEALTHY
    
    def check_branch_cleanliness(self) -> BranchStatus:
        """Check if the current branch is clean for spec operations.
        
        Returns:
            BranchStatus indicating the cleanliness state
        """
        debug_logger.log("DEBUG", "Checking branch cleanliness")
        
        try:
            # Check for uncommitted changes
            if self.git_repo.has_uncommitted_changes():
                debug_logger.log("WARNING", "Branch has uncommitted changes")
                return BranchStatus.UNCOMMITTED_CHANGES
            
            # Check for untracked files
            if self.git_repo.has_untracked_files():
                debug_logger.log("WARNING", "Branch has untracked files")
                return BranchStatus.UNTRACKED_FILES
            
            # Check for staged changes
            if self.git_repo.has_staged_changes():
                debug_logger.log("WARNING", "Branch has staged changes")
                return BranchStatus.STAGED_CHANGES
            
            debug_logger.log("INFO", "Branch is clean")
            return BranchStatus.CLEAN
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to check branch cleanliness", error=str(e))
            return BranchStatus.UNKNOWN
    
    def is_safe_for_spec_operations(self) -> bool:
        """Check if repository is safe for spec operations.
        
        Returns:
            True if safe to proceed with spec operations
        """
        try:
            health = self.check_repository_health()
            
            # Repository must be healthy or have only warnings
            if health["overall_health"] in [RepositoryHealth.ERROR, RepositoryHealth.CRITICAL]:
                return False
            
            # Must have basic repository structure
            checks = health["checks"]
            if not (checks["spec_repo_exists"] and checks["git_repo_valid"]):
                return False
            
            # Must have proper permissions
            if not checks["permissions_ok"]:
                return False
            
            return True
            
        except Exception as e:
            debug_logger.log("ERROR", "Safety check failed", error=str(e))
            return False
    
    def get_repository_summary(self) -> Dict[str, Any]:
        """Get a concise summary of repository status.
        
        Returns:
            Dictionary with summary information
        """
        try:
            health = self.check_repository_health()
            
            summary = {
                "initialized": health["checks"]["spec_repo_exists"],
                "healthy": health["overall_health"] in [RepositoryHealth.HEALTHY, RepositoryHealth.WARNING],
                "safe_for_operations": self.is_safe_for_spec_operations(),
                "branch_clean": health["checks"]["branch_status"] == BranchStatus.CLEAN,
                "specs_dir_exists": health["checks"]["spec_dir_exists"],
                "issue_count": len(health["issues"]),
                "warning_count": len(health["warnings"]),
                "current_branch": health["details"].get("current_branch", "unknown"),
            }
            
            return summary
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to get repository summary", error=str(e))
            return {
                "initialized": False,
                "healthy": False,
                "safe_for_operations": False,
                "error": str(e),
            }
    
    def validate_pre_operation_state(self, operation_name: str) -> List[str]:
        """Validate that repository state is ready for a specific operation.
        
        Args:
            operation_name: Name of the operation being attempted
            
        Returns:
            List of validation issues (empty if valid)
        """
        debug_logger.log("INFO", "Validating pre-operation state", operation=operation_name)
        
        issues = []
        
        try:
            health = self.check_repository_health()
            
            # Check overall health
            if health["overall_health"] == RepositoryHealth.CRITICAL:
                issues.append(f"Repository is in critical state, cannot perform {operation_name}")
                return issues  # Don't continue if critical
            
            # Check basic requirements
            if not health["checks"]["spec_repo_exists"]:
                issues.append("Spec repository not initialized")
            
            if not health["checks"]["git_repo_valid"]:
                issues.append("Git repository is not valid")
            
            if not health["checks"]["permissions_ok"]:
                issues.append("Insufficient permissions for spec operations")
            
            # Operation-specific validations
            if operation_name in ["commit", "add", "generate"]:
                if health["checks"]["branch_status"] not in [BranchStatus.CLEAN, BranchStatus.UNTRACKED_FILES]:
                    issues.append(f"Branch is not clean for {operation_name} operation")
            
            # Add any health issues as validation failures
            issues.extend(health["issues"])
            
        except Exception as e:
            issues.append(f"Pre-operation validation failed: {e}")
        
        debug_logger.log("INFO", "Pre-operation validation complete",
                        operation=operation_name,
                        issues=len(issues))
        
        return issues
```

### Step 3: Create spec_cli/core/repository_init.py

```python
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..exceptions import SpecRepositoryError, SpecGitError, SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..git.repository import SpecGitRepository
from ..file_system.directory_manager import DirectoryManager
from ..logging.debug import debug_logger
from .repository_state import RepositoryStateChecker, RepositoryHealth

class SpecRepositoryInitializer:
    """Handles spec repository initialization and setup."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
        self.state_checker = RepositoryStateChecker(self.settings)
        
        debug_logger.log("INFO", "SpecRepositoryInitializer initialized")
    
    def initialize_repository(self, force: bool = False) -> Dict[str, Any]:
        """Initialize a new spec repository with full setup.
        
        Args:
            force: Whether to reinitialize if repository already exists
            
        Returns:
            Dictionary with initialization results
            
        Raises:
            SpecRepositoryError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing spec repository", force=force)
        
        init_result = {
            "success": False,
            "created": [],
            "skipped": [],
            "errors": [],
            "warnings": [],
        }
        
        try:
            with debug_logger.timer("repository_initialization"):
                # Check current state
                current_state = self.state_checker.check_repository_health()
                
                if not force and current_state["checks"]["spec_repo_exists"]:
                    if current_state["overall_health"] in [RepositoryHealth.HEALTHY, RepositoryHealth.WARNING]:
                        init_result["skipped"].append("Repository already exists and is healthy")
                        init_result["success"] = True
                        return init_result
                
                # Initialize .spec Git repository
                self._initialize_spec_git_repo(init_result, force)
                
                # Create .specs directory structure
                self._initialize_specs_directory(init_result)
                
                # Setup ignore files
                self._setup_ignore_files(init_result)
                
                # Create initial commit if needed
                self._create_initial_commit(init_result)
                
                # Update main .gitignore
                self._update_main_gitignore(init_result)
                
                # Verify initialization
                self._verify_initialization(init_result)
                
                init_result["success"] = len(init_result["errors"]) == 0
            
            debug_logger.log("INFO", "Repository initialization complete",
                           success=init_result["success"],
                           created=len(init_result["created"]),
                           errors=len(init_result["errors"]))
            
            return init_result
            
        except Exception as e:
            error_msg = f"Repository initialization failed: {e}"
            debug_logger.log("ERROR", error_msg)
            init_result["errors"].append(error_msg)
            init_result["success"] = False
            return init_result
    
    def _initialize_spec_git_repo(self, result: Dict[str, Any], force: bool) -> None:
        """Initialize the .spec Git repository."""
        spec_dir = self.settings.spec_git_dir
        
        try:
            if force and spec_dir.exists():
                # Remove existing repository
                import shutil
                shutil.rmtree(spec_dir)
                result["created"].append(f"Removed existing repository: {spec_dir}")
            
            if not spec_dir.exists() or force:
                self.git_repo.initialize()
                result["created"].append(f"Created Git repository: {spec_dir}")
                
                # Configure repository
                self._configure_git_repository(result)
            else:
                result["skipped"].append(f"Git repository already exists: {spec_dir}")
                
        except Exception as e:
            result["errors"].append(f"Failed to initialize Git repository: {e}")
    
    def _configure_git_repository(self, result: Dict[str, Any]) -> None:
        """Configure the Git repository with appropriate settings."""
        try:
            # Set up Git configuration for spec repository
            config_commands = [
                ("user.name", "Spec CLI"),
                ("user.email", "spec-cli@local"),
                ("core.autocrlf", "input"),
                ("core.safecrlf", "true"),
            ]
            
            for key, value in config_commands:
                try:
                    self.git_repo.run_git_command(["config", key, value])
                    debug_logger.log("DEBUG", "Set Git config", key=key, value=value)
                except Exception as e:
                    result["warnings"].append(f"Could not set Git config {key}: {e}")
            
            result["created"].append("Configured Git repository settings")
            
        except Exception as e:
            result["warnings"].append(f"Git configuration failed: {e}")
    
    def _initialize_specs_directory(self, result: Dict[str, Any]) -> None:
        """Initialize the .specs directory structure."""
        try:
            self.directory_manager.ensure_specs_directory()
            result["created"].append(f"Created .specs directory: {self.settings.specs_dir}")
            
        except Exception as e:
            result["errors"].append(f"Failed to create .specs directory: {e}")
    
    def _setup_ignore_files(self, result: Dict[str, Any]) -> None:
        """Setup ignore files for the repository."""
        try:
            self.directory_manager.setup_ignore_files()
            result["created"].append("Created .specignore file with defaults")
            
        except Exception as e:
            result["warnings"].append(f"Could not setup ignore files: {e}")
    
    def _create_initial_commit(self, result: Dict[str, Any]) -> None:
        """Create an initial commit in the spec repository."""
        try:
            # Check if there are any commits
            try:
                commits = self.git_repo.get_recent_commits(1)
                if commits:
                    result["skipped"].append("Repository already has commits")
                    return
            except Exception:
                # No commits yet, proceed with initial commit
                pass
            
            # Create a simple README in .specs
            readme_path = self.settings.specs_dir / "README.md"
            if not readme_path.exists():
                readme_content = """# Spec Documentation

This directory contains versioned documentation for the project.

- Each file/directory has corresponding documentation in a mirrored structure
- `index.md` files contain current understanding and documentation
- `history.md` files track evolution, decisions, and lessons learned

Generated and maintained by [Spec CLI](https://github.com/spec-cli).
"""
                readme_path.write_text(readme_content, encoding="utf-8")
                result["created"].append(f"Created README: {readme_path}")
            
            # Add and commit the README
            try:
                self.git_repo.add_files(["README.md"])
                commit_hash = self.git_repo.commit("Initial spec repository setup")
                result["created"].append(f"Created initial commit: {commit_hash[:8]}")
            except Exception as e:
                result["warnings"].append(f"Could not create initial commit: {e}")
                
        except Exception as e:
            result["warnings"].append(f"Initial commit setup failed: {e}")
    
    def _update_main_gitignore(self, result: Dict[str, Any]) -> None:
        """Update the main project .gitignore to include spec files."""
        try:
            self.directory_manager.update_main_gitignore()
            result["created"].append("Updated main .gitignore with spec patterns")
            
        except Exception as e:
            result["warnings"].append(f"Could not update main .gitignore: {e}")
    
    def _verify_initialization(self, result: Dict[str, Any]) -> None:
        """Verify that initialization was successful."""
        try:
            health = self.state_checker.check_repository_health()
            
            if health["overall_health"] in [RepositoryHealth.HEALTHY, RepositoryHealth.WARNING]:
                result["created"].append("Repository initialization verified successfully")
            else:
                result["errors"].append("Repository initialization verification failed")
                result["errors"].extend(health["issues"])
            
        except Exception as e:
            result["warnings"].append(f"Could not verify initialization: {e}")
    
    def bootstrap_repository_structure(self) -> Dict[str, Any]:
        """Bootstrap additional repository structure and configuration.
        
        Returns:
            Dictionary with bootstrap results
        """
        debug_logger.log("INFO", "Bootstrapping repository structure")
        
        bootstrap_result = {
            "success": False,
            "created": [],
            "errors": [],
            "warnings": [],
        }
        
        try:
            # Ensure repository is initialized
            if not self.state_checker.is_safe_for_spec_operations():
                bootstrap_result["errors"].append("Repository not initialized or not safe for operations")
                return bootstrap_result
            
            # Create common directory structure in .specs
            self._create_common_directories(bootstrap_result)
            
            # Setup configuration files
            self._setup_configuration_files(bootstrap_result)
            
            # Create example templates if needed
            self._create_example_templates(bootstrap_result)
            
            bootstrap_result["success"] = len(bootstrap_result["errors"]) == 0
            
            debug_logger.log("INFO", "Repository bootstrap complete",
                           success=bootstrap_result["success"],
                           created=len(bootstrap_result["created"]))
            
            return bootstrap_result
            
        except Exception as e:
            error_msg = f"Repository bootstrap failed: {e}"
            debug_logger.log("ERROR", error_msg)
            bootstrap_result["errors"].append(error_msg)
            return bootstrap_result
    
    def _create_common_directories(self, result: Dict[str, Any]) -> None:
        """Create common directory structure in .specs."""
        common_dirs = [
            "docs",
            "src", 
            "tests",
            "config",
        ]
        
        for dir_name in common_dirs:
            dir_path = self.settings.specs_dir / dir_name
            try:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    result["created"].append(f"Created directory: {dir_path}")
            except Exception as e:
                result["warnings"].append(f"Could not create directory {dir_name}: {e}")
    
    def _setup_configuration_files(self, result: Dict[str, Any]) -> None:
        """Setup configuration files in the repository."""
        try:
            # Create .spec/config.json for repository-specific settings
            config_file = self.settings.spec_git_dir / "config.json"
            if not config_file.exists():
                import json
                config_data = {
                    "version": "1.0",
                    "created": debug_logger._get_timestamp(),
                    "settings": {
                        "auto_commit": False,
                        "backup_enabled": True,
                        "ai_enabled": False,
                    }
                }
                
                config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
                result["created"].append(f"Created config file: {config_file}")
                
        except Exception as e:
            result["warnings"].append(f"Could not create configuration files: {e}")
    
    def _create_example_templates(self, result: Dict[str, Any]) -> None:
        """Create example template files if they don't exist."""
        try:
            template_file = Path.cwd() / ".spectemplate"
            if not template_file.exists():
                example_template = """# Example Spec Template

## Purpose
{{{purpose}}}

## Overview
{{{overview}}}

## Key Information
- **File**: {{{filepath}}}
- **Type**: {{{file_type}}}
- **Last Updated**: {{{date}}}

## Implementation Notes
{{{implementation_notes}}}

## Related Documentation
{{{related_docs}}}
"""
                template_file.write_text(example_template, encoding="utf-8")
                result["created"].append(f"Created example template: {template_file}")
                
        except Exception as e:
            result["warnings"].append(f"Could not create example templates: {e}")
    
    def check_initialization_requirements(self) -> List[str]:
        """Check if system meets requirements for repository initialization.
        
        Returns:
            List of requirement issues (empty if all requirements met)
        """
        issues = []
        
        try:
            # Check if Git is available
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "--version"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                debug_logger.log("DEBUG", "Git version check", version=result.stdout.strip())
            except (subprocess.CalledProcessError, FileNotFoundError):
                issues.append("Git is not installed or not available in PATH")
            
            # Check directory permissions
            parent_dir = self.settings.spec_git_dir.parent
            if not parent_dir.exists():
                issues.append(f"Parent directory does not exist: {parent_dir}")
            else:
                import os
                if not os.access(parent_dir, os.W_OK):
                    issues.append(f"No write permission to parent directory: {parent_dir}")
            
            # Check for existing conflicting files
            if self.settings.spec_git_dir.exists() and not self.settings.spec_git_dir.is_dir():
                issues.append(f".spec exists but is not a directory: {self.settings.spec_git_dir}")
            
            if self.settings.specs_dir.exists() and not self.settings.specs_dir.is_dir():
                issues.append(f".specs exists but is not a directory: {self.settings.specs_dir}")
            
        except Exception as e:
            issues.append(f"Requirement check failed: {e}")
        
        return issues
    
    def get_initialization_plan(self) -> Dict[str, Any]:
        """Get a plan for what initialization would do.
        
        Returns:
            Dictionary describing the initialization plan
        """
        plan = {
            "actions": [],
            "requirements": self.check_initialization_requirements(),
            "current_state": self.state_checker.get_repository_summary(),
            "estimated_time": "< 10 seconds",
        }
        
        current_state = self.state_checker.check_repository_health()
        
        if not current_state["checks"]["spec_repo_exists"]:
            plan["actions"].append(f"Create Git repository: {self.settings.spec_git_dir}")
            plan["actions"].append("Configure Git repository settings")
        
        if not current_state["checks"]["spec_dir_exists"]:
            plan["actions"].append(f"Create .specs directory: {self.settings.specs_dir}")
        
        plan["actions"].extend([
            "Setup .specignore file with sensible defaults",
            "Create initial README.md in .specs",
            "Update main .gitignore to exclude spec files",
            "Create initial commit",
            "Verify repository health",
        ])
        
        return plan
```

## Test Requirements

Create comprehensive tests for repository initialization:

### Test Cases (18 tests total)

**Repository State Checker Tests:**
1. **test_repository_health_check_comprehensive**
2. **test_branch_cleanliness_detection**
3. **test_safety_validation_for_operations**
4. **test_pre_operation_state_validation**
5. **test_repository_summary_generation**
6. **test_permission_checking**

**Repository Initializer Tests:**
7. **test_repository_initialization_from_scratch**
8. **test_repository_initialization_with_force**
9. **test_repository_initialization_existing_healthy**
10. **test_git_repository_configuration**
11. **test_specs_directory_creation**
12. **test_ignore_files_setup**
13. **test_initial_commit_creation**
14. **test_repository_bootstrap_structure**

**Integration Tests:**
15. **test_initialization_requirements_checking**
16. **test_initialization_plan_generation**
17. **test_full_initialization_workflow**
18. **test_error_recovery_and_cleanup**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/core/test_repository_init.py tests/unit/core/test_repository_state.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/core/ --cov=spec_cli.core --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/core/

# Check code formatting
poetry run ruff check spec_cli/core/
poetry run ruff format spec_cli/core/

# Verify imports work correctly
python -c "from spec_cli.core import SpecRepositoryInitializer, RepositoryStateChecker; print('Import successful')"

# Test repository health checking
python -c "
from spec_cli.core.repository_state import RepositoryStateChecker

checker = RepositoryStateChecker()
health = checker.check_repository_health()
print(f'Repository health: {health["overall_health"].value}')
print(f'Issues: {len(health["issues"])}')
print(f'Warnings: {len(health["warnings"])}')

summary = checker.get_repository_summary()
print(f'Repository summary:')
for key, value in summary.items():
    print(f'  {key}: {value}')
"

# Test initialization planning
python -c "
from spec_cli.core.repository_init import SpecRepositoryInitializer

initializer = SpecRepositoryInitializer()
plan = initializer.get_initialization_plan()
print(f'Initialization plan:')
print(f'  Requirements issues: {len(plan["requirements"])}')
print(f'  Planned actions: {len(plan["actions"])}')
print(f'  Current state healthy: {plan["current_state"].get("healthy", False)}')
print(f'  Estimated time: {plan["estimated_time"]}')

if plan['requirements']:
    print('Requirements issues:')
    for issue in plan['requirements']:
        print(f'  - {issue}')

print('Planned actions:')
for action in plan['actions'][:3]:  # Show first 3 actions
    print(f'  - {action}')
"

# Test requirements checking
python -c "
from spec_cli.core.repository_init import SpecRepositoryInitializer

initializer = SpecRepositoryInitializer()
requirements = initializer.check_initialization_requirements()
if requirements:
    print(f'Requirements issues found: {len(requirements)}')
    for issue in requirements:
        print(f'  - {issue}')
else:
    print('All requirements met for initialization')
"

# Test branch cleanliness checking
python -c "
from spec_cli.core.repository_state import RepositoryStateChecker, BranchStatus

checker = RepositoryStateChecker()
status = checker.check_branch_cleanliness()
print(f'Branch status: {status.value}')
print(f'Is clean: {status == BranchStatus.CLEAN}')

safe = checker.is_safe_for_spec_operations()
print(f'Safe for operations: {safe}')
"
```

## Definition of Done

- [ ] SpecRepositoryInitializer class for repository creation and setup
- [ ] RepositoryStateChecker class for health monitoring and validation
- [ ] Branch cleanliness guards and safety checks
- [ ] .spec folder bootstrap with proper Git configuration
- [ ] Repository health checking with comprehensive diagnostics
- [ ] Pre-operation state validation for different operation types
- [ ] Initialization requirements checking and planning
- [ ] Error recovery and cleanup capabilities
- [ ] All 18 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with Git operations and directory management
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-10b (commit wrappers) by providing:
- Repository initialization and state management that commit operations can rely on
- Branch cleanliness validation that commit operations can use for safety
- Repository health checking that commit operations can verify before proceeding
- Foundation for safe Git operations in an isolated spec repository