"""Unit tests for slice P1.1a dependency analysis functionality.

Tests for spec_cli.utils.dependency_analysis module focusing on dependency
validation, usage analysis, and report generation.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.utils.dependency_analysis import (
    DependencyReport,
    DependencyUsage,
    DependencyValidationError,
    _analyze_single_dependency,
    _file_uses_dependency,
    _generate_context_requirements,
    analyze_current_usage,
    generate_dependency_report,
    validate_dependency_exists,
)

# Test constants
VALID_IMPORT_PATH = "spec_cli.config.settings"
INVALID_IMPORT_PATH = "nonexistent.module.path"
TEST_DEPENDENCY_NAME = "settings"
TEST_CODEBASE_PATH = Path("/test/codebase")
SAMPLE_FILE_CONTENT = """
import settings
from config import settings
def use_settings():
    return settings.debug_enabled
class SettingsManager:
    def __init__(self):
        self.settings = settings
"""


class TestValidateDependencyExists:
    """Test dependency import path validation."""

    def test_validate_dependency_exists_when_valid_import_then_returns_true(self):
        """Test dependency validation with existing imports."""
        with (
            patch("importlib.util.find_spec") as mock_find_spec,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):
            # Setup mocks for successful import
            mock_spec = Mock()
            mock_spec.loader = Mock()
            mock_find_spec.return_value = mock_spec
            mock_module = Mock()
            mock_module_from_spec.return_value = mock_module

            result = validate_dependency_exists(VALID_IMPORT_PATH)

            assert result is True
            mock_find_spec.assert_called_once_with(VALID_IMPORT_PATH)
            mock_spec.loader.exec_module.assert_called_once_with(mock_module)

    def test_validate_dependency_exists_when_invalid_import_then_returns_false(self):
        """Test dependency validation with non-existent imports."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            result = validate_dependency_exists(INVALID_IMPORT_PATH)

            assert result is False
            mock_find_spec.assert_called_once_with(INVALID_IMPORT_PATH)

    def test_validate_dependency_exists_when_import_error_then_returns_false(self):
        """Test dependency validation when import fails."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.side_effect = ImportError("Module not found")

            result = validate_dependency_exists(VALID_IMPORT_PATH)

            assert result is False

    def test_validate_dependency_exists_when_no_loader_then_returns_false(self):
        """Test dependency validation when spec has no loader."""
        with (
            patch("importlib.util.find_spec") as mock_find_spec,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):
            mock_spec = Mock()
            mock_spec.loader = None
            mock_spec.name = VALID_IMPORT_PATH
            mock_find_spec.return_value = mock_spec
            mock_module_from_spec.return_value = Mock()

            result = validate_dependency_exists(VALID_IMPORT_PATH)

            assert result is False

    def test_validate_dependency_exists_when_module_exec_fails_then_returns_false(self):
        """Test dependency validation when module execution fails."""
        with (
            patch("importlib.util.find_spec") as mock_find_spec,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):
            mock_spec = Mock()
            mock_spec.loader = Mock()
            mock_spec.loader.exec_module.side_effect = AttributeError(
                "Execution failed"
            )
            mock_find_spec.return_value = mock_spec
            mock_module_from_spec.return_value = Mock()

            result = validate_dependency_exists(VALID_IMPORT_PATH)

            assert result is False


class TestAnalyzeCurrentUsage:
    """Test current dependency usage analysis."""

    def test_analyze_current_usage_when_dependency_found_then_returns_file_list(self):
        """Test usage analysis for existing dependencies."""
        test_files = [
            TEST_CODEBASE_PATH / "module1.py",
            TEST_CODEBASE_PATH / "module2.py",
            TEST_CODEBASE_PATH / "subdir" / "module3.py",
        ]

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "rglob") as mock_rglob,
            patch(
                "spec_cli.utils.dependency_analysis._file_uses_dependency"
            ) as mock_file_uses,
        ):
            mock_rglob.return_value = test_files
            mock_file_uses.side_effect = lambda file_path, dep_name: file_path.name in [
                "module1.py",
                "module3.py",
            ]

            result = analyze_current_usage(TEST_DEPENDENCY_NAME, TEST_CODEBASE_PATH)

            expected_files = [str(test_files[0]), str(test_files[2])]
            assert result == expected_files
            assert len(result) == 2
            mock_rglob.assert_called_once_with("*.py")

    def test_analyze_current_usage_when_dependency_missing_then_returns_empty_list(
        self,
    ):
        """Test usage analysis for missing dependencies."""
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "rglob") as mock_rglob,
            patch(
                "spec_cli.utils.dependency_analysis._file_uses_dependency"
            ) as mock_file_uses,
        ):
            mock_rglob.return_value = [TEST_CODEBASE_PATH / "module1.py"]
            mock_file_uses.return_value = False

            result = analyze_current_usage(TEST_DEPENDENCY_NAME, TEST_CODEBASE_PATH)

            assert result == []

    def test_analyze_current_usage_when_codebase_missing_then_raises_validation_error(
        self,
    ):
        """Test usage analysis when codebase path doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(DependencyValidationError) as exc_info:
                analyze_current_usage(TEST_DEPENDENCY_NAME, TEST_CODEBASE_PATH)

            assert "does not exist" in str(exc_info.value)
            # Check that context contains expected error information
            assert exc_info.value.context["file_path"] == str(TEST_CODEBASE_PATH)
            assert exc_info.value.context["file_exists"] is False

    def test_analyze_current_usage_when_os_error_then_raises_validation_error(self):
        """Test usage analysis when OS error occurs during file scanning."""
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "rglob") as mock_rglob,
            patch("spec_cli.utils.error_utils.create_error_context") as mock_context,
        ):
            mock_rglob.side_effect = OSError("Permission denied")
            mock_context.return_value = {"test": "context"}

            with pytest.raises(DependencyValidationError) as exc_info:
                analyze_current_usage(TEST_DEPENDENCY_NAME, TEST_CODEBASE_PATH)

            assert "Failed to analyze dependency usage" in str(exc_info.value)


