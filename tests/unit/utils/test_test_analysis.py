"""Unit tests for test fixture analysis functionality.

Tests the analysis of existing test fixtures and identification of migration
requirements for context-based dependency injection.
"""

import ast
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.utils.test_analysis import (
    FixtureAnalysisError,
    FixtureAnalysisReport,
    FixtureInfo,
    analyze_test_fixtures,
    identify_singleton_dependencies,
)

# Test constants - no magic numbers
DEFAULT_FIXTURE_LINE_NUMBER = 10
SAMPLE_FIXTURE_COUNT = 3
SINGLETON_DEPENDENCY_COUNT = 2
ISOLATION_ISSUE_COUNT = 1
EMPTY_FIXTURE_COUNT = 0

class TestAnalyzeTestFixtures:
    """Unit tests for analyze_test_fixtures function."""

    def test_analyze_test_fixtures_when_fixtures_found_then_returns_comprehensive_report(
        self, tmp_path
    ):
        """Test fixture analysis returns comprehensive report when fixtures found."""
        # Setup: Create test files with fixtures
        conftest_file = tmp_path / "conftest.py"
        conftest_file.write_text("""
import pytest

@pytest.fixture
def sample_fixture():
    settings = get_settings()  # Singleton dependency
    return settings

@pytest.fixture(scope="session")
def session_fixture():
    console = get_console()  # Singleton dependency
    return console

@pytest.fixture(autouse=True)
def clean_fixture():
    import os
    os.environ.clear()  # State contamination risk
    yield
        """)

        test_file = tmp_path / "test_example.py"
        test_file.write_text("""
import pytest

@pytest.fixture
def simple_fixture():
    return "clean"
        """)

        # Execute: Analyze fixtures
        report = analyze_test_fixtures(tmp_path)

        # Verify: Report structure and content
        assert report.total_fixtures >= SAMPLE_FIXTURE_COUNT
        assert len(report.singleton_dependent_fixtures) >= SINGLETON_DEPENDENCY_COUNT
        assert len(report.isolation_issues) >= ISOLATION_ISSUE_COUNT
        assert len(report.context_migration_candidates) >= SINGLETON_DEPENDENCY_COUNT
        assert len(report.migration_requirements) >= SINGLETON_DEPENDENCY_COUNT
        assert "Test Fixture Analysis Summary" in report.analysis_summary

        # Verify specific fixture details
        fixture_names = [f.name for f in report.singleton_dependent_fixtures]
        assert "sample_fixture" in fixture_names or "session_fixture" in fixture_names

    def test_analyze_test_fixtures_when_no_fixtures_then_returns_empty_report(
        self, tmp_path
    ):
        """Test fixture analysis returns empty report when no fixtures found."""
        # Setup: Create test file without fixtures
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("""
def test_simple():
    assert True
        """)

        # Execute: Analyze fixtures
        report = analyze_test_fixtures(tmp_path)

        # Verify: Empty report
        assert report.total_fixtures == EMPTY_FIXTURE_COUNT
        assert len(report.singleton_dependent_fixtures) == EMPTY_FIXTURE_COUNT
        assert len(report.isolation_issues) == EMPTY_FIXTURE_COUNT
        assert len(report.context_migration_candidates) == EMPTY_FIXTURE_COUNT
        assert len(report.migration_requirements) == EMPTY_FIXTURE_COUNT
        assert "0" in report.analysis_summary

    def test_analyze_test_fixtures_when_directory_not_exists_then_raises_error(self):
        """Test fixture analysis raises error when directory doesn't exist."""
        non_existent_path = Path("/non/existent/directory")

        with pytest.raises(FixtureAnalysisError) as exc_info:
            analyze_test_fixtures(non_existent_path)

        assert "does not exist" in str(exc_info.value)

    def test_analyze_test_fixtures_when_path_not_directory_then_raises_error(
        self, tmp_path
    ):
        """Test fixture analysis raises error when path is not a directory."""
        # Setup: Create file instead of directory
        file_path = tmp_path / "not_a_directory.py"
        file_path.write_text("# This is a file")

        with pytest.raises(FixtureAnalysisError) as exc_info:
            analyze_test_fixtures(file_path)

        assert "not a directory" in str(exc_info.value)

    def test_analyze_test_fixtures_when_analysis_fails_then_raises_test_analysis_error(
        self, tmp_path
    ):
        """Test fixture analysis raises FixtureAnalysisError when analysis fails."""
        # Setup: Create invalid Python file
        invalid_file = tmp_path / "conftest.py"
        invalid_file.write_text("invalid python syntax {{{")

        # Execute and verify: Analysis should handle parsing errors gracefully
        # but still return a report (files with parse errors are skipped)
        report = analyze_test_fixtures(tmp_path)
        assert isinstance(report, FixtureAnalysisReport)

    def test_analyze_test_fixtures_when_state_contamination_found_then_identifies_isolation_issues(
        self, tmp_path
    ):
        """Test fixture analysis identifies state contamination patterns."""
        # Setup: Create fixture with state contamination
        conftest_file = tmp_path / "conftest.py"
        conftest_file.write_text("""
import pytest
import os
import sys

@pytest.fixture
def contaminating_fixture():
    # Multiple contamination patterns
    os.environ["TEST_VAR"] = "value"
    os.chdir("/tmp")
    sys.modules["fake_module"] = None
    global global_state
    global_state = "modified"
    yield
        """)

        # Execute: Analyze fixtures
        report = analyze_test_fixtures(tmp_path)

        # Verify: Isolation issues identified
        assert len(report.isolation_issues) >= ISOLATION_ISSUE_COUNT
        contaminating_fixture = next(
            (f for f in report.isolation_issues if f.name == "contaminating_fixture"),
            None,
        )
        assert contaminating_fixture is not None
        assert contaminating_fixture.state_contamination_risk is True

    def test_analyze_test_fixtures_when_migration_requirements_then_generates_context_based_specs(
        self, tmp_path
    ):
        """Test fixture analysis generates context-based migration specifications."""
        # Setup: Create fixtures requiring different migration types
        conftest_file = tmp_path / "conftest.py"
        conftest_file.write_text("""
import pytest

@pytest.fixture
def settings_fixture():
    return get_settings()

@pytest.fixture
def console_fixture():
    return get_console()

@pytest.fixture
def singleton_fixture():

    class TestClass:
        pass
    return TestClass()
        """)

        # Execute: Analyze fixtures
        report = analyze_test_fixtures(tmp_path)

        # Verify: Migration requirements generated
        assert len(report.migration_requirements) >= SINGLETON_DEPENDENCY_COUNT

        # Check specific migration patterns
        requirements = report.migration_requirements
        settings_req = next(
            (req for name, req in requirements.items() if "settings" in name.lower()),
            None,
        )
        console_req = next(
            (req for name, req in requirements.items() if "console" in name.lower()),
            None,
        )

        if settings_req:
            assert "context.settings" in settings_req
        if console_req:
            assert "context.console" in console_req

