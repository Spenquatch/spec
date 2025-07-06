"""Unit tests for cleanup_utils module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import InfrastructureRemovalError
from spec_cli.utils.cleanup_utils import (
    cleanup_compatibility_layer,
    cleanup_singleton_infrastructure,
    safe_file_removal,
    validate_no_references,
)

# Test constants
TEST_FILE_CONTENT = "test content"
SAMPLE_PYTHON_CODE = '''
import os

from ..core.compatibility import CompatibilityLayer

def test_function():
    pass
'''
CLEAN_PYTHON_CODE = '''
import os
from pathlib import Path

def test_function():
    pass
'''

class TestSafeFileRemoval:
    """Test safe_file_removal function."""

    def test_safe_file_removal_when_file_exists_then_removes_successfully(self):
        """Test successful file removal when file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_file.txt"
            test_file.write_text(TEST_FILE_CONTENT)

            assert test_file.exists()
            result = safe_file_removal(test_file)

            assert result is True
            assert not test_file.exists()

    def test_safe_file_removal_when_file_missing_then_handles_gracefully(self):
        """Test graceful handling when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_file = Path(temp_dir) / "non_existent.txt"

            result = safe_file_removal(non_existent_file)

            assert result is False

    def test_safe_file_removal_when_path_is_directory_then_raises_error(self):
        """Test error when trying to remove a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_directory"
            test_dir.mkdir()

            with pytest.raises(InfrastructureRemovalError) as exc_info:
                safe_file_removal(test_dir)

            assert "not a file" in str(exc_info.value)

    def test_safe_file_removal_when_invalid_path_type_then_raises_type_error(self):
        """Test TypeError when path is not a Path object."""
        with pytest.raises(TypeError) as exc_info:
            safe_file_removal("not_a_path_object")  # type: ignore

        assert "must be a Path object" in str(exc_info.value)

    @patch("pathlib.Path.unlink")
    def test_safe_file_removal_when_permission_error_then_raises_infrastructure_error(
        self, mock_unlink
    ):
        """Test InfrastructureRemovalError when file removal fails."""
        mock_unlink.side_effect = PermissionError("Permission denied")

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_file.txt"
            test_file.write_text(TEST_FILE_CONTENT)

            with pytest.raises(InfrastructureRemovalError) as exc_info:
                safe_file_removal(test_file)

            assert "Failed to remove file" in str(exc_info.value)

