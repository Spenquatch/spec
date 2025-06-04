from pathlib import Path

import pytest

from spec_cli.git.path_converter import GitPathConverter


class TestGitPathConverter:
    """Tests for GitPathConverter class."""

    @pytest.fixture
    def converter(self, tmp_path: Path) -> GitPathConverter:
        """Create GitPathConverter instance for testing."""
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir(exist_ok=True)
        return GitPathConverter(specs_dir)

    def test_path_converter_initialization(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test GitPathConverter initializes with correct specs directory."""
        assert converter.specs_dir == tmp_path / ".specs"

    def test_path_converter_converts_absolute_paths(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test conversion of absolute paths under .specs/ directory."""
        # Create absolute path under .specs/
        absolute_path = tmp_path / ".specs" / "src" / "main.py"

        result = converter.convert_to_git_path(absolute_path)

        assert result == "src/main.py"

    def test_path_converter_handles_absolute_paths_outside_specs(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test handling of absolute paths not under .specs/ directory."""
        # Create absolute path outside .specs/
        absolute_path = tmp_path / "other" / "file.py"

        result = converter.convert_to_git_path(absolute_path)

        # Should return path as-is when not under .specs/
        assert result == str(absolute_path)

    def test_path_converter_removes_specs_prefix(
        self, converter: GitPathConverter
    ) -> None:
        """Test removal of .specs/ prefix from paths."""
        test_cases = [
            (".specs/src/main.py", "src/main.py"),
            (".specs/docs/README.md", "docs/README.md"),
            (".specs/test.txt", "test.txt"),
        ]

        for input_path, expected in test_cases:
            result = converter.convert_to_git_path(input_path)
            assert result == expected

    def test_path_converter_handles_windows_separators(
        self, converter: GitPathConverter
    ) -> None:
        """Test handling of Windows-style path separators."""
        test_cases = [
            (".specs\\src\\main.py", "src/main.py"),
            (".specs\\docs\\README.md", "docs/README.md"),
            ("src\\utils\\helper.py", "src/utils/helper.py"),
        ]

        for input_path, expected in test_cases:
            result = converter.convert_to_git_path(input_path)
            assert result == expected

    def test_path_converter_handles_relative_paths(
        self, converter: GitPathConverter
    ) -> None:
        """Test handling of relative paths."""
        test_cases = [
            ("src/main.py", "src/main.py"),
            ("docs/README.md", "docs/README.md"),
            ("test.txt", "test.txt"),
        ]

        for input_path, expected in test_cases:
            result = converter.convert_to_git_path(input_path)
            assert result == expected

    def test_path_converter_converts_from_git_context(
        self, converter: GitPathConverter
    ) -> None:
        """Test conversion from Git work tree context to .specs/ prefixed paths."""
        test_cases = [
            ("src/main.py", Path(".specs/src/main.py")),
            ("docs/README.md", Path(".specs/docs/README.md")),
            ("test.txt", Path(".specs/test.txt")),
        ]

        for git_path, expected in test_cases:
            result = converter.convert_from_git_path(git_path)
            assert result == expected

    def test_path_converter_handles_already_prefixed_from_git(
        self, converter: GitPathConverter
    ) -> None:
        """Test handling of paths that already have .specs/ prefix in from_git conversion."""
        input_path = ".specs/src/main.py"
        result = converter.convert_from_git_path(input_path)

        assert result == Path(".specs/src/main.py")

    def test_path_converter_creates_absolute_specs_paths(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test creation of absolute paths under .specs/ directory."""
        test_cases = [
            "src/main.py",
            ".specs/src/main.py",
            "docs/README.md",
        ]

        for input_path in test_cases:
            result = converter.convert_to_absolute_specs_path(input_path)

            # Should be absolute path
            assert result.is_absolute()

            # Should be under .specs/ directory
            assert str(result).startswith(str(tmp_path / ".specs"))

            # Should end with correct relative path (normalize for cross-platform comparison)
            expected_suffix = converter.convert_to_git_path(input_path)
            result_str = str(result).replace(
                "\\", "/"
            )  # Normalize separators for comparison
            assert result_str.endswith(expected_suffix)

    def test_path_converter_detects_paths_under_specs_dir(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test detection of paths under .specs/ directory."""
        # Paths under .specs/
        under_specs: list[Path | str] = [
            tmp_path / ".specs" / "src" / "main.py",
            "src/main.py",  # Relative path interpreted as under .specs/
            ".specs/docs/README.md",
        ]

        for path in under_specs:
            assert converter.is_under_specs_dir(path) is True

        # Paths not under .specs/
        not_under_specs: list[Path | str] = [
            tmp_path / "other" / "file.py",
            "/absolute/path/elsewhere.py",
        ]

        for path in not_under_specs:
            assert converter.is_under_specs_dir(path) is False

    def test_path_converter_normalizes_path_separators(
        self, converter: GitPathConverter
    ) -> None:
        """Test normalization of path separators to forward slashes."""
        test_cases = [
            ("src\\main.py", "src/main.py"),
            ("docs\\sub\\README.md", "docs/sub/README.md"),
            ("src/main.py", "src/main.py"),  # Already normalized
            ("mixed\\path/separators.txt", "mixed/path/separators.txt"),
        ]

        for input_path, expected in test_cases:
            result = converter.normalize_path_separators(input_path)
            assert result == expected

    def test_path_converter_provides_conversion_info(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test comprehensive path conversion information."""
        test_path = ".specs/src/main.py"

        info = converter.get_conversion_info(test_path)

        # Check that all expected keys are present
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

        assert set(info.keys()) == expected_keys

        # Check specific values
        assert info["original_path"] == test_path
        assert info["has_specs_prefix"] is True
        assert info["git_path"] == "src/main.py"
        assert info["specs_prefixed_path"] == ".specs/src/main.py"
        assert info["normalized_separators"] == ".specs/src/main.py"

    def test_path_converter_info_for_absolute_path(
        self, converter: GitPathConverter, tmp_path: Path
    ) -> None:
        """Test conversion info for absolute paths."""
        absolute_path = tmp_path / ".specs" / "src" / "main.py"

        info = converter.get_conversion_info(absolute_path)

        assert info["original_path"] == str(absolute_path)
        assert info["is_absolute"] is True
        assert (
            info["has_specs_prefix"] is False
        )  # Absolute paths don't have .specs/ prefix
        assert info["git_path"] == "src/main.py"

    def test_path_converter_info_for_relative_path(
        self, converter: GitPathConverter
    ) -> None:
        """Test conversion info for relative paths."""
        relative_path = "src/main.py"

        info = converter.get_conversion_info(relative_path)

        assert info["original_path"] == relative_path
        assert info["is_absolute"] is False
        assert info["has_specs_prefix"] is False
        assert info["git_path"] == "src/main.py"
        assert info["specs_prefixed_path"] == ".specs/src/main.py"

    def test_path_converter_handles_pathlib_objects(
        self, converter: GitPathConverter
    ) -> None:
        """Test handling of pathlib.Path objects."""
        path_obj = Path(".specs") / "src" / "main.py"

        git_path = converter.convert_to_git_path(path_obj)
        assert git_path == "src/main.py"

        specs_path = converter.convert_from_git_path(path_obj)
        assert specs_path == Path(".specs/src/main.py")

    def test_path_converter_round_trip_conversion(
        self, converter: GitPathConverter
    ) -> None:
        """Test that conversion round trips work correctly."""
        original_paths = [
            "src/main.py",
            ".specs/docs/README.md",
            "tests/test_example.py",
        ]

        for original in original_paths:
            # Convert to Git path and back
            git_path = converter.convert_to_git_path(original)
            specs_path = converter.convert_from_git_path(git_path)

            # Should result in .specs/ prefixed version
            expected = Path(".specs") / converter.convert_to_git_path(original)
            assert specs_path == expected
