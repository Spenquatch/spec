"""Integration tests for singleton detection system."""

import tempfile
from pathlib import Path

import pytest

from spec_cli.utils.singleton_detection import (
    SingletonDetectionError,
    analyze_python_ast,
    scan_for_singleton_patterns,
)

# Test constants for realistic codebase scenarios
REALISTIC_SINGLETON_MODULE = '''
"""Legacy singleton configuration module."""

from typing import Dict, Any
import threading


class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigurationManager(metaclass=SingletonMeta):
    """Global configuration manager using singleton pattern."""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.loaded = False

    def load_config(self, config_path: str) -> None:
        """Load configuration from file."""
        if not self.loaded:
            # Simulate config loading
            self.config = {"app_name": "spec-cli", "debug": False}
            self.loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)


@singleton_decorator
def get_global_config():
    """Get global configuration instance."""
    return ConfigurationManager()


# Utility functions that don't use singletons
def process_data(data: str) -> str:
    """Process data without singleton dependencies."""
    return data.upper()
'''

MIXED_CODEBASE_MODULE = '''
"""Module with both clean and singleton code."""

from utils.singleton import singleton_decorator
import singleton_config


class RegularService:
    """Regular service class without singleton pattern."""

    def __init__(self, config: dict):
        self.config = config

    def process(self, data: str) -> str:
        return f"Processed: {data}"


@singleton
class LegacyCache:
    """Legacy cache using singleton decorator."""

    def __init__(self):
        self._cache = {}

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value):
        self._cache[key] = value


class ModernService:
    """Modern service with dependency injection."""

    def __init__(self, cache_service, config_service):
        self.cache = cache_service
        self.config = config_service

    def enhanced_process(self, data: str) -> str:
        cached = self.cache.get(data)
        if cached:
            return cached

        result = f"Enhanced: {data}"
        self.cache.set(data, result)
        return result
'''

CLEAN_MODULE = '''
"""Clean module without singleton patterns."""

from typing import Protocol
import logging

logger = logging.getLogger(__name__)


class CacheProtocol(Protocol):
    """Cache service protocol."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


class InMemoryCache:
    """In-memory cache implementation."""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value
        logger.debug("Cached value for key: %s", key)


class DataProcessor:
    """Data processor with dependency injection."""

    def __init__(self, cache: CacheProtocol):
        self.cache = cache

    def process(self, data: str) -> str:
        """Process data with caching."""
        cached_result = self.cache.get(data)
        if cached_result:
            return cached_result

        result = data.upper().strip()
        self.cache.set(data, result)
        return result
'''


