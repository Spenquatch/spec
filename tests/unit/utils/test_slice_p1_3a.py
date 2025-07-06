"""Unit tests for Slice P1.3a: Singleton Pattern Analysis functionality.

Tests comprehensive singleton pattern detection and access pattern documentation
for dependency injection migration planning.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import PatternAnalysisError
from spec_cli.utils.pattern_analysis import (
    AccessPatternReport,
    SingletonUsage,
    analyze_singleton_usage,
    document_access_patterns,
)

class TestAnalyzeSingletonUsage:
    """Test analyze_singleton_usage function for singleton pattern detection."""

    def test_analyze_singleton_usage_when_singleton_file_exists_then_returns_usage_list(
        self, tmp_path: Path
    ) -> None:
        """Test singleton usage analysis with actual singleton.py file content."""
        test_file = tmp_path / "test_singleton.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""
import threading
from typing import Any

class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class ProgressManagerSingleton:
    def __init__(self):
        self._manager = None

    def get_progress_manager(self):
        return self._manager

def get_progress_manager():
    return ProgressManagerSingleton().get_progress_manager()

class ServiceClass:
    pass
""")

        result = analyze_singleton_usage(test_file)

        assert len(result) > 0

        # Check for specific singleton patterns
        singleton_names = {usage.singleton_name for usage in result}
        assert "ProgressManagerSingleton" in singleton_names
        assert "SingletonMeta" in singleton_names

        # Check usage types
        usage_types = {usage.usage_type for usage in result}
        expected_types = {"class_definition", "instantiation", "decorator_usage"}
        assert expected_types.intersection(usage_types), (
            "Expected singleton usage types not found"
        )

    def test_analyze_singleton_usage_when_no_singletons_then_returns_empty_list(
        self, tmp_path: Path
    ) -> None:
        """Test singleton analysis with files containing no singleton patterns."""
        test_file = tmp_path / "normal_module.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""
class RegularClass:
    def __init__(self):
        self.value = 42

    def method(self):
        return self.value

def regular_function():
    return RegularClass()
""")

        result = analyze_singleton_usage(test_file)

        # Should return empty list for files with no singleton patterns
        assert result == []

    def test_analyze_singleton_usage_when_invalid_file_path_then_raises_analysis_error(
        self,
    ) -> None:
        """Test error handling for invalid file paths during analysis."""
        nonexistent_file = Path("/nonexistent/file.py")

        with pytest.raises(FileNotFoundError):
            analyze_singleton_usage(nonexistent_file)

    def test_analyze_singleton_usage_when_os_error_then_raises_pattern_analysis_error(
        self, tmp_path: Path
    ) -> None:
        """Test error handling for OS errors during file reading."""
        test_file = tmp_path / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("print('test')")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.side_effect = OSError("Permission denied")

            with pytest.raises(PatternAnalysisError) as exc_info:
                analyze_singleton_usage(test_file)

            assert "Failed to analyze singleton patterns" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)

    def test_analyze_singleton_usage_when_syntax_error_then_fallback_to_regex(
        self, tmp_path: Path
    ) -> None:
        """Test fallback to regex analysis when AST parsing fails."""
        test_file = tmp_path / "invalid_syntax.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""
# Invalid Python syntax but contains singleton patterns
class ProgressManagerSingleton(:  # Intentional syntax error
    pass

get_progress_manager()
""")

        # Should not raise exception, should fallback to regex analysis
        result = analyze_singleton_usage(test_file)

        # Should still find singleton patterns via regex
        singleton_names = {usage.singleton_name for usage in result}
        assert "ProgressManagerSingleton" in singleton_names

    def test_analyze_singleton_usage_when_non_python_file_then_returns_empty_list(
        self, tmp_path: Path
    ) -> None:
        """Test behavior with non-Python files."""
        text_file = tmp_path / "readme.txt"
        text_file.parent.mkdir(parents=True, exist_ok=True)
        text_file.write_text("This is not a Python file")

        result = analyze_singleton_usage(text_file)

        assert result == []

