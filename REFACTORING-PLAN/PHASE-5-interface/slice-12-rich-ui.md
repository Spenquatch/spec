# Slice 12: Rich Terminal UI System [DEPRECATED - SPLIT INTO 12A/12B/12C]

**NOTE: This slice has been split into focused components for better implementation:**
- **[slice-12a-console-theme.md](./slice-12a-console-theme.md)**: Console & Theme bootstrap with Rich Console and custom theming
- **[slice-12b-progress-components.md](./slice-12b-progress-components.md)**: Progress Components with spinner/progress-bar wrappers and progress manager
- **[slice-12c-formatter-error-views.md](./slice-12c-formatter-error-views.md)**: Formatter & Error Views with table/tree render utils and error panels

Please implement the individual slices instead of this combined version.

## Goal

Create a comprehensive Rich-based terminal UI system that replaces all emoji usage with styled text, provides progress indicators, and integrates enhanced error handling with user-friendly messages.

## Context

The current monolithic code uses emojis throughout for status indication and has basic print statements for user feedback. This slice creates a sophisticated terminal UI system using the Rich library that provides consistent styling, progress tracking, and enhanced error presentation. This integrates the terminal styling maintenance item into the refactoring architecture.

## Scope

**Included in this slice:**
- Rich-based console system with consistent theming
- Progress bars and status indicators for long operations
- Error formatting and presentation system
- Emoji replacement with styled text equivalents
- User message formatting utilities
- Logging formatters for structured debug output (moved from slice-2)

**NOT included in this slice:**
- CLI command implementations (comes in slice-13-cli-commands)
- Interactive prompts or wizards
- File system or Git operations (already implemented in previous phases)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (All exception types and error handling)
- `spec_cli.logging.debug` (debug_logger for operation tracking)
- `spec_cli.config.settings` (Settings for configuration)

**Required dependencies:**
- `rich` library installed via poetry (add to pyproject.toml dependencies)

## Files to Create

```
spec_cli/ui/
├── __init__.py              # Module exports
├── console.py               # Rich console wrapper and theming
├── progress.py              # Progress bars and indicators
├── formatters.py            # Message and error formatters
└── error_display.py         # Error presentation system
```

## Implementation Steps

### Step 1: Add Rich dependency

Update `pyproject.toml` to include Rich:

```toml
[tool.poetry.dependencies]
rich = "^13.7.0"
```

### Step 2: Create spec_cli/ui/__init__.py

```python
"""Rich terminal UI system for spec CLI.

This package provides Rich-based terminal styling, progress indicators,
and error presentation to replace emoji usage and enhance user experience.
"""

from .console import SpecConsole, get_console
from .progress import SpecProgress, FileProcessingProgress
from .formatters import MessageFormatter, CommandFormatter
from .error_display import ErrorDisplay

__all__ = [
    "SpecConsole",
    "get_console", 
    "SpecProgress",
    "FileProcessingProgress",
    "MessageFormatter",
    "CommandFormatter",
    "ErrorDisplay",
]
```

### Step 3: Create spec_cli/ui/console.py

