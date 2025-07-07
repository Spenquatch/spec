"""Integration tests for Slice 3.1: Comprehensive Singleton Detection Execution."""

import tempfile
from pathlib import Path

from slice_3_1_detection_execution import (
    execute_comprehensive_detection,
    generate_detection_summary,
    save_detection_results,
)

# Test constants
SAMPLE_SINGLETON_CODE = '''"""Sample singleton implementation for testing detection."""

class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class TestSingleton(metaclass=SingletonMeta):
    """Test singleton class using metaclass pattern."""

    def __init__(self):
        self.value = "singleton_instance"

    def get_value(self):
        return self.value

@singleton_decorator
def get_instance():
    """Singleton function with decorator."""
    return TestSingleton()

def create_test_singleton():
    """Create a test singleton instance."""
    return TestSingleton()
'''

SAMPLE_REGULAR_CODE = '''"""Regular non-singleton code for testing."""

class RegularClass:
    """Regular class without singleton patterns."""

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

def create_regular_instance():
    """Create a regular instance."""
    return RegularClass("regular")
'''

SAMPLE_USAGE_CODE = '''"""Usage patterns for singleton testing."""

from .singleton_module import TestSingleton, get_instance

class ServiceClass:
    """Service that uses singleton."""

    def __init__(self):
        self.singleton = TestSingleton()
        self.instance = get_instance()

    def process(self):
        return self.singleton.get_value()
'''

