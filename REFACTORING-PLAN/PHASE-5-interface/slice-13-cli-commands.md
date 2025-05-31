# Slice 13: CLI Commands and User Interface Integration

## Goal

Create the final CLI command interface that integrates all previous systems to provide a comprehensive, user-friendly command-line tool for spec documentation management with Rich UI, complete argument parsing, and intuitive workflows.

## Context

This is the final slice that brings together all previous systems into a cohesive CLI tool. Building on the Rich UI from slice-12 and all processing workflows from previous slices, this creates the complete user interface that developers will interact with. It replaces the current monolithic command structure with a well-organized, feature-rich CLI that provides all functionality through intuitive commands.

## Scope

**Included in this slice:**
- Complete CLI command structure with argparse/click integration
- All main commands: init, add, commit, status, log, diff, gen, regen, show
- Rich UI integration for beautiful command output
- Interactive command workflows with progress tracking
- Help system and command documentation
- Error handling and user-friendly error messages
- Configuration management through CLI
- Integration of all processing workflows and repository operations

**NOT included in this slice:**
- AI content generation implementation (extension points are defined)
- Advanced plugin system (future enhancement)
- Shell completion (future enhancement)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for CLI error handling)
- `spec_cli.logging.debug` (debug_logger for CLI operation tracking)
- `spec_cli.config.settings` (SpecSettings for configuration)
- `spec_cli.core.spec_repository` (SpecRepository for repository operations)
- `spec_cli.processing.file_processor` (FileProcessor for advanced workflows)
- `spec_cli.ui.rich_ui` (RichUI for beautiful terminal output)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration
- `SpecRepository` from slice-10-spec-repository
- `FileProcessor` from slice-11-file-processing
- `RichUI` and `get_rich_ui()` from slice-12-rich-ui

## Files to Create

```
spec_cli/
├── cli/
│   ├── __init__.py             # Module exports
│   ├── main.py                 # Main CLI entry point and argument parsing
│   ├── commands/
│   │   ├── __init__.py         # Command module exports
│   │   ├── init.py             # spec init command
│   │   ├── add.py              # spec add command
│   │   ├── commit.py           # spec commit command
│   │   ├── status.py           # spec status command
│   │   ├── log.py              # spec log command
│   │   ├── diff.py             # spec diff command
│   │   ├── gen.py              # spec gen command
│   │   ├── regen.py            # spec regen command
│   │   └── show.py             # spec show command
│   ├── utils.py                # CLI utility functions
│   └── help.py                 # Help system and documentation
```

## Implementation Steps

### Step 1: Create spec_cli/cli/__init__.py

```python
"""CLI interface for spec CLI.

This package provides the command-line interface with Rich UI integration
and comprehensive command support.
"""

from .main import main, create_parser
from .utils import handle_cli_error, setup_cli_logging

__all__ = [
    "main",
    "create_parser", 
    "handle_cli_error",
    "setup_cli_logging",
]
```

### Step 2: Create spec_cli/cli/utils.py

