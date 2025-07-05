"""Unit tests for GitPathConverter - Cross-Platform Path Conversion.

Test suite for git_003 slice: comprehensive cross-platform path conversion
testing for Git operations with .specs/ directory handling.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.git.path_converter import GitPathConverter


class TestGitPathConverterInitialization:
    """Test GitPathConverter initialization and basic setup."""

    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            converter = GitPathConverter(specs_dir)

            assert converter.specs_dir == specs_dir
            mock_logger.log.assert_called_once_with(
                "INFO", "GitPathConverter initialized", specs_dir=str(specs_dir)
            )

    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        converter = GitPathConverter(str(specs_dir))
        assert str(converter.specs_dir) == str(specs_dir)

    def test_init_nonexistent_directory(self, tmp_path):
        """Test initialization with non-existent specs directory."""
        specs_dir = tmp_path / ".specs"
        # Don't create the directory

        converter = GitPathConverter(specs_dir)
        assert converter.specs_dir == specs_dir


class TestConvertToGitPath:
    """Test convert_to_git_path method for various path scenarios."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_absolute_path_under_specs(self, converter, tmp_path):
        """Test absolute path that is under .specs/ directory."""
        specs_dir = tmp_path / ".specs"
        test_file = specs_dir / "src" / "main.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test file")

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_git_path(str(test_file))

            assert result == "src/main.py"
            mock_logger.log.assert_any_call(
                "DEBUG", "Converting path to Git context", input_path=str(test_file)
            )
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Converted absolute path",
                absolute=str(test_file),
                relative="src/main.py",
            )

    def test_absolute_path_outside_specs(self, converter, tmp_path):
        """Test absolute path that is outside .specs/ directory."""
        outside_file = tmp_path / "outside.py"
        outside_file.parent.mkdir(parents=True, exist_ok=True)
        outside_file.write_text("# outside file")

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_git_path(str(outside_file))

            assert result == str(outside_file)
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Absolute path not under .specs/, returning as-is",
                path=str(outside_file),
            )

    def test_specs_prefixed_path_unix_style(self, converter):
        """Test path with .specs/ prefix (Unix style)."""
        input_path = ".specs/src/models/user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_git_path(input_path)

            assert result == "src/models/user.py"
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Removed .specs prefix (cross-platform)",
                original=input_path,
                result="src/models/user.py",
            )

    def test_specs_prefixed_path_windows_style(self, converter):
        r"""Test path with .specs\ prefix (Windows style)."""
        input_path = r".specs\src\models\user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_git_path(input_path)

            assert result == "src/models/user.py"
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Removed .specs prefix (cross-platform)",
                original=input_path,
                result="src/models/user.py",
            )

    def test_relative_path_normalization(self, converter):
        """Test relative path gets normalized separators."""
        input_path = r"src\models\user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_git_path(input_path)

            assert result == "src/models/user.py"
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Path already relative, normalized separators",
                original=input_path,
                result="src/models/user.py",
            )

    def test_path_object_input(self, converter):
        """Test Path object as input."""
        input_path = Path("src") / "models" / "user.py"

        result = converter.convert_to_git_path(input_path)
        assert result == "src/models/user.py"

    def test_empty_path(self, converter):
        """Test empty path string."""
        result = converter.convert_to_git_path("")
        assert result == "."

    def test_root_specs_path(self, converter):
        """Test root .specs/ path."""
        result = converter.convert_to_git_path(".specs/")
        assert result == ""


