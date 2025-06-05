"""Interactive prompts for generation commands."""

from pathlib import Path

import click

from ....file_processing.conflict_resolver import ConflictResolutionStrategy
from ....ui.console import get_console


class TemplateSelector:
    """Interactive template selection."""

    def __init__(self) -> None:
        """Initialize template selector with console interface."""
        self.console = get_console()

    def select_template(self, current_template: str | None = None) -> str:
        """Prompt user to select a template.

        Args:
            current_template: Currently selected template

        Returns:
            Selected template name
        """
        # For now, use a simple list of known templates
        # In a future implementation, this could scan for .spectemplate files
        available_templates = ["default", "minimal", "comprehensive"]

        if not available_templates:
            self.console.print("[yellow]No templates available, using default[/yellow]")
            return "default"

        # Show template options
        self.console.print("\n[bold cyan]Available Templates:[/bold cyan]")
        for i, template in enumerate(available_templates, 1):
            marker = " (current)" if template == current_template else ""
            description = self._get_template_description(template)
            self.console.print(
                f"  {i}. [yellow]{template}[/yellow]{marker} - {description}"
            )

        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "\nSelect template number",
                    type=int,
                    default=str(
                        1
                        if current_template is None
                        else available_templates.index(current_template) + 1
                    ),
                )

                if 1 <= choice <= len(available_templates):
                    selected: str = available_templates[choice - 1]
                    self.console.print(f"[green]Selected template: {selected}[/green]")
                    return selected
                else:
                    self.console.print(
                        "[yellow]Invalid selection. Please try again.[/yellow]"
                    )

            except click.Abort:
                # User cancelled (Ctrl+C)
                return current_template or "default"
            except (ValueError, IndexError):
                self.console.print(
                    "[yellow]Invalid input. Please enter a number.[/yellow]"
                )

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

    def __init__(self) -> None:
        """Initialize conflict resolver with console interface."""
        self.console = get_console()

    def resolve_conflicts(
        self,
        source_file: Path,
        existing_files: list[Path],
        suggested_strategy: ConflictResolutionStrategy,
    ) -> ConflictResolutionStrategy:
        """Prompt user to resolve file conflicts.

        Args:
            source_file: Source file being processed
            existing_files: Existing spec files that conflict
            suggested_strategy: Suggested resolution strategy

        Returns:
            Selected conflict resolution strategy
        """
        self.console.print(
            f"\n[bold yellow]Conflict detected for {source_file.name}[/bold yellow]"
        )
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
        for i, (strategy_name, description) in enumerate(options, 1):
            marker = (
                " (suggested)"
                if strategy_name == suggested_strategy.value.lower()
                else ""
            )
            self.console.print(
                f"  {i}. [yellow]{strategy_name}[/yellow]{marker} - {description}"
            )

        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    "\nSelect resolution strategy",
                    type=int,
                    default="1",  # Default to backup
                )

                if 1 <= choice <= len(options):
                    selected_strategy_name = options[choice - 1][0]
                    selected_strategy = self._name_to_strategy(selected_strategy_name)

                    self.console.print(
                        f"[green]Selected strategy: {selected_strategy_name}[/green]"
                    )
                    return selected_strategy
                else:
                    self.console.print(
                        "[yellow]Invalid selection. Please try again.[/yellow]"
                    )

            except click.Abort:
                # User cancelled - default to skip
                return ConflictResolutionStrategy.SKIP
            except (ValueError, IndexError):
                self.console.print(
                    "[yellow]Invalid input. Please enter a number.[/yellow]"
                )

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

    def __init__(self) -> None:
        """Initialize generation prompts with selector, resolver, and console."""
        self.template_selector = TemplateSelector()
        self.conflict_resolver = ConflictResolver()
        self.console = get_console()

    def confirm_generation(
        self,
        source_files: list[Path],
        template_name: str,
        conflict_strategy: ConflictResolutionStrategy,
    ) -> bool:
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
        self.console.print(
            f"  Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]"
        )
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

    def get_generation_config(
        self, current_template: str | None = None, interactive: bool = True
    ) -> dict[str, str | ConflictResolutionStrategy | bool | None]:
        """Get complete generation configuration from user.

        Args:
            current_template: Current template selection
            interactive: Whether to show interactive prompts

        Returns:
            Dictionary with generation configuration
        """
        config: dict[str, str | ConflictResolutionStrategy | bool | None] = {}

        if interactive:
            # Template selection
            config["template"] = self.template_selector.select_template(
                current_template
            )

            # Conflict strategy
            conflict_options = [
                ("backup", "Create backup and replace (safest)"),
                ("overwrite", "Overwrite existing files"),
                ("skip", "Skip files with conflicts"),
            ]

            self.console.print("\n[bold cyan]Conflict Resolution:[/bold cyan]")
            for i, (strategy_name, description) in enumerate(conflict_options, 1):
                self.console.print(
                    f"  {i}. [yellow]{strategy_name}[/yellow] - {description}"
                )

            choice = click.prompt(
                "\nSelect conflict resolution strategy", type=int, default="1"
            )

            if 1 <= choice <= len(conflict_options):
                selected_strategy_name = conflict_options[choice - 1][0]
                config["conflict_strategy"] = self.conflict_resolver._name_to_strategy(
                    selected_strategy_name
                )
            else:
                config["conflict_strategy"] = (
                    ConflictResolutionStrategy.BACKUP_AND_REPLACE
                )

            # Auto-commit option
            config["auto_commit"] = click.confirm(
                "\nAutomatically commit generated files?", default=False
            )

            if config["auto_commit"]:
                config["commit_message"] = click.prompt(
                    "Commit message",
                    default="Generate documentation",
                    show_default=True,
                )

        else:
            # Non-interactive defaults
            config["template"] = current_template or "default"
            config["conflict_strategy"] = ConflictResolutionStrategy.BACKUP_AND_REPLACE
            config["auto_commit"] = False
            config["commit_message"] = None

        return config


# Convenience functions
def select_template(current_template: str | None = None) -> str:
    """Select template interactively."""
    selector = TemplateSelector()
    return selector.select_template(current_template)


def resolve_conflicts(
    source_file: Path,
    existing_files: list[Path],
    suggested_strategy: ConflictResolutionStrategy,
) -> ConflictResolutionStrategy:
    """Resolve conflicts interactively."""
    resolver = ConflictResolver()
    return resolver.resolve_conflicts(source_file, existing_files, suggested_strategy)


def confirm_generation(
    source_files: list[Path],
    template_name: str,
    conflict_strategy: ConflictResolutionStrategy,
) -> bool:
    """Confirm generation operation."""
    prompts = GenerationPrompts()
    return prompts.confirm_generation(source_files, template_name, conflict_strategy)
