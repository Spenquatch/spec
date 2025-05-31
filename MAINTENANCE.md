# Maintenance Items Vertical Slices - Detailed Plan

This document outlines comprehensive vertical slices for addressing maintenance items, bug fixes, and user experience improvements identified in the README.

## Technology Stack

### Core Libraries
- **Rich**: Terminal styling, colors, and progress bars
- **Click**: Enhanced CLI with better error handling
- **pathlib**: Improved path handling
- **colorama**: Cross-platform terminal colors (fallback)

### Development Libraries
- **pytest-mock**: Enhanced mocking for error scenarios
- **pytest-subprocess**: Testing command-line interactions

## Vertical Slice Breakdown

### Slice 1: Terminal Styling and User Experience Enhancement
**Goal**: Replace all emoji usage and implement comprehensive terminal styling system

**Implementation Details**:
- Remove all emoji characters and replace with text indicators
- Implement Rich-based terminal styling with colors and formatting
- Add progress bars and status indicators
- Create consistent styling theme across all commands
- Ensure compatibility across different terminal types

**Files to Create**:
```
spec_cli/ui/
├── __init__.py           # Public API exports
├── styling.py            # Terminal styling utilities
├── progress.py           # Progress bars and indicators
├── console.py           # Rich console wrapper
├── formatters.py        # Output formatters
└── themes.py            # Color themes and styles
```

**Detailed Implementation**:

**spec_cli/ui/styling.py**:
```python
from rich.console import Console
from rich.theme import Theme
from rich.style import Style
from typing import Optional, Dict, Any

# Define consistent color theme
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
})

class SpecConsole:
    def __init__(self):
        self.console = Console(theme=SPEC_THEME)
        self._emoji_replacements = {
            "✅": "[success]✓[/success]",
            "❌": "[error]✗[/error]",
            "⚠️": "[warning]![/warning]",
            "📝": "[info]→[/info]",
            "📁": "[directory]DIR[/directory]",
            "📄": "[file]FILE[/file]",
            "🔍": "[info]DEBUG[/info]",
            "🚀": "[success]START[/success]",
            "💾": "[info]BACKUP[/info]",
            "🔄": "[warning]OVERWRITE[/warning]",
            "⏭️": "[muted]SKIP[/muted]",
            "🎉": "[success]COMPLETE[/success]",
            "ℹ️": "[info]INFO[/info]",
        }
    
    def print_success(self, message: str, **kwargs) -> None:
        """Print success message with styling."""
        
    def print_error(self, message: str, **kwargs) -> None:
        """Print error message with styling."""
        
    def print_warning(self, message: str, **kwargs) -> None:
        """Print warning message with styling."""
        
    def print_info(self, message: str, **kwargs) -> None:
        """Print info message with styling."""
        
    def replace_emojis(self, text: str) -> str:
        """Replace emoji characters with styled text equivalents."""
```

**spec_cli/ui/progress.py**:
```python
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from typing import Optional, List
from pathlib import Path

class SpecProgress:
    def __init__(self, description: str = "Processing"):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console.console
        )
        self.task_id: Optional[TaskID] = None
        self.description = description
    
    def start(self, total: Optional[int] = None) -> TaskID:
        """Start progress tracking."""
        
    def update(self, advance: int = 1, description: Optional[str] = None) -> None:
        """Update progress."""
        
    def finish(self, message: Optional[str] = None) -> None:
        """Complete progress tracking."""
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

class FileProcessingProgress:
    """Specialized progress tracker for file processing operations."""
    
    def __init__(self, files: List[Path]):
        self.files = files
        self.current_file_index = 0
        self.progress = SpecProgress("Processing files")
    
    def process_file(self, file_path: Path, operation: str) -> None:
        """Update progress for current file being processed."""
        
    def complete_file(self, file_path: Path, success: bool) -> None:
        """Mark file as completed."""
```

**Files to Modify**:
```
spec_cli/__main__.py - Replace all emoji usage with styled text
```

**Detailed Modifications**:

