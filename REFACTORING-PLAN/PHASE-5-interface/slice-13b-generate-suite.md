# Slice 13B: Generate Suite

## Goal

Implement the `gen`, `regen`, and `add` commands that delegate to the template engine with focused integration tests for file generation workflows.

## Context

Building on the CLI scaffold from slice-13a, this slice implements the core generation functionality that users will use most frequently. These commands integrate the template system, file processing workflows, and conflict resolution to provide powerful documentation generation capabilities.

## Scope

**Included in this slice:**
- `gen` command for generating new documentation
- `regen` command for regenerating existing documentation
- `add` command for adding files to spec tracking
- Template engine integration and configuration
- File processing workflow coordination
- Conflict resolution strategies and user prompts
- Batch processing with progress tracking
- Integration tests for generation workflows

**NOT included in this slice:**
- Diff and history commands (comes in slice-13C)
- Complex Git operations beyond add/commit
- AI content generation (extension points defined)
- Advanced template customization

## Prerequisites

**Required modules that must exist:**
- `spec_cli.cli.app` (CLI application from slice-13a)
- `spec_cli.cli.options` (Shared CLI options from slice-13a)
- `spec_cli.cli.utils` (CLI utilities from slice-13a)
- `spec_cli.templates.config` (TemplateConfig from slice-7)
- `spec_cli.templates.generator` (SpecGenerator from slice-8b)
- `spec_cli.file_processing.batch_processor` (BatchProcessor from slice-11c)
- `spec_cli.git.repository` (GitRepository from slice-9)

**Required functions/classes:**
- `app`, CLI framework from slice-13a-core-cli-scaffold
- `spec_command`, `files_argument`, `force_option` from slice-13a-core-cli-scaffold
- `TemplateConfig`, `get_template_config()` from slice-7-template-config
- `SpecGenerator` from slice-8b-spec-generator
- `BatchProcessor`, `ConflictResolutionStrategy` from slice-11c-batch-processor
- `GitRepository` from slice-9-git-operations

## Files to Create

```
spec_cli/cli/commands/
├── gen.py              # spec gen command
├── regen.py            # spec regen command
├── add.py              # spec add command
└── generation/
    ├── __init__.py     # Generation utilities
    ├── workflows.py    # Generation workflow coordination
    ├── prompts.py      # Interactive prompts for generation
    └── validation.py   # Generation input validation
```

## Implementation Steps

### Step 1: Create spec_cli/cli/commands/generation/__init__.py

```python
"""Generation command utilities and workflows.

This package provides shared utilities for generation commands including
workflow coordination, user prompts, and validation.
"""

from .workflows import (
    GenerationWorkflow, RegenerationWorkflow, AddWorkflow,
    create_generation_workflow, create_regeneration_workflow, create_add_workflow
)
from .prompts import (
    TemplateSelector, ConflictResolver, GenerationPrompts,
    select_template, resolve_conflicts, confirm_generation
)
from .validation import (
    GenerationValidator, validate_generation_input,
    validate_template_selection, validate_file_paths
)

__all__ = [
    "GenerationWorkflow",
    "RegenerationWorkflow", 
    "AddWorkflow",
    "create_generation_workflow",
    "create_regeneration_workflow",
    "create_add_workflow",
    "TemplateSelector",
    "ConflictResolver",
    "GenerationPrompts",
    "select_template",
    "resolve_conflicts",
    "confirm_generation",
    "GenerationValidator",
    "validate_generation_input",
    "validate_template_selection",
    "validate_file_paths",
]
```

### Step 2: Create spec_cli/cli/commands/generation/workflows.py

