"""Integration tests for Slice 3.4: Detection Accuracy Validation and Baseline Finalization."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slice_3_4_accuracy_validation import (
    MigrationPlan,
    finalize_singleton_baseline,
    generate_accuracy_validation_report,
    validate_singleton_detection_accuracy,
)

# Test constants
DEFAULT_ACCURACY_THRESHOLD = 0.95
HIGH_ACCURACY_SCORE = 0.97
HIGH_COVERAGE_SCORE = 0.90
SAMPLE_LINE_NUMBER = 42
SAMPLE_CONFIDENCE_SCORE = 0.88
EXPECTED_TRUE_POSITIVES = 4
EXPECTED_FALSE_POSITIVES = 1
EXPECTED_FALSE_NEGATIVES = 1
EXPECTED_TOTAL_PATTERNS = 5
DEFAULT_EFFORT_HOURS = 40

class TestSlice34EndToEndIntegration:
    """Integration tests for complete detection accuracy validation workflow."""

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    @patch("slice_3_4_accuracy_validation.analyze_singleton_usage")
    def test_complete_accuracy_validation_pipeline(self, mock_analyze, mock_detect):
        """Test complete end-to-end accuracy validation and baseline finalization."""
        # Setup comprehensive mock detection results
        from pathlib import Path

        from spec_cli.utils.singleton_detection import SingletonViolation

        mock_violations = [
            SingletonViolation(
                file_path=Path("src/services/user_service.py"),
                line_number=15,
                column=0,
                pattern_type="class_singleton",
                description="UserService singleton class",
                code_snippet="class UserService:",
            ),
            SingletonViolation(
                file_path=Path("src/config/app_config.py"),
                line_number=8,
                column=0,
                pattern_type="module_singleton",
                description="Global configuration singleton",
                code_snippet="config = {}",
            ),
            SingletonViolation(
                file_path=Path("src/database/connection.py"),
                line_number=25,
                column=0,
                pattern_type="instance_singleton",
                description="Database connection singleton",
                code_snippet="_connection = None",
            ),
            SingletonViolation(
                file_path=Path("src/cache/redis_client.py"),
                line_number=12,
                column=0,
                pattern_type="class_singleton",
                description="Redis client singleton",
                code_snippet="class RedisClient:",
            ),
            SingletonViolation(
                file_path=Path("src/utils/logger.py"),
                line_number=5,
                column=0,
                pattern_type="module_singleton",
                description="Logger singleton instance",
                code_snippet="logger = None",
            ),
        ]
        mock_detect.return_value = mock_violations

        # Mock singleton usage analysis
        mock_usage = Mock()
        mock_usage.complexity_score = 5
        mock_analyze.return_value = [mock_usage]

        # Define known patterns (includes one false negative and excludes one false positive)
        known_patterns = [
            "src/services/user_service.py:15",
            "src/config/app_config.py:8",
            "src/database/connection.py:25",
            "src/cache/redis_client.py:12",
            "src/auth/session_manager.py:30",  # This will be false negative
            # "src/utils/logger.py:5" excluded - will be false positive
        ]

        # Create comprehensive migration plan
        migration_plan = MigrationPlan(
            patterns=[
                {
                    "file_path": "src/services/user_service.py",
                    "line_number": 15,
                    "pattern_type": "class_singleton",
                    "complexity_score": 7,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 12,
                    "confidence_score": 0.92,
                },
                {
                    "file_path": "src/config/app_config.py",
                    "line_number": 8,
                    "pattern_type": "module_singleton",
                    "complexity_score": 4,
                    "migration_strategy": "factory_pattern",
                    "effort_estimate": 6,
                    "confidence_score": 0.88,
                },
                {
                    "file_path": "src/database/connection.py",
                    "line_number": 25,
                    "pattern_type": "instance_singleton",
                    "complexity_score": 9,
                    "migration_strategy": "connection_pool",
                    "effort_estimate": 15,
                    "confidence_score": 0.95,
                },
                {
                    "file_path": "src/cache/redis_client.py",
                    "line_number": 12,
                    "pattern_type": "class_singleton",
                    "complexity_score": 5,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 8,
                    "confidence_score": 0.89,
                },
            ],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=DEFAULT_EFFORT_HOURS,
            risk_assessment="medium",
            implementation_steps=[
                "Analyze singleton dependencies",
                "Implement dependency injection framework",
                "Migrate high-risk singletons first",
                "Update tests for new patterns",
                "Validate migration completeness",
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target_directory = Path(temp_dir)

            # Step 1: Validate detection accuracy
            accuracy_report = validate_singleton_detection_accuracy(
                target_directory, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

            # Verify accuracy metrics
            assert accuracy_report.true_positives == EXPECTED_TRUE_POSITIVES
            assert accuracy_report.false_positives == EXPECTED_FALSE_POSITIVES
            assert accuracy_report.false_negatives == EXPECTED_FALSE_NEGATIVES
            assert accuracy_report.total_detected_patterns == EXPECTED_TOTAL_PATTERNS
            assert accuracy_report.precision == 0.8  # 4/(4+1)
            assert accuracy_report.recall == 0.8      # 4/(4+1)

            # Step 2: Finalize singleton baseline
            singleton_baseline = finalize_singleton_baseline(
                accuracy_report, migration_plan, target_directory
            )

            # Verify baseline finalization
            assert singleton_baseline.total_patterns == EXPECTED_TOTAL_PATTERNS
            assert len(singleton_baseline.validated_patterns) == len(migration_plan.patterns)
            assert singleton_baseline.migration_readiness is True
            assert singleton_baseline.approval_status is True
            assert singleton_baseline.baseline_timestamp is not None

            # Step 3: Generate comprehensive validation report
            validation_report = generate_accuracy_validation_report(singleton_baseline)

            # Verify comprehensive report structure
            assert "validation_summary" in validation_report
            assert "accuracy_metrics" in validation_report
            assert "completeness_analysis" in validation_report
            assert "validated_patterns" in validation_report
            assert "quality_issues" in validation_report

            # Verify report content
            summary = validation_report["validation_summary"]
            assert summary["total_patterns_detected"] == EXPECTED_TOTAL_PATTERNS
            assert summary["validation_passed"] is True
            assert summary["migration_readiness"] is True
            assert summary["baseline_approved"] is True

            # Verify accuracy metrics in report
            metrics = validation_report["accuracy_metrics"]
            assert metrics["true_positives"] == EXPECTED_TRUE_POSITIVES
            assert metrics["false_positives"] == EXPECTED_FALSE_POSITIVES
            assert metrics["false_negatives"] == EXPECTED_FALSE_NEGATIVES
            assert metrics["precision"] == 0.8
            assert metrics["recall"] == 0.8

            # Verify quality issues tracking
            quality_issues = validation_report["quality_issues"]
            assert len(quality_issues["false_positive_details"]) == EXPECTED_FALSE_POSITIVES
            assert len(quality_issues["false_negative_details"]) == EXPECTED_FALSE_NEGATIVES

            # Verify mock calls - functions are called for each Python file
            assert mock_detect.called
            assert mock_analyze.called

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    def test_accuracy_validation_with_insufficient_accuracy(self, mock_detect):
        """Test integration workflow when detection accuracy is insufficient."""
        # Setup mock with poor accuracy (many false positives/negatives)
        mock_detect.return_value = [
            {
                "file_path": "src/false_positive_1.py",
                "pattern_type": "class_singleton",
                "line_number": 10,
                "confidence_score": 0.60,
                "description": "False positive pattern",
            },
            {
                "file_path": "src/false_positive_2.py",
                "pattern_type": "module_singleton",
                "line_number": 20,
                "confidence_score": 0.55,
                "description": "Another false positive",
            },
            {
                "file_path": "src/true_singleton.py",
                "pattern_type": "class_singleton",
                "line_number": 15,
                "confidence_score": 0.85,
                "description": "Actual singleton pattern",
            },
        ]

        # Many known patterns that weren't detected (false negatives)
        known_patterns = [
            "src/true_singleton.py:15",  # Only this one detected
            "src/missed_singleton_1.py:25",
            "src/missed_singleton_2.py:30",
            "src/missed_singleton_3.py:40",
            "src/missed_singleton_4.py:50",
        ]

        migration_plan = MigrationPlan(
            patterns=[],  # No valid patterns due to poor detection
            coverage_percentage=0.30,  # Low coverage
            estimated_effort_hours=5,
            risk_assessment="low",
            implementation_steps=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target_directory = Path(temp_dir)

            # Validate detection accuracy (should fail)
            accuracy_report = validate_singleton_detection_accuracy(
                target_directory, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

            # Verify poor accuracy metrics
            assert accuracy_report.true_positives == 1
            assert accuracy_report.false_positives == 2
            assert accuracy_report.false_negatives == 4
            assert accuracy_report.accuracy_percentage < DEFAULT_ACCURACY_THRESHOLD
            assert accuracy_report.validation_passed is False
            assert accuracy_report.baseline_approved is False

            # Baseline finalization should fail
            with pytest.raises(ValueError, match="Accuracy report validation must pass"):
                finalize_singleton_baseline(accuracy_report, migration_plan, target_directory)

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    def test_baseline_finalization_with_edge_case_accuracy(self, mock_detect):
        """Test baseline finalization with accuracy right at threshold."""
        # Setup detection results with exactly 95% accuracy
        mock_detect.return_value = [
            {
                "file_path": f"src/singleton_{i}.py",
                "pattern_type": "class_singleton",
                "line_number": 10 + i,
                "confidence_score": 0.85 + (i * 0.02),
                "description": f"Singleton pattern {i}",
            }
            for i in range(19)  # 19 detected patterns
        ]

        # 20 known patterns (19 true positives, 1 false negative)
        # Accuracy = 19/20 = 0.95 (exactly at threshold)
        known_patterns = [
            f"src/singleton_{i}.py:{10 + i}" for i in range(19)
        ] + ["src/missed_singleton.py:100"]  # One false negative

        migration_plan = MigrationPlan(
            patterns=[
                {
                    "file_path": f"src/singleton_{i}.py",
                    "line_number": 10 + i,
                    "pattern_type": "class_singleton",
                    "complexity_score": 5,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 6,
                    "confidence_score": 0.85 + (i * 0.02),
                }
                for i in range(19)
            ],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=120,  # 19 patterns * 6 hours
            risk_assessment="medium",
            implementation_steps=["Migrate all detected singletons"],
        )

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("slice_3_4_accuracy_validation._calculate_pattern_diversity") as mock_diversity,
        ):
            target_directory = Path(temp_dir)
            mock_diversity.return_value = 0.80  # Good diversity

            # Validate detection accuracy (should pass at threshold)
            accuracy_report = validate_singleton_detection_accuracy(
                target_directory, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

            # Verify accuracy is exactly at threshold
            assert accuracy_report.accuracy_percentage == DEFAULT_ACCURACY_THRESHOLD
            assert accuracy_report.accuracy_threshold_met is True
            assert accuracy_report.validation_passed is True
            assert accuracy_report.baseline_approved is True

            # Baseline finalization should succeed
            singleton_baseline = finalize_singleton_baseline(
                accuracy_report, migration_plan, target_directory
            )

            assert singleton_baseline.approval_status is True
            assert singleton_baseline.migration_readiness is True
            assert len(singleton_baseline.validated_patterns) == 19

    @patch("slice_3_4_accuracy_validation.scan_for_singleton_patterns")
    def test_integration_with_complex_migration_scenarios(self, mock_detect):
        """Test integration with complex migration scenarios and pattern types."""
        # Setup diverse detection results with different pattern types
        mock_detect.return_value = [
            {
                "file_path": "src/auth/session_manager.py",
                "pattern_type": "metaclass_singleton",
                "line_number": 18,
                "confidence_score": 0.94,
                "description": "Metaclass-based singleton pattern",
            },
            {
                "file_path": "src/config/environment.py",
                "pattern_type": "decorator_singleton",
                "line_number": 5,
                "confidence_score": 0.91,
                "description": "Decorator-based singleton",
            },
            {
                "file_path": "src/logging/system_logger.py",
                "pattern_type": "borg_singleton",
                "line_number": 12,
                "confidence_score": 0.87,
                "description": "Borg pattern singleton",
            },
            {
                "file_path": "src/cache/memory_cache.py",
                "pattern_type": "lazy_singleton",
                "line_number": 22,
                "confidence_score": 0.93,
                "description": "Lazy initialization singleton",
            },
        ]

        known_patterns = [
            "src/auth/session_manager.py:18",
            "src/config/environment.py:5",
            "src/logging/system_logger.py:12",
            "src/cache/memory_cache.py:22",
        ]

        # Complex migration plan with varied strategies
        migration_plan = MigrationPlan(
            patterns=[
                {
                    "file_path": "src/auth/session_manager.py",
                    "line_number": 18,
                    "pattern_type": "metaclass_singleton",
                    "complexity_score": 9,
                    "migration_strategy": "registry_pattern",
                    "effort_estimate": 18,
                    "confidence_score": 0.94,
                },
                {
                    "file_path": "src/config/environment.py",
                    "line_number": 5,
                    "pattern_type": "decorator_singleton",
                    "complexity_score": 4,
                    "migration_strategy": "configuration_injection",
                    "effort_estimate": 8,
                    "confidence_score": 0.91,
                },
                {
                    "file_path": "src/logging/system_logger.py",
                    "line_number": 12,
                    "pattern_type": "borg_singleton",
                    "complexity_score": 6,
                    "migration_strategy": "factory_method",
                    "effort_estimate": 12,
                    "confidence_score": 0.87,
                },
                {
                    "file_path": "src/cache/memory_cache.py",
                    "line_number": 22,
                    "pattern_type": "lazy_singleton",
                    "complexity_score": 7,
                    "migration_strategy": "dependency_injection",
                    "effort_estimate": 14,
                    "confidence_score": 0.93,
                },
            ],
            coverage_percentage=HIGH_COVERAGE_SCORE * 100,
            estimated_effort_hours=52,  # Sum of individual efforts
            risk_assessment="high",  # Complex patterns
            implementation_steps=[
                "Analyze metaclass dependencies",
                "Design registry pattern replacement",
                "Implement configuration injection system",
                "Create factory methods for borg patterns",
                "Setup dependency injection for lazy singletons",
                "Comprehensive testing of all migrations",
            ],
        )

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("slice_3_4_accuracy_validation._calculate_pattern_diversity") as mock_diversity,
        ):
            target_directory = Path(temp_dir)
            mock_diversity.return_value = 0.95  # High diversity due to varied patterns

            # Complete integration workflow
            accuracy_report = validate_singleton_detection_accuracy(
                target_directory, known_patterns, DEFAULT_ACCURACY_THRESHOLD
            )

            # Perfect accuracy expected
            assert accuracy_report.true_positives == 4
            assert accuracy_report.false_positives == 0
            assert accuracy_report.false_negatives == 0
            assert accuracy_report.accuracy_percentage == 1.0

            singleton_baseline = finalize_singleton_baseline(
                accuracy_report, migration_plan, target_directory
            )

            # High complexity should still result in approved baseline
            assert singleton_baseline.approval_status is True
            assert singleton_baseline.migration_readiness is True

            # Verify all pattern types are preserved in validated patterns
            validated_types = {
                pattern["pattern_type"] for pattern in singleton_baseline.validated_patterns
            }
            expected_types = {
                "metaclass_singleton",
                "decorator_singleton",
                "borg_singleton",
                "lazy_singleton",
            }
            assert validated_types == expected_types

            # Generate final report
            validation_report = generate_accuracy_validation_report(singleton_baseline)

            # Verify high-quality metrics in report
            assert validation_report["validation_summary"]["baseline_approved"] is True
            assert validation_report["accuracy_metrics"]["precision"] == 1.0
            assert validation_report["accuracy_metrics"]["recall"] == 1.0
            assert validation_report["accuracy_metrics"]["f1_score"] == 1.0