**spec_cli/__main__.py emoji replacements**:
```python
# Before: print("✅ .spec/ initialized")
# After: console.print_success(".spec/ initialized")

# Before: print("❌ Please specify a file or directory to generate specs for")
# After: console.print_error("Please specify a file or directory to generate specs for")

# Before: print(f"📝 Generating spec for file: {resolved_path} (type: {file_type})")
# After: console.print_info(f"Generating spec for file: [path]{resolved_path}[/path] (type: [highlight]{file_type}[/highlight])")

# Before: print("🎉 Directory processing complete!")
# After: console.print_success("Directory processing complete!")
```

**Tests to Write** (22 comprehensive tests):
- `tests/unit/ui/test_styling.py`:
  - `test_spec_console_replaces_all_emoji_characters`
  - `test_spec_console_applies_success_styling`
  - `test_spec_console_applies_error_styling`
  - `test_spec_console_applies_warning_styling`
  - `test_spec_console_applies_info_styling`
  - `test_spec_console_handles_nested_styling`
  - `test_spec_console_works_without_color_support`
  - `test_spec_console_respects_no_color_environment`

- `tests/unit/ui/test_progress.py`:
  - `test_spec_progress_starts_and_updates_correctly`
  - `test_spec_progress_handles_unknown_total`
  - `test_spec_progress_context_manager_works`
  - `test_spec_progress_displays_time_elapsed`
  - `test_file_processing_progress_tracks_multiple_files`
  - `test_file_processing_progress_handles_failures`

- `tests/unit/test_emoji_removal.py`:
  - `test_main_module_contains_no_emoji_characters`
  - `test_all_success_messages_use_styled_console`
  - `test_all_error_messages_use_styled_console`
  - `test_all_warning_messages_use_styled_console`
  - `test_all_info_messages_use_styled_console`
  - `test_progress_indicators_use_rich_components`
  - `test_file_paths_are_highlighted_consistently`
  - `test_counts_and_numbers_are_emphasized`

**Quality Checks**:
```bash
poetry run pytest tests/unit/ui/ tests/unit/test_emoji_removal.py -v --cov=spec_cli.ui --cov-report=term-missing --cov-fail-under=80
poetry run mypy spec_cli/ui/
poetry run ruff check --fix spec_cli/ui/
# Manual verification: grep -r "[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]" spec_cli/ should return no results
```

**Commit**: `feat: implement slice 1 - terminal styling and emoji removal`

### Slice 2: Git Command Message Corrections and User Guidance
**Goal**: Fix Git command suggestions to use spec equivalents and improve user guidance

**Implementation Details**:
- Replace all Git command suggestions with spec equivalents
- Implement context-aware help suggestions
- Add user guidance for common workflows
- Create command translation system for Git to spec commands
- Improve error messages with actionable suggestions

**Files to Create**:
```
spec_cli/help/
├── __init__.py
├── command_suggestions.py
├── workflow_guide.py
├── error_guidance.py
└── examples.py
```

**Detailed Implementation**:

**spec_cli/help/command_suggestions.py**:
```python
from typing import Dict, List, Optional

class CommandTranslator:
    """Translates Git commands to spec equivalents."""
    
    GIT_TO_SPEC_MAPPING = {
        "git add .": "spec add .",
        "git add": "spec add",
        "git commit": "spec commit",
        "git status": "spec status",
        "git log": "spec log",
        "git diff": "spec diff",
        "git init": "spec init",
    }
    
    WORKFLOW_SUGGESTIONS = {
        "new_files": [
            "spec gen <file>  # Generate documentation",
            "spec add .       # Stage documentation",
            "spec commit -m 'Add documentation for new files'"
        ],
        "modified_files": [
            "spec gen <file>  # Regenerate documentation", 
            "spec add .       # Stage changes",
            "spec commit -m 'Update documentation'"
        ],
        "status_check": [
            "spec status      # Check documentation status",
            "spec diff        # Review changes",
            "spec log         # View history"
        ]
    }
    
    def translate_command(self, git_command: str) -> Optional[str]:
        """Translate Git command to spec equivalent."""
        
    def suggest_workflow(self, context: str) -> List[str]:
        """Suggest spec workflow for given context."""
        
    def get_help_for_operation(self, operation: str) -> str:
        """Get detailed help for specific operation."""

class HelpFormatter:
    """Formats help messages and suggestions."""
    
    def __init__(self, console: SpecConsole):
        self.console = console
        self.translator = CommandTranslator()
    
    def format_command_suggestion(self, git_command: str) -> str:
        """Format command suggestion with spec equivalent."""
        
    def format_workflow_help(self, workflow: str) -> str:
        """Format workflow help with steps."""
        
    def create_quick_help(self) -> str:
        """Create quick reference help."""
```