class TestConvertFromGitPath:
    """Test convert_from_git_path method for Git to .specs/ conversion."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_git_path_to_specs_path(self, converter):
        """Test converting Git relative path to .specs/ prefixed path."""
        git_path = "src/models/user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_from_git_path(git_path)

            assert result == Path(".specs/src/models/user.py")
            mock_logger.log.assert_any_call(
                "DEBUG", "Converting from Git context", git_path=git_path
            )
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Converted from Git context",
                git_path=git_path,
                result=".specs/src/models/user.py",
            )

    def test_git_path_with_windows_separators(self, converter):
        """Test Git path with Windows separators gets normalized."""
        git_path = r"src\models\user.py"

        result = converter.convert_from_git_path(git_path)
        assert result == Path(".specs/src/models/user.py")

    def test_already_specs_prefixed_path(self, converter):
        """Test path that already has .specs/ prefix."""
        git_path = ".specs/src/models/user.py"

        result = converter.convert_from_git_path(git_path)
        assert result == Path(".specs/src/models/user.py")

    def test_path_object_input(self, converter):
        """Test Path object as input."""
        git_path = Path("src") / "models" / "user.py"

        result = converter.convert_from_git_path(git_path)
        assert result == Path(".specs/src/models/user.py")

    def test_empty_git_path(self, converter):
        """Test empty Git path."""
        result = converter.convert_from_git_path("")
        assert result == Path(".specs/")

    def test_root_git_path(self, converter):
        """Test root Git path (single dot)."""
        result = converter.convert_from_git_path(".")
        assert result == Path(".specs/.")


class TestConvertToAbsoluteSpecsPath:
    """Test convert_to_absolute_specs_path method."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_relative_path_to_absolute(self, converter, tmp_path):
        """Test converting relative path to absolute under .specs/."""
        input_path = "src/main.py"
        specs_dir = tmp_path / ".specs"
        expected = specs_dir / "src" / "main.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.convert_to_absolute_specs_path(input_path)

            assert result == expected
            mock_logger.log.assert_any_call(
                "DEBUG", "Converting to absolute .specs/ path", input_path=input_path
            )
            mock_logger.log.assert_any_call(
                "DEBUG",
                "Converted to absolute .specs/ path",
                input_path=input_path,
                git_path="src/main.py",
                absolute=str(expected),
            )

    def test_specs_prefixed_path_to_absolute(self, converter, tmp_path):
        """Test converting .specs/ prefixed path to absolute."""
        input_path = ".specs/src/main.py"
        specs_dir = tmp_path / ".specs"
        expected = specs_dir / "src" / "main.py"

        result = converter.convert_to_absolute_specs_path(input_path)
        assert result == expected

    def test_absolute_path_under_specs(self, converter, tmp_path):
        """Test absolute path already under .specs/."""
        specs_dir = tmp_path / ".specs"
        input_path = specs_dir / "src" / "main.py"

        result = converter.convert_to_absolute_specs_path(str(input_path))
        assert result == input_path

    def test_path_object_input(self, converter, tmp_path):
        """Test Path object as input."""
        input_path = Path("src") / "main.py"
        specs_dir = tmp_path / ".specs"
        expected = specs_dir / "src" / "main.py"

        result = converter.convert_to_absolute_specs_path(input_path)
        assert result == expected


class TestIsUnderSpecsDir:
    """Test is_under_specs_dir method."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_absolute_path_under_specs(self, converter, tmp_path):
        """Test absolute path under .specs/ directory."""
        specs_dir = tmp_path / ".specs"
        test_file = specs_dir / "src" / "main.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.is_under_specs_dir(str(test_file))

            assert result is True
            mock_logger.log.assert_called_with(
                "DEBUG", "Path is under .specs/ directory", path=str(test_file)
            )

    def test_absolute_path_outside_specs(self, converter, tmp_path):
        """Test absolute path outside .specs/ directory."""
        outside_file = tmp_path / "outside.py"
        outside_file.parent.mkdir(parents=True, exist_ok=True)
        outside_file.write_text("# outside")

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.is_under_specs_dir(str(outside_file))

            assert result is False
            mock_logger.log.assert_called_with(
                "DEBUG", "Path is not under .specs/ directory", path=str(outside_file)
            )

    def test_relative_path_under_specs(self, converter):
        """Test relative path that would be under .specs/."""
        result = converter.is_under_specs_dir("src/main.py")
        assert result is True

    def test_relative_path_parent_traversal(self, converter):
        """Test relative path with parent directory traversal."""
        result = converter.is_under_specs_dir("../outside.py")
        assert result is False

    def test_path_object_input(self, converter, tmp_path):
        """Test Path object as input."""
        specs_dir = tmp_path / ".specs"
        test_file = specs_dir / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        result = converter.is_under_specs_dir(test_file)
        assert result is True


class TestNormalizePathSeparators:
    """Test normalize_path_separators method."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_windows_separators_to_forward(self, converter):
        """Test Windows backslash separators converted to forward slashes."""
        input_path = r"src\models\user.py"
        expected = "src/models/user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.normalize_path_separators(input_path)

            assert result == expected
            mock_logger.log.assert_called_once_with(
                "DEBUG",
                "Normalized path separators",
                original=input_path,
                normalized=expected,
            )

    def test_unix_separators_unchanged(self, converter):
        """Test Unix forward slashes remain unchanged."""
        input_path = "src/models/user.py"

        result = converter.normalize_path_separators(input_path)
        assert result == input_path

    def test_mixed_separators_normalized(self, converter):
        """Test mixed separators get normalized."""
        input_path = r"src/models\user.py"
        expected = "src/models/user.py"

        result = converter.normalize_path_separators(input_path)
        assert result == expected

    def test_path_object_input(self, converter):
        """Test Path object as input."""
        input_path = Path("src") / "models" / "user.py"

        result = converter.normalize_path_separators(input_path)
        # Path objects use platform separators, but should be normalized
        assert "/" in result
        assert "src" in result and "models" in result and "user.py" in result


