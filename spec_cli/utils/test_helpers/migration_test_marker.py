"""Migration test marking utilities for categorizing and tracking migration-specific tests.

This module provides functionality to mark tests as migration-related and
validate core test reliability.
"""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Test patterns that indicate migration-specific functionality
MIGRATION_TEST_PATTERNS = {
    "migration",
    "migrate",
    "legacy",
    "compatibility",
    "transition",
    "upgrade",
    "version",
    "context_injection",
    "dependency_injection",
    "di_migration",
    "context_migration",
    "injection_migration",
    "slice_p",  # Phase patterns
    "slice_2_",  # Migration slice patterns
}

# Core test patterns that should be highly reliable
CORE_TEST_PATTERNS = {
    "core",
    "basic",
    "fundamental",
    "essential",
    "critical",
    "primary",
    "main",
    "standard",
}


def mark_migration_test(test_path: str, reason: str) -> bool:
    """Mark a test file as migration-related with specified reason.

    Args:
        test_path: Path to the test file to mark
        reason: Reason for marking as migration test

    Returns:
        True if marking was successful, False otherwise

    Raises:
        FileNotFoundError: If test file doesn't exist
        ValueError: If test_path is invalid
    """
    test_file = Path(test_path)

    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found: {test_path}")

    if not test_file.suffix == ".py":
        raise ValueError(f"Invalid test file extension: {test_path}")

    try:
        # Read the current content
        content = test_file.read_text(encoding="utf-8")

        # Check if already marked
        if "pytest.mark.migration" in content:
            logger.info("Test file already marked as migration: %s", test_path)
            return True

        # Ensure this is actually a test file (contains test classes/functions)
        if not _is_actual_test_file(content):
            logger.info("Skipping non-test file: %s", test_path)
            return False

        # Insert migration marker at the top after imports
        lines = content.splitlines()

        # Ensure pytest is imported
        if "import pytest" not in content and "from pytest" not in content:
            # Find insertion point for pytest import
            import_index = _find_import_insertion_point(lines)
            lines.insert(import_index, "import pytest")
            lines.insert(import_index + 1, "")

        marker_line = f'pytestmark = pytest.mark.migration("{reason}")'

        # Find appropriate insertion point for marker
        insert_index = _find_marker_insertion_point(lines)

        # Insert the marker
        lines.insert(insert_index, marker_line)
        lines.insert(insert_index + 1, "")

        # Write back to file
        test_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        logger.info("Marked test file as migration: %s (reason: %s)", test_path, reason)
        return True

    except Exception as e:
        logger.error("Failed to mark test file %s: %s", test_path, str(e))
        return False


def identify_migration_tests(test_directory: str) -> dict[str, str]:
    """Identify tests that should be marked as migration-related.

    Args:
        test_directory: Directory containing test files

    Returns:
        Dictionary mapping test file paths to migration reasons
    """
    test_dir = Path(test_directory)
    migration_tests = {}

    for test_file in test_dir.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
            if _is_actual_test_file(content):
                reason = _analyze_test_for_migration_patterns(test_file)
                if reason:
                    migration_tests[str(test_file)] = reason
        except Exception as e:
            logger.warning("Failed to read test file %s: %s", test_file, str(e))

    return migration_tests


def identify_core_tests(test_directory: str) -> list[str]:
    """Identify tests that represent core functionality.

    Args:
        test_directory: Directory containing test files

    Returns:
        List of test file paths representing core functionality
    """
    test_dir = Path(test_directory)
    core_tests = []

    for test_file in test_dir.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8")
            if _is_actual_test_file(content) and _is_core_test(test_file):
                core_tests.append(str(test_file))
        except Exception as e:
            logger.warning("Failed to read test file %s: %s", test_file, str(e))

    return core_tests


def validate_test_reliability(
    test_paths: list[str], failure_threshold: float = 0.05
) -> dict[str, float]:
    """Validate reliability of test files based on historical data.

    Args:
        test_paths: List of test file paths to validate
        failure_threshold: Maximum acceptable failure rate (default 5%)

    Returns:
        Dictionary mapping test paths to their failure rates
    """
    # This would integrate with test execution history
    # For now, return mock data structure
    reliability_scores = {}

    for test_path in test_paths:
        # In real implementation, this would calculate actual failure rates
        # from test execution history/CI data
        reliability_scores[test_path] = 0.02  # Mock 2% failure rate

    return reliability_scores