```python
"""Generation workflow coordination."""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ....templates.generator import SpecGenerator
from ....file_processing.batch_processor import BatchProcessor, ConflictResolutionStrategy
from ....git.repository import GitRepository
from ....ui.progress_manager import get_progress_manager
from ....ui.formatters import show_message
from ....logging.debug import debug_logger
from ....exceptions import SpecGenerationError, SpecValidationError

@dataclass
class GenerationResult:
    """Result of a generation operation."""
    generated_files: List[Path]
    skipped_files: List[Path]
    failed_files: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    total_processing_time: float
    success: bool
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Get operation summary."""
        return {
            "generated": len(self.generated_files),
            "skipped": len(self.skipped_files),
            "failed": len(self.failed_files),
            "conflicts": len(self.conflicts_resolved),
            "time": f"{self.total_processing_time:.2f}s",
            "success": self.success
        }

class GenerationWorkflow:
    """Coordinates file generation workflow."""
    
    def __init__(self,
                 template_name: str = "default",
                 conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE,
                 auto_commit: bool = False,
                 commit_message: Optional[str] = None):
        """Initialize generation workflow.
        
        Args:
            template_name: Template to use for generation
            conflict_strategy: How to handle existing files
            auto_commit: Whether to automatically commit generated files
            commit_message: Commit message if auto_commit is True
        """
        self.template_name = template_name
        self.conflict_strategy = conflict_strategy
        self.auto_commit = auto_commit
        self.commit_message = commit_message
        
        # Initialize components
        self.generator = SpecGenerator()
        self.batch_processor = BatchProcessor()
        self.git_repo = GitRepository()
        self.progress_manager = get_progress_manager()
        
        debug_logger.log("INFO", "GenerationWorkflow initialized",
                        template=template_name,
                        conflict_strategy=conflict_strategy.value)
    
    def generate(self, source_files: List[Path]) -> GenerationResult:
        """Generate documentation for source files.
        
        Args:
            source_files: List of source files to generate docs for
            
        Returns:
            GenerationResult with operation details
        """
        start_time = time.time()
        generated_files = []
        skipped_files = []
        failed_files = []
        conflicts_resolved = []
        
        try:
            # Validate inputs
            self._validate_generation_inputs(source_files)
            
            # Set up progress tracking
            operation_id = f"generation_{int(time.time())}"
            self.progress_manager.start_indeterminate_operation(
                operation_id,
                f"Generating documentation for {len(source_files)} files"
            )
            
            try:
                # Process each file
                for source_file in source_files:
                    try:
                        result = self._generate_single_file(source_file)
                        
                        if result["generated"]:
                            generated_files.extend(result["files"])
                        elif result["skipped"]:
                            skipped_files.append(source_file)
                        
                        if result["conflicts"]:
                            conflicts_resolved.extend(result["conflicts"])
                        
                        # Update progress
                        self.progress_manager._update_operation_text(
                            operation_id,
                            f"Generated: {source_file.name}"
                        )
                        
                    except Exception as e:
                        failed_files.append({
                            "file": str(source_file),
                            "error": str(e),
                            "error_type": type(e).__name__
                        })
                        debug_logger.log("ERROR", "File generation failed",
                                        file=str(source_file), error=str(e))
                
                # Auto-commit if requested
                if self.auto_commit and generated_files:
                    self._commit_generated_files(generated_files)
                
            finally:
                self.progress_manager.finish_operation(operation_id)
            
            # Create result
            processing_time = time.time() - start_time
            success = len(failed_files) == 0
            
            result = GenerationResult(
                generated_files=generated_files,
                skipped_files=skipped_files,
                failed_files=failed_files,
                conflicts_resolved=conflicts_resolved,
                total_processing_time=processing_time,
                success=success
            )
            
            debug_logger.log("INFO", "Generation completed",
                           **result.summary)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            debug_logger.log("ERROR", "Generation workflow failed", error=str(e))
            
            return GenerationResult(
                generated_files=generated_files,
                skipped_files=skipped_files,
                failed_files=failed_files + [{
                    "file": "workflow",
                    "error": str(e),
                    "error_type": type(e).__name__
                }],
                conflicts_resolved=conflicts_resolved,
                total_processing_time=processing_time,
                success=False
            )
    
    def _validate_generation_inputs(self, source_files: List[Path]) -> None:
        """Validate generation inputs."""
        if not source_files:
            raise SpecValidationError("No source files provided for generation")
        
        # Check template exists
        if not self.generator.template_exists(self.template_name):
            available = self.generator.get_available_templates()
            raise SpecValidationError(
                f"Template '{self.template_name}' not found. "
                f"Available templates: {', '.join(available)}"
            )
        
        # Validate file paths
        for source_file in source_files:
            if not source_file.exists():
                raise SpecValidationError(f"Source file does not exist: {source_file}")
    
    def _generate_single_file(self, source_file: Path) -> Dict[str, Any]:
        """Generate documentation for a single file."""
        try:
            # Check if spec already exists
            spec_files = self.generator.get_spec_files_for_source(source_file)
            conflicts = []
            
            # Handle conflicts if files exist
            if any(f.exists() for f in spec_files.values()):
                conflict_result = self._handle_conflicts(source_file, spec_files)
                
                if conflict_result["skip"]:
                    return {
                        "generated": False,
                        "skipped": True,
                        "files": [],
                        "conflicts": []
                    }
                
                conflicts = conflict_result["resolutions"]
            
            # Generate documentation
            generated_files = self.generator.generate_for_file(
                source_file,
                template_name=self.template_name
            )
            
            return {
                "generated": True,
                "skipped": False,
                "files": generated_files,
                "conflicts": conflicts
            }
            
        except Exception as e:
            debug_logger.log("ERROR", "Single file generation failed",
                           file=str(source_file), error=str(e))
            raise SpecGenerationError(f"Failed to generate docs for {source_file}: {e}") from e
    
    def _handle_conflicts(self, source_file: Path, spec_files: Dict[str, Path]) -> Dict[str, Any]:
        """Handle file conflicts based on strategy."""
        resolutions = []
        
        if self.conflict_strategy == ConflictResolutionStrategy.SKIP:
            return {"skip": True, "resolutions": []}
        
        elif self.conflict_strategy == ConflictResolutionStrategy.FAIL:
            existing_files = [f for f in spec_files.values() if f.exists()]
            raise SpecGenerationError(
                f"Spec files already exist for {source_file}: {existing_files}"
            )
        
        elif self.conflict_strategy == ConflictResolutionStrategy.BACKUP_AND_REPLACE:
            for file_type, spec_file in spec_files.items():
                if spec_file.exists():
                    backup_file = self._create_backup(spec_file)
                    resolutions.append({
                        "type": "backup",
                        "original": str(spec_file),
                        "backup": str(backup_file)
                    })
        
        elif self.conflict_strategy == ConflictResolutionStrategy.OVERWRITE:
            for file_type, spec_file in spec_files.items():
                if spec_file.exists():
                    resolutions.append({
                        "type": "overwrite",
                        "file": str(spec_file)
                    })
        
        return {"skip": False, "resolutions": resolutions}
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of existing file."""
        timestamp = int(time.time())
        backup_path = file_path.with_suffix(f".backup-{timestamp}{file_path.suffix}")
        
        import shutil
        shutil.copy2(file_path, backup_path)
        
        debug_logger.log("INFO", "Backup created",
                        original=str(file_path), backup=str(backup_path))
        
        return backup_path
    
    def _commit_generated_files(self, generated_files: List[Path]) -> None:
        """Commit generated files to Git."""
        try:
            # Add files to Git
            for file_path in generated_files:
                self.git_repo.add_file(file_path)
            
            # Create commit
            message = self.commit_message or f"Generate documentation for {len(generated_files)} files"
            commit_hash = self.git_repo.commit(message)
            
            show_message(
                f"Generated files committed: {commit_hash[:8]}",
                "success"
            )
            
            debug_logger.log("INFO", "Generated files committed",
                           files=len(generated_files), commit=commit_hash)
            
        except Exception as e:
            debug_logger.log("ERROR", "Auto-commit failed", error=str(e))
            show_message(
                f"Generated files successfully, but auto-commit failed: {e}",
                "warning"
            )

class RegenerationWorkflow(GenerationWorkflow):
    """Workflow for regenerating existing documentation."""
    
    def __init__(self, **kwargs):
        """Initialize regeneration workflow."""
        # Default to overwrite for regeneration
        if 'conflict_strategy' not in kwargs:
            kwargs['conflict_strategy'] = ConflictResolutionStrategy.OVERWRITE
        
        super().__init__(**kwargs)
    
    def regenerate(self, source_files: List[Path], preserve_history: bool = True) -> GenerationResult:
        """Regenerate documentation for existing files.
        
        Args:
            source_files: Source files to regenerate docs for
            preserve_history: Whether to preserve history.md files
            
        Returns:
            GenerationResult with operation details
        """
        # Filter to only files that have existing specs
        existing_spec_files = []
        
        for source_file in source_files:
            spec_files = self.generator.get_spec_files_for_source(source_file)
            if any(f.exists() for f in spec_files.values()):
                existing_spec_files.append(source_file)
        
        if not existing_spec_files:
            show_message(
                "No existing spec files found for regeneration",
                "warning"
            )
            return GenerationResult(
                generated_files=[],
                skipped_files=source_files,
                failed_files=[],
                conflicts_resolved=[],
                total_processing_time=0.0,
                success=True
            )
        
        # Preserve history files if requested
        if preserve_history:
            self._preserve_history_files(existing_spec_files)
        
        # Use parent generation method
        return self.generate(existing_spec_files)
    
    def _preserve_history_files(self, source_files: List[Path]) -> None:
        """Preserve history.md files during regeneration."""
        import shutil
        
        for source_file in source_files:
            spec_files = self.generator.get_spec_files_for_source(source_file)
            history_file = spec_files.get('history')
            
            if history_file and history_file.exists():
                temp_file = history_file.with_suffix('.temp')
                shutil.copy2(history_file, temp_file)
                
                debug_logger.log("INFO", "History file preserved",
                               file=str(history_file))

class AddWorkflow:
    """Workflow for adding files to spec tracking."""
    
    def __init__(self, force: bool = False):
        """Initialize add workflow.
        
        Args:
            force: Whether to force add ignored files
        """
        self.force = force
        self.git_repo = GitRepository()
        
        debug_logger.log("INFO", "AddWorkflow initialized", force=force)
    
    def add_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Add files to spec tracking.
        
        Args:
            file_paths: Files to add to tracking
            
        Returns:
            Dictionary with operation results
        """
        added_files = []
        skipped_files = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                # Validate file is in .specs directory
                if not self._is_spec_file(file_path):
                    skipped_files.append({
                        "file": str(file_path),
                        "reason": "Not in .specs directory"
                    })
                    continue
                
                # Add to Git
                self.git_repo.add_file(file_path, force=self.force)
                added_files.append(file_path)
                
                debug_logger.log("INFO", "File added to tracking",
                               file=str(file_path))
                
            except Exception as e:
                failed_files.append({
                    "file": str(file_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                debug_logger.log("ERROR", "Failed to add file",
                               file=str(file_path), error=str(e))
        
        return {
            "added": added_files,
            "skipped": skipped_files,
            "failed": failed_files,
            "success": len(failed_files) == 0
        }
    
    def _is_spec_file(self, file_path: Path) -> bool:
        """Check if file is in .specs directory."""
        try:
            file_path.relative_to(Path(".specs"))
            return True
        except ValueError:
            return False

# Factory functions
def create_generation_workflow(**kwargs) -> GenerationWorkflow:
    """Create a generation workflow with configuration."""
    return GenerationWorkflow(**kwargs)

def create_regeneration_workflow(**kwargs) -> RegenerationWorkflow:
    """Create a regeneration workflow with configuration."""
    return RegenerationWorkflow(**kwargs)

def create_add_workflow(**kwargs) -> AddWorkflow:
    """Create an add workflow with configuration."""
    return AddWorkflow(**kwargs)
```