class TestGetConversionInfo:
    """Test get_conversion_info method for comprehensive path analysis."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_relative_path_conversion_info(self, converter):
        """Test conversion info for relative path."""
        input_path = "src/models/user.py"

        with patch("spec_cli.git.path_converter.debug_logger") as mock_logger:
            result = converter.get_conversion_info(input_path)

            expected_keys = {
                "original_path",
                "is_absolute",
                "has_specs_prefix",
                "is_under_specs_dir",
                "git_path",
                "specs_prefixed_path",
                "absolute_specs_path",
                "normalized_separators",
            }
            assert set(result.keys()) == expected_keys

            assert result["original_path"] == input_path
            assert result["is_absolute"] is False
            assert result["has_specs_prefix"] is False
            assert result["is_under_specs_dir"] is True
            assert result["git_path"] == "src/models/user.py"
            assert result["specs_prefixed_path"] == ".specs/src/models/user.py"
            assert result["normalized_separators"] == "src/models/user.py"

            mock_logger.log.assert_called_with(
                "DEBUG",
                "Path conversion info generated",
                original=input_path,
                conversions=len(result),
            )

    def test_specs_prefixed_path_conversion_info(self, converter):
        """Test conversion info for .specs/ prefixed path."""
        input_path = ".specs/src/models/user.py"

        result = converter.get_conversion_info(input_path)

        assert result["original_path"] == input_path
        assert result["is_absolute"] is False
        assert result["has_specs_prefix"] is True
        assert result["git_path"] == "src/models/user.py"
        assert result["specs_prefixed_path"] == ".specs/src/models/user.py"

    def test_absolute_path_conversion_info(self, converter, tmp_path):
        """Test conversion info for absolute path."""
        specs_dir = tmp_path / ".specs"
        test_file = specs_dir / "src" / "main.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        result = converter.get_conversion_info(str(test_file))

        assert result["original_path"] == str(test_file)
        assert result["is_absolute"] is True
        assert result["has_specs_prefix"] is False
        assert result["is_under_specs_dir"] is True
        assert result["git_path"] == "src/main.py"

    def test_windows_style_path_conversion_info(self, converter):
        """Test conversion info for Windows-style path."""
        input_path = r".specs\src\models\user.py"

        result = converter.get_conversion_info(input_path)

        assert result["original_path"] == input_path
        assert result["has_specs_prefix"] is True
        assert result["git_path"] == "src/models/user.py"
        assert result["normalized_separators"] == ".specs/src/models/user.py"

    def test_path_object_conversion_info(self, converter):
        """Test conversion info for Path object input."""
        input_path = Path(".specs") / "src" / "models" / "user.py"

        result = converter.get_conversion_info(input_path)

        assert result["original_path"] == str(input_path)
        assert result["has_specs_prefix"] is True
        assert result["git_path"] == "src/models/user.py"


class TestCrossPlatformBehavior:
    """Test cross-platform behavior and edge cases."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_mixed_separator_styles(self, converter):
        """Test handling of mixed separator styles in paths."""
        input_paths = [
            r"src\models/user.py",
            r"src/models\user.py",
            r".specs\src/models\user.py",
        ]

        for input_path in input_paths:
            result = converter.convert_to_git_path(input_path)
            # All should normalize to forward slashes
            assert result == "src/models/user.py"

    def test_relative_path_edge_cases(self, converter):
        """Test edge cases with relative paths."""
        test_cases = [
            (".", "."),
            ("./src/main.py", "src/main.py"),  # Path normalization removes "./"
            ("../outside.py", "../outside.py"),
            ("", "."),  # Empty path becomes "."
        ]

        for input_path, expected in test_cases:
            result = converter.convert_to_git_path(input_path)
            # Normalize separators in expected
            expected_normalized = expected.replace("\\", "/")
            assert result == expected_normalized

    def test_specs_prefix_variations(self, converter):
        """Test various .specs prefix variations."""
        test_cases = [
            ".specs/src/main.py",
            r".specs\src\main.py",
            ".specs/",
            ".specs\\",  # Windows style .specs\ prefix
        ]

        expected_results = [
            "src/main.py",
            "src/main.py",
            "",  # Path(".specs/") becomes "" after removing prefix
            "",  # Same for Windows style
        ]

        for input_path, expected in zip(test_cases, expected_results, strict=False):
            result = converter.convert_to_git_path(input_path)
            assert result == expected

    @pytest.mark.parametrize(
        "path_input",
        [
            "regular/path.py",
            Path("regular/path.py"),
            r"regular\path.py",
            Path("regular") / "path.py",
        ],
    )
    def test_input_type_handling(self, converter, path_input):
        """Test various input types (string, Path, mixed separators)."""
        result = converter.convert_to_git_path(path_input)
        assert result == "regular/path.py"

    def test_performance_with_deep_paths(self, converter):
        """Test performance and correctness with deeply nested paths."""
        deep_path = "/".join([f"level{i}" for i in range(20)]) + "/file.py"
        specs_prefixed = f".specs/{deep_path}"

        result = converter.convert_to_git_path(specs_prefixed)
        assert result == deep_path

        # Test round-trip conversion
        back_to_specs = converter.convert_from_git_path(result)
        assert str(back_to_specs) == specs_prefixed


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_safe_relative_to_error_handling(self, converter, tmp_path):
        """Test error handling when safe_relative_to fails."""
        outside_path = tmp_path / "outside" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.write_text("# outside")

        # This should not raise an exception, should return path as-is
        result = converter.convert_to_git_path(str(outside_path))
        assert result == str(outside_path)

    def test_none_input_handling(self, converter):
        """Test handling of None input (should not occur in practice)."""
        with pytest.raises(TypeError):
            converter.convert_to_git_path(None)

    def test_numeric_input_handling(self, converter):
        """Test handling of numeric input (should raise TypeError)."""
        with pytest.raises(TypeError):
            converter.convert_to_git_path(123)

    def test_empty_specs_dir_handling(self, tmp_path):
        """Test behavior with empty/non-existent specs directory."""
        non_existent_specs = tmp_path / "nonexistent" / ".specs"
        converter = GitPathConverter(non_existent_specs)

        # Should still work for relative paths
        result = converter.convert_to_git_path("src/main.py")
        assert result == "src/main.py"


