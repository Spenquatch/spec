"""Console management for the spec CLI interface.

This module provides a wrapper around Rich Console with spec-specific configuration,
theming, and emoji handling for consistent output formatting across the CLI.
"""

from typing import Any

from rich.console import Console

from ..core.context_bridge import debug_logger, get_current_theme
from .theme import SpecTheme


class SpecConsole:
    """Wrapper around Rich Console with spec-specific configuration."""

    def __init__(
        self,
        theme: SpecTheme | None = None,
        width: int | None = None,
        force_terminal: bool | None = None,
        no_color: bool = False,
    ) -> None:
        """Initialize the spec console.

        Args:
            theme: Optional theme to use (uses global theme if None)
            width: Console width (auto-detect if None)
            force_terminal: Force terminal mode
            no_color: Disable color output
        """
        self.theme = theme or get_current_theme()
        self.no_color = no_color

        # Initialize Rich console
        self._console = Console(
            theme=self.theme.theme,
            width=width,
            force_terminal=force_terminal,
            no_color=no_color,
            highlight=False,  # Disable automatic highlighting
            markup=True,  # Enable Rich markup
            emoji=False,  # Disable emoji (we handle this manually)
            record=True,  # Enable recording for testing
        )

        debug_logger.log(
            "INFO",
            "SpecConsole initialized",
            width=self._console.width,
            color_system=self._console._color_system.name
            if self._console._color_system
            else "none",
            theme=self.theme.color_scheme.value,
        )

    @property
    def console(self) -> Console:
        """Get the underlying Rich console."""
        return self._console

    def print(self, *objects: Any, **kwargs: Any) -> None:
        """Print objects to the console with emoji replacement.

        Args:
            *objects: Objects to print
            **kwargs: Additional keyword arguments for Rich print
        """
        # Convert objects to strings and replace emojis
        processed_objects = []
        for obj in objects:
            if isinstance(obj, str):
                processed_objects.append(self._replace_emojis(obj))
            else:
                processed_objects.append(obj)

        self._console.print(*processed_objects, **kwargs)

    def print_status(self, message: str, status: str = "info", **kwargs: Any) -> None:
        """Print a status message with appropriate styling.

        Args:
            message: Message to print
            status: Status type (success, warning, error, info)
            **kwargs: Additional keyword arguments for Rich print
        """
        styled_message = f"[{status}]{message}[/{status}]"
        self.print(styled_message, **kwargs)

    def print_section(self, title: str, content: str = "", **kwargs: Any) -> None:
        """Print a section with title and optional content.

        Args:
            title: Section title
            content: Optional section content
            **kwargs: Additional keyword arguments for Rich print
        """
        self.print(f"\n[title]{title}[/title]")
        if content:
            self.print(content, **kwargs)

    def print_message(
        self, message: str, style: str | None = None, **kwargs: Any
    ) -> None:
        """Print a message with optional styling.

        Args:
            message: Message to print
            style: Optional style to apply
            **kwargs: Additional arguments for console.print
        """
        if style:
            self.print_status(message, style, **kwargs)
        else:
            self.print(message, **kwargs)

    def print_error(self, message: str, **kwargs: Any) -> None:
        """Print an error message.

        Args:
            message: Error message to print
            **kwargs: Additional arguments for console.print
        """
        self.print_status(message, "error", **kwargs)

    def print_success(self, message: str, **kwargs: Any) -> None:
        """Print a success message.

        Args:
            message: Success message to print
            **kwargs: Additional arguments for console.print
        """
        self.print_status(message, "success", **kwargs)

    def print_warning(self, message: str, **kwargs: Any) -> None:
        """Print a warning message.

        Args:
            message: Warning message to print
            **kwargs: Additional arguments for console.print
        """
        self.print_status(message, "warning", **kwargs)

    def _replace_emojis(self, text: str) -> str:
        """Replace emojis with styled text equivalents.

        Args:
            text: Text containing emojis

        Returns:
            Text with emojis replaced by styled equivalents
        """
        if self.no_color:
            # If no color, just remove emojis
            replacements = self.theme.get_emoji_replacements()
            for emoji in replacements:
                # Extract just the character part (remove Rich markup)
                replacement = replacements[emoji]
                # Simple regex to extract content between tags
                import re

                match = re.search(r"\[.*?\](.*?)\[/.*?\]", replacement)
                if match:
                    text = text.replace(emoji, match.group(1))
                else:
                    text = text.replace(emoji, "")
            return text

        # Normal emoji replacement with styling
        replacements = self.theme.get_emoji_replacements()
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)

        return text

    def get_width(self) -> int:
        """Get the console width."""
        return int(self._console.width)

    def is_terminal(self) -> bool:
        """Check if output is going to a terminal."""
        return bool(self._console.is_terminal)

    def export_text(self, clear: bool = True) -> str:
        """Export console output as plain text.

        Args:
            clear: Whether to clear the console after export

        Returns:
            Plain text representation of console output
        """
        text = str(self._console.export_text(clear=clear))
        debug_logger.log(
            "DEBUG", "Console output exported", length=len(text), cleared=clear
        )
        return text

    def export_html(self, clear: bool = True) -> str:
        """Export console output as HTML.

        Args:
            clear: Whether to clear the console after export

        Returns:
            HTML representation of console output
        """
        html = str(self._console.export_html(clear=clear))
        debug_logger.log(
            "DEBUG", "Console HTML exported", length=len(html), cleared=clear
        )
        return html

    def clear(self) -> None:
        """Clear the console."""
        self._console.clear()
        debug_logger.log("DEBUG", "Console cleared")

    def update_theme(self, theme: SpecTheme) -> None:
        """Update the console theme.

        Args:
            theme: New theme to use
        """
        self.theme = theme
        # Note: Rich Console doesn't support theme updates after creation
        # So we need to recreate the console
        old_width = self._console.width
        old_force_terminal = self._console._force_terminal

        self._console = Console(
            theme=self.theme.theme,
            width=old_width,
            force_terminal=old_force_terminal,
            no_color=self.no_color,
            highlight=False,
            markup=True,
            emoji=False,
            record=True,
        )

        debug_logger.log(
            "INFO", "Console theme updated", new_theme=theme.color_scheme.value
        )