```python
import sys
from typing import Any, Optional
from rich.console import Console
from ..exceptions import SpecError
from ..logging.debug import debug_logger
from ..ui.rich_ui import get_rich_ui

def handle_cli_error(error: Exception, context: Optional[str] = None, exit_code: int = 1) -> None:
    """Handle CLI errors with appropriate formatting and exit codes.
    
    Args:
        error: Exception that occurred
        context: Optional context information
        exit_code: Exit code to use when exiting
    """
    ui = get_rich_ui()
    
    # Display error using Rich UI
    ui.display_error(error, context)
    
    # Log error for debugging
    debug_logger.log("ERROR", "CLI error occurred", 
                    error=str(error), 
                    error_type=type(error).__name__,
                    context=context)
    
    # Exit with appropriate code
    sys.exit(exit_code)

def setup_cli_logging(debug_mode: bool = False) -> None:
    """Set up CLI logging based on debug mode.
    
    Args:
        debug_mode: Whether debug mode is enabled
    """
    if debug_mode:
        debug_logger.log("INFO", "Debug mode enabled for CLI")
    else:
        # In normal mode, reduce logging verbosity
        pass

def validate_file_paths(file_paths: list) -> list:
    """Validate and normalize file paths from CLI input.
    
    Args:
        file_paths: List of file path strings
        
    Returns:
        List of validated file paths
        
    Raises:
        SpecError: If validation fails
    """
    from pathlib import Path
    from ..exceptions import SpecValidationError
    
    if not file_paths:
        raise SpecValidationError("No file paths provided")
    
    validated_paths = []
    for path_str in file_paths:
        try:
            path = Path(path_str)
            validated_paths.append(str(path))
        except Exception as e:
            raise SpecValidationError(f"Invalid file path '{path_str}': {e}") from e
    
    return validated_paths

def get_user_confirmation(message: str, default: bool = False) -> bool:
    """Get user confirmation with Rich UI.
    
    Args:
        message: Confirmation message
        default: Default value
        
    Returns:
        True if user confirms
    """
    from ..ui.prompts import confirm_action
    return confirm_action(message, default)

def display_operation_progress(operation_name: str, file_count: int):
    """Create a context manager for operation progress display.
    
    Args:
        operation_name: Name of the operation
        file_count: Number of files to process
        
    Returns:
        Progress context manager
    """
    ui = get_rich_ui()
    progress_manager = ui.get_progress_manager()
    
    return progress_manager.progress_context()

def format_command_output(data: Any, format_type: str = "table") -> None:
    """Format and display command output using Rich UI.
    
    Args:
        data: Data to display
        format_type: Format type (table, list, panel)
    """
    ui = get_rich_ui()
    
    if format_type == "table" and isinstance(data, dict):
        if "status" in data:
            ui.display_repository_status(data)
        elif "operation" in data:
            ui.display_operation_results(data)
    elif format_type == "list" and isinstance(data, list):
        ui.display_file_list(data, "Files")
    else:
        # Fallback to simple display
        console = Console()
        console.print(data)
```

### Step 3: Create spec_cli/cli/help.py

