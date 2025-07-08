"""Dependency analysis utilities for validating and analyzing codebase dependencies.

This module provides utilities for validating dependency existence, analyzing current
usage patterns, and generating dependency requirements for SpecContext implementation.
"""

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.context_bridge import debug_logger
from .error_utils import create_error_context


@dataclass
class DependencyUsage:
    """Represents usage of a dependency in the codebase.

    Attributes:
        file_path: Path to file where dependency is used
        line_number: Line number where dependency is referenced
        usage_type: Type of usage (import, instantiation, method_call)
        context: Additional context about the usage
    """

    file_path: str
    line_number: int
    usage_type: str
    context: str


@dataclass
class DependencyReport:
    """Comprehensive dependency analysis report.

    Attributes:
        dependency_name: Name of the analyzed dependency
        exists: Whether the dependency exists in codebase
        usage_patterns: List of DependencyUsage instances
        import_paths: Set of import paths where dependency is found
        requirements: Specification requirements for SpecContext
        analysis_errors: Any errors encountered during analysis
    """

    dependency_name: str
    exists: bool
    usage_patterns: list[DependencyUsage]
    import_paths: set[str]
    requirements: dict[str, Any]
    analysis_errors: list[str]


class DependencyValidationError(Exception):
    """Exception raised when dependency validation fails."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize DependencyValidationError with message and context.

        Args:
            message: Error message describing the validation failure
            context: Optional context dictionary with additional error details
        """
        super().__init__(message)
        self.context = context or {}


