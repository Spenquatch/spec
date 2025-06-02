import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..config.settings import SpecSettings, get_settings
from ..logging.debug import debug_logger
from .operations import GitOperations
from .path_converter import GitPathConverter


class GitRepository(ABC):
    """Abstract interface for Git repository operations."""

    @abstractmethod
    def add(self, paths: List[str]) -> None:
        """Add files to Git index.

        Args:
            paths: List of file paths to add

        Raises:
            SpecGitError: If add operation fails
        """
        pass

    @abstractmethod
    def commit(self, message: str) -> None:
        """Create a commit with the given message.

        Args:
            message: Commit message

        Raises:
            SpecGitError: If commit operation fails
        """
        pass

    @abstractmethod
    def status(self) -> None:
        """Show repository status.

        Raises:
            SpecGitError: If status operation fails
        """
        pass

    @abstractmethod
    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show commit log.

        Args:
            paths: Optional list of paths to show log for

        Raises:
            SpecGitError: If log operation fails
        """
        pass

    @abstractmethod
    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show differences.

        Args:
            paths: Optional list of paths to show diff for

        Raises:
            SpecGitError: If diff operation fails
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if repository is initialized.

        Returns:
            True if repository is initialized
        """
        pass


class SpecGitRepository(GitRepository):
    """Git repository implementation for spec operations with isolated repository."""

    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.operations = GitOperations(
            spec_dir=self.settings.spec_dir,
            specs_dir=self.settings.specs_dir,
            index_file=self.settings.index_file,
        )
        self.path_converter = GitPathConverter(self.settings.specs_dir)

        debug_logger.log(
            "INFO",
            "SpecGitRepository initialized",
            spec_dir=str(self.settings.spec_dir),
            specs_dir=str(self.settings.specs_dir),
        )

    def add(self, paths: List[str]) -> None:
        """Add files to spec Git index.

        Args:
            paths: List of file paths to add (will be converted to Git work tree context)
        """
        debug_logger.log(
            "INFO", "Adding files to spec repository", path_count=len(paths)
        )

        # Convert paths to Git work tree context
        converted_paths = []
        for path in paths:
            converted_path = self.path_converter.convert_to_git_path(path)
            converted_paths.append(converted_path)
            debug_logger.log(
                "DEBUG",
                "Path conversion for add",
                original=path,
                converted=converted_path,
            )

        # Add files with force flag to bypass ignore rules
        git_args = ["add", "-f"] + converted_paths
        self.operations.run_git_command(git_args)

        debug_logger.log(
            "INFO",
            "Files added to spec repository successfully",
            files_added=len(converted_paths),
        )

    def commit(self, message: str) -> None:
        """Create commit in spec repository.

        Args:
            message: Commit message
        """
        debug_logger.log(
            "INFO",
            "Creating commit in spec repository",
            commit_message=message[:50] + "..." if len(message) > 50 else message,
        )

        git_args = ["commit", "-m", message]
        self.operations.run_git_command(git_args)

        debug_logger.log("INFO", "Commit created successfully")

    def status(self) -> None:
        """Show spec repository status."""
        debug_logger.log("INFO", "Showing spec repository status")

        git_args = ["status"]
        self.operations.run_git_command(git_args)

    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository log.

        Args:
            paths: Optional list of paths to show log for
        """
        debug_logger.log("INFO", "Showing spec repository log", path_filter=bool(paths))

        git_args = ["log", "--oneline", "--graph"]

        if paths:
            # Convert paths to Git work tree context
            converted_paths = [
                self.path_converter.convert_to_git_path(path) for path in paths
            ]
            git_args.extend(["--"] + converted_paths)
            debug_logger.log(
                "DEBUG",
                "Log with path filter",
                original_paths=paths,
                converted_paths=converted_paths,
            )

        self.operations.run_git_command(git_args)

    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository diff.

        Args:
            paths: Optional list of paths to show diff for
        """
        debug_logger.log(
            "INFO", "Showing spec repository diff", path_filter=bool(paths)
        )

        git_args = ["diff"]

        if paths:
            # Convert paths to Git work tree context
            converted_paths = [
                self.path_converter.convert_to_git_path(path) for path in paths
            ]
            git_args.extend(["--"] + converted_paths)
            debug_logger.log(
                "DEBUG",
                "Diff with path filter",
                original_paths=paths,
                converted_paths=converted_paths,
            )

        self.operations.run_git_command(git_args)

    def is_initialized(self) -> bool:
        """Check if spec repository is initialized.

        Returns:
            True if .spec directory exists and is a valid Git repository
        """
        if not self.settings.spec_dir.exists():
            debug_logger.log("DEBUG", "Spec directory does not exist")
            return False

        if not self.settings.spec_dir.is_dir():
            debug_logger.log("DEBUG", "Spec directory is not a directory")
            return False

        # Check if it's a valid Git repository by looking for Git objects
        git_objects_dir = self.settings.spec_dir / "objects"
        is_initialized = git_objects_dir.exists() and git_objects_dir.is_dir()

        debug_logger.log(
            "DEBUG",
            "Spec repository initialization check",
            is_initialized=is_initialized,
        )

        return is_initialized

    def initialize_repository(self) -> None:
        """Initialize the spec repository.

        Raises:
            SpecGitError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing spec repository")

        if self.is_initialized():
            debug_logger.log("INFO", "Spec repository already initialized")
            return

        # Create .spec directory if it doesn't exist
        self.settings.spec_dir.mkdir(parents=True, exist_ok=True)

        # Create .specs directory if it doesn't exist
        self.settings.specs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize bare Git repository
        self.operations.initialize_repository()

        debug_logger.log("INFO", "Spec repository initialized successfully")

    def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the spec repository.

        Returns:
            Dictionary with repository information
        """
        info = {
            "is_initialized": self.is_initialized(),
            "spec_dir": str(self.settings.spec_dir),
            "specs_dir": str(self.settings.specs_dir),
            "index_file": str(self.settings.index_file),
        }

        if self.is_initialized():
            try:
                # Try to get additional repository information
                info.update(
                    {
                        "spec_dir_exists": self.settings.spec_dir.exists(),
                        "specs_dir_exists": self.settings.specs_dir.exists(),
                        "index_file_exists": self.settings.index_file.exists(),
                    }
                )
            except Exception as e:
                info["error"] = str(e)

        return info

    def get_current_branch(self) -> str:
        """Get the current branch name.
        
        Returns:
            Current branch name
            
        Raises:
            SpecGitError: If unable to determine current branch
        """
        debug_logger.log("DEBUG", "Getting current branch")
        
        try:
            # Use symbolic-ref to get current branch
            result = self.operations.run_git_command(["symbolic-ref", "--short", "HEAD"])
            branch = result.stdout.strip() if result.stdout else "HEAD"
            
            debug_logger.log("DEBUG", "Current branch determined", branch=branch)
            return branch
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not determine current branch", error=str(e))
            return "HEAD"  # Fallback for detached HEAD state

    def has_uncommitted_changes(self) -> bool:
        """Check if repository has uncommitted changes.
        
        Returns:
            True if there are uncommitted changes
        """
        try:
            # Use diff-index to check for changes
            result = self.operations.run_git_command(["diff-index", "--quiet", "HEAD", "--"])
            return False  # No changes if command succeeds
        except Exception:
            return True  # Assume changes if command fails

    def has_untracked_files(self) -> bool:
        """Check if repository has untracked files.
        
        Returns:
            True if there are untracked files
        """
        try:
            # Use ls-files to check for untracked files
            result = self.operations.run_git_command(["ls-files", "--others", "--exclude-standard"])
            return bool(result.stdout and result.stdout.strip())
        except Exception:
            return False  # Assume no untracked files if command fails

    def has_staged_changes(self) -> bool:
        """Check if repository has staged changes.
        
        Returns:
            True if there are staged changes
        """
        try:
            # Use diff-index to check for staged changes
            result = self.operations.run_git_command(["diff-index", "--quiet", "--cached", "HEAD", "--"])
            return False  # No staged changes if command succeeds
        except Exception:
            return True  # Assume staged changes if command fails

    def get_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent commits from the repository.
        
        Args:
            count: Number of recent commits to retrieve
            
        Returns:
            List of commit information dictionaries
        """
        debug_logger.log("DEBUG", "Getting recent commits", count=count)
        
        try:
            # Use log with format to get structured commit data
            result = self.operations.run_git_command([
                "log", 
                f"--max-count={count}",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso"
            ])
            
            commits = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "subject": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                        })
            
            debug_logger.log("DEBUG", "Retrieved recent commits", count=len(commits))
            return commits
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not get recent commits", error=str(e))
            return []

    def add_files(self, files: List[str]) -> None:
        """Add specific files to the Git index.
        
        Args:
            files: List of file paths to add (relative to .specs/)
        """
        debug_logger.log("INFO", "Adding specific files", files=files)
        
        # Convert to Git work tree context and add
        converted_paths = [self.path_converter.convert_to_git_path(f) for f in files]
        git_args = ["add", "-f"] + converted_paths
        self.operations.run_git_command(git_args)
        
        debug_logger.log("INFO", "Files added successfully", count=len(files))

    def commit(self, message: str) -> None:
        """Create a commit and return the commit hash.
        
        Args:
            message: Commit message
            
        Returns:
            Commit hash of the created commit
        """
        debug_logger.log("INFO", "Creating commit",
                        commit_message=message[:50] + "..." if len(message) > 50 else message)
        
        git_args = ["commit", "-m", message]
        self.operations.run_git_command(git_args)
        
        # Get the commit hash of the just-created commit
        try:
            result = self.operations.run_git_command(["rev-parse", "HEAD"])
            commit_hash = result.stdout.strip() if result.stdout else "unknown"
        except Exception:
            commit_hash = "unknown"
        
        debug_logger.log("INFO", "Commit created successfully")

    def initialize(self) -> None:
        """Initialize the spec repository (wrapper for initialize_repository)."""
        self.initialize_repository()

    def run_git_command(self, args: List[str]):
        """Run a Git command (exposed for configuration purposes).
        
        Args:
            args: Git command arguments
            
        Returns:
            CompletedProcess result
        """
        return self.operations.run_git_command(args)

    def get_staged_files(self) -> List[str]:
        """Get list of staged files.
        
        Returns:
            List of staged file paths
        """
        try:
            result = self.operations.run_git_command(["diff", "--cached", "--name-only"])
            if result.stdout:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return []
        except Exception:
            return []

    def get_unstaged_files(self) -> List[str]:
        """Get list of unstaged files.
        
        Returns:
            List of unstaged file paths
        """
        try:
            result = self.operations.run_git_command(["diff", "--name-only"])
            if result.stdout:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return []
        except Exception:
            return []

    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files.
        
        Returns:
            List of untracked file paths
        """
        try:
            result = self.operations.run_git_command(["ls-files", "--others", "--exclude-standard"])
            if result.stdout:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return []
        except Exception:
            return []

    def get_current_commit_hash(self) -> Optional[str]:
        """Get current commit hash.
        
        Returns:
            Current commit hash or None if no commits
        """
        try:
            result = self.operations.run_git_command(["rev-parse", "HEAD"])
            return result.stdout.strip() if result.stdout else None
        except Exception:
            return None

    def get_parent_commit_hash(self, commit_hash: str) -> Optional[str]:
        """Get parent commit hash.
        
        Args:
            commit_hash: Hash of commit to get parent for
            
        Returns:
            Parent commit hash or None if no parent
        """
        try:
            result = self.operations.run_git_command(["rev-parse", f"{commit_hash}^"])
            return result.stdout.strip() if result.stdout else None
        except Exception:
            return None