### Step 3: Create spec_cli/cli/commands/generation/prompts.py

```python
"""Interactive prompts for generation commands."""

import click
from typing import List, Dict, Any, Optional
from pathlib import Path
from ....templates.generator import SpecGenerator
from ....file_processing.batch_processor import ConflictResolutionStrategy
from ....ui.console import get_console
from ....ui.formatters import show_message

class TemplateSelector:
    """Interactive template selection."""
    
    def __init__(self):
        self.generator = SpecGenerator()
        self.console = get_console()
    
    def select_template(self, current_template: Optional[str] = None) -> str:
        """Prompt user to select a template.
        
        Args:
            current_template: Currently selected template
            
        Returns:
            Selected template name
        """
        available_templates = self.generator.get_available_templates()
        
        if not available_templates:
            show_message("No templates available", "error")
            return "default"
        
        # Show template options
        self.console.print("\n[bold cyan]Available Templates:[/bold cyan]")
        for i, template in enumerate(available_templates, 1):
            marker = " (current)" if template == current_template else ""
            description = self._get_template_description(template)
            self.console.print(f"  {i}. [yellow]{template}[/yellow]{marker} - {description}")
        
        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "\nSelect template number",
                    type=int,
                    default=1 if current_template is None else available_templates.index(current_template) + 1
                )
                
                if 1 <= choice <= len(available_templates):
                    selected = available_templates[choice - 1]
                    show_message(f"Selected template: {selected}", "success")
                    return selected
                else:
                    show_message("Invalid selection. Please try again.", "warning")
                    
            except click.Abort:
                # User cancelled (Ctrl+C)
                return current_template or "default"
            except (ValueError, IndexError):
                show_message("Invalid input. Please enter a number.", "warning")
    
    def _get_template_description(self, template_name: str) -> str:
        """Get description for a template."""
        descriptions = {
            "default": "Standard documentation template with index and history",
            "minimal": "Minimal template with basic structure",
            "comprehensive": "Detailed template with extensive sections",
        }
        return descriptions.get(template_name, "Custom template")

class ConflictResolver:
    """Interactive conflict resolution."""
    
    def __init__(self):
        self.console = get_console()
    
    def resolve_conflicts(self, 
                         source_file: Path,
                         existing_files: List[Path],
                         suggested_strategy: ConflictResolutionStrategy) -> ConflictResolutionStrategy:
        """Prompt user to resolve file conflicts.
        
        Args:
            source_file: Source file being processed
            existing_files: Existing spec files that conflict
            suggested_strategy: Suggested resolution strategy
            
        Returns:
            Selected conflict resolution strategy
        """
        self.console.print(f"\n[bold yellow]Conflict detected for {source_file.name}[/bold yellow]")
        self.console.print("Existing spec files:")
        
        for file_path in existing_files:
            self.console.print(f"  • [path]{file_path}[/path]")
        
        # Show resolution options
        options = [
            ("backup", "Create backup and replace (recommended)"),
            ("overwrite", "Overwrite existing files"),
            ("skip", "Skip this file"),
            ("fail", "Stop processing"),
        ]
        
        self.console.print("\n[bold cyan]Resolution options:[/bold cyan]")
        for i, (strategy, description) in enumerate(options, 1):
            marker = " (suggested)" if strategy == suggested_strategy.value.lower() else ""
            self.console.print(f"  {i}. [yellow]{strategy}[/yellow]{marker} - {description}")
        
        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "\nSelect resolution strategy",
                    type=int,
                    default=1  # Default to backup
                )
                
                if 1 <= choice <= len(options):
                    strategy_name = options[choice - 1][0]
                    strategy = self._name_to_strategy(strategy_name)
                    
                    show_message(f"Selected strategy: {strategy_name}", "info")
                    return strategy
                else:
                    show_message("Invalid selection. Please try again.", "warning")
                    
            except click.Abort:
                # User cancelled - default to skip
                return ConflictResolutionStrategy.SKIP
            except (ValueError, IndexError):
                show_message("Invalid input. Please enter a number.", "warning")
    
    def _name_to_strategy(self, name: str) -> ConflictResolutionStrategy:
        """Convert strategy name to enum."""
        mapping = {
            "backup": ConflictResolutionStrategy.BACKUP_AND_REPLACE,
            "overwrite": ConflictResolutionStrategy.OVERWRITE,
            "skip": ConflictResolutionStrategy.SKIP,
            "fail": ConflictResolutionStrategy.FAIL,
        }
        return mapping.get(name, ConflictResolutionStrategy.BACKUP_AND_REPLACE)

class GenerationPrompts:
    """Comprehensive generation prompts."""
    
    def __init__(self):
        self.template_selector = TemplateSelector()
        self.conflict_resolver = ConflictResolver()
        self.console = get_console()
    
    def confirm_generation(self, 
                          source_files: List[Path],
                          template_name: str,
                          conflict_strategy: ConflictResolutionStrategy) -> bool:
        """Confirm generation operation with user.
        
        Args:
            source_files: Files to generate docs for
            template_name: Template to use
            conflict_strategy: Conflict resolution strategy
            
        Returns:
            True if user confirms
        """
        self.console.print("\n[bold cyan]Generation Summary:[/bold cyan]")
        self.console.print(f"  Template: [yellow]{template_name}[/yellow]")
        self.console.print(f"  Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]")
        self.console.print(f"  Files to process: [yellow]{len(source_files)}[/yellow]")
        
        if len(source_files) <= 5:
            self.console.print("\n  Files:")
            for file_path in source_files:
                self.console.print(f"    • [path]{file_path}[/path]")
        else:
            self.console.print("\n  Files:")
            for file_path in source_files[:3]:
                self.console.print(f"    • [path]{file_path}[/path]")
            self.console.print(f"    ... and {len(source_files) - 3} more")
        
        return click.confirm("\nProceed with generation?", default=True)
    
    def get_generation_config(self, 
                             current_template: Optional[str] = None,
                             interactive: bool = True) -> Dict[str, Any]:
        """Get complete generation configuration from user.
        
        Args:
            current_template: Current template selection
            interactive: Whether to show interactive prompts
            
        Returns:
            Dictionary with generation configuration
        """
        config = {}
        
        if interactive:
            # Template selection
            config["template"] = self.template_selector.select_template(current_template)
            
            # Conflict strategy
            conflict_options = [
                ("backup", "Create backup and replace (safest)"),
                ("overwrite", "Overwrite existing files"),
                ("skip", "Skip files with conflicts"),
            ]
            
            self.console.print("\n[bold cyan]Conflict Resolution:[/bold cyan]")
            for i, (strategy, description) in enumerate(conflict_options, 1):
                self.console.print(f"  {i}. [yellow]{strategy}[/yellow] - {description}")
            
            choice = click.prompt(
                "\nSelect conflict resolution strategy",
                type=int,
                default=1
            )
            
            if 1 <= choice <= len(conflict_options):
                strategy_name = conflict_options[choice - 1][0]
                config["conflict_strategy"] = self.conflict_resolver._name_to_strategy(strategy_name)
            else:
                config["conflict_strategy"] = ConflictResolutionStrategy.BACKUP_AND_REPLACE
            
            # Auto-commit option
            config["auto_commit"] = click.confirm(
                "\nAutomatically commit generated files?",
                default=False
            )
            
            if config["auto_commit"]:
                config["commit_message"] = click.prompt(
                    "Commit message",
                    default="Generate documentation",
                    show_default=True
                )
        
        else:
            # Non-interactive defaults
            config["template"] = current_template or "default"
            config["conflict_strategy"] = ConflictResolutionStrategy.BACKUP_AND_REPLACE
            config["auto_commit"] = False
            config["commit_message"] = None
        
        return config

# Convenience functions
def select_template(current_template: Optional[str] = None) -> str:
    """Select template interactively."""
    selector = TemplateSelector()
    return selector.select_template(current_template)

def resolve_conflicts(source_file: Path, 
                     existing_files: List[Path],
                     suggested_strategy: ConflictResolutionStrategy) -> ConflictResolutionStrategy:
    """Resolve conflicts interactively."""
    resolver = ConflictResolver()
    return resolver.resolve_conflicts(source_file, existing_files, suggested_strategy)

def confirm_generation(source_files: List[Path],
                      template_name: str,
                      conflict_strategy: ConflictResolutionStrategy) -> bool:
    """Confirm generation operation."""
    prompts = GenerationPrompts()
    return prompts.confirm_generation(source_files, template_name, conflict_strategy)
```

