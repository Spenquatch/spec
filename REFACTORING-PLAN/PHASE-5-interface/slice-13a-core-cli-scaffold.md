# Slice 13A: Core CLI Scaffold

## Goal

Build the Click/Typer parser, shared options, and core commands (`init`, `status`, `help`) with comprehensive unit tests to establish the CLI foundation.

## Context

This slice creates the foundational CLI infrastructure using modern argument parsing with Click or Typer, establishing shared option patterns, error handling, and the core commands that form the base of the CLI system. It provides the scaffolding that subsequent CLI slices will build upon.

## Scope

**Included in this slice:**
- Modern CLI framework setup (Click/Typer with Rich integration)
- Shared CLI options and configuration patterns
- Core commands: `init`, `status`, `help`
- CLI error handling and user-friendly messaging
- Argument validation and path resolution
- Debug mode and logging integration
- CLI utilities and helper functions
- Comprehensive unit tests for all CLI components

**NOT included in this slice:**
- Generation commands (comes in slice-13B)
- Diff and history commands (comes in slice-13C)
- Complex interactive workflows
- Shell completion (future enhancement)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.ui.console` (SpecConsole from slice-12a)
- `spec_cli.ui.progress_manager` (ProgressManager from slice-12b)
- `spec_cli.ui.formatters` (MessageFormatter from slice-12c)
- `spec_cli.exceptions` (All exception types for CLI error handling)
- `spec_cli.logging.debug` (debug_logger for CLI operation tracking)
- `spec_cli.config.settings` (SpecSettings for configuration)
- `spec_cli.git.repository` (GitRepository from slice-9)

**Required functions/classes:**
- `get_console()`, `SpecConsole` from slice-12a-console-theme
- `get_progress_manager()`, `ProgressManager` from slice-12b-progress-components
- `MessageFormatter`, `show_message()` from slice-12c-formatter-error-views
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings`, `get_settings()` from slice-3a-settings-console
- `GitRepository` from slice-9-git-operations

## Files to Create

```
spec_cli/
├── cli/
│   ├── __init__.py           # Module exports
│   ├── app.py               # Main CLI application with Click/Typer
│   ├── options.py           # Shared CLI options and decorators
│   ├── utils.py             # CLI utility functions
│   ├── exceptions.py        # CLI-specific exception handling
│   └── commands/
│       ├── __init__.py      # Command module exports
│       ├── init.py          # spec init command
│       ├── status.py        # spec status command
│       └── help.py          # spec help command
```

## Implementation Steps

### Step 1: Add Click dependency to pyproject.toml

```toml
[tool.poetry.dependencies]
click = "^8.1.7"
rich-click = "^1.7.1"
```

### Step 2: Create spec_cli/cli/__init__.py

```python
"""CLI interface for spec CLI.

This package provides the command-line interface with Click and Rich integration
for beautiful, modern command-line interactions.
"""

from .app import app, main
from .utils import (
    handle_cli_error, setup_cli_logging, validate_file_paths,
    get_user_confirmation, format_command_output
)
from .options import (
    debug_option, verbose_option, dry_run_option,
    force_option, message_option, common_options
)

__all__ = [
    "app",
    "main",
    "handle_cli_error",
    "setup_cli_logging", 
    "validate_file_paths",
    "get_user_confirmation",
    "format_command_output",
    "debug_option",
    "verbose_option",
    "dry_run_option",
    "force_option",
    "message_option",
    "common_options",
]
```

### Step 3: Create spec_cli/cli/options.py