**spec_cli/help/error_guidance.py**:
```python
class ErrorGuidance:
    """Provides contextual guidance for common errors."""
    
    ERROR_GUIDANCE = {
        "not_initialized": {
            "message": "This directory is not initialized as a spec repository.",
            "solutions": [
                "Run 'spec init' to initialize spec in this directory",
                "Navigate to a directory with an existing spec repository",
                "Check if you're in the correct project directory"
            ],
            "example": "cd /path/to/your/project && spec init"
        },
        "no_git_repo": {
            "message": "This directory is not a Git repository.",
            "solutions": [
                "Initialize Git first: git init",
                "Clone an existing repository",
                "Navigate to an existing Git repository"
            ],
            "example": "git init && spec init"
        },
        "permission_denied": {
            "message": "Permission denied accessing files or directories.",
            "solutions": [
                "Check file permissions",
                "Ensure you have write access to the directory",
                "Run with appropriate permissions if needed"
            ],
            "example": "chmod 755 .spec && spec status"
        }
    }
    
    def get_guidance(self, error_type: str) -> Dict[str, Any]:
        """Get guidance for specific error type."""
        
    def format_error_with_guidance(self, error_type: str, console: SpecConsole) -> None:
        """Format and display error with guidance."""
```

**Files to Modify**:
```
spec_cli/__main__.py - Update run_git() and error messages
```

**Detailed Modifications**:

**Modify run_git() to provide better error handling**:
```python
def run_git(args: List[str]) -> None:
    # ... existing code ...
    
    try:
        subprocess.check_call(cmd, env=env)
    except subprocess.CalledProcessError as e:
        # Translate Git error to user-friendly spec guidance
        if "not a git repository" in str(e).lower():
            error_guidance.format_error_with_guidance("not_initialized", console)
            raise SpecNotInitializedError("Spec repository not initialized")
        elif "permission denied" in str(e).lower():
            error_guidance.format_error_with_guidance("permission_denied", console)
            raise SpecPermissionError("Permission denied")
        else:
            raise SpecGitError(f"Git operation failed: {e}")
```

**Add command suggestions to status output**:
```python
def cmd_status(_: List[str]) -> None:
    try:
        run_git(["status"])
        # Add helpful suggestions after status
        console.print_info("\nNext steps:")
        console.print("  spec add .     # Stage documentation changes")
        console.print("  spec commit -m 'message'  # Commit changes")
        console.print("  spec gen <file>  # Generate new documentation")
    except SpecNotInitializedError:
        error_guidance.format_error_with_guidance("not_initialized", console)
```

**Tests to Write** (18 comprehensive tests):
- `tests/unit/help/test_command_suggestions.py`:
  - `test_translator_converts_git_add_to_spec_add`
  - `test_translator_converts_git_status_to_spec_status`
  - `test_translator_converts_git_commit_to_spec_commit`
  - `test_translator_suggests_appropriate_workflows`
  - `test_translator_handles_unknown_commands_gracefully`
  - `test_help_formatter_creates_readable_suggestions`

- `tests/unit/help/test_error_guidance.py`:
  - `test_error_guidance_provides_not_initialized_help`
  - `test_error_guidance_provides_permission_denied_help`
  - `test_error_guidance_provides_no_git_repo_help`
  - `test_error_guidance_formats_solutions_clearly`
  - `test_error_guidance_includes_practical_examples`

