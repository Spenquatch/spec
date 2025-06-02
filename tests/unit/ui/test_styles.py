"""Tests for styles functionality."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from rich.text import Text
from rich.style import Style

from spec_cli.ui.styles import (
    SpecStyles,
    style_text,
    format_path,
    format_status,
    create_rich_text
)
from spec_cli.ui.theme import SpecTheme, ColorScheme


class TestSpecStyles:
    """Test the SpecStyles class."""
    
    def test_spec_styles_formatting(self):
        """Test all SpecStyles formatting methods."""
        # Test status styles
        assert SpecStyles.success("message") == "[success]message[/success]"
        assert SpecStyles.warning("message") == "[warning]message[/warning]"
        assert SpecStyles.error("message") == "[error]message[/error]"
        assert SpecStyles.info("message") == "[info]message[/info]"
        
        # Test path styles
        assert SpecStyles.path("/path/to/file") == "[path]/path/to/file[/path]"
        assert SpecStyles.file("file.py") == "[file]file.py[/file]"
        assert SpecStyles.directory("src") == "[directory]src[/directory]"
        assert SpecStyles.spec_file("index.md") == "[spec_file]index.md[/spec_file]"
        
        # Test content styles
        assert SpecStyles.code("print('hello')") == "[code]print('hello')[/code]"
        assert SpecStyles.command("git status") == "[command]git status[/command]"
        
        # Test UI element styles
        assert SpecStyles.title("Title") == "[title]Title[/title]"
        assert SpecStyles.subtitle("Subtitle") == "[subtitle]Subtitle[/subtitle]"
        assert SpecStyles.label("Label") == "[label]Label[/label]"
        assert SpecStyles.value("Value") == "[value]Value[/value]"
        assert SpecStyles.muted("Muted text") == "[muted]Muted text[/muted]"
        
        # Test with Path objects
        path_obj = Path("/home/user/file.txt")
        assert SpecStyles.path(path_obj) == f"[path]{path_obj}[/path]"
        assert SpecStyles.file(path_obj) == f"[file]{path_obj}[/file]"
        assert SpecStyles.directory(path_obj) == f"[directory]{path_obj}[/directory]"
    
    def test_style_helpers_and_utilities(self):
        """Test style helper functions and utilities."""
        # Test style_text function
        assert style_text("text", "custom") == "[custom]text[/custom]"
        assert style_text("", "style") == "[style][/style]"
        
        # Test format_path with auto-detection
        assert format_path("file.py") == "[file]file.py[/file]"
        assert format_path("directory/") == "[directory]directory/[/directory]"
        assert format_path(".specs/file.md") == "[spec_file].specs/file.md[/spec_file]"
        assert format_path("src/main.py", "auto") == "[file]src/main.py[/file]"
        
        # Test format_path with explicit types
        assert format_path("test", "file") == "[file]test[/file]"
        assert format_path("test", "directory") == "[directory]test[/directory]"
        assert format_path("test", "spec_file") == "[spec_file]test[/spec_file]"
        assert format_path("test", "unknown") == "[path]test[/path]"
        
        # Test format_status without indicator
        assert format_status("message", "success", False) == "[success]message[/success]"
        assert format_status("message", "error", False) == "[error]message[/error]"
        
        # Test format_status with indicator
        with patch('spec_cli.ui.styles.get_current_theme') as mock_theme:
            mock_theme_obj = Mock()
            mock_theme_obj.get_emoji_replacements.return_value = {
                "✅": "[success]✓[/success]",
                "❌": "[error]✗[/error]",
                "⚠️": "[warning]⚠[/warning]",
                "ℹ️": "[info]i[/info]",
            }
            mock_theme.return_value = mock_theme_obj
            
            success_result = format_status("Done", "success", True)
            assert "[success]✓[/success]" in success_result
            assert "[success]Done[/success]" in success_result
            
            error_result = format_status("Failed", "error", True)
            assert "[error]✗[/error]" in error_result
            assert "[error]Failed[/error]" in error_result
            
            # Test unknown status type
            unknown_result = format_status("message", "unknown", True)
            assert "[unknown]message[/unknown]" in unknown_result
        
        # Test create_rich_text
        text_obj = create_rich_text("test text")
        assert isinstance(text_obj, Text)
        assert str(text_obj) == "test text"
        
        # Test create_rich_text with string style
        with patch('spec_cli.ui.styles.get_current_theme') as mock_theme:
            mock_theme_obj = Mock()
            mock_theme_obj.get_style.return_value = "bold red"
            mock_theme.return_value = mock_theme_obj
            
            styled_text = create_rich_text("styled text", "success")
            assert isinstance(styled_text, Text)
            mock_theme_obj.get_style.assert_called_with("success")
        
        # Test create_rich_text with Style object
        style_obj = Style(color="blue", bold=True)
        styled_text_obj = create_rich_text("blue text", style_obj)
        assert isinstance(styled_text_obj, Text)
        assert str(styled_text_obj) == "blue text"


class TestPathFormatting:
    """Test path formatting edge cases."""
    
    def test_path_auto_detection(self):
        """Test automatic path type detection."""
        # Test spec file detection
        spec_paths = [
            ".specs/file.md",
            "project/.specs/component.md",
            Path(".specs/docs/readme.md")
        ]
        for path in spec_paths:
            result = format_path(path, "auto")
            assert "[spec_file]" in result
        
        # Test file detection by extension
        file_paths = [
            "script.py",
            "document.txt",
            "config.json",
            Path("src/main.cpp")
        ]
        for path in file_paths:
            result = format_path(path, "auto")
            assert "[file]" in result
        
        # Test directory detection (no extension)
        dir_paths = [
            "src",
            "tests",
            "documentation",
            Path("build")
        ]
        for path in dir_paths:
            result = format_path(path, "auto")
            assert "[directory]" in result
    
    def test_path_formatting_edge_cases(self):
        """Test path formatting with edge cases."""
        # Test empty path
        assert format_path("") == "[directory][/directory]"
        
        # Test path with dots but not .specs
        dotted_path = "file.with.dots.txt"
        result = format_path(dotted_path, "auto")
        assert "[file]" in result
        
        # Test .specs in middle of path but not .md
        specs_path = ".specs/file.txt"
        result = format_path(specs_path, "auto")
        assert "[file]" in result  # Should be file due to .txt extension
        
        # Test explicit override of auto-detection
        override_result = format_path("file.py", "directory")
        assert "[directory]" in override_result
        assert "[file]" not in override_result


class TestStyleIntegration:
    """Test style integration with themes."""
    
    def test_style_integration_with_themes(self):
        """Test that styles work correctly with different themes."""
        # Test that create_rich_text handles missing styles gracefully
        with patch('spec_cli.ui.styles.get_current_theme') as mock_theme:
            mock_theme_obj = Mock()
            mock_theme_obj.get_style.return_value = ""  # Empty style
            mock_theme.return_value = mock_theme_obj
            
            text_obj = create_rich_text("text", "nonexistent_style")
            assert isinstance(text_obj, Text)
            assert str(text_obj) == "text"
    
    def test_format_status_integration(self):
        """Test format_status integration with theme emoji replacements."""
        # Test when theme has no emoji replacements
        with patch('spec_cli.ui.styles.get_current_theme') as mock_theme:
            mock_theme_obj = Mock()
            mock_theme_obj.get_emoji_replacements.return_value = {}
            mock_theme.return_value = mock_theme_obj
            
            result = format_status("message", "success", True)
            # Should still work but without indicator
            assert "[success]message[/success]" in result
        
        # Test partial emoji replacements
        with patch('spec_cli.ui.styles.get_current_theme') as mock_theme:
            mock_theme_obj = Mock()
            mock_theme_obj.get_emoji_replacements.return_value = {
                "✅": "[success]✓[/success]"
                # Missing other emojis
            }
            mock_theme.return_value = mock_theme_obj
            
            success_result = format_status("ok", "success", True)
            assert "[success]✓[/success]" in success_result
            
            # Should work without indicator for missing emoji
            warning_result = format_status("warn", "warning", True)
            assert "[warning]warn[/warning]" in warning_result
            # Note: Since warning is not in our partial replacements, 
            # format_status will still get the default from the emoji mapping