```python
"""Shared CLI options and decorators."""

import click
from functools import update_wrapper
from typing import Callable, Any
from ..logging.debug import debug_logger

# Common option decorators
def debug_option(f: Callable) -> Callable:
    """Add debug mode option."""
    def callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
        if value:
            debug_logger.log("INFO", "Debug mode enabled via CLI")
        return value
    
    return click.option(
        '--debug',
        is_flag=True,
        help='Enable debug output and detailed logging',
        callback=callback,
        expose_value=True,
    )(f)

def verbose_option(f: Callable) -> Callable:
    """Add verbose mode option."""
    return click.option(
        '--verbose', '-v',
        is_flag=True,
        help='Enable verbose output',
    )(f)

def dry_run_option(f: Callable) -> Callable:
    """Add dry run option."""
    return click.option(
        '--dry-run',
        is_flag=True,
        help='Show what would be done without making changes',
    )(f)

def force_option(f: Callable) -> Callable:
    """Add force option."""
    return click.option(
        '--force',
        is_flag=True,
        help='Force operation even if conflicts or warnings exist',
    )(f)

def message_option(required: bool = False) -> Callable:
    """Add commit message option."""
    def decorator(f: Callable) -> Callable:
        return click.option(
            '--message', '-m',
            required=required,
            help='Commit message' + (' (required)' if required else ''),
        )(f)
    return decorator

def files_argument(f: Callable) -> Callable:
    """Add files argument."""
    return click.argument(
        'files',
        nargs=-1,
        type=click.Path(exists=False),  # Allow non-existent files for generation
        required=True,
    )(f)

def optional_files_argument(f: Callable) -> Callable:
    """Add optional files argument."""
    return click.argument(
        'files',
        nargs=-1,
        type=click.Path(exists=False),
        required=False,
    )(f)

def common_options(f: Callable) -> Callable:
    """Apply common options to a command."""
    f = debug_option(f)
    f = verbose_option(f)
    return f

def spec_command(name: str = None, **kwargs) -> Callable:
    """Decorator for spec commands with common setup."""
    def decorator(f: Callable) -> Callable:
        # Apply common options
        f = common_options(f)
        
        # Create click command
        cmd = click.command(name, **kwargs)(f)
        
        # Add error handling wrapper
        def wrapper(*args, **kwargs):
            from .utils import handle_cli_error
            try:
                return cmd.callback(*args, **kwargs)
            except Exception as e:
                handle_cli_error(e, f"Command '{name or f.__name__}' failed")
        
        # Preserve command metadata
        wrapper = update_wrapper(wrapper, f)
        cmd.callback = wrapper
        
        return cmd
    
    return decorator

# Validation helpers
def validate_spec_repository(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """Validate that we're in a spec repository."""
    from ..git.repository import GitRepository
    from ..exceptions import SpecRepositoryError
    
    try:
        repo = GitRepository()
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return value
    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository error: {e}")

def validate_file_exists(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """Validate that file exists."""
    if value and not click.Path(exists=True).convert(value, param, ctx):
        raise click.BadParameter(f"File '{value}' does not exist")
    return value
```

### Step 4: Create spec_cli/cli/utils.py

