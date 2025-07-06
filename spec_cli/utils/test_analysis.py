"""Test fixture analysis for migration to context-based dependency injection.

This module provides comprehensive analysis of existing test fixtures and identifies
migration requirements for converting singleton-dependent tests to context-based
dependency injection patterns.
"""

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .error_utils import SpecAnalysisError

@dataclass
class FixtureInfo:
    """Information about a single pytest fixture."""

    name: str
    file_path: Path
    line_number: int
    scope: str = "function"
    autouse: bool = False
    singleton_dependencies: list[str] = field(default_factory=list)
    state_contamination_risk: bool = False
    context_migration_required: bool = False

@dataclass
class FixtureAnalysisReport:
    """Comprehensive report of test fixture analysis."""

    total_fixtures: int = 0
    singleton_dependent_fixtures: list[FixtureInfo] = field(default_factory=list)
    isolation_issues: list[FixtureInfo] = field(default_factory=list)
    context_migration_candidates: list[FixtureInfo] = field(default_factory=list)
    migration_requirements: dict[str, str] = field(default_factory=dict)
    analysis_summary: str = ""

class FixtureAnalysisError(SpecAnalysisError):
    """Error during test fixture analysis."""

def analyze_test_fixtures(test_dir: Path) -> FixtureAnalysisReport:
    """Analyze existing test fixture structure and patterns.

    Scans all test files in the provided directory to identify fixtures,
    their dependencies, and requirements for migration to context-based
    dependency injection.

    Args:
        test_dir: Path to test directory to analyze

    Returns:
        FixtureAnalysisReport with comprehensive fixture analysis

    Raises:
        FixtureAnalysisError: If test directory analysis fails

    Example:
        report = analyze_test_fixtures(Path("tests"))
        print(f"Found {report.total_fixtures} fixtures")
        for fixture in report.singleton_dependent_fixtures:
            print(f"Fixture {fixture.name} needs migration")
    """
    if not test_dir.exists():
        raise FixtureAnalysisError(f"Test directory does not exist: {test_dir}")

    if not test_dir.is_dir():
        raise FixtureAnalysisError(f"Path is not a directory: {test_dir}")

    try:
        fixtures = _discover_fixtures(test_dir)
        singleton_deps = _analyze_singleton_dependencies(fixtures)
        isolation_issues = _identify_isolation_issues(fixtures)

        migration_candidates = _identify_migration_candidates(fixtures)

        report = FixtureAnalysisReport(
            total_fixtures=len(fixtures),
            singleton_dependent_fixtures=singleton_deps,
            isolation_issues=isolation_issues,
            context_migration_candidates=migration_candidates,
            migration_requirements=_generate_migration_requirements(
                migration_candidates
            ),
            analysis_summary=_create_analysis_summary(
                fixtures, singleton_deps, isolation_issues
            ),
        )

        return report

    except Exception as e:
        raise FixtureAnalysisError(f"Failed to analyze test fixtures: {e}") from e

def identify_singleton_dependencies(fixture_func: Callable) -> list[str]:
    """Identify singleton dependencies in a fixture function.

    Analyzes the source code of a fixture function to detect patterns
    that indicate dependency on singleton infrastructure that needs
    migration to context-based injection.

    Args:
        fixture_func: Function object to analyze for singleton patterns

    Returns:
        List of singleton dependency names found in the function

    Raises:
        FixtureAnalysisError: If function analysis fails

    Example:
        deps = identify_singleton_dependencies(my_fixture)
        if "get_settings" in deps:
            print("Fixture uses singleton settings access")
    """
    try:
        if not hasattr(fixture_func, "__code__"):
            return []

        # Get source file path
        code_obj = fixture_func.__code__
        filename = code_obj.co_filename

        if not Path(filename).exists():
            return []

        # Read source file and parse
        source = Path(filename).read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find the function node
        func_name = fixture_func.__name__
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return _extract_singleton_patterns(node)

        return []

    except Exception as e:
        raise FixtureAnalysisError(f"Failed to analyze fixture function: {e}") from e

def _discover_fixtures(test_dir: Path) -> list[FixtureInfo]:
    """Discover all pytest fixtures in test directory."""
    fixtures = []

    # Search for Python test files
    test_files = list(test_dir.rglob("*.py"))

    for test_file in test_files:
        if test_file.name.startswith("test_") or test_file.name == "conftest.py":
            file_fixtures = _parse_fixtures_from_file(test_file)
            fixtures.extend(file_fixtures)

    return fixtures

def _parse_fixtures_from_file(file_path: Path) -> list[FixtureInfo]:
    """Parse fixtures from a single test file."""
    fixtures = []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fixture_info = _extract_fixture_info(node, file_path)
                if fixture_info:
                    fixtures.append(fixture_info)

    except Exception:
        # Skip files that can't be parsed
        pass

    return fixtures

def _extract_fixture_info(
    func_node: ast.FunctionDef, file_path: Path
) -> FixtureInfo | None:
    """Extract fixture information from function node."""
    # Check if function has pytest.fixture decorator
    for decorator in func_node.decorator_list:
        if _is_pytest_fixture_decorator(decorator):
            return FixtureInfo(
                name=func_node.name,
                file_path=file_path,
                line_number=func_node.lineno,
                scope=_extract_fixture_scope(decorator),
                autouse=_extract_autouse_flag(decorator),
                singleton_dependencies=_extract_singleton_patterns(func_node),
                state_contamination_risk=_assess_contamination_risk(func_node),
                context_migration_required=_requires_context_migration(func_node),
            )

    return None