```python
from rich.console import Console
from rich.theme import Theme
from rich.style import Style
from typing import Optional, Dict, Any
from ..config.settings import get_settings

# Define consistent color theme for spec operations
SPEC_THEME = Theme({
    "success": "bold green",
    "warning": "bold yellow", 
    "error": "bold red",
    "info": "bold blue",
    "highlight": "bold cyan",
    "muted": "dim white",
    "path": "bold magenta",
    "file": "green",
    "directory": "blue",
    "count": "bold white",
    "command": "bold yellow",
    "progress": "cyan",
})

class SpecConsole:
    """Rich console wrapper with spec-specific styling and emoji replacement."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console(theme=SPEC_THEME)
        self.settings = get_settings()
        
        # Emoji to styled text mapping
        self._emoji_replacements = {
            "✅": "[success]✓[/success]",
            "❌": "[error]✗[/error]", 
            "⚠️": "[warning]![/warning]",
            "📝": "[info]→[/info]",
            "📁": "[directory]DIR[/directory]",
            "📄": "[file]FILE[/file]",
            "🔍": "[info]DEBUG[/info]",
            "🚀": "[success]START[/success]",
            "💾": "[info]SAVE[/info]",
            "🔄": "[warning]UPDATE[/warning]",
            "⏭️": "[muted]SKIP[/muted]",
            "🎉": "[success]COMPLETE[/success]",
            "ℹ️": "[info]INFO[/info]",
        }
    
    def print_success(self, message: str, **kwargs) -> None:
        """Print success message with green styling."""
        styled_message = self._replace_emojis(message)
        self.console.print(f"[success]✓[/success] {styled_message}", **kwargs)
    
    def print_error(self, message: str, **kwargs) -> None:
        """Print error message with red styling."""
        styled_message = self._replace_emojis(message)
        self.console.print(f"[error]✗[/error] {styled_message}", **kwargs)
    
    def print_warning(self, message: str, **kwargs) -> None:
        """Print warning message with yellow styling."""
        styled_message = self._replace_emojis(message)
        self.console.print(f"[warning]![/warning] {styled_message}", **kwargs)
    
    def print_info(self, message: str, **kwargs) -> None:
        """Print info message with blue styling."""
        styled_message = self._replace_emojis(message)
        self.console.print(f"[info]→[/info] {styled_message}", **kwargs)
    
    def print_command(self, command: str, description: str = "") -> None:
        """Print command suggestion with highlighting."""
        if description:
            self.console.print(f"  [command]{command}[/command]  # {description}")
        else:
            self.console.print(f"  [command]{command}[/command]")
    
    def print_path(self, path: str, label: str = "") -> None:
        """Print file path with appropriate styling."""
        if label:
            self.console.print(f"{label}: [path]{path}[/path]")
        else:
            self.console.print(f"[path]{path}[/path]")
    
    def print_count(self, count: int, label: str) -> None:
        """Print count with emphasis."""
        self.console.print(f"[count]{count}[/count] {label}")
    
    def print(self, *args, **kwargs) -> None:
        """Print with emoji replacement."""
        if args and isinstance(args[0], str):
            styled_message = self._replace_emojis(args[0])
            self.console.print(styled_message, *args[1:], **kwargs)
        else:
            self.console.print(*args, **kwargs)
    
    def _replace_emojis(self, text: str) -> str:
        """Replace emoji characters with styled text equivalents."""
        for emoji, replacement in self._emoji_replacements.items():
            text = text.replace(emoji, replacement)
        return text
    
    @property
    def width(self) -> int:
        """Get console width."""
        return self.console.width
    
    @property  
    def height(self) -> int:
        """Get console height."""
        return self.console.height

# Global console instance
_console: Optional[SpecConsole] = None

def get_console() -> SpecConsole:
    """Get global console instance."""
    global _console
    if _console is None:
        _console = SpecConsole()
    return _console
```

### Step 4: Create spec_cli/ui/progress.py

```python
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager
from .console import get_console

class SpecProgress:
    """Progress tracker for spec operations with Rich styling."""
    
    def __init__(self, description: str = "Processing"):
        self.console = get_console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console.console
        )
        self.task_id: Optional[TaskID] = None
        self.description = description
        self._active = False
    
    def start(self, total: Optional[int] = None) -> TaskID:
        """Start progress tracking."""
        if not self._active:
            self.progress.start()
            self._active = True
        
        self.task_id = self.progress.add_task(
            description=self.description,
            total=total
        )
        return self.task_id
    
    def update(self, advance: int = 1, description: Optional[str] = None) -> None:
        """Update progress."""
        if self.task_id is not None:
            update_kwargs = {"advance": advance}
            if description:
                update_kwargs["description"] = description
            self.progress.update(self.task_id, **update_kwargs)
    
    def finish(self, message: Optional[str] = None) -> None:
        """Complete progress tracking."""
        if self._active:
            self.progress.stop()
            self._active = False
        
        if message:
            self.console.print_success(message)
    
    @contextmanager
    def track(self, total: Optional[int] = None):
        """Context manager for progress tracking."""
        try:
            self.start(total)
            yield self
        finally:
            self.finish()

class FileProcessingProgress:
    """Specialized progress tracker for file processing operations."""
    
    def __init__(self, files: List[Path], operation: str = "Processing"):
        self.files = files
        self.operation = operation
        self.console = get_console()
        self.current_file_index = 0
        self.results: Dict[str, Any] = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "error_files": []
        }
    
    @contextmanager
    def track_files(self):
        """Track processing of multiple files."""
        with SpecProgress(f"{self.operation} files") as progress:
            progress.start(len(self.files))
            
            try:
                yield self
            finally:
                self._show_summary()
    
    def process_file(self, file_path: Path, success: bool, error: Optional[str] = None) -> None:
        """Update progress for file processing result."""
        if success:
            self.results["processed"] += 1
            self.console.print_info(f"Processed: [path]{file_path}[/path]")
        elif error:
            self.results["errors"] += 1
            self.results["error_files"].append({"file": str(file_path), "error": error})
            self.console.print_error(f"Error processing [path]{file_path}[/path]: {error}")
        else:
            self.results["skipped"] += 1
            self.console.print_warning(f"Skipped: [path]{file_path}[/path]")
        
        self.current_file_index += 1
    
    def _show_summary(self) -> None:
        """Show processing summary."""
        self.console.print()
        self.console.print_success(f"{self.operation} complete!")
        self.console.print_count(self.results["processed"], "files processed")
        
        if self.results["skipped"] > 0:
            self.console.print_count(self.results["skipped"], "files skipped")
        
        if self.results["errors"] > 0:
            self.console.print_count(self.results["errors"], "files with errors")
```

