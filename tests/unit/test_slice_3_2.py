"""Unit tests for Slice 3.2: Pattern Analysis and Classification."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slice_3_2_pattern_analysis import (
    ClassifiedSingletonPattern,
    PatternAnalysisError,
    PatternAnalysisResult,
    _calculate_complexity_distribution,
    _classify_single_pattern,
    _determine_migration_order,
    _determine_pattern_category,
    _extract_all_files,
    _extract_singleton_name,
    _find_dependent_files,
    _generate_migration_notes,
    _priority_score,
    analyze_singleton_patterns,
)
from spec_cli.utils.pattern_classification.complexity_analyzer import (
    ComplexityAssessment,
)
from spec_cli.utils.singleton_detection import SingletonViolation

# Test constants
TEST_FILE_PATH = Path("/test/file.py")
TEST_FILE_PATH_2 = Path("/test/file2.py")
SIMPLE_COMPLEXITY_SCORE = 3
MODERATE_COMPLEXITY_SCORE = 5
COMPLEX_COMPLEXITY_SCORE = 7
CRITICAL_COMPLEXITY_SCORE = 9
DEFAULT_DEPENDENCY_COUNT = 2
HIGH_DEPENDENCY_COUNT = 8
SIMPLE_EFFORT_HOURS = 6
MODERATE_EFFORT_HOURS = 10
COMPLEX_EFFORT_HOURS = 14
CRITICAL_EFFORT_HOURS = 18

class TestAnalyzeSingletonPatterns:
    """Test the main analyze_singleton_patterns function."""

    def test_analyze_singleton_patterns_when_valid_patterns_then_returns_analysis_result(
        self,
    ):
        """Test successful analysis of valid singleton patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test metaclass singleton",
            code_snippet="class TestClass(metaclass=SingletonMeta):",
        )
        patterns = [pattern]
        structure = {"files": [str(TEST_FILE_PATH), str(TEST_FILE_PATH_2)]}

        with (
            patch(
                "slice_3_2_pattern_analysis._classify_single_pattern"
            ) as mock_classify,
            patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_deps,
        ):
            mock_classify.return_value = ClassifiedSingletonPattern(
                original_violation=pattern,
                pattern_category="critical",
                complexity_assessment=ComplexityAssessment(
                    complexity_score=CRITICAL_COMPLEXITY_SCORE,
                    migration_priority="critical",
                    risk_factors=["test risk"],
                    estimated_effort_hours=CRITICAL_EFFORT_HOURS,
                    dependency_count=DEFAULT_DEPENDENCY_COUNT,
                ),
                dependent_files=[TEST_FILE_PATH_2],
                usage_patterns=[],
                migration_notes=["test note"],
            )
            mock_deps.return_value = []

            # Act
            result = analyze_singleton_patterns(patterns, structure)

            # Assert
            assert isinstance(result, PatternAnalysisResult)
            assert len(result.classified_patterns) == 1
            assert result.classified_patterns[0].pattern_category == "critical"
            assert str(TEST_FILE_PATH) in result.dependency_graph
            assert result.complexity_distribution["critical"] == 1
            assert len(result.migration_priority_order) == 1

    def test_analyze_singleton_patterns_when_empty_patterns_then_returns_empty_result(
        self,
    ):
        """Test analysis with empty pattern list."""
        # Arrange
        patterns = []
        structure = {"files": []}

        # Act
        result = analyze_singleton_patterns(patterns, structure)

        # Assert
        assert isinstance(result, PatternAnalysisResult)
        assert len(result.classified_patterns) == 0
        assert len(result.dependency_graph) == 0
        assert all(count == 0 for count in result.complexity_distribution.values())
        assert len(result.migration_priority_order) == 0

    def test_analyze_singleton_patterns_when_analysis_fails_then_raises_error(self):
        """Test error handling when pattern analysis fails."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="invalid_type",
            description="Invalid pattern",
            code_snippet="invalid code",
        )
        patterns = [pattern]
        structure = {"files": [str(TEST_FILE_PATH)]}

        with patch(
            "slice_3_2_pattern_analysis._classify_single_pattern"
        ) as mock_classify:
            mock_classify.side_effect = Exception("Classification failed")

            # Act & Assert
            with pytest.raises(PatternAnalysisError, match="Failed to analyze"):
                analyze_singleton_patterns(patterns, structure)

class TestClassifySinglePattern:
    """Test pattern classification functionality."""

    def test_classify_single_pattern_when_metaclass_pattern_then_returns_critical_classification(
        self,
    ):
        """Test classification of metaclass singleton patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Metaclass: SingletonMeta",
            code_snippet="class TestClass(metaclass=SingletonMeta):",
        )
        all_files = [TEST_FILE_PATH, TEST_FILE_PATH_2]

        with (
            patch("slice_3_2_pattern_analysis._find_dependent_files") as mock_find_deps,
            patch(
                "slice_3_2_pattern_analysis.analyze_pattern_complexity"
            ) as mock_analyze,
            patch("slice_3_2_pattern_analysis._analyze_usage_patterns") as mock_usage,
        ):
            mock_find_deps.return_value = [TEST_FILE_PATH_2]
            mock_analyze.return_value = ComplexityAssessment(
                complexity_score=CRITICAL_COMPLEXITY_SCORE,
                migration_priority="critical",
                risk_factors=["Metaclass complexity"],
                estimated_effort_hours=CRITICAL_EFFORT_HOURS,
                dependency_count=1,
            )
            mock_usage.return_value = []

            # Act
            result = _classify_single_pattern(pattern, all_files)

            # Assert
            assert isinstance(result, ClassifiedSingletonPattern)
            assert result.pattern_category == "critical"
            assert result.original_violation == pattern
            assert len(result.dependent_files) == 1
            assert result.dependent_files[0] == TEST_FILE_PATH_2
            assert (
                result.complexity_assessment.complexity_score
                == CRITICAL_COMPLEXITY_SCORE
            )

    def test_classify_single_pattern_when_decorator_pattern_then_returns_complex_classification(
        self,
    ):
        """Test classification of decorator singleton patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="decorator_singleton",
            description="Decorator: singleton",
            code_snippet="@singleton",
        )
        all_files = [TEST_FILE_PATH]

        with (
            patch("slice_3_2_pattern_analysis._find_dependent_files") as mock_find_deps,
            patch(
                "slice_3_2_pattern_analysis.analyze_pattern_complexity"
            ) as mock_analyze,
            patch("slice_3_2_pattern_analysis._analyze_usage_patterns") as mock_usage,
        ):
            mock_find_deps.return_value = []
            mock_analyze.return_value = ComplexityAssessment(
                complexity_score=COMPLEX_COMPLEXITY_SCORE,
                migration_priority="high",
                risk_factors=["Decorator removal"],
                estimated_effort_hours=COMPLEX_EFFORT_HOURS,
                dependency_count=0,
            )
            mock_usage.return_value = []

            # Act
            result = _classify_single_pattern(pattern, all_files)

            # Assert
            assert result.pattern_category == "complex"
            assert result.complexity_assessment.migration_priority == "high"

class TestFindDependentFiles:
    """Test dependent file discovery functionality."""

    def test_find_dependent_files_when_dependencies_exist_then_returns_dependent_files(
        self,
    ):
        """Test finding files that depend on a singleton pattern."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="test code",
        )
        all_files = [TEST_FILE_PATH, TEST_FILE_PATH_2]

        with patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_analyze:
            # analyze_current_usage takes (dependency_name, codebase_path)
            # and returns list of file paths that use the dependency
            mock_analyze.side_effect = lambda dep_name, codebase_path: (
                [str(TEST_FILE_PATH)] if dep_name == TEST_FILE_PATH.stem else []
            )

            # Act
            result = _find_dependent_files(pattern, all_files)

            # Assert
            assert len(result) == 1
            assert result[0] == TEST_FILE_PATH_2

    def test_find_dependent_files_when_no_dependencies_then_returns_empty_list(self):
        """Test finding dependent files when none exist."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="import_singleton",
            description="Test pattern",
            code_snippet="import singleton",
        )
        all_files = [TEST_FILE_PATH, TEST_FILE_PATH_2]

        with patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_analyze:
            mock_analyze.return_value = []

            # Act
            result = _find_dependent_files(pattern, all_files)

            # Assert
            assert len(result) == 0

    def test_find_dependent_files_when_analysis_fails_then_handles_gracefully(self):
        """Test graceful handling of dependency analysis failures."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="test code",
        )
        all_files = [TEST_FILE_PATH, TEST_FILE_PATH_2]

        with patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")

            # Act
            result = _find_dependent_files(pattern, all_files)

            # Assert
            assert len(result) == 0  # Should handle error gracefully

