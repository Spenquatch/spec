"""Theme management for the spec CLI interface.

This module provides color schemes and theming functionality for the spec CLI,
allowing customization of the visual appearance and supporting different
terminal environments.
"""

from enum import Enum

from rich.theme import Theme

from ..config.settings import SpecSettings, get_settings
from ..logging.debug import debug_logger
from ..utils.singleton import reset_singleton, singleton_decorator


class ColorScheme(Enum):
    """Available color schemes for the spec CLI."""

    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    MINIMAL = "minimal"


class SpecTheme:
    """Manages theming and color schemes for the spec CLI interface."""

    def __init__(self, color_scheme: ColorScheme = ColorScheme.DEFAULT):
        """Initialize the SpecTheme.

        Args:
            color_scheme: Color scheme to use for the theme
        """
        self.color_scheme = color_scheme
        self._theme: Theme | None = None
        self._load_theme()

        debug_logger.log(
            "INFO", "SpecTheme initialized", color_scheme=color_scheme.value
        )

    def _load_theme(self) -> None:
        """Load the Rich theme based on color scheme."""
        theme_styles = self._get_theme_styles()
        self._theme = Theme(theme_styles)

        debug_logger.log("DEBUG", "Theme loaded", style_count=len(theme_styles))

    def _get_theme_styles(self) -> dict[str, str]:
        """Get theme styles based on current color scheme."""
        base_styles = {
            # Core status colors
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
            "info": "bold blue",
            "debug": "dim cyan",
            # File and path styling
            "path": "bold cyan",
            "file": "cyan",
            "directory": "bold blue",
            "spec_file": "bold magenta",
            # Git and repository styling
            "git_branch": "bold green",
            "git_commit": "yellow",
            "git_modified": "bold yellow",
            "git_staged": "bold green",
            # Operation status
            "operation_start": "bold blue",
            "operation_complete": "bold green",
            "operation_failed": "bold red",
            "operation_skipped": "dim yellow",
            # Content types
            "code": "bright_black on white",
            "command": "bold white on black",
            "config": "bold cyan",
            "template": "bold magenta",
            # UI elements
            "border": "bright_black",
            "title": "bold white",
            "subtitle": "bold bright_black",
            "label": "bold",
            "value": "bright_white",
            "muted": "dim bright_black",
            # Progress and status indicators
            "progress_bar": "green",
            "progress_complete": "bold green",
            "progress_pending": "yellow",
            "spinner": "cyan",
        }

        # Apply color scheme modifications
        if self.color_scheme == ColorScheme.DARK:
            base_styles.update(
                {
                    "title": "bold bright_white",
                    "value": "white",
                    "border": "bright_black",
                    "muted": "dim white",
                }
            )
        elif self.color_scheme == ColorScheme.LIGHT:
            base_styles.update(
                {
                    "title": "bold black",
                    "value": "black",
                    "border": "black",
                    "muted": "dim black",
                    "code": "black on bright_white",
                }
            )
        elif self.color_scheme == ColorScheme.MINIMAL:
            # Minimal color scheme - mostly monochrome
            base_styles.update(
                {
                    "success": "bold white",
                    "warning": "bold white",
                    "error": "bold white",
                    "info": "bold white",
                    "path": "white",
                    "file": "white",
                    "directory": "bold white",
                    "progress_bar": "white",
                    "spinner": "white",
                }
            )

        return base_styles

    @property
    def theme(self) -> Theme:
        """Get the Rich theme object."""
        if self._theme is None:
            raise RuntimeError("Theme not initialized")
        return self._theme

    def get_style(self, style_name: str) -> str:
        """Get a specific style by name.

        Args:
            style_name: Name of the style to retrieve

        Returns:
            Style string, or empty string if not found
        """
        if not self._theme or style_name not in self._theme.styles:
            debug_logger.log("WARNING", "Style not found", style_name=style_name)
            return ""

        return str(self._theme.styles[style_name])

    def update_color_scheme(self, color_scheme: ColorScheme) -> None:
        """Update the color scheme and reload theme.

        Args:
            color_scheme: New color scheme to use
        """
        self.color_scheme = color_scheme
        self._load_theme()

        debug_logger.log("INFO", "Color scheme updated", new_scheme=color_scheme.value)

    def get_emoji_replacements(self) -> dict[str, str]:
        """Get emoji to styled text replacements.

        Returns:
            Dictionary mapping emoji to styled text
        """
        return {
            # Status emojis
            "✅": "[success]✓[/success]",
            "❌": "[error]✗[/error]",
            "⚠️": "[warning]⚠[/warning]",
            "ℹ️": "[info]i[/info]",
            "🔍": "[info]?[/info]",
            # File and folder emojis
            "📁": "[directory]📁[/directory]",
            "📄": "[file]📄[/file]",
            "📝": "[spec_file]📝[/spec_file]",
            # Git emojis
            "🌿": "[git_branch]⎇[/git_branch]",
            "💾": "[git_commit]○[/git_commit]",
            "📊": "[git_modified]±[/git_modified]",
            "➕": "[git_staged]+[/git_staged]",
            # Process emojis
            "🚀": "[operation_start]→[/operation_start]",
            "🎉": "[operation_complete]✓[/operation_complete]",
            "💥": "[operation_failed]✗[/operation_failed]",
            "⏭️": "[operation_skipped]⤸[/operation_skipped]",
            # Progress emojis
            "⏳": "[spinner]⧗[/spinner]",
            "🔄": "[spinner]↻[/spinner]",
            "✨": "[progress_complete]★[/progress_complete]",
        }

    @classmethod
    def from_settings(cls, settings: SpecSettings | None = None) -> "SpecTheme":
        """Create theme from settings configuration.

        Args:
            settings: Optional settings object

        Returns:
            SpecTheme instance configured from settings
        """
        settings = settings or get_settings()

        # Try to get color scheme from settings
        color_scheme_name = getattr(settings, "ui_color_scheme", "default")

        try:
            color_scheme = ColorScheme(color_scheme_name.lower())
        except ValueError:
            debug_logger.log(
                "WARNING", "Invalid color scheme in settings", scheme=color_scheme_name
            )
            color_scheme = ColorScheme.DEFAULT

        return cls(color_scheme)


@singleton_decorator
class ThemeManager:
    """Manages global theme instances."""

    def __init__(self) -> None:
        """Initialize theme manager."""
        self._current_theme: SpecTheme | None = None

    def get_current_theme(self) -> SpecTheme:
        """Get the current global theme instance.

        Returns:
            Current SpecTheme instance
        """
        if self._current_theme is None:
            self._current_theme = SpecTheme.from_settings()
            debug_logger.log("INFO", "Global theme initialized")

        return self._current_theme

    def set_current_theme(self, theme: SpecTheme) -> None:
        """Set the current global theme.

        Args:
            theme: SpecTheme instance to set as current
        """
        self._current_theme = theme

        debug_logger.log(
            "INFO", "Global theme updated", color_scheme=theme.color_scheme.value
        )

    def reset_theme(self) -> None:
        """Reset the global theme to default."""
        self._current_theme = None
        debug_logger.log("INFO", "Global theme reset")


# Convenience functions
def get_current_theme() -> SpecTheme:
    """Get the current global theme instance."""
    return ThemeManager().get_current_theme()


def set_current_theme(theme: SpecTheme) -> None:
    """Set the current global theme."""
    ThemeManager().set_current_theme(theme)


def reset_theme() -> None:
    """Reset the global theme to default."""
    manager = ThemeManager()
    manager.reset_theme()
    reset_singleton(ThemeManager)