- `tests/unit/test_git_message_corrections.py`:
  - `test_status_command_shows_spec_suggestions_not_git`
  - `test_error_messages_suggest_spec_commands`
  - `test_git_errors_provide_spec_context`
  - `test_command_suggestions_are_contextually_appropriate`
  - `test_no_raw_git_commands_in_user_output`
  - `test_workflow_guidance_matches_user_context`
  - `test_help_text_uses_spec_commands_consistently`

**Quality Checks**: 80%+ coverage including error scenarios

**Commit**: `feat: implement slice 2 - Git command message corrections and user guidance`

### Slice 3: Uninitialized Directory Error Handling
**Goal**: Implement proper validation and user-friendly error messages for uninitialized directories

**Implementation Details**:
- Add directory initialization validation to all commands
- Create custom exception hierarchy for spec errors
- Implement early validation before Git operations
- Add helpful guidance for initialization steps
- Provide clear error messages with next steps

**Files to Create**:
```
spec_cli/exceptions.py
spec_cli/validation.py
spec_cli/initialization.py
```

**Detailed Implementation**:

**spec_cli/exceptions.py**:
```python
class SpecError(Exception):
    """Base exception for all spec-related errors."""
    pass

class SpecNotInitializedError(SpecError):
    """Raised when spec operations are attempted in uninitialized directory."""
    
    def __init__(self, message: str = "Spec repository not initialized"):
        self.message = message
        super().__init__(self.message)
    
    def get_guidance(self) -> Dict[str, Any]:
        """Get guidance for resolving this error."""
        return {
            "message": self.message,
            "solutions": [
                "Run 'spec init' to initialize spec in this directory",
                "Navigate to a directory with an existing spec repository", 
                "Verify you're in the correct project directory"
            ],
            "command": "spec init",
            "description": "Initialize spec documentation system"
        }

class SpecPermissionError(SpecError):
    """Raised when permission is denied for spec operations."""
    pass

class SpecGitError(SpecError):
    """Raised when Git operations fail."""
    pass

class SpecConfigurationError(SpecError):
    """Raised when configuration is invalid."""
    pass

class SpecTemplateError(SpecError):
    """Raised when template processing fails."""
    pass
```

**spec_cli/validation.py**:
```python
from pathlib import Path
from typing import Optional, List
from .exceptions import SpecNotInitializedError, SpecPermissionError

class SpecValidator:
    """Validates spec repository state and requirements."""
    
    def __init__(self, root_path: Path = None):
        self.root_path = root_path or Path.cwd()
        self.spec_dir = self.root_path / ".spec"
        self.specs_dir = self.root_path / ".specs"
        self.index_file = self.root_path / ".spec-index"
    
    def validate_initialized(self) -> None:
        """Validate that spec is initialized in current directory."""
        if not self.is_initialized():
            raise SpecNotInitializedError(
                f"Spec not initialized in {self.root_path}. Run 'spec init' first."
            )
    
    def is_initialized(self) -> bool:
        """Check if spec is initialized."""
        return (
            self.spec_dir.exists() and 
            self.spec_dir.is_dir() and
            self.specs_dir.exists() and
            self.specs_dir.is_dir()
        )
    
    def validate_permissions(self) -> None:
        """Validate that we have required permissions."""
        if self.is_initialized():
            if not os.access(self.spec_dir, os.W_OK):
                raise SpecPermissionError(f"No write permission for {self.spec_dir}")
            if not os.access(self.specs_dir, os.W_OK):
                raise SpecPermissionError(f"No write permission for {self.specs_dir}")
    
    def validate_git_repository(self) -> bool:
        """Check if current directory is a Git repository."""
        git_dir = self.root_path / ".git"
        return git_dir.exists()
    
    def get_validation_issues(self) -> List[str]:
        """Get list of validation issues."""
        issues = []
        
        if not self.is_initialized():
            issues.append("Spec not initialized")
        
        if not self.validate_git_repository():
            issues.append("Not a Git repository")
        
        try:
            self.validate_permissions()
        except SpecPermissionError as e:
            issues.append(str(e))
        
        return issues
    
    def create_validation_report(self) -> Dict[str, Any]:
        """Create comprehensive validation report."""
        return {
            "initialized": self.is_initialized(),
            "git_repository": self.validate_git_repository(),
            "spec_dir_exists": self.spec_dir.exists(),
            "specs_dir_exists": self.specs_dir.exists(),
            "has_permissions": self._check_permissions(),
            "issues": self.get_validation_issues()
        }
    
    def _check_permissions(self) -> bool:
        """Check if we have required permissions."""
        try:
            self.validate_permissions()
            return True
        except SpecPermissionError:
            return False
```