### Step 4: Create spec_cli/cli/commands/generation/validation.py

```python
"""Generation input validation."""

import click
from typing import List, Dict, Any
from pathlib import Path
from ....templates.generator import SpecGenerator
from ....file_processing.batch_processor import ConflictResolutionStrategy
from ....exceptions import SpecValidationError
from ....logging.debug import debug_logger

class GenerationValidator:
    """Validates generation command inputs."""
    
    def __init__(self):
        self.generator = SpecGenerator()
    
    def validate_generation_input(self,
                                 source_files: List[Path],
                                 template_name: str,
                                 conflict_strategy: ConflictResolutionStrategy) -> Dict[str, Any]:
        """Validate complete generation input.
        
        Args:
            source_files: Source files to validate
            template_name: Template name to validate
            conflict_strategy: Conflict resolution strategy
            
        Returns:
            Validation result with details
            
        Raises:
            SpecValidationError: If validation fails
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_analysis": [],
        }
        
        try:
            # Validate file paths
            file_validation = self.validate_file_paths(source_files)
            validation_result["file_analysis"] = file_validation["analysis"]
            
            if file_validation["errors"]:
                validation_result["errors"].extend(file_validation["errors"])
                validation_result["valid"] = False
            
            if file_validation["warnings"]:
                validation_result["warnings"].extend(file_validation["warnings"])
            
            # Validate template
            template_validation = self.validate_template_selection(template_name)
            if not template_validation["valid"]:
                validation_result["errors"].append(template_validation["error"])
                validation_result["valid"] = False
            
            # Validate conflict strategy
            if not isinstance(conflict_strategy, ConflictResolutionStrategy):
                validation_result["errors"].append(
                    f"Invalid conflict strategy: {conflict_strategy}"
                )
                validation_result["valid"] = False
            
            debug_logger.log("INFO", "Generation input validated",
                           valid=validation_result["valid"],
                           errors=len(validation_result["errors"]),
                           warnings=len(validation_result["warnings"]))
            
            return validation_result
            
        except Exception as e:
            debug_logger.log("ERROR", "Validation failed", error=str(e))
            raise SpecValidationError(f"Validation failed: {e}") from e
    
    def validate_file_paths(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Validate source file paths.
        
        Args:
            file_paths: File paths to validate
            
        Returns:
            Validation result with file analysis
        """
        if not file_paths:
            return {
                "valid": False,
                "errors": ["No source files provided"],
                "warnings": [],
                "analysis": []
            }
        
        errors = []
        warnings = []
        analysis = []
        
        for file_path in file_paths:
            file_info = {
                "path": file_path,
                "exists": file_path.exists(),
                "is_file": file_path.is_file() if file_path.exists() else None,
                "is_directory": file_path.is_dir() if file_path.exists() else None,
                "size": file_path.stat().st_size if file_path.exists() and file_path.is_file() else None,
                "processable": False,
                "existing_specs": {}
            }
            
            # Check existence
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
                file_info["processable"] = False
            
            elif file_path.is_dir():
                # Directory - check if it contains processable files
                processable_files = self._get_processable_files_in_directory(file_path)
                file_info["processable"] = len(processable_files) > 0
                file_info["processable_files"] = processable_files
                
                if not processable_files:
                    warnings.append(f"Directory contains no processable files: {file_path}")
            
            elif file_path.is_file():
                # File - check if processable
                file_info["processable"] = self._is_processable_file(file_path)
                
                if not file_info["processable"]:
                    warnings.append(f"File type may not be processable: {file_path}")
                
                # Check for existing specs
                existing_specs = self.generator.get_spec_files_for_source(file_path)
                existing_files = {k: v for k, v in existing_specs.items() if v.exists()}
                file_info["existing_specs"] = existing_files
                
                if existing_files:
                    warnings.append(
                        f"Existing spec files found for {file_path}: {list(existing_files.keys())}"
                    )
            
            analysis.append(file_info)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "analysis": analysis
        }
    
    def validate_template_selection(self, template_name: str) -> Dict[str, Any]:
        """Validate template selection.
        
        Args:
            template_name: Template name to validate
            
        Returns:
            Validation result
        """
        try:
            available_templates = self.generator.get_available_templates()
            
            if template_name in available_templates:
                return {
                    "valid": True,
                    "template": template_name,
                    "available": available_templates
                }
            else:
                return {
                    "valid": False,
                    "error": (
                        f"Template '{template_name}' not found. "
                        f"Available templates: {', '.join(available_templates)}"
                    ),
                    "available": available_templates
                }
        
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to validate template: {e}",
                "available": []
            }
    
    def _get_processable_files_in_directory(self, directory: Path) -> List[Path]:
        """Get processable files in a directory."""
        processable_files = []
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and self._is_processable_file(file_path):
                    processable_files.append(file_path)
        except Exception as e:
            debug_logger.log("WARNING", "Error scanning directory",
                           directory=str(directory), error=str(e))
        
        return processable_files
    
    def _is_processable_file(self, file_path: Path) -> bool:
        """Check if file is processable for documentation generation."""
        # Common processable file extensions
        processable_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx',
            '.java', '.cpp', '.c', '.h', '.hpp',
            '.rs', '.go', '.rb', '.php', '.cs',
            '.md', '.rst', '.txt'
        }
        
        # Check extension
        if file_path.suffix.lower() not in processable_extensions:
            return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return False
        except Exception:
            return False
        
        # Skip hidden files and common non-source files
        if file_path.name.startswith('.'):
            return False
        
        skip_patterns = ['__pycache__', '.git', 'node_modules', '.venv', 'venv']
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False
        
        return True

# Convenience functions
def validate_generation_input(source_files: List[Path],
                            template_name: str,
                            conflict_strategy: ConflictResolutionStrategy) -> Dict[str, Any]:
    """Validate generation input."""
    validator = GenerationValidator()
    return validator.validate_generation_input(source_files, template_name, conflict_strategy)

def validate_template_selection(template_name: str) -> Dict[str, Any]:
    """Validate template selection."""
    validator = GenerationValidator()
    return validator.validate_template_selection(template_name)

def validate_file_paths(file_paths: List[Path]) -> Dict[str, Any]:
    """Validate file paths for generation."""
    validator = GenerationValidator()
    return validator.validate_file_paths(file_paths)
```

