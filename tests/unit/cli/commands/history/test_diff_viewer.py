"""Tests for diff viewer module."""

from typing import Any
from unittest.mock import Mock, patch

from spec_cli.cli.commands.history.diff_viewer import (
    DiffViewer,
    create_diff_view,
    display_file_diff,
    display_unified_diff,
)


class TestDiffViewer:
    """Test the DiffViewer class."""

    def test_display_no_diff_message_when_no_context_then_shows_basic_message(
        self,
    ) -> None:
        """Test that no diff message displays basic message when no context provided."""
        with patch(
            "spec_cli.cli.commands.history.diff_viewer.get_console"
        ) as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance

            viewer = DiffViewer()
            viewer.display_no_diff_message()

            mock_console_instance.print.assert_called_once_with(
                "[muted]No differences found[/muted]"
            )

    def test_display_no_diff_message_when_context_provided_then_includes_context(
        self,
    ) -> None:
        """Test that no diff message includes context when provided."""
        with patch(
            "spec_cli.cli.commands.history.diff_viewer.get_console"
        ) as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance

            viewer = DiffViewer()
            viewer.display_no_diff_message("for specified files")

            mock_console_instance.print.assert_called_once_with(
                "[muted]No differences found for specified files[/muted]"
            )

    def test_display_diff_summary_when_summary_provided_then_displays_table(
        self,
    ) -> None:
        """Test that diff summary displays table with statistics."""
        with (
            patch("spec_cli.cli.commands.history.diff_viewer.get_console"),
            patch("spec_cli.ui.tables.StatusTable") as mock_table_class,
        ):
            mock_table = Mock()
            mock_table_class.return_value = mock_table

            viewer = DiffViewer()
            diff_summary = {"files_changed": 2, "insertions": 10, "deletions": 5}

            viewer.display_diff_summary(diff_summary)

            mock_table_class.assert_called_once_with("Diff Summary")
            assert mock_table.add_status_item.call_count == 3
            mock_table.print.assert_called_once()

    @patch("spec_cli.cli.commands.history.diff_viewer.get_console")
    def test_display_unified_diff_when_diff_lines_provided_then_formats_correctly(
        self, mock_console: Any
    ) -> None:
        """Test that unified diff displays lines with correct formatting."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        viewer = DiffViewer()
        diff_lines = [
            "--- old_file.py",
            "+++ new_file.py",
            "@@ -1,3 +1,3 @@",
            " unchanged line",
            "-removed line",
            "+added line",
        ]

        viewer._display_unified_diff(diff_lines)

        # Should call print for each line with appropriate formatting
        assert mock_console_instance.print.call_count == 6

        # Check that different line types get different formatting
        calls = mock_console_instance.print.call_args_list
        assert "[bold]" in str(calls[0])  # File headers
        assert "[bold]" in str(calls[1])
        assert "[cyan]" in str(calls[2])  # Line numbers
        assert "[dim]" in str(calls[3])  # Unchanged lines
        assert "[red]" in str(calls[4])  # Removed lines
        assert "[green]" in str(calls[5])  # Added lines

    @patch("spec_cli.cli.commands.history.diff_viewer.get_console")
    def test_display_side_by_side_diff_when_content_provided_then_creates_panels(
        self, mock_console: Any
    ) -> None:
        """Test that side-by-side diff creates proper panels."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        viewer = DiffViewer()
        old_content = "line 1\nline 2\nold line 3"
        new_content = "line 1\nline 2\nnew line 3"
        syntax = "python"

        with (
            patch(
                "spec_cli.cli.commands.history.diff_viewer.Panel"
            ) as mock_panel_class,
            patch(
                "spec_cli.cli.commands.history.diff_viewer.Columns"
            ) as mock_columns_class,
        ):
            mock_panel1 = Mock()
            mock_panel2 = Mock()
            mock_panel_class.side_effect = [mock_panel1, mock_panel2]
            mock_columns = Mock()
            mock_columns_class.return_value = mock_columns

            viewer._display_side_by_side_diff(old_content, new_content, syntax)

            # Should create two panels and display them in columns
            assert mock_panel_class.call_count == 2
            mock_columns_class.assert_called_once_with(
                [mock_panel1, mock_panel2], equal=True
            )
            mock_console_instance.print.assert_called_with(mock_columns)


class TestConvenienceFunctions:
    """Test the standalone convenience functions."""

    def test_create_diff_view_when_called_then_returns_diff_viewer_instance(
        self,
    ) -> None:
        """Test that create_diff_view returns a DiffViewer instance."""
        result = create_diff_view()

        assert isinstance(result, DiffViewer)

    @patch("spec_cli.cli.commands.history.diff_viewer.DiffViewer.display_file_diff")
    def test_display_file_diff_function_when_called_then_creates_viewer_and_calls_method(
        self, mock_display: Any
    ) -> None:
        """Test the display_file_diff convenience function."""
        display_file_diff("test.py", "old", "new", None, "python")

        mock_display.assert_called_once_with("test.py", "old", "new", None, "python")

    @patch("spec_cli.cli.commands.history.diff_viewer.DiffViewer._display_unified_diff")
    def test_display_unified_diff_function_when_called_then_creates_viewer_and_calls_method(
        self, mock_display: Any
    ) -> None:
        """Test the display_unified_diff convenience function."""
        diff_lines = ["+ added line", "- removed line"]

        display_unified_diff(diff_lines)

        mock_display.assert_called_once_with(diff_lines)
