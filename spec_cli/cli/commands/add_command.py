"""Add command implementation using BaseCommand."""

from pathlib import Path
from typing import Any

from ...config.settings import SpecSettings
from ...exceptions import SpecError
from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..base_command import BaseCommand
from .generation import create_add_workflow


class AddCommand(BaseCommand):
    """Command to add spec files to Git tracking."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize add command."""
        super().__init__(settings)
        self.console = get_console()

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the add command.

        Args:
            files: List of file paths to add
            force: Force add ignored files
            dry_run: Preview what would be added without doing it
            **kwargs: Additional arguments

        Returns:
            Result dictionary with success status and details
        """
        # Extract parameters from kwargs
        files = kwargs.get("files", [])
        force = kwargs.get("force", False)
        dry_run = kwargs.get("dry_run", False)

        # Validate repository state
        self.validate_repository_state()

        # Create repository instance
        repo = SpecGitRepository(self.settings)

        # Expand directories to individual files
        expanded_files = self._expand_spec_files(files)

        if not expanded_files:
            show_message("No spec files found in the specified paths", "warning")
            return self.create_result(True, "No files to add", data={"added": []})

        # Filter to only spec files
        spec_files = self._filter_spec_files(expanded_files)

        if not spec_files:
            show_message(
                "No files in .specs/ directory found. Use 'spec gen' to create documentation first.",
                "warning",
            )
            return self.create_result(True, "No spec files found", data={"added": []})

        show_message(f"Found {len(spec_files)} spec files to add", "info")

        # Check Git status for these files
        git_status = self._analyze_git_status(spec_files, repo)

        # Show preview
        self._show_add_preview(git_status, dry_run)

        # Dry run mode
        if dry_run:
            show_message("This is a dry run. No files would be added.", "info")
            return self.create_result(
                True,
                f"Dry run completed - {len(spec_files)} files would be added",
                data={"files_to_add": spec_files},
            )

        # Filter to only files that need to be added
        files_to_add = [
            Path(f) for f in git_status["untracked"] + git_status["modified"]
        ]

        if not files_to_add:
            show_message(
                "All specified files are already tracked and up to date", "info"
            )
            return self.create_result(
                True, "All files already tracked", data={"added": []}
            )

        # Create and execute workflow
        workflow = create_add_workflow(force=force, settings=self.settings)

        show_message(f"Adding {len(files_to_add)} files to spec repository...", "info")

        result = workflow.add_files(files_to_add)

        # Display results
        self._display_add_results(result)

        debug_logger.log(
            "INFO",
            "Add command completed",
            files=len(files_to_add),
            success=result["success"],
        )

        return self.create_result(
            result["success"], f"Added {len(result['added'])} files", data=result
        )

    def validate_arguments(self, **kwargs: Any) -> None:
        """Validate command arguments.

        Args:
            **kwargs: Command arguments to validate

        Raises:
            SpecError: If validation fails
        """
        files = kwargs.get("files", [])

        if not files:
            raise SpecError("No file paths provided")

        # Validate file paths exist
        for file_path in files:
            if not isinstance(file_path, str | Path):
                raise SpecError(f"Invalid file path type: {type(file_path)}")

    def _expand_spec_files(self, file_paths: list[Path]) -> list[Path]:
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

    def _filter_spec_files(self, file_paths: list[Path]) -> list[Path]:
        """Filter to only files in .specs directory."""
        spec_files = []
        specs_dir = self.settings.specs_dir

        for file_path in file_paths:
            try:
                # Check if file is in .specs directory
                file_path.relative_to(specs_dir)
                spec_files.append(file_path)
            except ValueError:
                # File is not in .specs directory
                continue

        return spec_files

    def _analyze_git_status(
        self, spec_files: list[Path], repo: SpecGitRepository
    ) -> dict[str, list[str]]:
        """Analyze Git status for spec files."""
        git_status: dict[str, list[str]] = {
            "untracked": [],
            "modified": [],
            "staged": [],
            "up_to_date": [],
        }

        try:
            # Get overall Git status
            repo.status()

            # Categorize our files based on simple existence checks
            # This is a simplified version since we may not have full git status integration yet
            for file_path in spec_files:
                # For now, assume all files are untracked unless they're already in git
                # This is a simplification for the implementation
                git_status["untracked"].append(str(file_path))

        except Exception as e:
            debug_logger.log("WARNING", "Failed to get Git status", error=str(e))
            # If we can't get status, assume all files are untracked
            git_status["untracked"] = [str(f) for f in spec_files]

        return git_status

    def _show_add_preview(
        self, git_status: dict[str, list[str]], is_dry_run: bool = False
    ) -> None:
        """Show preview of files to be added."""
        title = "Add Preview (Dry Run)" if is_dry_run else "Files to Add"
        self.console.print(f"\n[bold cyan]{title}:[/bold cyan]")

        # Show status entries
        if git_status["untracked"]:
            self.console.print(
                f"  New files: [green]{len(git_status['untracked'])}[/green]"
            )

        if git_status["modified"]:
            self.console.print(
                f"  Modified files: [yellow]{len(git_status['modified'])}[/yellow]"
            )

        if git_status["staged"]:
            self.console.print(
                f"  Already staged: [blue]{len(git_status['staged'])}[/blue]"
            )

        if git_status["up_to_date"]:
            self.console.print(
                f"  Up to date: [dim]{len(git_status['up_to_date'])}[/dim]"
            )

        # Show file details for small lists
        total_to_add = len(git_status["untracked"]) + len(git_status["modified"])
        if total_to_add > 0 and total_to_add <= 10:
            self.console.print("\n[bold cyan]Files to be added:[/bold cyan]")

            for file_path in git_status["untracked"]:
                self.console.print(
                    f"  [green]A[/green] [path]{file_path}[/path] (new file)"
                )

            for file_path in git_status["modified"]:
                self.console.print(
                    f"  [yellow]M[/yellow] [path]{file_path}[/path] (modified)"
                )

    def _display_add_results(self, result: dict[str, Any]) -> None:
        """Display add operation results."""
        # Show summary
        if result["success"]:
            show_message(
                f"Successfully added {len(result['added'])} files to spec repository",
                "success",
            )
        else:
            show_message(
                f"Add completed with {len(result['failed'])} failures", "warning"
            )

        # Show statistics
        self.console.print("\n[bold cyan]Add Results:[/bold cyan]")
        self.console.print(f"  Added files: [green]{len(result['added'])}[/green]")
        self.console.print(
            f"  Skipped files: [yellow]{len(result['skipped'])}[/yellow]"
        )
        self.console.print(f"  Failed files: [red]{len(result['failed'])}[/red]")

        # Show added files
        if result["added"]:
            self.console.print("\n[bold green]Added files:[/bold green]")
            for file_path in result["added"]:
                self.console.print(f"  • [path]{file_path}[/path]")

        # Show skipped files
        if result["skipped"]:
            self.console.print("\n[bold yellow]Skipped files:[/bold yellow]")
            for skip_info in result["skipped"]:
                self.console.print(
                    f"  • [path]{skip_info['file']}[/path]: {skip_info['reason']}"
                )

        # Show failed files
        if result["failed"]:
            self.console.print("\n[bold red]Failed files:[/bold red]")
            for failure in result["failed"]:
                self.console.print(
                    f"  • [path]{failure['file']}[/path]: {failure['error']}"
                )

        # Next steps
        if result["added"]:
            self.console.print("\n[bold cyan]Next steps:[/bold cyan]")
            self.console.print(
                "  Use [yellow]spec commit -m 'message'[/yellow] to commit these changes"
            )