### Step 5: Create remaining UI modules

Create the other required files (`formatters.py` and `error_display.py`) following similar patterns with Rich styling and error presentation capabilities.

## Test Requirements

Create `tests/unit/ui/test_console.py`, `test_progress.py`, and other UI test files with these focus areas:

### Test Categories (31+ tests total)

**Console Tests:**
1. **test_spec_console_replaces_all_emoji_characters**
2. **test_spec_console_applies_success_styling** 
3. **test_spec_console_applies_error_styling**
4. **test_spec_console_applies_warning_styling**
5. **test_spec_console_applies_info_styling**
6. **test_spec_console_handles_command_formatting**
7. **test_spec_console_handles_path_formatting**
8. **test_spec_console_handles_count_formatting**
9. **test_get_console_returns_singleton_instance**

**Progress Tests:**
10. **test_spec_progress_starts_and_updates_correctly**
11. **test_spec_progress_handles_unknown_total**
12. **test_spec_progress_context_manager_works**
13. **test_spec_progress_displays_time_elapsed**
14. **test_file_processing_progress_tracks_multiple_files**
15. **test_file_processing_progress_handles_failures**
16. **test_file_processing_progress_shows_summary**

**Formatter Tests (moved from slice-2):**
17. **test_structured_formatter_formats_with_timestamp**
18. **test_structured_formatter_formats_without_timestamp**
19. **test_format_operation_summary_displays_sorted_results**
20. **test_format_debug_context_handles_nested_data**
21. **test_format_debug_context_handles_lists_and_dicts**
22. **test_formatter_handles_empty_context**

**Integration Tests:**
23. **test_ui_system_works_without_color_support**
24. **test_ui_system_respects_no_color_environment**
25. **test_ui_system_handles_narrow_terminals**
26. **test_ui_components_integrate_with_rich_properly**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Install Rich dependency
poetry add rich

# Run the specific tests for this slice
poetry run pytest tests/unit/ui/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/ui/ --cov=spec_cli.ui --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/ui/

# Check code formatting
poetry run ruff check spec_cli/ui/
poetry run ruff format spec_cli/ui/

# Verify imports work correctly
python -c "from spec_cli.ui import get_console, SpecProgress; print('Import successful')"

# Test emoji replacement functionality
python -c "
from spec_cli.ui import get_console
console = get_console()
console.print_success('✅ This should show a styled checkmark')
console.print_error('❌ This should show a styled X')
"

# Verify no emoji characters remain in main module
python -c "
import re
with open('spec_cli/__main__.py', 'r') as f:
    content = f.read()
emoji_pattern = r'[\\u{1F600}-\\u{1F64F}]|[\\u{1F300}-\\u{1F5FF}]|[\\u{1F680}-\\u{1F6FF}]|[\\u{1F1E0}-\\u{1F1FF}]'
matches = re.findall(emoji_pattern, content)
if matches:
    print(f'Found {len(matches)} emoji characters that need replacement')
else:
    print('No emoji characters found - replacement complete')
"
```

## Definition of Done

- [ ] `spec_cli/ui/` package created with all required modules
- [ ] Rich library integrated with consistent theming throughout
- [ ] All emoji characters replaced with styled text equivalents
- [ ] Progress tracking system implemented for long operations
- [ ] Error presentation system with user-friendly formatting
- [ ] Console singleton pattern implemented for consistent access
- [ ] All 25+ test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Rich dependency added to pyproject.toml
- [ ] No emoji characters remain in codebase
- [ ] Integration with settings and logging systems verified

## Next Slice Preparation

This slice enables **slice-13-cli-commands.md** by providing:
- `SpecConsole` for all user output with consistent styling
- `SpecProgress` for progress tracking during operations
- `ErrorDisplay` for enhanced error presentation
- Complete emoji replacement system

The CLI commands slice will use these UI components to provide an excellent user experience with rich terminal output and comprehensive error handling.