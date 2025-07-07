"""Unit tests for migration cleanup utilities."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import InfrastructureRemovalError
from spec_cli.utils.migration_cleanup_utils import (
    MigrationValidationReport,
    add_context_imports,
    cleanup_migration,
    remove_singleton_imports,
    validate_migration_complete,
)

# Test constants
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 4000
TEST_USER_ID = "test_123"
TEST_EMAIL = "test@example.com"
EXPECTED_SUCCESS_COUNT = 5
EXPECTED_ERROR_CODE = 400

# Test file content templates
SINGLETON_IMPORT_CODE = """

class TestClass:
    def __init__(self):
        pass
"""

CLEAN_CODE = """
from pathlib import Path
from typing import Any

class RegularClass:
    def __init__(self):
        pass
"""

CONTEXT_IMPORT_CODE = """
from pathlib import Path
from ..core.context import SpecContext

class TestClass:
    def __init__(self, context: SpecContext):
        self.context = context
"""

class TestRemoveSingletonImports:
    """Test remove_singleton_imports function."""

    def test_remove_singleton_imports_when_valid_file_then_removes_imports_successfully(
        self,
    ):
        """Test successful removal of singleton imports from valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(SINGLETON_IMPORT_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            result = remove_singleton_imports(file_path)

            assert result is True

            # Verify imports were removed
            content = file_path.read_text(encoding="utf-8")
            assert "from ..utils.singleton import" not in content
            assert "from spec_cli.utils.singleton import" not in content

        finally:
            file_path.unlink()

    def test_remove_singleton_imports_when_no_imports_found_then_returns_false_unchanged(
        self,
    ):
        """Test file with no singleton imports returns False and remains unchanged."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CLEAN_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            original_content = file_path.read_text(encoding="utf-8")
            result = remove_singleton_imports(file_path)

            assert result is False

            # Verify content unchanged
            new_content = file_path.read_text(encoding="utf-8")
            assert new_content == original_content

        finally:
            file_path.unlink()

    def test_remove_singleton_imports_when_file_not_found_then_raises_cleanup_error(
        self,
    ):
        """Test error handling when file does not exist."""
        non_existent_file = Path("/nonexistent/test.py")

        with pytest.raises(InfrastructureRemovalError) as exc_info:
            remove_singleton_imports(non_existent_file)

        assert "File not found" in str(exc_info.value)

    def test_remove_singleton_imports_when_invalid_path_type_then_raises_type_error(
        self,
    ):
        """Test type validation for file_path parameter."""
        with pytest.raises(TypeError) as exc_info:
            remove_singleton_imports("not_a_path")

        assert "file_path must be a Path object" in str(exc_info.value)

class TestAddContextImports:
    """Test add_context_imports function."""

    def test_add_context_imports_when_valid_file_then_adds_imports_successfully(self):
        """Test successful addition of context imports to valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CLEAN_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            imports_to_add = ["from ..core.context import SpecContext"]
            result = add_context_imports(file_path, imports_to_add)

            assert result is True

            # Verify imports were added
            content = file_path.read_text(encoding="utf-8")
            assert "from ..core.context import SpecContext" in content

        finally:
            file_path.unlink()

    def test_add_context_imports_when_import_already_exists_then_skips_duplicate(self):
        """Test that duplicate imports are not added."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CONTEXT_IMPORT_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            imports_to_add = ["from ..core.context import SpecContext"]
            result = add_context_imports(file_path, imports_to_add)

            assert result is False

            # Verify no duplicate imports added
            content = file_path.read_text(encoding="utf-8")
            import_count = content.count("from ..core.context import SpecContext")
            assert import_count == 1

        finally:
            file_path.unlink()

    def test_add_context_imports_when_empty_imports_list_then_returns_false(self):
        """Test behavior with empty imports list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(CLEAN_CODE)
            f.flush()
            file_path = Path(f.name)

        try:
            result = add_context_imports(file_path, [])

            assert result is False

        finally:
            file_path.unlink()

    def test_add_context_imports_when_invalid_types_then_raises_type_error(self):
        """Test type validation for parameters."""
        with pytest.raises(TypeError):
            add_context_imports("not_a_path", [])

        with pytest.raises(TypeError):
            add_context_imports(Path("test.py"), "not_a_list")

class TestValidateMigrationComplete:
    """Test validate_migration_complete function."""

    @patch("spec_cli.utils.migration_cleanup_utils.validate_no_references")
    @patch("spec_cli.utils.migration_cleanup_utils.SingletonPatternDetector")
    def test_validate_migration_complete_when_no_singletons_then_returns_success_report(
        self, mock_detector, mock_validate_refs
    ):
        """Test successful validation when no singleton patterns remain."""
        # Setup mocks
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance
        mock_validate_refs.return_value = []

        result = validate_migration_complete()

        assert isinstance(result, MigrationValidationReport)
        assert result.success is True
        assert len(result.singleton_violations) == 0
        assert len(result.errors) == 0
        assert result.files_processed > 0

    @patch("spec_cli.utils.migration_cleanup_utils.validate_no_references")
    @patch("spec_cli.utils.migration_cleanup_utils.SingletonPatternDetector")
    def test_validate_migration_complete_when_singletons_remain_then_returns_failure_report(
        self, mock_detector, mock_validate_refs
    ):
        """Test validation failure when singleton patterns remain."""
        # Setup mocks to indicate remaining singletons
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance
        mock_validate_refs.return_value = ["file1.py", "file2.py"]

        result = validate_migration_complete()

        assert isinstance(result, MigrationValidationReport)
        assert result.success is False
        assert len(result.errors) == 0

    @patch("spec_cli.utils.migration_cleanup_utils.validate_no_references")
    def test_validate_migration_complete_when_validation_fails_then_raises_error(
        self, mock_validate_refs
    ):
        """Test error handling when validation process fails."""
        mock_validate_refs.side_effect = Exception("Validation failed")

        with pytest.raises(InfrastructureRemovalError) as exc_info:
            validate_migration_complete()

        assert "Migration validation failed" in str(exc_info.value)

class TestCleanupMigration:
    """Test cleanup_migration function."""

    @patch("spec_cli.utils.migration_cleanup_utils.validate_migration_complete")
    @patch("spec_cli.utils.migration_cleanup_utils.add_context_imports")
    @patch("spec_cli.utils.migration_cleanup_utils.remove_singleton_imports")
    def test_cleanup_migration_when_all_files_processed_then_updates_imports_to_context(
        self, mock_remove, mock_add, mock_validate
    ):
        """Test successful migration cleanup of all files."""
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            test_file1 = temp_path / "test1.py"
            test_file2 = temp_path / "test2.py"
            test_file1.write_text(SINGLETON_IMPORT_CODE)
            test_file2.write_text(SINGLETON_IMPORT_CODE)

            # Mock functions
            mock_remove.return_value = True
            mock_add.return_value = True
            mock_validate.return_value = MigrationValidationReport(
                success=True,
                singleton_violations=[],
                files_processed=2,
                imports_removed=0,
                context_imports_added=0,
                errors=[],
            )

            result = cleanup_migration(temp_path)

            assert isinstance(result, MigrationValidationReport)
            assert result.success is True
            assert result.files_processed == 2
            assert result.imports_removed == 2
            assert result.context_imports_added == 2

    def test_cleanup_migration_when_invalid_path_type_then_raises_type_error(self):
        """Test type validation for codebase_path parameter."""
        with pytest.raises(TypeError) as exc_info:
            cleanup_migration("not_a_path")

        assert "codebase_path must be a Path object" in str(exc_info.value)

    @patch("spec_cli.utils.migration_cleanup_utils.validate_migration_complete")
    def test_cleanup_migration_when_validation_fails_then_includes_errors(
        self, mock_validate
    ):
        """Test error handling during migration cleanup."""
        mock_validate.side_effect = Exception("Validation error")

        with pytest.raises(InfrastructureRemovalError) as exc_info:
            cleanup_migration(Path("."))

        assert "Migration cleanup failed" in str(exc_info.value)

class TestMigrationValidationReport:
    """Test MigrationValidationReport dataclass."""

    def test_migration_validation_when_test_suite_passes_then_confirms_complete_migration(
        self,
    ):
        """Test migration validation report creation and attributes."""
        report = MigrationValidationReport(
            success=True,
            singleton_violations=[],
            files_processed=EXPECTED_SUCCESS_COUNT,
            imports_removed=10,
            context_imports_added=EXPECTED_SUCCESS_COUNT,
            errors=[],
        )

        assert report.success is True
        assert len(report.singleton_violations) == 0
        assert report.files_processed == EXPECTED_SUCCESS_COUNT
        assert report.imports_removed == 10
        assert report.context_imports_added == EXPECTED_SUCCESS_COUNT
        assert len(report.errors) == 0

    def test_migration_validation_when_errors_occur_then_reports_failure_details(self):
        """Test migration validation report with errors."""
        test_violations = ["violation1", "violation2"]
        test_errors = ["error1", "error2"]

        report = MigrationValidationReport(
            success=False,
            singleton_violations=test_violations,
            files_processed=3,
            imports_removed=1,
            context_imports_added=0,
            errors=test_errors,
        )

        assert report.success is False
        assert len(report.singleton_violations) == 2
        assert len(report.errors) == 2
        assert report.files_processed == 3

class TestCleanupOrchestration:
    """Test orchestration of cleanup and validation functions."""

    def test_cleanup_orchestration_when_cleanup_and_validation_then_generates_completion_report(
        self,
    ):
        """Test end-to-end orchestration of cleanup and validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file with singleton imports
            test_file = temp_path / "spec_cli" / "config" / "settings.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(SINGLETON_IMPORT_CODE)

            # Run cleanup
            result = cleanup_migration(temp_path)

            # Verify cleanup occurred
            assert isinstance(result, MigrationValidationReport)
            assert result.files_processed >= 1

            # Verify imports were processed
            content = test_file.read_text(encoding="utf-8")
            assert "from ..utils.singleton import" not in content
