import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecFileError, SpecPermissionError, SpecValidationError
from ..logging.debug import debug_logger
from ..utils.path_utils import ensure_directory, ensure_path_permissions
from .ignore_patterns import IgnorePatternMatcher
from .path_resolver import PathResolver


class DirectoryManager:
    """Manages spec directory creation, structure, and safety operations."""

    def __init__(self, settings: SpecSettings | None = None):
        self.settings = settings or get_settings()
        self.path_resolver = PathResolver(self.settings)
        self.ignore_matcher = IgnorePatternMatcher(self.settings)

    def ensure_specs_directory(self) -> None:
        """Ensure .specs directory exists and is properly configured."""
        specs_dir = self.settings.specs_dir

        debug_logger.log(
            "INFO", "Ensuring .specs directory exists", specs_dir=str(specs_dir)
        )

        try:
            # Use centralized directory creation utility
            ensure_directory(specs_dir)
            debug_logger.log(
                "INFO", "Ensured .specs directory exists", specs_dir=str(specs_dir)
            )

            # Verify permissions using centralized utility
            try:
                ensure_path_permissions(specs_dir, require_write=True)
            except SpecValidationError as e:
                # Convert validation error to permission error for backward compatibility
                if "permission" in str(e).lower():
                    raise SpecPermissionError(
                        str(e), {"directory": str(specs_dir), "permission": "write"}
                    ) from e
                raise

            # Create basic structure
            self._create_basic_structure(specs_dir)

        except OSError as e:
            raise SpecFileError(
                f"Failed to create .specs directory: {e}",
                {"specs_dir": str(specs_dir), "os_error": str(e)},
            ) from e

    def _create_basic_structure(self, specs_dir: Path) -> None:
        """Create basic directory structure in .specs."""
        # Create .specignore if it doesn't exist in .specs
        specignore_in_specs = specs_dir / ".specignore"
        if not specignore_in_specs.exists():
            default_content = """# Spec-specific ignores
*.tmp
*.backup
.DS_Store
"""
            try:
                specignore_in_specs.write_text(default_content, encoding="utf-8")
                debug_logger.log(
                    "INFO",
                    "Created default .specignore in .specs",
                    file_path=str(specignore_in_specs),
                )
            except OSError as e:
                debug_logger.log(
                    "WARNING",
                    "Could not create .specignore in .specs",
                    error=str(e),
                )

    def create_spec_directory(self, file_path: Path) -> Path:
        """Create directory structure for a file's spec documentation.

        Args:
            file_path: Path to the source file (relative to project root)

        Returns:
            Path to the created spec directory
        """
        # Resolve to spec directory path
        spec_dir = self.path_resolver.convert_to_spec_directory_path(file_path)

        debug_logger.log(
            "INFO",
            "Creating spec directory",
            file_path=str(file_path),
            spec_dir=str(spec_dir),
        )

        try:
            # Use centralized directory creation utility
            created_dir = ensure_directory(spec_dir)

            # Verify permissions using centralized utility
            try:
                ensure_path_permissions(created_dir, require_write=True)
            except SpecValidationError as e:
                # Convert validation error to permission error for backward compatibility
                if "permission" in str(e).lower():
                    raise SpecPermissionError(
                        str(e), {"directory": str(created_dir), "permission": "write"}
                    ) from e
                raise

            debug_logger.log(
                "INFO", "Successfully created spec directory", spec_dir=str(spec_dir)
            )

            return created_dir

        except OSError as e:
            raise SpecFileError(
                f"Failed to create spec directory {spec_dir}: {e}",
                {
                    "spec_dir": str(spec_dir),
                    "file_path": str(file_path),
                    "os_error": str(e),
                },
            ) from e

    def check_existing_specs(self, spec_dir: Path) -> dict[str, bool]:
        """Check which spec files already exist in the directory.

        Args:
            spec_dir: Directory to check

        Returns:
            Dictionary indicating which files exist
        """
        index_file = spec_dir / "index.md"
        history_file = spec_dir / "history.md"

        existing = {
            "index.md": index_file.exists(),
            "history.md": history_file.exists(),
            "directory": spec_dir.exists(),
        }

        debug_logger.log(
            "DEBUG",
            "Checked existing spec files",
            spec_dir=str(spec_dir),
            existing=existing,
        )

        return existing

    def backup_existing_files(
        self, spec_dir: Path, backup_suffix: str | None = None
    ) -> list[Path]:
        """Create backups of existing spec files.

        Args:
            spec_dir: Directory containing files to backup
            backup_suffix: Suffix for backup files (default: timestamp)

        Returns:
            List of created backup file paths
        """
        if backup_suffix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_suffix = f".backup_{timestamp}"

        backup_files: list[Path] = []

        if not spec_dir.exists():
            return backup_files

        try:
            for file_path in spec_dir.glob("*.md"):
                backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
                shutil.copy2(file_path, backup_path)
                backup_files.append(backup_path)

                debug_logger.log(
                    "INFO",
                    "Created backup file",
                    original=str(file_path),
                    backup=str(backup_path),
                )

            return backup_files

        except OSError as e:
            raise SpecFileError(
                f"Failed to create backup files in {spec_dir}: {e}",
                {"spec_dir": str(spec_dir), "os_error": str(e)},
            ) from e

    def remove_spec_directory(
        self, spec_dir: Path, backup_first: bool = True
    ) -> list[Path] | None:
        """Remove a spec directory and optionally create backups.

        Args:
            spec_dir: Directory to remove
            backup_first: Whether to create backups before removal

        Returns:
            List of backup files if backup_first is True, None otherwise
        """
        backup_files = None

        if not spec_dir.exists():
            debug_logger.log(
                "INFO",
                "Spec directory does not exist, nothing to remove",
                spec_dir=str(spec_dir),
            )
            return backup_files

        try:
            if backup_first:
                backup_files = self.backup_existing_files(spec_dir)

            shutil.rmtree(spec_dir)

            debug_logger.log(
                "INFO",
                "Removed spec directory",
                spec_dir=str(spec_dir),
                backup_created=backup_first,
            )

            return backup_files

        except OSError as e:
            raise SpecFileError(
                f"Failed to remove spec directory {spec_dir}: {e}",
                {"spec_dir": str(spec_dir), "os_error": str(e)},
            ) from e

    def setup_ignore_files(self) -> None:
        """Setup ignore files for the project."""
        # Ensure .specignore exists with sensible defaults
        ignore_file = self.settings.ignore_file

        if not ignore_file.exists():
            default_patterns = """# Generated files
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Testing and coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Documentation builds
docs/_build/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
            try:
                ignore_file.write_text(default_patterns, encoding="utf-8")
                debug_logger.log(
                    "INFO",
                    "Created default .specignore file",
                    ignore_file=str(ignore_file),
                )
            except OSError as e:
                debug_logger.log(
                    "WARNING",
                    "Could not create .specignore file",
                    ignore_file=str(ignore_file),
                    error=str(e),
                )

    def update_main_gitignore(self) -> None:
        """Update main .gitignore to include spec files."""
        gitignore_file = self.settings.gitignore_file

        spec_patterns = [
            "# Spec CLI files",
            ".spec/",
            ".spec-index",
        ]

        try:
            # Read existing content
            existing_content = ""
            if gitignore_file.exists():
                existing_content = gitignore_file.read_text(encoding="utf-8")

            # Check if spec patterns are already present
            if ".spec/" in existing_content:
                debug_logger.log("INFO", ".gitignore already contains spec patterns")
                return

            # Append spec patterns
            new_content = existing_content
            if not new_content.endswith("\n") and new_content:
                new_content += "\n"
            new_content += "\n".join(spec_patterns) + "\n"

            gitignore_file.write_text(new_content, encoding="utf-8")

            debug_logger.log(
                "INFO",
                "Updated .gitignore with spec patterns",
                gitignore_file=str(gitignore_file),
            )

        except OSError as e:
            debug_logger.log(
                "WARNING",
                "Could not update .gitignore",
                gitignore_file=str(gitignore_file),
                error=str(e),
            )

    def get_directory_stats(self, directory: Path) -> dict[str, Any]:
        """Get statistics about a directory.

        Args:
            directory: Directory to analyze

        Returns:
            Dictionary with directory statistics
        """
        if not directory.exists() or not directory.is_dir():
            return {"exists": False}

        try:
            stats = {
                "exists": True,
                "total_items": 0,
                "files": 0,
                "directories": 0,
                "total_size": 0,
                "spec_files": 0,
            }

            for item in directory.rglob("*"):
                stats["total_items"] += 1

                if item.is_file():
                    stats["files"] += 1
                    try:
                        stats["total_size"] += item.stat().st_size
                        if item.suffix == ".md" and item.parent.name != directory.name:
                            stats["spec_files"] += 1
                    except OSError:
                        pass
                elif item.is_dir():
                    stats["directories"] += 1

            debug_logger.log(
                "DEBUG", "Directory statistics", directory=str(directory), stats=stats
            )

            return stats

        except OSError as e:
            debug_logger.log(
                "ERROR",
                "Could not analyze directory",
                directory=str(directory),
                error=str(e),
            )
            return {"exists": True, "error": str(e)}
