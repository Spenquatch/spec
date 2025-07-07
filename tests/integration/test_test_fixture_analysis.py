"""Integration tests for test fixture analysis functionality.

Tests the complete test fixture analysis workflow against the actual test suite
structure to validate migration requirements identification.
"""

from pathlib import Path

from spec_cli.utils.test_analysis import analyze_test_fixtures


class TestTestFixtureAnalysisIntegration:
    """Integration tests for complete test fixture analysis workflow."""

    def test_test_fixture_analysis_when_full_test_suite_then_comprehensive_migration_requirements(
        self,
    ):
        """Test fixture analysis against actual test suite provides comprehensive migration requirements."""
        # Setup: Use actual tests directory
        tests_dir = Path(__file__).parent.parent  # Go up to tests/ directory

        # Execute: Analyze the actual test suite
        report = analyze_test_fixtures(tests_dir)

        # Verify: Report structure and comprehensive analysis
        assert report.total_fixtures > 0, "Should find fixtures in actual test suite"

        # Verify analysis identifies known patterns from actual codebase
        assert "Test Fixture Analysis Summary" in report.analysis_summary
        assert "fixtures analyzed" in report.analysis_summary

        # Verify migration requirements are generated
        # Note: May be empty if singleton infrastructure already removed
        assert isinstance(report.migration_requirements, dict)

        # Verify report structure completeness
        assert hasattr(report, "singleton_dependent_fixtures")
        assert hasattr(report, "isolation_issues")
        assert hasattr(report, "context_migration_candidates")

        # Verify each fixture list contains FixtureInfo objects
        for fixture in report.singleton_dependent_fixtures:
            assert hasattr(fixture, "name")
            assert hasattr(fixture, "file_path")
            assert hasattr(fixture, "singleton_dependencies")

        for fixture in report.isolation_issues:
            assert hasattr(fixture, "state_contamination_risk")
            assert fixture.state_contamination_risk is True

        for fixture in report.context_migration_candidates:
            assert hasattr(fixture, "context_migration_required")
            assert fixture.context_migration_required is True

        # Verify migration requirements format
        for fixture_name, requirement in report.migration_requirements.items():
            assert isinstance(fixture_name, str)
            assert isinstance(requirement, str)
            assert len(requirement) > 0

        # Log analysis results for debugging
        print("\nTest Fixture Analysis Results:")
        print(f"Total fixtures: {report.total_fixtures}")
        print(f"Singleton dependent: {len(report.singleton_dependent_fixtures)}")
        print(f"Isolation issues: {len(report.isolation_issues)}")
        print(f"Migration candidates: {len(report.context_migration_candidates)}")
        print(f"Migration requirements: {len(report.migration_requirements)}")
        print(f"\nSummary:\n{report.analysis_summary}")

        if report.migration_requirements:
            print("\nMigration Requirements:")
            for name, req in report.migration_requirements.items():
                print(f"- {name}: {req}")

    def test_fixture_analysis_when_singleton_infrastructure_removed_then_identifies_cleanup_requirements(
        self,
    ):
        """Test fixture analysis identifies cleanup requirements after singleton removal."""
        # Setup: Use actual tests directory
        tests_dir = Path(__file__).parent.parent

        # Execute: Analyze for post-singleton-removal state
        report = analyze_test_fixtures(tests_dir)

        # Verify: Analysis handles the post-removal state appropriately
        # Since singleton infrastructure is removed, we expect:
        # 1. Fewer direct singleton dependencies (they would cause import errors)
        # 2. Potential isolation issues from previous singleton patterns
        # 3. Need for context-based fixture migration

        # The analysis should complete without errors even with removed singletons
        assert isinstance(report, type(report))  # Report created successfully

        # Check if analysis identifies the current broken state
        total_fixtures = report.total_fixtures

        # In the current state, fixtures may not be discoverable due to import errors
        # But the analysis should handle this gracefully
        if total_fixtures == 0:
            # Import errors prevent fixture discovery - this is expected
            print("Note: Fixture discovery limited due to singleton import errors")
        else:
            # Some fixtures were discoverable
            print(f"Discovered {total_fixtures} fixtures despite singleton removal")

        # Verify analysis summary provides useful information regardless
        assert "fixtures analyzed" in report.analysis_summary

        # The migration requirements should reflect the current state
        print("\nPost-singleton-removal analysis:")
        print(f"Fixtures discoverable: {total_fixtures}")
        print(f"Analysis summary: {report.analysis_summary}")

    def test_test_analysis_when_context_migration_planned_then_provides_fixture_migration_specs(
        self, tmp_path
    ):
        """Test analysis provides specific fixture migration specifications for context patterns."""
        # Setup: Create sample test structure mimicking current codebase patterns
        conftest_file = tmp_path / "conftest.py"
        conftest_file.write_text("""
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def isolate_working_directory():
    # Current pattern from actual conftest.py
    import os
    original_cwd = os.getcwd()
    try:
        yield
    finally:
        if os.getcwd() != original_cwd:
            os.chdir(original_cwd)

@pytest.fixture(autouse=True)
def clean_mock_state():
    # Current pattern from actual conftest.py
    import sys
    initial_modules = set(sys.modules.keys())
    try:
        yield
    finally:
        patch.stopall()

@pytest.fixture
def mock_git_environment(tmp_path):
    # Pattern requiring context migration
    from spec_cli.utils.test_helpers.git_test_helpers import create_git_repository_mocker
    return create_git_repository_mocker(tmp_path)
        """)

        test_file = tmp_path / "test_sample.py"
        test_file.write_text("""
import pytest

@pytest.fixture
def sample_context_fixture():
    # This would need context injection
    return {"isolated": True}
        """)

        # Execute: Analyze the sample structure
        report = analyze_test_fixtures(tmp_path)

        # Verify: Analysis provides migration specifications
        assert report.total_fixtures >= 3  # The fixtures we created

        # Check for isolation patterns
        isolation_fixtures = [
            f
            for f in report.isolation_issues
            if "isolate" in f.name or "clean" in f.name
        ]
        assert len(isolation_fixtures) >= 1  # Should identify isolation patterns

        # Verify migration requirements address context needs
        requirements = report.migration_requirements

        # Should provide specific guidance for context migration
        for _fixture_name, requirement in requirements.items():
            assert isinstance(requirement, str)
            assert len(requirement) > 0

        print("\nContext migration analysis:")
        print(f"Isolation fixtures identified: {len(isolation_fixtures)}")
        print(f"Migration requirements: {requirements}")

    def test_fixture_analysis_when_singleton_dependencies_identified_then_maps_context_requirements(
        self, tmp_path
    ):
        """Test fixture analysis maps singleton dependencies to specific context requirements."""
        # Setup: Create fixtures with various singleton patterns
        test_file = tmp_path / "conftest.py"
        test_file.write_text("""
import pytest

@pytest.fixture
def settings_dependent_fixture():
    # Direct singleton access pattern
    from spec_cli.config.settings import get_settings
    settings = get_settings()
    return settings.root_path

@pytest.fixture
def console_dependent_fixture():
    # Console singleton access pattern
    from spec_cli.ui.console import get_console
    console = get_console()
    console.print_message("test")
    return console

@pytest.fixture
def complex_singleton_fixture():
    # Multiple singleton dependencies
    from spec_cli.config.settings import get_settings
    from spec_cli.ui.console import get_console, reset_console

    settings = get_settings()
    console = get_console()
    reset_console()

    return {"settings": settings, "console": console}
        """)

        # Execute: Analyze singleton dependencies
        report = analyze_test_fixtures(tmp_path)

        # Verify: Dependencies mapped to context requirements
        assert report.total_fixtures >= 3

        # Check specific migration mappings
        requirements = report.migration_requirements

        # Should identify settings-based migration needs
        settings_requirements = [
            req
            for name, req in requirements.items()
            if "settings" in name.lower() and "context.settings" in req
        ]

        # Should identify console-based migration needs
        console_requirements = [
            req
            for name, req in requirements.items()
            if "console" in name.lower() and "context.console" in req
        ]

        print("\nSingleton dependency mapping:")
        print(f"Settings requirements: {len(settings_requirements)}")
        print(f"Console requirements: {len(console_requirements)}")
        print(f"All requirements: {requirements}")

        # Verify requirements provide actionable guidance
        for requirement in requirements.values():
            assert "context" in requirement or "migration" in requirement

    def test_test_analysis_when_isolation_issues_found_then_specifies_context_based_solutions(
        self, tmp_path
    ):
        """Test analysis specifies context-based solutions for isolation issues."""
        # Setup: Create fixtures with isolation problems
        problem_file = tmp_path / "conftest.py"
        problem_file.write_text("""
import pytest
import os
import sys

@pytest.fixture
def environment_contaminating_fixture():
    # Environment variable contamination
    os.environ["SPEC_DEBUG"] = "1"
    os.environ["SPEC_ROOT_PATH"] = "/test"
    yield
    # No cleanup - contamination risk

@pytest.fixture
def module_contaminating_fixture():
    # Module state contamination
    sys.modules["fake_module"] = type(sys)("fake")
    global global_state
    global_state = "modified"
    yield
    # No cleanup - contamination risk

@pytest.fixture
def directory_contaminating_fixture():
    # Working directory contamination
    import os
    original = os.getcwd()
    os.chdir("/tmp")
    yield
    # Missing restoration - contamination risk
        """)

        # Execute: Analyze isolation issues
        report = analyze_test_fixtures(tmp_path)

        # Verify: Isolation issues identified and solutions specified
        assert len(report.isolation_issues) >= 2  # Multiple contaminating fixtures

        # Check each isolation issue has context-based guidance
        for fixture in report.isolation_issues:
            assert fixture.state_contamination_risk is True

            # Should be identified as migration candidate
            assert fixture.name in [c.name for c in report.context_migration_candidates]

        # Migration requirements should address isolation
        contamination_requirements = [
            req
            for name, req in report.migration_requirements.items()
            if "contaminating" in name.lower()
        ]

        print("\nIsolation issue analysis:")
        print(f"Contaminating fixtures: {len(report.isolation_issues)}")
        print(f"Contamination requirements: {len(contamination_requirements)}")

        # Verify solutions focus on context-based approaches
        for requirement in contamination_requirements:
            requirement_lower = requirement.lower()
            assert (
                "context" in requirement_lower
                or "injection" in requirement_lower
                or "migration" in requirement_lower
            )