class TestValidateNoReferences:
    """Test validate_no_references function."""

    def test_validate_no_references_when_clean_codebase_then_returns_empty_list(self):
        """Test empty result when no references found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create clean Python file
            test_file = Path(temp_dir) / "clean_file.py"
            test_file.write_text(CLEAN_PYTHON_CODE)

            violations = validate_no_references(
                Path(temp_dir), ["singleton", "compatibility"]
            )

            assert violations == []

    def test_validate_no_references_when_references_found_then_returns_violation_list(self):
        """Test violations returned when references found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with singleton references
            violating_file = Path(temp_dir) / "violating_file.py"
            violating_file.write_text(SAMPLE_PYTHON_CODE)

            violations = validate_no_references(
                Path(temp_dir), ["singleton", "compatibility"]
            )

            assert len(violations) == 1
            assert str(violating_file) in violations

    def test_validate_no_references_when_invalid_path_type_then_raises_type_error(self):
        """Test TypeError when codebase_path is not a Path object."""
        with pytest.raises(TypeError) as exc_info:
            validate_no_references("not_a_path", ["singleton"])  # type: ignore

        assert "must be a Path object" in str(exc_info.value)

    def test_validate_no_references_when_invalid_modules_type_then_raises_type_error(self):
        """Test TypeError when removed_modules is not a list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(TypeError) as exc_info:
                validate_no_references(Path(temp_dir), "not_a_list")  # type: ignore

            assert "must be a list" in str(exc_info.value)

    def test_validate_no_references_when_unicode_decode_error_then_skips_file(self):
        """Test graceful handling of non-text files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create binary file
            binary_file = Path(temp_dir) / "binary_file.py"
            binary_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8

            # Should not raise exception
            violations = validate_no_references(
                Path(temp_dir), ["singleton"]
            )

            assert violations == []  # Binary file should be skipped

    def test_validate_no_references_when_multiple_patterns_then_detects_all(self):
        """Test detection of multiple reference patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with multiple reference types
            multi_ref_code = '''

            import spec_cli.core.compatibility

            CompatibilityLayer = None
            '''
            ref_file = Path(temp_dir) / "multi_ref.py"
            ref_file.write_text(multi_ref_code)

            violations = validate_no_references(
                Path(temp_dir), ["singleton", "compatibility"]
            )

            assert len(violations) == 1
            assert str(ref_file) in violations

class TestCleanupSingletonInfrastructure:
    """Test cleanup_singleton_infrastructure function."""

    def test_cleanup_singleton_infrastructure_when_removal_complete_then_no_singleton_files(self):
        """Test complete removal of singleton infrastructure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock singleton file structure
            spec_cli_dir = Path(temp_dir) / "spec_cli" / "utils"
            spec_cli_dir.mkdir(parents=True)
            singleton_file = spec_cli_dir / "singleton.py"
            singleton_file.write_text("# Singleton implementation")

            removed_files = cleanup_singleton_infrastructure(Path(temp_dir))

            assert len(removed_files) == 1
            assert str(singleton_file) in removed_files
            assert not singleton_file.exists()

    def test_cleanup_singleton_infrastructure_when_files_missing_then_empty_result(self):
        """Test handling when singleton files don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory structure without singleton files
            spec_cli_dir = Path(temp_dir) / "spec_cli" / "utils"
            spec_cli_dir.mkdir(parents=True)

            removed_files = cleanup_singleton_infrastructure(Path(temp_dir))

            assert removed_files == []

    @patch("spec_cli.utils.cleanup_utils.safe_file_removal")
    def test_cleanup_singleton_infrastructure_when_errors_occur_then_raises_infrastructure_removal_error(
        self, mock_safe_removal
    ):
        """Test error handling during singleton infrastructure cleanup."""
        mock_safe_removal.side_effect = Exception("Mock removal error")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(InfrastructureRemovalError) as exc_info:
                cleanup_singleton_infrastructure(Path(temp_dir))

            assert "Singleton infrastructure cleanup failed" in str(exc_info.value)

class TestCleanupCompatibilityLayer:
    """Test cleanup_compatibility_layer function."""

    def test_cleanup_compatibility_layer_when_removal_complete_then_no_compatibility_files(self):
        """Test complete removal of compatibility layer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock compatibility file structure
            spec_cli_dir = Path(temp_dir) / "spec_cli" / "core"
            spec_cli_dir.mkdir(parents=True)
            compatibility_file = spec_cli_dir / "compatibility.py"
            compatibility_file.write_text("# Compatibility layer")

            removed_files = cleanup_compatibility_layer(Path(temp_dir))

            assert len(removed_files) == 1
            assert str(compatibility_file) in removed_files
            assert not compatibility_file.exists()

    def test_cleanup_compatibility_layer_when_files_missing_then_empty_result(self):
        """Test handling when compatibility files don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory structure without compatibility files
            spec_cli_dir = Path(temp_dir) / "spec_cli" / "core"
            spec_cli_dir.mkdir(parents=True)

            removed_files = cleanup_compatibility_layer(Path(temp_dir))

            assert removed_files == []

    @patch("spec_cli.utils.cleanup_utils.safe_file_removal")
    def test_cleanup_compatibility_layer_when_errors_occur_then_raises_infrastructure_removal_error(
        self, mock_safe_removal
    ):
        """Test error handling during compatibility layer cleanup."""
        mock_safe_removal.side_effect = Exception("Mock removal error")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(InfrastructureRemovalError) as exc_info:
                cleanup_compatibility_layer(Path(temp_dir))

            assert "Compatibility layer cleanup failed" in str(exc_info.value)

class TestCleanupUtilsIntegration:
    """Integration tests for cleanup utilities."""

    def test_complete_cleanup_workflow_then_infrastructure_removed_successfully(self):
        """Test complete cleanup workflow with both singleton and compatibility removal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create complete file structure
            singleton_dir = Path(temp_dir) / "spec_cli" / "utils"
            singleton_dir.mkdir(parents=True)
            singleton_file = singleton_dir / "singleton.py"
            singleton_file.write_text("# Singleton implementation")

            compatibility_dir = Path(temp_dir) / "spec_cli" / "core"
            compatibility_dir.mkdir(parents=True)
            compatibility_file = compatibility_dir / "compatibility.py"
            compatibility_file.write_text("# Compatibility layer")

            # Perform cleanup
            singleton_removed = cleanup_singleton_infrastructure(Path(temp_dir))
            compatibility_removed = cleanup_compatibility_layer(Path(temp_dir))

            # Validate results
            assert len(singleton_removed) == 1
            assert len(compatibility_removed) == 1
            assert not singleton_file.exists()
            assert not compatibility_file.exists()

            # Validate no references remain
            violations = validate_no_references(
                Path(temp_dir), ["singleton", "compatibility"]
            )
            assert violations == []

    def test_cleanup_with_reference_validation_then_detects_remaining_references(self):
        """Test cleanup followed by reference validation detects remaining usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create singleton file
            singleton_dir = Path(temp_dir) / "spec_cli" / "utils"
            singleton_dir.mkdir(parents=True)
            singleton_file = singleton_dir / "singleton.py"
            singleton_file.write_text("# Singleton implementation")

            # Create file with references
            ref_file = Path(temp_dir) / "test_file.py"
            ref_file.write_text(SAMPLE_PYTHON_CODE)

            # Remove singleton infrastructure
            removed_files = cleanup_singleton_infrastructure(Path(temp_dir))
            assert len(removed_files) == 1

            # Validate references remain in other files
            violations = validate_no_references(
                Path(temp_dir), ["singleton", "compatibility"]
            )
            assert len(violations) == 1
            assert str(ref_file) in violations