def _is_pytest_fixture_decorator(decorator: ast.expr) -> bool:
    """Check if decorator is pytest.fixture."""
    if isinstance(decorator, ast.Name) and decorator.id == "pytest.fixture":
        return True
    if isinstance(decorator, ast.Attribute):
        if (
            isinstance(decorator.value, ast.Name)
            and decorator.value.id == "pytest"
            and decorator.attr == "fixture"
        ):
            return True
    if isinstance(decorator, ast.Call):
        return _is_pytest_fixture_decorator(decorator.func)

    return False

def _extract_fixture_scope(decorator: ast.expr) -> str:
    """Extract scope from fixture decorator."""
    if isinstance(decorator, ast.Call):
        for keyword in decorator.keywords:
            if keyword.arg == "scope" and isinstance(keyword.value, ast.Constant):
                return str(keyword.value.value)
    return "function"

def _extract_autouse_flag(decorator: ast.expr) -> bool:
    """Extract autouse flag from fixture decorator."""
    if isinstance(decorator, ast.Call):
        for keyword in decorator.keywords:
            if keyword.arg == "autouse" and isinstance(keyword.value, ast.Constant):
                return bool(keyword.value.value)
    return False

def _extract_singleton_patterns(func_node: ast.FunctionDef) -> list[str]:
    """Extract singleton dependency patterns from function."""
    patterns = []

    # Get the actual source code using ast.unparse
    try:
        source = ast.unparse(func_node)
    except Exception:
        # Fallback for older Python versions or if unparse fails
        source = ""

    # Patterns to detect singleton usage
    singleton_patterns = {
        r"get_settings\s*\(",
        r"get_console\s*\(",
        r"reset_console\s*\(",
        r"spec_console\.",
        r"SpecSettings\s*\(",
        r"SpecConsole\s*\(",
        r"\.instance\s*\(",
        r"@singleton",
        r"SingletonMeta",
    }

    for pattern in singleton_patterns:
        if re.search(pattern, source):
            # Clean up pattern name for reporting
            clean_pattern = (
                pattern.replace(r"\s*\(", "")
                .replace(r"\s*", "")
                .replace("\\", "")
                .replace("(", "")
                .replace(".", "")
                .replace("@", "")
            )
            patterns.append(clean_pattern)

    return patterns

def _assess_contamination_risk(func_node: ast.FunctionDef) -> bool:
    """Assess if fixture has state contamination risk."""
    # Look for global state access patterns
    contamination_indicators = [
        "os.environ",
        "os.chdir",
        "sys.modules",
        "global ",
        "patch.object",
        "monkeypatch",
    ]

    source = ast.unparse(func_node)
    return any(indicator in source for indicator in contamination_indicators)

def _requires_context_migration(func_node: ast.FunctionDef) -> bool:
    """Determine if fixture requires context-based migration."""
    singleton_deps = _extract_singleton_patterns(func_node)
    contamination_risk = _assess_contamination_risk(func_node)
    return len(singleton_deps) > 0 or contamination_risk

def _analyze_singleton_dependencies(fixtures: list[FixtureInfo]) -> list[FixtureInfo]:
    """Analyze fixtures for singleton dependencies."""
    return [f for f in fixtures if f.singleton_dependencies]

def _identify_isolation_issues(fixtures: list[FixtureInfo]) -> list[FixtureInfo]:
    """Identify fixtures with test isolation issues."""
    return [f for f in fixtures if f.state_contamination_risk]

def _identify_migration_candidates(fixtures: list[FixtureInfo]) -> list[FixtureInfo]:
    """Identify fixtures requiring context migration."""
    return [f for f in fixtures if f.context_migration_required]

def _generate_migration_requirements(
    singleton_deps: list[FixtureInfo],
) -> dict[str, str]:
    """Generate migration requirements for singleton-dependent fixtures."""
    requirements = {}

    for fixture in singleton_deps:
        fixture_name = fixture.name
        deps = fixture.singleton_dependencies

        if "get_settings" in deps:
            requirements[fixture_name] = "Replace with context.settings injection"
        elif "get_console" in deps:
            requirements[fixture_name] = "Replace with context.console injection"
        elif any("singleton" in dep.lower() for dep in deps):
            requirements[fixture_name] = "Migrate from singleton to context dependency"
        elif fixture.state_contamination_risk:
            requirements[fixture_name] = "Context-based isolation required"
        else:
            requirements[fixture_name] = "General context-based migration required"

    return requirements

def _create_analysis_summary(
    fixtures: list[FixtureInfo],
    singleton_deps: list[FixtureInfo],
    isolation_issues: list[FixtureInfo],
) -> str:
    """Create analysis summary report."""
    total = len(fixtures)
    singleton_count = len(singleton_deps)
    isolation_count = len(isolation_issues)

    summary_lines = [
        "Test Fixture Analysis Summary:",
        f"- Total fixtures analyzed: {total}",
        f"- Singleton-dependent fixtures: {singleton_count}",
        f"- Fixtures with isolation issues: {isolation_count}",
        f"- Migration priority: {'HIGH' if singleton_count > 5 else 'MEDIUM' if singleton_count > 0 else 'LOW'}",
    ]

    if singleton_count > 0:
        summary_lines.append(
            "- Primary migration need: Context-based dependency injection"
        )

    if isolation_count > 0:
        summary_lines.append("- Test isolation improvements needed")

    return "\n".join(summary_lines)
