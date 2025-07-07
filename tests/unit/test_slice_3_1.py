"""Unit tests for Slice 3.1: Comprehensive Singleton Detection Execution."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from slice_3_1_detection_execution import (
    DetectionExecutionError,
    execute_comprehensive_detection,
    generate_detection_summary,
    save_detection_results,
)
from spec_cli.utils.detection_execution.comprehensive_scanner import (
    ComprehensiveScanResult,
    ScanStatistics,
    SingletonPattern,
)

# Test constants
SAMPLE_CODEBASE_ROOT = "spec_cli"
DEFAULT_SCAN_CONFIG = {"max_workers": 4, "timeout_seconds": 300}
DEFAULT_EXCLUSION_PATTERNS = ["test_*", "*.pyc"]
SAMPLE_SINGLETON_NAME = "TestSingleton"
SAMPLE_FILE_PATH = Path("spec_cli/core/test_module.py")
SAMPLE_LINE_NUMBER = 42
SAMPLE_PATTERN_TYPE = "metaclass_singleton"
SAMPLE_DESCRIPTION = "Class uses singleton metaclass: SingletonMeta"
SAMPLE_CODE_SNIPPET = "class TestSingleton(metaclass=SingletonMeta):"

class TestExecuteComprehensiveDetection:
    """Test comprehensive detection execution logic."""

    @patch("slice_3_1_detection_execution.execute_full_codebase_scan")
    def test_execute_comprehensive_detection_success(self, mock_scan):
        """Test successful comprehensive detection execution."""
        # Arrange
        mock_pattern = SingletonPattern(
            file_path=SAMPLE_FILE_PATH,
            line_number=SAMPLE_LINE_NUMBER,
            pattern_type=SAMPLE_PATTERN_TYPE,
            singleton_name=SAMPLE_SINGLETON_NAME,
            description=SAMPLE_DESCRIPTION,
            code_snippet=SAMPLE_CODE_SNIPPET,
        )

        mock_stats = ScanStatistics(
            total_files_scanned=10,
            python_files_found=10,
            singleton_patterns_detected=1,
            scan_duration_seconds=5.0,
            files_per_second=2.0,
            errors_encountered=0,
            excluded_files=0,
        )

        mock_result = ComprehensiveScanResult(
            singleton_patterns=[mock_pattern],
            scan_statistics=mock_stats,
            detection_report="Test report",
            scan_config=DEFAULT_SCAN_CONFIG,
            error_details=[],
        )
        mock_scan.return_value = mock_result

        # Act
        result = execute_comprehensive_detection(
            SAMPLE_CODEBASE_ROOT, DEFAULT_SCAN_CONFIG, DEFAULT_EXCLUSION_PATTERNS
        )

        # Assert
        assert "singleton_patterns" in result
        assert "scan_statistics" in result
        assert "detection_report" in result
        assert len(result["singleton_patterns"]) == 1

        pattern = result["singleton_patterns"][0]
        assert pattern["singleton_name"] == SAMPLE_SINGLETON_NAME
        assert pattern["pattern_type"] == SAMPLE_PATTERN_TYPE
        assert pattern["file_path"] == str(SAMPLE_FILE_PATH)

        mock_scan.assert_called_once()
        call_args = mock_scan.call_args[0][0]
        assert call_args["codebase_root"] == SAMPLE_CODEBASE_ROOT
        assert call_args["exclusion_patterns"] == DEFAULT_EXCLUSION_PATTERNS

    def test_execute_comprehensive_detection_invalid_codebase_root(self):
        """Test detection execution with invalid codebase root."""
        # Test empty string
        with pytest.raises(DetectionExecutionError, match="codebase_root must be a non-empty string"):
            execute_comprehensive_detection("", DEFAULT_SCAN_CONFIG, DEFAULT_EXCLUSION_PATTERNS)

        # Test None
        with pytest.raises(DetectionExecutionError, match="codebase_root must be a non-empty string"):
            execute_comprehensive_detection(None, DEFAULT_SCAN_CONFIG, DEFAULT_EXCLUSION_PATTERNS)

        # Test non-string
        with pytest.raises(DetectionExecutionError, match="codebase_root must be a non-empty string"):
            execute_comprehensive_detection(123, DEFAULT_SCAN_CONFIG, DEFAULT_EXCLUSION_PATTERNS)

    def test_execute_comprehensive_detection_invalid_scan_config(self):
        """Test detection execution with invalid scan config."""
        with pytest.raises(DetectionExecutionError, match="scan_config must be a dictionary"):
            execute_comprehensive_detection(SAMPLE_CODEBASE_ROOT, "not_a_dict", DEFAULT_EXCLUSION_PATTERNS)

    def test_execute_comprehensive_detection_invalid_exclusion_patterns(self):
        """Test detection execution with invalid exclusion patterns."""
        with pytest.raises(DetectionExecutionError, match="exclusion_patterns must be a list"):
            execute_comprehensive_detection(SAMPLE_CODEBASE_ROOT, DEFAULT_SCAN_CONFIG, "not_a_list")

    @patch("slice_3_1_detection_execution.execute_full_codebase_scan")
    def test_execute_comprehensive_detection_scan_failure(self, mock_scan):
        """Test detection execution when scan fails."""
        # Arrange
        mock_scan.side_effect = Exception("Scan failed")

        # Act & Assert
        with pytest.raises(DetectionExecutionError, match="Detection execution failed: Scan failed"):
            execute_comprehensive_detection(
                SAMPLE_CODEBASE_ROOT, DEFAULT_SCAN_CONFIG, DEFAULT_EXCLUSION_PATTERNS
            )

class TestGenerateDetectionSummary:
    """Test detection summary generation."""

    def test_generate_detection_summary_multiple_patterns(self):
        """Test summary generation with multiple patterns."""
        # Arrange
        patterns = [
            {
                "pattern_type": "metaclass_singleton",
                "singleton_name": "SingletonA",
                "file_path": "/path/to/file1.py",
            },
            {
                "pattern_type": "decorator_singleton",
                "singleton_name": "SingletonB",
                "file_path": "/path/to/file2.py",
            },
            {
                "pattern_type": "metaclass_singleton",
                "singleton_name": "SingletonA",
                "file_path": "/path/to/file3.py",
            },
        ]

        # Act
        summary = generate_detection_summary(patterns)

        # Assert
        assert summary["total_patterns"] == 3
        assert summary["unique_singletons"] == 2
        assert summary["files_with_patterns"] == 3
        assert summary["metaclass_singleton"] == 2
        assert summary["decorator_singleton"] == 1

    def test_generate_detection_summary_empty_patterns(self):
        """Test summary generation with empty patterns list."""
        # Act
        summary = generate_detection_summary([])

        # Assert
        assert summary["total_patterns"] == 0
        assert summary["unique_singletons"] == 0
        assert summary["files_with_patterns"] == 0

    def test_generate_detection_summary_unknown_pattern_type(self):
        """Test summary generation with unknown pattern types."""
        # Arrange
        patterns = [
            {"singleton_name": "TestSingleton", "file_path": "/path/to/file.py"}
        ]

        # Act
        summary = generate_detection_summary(patterns)

        # Assert
        assert summary["total_patterns"] == 1
        assert summary["unknown"] == 1

    def test_generate_detection_summary_missing_fields(self):
        """Test summary generation with missing pattern fields."""
        # Arrange
        patterns = [
            {"pattern_type": "test_type"},
            {"singleton_name": "TestSingleton"},
            {"file_path": "/path/to/file.py"},
            {},
        ]

        # Act
        summary = generate_detection_summary(patterns)

        # Assert
        assert summary["total_patterns"] == 4
        assert summary["unique_singletons"] == 1
        assert summary["files_with_patterns"] == 1

class TestSaveDetectionResults:
    """Test saving detection results to file."""

    def test_save_detection_results_success(self):
        """Test successful saving of detection results."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.json"
            results = {
                "singleton_patterns": [
                    {
                        "pattern_type": SAMPLE_PATTERN_TYPE,
                        "singleton_name": SAMPLE_SINGLETON_NAME,
                        "file_path": str(SAMPLE_FILE_PATH),
                    }
                ],
                "summary": {"total_patterns": 1},
            }

            # Act
            save_detection_results(results, output_path)

            # Assert
            assert output_path.exists()
            with output_path.open("r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert "singleton_patterns" in saved_data
            assert "summary" in saved_data
            assert saved_data["summary"]["total_patterns"] == 1

    def test_save_detection_results_creates_directory(self):
        """Test that save_detection_results creates parent directories."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "results.json"
            results = {"test": "data"}

            # Act
            save_detection_results(results, output_path)

            # Assert
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_save_detection_results_path_object_serialization(self):
        """Test saving results with Path objects that need serialization."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.json"
            results = {
                "path_object": Path("/test/path"),
                "nested": {"path_object": Path("/nested/path")},
                "list_with_paths": [{"path": Path("/list/path")}],
            }

            # Act
            save_detection_results(results, output_path)

            # Assert
            assert output_path.exists()
            with output_path.open("r", encoding="utf-8") as f:
                saved_data = json.load(f)

            # All Path objects should be converted to strings
            assert isinstance(saved_data["path_object"], str)
            assert isinstance(saved_data["nested"]["path_object"], str)
            assert isinstance(saved_data["list_with_paths"][0]["path"], str)

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_detection_results_file_error(self, mock_open):
        """Test save_detection_results with file system error."""
        # Arrange
        output_path = Path("/invalid/path/results.json")
        results = {"test": "data"}

        # Act & Assert
        with pytest.raises(DetectionExecutionError, match="Failed to save results"):
            save_detection_results(results, output_path)

class TestComprehensiveScannerHelperIntegration:
    """Test integration with comprehensive scanner helper."""

    @patch("spec_cli.utils.detection_execution.comprehensive_scanner.scan_for_singleton_patterns")
    @patch("spec_cli.utils.detection_execution.comprehensive_scanner.analyze_singleton_usage")
    def test_scanner_helper_integration(self, mock_analyze_usage, mock_scan_patterns):
        """Test that the scanner helper integrates properly with detection utilities."""
        from spec_cli.utils.detection_execution.comprehensive_scanner import (
            _scan_single_file,
        )
        from spec_cli.utils.pattern_analysis import SingletonUsage
        from spec_cli.utils.singleton_detection import SingletonViolation

        # Arrange
        test_file = Path("test_file.py")

        mock_violation = SingletonViolation(
            file_path=test_file,
            line_number=10,
            column=0,
            pattern_type="test_pattern",
            description="Test: TestSingleton",
            code_snippet="class TestSingleton:",
        )
        mock_scan_patterns.return_value = [mock_violation]

        mock_usage = SingletonUsage(
            file_path=test_file,
            line_number=20,
            usage_type="instantiation",
            singleton_name="UsageSingleton",
            context="UsageSingleton()",
        )
        mock_analyze_usage.return_value = [mock_usage]

        # Act
        patterns = _scan_single_file(test_file)

        # Assert
        assert len(patterns) == 2

        # Check violation-based pattern
        violation_pattern = patterns[0]
        assert violation_pattern.singleton_name == "TestSingleton"
        assert violation_pattern.pattern_type == "test_pattern"

        # Check usage-based pattern
        usage_pattern = patterns[1]
        assert usage_pattern.singleton_name == "UsageSingleton"
        assert usage_pattern.pattern_type == "usage_instantiation"

        mock_scan_patterns.assert_called_once_with(test_file)
        mock_analyze_usage.assert_called_once_with(test_file)

class TestDetectionExecutionError:
    """Test DetectionExecutionError exception class."""

    def test_detection_execution_error_with_context(self):
        """Test DetectionExecutionError with execution context."""
        # Arrange
        message = "Test error"
        context = {"test_key": "test_value"}

        # Act
        error = DetectionExecutionError(message, context)

        # Assert
        assert str(error) == message
        assert error.execution_context == context

    def test_detection_execution_error_without_context(self):
        """Test DetectionExecutionError without execution context."""
        # Arrange
        message = "Test error"

        # Act
        error = DetectionExecutionError(message)

        # Assert
        assert str(error) == message
        assert error.execution_context == {}

class TestConfigurationPreperation:
    """Test scan configuration preparation logic."""

    @patch("slice_3_1_detection_execution.execute_full_codebase_scan")
    def test_configuration_preparation_merges_defaults(self, mock_scan):
        """Test that configuration preparation merges with defaults correctly."""
        # Arrange
        mock_stats = ScanStatistics(
            total_files_scanned=0,
            python_files_found=0,
            singleton_patterns_detected=0,
            scan_duration_seconds=0.0,
            files_per_second=0.0,
            errors_encountered=0,
            excluded_files=0,
        )

        mock_scan.return_value = ComprehensiveScanResult(
            singleton_patterns=[],
            scan_statistics=mock_stats,
            detection_report="",
            scan_config={},
            error_details=[],
        )

        custom_config = {"timeout_seconds": 600}
        expected_workers = 4  # Default value

        # Act
        execute_comprehensive_detection(SAMPLE_CODEBASE_ROOT, custom_config, DEFAULT_EXCLUSION_PATTERNS)

        # Assert
        mock_scan.assert_called_once()
        call_config = mock_scan.call_args[0][0]
        assert call_config["max_workers"] == expected_workers
        assert call_config["timeout_seconds"] == 600
        assert call_config["codebase_root"] == SAMPLE_CODEBASE_ROOT
        assert call_config["exclusion_patterns"] == DEFAULT_EXCLUSION_PATTERNS

    @patch("slice_3_1_detection_execution.execute_full_codebase_scan")
    def test_configuration_preparation_overrides_defaults(self, mock_scan):
        """Test that user configuration overrides defaults."""
        # Arrange
        mock_stats = ScanStatistics(
            total_files_scanned=0,
            python_files_found=0,
            singleton_patterns_detected=0,
            scan_duration_seconds=0.0,
            files_per_second=0.0,
            errors_encountered=0,
            excluded_files=0,
        )

        mock_scan.return_value = ComprehensiveScanResult(
            singleton_patterns=[],
            scan_statistics=mock_stats,
            detection_report="",
            scan_config={},
            error_details=[],
        )

        custom_config = {"max_workers": 8, "timeout_seconds": 600}

        # Act
        execute_comprehensive_detection(SAMPLE_CODEBASE_ROOT, custom_config, DEFAULT_EXCLUSION_PATTERNS)

        # Assert
        mock_scan.assert_called_once()
        call_config = mock_scan.call_args[0][0]
        assert call_config["max_workers"] == 8
        assert call_config["timeout_seconds"] == 600