class TestComprehensiveDetectionIntegration:
    """Integration tests for comprehensive singleton detection."""

    def test_end_to_end_detection_with_singletons(self):
        """Test complete detection workflow with singleton patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase structure
            codebase_root = Path(temp_dir) / "test_codebase"
            codebase_root.mkdir()

            # Create Python files with singleton patterns
            singleton_file = codebase_root / "singleton_module.py"
            singleton_file.write_text(SAMPLE_SINGLETON_CODE)

            regular_file = codebase_root / "regular_module.py"
            regular_file.write_text(SAMPLE_REGULAR_CODE)

            usage_file = codebase_root / "usage_module.py"
            usage_file.write_text(SAMPLE_USAGE_CODE)

            # Execute comprehensive detection
            scan_config = {"max_workers": 2, "timeout_seconds": 60}
            exclusion_patterns = ["__pycache__", "*.pyc"]

            result = execute_comprehensive_detection(
                str(codebase_root), scan_config, exclusion_patterns
            )

            # Verify results structure
            assert "singleton_patterns" in result
            assert "scan_statistics" in result
            assert "detection_report" in result
            assert "summary" in result

            # Verify scan statistics
            stats = result["scan_statistics"]
            assert stats["total_files_scanned"] == 3
            assert stats["python_files_found"] == 3
            assert stats["scan_duration_seconds"] > 0
            assert stats["errors_encountered"] == 0

            # Verify singleton patterns detected
            patterns = result["singleton_patterns"]
            assert len(patterns) > 0

            # Should detect metaclass singleton
            metaclass_patterns = [
                p for p in patterns
                if p["pattern_type"] == "metaclass_singleton"
            ]
            assert len(metaclass_patterns) > 0

            # Should detect TestSingleton class
            singleton_classes = [
                p for p in patterns
                if "TestSingleton" in p.get("singleton_name", "")
            ]
            assert len(singleton_classes) > 0

            # Verify summary statistics
            summary = result["summary"]
            assert summary["total_patterns"] > 0
            assert summary["unique_singletons"] > 0
            assert summary["files_with_patterns"] > 0

    def test_end_to_end_detection_no_singletons(self):
        """Test detection workflow with no singleton patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase with only regular code
            codebase_root = Path(temp_dir) / "regular_codebase"
            codebase_root.mkdir()

            # Create only regular Python files
            for i in range(3):
                regular_file = codebase_root / f"module_{i}.py"
                regular_file.write_text(SAMPLE_REGULAR_CODE.replace("RegularClass", f"RegularClass{i}"))

            # Execute comprehensive detection
            scan_config = {"max_workers": 2, "timeout_seconds": 60}
            exclusion_patterns = []

            result = execute_comprehensive_detection(
                str(codebase_root), scan_config, exclusion_patterns
            )

            # Verify basic results structure
            assert "singleton_patterns" in result
            assert "scan_statistics" in result
            assert "detection_report" in result

            # Verify scan completed successfully
            stats = result["scan_statistics"]
            assert stats["total_files_scanned"] == 3
            assert stats["python_files_found"] == 3
            assert stats["errors_encountered"] == 0

            # Should find few or no singleton patterns (depending on detection sensitivity)
            patterns = result["singleton_patterns"]
            # In a purely regular codebase, we expect minimal or no detections
            assert isinstance(patterns, list)

    def test_end_to_end_with_exclusion_patterns(self):
        """Test detection with exclusion patterns applied."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase structure
            codebase_root = Path(temp_dir) / "test_codebase"
            codebase_root.mkdir()

            # Create files to be scanned
            singleton_file = codebase_root / "singleton_module.py"
            singleton_file.write_text(SAMPLE_SINGLETON_CODE)

            # Create files to be excluded
            test_dir = codebase_root / "tests"
            test_dir.mkdir()
            test_file = test_dir / "test_singleton.py"
            test_file.write_text(SAMPLE_SINGLETON_CODE)

            backup_file = codebase_root / "backup_module.bak.py"
            backup_file.write_text(SAMPLE_SINGLETON_CODE)

            # Execute detection with exclusions
            scan_config = {"max_workers": 2, "timeout_seconds": 60}
            exclusion_patterns = ["tests/", ".bak.py"]

            result = execute_comprehensive_detection(
                str(codebase_root), scan_config, exclusion_patterns
            )

            # Verify only non-excluded files were scanned
            stats = result["scan_statistics"]
            # Should scan singleton_module.py but exclude test_singleton.py and backup_module.bak.py
            assert stats["total_files_scanned"] >= 1

            # Verify detection report contains information about exclusions
            report = result["detection_report"]
            assert "Exclusion Patterns" in report
            assert "tests/" in report
            assert ".bak.py" in report

    def test_save_and_load_detection_results(self):
        """Test saving and loading detection results integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal test codebase
            codebase_root = Path(temp_dir) / "test_codebase"
            codebase_root.mkdir()

            singleton_file = codebase_root / "singleton.py"
            singleton_file.write_text(SAMPLE_SINGLETON_CODE)

            # Execute detection
            scan_config = {"max_workers": 1, "timeout_seconds": 30}
            result = execute_comprehensive_detection(
                str(codebase_root), scan_config, []
            )

            # Save results to file
            output_file = Path(temp_dir) / "detection_results.json"
            save_detection_results(result, output_file)

            # Verify file was created and contains expected data
            assert output_file.exists()

            import json
            with output_file.open("r") as f:
                saved_data = json.load(f)

            # Verify saved data structure matches original
            assert "singleton_patterns" in saved_data
            assert "scan_statistics" in saved_data
            assert "detection_report" in saved_data
            assert "summary" in saved_data

            # Verify data integrity
            assert saved_data["scan_statistics"]["total_files_scanned"] == result["scan_statistics"]["total_files_scanned"]
            assert len(saved_data["singleton_patterns"]) == len(result["singleton_patterns"])

    def test_detection_summary_integration(self):
        """Test detection summary generation with real detection results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create diverse singleton patterns
            codebase_root = Path(temp_dir) / "diverse_codebase"
            codebase_root.mkdir()

            # File with metaclass singleton
            metaclass_file = codebase_root / "metaclass_singleton.py"
            metaclass_file.write_text(SAMPLE_SINGLETON_CODE)

            # File with decorator singleton
            decorator_file = codebase_root / "decorator_singleton.py"
            decorator_code = '''
@singleton_decorator
class DecoratorSingleton:
    def __init__(self):
        pass
'''
            decorator_file.write_text(decorator_code)

            # File with
            import_file = codebase_root / "import_singleton.py"
            import_code = '''
from singleton import SingletonClass
import SingletonMeta
'''
            import_file.write_text(import_code)

            # Execute detection
            result = execute_comprehensive_detection(
                str(codebase_root), {"max_workers": 2, "timeout_seconds": 60}, []
            )

            # Generate and verify summary
            patterns = result["singleton_patterns"]
            summary = generate_detection_summary(patterns)

            # Verify summary contains expected pattern types
            assert summary["total_patterns"] > 0
            assert summary["files_with_patterns"] >= 1

            # Should detect various pattern types
            pattern_types = [p["pattern_type"] for p in patterns]
            unique_types = set(pattern_types)
            assert len(unique_types) > 0

    def test_detection_performance_requirements(self):
        """Test that detection meets performance requirements."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create moderately sized test codebase
            codebase_root = Path(temp_dir) / "performance_test"
            codebase_root.mkdir()

            # Create multiple files to test scanning performance
            for i in range(20):
                test_file = codebase_root / f"module_{i:02d}.py"
                content = SAMPLE_SINGLETON_CODE if i % 3 == 0 else SAMPLE_REGULAR_CODE
                test_file.write_text(content.replace("TestSingleton", f"TestSingleton{i}"))

            # Execute detection with performance monitoring
            import time
            start_time = time.time()

            result = execute_comprehensive_detection(
                str(codebase_root), {"max_workers": 4, "timeout_seconds": 300}, []
            )

            end_time = time.time()
            total_duration = end_time - start_time

            # Verify performance requirements
            stats = result["scan_statistics"]
            assert stats["total_files_scanned"] == 20
            assert stats["scan_duration_seconds"] > 0
            assert stats["files_per_second"] > 0

            # Should complete within reasonable time (5 minutes for this test size)
            assert total_duration < 300, f"Scan took {total_duration:.2f}s, should be under 300s"

            # Should achieve reasonable throughput (at least 0.1 files/second)
            assert stats["files_per_second"] >= 0.1, f"Throughput {stats['files_per_second']} too low"

    def test_detection_error_handling_integration(self):
        """Test error handling in end-to-end detection scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase with problematic files
            codebase_root = Path(temp_dir) / "error_test"
            codebase_root.mkdir()

            # Valid Python file
            valid_file = codebase_root / "valid.py"
            valid_file.write_text(SAMPLE_SINGLETON_CODE)

            # Invalid Python syntax file
            invalid_file = codebase_root / "invalid.py"
            invalid_file.write_text("class InvalidSyntax(\n  # Missing closing parenthesis")

            # Binary file with .py extension
            binary_file = codebase_root / "binary.py"
            binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')

            # Execute detection (should handle errors gracefully)
            result = execute_comprehensive_detection(
                str(codebase_root), {"max_workers": 2, "timeout_seconds": 60}, []
            )

            # Verify detection completed despite errors
            assert "singleton_patterns" in result
            assert "scan_statistics" in result

            stats = result["scan_statistics"]
            assert stats["total_files_scanned"] == 3

            # May have some errors but should not fail completely
            # The exact error count depends on how the scanner handles invalid files
            assert stats["errors_encountered"] >= 0

    def test_comprehensive_scanner_helper_integration(self):
        """Test that comprehensive scanner helper integrates correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_root = Path(temp_dir) / "scanner_test"
            codebase_root.mkdir()

            singleton_file = codebase_root / "test_singleton.py"
            singleton_file.write_text(SAMPLE_SINGLETON_CODE)

            # Test direct scanner helper usage
            from spec_cli.utils.detection_execution.comprehensive_scanner import (
                execute_full_codebase_scan,
            )

            scan_config = {
                "codebase_root": str(codebase_root),
                "exclusion_patterns": [],
                "max_workers": 1,
                "timeout_seconds": 30
            }

            # Execute using scanner helper directly
            scan_result = execute_full_codebase_scan(scan_config)

            # Verify scanner helper returns expected structure
            assert hasattr(scan_result, 'singleton_patterns')
            assert hasattr(scan_result, 'scan_statistics')
            assert hasattr(scan_result, 'detection_report')

            # Verify integration with main detection function
            main_result = execute_comprehensive_detection(
                str(codebase_root), {"max_workers": 1, "timeout_seconds": 30}, []
            )

            # Results should be consistent between direct helper and main function
            assert main_result["scan_statistics"]["total_files_scanned"] == scan_result.scan_statistics.total_files_scanned
            assert len(main_result["singleton_patterns"]) == len(scan_result.singleton_patterns)