class TestDocumentAccessPatterns:
    """Test document_access_patterns function for access pattern analysis."""

    def test_document_access_patterns_when_singleton_class_found_then_generates_access_report(
        self,
    ) -> None:
        """Test access pattern documentation for specific singleton classes."""
        # Create sample usage data
        sample_usages = [
            SingletonUsage(
                file_path=Path("test1.py"),
                line_number=10,
                usage_type="instantiation",
                singleton_name="ProgressManagerSingleton",
                context="ProgressManagerSingleton()",
                function_name="get_manager",
            ),
            SingletonUsage(
                file_path=Path("test2.py"),
                line_number=15,
                usage_type="method_call",
                singleton_name="ProgressManagerSingleton",
                context="ProgressManagerSingleton().get_progress_manager()",
                function_name="setup_progress",
            ),
            SingletonUsage(
                file_path=Path("test3.py"),
                line_number=20,
                usage_type="instantiation",
                singleton_name="OtherSingleton",
                context="OtherSingleton()",
            ),
        ]

        result = document_access_patterns("ProgressManagerSingleton", sample_usages)

        assert isinstance(result, AccessPatternReport)
        assert result.singleton_name == "ProgressManagerSingleton"
        assert result.total_usages == 2  # Only ProgressManagerSingleton usages
        assert len(result.usage_locations) == 2

        # Check access methods detection
        expected_access_methods = {"direct_instantiation", "method_call"}
        assert expected_access_methods.issubset(result.access_methods)

        # Check wrapper requirements generation
        assert len(result.wrapper_requirements) > 0
        assert (
            "Maintain thread-safe access during migration"
            in result.wrapper_requirements
        )

    def test_document_access_patterns_when_convenience_functions_found_then_includes_in_access_methods(
        self,
    ) -> None:
        """Test detection of convenience function usage patterns."""
        sample_usages = [
            SingletonUsage(
                file_path=Path("test.py"),
                line_number=5,
                usage_type="method_call",
                singleton_name="ProgressManagerSingleton",
                context="get_progress_manager()",
                function_name="setup",
            ),
            SingletonUsage(
                file_path=Path("test.py"),
                line_number=10,
                usage_type="method_call",
                singleton_name="ProgressManagerSingleton",
                context="reset_progress_manager()",
                function_name="cleanup",
            ),
        ]

        result = document_access_patterns("ProgressManagerSingleton", sample_usages)

        assert "convenience_function" in result.access_methods
        assert "reset_function" in result.access_methods

        # Check ProgressManager specific requirements
        progress_requirements = [
            req for req in result.wrapper_requirements if "progress" in req.lower()
        ]
        assert len(progress_requirements) > 0

class TestSingletonMetaclassAnalysis:
    """Test singleton metaclass analysis and behavior documentation."""

    def test_singleton_metaclass_analysis_when_singleton_py_exists_then_documents_behavior(
        self, tmp_path: Path
    ) -> None:
        """Test analysis of existing SingletonMeta behavior."""
        singleton_file = tmp_path / "singleton_impl.py"
        singleton_file.parent.mkdir(parents=True, exist_ok=True)
        singleton_file.write_text("""
import threading
from typing import Any

class SingletonMeta(type):
    _instances = {}
    _locks = {}
    _global_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._global_lock:
                if cls not in cls._instances:
                    cls._locks[cls] = threading.Lock()
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

class MyService(metaclass=SingletonMeta):
    def __init__(self):
        self.initialized = True
""")

        result = analyze_singleton_usage(singleton_file)

        # Should detect SingletonMeta class definition
        metaclass_usages = [u for u in result if u.singleton_name == "SingletonMeta"]
        assert len(metaclass_usages) > 0

        # Should detect class using metaclass
        service_usages = [u for u in result if u.usage_type == "class_definition"]
        assert len(service_usages) > 0

    def test_compatibility_requirements_generation_when_usage_patterns_found_then_creates_requirements(
        self,
    ) -> None:
        """Test compatibility requirements generation from usage analysis."""
        # Comprehensive usage patterns
        comprehensive_usages = [
            SingletonUsage(
                file_path=Path("prod_module.py"),
                line_number=10,
                usage_type="instantiation",
                singleton_name="ProgressManagerSingleton",
                context="ProgressManagerSingleton()",
            ),
            SingletonUsage(
                file_path=Path("prod_module.py"),
                line_number=15,
                usage_type="method_call",
                singleton_name="ProgressManagerSingleton",
                context="ProgressManagerSingleton().get_progress_manager()",
            ),
            SingletonUsage(
                file_path=Path("tests/test_module.py"),
                line_number=20,
                usage_type="reset_function",
                singleton_name="ProgressManagerSingleton",

            ),
            SingletonUsage(
                file_path=Path("utils.py"),
                line_number=25,
                usage_type="instantiation",
                singleton_name="ProgressManagerSingleton",
                context="get_progress_manager()",
            ),
        ]

        result = document_access_patterns(
            "ProgressManagerSingleton", comprehensive_usages
        )

        # Should generate comprehensive requirements
        requirements = result.wrapper_requirements

        # Check for specific requirement categories
        thread_safety_req = any("thread-safe" in req.lower() for req in requirements)
        assert thread_safety_req, "Thread safety requirements should be included"

        api_preservation_req = any("api" in req.lower() for req in requirements)
        assert api_preservation_req, "API preservation requirements should be included"

        test_utilities_req = any("test" in req.lower() for req in requirements)
        assert test_utilities_req, (
            "Test utilities should be included due to test file usage"
        )

        # Check ProgressManager specific requirements
        progress_specific = [
            req for req in requirements if "get_progress_manager" in req
        ]
        assert len(progress_specific) > 0, (
            "ProgressManager specific requirements should be included"
        )

