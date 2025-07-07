"""Singleton pattern detection utilities for continuous validation.

This module provides utilities to detect singleton patterns in Python code using AST parsing.
It identifies metaclass-based singletons, decorator patterns, and import-based singleton usage.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

from ..exceptions import SpecError


class SingletonDetectionError(SpecError):
    """Exception raised when singleton detection fails."""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        super().__init__(message)
        self.file_path = file_path

@dataclass
class SingletonViolation:
    """Represents a detected singleton pattern violation."""

    file_path: Path
    line_number: int
    column: int
    pattern_type: str
    description: str
    code_snippet: str

@dataclass
class ASTAnalysisReport:
    """Report from AST analysis of a Python file."""

    file_path: Path
    violations: list[SingletonViolation]
    imports: set[str]
    classes: set[str]
    decorators: set[str]
    metaclasses: set[str]

class SingletonPatternDetector:
    """Detects singleton patterns in Python AST nodes."""

    SINGLETON_METACLASS_NAMES = {
        "SingletonMeta",
        "Singleton",
        "SingletonType",
        "MetaSingleton",
    }

    SINGLETON_DECORATOR_NAMES = {
        "singleton",
        "@singleton",
    }

    SINGLETON_IMPORT_PATTERNS = {
        "singleton",
        "SingletonMeta",
    }

    def __init__(self) -> None:
        self.violations: list[SingletonViolation] = []
        self.current_file: Path | None = None

    def detect_violations(self, file_path: Path) -> list[SingletonViolation]:
        """Detect singleton violations in a Python file.

        Args:
            file_path: Path to Python file to analyze

        Returns:
            List of detected singleton violations

        Raises:
            SingletonDetectionError: If file cannot be parsed or analyzed
        """
        self.current_file = file_path
        self.violations = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except (OSError, UnicodeDecodeError) as e:
            raise SingletonDetectionError(f"Cannot read file: {e}", file_path) from e
        except SyntaxError as e:
            raise SingletonDetectionError(
                f"Cannot parse Python file: {e}", file_path
            ) from e

        self.visit_node(tree)
        return self.violations

    def visit_node(self, node: ast.AST) -> None:
        """Visit AST node and detect singleton patterns."""
        if isinstance(node, ast.ClassDef):
            self._check_class_definition(node)
        elif isinstance(node, ast.Import):
            self._check_import_statement(node)
        elif isinstance(node, ast.ImportFrom):
            self._check_import_from_statement(node)
        elif isinstance(node, ast.FunctionDef):
            self._check_function_decorators(node)

        # Recursively visit child nodes
        for child in ast.iter_child_nodes(node):
            self.visit_node(child)

    def _check_class_definition(self, node: ast.ClassDef) -> None:
        """Check class definition for singleton patterns."""
        # Check metaclass usage
        for keyword in node.keywords:
            if keyword.arg == "metaclass" and isinstance(keyword.value, ast.Name):
                if keyword.value.id in self.SINGLETON_METACLASS_NAMES:
                    self._add_violation(
                        node,
                        "metaclass_singleton",
                        f"Class uses singleton metaclass: {keyword.value.id}",
                    )

        # Check class decorators
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name in self.SINGLETON_DECORATOR_NAMES:
                self._add_violation(
                    node,
                    "decorator_singleton",
                    f"Class uses singleton decorator: {decorator_name}",
                )

    def _check_import_statement(self, node: ast.Import) -> None:
        """Check Import statements for singleton module imports."""
        for alias in node.names:
            if any(pattern in alias.name for pattern in self.SINGLETON_IMPORT_PATTERNS):
                self._add_violation(
                    node,
                    "import_singleton",
                    f"Import of singleton module: {alias.name}",
                )

    def _check_import_from_statement(self, node: ast.ImportFrom) -> None:
        """Check ImportFrom statements for singleton module imports."""
        if node.module and any(
            pattern in node.module for pattern in self.SINGLETON_IMPORT_PATTERNS
        ):
            self._add_violation(
                node,
                "import_from_singleton",
                f"Import from singleton module: {node.module}",
            )

        for alias in node.names:
            if alias.name in self.SINGLETON_IMPORT_PATTERNS:
                self._add_violation(
                    node,
                    "import_singleton_name",
                    f"Import of singleton name: {alias.name}",
                )

    def _check_function_decorators(self, node: ast.FunctionDef) -> None:
        """Check function decorators for singleton patterns."""
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name in self.SINGLETON_DECORATOR_NAMES:
                self._add_violation(
                    node,
                    "function_decorator_singleton",
                    f"Function uses singleton decorator: {decorator_name}",
                )

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            return decorator.func.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""

    def _add_violation(
        self, node: ast.AST, pattern_type: str, description: str
    ) -> None:
        """Add a singleton violation to the results."""
        if not self.current_file:
            return

        violation = SingletonViolation(
            file_path=self.current_file,
            line_number=getattr(node, "lineno", 0),
            column=getattr(node, "col_offset", 0),
            pattern_type=pattern_type,
            description=description,
            code_snippet=self._extract_code_snippet(node),
        )
        self.violations.append(violation)

    def _extract_code_snippet(self, node: ast.AST) -> str:
        """Extract code snippet from AST node."""
        if not self.current_file:
            return ""

        try:
            lines = self.current_file.read_text(encoding="utf-8").splitlines()
            line_num = getattr(node, "lineno", 1) - 1
            if 0 <= line_num < len(lines):
                return lines[line_num].strip()
        except (OSError, UnicodeDecodeError):
            pass
        return ""

def scan_for_singleton_patterns(file_path: Path) -> list[SingletonViolation]:
    """Scan a Python file for singleton patterns.

    Args:
        file_path: Path to Python file to scan

    Returns:
        List of detected singleton violations

    Raises:
        SingletonDetectionError: If file cannot be analyzed
    """
    detector = SingletonPatternDetector()
    return detector.detect_violations(file_path)

def analyze_python_ast(file_path: Path) -> ASTAnalysisReport:
    """Analyze Python file AST for singleton patterns and metadata.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        AST analysis report with violations and metadata

    Raises:
        SingletonDetectionError: If file cannot be analyzed
    """
    detector = SingletonPatternDetector()
    violations = detector.detect_violations(file_path)

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except (OSError, UnicodeDecodeError) as e:
        raise SingletonDetectionError(f"Cannot read file: {e}", file_path) from e
    except SyntaxError as e:
        raise SingletonDetectionError(
            f"Cannot parse Python file: {e}", file_path
        ) from e

    # Extract metadata
    imports = set()
    classes = set()
    decorators = set()
    metaclasses = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.ClassDef):
            classes.add(node.name)
            for keyword in node.keywords:
                if keyword.arg == "metaclass" and isinstance(keyword.value, ast.Name):
                    metaclasses.add(keyword.value.id)
            for decorator in node.decorator_list:
                decorator_name = detector._get_decorator_name(decorator)
                if decorator_name:
                    decorators.add(decorator_name)
        elif isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                decorator_name = detector._get_decorator_name(decorator)
                if decorator_name:
                    decorators.add(decorator_name)

    return ASTAnalysisReport(
        file_path=file_path,
        violations=violations,
        imports=imports,
        classes=classes,
        decorators=decorators,
        metaclasses=metaclasses,
    )