def validate_dependency_exists(import_path: str) -> bool:
    """Validate that a dependency import path exists and can be imported.

    Args:
        import_path: Import path to validate (e.g., "spec_cli.config.settings")

    Returns:
        True if dependency exists and can be imported, False otherwise

    Example:
        exists = validate_dependency_exists("spec_cli.config.settings")
        if not exists:
            print("Settings dependency not found")
    """
    debug_logger.log(
        "DEBUG", "Validating dependency import path", import_path=import_path
    )

    try:
        # Try to find the module spec
        spec = importlib.util.find_spec(import_path)
        if spec is None:
            debug_logger.log(
                "WARNING", "Dependency import path not found", import_path=import_path
            )
            return False

        # Try to import the module
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            debug_logger.log(
                "WARNING", "Dependency loader not available", import_path=import_path
            )
            return False

        spec.loader.exec_module(module)

        debug_logger.log(
            "INFO", "Dependency validation successful", import_path=import_path
        )
        return True

    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        debug_logger.log(
            "WARNING",
            "Dependency import failed",
            import_path=import_path,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


def analyze_current_usage(dependency_name: str, codebase_path: Path) -> list[str]:
    """Analyze current usage patterns of a dependency in the codebase.

    Args:
        dependency_name: Name of dependency to analyze (e.g., "settings", "console")
        codebase_path: Path to codebase root directory

    Returns:
        List of file paths where dependency is used

    Raises:
        DependencyValidationError: If codebase_path doesn't exist or analysis fails

    Example:
        usage_files = analyze_current_usage("settings", Path("spec_cli"))
        print(f"Settings used in {len(usage_files)} files")
    """
    if not codebase_path.exists():
        error_context = create_error_context(codebase_path)
        raise DependencyValidationError(
            f"Codebase path does not exist: {codebase_path}", error_context
        )

    debug_logger.log(
        "DEBUG",
        "Analyzing dependency usage patterns",
        dependency_name=dependency_name,
        codebase_path=str(codebase_path),
    )

    usage_files = []

    try:
        # Search through Python files
        for py_file in codebase_path.rglob("*.py"):
            if _file_uses_dependency(py_file, dependency_name):
                usage_files.append(str(py_file))

        debug_logger.log(
            "INFO",
            "Dependency usage analysis completed",
            dependency_name=dependency_name,
            files_found=len(usage_files),
            files=usage_files[:5]
            if len(usage_files) <= 5
            else usage_files[:5] + ["..."],
        )

        return usage_files

    except OSError as e:
        error_context = create_error_context(codebase_path)
        error_context.update({"dependency_name": dependency_name})
        raise DependencyValidationError(
            f"Failed to analyze dependency usage: {e}", error_context
        ) from e


def generate_dependency_report(
    dependency_names: list[str], codebase_path: Path
) -> dict[str, DependencyReport]:
    """Generate comprehensive dependency analysis report for multiple dependencies.

    Args:
        dependency_names: List of dependency names to analyze
        codebase_path: Path to codebase root directory

    Returns:
        Dictionary mapping dependency names to DependencyReport objects

    Raises:
        DependencyValidationError: If analysis fails for critical dependencies

    Example:
        reports = generate_dependency_report(
            ["settings", "console", "progress"],
            Path("spec_cli")
        )
        for name, report in reports.items():
            print(f"{name}: {'EXISTS' if report.exists else 'MISSING'}")
    """
    debug_logger.log(
        "INFO",
        "Generating comprehensive dependency report",
        dependency_count=len(dependency_names),
        dependencies=dependency_names,
        codebase_path=str(codebase_path),
    )

    reports = {}

    for dep_name in dependency_names:
        try:
            report = _analyze_single_dependency(dep_name, codebase_path)
            reports[dep_name] = report

        except Exception as e:
            # Create error report for failed dependency analysis
            reports[dep_name] = DependencyReport(
                dependency_name=dep_name,
                exists=False,
                usage_patterns=[],
                import_paths=set(),
                requirements={},
                analysis_errors=[str(e)],
            )

            debug_logger.log(
                "ERROR",
                "Dependency analysis failed",
                dependency_name=dep_name,
                error=str(e),
                error_type=type(e).__name__,
            )

    debug_logger.log(
        "INFO",
        "Dependency report generation completed",
        total_dependencies=len(dependency_names),
        successful_analyses=len([r for r in reports.values() if not r.analysis_errors]),
        failed_analyses=len([r for r in reports.values() if r.analysis_errors]),
    )

    return reports


def _file_uses_dependency(file_path: Path, dependency_name: str) -> bool:
    """Check if a Python file uses a specific dependency.

    Args:
        file_path: Path to Python file to analyze
        dependency_name: Name of dependency to search for

    Returns:
        True if file uses dependency, False otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Simple text search for dependency name (case-insensitive)
        dependency_lower = dependency_name.lower()
        content_lower = content.lower()

        # Check for common usage patterns
        patterns = [
            f"import {dependency_lower}",
            f"from {dependency_lower}",
            f".{dependency_lower}",
            f"{dependency_lower}(",
            f"{dependency_lower}.",
            f"class {dependency_lower.title()}",
            f"def {dependency_lower}",
        ]

        for pattern in patterns:
            if pattern in content_lower:
                return True

        return False

    except (OSError, UnicodeDecodeError):
        # Skip files that can't be read
        return False


def _analyze_single_dependency(
    dependency_name: str, codebase_path: Path
) -> DependencyReport:
    """Analyze a single dependency and generate detailed report.

    Args:
        dependency_name: Name of dependency to analyze
        codebase_path: Path to codebase root directory

    Returns:
        DependencyReport for the analyzed dependency
    """
    debug_logger.log(
        "DEBUG", "Analyzing single dependency", dependency_name=dependency_name
    )

    # Check if dependency exists via import validation
    common_import_paths = [
        f"spec_cli.{dependency_name}",
        f"spec_cli.config.{dependency_name}",
        f"spec_cli.core.{dependency_name}",
        f"spec_cli.ui.{dependency_name}",
    ]

    exists = False
    found_import_paths = set()

    for import_path in common_import_paths:
        if validate_dependency_exists(import_path):
            exists = True
            found_import_paths.add(import_path)

    # Analyze usage patterns
    usage_files = analyze_current_usage(dependency_name, codebase_path)
    usage_patterns = []

    for file_path in usage_files:
        # Create basic usage pattern entry
        usage_patterns.append(
            DependencyUsage(
                file_path=file_path,
                line_number=0,  # Simplified - would need AST parsing for exact lines
                usage_type="reference",
                context=f"File references {dependency_name}",
            )
        )

    # Generate requirements based on usage patterns
    requirements = _generate_context_requirements(dependency_name, usage_patterns)

    return DependencyReport(
        dependency_name=dependency_name,
        exists=exists,
        usage_patterns=usage_patterns,
        import_paths=found_import_paths,
        requirements=requirements,
        analysis_errors=[],
    )


def _generate_context_requirements(
    dependency_name: str, usage_patterns: list[DependencyUsage]
) -> dict[str, Any]:
    """Generate SpecContext requirements based on dependency usage patterns.

    Args:
        dependency_name: Name of the dependency
        usage_patterns: List of usage patterns found in codebase

    Returns:
        Dictionary containing SpecContext requirements for this dependency
    """
    requirements: dict[str, Any] = {
        "name": dependency_name,
        "required": len(usage_patterns) > 0,
        "usage_count": len(usage_patterns),
        "interface_requirements": [],
        "injection_points": [],
    }

    # Determine interface requirements based on dependency name
    if dependency_name.lower() in ["settings", "config"]:
        requirements["interface_requirements"] = [
            "debug_enabled: bool",
            "console_width: int",
            "use_color: bool",
            "get_setting(key: str) -> Any",
        ]
    elif dependency_name.lower() in ["console", "ui"]:
        requirements["interface_requirements"] = [
            "print_message(text: str) -> None",
            "print_error(text: str) -> None",
            "get_width() -> int",
            "supports_color() -> bool",
        ]
    elif dependency_name.lower() in ["progress", "progressbar"]:
        requirements["interface_requirements"] = [
            "show_progress(current: int, total: int) -> None",
            "update_status(status: str) -> None",
            "finish() -> None",
        ]

    # Identify injection points from usage patterns
    for pattern in usage_patterns:
        if pattern.usage_type == "reference":
            requirements["injection_points"].append(
                {"file": pattern.file_path, "type": "constructor_injection"}
            )

    return requirements