```python
"""CLI utility functions."""

import sys
import click
from typing import Any, Optional, List
from pathlib import Path
from ..exceptions import SpecError
from ..logging.debug import debug_logger
from ..ui.console import get_console
from ..ui.formatters import show_message

def handle_cli_error(error: Exception, context: Optional[str] = None, exit_code: int = 1) -> None:
    """Handle CLI errors with appropriate formatting and exit codes.
    
    Args:
        error: Exception that occurred
        context: Optional context information
        exit_code: Exit code to use when exiting
    """
    console = get_console()
    
    # Format error message based on type
    if isinstance(error, click.ClickException):
        # Click handles its own formatting
        error.show()
    elif isinstance(error, SpecError):
        # Use our custom error formatting
        error_msg = str(error)
        if hasattr(error, 'suggestions') and error.suggestions:
            error_msg += "\n\nSuggestions:"
            for suggestion in error.suggestions:
                error_msg += f"\n  • {suggestion}"
        
        show_message(error_msg, "error", context)
    else:
        # Generic error handling
        error_msg = f"{type(error).__name__}: {error}"
        show_message(error_msg, "error", context)
    
    # Log error for debugging
    debug_logger.log("ERROR", "CLI error occurred", 
                    error=str(error), 
                    error_type=type(error).__name__,
                    context=context)
    
    # Exit with appropriate code
    sys.exit(exit_code)

def setup_cli_logging(debug_mode: bool = False, verbose: bool = False) -> None:
    """Set up CLI logging based on debug and verbose modes.
    
    Args:
        debug_mode: Whether debug mode is enabled
        verbose: Whether verbose mode is enabled
    """
    if debug_mode:
        debug_logger.log("INFO", "Debug mode enabled for CLI")
        # In debug mode, enable more detailed logging
    elif verbose:
        debug_logger.log("INFO", "Verbose mode enabled for CLI")
        # In verbose mode, show more user-facing information
    else:
        # In normal mode, reduce logging verbosity
        pass

def validate_file_paths(file_paths: List[str]) -> List[Path]:
    """Validate and normalize file paths from CLI input.
    
    Args:
        file_paths: List of file path strings
        
    Returns:
        List of validated Path objects
        
    Raises:
        click.BadParameter: If validation fails
    """
    if not file_paths:
        raise click.BadParameter("No file paths provided")
    
    validated_paths = []
    for path_str in file_paths:
        try:
            path = Path(path_str).resolve()
            validated_paths.append(path)
        except Exception as e:
            raise click.BadParameter(f"Invalid file path '{path_str}': {e}") from e
    
    return validated_paths

def get_user_confirmation(message: str, default: bool = False) -> bool:
    """Get user confirmation with Click prompt.
    
    Args:
        message: Confirmation message
        default: Default value
        
    Returns:
        True if user confirms
    """
    return click.confirm(message, default=default)

def format_command_output(data: Any, format_type: str = "auto") -> None:
    """Format and display command output using Rich UI.
    
    Args:
        data: Data to display
        format_type: Format type (auto, table, list, json)
    """
    from ..ui.formatters import format_data
    
    if format_type == "auto":
        # Auto-detect format based on data type
        format_data(data)
    else:
        # Use specific format
        format_data(data, format_type)

def echo_status(message: str, status_type: str = "info") -> None:
    """Echo a status message with styling.
    
    Args:
        message: Message to display
        status_type: Type of status (info, success, warning, error)
    """
    show_message(message, status_type)

def get_spec_repository():
    """Get the spec repository instance with error handling.
    
    Returns:
        GitRepository instance
        
    Raises:
        click.ClickException: If repository is not initialized
    """
    from ..git.repository import GitRepository
    from ..exceptions import SpecRepositoryError
    
    try:
        repo = GitRepository()
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return repo
    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository error: {e}")

def with_progress_context(operation_name: str):
    """Decorator to wrap command with progress context.
    
    Args:
        operation_name: Name of the operation for progress tracking
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from ..ui.progress_manager import get_progress_manager
            
            progress_manager = get_progress_manager()
            operation_id = f"{operation_name}_{id(f)}"
            
            progress_manager.start_indeterminate_operation(
                operation_id,
                f"Running {operation_name}..."
            )
            
            try:
                result = f(*args, **kwargs)
                progress_manager.finish_operation(operation_id)
                return result
            except Exception as e:
                progress_manager.finish_operation(operation_id)
                raise
        
        return wrapper
    return decorator

def get_current_working_directory() -> Path:
    """Get current working directory as Path object.
    
    Returns:
        Current working directory
    """
    return Path.cwd()

def is_in_spec_repository() -> bool:
    """Check if current directory is in a spec repository.
    
    Returns:
        True if in spec repository
    """
    try:
        from ..git.repository import GitRepository
        repo = GitRepository()
        return repo.is_initialized()
    except Exception:
        return False
```

### Step 5: Create spec_cli/cli/exceptions.py

```python
"""CLI-specific exception handling."""

import click
from typing import Optional, List
from ..exceptions import SpecError

class CLIError(SpecError):
    """Base exception for CLI-specific errors."""
    pass

class CLIValidationError(CLIError):
    """CLI input validation error."""
    
    def __init__(self, message: str, parameter: Optional[str] = None, suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.parameter = parameter
        self.suggestions = suggestions or []

class CLIConfigurationError(CLIError):
    """CLI configuration error."""
    pass

class CLIOperationError(CLIError):
    """CLI operation error."""
    pass

def convert_to_click_exception(error: Exception) -> click.ClickException:
    """Convert various exceptions to Click exceptions.
    
    Args:
        error: Exception to convert
        
    Returns:
        ClickException with appropriate message
    """
    if isinstance(error, click.ClickException):
        return error
    elif isinstance(error, CLIError):
        return click.ClickException(str(error))
    elif isinstance(error, SpecError):
        return click.ClickException(f"Spec error: {error}")
    else:
        return click.ClickException(f"Unexpected error: {error}")

def handle_validation_error(parameter: str, message: str, suggestions: Optional[List[str]] = None) -> None:
    """Handle validation errors with suggestions.
    
    Args:
        parameter: Parameter name that failed validation
        message: Error message
        suggestions: Optional list of suggestions
        
    Raises:
        click.BadParameter: With formatted message
    """
    error_msg = message
    if suggestions:
        error_msg += "\n\nSuggestions:"
        for suggestion in suggestions:
            error_msg += f"\n  • {suggestion}"
    
    raise click.BadParameter(error_msg)
```

