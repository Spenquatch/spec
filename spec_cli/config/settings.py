"""Configuration settings and management for spec CLI.

Provides SpecSettings dataclass for application settings and Rich console
instances with theming.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from rich.theme import Theme

from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger
from ..utils.path_utils import normalize_path

# Rich theme for consistent styling throughout the application
SPEC_THEME = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "warning": "bold yellow",
        "info": "bold blue",
        "debug": "dim white",
        "path": "bold cyan",
        "count": "bold white",
    }
)


@dataclass
class SpecSettings:
    """Global settings for spec operations with Rich terminal styling."""

    # Directory paths
    root_path: Path = field(default_factory=lambda: Path.cwd())

    # Computed paths (set in __post_init__)
    spec_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)
    index_file: Path = field(init=False)
    ignore_file: Path = field(init=False)
    template_file: Path = field(init=False)
    gitignore_file: Path = field(init=False)

    # Debug settings
    debug_enabled: bool = field(init=False)
    debug_level: str = field(init=False)
    debug_timing: bool = field(init=False)

    # Terminal styling settings
    use_color: bool = field(init=False)
    console_width: int | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialize computed paths and environment settings."""
        # Normalize root path and compute directory paths
        # Use resolve_symlinks=False to preserve original path structure
        self.root_path = normalize_path(self.root_path, resolve_symlinks=False)
        self.spec_dir = self.root_path / ".spec"
        self.specs_dir = self.root_path / ".specs"
        self.index_file = self.root_path / ".spec-index"
        self.ignore_file = self.root_path / ".specignore"
        self.template_file = self.root_path / ".spectemplate"
        self.gitignore_file = self.root_path / ".gitignore"

        # Environment-based settings
        self.debug_enabled = self._get_bool_env("SPEC_DEBUG", False)
        self.debug_level = os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
        self.debug_timing = self._get_bool_env("SPEC_DEBUG_TIMING", False)

        # Terminal settings
        self.use_color = self._get_bool_env("SPEC_USE_COLOR", True)
        width_str = os.environ.get("SPEC_CONSOLE_WIDTH")
        if width_str:
            try:
                self.console_width = int(width_str)
                if self.console_width < 40:
                    self.console_width = 40
            except ValueError:
                debug_logger.log(
                    "WARNING", "Invalid SPEC_CONSOLE_WIDTH value", value=width_str
                )

        debug_logger.log(
            "INFO",
            "Settings initialized",
            root_path=str(self.root_path),
            debug_enabled=self.debug_enabled,
            use_color=self.use_color,
        )

    def _get_bool_env(self, var_name: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.environ.get(var_name, "").lower()
        if value in ["1", "true", "yes"]:
            return True
        elif value in ["0", "false", "no"]:
            return False
        return default

    def is_initialized(self) -> bool:
        """Check if spec is initialized in the directory."""
        return (
            self.spec_dir.exists()
            and self.spec_dir.is_dir()
            and self.specs_dir.exists()
            and self.specs_dir.is_dir()
        )

    def validate_permissions(self) -> None:
        """Validate required permissions for spec operations."""
        if self.is_initialized():
            if not os.access(self.spec_dir, os.W_OK):
                raise SpecConfigurationError(
                    f"No write permission for {self.spec_dir}",
                    {"directory": str(self.spec_dir), "permission": "write"},
                )
            if not os.access(self.specs_dir, os.W_OK):
                raise SpecConfigurationError(
                    f"No write permission for {self.specs_dir}",
                    {"directory": str(self.specs_dir), "permission": "write"},
                )
