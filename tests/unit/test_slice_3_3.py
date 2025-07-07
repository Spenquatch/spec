"""Tests for Slice 3.3: Migration Strategy Development and Planning."""

from pathlib import Path
from typing import Any

import pytest

from slice_3_2_pattern_analysis import (
    ClassifiedSingletonPattern,
    PatternAnalysisResult,
)
from slice_3_3_strategy_development import (
    StrategyDevelopmentError,
    develop_migration_strategies,
    generate_migration_plan_document,
)
from spec_cli.utils.migration_planning.strategy_generator import (
    generate_elimination_strategy,
)
from spec_cli.utils.pattern_analysis import SingletonUsage
from spec_cli.utils.pattern_classification.complexity_analyzer import (
    ComplexityAssessment,
)
from spec_cli.utils.singleton_detection import SingletonViolation

class TestStrategyGenerator:
    """Test cases for strategy generation functionality."""

    @pytest.fixture
    def sample_complexity_assessment(self) -> ComplexityAssessment:
        """Create sample complexity assessment."""
        return ComplexityAssessment(
            complexity_score=6,
            dependency_count=3,
            migration_priority="medium",
            estimated_effort_hours=8,
            risk_factors=["database_dependency", "thread_safety"],
        )

    @pytest.fixture
    def sample_singleton_violation(self) -> SingletonViolation:
        """Create sample singleton violation."""
        return SingletonViolation(
            file_path=Path("src/models/user.py"),
            line_number=25,
            column=0,
            pattern_type="decorator_singleton",
            description="Singleton decorator on UserManager class",
            code_snippet="@singleton\nclass UserManager:",
        )

    @pytest.fixture
    def sample_classified_pattern(
        self, sample_singleton_violation, sample_complexity_assessment
    ) -> ClassifiedSingletonPattern:
        """Create sample classified singleton pattern."""
        return ClassifiedSingletonPattern(
            original_violation=sample_singleton_violation,
            pattern_category="moderate",
            complexity_assessment=sample_complexity_assessment,
            dependent_files=[Path("src/controllers/auth.py"), Path("src/services/user_service.py")],
            usage_patterns=[
                SingletonUsage(
                    file_path=Path("src/controllers/auth.py"),
                    line_number=15,
                    usage_type="instantiation",
                    singleton_name="UserManager",
                    context="user_manager = UserManager()",
                )
            ],
            migration_notes=["Remove singleton decorator", "Update calling code"],
        )

    def test_generate_elimination_strategy_when_decorator_pattern_then_returns_decorator_removal(
        self, sample_classified_pattern
    ):
        """Test strategy generation for decorator singleton pattern."""
        strategy = generate_elimination_strategy(sample_classified_pattern)

        assert strategy["strategy_type"] == "decorator_removal"
        assert strategy["description"] == "Remove singleton decorator and implement factory pattern"
        assert strategy["effort_estimate_hours"] == 8  # Uses complexity assessment effort
        assert strategy["risk_level"] == "medium"
        assert strategy["dependency_count"] == 2
        assert strategy["complexity_score"] == 6
        assert len(strategy["implementation_steps"]) >= 5

    def test_generate_elimination_strategy_when_high_complexity_then_increases_risk(
        self, sample_classified_pattern
    ):
        """Test strategy generation with high complexity increases risk level."""
        # Modify pattern to have high complexity
        sample_classified_pattern.complexity_assessment.complexity_score = 9
        sample_classified_pattern.dependent_files = [Path(f"file_{i}.py") for i in range(6)]

        strategy = generate_elimination_strategy(sample_classified_pattern)

        assert strategy["risk_level"] == "high"
        assert strategy["dependency_count"] == 6

    def test_generate_elimination_strategy_when_metaclass_pattern_then_returns_dependency_injection(
        self, sample_classified_pattern
    ):
        """Test strategy generation for metaclass singleton pattern."""
        sample_classified_pattern.original_violation.pattern_type = "metaclass_singleton"

        strategy = generate_elimination_strategy(sample_classified_pattern)

        assert strategy["strategy_type"] == "dependency_injection_replacement"
        assert "dependency injection container" in strategy["description"]
        assert "dependency_injection_framework" in strategy["prerequisites"]

    def test_generate_elimination_strategy_when_unknown_pattern_then_returns_generic_strategy(
        self, sample_classified_pattern
    ):
        """Test strategy generation for unknown pattern type."""
        sample_classified_pattern.original_violation.pattern_type = "unknown_pattern"

        strategy = generate_elimination_strategy(sample_classified_pattern)

        assert strategy["strategy_type"] == "general_refactoring"
        assert "Analyze and refactor singleton pattern" in strategy["description"]

    def test_generate_elimination_strategy_when_migration_notes_exist_then_includes_notes(
        self, sample_classified_pattern
    ):
        """Test that migration notes are included in implementation steps."""
        strategy = generate_elimination_strategy(sample_classified_pattern)

        # Check that migration notes are added to implementation steps
        implementation_text = " ".join(strategy["implementation_steps"])
        assert "Note: Remove singleton decorator" in implementation_text
        assert "Note: Update calling code" in implementation_text