class TestSingletonDetectionSystemIntegration:
    """Integration tests for the complete singleton detection system."""

    def test_singleton_detection_system_when_full_codebase_scan_then_accurate_comprehensive_reporting(
        self,
    ):
        """Test complete system with realistic codebase structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create realistic codebase structure
            (temp_path / "src").mkdir()
            (temp_path / "src" / "legacy").mkdir()
            (temp_path / "src" / "modern").mkdir()

            # Write different types of modules
            (temp_path / "src" / "legacy" / "config.py").write_text(
                REALISTIC_SINGLETON_MODULE
            )
            (temp_path / "src" / "mixed_service.py").write_text(MIXED_CODEBASE_MODULE)
            (temp_path / "src" / "modern" / "services.py").write_text(CLEAN_MODULE)
            (temp_path / "src" / "__init__.py").write_text("")

            # Scan each file and collect violations
            all_violations = []

            # Test legacy module with multiple singleton patterns
            legacy_violations = scan_for_singleton_patterns(
                temp_path / "src" / "legacy" / "config.py"
            )
            all_violations.extend(legacy_violations)

            # Test mixed module
            mixed_violations = scan_for_singleton_patterns(
                temp_path / "src" / "mixed_service.py"
            )
            all_violations.extend(mixed_violations)

            # Test clean module
            clean_violations = scan_for_singleton_patterns(
                temp_path / "src" / "modern" / "services.py"
            )
            all_violations.extend(clean_violations)

            # Verify comprehensive detection
            assert len(legacy_violations) >= 2  # Should detect metaclass and decorator
            assert len(mixed_violations) >= 3  # Should detect imports and decorator
            assert len(clean_violations) == 0  # Should be clean

            # Verify violation details
            violation_types = {v.pattern_type for v in all_violations}
            expected_types = {
                "metaclass_singleton",
                "decorator_singleton",
                "function_singleton_decorator",
                "import_singleton_name",
                "import_singleton",
            }

            # Should detect multiple pattern types
            assert len(violation_types.intersection(expected_types)) >= 3

            # Verify file paths and line numbers are accurate
            for violation in all_violations:
                assert violation.file_path.exists()
                assert violation.line_number > 0
                assert violation.description != ""
                assert violation.code_snippet != ""

    def test_detection_system_when_ast_analysis_comprehensive_then_metadata_extraction(
        self,
    ):
        """Test comprehensive AST analysis with metadata extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "complex.py"
            test_file.write_text(REALISTIC_SINGLETON_MODULE)

            # Perform comprehensive AST analysis
            report = analyze_python_ast(test_file)

            # Verify comprehensive metadata extraction
            assert "ConfigurationManager" in report.classes
            assert "SingletonMeta" in report.classes
            assert "SingletonMeta" in report.metaclasses
            assert "singleton_decorator" in report.decorators
            assert len(report.imports) > 0

            # Verify violations are properly linked to metadata
            assert len(report.violations) >= 2

            # Verify violation accuracy
            metaclass_violations = [
                v for v in report.violations if v.pattern_type == "metaclass_singleton"
            ]
            decorator_violations = [
                v
                for v in report.violations
                if v.pattern_type == "function_singleton_decorator"
            ]

            assert len(metaclass_violations) >= 1
            assert len(decorator_violations) >= 1

    def test_detection_system_when_error_handling_then_graceful_failure(self):
        """Test system error handling with various failure scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test with non-existent file
            non_existent = temp_path / "missing.py"
            with pytest.raises(SingletonDetectionError) as exc_info:
                scan_for_singleton_patterns(non_existent)
            assert "Cannot read file" in str(exc_info.value)

            # Test with invalid Python syntax
            invalid_file = temp_path / "invalid.py"
            invalid_file.write_text("class Broken(\n    def __init__(")

            with pytest.raises(SingletonDetectionError) as exc_info:
                scan_for_singleton_patterns(invalid_file)
            assert "Cannot parse Python file" in str(exc_info.value)

            # Test with binary file
            binary_file = temp_path / "binary.py"
            binary_file.write_bytes(b"\x00\x01\x02\x03")

            with pytest.raises(SingletonDetectionError):
                scan_for_singleton_patterns(binary_file)

    def test_detection_system_when_edge_cases_then_robust_handling(self):
        """Test detection system with edge cases and boundary conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test empty file
            empty_file = temp_path / "empty.py"
            empty_file.write_text("")
            violations = scan_for_singleton_patterns(empty_file)
            assert len(violations) == 0

            # Test file with only comments
            comment_file = temp_path / "comments.py"
            comment_file.write_text("# This is just a comment\n# Another comment\n")
            violations = scan_for_singleton_patterns(comment_file)
            assert len(violations) == 0

            # Test file with string containing singleton patterns
            string_file = temp_path / "strings.py"
            string_file.write_text("""
def example():
    text = "This mentions SingletonMeta but is just a string"
    return text
""")
            violations = scan_for_singleton_patterns(string_file)
            assert len(violations) == 0  # Should not detect patterns in strings

            # Test nested class with singleton
            nested_file = temp_path / "nested.py"
            nested_file.write_text("""
class Outer:
    class Inner(metaclass=SingletonMeta):
        pass
""")
            violations = scan_for_singleton_patterns(nested_file)
            assert len(violations) == 1
            assert violations[0].pattern_type == "metaclass_singleton"

    def test_detection_system_when_performance_validation_then_acceptable_speed(self):
        """Test detection system performance with larger codebases."""
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple files to simulate larger codebase
            for i in range(10):
                file_path = temp_path / f"module_{i}.py"
                # Alternate between clean and singleton code
                if i % 2 == 0:
                    file_path.write_text(CLEAN_MODULE)
                else:
                    file_path.write_text(MIXED_CODEBASE_MODULE)

            # Measure detection performance
            start_time = time.time()

            total_violations = 0
            for i in range(10):
                file_path = temp_path / f"module_{i}.py"
                violations = scan_for_singleton_patterns(file_path)
                total_violations += len(violations)

            elapsed_time = time.time() - start_time

            # Performance validation - should complete in reasonable time
            assert elapsed_time < 5.0  # Should complete within 5 seconds
            assert total_violations > 0  # Should detect some violations

            # Verify detection accuracy wasn't compromised for speed
            assert total_violations >= 10  # Should detect multiple violations
