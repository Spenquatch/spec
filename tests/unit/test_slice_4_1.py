"""Unit tests for Slice 4.1: Migration Readiness Assessment and Foundation Validation."""

from pathlib import Path
from unittest.mock import patch

import pytest

from slice_4_1_readiness_assessment import (
    ReadinessAssessmentResult,
    _calculate_foundation_stability,
    _calculate_phase_score,
    assess_phase_deliverables,
    execute_readiness_assessment,
    validate_foundation_integration,
    validate_test_infrastructure,
)
from spec_cli.utils.assessment.readiness_evaluator import (
    FoundationState,
    ReadinessReport,
)
from spec_cli.utils.migration_utils import MigrationError
from spec_cli.utils.test_analysis import FixtureAnalysisReport, FixtureInfo

class TestAssessPhaseDeliverables:
    """Test phase deliverable assessment functionality."""

    def test_assess_phase_deliverables_when_all_phases_complete_then_returns_high_scores(self):
        """Test assessment with complete phase data."""
        phase_1_data = {
            "dependency_analysis": {"complete": True},
            "spec_context": {"implemented": True},
            "factory_methods": {"working": True}
        }
        phase_2_data = {
            "click_integration": {"complete": True},
            "command_migration": {"done": True},
            "decorator_system": {"functional": True}
        }
        phase_3_data = {
            "singleton_detection": {"operational": True},
            "pattern_analysis": {"complete": True},
            "baseline_establishment": {"finished": True}
        }

        result = assess_phase_deliverables(phase_1_data, phase_2_data, phase_3_data)

        assert result["phase_1"] == 1.0
        assert result["phase_2"] == 1.0
        assert result["phase_3"] == 1.0
        assert len(result) == 3

    def test_assess_phase_deliverables_when_partial_completion_then_returns_proportional_scores(self):
        """Test assessment with partially complete phases."""
        phase_1_data = {
            "dependency_analysis": {"complete": True},
            "spec_context": None,  # Missing
            "factory_methods": {"working": True}
        }
        phase_2_data = {
            "click_integration": {"complete": True},
            # Missing other components
        }
        phase_3_data = {
            "singleton_detection": {"operational": True},
            "pattern_analysis": {"complete": True},
            "baseline_establishment": {"finished": True}
        }

        result = assess_phase_deliverables(phase_1_data, phase_2_data, phase_3_data)

        assert result["phase_1"] == pytest.approx(0.67, abs=0.1)  # 2/3 components
        assert result["phase_2"] == pytest.approx(0.33, abs=0.1)  # 1/3 components
        assert result["phase_3"] == 1.0

    def test_assess_phase_deliverables_when_missing_phase_then_raises_migration_error(self):
        """Test error handling for missing phase data."""
        phase_1_data = {"dependency_analysis": True}
        phase_2_data = None
        phase_3_data = {"singleton_detection": True}

        with pytest.raises(MigrationError, match="Phase 2 data is required"):
            assess_phase_deliverables(phase_1_data, phase_2_data, phase_3_data)

    def test_assess_phase_deliverables_when_empty_phases_then_returns_zero_scores(self):
        """Test assessment with empty phase data."""
        # Use non-empty but incomplete data to avoid validation error
        result = assess_phase_deliverables({"placeholder": None}, {"placeholder": None}, {"placeholder": None})

        assert result["phase_1"] == 0.0
        assert result["phase_2"] == 0.0
        assert result["phase_3"] == 0.0