### Step 6: Create spec_cli/cli/commands/__init__.py

```python
"""CLI command implementations.

This package contains all CLI command implementations with Click integration.
"""

from .init import init_command
from .status import status_command
from .help import help_command

__all__ = [
    "init_command",
    "status_command", 
    "help_command",
]
```

### Step 7: Create spec_cli/cli/commands/init.py

```python
"""Spec init command implementation."""

import click
from pathlib import Path
from ...git.repository import GitRepository
from ...exceptions import SpecRepositoryError
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...logging.debug import debug_logger
from ..options import spec_command, force_option
from ..utils import echo_status

@spec_command()
@force_option
def init_command(debug: bool, verbose: bool, force: bool) -> None:
    """Initialize spec repository.
    
    Creates a new spec repository in the current directory with proper
    directory structure and Git configuration.
    """
    console = get_console()
    
    try:
        # Create repository instance
        repo = GitRepository()
        current_dir = Path.cwd()
        
        # Check if already initialized
        if repo.is_initialized() and not force:
            echo_status(
                "Spec repository is already initialized. Use --force to reinitialize.",
                "warning"
            )
            return
        
        if force and repo.is_initialized():
            echo_status("Force reinitializing spec repository...", "info")
        else:
            echo_status("Initializing spec repository...", "info")
        
        # Initialize repository
        repo.initialize()
        
        # Verify initialization
        if not repo.is_initialized():
            raise SpecRepositoryError("Repository initialization failed")
        
        # Display success message
        success_msg = (
            "Spec repository initialized successfully!\n\n"
            "Created directories:\n"
            "  • .spec/     - Git repository for spec tracking\n"
            "  • .specs/    - Documentation directory\n\n"
            "Next steps:\n"
            "  • Run 'spec status' to check repository status\n"
            "  • Run 'spec gen <files>' to generate documentation"
        )
        
        echo_status(success_msg, "success")
        
        debug_logger.log("INFO", "Repository initialized", 
                        directory=str(current_dir),
                        force=force)
        
    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository initialization failed: {e}")
    except Exception as e:
        debug_logger.log("ERROR", "Initialization failed", error=str(e))
        raise click.ClickException(f"Unexpected error during initialization: {e}")
```

### Step 8: Create spec_cli/cli/commands/status.py

