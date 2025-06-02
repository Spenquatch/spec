import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from ..exceptions import SpecGitError, SpecRepositoryError
from ..config.settings import get_settings, SpecSettings
from ..git.repository import SpecGitRepository
from ..logging.debug import debug_logger
from .repository_state import RepositoryStateChecker, BranchStatus

class SpecCommitManager:
    """Manages Git commit operations for spec repository."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)
        self.state_checker = RepositoryStateChecker(self.settings)
        
        debug_logger.log("INFO", "SpecCommitManager initialized")
    
    def add_files(self, 
                  file_paths: List[str], 
                  force: bool = False,
                  validate: bool = True) -> Dict[str, Any]:
        """Add files to the Git staging area.
        
        Args:
            file_paths: List of file paths to add (relative to .specs)
            force: Whether to force add files (bypass ignore rules)
            validate: Whether to validate repository state before adding
            
        Returns:
            Dictionary with add operation results
            
        Raises:
            SpecGitError: If add operation fails
        """
        debug_logger.log("INFO", "Adding files to staging area",
                        file_count=len(file_paths),
                        force=force)
        
        add_result = {
            "success": False,
            "added": [],
            "skipped": [],
            "errors": [],
            "warnings": [],
        }
        
        try:
            with debug_logger.timer("git_add_operation"):
                # Validate repository state if requested
                if validate:
                    validation_issues = self._validate_for_add_operation()
                    if validation_issues:
                        add_result["errors"].extend(validation_issues)
                        return add_result
                
                # Process each file
                for file_path in file_paths:
                    try:
                        self._add_single_file(file_path, force, add_result)
                    except Exception as e:
                        add_result["errors"].append(f"Failed to add {file_path}: {e}")
                        debug_logger.log("ERROR", "File add failed",
                                       file_path=file_path, error=str(e))
                
                add_result["success"] = len(add_result["errors"]) == 0
            
            debug_logger.log("INFO", "Add operation complete",
                           success=add_result["success"],
                           added=len(add_result["added"]),
                           errors=len(add_result["errors"]))
            
            return add_result
            
        except Exception as e:
            error_msg = f"Add operation failed: {e}"
            debug_logger.log("ERROR", error_msg)
            add_result["errors"].append(error_msg)
            raise SpecGitError(error_msg) from e
    
    def _add_single_file(self, file_path: str, force: bool, result: Dict[str, Any]) -> None:
        """Add a single file to staging area."""
        # Validate file exists in .specs
        full_path = self.settings.specs_dir / file_path
        if not full_path.exists():
            result["errors"].append(f"File does not exist: {file_path}")
            return
        
        # Check if file is already staged
        try:
            staged_files = self.git_repo.get_staged_files()
            if file_path in staged_files:
                result["skipped"].append(f"File already staged: {file_path}")
                return
        except Exception as e:
            result["warnings"].append(f"Could not check staging status for {file_path}: {e}")
        
        # Add file to Git
        try:
            add_args = ["add"]
            if force:
                add_args.append("-f")
            add_args.append(file_path)
            
            self.git_repo.run_git_command(add_args)
            result["added"].append(file_path)
            
            debug_logger.log("DEBUG", "File added to staging",
                           file_path=file_path, force=force)
            
        except Exception as e:
            result["errors"].append(f"Git add failed for {file_path}: {e}")
    
    def commit_changes(self,
                      message: str,
                      author: Optional[str] = None,
                      validate: bool = True,
                      allow_empty: bool = False) -> Dict[str, Any]:
        """Commit staged changes to the repository.
        
        Args:
            message: Commit message
            author: Optional author override
            validate: Whether to validate repository state before committing
            allow_empty: Whether to allow empty commits
            
        Returns:
            Dictionary with commit operation results
            
        Raises:
            SpecGitError: If commit operation fails
        """
        debug_logger.log("INFO", "Committing changes",
                        message_length=len(message),
                        author=author)
        
        commit_result = {
            "success": False,
            "commit_hash": None,
            "files_committed": [],
            "errors": [],
            "warnings": [],
        }
        
        try:
            with debug_logger.timer("git_commit_operation"):
                # Validate repository state if requested
                if validate:
                    validation_issues = self._validate_for_commit_operation(allow_empty)
                    if validation_issues:
                        commit_result["errors"].extend(validation_issues)
                        return commit_result
                
                # Format commit message
                formatted_message = self._format_commit_message(message)
                
                # Get staged files for reference
                try:
                    staged_files = self.git_repo.get_staged_files()
                    commit_result["files_committed"] = staged_files
                except Exception as e:
                    commit_result["warnings"].append(f"Could not get staged files: {e}")
                
                # Perform commit
                commit_args = ["commit", "-m", formatted_message]
                if author:
                    commit_args.extend(["--author", author])
                if allow_empty:
                    commit_args.append("--allow-empty")
                
                result_output = self.git_repo.run_git_command(commit_args)
                
                # Extract commit hash from output
                commit_hash = self._extract_commit_hash(str(result_output.stdout or ""))
                commit_result["commit_hash"] = commit_hash
                
                commit_result["success"] = True
            
            debug_logger.log("INFO", "Commit operation complete",
                           commit_hash=commit_hash,
                           files_committed=len(commit_result["files_committed"]))
            
            return commit_result
            
        except Exception as e:
            error_msg = f"Commit operation failed: {e}"
            debug_logger.log("ERROR", error_msg)
            commit_result["errors"].append(error_msg)
            raise SpecGitError(error_msg) from e
    
    def create_tag(self,
                   tag_name: str,
                   message: Optional[str] = None,
                   commit_hash: Optional[str] = None,
                   force: bool = False) -> Dict[str, Any]:
        """Create a Git tag for marking important commits.
        
        Args:
            tag_name: Name of the tag to create
            message: Optional tag message (creates annotated tag)
            commit_hash: Optional specific commit to tag (defaults to HEAD)
            force: Whether to overwrite existing tag
            
        Returns:
            Dictionary with tag operation results
            
        Raises:
            SpecGitError: If tag operation fails
        """
        debug_logger.log("INFO", "Creating Git tag",
                        tag_name=tag_name,
                        message=message is not None,
                        commit_hash=commit_hash)
        
        tag_result = {
            "success": False,
            "tag_name": tag_name,
            "commit_hash": commit_hash or "HEAD",
            "errors": [],
            "warnings": [],
        }
        
        try:
            with debug_logger.timer("git_tag_operation"):
                # Validate tag name
                validation_issues = self._validate_tag_name(tag_name)
                if validation_issues:
                    tag_result["errors"].extend(validation_issues)
                    return tag_result
                
                # Check if tag already exists
                if not force and self._tag_exists(tag_name):
                    tag_result["errors"].append(f"Tag already exists: {tag_name}")
                    return tag_result
                
                # Build tag command
                tag_args = ["tag"]
                if force:
                    tag_args.append("-f")
                
                if message:
                    tag_args.extend(["-a", tag_name, "-m", message])
                else:
                    tag_args.append(tag_name)
                
                if commit_hash:
                    tag_args.append(commit_hash)
                
                # Create tag
                self.git_repo.run_git_command(tag_args)
                tag_result["success"] = True
            
            debug_logger.log("INFO", "Tag creation complete",
                           tag_name=tag_name)
            
            return tag_result
            
        except Exception as e:
            error_msg = f"Tag creation failed: {e}"
            debug_logger.log("ERROR", error_msg)
            tag_result["errors"].append(error_msg)
            raise SpecGitError(error_msg) from e
    
    def rollback_to_commit(self,
                          commit_hash: str,
                          hard: bool = False,
                          create_backup: bool = True) -> Dict[str, Any]:
        """Rollback repository to a specific commit.
        
        Args:
            commit_hash: Hash of commit to rollback to
            hard: Whether to perform hard reset (loses uncommitted changes)
            create_backup: Whether to create backup tag before rollback
            
        Returns:
            Dictionary with rollback operation results
            
        Raises:
            SpecGitError: If rollback operation fails
        """
        debug_logger.log("INFO", "Rolling back to commit",
                        commit_hash=commit_hash,
                        hard=hard,
                        create_backup=create_backup)
        
        rollback_result = {
            "success": False,
            "target_commit": commit_hash,
            "backup_tag": None,
            "reset_type": "hard" if hard else "soft",
            "errors": [],
            "warnings": [],
        }
        
        try:
            with debug_logger.timer("git_rollback_operation"):
                # Validate commit exists
                if not self._commit_exists(commit_hash):
                    rollback_result["errors"].append(f"Commit does not exist: {commit_hash}")
                    return rollback_result
                
                # Create backup tag if requested
                if create_backup:
                    backup_tag_name = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    try:
                        backup_result = self.create_tag(backup_tag_name, 
                                                       f"Backup before rollback to {commit_hash}")
                        if backup_result["success"]:
                            rollback_result["backup_tag"] = backup_tag_name
                        else:
                            rollback_result["warnings"].append("Could not create backup tag")
                    except Exception as e:
                        rollback_result["warnings"].append(f"Backup tag creation failed: {e}")
                
                # Perform reset
                reset_args = ["reset"]
                if hard:
                    reset_args.append("--hard")
                reset_args.append(commit_hash)
                
                self.git_repo.run_git_command(reset_args)
                rollback_result["success"] = True
            
            debug_logger.log("INFO", "Rollback operation complete",
                           target_commit=commit_hash,
                           backup_tag=rollback_result["backup_tag"])
            
            return rollback_result
            
        except Exception as e:
            error_msg = f"Rollback operation failed: {e}"
            debug_logger.log("ERROR", error_msg)
            rollback_result["errors"].append(error_msg)
            raise SpecGitError(error_msg) from e
    
    def rollback_last_commit(self, 
                           create_backup: bool = True) -> Dict[str, Any]:
        """Rollback the last commit (soft reset).
        
        Args:
            create_backup: Whether to create backup tag
            
        Returns:
            Dictionary with rollback operation results
        """
        debug_logger.log("INFO", "Rolling back last commit")
        
        try:
            # Get current commit hash
            current_commit = self.git_repo.get_current_commit_hash()
            if not current_commit:
                return {
                    "success": False,
                    "errors": ["No commits found to rollback"],
                }
            
            # Get parent commit
            parent_commit = self.git_repo.get_parent_commit_hash(current_commit)
            if not parent_commit:
                return {
                    "success": False,
                    "errors": ["No parent commit found (this is the first commit)"],
                }
            
            # Perform rollback to parent (soft reset to keep changes)
            return self.rollback_to_commit(parent_commit, hard=False, create_backup=create_backup)
            
        except Exception as e:
            error_msg = f"Last commit rollback failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e
    
    def get_commit_status(self) -> Dict[str, Any]:
        """Get current commit status and staging information.
        
        Returns:
            Dictionary with current Git status
        """
        debug_logger.log("DEBUG", "Getting commit status")
        
        try:
            status = {
                "repository_initialized": self.git_repo.is_initialized(),
                "branch_status": self.state_checker.check_branch_cleanliness(),
                "staged_files": [],
                "unstaged_files": [],
                "untracked_files": [],
                "current_commit": None,
                "commit_count": 0,
                "safe_for_operations": False,
            }
            
            if status["repository_initialized"]:
                try:
                    status["staged_files"] = self.git_repo.get_staged_files()
                except Exception as e:
                    debug_logger.log("WARNING", "Could not get staged files", error=str(e))
                
                try:
                    status["unstaged_files"] = self.git_repo.get_unstaged_files()
                except Exception as e:
                    debug_logger.log("WARNING", "Could not get unstaged files", error=str(e))
                
                try:
                    status["untracked_files"] = self.git_repo.get_untracked_files()
                except Exception as e:
                    debug_logger.log("WARNING", "Could not get untracked files", error=str(e))
                
                try:
                    status["current_commit"] = self.git_repo.get_current_commit_hash()
                except Exception as e:
                    debug_logger.log("WARNING", "Could not get current commit", error=str(e))
                
                try:
                    commits = self.git_repo.get_recent_commits(1000)  # Get reasonable history
                    status["commit_count"] = len(commits)
                except Exception as e:
                    debug_logger.log("WARNING", "Could not get commit count", error=str(e))
                
                status["safe_for_operations"] = self.state_checker.is_safe_for_spec_operations()
            
            return status
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to get commit status", error=str(e))
            return {
                "repository_initialized": False,
                "error": str(e),
                "safe_for_operations": False,
            }
    
    def _validate_for_add_operation(self) -> List[str]:
        """Validate repository state for add operation."""
        return self.state_checker.validate_pre_operation_state("add")
    
    def _validate_for_commit_operation(self, allow_empty: bool) -> List[str]:
        """Validate repository state for commit operation."""
        issues = self.state_checker.validate_pre_operation_state("commit")
        
        # Check if there's anything to commit
        if not allow_empty:
            try:
                staged_files = self.git_repo.get_staged_files()
                if not staged_files:
                    issues.append("No staged files to commit")
            except Exception as e:
                issues.append(f"Could not check staged files: {e}")
        
        return issues
    
    def _format_commit_message(self, message: str) -> str:
        """Format commit message according to spec conventions."""
        # Clean up the message
        formatted = message.strip()
        
        # Ensure first line is not too long (50 chars recommended)
        lines = formatted.split('\n')
        if lines and len(lines[0]) > 72:
            debug_logger.log("WARNING", "Commit message first line is long",
                           length=len(lines[0]))
        
        return formatted
    
    def _extract_commit_hash(self, git_output: str) -> Optional[str]:
        """Extract commit hash from Git command output."""
        # Look for commit hash patterns in output
        hash_pattern = r'\[\w+\s+([a-f0-9]{7,40})\]'
        match = re.search(hash_pattern, git_output)
        if match:
            return match.group(1)
        
        # Alternative pattern
        hash_pattern2 = r'([a-f0-9]{40})'
        match2 = re.search(hash_pattern2, git_output)
        if match2:
            return match2.group(1)
        
        return None
    
    def _validate_tag_name(self, tag_name: str) -> List[str]:
        """Validate Git tag name."""
        issues = []
        
        if not tag_name or not tag_name.strip():
            issues.append("Tag name cannot be empty")
            return issues
        
        # Git tag name restrictions
        if tag_name.startswith('-'):
            issues.append("Tag name cannot start with dash")
        
        if '..' in tag_name:
            issues.append("Tag name cannot contain '..'")
        
        if tag_name.endswith('.lock'):
            issues.append("Tag name cannot end with '.lock'")
        
        # Check for invalid characters
        invalid_chars = r'[\s~^:?*\[\\\x00-\x1f\x7f]'
        if re.search(invalid_chars, tag_name):
            issues.append("Tag name contains invalid characters")
        
        return issues
    
    def _tag_exists(self, tag_name: str) -> bool:
        """Check if a tag already exists."""
        try:
            result = self.git_repo.run_git_command(["tag", "-l", tag_name])
            return bool(result.stdout and result.stdout.strip())
        except Exception:
            return False
    
    def _commit_exists(self, commit_hash: str) -> bool:
        """Check if a commit exists."""
        try:
            self.git_repo.run_git_command(["cat-file", "-e", commit_hash])
            return True
        except Exception:
            return False
    
    def get_recent_operations(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent Git operations for audit/debugging.
        
        Args:
            count: Number of recent operations to retrieve
            
        Returns:
            List of operation dictionaries
        """
        try:
            commits = self.git_repo.get_recent_commits(count)
            operations = []
            
            for commit in commits:
                operations.append({
                    "type": "commit",
                    "hash": commit.get("hash"),
                    "message": commit.get("subject"),  # Updated to match actual field name
                    "author": commit.get("author"),
                    "date": commit.get("date"),
                    "files_changed": [],  # Would need additional git command to get this
                })
            
            return operations
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to get recent operations", error=str(e))
            return []
    
    def create_operation_summary(self, operation_type: str, result: Dict[str, Any]) -> str:
        """Create a human-readable summary of an operation.
        
        Args:
            operation_type: Type of operation (add, commit, tag, rollback)
            result: Operation result dictionary
            
        Returns:
            Human-readable summary string
        """
        if operation_type == "add":
            if result["success"]:
                return f"Successfully added {len(result['added'])} files to staging"
            else:
                return f"Add failed: {len(result['errors'])} errors"
        
        elif operation_type == "commit":
            if result["success"]:
                hash_short = result["commit_hash"][:8] if result["commit_hash"] else "unknown"
                return f"Committed {len(result['files_committed'])} files [{hash_short}]"
            else:
                return f"Commit failed: {len(result['errors'])} errors"
        
        elif operation_type == "tag":
            if result["success"]:
                return f"Created tag '{result['tag_name']}' at {result['commit_hash']}"
            else:
                return f"Tag creation failed: {result['errors'][0] if result['errors'] else 'unknown error'}"
        
        elif operation_type == "rollback":
            if result["success"]:
                backup_info = f" (backup: {result['backup_tag']})" if result.get('backup_tag') else ""
                return f"Rolled back to {result['target_commit'][:8]}{backup_info}"
            else:
                return f"Rollback failed: {result['errors'][0] if result['errors'] else 'unknown error'}"
        
        else:
            return f"{operation_type}: {'success' if result.get('success') else 'failed'}"