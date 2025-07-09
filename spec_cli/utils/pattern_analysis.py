"""Singleton pattern analysis utilities for dependency injection migration planning.

This module provides tools to analyze existing singleton usage patterns in the codebase
to support the creation of compatibility wrappers during the migration to dependency injection.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..exceptions import PatternAnalysisError
from ..logging.debug import debug_logger
from .error_utils import handle_os_error


@dataclass
class SingletonUsage:
    """Represents a singleton usage found in code analysis."""

    file_path: Path
    line_number: int
    usage_type: str  # "class_definition", "instantiation", "method_call", "import"
    singleton_name: str
    context: str  # The actual code line or context
    function_name: str | None = None
    class_name: str | None = None


@dataclass
class AccessPatternReport:
    """Report of access patterns for a specific singleton class."""

    singleton_name: str
    total_usages: int
    usage_locations: list[SingletonUsage]
    access_methods: set[str]  # Direct instantiation, function calls, etc.
    wrapper_requirements: list[str]  # Requirements for compatibility wrapper


def analyze_singleton_usage(file_path: Path) -> list[SingletonUsage]:
    """Analyze a Python file for singleton usage patterns.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        List of singleton usage instances found

    Raises:
        PatternAnalysisError: If file analysis fails or file is invalid
        FileNotFoundError: If file does not exist

    Example:
        >>> from pathlib import Path
        >>> usages = analyze_singleton_usage(Path("my_module.py"))
        >>> print(f"Found {len(usages)} singleton usages")
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.suffix == ".py":
        debug_logger.log("DEBUG", "Skipping non-Python file", file_path=str(file_path))
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
        debug_logger.log(
            "DEBUG", "Analyzing file for singleton patterns", file_path=str(file_path)
        )

        usages = []

        # Parse AST for structured analysis
        try:
            tree = ast.parse(content, filename=str(file_path))
            usages.extend(_analyze_ast_for_singletons(tree, file_path))
        except SyntaxError as e:
            debug_logger.log(
                "WARNING",
                "Failed to parse AST, falling back to regex analysis",
                file_path=str(file_path),
                error=str(e),
            )

        # Supplement with regex-based analysis for edge cases
        usages.extend(_analyze_regex_for_singletons(content, file_path))

        # Remove duplicates while preserving order
        unique_usages = []
        seen = set()
        for usage in usages:
            key = (
                usage.file_path,
                usage.line_number,
                usage.usage_type,
                usage.singleton_name,
            )
            if key not in seen:
                unique_usages.append(usage)
                seen.add(key)

        debug_logger.log(
            "INFO",
            "Singleton analysis completed",
            file_path=str(file_path),
            usage_count=len(unique_usages),
        )

        return unique_usages

    except UnicodeDecodeError as e:
        raise PatternAnalysisError(
            f"Failed to decode file encoding for {file_path}: {e}"
        ) from e
    except OSError as e:
        formatted_error = handle_os_error(e)
        raise PatternAnalysisError(
            f"Failed to analyze singleton patterns in {file_path}: {formatted_error}"
        ) from e


