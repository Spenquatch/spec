"""CLI command structure analysis utilities."""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .error_handler import ErrorHandler

# Create error handler for command analysis
command_analysis_error_handler = ErrorHandler(
    {"module": "utils", "component": "command_analysis"}
)

@dataclass
class ClickPattern:
    """Represents a Click decorator pattern found in code."""

    decorator_name: str
    function_name: str
    file_path: str
    line_number: int
    parameters: list[str] = field(default_factory=list)
    is_command: bool = False
    is_group: bool = False

@dataclass
class SingletonUsage:
    """Represents usage of singleton pattern in CLI command."""

    singleton_class: str
    usage_pattern: str  # "direct_instantiation", "factory_function", "import_access"
    file_path: str
    line_number: int
    context: str  # surrounding code context
    import_source: str | None = None

@dataclass
class CommandStructureReport:
    """Complete CLI command structure analysis report."""

    commands: list[dict[str, str]] = field(default_factory=list)
    click_patterns: list[ClickPattern] = field(default_factory=list)
    singleton_usage: list[SingletonUsage] = field(default_factory=list)
    file_count: int = 0
    analysis_errors: list[str] = field(default_factory=list)

class CommandAnalysisError(Exception):
    """Error during command analysis."""

    pass

@command_analysis_error_handler.wrap
def analyze_command_structure(cli_dir: Path) -> CommandStructureReport:
    """Analyze CLI directory structure and command organization.

    Args:
        cli_dir: Path to CLI directory to analyze

    Returns:
        CommandStructureReport with complete structure analysis

    Raises:
        CommandAnalysisError: If analysis fails or directory invalid
    """
    if not cli_dir.exists():
        raise CommandAnalysisError(f"CLI directory does not exist: {cli_dir}")

    if not cli_dir.is_dir():
        raise CommandAnalysisError(f"Path is not a directory: {cli_dir}")

    report = CommandStructureReport()

    # Find all Python files in CLI directory
    python_files = list(cli_dir.rglob("*.py"))
    report.file_count = len(python_files)

    for py_file in python_files:
        try:
            # Skip __init__.py files for command analysis
            if py_file.name == "__init__.py":
                continue

            # Analyze file for commands and patterns
            file_commands = _extract_commands_from_file(py_file)
            file_click_patterns = _extract_click_patterns_from_file(py_file)
            file_singleton_usage = identify_singleton_usage(py_file)

            # Add to report
            report.commands.extend(file_commands)
            report.click_patterns.extend(file_click_patterns)
            report.singleton_usage.extend(file_singleton_usage)

        except Exception as e:
            error_msg = f"Failed to analyze {py_file}: {e}"
            report.analysis_errors.append(error_msg)
            command_analysis_error_handler.report(
                e, "file analysis", file_path=str(py_file)
            )

    return report

@command_analysis_error_handler.wrap
def identify_singleton_usage(command_file: Path) -> list[SingletonUsage]:
    """Identify singleton usage patterns in a command file.

    Args:
        command_file: Path to command file to analyze

    Returns:
        List of SingletonUsage patterns found

    Raises:
        CommandAnalysisError: If file cannot be analyzed
    """
    if not command_file.exists():
        raise CommandAnalysisError(f"Command file does not exist: {command_file}")

    if not command_file.is_file():
        raise CommandAnalysisError(f"Path is not a file: {command_file}")

    singleton_patterns = []

    try:
        content = command_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Parse AST for detailed analysis
        try:
            tree = ast.parse(content)
            ast_patterns = _analyze_ast_for_singletons(tree, str(command_file))
            singleton_patterns.extend(ast_patterns)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            regex_patterns = _analyze_regex_for_singletons(lines, str(command_file))
            singleton_patterns.extend(regex_patterns)

    except UnicodeDecodeError as e:
        raise CommandAnalysisError(f"Cannot decode file {command_file}: {e}") from e
    except Exception as e:
        raise CommandAnalysisError(f"Failed to analyze file {command_file}: {e}") from e

    return singleton_patterns

def _extract_commands_from_file(py_file: Path) -> list[dict[str, str]]:
    """Extract command definitions from a Python file."""
    commands = []

    try:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has Click command decorator
                has_command_decorator = False
                for decorator in node.decorator_list:
                    if _is_click_command_decorator(decorator):
                        has_command_decorator = True
                        break

                if has_command_decorator:
                    commands.append(
                        {
                            "name": node.name,
                            "file": str(py_file),
                            "line": str(node.lineno),
                            "type": "command",
                        }
                    )

    except Exception:
        # Skip files that can't be parsed
        pass

    return commands

def _extract_click_patterns_from_file(py_file: Path) -> list[ClickPattern]:
    """Extract Click decorator patterns from a Python file."""
    patterns = []

    try:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    click_pattern = _analyze_click_decorator(
                        decorator, node.name, str(py_file), node.lineno
                    )
                    if click_pattern:
                        patterns.append(click_pattern)

    except Exception:
        # Skip files that can't be parsed
        pass

    return patterns

