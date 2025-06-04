"""Tests for console functionality."""

from unittest.mock import Mock, patch

from rich.console import Console

from spec_cli.config.settings import SpecSettings
from spec_cli.ui.console import (
    ConsoleManager,
    SpecConsole,
    get_console,
    reset_console,
    set_console,
)
from spec_cli.ui.theme import ColorScheme, SpecTheme


class TestSpecConsole:
    """Test the SpecConsole class."""

    def test_spec_console_initialization(self) -> None:
        """Test SpecConsole can be initialized with various options."""
        # Test default initialization
        console = SpecConsole()
        assert console.theme is not None
        assert console.no_color is False
        assert console._console is not None
        assert isinstance(console._console, Console)

        # Test with custom theme
        custom_theme = SpecTheme(ColorScheme.DARK)
        console_with_theme = SpecConsole(theme=custom_theme)
        assert console_with_theme.theme is custom_theme
        assert console_with_theme.theme.color_scheme == ColorScheme.DARK

        # Test with no_color option
        no_color_console = SpecConsole(no_color=True)
        assert no_color_console.no_color is True
        # Rich console no_color is passed as constructor argument, not in options

        # Test with custom width
        console_with_width = SpecConsole(width=120)
        assert console_with_width._console.width == 120

    def test_console_emoji_replacement(self) -> None:
        """Test emoji replacement functionality."""
        console = SpecConsole()

        # Test basic emoji replacement
        text_with_emoji = "Operation completed ✅"
        replaced = console._replace_emojis(text_with_emoji)
        assert "✅" not in replaced
        assert "[success]" in replaced
        assert "✓" in replaced

        # Test multiple emojis
        multi_emoji_text = "Warning ⚠️ and error ❌ occurred"
        replaced_multi = console._replace_emojis(multi_emoji_text)
        assert "⚠️" not in replaced_multi
        assert "❌" not in replaced_multi
        assert "[warning]" in replaced_multi
        assert "[error]" in replaced_multi

        # Test no_color mode strips formatting
        no_color_console = SpecConsole(no_color=True)
        no_color_replaced = no_color_console._replace_emojis("Success ✅")
        assert "[success]" not in no_color_replaced
        assert "✓" in no_color_replaced or "✅" not in no_color_replaced

    def test_console_status_printing(self) -> None:
        """Test status message printing with styling."""
        console = SpecConsole()

        # Mock the underlying Rich console
        with patch.object(console, "_console") as mock_console:
            console.print_status("Test message", "success")

            # Verify print was called with styled message
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0]
            assert "[success]Test message[/success]" in call_args

        # Test print_section
        with patch.object(console, "_console") as mock_console:
            console.print_section("Test Section", "Content here")

            # Should be called twice - once for title, once for content
            assert mock_console.print.call_count == 2

            # First call should be the title
            first_call = mock_console.print.call_args_list[0][0]
            assert "[title]Test Section[/title]" in str(first_call)

    def test_console_theme_updates(self) -> None:
        """Test updating console theme."""
        console = SpecConsole()
        original_console = console._console
        original_width = console._console.width

        # Update to new theme
        new_theme = SpecTheme(ColorScheme.MINIMAL)
        console.update_theme(new_theme)

        # Verify theme was updated
        assert console.theme is new_theme
        assert console.theme.color_scheme == ColorScheme.MINIMAL

        # Verify console was recreated (Rich doesn't support theme updates)
        assert console._console is not original_console
        assert console._console.width == original_width  # Width preserved

    def test_console_export_functionality(self) -> None:
        """Test console export capabilities."""
        console = SpecConsole()

        # Print some content
        console.print("Test content")
        console.print_status("Success message", "success")

        # Test text export
        text_output = console.export_text(clear=False)
        assert "Test content" in text_output
        assert len(text_output) > 0

        # Test HTML export
        html_output = console.export_html(clear=False)
        assert len(html_output) > 0
        assert "<" in html_output  # Should contain HTML tags

        # Test console properties
        width = console.get_width()
        assert isinstance(width, int)
        assert width > 0

        is_terminal = console.is_terminal()
        assert isinstance(is_terminal, bool)

    def test_global_console_management(self) -> None:
        """Test global console management functions."""
        # Reset console to ensure clean state
        reset_console()

        # Test get_console creates console on first call
        with patch("spec_cli.ui.console.SpecConsole") as mock_spec_console:
            mock_instance = Mock()
            mock_spec_console.return_value = mock_instance

            console = get_console()
            assert console is not None
            mock_spec_console.assert_called_once()

        # Test set_console
        custom_console = SpecConsole()
        set_console(custom_console)

        current = get_console()
        assert current is custom_console

        # Test reset_console
        reset_console()
        # After reset, next call should create new console
        with patch("spec_cli.ui.console.SpecConsole") as mock_spec_console:
            mock_instance = Mock()
            mock_spec_console.return_value = mock_instance

            console = get_console()
            mock_spec_console.assert_called_once()


