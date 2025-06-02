"""Tests for add command module."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from spec_cli.cli.commands.add import (
    _analyze_git_status,
    _expand_spec_files,
    _filter_spec_files,
)


class TestExpandSpecFiles:
    """Test the _expand_spec_files function."""

    def test_expand_spec_files_when_single_file_then_returns_file(
        self, tmp_path: Any
    ) -> None:
        """Test that single file is returned as-is."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        result = _expand_spec_files([test_file])

        assert result == [test_file]

    def test_expand_spec_files_when_directory_then_returns_all_files(
        self, tmp_path: Any
    ) -> None:
        """Test that directory is expanded to all contained files."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        file1 = test_dir / "file1.md"
        file1.write_text("content1")
        file2 = test_dir / "file2.md"
        file2.write_text("content2")

        result = _expand_spec_files([test_dir])

        assert len(result) == 2
        assert file1 in result
        assert file2 in result


class TestFilterSpecFiles:
    """Test the _filter_spec_files function."""

    def test_filter_spec_files_when_file_in_specs_directory_then_included(self) -> None:
        """Test that files in .specs directory are included."""
        spec_file = Path(".specs/test.md")

        result = _filter_spec_files([spec_file])

        assert result == [spec_file]

    def test_filter_spec_files_when_file_outside_specs_directory_then_excluded(
        self,
    ) -> None:
        """Test that files outside .specs directory are excluded."""
        non_spec_file = Path("src/test.py")

        result = _filter_spec_files([non_spec_file])

        assert result == []


class TestAnalyzeGitStatus:
    """Test the _analyze_git_status function."""

    @patch("spec_cli.cli.commands.add.debug_logger")
    def test_analyze_git_status_when_repo_status_succeeds_then_returns_status_dict(
        self, mock_logger: Any
    ) -> None:
        """Test that git status analysis returns proper structure."""
        mock_repo = Mock()
        mock_repo.status.return_value = None
        spec_files = [Path(".specs/test.md")]

        result = _analyze_git_status(spec_files, mock_repo)

        assert "untracked" in result
        assert "modified" in result
        assert "staged" in result
        assert "up_to_date" in result
        assert ".specs/test.md" in result["untracked"]

    @patch("spec_cli.cli.commands.add.debug_logger")
    def test_analyze_git_status_when_repo_status_fails_then_assumes_untracked(
        self, mock_logger: Any
    ) -> None:
        """Test that git status failure defaults to untracked files."""
        mock_repo = Mock()
        mock_repo.status.side_effect = Exception("Git error")
        spec_files = [Path(".specs/test.md")]

        result = _analyze_git_status(spec_files, mock_repo)

        assert ".specs/test.md" in result["untracked"]
        mock_logger.log.assert_called_with(
            "WARNING", "Failed to get Git status", error="Git error"
        )
