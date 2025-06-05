"""
Global style helpers and utilities for consistent text formatting.

Provides style functions for paths, messages, and Rich text creation.
"""

from pathlib import Path

from rich.style import Style
from rich.text import Text

from ..logging.debug import debug_logger
from .theme import get_current_theme


class SpecStyles:
    """Global style helpers and utilities for consistent text formatting."""

    @staticmethod
    def success(text: str) -> str:
        """Format text as success message.

        Args:
            text: Text to format

        Returns:
            Formatted text with success styling
        """
        return f"[success]{text}[/success]"

    @staticmethod
    def warning(text: str) -> str:
        """Format text as warning message.

        Args:
            text: Text to format

        Returns:
            Formatted text with warning styling
        """
        return f"[warning]{text}[/warning]"

    @staticmethod
    def error(text: str) -> str:
        """Format text as error message.

        Args:
            text: Text to format

        Returns:
            Formatted text with error styling
        """
        return f"[error]{text}[/error]"

    @staticmethod
    def info(text: str) -> str:
        """Format text as info message.

        Args:
            text: Text to format

        Returns:
            Formatted text with info styling
        """
        return f"[info]{text}[/info]"

    @staticmethod
    def path(path: str | Path) -> str:
        """Format path with appropriate styling.

        Args:
            path: Path to format

        Returns:
            Formatted path with path styling
        """
        return f"[path]{path}[/path]"

    @staticmethod
    def file(filename: str | Path) -> str:
        """Format filename with appropriate styling.

        Args:
            filename: Filename to format

        Returns:
            Formatted filename with file styling
        """
        return f"[file]{filename}[/file]"

    @staticmethod
    def directory(dirname: str | Path) -> str:
        """Format directory name with appropriate styling.

        Args:
            dirname: Directory name to format

        Returns:
            Formatted directory name with directory styling
        """
        return f"[directory]{dirname}[/directory]"

    @staticmethod
    def spec_file(filename: str | Path) -> str:
        """Format spec file name with appropriate styling.

        Args:
            filename: Spec filename to format

        Returns:
            Formatted spec filename with spec_file styling
        """
        return f"[spec_file]{filename}[/spec_file]"

    @staticmethod
    def code(code_text: str) -> str:
        """Format code text with appropriate styling.

        Args:
            code_text: Code to format

        Returns:
            Formatted code with code styling
        """
        return f"[code]{code_text}[/code]"

    @staticmethod
    def command(command_text: str) -> str:
        """Format command text with appropriate styling.

        Args:
            command_text: Command to format

        Returns:
            Formatted command with command styling
        """
        return f"[command]{command_text}[/command]"

    @staticmethod
    def title(text: str) -> str:
        """Format text as title.

        Args:
            text: Text to format as title

        Returns:
            Formatted title text
        """
        return f"[title]{text}[/title]"

    @staticmethod
    def subtitle(text: str) -> str:
        """Format text as subtitle.

        Args:
            text: Text to format as subtitle

        Returns:
            Formatted subtitle text
        """
        return f"[subtitle]{text}[/subtitle]"

    @staticmethod
    def label(text: str) -> str:
        """Format text as label.

        Args:
            text: Text to format as label

        Returns:
            Formatted label text
        """
        return f"[label]{text}[/label]"

    @staticmethod
    def value(text: str) -> str:
        """Format text as value.

        Args:
            text: Text to format as value

        Returns:
            Formatted value text
        """
        return f"[value]{text}[/value]"

    @staticmethod
    def muted(text: str) -> str:
        """Format text as muted/dimmed.

        Args:
            text: Text to format as muted

        Returns:
            Formatted muted text
        """
        return f"[muted]{text}[/muted]"


def style_text(text: str, style_name: str) -> str:
    """Apply a named style to text.

    Args:
        text: Text to style
        style_name: Name of the style to apply

    Returns:
        Styled text
    """
    return f"[{style_name}]{text}[/{style_name}]"


def format_path(path: str | Path, path_type: str = "auto") -> str:
    """Format a path with appropriate styling based on type.

    Args:
        path: Path to format
        path_type: Type of path (auto, file, directory, spec_file)

    Returns:
        Formatted path with appropriate styling
    """
    path_obj = Path(path)

    if path_type == "auto":
        # Auto-detect path type
        if path_obj.suffix == ".md" and ".specs" in str(path_obj):
            return SpecStyles.spec_file(path)
        elif path_obj.is_file() if path_obj.exists() else path_obj.suffix:
            return SpecStyles.file(path)
        else:
            return SpecStyles.directory(path)
    elif path_type == "file":
        return SpecStyles.file(path)
    elif path_type == "directory":
        return SpecStyles.directory(path)
    elif path_type == "spec_file":
        return SpecStyles.spec_file(path)
    else:
        return SpecStyles.path(path)


def format_status(message: str, status: str, include_indicator: bool = True) -> str:
    """Format a status message with optional indicator.

    Args:
        message: Message to format
        status: Status type (success, warning, error, info)
        include_indicator: Whether to include status indicator

    Returns:
        Formatted status message
    """
    if not include_indicator:
        return style_text(message, status)

    # Get appropriate indicator from theme
    theme = get_current_theme()
    emoji_replacements = theme.get_emoji_replacements()

    indicators = {
        "success": emoji_replacements.get("✅", "[success]✓[/success]"),
        "warning": emoji_replacements.get("⚠️", "[warning]⚠[/warning]"),
        "error": emoji_replacements.get("❌", "[error]✗[/error]"),
        "info": emoji_replacements.get("ℹ️", "[info]i[/info]"),
    }

    indicator = indicators.get(status, "")
    formatted_message = style_text(message, status)

    return f"{indicator} {formatted_message}" if indicator else formatted_message


def create_rich_text(text: str, style: str | Style | None = None) -> Text:
    """Create a Rich Text object with optional styling.

    Args:
        text: Text content
        style: Optional style to apply

    Returns:
        Rich Text object
    """
    rich_text = Text(text)
    if style:
        if isinstance(style, str):
            # Convert style name to actual style from theme
            theme = get_current_theme()
            style_str = theme.get_style(style)
            if style_str:
                rich_text.stylize(style_str)
        else:
            rich_text.stylize(style)

    debug_logger.log(
        "DEBUG", "Rich Text created", text_length=len(text), has_style=style is not None
    )

    return rich_text
