"""Unit tests for path resolution functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.__main__ import ROOT, resolve_file_path


class TestResolveFilePath:
    """Test the resolve_file_path function."""

    def test_resolve_file_path_with_relative_path_returns_relative(self):
        """Test that resolve_file_path with relative path returns correct relative path."""
        # Create a test file in the project directory
        test_file = ROOT / "test_file.py"
        test_file.write_text("# test")

        try:
            result = resolve_file_path("test_file.py")

            # Result should be a Path object relative to project root
            assert isinstance(result, Path)
            assert not result.is_absolute()
            assert result == Path("test_file.py")
        finally:
            test_file.unlink()

    def test_resolve_file_path_with_absolute_path_returns_relative(self):
        """Test that resolve_file_path with absolute path returns relative path."""
        # Create a test file in the project directory
        test_file = ROOT / "test_absolute.py"
        test_file.write_text("# test")

        try:
            # Use absolute path
            result = resolve_file_path(str(test_file))

            # Result should be a Path object relative to project root
            assert isinstance(result, Path)
            assert not result.is_absolute()
            assert result == Path("test_absolute.py")
        finally:
            test_file.unlink()

    def test_resolve_file_path_with_nonexistent_file_raises_error(self):
        """Test that resolve_file_path with non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found:"):
            resolve_file_path("nonexistent_file.py")

    def test_resolve_file_path_with_directory_raises_error(self):
        """Test that resolve_file_path with directory raises IsADirectoryError."""
        # Create a test directory in the project
        test_dir = ROOT / "test_directory"
        test_dir.mkdir()

        try:
            with pytest.raises(
                IsADirectoryError, match="Path is a directory, not a file:"
            ):
                resolve_file_path("test_directory")
        finally:
            test_dir.rmdir()

    @patch("spec_cli.__main__.ROOT")
    def test_resolve_file_path_with_path_outside_project_raises_error(self, mock_root):
        """Test that resolve_file_path with path outside project root raises ValueError."""
        # Mock ROOT to be a subdirectory
        mock_root.__truediv__ = Path.__truediv__
        mock_root.return_value = Path("/fake/project/root")

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # This absolute path will be outside our mocked project root
            with pytest.raises(ValueError, match="Path is outside project root:"):
                resolve_file_path(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_resolve_file_path_handles_special_file_types(self):
        """Test that resolve_file_path handles different file types correctly."""
        # Test with a regular file (should work)
        test_file = ROOT / "test_file.txt"
        test_file.write_text("test content")

        try:
            result = resolve_file_path("test_file.txt")
            assert isinstance(result, Path)
            assert result == Path("test_file.txt")
        finally:
            test_file.unlink()

    def test_resolve_file_path_with_symlink_to_file(self):
        """Test that resolve_file_path works with symbolic links to files."""
        # Create a regular file in project
        test_file = ROOT / "test_target.py"
        test_file.write_text("# target")

        # Create symlink in project
        symlink_file = ROOT / "test_link.py"

        try:
            # Create symbolic link
            os.symlink(test_file, symlink_file)

            result = resolve_file_path("test_link.py")
            assert isinstance(result, Path)
        except OSError:
            # Skip test if symlinks aren't supported on this system
            pytest.skip("Symbolic links not supported")
        finally:
            if symlink_file.exists():
                symlink_file.unlink()
            test_file.unlink()

    def test_resolve_file_path_preserves_file_extension(self):
        """Test that resolve_file_path preserves the original file extension."""
        extensions = [".py", ".js", ".ts", ".md", ".txt"]

        for ext in extensions:
            test_file = ROOT / f"test_ext{ext}"
            test_file.write_text("test")

            try:
                result = resolve_file_path(f"test_ext{ext}")
                assert result.suffix == ext
            finally:
                test_file.unlink()