class TestStrategyDevelopment:
    """Test cases for migration strategy development."""

    @pytest.fixture
    def sample_pattern_analysis_result(self) -> PatternAnalysisResult:
        """Create sample pattern analysis result from Slice 3.2."""
        # Create multiple classified patterns
        pattern1 = ClassifiedSingletonPattern(
            original_violation=SingletonViolation(
                file_path=Path("src/models/user.py"),
                line_number=25,
                column=0,
                pattern_type="decorator_singleton",
                description="Singleton decorator",
                code_snippet="@singleton\nclass UserManager:",
            ),
            pattern_category="moderate",
            complexity_assessment=ComplexityAssessment(
                complexity_score=5,
                dependency_count=2,
                migration_priority="medium",
                estimated_effort_hours=6,
                risk_factors=["decorator_pattern"],
            ),
            dependent_files=[Path("src/controllers/auth.py")],
            usage_patterns=[],
            migration_notes=["Remove decorator"],
        )

        pattern2 = ClassifiedSingletonPattern(
            original_violation=SingletonViolation(
                file_path=Path("src/config/settings.py"),
                line_number=10,
                column=0,
                pattern_type="metaclass_singleton",
                description="Metaclass singleton",
                code_snippet="class Settings(metaclass=SingletonMeta):",
            ),
            pattern_category="complex",
            complexity_assessment=ComplexityAssessment(
                complexity_score=8,
                dependency_count=5,
                migration_priority="high",
                estimated_effort_hours=12,
                risk_factors=["metaclass_pattern", "thread_safety", "high_usage"],
            ),
            dependent_files=[Path("src/app.py"), Path("src/database.py"), Path("src/logging.py")],
            usage_patterns=[],
            migration_notes=["Critical migration", "High dependency count"],
        )

        return PatternAnalysisResult(
            classified_patterns=[pattern1, pattern2],
            dependency_graph={
                "src/models/user.py": ["src/controllers/auth.py"],
                "src/config/settings.py": ["src/app.py", "src/database.py", "src/logging.py"],
            },
            complexity_distribution={"moderate": 1, "complex": 1},
            migration_priority_order=["src/config/settings.py", "src/models/user.py"],
        )

    def test_develop_migration_strategies_when_valid_input_then_returns_complete_result(
        self, sample_pattern_analysis_result
    ):
        """Test successful migration strategy development."""
        result = develop_migration_strategies(sample_pattern_analysis_result)

        # Verify structure
        assert "migration_strategies" in result
        assert "implementation_order" in result
        assert "effort_estimates" in result
        assert "implementation_phases" in result
        assert "dependency_graph" in result

        # Verify strategy count matches input patterns
        assert len(result["migration_strategies"]) == 2
        assert result["total_patterns"] == 2

        # Verify implementation order is preserved from Slice 3.2
        assert result["implementation_order"] == [
            "src/config/settings.py",
            "src/models/user.py",
        ]

        # Verify effort estimates
        effort = result["effort_estimates"]
        assert effort["total_effort_hours"] == 18  # 6 + 12 from patterns
        assert len(effort["effort_by_pattern"]) == 2
        assert "effort_by_risk_level" in effort
        assert "effort_by_strategy_type" in effort

    def test_develop_migration_strategies_when_empty_patterns_then_returns_empty_result(self):
        """Test strategy development with empty pattern list."""
        empty_result = PatternAnalysisResult(
            classified_patterns=[],
            dependency_graph={},
            complexity_distribution={},
            migration_priority_order=[],
        )

        result = develop_migration_strategies(empty_result)

        assert len(result["migration_strategies"]) == 0
        assert result["total_patterns"] == 0
        assert result["effort_estimates"]["total_effort_hours"] == 0
        assert len(result["implementation_phases"]) == 0

    def test_develop_migration_strategies_when_project_constraints_provided_then_includes_constraints(
        self, sample_pattern_analysis_result
    ):
        """Test strategy development with project constraints."""
        constraints = {"max_phase_effort": 20, "parallel_execution": True}

        result = develop_migration_strategies(sample_pattern_analysis_result, constraints)

        # Should still generate strategies successfully
        assert len(result["migration_strategies"]) == 2
        # Note: Current implementation doesn't use constraints, but validates they don't break functionality

    def test_develop_migration_strategies_when_complex_patterns_then_creates_phases(
        self, sample_pattern_analysis_result
    ):
        """Test that implementation phases are created based on complexity."""
        result = develop_migration_strategies(sample_pattern_analysis_result)

        phases = result["implementation_phases"]
        assert len(phases) >= 1  # Should create at least one phase

        # First phase should contain high-effort/high-risk patterns
        first_phase = phases[0]
        assert first_phase["phase_number"] == 1
        assert "Critical" in first_phase["phase_name"]
        assert first_phase["estimated_effort_hours"] > 0

    def test_develop_migration_strategies_when_invalid_input_then_raises_error(self):
        """Test error handling for invalid input."""
        with pytest.raises((StrategyDevelopmentError, AttributeError)):
            # This will fail because we're passing None instead of PatternAnalysisResult
            develop_migration_strategies(None)  # type: ignore