class TestValidateTestInfrastructure:
    """Test test infrastructure validation functionality."""

    def test_validate_test_infrastructure_when_valid_path_then_returns_quality_scores(self):
        """Test validation with valid test results path."""
        test_path = Path("/tmp/test_results")

        with (
            patch("slice_4_1_readiness_assessment.analyze_test_fixtures") as mock_analyze,
            patch("pathlib.Path.exists", return_value=True),
            patch("slice_4_1_readiness_assessment._assess_coverage_quality", return_value=0.9),
            patch("slice_4_1_readiness_assessment._evaluate_test_isolation", return_value=0.85),
            patch("slice_4_1_readiness_assessment._check_integration_completeness", return_value=0.8),
        ):
            # Mock fixture analysis
            mock_fixtures = [
                FixtureInfo("fixture1", test_path, 1, state_contamination_risk=False),
                FixtureInfo("fixture2", test_path, 2, state_contamination_risk=True),
            ]
            mock_report = FixtureAnalysisReport(
                total_fixtures=2,
                singleton_dependent_fixtures=[mock_fixtures[0]],
                isolation_issues=[mock_fixtures[1]],
                context_migration_candidates=[],
                migration_requirements={},
                analysis_summary="Test report"
            )
            mock_analyze.return_value = mock_report

            result = validate_test_infrastructure(test_path)

            assert "fixture_stability" in result
            assert "coverage_quality" in result
            assert "test_isolation" in result
            assert "integration_completeness" in result
            assert result["fixture_stability"] == 0.5  # 1/2 stable fixtures
            assert result["coverage_quality"] == 0.9
            assert result["test_isolation"] == 0.85
            assert result["integration_completeness"] == 0.8

    def test_validate_test_infrastructure_when_path_missing_then_raises_migration_error(self):
        """Test error handling for missing test results path."""
        test_path = Path("/nonexistent/path")

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(MigrationError, match="Test results path does not exist"):
                validate_test_infrastructure(test_path)

    def test_validate_test_infrastructure_when_fixture_analysis_fails_then_uses_fallback(self):
        """Test graceful handling of fixture analysis failures."""
        test_path = Path("/tmp/test_results")

        with (
            patch("slice_4_1_readiness_assessment.analyze_test_fixtures", side_effect=Exception("Analysis failed")),
            patch("pathlib.Path.exists", return_value=True),
            patch("slice_4_1_readiness_assessment._assess_coverage_quality", return_value=0.9),
            patch("slice_4_1_readiness_assessment._evaluate_test_isolation", return_value=0.85),
            patch("slice_4_1_readiness_assessment._check_integration_completeness", return_value=0.8),
        ):
            result = validate_test_infrastructure(test_path)

            assert result["fixture_stability"] == 0.5  # Fallback value

class TestValidateFoundationIntegration:
    """Test foundation integration validation functionality."""

    def test_validate_foundation_integration_when_all_phases_present_then_validates_successfully(self):
        """Test integration validation with complete phase data."""
        phase_deliverables = {
            "phase_1": {"dependency_analysis": True},
            "phase_2": {"click_integration": True},
            "phase_3": {"singleton_detection": True}
        }
        test_infrastructure = {
            "fixture_stability": 0.9,
            "coverage_quality": 0.85,
            "test_isolation": 0.8
        }

        result = validate_foundation_integration(phase_deliverables, test_infrastructure)

        assert result["phase_1_to_2"] is True
        assert result["phase_2_to_3"] is True
        assert result["test_infrastructure_ready"] is True
        assert result["foundation_coherent"] is True

    def test_validate_foundation_integration_when_missing_phases_then_fails_validation(self):
        """Test integration validation with missing phases."""
        phase_deliverables = {
            "phase_1": {"dependency_analysis": True}
            # Missing phase_2 and phase_3
        }
        test_infrastructure = {"coverage_quality": 0.8}

        result = validate_foundation_integration(phase_deliverables, test_infrastructure)

        assert result["phase_1_to_2"] is False  # phase_2 missing
        assert result["phase_2_to_3"] is False  # phase_2 and phase_3 missing

    def test_validate_foundation_integration_when_poor_test_quality_then_fails_infrastructure_check(self):
        """Test integration validation with poor test infrastructure quality."""
        phase_deliverables = {
            "phase_1": {"dependency_analysis": True},
            "phase_2": {"click_integration": True},
            "phase_3": {"singleton_detection": True}
        }
        test_infrastructure = {
            "fixture_stability": 0.6,  # Below 0.7 threshold
            "coverage_quality": 0.5,   # Below threshold
        }

        result = validate_foundation_integration(phase_deliverables, test_infrastructure)

        assert result["test_infrastructure_ready"] is False
        assert result["foundation_coherent"] is False

    def test_validate_foundation_integration_when_empty_deliverables_then_raises_error(self):
        """Test error handling for empty phase deliverables."""
        with pytest.raises(MigrationError, match="Phase deliverables required"):
            validate_foundation_integration({}, {"test_score": 0.8})

