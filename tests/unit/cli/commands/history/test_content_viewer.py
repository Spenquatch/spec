"""Tests for content viewer module."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

from spec_cli.cli.commands.history.content_viewer import (
    ContentViewer,
    create_content_display,
    display_file_content,
    display_spec_content,
)


class TestContentViewer:
    """Test the ContentViewer class."""

    def test_get_syntax_language_when_python_extension_then_returns_python(
        self,
    ) -> None:
        """Test that Python file extension returns python language."""
        viewer = ContentViewer()

        result = viewer._get_syntax_language(".py")

        assert result == "python"

    def test_get_syntax_language_when_unknown_extension_then_returns_text(self) -> None:
        """Test that unknown file extension returns text language."""
        viewer = ContentViewer()

        result = viewer._get_syntax_language(".unknown")

        assert result == "text"

    def test_looks_like_markdown_when_contains_header_then_returns_true(self) -> None:
        """Test that content with markdown headers is detected as markdown."""
        viewer = ContentViewer()

        result = viewer._looks_like_markdown("# This is a header\nSome content")

        assert result is True

    def test_looks_like_markdown_when_plain_text_then_returns_false(self) -> None:
        """Test that plain text content is not detected as markdown."""
        viewer = ContentViewer()

        result = viewer._looks_like_markdown(
            "This is just plain text without markdown indicators"
        )

        assert result is False

    @patch("spec_cli.cli.commands.history.content_viewer.get_console")
    def test_display_spec_content_when_no_content_then_shows_no_content_message(
        self, mock_console: Any
    ) -> None:
        """Test that spec content without content shows appropriate message."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        viewer = ContentViewer()
        spec_data: Dict[str, Any] = {"metadata": {}}

        viewer.display_spec_content(spec_data, show_metadata=False)

        mock_console_instance.print.assert_called_with(
            "[muted]No content available[/muted]"
        )


class TestConvenienceFunctions:
    """Test the standalone convenience functions."""

    @patch(
        "spec_cli.cli.commands.history.content_viewer.ContentViewer.display_spec_content"
    )
    def test_display_spec_content_function_when_called_then_creates_viewer_and_calls_method(
        self, mock_display: Any
    ) -> None:
        """Test the display_spec_content convenience function."""
        spec_data = {"content": "test content"}

        display_spec_content(spec_data, True)

        mock_display.assert_called_once_with(spec_data, True)

    @patch(
        "spec_cli.cli.commands.history.content_viewer.ContentViewer.display_file_content"
    )
    def test_display_file_content_function_when_called_then_creates_viewer_and_calls_method(
        self, mock_display: Any
    ) -> None:
        """Test the display_file_content convenience function."""
        file_path = Path("test.py")

        display_file_content(file_path, "content", True, False)

        mock_display.assert_called_once_with(file_path, "content", True, False)

    def test_create_content_display_when_called_then_returns_content_viewer_instance(
        self,
    ) -> None:
        """Test that create_content_display returns a ContentViewer instance."""
        result = create_content_display()

        assert isinstance(result, ContentViewer)
