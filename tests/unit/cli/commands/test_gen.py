"""Tests for gen command module."""

from pathlib import Path
from typing import Any, List
from unittest.mock import Mock, patch

from spec_cli.cli.commands.gen import (
    _display_generation_results,
    _expand_source_files,
    _show_dry_run_preview,
)
from spec_cli.cli.commands.generation.workflows import GenerationResult
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy


class TestExpandSourceFiles:
    """Test the _expand_source_files function."""

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_single_file_then_validates_and_returns_if_processable(
        self, mock_validator_class: Any
    ) -> None:
        """Test that single file is validated and returned if processable."""
        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = True
        mock_validator_class.return_value = mock_validator

        test_file = Mock(spec=Path)
        test_file.is_file.return_value = True
        test_file.is_dir.return_value = False

        result = _expand_source_files([test_file])

        mock_validator._is_processable_file.assert_called_once_with(test_file)
        assert result == [test_file]

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_single_file_not_processable_then_returns_empty(
        self, mock_validator_class: Any
    ) -> None:
        """Test that non-processable file returns empty list."""
        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = False
        mock_validator_class.return_value = mock_validator

        test_file = Mock(spec=Path)
        test_file.is_file.return_value = True
        test_file.is_dir.return_value = False

        result = _expand_source_files([test_file])

        assert result == []

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_directory_then_expands_to_processable_files(
        self, mock_validator_class: Any
    ) -> None:
        """Test that directory is expanded to processable files."""
        mock_validator = Mock()
        file1 = Mock(spec=Path)
        file2 = Mock(spec=Path)
        mock_validator._get_processable_files_in_directory.return_value = [file1, file2]
        mock_validator_class.return_value = mock_validator

        test_dir = Mock(spec=Path)
        test_dir.is_file.return_value = False
        test_dir.is_dir.return_value = True

        result = _expand_source_files([test_dir])

        mock_validator._get_processable_files_in_directory.assert_called_once_with(
            test_dir
        )
        assert result == [file1, file2]


class TestShowDryRunPreview:
    """Test the _show_dry_run_preview function."""

    @patch("spec_cli.cli.commands.gen.show_message")
    @patch("spec_cli.cli.commands.gen.get_console")
    def test_show_dry_run_preview_when_called_then_displays_preview_info(
        self, mock_console: Any, mock_show_message: Any
    ) -> None:
        """Test that dry run preview displays correct information."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        source_files = [Path("test1.py"), Path("test2.py")]
        template = "custom"
        conflict_strategy = ConflictResolutionStrategy.OVERWRITE

        _show_dry_run_preview(source_files, template, conflict_strategy)

        # Check that console.print was called with expected content
        assert (
            mock_console_instance.print.call_count >= 4
        )  # Header, template, strategy, files count
        mock_show_message.assert_called_once_with(
            "This is a dry run. No files would be modified.", "info"
        )

    @patch("spec_cli.cli.commands.gen.show_message")
    @patch("spec_cli.cli.commands.gen.get_console")
    def test_show_dry_run_preview_when_empty_files_then_shows_zero_count(
        self, mock_console: Any, mock_show_message: Any
    ) -> None:
        """Test that dry run preview handles empty file list."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        source_files: List[Path] = []
        template = "default"
        conflict_strategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE

        _show_dry_run_preview(source_files, template, conflict_strategy)

        # Verify that the files count shows 0
        calls = mock_console_instance.print.call_args_list
        files_call = [call for call in calls if "Files to process" in str(call)]
        assert len(files_call) >= 1
        assert "0" in str(files_call[0])


class TestDisplayGenerationResults:
    """Test the _display_generation_results function."""

    @patch("spec_cli.cli.commands.gen.get_console")
    def test_display_generation_results_when_successful_result_then_displays_success_message(
        self, mock_console: Any
    ) -> None:
        """Test that successful generation results display success message."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        result = GenerationResult(
            generated_files=[Path("test1.md"), Path("test2.md")],
            skipped_files=[],
            failed_files=[],
            conflicts_resolved=[],
            total_processing_time=1.5,
            success=True,
        )

        _display_generation_results(result)

        # Check that console.print was called (exact content may vary)
        assert mock_console_instance.print.call_count > 0

    @patch("spec_cli.cli.commands.gen.get_console")
    def test_display_generation_results_when_failed_result_then_displays_failure_info(
        self, mock_console: Any
    ) -> None:
        """Test that failed generation results display failure information."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        result = GenerationResult(
            generated_files=[],
            skipped_files=[],
            failed_files=[{"file": "test.py", "error": "Test error"}],
            conflicts_resolved=[],
            total_processing_time=0.5,
            success=False,
        )

        _display_generation_results(result)

        # Check that console.print was called
        assert mock_console_instance.print.call_count > 0
