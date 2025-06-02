# Slice 12A: Console & Theme Bootstrap

## Goal

Bootstrap a Rich `Console` with custom theme and global style helpers, replacing emoji usage with styled text throughout the application.

## Context

Building on the foundational systems from previous phases, this slice establishes the core Rich console infrastructure with custom theming and styling. It provides the foundation that progress components (slice-12b) and formatter views (slice-12c) will build upon. This slice focuses specifically on console initialization, theme configuration, and basic styling utilities.

## Scope

**Included in this slice:**
- Rich Console wrapper with custom theme configuration
- Global style helpers and color scheme definitions
- Emoji replacement with styled text equivalents
- Console singleton pattern for consistent usage
- Basic message styling utilities
- Theme customization and configuration management

**NOT included in this slice:**
- Progress bars and spinners (comes in slice-12b)
- Complex formatters and error views (comes in slice-12c)
- CLI command integration (comes in slice-13)
- Interactive prompts or wizards

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for UI errors)
- `spec_cli.logging.debug` (debug_logger for UI operation tracking)
- `spec_cli.config.settings` (SpecSettings for theme configuration)

**Required dependencies:**
- `rich` library installed via poetry (add to pyproject.toml dependencies)

## Files to Create

```
spec_cli/ui/
├── __init__.py           # Module exports
├── console.py           # Rich console wrapper and theming
├── theme.py             # Theme definitions and styling
└── styles.py            # Global style helpers and utilities
```

## Implementation Steps

### Step 1: Add Rich dependency to pyproject.toml

```toml
[tool.poetry.dependencies]
# ... existing dependencies
rich = "^13.0.0"
```

### Step 2: Create spec_cli/ui/__init__.py

```python
"""Rich-based terminal UI system for spec CLI.

This package provides console theming, styling utilities, and the foundation
for progress tracking and error display components.
"""

from .console import get_console, spec_console
from .theme import SpecTheme, get_current_theme
from .styles import SpecStyles, style_text, format_path, format_status

__all__ = [
    "get_console",
    "spec_console", 
    "SpecTheme",
    "get_current_theme",
    "SpecStyles",
    "style_text",
    "format_path",
    "format_status",
]
```

### Step 3: Create spec_cli/ui/theme.py

```python
from enum import Enum
from typing import Dict, Any, Optional
from rich.theme import Theme
from rich.style import Style
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class ColorScheme(Enum):
    """Available color schemes for the spec CLI."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    MINIMAL = "minimal"

class SpecTheme:
    """Manages theming and color schemes for the spec CLI interface."""
    
    def __init__(self, color_scheme: ColorScheme = ColorScheme.DEFAULT):
        self.color_scheme = color_scheme
        self._theme: Optional[Theme] = None
        self._load_theme()
        
        debug_logger.log("INFO", "SpecTheme initialized", 
                        color_scheme=color_scheme.value)
    
    def _load_theme(self) -> None:
        """Load the Rich theme based on color scheme."""
        theme_styles = self._get_theme_styles()
        self._theme = Theme(theme_styles)
        
        debug_logger.log("DEBUG", "Theme loaded",
                        style_count=len(theme_styles))
    
    def _get_theme_styles(self) -> Dict[str, str]:
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
            base_styles.update({
                "title": "bold bright_white",
                "value": "white",
                "border": "bright_black",
                "muted": "dim white",
            })
        elif self.color_scheme == ColorScheme.LIGHT:
            base_styles.update({
                "title": "bold black",
                "value": "black", 
                "border": "black",
                "muted": "dim black",
                "code": "black on bright_white",
            })
        elif self.color_scheme == ColorScheme.MINIMAL:
            # Minimal color scheme - mostly monochrome
            base_styles.update({
                "success": "bold white",
                "warning": "bold white",
                "error": "bold white",
                "info": "bold white",
                "path": "white",
                "file": "white",
                "directory": "bold white",
                "progress_bar": "white",
                "spinner": "white",
            })
        
        return base_styles
    
    @property
    def theme(self) -> Theme:
        """Get the Rich theme object."""
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
        
        debug_logger.log("INFO", "Color scheme updated", 
                        new_scheme=color_scheme.value)
    
    def get_emoji_replacements(self) -> Dict[str, str]:
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
            "📝": "[git_commit]○[/git_commit]",
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
    def from_settings(cls, settings: Optional[SpecSettings] = None) -> 'SpecTheme':
        """Create theme from settings configuration.
        
        Args:
            settings: Optional settings object
            
        Returns:
            SpecTheme instance configured from settings
        """
        settings = settings or get_settings()
        
        # Try to get color scheme from settings
        color_scheme_name = getattr(settings, 'ui_color_scheme', 'default')
        
        try:
            color_scheme = ColorScheme(color_scheme_name.lower())
        except ValueError:
            debug_logger.log("WARNING", "Invalid color scheme in settings", 
                           scheme=color_scheme_name)
            color_scheme = ColorScheme.DEFAULT
        
        return cls(color_scheme)

# Global theme instance
_current_theme: Optional[SpecTheme] = None

def get_current_theme() -> SpecTheme:
    """Get the current global theme instance.
    
    Returns:
        Current SpecTheme instance
    """
    global _current_theme
    
    if _current_theme is None:
        _current_theme = SpecTheme.from_settings()
        debug_logger.log("INFO", "Global theme initialized")
    
    return _current_theme

def set_current_theme(theme: SpecTheme) -> None:
    """Set the current global theme.
    
    Args:
        theme: SpecTheme instance to set as current
    """
    global _current_theme
    _current_theme = theme
    
    debug_logger.log("INFO", "Global theme updated",
                    color_scheme=theme.color_scheme.value)

def reset_theme() -> None:
    """Reset the global theme to default."""
    global _current_theme
    _current_theme = None
    debug_logger.log("INFO", "Global theme reset")
```