def _analyze_ast_for_singletons(tree: ast.AST, file_path: Path) -> list[SingletonUsage]:
    """Analyze AST for singleton patterns.

    Args:
        tree: Parsed AST tree
        file_path: Source file path

    Returns:
        List of singleton usages found in AST
    """
    usages = []

    class SingletonVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.current_function: str | None = None
            self.current_class: str | None = None

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            old_class = self.current_class
            self.current_class = node.name

            # Check for singleton class definitions
            if _is_singleton_class(node):
                usages.append(
                    SingletonUsage(
                        file_path=file_path,
                        line_number=node.lineno,
                        usage_type="class_definition",
                        singleton_name=node.name,
                        context=f"class {node.name}",
                        class_name=node.name,
                    )
                )

            self.generic_visit(node)
            self.current_class = old_class

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            old_function = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_function

        def visit_Call(self, node: ast.Call) -> None:
            # Check for singleton instantiation or method calls
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if _is_singleton_name(name):
                    usages.append(
                        SingletonUsage(
                            file_path=file_path,
                            line_number=node.lineno,
                            usage_type="instantiation",
                            singleton_name=name,
                            context=f"{name}()",
                            function_name=self.current_function,
                            class_name=self.current_class,
                        )
                    )
            elif isinstance(node.func, ast.Attribute):
                # Handle method calls on singleton instances
                if isinstance(node.func.value, ast.Call) and isinstance(
                    node.func.value.func, ast.Name
                ):
                    base_name = node.func.value.func.id
                    method_name = node.func.attr
                    if _is_singleton_name(base_name):
                        usages.append(
                            SingletonUsage(
                                file_path=file_path,
                                line_number=node.lineno,
                                usage_type="method_call",
                                singleton_name=base_name,
                                context=f"{base_name}().{method_name}()",
                                function_name=self.current_function,
                                class_name=self.current_class,
                            )
                        )

            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                if _is_singleton_import(alias.name):
                    usages.append(
                        SingletonUsage(
                            file_path=file_path,
                            line_number=node.lineno,
                            usage_type="import",
                            singleton_name=alias.name.split(".")[-1],
                            context=f"import {alias.name}",
                            function_name=self.current_function,
                            class_name=self.current_class,
                        )
                    )
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module and _is_singleton_module(node.module):
                for alias in node.names:
                    if _is_singleton_name(alias.name):
                        usages.append(
                            SingletonUsage(
                                file_path=file_path,
                                line_number=node.lineno,
                                usage_type="import",
                                singleton_name=alias.name,
                                context=f"from {node.module} import {alias.name}",
                                function_name=self.current_function,
                                class_name=self.current_class,
                            )
                        )
            self.generic_visit(node)

    visitor = SingletonVisitor()
    visitor.visit(tree)
    return usages


