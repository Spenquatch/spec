"""Unit tests for Slice 3.4: Detection Accuracy Validation and Baseline Finalization."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slice_3_4_accuracy_validation import (
    MigrationPlan,
    SingletonBaseline,
    finalize_singleton_baseline,
    generate_accuracy_validation_report,
    validate_singleton_detection_accuracy,
)
from spec_cli.utils.validation.detection_accuracy_validator import (
    AccuracyReport,
    SingletonPattern,
    calculate_baseline_completeness,
    validate_detection_accuracy,
)

# Test constants to avoid magic numbers
DEFAULT_ACCURACY_THRESHOLD = 0.95
HIGH_ACCURACY_SCORE = 0.97
LOW_ACCURACY_SCORE = 0.85
MINIMUM_COVERAGE_THRESHOLD = 0.80
HIGH_COVERAGE_SCORE = 0.90
SAMPLE_LINE_NUMBER = 42
SAMPLE_CONFIDENCE_SCORE = 0.88
EXPECTED_TRUE_POSITIVES = 3
EXPECTED_FALSE_POSITIVES = 1
EXPECTED_FALSE_NEGATIVES = 1
EXPECTED_TOTAL_PATTERNS = 4
DEFAULT_EFFORT_HOURS = 25
PATTERN_DIVERSITY_SCORE = 0.75

class TestValidateDetectionAccuracy:
    """Test cases for validate_detection_accuracy function."""

    def test_validate_detection_accuracy_perfect_match(self):
        """Test validation with perfect pattern matching."""
        detected_patterns = [
            SingletonPattern(
                file_path=Path("src/singleton.py"),
                pattern_type="class_singleton",
                line_number=SAMPLE_LINE_NUMBER,
                confidence_score=SAMPLE_CONFIDENCE_SCORE,
                description="Singleton class pattern",
            )
        ]
        known_patterns = ["src/singleton.py:42"]

        result = validate_detection_accuracy(
            detected_patterns, known_patterns, DEFAULT_ACCURACY_THRESHOLD
        )

        assert result.true_positives == 1
        assert result.false_positives == 0
        assert result.false_negatives == 0
        assert result.accuracy_percentage == 1.0
        assert result.validation_passed is True
        assert result.accuracy_threshold_met is True

    def test_validate_detection_accuracy_with_false_positives(self):
        """Test validation with false positive detections."""
        detected_patterns = [
            SingletonPattern(
                file_path=Path("src/singleton.py"),
                pattern_type="class_singleton",
                line_number=SAMPLE_LINE_NUMBER,
                confidence_score=SAMPLE_CONFIDENCE_SCORE,
                description="Singleton class pattern",
            ),
            SingletonPattern(
                file_path=Path("src/not_singleton.py"),
                pattern_type="class_singleton",
                line_number=10,
                confidence_score=0.60,
                description="False positive pattern",
            ),
        ]
        known_patterns = ["src/singleton.py:42"]

        result = validate_detection_accuracy(
            detected_patterns, known_patterns, DEFAULT_ACCURACY_THRESHOLD
        )

        assert result.true_positives == 1
        assert result.false_positives == 1
        assert result.false_negatives == 0
        assert result.accuracy_percentage == 0.5  # 1 true positive out of 2 detected
        assert result.validation_passed is False  # Below threshold
        assert len(result.false_positive_details) == 1

    def test_validate_detection_accuracy_with_false_negatives(self):
        """Test validation with false negative detections."""
        detected_patterns = [
            SingletonPattern(
                file_path=Path("src/singleton.py"),
                pattern_type="class_singleton",
                line_number=SAMPLE_LINE_NUMBER,
                confidence_score=SAMPLE_CONFIDENCE_SCORE,
                description="Singleton class pattern",
            )
        ]
        known_patterns = ["src/singleton.py:42", "src/missed_singleton.py:20"]

        result = validate_detection_accuracy(
            detected_patterns, known_patterns, DEFAULT_ACCURACY_THRESHOLD
        )

        assert result.true_positives == 1
        assert result.false_positives == 0
        assert result.false_negatives == 1
        assert result.accuracy_percentage == 0.5  # 1 true positive out of 2 known
        assert result.validation_passed is False
        assert len(result.false_negative_details) == 1

    def test_validate_detection_accuracy_invalid_threshold(self):
        """Test validation with invalid accuracy threshold."""
        detected_patterns = []
        known_patterns = []

        with pytest.raises(ValueError, match="Accuracy threshold must be between 0 and 1"):
            validate_detection_accuracy(detected_patterns, known_patterns, 1.5)

    def test_validate_detection_accuracy_invalid_input_types(self):
        """Test validation with invalid input types."""
        with pytest.raises(TypeError, match="detected_patterns must be a list"):
            validate_detection_accuracy("invalid", [], DEFAULT_ACCURACY_THRESHOLD)

        with pytest.raises(TypeError, match="known_patterns must be a list"):
            validate_detection_accuracy([], "invalid", DEFAULT_ACCURACY_THRESHOLD)

    def test_validate_detection_accuracy_empty_inputs(self):
        """Test validation with empty pattern lists."""
        result = validate_detection_accuracy([], [], DEFAULT_ACCURACY_THRESHOLD)

        assert result.true_positives == 0
        assert result.false_positives == 0
        assert result.false_negatives == 0
        assert result.accuracy_percentage == 0.0
        assert result.validation_passed is False  # Empty input should fail validation

class TestCalculateBaselineCompleteness:
    """Test cases for calculate_baseline_completeness function."""

    def test_calculate_baseline_completeness_high_scores(self):
        """Test baseline completeness with high scores across all metrics."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=0,
            false_negatives=0,
            total_known_patterns=EXPECTED_TRUE_POSITIVES,
            total_detected_patterns=EXPECTED_TRUE_POSITIVES,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        result = calculate_baseline_completeness(
            accuracy_report, HIGH_COVERAGE_SCORE, PATTERN_DIVERSITY_SCORE
        )

        assert result["completeness_score"] > 0.85
        assert result["baseline_ready"] is True
        assert result["approval_criteria"]["accuracy_approved"] is True
        assert result["approval_criteria"]["coverage_sufficient"] is True
        assert result["approval_criteria"]["diversity_sufficient"] is True

    def test_calculate_baseline_completeness_low_coverage(self):
        """Test baseline completeness with insufficient migration coverage."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=0,
            false_negatives=0,
            total_known_patterns=EXPECTED_TRUE_POSITIVES,
            total_detected_patterns=EXPECTED_TRUE_POSITIVES,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        low_coverage = 0.60  # Below threshold
        result = calculate_baseline_completeness(
            accuracy_report, low_coverage, PATTERN_DIVERSITY_SCORE
        )

        assert result["baseline_ready"] is False
        assert result["approval_criteria"]["coverage_sufficient"] is False

    def test_calculate_baseline_completeness_component_weights(self):
        """Test that completeness score components have correct weights."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=0,
            false_negatives=0,
            total_known_patterns=EXPECTED_TRUE_POSITIVES,
            total_detected_patterns=EXPECTED_TRUE_POSITIVES,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy_percentage=1.0,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        result = calculate_baseline_completeness(accuracy_report, 1.0, 1.0)

        # Check component weights: accuracy=0.5, coverage=0.3, diversity=0.2
        expected_accuracy_component = 1.0 * 0.5
        expected_coverage_component = 1.0 * 0.3
        expected_diversity_component = 1.0 * 0.2

        assert result["accuracy_component"] == expected_accuracy_component
        assert result["coverage_component"] == expected_coverage_component
        assert result["diversity_component"] == expected_diversity_component