class TestExecuteReadinessAssessment:
    """Test comprehensive readiness assessment execution."""

    @patch("slice_4_1_readiness_assessment.assess_migration_readiness")
    @patch("slice_4_1_readiness_assessment.validate_foundation_integration")
    def test_execute_readiness_assessment_when_complete_data_then_returns_assessment_result(
        self, mock_validate_integration, mock_assess_readiness
    ):
        """Test execution with complete input data."""
        # Setup mocks
        mock_readiness_report = ReadinessReport(
            overall_readiness_score=0.85,
            foundation_stability_verified=True,
            deliverable_completeness={"phase_1": 0.9, "phase_2": 0.8, "phase_3": 0.9},
            test_infrastructure_quality={"coverage": 0.9, "isolation": 0.8},
            integration_validation_results={"integration_check": True},
            risk_factors=[],
            recommendations=["Ready for migration"],
            migration_blockers=[]
        )
        mock_assess_readiness.return_value = mock_readiness_report

        mock_integration_results = {
            "phase_1_to_2": True,
            "phase_2_to_3": True,
            "test_infrastructure_ready": True
        }
        mock_validate_integration.return_value = mock_integration_results

        # Input data
        phase_deliverables = {
            "phase_1": {"dependency_analysis": True},
            "phase_2": {"click_integration": True},
            "phase_3": {"singleton_detection": True}
        }
        test_infrastructure_status = {"coverage": 0.9, "isolation": 0.8}
        singleton_baseline = {"detected_patterns": ["pattern1", "pattern2"]}

        result = execute_readiness_assessment(
            phase_deliverables, test_infrastructure_status, singleton_baseline
        )

        # Verify result structure
        assert isinstance(result, ReadinessAssessmentResult)
        assert result.readiness_report == mock_readiness_report
        assert result.foundation_stability_score > 0.0
        assert result.integration_validation_results == mock_integration_results
        assert "assessment_timestamp" in result.assessment_metadata
        assert "total_phases_assessed" in result.assessment_metadata

        # Verify foundation state was created correctly
        mock_assess_readiness.assert_called_once()
        foundation_state = mock_assess_readiness.call_args[0][0]
        assert isinstance(foundation_state, FoundationState)
        assert foundation_state.phase_deliverables == phase_deliverables
        assert foundation_state.test_infrastructure_status == test_infrastructure_status
        assert foundation_state.singleton_baseline == singleton_baseline