```python
"""Spec status command implementation."""

import click
from typing import Dict, Any
from ...git.repository import GitRepository
from ...exceptions import SpecRepositoryError
from ...ui.console import get_console
from ...ui.formatters import show_message, format_data
from ...ui.tables import StatusTable, create_key_value_table
from ...logging.debug import debug_logger
from ..options import spec_command
from ..utils import get_spec_repository, echo_status

@spec_command()
@click.option(
    '--health',
    is_flag=True,
    help='Show repository health check instead of regular status'
)
@click.option(
    '--git',
    is_flag=True,
    help='Also show Git repository status'
)
@click.option(
    '--summary',
    is_flag=True,
    help='Show processing capabilities summary'
)
def status_command(debug: bool, verbose: bool, health: bool, git: bool, summary: bool) -> None:
    """Show repository status.
    
    Displays comprehensive information about the spec repository including
    file counts, Git status, and system health.
    """
    console = get_console()
    
    try:
        # Get repository (validates initialization)
        repo = get_spec_repository()
        
        if health:
            # Show health check
            echo_status("Running repository health check...", "info")
            health_info = _get_repository_health(repo)
            _display_health_check(health_info)
        else:
            # Show regular status
            echo_status("Checking repository status...", "info")
            status_info = _get_repository_status(repo)
            _display_repository_status(status_info)
        
        # Show Git status if requested
        if git:
            console.print("\n[bold cyan]Git Status:[/bold cyan]")
            git_status = repo.get_git_status()
            _display_git_status(git_status)
        
        # Show processing summary if requested
        if summary:
            console.print("\n[bold cyan]Processing Summary:[/bold cyan]")
            summary_info = _get_processing_summary()
            _display_processing_summary(summary_info)
        
        debug_logger.log("INFO", "Status check completed",
                        health=health, git=git, summary=summary)
        
    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository error: {e}")
    except Exception as e:
        debug_logger.log("ERROR", "Status check failed", error=str(e))
        raise click.ClickException(f"Status check failed: {e}")

def _get_repository_status(repo: GitRepository) -> Dict[str, Any]:
    """Get repository status information."""
    from pathlib import Path
    
    spec_dir = Path(".spec")
    specs_dir = Path(".specs")
    
    # Count files in specs directory
    spec_files = list(specs_dir.rglob("*.md")) if specs_dir.exists() else []
    index_files = [f for f in spec_files if f.name == "index.md"]
    history_files = [f for f in spec_files if f.name == "history.md"]
    
    # Get Git status
    git_status = repo.get_git_status()
    
    return {
        "repository": {
            "initialized": repo.is_initialized(),
            "directory": str(Path.cwd()),
            "spec_dir_exists": spec_dir.exists(),
            "specs_dir_exists": specs_dir.exists(),
        },
        "files": {
            "total_spec_files": len(spec_files),
            "index_files": len(index_files),
            "history_files": len(history_files),
        },
        "git": {
            "staged_files": len(git_status.get("staged", [])),
            "modified_files": len(git_status.get("modified", [])),
            "untracked_files": len(git_status.get("untracked", [])),
        }
    }

def _get_repository_health(repo: GitRepository) -> Dict[str, Any]:
    """Get repository health information."""
    from pathlib import Path
    
    spec_dir = Path(".spec")
    specs_dir = Path(".specs")
    
    health = {
        "repository_structure": {
            "status": "healthy",
            "details": []
        },
        "git_configuration": {
            "status": "healthy", 
            "details": []
        },
        "file_permissions": {
            "status": "healthy",
            "details": []
        }
    }
    
    # Check repository structure
    if not spec_dir.exists():
        health["repository_structure"]["status"] = "error"
        health["repository_structure"]["details"].append(".spec directory missing")
    
    if not specs_dir.exists():
        health["repository_structure"]["status"] = "warning"
        health["repository_structure"]["details"].append(".specs directory missing")
    
    # Check Git configuration
    try:
        git_status = repo.get_git_status()
        if not git_status:
            health["git_configuration"]["status"] = "warning"
            health["git_configuration"]["details"].append("Unable to get Git status")
    except Exception as e:
        health["git_configuration"]["status"] = "error"
        health["git_configuration"]["details"].append(f"Git error: {e}")
    
    # Check file permissions
    try:
        if spec_dir.exists() and not spec_dir.is_dir():
            health["file_permissions"]["status"] = "error"
            health["file_permissions"]["details"].append(".spec exists but is not a directory")
        
        if specs_dir.exists() and not specs_dir.is_dir():
            health["file_permissions"]["status"] = "error"
            health["file_permissions"]["details"].append(".specs exists but is not a directory")
    except PermissionError:
        health["file_permissions"]["status"] = "error"
        health["file_permissions"]["details"].append("Permission denied accessing directories")
    
    return health

def _get_processing_summary() -> Dict[str, Any]:
    """Get processing capabilities summary."""
    return {
        "template_system": {
            "available_templates": ["default", "minimal", "comprehensive"],
            "custom_templates_supported": True,
        },
        "file_processing": {
            "supported_languages": ["python", "javascript", "typescript", "markdown"],
            "batch_processing": True,
            "conflict_resolution": True,
        },
        "ai_integration": {
            "enabled": False,  # Extension point
            "providers": [],
        }
    }

def _display_repository_status(status_info: Dict[str, Any]) -> None:
    """Display repository status using Rich formatting."""
    console = get_console()
    
    # Repository information
    repo_table = create_key_value_table(
        status_info["repository"],
        "Repository Information"
    )
    repo_table.print()
    
    # File counts
    files_table = create_key_value_table(
        status_info["files"],
        "File Statistics"
    )
    files_table.print()
    
    # Git status summary
    git_table = create_key_value_table(
        status_info["git"],
        "Git Status Summary"
    )
    git_table.print()

def _display_health_check(health_info: Dict[str, Any]) -> None:
    """Display health check results."""
    from ...ui.tables import StatusTable
    
    table = StatusTable("Repository Health Check")
    
    for component, info in health_info.items():
        status = info["status"]
        details = "; ".join(info["details"]) if info["details"] else "OK"
        
        # Map status to appropriate type
        status_type = {
            "healthy": "success",
            "warning": "warning", 
            "error": "error"
        }.get(status, "info")
        
        table.add_status(
            component.replace("_", " ").title(),
            status.upper(),
            details,
            status_type
        )
    
    table.print()

def _display_git_status(git_status: Dict[str, Any]) -> None:
    """Display Git status information."""
    console = get_console()
    
    if git_status.get("staged"):
        console.print("\n[green]Staged files:[/green]")
        for file in git_status["staged"]:
            console.print(f"  [green]A[/green] {file}")
    
    if git_status.get("modified"):
        console.print("\n[yellow]Modified files:[/yellow]")
        for file in git_status["modified"]:
            console.print(f"  [yellow]M[/yellow] {file}")
    
    if git_status.get("untracked"):
        console.print("\n[red]Untracked files:[/red]")
        for file in git_status["untracked"]:
            console.print(f"  [red]?[/red] {file}")
    
    if not any(git_status.values()):
        console.print("\n[green]Working directory clean[/green]")

def _display_processing_summary(summary_info: Dict[str, Any]) -> None:
    """Display processing capabilities summary."""
    format_data(summary_info, "Processing Capabilities")
```

