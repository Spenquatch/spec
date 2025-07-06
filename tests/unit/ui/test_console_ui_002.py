"""Unit tests for Console UI Module - Console Interface.

Test Coverage Focus:
- SpecConsole initialization and configuration
- Console printing methods (print, print_status, print_section)
- Emoji replacement functionality
- Console properties and methods (width, terminal, export)
- Theme management and updates
- ConsoleManager singleton functionality
- Global console convenience functions

This test module achieves 40% coverage target for console UI functionality.
"""

from unittest.mock import Mock, patch

from rich.console import Console
from rich.theme import Theme

from spec_cli.ui.console import (
    ConsoleManager,
    SpecConsole,
    get_console,
    reset_console,
    set_console,
    spec_console,
)
from spec_cli.ui.theme import SpecTheme

class TestSpecConsole:
    """Test SpecConsole class functionality."""

    @patch("spec_cli.ui.console.get_current_theme")
    @patch("spec_cli.ui.console.debug_logger")
    def test_spec_console_initialization_with_defaults(self, mock_logger, mock_theme):
        """Test SpecConsole initialization with default parameters."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        # Act
        console = SpecConsole()

        # Assert
        assert console.theme == mock_theme_instance
        assert console.no_color is False
        assert isinstance(console._console, Console)
        mock_logger.log.assert_called_once()

    @patch("spec_cli.ui.console.get_current_theme")
    @patch("spec_cli.ui.console.debug_logger")
    def test_spec_console_initialization_with_custom_params(
        self, mock_logger, mock_theme
    ):
        """Test SpecConsole initialization with custom parameters."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "dark"

        custom_theme = Mock(spec=SpecTheme)
        custom_theme.theme = Theme({})
        custom_theme.color_scheme = Mock()
        custom_theme.color_scheme.value = "custom"

        # Act
        console = SpecConsole(
            theme=custom_theme, width=120, force_terminal=True, no_color=True
        )

        # Assert
        assert console.theme == custom_theme
        assert console.no_color is True
        mock_logger.log.assert_called_once()

    def test_console_property_access(self):
        """Test console property returns Rich Console instance."""
        # Arrange & Act
        with patch("spec_cli.ui.console.get_current_theme") as mock_theme:
            mock_theme_instance = Mock(spec=SpecTheme)
            mock_theme_instance.theme = Theme({})
            mock_theme_instance.color_scheme = Mock()
            mock_theme_instance.color_scheme.value = "default"
            mock_theme.return_value = mock_theme_instance

            console = SpecConsole()
            rich_console = console.console

        # Assert
        assert isinstance(rich_console, Console)
        assert rich_console is console._console

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_with_string_objects(self, mock_theme):
        """Test print method with string objects and emoji replacement."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._replace_emojis = Mock(return_value="processed text")
        console._console.print = Mock()

        # Act
        console.print("test message", "another string")

        # Assert
        console._replace_emojis.assert_called()
        console._console.print.assert_called_once_with(
            "processed text", "processed text"
        )

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_with_non_string_objects(self, mock_theme):
        """Test print method with non-string objects."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._console.print = Mock()

        # Act
        test_obj = {"key": "value"}
        console.print(test_obj, 42)

        # Assert
        console._console.print.assert_called_once_with(test_obj, 42)

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_status_with_default_status(self, mock_theme):
        """Test print_status method with default info status."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console.print = Mock()

        # Act
        console.print_status("Test message")

        # Assert
        console.print.assert_called_once_with("[info]Test message[/info]")

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_status_with_custom_status(self, mock_theme):
        """Test print_status method with custom status type."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console.print = Mock()

        # Act
        console.print_status("Error occurred", status="error", style="bold")

        # Assert
        console.print.assert_called_once_with(
            "[error]Error occurred[/error]", style="bold"
        )

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_section_with_title_only(self, mock_theme):
        """Test print_section method with title only."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console.print = Mock()

        # Act
        console.print_section("Section Title")

        # Assert
        console.print.assert_called_once_with("\n[title]Section Title[/title]")

    @patch("spec_cli.ui.console.get_current_theme")
    def test_print_section_with_content(self, mock_theme):
        """Test print_section method with title and content."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console.print = Mock()

        # Act
        console.print_section("Section Title", "Content here", style="dim")

        # Assert
        expected_calls = [
            (("\n[title]Section Title[/title]",), {}),
            (("Content here",), {"style": "dim"}),
        ]
        assert console.print.call_args_list == expected_calls

    @patch("spec_cli.ui.console.get_current_theme")
    def test_replace_emojis_with_no_color(self, mock_theme):
        """Test emoji replacement when no_color is True."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme_instance.get_emoji_replacements.return_value = {
            "😀": "[green]happy[/green]",
            "❌": "[red]error[/red]",
        }
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole(no_color=True)

        # Act
        result = console._replace_emojis("😀 Test ❌ message")

        # Assert
        assert "happy Test error message" == result

    @patch("spec_cli.ui.console.get_current_theme")
    def test_replace_emojis_with_color(self, mock_theme):
        """Test emoji replacement when no_color is False."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme_instance.get_emoji_replacements.return_value = {
            "😀": "[green]happy[/green]",
            "❌": "[red]error[/red]",
        }
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole(no_color=False)

        # Act
        result = console._replace_emojis("😀 Test ❌ message")

        # Assert
        assert "[green]happy[/green] Test [red]error[/red] message" == result

    @patch("spec_cli.ui.console.get_current_theme")
    def test_get_width_returns_integer(self, mock_theme):
        """Test get_width method returns integer width."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._console.width = 80.0

        # Act
        width = console.get_width()

        # Assert
        assert width == 80
        assert isinstance(width, int)

    @patch("spec_cli.ui.console.get_current_theme")
    def test_is_terminal_returns_boolean(self, mock_theme):
        """Test is_terminal method returns boolean."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        # Replace the console with a mock that has is_terminal property
        mock_console = Mock()
        mock_console.is_terminal = True
        console._console = mock_console

        # Act
        is_terminal = console.is_terminal()

        # Assert
        assert is_terminal is True
        assert isinstance(is_terminal, bool)

    @patch("spec_cli.ui.console.get_current_theme")
    @patch("spec_cli.ui.console.debug_logger")
    def test_export_text_functionality(self, mock_logger, mock_theme):
        """Test export_text method functionality."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._console.export_text = Mock(return_value="exported text")

        # Act
        result = console.export_text(clear=False)

        # Assert
        assert result == "exported text"
        console._console.export_text.assert_called_once_with(clear=False)
        mock_logger.log.assert_called()

    @patch("spec_cli.ui.console.get_current_theme")
    @patch("spec_cli.ui.console.debug_logger")
    def test_export_html_functionality(self, mock_logger, mock_theme):
        """Test export_html method functionality."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._console.export_html = Mock(return_value="<html>content</html>")

        # Act
        result = console.export_html(clear=True)

        # Assert
        assert result == "<html>content</html>"
        console._console.export_html.assert_called_once_with(clear=True)
        mock_logger.log.assert_called()

    @patch("spec_cli.ui.console.get_current_theme")
    @patch("spec_cli.ui.console.debug_logger")
    def test_clear_console_functionality(self, mock_logger, mock_theme):
        """Test clear method functionality."""
        # Arrange
        mock_theme_instance = Mock(spec=SpecTheme)
        mock_theme_instance.theme = Theme({})
        mock_theme_instance.color_scheme = Mock()
        mock_theme_instance.color_scheme.value = "default"
        mock_theme.return_value = mock_theme_instance

        console = SpecConsole()
        console._console.clear = Mock()

        # Act
        console.clear()

        # Assert
        console._console.clear.assert_called_once()
        mock_logger.log.assert_called_with("DEBUG", "Console cleared")

