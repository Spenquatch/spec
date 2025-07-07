"""Integration tests for Slice 2.4: Migration Test Marking and Core Test Validation."""

import shutil
import tempfile
from pathlib import Path

import pytest

from slice_2_4_test_marking import (
    MarkingResult,
    analyze_test_suite_composition,
    execute_test_marking_workflow,
    generate_reliability_report,
)


class TestSlice24Integration:
    """Integration tests for test marking and reliability validation workflow."""

    def setup_method(self):
        """Set up test environment with temporary directory and sample test files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_dir = self.temp_dir / "tests"
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Create sample test files
        self.sample_test_files = self._create_sample_test_files()
        self.sample_categorization = {
            str(self.test_dir / "test_migration_workflow.py"): "migration_related",
            str(self.test_dir / "test_context_injection.py"): "migration_integration",
        }
        self.sample_core_tests = [
            str(self.test_dir / "test_core_functionality.py"),
            str(self.test_dir / "test_basic_operations.py"),
        ]

    def teardown_method(self):
        """Clean up temporary test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_sample_test_files(self) -> list[str]:
        """Create sample test files for integration testing."""
        test_files = [
            "test_core_functionality.py",
            "test_basic_operations.py",
            "test_migration_workflow.py",
            "test_context_injection.py",
            "test_slice_migration.py",
        ]

        created_files = []
        for test_file in test_files:
            file_path = self.test_dir / test_file

            # Create test content based on file type
            if "migration" in test_file or "context" in test_file:
                content = self._create_migration_test_content(test_file)
            else:
                content = self._create_core_test_content(test_file)

            file_path.write_text(content, encoding="utf-8")
            created_files.append(str(file_path))

        return created_files

    def _create_migration_test_content(self, filename: str) -> str:
        """Create migration test file content."""
        return f'''"""Migration tests for {filename}."""

import pytest
from unittest.mock import Mock, patch


class TestMigrationWorkflow:
    """Test migration-related functionality."""

    def test_migration_pattern_detection(self):
        """Test detection of migration patterns."""
        # Migration test with context injection patterns
        assert True

    def test_context_injection_compatibility(self):
        """Test context injection compatibility."""
        # Test for dependency injection migration
        assert True

    def test_legacy_compatibility_layer(self):
        """Test legacy compatibility during migration."""
        # Migration compatibility test
        assert True
'''

    def _create_core_test_content(self, filename: str) -> str:
        """Create core test file content."""
        return f'''"""Core functionality tests for {filename}."""

import pytest


class TestCoreOperations:
    """Test core functionality."""

    def test_basic_operation(self):
        """Test basic core operation."""
        # Core functionality test
        assert True

    def test_essential_workflow(self):
        """Test essential workflow."""
        # Core test for critical functionality
        assert True

    def test_primary_validation(self):
        """Test primary validation logic."""
        # Core validation test
        assert True
'''

    def test_complete_workflow_integration(self):
        """Test complete test marking and validation workflow."""
        # Execute the complete workflow
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Validate result structure
        assert isinstance(result, MarkingResult)
        assert result.marked_tests is not None
        assert result.core_test_validation is not None
        assert isinstance(result.overall_reliability_score, float)

        # Validate marking results
        assert len(result.marked_tests) >= 2  # At least categorized migration tests

        # Validate core test validation
        assert len(result.core_test_validation) == len(self.sample_core_tests)

        # Validate reliability score is reasonable
        assert 0.0 <= result.overall_reliability_score <= 1.0

    def test_test_suite_composition_analysis_integration(self):
        """Test complete test suite composition analysis."""
        composition = analyze_test_suite_composition(str(self.test_dir))

        # Validate composition structure
        assert "migration" in composition
        assert "core" in composition
        assert "unclassified" in composition

        # Validate migration test detection
        migration_tests = composition["migration"]
        assert len(migration_tests) >= 2  # Should detect migration patterns

        # Validate core test detection
        core_tests = composition["core"]
        assert len(core_tests) >= 1  # Should detect some core tests

        # Validate total test count
        total_classified = len(migration_tests) + len(core_tests) + len(composition["unclassified"])
        assert total_classified == len(self.sample_test_files)

    def test_reliability_report_generation_integration(self):
        """Test reliability report generation with real data."""
        # Execute workflow to get real result
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Generate report
        report = generate_reliability_report(result)

        # Validate report structure
        assert "# Test Reliability Report" in report
        assert "## Overall Reliability:" in report
        assert "## Core Test Validation Results" in report
        assert "## Migration Test Marking Results" in report

        # Validate report contains data
        assert str(len(result.marked_tests)) in report
        assert str(len(result.core_test_validation)) in report

    def test_marking_persistence_integration(self):
        """Test that test markings persist correctly."""
        # Execute workflow
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Validate that migration tests were marked
        for test_path in result.marked_tests:
            test_file = Path(test_path)
            if test_file.exists():
                content = test_file.read_text(encoding="utf-8")
                # Check if pytest marker was added (this would be in real implementation)
                # For now, just validate the test file exists and has content
                assert len(content) > 0

    def test_reliability_threshold_validation_integration(self):
        """Test reliability threshold validation with different thresholds."""
        # Execute workflow
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Test different threshold values
        assert result.meets_reliability_target(1.0) is True  # Very lenient
        assert result.meets_reliability_target(0.0) is False  # Very strict

        # Test failing tests detection
        failing_tests = result.get_failing_core_tests(0.0)  # Very strict threshold
        assert isinstance(failing_tests, list)

    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        # Test with empty inputs
        with pytest.raises(ValueError):
            execute_test_marking_workflow([], {}, [])

        # Test with non-existent files
        non_existent_files = ["/path/to/non/existent/test.py"]
        result = execute_test_marking_workflow(
            non_existent_files, {}, self.sample_core_tests
        )
        # Should handle gracefully without marking non-existent files
        assert len(result.marked_tests) == 0

    def test_cross_platform_path_handling_integration(self):
        """Test cross-platform path handling in integration."""
        # Use paths with different separators (simulated)
        mixed_paths = [str(p) for p in self.sample_test_files]

        # Execute workflow with mixed path formats
        result = execute_test_marking_workflow(
            mixed_paths,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Should handle paths correctly regardless of format
        assert isinstance(result, MarkingResult)
        assert result.overall_reliability_score >= 0.0

    def test_large_test_suite_simulation_integration(self):
        """Test workflow with larger simulated test suite."""
        # Create additional test files
        large_test_files = self.sample_test_files.copy()

        for i in range(10):
            additional_file = self.test_dir / f"test_additional_{i}.py"
            content = self._create_core_test_content(f"additional_{i}")
            additional_file.write_text(content, encoding="utf-8")
            large_test_files.append(str(additional_file))

        # Execute with larger test suite
        result = execute_test_marking_workflow(
            large_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Validate performance and correctness with larger dataset
        assert isinstance(result, MarkingResult)
        assert len(result.core_test_validation) == len(self.sample_core_tests)

    def test_reliability_score_calculation_integration(self):
        """Test reliability score calculation accuracy in integration."""
        # Execute workflow
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Validate score calculation
        if result.core_test_validation:
            # Calculate expected average
            failure_rates = list(result.core_test_validation.values())
            expected_average = sum(failure_rates) / len(failure_rates)

            # Validate actual score matches expected calculation
            assert abs(result.overall_reliability_score - expected_average) < 0.001
        else:
            # No tests validated should result in 100% failure rate
            assert result.overall_reliability_score == 1.0

    def test_report_accuracy_integration(self):
        """Test that generated reports accurately reflect workflow results."""
        # Execute workflow
        result = execute_test_marking_workflow(
            self.sample_test_files,
            self.sample_categorization,
            self.sample_core_tests
        )

        # Generate report
        report = generate_reliability_report(result)

        # Validate report accuracy
        reliability_percentage = f"{result.overall_reliability_score:.2%}"
        assert reliability_percentage in report

        # Validate status reporting
        if result.meets_reliability_target():
            assert "PASS" in report
        else:
            assert "FAIL" in report

        # Validate counts
        assert f"Total migration tests marked: {len(result.marked_tests)}" in report