### Step 9: Create spec_cli/cli/commands/help.py

```python
"""Spec help command implementation."""

import click
from typing import Dict, List, Optional
from ...ui.console import get_console
from ...ui.tables import SpecTable
from ..options import spec_command

@spec_command()
@click.argument('command_name', required=False)
def help_command(debug: bool, verbose: bool, command_name: Optional[str]) -> None:
    """Show help information for spec commands.
    
    COMMAND_NAME: Optional specific command to show help for
    """
    console = get_console()
    
    if command_name:
        _display_command_help(command_name)
    else:
        _display_main_help()

def _display_main_help() -> None:
    """Display main help with command overview."""
    console = get_console()
    
    # Header
    console.print("\n[bold cyan]Spec CLI[/bold cyan] - Versioned Documentation for AI-Assisted Development\n")
    console.print("Manage documentation specs for your codebase with Git integration.\n")
    
    # Commands table
    table = SpecTable(title="Available Commands")
    table.add_column("Command", style="yellow", width=12)
    table.add_column("Description", style="white")
    table.add_column("Usage Example", style="dim", width=30)
    
    commands = [
        ("init", "Initialize spec repository", "spec init"),
        ("status", "Show repository status", "spec status"),
        ("help", "Show help information", "spec help [command]"),
    ]
    
    for cmd, desc, example in commands:
        table.add_row(cmd, desc, example)
    
    table.print()
    
    # Footer
    console.print("\nUse [yellow]spec <command> --help[/yellow] for detailed command information.")
    console.print("Use [yellow]spec help <command>[/yellow] for comprehensive command help.\n")

def _display_command_help(command: str) -> None:
    """Display detailed help for a specific command."""
    console = get_console()
    
    help_data = _get_command_help(command)
    
    if not help_data:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("\nAvailable commands: init, status, help")
        return
    
    # Command title
    console.print(f"\n[bold yellow]{command}[/bold yellow] - {help_data['description']}\n")
    
    # Usage
    console.print("[bold]Usage:[/bold]")
    console.print(f"  spec {help_data['usage']}\n")
    
    # Description
    if help_data.get('long_description'):
        console.print("[bold]Description:[/bold]")
        console.print(f"  {help_data['long_description']}\n")
    
    # Options
    if help_data.get('options'):
        options_table = SpecTable(title="Options")
        options_table.add_column("Option", style="yellow")
        options_table.add_column("Description", style="white")
        options_table.add_column("Default", style="dim", width=10)
        
        for opt in help_data['options']:
            default = str(opt.get('default', '')) if opt.get('default') is not None else ''
            options_table.add_row(opt['name'], opt['description'], default)
        
        options_table.print()
        console.print()
    
    # Examples
    if help_data.get('examples'):
        console.print("[bold]Examples:[/bold]")
        for example in help_data['examples']:
            console.print(f"  [dim]# {example['description']}[/dim]")
            console.print(f"  spec {example['command']}\n")

def _get_command_help(command: str) -> Dict:
    """Get help data for a specific command."""
    
    help_data = {
        "init": {
            "description": "Initialize spec repository",
            "usage": "init [options]",
            "long_description": (
                "Initialize a new spec repository in the current directory. "
                "Creates .spec/ and .specs/ directories and sets up Git tracking for documentation."
            ),
            "options": [
                {
                    "name": "--force",
                    "description": "Force initialization even if repository already exists",
                    "default": False
                },
                {
                    "name": "--debug",
                    "description": "Enable debug output and detailed logging",
                    "default": False
                },
                {
                    "name": "--verbose",
                    "description": "Enable verbose output",
                    "default": False
                },
            ],
            "examples": [
                {"description": "Initialize in current directory", "command": "init"},
                {"description": "Force reinitialize", "command": "init --force"},
                {"description": "Initialize with debug output", "command": "init --debug"},
            ]
        },
        "status": {
            "description": "Show repository status",
            "usage": "status [options]",
            "long_description": (
                "Display comprehensive information about the spec repository including "
                "file counts, Git status, and system health checks."
            ),
            "options": [
                {
                    "name": "--health",
                    "description": "Show repository health check instead of regular status",
                    "default": False
                },
                {
                    "name": "--git",
                    "description": "Also show Git repository status",
                    "default": False
                },
                {
                    "name": "--summary",
                    "description": "Show processing capabilities summary",
                    "default": False
                },
                {
                    "name": "--debug",
                    "description": "Enable debug output and detailed logging",
                    "default": False
                },
                {
                    "name": "--verbose",
                    "description": "Enable verbose output",
                    "default": False
                },
            ],
            "examples": [
                {"description": "Show basic repository status", "command": "status"},
                {"description": "Show health check", "command": "status --health"},
                {"description": "Show status with Git information", "command": "status --git"},
                {"description": "Show comprehensive status", "command": "status --health --git --summary"},
            ]
        },
        "help": {
            "description": "Show help information",
            "usage": "help [command]",
            "long_description": (
                "Display help information for spec commands. "
                "Use without arguments to show all commands, or specify a command for detailed help."
            ),
            "examples": [
                {"description": "Show all available commands", "command": "help"},
                {"description": "Show detailed help for init command", "command": "help init"},
                {"description": "Show detailed help for status command", "command": "help status"},
            ]
        },
    }
    
    return help_data.get(command, {})
```