```python
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class HelpSystem:
    """Provides comprehensive help and documentation for CLI commands."""
    
    def __init__(self):
        self.console = Console()
    
    def display_main_help(self) -> None:
        """Display main help with command overview."""
        
        # Header
        header_text = """
[bold cyan]Spec CLI[/bold cyan] - Versioned Documentation for AI-Assisted Development

Manage documentation specs for your codebase with Git integration.
        """.strip()
        
        self.console.print(Panel(header_text, border_style="cyan"))
        self.console.print()
        
        # Commands table
        table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="yellow", width=12)
        table.add_column("Description", style="white")
        table.add_column("Usage Example", style="dim", width=30)
        
        commands = [
            ("init", "Initialize spec repository", "spec init"),
            ("add", "Add files to spec tracking", "spec add src/main.py"),
            ("commit", "Commit spec changes", "spec commit -m 'Update docs'"),
            ("status", "Show repository status", "spec status"),
            ("log", "Show commit history", "spec log"),
            ("diff", "Show differences", "spec diff"),
            ("gen", "Generate documentation", "spec gen src/"),
            ("regen", "Regenerate documentation", "spec regen --all"),
            ("show", "Display documentation", "spec show src/main.py"),
        ]
        
        for cmd, desc, example in commands:
            table.add_row(cmd, desc, example)
        
        self.console.print(table)
        self.console.print()
        
        # Footer
        footer_text = """
Use [yellow]spec <command> --help[/yellow] for detailed command information.
Visit the documentation for more examples and advanced usage.
        """.strip()
        
        self.console.print(Panel(footer_text, border_style="blue"))
    
    def display_command_help(self, command: str) -> None:
        """Display detailed help for a specific command."""
        
        help_data = self._get_command_help(command)
        
        if not help_data:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            return
        
        # Command title
        title = f"[bold yellow]{command}[/bold yellow] - {help_data['description']}"
        self.console.print(Panel(title, border_style="yellow"))
        self.console.print()
        
        # Usage
        self.console.print("[bold]Usage:[/bold]")
        self.console.print(f"  spec {help_data['usage']}")
        self.console.print()
        
        # Description
        if help_data.get('long_description'):
            self.console.print("[bold]Description:[/bold]")
            self.console.print(f"  {help_data['long_description']}")
            self.console.print()
        
        # Arguments
        if help_data.get('arguments'):
            args_table = Table(title="Arguments", show_header=True, header_style="bold cyan")
            args_table.add_column("Argument", style="yellow")
            args_table.add_column("Description", style="white")
            args_table.add_column("Required", style="green", width=8)
            
            for arg in help_data['arguments']:
                required = "Yes" if arg.get('required', False) else "No"
                args_table.add_row(arg['name'], arg['description'], required)
            
            self.console.print(args_table)
            self.console.print()
        
        # Options
        if help_data.get('options'):
            opts_table = Table(title="Options", show_header=True, header_style="bold cyan")
            opts_table.add_column("Option", style="yellow")
            opts_table.add_column("Description", style="white")
            opts_table.add_column("Default", style="dim", width=10)
            
            for opt in help_data['options']:
                default = str(opt.get('default', '')) if opt.get('default') is not None else ''
                opts_table.add_row(opt['name'], opt['description'], default)
            
            self.console.print(opts_table)
            self.console.print()
        
        # Examples
        if help_data.get('examples'):
            self.console.print("[bold]Examples:[/bold]")
            for example in help_data['examples']:
                self.console.print(f"  [dim]# {example['description']}[/dim]")
                self.console.print(f"  spec {example['command']}")
                self.console.print()
    
    def _get_command_help(self, command: str) -> Dict:
        """Get help data for a specific command."""
        
        help_data = {
            "init": {
                "description": "Initialize spec repository",
                "usage": "init [options]",
                "long_description": "Initialize a new spec repository in the current directory. Creates .spec/ and .specs/ directories and sets up Git tracking.",
                "options": [
                    {"name": "--force", "description": "Force initialization even if already exists", "default": False},
                ],
                "examples": [
                    {"description": "Initialize in current directory", "command": "init"},
                    {"description": "Force reinitialize", "command": "init --force"},
                ]
            },
            "add": {
                "description": "Add files to spec tracking",
                "usage": "add <files> [options]",
                "long_description": "Add specification files to Git tracking. Files should be in .specs/ directory.",
                "arguments": [
                    {"name": "files", "description": "Files to add (glob patterns supported)", "required": True},
                ],
                "options": [
                    {"name": "--force", "description": "Force add ignored files", "default": False},
                    {"name": "--dry-run", "description": "Show what would be added", "default": False},
                ],
                "examples": [
                    {"description": "Add specific spec file", "command": "add .specs/src/main.py/index.md"},
                    {"description": "Add all spec files", "command": "add .specs/"},
                    {"description": "Force add with dry run", "command": "add .specs/ --force --dry-run"},
                ]
            },
            "gen": {
                "description": "Generate documentation",
                "usage": "gen <files> [options]",
                "long_description": "Generate specification documentation for source files. Creates index.md and history.md files in .specs/ directory structure.",
                "arguments": [
                    {"name": "files", "description": "Source files or directories to document", "required": True},
                ],
                "options": [
                    {"name": "--template", "description": "Template preset to use", "default": "default"},
                    {"name": "--ai", "description": "Enable AI content generation", "default": False},
                    {"name": "--conflict", "description": "Conflict resolution strategy", "default": "backup"},
                    {"name": "--commit", "description": "Auto-commit generated files", "default": False},
                    {"name": "--message", "description": "Commit message", "default": None},
                ],
                "examples": [
                    {"description": "Generate docs for a file", "command": "gen src/main.py"},
                    {"description": "Generate with AI and commit", "command": "gen src/ --ai --commit"},
                    {"description": "Use custom template", "command": "gen src/main.py --template comprehensive"},
                ]
            },
        }
        
        return help_data.get(command, {})

# Global help system instance
_help_system = None

def get_help_system() -> HelpSystem:
    """Get the global help system instance."""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem()
    return _help_system
```

### Step 4: Create spec_cli/cli/commands/__init__.py

```python
"""CLI command implementations.

This package contains all CLI command implementations with Rich UI integration.
"""

from .init import cmd_init
from .add import cmd_add
from .commit import cmd_commit
from .status import cmd_status
from .log import cmd_log
from .diff import cmd_diff
from .gen import cmd_gen
from .regen import cmd_regen
from .show import cmd_show

__all__ = [
    "cmd_init",
    "cmd_add", 
    "cmd_commit",
    "cmd_status",
    "cmd_log",
    "cmd_diff",
    "cmd_gen",
    "cmd_regen",
    "cmd_show",
]
```

### Step 5: Create spec_cli/cli/commands/init.py