class TestConsoleManager:
    """Test ConsoleManager singleton functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset singleton state
        if hasattr(ConsoleManager, "_instances"):
            ConsoleManager._instances.clear()
        # Reset any cached console
        manager = ConsoleManager()
        manager.reset_console()

    @patch("spec_cli.ui.console.get_settings")
    @patch("spec_cli.ui.console.debug_logger")
    def test_console_manager_get_console_creates_new(self, mock_logger, mock_settings):
        """Test ConsoleManager creates new console when none exists."""
        # Arrange
        mock_settings.return_value = Mock(no_color=False)

        # Act
        with patch("spec_cli.ui.console.SpecConsole") as mock_spec_console:
            mock_instance = Mock()
            mock_spec_console.return_value = mock_instance
            manager = ConsoleManager()  # Create manager inside patch
            console = manager.get_console()

        # Assert
        assert console == mock_instance
        mock_spec_console.assert_called_once_with(no_color=False)
        mock_logger.log.assert_called_with("INFO", "Global console initialized")

    def test_console_manager_get_console_returns_existing(self):
        """Test ConsoleManager returns existing console."""
        # Arrange
        manager = ConsoleManager()
        existing_console = Mock(spec=SpecConsole)
        manager._spec_console = existing_console

        # Act
        console = manager.get_console()

        # Assert
        assert console == existing_console

    @patch("spec_cli.ui.console.debug_logger")
    def test_console_manager_set_console(self, mock_logger):
        """Test ConsoleManager set_console method."""
        # Arrange
        manager = ConsoleManager()
        new_console = Mock(spec=SpecConsole)

        # Act
        manager.set_console(new_console)

        # Assert
        assert manager._spec_console == new_console
        mock_logger.log.assert_called_with("INFO", "Global console updated")

    @patch("spec_cli.ui.console.debug_logger")
    def test_console_manager_reset_console(self, mock_logger):
        """Test ConsoleManager reset_console method."""
        # Arrange
        manager = ConsoleManager()
        manager._spec_console = Mock(spec=SpecConsole)

        # Act
        manager.reset_console()

        # Assert
        assert manager._spec_console is None
        mock_logger.log.assert_called_with("INFO", "Global console reset")

class TestGlobalConsoleFunctions:
    """Test global console convenience functions."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset singleton state
        if hasattr(ConsoleManager, "_instances"):
            ConsoleManager._instances.clear()

    @patch("spec_cli.ui.console.ConsoleManager")
    def test_get_console_function(self, mock_manager_class):
        """Test get_console convenience function."""
        # Arrange
        mock_manager = Mock()
        mock_console = Mock(spec=SpecConsole)
        mock_manager.get_console.return_value = mock_console
        mock_manager_class.return_value = mock_manager

        # Act
        result = get_console()

        # Assert
        assert result == mock_console
        mock_manager.get_console.assert_called_once()

    @patch("spec_cli.ui.console.ConsoleManager")
    def test_set_console_function(self, mock_manager_class):
        """Test set_console convenience function."""
        # Arrange
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        test_console = Mock(spec=SpecConsole)

        # Act
        set_console(test_console)

        # Assert
        mock_manager.set_console.assert_called_once_with(test_console)

        """Test reset_console convenience function."""
        # Arrange
        with patch("spec_cli.ui.console.ConsoleManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            # Act
            reset_console()

            # Assert
            mock_manager.reset_console.assert_called_once()
            # Import the actual class for comparison

    def test_spec_console_alias_function(self):
        """Test spec_console alias points to get_console."""
        # Act & Assert
        assert spec_console == get_console