### Step 10: Create spec_cli/cli/app.py

```python
"""Main CLI application with Click framework."""

import sys
import click
from typing import Optional
from ..ui.console import get_console
from ..logging.debug import debug_logger
from .utils import setup_cli_logging, handle_cli_error
from .commands import init_command, status_command, help_command

# Configure rich-click for beautiful help
try:
    import rich_click as click_impl
    click_impl.rich_click.USE_MARKDOWN = True
    click_impl.rich_click.SHOW_ARGUMENTS = True
    click_impl.rich_click.GROUP_ARGUMENTS_OPTIONS = True
except ImportError:
    # Fallback to regular click if rich-click not available
    click_impl = click

@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option(
    '--version',
    is_flag=True,
    help='Show version information'
)
@click.pass_context
def app(ctx: click.Context, version: bool) -> None:
    """Spec CLI - Versioned Documentation for AI-Assisted Development.
    
    Manage documentation specs for your codebase with Git integration.
    
    Examples:
        spec init                    # Initialize repository
        spec status                  # Show repository status
        spec help init               # Get help for init command
    """
    if version:
        click.echo("Spec CLI v0.1.0")
        return
    
    if ctx.invoked_subcommand is None:
        # No subcommand provided, show help
        help_command.callback(False, False, None)

# Add commands to the main group
app.add_command(init_command, name="init")
app.add_command(status_command, name="status")
app.add_command(help_command, name="help")

def main(args: Optional[list] = None) -> None:
    """Main CLI entry point.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
    """
    try:
        # Handle keyboard interrupt gracefully
        app(args=args, standalone_mode=False)
    except KeyboardInterrupt:
        console = get_console()
        console.print_warning("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except click.ClickException as e:
        # Click exceptions are already formatted
        e.show()
        sys.exit(e.exit_code)
    except Exception as e:
        # Handle unexpected errors
        handle_cli_error(e, "CLI execution failed")

if __name__ == '__main__':
    main()
```