def _analyze_ast_for_singletons(tree: ast.AST, file_path: str) -> list[SingletonUsage]:
    """Analyze AST tree for singleton usage patterns."""
    singleton_patterns = []

    # Known singleton patterns to detect
    singleton_classes = {
        "SpecGitRepository",
        "Console",
        "ProviderManager",
        "ProgressManager",
        "DebugLogger",
    }

    singleton_functions = {"get_spec_repository", "get_console", "get_progress_manager"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Direct instantiation: ClassName()
            if isinstance(node.func, ast.Name) and node.func.id in singleton_classes:
                singleton_patterns.append(
                    SingletonUsage(
                        singleton_class=node.func.id,
                        usage_pattern="direct_instantiation",
                        file_path=file_path,
                        line_number=node.lineno,
                        context=f"{node.func.id}()",
                    )
                )

            # Factory function calls: get_something()
            elif (
                isinstance(node.func, ast.Name) and node.func.id in singleton_functions
            ):
                # Map function to class
                class_name = _map_factory_to_class(node.func.id)
                singleton_patterns.append(
                    SingletonUsage(
                        singleton_class=class_name,
                        usage_pattern="factory_function",
                        file_path=file_path,
                        line_number=node.lineno,
                        context=f"{node.func.id}()",
                    )
                )

    return singleton_patterns

def _analyze_regex_for_singletons(
    lines: list[str], file_path: str
) -> list[SingletonUsage]:
    """Fallback regex analysis for singleton patterns."""
    singleton_patterns = []

    # Regex patterns for common singleton usage
    direct_instantiation_pattern = re.compile(r"(\w+Repository|Console|Manager)\(\)")
    factory_function_pattern = re.compile(r"get_(\w+)\(\)")

    for line_num, line in enumerate(lines, 1):
        # Check for direct instantiation
        for match in direct_instantiation_pattern.finditer(line):
            singleton_patterns.append(
                SingletonUsage(
                    singleton_class=match.group(1),
                    usage_pattern="direct_instantiation",
                    file_path=file_path,
                    line_number=line_num,
                    context=line.strip(),
                )
            )

        # Check for factory functions
        for match in factory_function_pattern.finditer(line):
            class_name = _map_factory_to_class(f"get_{match.group(1)}")
            singleton_patterns.append(
                SingletonUsage(
                    singleton_class=class_name,
                    usage_pattern="factory_function",
                    file_path=file_path,
                    line_number=line_num,
                    context=line.strip(),
                )
            )

    return singleton_patterns

def _is_click_command_decorator(decorator: ast.expr) -> bool:
    """Check if a decorator is a Click command decorator."""
    if isinstance(decorator, ast.Name):
        return decorator.id in {"command", "group"}
    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
        return decorator.func.id in {"command", "group", "spec_command"}
    elif isinstance(decorator, ast.Attribute):
        # Handle click.command, click.group patterns
        if isinstance(decorator.value, ast.Name) and decorator.value.id == "click":
            return decorator.attr in {"command", "group"}
        return decorator.attr in {"command", "group"}
    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        # Handle @click.command(), @click.group() patterns
        if (
            isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "click"
        ):
            return decorator.func.attr in {"command", "group"}
    return False

def _analyze_click_decorator(
    decorator: ast.expr, func_name: str, file_path: str, line_num: int
) -> ClickPattern | None:
    """Analyze a decorator to extract Click pattern information."""
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
        decorator_name = decorator.func.id
        if decorator_name in {"command", "group", "spec_command"}:
            return ClickPattern(
                decorator_name=decorator_name,
                function_name=func_name,
                file_path=file_path,
                line_number=line_num,
                is_command=decorator_name in {"command", "spec_command"},
                is_group=decorator_name == "group",
            )
    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        # Handle @click.command(), @click.group() patterns
        if (
            isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "click"
        ):
            decorator_name = decorator.func.attr
            return ClickPattern(
                decorator_name=decorator_name,
                function_name=func_name,
                file_path=file_path,
                line_number=line_num,
                is_command=decorator_name == "command",
                is_group=decorator_name == "group",
            )
    elif isinstance(decorator, ast.Name):
        if decorator.id in {"command", "group"}:
            return ClickPattern(
                decorator_name=decorator.id,
                function_name=func_name,
                file_path=file_path,
                line_number=line_num,
                is_command=decorator.id == "command",
                is_group=decorator.id == "group",
            )
    elif isinstance(decorator, ast.Attribute):
        # Handle click.command without parentheses
        if isinstance(decorator.value, ast.Name) and decorator.value.id == "click":
            decorator_name = decorator.attr
            return ClickPattern(
                decorator_name=decorator_name,
                function_name=func_name,
                file_path=file_path,
                line_number=line_num,
                is_command=decorator_name == "command",
                is_group=decorator_name == "group",
            )

    return None

def _map_factory_to_class(factory_function: str) -> str:
    """Map factory function names to their corresponding class names."""
    factory_mapping = {
        "get_spec_repository": "SpecGitRepository",
        "get_console": "Console",
        "get_progress_manager": "ProgressManager",
        "get_debug_logger": "DebugLogger",
    }

    return factory_mapping.get(factory_function, "Unknown")