### Step 5: Create spec_cli/cli/commands/gen.py

```python
"""Spec gen command implementation."""

import click
from pathlib import Path
from typing import List
from ...ui.console import get_console
from ...ui.formatters import show_message, format_data
from ...logging.debug import debug_logger
from ..options import spec_command, files_argument, force_option, dry_run_option
from ..utils import validate_file_paths, get_user_confirmation
from .generation import (
    create_generation_workflow, validate_generation_input,
    select_template, confirm_generation
)
from ....file_processing.batch_processor import ConflictResolutionStrategy

@spec_command()
@files_argument
@click.option(
    '--template', '-t',
    default='default',
    help='Template to use for generation'
)
@click.option(
    '--conflict-strategy',
    type=click.Choice(['backup', 'overwrite', 'skip', 'fail']),
    default='backup',
    help='How to handle existing spec files'
)
@click.option(
    '--commit',
    is_flag=True,
    help='Automatically commit generated files'
)
@click.option(
    '--message', '-m',
    help='Commit message (implies --commit)'
)
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help='Enable interactive prompts for configuration'
)
@force_option
@dry_run_option
def gen_command(debug: bool, verbose: bool, files: tuple, template: str,
               conflict_strategy: str, commit: bool, message: str,
               interactive: bool, force: bool, dry_run: bool) -> None:
    """Generate documentation for source files.
    
    Creates spec documentation (index.md and history.md) for the specified
    source files using the selected template. Files can be individual source
    files or directories containing source files.
    
    Examples:
        spec gen src/main.py                    # Generate for single file
        spec gen src/ --template comprehensive  # Generate for directory
        spec gen src/ --interactive             # Interactive configuration
        spec gen src/ --commit -m "Add docs"    # Generate and commit
    """
    console = get_console()
    
    try:
        # Convert and validate file paths
        source_files = validate_file_paths(list(files))
        
        if not source_files:
            raise click.BadParameter("No valid source files provided")
        
        # Expand directories to individual files
        expanded_files = _expand_source_files(source_files)
        
        if not expanded_files:
            show_message("No processable files found in the specified paths", "warning")
            return
        
        show_message(f"Found {len(expanded_files)} files to process", "info")
        
        # Configure conflict strategy
        strategy_map = {
            'backup': ConflictResolutionStrategy.BACKUP_AND_REPLACE,
            'overwrite': ConflictResolutionStrategy.OVERWRITE,
            'skip': ConflictResolutionStrategy.SKIP,
            'fail': ConflictResolutionStrategy.FAIL,
        }
        conflict_enum = strategy_map[conflict_strategy]
        
        # Interactive configuration
        if interactive:
            template = select_template(template)
            
            # Confirm configuration
            if not confirm_generation(expanded_files, template, conflict_enum):
                show_message("Generation cancelled by user", "info")
                return
        
        # Validate inputs
        validation_result = validate_generation_input(
            expanded_files, template, conflict_enum
        )
        
        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                console.print(f"  • [red]{error}[/red]")
            return
        
        # Show warnings if any
        if validation_result["warnings"]:
            show_message("Warnings:", "warning")
            for warning in validation_result["warnings"]:
                console.print(f"  • [yellow]{warning}[/yellow]")
            
            if not force and not get_user_confirmation(
                "Continue despite warnings?", default=True
            ):
                show_message("Generation cancelled", "info")
                return
        
        # Dry run mode
        if dry_run:
            _show_dry_run_preview(expanded_files, template, conflict_enum)
            return
        
        # Set up auto-commit
        auto_commit = commit or bool(message)
        commit_message = message or "Generate documentation" if auto_commit else None
        
        # Create and execute workflow
        workflow = create_generation_workflow(
            template_name=template,
            conflict_strategy=conflict_enum,
            auto_commit=auto_commit,
            commit_message=commit_message
        )
        
        show_message(f"Generating documentation using '{template}' template...", "info")
        
        result = workflow.generate(expanded_files)
        
        # Display results
        _display_generation_results(result)
        
        debug_logger.log("INFO", "Generation command completed",
                        files=len(expanded_files),
                        success=result.success)
        
    except click.BadParameter as e:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Generation command failed", error=str(e))
        raise click.ClickException(f"Generation failed: {e}")

def _expand_source_files(source_files: List[Path]) -> List[Path]:
    """Expand directories to individual source files."""
    from .generation.validation import GenerationValidator
    
    validator = GenerationValidator()
    expanded_files = []
    
    for file_path in source_files:
        if file_path.is_file():
            if validator._is_processable_file(file_path):
                expanded_files.append(file_path)
        elif file_path.is_dir():
            processable_files = validator._get_processable_files_in_directory(file_path)
            expanded_files.extend(processable_files)
    
    return expanded_files

def _show_dry_run_preview(source_files: List[Path],
                         template: str,
                         conflict_strategy: ConflictResolutionStrategy) -> None:
    """Show dry run preview of what would be generated."""
    from ....templates.generator import SpecGenerator
    
    console = get_console()
    generator = SpecGenerator()
    
    console.print("\n[bold cyan]Dry Run Preview:[/bold cyan]")
    console.print(f"Template: [yellow]{template}[/yellow]")
    console.print(f"Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]")
    console.print(f"Files to process: [yellow]{len(source_files)}[/yellow]\n")
    
    for source_file in source_files:
        spec_files = generator.get_spec_files_for_source(source_file)
        
        console.print(f"[bold]{source_file}[/bold]")
        for file_type, spec_file in spec_files.items():
            status = "[yellow]exists[/yellow]" if spec_file.exists() else "[green]new[/green]"
            console.print(f"  • {file_type}: [path]{spec_file}[/path] ({status})")
        console.print()
    
    show_message("This is a dry run. No files would be modified.", "info")

def _display_generation_results(result) -> None:
    """Display generation results."""
    from ....ui.tables import StatusTable
    
    console = get_console()
    
    # Show summary
    if result.success:
        show_message(
            f"Generation completed successfully in {result.total_processing_time:.2f}s",
            "success"
        )
    else:
        show_message(
            f"Generation completed with errors in {result.total_processing_time:.2f}s",
            "warning"
        )
    
    # Show statistics table
    stats_table = StatusTable("Generation Statistics")
    stats_table.add_status("Generated files", str(len(result.generated_files)), 
                          status_type="success" if result.generated_files else "info")
    stats_table.add_status("Skipped files", str(len(result.skipped_files)),
                          status_type="warning" if result.skipped_files else "info")
    stats_table.add_status("Failed files", str(len(result.failed_files)),
                          status_type="error" if result.failed_files else "info")
    stats_table.add_status("Conflicts resolved", str(len(result.conflicts_resolved)),
                          status_type="info")
    stats_table.print()
    
    # Show generated files
    if result.generated_files:
        console.print("\n[bold green]Generated files:[/bold green]")
        for file_path in result.generated_files:
            console.print(f"  • [path]{file_path}[/path]")
    
    # Show failed files
    if result.failed_files:
        console.print("\n[bold red]Failed files:[/bold red]")
        for failure in result.failed_files:
            console.print(f"  • [path]{failure['file']}[/path]: {failure['error']}")
    
    # Show conflicts
    if result.conflicts_resolved:
        console.print("\n[bold yellow]Conflicts resolved:[/bold yellow]")
        for conflict in result.conflicts_resolved:
            if conflict["type"] == "backup":
                console.print(f"  • Backed up [path]{conflict['original']}[/path] to [path]{conflict['backup']}[/path]")
            elif conflict["type"] == "overwrite":
                console.print(f"  • Overwrote [path]{conflict['file']}[/path]")
```

