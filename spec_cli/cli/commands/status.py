"""Spec status command implementation."""

from pathlib import Path
from typing import Any, Dict

import click

from ...exceptions import SpecRepositoryError
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.tables import StatusTable, create_key_value_table
from ..options import spec_command
from ..utils import echo_status, get_spec_repository


@spec_command()
@click.option(
    "--health",
    is_flag=True,
    help="Show repository health check instead of regular status",
)
@click.option("--git", is_flag=True, help="Also show Git repository status")
@click.option("--summary", is_flag=True, help="Show processing capabilities summary")
def status_command(
    debug: bool, verbose: bool, health: bool, git: bool, summary: bool
) -> None:
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
            git_status = _get_git_status_data(repo)
            _display_git_status(git_status)

        # Show processing summary if requested
        if summary:
            console.print("\n[bold cyan]Processing Summary:[/bold cyan]")
            summary_info = _get_processing_summary()
            _display_processing_summary(summary_info)

        debug_logger.log(
            "INFO", "Status check completed", health=health, git=git, summary=summary
        )

    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository error: {e}") from e
    except Exception as e:
        debug_logger.log("ERROR", "Status check failed", error=str(e))
        raise click.ClickException(f"Status check failed: {e}") from e


def _get_repository_status(repo: Any) -> Dict[str, Any]:
    """Get repository status information."""
    spec_dir = Path(".spec")
    specs_dir = Path(".specs")

    # Count files in specs directory
    spec_files = list(specs_dir.rglob("*.md")) if specs_dir.exists() else []
    index_files = [f for f in spec_files if f.name == "index.md"]
    history_files = [f for f in spec_files if f.name == "history.md"]

    # Get Git status
    git_status = _get_git_status_data(repo)

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
        },
    }


def _get_git_status_data(repo: Any) -> Dict[str, Any]:
    """Get git status data from repository.

    Args:
        repo: SpecGitRepository instance

    Returns:
        Dictionary with staged, modified, and untracked files
    """
    try:
        return {
            "staged": repo.get_staged_files(),
            "modified": repo.get_unstaged_files(),
            "untracked": repo.get_untracked_files(),
        }
    except Exception:
        return {"staged": [], "modified": [], "untracked": []}


def _get_repository_health(repo: Any) -> Dict[str, Any]:
    """Get repository health information."""
    spec_dir = Path(".spec")
    specs_dir = Path(".specs")

    health: Dict[str, Dict[str, Any]] = {
        "repository_structure": {"status": "healthy", "details": []},
        "git_configuration": {"status": "healthy", "details": []},
        "file_permissions": {"status": "healthy", "details": []},
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
        git_status = _get_git_status_data(repo)
        if not any(git_status.values()):
            health["git_configuration"]["status"] = "warning"
            health["git_configuration"]["details"].append("Unable to get Git status")
    except Exception as e:
        health["git_configuration"]["status"] = "error"
        health["git_configuration"]["details"].append(f"Git error: {e}")

    # Check file permissions
    try:
        if spec_dir.exists() and not spec_dir.is_dir():
            health["file_permissions"]["status"] = "error"
            health["file_permissions"]["details"].append(
                ".spec exists but is not a directory"
            )

        if specs_dir.exists() and not specs_dir.is_dir():
            health["file_permissions"]["status"] = "error"
            health["file_permissions"]["details"].append(
                ".specs exists but is not a directory"
            )
    except PermissionError:
        health["file_permissions"]["status"] = "error"
        health["file_permissions"]["details"].append(
            "Permission denied accessing directories"
        )

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
        },
    }


def _display_repository_status(status_info: Dict[str, Any]) -> None:
    """Display repository status using Rich formatting."""

    # Repository information
    repo_table = create_key_value_table(
        status_info["repository"], "Repository Information"
    )
    repo_table.print()

    # File counts
    files_table = create_key_value_table(status_info["files"], "File Statistics")
    files_table.print()

    # Git status summary
    git_table = create_key_value_table(status_info["git"], "Git Status Summary")
    git_table.print()


def _display_health_check(health_info: Dict[str, Any]) -> None:
    """Display health check results."""
    table = StatusTable("Repository Health Check")

    for component, info in health_info.items():
        status = info["status"]
        details = "; ".join(info["details"]) if info["details"] else "OK"

        # Map status to appropriate type
        status_type = {
            "healthy": "success",
            "warning": "warning",
            "error": "error",
        }.get(status, "info")

        table.add_status_item(component.replace("_", " ").title(), details, status_type)

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
    from ...ui.error_display import format_data

    format_data(summary_info, "Processing Capabilities")