class TestMigrationPlanDocument:
    """Test cases for migration plan document generation."""

    @pytest.fixture
    def sample_strategy_result(self) -> dict[str, Any]:
        """Create sample strategy result for testing."""
        return {
            "migration_strategies": {
                "src/models/user.py": {
                    "strategy_type": "decorator_removal",
                    "effort_estimate_hours": 6,
                    "risk_level": "medium",
                },
                "src/config/settings.py": {
                    "strategy_type": "dependency_injection_replacement",
                    "effort_estimate_hours": 12,
                    "risk_level": "high",
                },
            },
            "implementation_order": ["src/config/settings.py", "src/models/user.py"],
            "effort_estimates": {
                "total_effort_hours": 18,
                "effort_by_strategy_type": {
                    "decorator_removal": 6,
                    "dependency_injection_replacement": 12,
                },
            },
            "implementation_phases": [
                {
                    "phase_number": 1,
                    "phase_name": "Critical Pattern Migration",
                    "description": "High-risk patterns",
                    "estimated_effort_hours": 12,
                    "patterns": ["src/config/settings.py"],
                    "execution_strategy": "sequential",
                },
                {
                    "phase_number": 2,
                    "phase_name": "Medium Priority Migration",
                    "description": "Medium-risk patterns",
                    "estimated_effort_hours": 6,
                    "patterns": ["src/models/user.py"],
                    "execution_strategy": "parallel",
                },
            ],
            "total_patterns": 2,
            "complexity_distribution": {"moderate": 1, "complex": 1},
        }

    def test_generate_migration_plan_document_when_markdown_format_then_returns_markdown(
        self, sample_strategy_result
    ):
        """Test markdown format migration plan generation."""
        document = generate_migration_plan_document(sample_strategy_result, "markdown")

        assert "# Singleton Pattern Migration Plan" in document
        assert "## Overview" in document
        assert "**Total Patterns**: 2" in document
        assert "**Total Effort**: 18 hours" in document
        assert "## Implementation Phases" in document
        assert "### Phase 1: Critical Pattern Migration" in document

    def test_generate_migration_plan_document_when_text_format_then_returns_text(
        self, sample_strategy_result
    ):
        """Test plain text format migration plan generation."""
        document = generate_migration_plan_document(sample_strategy_result, "text")

        assert "SINGLETON PATTERN MIGRATION PLAN" in document
        assert "Total Patterns: 2" in document
        assert "Total Effort: 18 hours" in document
        assert "Phase 1: Critical Pattern Migration" in document

    def test_generate_migration_plan_document_when_json_format_then_returns_json(
        self, sample_strategy_result
    ):
        """Test JSON format migration plan generation."""
        document = generate_migration_plan_document(sample_strategy_result, "json")

        import json
        parsed = json.loads(document)
        assert parsed["total_patterns"] == 2
        assert parsed["effort_estimates"]["total_effort_hours"] == 18
        assert len(parsed["implementation_phases"]) == 2

    def test_generate_migration_plan_document_when_unsupported_format_then_raises_error(
        self, sample_strategy_result
    ):
        """Test error handling for unsupported format."""
        with pytest.raises(StrategyDevelopmentError):
            generate_migration_plan_document(sample_strategy_result, "xml")

