import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

if sys.version_info >= (3, 9):
    from subprocess import CompletedProcess
else:
    # For Python 3.8, import without subscripting support
    CompletedProcess = subprocess.CompletedProcess

from ..exceptions import SpecGitError
from ..logging.debug import debug_logger


class GitOperations:
    """Handles low-level Git command execution with spec environment configuration."""

    def __init__(self, spec_dir: Path, specs_dir: Path, index_file: Path):
        self.spec_dir = spec_dir
        self.specs_dir = specs_dir
        self.index_file = index_file

        debug_logger.log(
            "INFO",
            "GitOperations initialized",
            spec_dir=str(spec_dir),
            specs_dir=str(specs_dir),
            index_file=str(index_file),
        )

    def run_git_command(
        self, args: List[str], capture_output: bool = True
    ) -> "CompletedProcess[str]":
        """Execute Git command with spec environment configuration.

        Args:
            args: Git command arguments (without 'git' prefix)
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess instance

        Raises:
            SpecGitError: If Git command fails
        """
        env = self._prepare_git_environment()
        cmd = self._prepare_git_command(args)

        debug_logger.log(
            "INFO",
            "Executing Git command",
            command=" ".join(cmd),
            git_dir=str(self.spec_dir),
            work_tree=str(self.specs_dir),
        )

        try:
            with debug_logger.timer(f"git_{args[0]}"):
                result = subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    capture_output=capture_output,
                    text=True,
                    cwd=str(self.specs_dir.parent),  # Run from project root
                )

            debug_logger.log(
                "INFO",
                "Git command completed successfully",
                command=args[0],
                return_code=result.returncode,
            )

            return result

        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(cmd)}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"

            debug_logger.log(
                "ERROR",
                "Git command failed",
                command=" ".join(cmd),
                return_code=e.returncode,
                error=error_msg,
            )

            raise SpecGitError(error_msg) from e

        except FileNotFoundError as e:
            error_msg = "Git not found. Please ensure Git is installed and in PATH."
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error running Git command: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e

    def _prepare_git_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Git command.

        Returns:
            Environment dictionary with Git configuration
        """
        env = os.environ.copy()

        # Set spec-specific Git environment
        git_env = {
            "GIT_DIR": str(self.spec_dir),
            "GIT_WORK_TREE": str(self.specs_dir),
            "GIT_INDEX_FILE": str(self.index_file),
        }

        env.update(git_env)

        debug_logger.log("DEBUG", "Git environment prepared", **git_env)

        return env

    def _prepare_git_command(self, args: List[str]) -> List[str]:
        """Prepare Git command with required configuration flags.

        Args:
            args: Git command arguments

        Returns:
            Complete command list
        """
        cmd = [
            "git",
            # Disable global excludes file to prevent interference
            "-c",
            "core.excludesFile=",
            # Ensure case sensitivity for cross-platform compatibility
            "-c",
            "core.ignoreCase=false",
        ]

        # Add the actual command arguments
        cmd.extend(args)

        debug_logger.log(
            "DEBUG", "Git command prepared", original_args=args, full_command=cmd
        )

        return cmd

    def initialize_repository(self) -> None:
        """Initialize bare Git repository for spec.

        Raises:
            SpecGitError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing bare Git repository")

        try:
            # Ensure spec directory exists
            self.spec_dir.mkdir(parents=True, exist_ok=True)

            # Initialize bare repository
            init_cmd = ["git", "init", "--bare", str(self.spec_dir)]

            result = subprocess.run(
                init_cmd, check=True, capture_output=True, text=True
            )

            debug_logger.log(
                "INFO",
                "Bare Git repository initialized",
                spec_dir=str(self.spec_dir),
                stdout=result.stdout,
            )

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to initialize Git repository: {e}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error initializing repository: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e

    def check_git_available(self) -> bool:
        """Check if Git is available in the system.

        Returns:
            True if Git is available
        """
        try:
            result = subprocess.run(
                ["git", "--version"], check=True, capture_output=True, text=True
            )

            debug_logger.log(
                "DEBUG", "Git availability check passed", version=result.stdout.strip()
            )
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            debug_logger.log("WARNING", "Git is not available")
            return False

    def get_git_version(self) -> Optional[str]:
        """Get Git version string.

        Returns:
            Git version string or None if Git is not available
        """
        try:
            result = subprocess.run(
                ["git", "--version"], check=True, capture_output=True, text=True
            )

            version = result.stdout.strip()
            debug_logger.log("DEBUG", "Git version obtained", version=version)
            return version

        except (subprocess.CalledProcessError, FileNotFoundError):
            debug_logger.log("WARNING", "Could not get Git version")
            return None
