"""Click framework pattern analysis utilities for context storage integration."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

from ..exceptions import SpecValidationError
from .error_utils import create_error_context


@dataclass
class ClickPatternReport:
    """Report of Click framework usage patterns and integration capabilities.

    Attributes:
        commands_found: List of Click command names discovered
        decorators_used: Set of Click decorator types found
        context_usage: Dict mapping files to context usage patterns
        storage_capabilities: Dict of Click context storage validation results
        integration_requirements: List of requirements for context integration
        cli_structure: Dict describing the CLI command hierarchy
    """

    commands_found: list[str] = field(default_factory=list)
    decorators_used: set[str] = field(default_factory=set)
    context_usage: dict[str, list[str]] = field(default_factory=dict)
    storage_capabilities: dict[str, bool] = field(default_factory=dict)
    integration_requirements: list[str] = field(default_factory=list)
    cli_structure: dict[str, Any] = field(default_factory=dict)


def analyze_click_patterns(cli_dir: Path) -> ClickPatternReport:
    """Analyze existing Click command patterns and decorator usage.

    Args:
        cli_dir: Path to CLI directory to analyze

    Returns:
        ClickPatternReport with discovered patterns and capabilities

    Raises:
        SpecValidationError: If cli_dir is invalid or analysis fails

    Example:
        >>> from pathlib import Path
        >>> report = analyze_click_patterns(Path("spec_cli/cli"))
        >>> print(len(report.commands_found))  # Number of commands found
        >>> print("group" in report.decorators_used)  # True if @click.group found
    """
    if not isinstance(cli_dir, Path):
        raise SpecValidationError(
            "CLI directory must be a Path object",
            create_error_context(cli_dir if isinstance(cli_dir, Path) else Path(".")),
        )

    if not cli_dir.exists():
        raise SpecValidationError(
            f"CLI directory does not exist: {cli_dir}", create_error_context(cli_dir)
        )

    if not cli_dir.is_dir():
        raise SpecValidationError(
            f"CLI path is not a directory: {cli_dir}", create_error_context(cli_dir)
        )

    report = ClickPatternReport()

    try:
        # Analyze Python files in CLI directory recursively
        for py_file in cli_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            _analyze_file_patterns(py_file, report)

        # Generate integration requirements based on findings
        _generate_integration_requirements(report)

        return report

    except Exception as e:
        raise SpecValidationError(
            f"Failed to analyze Click patterns: {e}", create_error_context(cli_dir)
        ) from e


def validate_context_storage_capability() -> bool:
    """Validate Click context object capabilities for custom data storage.

    Returns:
        True if Click context supports custom data storage, False otherwise

    Example:
        >>> can_store = validate_context_storage_capability()
        >>> print(can_store)  # True - Click contexts support custom storage
    """
    try:
        # Create a test Click context to validate storage capabilities
        ctx = click.Context(click.Command("test"))

        # Test basic attribute storage
        test_key = "test_spec_context_storage"
        test_value = {"test": "data"}

        # Verify we can store custom data
        setattr(ctx, test_key, test_value)
        stored_value = getattr(ctx, test_key, None)

        # Verify meta dictionary access
        ctx.meta["test_meta"] = "meta_value"
        meta_value = ctx.meta.get("test_meta")

        # Validation successful if both storage methods work
        return stored_value == test_value and meta_value == "meta_value"

    except Exception:
        # If any storage method fails, context storage not supported
        return False


def _analyze_file_patterns(py_file: Path, report: ClickPatternReport) -> None:
    """Analyze a single Python file for Click patterns.

    Args:
        py_file: Python file to analyze
        report: ClickPatternReport to update with findings
    """
    try:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        file_context_usage = []

        for node in ast.walk(tree):
            # Look for Click decorators
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    _analyze_decorator(decorator, report)

                # Look for function parameters that use Click context
                for arg in node.args.args:
                    if arg.arg == "ctx" or "context" in arg.arg.lower():
                        file_context_usage.append(
                            f"Function {node.name} uses context parameter"
                        )

            # Look for Click imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "click":
                        report.decorators_used.add("click_import")

            elif isinstance(node, ast.ImportFrom):
                if node.module == "click":
                    for alias in node.names:
                        report.decorators_used.add(f"from_click_{alias.name}")

            # Look for click.Context usage
            elif isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "click"
                    and node.attr == "Context"
                ):
                    file_context_usage.append("Direct Click.Context usage")

        if file_context_usage:
            report.context_usage[str(py_file)] = file_context_usage

    except Exception:
        # Skip files that can't be parsed (non-Python, syntax errors, etc.)
        pass


def _analyze_decorator(decorator: ast.AST, report: ClickPatternReport) -> None:
    """Analyze a decorator node for Click patterns.

    Args:
        decorator: AST decorator node to analyze
        report: ClickPatternReport to update
    """
    if isinstance(decorator, ast.Attribute):
        # Handle @click.command, @click.group, etc.
        if isinstance(decorator.value, ast.Name) and decorator.value.id == "click":
            decorator_name = decorator.attr
            report.decorators_used.add(f"click_{decorator_name}")

            if decorator_name in ("command", "group"):
                report.commands_found.append(decorator_name)

    elif isinstance(decorator, ast.Call):
        # Handle @click.command(), @click.option(), etc.
        if isinstance(decorator.func, ast.Attribute):
            if (
                isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "click"
            ):
                decorator_name = decorator.func.attr
                report.decorators_used.add(f"click_{decorator_name}")

                if decorator_name in ("command", "group"):
                    report.commands_found.append(decorator_name)


def _generate_integration_requirements(report: ClickPatternReport) -> None:
    """Generate integration requirements based on discovered patterns.

    Args:
        report: ClickPatternReport to update with requirements
    """
    requirements = []

    # Basic Click integration requirements
    if report.decorators_used:
        requirements.append(
            "Click framework integration required for command context access"
        )

    # Context storage requirements
    if report.context_usage:
        requirements.append(
            "Click context parameter injection needed for SpecContext integration"
        )
        requirements.append(
            "Context storage mechanism required for dependency injection"
        )

    # Command-specific requirements
    if "command" in report.commands_found:
        requirements.append(
            "Individual Click command context storage integration needed"
        )

    if "group" in report.commands_found:
        requirements.append(
            "Click group context inheritance for nested command support"
        )

    # Decorator pattern requirements
    if any("option" in dec for dec in report.decorators_used):
        requirements.append(
            "Click option decorator compatibility with context injection"
        )

    if any("argument" in dec for dec in report.decorators_used):
        requirements.append("Click argument decorator integration with context storage")

    # Storage capability requirements
    storage_supported = validate_context_storage_capability()
    if storage_supported:
        requirements.append(
            "Click context custom data storage verified - integration feasible"
        )
        report.storage_capabilities["custom_data_storage"] = True
        report.storage_capabilities["meta_dictionary_access"] = True
    else:
        requirements.append(
            "Click context storage limitations - alternative approach needed"
        )
        report.storage_capabilities["custom_data_storage"] = False
        report.storage_capabilities["meta_dictionary_access"] = False

    report.integration_requirements = requirements