class ConsoleManager:
    """Manages global console instances."""

    def __init__(self, settings: Any = None) -> None:
        """Initialize console manager.

        Args:
            settings: Optional settings instance for console configuration
        """
        self._spec_console: SpecConsole | None = None
        self._settings = settings

    def get_console(self) -> SpecConsole:
        """Get the global spec console instance.

        Returns:
            Global SpecConsole instance
        """
        if self._spec_console is None:
            # Check for no-color preference from settings
            no_color = False
            if self._settings:
                no_color = getattr(self._settings, "no_color", False)
            # If no settings provided, use default (no_color = False)

            self._spec_console = SpecConsole(no_color=no_color)
            debug_logger.log("INFO", "Global console initialized")

        return self._spec_console

    def set_console(self, console: SpecConsole) -> None:
        """Set the global console instance.

        Args:
            console: SpecConsole instance to set as global
        """
        self._spec_console = console
        debug_logger.log("INFO", "Global console updated")

    def reset_console(self) -> None:
        """Reset the global console to default."""
        self._spec_console = None
        debug_logger.log("INFO", "Global console reset")


# Module-level console cache for factory pattern
_console_cache: SpecConsole | None = None


# Factory functions (modernized from singleton pattern)
def create_console(
    cache: bool = True, no_color: bool | None = None, settings: Any = None
) -> SpecConsole:
    """Create console instance with optional caching.

    SINGLETON JUSTIFICATION ANALYSIS
    Date: 2025-01-08
    Factory: ConsoleManager
    Decision: CONVERT_TO_FACTORY

    EVALUATION CRITERIA:
    Resource Management: MEDIUM - manages terminal resources but not critically scarce
    Performance: LOW-MEDIUM - 39.57ms/1000 instances, not performance-critical
    Thread Safety: LOW - no inherent thread safety needs
    State Management: MEDIUM - maintains theme/settings but easily recreated

    DECISION RATIONALE:
    Insufficient justification for singleton pattern. Console creation is not expensive enough
    to warrant caching, and resource management is not critical. Factory pattern provides
    better flexibility and architectural consistency.

    Args:
        cache: Whether to cache console instance for reuse
        no_color: Override no-color setting (uses settings if None)
        settings: Optional settings instance for configuration

    Returns:
        Console instance
    """
    global _console_cache

    if cache and _console_cache is not None:
        return _console_cache

    # Determine no_color setting
    if no_color is None:
        if settings:
            no_color = getattr(settings, "no_color", False)
        else:
            # Default to False when no settings provided
            no_color = False

    console = SpecConsole(no_color=no_color)

    if cache:
        _console_cache = console

    return console


def set_console(console: SpecConsole) -> None:
    """Set the cached console instance."""
    global _console_cache
    _console_cache = console
    debug_logger.log("INFO", "Global console updated")


def reset_console() -> None:
    """Reset the cached console to default."""
    global _console_cache
    _console_cache = None
    debug_logger.log("INFO", "Global console reset")


# Convenient alias for the global console
def spec_console() -> SpecConsole:
    return create_console(cache=True)