def _analyze_regex_for_singletons(
    content: str, file_path: Path
) -> list[SingletonUsage]:
    """Analyze file content using regex patterns for singleton detection.

    Args:
        content: File content to analyze
        file_path: Source file path

    Returns:
        List of singleton usages found via regex
    """
    usages = []
    lines = content.splitlines()

    # Patterns to detect singleton usage
    singleton_patterns = [
        (r"SingletonMeta", "metaclass_reference"),
        (r"@singleton_decorator", "decorator_singleton"),
        (r"ProgressManagerSingleton", "progress_singleton_instantiation"),
        (r"get_progress_manager\(\)", "progress_singleton_access"),
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern, usage_type in singleton_patterns:
            if re.search(pattern, line):
                # Extract singleton name from context
                singleton_name = _extract_singleton_name_from_line(line, pattern)

                usages.append(
                    SingletonUsage(
                        file_path=file_path,
                        line_number=line_num,
                        usage_type=usage_type,
                        singleton_name=singleton_name,
                        context=line.strip(),
                    )
                )

    return usages


def _is_singleton_class(node: ast.ClassDef) -> bool:
    """Check if a class definition uses singleton patterns."""
    # Check for metaclass=SingletonMeta
    for keyword in node.keywords:
        if keyword.arg == "metaclass" and isinstance(keyword.value, ast.Name):
            if keyword.value.id == "SingletonMeta":
                return True

    for decorator in node.decorator_list:
        if hasattr(decorator, "id") and "singleton" in getattr(decorator, "id", ""):
            return True

    # Check for "Singleton" in class name
    return "Singleton" in node.name


def _is_singleton_name(name: str) -> bool:
    """Check if a name indicates a singleton class or pattern."""
    singleton_indicators = ["Singleton", "ProgressManagerSingleton", "SingletonMeta"]
    return any(indicator in name for indicator in singleton_indicators)


def _is_singleton_import(module_name: str) -> bool:
    """Check if a module contains singleton imports."""
    singleton_modules = ["singleton", "progress_manager"]
    return any(mod in module_name for mod in singleton_modules)


def _is_singleton_module(module_name: str) -> bool:
    """Check if a module contains singleton functionality."""
    return _is_singleton_import(module_name)


def _extract_singleton_name_from_line(line: str, pattern: str) -> str:
    """Extract singleton name from a line of code."""
    # Try to extract specific class names first
    if "ProgressManagerSingleton" in line:
        return "ProgressManagerSingleton"
    elif "ProgressManager" in line:
        return "ProgressManagerSingleton"
    elif "SingletonMeta" in line:
        return "SingletonMeta"

    # Generic singleton pattern match
    match = re.search(r"(\w*[Ss]ingleton\w*)", line)
    if match:
        return match.group(1).strip()
    return "unknown_singleton"


def document_access_patterns(
    singleton_name: str, usages: list[SingletonUsage]
) -> AccessPatternReport:
    """Document access patterns for a specific singleton class.

    Args:
        singleton_name: Name of the singleton class to analyze
        usages: List of all singleton usages to filter

    Returns:
        Access pattern report with wrapper requirements

    Example:
        >>> usages = analyze_singleton_usage(Path("my_module.py"))
        >>> report = document_access_patterns("ProgressManagerSingleton", usages)
        >>> print(f"Found {report.total_usages} usages of {report.singleton_name}")
    """
    # Filter usages for the specific singleton
    singleton_usages = [
        usage
        for usage in usages
        if usage.singleton_name == singleton_name
        or singleton_name in usage.singleton_name
    ]

    # Extract access methods
    access_methods = set()
    for usage in singleton_usages:
        if usage.usage_type == "instantiation":
            access_methods.add("direct_instantiation")
        elif usage.usage_type == "method_call":
            access_methods.add("method_call")
        elif usage.usage_type == "import":
            access_methods.add("import_reference")

        # Check context for specific patterns
        if "get_progress_manager" in usage.context:
            access_methods.add("convenience_function")
        if "set_progress_manager" in usage.context:
            access_methods.add("convenience_function")
        if "reset" in usage.context.lower():
            access_methods.add("reset_function")

    # Generate wrapper requirements based on access patterns
    wrapper_requirements = _generate_wrapper_requirements(
        singleton_name, access_methods, singleton_usages
    )

    debug_logger.log(
        "INFO",
        "Access pattern documentation completed",
        singleton_name=singleton_name,
        total_usages=len(singleton_usages),
        access_methods=list(access_methods),
    )

    return AccessPatternReport(
        singleton_name=singleton_name,
        total_usages=len(singleton_usages),
        usage_locations=singleton_usages,
        access_methods=access_methods,
        wrapper_requirements=wrapper_requirements,
    )


def _generate_wrapper_requirements(
    singleton_name: str, access_methods: set[str], usages: list[SingletonUsage]
) -> list[str]:
    """Generate wrapper requirements based on usage patterns."""
    requirements = []

    # Base requirements for all singletons
    requirements.append("Maintain thread-safe access during migration")
    requirements.append("Preserve existing public API interface")

    # Requirements based on access methods
    if "direct_instantiation" in access_methods:
        requirements.append("Support direct class instantiation: ClassName()")

    if "convenience_function" in access_methods:
        requirements.append("Maintain convenience function compatibility")

    if "method_call" in access_methods:
        requirements.append("Support chained method calls: ClassName().method()")

    if "reset_function" in access_methods:
        requirements.append("Provide reset functionality for testing")

    # Specific requirements for ProgressManagerSingleton
    if "ProgressManager" in singleton_name:
        requirements.extend(
            [
                "Support get_progress_manager() function",
                "Support set_progress_manager(manager) function",
                "Support reset_progress_manager() function",
                "Maintain progress state across calls",
                "Thread-safe progress manager instance management",
            ]
        )

    # Requirements based on usage locations
    test_files = [usage for usage in usages if "test" in str(usage.file_path)]
    if test_files:
        requirements.append("Provide test utilities for instance reset and mocking")

    return requirements
