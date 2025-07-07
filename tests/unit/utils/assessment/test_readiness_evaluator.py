"""Unit tests for readiness evaluator helper module."""

import pytest

from spec_cli.utils.assessment.readiness_evaluator import (
    FoundationState,
    ReadinessAssessmentError,
    ReadinessReport,
    _calculate_overall_readiness,
    _calculate_stability_score,
    _evaluate_deliverable_completeness,
    _generate_recommendations,
    _identify_migration_blockers,
    _identify_risk_factors,
    assess_migration_readiness,
)

class TestAssessMigrationReadiness:
    """Test main readiness assessment functionality."""

    def test_assess_migration_readiness_when_complete_foundation_then_returns_high_readiness(self):
        """Test assessment with complete foundation state."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_1": {"implementation": True, "tests": True, "documentation": True},
                "phase_2": {"implementation": True, "tests": True, "documentation": True},
                "phase_3": {"implementation": True, "tests": True, "documentation": True},
                "dependency_analysis": {"complete": True},
                "context_infrastructure": {"ready": True},
                "compatibility_layer": {"implemented": True}
            },
            test_infrastructure_status={
                "unit_tests": 0.95,
                "integration_tests": 0.9,
                "coverage": 0.92
            },
            singleton_baseline={"patterns": ["pattern1", "pattern2"]},
            integration_health={"all_systems": True}
        )

        result = assess_migration_readiness(foundation_state)

        assert isinstance(result, ReadinessReport)
        assert result.overall_readiness_score > 0.8
        assert result.foundation_stability_verified is True
        assert "phase_1" in result.deliverable_completeness
        assert "phase_2" in result.deliverable_completeness
        assert "phase_3" in result.deliverable_completeness
        assert len(result.migration_blockers) == 0

    def test_assess_migration_readiness_when_incomplete_foundation_then_returns_moderate_readiness(self):
        """Test assessment with incomplete foundation state."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_1": {"implementation": True, "tests": False, "documentation": True},
                "phase_2": {"implementation": True, "tests": True, "documentation": False},
                "phase_3": {"implementation": False, "tests": False, "documentation": False}
            },
            test_infrastructure_status={
                "unit_tests": 0.7,
                "integration_tests": 0.6
            },
            singleton_baseline={"patterns": ["pattern1"]},
            integration_health={"some_systems": True, "others": False}
        )

        result = assess_migration_readiness(foundation_state)

        assert result.overall_readiness_score < 0.8
        assert result.foundation_stability_verified is False
        assert len(result.recommendations) > 0
        assert len(result.risk_factors) > 0

    def test_assess_migration_readiness_when_empty_deliverables_then_raises_error(self):
        """Test error handling for empty phase deliverables."""
        foundation_state = FoundationState(
            phase_deliverables={},
            test_infrastructure_status={"tests": 0.8},
            singleton_baseline={},
            integration_health={}
        )

        with pytest.raises(ReadinessAssessmentError, match="Cannot assess readiness without phase deliverables"):
            assess_migration_readiness(foundation_state)

    def test_assess_migration_readiness_when_poor_foundation_then_identifies_blockers(self):
        """Test assessment with poor foundation state."""
        foundation_state = FoundationState(
            phase_deliverables={
                "incomplete_phase": {"implementation": False},
                "dependency_analysis": {"complete": True},
                "context_infrastructure": {"ready": True},
                "compatibility_layer": {"implemented": True}
            },
            test_infrastructure_status={
                "poor_tests": 0.3
            },
            singleton_baseline={},
            integration_health={"failing": False}
        )

        result = assess_migration_readiness(foundation_state)

        assert result.overall_readiness_score < 0.5
        assert len(result.migration_blockers) > 0
        assert "Overall readiness score too low - foundation must be stabilized" in result.migration_blockers or result.overall_readiness_score >= 0.5

class TestStabilityScoreCalculation:
    """Test stability score calculation logic."""

    def test_calculate_stability_score_when_good_test_scores_then_returns_high_score(self):
        """Test stability calculation with good test infrastructure."""
        foundation_state = FoundationState(
            phase_deliverables={"phase1": {}, "phase2": {}},
            test_infrastructure_status={
                "unit_tests": 0.9,
                "integration_tests": 0.85,
                "coverage": 0.88
            },
            singleton_baseline={},
            integration_health={}
        )

        score = _calculate_stability_score(foundation_state)

        expected_score = (0.9 + 0.85 + 0.88) / 3
        assert score == pytest.approx(expected_score, abs=0.01)

    def test_calculate_stability_score_when_no_deliverables_then_returns_zero(self):
        """Test stability calculation with no deliverables."""
        foundation_state = FoundationState(
            phase_deliverables={},
            test_infrastructure_status={"tests": 0.8},
            singleton_baseline={},
            integration_health={}
        )

        score = _calculate_stability_score(foundation_state)

        assert score == 0.0

    def test_calculate_stability_score_when_no_test_scores_then_returns_fallback(self):
        """Test stability calculation with no test scores."""
        foundation_state = FoundationState(
            phase_deliverables={"phase1": {}},
            test_infrastructure_status={},
            singleton_baseline={},
            integration_health={}
        )

        score = _calculate_stability_score(foundation_state)

        assert score == 0.5  # Fallback value

