"""Tests for cross-platform path utilities."""

from pathlib import Path

from spec_cli.file_system.path_utils import (
    convert_to_posix_style,
    ensure_specs_prefix,
    is_specs_path,
    normalize_path_separators,
    remove_specs_prefix,
)


class TestNormalizePathSeparators:
    """Test normalize_path_separators function."""

    def test_normalize_windows_separators(self) -> None:
        """Test normalization of Windows-style backslashes."""
        windows_path = "src\\models\\user.py"
        result = normalize_path_separators(windows_path)
        assert result == "src/models/user.py"

    def test_normalize_unix_separators(self) -> None:
        """Test that Unix-style paths remain unchanged."""
        unix_path = "src/models/user.py"
        result = normalize_path_separators(unix_path)
        assert result == "src/models/user.py"

    def test_normalize_mixed_separators(self) -> None:
        """Test normalization of mixed separator styles."""
        mixed_path = "src\\models/user.py"
        result = normalize_path_separators(mixed_path)
        assert result == "src/models/user.py"

    def test_normalize_path_object(self) -> None:
        """Test normalization with Path objects."""
        path_obj = Path("src") / "models" / "user.py"
        result = normalize_path_separators(path_obj)
        assert result == "src/models/user.py"

    def test_normalize_absolute_path(self) -> None:
        """Test normalization of absolute paths."""
        # Note: This test normalizes separators but keeps the path structure
        abs_path = "C:\\Users\\test\\project\\src\\models\\user.py"
        result = normalize_path_separators(abs_path)
        assert result == "C:/Users/test/project/src/models/user.py"

    def test_normalize_empty_path(self) -> None:
        """Test normalization of empty path."""
        result = normalize_path_separators("")
        assert result == ""

    def test_normalize_single_file(self) -> None:
        """Test normalization of single file name."""
        result = normalize_path_separators("user.py")
        assert result == "user.py"


class TestRemoveSpecsPrefix:
    """Test remove_specs_prefix function."""

    def test_remove_unix_specs_prefix(self) -> None:
        """Test removal of Unix-style .specs/ prefix."""
        path_with_prefix = ".specs/src/models/user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_windows_specs_prefix(self) -> None:
        """Test removal of Windows-style .specs\\ prefix."""
        path_with_prefix = ".specs\\src\\models\\user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_no_prefix(self) -> None:
        """Test handling of paths without .specs prefix."""
        path_without_prefix = "src/models/user.py"
        result = remove_specs_prefix(path_without_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_mixed_separators(self) -> None:
        """Test removal with mixed separators in remaining path."""
        path_with_prefix = ".specs/src\\models/user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_root_file(self) -> None:
        """Test removal when file is directly in .specs."""
        path_with_prefix = ".specs/README.md"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "README.md"

    def test_remove_specs_prefix_windows_root_file(self) -> None:
        """Test removal of Windows prefix for root file."""
        path_with_prefix = ".specs\\README.md"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "README.md"


class TestEnsureSpecsPrefix:
    """Test ensure_specs_prefix function."""

    def test_ensure_specs_prefix_adds_prefix(self) -> None:
        """Test adding .specs/ prefix to path without it."""
        path_without_prefix = "src/models/user.py"
        result = ensure_specs_prefix(path_without_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_keeps_existing(self) -> None:
        """Test that existing .specs/ prefix is preserved."""
        path_with_prefix = ".specs/src/models/user.py"
        result = ensure_specs_prefix(path_with_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_normalizes_windows(self) -> None:
        """Test that Windows .specs\\ prefix is normalized."""
        path_with_windows_prefix = ".specs\\src\\models\\user.py"
        result = ensure_specs_prefix(path_with_windows_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_with_path_object(self) -> None:
        """Test with Path object input."""
        path_obj = Path("src") / "models" / "user.py"
        result = ensure_specs_prefix(path_obj)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_root_file(self) -> None:
        """Test adding prefix to root file."""
        result = ensure_specs_prefix("README.md")
        assert result == ".specs/README.md"


class TestIsSpecsPath:
    """Test is_specs_path function."""

    def test_is_specs_path_unix_prefix(self) -> None:
        """Test detection of Unix-style .specs/ prefix."""
        specs_path = ".specs/src/models/user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_windows_prefix(self) -> None:
        """Test detection of Windows-style .specs\\ prefix."""
        specs_path = ".specs\\src\\models\\user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_no_prefix(self) -> None:
        """Test detection when no .specs prefix exists."""
        regular_path = "src/models/user.py"
        assert is_specs_path(regular_path) is False

    def test_is_specs_path_with_path_object(self) -> None:
        """Test detection with Path object."""
        specs_path = Path(".specs") / "src" / "models" / "user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_similar_name(self) -> None:
        """Test that similar but different names are not detected."""
        similar_paths = [
            "specs/src/models/user.py",  # Missing dot
            ".spec/src/models/user.py",  # Missing 's'
            "myspecs/src/models/user.py",  # Different name
        ]
        for path in similar_paths:
            assert is_specs_path(path) is False

    def test_is_specs_path_root_file(self) -> None:
        """Test detection for file directly in .specs."""
        specs_path = ".specs/README.md"
        assert is_specs_path(specs_path) is True


class TestConvertToPosixStyle:
    """Test convert_to_posix_style function (alias for normalize_path_separators)."""

    def test_convert_to_posix_style_basic(self) -> None:
        """Test basic conversion to POSIX style."""
        windows_path = "src\\models\\user.py"
        result = convert_to_posix_style(windows_path)
        assert result == "src/models/user.py"

    def test_convert_to_posix_style_with_path_object(self) -> None:
        """Test conversion with Path object."""
        path_obj = Path("src") / "models" / "user.py"
        result = convert_to_posix_style(path_obj)
        assert result == "src/models/user.py"


class TestCrossplatformBehavior:
    """Test cross-platform behavior patterns."""

    def test_round_trip_specs_operations(self) -> None:
        """Test that adding and removing .specs prefix works correctly."""
        original_paths = [
            "src/models/user.py",
            "src\\models\\user.py",
            "docs/README.md",
            "test.py",
        ]

        for original in original_paths:
            # Add prefix
            with_prefix = ensure_specs_prefix(original)
            # Remove prefix
            without_prefix = remove_specs_prefix(with_prefix)
            # Should match normalized original
            expected = normalize_path_separators(original)
            assert without_prefix == expected

    def test_consistent_separator_handling(self) -> None:
        """Test that all functions consistently use forward slashes."""
        windows_paths = [
            "src\\models\\user.py",
            ".specs\\src\\models\\user.py",
            "docs\\README.md",
        ]

        for path in windows_paths:
            # All functions should return paths with forward slashes
            assert "\\" not in normalize_path_separators(path)
            assert "\\" not in remove_specs_prefix(path)
            assert "\\" not in ensure_specs_prefix(path)
            assert "\\" not in convert_to_posix_style(path)

    def test_path_object_compatibility(self) -> None:
        """Test that all functions work with both strings and Path objects."""
        test_path = Path("src") / "models" / "user.py"

        # All functions should accept Path objects
        normalize_result = normalize_path_separators(test_path)
        prefix_result = ensure_specs_prefix(test_path)
        posix_result = convert_to_posix_style(test_path)
        is_specs_result = is_specs_path(test_path)

        # Results should be consistent
        assert normalize_result == "src/models/user.py"
        assert prefix_result == ".specs/src/models/user.py"
        assert posix_result == "src/models/user.py"
        assert is_specs_result is False