```python
import argparse
from typing import List
from ...core.spec_repository import SpecRepository
from ...ui.rich_ui import get_rich_ui
from ...exceptions import SpecOperationError
from ..utils import handle_cli_error

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize spec repository.
    
    Args:
        args: Parsed command line arguments
    """
    ui = get_rich_ui()
    
    try:
        # Create repository instance
        repo = SpecRepository()
        
        # Check if already initialized
        if repo.is_initialized() and not args.force:
            ui.display_warning(
                "Spec repository is already initialized. Use --force to reinitialize.",
                title="Already Initialized"
            )
            return
        
        # Initialize with progress
        ui.display_info("Initializing spec repository...")
        
        with ui.get_progress_manager().progress_context() as progress:
            task = progress.add_task("init", "Initializing repository...", 3)
            
            # Initialize repository
            repo.initialize()
            progress.advance_task("init")
            
            # Update progress
            progress.update_task("init", 3, "Repository initialized successfully")
        
        # Display success
        ui.display_success(
            "Spec repository initialized successfully!\n\n"
            "• Created .spec/ directory for Git repository\n"
            "• Created .specs/ directory for documentation\n"
            "• Updated .gitignore to exclude spec directories\n\n"
            "You can now use 'spec gen' to generate documentation.",
            title="Initialization Complete"
        )
        
    except SpecOperationError as e:
        handle_cli_error(e, "Repository initialization failed")
    except Exception as e:
        handle_cli_error(e, "Unexpected error during initialization")

def add_init_parser(subparsers) -> None:
    """Add init command parser.
    
    Args:
        subparsers: Subparser group to add to
    """
    parser = subparsers.add_parser(
        'init',
        help='Initialize spec repository',
        description='Initialize a new spec repository in the current directory'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force initialization even if repository already exists'
    )
    
    parser.set_defaults(func=cmd_init)
```

### Step 6: Create spec_cli/cli/commands/gen.py

```python
import argparse
from pathlib import Path
from typing import List, Optional
from ...processing.file_processor import FileProcessor
from ...processing.conflict_resolution import ConflictResolutionStrategy
from ...ui.rich_ui import get_rich_ui
from ...ui.prompts import confirm_action, select_option
from ...exceptions import SpecOperationError
from ..utils import handle_cli_error, validate_file_paths

def cmd_gen(args: argparse.Namespace) -> None:
    """Generate spec documentation for files.
    
    Args:
        args: Parsed command line arguments
    """
    ui = get_rich_ui()
    
    try:
        # Validate file paths
        file_paths = validate_file_paths(args.files)
        
        # Create file processor
        processor = FileProcessor()
        
        # Get conflict resolution strategy
        conflict_strategy = _get_conflict_strategy(args.conflict_strategy)
        
        # Check if any files exist that might be processed
        ui.display_info(f"Preparing to generate documentation for {len(file_paths)} files...")
        
        # Interactive template selection if not specified
        template_name = args.template
        if not template_name and args.interactive:
            template_options = ["default", "minimal", "comprehensive"]
            template_name = select_option(
                "Select template preset:",
                template_options,
                default=0,
                title="Template Selection"
            )
        
        # Confirm AI usage if enabled
        ai_enabled = args.ai
        if ai_enabled and args.interactive:
            ai_enabled = confirm_action(
                "AI content generation is enabled. This will attempt to generate "
                "documentation content automatically. Continue?",
                default=True,
                title="AI Content Generation"
            )
        
        # Process files with progress tracking
        with ui.get_progress_manager().progress_context() as progress:
            # Set up progress callback
            progress_callback = progress.setup_batch_progress_callback()
            
            # Configure processor for progress tracking
            processor.batch_processor.set_progress_callback(progress_callback)
            
            # Process files
            result = processor.process_files_for_specs(
                file_paths,
                template_name=template_name,
                ai_enabled=ai_enabled,
                conflict_strategy=conflict_strategy,
                incremental=not args.force,
                commit_changes=args.commit,
                commit_message=args.message
            )
        
        # Display results
        ui.display_operation_results(result)
        
        # Show summary
        if result.get("generation_result", {}).get("generated_files"):
            generated_count = len(result["generation_result"]["generated_files"])
            ui.display_success(
                f"Successfully generated documentation for {generated_count} files.\n\n"
                f"Documentation files created in .specs/ directory.\n"
                f"{'Changes committed to Git.' if args.commit else 'Use \"spec add\" and \"spec commit\" to save changes.'}",
                title="Generation Complete"
            )
        else:
            ui.display_warning(
                "No documentation was generated. This might be because:\n"
                "• Files have not changed (use --force to regenerate)\n"
                "• Conflicts were skipped\n"
                "• Files are not processable",
                title="No Documentation Generated"
            )
    
    except SpecOperationError as e:
        handle_cli_error(e, "Documentation generation failed")
    except Exception as e:
        handle_cli_error(e, "Unexpected error during generation")

def _get_conflict_strategy(strategy_name: str) -> ConflictResolutionStrategy:
    """Convert strategy name to enum."""
    strategy_map = {
        "overwrite": ConflictResolutionStrategy.OVERWRITE,
        "backup": ConflictResolutionStrategy.BACKUP_AND_REPLACE,
        "merge": ConflictResolutionStrategy.MERGE,
        "skip": ConflictResolutionStrategy.SKIP,
        "fail": ConflictResolutionStrategy.FAIL,
    }
    
    return strategy_map.get(strategy_name, ConflictResolutionStrategy.BACKUP_AND_REPLACE)

def add_gen_parser(subparsers) -> None:
    """Add gen command parser.
    
    Args:
        subparsers: Subparser group to add to
    """
    parser = subparsers.add_parser(
        'gen',
        help='Generate documentation for files',
        description='Generate spec documentation for source files'
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='Files or directories to generate documentation for'
    )
    
    parser.add_argument(
        '--template',
        choices=['default', 'minimal', 'comprehensive'],
        default='default',
        help='Template preset to use (default: %(default)s)'
    )
    
    parser.add_argument(
        '--ai',
        action='store_true',
        help='Enable AI content generation'
    )
    
    parser.add_argument(
        '--conflict-strategy',
        choices=['overwrite', 'backup', 'merge', 'skip', 'fail'],
        default='backup',
        help='How to handle existing spec files (default: %(default)s)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force generation even if files have not changed'
    )
    
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Automatically commit generated files'
    )
    
    parser.add_argument(
        '--message', '-m',
        help='Commit message (implies --commit)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Enable interactive prompts for options'
    )
    
    parser.set_defaults(func=cmd_gen)
```