class TestValidateSingletonDetectionAccuracy:
    """Test cases for validate_singleton_detection_accuracy function."""

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    def test_validate_singleton_detection_accuracy_success(self, mock_detect):
        """Test successful singleton detection accuracy validation."""
        # Setup mock detection results
        # Mock the return value as SingletonViolation objects
        from pathlib import Path

        from spec_cli.utils.singleton_detection import SingletonViolation

        mock_violation = SingletonViolation(
            file_path=Path("src/singleton.py"),
            line_number=SAMPLE_LINE_NUMBER,
            column=0,
            pattern_type="class_singleton",
            description="Singleton class pattern",
            code_snippet="class Singleton:",
        )
        mock_detect.return_value = [mock_violation]

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            # Create a dummy Python file to trigger the scan
            (target_dir / "singleton.py").write_text("class Singleton: pass")
            known_patterns = ["singleton.py:42"]

            result = validate_singleton_detection_accuracy(
                target_dir, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

            assert isinstance(result, AccuracyReport)
            assert result.true_positives == 1
            # scan_for_singleton_patterns is called for each Python file found
            assert mock_detect.called

    def test_validate_singleton_detection_accuracy_invalid_directory(self):
        """Test validation with non-existent target directory."""
        invalid_dir = Path("/nonexistent/directory")
        known_patterns = ["src/singleton.py:42"]

        with pytest.raises(ValueError, match="Target directory does not exist"):
            validate_singleton_detection_accuracy(
                invalid_dir, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

    def test_validate_singleton_detection_accuracy_invalid_threshold(self):
        """Test validation with invalid accuracy threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            known_patterns = ["src/singleton.py:42"]

            with pytest.raises(ValueError, match="Accuracy threshold must be between 0 and 1"):
                validate_singleton_detection_accuracy(target_dir, known_patterns, 1.5)

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    def test_validate_singleton_detection_accuracy_detection_failure(self, mock_detect):
        """Test handling of detection system failure."""
        mock_detect.side_effect = Exception("Detection system error")

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            # Create a dummy Python file to trigger the scan
            (target_dir / "singleton.py").write_text("class Singleton: pass")
            known_patterns = ["singleton.py:42"]

            with pytest.raises(RuntimeError, match="Detection system execution failed"):
                validate_singleton_detection_accuracy(
                    target_dir, known_patterns, DEFAULT_ACCURACY_THRESHOLD
                )

class TestFinalizeSingletonBaseline:
    """Test cases for finalize_singleton_baseline function."""

    def test_finalize_singleton_baseline_success(self):
        """Test successful singleton baseline finalization."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=EXPECTED_FALSE_POSITIVES,
            false_negatives=EXPECTED_FALSE_NEGATIVES,
            total_known_patterns=EXPECTED_TOTAL_PATTERNS,
            total_detected_patterns=EXPECTED_TOTAL_PATTERNS,
            precision=0.75,
            recall=0.75,
            f1_score=0.75,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        migration_plan = MigrationPlan(
            patterns=[
                {
                    "file_path": "src/singleton.py",
                    "line_number": SAMPLE_LINE_NUMBER,
                    "pattern_type": "class_singleton",
                    "complexity_score": 5,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 8,
                    "confidence_score": SAMPLE_CONFIDENCE_SCORE,
                }
            ],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,  # Convert to percentage
            estimated_effort_hours=DEFAULT_EFFORT_HOURS,
            risk_assessment="medium",
            implementation_steps=["Step 1", "Step 2"],
        )

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("slice_3_4_accuracy_validation._calculate_pattern_diversity") as mock_diversity,
        ):
            target_dir = Path(temp_dir)
            mock_diversity.return_value = PATTERN_DIVERSITY_SCORE

            result = finalize_singleton_baseline(accuracy_report, migration_plan, target_dir)

            assert isinstance(result, SingletonBaseline)
            assert result.total_patterns == EXPECTED_TOTAL_PATTERNS
            assert result.migration_readiness is True
            assert result.approval_status is True
            assert len(result.validated_patterns) == 1
            assert result.baseline_timestamp is not None

    def test_finalize_singleton_baseline_validation_failed(self):
        """Test baseline finalization with failed validation."""
        accuracy_report = AccuracyReport(
            true_positives=1,
            false_positives=1,
            false_negatives=1,
            total_known_patterns=2,
            total_detected_patterns=2,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            accuracy_percentage=LOW_ACCURACY_SCORE,
            validation_passed=False,  # Validation failed
            accuracy_threshold_met=False,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=False,
        )

        migration_plan = MigrationPlan(
            patterns=[],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=DEFAULT_EFFORT_HOURS,
            risk_assessment="low",
            implementation_steps=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with pytest.raises(ValueError, match="Accuracy report validation must pass"):
                finalize_singleton_baseline(accuracy_report, migration_plan, target_dir)

    def test_finalize_singleton_baseline_low_accuracy(self):
        """Test baseline finalization with accuracy below threshold."""
        accuracy_report = AccuracyReport(
            true_positives=2,
            false_positives=1,
            false_negatives=1,
            total_known_patterns=3,
            total_detected_patterns=3,
            precision=0.67,
            recall=0.67,
            f1_score=0.67,
            accuracy_percentage=LOW_ACCURACY_SCORE,  # Below 95% threshold
            validation_passed=True,  # Passed but low accuracy
            accuracy_threshold_met=False,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=False,
        )

        migration_plan = MigrationPlan(
            patterns=[],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=DEFAULT_EFFORT_HOURS,
            risk_assessment="medium",
            implementation_steps=[],
        )

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("slice_3_4_accuracy_validation._calculate_pattern_diversity") as mock_diversity,
        ):
            target_dir = Path(temp_dir)
            mock_diversity.return_value = PATTERN_DIVERSITY_SCORE

            result = finalize_singleton_baseline(accuracy_report, migration_plan, target_dir)

            assert result.migration_readiness is False  # Low accuracy
            assert result.approval_status is False

class TestGenerateAccuracyValidationReport:
    """Test cases for generate_accuracy_validation_report function."""

    def test_generate_accuracy_validation_report_success(self):
        """Test successful validation report generation."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=EXPECTED_FALSE_POSITIVES,
            false_negatives=EXPECTED_FALSE_NEGATIVES,
            total_known_patterns=EXPECTED_TOTAL_PATTERNS,
            total_detected_patterns=EXPECTED_TOTAL_PATTERNS,
            precision=0.75,
            recall=0.75,
            f1_score=0.75,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        baseline = SingletonBaseline(
            total_patterns=EXPECTED_TOTAL_PATTERNS,
            validated_patterns=[],
            accuracy_report=accuracy_report,
            completeness_metrics={"completeness_score": 0.90, "baseline_ready": True},
            migration_readiness=True,
            baseline_timestamp=datetime.now().isoformat(),
            approval_status=True,
        )

        result = generate_accuracy_validation_report(baseline)

        assert "validation_summary" in result
        assert "accuracy_metrics" in result
        assert "completeness_analysis" in result
        assert "validated_patterns" in result
        assert "quality_issues" in result
        assert result["validation_summary"]["baseline_approved"] is True

    def test_generate_accuracy_validation_report_not_approved(self):
        """Test report generation with non-approved baseline."""
        accuracy_report = AccuracyReport(
            true_positives=1,
            false_positives=1,
            false_negatives=1,
            total_known_patterns=2,
            total_detected_patterns=2,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            accuracy_percentage=LOW_ACCURACY_SCORE,
            validation_passed=False,
            accuracy_threshold_met=False,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=False,
        )

        baseline = SingletonBaseline(
            total_patterns=2,
            validated_patterns=[],
            accuracy_report=accuracy_report,
            completeness_metrics={"completeness_score": 0.60, "baseline_ready": False},
            migration_readiness=False,
            baseline_timestamp=datetime.now().isoformat(),
            approval_status=False,  # Not approved
        )

        with pytest.raises(ValueError, match="Baseline must be approved"):
            generate_accuracy_validation_report(baseline)

    def test_generate_accuracy_validation_report_with_file_output(self):
        """Test report generation with file output."""
        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=0,
            false_negatives=0,
            total_known_patterns=EXPECTED_TRUE_POSITIVES,
            total_detected_patterns=EXPECTED_TRUE_POSITIVES,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        baseline = SingletonBaseline(
            total_patterns=EXPECTED_TRUE_POSITIVES,
            validated_patterns=[],
            accuracy_report=accuracy_report,
            completeness_metrics={"completeness_score": 0.95, "baseline_ready": True},
            migration_readiness=True,
            baseline_timestamp=datetime.now().isoformat(),
            approval_status=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "validation_report.json"

            result = generate_accuracy_validation_report(baseline, output_path)

            assert output_path.exists()
            assert "validation_summary" in result

            # Verify file content
            with output_path.open("r", encoding="utf-8") as f:
                saved_report = json.load(f)
            assert saved_report["validation_summary"]["baseline_approved"] is True

class TestSingletonPattern:
    """Test cases for SingletonPattern dataclass."""

    def test_singleton_pattern_hash(self):
        """Test that SingletonPattern objects are hashable for set operations."""
        pattern1 = SingletonPattern(
            file_path=Path("src/test.py"),
            pattern_type="class_singleton",
            line_number=SAMPLE_LINE_NUMBER,
            confidence_score=SAMPLE_CONFIDENCE_SCORE,
            description="Test pattern",
        )

        pattern2 = SingletonPattern(
            file_path=Path("src/test.py"),
            pattern_type="class_singleton",
            line_number=SAMPLE_LINE_NUMBER,
            confidence_score=0.90,  # Different confidence
            description="Different description",
        )

        # Same file, type, and line should hash to same value
        assert hash(pattern1) == hash(pattern2)

        # Should be usable in sets - but different confidence/description makes them different
        pattern_set = {pattern1, pattern2}
        assert len(pattern_set) == 1  # Same location should be treated as one pattern

class TestPrivateHelperFunctions:
    """Test cases for private helper functions."""

    @patch("slice_3_4_accuracy_validation.analyze_singleton_usage")
    def test_calculate_pattern_diversity_success(self, mock_analyze):
        """Test successful pattern diversity calculation."""
        from slice_3_4_accuracy_validation import _calculate_pattern_diversity

        # Mock singleton usage analysis results
        mock_usage = Mock()
        mock_usage.complexity_score = 5
        mock_analyze.return_value = [mock_usage]

        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=EXPECTED_FALSE_POSITIVES,
            false_negatives=EXPECTED_FALSE_NEGATIVES,
            total_known_patterns=EXPECTED_TOTAL_PATTERNS,
            total_detected_patterns=EXPECTED_TOTAL_PATTERNS,
            precision=0.75,
            recall=0.75,
            f1_score=0.75,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[
                {"pattern_type": "class_singleton"},
                {"pattern_type": "module_singleton"},
            ],
            false_negative_details=[],
            baseline_approved=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            result = _calculate_pattern_diversity(accuracy_report, target_dir)

            assert 0 <= result <= 1  # Valid diversity score range
            # analyze_singleton_usage is called for each Python file
            assert mock_analyze.called

    def test_prepare_validated_patterns_success(self):
        """Test successful preparation of validated patterns."""
        from slice_3_4_accuracy_validation import _prepare_validated_patterns

        accuracy_report = AccuracyReport(
            true_positives=EXPECTED_TRUE_POSITIVES,
            false_positives=0,
            false_negatives=0,
            total_known_patterns=EXPECTED_TRUE_POSITIVES,
            total_detected_patterns=EXPECTED_TRUE_POSITIVES,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy_percentage=HIGH_ACCURACY_SCORE,
            validation_passed=True,
            accuracy_threshold_met=True,
            false_positive_details=[],
            false_negative_details=[],
            baseline_approved=True,
        )

        migration_plan = MigrationPlan(
            patterns=[
                {
                    "file_path": "src/singleton.py",
                    "line_number": SAMPLE_LINE_NUMBER,
                    "pattern_type": "class_singleton",
                    "complexity_score": 5,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 8,
                    "confidence_score": SAMPLE_CONFIDENCE_SCORE,
                }
            ],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=DEFAULT_EFFORT_HOURS,
            risk_assessment="medium",
            implementation_steps=[],
        )

        result = _prepare_validated_patterns(accuracy_report, migration_plan)

        assert len(result) == 1
        pattern = result[0]
        assert pattern["file_path"] == "src/singleton.py"
        assert pattern["line_number"] == SAMPLE_LINE_NUMBER
        assert pattern["validation_status"] == "validated"