class TestIntegrationWithSlice32:
    """Integration tests with Slice 3.2 output."""

    def test_end_to_end_strategy_development_with_slice_32_result(self):
        """Test complete workflow using actual Slice 3.2 structures."""
        # Create realistic pattern analysis result as would come from Slice 3.2
        violation = SingletonViolation(
            file_path=Path("src/database/connection.py"),
            line_number=45,
            column=0,
            pattern_type="import_singleton",
            description="Singleton import pattern",
            code_snippet="from .singleton import DatabaseConnection\ndb = DatabaseConnection()",
        )

        classified_pattern = ClassifiedSingletonPattern(
            original_violation=violation,
            pattern_category="complex",
            complexity_assessment=ComplexityAssessment(
                complexity_score=7,
                dependency_count=4,
                migration_priority="high",
                estimated_effort_hours=10,
                risk_factors=["import_pattern", "high_usage"],
            ),
            dependent_files=[
                Path("src/models/user.py"),
                Path("src/models/order.py"),
                Path("src/services/data_service.py"),
                Path("src/controllers/api.py"),
            ],
            usage_patterns=[
                SingletonUsage(
                    file_path=Path("src/models/user.py"),
                    line_number=20,
                    usage_type="import",
                    singleton_name="DatabaseConnection",
                    context="Using db connection",
                )
            ],
            migration_notes=[
                "HIGH PRIORITY: Schedule for early migration phase",
                "Update import statements across dependent modules",
            ],
        )

        pattern_analysis_result = PatternAnalysisResult(
            classified_patterns=[classified_pattern],
            dependency_graph={
                "src/database/connection.py": [
                    "src/models/user.py",
                    "src/models/order.py",
                    "src/services/data_service.py",
                    "src/controllers/api.py",
                ],
            },
            complexity_distribution={"complex": 1},
            migration_priority_order=["src/database/connection.py"],
        )

        # Test complete strategy development workflow
        result = develop_migration_strategies(pattern_analysis_result)

        # Verify integration worked correctly
        assert len(result["migration_strategies"]) == 1
        assert "src/database/connection.py" in result["migration_strategies"]

        strategy = result["migration_strategies"]["src/database/connection.py"]
        assert strategy["strategy_type"] == "import_refactoring"
        assert strategy["effort_estimate_hours"] == 10
        assert strategy["dependency_count"] == 4
        assert strategy["complexity_score"] == 7

        # Verify implementation phases include the pattern
        phases = result["implementation_phases"]
        assert len(phases) >= 1

        # Should be in critical phase due to high effort
        critical_phase = phases[0]
        assert "src/database/connection.py" in critical_phase["patterns"]

        # Test document generation
        document = generate_migration_plan_document(result, "markdown")
        assert "src/database/connection.py" in document or "Import Refactoring" in document