### Step 7: Create spec_cli/cli/commands/status.py

```python
import argparse
from ...core.spec_repository import SpecRepository
from ...ui.rich_ui import get_rich_ui
from ...exceptions import SpecOperationError
from ..utils import handle_cli_error

def cmd_status(args: argparse.Namespace) -> None:
    """Show repository status.
    
    Args:
        args: Parsed command line arguments
    """
    ui = get_rich_ui()
    
    try:
        # Create repository instance
        repo = SpecRepository()
        
        if not repo.is_initialized():
            ui.display_warning(
                "Spec repository is not initialized. Run 'spec init' first.",
                title="Not Initialized"
            )
            return
        
        # Get comprehensive status
        if args.health:
            # Show health check
            health_info = repo.get_repository_health()
            ui.display_health_check(health_info)
        else:
            # Show regular status
            status_info = repo.get_status()
            ui.display_repository_status(status_info)
        
        # Show Git status if requested
        if args.git:
            ui.print_separator("Git Status")
            repo.show_repository_status()
        
        # Show processing summary if requested
        if args.summary:
            from ...processing.file_processor import FileProcessor
            processor = FileProcessor()
            summary = processor.get_processing_summary()
            ui.display_processing_summary(summary)
    
    except SpecOperationError as e:
        handle_cli_error(e, "Status check failed")
    except Exception as e:
        handle_cli_error(e, "Unexpected error during status check")

def add_status_parser(subparsers) -> None:
    """Add status command parser.
    
    Args:
        subparsers: Subparser group to add to
    """
    parser = subparsers.add_parser(
        'status',
        help='Show repository status',
        description='Display spec repository status and statistics'
    )
    
    parser.add_argument(
        '--health',
        action='store_true',
        help='Show repository health check instead of regular status'
    )
    
    parser.add_argument(
        '--git',
        action='store_true',
        help='Also show Git repository status'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show processing capabilities summary'
    )
    
    parser.set_defaults(func=cmd_status)
```

### Step 8: Create spec_cli/cli/main.py