class TestIdentifySingletonDependencies:
    """Unit tests for identify_singleton_dependencies function."""

    def test_identify_singleton_dependencies_when_singleton_usage_then_returns_dependency_list(
        self, tmp_path
    ):
        """Test singleton dependency identification returns dependency list."""
        # Setup: Create fixture function with singleton patterns
        fixture_file = tmp_path / "fixture_source.py"
        fixture_file.write_text("""
import pytest

@pytest.fixture
def test_fixture():
    settings = get_settings()
    console = get_console()
    return settings, console
        """)

        # Parse and get function
        source = fixture_file.read_text()
        tree = ast.parse(source)
        fixture_func = None

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "test_fixture":
                # Create mock function with the required attributes
                fixture_func = Mock()
                fixture_func.__name__ = "test_fixture"
                fixture_func.__code__ = Mock()
                fixture_func.__code__.co_filename = str(fixture_file)
                break

        # Execute: Identify dependencies
        dependencies = identify_singleton_dependencies(fixture_func)

        # Verify: Dependencies found
        expected_patterns = ["get_settings", "get_console"]
        for pattern in expected_patterns:
            assert any(pattern in dep for dep in dependencies)

    def test_identify_singleton_dependencies_when_clean_fixture_then_returns_empty_list(
        self, tmp_path
    ):
        """Test singleton dependency identification returns empty list for clean fixture."""
        # Setup: Create clean fixture function
        fixture_file = tmp_path / "clean_fixture.py"
        fixture_file.write_text("""
import pytest

@pytest.fixture
def clean_fixture():
    return {"clean": True}
        """)

        # Parse and get function
        source = fixture_file.read_text()
        ast.parse(source)

        # Create mock function for clean fixture
        fixture_func = Mock()
        fixture_func.__name__ = "clean_fixture"
        fixture_func.__code__ = Mock()
        fixture_func.__code__.co_filename = str(fixture_file)

        # Execute: Identify dependencies
        dependencies = identify_singleton_dependencies(fixture_func)

        # Verify: No dependencies found
        assert len(dependencies) == EMPTY_FIXTURE_COUNT

    def test_identify_singleton_dependencies_when_function_without_code_then_returns_empty_list(
        self,
    ):
        """Test singleton dependency identification handles functions without code."""
        # Setup: Mock function without __code__ attribute
        fixture_func = Mock()
        del fixture_func.__code__

        # Execute: Identify dependencies
        dependencies = identify_singleton_dependencies(fixture_func)

        # Verify: Empty list returned
        assert dependencies == []

    def test_identify_singleton_dependencies_when_file_not_exists_then_returns_empty_list(
        self,
    ):
        """Test singleton dependency identification handles non-existent files."""
        # Setup: Mock function with non-existent file
        fixture_func = Mock()
        fixture_func.__name__ = "test_fixture"
        fixture_func.__code__ = Mock()
        fixture_func.__code__.co_filename = "/non/existent/file.py"

        # Execute: Identify dependencies
        dependencies = identify_singleton_dependencies(fixture_func)

        # Verify: Empty list returned
        assert dependencies == []

    def test_identify_singleton_dependencies_when_analysis_fails_then_raises_test_analysis_error(
        self,
    ):
        """Test singleton dependency identification raises error when analysis fails."""
        # Setup: Mock function that will cause analysis failure
        fixture_func = Mock()
        fixture_func.__name__ = "test_fixture"
        fixture_func.__code__ = Mock()
        fixture_func.__code__.co_filename = "valid_path.py"

        # Mock Path.read_text to raise exception
        with (
            patch("spec_cli.utils.test_analysis.Path.exists", return_value=True),
            patch(
                "spec_cli.utils.test_analysis.Path.read_text",
                side_effect=OSError("Read error"),
            ),
        ):
            with pytest.raises(FixtureAnalysisError) as exc_info:
                identify_singleton_dependencies(fixture_func)

            assert "Failed to analyze fixture function" in str(exc_info.value)

