"""Unit tests for directory creation functionality."""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.__main__ import SPECS_DIR, create_spec_directory


class TestCreateSpecDirectory:
    """Test the create_spec_directory function."""

    def test_create_spec_directory_creates_nested_structure(self):
        """Test that create_spec_directory creates nested directory structure."""
        # Test with nested path
        file_path = Path("src/models/user.py")

        try:
            result = create_spec_directory(file_path)

            # Check that directory was created
            expected_path = SPECS_DIR / "src" / "models" / "user"
            assert result == expected_path
            assert result.exists()
            assert result.is_dir()

            # Check that intermediate directories were created
            assert (SPECS_DIR / "src").exists()
            assert (SPECS_DIR / "src" / "models").exists()

        finally:
            # Clean up - remove the entire src directory
            if (SPECS_DIR / "src").exists():
                shutil.rmtree(SPECS_DIR / "src")

    def test_create_spec_directory_handles_existing_directory(self):
        """Test that create_spec_directory handles existing directories gracefully."""
        file_path = Path("existing_test.py")

        # Create the directory first
        spec_dir = SPECS_DIR / "existing_test"
        spec_dir.mkdir(parents=True, exist_ok=True)

        try:
            # This should not raise an error
            result = create_spec_directory(file_path)

            assert result == spec_dir
            assert result.exists()
            assert result.is_dir()

        finally:
            # Clean up
            if spec_dir.exists():
                spec_dir.rmdir()

    def test_create_spec_directory_returns_correct_path(self):
        """Test that create_spec_directory returns the correct path structure."""
        test_cases = [
            ("simple.py", SPECS_DIR / "simple"),
            ("src/main.py", SPECS_DIR / "src" / "main"),
            (
                "deep/nested/path/file.js",
                SPECS_DIR / "deep" / "nested" / "path" / "file",
            ),
            ("file_with_dots.test.py", SPECS_DIR / "file_with_dots.test"),
        ]

        for file_path_str, expected_path in test_cases:
            file_path = Path(file_path_str)

            try:
                result = create_spec_directory(file_path)

                assert result == expected_path
                assert result.exists()
                assert result.is_dir()

            finally:
                # Clean up - remove the top-level directory created
                top_level = SPECS_DIR / file_path.parts[0]
                if top_level.exists() and top_level != SPECS_DIR:
                    shutil.rmtree(top_level)

    def test_create_spec_directory_handles_file_in_root(self):
        """Test that create_spec_directory handles files in project root correctly."""
        file_path = Path("root_file.py")

        try:
            result = create_spec_directory(file_path)

            # Should create directory directly in .specs/
            expected_path = SPECS_DIR / "root_file"
            assert result == expected_path
            assert result.exists()
            assert result.is_dir()

        finally:
            # Clean up
            if (SPECS_DIR / "root_file").exists():
                (SPECS_DIR / "root_file").rmdir()

    @patch("spec_cli.__main__.DEBUG", True)
    def test_create_spec_directory_debug_output(self, capsys):
        """Test that create_spec_directory produces debug output when DEBUG is True."""
        file_path = Path("debug_test.py")

        try:
            create_spec_directory(file_path)

            captured = capsys.readouterr()
            assert "🔍 Debug: Created spec directory:" in captured.out
            assert "debug_test" in captured.out

        finally:
            # Clean up
            if (SPECS_DIR / "debug_test").exists():
                (SPECS_DIR / "debug_test").rmdir()

    @patch("spec_cli.__main__.DEBUG", False)
    def test_create_spec_directory_no_debug_output(self, capsys):
        """Test that create_spec_directory produces no debug output when DEBUG is False."""
        file_path = Path("no_debug_test.py")

        try:
            create_spec_directory(file_path)

            captured = capsys.readouterr()
            assert "🔍 Debug:" not in captured.out

        finally:
            # Clean up
            if (SPECS_DIR / "no_debug_test").exists():
                (SPECS_DIR / "no_debug_test").rmdir()

    def test_create_spec_directory_preserves_directory_structure(self):
        """Test that directory structure matches source file structure."""
        # Create multiple nested files to test structure preservation
        test_files = [
            "api/handlers/user.py",
            "api/handlers/auth.py",
            "api/models/user.py",
            "frontend/components/button.tsx",
        ]

        created_dirs = []

        try:
            for file_path_str in test_files:
                file_path = Path(file_path_str)
                result = create_spec_directory(file_path)
                created_dirs.append(result)

                # Verify the structure matches
                expected = SPECS_DIR / file_path.parent / file_path.stem
                assert result == expected
                assert result.exists()

            # Verify the full directory structure exists
            assert (SPECS_DIR / "api" / "handlers").exists()
            assert (SPECS_DIR / "api" / "models").exists()
            assert (SPECS_DIR / "frontend" / "components").exists()

        finally:
            # Clean up top-level directories
            for top_dir in ["api", "frontend"]:
                top_path = SPECS_DIR / top_dir
                if top_path.exists():
                    shutil.rmtree(top_path)

    @patch("spec_cli.__main__.SPECS_DIR")
    def test_create_spec_directory_handles_permission_error(self, mock_specs_dir):
        """Test that create_spec_directory handles permission errors properly."""
        # Mock SPECS_DIR to raise a permission error
        mock_path = Mock()
        mock_path.__truediv__ = Mock(return_value=mock_path)
        mock_path.mkdir.side_effect = PermissionError("Permission denied")
        mock_specs_dir.__truediv__ = Mock(return_value=mock_path)

        file_path = Path("permission_test.py")

        with pytest.raises(
            OSError, match="Failed to create spec directory.*Permission denied"
        ):
            create_spec_directory(file_path)