class TestConsoleIntegration:
    """Test console integration with settings and themes."""

    def test_console_with_settings_integration(self) -> None:
        """Test console initialization with settings."""
        # Test with no_color setting
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.no_color = True

        with patch("spec_cli.ui.console.get_settings", return_value=mock_settings):
            reset_console()  # Clear any cached console
            console = get_console()
            assert console.no_color is True

        # Test without no_color setting (default False)
        mock_settings_default = Mock(spec=SpecSettings)
        # Use getattr default behavior for missing attributes

        with patch(
            "spec_cli.ui.console.get_settings", return_value=mock_settings_default
        ):
            reset_console()
            console = get_console()
            assert console.no_color is False

    def test_console_print_methods(self) -> None:
        """Test various print methods handle input correctly."""
        console = SpecConsole()

        # Test print with mixed object types
        with patch.object(console, "_console") as mock_console:
            console.print("string", 123, ["list"])

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0]
            assert len(call_args) == 3
            assert call_args[1] == 123  # Non-string objects passed through
            assert call_args[2] == ["list"]

        # Test print_section without content
        with patch.object(console, "_console") as mock_console:
            console.print_section("Title Only")

            # Should only call print once (for title)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0]
            assert "[title]Title Only[/title]" in str(call_args)

    def test_console_properties_and_methods(self) -> None:
        """Test console property access and utility methods."""
        console = SpecConsole()

        # Test console property returns Rich console
        rich_console = console.console
        assert isinstance(rich_console, Console)
        assert rich_console is console._console

        # Test clear method
        with patch.object(console._console, "clear") as mock_clear:
            console.clear()
            mock_clear.assert_called_once()


class TestEmojiReplacement:
    """Test emoji replacement edge cases."""

    def test_emoji_replacement_edge_cases(self) -> None:
        """Test emoji replacement handles edge cases correctly."""
        console = SpecConsole()

        # Test empty string
        assert console._replace_emojis("") == ""

        # Test string with no emojis
        text_no_emoji = "Regular text with no emojis"
        assert console._replace_emojis(text_no_emoji) == text_no_emoji

        # Test unknown emoji (not in replacement map)
        text_unknown_emoji = "Unknown emoji 🦄"
        replaced = console._replace_emojis(text_unknown_emoji)
        assert "🦄" in replaced  # Should remain unchanged

        # Test repeated emojis
        text_repeated = "Success ✅ and more success ✅"
        replaced_repeated = console._replace_emojis(text_repeated)
        assert text_repeated.count("✅") == replaced_repeated.count("✓")

    def test_no_color_emoji_stripping(self) -> None:
        """Test emoji replacement in no_color mode strips markup correctly."""
        no_color_console = SpecConsole(no_color=True)

        # Test that markup is stripped but content remains
        text_with_emoji = "Complete ✅"
        replaced = no_color_console._replace_emojis(text_with_emoji)

        # Should not contain Rich markup tags
        assert "[success]" not in replaced
        assert "[/success]" not in replaced

        # Should contain the replacement character or remove emoji entirely
        assert "✅" not in replaced or "✓" in replaced


class TestConsoleManager:
    """Test ConsoleManager singleton functionality."""

    def teardown_method(self) -> None:
        """Reset console manager after each test."""
        reset_console()

    def test_console_manager_singleton_behavior(self) -> None:
        """Test ConsoleManager provides singleton behavior."""
        manager1 = ConsoleManager()
        manager2 = ConsoleManager()

        # Should be the same instance
        assert manager1 is manager2

        # Should have singleton attributes
        assert hasattr(ConsoleManager, "_is_singleton")
        assert hasattr(ConsoleManager, "_original_class")
        assert ConsoleManager._is_singleton is True

    def test_console_manager_provides_consistent_console(self) -> None:
        """Test ConsoleManager returns consistent console instances."""
        manager = ConsoleManager()

        console1 = manager.get_console()
        console2 = manager.get_console()

        # Should return the same console instance
        assert console1 is console2

    def test_console_manager_reset_clears_console(self) -> None:
        """Test ConsoleManager reset functionality."""
        manager1 = ConsoleManager()
        console1 = manager1.get_console()

        reset_console()

        manager2 = ConsoleManager()
        console2 = manager2.get_console()

        # Should be different managers and consoles after reset
        assert manager1 is not manager2
        assert console1 is not console2