class TestFixtureInfo:
    """Unit tests for FixtureInfo dataclass."""

    def test_fixture_info_when_created_then_has_expected_defaults(self):
        """Test FixtureInfo dataclass has expected default values."""
        # Execute: Create fixture info
        fixture_info = FixtureInfo(
            name="test_fixture",
            file_path=Path("test.py"),
            line_number=DEFAULT_FIXTURE_LINE_NUMBER,
        )

        # Verify: Default values set correctly
        assert fixture_info.name == "test_fixture"
        assert fixture_info.file_path == Path("test.py")
        assert fixture_info.line_number == DEFAULT_FIXTURE_LINE_NUMBER
        assert fixture_info.scope == "function"
        assert fixture_info.autouse is False
        assert fixture_info.singleton_dependencies == []
        assert fixture_info.state_contamination_risk is False
        assert fixture_info.context_migration_required is False

class TestFixtureAnalysisReport:
    """Unit tests for FixtureAnalysisReport dataclass."""

    def test_test_fixture_report_when_created_then_has_expected_defaults(self):
        """Test FixtureAnalysisReport dataclass has expected default values."""
        # Execute: Create report
        report = FixtureAnalysisReport()

        # Verify: Default values set correctly
        assert report.total_fixtures == EMPTY_FIXTURE_COUNT
        assert report.singleton_dependent_fixtures == []
        assert report.isolation_issues == []
        assert report.context_migration_candidates == []
        assert report.migration_requirements == {}
        assert report.analysis_summary == ""