class TestPatternCategoryDetermination:
    """Test pattern category determination logic."""

    def test_determine_pattern_category_when_critical_score_then_returns_critical(self):
        """Test critical category determination."""
        # Arrange
        assessment = ComplexityAssessment(
            complexity_score=CRITICAL_COMPLEXITY_SCORE,
            migration_priority="critical",
            risk_factors=[],
            estimated_effort_hours=CRITICAL_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _determine_pattern_category(assessment)

        # Assert
        assert result == "critical"

    def test_determine_pattern_category_when_complex_score_then_returns_complex(self):
        """Test complex category determination."""
        # Arrange
        assessment = ComplexityAssessment(
            complexity_score=COMPLEX_COMPLEXITY_SCORE,
            migration_priority="high",
            risk_factors=[],
            estimated_effort_hours=COMPLEX_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _determine_pattern_category(assessment)

        # Assert
        assert result == "complex"

    def test_determine_pattern_category_when_moderate_score_then_returns_moderate(self):
        """Test moderate category determination."""
        # Arrange
        assessment = ComplexityAssessment(
            complexity_score=MODERATE_COMPLEXITY_SCORE,
            migration_priority="medium",
            risk_factors=[],
            estimated_effort_hours=MODERATE_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _determine_pattern_category(assessment)

        # Assert
        assert result == "moderate"

    def test_determine_pattern_category_when_simple_score_then_returns_simple(self):
        """Test simple category determination."""
        # Arrange
        assessment = ComplexityAssessment(
            complexity_score=SIMPLE_COMPLEXITY_SCORE,
            migration_priority="low",
            risk_factors=[],
            estimated_effort_hours=SIMPLE_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _determine_pattern_category(assessment)

        # Assert
        assert result == "simple"

class TestExtractSingletonName:
    """Test singleton name extraction functionality."""

    def test_extract_singleton_name_when_description_has_colon_then_extracts_name(self):
        """Test singleton name extraction from description."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Metaclass: SingletonMeta",
            code_snippet="test code",
        )

        # Act
        result = _extract_singleton_name(pattern)

        # Assert
        assert result == "SingletonMeta"

    def test_extract_singleton_name_when_class_in_code_then_extracts_class_name(self):
        """Test singleton name extraction from code snippet."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="class TestSingleton(metaclass=SingletonMeta):",
        )

        # Act
        result = _extract_singleton_name(pattern)

        # Assert
        assert result == "TestSingleton"

    def test_extract_singleton_name_when_no_recognizable_pattern_then_returns_default(
        self,
    ):
        """Test default singleton name when no pattern is recognized."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="import_singleton",
            description="Test pattern",
            code_snippet="import something",
        )

        # Act
        result = _extract_singleton_name(pattern)

        # Assert
        assert result == "unknown_singleton"

class TestGenerateMigrationNotes:
    """Test migration notes generation."""

    def test_generate_migration_notes_when_metaclass_pattern_then_includes_metaclass_notes(
        self,
    ):
        """Test migration notes for metaclass patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test metaclass",
            code_snippet="class Test(metaclass=SingletonMeta):",
        )
        assessment = ComplexityAssessment(
            complexity_score=CRITICAL_COMPLEXITY_SCORE,
            migration_priority="critical",
            risk_factors=[],
            estimated_effort_hours=CRITICAL_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        assert len(result) >= 3
        assert any("metaclass" in note.lower() for note in result)
        assert any("dependency injection" in note.lower() for note in result)
        assert any("CRITICAL" in note for note in result)

    def test_generate_migration_notes_when_decorator_pattern_then_includes_decorator_notes(
        self,
    ):
        """Test migration notes for decorator patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="decorator_singleton",
            description="Test decorator",
            code_snippet="@singleton",
        )
        assessment = ComplexityAssessment(
            complexity_score=MODERATE_COMPLEXITY_SCORE,
            migration_priority="medium",
            risk_factors=[],
            estimated_effort_hours=MODERATE_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        assert len(result) >= 2
        assert any("decorator" in note.lower() for note in result)
        assert any("api" in note.lower() for note in result)

    def test_generate_migration_notes_when_high_effort_then_includes_effort_note(self):
        """Test migration notes include effort estimation."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="test code",
        )
        HIGH_EFFORT_HOURS = 25
        assessment = ComplexityAssessment(
            complexity_score=CRITICAL_COMPLEXITY_SCORE,
            migration_priority="critical",
            risk_factors=[],
            estimated_effort_hours=HIGH_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        assert any(
            "effort" in note.lower() and str(HIGH_EFFORT_HOURS) in note
            for note in result
        )

class TestComplexityDistribution:
    """Test complexity distribution calculation."""

    def test_calculate_complexity_distribution_when_mixed_patterns_then_returns_correct_counts(
        self,
    ):
        """Test complexity distribution calculation with mixed patterns."""
        # Arrange
        patterns = [
            ClassifiedSingletonPattern(
                original_violation=Mock(),
                pattern_category="simple",
                complexity_assessment=Mock(),
                dependent_files=[],
                usage_patterns=[],
                migration_notes=[],
            ),
            ClassifiedSingletonPattern(
                original_violation=Mock(),
                pattern_category="complex",
                complexity_assessment=Mock(),
                dependent_files=[],
                usage_patterns=[],
                migration_notes=[],
            ),
            ClassifiedSingletonPattern(
                original_violation=Mock(),
                pattern_category="simple",
                complexity_assessment=Mock(),
                dependent_files=[],
                usage_patterns=[],
                migration_notes=[],
            ),
        ]

        # Act
        result = _calculate_complexity_distribution(patterns)

        # Assert
        assert result["simple"] == 2
        assert result["complex"] == 1
        assert result["moderate"] == 0
        assert result["critical"] == 0

    def test_calculate_complexity_distribution_when_empty_patterns_then_returns_zero_counts(
        self,
    ):
        """Test complexity distribution with empty pattern list."""
        # Arrange
        patterns = []

        # Act
        result = _calculate_complexity_distribution(patterns)

        # Assert
        assert all(count == 0 for count in result.values())

class TestMigrationOrder:
    """Test migration order determination."""

    def test_determine_migration_order_when_mixed_priorities_then_orders_by_priority(
        self,
    ):
        """Test migration order prioritizes critical patterns first."""
        # Arrange
        critical_pattern = ClassifiedSingletonPattern(
            original_violation=SingletonViolation(
                file_path=Path("/critical.py"),
                line_number=1,
                column=0,
                pattern_type="metaclass_singleton",
                description="Critical",
                code_snippet="code",
            ),
            pattern_category="critical",
            complexity_assessment=ComplexityAssessment(
                complexity_score=CRITICAL_COMPLEXITY_SCORE,
                migration_priority="critical",
                risk_factors=[],
                estimated_effort_hours=CRITICAL_EFFORT_HOURS,
                dependency_count=0,
            ),
            dependent_files=[],
            usage_patterns=[],
            migration_notes=[],
        )

        low_pattern = ClassifiedSingletonPattern(
            original_violation=SingletonViolation(
                file_path=Path("/low.py"),
                line_number=1,
                column=0,
                pattern_type="import_singleton",
                description="Low",
                code_snippet="import code",
            ),
            pattern_category="simple",
            complexity_assessment=ComplexityAssessment(
                complexity_score=SIMPLE_COMPLEXITY_SCORE,
                migration_priority="low",
                risk_factors=[],
                estimated_effort_hours=SIMPLE_EFFORT_HOURS,
                dependency_count=0,
            ),
            dependent_files=[],
            usage_patterns=[],
            migration_notes=[],
        )

        patterns = [low_pattern, critical_pattern]  # Deliberately out of order

        # Act
        result = _determine_migration_order(patterns)

        # Assert
        assert len(result) == 2
        assert result[0] == "/critical.py"  # Critical should be first
        assert result[1] == "/low.py"  # Low should be last

class TestPriorityScore:
    """Test priority scoring functionality."""

    def test_priority_score_when_critical_then_returns_zero(self):
        """Test critical priority gets highest score (lowest number)."""
        result = _priority_score("critical")
        assert result == 0

    def test_priority_score_when_high_then_returns_one(self):
        """Test high priority scoring."""
        result = _priority_score("high")
        assert result == 1

    def test_priority_score_when_medium_then_returns_two(self):
        """Test medium priority scoring."""
        result = _priority_score("medium")
        assert result == 2

    def test_priority_score_when_low_then_returns_three(self):
        """Test low priority scoring."""
        result = _priority_score("low")
        assert result == 3

    def test_priority_score_when_unknown_then_returns_default(self):
        """Test unknown priority gets default score."""
        result = _priority_score("unknown")
        assert result == 3

class TestExtractAllFiles:
    """Test file extraction from codebase structure."""

    def test_extract_all_files_when_files_key_exists_then_returns_file_paths(self):
        """Test file extraction from files key."""
        # Arrange
        structure = {"files": ["/test/file1.py", "/test/file2.py"]}

        # Act
        result = _extract_all_files(structure)

        # Assert
        assert len(result) == 2
        assert all(isinstance(f, Path) for f in result)
        assert str(result[0]) == "/test/file1.py"

    def test_extract_all_files_when_python_files_key_exists_then_returns_file_paths(
        self,
    ):
        """Test file extraction from python_files key."""
        # Arrange
        structure = {"python_files": ["/test/module.py"]}

        # Act
        result = _extract_all_files(structure)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], Path)
        assert str(result[0]) == "/test/module.py"

    def test_extract_all_files_when_both_keys_exist_then_returns_combined_paths(self):
        """Test file extraction with both files and python_files keys."""
        # Arrange
        structure = {
            "files": ["/test/file1.py"],
            "python_files": ["/test/file2.py"],
        }

        # Act
        result = _extract_all_files(structure)

        # Assert
        assert len(result) == 2

    def test_extract_all_files_when_empty_structure_then_returns_empty_list(self):
        """Test file extraction with empty structure."""
        # Arrange
        structure = {}

        # Act
        result = _extract_all_files(structure)

        # Assert
        assert len(result) == 0

class TestAnalyzeUsagePatterns:
    """Test usage pattern analysis functionality."""

    def test_analyze_usage_patterns_when_valid_pattern_then_returns_usage(self):
        """Test usage pattern generation for valid patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=5,
            column=0,
            pattern_type="metaclass_singleton",
            description="Metaclass: TestSingleton",
            code_snippet="class TestSingleton(metaclass=SingletonMeta):",
        )

        # Act
        from slice_3_2_pattern_analysis import _analyze_usage_patterns

        result = _analyze_usage_patterns(pattern)

        # Assert
        assert len(result) == 1
        assert result[0].file_path == pattern.file_path
        assert result[0].line_number == pattern.line_number
        assert result[0].usage_type == pattern.pattern_type
        assert result[0].singleton_name == "TestSingleton"

class TestComplexCodePaths:
    """Test complex code paths and edge cases."""

    def test_extract_singleton_name_when_complex_class_definition_then_handles_gracefully(
        self,
    ):
        """Test singleton name extraction with complex class definition."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Complex pattern",
            code_snippet="class ComplexSingleton(BaseClass, SecondBase):",
        )

        # Act
        result = _extract_singleton_name(pattern)

        # Assert
        assert result == "ComplexSingleton"

    def test_generate_migration_notes_when_import_pattern_then_includes_import_notes(
        self,
    ):
        """Test migration notes for import patterns."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="import_from_singleton",
            description="Import pattern",
            code_snippet="from singleton import SingletonMeta",
        )
        assessment = ComplexityAssessment(
            complexity_score=MODERATE_COMPLEXITY_SCORE,
            migration_priority="medium",
            risk_factors=[],
            estimated_effort_hours=MODERATE_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        assert len(result) >= 2
        assert any("import" in note.lower() for note in result)
        assert any("container configuration" in note.lower() for note in result)

    def test_generate_migration_notes_when_high_priority_then_includes_priority_note(
        self,
    ):
        """Test migration notes include high priority guidance."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="decorator_singleton",
            description="High priority pattern",
            code_snippet="@singleton",
        )
        assessment = ComplexityAssessment(
            complexity_score=COMPLEX_COMPLEXITY_SCORE,
            migration_priority="high",
            risk_factors=[],
            estimated_effort_hours=COMPLEX_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        assert any("HIGH PRIORITY" in note for note in result)

class TestEdgeCaseBranches:
    """Test edge cases to reach 100% branch coverage."""

    def test_calculate_complexity_distribution_when_unknown_category_then_ignored(self):
        """Test complexity distribution with unknown pattern category."""
        # Arrange
        pattern_with_unknown_category = ClassifiedSingletonPattern(
            original_violation=Mock(),
            pattern_category="unknown",  # Not in the distribution keys
            complexity_assessment=Mock(),
            dependent_files=[],
            usage_patterns=[],
            migration_notes=[],
        )
        patterns = [pattern_with_unknown_category]

        # Act
        result = _calculate_complexity_distribution(patterns)

        # Assert
        # Unknown category should not increase any counts
        assert all(count == 0 for count in result.values())

    def test_extract_singleton_name_when_class_with_colon_then_handles_correctly(self):
        """Test singleton name extraction with class definition containing colon."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="class TestSingleton:",  # Just class name with colon
        )

        # Act
        result = _extract_singleton_name(pattern)

        # Assert
        assert result == "TestSingleton"

    def test_generate_migration_notes_when_low_effort_then_no_effort_note(self):
        """Test migration notes don't include effort note for low effort."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="import_singleton",
            description="Low effort pattern",
            code_snippet="import singleton",
        )
        LOW_EFFORT_HOURS = 10  # Below the 20 hour threshold
        assessment = ComplexityAssessment(
            complexity_score=SIMPLE_COMPLEXITY_SCORE,
            migration_priority="low",
            risk_factors=[],
            estimated_effort_hours=LOW_EFFORT_HOURS,
            dependency_count=0,
        )

        # Act
        result = _generate_migration_notes(pattern, assessment)

        # Assert
        # Should not include effort note since it's under 20 hours
        assert not any("effort" in note.lower() for note in result)

    def test_analyze_singleton_patterns_when_multiple_dependencies_then_builds_graph(
        self,
    ):
        """Test dependency graph building with multiple patterns and dependencies."""
        # Arrange
        pattern1 = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Pattern 1",
            code_snippet="class Singleton1:",
        )
        pattern2 = SingletonViolation(
            file_path=TEST_FILE_PATH_2,
            line_number=1,
            column=0,
            pattern_type="decorator_singleton",
            description="Pattern 2",
            code_snippet="@singleton",
        )
        patterns = [pattern1, pattern2]
        structure = {"files": [str(TEST_FILE_PATH), str(TEST_FILE_PATH_2)]}

        with (
            patch(
                "slice_3_2_pattern_analysis._classify_single_pattern"
            ) as mock_classify,
            patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_deps,
        ):
            # Create mock classified patterns with dependencies
            mock_classify.side_effect = [
                ClassifiedSingletonPattern(
                    original_violation=pattern1,
                    pattern_category="critical",
                    complexity_assessment=ComplexityAssessment(
                        complexity_score=CRITICAL_COMPLEXITY_SCORE,
                        migration_priority="critical",
                        risk_factors=[],
                        estimated_effort_hours=CRITICAL_EFFORT_HOURS,
                        dependency_count=1,
                    ),
                    dependent_files=[TEST_FILE_PATH_2],
                    usage_patterns=[],
                    migration_notes=[],
                ),
                ClassifiedSingletonPattern(
                    original_violation=pattern2,
                    pattern_category="complex",
                    complexity_assessment=ComplexityAssessment(
                        complexity_score=COMPLEX_COMPLEXITY_SCORE,
                        migration_priority="high",
                        risk_factors=[],
                        estimated_effort_hours=COMPLEX_EFFORT_HOURS,
                        dependency_count=0,
                    ),
                    dependent_files=[],
                    usage_patterns=[],
                    migration_notes=[],
                ),
            ]
            mock_deps.return_value = []

            # Act
            result = analyze_singleton_patterns(patterns, structure)

            # Assert
            assert len(result.dependency_graph) == 2
            assert str(TEST_FILE_PATH) in result.dependency_graph
            assert str(TEST_FILE_PATH_2) in result.dependency_graph
            # First pattern should have dependency to second
            assert str(TEST_FILE_PATH_2) in result.dependency_graph[str(TEST_FILE_PATH)]

    def test_analyze_singleton_patterns_when_duplicate_dependencies_then_handles_correctly(
        self,
    ):
        """Test dependency graph handling with duplicate dependencies."""
        # Arrange
        pattern = SingletonViolation(
            file_path=TEST_FILE_PATH,
            line_number=1,
            column=0,
            pattern_type="metaclass_singleton",
            description="Test pattern",
            code_snippet="class Test:",
        )
        patterns = [pattern]
        structure = {"files": [str(TEST_FILE_PATH), str(TEST_FILE_PATH_2)]}

        with (
            patch(
                "slice_3_2_pattern_analysis._classify_single_pattern"
            ) as mock_classify,
            patch("slice_3_2_pattern_analysis.analyze_current_usage") as mock_deps,
        ):
            # Create pattern with same dependency twice (to test duplicate handling)
            mock_classify.return_value = ClassifiedSingletonPattern(
                original_violation=pattern,
                pattern_category="simple",
                complexity_assessment=ComplexityAssessment(
                    complexity_score=SIMPLE_COMPLEXITY_SCORE,
                    migration_priority="low",
                    risk_factors=[],
                    estimated_effort_hours=SIMPLE_EFFORT_HOURS,
                    dependency_count=1,
                ),
                dependent_files=[
                    TEST_FILE_PATH_2,
                    TEST_FILE_PATH_2,
                ],  # Duplicate dependency
                usage_patterns=[],
                migration_notes=[],
            )
            mock_deps.return_value = []

            # Act
            result = analyze_singleton_patterns(patterns, structure)

            # Assert
            # Should handle duplicate dependencies correctly (no duplicates in graph)
            dependencies = result.dependency_graph[str(TEST_FILE_PATH)]
            assert dependencies.count(str(TEST_FILE_PATH_2)) == 1  # Only one instance