def _is_actual_test_file(content: str) -> bool:
    """Check if file content indicates this is a real test file.

    Args:
        content: File content to analyze

    Returns:
        True if file contains test classes or test functions
    """
    content_lower = content.lower()

    # Check for test class patterns
    test_indicators = [
        "class test",
        "def test_",
        "@pytest.",
        "import pytest",
        "from pytest",
        "unittest.testcase",
        "class.*test.*:",
    ]

    for indicator in test_indicators:
        if indicator in content_lower:
            return True

    return False


def _find_import_insertion_point(lines: list[str]) -> int:
    """Find appropriate line index to insert import statements.

    Args:
        lines: List of file lines

    Returns:
        Line index where import should be inserted
    """
    # Find the end of docstrings and before first import
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip module docstring at the top
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            continue

        # If we hit an import or class/function, insert before it
        if (stripped.startswith("import ") or
            stripped.startswith("from ") or
            stripped.startswith("class ") or
            stripped.startswith("def ")):
            return i

    # If no imports found, insert at the end of any docstrings
    return 0


def _find_marker_insertion_point(lines: list[str]) -> int:
    """Find appropriate line index to insert pytest marker.

    Args:
        lines: List of file lines

    Returns:
        Line index where marker should be inserted
    """
    # Find the end of imports and docstrings
    import_end = 0
    in_docstring = False
    docstring_quote = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track docstrings
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_quote = stripped[:3]
                if stripped.endswith(docstring_quote) and len(stripped) > 3:
                    in_docstring = False
                    docstring_quote = None
            elif stripped.startswith("import ") or stripped.startswith("from "):
                import_end = i + 1
        else:
            if docstring_quote and stripped.endswith(docstring_quote):
                in_docstring = False
                docstring_quote = None

        # If we hit a class or function definition, stop
        if stripped.startswith("class ") or stripped.startswith("def "):
            break

    return import_end


def _analyze_test_for_migration_patterns(test_file: Path) -> str | None:
    """Analyze test file to determine if it's migration-related.

    Args:
        test_file: Path to test file

    Returns:
        Migration reason if patterns found, None otherwise
    """
    try:
        content = test_file.read_text(encoding="utf-8")
        content_lower = content.lower()
        file_name_lower = test_file.name.lower()

        # Check filename patterns
        for pattern in MIGRATION_TEST_PATTERNS:
            if pattern in file_name_lower:
                return f"filename_pattern_{pattern}"

        # Check content patterns
        for pattern in MIGRATION_TEST_PATTERNS:
            if pattern in content_lower:
                return f"content_pattern_{pattern}"

        # Check for specific test class/function names
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef | ast.FunctionDef):
                    name_lower = node.name.lower()
                    for pattern in MIGRATION_TEST_PATTERNS:
                        if pattern in name_lower:
                            return f"test_name_pattern_{pattern}"
        except SyntaxError:
            # If we can't parse, just use string matching
            pass

        return None

    except Exception as e:
        logger.warning("Failed to analyze test file %s: %s", test_file, str(e))
        return None


def _is_core_test(test_file: Path) -> bool:
    """Check if test file represents core functionality.

    Args:
        test_file: Path to test file

    Returns:
        True if test represents core functionality
    """
    file_name_lower = test_file.name.lower()

    # Check for core patterns in filename
    for pattern in CORE_TEST_PATTERNS:
        if pattern in file_name_lower:
            return True

    # Check if it's NOT a migration test
    migration_reason = _analyze_test_for_migration_patterns(test_file)
    if migration_reason:
        return False

    # Check directory structure for core indicators
    path_parts = [p.lower() for p in test_file.parts]
    for pattern in CORE_TEST_PATTERNS:
        if any(pattern in part for part in path_parts):
            return True

    return False