class TestPatternAnalysisErrorHandling:
    """Test error handling in pattern analysis functionality."""

    def test_pattern_analysis_error_when_invalid_file_encoding_then_raises_analysis_error(
        self, tmp_path: Path
    ) -> None:
        """Test error handling for file encoding issues."""
        test_file = tmp_path / "bad_encoding.py"
        # Write binary data that's not valid UTF-8
        test_file.write_bytes(b"\xff\xfe\x00Invalid encoding")

        with pytest.raises(PatternAnalysisError) as exc_info:
            analyze_singleton_usage(test_file)

        assert "Failed to decode file encoding" in str(exc_info.value)

    def test_analyze_singleton_usage_when_permission_error_then_provides_context(
        self, tmp_path: Path
    ) -> None:
        """Test that permission errors include helpful context."""
        test_file = tmp_path / "protected.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("class Test: pass")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.side_effect = PermissionError("Access denied")

            with pytest.raises(PatternAnalysisError) as exc_info:
                analyze_singleton_usage(test_file)

            # Should include file path and formatted error
            assert str(test_file) in str(exc_info.value)
            assert "Access denied" in str(exc_info.value)

class TestCrossPlatformSupport:
    """Test cross-platform compatibility for pattern analysis."""

    def test_pattern_analysis_cross_platform_path_handling(
        self, tmp_path: Path
    ) -> None:
        """Test that pattern analysis works with cross-platform paths."""
        # Create file with mixed path separators in content
        test_file = tmp_path / "cross_platform.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("""
# Test file with various path references
from spec_cli.ui.progress_manager import ProgressManagerSingleton
from spec_cli\\utils\\singleton import SingletonMeta  # Windows-style path in comment

class TestSingleton(metaclass=SingletonMeta):
    pass

manager = ProgressManagerSingleton()
""")

        result = analyze_singleton_usage(test_file)

        # Should handle paths correctly regardless of platform
        assert len(result) > 0

        # All file paths should be Path objects
        for usage in result:
            assert isinstance(usage.file_path, Path)
            assert usage.file_path == test_file

class TestIntegrationWithExistingCode:
    """Test integration of pattern analysis with existing codebase patterns."""

    def test_pattern_analysis_integration_with_actual_progress_manager_patterns(
        self,
    ) -> None:
        """Test pattern analysis with realistic ProgressManager usage."""
        # Create content similar to actual codebase usage
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
from spec_cli.ui.progress_manager import (
    ProgressManagerSingleton,
    get_progress_manager,
    set_progress_manager,
    reset_progress_manager
)

class WorkflowManager:
    def __init__(self):
        self.progress_manager = get_progress_manager()

    def start_workflow(self):
        progress_manager = ProgressManagerSingleton().get_progress_manager()
        progress_manager.start_operation("workflow")

    def cleanup(self):
        reset_progress_manager()

def setup_custom_progress():
    custom_manager = CustomProgressManager()
    set_progress_manager(custom_manager)
""")
            f.flush()

            result = analyze_singleton_usage(Path(f.name))

            # Should detect multiple usage patterns
            progress_usages = [
                u for u in result if "ProgressManager" in u.singleton_name
            ]
            assert len(progress_usages) > 0

            # Should detect various access methods
            usage_types = {u.usage_type for u in progress_usages}
            expected_types = {"instantiation", "import"}
            assert expected_types.intersection(usage_types)

            # Clean up
            Path(f.name).unlink()

    def test_pattern_analysis_performance_with_large_file(self, tmp_path: Path) -> None:
        """Test pattern analysis performance with larger files."""
        large_file = tmp_path / "large_module.py"

        # Generate a large file with some singleton patterns
        content_lines = [
            "# Large module with singleton patterns",
            "from spec_cli.ui.progress_manager import ProgressManagerSingleton",
            "",
        ]

        # Add many regular classes/functions
        for i in range(100):
            content_lines.extend(
                [
                    f"class RegularClass{i}:",
                    f"    def method{i}(self):",
                    f"        return {i}",
                    "",
                ]
            )

        # Add some singleton usage
        content_lines.extend(
            [
                "def use_progress():",
                "    manager = ProgressManagerSingleton().get_progress_manager()",
                "    return manager",
            ]
        )

        large_file.parent.mkdir(parents=True, exist_ok=True)
        large_file.write_text("\n".join(content_lines))

        # Should complete analysis without performance issues
        result = analyze_singleton_usage(large_file)

        # Should find the singleton patterns despite file size
        progress_usages = [u for u in result if "ProgressManager" in u.singleton_name]
        assert len(progress_usages) > 0