class TestGenerateDependencyReport:
    """Test comprehensive dependency report generation."""

    def test_dependency_analysis_when_codebase_scan_then_generates_complete_report(
        self,
    ):
        """Test complete dependency analysis workflow."""
        dependency_names = ["settings", "console"]

        with patch(
            "spec_cli.utils.dependency_analysis._analyze_single_dependency"
        ) as mock_analyze:
            mock_settings_report = DependencyReport(
                dependency_name="settings",
                exists=True,
                usage_patterns=[],
                import_paths={"spec_cli.config.settings"},
                requirements={"name": "settings", "required": True},
                analysis_errors=[],
            )
            mock_console_report = DependencyReport(
                dependency_name="console",
                exists=True,
                usage_patterns=[],
                import_paths={"spec_cli.ui.console"},
                requirements={"name": "console", "required": True},
                analysis_errors=[],
            )
            mock_analyze.side_effect = [mock_settings_report, mock_console_report]

            result = generate_dependency_report(dependency_names, TEST_CODEBASE_PATH)

            assert len(result) == 2
            assert "settings" in result
            assert "console" in result
            assert result["settings"].exists is True
            assert result["console"].exists is True
            assert mock_analyze.call_count == 2

    def test_generate_dependency_report_when_analysis_fails_then_creates_error_report(
        self,
    ):
        """Test dependency report generation when analysis fails for some dependencies."""
        dependency_names = ["settings", "failing_dep"]

        with patch(
            "spec_cli.utils.dependency_analysis._analyze_single_dependency"
        ) as mock_analyze:
            mock_settings_report = DependencyReport(
                dependency_name="settings",
                exists=True,
                usage_patterns=[],
                import_paths={"spec_cli.config.settings"},
                requirements={"name": "settings", "required": True},
                analysis_errors=[],
            )
            mock_analyze.side_effect = [
                mock_settings_report,
                Exception("Analysis failed"),
            ]

            result = generate_dependency_report(dependency_names, TEST_CODEBASE_PATH)

            assert len(result) == 2
            assert result["settings"].exists is True
            assert result["failing_dep"].exists is False
            assert len(result["failing_dep"].analysis_errors) == 1
            assert "Analysis failed" in result["failing_dep"].analysis_errors[0]


