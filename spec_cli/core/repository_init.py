"""Repository initialization module for spec CLI.

This module provides the SpecRepositoryInitializer class which handles the complete
setup and initialization of spec repositories. It manages the creation of the
.spec Git repository, .specs directory structure, configuration files, and
initial repository health validation.

Key responsibilities:
- Creating isolated .spec Git repository with proper configuration
- Setting up .specs directory structure and ignore files
- Bootstrapping common directories and example templates
- Validating system requirements and repository health
- Creating initial commits and managing repository state
"""

from pathlib import Path
from typing import Any, cast

from ..config.settings import SpecSettings, get_settings
from ..file_system.directory_manager import DirectoryManager
from ..git.repository import SpecGitRepository
from ..logging.debug import debug_logger
from .repository_state import RepositoryHealth, RepositoryStateChecker


class SpecRepositoryInitializer:
    """Handles spec repository initialization and setup."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize the repository initializer with configuration and dependencies.

        Args:
            settings: Optional SpecSettings instance. If None, uses default settings
                     from get_settings()

        The initializer sets up all required components for repository operations:
        - Git repository interface for .spec operations
        - Directory manager for .specs structure
        - State checker for repository health validation
        """
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
        self.state_checker = RepositoryStateChecker(self.settings)

        debug_logger.log("INFO", "SpecRepositoryInitializer initialized")

    def initialize_repository(self, force: bool = False) -> dict[str, Any]:
        """Initialize a new spec repository with full setup.

        Args:
            force: Whether to reinitialize if repository already exists

        Returns:
            Dictionary with initialization results

        Raises:
            SpecRepositoryError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing spec repository", force=force)

        init_result: dict[str, Any] = {
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
                    if current_state["overall_health"] in [
                        RepositoryHealth.HEALTHY,
                        RepositoryHealth.WARNING,
                    ]:
                        cast(list[str], init_result["skipped"]).append(
                            "Repository already exists and is healthy"
                        )
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

                init_result["success"] = (
                    len(cast(list[str], init_result["errors"])) == 0
                )

            debug_logger.log(
                "INFO",
                "Repository initialization complete",
                success=init_result["success"],
                created=len(cast(list[str], init_result["created"])),
                errors=len(cast(list[str], init_result["errors"])),
            )

            return init_result

        except Exception as e:
            error_msg = f"Repository initialization failed: {e}"
            debug_logger.log("ERROR", error_msg)
            cast(list[str], init_result["errors"]).append(error_msg)
            init_result["success"] = False
            return init_result

    def _initialize_spec_git_repo(self, result: dict[str, Any], force: bool) -> None:
        """Initialize the .spec Git repository."""
        spec_dir = self.settings.spec_dir

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

    def _configure_git_repository(self, result: dict[str, Any]) -> None:
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

    def _initialize_specs_directory(self, result: dict[str, Any]) -> None:
        """Initialize the .specs directory structure."""
        try:
            self.directory_manager.ensure_specs_directory()
            result["created"].append(
                f"Created .specs directory: {self.settings.specs_dir}"
            )

        except Exception as e:
            result["errors"].append(f"Failed to create .specs directory: {e}")

    def _setup_ignore_files(self, result: dict[str, Any]) -> None:
        """Set up ignore files for the repository."""
        try:
            self.directory_manager.setup_ignore_files()
            result["created"].append("Created .specignore file with defaults")

        except Exception as e:
            result["warnings"].append(f"Could not setup ignore files: {e}")

    def _create_initial_commit(self, result: dict[str, Any]) -> None:
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
                _ = self.git_repo.commit("Initial spec repository setup")
                result["created"].append("Created initial commit")
            except Exception as e:
                result["warnings"].append(f"Could not create initial commit: {e}")

        except Exception as e:
            result["warnings"].append(f"Initial commit setup failed: {e}")

    def _update_main_gitignore(self, result: dict[str, Any]) -> None:
        """Update the main project .gitignore to include spec files."""
        try:
            self.directory_manager.update_main_gitignore()
            result["created"].append("Updated main .gitignore with spec patterns")

        except Exception as e:
            result["warnings"].append(f"Could not update main .gitignore: {e}")

    def _verify_initialization(self, result: dict[str, Any]) -> None:
        """Verify that initialization was successful."""
        try:
            health = self.state_checker.check_repository_health()

            if health["overall_health"] in [
                RepositoryHealth.HEALTHY,
                RepositoryHealth.WARNING,
            ]:
                result["created"].append(
                    "Repository initialization verified successfully"
                )
            else:
                result["errors"].append("Repository initialization verification failed")
                result["errors"].extend(health["issues"])

        except Exception as e:
            result["warnings"].append(f"Could not verify initialization: {e}")

    def bootstrap_repository_structure(self) -> dict[str, Any]:
        """Bootstrap additional repository structure and configuration.

        Returns:
            Dictionary with bootstrap results
        """
        debug_logger.log("INFO", "Bootstrapping repository structure")

        bootstrap_result: dict[str, Any] = {
            "success": False,
            "created": [],
            "errors": [],
            "warnings": [],
        }

        try:
            # Ensure repository is initialized
            if not self.state_checker.is_safe_for_spec_operations():
                cast(list[str], bootstrap_result["errors"]).append(
                    "Repository not initialized or not safe for operations"
                )
                return bootstrap_result

            # Create common directory structure in .specs
            self._create_common_directories(bootstrap_result)

            # Setup configuration files
            self._setup_configuration_files(bootstrap_result)

            # Create example templates if needed
            self._create_example_templates(bootstrap_result)

            bootstrap_result["success"] = (
                len(cast(list[str], bootstrap_result["errors"])) == 0
            )

            debug_logger.log(
                "INFO",
                "Repository bootstrap complete",
                success=bootstrap_result["success"],
                created=len(cast(list[str], bootstrap_result["created"])),
            )

            return bootstrap_result

        except Exception as e:
            error_msg = f"Repository bootstrap failed: {e}"
            debug_logger.log("ERROR", error_msg)
            cast(list[str], bootstrap_result["errors"]).append(error_msg)
            return bootstrap_result

    def _create_common_directories(self, result: dict[str, Any]) -> None:
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

    def _setup_configuration_files(self, result: dict[str, Any]) -> None:
        """Set up configuration files in the repository."""
        try:
            # Create .spec/config.json for repository-specific settings
            config_file = self.settings.spec_dir / "config.json"
            if not config_file.exists():
                import datetime
                import json

                config_data = {
                    "version": "1.0",
                    "created": datetime.datetime.now().isoformat(),
                    "settings": {
                        "auto_commit": False,
                        "backup_enabled": True,
                        "ai_enabled": False,
                    },
                }

                config_file.write_text(
                    json.dumps(config_data, indent=2), encoding="utf-8"
                )
                result["created"].append(f"Created config file: {config_file}")

        except Exception as e:
            result["warnings"].append(f"Could not create configuration files: {e}")

    def _create_example_templates(self, result: dict[str, Any]) -> None:
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

    def check_initialization_requirements(self) -> list[str]:
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
                    ["git", "--version"], capture_output=True, text=True, check=True
                )
                debug_logger.log(
                    "DEBUG", "Git version check", version=result.stdout.strip()
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                issues.append("Git is not installed or not available in PATH")

            # Check directory permissions
            parent_dir = self.settings.spec_dir.parent
            if not parent_dir.exists():
                issues.append(f"Parent directory does not exist: {parent_dir}")
            else:
                import os

                if not os.access(parent_dir, os.W_OK):
                    issues.append(
                        f"No write permission to parent directory: {parent_dir}"
                    )

            # Check for existing conflicting files
            if self.settings.spec_dir.exists() and not self.settings.spec_dir.is_dir():
                issues.append(
                    f".spec exists but is not a directory: {self.settings.spec_dir}"
                )

            if (
                self.settings.specs_dir.exists()
                and not self.settings.specs_dir.is_dir()
            ):
                issues.append(
                    f".specs exists but is not a directory: {self.settings.specs_dir}"
                )

        except Exception as e:
            issues.append(f"Requirement check failed: {e}")

        return issues

    def get_initialization_plan(self) -> dict[str, Any]:
        """Get a plan for what initialization would do.

        Returns:
            Dictionary describing the initialization plan
        """
        plan: dict[str, Any] = {
            "actions": [],
            "requirements": self.check_initialization_requirements(),
            "current_state": self.state_checker.get_repository_summary(),
            "estimated_time": "< 10 seconds",
        }

        current_state = self.state_checker.check_repository_health()

        if not current_state["checks"]["spec_repo_exists"]:
            cast(list[str], plan["actions"]).append(
                f"Create Git repository: {self.settings.spec_dir}"
            )
            cast(list[str], plan["actions"]).append("Configure Git repository settings")

        if not current_state["checks"]["spec_dir_exists"]:
            cast(list[str], plan["actions"]).append(
                f"Create .specs directory: {self.settings.specs_dir}"
            )

        cast(list[str], plan["actions"]).extend(
            [
                "Setup .specignore file with sensible defaults",
                "Create initial README.md in .specs",
                "Update main .gitignore to exclude spec files",
                "Create initial commit",
                "Verify repository health",
            ]
        )

        return plan