```python
import argparse
import sys
from typing import List, Optional
from ..ui.rich_ui import get_rich_ui
from ..logging.debug import debug_logger
from .utils import handle_cli_error, setup_cli_logging
from .help import get_help_system
from .commands import (
    cmd_init, cmd_add, cmd_commit, cmd_status, 
    cmd_log, cmd_diff, cmd_gen, cmd_regen, cmd_show
)

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    
    parser = argparse.ArgumentParser(
        prog='spec',
        description='Spec CLI - Versioned Documentation for AI-Assisted Development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spec init                    # Initialize repository
  spec gen src/main.py         # Generate docs for file
  spec gen src/ --ai           # Generate with AI content
  spec add .specs/             # Add all spec files
  spec commit -m "Update docs" # Commit changes
  spec status                  # Show status
  spec log                     # Show history

For more help: spec <command> --help
        """
    )
    
    # Global options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        title='Commands',
        description='Available spec commands',
        dest='command',
        help='Command to run'
    )
    
    # Add command parsers
    _add_command_parsers(subparsers)
    
    return parser

def _add_command_parsers(subparsers) -> None:
    """Add all command parsers to subparsers."""
    
    # Import parser functions from command modules
    from .commands.init import add_init_parser
    from .commands.gen import add_gen_parser
    from .commands.status import add_status_parser
    # Add other command parsers as they're implemented
    
    # Add parsers
    add_init_parser(subparsers)
    add_gen_parser(subparsers)
    add_status_parser(subparsers)
    
    # Placeholder parsers for remaining commands
    _add_placeholder_parsers(subparsers)

def _add_placeholder_parsers(subparsers) -> None:
    """Add placeholder parsers for commands not yet fully implemented."""
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add files to spec tracking')
    add_parser.add_argument('files', nargs='+', help='Files to add')
    add_parser.add_argument('--force', action='store_true', help='Force add')
    add_parser.set_defaults(func=cmd_add)
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Commit spec changes')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')
    commit_parser.set_defaults(func=cmd_commit)
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Show commit history')
    log_parser.add_argument('files', nargs='*', help='Files to show log for')
    log_parser.add_argument('--limit', type=int, default=10, help='Limit number of commits')
    log_parser.set_defaults(func=cmd_log)
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Show differences')
    diff_parser.add_argument('files', nargs='*', help='Files to show diff for')
    diff_parser.set_defaults(func=cmd_diff)
    
    # Regen command
    regen_parser = subparsers.add_parser('regen', help='Regenerate documentation')
    regen_parser.add_argument('files', nargs='*', help='Files to regenerate')
    regen_parser.add_argument('--all', action='store_true', help='Regenerate all')
    regen_parser.set_defaults(func=cmd_regen)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Display documentation')
    show_parser.add_argument('files', nargs='+', help='Files to show')
    show_parser.set_defaults(func=cmd_show)

def main(argv: Optional[List[str]] = None) -> None:
    """Main CLI entry point.
    
    Args:
        argv: Command line arguments (uses sys.argv if None)
    """
    parser = create_parser()
    
    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]
    
    # Handle no arguments or help
    if not argv or argv[0] in ['-h', '--help']:
        if not argv:
            # Show main help instead of argument parser help
            get_help_system().display_main_help()
            return
        else:
            parser.print_help()
            return
    
    # Handle command-specific help
    if len(argv) == 2 and argv[1] in ['-h', '--help']:
        get_help_system().display_command_help(argv[0])
        return
    
    args = parser.parse_args(argv)
    
    # Set up logging
    setup_cli_logging(args.debug)
    
    try:
        # Display welcome banner for interactive commands
        if hasattr(args, 'func') and args.command in ['init', 'gen']:
            ui = get_rich_ui()
            if args.command == 'init':
                ui.display_welcome_banner()
        
        # Execute command
        if hasattr(args, 'func'):
            debug_logger.log("INFO", "Executing CLI command", command=args.command)
            args.func(args)
        else:
            # No command specified
            get_help_system().display_main_help()
    
    except KeyboardInterrupt:
        ui = get_rich_ui()
        ui.display_warning("Operation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    
    except Exception as e:
        handle_cli_error(e, f"Command '{args.command}' failed")

if __name__ == '__main__':
    main()
```

### Step 9: Update spec_cli/__main__.py

```python
"""Main entry point for spec CLI when run as module."""

from .cli.main import main

if __name__ == '__main__':
    main()
```

## Test Requirements

Create comprehensive tests for the CLI system:

### Test Cases (25 tests total)

**Main CLI Tests:**
1. **test_cli_main_parses_arguments_correctly**
2. **test_cli_main_handles_no_arguments**
3. **test_cli_main_displays_help_appropriately**
4. **test_cli_main_handles_keyboard_interrupt**
5. **test_cli_main_handles_unknown_commands**