class TestHelperFunctions:
    """Test helper function implementations."""

    def test_calculate_phase_score_when_all_components_present_then_returns_one(self):
        """Test phase score calculation with complete data."""
        phase_data = {
            "component1": {"status": "complete"},
            "component2": {"status": "done"},
            "component3": {"status": "ready"}
        }
        required_components = ["component1", "component2", "component3"]

        score = _calculate_phase_score(phase_data, required_components)

        assert score == 1.0

    def test_calculate_phase_score_when_partial_components_then_returns_proportion(self):
        """Test phase score calculation with partial completion."""
        phase_data = {
            "component1": {"status": "complete"},
            "component2": None,  # Missing
            "component3": {"status": "ready"}
        }
        required_components = ["component1", "component2", "component3"]

        score = _calculate_phase_score(phase_data, required_components)

        assert score == pytest.approx(0.67, abs=0.1)  # 2/3 components

    def test_calculate_phase_score_when_empty_data_then_returns_zero(self):
        """Test phase score calculation with empty data."""
        score = _calculate_phase_score({}, ["component1", "component2"])

        assert score == 0.0

    def test_calculate_foundation_stability_when_good_scores_then_returns_weighted_average(self):
        """Test foundation stability calculation with good scores."""
        deliverable_completeness = {"phase_1": 0.9, "phase_2": 0.8, "phase_3": 0.85}
        test_infrastructure_quality = {"coverage": 0.9, "isolation": 0.8}

        stability_score = _calculate_foundation_stability(
            deliverable_completeness, test_infrastructure_quality
        )

        # Expected: (0.85 * 0.6) + (0.85 * 0.4) = 0.85
        assert stability_score == pytest.approx(0.85, abs=0.01)

    def test_calculate_foundation_stability_when_no_deliverables_then_returns_zero(self):
        """Test foundation stability calculation with no deliverables."""
        stability_score = _calculate_foundation_stability({}, {"test": 0.8})

        assert stability_score == 0.0

    def test_calculate_foundation_stability_when_no_test_data_then_uses_fallback(self):
        """Test foundation stability calculation with missing test data."""
        deliverable_completeness = {"phase_1": 0.8}

        stability_score = _calculate_foundation_stability(deliverable_completeness, {})

        # Expected: (0.8 * 0.6) + (0.5 * 0.4) = 0.68
        assert stability_score == pytest.approx(0.68, abs=0.01)

class TestReadinessAssessmentIntegration:
    """Test integration scenarios for readiness assessment."""

    @patch("slice_4_1_readiness_assessment.assess_migration_readiness")
    def test_readiness_assessment_integration_when_high_readiness_then_recommends_proceed(
        self, mock_assess_readiness
    ):
        """Test integration scenario with high readiness scores."""
        # Mock high-quality assessment
        mock_readiness_report = ReadinessReport(
            overall_readiness_score=0.92,
            foundation_stability_verified=True,
            deliverable_completeness={"phase_1": 0.95, "phase_2": 0.9, "phase_3": 0.9},
            test_infrastructure_quality={"coverage": 0.95, "isolation": 0.9, "integration": 0.85},
            integration_validation_results={"all_checks": True},
            risk_factors=[],
            recommendations=["Foundation ready for final migration phases"],
            migration_blockers=[]
        )
        mock_assess_readiness.return_value = mock_readiness_report

        # Execute assessment
        result = execute_readiness_assessment(
            {"phase_1": {}, "phase_2": {}, "phase_3": {}},
            {"coverage": 0.95, "isolation": 0.9},
            {"baseline": "established"}
        )

        assert result.readiness_report.overall_readiness_score >= 0.9
        assert result.foundation_stability_score > 0.8
        assert len(result.readiness_report.migration_blockers) == 0

    @patch("slice_4_1_readiness_assessment.assess_migration_readiness")
    def test_readiness_assessment_integration_when_low_readiness_then_identifies_blockers(
        self, mock_assess_readiness
    ):
        """Test integration scenario with low readiness scores."""
        # Mock low-quality assessment
        mock_readiness_report = ReadinessReport(
            overall_readiness_score=0.45,
            foundation_stability_verified=False,
            deliverable_completeness={"phase_1": 0.6, "phase_2": 0.4, "phase_3": 0.3},
            test_infrastructure_quality={"coverage": 0.5, "isolation": 0.4},
            integration_validation_results={"critical_check": False},
            risk_factors=["Low test coverage", "Incomplete deliverables"],
            recommendations=["Complete Phase 2 and 3 deliverables", "Improve test coverage"],
            migration_blockers=["Foundation stability insufficient"]
        )
        mock_assess_readiness.return_value = mock_readiness_report

        # Execute assessment
        result = execute_readiness_assessment(
            {"phase_1": {}, "phase_2": {}, "phase_3": {}},
            {"coverage": 0.5, "isolation": 0.4},
            {}
        )

        assert result.readiness_report.overall_readiness_score < 0.5
        assert not result.readiness_report.foundation_stability_verified
        assert len(result.readiness_report.migration_blockers) > 0
        assert len(result.readiness_report.risk_factors) > 0