### Step 4: Create spec_cli/ui/console.py

```python
from typing import Optional, Any, Dict
from rich.console import Console
from rich.style import Style
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from .theme import get_current_theme, SpecTheme

class SpecConsole:
    """Wrapper around Rich Console with spec-specific configuration."""
    
    def __init__(self, 
                 theme: Optional[SpecTheme] = None,
                 width: Optional[int] = None,
                 force_terminal: Optional[bool] = None,
                 no_color: bool = False):
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
            markup=True,      # Enable Rich markup
            emoji=False,      # Disable emoji (we handle this manually)
            record=True,      # Enable recording for testing
        )
        
        debug_logger.log("INFO", "SpecConsole initialized",
                        width=self._console.width,
                        color_system=self._console._color_system.name if self._console._color_system else "none",
                        theme=self.theme.color_scheme.value)
    
    @property
    def console(self) -> Console:
        """Get the underlying Rich console."""
        return self._console
    
    def print(self, *objects: Any, **kwargs) -> None:
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
    
    def print_status(self, message: str, status: str = "info", **kwargs) -> None:
        """Print a status message with appropriate styling.
        
        Args:
            message: Message to print
            status: Status type (success, warning, error, info)
            **kwargs: Additional keyword arguments for Rich print
        """
        styled_message = f"[{status}]{message}[/{status}]"
        self.print(styled_message, **kwargs)
    
    def print_section(self, title: str, content: str = "", **kwargs) -> None:
        """Print a section with title and optional content.
        
        Args:
            title: Section title
            content: Optional section content
            **kwargs: Additional keyword arguments for Rich print
        """
        self.print(f"\n[title]{title}[/title]")
        if content:
            self.print(content, **kwargs)
    
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
                match = re.search(r'\[.*?\](.*?)\[/.*?\]', replacement)
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
        return self._console.width
    
    def is_terminal(self) -> bool:
        """Check if output is going to a terminal."""
        return self._console.is_terminal
    
    def export_text(self, clear: bool = True) -> str:
        """Export console output as plain text.
        
        Args:
            clear: Whether to clear the console after export
            
        Returns:
            Plain text representation of console output
        """
        text = self._console.export_text(clear=clear)
        debug_logger.log("DEBUG", "Console output exported",
                        length=len(text), cleared=clear)
        return text
    
    def export_html(self, clear: bool = True) -> str:
        """Export console output as HTML.
        
        Args:
            clear: Whether to clear the console after export
            
        Returns:
            HTML representation of console output
        """
        html = self._console.export_html(clear=clear)
        debug_logger.log("DEBUG", "Console HTML exported",
                        length=len(html), cleared=clear)
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
        
        debug_logger.log("INFO", "Console theme updated",
                        new_theme=theme.color_scheme.value)

# Global console instance
_spec_console: Optional[SpecConsole] = None

def get_console() -> SpecConsole:
    """Get the global spec console instance.
    
    Returns:
        Global SpecConsole instance
    """
    global _spec_console
    
    if _spec_console is None:
        settings = get_settings()
        
        # Check for no-color preference
        no_color = getattr(settings, 'no_color', False)
        
        _spec_console = SpecConsole(no_color=no_color)
        debug_logger.log("INFO", "Global console initialized")
    
    return _spec_console

def set_console(console: SpecConsole) -> None:
    """Set the global console instance.
    
    Args:
        console: SpecConsole instance to set as global
    """
    global _spec_console
    _spec_console = console
    debug_logger.log("INFO", "Global console updated")

def reset_console() -> None:
    """Reset the global console to default."""
    global _spec_console
    _spec_console = None
    debug_logger.log("INFO", "Global console reset")

# Convenient alias for the global console
spec_console = get_console
```