### Step 6: Create spec_cli/cli/commands/regen.py

```python
"""Spec regen command implementation."""

import click
from pathlib import Path
from typing import List
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...logging.debug import debug_logger
from ..options import spec_command, optional_files_argument, force_option, dry_run_option
from ..utils import validate_file_paths, get_user_confirmation
from .generation import create_regeneration_workflow, validate_generation_input
from ....file_processing.batch_processor import ConflictResolutionStrategy

@spec_command()
@optional_files_argument
@click.option(
    '--all',
    is_flag=True,
    help='Regenerate all existing spec files'
)
@click.option(
    '--template', '-t',
    help='Template to use for regeneration (keeps existing if not specified)'
)
@click.option(
    '--preserve-history',
    is_flag=True,
    default=True,
    help='Preserve history.md files during regeneration'
)
@click.option(
    '--commit',
    is_flag=True,
    help='Automatically commit regenerated files'
)
@click.option(
    '--message', '-m',
    help='Commit message (implies --commit)'
)
@force_option
@dry_run_option
def regen_command(debug: bool, verbose: bool, files: tuple, all: bool,
                 template: str, preserve_history: bool, commit: bool,
                 message: str, force: bool, dry_run: bool) -> None:
    """Regenerate existing spec documentation.
    
    Updates existing spec files with fresh content while preserving history.
    Can target specific files or regenerate all existing specs.
    
    Examples:
        spec regen                           # Regenerate all specs
        spec regen src/main.py               # Regenerate specific file
        spec regen --template comprehensive  # Use different template
        spec regen --no-preserve-history     # Recreate history files
    """
    console = get_console()
    
    try:
        # Determine source files
        if all:
            if files:
                raise click.BadParameter("Cannot specify both --all and file paths")
            source_files = _find_all_spec_sources()
        elif files:
            source_files = validate_file_paths(list(files))
        else:
            # Default to all if no files specified
            source_files = _find_all_spec_sources()
        
        if not source_files:
            show_message("No source files with existing specs found", "warning")
            return
        
        # Filter to only files with existing specs
        files_with_specs = _filter_files_with_specs(source_files)
        
        if not files_with_specs:
            show_message("No existing spec files found for regeneration", "warning")
            if not all:
                show_message("Use 'spec gen' to create new documentation", "info")
            return
        
        show_message(f"Found {len(files_with_specs)} files with existing specs", "info")
        
        # Use default template if not specified
        if not template:
            template = "default"
        
        # Regeneration always overwrites (that's the point)
        conflict_strategy = ConflictResolutionStrategy.OVERWRITE
        
        # Validate inputs
        validation_result = validate_generation_input(
            files_with_specs, template, conflict_strategy
        )
        
        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                console.print(f"  • [red]{error}[/red]")
            return
        
        # Show what will be regenerated
        console.print(f"\n[bold cyan]Regeneration Preview:[/bold cyan]")
        console.print(f"Template: [yellow]{template}[/yellow]")
        console.print(f"Preserve history: [yellow]{preserve_history}[/yellow]")
        console.print(f"Files to regenerate: [yellow]{len(files_with_specs)}[/yellow]")
        
        if len(files_with_specs) <= 10:
            console.print("\nFiles:")
            for file_path in files_with_specs:
                console.print(f"  • [path]{file_path}[/path]")
        else:
            console.print("\nFiles:")
            for file_path in files_with_specs[:5]:
                console.print(f"  • [path]{file_path}[/path]")
            console.print(f"  ... and {len(files_with_specs) - 5} more")
        
        # Confirmation
        if not force and not dry_run:
            if not get_user_confirmation(
                "\nProceed with regeneration? This will overwrite existing content.",
                default=False
            ):
                show_message("Regeneration cancelled", "info")
                return
        
        # Dry run mode
        if dry_run:
            _show_regen_dry_run_preview(files_with_specs, template, preserve_history)
            return
        
        # Set up auto-commit
        auto_commit = commit or bool(message)
        commit_message = message or "Regenerate documentation" if auto_commit else None
        
        # Create and execute workflow
        workflow = create_regeneration_workflow(
            template_name=template,
            conflict_strategy=conflict_strategy,
            auto_commit=auto_commit,
            commit_message=commit_message
        )
        
        show_message(f"Regenerating documentation using '{template}' template...", "info")
        
        result = workflow.regenerate(files_with_specs, preserve_history=preserve_history)
        
        # Display results (reuse from gen command)
        from .gen import _display_generation_results
        _display_generation_results(result)
        
        debug_logger.log("INFO", "Regeneration command completed",
                        files=len(files_with_specs),
                        success=result.success)
        
    except click.BadParameter as e:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Regeneration command failed", error=str(e))
        raise click.ClickException(f"Regeneration failed: {e}")

def _find_all_spec_sources() -> List[Path]:
    """Find all source files that have existing specs."""
    from ....templates.generator import SpecGenerator
    
    generator = SpecGenerator()
    source_files = []
    specs_dir = Path(".specs")
    
    if not specs_dir.exists():
        return []
    
    # Find all index.md files and derive source paths
    for index_file in specs_dir.rglob("index.md"):
        try:
            # Convert spec path back to source path
            relative_path = index_file.parent.relative_to(specs_dir)
            potential_source = Path(relative_path)
            
            if potential_source.exists():
                source_files.append(potential_source)
        except (ValueError, OSError):
            # Skip invalid paths
            continue
    
    return source_files

def _filter_files_with_specs(source_files: List[Path]) -> List[Path]:
    """Filter files to only those with existing specs."""
    from ....templates.generator import SpecGenerator
    
    generator = SpecGenerator()
    files_with_specs = []
    
    for source_file in source_files:
        spec_files = generator.get_spec_files_for_source(source_file)
        if any(f.exists() for f in spec_files.values()):
            files_with_specs.append(source_file)
    
    return files_with_specs

def _show_regen_dry_run_preview(source_files: List[Path],
                               template: str,
                               preserve_history: bool) -> None:
    """Show dry run preview of regeneration."""
    from ....templates.generator import SpecGenerator
    
    console = get_console()
    generator = SpecGenerator()
    
    console.print("\n[bold cyan]Regeneration Dry Run Preview:[/bold cyan]")
    console.print(f"Template: [yellow]{template}[/yellow]")
    console.print(f"Preserve history: [yellow]{preserve_history}[/yellow]")
    console.print(f"Files to regenerate: [yellow]{len(source_files)}[/yellow]\n")
    
    for source_file in source_files:
        spec_files = generator.get_spec_files_for_source(source_file)
        
        console.print(f"[bold]{source_file}[/bold]")
        for file_type, spec_file in spec_files.items():
            if spec_file.exists():
                if file_type == "history" and preserve_history:
                    action = "[green]preserve[/green]"
                else:
                    action = "[yellow]regenerate[/yellow]"
                console.print(f"  • {file_type}: [path]{spec_file}[/path] ({action})")
        console.print()
    
    show_message("This is a dry run. No files would be modified.", "info")
```

