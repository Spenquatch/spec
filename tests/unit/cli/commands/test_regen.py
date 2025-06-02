"""Tests for regen command module."""

from pathlib import Path
from unittest.mock import Mock, patch

from spec_cli.cli.commands.regen import (
    _filter_files_with_specs,
    _find_all_spec_sources,
    _show_regen_dry_run_preview,
)


class TestFindAllSpecSources:
    """Test the _find_all_spec_sources function."""

    @patch("spec_cli.cli.commands.regen.Path")
    def test_find_all_spec_sources_when_no_specs_dir_then_returns_empty(
        self, mock_path_class
    ):
        """Test that missing .specs directory returns empty list."""
        mock_specs_dir = Mock()
        mock_specs_dir.exists.return_value = False
        mock_path_class.return_value = mock_specs_dir

        result = _find_all_spec_sources()

        assert result == []

    @patch("spec_cli.cli.commands.regen.Path")
    def test_find_all_spec_sources_when_specs_exist_then_returns_source_files(
        self, mock_path_class
    ):
        """Test that existing specs return corresponding source files."""
        # Mock .specs directory
        mock_specs_dir = Mock()
        mock_specs_dir.exists.return_value = True

        # Mock index.md files found in .specs
        mock_index1 = Mock()
        mock_index1.parent.relative_to.return_value = Path("src/module1.py")
        mock_index2 = Mock()
        mock_index2.parent.relative_to.return_value = Path("src/module2.py")

        mock_specs_dir.rglob.return_value = [mock_index1, mock_index2]

        # Mock the Path constructor calls
        def path_side_effect(arg):
            if arg == ".specs":
                return mock_specs_dir
            elif arg == Path("src/module1.py"):
                mock_source1 = Mock()
                mock_source1.exists.return_value = True
                return mock_source1
            elif arg == Path("src/module2.py"):
                mock_source2 = Mock()
                mock_source2.exists.return_value = True
                return mock_source2
            else:
                return Mock()

        mock_path_class.side_effect = path_side_effect

        result = _find_all_spec_sources()

        # Should return the source files that exist
        assert len(result) == 2

    @patch("spec_cli.cli.commands.regen.Path")
    def test_find_all_spec_sources_when_source_files_missing_then_skips_them(
        self, mock_path_class
    ):
        """Test that missing source files are skipped."""
        # Mock .specs directory
        mock_specs_dir = Mock()
        mock_specs_dir.exists.return_value = True

        # Mock index.md file with non-existent source
        mock_index = Mock()
        mock_index.parent.relative_to.return_value = Path("missing/file.py")
        mock_specs_dir.rglob.return_value = [mock_index]

        # Mock path creation
        def path_side_effect(arg):
            if arg == ".specs":
                return mock_specs_dir
            elif arg == Path("missing/file.py"):
                mock_source = Mock()
                mock_source.exists.return_value = False  # Source doesn't exist
                return mock_source
            else:
                return Mock()

        mock_path_class.side_effect = path_side_effect

        result = _find_all_spec_sources()

        assert result == []


class TestFilterFilesWithSpecs:
    """Test the _filter_files_with_specs function."""

    def test_filter_files_with_specs_when_file_has_existing_spec_then_included(
        self, tmp_path
    ):
        """Test that files with existing specs are included."""
        # Create test source file
        source_file = tmp_path / "test.py"
        source_file.write_text("# test file")

        # Create corresponding spec file
        specs_dir = tmp_path / ".specs" / "test.py"
        specs_dir.mkdir(parents=True)
        (specs_dir / "index.md").write_text("# spec content")

        # Change to the temp directory for relative path resolution
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _filter_files_with_specs([Path("test.py")])
            assert Path("test.py") in result
        finally:
            os.chdir(original_cwd)

    def test_filter_files_with_specs_when_file_has_no_spec_then_excluded(
        self, tmp_path
    ):
        """Test that files without specs are excluded."""
        # Create test source file but no spec
        source_file = tmp_path / "test.py"
        source_file.write_text("# test file")

        # Change to the temp directory for relative path resolution
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _filter_files_with_specs([Path("test.py")])
            assert result == []
        finally:
            os.chdir(original_cwd)

    def test_filter_files_with_specs_when_empty_list_then_returns_empty(self):
        """Test that empty file list returns empty result."""
        result = _filter_files_with_specs([])

        assert result == []


class TestShowRegenDryRunPreview:
    """Test the _show_regen_dry_run_preview function."""

    @patch("spec_cli.cli.commands.regen.get_console")
    def test_show_regen_dry_run_preview_when_called_then_displays_preview_info(
        self, mock_console
    ):
        """Test that dry run preview displays correct information."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        source_files = [Path("test1.py"), Path("test2.py")]
        template = "custom"
        preserve_history = True

        _show_regen_dry_run_preview(source_files, template, preserve_history)

        # Check that console.print was called with expected content
        assert (
            mock_console_instance.print.call_count >= 4
        )  # Header, template, preserve_history, files count

    @patch("spec_cli.cli.commands.regen.get_console")
    def test_show_regen_dry_run_preview_when_empty_files_then_shows_zero_count(
        self, mock_console
    ):
        """Test that dry run preview handles empty file list."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        source_files = []
        template = "default"
        preserve_history = False

        _show_regen_dry_run_preview(source_files, template, preserve_history)

        # Verify that the files count shows 0
        calls = mock_console_instance.print.call_args_list
        files_call = [call for call in calls if "Files to regenerate" in str(call)]
        assert len(files_call) >= 1
        assert "0" in str(files_call[0])

    @patch("spec_cli.cli.commands.regen.get_console")
    def test_show_regen_dry_run_preview_when_preserve_history_false_then_shows_correct_setting(
        self, mock_console
    ):
        """Test that preserve history setting is displayed correctly."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        source_files = [Path("test.py")]
        template = "default"
        preserve_history = False

        _show_regen_dry_run_preview(source_files, template, preserve_history)

        # Verify preserve_history setting is shown
        calls = mock_console_instance.print.call_args_list
        preserve_call = [call for call in calls if "Preserve history" in str(call)]
        assert len(preserve_call) >= 1
        assert "False" in str(preserve_call[0])