**spec_cli/initialization.py**:
```python
class InitializationChecker:
    """Handles initialization checking and guidance."""
    
    def __init__(self, console: SpecConsole):
        self.console = console
        self.validator = SpecValidator()
        self.error_guidance = ErrorGuidance()
    
    def check_and_guide(self, command: str) -> None:
        """Check initialization and provide guidance if needed."""
        if not self.validator.is_initialized():
            self._show_not_initialized_guidance(command)
            raise SpecNotInitializedError()
    
    def _show_not_initialized_guidance(self, command: str) -> None:
        """Show guidance for uninitialized repository."""
        self.console.print_error(f"Cannot run 'spec {command}' - spec not initialized")
        self.console.print("\nTo fix this:")
        self.console.print_info("  1. Initialize spec: spec init")
        self.console.print_info("  2. Then run your command: spec " + command)
        
        if not self.validator.validate_git_repository():
            self.console.print("\nNote: This is not a Git repository.")
            self.console.print_info("  Consider running 'git init' first")
    
    def validate_for_command(self, command: str) -> None:
        """Validate requirements for specific command."""
        validation_map = {
            "add": ["initialized", "permissions"],
            "commit": ["initialized", "permissions"],
            "status": ["initialized"],
            "log": ["initialized"],
            "diff": ["initialized"],
            "gen": ["initialized", "permissions"]
        }
        
        required_validations = validation_map.get(command, ["initialized"])
        
        if "initialized" in required_validations:
            self.validator.validate_initialized()
        
        if "permissions" in required_validations:
            self.validator.validate_permissions()
```

**Files to Modify**:
```
spec_cli/__main__.py - Add validation to all commands
```

**Detailed Modifications**:

**Add validation to command functions**:
```python
def cmd_add(paths: List[str]) -> None:
    # Add validation before Git operations
    checker = InitializationChecker(console)
    checker.validate_for_command("add")
    
    run_git(["add", *paths])
    console.print_success(f"Staged specs: {', '.join(paths)}")

def cmd_status(_: List[str]) -> None:
    checker = InitializationChecker(console)
    checker.validate_for_command("status")
    
    run_git(["status"])

def cmd_gen(args: List[str]) -> None:
    # Add validation at the start
    checker = InitializationChecker(console)
    checker.validate_for_command("gen")
    
    # ... rest of existing cmd_gen code ...
```

**Add early error handling**:
```python
def main(argv: Optional[List[str]] = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] not in COMMANDS:
        print("Usage: spec [init|add|commit|log|diff|status|gen]")
        sys.exit(1)
    
    command = argv[0]
    
    # Skip validation for init command
    if command != "init":
        try:
            # Early validation for all commands except init
            checker = InitializationChecker(console)
            checker.check_and_guide(command)
        except SpecNotInitializedError:
            sys.exit(1)
        except SpecPermissionError as e:
            console.print_error(str(e))
            console.print_info("Check file permissions and try again")
            sys.exit(1)
    
    try:
        COMMANDS[command](argv[1:])
    except (SpecError) as e:
        console.print_error(str(e))
        sys.exit(1)
```

**Tests to Write** (20 comprehensive tests):
- `tests/unit/test_validation.py`:
  - `test_validator_detects_uninitialized_directory`
  - `test_validator_detects_initialized_directory`
  - `test_validator_checks_spec_dir_exists`
  - `test_validator_checks_specs_dir_exists`
  - `test_validator_validates_write_permissions`
  - `test_validator_detects_git_repository`
  - `test_validator_creates_comprehensive_report`