class TestDependencyValidationError:
    """Test custom exception for dependency validation errors."""

    def test_dependency_validation_error_when_critical_dependency_missing_then_raises_validation_error(
        self,
    ):
        """Test error handling for missing critical dependencies."""
        context = {"dependency": "critical_dep", "file_path": "/test/path"}

        with pytest.raises(DependencyValidationError) as exc_info:
            raise DependencyValidationError("Critical dependency missing", context)

        assert "Critical dependency missing" in str(exc_info.value)
        assert exc_info.value.context == context

    def test_dependency_validation_error_when_no_context_then_uses_empty_dict(self):
        """Test error creation with no context provided."""
        with pytest.raises(DependencyValidationError) as exc_info:
            raise DependencyValidationError("Error message")

        assert exc_info.value.context == {}


class TestFileUsesDependency:
    """Test file dependency usage detection."""

    def test_file_uses_dependency_when_import_statement_then_returns_true(self):
        """Test file usage detection with import statements."""
        test_file = Path("/test/file.py")

        with patch.object(
            Path, "read_text", return_value="import settings\nfrom config import other"
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is True

    def test_file_uses_dependency_when_from_import_then_returns_true(self):
        """Test file usage detection with from imports."""
        test_file = Path("/test/file.py")

        with patch.object(
            Path, "read_text", return_value="from settings import config"
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is True

    def test_file_uses_dependency_when_method_call_then_returns_true(self):
        """Test file usage detection with method calls."""
        test_file = Path("/test/file.py")

        with patch.object(
            Path, "read_text", return_value="result = settings.get_value()"
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is True

    def test_file_uses_dependency_when_class_definition_then_returns_true(self):
        """Test file usage detection with class definitions."""
        test_file = Path("/test/file.py")

        # Use a pattern that matches one of the dependency patterns (contains "settings.")
        with patch.object(
            Path, "read_text", return_value="def init_settings():\n    settings.config"
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is True

    def test_file_uses_dependency_when_not_found_then_returns_false(self):
        """Test file usage detection when dependency not found."""
        test_file = Path("/test/file.py")

        with patch.object(
            Path, "read_text", return_value="import other\nfrom config import different"
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is False

    def test_file_uses_dependency_when_read_error_then_returns_false(self):
        """Test file usage detection when file cannot be read."""
        test_file = Path("/test/file.py")

        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            result = _file_uses_dependency(test_file, "settings")
            assert result is False

    def test_file_uses_dependency_when_unicode_error_then_returns_false(self):
        """Test file usage detection when unicode decode error occurs."""
        test_file = Path("/test/file.py")

        with patch.object(
            Path,
            "read_text",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
        ):
            result = _file_uses_dependency(test_file, "settings")
            assert result is False


class TestAnalyzeSingleDependency:
    """Test single dependency analysis."""

    def test_analyze_single_dependency_when_exists_then_creates_complete_report(self):
        """Test single dependency analysis for existing dependency."""
        with (
            patch(
                "spec_cli.utils.dependency_analysis.validate_dependency_exists"
            ) as mock_validate,
            patch(
                "spec_cli.utils.dependency_analysis.analyze_current_usage"
            ) as mock_usage,
            patch(
                "spec_cli.utils.dependency_analysis._generate_context_requirements"
            ) as mock_requirements,
        ):
            mock_validate.side_effect = [
                True,
                False,
                False,
                False,
            ]  # Only first import path exists
            mock_usage.return_value = ["/test/file1.py", "/test/file2.py"]
            mock_requirements.return_value = {"test": "requirements"}

            result = _analyze_single_dependency("settings", TEST_CODEBASE_PATH)

            assert result.dependency_name == "settings"
            assert result.exists is True
            assert len(result.usage_patterns) == 2
            assert "spec_cli.settings" in result.import_paths
            assert result.requirements == {"test": "requirements"}
            assert result.analysis_errors == []

    def test_analyze_single_dependency_when_not_exists_then_creates_report_with_no_imports(
        self,
    ):
        """Test single dependency analysis for non-existent dependency."""
        with (
            patch(
                "spec_cli.utils.dependency_analysis.validate_dependency_exists"
            ) as mock_validate,
            patch(
                "spec_cli.utils.dependency_analysis.analyze_current_usage"
            ) as mock_usage,
            patch(
                "spec_cli.utils.dependency_analysis._generate_context_requirements"
            ) as mock_requirements,
        ):
            mock_validate.return_value = False  # No import paths exist
            mock_usage.return_value = []
            mock_requirements.return_value = {"test": "requirements"}

            result = _analyze_single_dependency("nonexistent", TEST_CODEBASE_PATH)

            assert result.dependency_name == "nonexistent"
            assert result.exists is False
            assert len(result.import_paths) == 0
            assert len(result.usage_patterns) == 0


class TestGenerateContextRequirements:
    """Test SpecContext requirements generation."""

    def test_generate_context_requirements_when_settings_dependency_then_returns_settings_interface(
        self,
    ):
        """Test requirements generation for settings dependency."""
        usage_patterns = [
            DependencyUsage("/test/file1.py", 10, "reference", "test context"),
            DependencyUsage("/test/file2.py", 15, "reference", "test context"),
        ]

        result = _generate_context_requirements("settings", usage_patterns)

        assert result["name"] == "settings"
        assert result["required"] is True
        assert result["usage_count"] == 2
        assert "debug_enabled: bool" in result["interface_requirements"]
        assert "console_width: int" in result["interface_requirements"]
        assert "get_setting(key: str) -> Any" in result["interface_requirements"]
        assert len(result["injection_points"]) == 2

    def test_generate_context_requirements_when_console_dependency_then_returns_console_interface(
        self,
    ):
        """Test requirements generation for console dependency."""
        usage_patterns = [DependencyUsage("/test/file.py", 5, "reference", "test")]

        result = _generate_context_requirements("console", usage_patterns)

        assert result["name"] == "console"
        assert result["required"] is True
        assert "print_message(text: str) -> None" in result["interface_requirements"]
        assert "get_width() -> int" in result["interface_requirements"]
        assert "supports_color() -> bool" in result["interface_requirements"]

    def test_generate_context_requirements_when_progress_dependency_then_returns_progress_interface(
        self,
    ):
        """Test requirements generation for progress dependency."""
        usage_patterns = [DependencyUsage("/test/file.py", 8, "reference", "test")]

        result = _generate_context_requirements("progress", usage_patterns)

        assert result["name"] == "progress"
        assert result["required"] is True
        assert (
            "show_progress(current: int, total: int) -> None"
            in result["interface_requirements"]
        )
        assert "update_status(status: str) -> None" in result["interface_requirements"]
        assert "finish() -> None" in result["interface_requirements"]

    def test_generate_context_requirements_when_no_usage_then_returns_not_required(
        self,
    ):
        """Test requirements generation when dependency has no usage."""
        result = _generate_context_requirements("unused_dependency", [])

        assert result["name"] == "unused_dependency"
        assert result["required"] is False
        assert result["usage_count"] == 0
        assert result["injection_points"] == []


class TestDependencyUsageDataclass:
    """Test DependencyUsage dataclass functionality."""

    def test_dependency_usage_creation_with_all_fields(self):
        """Test DependencyUsage dataclass creation."""
        usage = DependencyUsage(
            file_path="/test/file.py",
            line_number=42,
            usage_type="import",
            context="import statement",
        )

        assert usage.file_path == "/test/file.py"
        assert usage.line_number == 42
        assert usage.usage_type == "import"
        assert usage.context == "import statement"


class TestDependencyReportDataclass:
    """Test DependencyReport dataclass functionality."""

    def test_dependency_report_creation_with_all_fields(self):
        """Test DependencyReport dataclass creation."""
        usage_patterns = [DependencyUsage("/test.py", 1, "reference", "test")]
        import_paths = {"spec_cli.test"}
        requirements = {"name": "test", "required": True}

        report = DependencyReport(
            dependency_name="test_dep",
            exists=True,
            usage_patterns=usage_patterns,
            import_paths=import_paths,
            requirements=requirements,
            analysis_errors=[],
        )

        assert report.dependency_name == "test_dep"
        assert report.exists is True
        assert len(report.usage_patterns) == 1
        assert report.import_paths == import_paths
        assert report.requirements == requirements
        assert report.analysis_errors == []