### Step 5: Create spec_cli/ui/styles.py

```python
from typing import Any, Optional, Union
from rich.text import Text
from rich.style import Style
from pathlib import Path
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
    def path(path: Union[str, Path]) -> str:
        """Format path with appropriate styling.
        
        Args:
            path: Path to format
            
        Returns:
            Formatted path with path styling
        """
        return f"[path]{path}[/path]"
    
    @staticmethod
    def file(filename: Union[str, Path]) -> str:
        """Format filename with appropriate styling.
        
        Args:
            filename: Filename to format
            
        Returns:
            Formatted filename with file styling
        """
        return f"[file]{filename}[/file]"
    
    @staticmethod
    def directory(dirname: Union[str, Path]) -> str:
        """Format directory name with appropriate styling.
        
        Args:
            dirname: Directory name to format
            
        Returns:
            Formatted directory name with directory styling
        """
        return f"[directory]{dirname}[/directory]"
    
    @staticmethod
    def spec_file(filename: Union[str, Path]) -> str:
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

def format_path(path: Union[str, Path], 
               path_type: str = "auto") -> str:
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

def format_status(message: str, 
                 status: str,
                 include_indicator: bool = True) -> str:
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

def create_rich_text(text: str, 
                    style: Optional[Union[str, Style]] = None) -> Text:
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
    
    debug_logger.log("DEBUG", "Rich Text created",
                    text_length=len(text),
                    has_style=style is not None)
    
    return rich_text
```

## Test Requirements

Create comprehensive tests for console and theme functionality:

### Test Cases (14 tests total)

**Theme Tests:**
1. **test_spec_theme_initialization**
2. **test_color_scheme_variations**
3. **test_theme_style_retrieval**
4. **test_emoji_replacements_mapping**
5. **test_theme_from_settings**
6. **test_global_theme_management**

**Console Tests:**
7. **test_spec_console_initialization**
8. **test_console_emoji_replacement**
9. **test_console_status_printing**
10. **test_console_theme_updates**
11. **test_console_export_functionality**
12. **test_global_console_management**

**Styles Tests:**
13. **test_spec_styles_formatting**
14. **test_style_helpers_and_utilities**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Add Rich dependency
poetry add rich

# Run the specific tests for this slice
poetry run pytest tests/unit/ui/test_console.py tests/unit/ui/test_theme.py tests/unit/ui/test_styles.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/ui/ --cov=spec_cli.ui --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/ui/

# Check code formatting
poetry run ruff check spec_cli/ui/
poetry run ruff format spec_cli/ui/

# Verify imports work correctly
python -c "from spec_cli.ui import get_console, SpecTheme, SpecStyles; print('Import successful')"

# Test theme functionality
python -c "
from spec_cli.ui.theme import SpecTheme, ColorScheme
from spec_cli.ui.console import SpecConsole

# Test theme creation
theme = SpecTheme(ColorScheme.DARK)
print(f'Theme loaded with scheme: {theme.color_scheme.value}')
print(f'Success style: {theme.get_style(\"success\")}')

# Test emoji replacements
replacements = theme.get_emoji_replacements()
print(f'Emoji replacements: {len(replacements)} defined')
print(f'✅ becomes: {replacements[\"✅\"]}')
"

# Test console functionality
python -c "
from spec_cli.ui.console import SpecConsole
from spec_cli.ui.styles import SpecStyles

console = SpecConsole()
print(f'Console width: {console.get_width()}')
print(f'Is terminal: {console.is_terminal()}')

# Test emoji replacement
test_text = 'Operation completed ✅'
replaced = console._replace_emojis(test_text)
print(f'Original: {test_text}')
print(f'Replaced: {replaced}')
"

# Test style helpers
python -c "
from spec_cli.ui.styles import SpecStyles, format_path, format_status
from pathlib import Path

# Test basic styles
print(SpecStyles.success('Success message'))
print(SpecStyles.error('Error message'))
print(SpecStyles.path('/path/to/file'))

# Test format helpers
print(format_path(Path('src/main.py')))
print(format_status('Operation completed', 'success'))
"
```

## Definition of Done

- [ ] Rich dependency added to pyproject.toml
- [ ] SpecTheme class with color scheme management
- [ ] SpecConsole wrapper with emoji replacement
- [ ] Global style helpers and utilities
- [ ] Theme configuration from settings
- [ ] Emoji to styled text replacement system
- [ ] Console singleton pattern implementation
- [ ] All 14 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Foundation ready for progress components (slice-12b)

## Next Slice Preparation

This slice enables **slice-12b-progress-components.md** by providing:
- SpecConsole foundation for progress display
- Theme system for consistent progress styling
- Style helpers for progress indicators
- Console management for progress updates