- `tests/unit/test_exceptions.py`:
  - `test_spec_not_initialized_error_provides_guidance`
  - `test_spec_permission_error_includes_path_info`
  - `test_spec_error_hierarchy_inheritance`

- `tests/unit/test_initialization_checker.py`:
  - `test_checker_guides_uninitialized_users`
  - `test_checker_validates_different_commands`
  - `test_checker_shows_git_init_suggestion_when_appropriate`
  - `test_checker_handles_permission_errors`

- `tests/unit/test_command_validation.py`:
  - `test_add_command_validates_initialization`
  - `test_status_command_validates_initialization`
  - `test_gen_command_validates_initialization_and_permissions`
  - `test_init_command_skips_validation`
  - `test_commands_exit_gracefully_on_validation_failure`
  - `test_validation_errors_show_helpful_messages`

**Quality Checks**: 80%+ coverage including all error paths

**Commit**: `feat: implement slice 3 - uninitialized directory error handling`

### Slice 4: Enhanced Error Messages and User Experience
**Goal**: Implement comprehensive error handling with actionable guidance and improved UX

**Implementation Details**:
- Create user-friendly error messages for all common scenarios
- Implement contextual help and suggestions
- Add error recovery suggestions and workflows
- Create comprehensive error logging and debugging support
- Implement graceful degradation and fallback options

**Files to Create**:
```
spec_cli/errors/
├── __init__.py
├── handlers.py
├── recovery.py
├── logging.py
└── user_messages.py
```

**Detailed Implementation**:

**spec_cli/errors/handlers.py**:
```python
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import traceback
import sys

class ErrorHandler:
    """Central error handling with user-friendly messages."""
    
    def __init__(self, console: SpecConsole):
        self.console = console
        self.recovery = ErrorRecovery(console)
        self.message_formatter = UserMessageFormatter(console)
        
        # Map exception types to handlers
        self.handlers: Dict[type, Callable] = {
            SpecNotInitializedError: self._handle_not_initialized,
            SpecPermissionError: self._handle_permission_error,
            FileNotFoundError: self._handle_file_not_found,
            IsADirectoryError: self._handle_is_directory,
            OSError: self._handle_os_error,
            yaml.YAMLError: self._handle_yaml_error,
            subprocess.CalledProcessError: self._handle_subprocess_error,
            KeyboardInterrupt: self._handle_user_interrupt,
        }
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> bool:
        """Handle error with appropriate user message and recovery options."""
        error_type = type(error)
        
        # Find appropriate handler
        handler = self.handlers.get(error_type, self._handle_generic_error)
        
        try:
            return handler(error, context)
        except Exception as handler_error:
            # Fallback if handler itself fails
            self._handle_handler_failure(error, handler_error)
            return False
    
    def _handle_not_initialized(self, error: SpecNotInitializedError, context: str) -> bool:
        """Handle uninitialized repository errors."""
        self.console.print_error("Spec repository not initialized")
        self.console.print()
        self.console.print("This directory doesn't have spec documentation set up yet.")
        self.console.print()
        self.console.print_info("To fix this:")
        self.console.print("  [highlight]spec init[/highlight]  # Initialize spec documentation")
        self.console.print()
        self.console.print("Then try your command again.")
        return True
    
    def _handle_permission_error(self, error: SpecPermissionError, context: str) -> bool:
        """Handle permission denied errors."""
        self.console.print_error("Permission denied")
        self.console.print()
        self.console.print(f"Cannot access required files or directories: {error}")
        self.console.print()
        self.console.print_info("Possible solutions:")
        self.console.print("  • Check file permissions")
        self.console.print("  • Ensure you have write access to the project directory")
        self.console.print("  • Try running with appropriate permissions")
        return True
    
    def _handle_file_not_found(self, error: FileNotFoundError, context: str) -> bool:
        """Handle file not found errors."""
        file_path = str(error).split("'")[1] if "'" in str(error) else "unknown"
        
        self.console.print_error(f"File not found: {file_path}")
        self.console.print()
        
        # Provide context-specific suggestions
        if context == "gen":
            self.console.print_info("Make sure the file path is correct:")
            self.console.print("  • Use relative paths from the project root")
            self.console.print("  • Check file spelling and case sensitivity")
            self.console.print("  • Verify the file exists")
        elif context == "template":
            self.console.print_info("Template file issue:")
            self.console.print("  • Check if .spectemplate file is valid")
            self.console.print("  • Remove .spectemplate to use defaults")
        
        return True
    
    def _handle_yaml_error(self, error: yaml.YAMLError, context: str) -> bool:
        """Handle YAML parsing errors."""
        self.console.print_error("Configuration file error")
        self.console.print()
        self.console.print(f"Invalid YAML syntax: {error}")
        self.console.print()
        self.console.print_info("To fix this:")
        self.console.print("  • Check YAML syntax in configuration files")
        self.console.print("  • Validate indentation (use spaces, not tabs)")
        self.console.print("  • Remove invalid characters or escape them")
        return True
```