### Step 7: Create spec_cli/cli/commands/add.py

```python
"""Spec add command implementation."""

import click
from pathlib import Path
from typing import List
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...ui.tables import StatusTable
from ...logging.debug import debug_logger
from ..options import spec_command, files_argument, force_option, dry_run_option
from ..utils import validate_file_paths, get_spec_repository
from .generation import create_add_workflow

@spec_command()
@files_argument
@force_option
@dry_run_option
def add_command(debug: bool, verbose: bool, files: tuple,
               force: bool, dry_run: bool) -> None:
    """Add spec files to Git tracking.
    
    Adds specification files to the spec repository for version control.
    Files must be in the .specs/ directory to be added.
    
    Examples:
        spec add .specs/src/main.py/index.md  # Add specific spec file
        spec add .specs/                      # Add all spec files
        spec add .specs/ --force              # Force add ignored files
        spec add .specs/ --dry-run            # Preview what would be added
    """
    console = get_console()
    
    try:
        # Validate we're in a spec repository
        repo = get_spec_repository()
        
        # Convert and validate file paths
        file_paths = validate_file_paths(list(files))
        
        if not file_paths:
            raise click.BadParameter("No valid file paths provided")
        
        # Expand directories to individual files
        expanded_files = _expand_spec_files(file_paths)
        
        if not expanded_files:
            show_message("No spec files found in the specified paths", "warning")
            return
        
        # Filter to only spec files
        spec_files = _filter_spec_files(expanded_files)
        
        if not spec_files:
            show_message(
                "No files in .specs/ directory found. Use 'spec gen' to create documentation first.",
                "warning"
            )
            return
        
        show_message(f"Found {len(spec_files)} spec files to add", "info")
        
        # Check Git status for these files
        git_status = _analyze_git_status(spec_files, repo)
        
        # Show preview
        _show_add_preview(git_status, dry_run)
        
        # Dry run mode
        if dry_run:
            show_message("This is a dry run. No files would be added.", "info")
            return
        
        # Filter to only files that need to be added
        files_to_add = git_status["untracked"] + git_status["modified"]
        
        if not files_to_add:
            show_message("All specified files are already tracked and up to date", "info")
            return
        
        # Create and execute workflow
        workflow = create_add_workflow(force=force)
        
        show_message(f"Adding {len(files_to_add)} files to spec repository...", "info")
        
        result = workflow.add_files(files_to_add)
        
        # Display results
        _display_add_results(result)
        
        debug_logger.log("INFO", "Add command completed",
                        files=len(files_to_add),
                        success=result["success"])
        
    except click.BadParameter as e:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Add command failed", error=str(e))
        raise click.ClickException(f"Add failed: {e}")

def _expand_spec_files(file_paths: List[Path]) -> List[Path]:
    """Expand directories to individual files."""
    expanded_files = []
    
    for file_path in file_paths:
        if file_path.is_file():
            expanded_files.append(file_path)
        elif file_path.is_dir():
            # Find all files in directory
            for child_file in file_path.rglob("*"):
                if child_file.is_file():
                    expanded_files.append(child_file)
    
    return expanded_files

def _filter_spec_files(file_paths: List[Path]) -> List[Path]:
    """Filter to only files in .specs directory."""
    spec_files = []
    specs_dir = Path(".specs")
    
    for file_path in file_paths:
        try:
            # Check if file is in .specs directory
            file_path.relative_to(specs_dir)
            spec_files.append(file_path)
        except ValueError:
            # File is not in .specs directory
            continue
    
    return spec_files

def _analyze_git_status(spec_files: List[Path], repo) -> dict:
    """Analyze Git status for spec files."""
    git_status = {
        "untracked": [],
        "modified": [],
        "staged": [],
        "up_to_date": []
    }
    
    try:
        # Get overall Git status
        status = repo.get_git_status()
        
        # Categorize our files
        for file_path in spec_files:
            file_str = str(file_path)
            
            if file_str in status.get("untracked", []):
                git_status["untracked"].append(file_path)
            elif file_str in status.get("modified", []):
                git_status["modified"].append(file_path)
            elif file_str in status.get("staged", []):
                git_status["staged"].append(file_path)
            else:
                git_status["up_to_date"].append(file_path)
    
    except Exception as e:
        debug_logger.log("WARNING", "Failed to get Git status", error=str(e))
        # If we can't get status, assume all files are untracked
        git_status["untracked"] = spec_files
    
    return git_status

def _show_add_preview(git_status: dict, is_dry_run: bool = False) -> None:
    """Show preview of files to be added."""
    console = get_console()
    
    title = "Add Preview (Dry Run)" if is_dry_run else "Files to Add"
    table = StatusTable(title)
    
    # Add status entries
    if git_status["untracked"]:
        table.add_status(
            "New files",
            str(len(git_status["untracked"])),
            "Will be added to tracking",
            "success"
        )
    
    if git_status["modified"]:
        table.add_status(
            "Modified files",
            str(len(git_status["modified"])),
            "Changes will be staged",
            "info"
        )
    
    if git_status["staged"]:
        table.add_status(
            "Already staged",
            str(len(git_status["staged"])),
            "No action needed",
            "info"
        )
    
    if git_status["up_to_date"]:
        table.add_status(
            "Up to date",
            str(len(git_status["up_to_date"])),
            "No changes to add",
            "info"
        )
    
    table.print()
    
    # Show file details for small lists
    total_to_add = len(git_status["untracked"]) + len(git_status["modified"])
    if total_to_add > 0 and total_to_add <= 10:
        console.print("\n[bold cyan]Files to be added:[/bold cyan]")
        
        for file_path in git_status["untracked"]:
            console.print(f"  [green]A[/green] [path]{file_path}[/path] (new file)")
        
        for file_path in git_status["modified"]:
            console.print(f"  [yellow]M[/yellow] [path]{file_path}[/path] (modified)")

def _display_add_results(result: dict) -> None:
    """Display add operation results."""
    console = get_console()
    
    # Show summary
    if result["success"]:
        show_message(
            f"Successfully added {len(result['added'])} files to spec repository",
            "success"
        )
    else:
        show_message(
            f"Add completed with {len(result['failed'])} failures",
            "warning"
        )
    
    # Show statistics
    stats_table = StatusTable("Add Results")
    stats_table.add_status(
        "Added files",
        str(len(result["added"])),
        status_type="success" if result["added"] else "info"
    )
    stats_table.add_status(
        "Skipped files",
        str(len(result["skipped"])),
        status_type="warning" if result["skipped"] else "info"
    )
    stats_table.add_status(
        "Failed files",
        str(len(result["failed"])),
        status_type="error" if result["failed"] else "info"
    )
    stats_table.print()
    
    # Show added files
    if result["added"]:
        console.print("\n[bold green]Added files:[/bold green]")
        for file_path in result["added"]:
            console.print(f"  • [path]{file_path}[/path]")
    
    # Show skipped files
    if result["skipped"]:
        console.print("\n[bold yellow]Skipped files:[/bold yellow]")
        for skip_info in result["skipped"]:
            console.print(f"  • [path]{skip_info['file']}[/path]: {skip_info['reason']}")
    
    # Show failed files
    if result["failed"]:
        console.print("\n[bold red]Failed files:[/bold red]")
        for failure in result["failed"]:
            console.print(f"  • [path]{failure['file']}[/path]: {failure['error']}")
    
    # Next steps
    if result["added"]:
        console.print("\n[bold cyan]Next steps:[/bold cyan]")
        console.print("  Use [yellow]spec commit -m 'message'[/yellow] to commit these changes")
```