class TestIntegrationWithUtilities:
    """Test integration with path utilities from path_utils module."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create GitPathConverter with temporary specs directory."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        return GitPathConverter(specs_dir)

    def test_integration_with_normalize_path_separators(self, converter):
        """Test integration with normalize_path_separators utility."""
        input_path = r"src\models\user.py"

        # Both should produce same result
        converter_result = converter.normalize_path_separators(input_path)

        from spec_cli.utils.path_utils import normalize_path_separators

        utility_result = normalize_path_separators(input_path)

        assert converter_result == utility_result == "src/models/user.py"

    def test_integration_with_remove_specs_prefix(self, converter):
        """Test integration with remove_specs_prefix utility."""
        input_path = r".specs\src\models\user.py"

        converter_result = converter.convert_to_git_path(input_path)

        from spec_cli.utils.path_utils import remove_specs_prefix

        utility_result = remove_specs_prefix(input_path)

        assert converter_result == utility_result == "src/models/user.py"

    def test_integration_with_safe_relative_to(self, converter, tmp_path):
        """Test integration with safe_relative_to utility."""
        specs_dir = tmp_path / ".specs"
        test_file = specs_dir / "src" / "main.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        # Converter should use safe_relative_to internally
        result = converter.convert_to_git_path(str(test_file))
        assert result == "src/main.py"

        # Direct utility should give same relative path
        from spec_cli.utils.path_utils import safe_relative_to

        direct_result = safe_relative_to(test_file, specs_dir)
        assert str(direct_result) == result