**spec_cli/errors/recovery.py**:
```python
class ErrorRecovery:
    """Provides error recovery options and workflows."""
    
    def __init__(self, console: SpecConsole):
        self.console = console
    
    def suggest_recovery_workflow(self, error_type: str, context: str) -> List[str]:
        """Suggest recovery workflow for specific error."""
        workflows = {
            "not_initialized": [
                "spec init",
                "spec gen <your-file>",
                "spec add .",
                "spec commit -m 'Initial documentation'"
            ],
            "permission_error": [
                "chmod 755 .spec/",
                "chmod 755 .specs/",
                "spec status  # Test access"
            ],
            "file_not_found": [
                "ls -la  # Check files exist",
                "spec gen .  # Generate for all files",
                "spec status  # Check results"
            ]
        }
        
        return workflows.get(error_type, [])
    
    def offer_interactive_recovery(self, error_type: str) -> bool:
        """Offer interactive recovery options."""
        if error_type == "not_initialized":
            self.console.print()
            response = input("Would you like me to initialize spec now? [y/N]: ")
            if response.lower() in ['y', 'yes']:
                try:
                    # Import here to avoid circular imports
                    from .. import cmd_init
                    cmd_init([])
                    self.console.print_success("Spec initialized! You can now run your command.")
                    return True
                except Exception as e:
                    self.console.print_error(f"Failed to initialize: {e}")
                    return False
        
        return False
```

**spec_cli/errors/user_messages.py**:
```python
class UserMessageFormatter:
    """Formats user-friendly error messages."""
    
    def __init__(self, console: SpecConsole):
        self.console = console
    
    def format_command_suggestion(self, command: str, description: str) -> str:
        """Format a command suggestion with description."""
        return f"  [highlight]{command}[/highlight]  # {description}"
    
    def format_troubleshooting_section(self, title: str, items: List[str]) -> None:
        """Format a troubleshooting section."""
        self.console.print_info(f"{title}:")
        for item in items:
            self.console.print(f"  • {item}")
    
    def create_error_summary(self, error: Exception, context: str) -> Dict[str, Any]:
        """Create structured error summary."""
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "suggestion": self._get_suggestion_for_error(error, context)
        }
    
    def _get_suggestion_for_error(self, error: Exception, context: str) -> str:
        """Get appropriate suggestion for error."""
        if isinstance(error, SpecNotInitializedError):
            return "Run 'spec init' to initialize spec documentation"
        elif isinstance(error, FileNotFoundError):
            return "Check file path and ensure file exists"
        elif isinstance(error, PermissionError):
            return "Check file permissions and access rights"
        else:
            return "Check the error message and try again"
```

**Files to Modify**:
```
spec_cli/__main__.py - Integrate error handling throughout
```

**Detailed Modifications**:

