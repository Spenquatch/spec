"""Unit tests for singleton detection utilities."""

import ast
import tempfile
from pathlib import Path

import pytest

from spec_cli.utils.singleton_detection import (
    ASTAnalysisReport,
    SingletonDetectionError,
    SingletonPatternDetector,
    SingletonViolation,
    analyze_python_ast,
    scan_for_singleton_patterns,
)

# Test constants
METACLASS_SINGLETON_CODE = """
class TestClass(metaclass=SingletonMeta):
    def __init__(self):
        pass
"""

DECORATOR_SINGLETON_CODE = """
@singleton
class TestClass:
    def __init__(self):
        pass
"""

IMPORT_SINGLETON_CODE = """

class TestClass:
    pass
"""

CLEAN_CODE = """
class RegularClass:
    def __init__(self):
        pass

def regular_function():
    return "hello"
"""

COMPLEX_SINGLETON_CODE = """

from utils import SingletonMeta

class SingletonClass(metaclass=SingletonMeta):
    def __init__(self):
        pass

@singleton
def singleton_function():
    return "instance"
"""

INVALID_PYTHON_CODE = """
class InvalidSyntax(
    def __init__(self):
        pass
"""

class TestSingletonPatternDetector:
    """Test the SingletonPatternDetector class."""

    def test_detect_violations_when_metaclass_singleton_then_returns_violations(self):
        """Test detection of metaclass-based singleton patterns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(METACLASS_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            assert len(violations) == 1
            violation = violations[0]
            assert violation.pattern_type == "metaclass_singleton"
            assert "SingletonMeta" in violation.description
            assert violation.line_number == 2
            assert violation.file_path == file_path

        finally:
            file_path.unlink()

    def test_detect_violations_when_decorator_singleton_then_returns_violations(self):
        """Test detection of decorator-based singleton patterns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(DECORATOR_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            assert len(violations) == 1
            violation = violations[0]
            assert violation.pattern_type == "decorator_singleton"
            assert "singleton" in violation.description
            assert violation.line_number == 3

        finally:
            file_path.unlink()

    def test_detect_violations_when_import_singleton_then_returns_violations(self):
        """Test detection of singleton import patterns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(IMPORT_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            assert len(violations) >= 2  # Should detect both import statements
            pattern_types = {v.pattern_type for v in violations}
            assert "import_singleton_name" in pattern_types
            assert "import_singleton" in pattern_types

        finally:
            file_path.unlink()

    def test_detect_violations_when_clean_code_then_returns_empty_list(self):
        """Test that clean code without singleton patterns returns no violations."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CLEAN_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            assert len(violations) == 0

        finally:
            file_path.unlink()

    def test_detect_violations_when_complex_patterns_then_identifies_all_variations(
        self,
    ):
        """Test detection of multiple singleton patterns in one file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(COMPLEX_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            assert len(violations) >= 4  # Multiple patterns should be detected
            pattern_types = {v.pattern_type for v in violations}
            assert "import_singleton" in pattern_types
            assert (
                "import_from_singleton" in pattern_types
                or "import_singleton_name" in pattern_types
            )
            assert "decorator_singleton" in pattern_types
            assert "metaclass_singleton" in pattern_types

        finally:
            file_path.unlink()

    def test_detect_violations_when_file_not_found_then_raises_detection_error(self):
        """Test that missing files raise appropriate error."""
        detector = SingletonPatternDetector()
        non_existent_path = Path("/nonexistent/file.py")

        with pytest.raises(SingletonDetectionError) as exc_info:
            detector.detect_violations(non_existent_path)

        assert "Cannot read file" in str(exc_info.value)
        assert exc_info.value.file_path == non_existent_path

    def test_detect_violations_when_invalid_syntax_then_raises_detection_error(self):
        """Test that invalid Python syntax raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(INVALID_PYTHON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            detector = SingletonPatternDetector()

            with pytest.raises(SingletonDetectionError) as exc_info:
                detector.detect_violations(file_path)

            assert "Cannot parse Python file" in str(exc_info.value)
            assert exc_info.value.file_path == file_path

        finally:
            file_path.unlink()

    def test_get_decorator_name_when_various_decorator_types_then_extracts_correctly(
        self,
    ):
        """Test decorator name extraction from different AST node types."""
        detector = SingletonPatternDetector()

        # Test Name node
        name_node = ast.Name(id="singleton", ctx=ast.Load())
        assert detector._get_decorator_name(name_node) == "singleton"

        # Test Call node
        ast.Call(

            args=[],
            keywords=[],
        )

        # Test Attribute node
        attr_node = ast.Attribute(
            value=ast.Name(id="utils", ctx=ast.Load()), attr="singleton", ctx=ast.Load()
        )
        assert detector._get_decorator_name(attr_node) == "singleton"

        # Test unknown node type
        unknown_node = ast.Constant(value="test")
        assert detector._get_decorator_name(unknown_node) == ""

class TestScanForSingletonPatterns:
    """Test the scan_for_singleton_patterns function."""

    def test_scan_for_singleton_patterns_when_singleton_found_then_returns_violations(
        self,
    ):
        """Test that singleton patterns are properly detected and returned."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(METACLASS_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_for_singleton_patterns(file_path)

            assert len(violations) == 1
            assert isinstance(violations[0], SingletonViolation)
            assert violations[0].pattern_type == "metaclass_singleton"

        finally:
            file_path.unlink()

    def test_scan_for_singleton_patterns_when_clean_code_then_returns_empty_list(self):
        """Test that clean code returns no violations."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CLEAN_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            violations = scan_for_singleton_patterns(file_path)

            assert len(violations) == 0

        finally:
            file_path.unlink()

class TestAnalyzePythonAST:
    """Test the analyze_python_ast function."""

    def test_analyze_python_ast_when_singleton_class_then_detects_metaclass_pattern(
        self,
    ):
        """Test AST analysis detects metaclass patterns and extracts metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(METACLASS_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            report = analyze_python_ast(file_path)

            assert isinstance(report, ASTAnalysisReport)
            assert report.file_path == file_path
            assert len(report.violations) == 1
            assert "TestClass" in report.classes
            assert "SingletonMeta" in report.metaclasses

        finally:
            file_path.unlink()

    def test_analyze_python_ast_when_singleton_import_then_detects_import_pattern(self):
        """Test AST analysis detects import patterns and extracts metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(IMPORT_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            report = analyze_python_ast(file_path)

            assert len(report.violations) >= 2
            assert "singleton" in report.imports
            assert "TestClass" in report.classes

        finally:
            file_path.unlink()

    def test_analyze_python_ast_when_complex_file_then_comprehensive_analysis(self):
        """Test comprehensive AST analysis of complex file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(COMPLEX_SINGLETON_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            report = analyze_python_ast(file_path)

            assert len(report.violations) >= 4
            assert "SingletonClass" in report.classes
            assert "SingletonMeta" in report.metaclasses
            assert (
                "singleton" in report.decorators

            )
            assert "singleton" in report.imports

        finally:
            file_path.unlink()

    def test_analyze_python_ast_when_invalid_file_then_raises_detection_error(self):
        """Test that invalid files raise appropriate errors."""
        non_existent_path = Path("/nonexistent/file.py")

        with pytest.raises(SingletonDetectionError):
            analyze_python_ast(non_existent_path)

class TestSingletonViolation:
    """Test the SingletonViolation dataclass."""

    def test_violation_reporting_when_patterns_found_then_provides_clear_context(self):
        """Test that violations provide clear context and information."""
        violation = SingletonViolation(
            file_path=Path("test.py"),
            line_number=10,
            column=4,
            pattern_type="metaclass_singleton",
            description="Class uses singleton metaclass: SingletonMeta",
            code_snippet="class TestClass(metaclass=SingletonMeta):",
        )

        assert violation.file_path == Path("test.py")
        assert violation.line_number == 10
        assert violation.column == 4
        assert violation.pattern_type == "metaclass_singleton"
        assert "SingletonMeta" in violation.description
        assert "TestClass" in violation.code_snippet

class TestSingletonDetectionError:
    """Test the SingletonDetectionError exception."""

    def test_detection_system_when_ast_parsing_fails_then_raises_detection_system_error(
        self,
    ):
        """Test that AST parsing failures raise appropriate errors."""
        error = SingletonDetectionError("Test error", Path("test.py"))

        assert str(error) == "Test error"
        assert error.file_path == Path("test.py")

    def test_detection_error_without_file_path_then_file_path_is_none(self):
        """Test error creation without file path."""
        error = SingletonDetectionError("Test error")

        assert str(error) == "Test error"
        assert error.file_path is None