### Step 11: Update spec_cli/__main__.py

```python
"""Main entry point for spec CLI when run as module."""

from .cli.app import main

if __name__ == '__main__':
    main()
```

## Test Requirements

Create comprehensive tests for the CLI scaffold:

### Test Cases (14 tests total)

**CLI App Tests:**
1. **test_cli_app_initialization**
2. **test_cli_app_help_display**
3. **test_cli_app_version_display**
4. **test_cli_app_handles_keyboard_interrupt**

**Options Tests:**
5. **test_common_options_applied_correctly**
6. **test_spec_command_decorator_functionality**
7. **test_option_validation_helpers**

**Utils Tests:**
8. **test_cli_error_handling**
9. **test_file_path_validation**
10. **test_cli_logging_setup**
11. **test_repository_access_helpers**

**Command Tests:**
12. **test_init_command_functionality**
13. **test_status_command_functionality**
14. **test_help_command_functionality**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Add Click dependencies
poetry add click rich-click

# Run the specific tests for this slice
poetry run pytest tests/unit/cli/test_app.py tests/unit/cli/test_options.py tests/unit/cli/test_utils.py tests/unit/cli/test_commands/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/cli/ --cov=spec_cli.cli --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/cli/

# Check code formatting
poetry run ruff check spec_cli/cli/
poetry run ruff format spec_cli/cli/

# Verify CLI entry point works
python -m spec_cli --help
python -m spec_cli --version

# Test main commands
python -m spec_cli init --help
python -m spec_cli status --help
python -m spec_cli help init

# Test CLI functionality (in test directory)
cd test_area
python -m spec_cli init
python -m spec_cli status
python -m spec_cli status --health

# Test Click integration
python -c "
from spec_cli.cli.app import app
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ['--help'])
print(f'Help command exit code: {result.exit_code}')
print('CLI integration working correctly')
"

# Test options and decorators
python -c "
from spec_cli.cli.options import debug_option, force_option, spec_command
import click

@spec_command()
@force_option
@debug_option
def test_cmd(debug, verbose, force):
    print(f'Debug: {debug}, Force: {force}')

print('Options and decorators loaded successfully')
"

# Test CLI utilities
python -c "
from spec_cli.cli.utils import validate_file_paths, is_in_spec_repository
from pathlib import Path

# Test path validation
try:
    paths = validate_file_paths(['src/test.py', 'docs/readme.md'])
    print(f'Path validation works: {len(paths)} paths')
except Exception as e:
    print(f'Path validation test: {e}')

# Test repository check
in_repo = is_in_spec_repository()
print(f'Repository check works: {in_repo}')
"
```

## Definition of Done

- [ ] Click/Typer CLI framework with Rich integration
- [ ] Shared CLI options and decorators system
- [ ] Core commands: init, status, help implemented
- [ ] CLI error handling with user-friendly messages
- [ ] Argument validation and path resolution
- [ ] Debug mode and logging integration
- [ ] CLI utilities and helper functions
- [ ] All 14 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Click integration with Rich UI components
- [ ] Foundation ready for generation commands (slice-13B)

## Next Slice Preparation

This slice enables **slice-13b-generate-suite.md** by providing:
- Complete CLI scaffolding with Click framework
- Shared options and validation patterns
- Error handling and user interaction patterns
- Rich UI integration examples
- Foundation for complex command workflows

The CLI scaffold is now complete and ready for the generation command suite.