class TestDeliverableCompletenessEvaluation:
    """Test deliverable completeness evaluation logic."""

    def test_evaluate_deliverable_completeness_when_complete_deliverables_then_returns_high_scores(self):
        """Test evaluation with complete deliverables."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_1": {
                    "implementation": {"status": "complete"},
                    "tests": {"coverage": "95%"},
                    "documentation": {"status": "done"}
                },
                "phase_2": {
                    "implementation": {"status": "complete"},
                    "tests": {"coverage": "90%"},
                    "documentation": {"status": "done"}
                }
            },
            test_infrastructure_status={},
            singleton_baseline={},
            integration_health={}
        )

        completeness = _evaluate_deliverable_completeness(foundation_state)

        assert completeness["phase_1"] == 1.0
        assert completeness["phase_2"] == 1.0

    def test_evaluate_deliverable_completeness_when_partial_deliverables_then_returns_proportional_scores(self):
        """Test evaluation with partial deliverables."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_1": {
                    "implementation": {"status": "complete"},
                    "tests": None,  # Missing
                    "documentation": {"status": "done"}
                },
                "phase_2": {
                    "implementation": {"status": "complete"}
                    # Missing tests and documentation
                }
            },
            test_infrastructure_status={},
            singleton_baseline={},
            integration_health={}
        )

        completeness = _evaluate_deliverable_completeness(foundation_state)

        assert completeness["phase_1"] == pytest.approx(0.67, abs=0.1)  # 2/3 fields
        assert completeness["phase_2"] == pytest.approx(0.33, abs=0.1)  # 1/3 fields

    def test_evaluate_deliverable_completeness_when_non_dict_deliverables_then_uses_presence_check(self):
        """Test evaluation with non-dictionary deliverables."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_with_data": "some_data",
                "phase_without_data": None
            },
            test_infrastructure_status={},
            singleton_baseline={},
            integration_health={}
        )

        completeness = _evaluate_deliverable_completeness(foundation_state)

        assert completeness["phase_with_data"] == 1.0
        assert completeness["phase_without_data"] == 0.0

class TestOverallReadinessCalculation:
    """Test overall readiness score calculation."""

    def test_calculate_overall_readiness_when_high_scores_then_returns_high_readiness(self):
        """Test calculation with high component scores."""
        stability_score = 0.9
        completeness_scores = {"phase_1": 0.95, "phase_2": 0.9, "phase_3": 0.88}
        test_quality_scores = {"unit": 0.92, "integration": 0.87}
        integration_results = {"check_1": True, "check_2": True, "check_3": True}

        overall_score = _calculate_overall_readiness(
            stability_score, completeness_scores, test_quality_scores, integration_results
        )

        assert overall_score > 0.85
        assert overall_score <= 1.0

    def test_calculate_overall_readiness_when_low_scores_then_returns_low_readiness(self):
        """Test calculation with low component scores."""
        stability_score = 0.4
        completeness_scores = {"phase_1": 0.5, "phase_2": 0.3}
        test_quality_scores = {"unit": 0.4, "integration": 0.2}
        integration_results = {"check_1": False, "check_2": False}

        overall_score = _calculate_overall_readiness(
            stability_score, completeness_scores, test_quality_scores, integration_results
        )

        assert overall_score < 0.5
        assert overall_score >= 0.0

    def test_calculate_overall_readiness_when_empty_components_then_handles_gracefully(self):
        """Test calculation with empty component data."""
        stability_score = 0.8
        completeness_scores = {}
        test_quality_scores = {}
        integration_results = {}

        overall_score = _calculate_overall_readiness(
            stability_score, completeness_scores, test_quality_scores, integration_results
        )

        # Should primarily reflect stability score with fallback values
        expected_score = 0.8 * 0.4 + 0.0 * 0.3 + 0.0 * 0.2 + 0.0 * 0.1
        assert overall_score == pytest.approx(expected_score, abs=0.01)

class TestRecommendationGeneration:
    """Test recommendation generation logic."""

    def test_generate_recommendations_when_good_scores_then_recommends_proceed(self):
        """Test recommendations with good scores."""
        stability_score = 0.9
        completeness_scores = {"phase_1": 0.95, "phase_2": 0.92}
        test_quality_scores = {"unit": 0.9, "integration": 0.85}

        recommendations = _generate_recommendations(
            stability_score, completeness_scores, test_quality_scores
        )

        assert "Foundation is ready for migration planning" in recommendations
        assert len(recommendations) == 1

    def test_generate_recommendations_when_poor_scores_then_provides_specific_guidance(self):
        """Test recommendations with poor scores."""
        stability_score = 0.6  # Below 0.8 threshold
        completeness_scores = {"phase_1": 0.85, "phase_2": 0.7}  # phase_2 below 0.9
        test_quality_scores = {"unit": 0.9, "integration": 0.6}  # integration below 0.8

        recommendations = _generate_recommendations(
            stability_score, completeness_scores, test_quality_scores
        )

        assert "Improve foundation stability before proceeding with migration" in recommendations
        assert "Complete missing deliverables for phase_2" in recommendations
        assert "Enhance test coverage for integration" in recommendations
        assert len(recommendations) >= 3  # Expect at least 3 recommendations

class TestRiskFactorIdentification:
    """Test risk factor identification logic."""

    def test_identify_risk_factors_when_low_overall_score_then_identifies_high_risk(self):
        """Test risk identification with low overall readiness."""
        foundation_state = FoundationState(
            phase_deliverables={"phase1": {}},
            test_infrastructure_status={"poor_test": 0.5},  # Below 0.6 threshold
            singleton_baseline={},
            integration_health={}
        )
        overall_score = 0.6  # Below 0.7 threshold

        risks = _identify_risk_factors(foundation_state, overall_score)

        assert "Low overall readiness score indicates high migration risk" in risks
        assert "Missing singleton baseline may complicate migration planning" in risks
        assert "Poor test coverage in some areas may lead to regressions" in risks

    def test_identify_risk_factors_when_good_state_then_identifies_minimal_risks(self):
        """Test risk identification with good foundation state."""
        foundation_state = FoundationState(
            phase_deliverables={"phase1": {}},
            test_infrastructure_status={"good_test": 0.9},
            singleton_baseline={"patterns": ["pattern1"]},
            integration_health={}
        )
        overall_score = 0.85

        risks = _identify_risk_factors(foundation_state, overall_score)

        assert len(risks) == 0

class TestMigrationBlockerIdentification:
    """Test migration blocker identification logic."""

    def test_identify_migration_blockers_when_very_poor_state_then_identifies_critical_blockers(self):
        """Test blocker identification with critically poor state."""
        foundation_state = FoundationState(
            phase_deliverables={},  # No deliverables
            test_infrastructure_status={},
            singleton_baseline={},
            integration_health={}
        )
        overall_score = 0.3  # Below 0.5 threshold

        blockers = _identify_migration_blockers(foundation_state, overall_score)

        assert "Overall readiness score too low - foundation must be stabilized" in blockers
        assert "No phase deliverables found - cannot proceed with migration" in blockers

    def test_identify_migration_blockers_when_missing_critical_components_then_identifies_specific_blockers(self):
        """Test blocker identification with missing critical components."""
        foundation_state = FoundationState(
            phase_deliverables={
                "phase_1": {"some_component": True}
                # Missing critical components
            },
            test_infrastructure_status={"test": 0.8},
            singleton_baseline={},
            integration_health={}
        )
        overall_score = 0.6

        blockers = _identify_migration_blockers(foundation_state, overall_score)

        assert "Critical component missing: dependency_analysis" in blockers
        assert "Critical component missing: context_infrastructure" in blockers
        assert "Critical component missing: compatibility_layer" in blockers

    def test_identify_migration_blockers_when_good_state_then_no_blockers(self):
        """Test blocker identification with good foundation state."""
        foundation_state = FoundationState(
            phase_deliverables={
                "dependency_analysis": {"complete": True},
                "context_infrastructure": {"ready": True},
                "compatibility_layer": {"implemented": True}
            },
            test_infrastructure_status={"test": 0.8},
            singleton_baseline={"baseline": "established"},
            integration_health={}
        )
        overall_score = 0.8

        blockers = _identify_migration_blockers(foundation_state, overall_score)

        assert len(blockers) == 0

class TestReadinessAssessmentError:
    """Test readiness assessment error handling."""

    def test_readiness_assessment_error_when_created_with_context_then_includes_context(self):
        """Test error creation with assessment context."""
        context = {"component": "test_infrastructure", "score": 0.3}

        error = ReadinessAssessmentError("Assessment failed", context)

        assert str(error) == "Assessment failed"
        assert error.context["component"] == "test_infrastructure"
        assert error.context["score"] == 0.3

    def test_readiness_assessment_error_when_created_without_context_then_basic_error(self):
        """Test error creation without context."""
        error = ReadinessAssessmentError("Simple error")

        assert str(error) == "Simple error"