### Step 8: Update spec_cli/cli/app.py

```python
"""Main CLI application with Click framework."""

# Add imports for new commands
from .commands import init_command, status_command, help_command
from .commands.gen import gen_command
from .commands.regen import regen_command
from .commands.add import add_command

# Add commands to the main group (after existing commands)
app.add_command(gen_command, name="gen")
app.add_command(regen_command, name="regen")
app.add_command(add_command, name="add")

# (rest of the file remains the same)
```

## Test Requirements

Create focused integration tests for generation commands:

### Test Cases (16 tests total)

**Generation Workflow Tests:**
1. **test_generation_workflow_creates_spec_files**
2. **test_generation_workflow_handles_conflicts**
3. **test_generation_workflow_auto_commits_when_requested**
4. **test_regeneration_workflow_preserves_history**

**Gen Command Tests:**
5. **test_gen_command_generates_single_file**
6. **test_gen_command_generates_directory**
7. **test_gen_command_interactive_template_selection**
8. **test_gen_command_dry_run_preview**

**Regen Command Tests:**
9. **test_regen_command_regenerates_existing_specs**
10. **test_regen_command_finds_all_specs_automatically**
11. **test_regen_command_preserves_history_by_default**
12. **test_regen_command_handles_no_existing_specs**

**Add Command Tests:**
13. **test_add_command_adds_spec_files_to_git**
14. **test_add_command_filters_non_spec_files**
15. **test_add_command_handles_git_status_correctly**
16. **test_add_command_force_adds_ignored_files**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/cli/commands/test_gen.py tests/unit/cli/commands/test_regen.py tests/unit/cli/commands/test_add.py tests/unit/cli/commands/generation/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/cli/commands/ --cov=spec_cli.cli.commands --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/cli/commands/

# Check code formatting
poetry run ruff check spec_cli/cli/commands/
poetry run ruff format spec_cli/cli/commands/

# Test generation commands
python -m spec_cli gen --help
python -m spec_cli regen --help
python -m spec_cli add --help

# Test CLI functionality (in test directory)
cd test_area
python -m spec_cli init
echo "print('hello')" > test.py
python -m spec_cli gen test.py --dry-run
python -m spec_cli gen test.py
python -m spec_cli add .specs/
python -m spec_cli regen --dry-run

# Test generation workflows
python -c "
from spec_cli.cli.commands.generation import create_generation_workflow
from pathlib import Path

# Test workflow creation
workflow = create_generation_workflow(template_name='default')
print(f'Generation workflow created: {workflow.template_name}')

# Test validation
from spec_cli.cli.commands.generation.validation import validate_file_paths
result = validate_file_paths([Path('test.py')])
print(f'File validation works: {result["valid"]}')
"

# Test template integration
python -c "
from spec_cli.cli.commands.generation.prompts import TemplateSelector

selector = TemplateSelector()
available = selector.generator.get_available_templates()
print(f'Available templates: {available}')
"

# Test conflict resolution
python -c "
from spec_cli.cli.commands.generation.workflows import GenerationWorkflow
from spec_cli.file_processing.batch_processor import ConflictResolutionStrategy

workflow = GenerationWorkflow(
    conflict_strategy=ConflictResolutionStrategy.BACKUP_AND_REPLACE
)
print(f'Workflow configured with conflict strategy: {workflow.conflict_strategy.value}')
"
```

## Definition of Done

- [ ] Generation workflow coordination with template integration
- [ ] Gen command for new documentation generation
- [ ] Regen command for existing documentation regeneration
- [ ] Add command for Git tracking integration
- [ ] Interactive prompts for template and conflict resolution
- [ ] Comprehensive input validation and error handling
- [ ] Batch processing with progress tracking
- [ ] Dry run functionality for all commands
- [ ] All 16 integration tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Complete CLI workflow from generation to Git tracking

## Next Slice Preparation

This slice enables **slice-13c-diff-history-suite.md** by providing:
- Complete generation command infrastructure
- File tracking and Git integration patterns
- Workflow coordination examples
- Error handling and validation patterns
- Rich UI integration for command output

The generation suite is now complete and ready for the diff and history commands.