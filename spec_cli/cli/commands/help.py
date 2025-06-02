"""Spec help command implementation."""

from typing import Dict, Optional

import click

from ...ui.console import get_console
from ...ui.tables import SpecTable


@click.command()
@click.argument("command_name", required=False)
def help_command(command_name: Optional[str]) -> None:
    """Show help information for spec commands.

    COMMAND_NAME: Optional specific command to show help for
    """
    if command_name:
        _display_command_help(command_name)
    else:
        _display_main_help()


def _display_main_help() -> None:
    """Display main help with command overview."""
    console = get_console()

    # Header
    console.print(
        "\n[bold cyan]Spec CLI[/bold cyan] - Versioned Documentation for AI-Assisted Development\n"
    )
    console.print(
        "Manage documentation specs for your codebase with Git integration.\n"
    )

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
    console.print(
        "\nUse [yellow]spec <command> --help[/yellow] for detailed command information."
    )
    console.print(
        "Use [yellow]spec help <command>[/yellow] for comprehensive command help.\n"
    )


def _display_command_help(command: str) -> None:
    """Display detailed help for a specific command."""
    console = get_console()

    help_data = _get_command_help(command)

    if not help_data:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("\nAvailable commands: init, status, help")
        return

    # Command title
    console.print(
        f"\n[bold yellow]{command}[/bold yellow] - {help_data['description']}\n"
    )

    # Usage
    console.print("[bold]Usage:[/bold]")
    console.print(f"  spec {help_data['usage']}\n")

    # Description
    if help_data.get("long_description"):
        console.print("[bold]Description:[/bold]")
        console.print(f"  {help_data['long_description']}\n")

    # Options
    if help_data.get("options"):
        options_table = SpecTable(title="Options")
        options_table.add_column("Option", style="yellow")
        options_table.add_column("Description", style="white")
        options_table.add_column("Default", style="dim", width=10)

        for opt in help_data["options"]:
            default = (
                str(opt.get("default", "")) if opt.get("default") is not None else ""
            )
            options_table.add_row(opt["name"], opt["description"], default)

        options_table.print()
        console.print()

    # Examples
    if help_data.get("examples"):
        console.print("[bold]Examples:[/bold]")
        for example in help_data["examples"]:
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
                    "default": False,
                },
                {
                    "name": "--debug",
                    "description": "Enable debug output and detailed logging",
                    "default": False,
                },
                {
                    "name": "--verbose",
                    "description": "Enable verbose output",
                    "default": False,
                },
            ],
            "examples": [
                {"description": "Initialize in current directory", "command": "init"},
                {"description": "Force reinitialize", "command": "init --force"},
                {
                    "description": "Initialize with debug output",
                    "command": "init --debug",
                },
            ],
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
                    "default": False,
                },
                {
                    "name": "--git",
                    "description": "Also show Git repository status",
                    "default": False,
                },
                {
                    "name": "--summary",
                    "description": "Show processing capabilities summary",
                    "default": False,
                },
                {
                    "name": "--debug",
                    "description": "Enable debug output and detailed logging",
                    "default": False,
                },
                {
                    "name": "--verbose",
                    "description": "Enable verbose output",
                    "default": False,
                },
            ],
            "examples": [
                {"description": "Show basic repository status", "command": "status"},
                {"description": "Show health check", "command": "status --health"},
                {
                    "description": "Show status with Git information",
                    "command": "status --git",
                },
                {
                    "description": "Show comprehensive status",
                    "command": "status --health --git --summary",
                },
            ],
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
                {
                    "description": "Show detailed help for init command",
                    "command": "help init",
                },
                {
                    "description": "Show detailed help for status command",
                    "command": "help status",
                },
            ],
        },
    }

    return help_data.get(command, {})