**Add comprehensive error handling to main()**:
```python
def main(argv: Optional[List[str]] = None) -> None:
    error_handler = ErrorHandler(console)
    
    try:
        argv = argv or sys.argv[1:]
        if not argv or argv[0] not in COMMANDS:
            console.print_error("No command specified")
            console.print()
            console.print_info("Available commands:")
            for cmd in COMMANDS.keys():
                console.print(f"  [highlight]spec {cmd}[/highlight]")
            console.print()
            console.print("For help: [highlight]spec --help[/highlight]")
            sys.exit(1)
        
        command = argv[0]
        
        # Initialize error handling context
        error_context = f"command_{command}"
        
        try:
            COMMANDS[command](argv[1:])
        except Exception as e:
            handled = error_handler.handle_error(e, error_context)
            if not handled:
                # Re-raise if not handled
                raise
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print()
        console.print_warning("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Final fallback error handling
        console.print_error("An unexpected error occurred")
        if DEBUG:
            console.print(f"Error details: {e}")
            console.print(traceback.format_exc())
        else:
            console.print("Run with SPEC_DEBUG=1 for detailed error information")
        sys.exit(1)
```

**Tests to Write** (24 comprehensive tests):
- `tests/unit/errors/test_handlers.py`:
  - `test_error_handler_handles_not_initialized_error`
  - `test_error_handler_handles_permission_error`
  - `test_error_handler_handles_file_not_found_error`
  - `test_error_handler_handles_yaml_error`
  - `test_error_handler_handles_subprocess_error`
  - `test_error_handler_handles_keyboard_interrupt`
  - `test_error_handler_provides_context_specific_guidance`
  - `test_error_handler_falls_back_gracefully`

- `tests/unit/errors/test_recovery.py`:
  - `test_recovery_suggests_appropriate_workflows`
  - `test_recovery_offers_interactive_initialization`
  - `test_recovery_handles_user_declining_help`
  - `test_recovery_validates_recovery_actions`

- `tests/unit/errors/test_user_messages.py`:
  - `test_message_formatter_creates_readable_suggestions`
  - `test_message_formatter_formats_troubleshooting_sections`
  - `test_message_formatter_creates_error_summaries`
  - `test_message_formatter_provides_contextual_help`

- `tests/unit/test_enhanced_error_handling.py`:
  - `test_main_handles_no_command_gracefully`
  - `test_main_handles_invalid_command_gracefully`
  - `test_main_handles_keyboard_interrupt`
  - `test_main_provides_debug_information_when_enabled`
  - `test_command_errors_show_helpful_guidance`
  - `test_error_messages_are_user_friendly`
  - `test_error_handling_preserves_exit_codes`
  - `test_error_recovery_offers_actionable_solutions`

**Quality Checks**: 80%+ coverage including all error scenarios

**Commit**: `feat: implement slice 4 - enhanced error messages and user experience`

## Dependencies to Add

### Core Dependencies
```toml
[tool.poetry.dependencies]
# Terminal styling and UI
rich = "^13.7.0"
click = "^8.1.7"

# Cross-platform color support
colorama = "^0.4.6"
```

### Development Dependencies  
```toml
[tool.poetry.group.dev.dependencies]
# Enhanced testing for UI components
pytest-mock = "^3.12.0"
pytest-subprocess = "^1.5.0"
```

## Quality Standards Summary

### Test Coverage Requirements
- **Total Tests Planned**: 84 comprehensive tests across all slices
- **Overall Coverage**: Minimum 80% per slice
- **UI Coverage**: All styling and formatting components tested
- **Error Path Coverage**: All error scenarios and recovery workflows tested
- **User Experience Coverage**: All user-facing messages and interactions tested

### Performance Requirements
- [ ] Terminal styling adds minimal overhead (< 50ms)
- [ ] Error handling completes quickly (< 100ms)
- [ ] Progress indicators update smoothly
- [ ] Color detection works across terminal types
- [ ] Error recovery options are responsive

### Success Criteria
- [ ] All 4 slices implemented with 80%+ test coverage
- [ ] No emoji characters remain in codebase
- [ ] All error messages provide actionable guidance
- [ ] Terminal styling works across platforms
- [ ] Error handling is comprehensive and user-friendly
- [ ] Git command suggestions use spec equivalents
- [ ] Uninitialized directory errors are caught early
- [ ] User experience is significantly improved