**Command Tests:**
6. **test_cmd_init_initializes_repository**
7. **test_cmd_init_handles_existing_repository**
8. **test_cmd_init_forces_reinitialization**
9. **test_cmd_gen_generates_documentation**
10. **test_cmd_gen_handles_conflict_strategies**
11. **test_cmd_gen_integrates_ai_options**
12. **test_cmd_gen_commits_when_requested**
13. **test_cmd_status_displays_repository_status**
14. **test_cmd_status_shows_health_check**
15. **test_cmd_status_handles_uninitialized_repo**

**CLI Utils Tests:**
16. **test_cli_utils_validates_file_paths**
17. **test_cli_utils_handles_cli_errors**
18. **test_cli_utils_sets_up_logging**
19. **test_cli_utils_gets_user_confirmation**

**Help System Tests:**
20. **test_help_system_displays_main_help**
21. **test_help_system_displays_command_help**
22. **test_help_system_handles_unknown_commands**

**Integration Tests:**
23. **test_cli_integrates_with_rich_ui**
24. **test_cli_integrates_with_processing_workflows**
25. **test_cli_provides_complete_user_workflow**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/cli/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/cli/ --cov=spec_cli.cli --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/cli/

# Check code formatting
poetry run ruff check spec_cli/cli/
poetry run ruff format spec_cli/cli/

# Verify CLI entry point works
python -m spec_cli --help

# Test main commands
python -m spec_cli init --help
python -m spec_cli gen --help
python -m spec_cli status --help

# Test CLI functionality (in test directory)
cd test_area
python -m spec_cli init
python -m spec_cli status
python -m spec_cli gen --help

# Test help system
python -c "
from spec_cli.cli.help import get_help_system

help_system = get_help_system()
print('Help system initialized successfully')

# Test command help data
help_data = help_system._get_command_help('gen')
print(f'Gen command help loaded: {bool(help_data)}')
"

# Test argument parsing
python -c "
from spec_cli.cli.main import create_parser

parser = create_parser()
print('Argument parser created successfully')

# Test parsing sample arguments
args = parser.parse_args(['gen', 'src/main.py', '--template', 'default'])
print(f'Parsed args: {args.command}, {args.files}, {args.template}')
"

# Test CLI utils
python -c "
from spec_cli.cli.utils import validate_file_paths, handle_cli_error

# Test file path validation
try:
    paths = validate_file_paths(['src/test.py', 'docs/readme.md'])
    print(f'File path validation works: {len(paths)} paths')
except Exception as e:
    print(f'Validation test: {e}')

print('CLI utilities loaded successfully')
"

# Test complete CLI workflow (dry run)
python -c "
import sys
from spec_cli.cli.main import main

# Test help display
print('Testing CLI help display...')
try:
    main(['--help'])
except SystemExit:
    pass  # Expected for help

print('CLI main function works correctly')
"
```

## Definition of Done

- [ ] Complete CLI command structure with intuitive argument parsing
- [ ] All main commands implemented: init, add, commit, status, log, diff, gen, regen, show
- [ ] Rich UI integration for beautiful command output and progress tracking
- [ ] Interactive command workflows with user prompts and confirmations
- [ ] Comprehensive help system with command documentation and examples
- [ ] Error handling with user-friendly error messages and appropriate exit codes
- [ ] Integration of all processing workflows and repository operations
- [ ] Configuration management and debug mode support
- [ ] All 25 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Complete user workflow from initialization to documentation generation
- [ ] Entry point integration with proper module execution

## Next Steps

This completes the 13-slice refactoring plan! The CLI now provides:

1. **Complete Architecture**: All 13 slices working together to provide a robust, well-architected spec CLI
2. **Rich User Experience**: Beautiful terminal UI with progress tracking, tables, and interactive prompts
3. **Powerful Processing**: Advanced file processing workflows with batch operations, change detection, and conflict resolution
4. **Git Integration**: Full Git repository management with isolated spec tracking
5. **Template System**: Flexible template system with AI integration extension points
6. **Comprehensive Testing**: 80%+ test coverage across all components
7. **Type Safety**: Full type hints with mypy compliance
8. **Maintainable Code**: Clean architecture with dependency injection and proper separation of concerns

The refactored spec CLI is now ready for production use and future enhancements!