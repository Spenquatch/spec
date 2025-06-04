"""Gen command implementation using BaseCommand."""

from pathlib import Path
from typing import Any

from ...config.settings import SpecSettings
from ...exceptions import SpecError
from ...file_processing.conflict_resolver import ConflictResolutionStrategy
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..base_command import BaseCommand
from ..utils import get_user_confirmation
from .generation import (
    confirm_generation,
    create_generation_workflow,
    select_template,
    validate_generation_input,
)
from .generation.workflows import GenerationResult


class GenCommand(BaseCommand):
    """Command to generate documentation for source files."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize gen command."""
        super().__init__(settings)
        self.console = get_console()

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the gen command.

        Args:
            files: List of source files or directories
            template: Template name to use
            conflict_strategy: How to handle existing spec files
            commit: Automatically commit generated files
            message: Commit message (implies commit)
            interactive: Enable interactive prompts
            force: Force generation despite warnings
            dry_run: Preview what would be generated
            **kwargs: Additional arguments

        Returns:
            Result dictionary with success status and details
        """
        # Extract parameters from kwargs
        files = kwargs.get("files", [])
        template = kwargs.get("template", "default")
        conflict_strategy = kwargs.get("conflict_strategy", "backup")
        commit = kwargs.get("commit", False)
        message = kwargs.get("message", None)
        interactive = kwargs.get("interactive", False)
        force = kwargs.get("force", False)
        dry_run = kwargs.get("dry_run", False)

        # Validate repository state
        self.validate_repository_state()

        # Expand directories to individual files
        expanded_files = self._expand_source_files(files)

        if not expanded_files:
            show_message("No processable files found in the specified paths", "warning")
            return self.create_result(
                True, "No files to process", data={"generated": []}
            )

        show_message(f"Found {len(expanded_files)} files to process", "info")

        # Configure conflict strategy
        strategy_map = {
            "backup": ConflictResolutionStrategy.BACKUP_AND_REPLACE,
            "overwrite": ConflictResolutionStrategy.OVERWRITE,
            "skip": ConflictResolutionStrategy.SKIP,
            "fail": ConflictResolutionStrategy.FAIL,
        }
        conflict_enum = strategy_map.get(
            conflict_strategy, ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )

        # Interactive configuration
        if interactive:
            template = select_template(template)

            # Confirm configuration
            if not confirm_generation(expanded_files, template, conflict_enum):
                show_message("Generation cancelled by user", "info")
                return self.create_result(False, "Generation cancelled by user")

        # Validate inputs
        validation_result = validate_generation_input(
            expanded_files, template, conflict_enum
        )

        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                self.console.print(f"  • [red]{error}[/red]")

            errors_str = "; ".join(validation_result["errors"])
            raise SpecError(f"Validation failed: {errors_str}")

        # Show warnings if any
        if validation_result["warnings"]:
            show_message("Warnings:", "warning")
            for warning in validation_result["warnings"]:
                self.console.print(f"  • [yellow]{warning}[/yellow]")

            if not force and not get_user_confirmation(
                "Continue despite warnings?", default=True
            ):
                show_message("Generation cancelled", "info")
                return self.create_result(False, "Generation cancelled due to warnings")

        # Dry run mode
        if dry_run:
            self._show_dry_run_preview(expanded_files, template, conflict_enum)
            return self.create_result(
                True,
                f"Dry run completed - {len(expanded_files)} files would be processed",
                data={"files_to_process": expanded_files},
            )

        # Set up auto-commit
        auto_commit = commit or bool(message)
        commit_message = message or "Generate documentation" if auto_commit else None

        # Create and execute workflow
        workflow = create_generation_workflow(
            template_name=template,
            conflict_strategy=conflict_enum,
            auto_commit=auto_commit,
            commit_message=commit_message,
        )

        show_message(f"Generating documentation using '{template}' template...", "info")

        result = workflow.generate(expanded_files)

        # Display results
        self._display_generation_results(result)

        debug_logger.log(
            "INFO",
            "Generation command completed",
            files=len(expanded_files),
            success=result.success,
        )

        return self.create_result(
            result.success,
            f"Generated documentation for {len(result.generated_files)} files",
            data={
                "generated": result.generated_files,
                "skipped": result.skipped_files,
                "failed": result.failed_files,
                "conflicts": result.conflicts_resolved,
                "processing_time": result.total_processing_time,
            },
        )

    def validate_arguments(self, **kwargs: Any) -> None:
        """Validate command arguments.

        Args:
            **kwargs: Command arguments to validate

        Raises:
            SpecError: If validation fails
        """
        files = kwargs.get("files", [])
        template = kwargs.get("template", "default")
        conflict_strategy = kwargs.get("conflict_strategy", "backup")

        if not files:
            raise SpecError("No source files provided")

        # Validate file paths
        for file_path in files:
            if not isinstance(file_path, str | Path):
                raise SpecError(f"Invalid file path type: {type(file_path)}")

        # Validate template
        if not isinstance(template, str):
            raise SpecError(f"Invalid template type: {type(template)}")

        # Validate conflict strategy
        valid_strategies = ["backup", "overwrite", "skip", "fail"]
        if conflict_strategy not in valid_strategies:
            raise SpecError(
                f"Invalid conflict strategy: {conflict_strategy}. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )

    def _expand_source_files(self, source_files: list[Path]) -> list[Path]:
        """Expand directories to individual source files."""
        from .generation.validation import GenerationValidator

        validator = GenerationValidator()
        expanded_files = []

        for file_path in source_files:
            if file_path.is_file():
                if validator._is_processable_file(file_path):
                    expanded_files.append(file_path)
            elif file_path.is_dir():
                processable_files = validator._get_processable_files_in_directory(
                    file_path
                )
                expanded_files.extend(processable_files)

        return expanded_files

    def _show_dry_run_preview(
        self,
        source_files: list[Path],
        template: str,
        conflict_strategy: ConflictResolutionStrategy,
    ) -> None:
        """Show dry run preview of what would be generated."""
        self.console.print("\n[bold cyan]Dry Run Preview:[/bold cyan]")
        self.console.print(f"Template: [yellow]{template}[/yellow]")
        self.console.print(
            f"Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]"
        )
        self.console.print(f"Files to process: [yellow]{len(source_files)}[/yellow]\n")

        # Helper to get spec files using centralized method
        def get_spec_files_for_source(source_file: Path) -> dict[str, Path]:
            from ...file_system.path_resolver import PathResolver

            path_resolver = PathResolver(self.settings)
            return path_resolver.get_spec_files_for_source(source_file)

        for source_file in source_files:
            spec_files = get_spec_files_for_source(source_file)

            self.console.print(f"[bold]{source_file}[/bold]")
            for file_type, spec_file in spec_files.items():
                status = (
                    "[yellow]exists[/yellow]"
                    if spec_file.exists()
                    else "[green]new[/green]"
                )
                self.console.print(
                    f"  • {file_type}: [path]{spec_file}[/path] ({status})"
                )
            self.console.print()

        show_message("This is a dry run. No files would be modified.", "info")

    def _display_generation_results(self, result: GenerationResult) -> None:
        """Display generation results."""
        # Show summary
        if result.success:
            show_message(
                f"Generation completed successfully in {result.total_processing_time:.2f}s",
                "success",
            )
        else:
            show_message(
                f"Generation completed with errors in {result.total_processing_time:.2f}s",
                "warning",
            )

        # Show statistics using simple formatting
        self.console.print("\n[bold cyan]Generation Statistics:[/bold cyan]")
        self.console.print(
            f"  Generated files: [green]{len(result.generated_files)}[/green]"
        )
        self.console.print(
            f"  Skipped files: [yellow]{len(result.skipped_files)}[/yellow]"
        )
        self.console.print(f"  Failed files: [red]{len(result.failed_files)}[/red]")
        self.console.print(
            f"  Conflicts resolved: [blue]{len(result.conflicts_resolved)}[/blue]"
        )

        # Show generated files
        if result.generated_files:
            self.console.print("\n[bold green]Generated files:[/bold green]")
            for file_path in result.generated_files:
                self.console.print(f"  • [path]{file_path}[/path]")

        # Show failed files
        if result.failed_files:
            self.console.print("\n[bold red]Failed files:[/bold red]")
            for failure in result.failed_files:
                self.console.print(
                    f"  • [path]{failure['file']}[/path]: {failure['error']}"
                )

        # Show conflicts
        if result.conflicts_resolved:
            self.console.print("\n[bold yellow]Conflicts resolved:[/bold yellow]")
            for conflict in result.conflicts_resolved:
                if conflict["type"] == "backup":
                    self.console.print(
                        f"  • Backed up [path]{conflict['original']}[/path] to [path]{conflict['backup']}[/path]"
                    )
                elif conflict["type"] == "overwrite":
                    self.console.print(f"  • Overwrote [path]{conflict['file']}[/path]")
